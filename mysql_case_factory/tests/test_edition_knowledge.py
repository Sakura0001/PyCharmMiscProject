from __future__ import annotations

from pathlib import Path

from mysql_case_factory.knowledge_audit import audit_edition_knowledge


ROOT = Path(__file__).resolve().parents[1]


def test_8022_edition_has_closed_statement_factor_and_matrix_coverage() -> None:
    report = audit_edition_knowledge(ROOT / "editions" / "mysql_8_0_22")
    assert report.ok, report.errors
    assert report.statement_count == 112
    assert report.matrix_count == report.statement_count
    assert report.factor_pair_count > report.statement_count
    assert report.factor_value_count > report.factor_pair_count
    assert report.unreviewed_count == 0


def test_8041_edition_has_closed_statement_factor_and_matrix_coverage() -> None:
    report = audit_edition_knowledge(ROOT / "editions" / "mysql_8_0_41")
    assert report.ok, report.errors
    assert report.statement_count == 112
    assert report.matrix_count == report.statement_count
    assert report.factor_pair_count == 512
    assert report.factor_value_count == 1389
    assert report.unreviewed_count == 0


def test_edition_audit_rejects_missing_matrix(tmp_path: Path) -> None:
    edition = tmp_path / "edition"
    skill = edition / "skills" / "test-skill"
    (skill / "references" / "statements").mkdir(parents=True)
    (skill / "references" / "combinations").mkdir(parents=True)
    (edition / "edition.yaml").write_text(
        "schema_version: 1\nkind: mysql_case_factory_edition\n"
        "edition_id: mysql-community-8.0.22\ntarget_version: 8.0.22\n"
        "target_version_num: 80022\nreview_state: complete\n"
        "oracle: {engine: mysql-community-server, exact_patch: true}\n"
        "skill: {name: test-skill, root: skills/test-skill}\ninventories: []\n",
        encoding="utf-8",
    )
    report = audit_edition_knowledge(edition)
    assert report.ok is False
    assert any("statement_support_inventory.yaml" in error for error in report.errors)
