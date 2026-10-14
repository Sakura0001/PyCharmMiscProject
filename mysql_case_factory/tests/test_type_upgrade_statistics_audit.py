from __future__ import annotations

import json
from pathlib import Path

from mysql_case_factory.type_upgrade_statistics_audit import audit_statistics


def test_statistics_audit_covers_artifacts_profiles_and_semantics(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    baseline = root / "generated" / "type_upgrade_consistency_extension_v1"
    statistics = root / "generated" / "type_upgrade_statistics_v1"

    result = audit_statistics(baseline, statistics, tmp_path)

    assert result["passed"] is True
    assert result["parent_batch_id"] == "2026-10-13-type-upgrade-consistency-extension-v1"
    assert result["statistics_batch_id"] == "2026-10-14-type-upgrade-statistics-and-chain-v1"
    assert result["parent_case_count"] == 13721
    assert result["statistics_case_count"] == 47
    assert result["case_id_overlap_count"] == 0
    assert result["profile_counts"] == {"copy": 47, "inplace": 47, "instant": 47}
    assert result["local_all_pass"] is True
    assert result["semantic_checks"]["persistent_table_stats"] > 0
    assert result["semantic_checks"]["persistent_index_stats"] > 0
    assert result["semantic_checks"]["information_schema_statistics"] > 0
    assert result["semantic_checks"]["information_schema_tables"] > 0
    assert result["semantic_checks"]["partition_stats"] > 0
    assert result["semantic_checks"]["explain_plans"] > 0
    assert result["semantic_checks"]["chained_upgrade"] > 0
    assert result["semantic_checks"]["duplicate_modify_reject"] > 0

    gap_report = tmp_path / "coverage_gap_report.tsv"
    summary = tmp_path / "coverage_summary.md"
    assert gap_report.exists()
    assert summary.exists()
    assert "GAP-STATS-TABLE" in gap_report.read_text(encoding="utf-8")
    assert "Statistics case count: 47" in summary.read_text(encoding="utf-8")


def test_statistics_audit_validates_result_metadata_and_summary(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    parent = root / "generated" / "type_upgrade_consistency_extension_v1"
    statistics = root / "generated" / "type_upgrade_statistics_v1"

    result = audit_statistics(parent, statistics, tmp_path)

    assert result["result_metadata_ok"] is True
    assert result["summary_consistent"] is True
    assert result["summary_batch_id"] == "2026-10-14-type-upgrade-statistics-and-chain-v1"
    assert result["summary_executed_count"] == 47
