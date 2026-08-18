#!/usr/bin/env python3
"""Validate SQL regress filenames and file-scoped object prefixes."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


IDENT = r'(?:"[^"]+"|[A-Za-z_][A-Za-z0-9_$]*)(?:\s*\.\s*(?:"[^"]+"|[A-Za-z_][A-Za-z0-9_$]*))*'


@dataclass(frozen=True)
class Issue:
    file: str
    message: str


def strip_sql_noise(sql: str) -> str:
    """Remove comments and string literals so identifier scans are less noisy."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"'(?:''|[^'])*'", "''", sql)
    sql = re.sub(r"\$[A-Za-z0-9_]*\$.*?\$[A-Za-z0-9_]*\$", "$$", sql, flags=re.DOTALL)
    # GRANT/REVOKE use ON and FROM for privilege targets and grantees; those
    # clauses are not relation references for this file-prefix check.
    sql = re.sub(r"\b(?:GRANT|REVOKE)\b[^;]*;", " ", sql, flags=re.IGNORECASE | re.DOTALL)
    return sql


def normalize_identifier(identifier: str) -> str:
    parts = [part.strip().strip('"') for part in re.split(r"\s*\.\s*", identifier)]
    return parts[-1].lower()


def object_prefix(prefix: str, number: str) -> str:
    return f"{prefix}_{number}_".lower()


def infer_prefix(sql_files: list[Path]) -> str | None:
    prefixes = set()
    for path in sql_files:
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_]*?)(\d{3,})\.sql", path.name)
        if not match:
            return None
        prefixes.add(match.group(1))
    return prefixes.pop() if len(prefixes) == 1 else None


def validate_filenames(sql_files: list[Path], prefix: str) -> list[Issue]:
    issues: list[Issue] = []
    parsed: list[tuple[Path, str]] = []
    for path in sql_files:
        match = re.fullmatch(rf"{re.escape(prefix)}(\d{{3,}})\.sql", path.name)
        if match is None:
            issues.append(
                Issue(
                    path.name,
                    f"filename must match {prefix}<NNN>.sql with at least 3 digits",
                )
            )
        else:
            parsed.append((path, match.group(1)))

    widths = {len(number) for _, number in parsed}
    if len(widths) > 1:
        for path, _ in parsed:
            issues.append(Issue(path.name, "all SQL filenames must use one numbering width"))
        return issues
    if not widths:
        return issues
    width = widths.pop()
    minimum_width = max(3, len(str(len(sql_files))))
    if width < minimum_width:
        issues.append(
            Issue(
                str(sql_files[0].parent),
                f"numbering width {width} cannot represent this {len(sql_files)}-file batch",
            )
        )
    expected_names = {f"{prefix}{index:0{width}d}.sql" for index in range(1, len(sql_files) + 1)}
    actual_names = {path.name for path in sql_files}

    for missing in sorted(expected_names - actual_names):
        issues.append(Issue(missing, "missing expected SQL file in contiguous sequence"))

    for extra in sorted(actual_names - expected_names):
        issues.append(Issue(extra, "unexpected SQL filename for contiguous sequence"))

    return issues


