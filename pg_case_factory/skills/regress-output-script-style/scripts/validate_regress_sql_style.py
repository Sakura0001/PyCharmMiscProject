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


def expected_width(count: int) -> int:
    return max(3, len(str(count)))


def validate_filenames(sql_files: list[Path], prefix: str) -> list[Issue]:
    issues: list[Issue] = []
    width = expected_width(len(sql_files))
    expected_names = {f"{prefix}{index:0{width}d}.sql" for index in range(1, len(sql_files) + 1)}
    actual_names = {path.name for path in sql_files}

    for path in sql_files:
        match = re.fullmatch(rf"{re.escape(prefix)}(\d{{{width}}})\.sql", path.name)
        if not match:
            issues.append(
                Issue(
                    path.name,
                    f"filename must match {prefix}<NNN>.sql with {width} digit numbering",
                )
            )

    for missing in sorted(expected_names - actual_names):
        issues.append(Issue(missing, "missing expected SQL file in contiguous sequence"))

    for extra in sorted(actual_names - expected_names):
        issues.append(Issue(extra, "unexpected SQL filename for contiguous sequence"))

    return issues


def object_references(sql: str) -> set[str]:
    clean = strip_sql_noise(sql)
    patterns = [
        rf"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP(?:ORARY)?\s+|UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP(?:ORARY)?\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bDROP\s+VIEW\s+(?:IF\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bALTER\s+VIEW\s+(?:IF\s+EXISTS\s+)?(?P<name>{IDENT})",
        rf"\bINSERT\s+INTO\s+(?P<name>{IDENT})",
        rf"\bUPDATE\s+(?P<name>{IDENT})",
        rf"\bDELETE\s+FROM\s+(?P<name>{IDENT})",
        rf"\bTRUNCATE\s+(?:TABLE\s+)?(?P<name>{IDENT})",
        rf"\bFROM\s+(?P<name>{IDENT})",
        rf"\bJOIN\s+(?P<name>{IDENT})",
    ]

    names: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, clean, flags=re.IGNORECASE):
            name = normalize_identifier(match.group("name"))
            if name not in {"select", "values", "only", "lateral"}:
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
