from __future__ import annotations

import re
from pathlib import Path

from .models import AuditReport


REQUIRED_METADATA = (
    "object_key",
    "aliases",
    "object_kind",
    "compatibility_target",
    "purpose",
    "primary_object",
)
NON_BASE_STATEMENTS = (
    re.compile(r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\b", re.IGNORECASE),
    re.compile(r"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE|TRIGGER|RULE|POLICY)\b", re.IGNORECASE),
    re.compile(r"\b(?:INSERT\s+INTO|UPDATE\s+[^;]+\s+SET|DELETE\s+FROM|CALL)\b", re.IGNORECASE),
)
CREATE_TABLE_PATTERN = re.compile(
    r"\bCREATE\s+(?:UNLOGGED\s+|TEMP(?:ORARY)?\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_$]*)",
    re.IGNORECASE,
)


def read_asset_metadata(path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:20]:
        stripped = line.strip()
        if not stripped.startswith("-- "):
            continue
        body = stripped[3:]
        if ":" not in body:
            continue
        key, value = body.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def audit_assets(root: Path | str) -> AuditReport:
    root = Path(root)
    report = AuditReport()
    object_root = root / "skills" / "pg-sql-generation" / "assets" / "objects"
    paths = sorted(object_root.glob("**/*.sql")) if object_root.exists() else []
    keys: dict[str, list[Path]] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        metadata = read_asset_metadata(path)
        missing = [key for key in REQUIRED_METADATA if not metadata.get(key)]
        if missing:
            report.error(
                "asset.missing_metadata",
                f"asset metadata is missing: {', '.join(missing)}",
                path=path,
                root=root,
            )
        object_key = metadata.get("object_key", "")
        if object_key:
            keys.setdefault(object_key, []).append(path)
        compatibility = metadata.get("compatibility_target")
        if compatibility and compatibility != "postgresql-18.4":
            report.error(
                "asset.unsupported_compatibility_target",
                f"asset compatibility_target must be postgresql-18.4, got {compatibility!r}",
                path=path,
                root=root,
            )
        for pattern in NON_BASE_STATEMENTS:
            if pattern.search(text):
                report.error(
                    "asset.non_base_statement",
                    "base object assets may contain setup DDL only; target DML, indexes, routines, and calls belong in generated cases",
                    path=path,
                    root=root,
                )
                break

        if metadata.get("object_kind") == "table":
            table_names = {match.group("name") for match in CREATE_TABLE_PATTERN.finditer(text)}
            if not table_names:
                report.error(
                    "asset.missing_primary_ddl",
                    "table asset must contain CREATE TABLE",
                    path=path,
                    root=root,
                )
            primary_object = metadata.get("primary_object")
            if primary_object and primary_object not in table_names:
                report.error(
                    "asset.primary_object_mismatch",
                    f"primary_object {primary_object!r} is not created by this asset",
                    path=path,
                    root=root,
                )

    for object_key, duplicate_paths in keys.items():
        if len(duplicate_paths) > 1:
            for path in duplicate_paths:
                report.error(
                    "asset.duplicate_object_key",
                    f"object_key {object_key!r} is used by more than one asset",
                    path=path,
                    root=root,
                )
    report.summary["asset_count"] = len(paths)
    return report
