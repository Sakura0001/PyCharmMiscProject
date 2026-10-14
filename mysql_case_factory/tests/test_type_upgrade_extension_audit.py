from __future__ import annotations

import json
from pathlib import Path

from mysql_case_factory.type_upgrade_extension_audit import audit_extension


def test_extension_audit_links_baseline_and_covers_all_p0_gaps(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    baseline = root / "generated" / "type_upgrade_consistency"
    extension = root / "generated" / "type_upgrade_consistency_extension_v1"
    report_dir = tmp_path

    result = audit_extension(baseline, extension, report_dir)

    assert result["passed"] is True
    assert result["baseline_batch_id"] == "2026-10-13-type-upgrade-consistency"
    assert result["extension_batch_id"] == "2026-10-13-type-upgrade-consistency-extension-v1"
    assert result["baseline_case_count"] == 8270
    assert result["extension_case_count"] == 13721
    assert result["extension_parent_batch_id"] == "2026-10-13-type-upgrade-consistency"
    assert result["case_id_overlap_count"] == 0
    assert result["p0_gap_count"] == 5
    assert result["p0_missing_gaps"] == []
    assert result["forbidden_types_absent"] is True
    assert result["local_all_pass"] is True
    assert result["semantic_checks"]["explain_query_plans"] > 0
    assert result["semantic_checks"]["ordered_by_id_checks"] > 0
    assert result["semantic_checks"]["prefix_order_checks"] > 0
    assert result["semantic_checks"]["descending_order_checks"] > 0
    assert result["semantic_checks"]["delete_no_action_clauses"] > 0
    assert result["semantic_checks"]["update_no_action_clauses"] > 0

    gap_report = report_dir / "coverage_gap_report.tsv"
    summary = report_dir / "coverage_summary.md"
    assert gap_report.exists()
    assert summary.exists()
    assert "GAP-DATA-BEHAVIOR" in gap_report.read_text(encoding="utf-8")
    assert "Extension case count: 13721" in summary.read_text(encoding="utf-8")


def test_audit_rejects_missing_profiles_and_corrupt_suite_artifact(tmp_path: Path) -> None:
    import shutil

    import pytest

    root = Path(__file__).parents[1]
    baseline = root / "generated" / "type_upgrade_consistency"
    extension = root / "generated" / "type_upgrade_consistency_extension_v1"
    copied = tmp_path / "extension"
    shutil.copytree(extension, copied)

    manifest_path = copied / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["profiles"].pop("inplace")
    manifest["profiles"].pop("instant")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (copied / "copy_suite.sql.gz").write_bytes(b"corrupt")

    with pytest.raises(ValueError, match="artifact integrity check failed|missing required profiles"):
        audit_extension(baseline, copied, tmp_path / "report")


def test_docs_and_audit_claim_verified_query_access_path_coverage() -> None:
    doc = Path(__file__).parents[1] / "docs" / "type_upgrade_consistency_extension_v1.md"
    text = doc.read_text(encoding="utf-8")
    assert "result and access-path checks" in text
    assert "EXPLAIN FORMAT=JSON" in text
    assert "Ordered full-table/primary-key result comparison" in text
    assert "Descending-order" in text
    assert "Prefix-index ordering" in text
