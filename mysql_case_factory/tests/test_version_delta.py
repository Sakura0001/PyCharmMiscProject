from __future__ import annotations

from pathlib import Path

from mysql_case_factory.version_delta import audit_version_delta
from mysql_case_factory.editions import load_edition


ROOT = Path(__file__).resolve().parents[1]


def test_8041_delta_closes_the_8022_to_8041_factor_universe() -> None:
    report = audit_version_delta(
        ROOT / "editions" / "mysql_8_0_22",
        ROOT / "editions" / "mysql_8_0_41",
        ROOT / "editions" / "mysql_8_0_41" / "version_delta_from_8_0_22.tsv",
    )
    assert report.ok, report.errors
    assert report.added > 0
    assert report.changed > 0
    assert report.removed == 0
    assert report.unreviewed == 0
    edition = load_edition(
        ROOT / "editions" / "mysql_8_0_41",
        repository_root=ROOT,
        verify_files=True,
    )
    assert "version_delta" in {item.kind for item in edition.inventories}


def test_8041_skill_is_an_independent_snapshot() -> None:
    skill = ROOT / "editions" / "mysql_8_0_41" / "skills" / "mysql-8-0-41-sql-generation"
    for path in skill.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "editions/mysql_8_0_22" not in text
            assert "skills/mysql-8-0-22-sql-generation" not in text