def object_references(sql: str) -> set[str]:
    # Normalize whitespace so the fixed-width guards below also handle row-lock
    # clauses split across lines (FOR UPDATE / FOR NO KEY UPDATE).  Those UPDATE
    # tokens are SELECT syntax, not DML statements with relation targets.
    clean = re.sub(r"\s+", " ", strip_sql_noise(sql))
    cte_pattern = re.compile(
        r'(?i)(?:\bWITH\s+(?:RECURSIVE\s+)?|,)\s*'
        r'(?P<name>"[^"]+"|[A-Za-z_][A-Za-z0-9_$]*)'
        r'(?:\s*\([^)]*\))?\s+AS\s+'
        r'(?:(?:NOT\s+)?MATERIALIZED\s+)?\('
    )
    persistent_patterns = [
        rf"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP(?:ORARY)?\s+|UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP(?:ORARY)?\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bDROP\s+VIEW\s+(?:IF\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bALTER\s+VIEW\s+(?:IF\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bINSERT\s+INTO\s+(?P<name>{IDENT})",
        # Avoid MERGE's "UPDATE SET", trigger event "UPDATE OF", row-lock
        # "FOR UPDATE OF", and privilege "UPDATE ON" keyword sequences.
        rf"(?<!FOR\s)(?<!KEY\s)\bUPDATE\s+(?!(?:SET|OF|ON|TO)\b)(?:ONLY\s+)?(?P<name>{IDENT})",
        rf"\bDELETE\s+FROM\s+(?P<name>{IDENT})",
        rf"\bTRUNCATE\s+(?:TABLE\s+)?(?P<name>{IDENT})",
    ]
    relation_reference_patterns = [
        # A FROM item followed by '(' is a table function, not a persistent
        # relation.  ROWS FROM is likewise a grammar production.  The explicit
        # trailing guard prevents regex backtracking from accepting a truncated
        # function identifier merely to avoid the opening parenthesis.
        rf"\bFROM\s+(?!ROWS\s+FROM\b)(?P<name>{IDENT})(?![A-Za-z0-9_$\"]|\s*(?:\.|\())",
        rf"\bJOIN\s+(?P<name>{IDENT})(?![A-Za-z0-9_$\"]|\s*(?:\.|\())",
    ]

    names: set[str] = set()
    # A CTE name is visible only within its own SQL statement.  Scanning the
    # whole file with one global exemption would let a later, unrelated
    # persistent relation reference reuse that name without prefix validation.
    statements = (statement.strip() for statement in clean.split(";"))
    for statement in (item for item in statements if item):
        create_conversion = re.match(
            r"(?is)^\s*CREATE\s+(?:DEFAULT\s+)?CONVERSION\b",
            statement,
        ) is not None
        alter_database = re.search(
            r"(?i)\bALTER\s+DATABASE\b",
            statement,
        ) is not None
        create_collation_or_transform = re.match(
            r"(?is)^\s*CREATE\s+(?:COLLATION|TRANSFORM)\b",
            statement,
        ) is not None
        cte_names = {
            normalize_identifier(match.group("name"))
            for match in cte_pattern.finditer(statement)
        }
        for pattern in persistent_patterns:
            for match in re.finditer(pattern, statement, flags=re.IGNORECASE):
                name = normalize_identifier(match.group("name"))
                if name not in {"select", "values", "only", "lateral"}:
                    names.add(name)
        if not create_conversion and not alter_database and not create_collation_or_transform:
            for pattern in relation_reference_patterns:
                for match in re.finditer(pattern, statement, flags=re.IGNORECASE):
                    raw_name = match.group("name")
                    # A read of an information_schema.<view> catalog relation
                    # is a system-catalog reference, not a file-scoped object;
                    # normalize_identifier keeps only the view name and would
                    # otherwise lose the system-schema qualifier.
                    if raw_name.lower().startswith("information_schema."):
                        continue
                    name = normalize_identifier(raw_name)
                    if name not in {"select", "values", "only", "lateral"} | cte_names:
                        names.add(name)
    return names


def validate_objects(sql_files: list[Path], prefix: str) -> list[Issue]:
    issues: list[Issue] = []
    seen: dict[str, str] = {}

    for path in sql_files:
        match = re.fullmatch(rf"{re.escape(prefix)}(\d{{3,}})\.sql", path.name)
        if not match:
            continue
        required_prefix = object_prefix(prefix, match.group(1))
        names = object_references(path.read_text(errors="replace"))

        for name in sorted(names):
            if name.startswith("pg_") or name in {"information_schema"}:
                continue
            if not name.startswith(required_prefix):
                issues.append(
                    Issue(
                        path.name,
                        f"object '{name}' must start with '{required_prefix}' derived from filename",
                    )
                )
            owner = seen.setdefault(name, path.name)
            if owner != path.name:
                issues.append(
                    Issue(
                        path.name,
                        f"object '{name}' also appears in {owner}; manual confirmation is required",
                    )
                )

    return issues


def validate_directory(sql_dir: Path, prefix: str | None) -> tuple[str | None, list[Issue]]:
    if not sql_dir.exists() or not sql_dir.is_dir():
        return prefix, [Issue(str(sql_dir), "path is not a directory")]

    sql_files = sorted(path for path in sql_dir.iterdir() if path.is_file() and path.suffix.lower() == ".sql")
    if not sql_files:
        return prefix, [Issue(str(sql_dir), "no direct child .sql files found")]

    resolved_prefix = prefix or infer_prefix(sql_files)
    if not resolved_prefix:
        return None, [Issue(str(sql_dir), "cannot infer a single filename prefix; pass --prefix")]

    issues = validate_filenames(sql_files, resolved_prefix)
    issues.extend(validate_objects(sql_files, resolved_prefix))
    return resolved_prefix, issues


def print_report(sql_dir: Path, prefix: str | None, issues: list[Issue]) -> None:
    print(f"directory: {sql_dir}")
    if prefix:
        print(f"prefix: {prefix}")

    if not issues:
        print("PASS: SQL files satisfy regress output script style checks.")
        return

    print("MANUAL_CONFIRMATION_REQUIRED")
    print("The SQL directory does not satisfy the skill requirements. Review each issue and confirm whether it is intentional.")
    for issue in issues:
        print(f"- {issue.file}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default=".", help="Directory containing SQL files")
    parser.add_argument("--prefix", help="Expected shared filename prefix, e.g. A for A001.sql")
    args = parser.parse_args(argv)

    sql_dir = Path(args.directory).resolve()
    prefix, issues = validate_directory(sql_dir, args.prefix)
    print_report(sql_dir, prefix, issues)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
