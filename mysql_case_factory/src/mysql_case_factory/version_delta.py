from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml


DELTA_COLUMNS = (
    "statement_key",
    "factor",
    "value",
    "disposition",
    "source_8_0_22",
    "source_8_0_41",
    "official_locator",
    "review_status",
    "notes",
)

CHANGED_STATEMENT_SOURCES = {
    "create_table": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-23.html",
    "alter_instance": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-24.html",
    "create_user": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-27.html",
    "alter_user": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-27.html",
    "create_procedure": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-29.html",
    "create_function": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-29.html",
    "create_trigger": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-29.html",
    "create_function_loadable": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-29.html",
    "select": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-31.html",
    "analyze_table": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-31.html",
    "install_component": "https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-33.html",
}


@dataclass
class VersionDeltaReport:
    added: int = 0
    changed: int = 0
    removed: int = 0
    unchanged: int = 0
    unreviewed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "added": self.added,
            "changed": self.changed,
            "removed": self.removed,
            "unchanged": self.unchanged,
            "unreviewed": self.unreviewed,
            "errors": list(self.errors),
        }


def _load_yaml(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError(f"{path} must contain a mapping")
    return dict(document)


def _factor_rows(edition_root: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    manifest = _load_yaml(edition_root / "edition.yaml")
    skill_root = edition_root / manifest["skill"]["root"]
    support = _load_yaml(skill_root / "references/common/statement_support_inventory.yaml")
    ledger = skill_root / support["factor_audit"]["path"]
    with ledger.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        rows = list(reader)
    return {
        (row["statement_key"], row["factor"], row["value"]): row
        for row in rows
    }


def audit_version_delta(
    edition_8022_root: Path | str,
    edition_8041_root: Path | str,
    delta_path: Path | str,
) -> VersionDeltaReport:
    report = VersionDeltaReport()
    try:
        rows_22 = _factor_rows(Path(edition_8022_root).resolve())
        rows_41 = _factor_rows(Path(edition_8041_root).resolve())
        with Path(delta_path).open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != DELTA_COLUMNS:
                raise ValueError("version delta header mismatch")
            delta_rows = list(reader)
    except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        report.errors.append(str(exc))
        return report

    expected_keys = set(rows_22) | set(rows_41)
    seen: set[tuple[str, str, str]] = set()
    for line, row in enumerate(delta_rows, start=2):
        key = (row["statement_key"], row["factor"], row["value"])
        if key in seen:
            report.errors.append(f"version delta line {line}: duplicate key {key}")
            continue
        seen.add(key)
        if key not in expected_keys:
            report.errors.append(f"version delta line {line}: unexpected key {key}")
            continue
        if key not in rows_22:
            expected = "added"
        elif key not in rows_41:
            expected = "removed"
        elif key[0] in CHANGED_STATEMENT_SOURCES:
            expected = "changed"
        else:
            expected = "unchanged"
        disposition = row["disposition"]
        if disposition != expected:
            report.errors.append(
                f"version delta line {line}: {key} must be {expected}, got {disposition}"
            )
        else:
            setattr(report, disposition, getattr(report, disposition) + 1)
        if row["review_status"] != "static_reviewed":
            report.unreviewed += 1
            report.errors.append(f"version delta line {line}: review_status is not static_reviewed")
        if disposition in {"added", "changed", "removed"}:
            expected_locator = CHANGED_STATEMENT_SOURCES.get(key[0])
            if not expected_locator or row["official_locator"] != expected_locator:
                report.errors.append(f"version delta line {line}: official release-note locator mismatch")
        elif not row["official_locator"].startswith("https://dev.mysql.com/"):
            report.errors.append(f"version delta line {line}: unchanged row lacks official locator")
        if not row["notes"].strip():
            report.errors.append(f"version delta line {line}: notes must be nonempty")
    missing = expected_keys - seen
    if missing:
        report.errors.append(f"version delta is missing {len(missing)} factor/value rows")
    return report
