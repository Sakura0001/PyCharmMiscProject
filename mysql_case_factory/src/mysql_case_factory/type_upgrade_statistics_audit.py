"""Audit the TUCS statistics and chained-upgrade batch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mysql_case_factory.type_upgrade_extension_audit import _verify_manifest_artifacts
from mysql_case_factory.type_upgrade_statistics import STATS_GAPS
from mysql_case_factory.type_upgrade_runner import _load_cases, verify_case_artifacts


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_results(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def audit_statistics(parent_dir: Path, statistics_dir: Path, report_dir: Path) -> dict[str, Any]:
    parent_manifest = _read_json(parent_dir / "manifest.json")
    statistics_manifest = _read_json(statistics_dir / "manifest.json")
    _verify_manifest_artifacts(parent_dir, parent_manifest)
    _verify_manifest_artifacts(statistics_dir, statistics_manifest)

    parent_metadata = verify_case_artifacts(parent_dir / "cases.jsonl.gz")
    statistics_metadata = verify_case_artifacts(statistics_dir / "cases.jsonl.gz")
    parent_cases = _load_cases(parent_dir / "cases.jsonl.gz")
    statistics_cases = _load_cases(statistics_dir / "cases.jsonl.gz")
    parent_ids = set(parent_cases)
    statistics_ids = set(statistics_cases)
    overlap = sorted(parent_ids & statistics_ids)

    profile_counts = {
        profile: manifest["case_count"]
        for profile, manifest in statistics_manifest["profiles"].items()
    }
    profile_counts_match = all(count == len(statistics_cases) for count in profile_counts.values())

    results = _read_results(statistics_dir / "local_results.jsonl")
    result_ids = [result["case_id"] for result in results]
    local_all_pass = (
        len(results) == len(statistics_cases)
        and set(result_ids) == statistics_ids
        and len(result_ids) == len(set(result_ids))
        and all(result["outcome"] == "PASS" for result in results)
    )
    result_metadata_ok = all(
        result.get("batch_id") == statistics_manifest.get("batch_id")
        and result.get("batch_kind") == statistics_manifest.get("batch_kind")
        and result.get("profile") == "copy"
        for result in results
    )
    summary = _read_json(statistics_dir / "local_summary.json")
    summary_consistent = (
        summary.get("batch_id") == statistics_manifest.get("batch_id")
        and summary.get("batch_kind") == statistics_manifest.get("batch_kind")
        and summary.get("selected_count") == len(statistics_cases)
        and summary.get("executed_count") == len(results)
        and summary.get("counts", {}).get("PASS") == len(results)
        and summary.get("all_pass") is local_all_pass
        and summary.get("stopped_early") is False
    )

    stats_sql_by_case = [
        case.stats_pre_analyze_sql + case.stats_post_analyze_sql
        for case in statistics_cases.values()
    ]
    semantic_checks = {
        "persistent_table_stats": sum(
            any("mysql.innodb_table_stats" in statement for statement in statements)
            for statements in stats_sql_by_case
        ),
        "persistent_index_stats": sum(
            any("mysql.innodb_index_stats" in statement for statement in statements)
            for statements in stats_sql_by_case
        ),
        "information_schema_statistics": sum(
            any("information_schema.STATISTICS" in statement for statement in statements)
            for statements in stats_sql_by_case
        ),
        "information_schema_tables": sum(
            any("information_schema.TABLES" in statement for statement in statements)
            for statements in stats_sql_by_case
        ),
        "partition_stats": sum(case.table_form != "ordinary" for case in statistics_cases.values()),
        "explain_plans": sum(bool(case.query_plans) for case in statistics_cases.values()),
        "chained_upgrade": sum(bool(case.pre_ddl_sql) for case in statistics_cases.values()),
        "duplicate_modify_reject": sum(
            case.expected_outcome == "reject" and case.ddl_sql.count("MODIFY target_col") == 2
            for case in statistics_cases.values()
        ),
    }
    semantic_coverage_ok = all(count > 0 for count in semantic_checks.values())
    gap_counts = {
        gap: sum(case.gap_id == gap for case in statistics_cases.values())
        for gap in STATS_GAPS
    }
    parent_link_ok = (
        statistics_manifest.get("parent_batch_id") == parent_manifest.get("batch_id")
        and all(
            case.parent_batch_id == parent_manifest["batch_id"]
            for case in statistics_cases.values()
        )
    )
    forbidden_absent = bool(
        parent_manifest.get("forbidden_types_absent")
        and statistics_manifest.get("forbidden_types_absent")
    )
    passed = bool(
        not overlap
        and profile_counts_match
        and parent_link_ok
        and forbidden_absent
        and local_all_pass
        and result_metadata_ok
        and summary_consistent
        and semantic_coverage_ok
    )

    result = {
        "passed": passed,
        "parent_batch_id": parent_manifest["batch_id"],
        "statistics_batch_id": statistics_manifest["batch_id"],
        "parent_case_count": len(parent_cases),
        "statistics_case_count": len(statistics_cases),
        "case_id_overlap_count": len(overlap),
        "case_id_overlap": overlap,
        "profile_counts": profile_counts,
        "profile_counts_match": profile_counts_match,
        "parent_link_ok": parent_link_ok,
        "forbidden_types_absent": forbidden_absent,
        "local_all_pass": local_all_pass,
        "result_metadata_ok": result_metadata_ok,
        "summary_consistent": summary_consistent,
        "summary_batch_id": summary.get("batch_id"),
        "summary_executed_count": summary.get("executed_count"),
        "local_result_count": len(results),
        "semantic_checks": semantic_checks,
        "semantic_coverage_ok": semantic_coverage_ok,
        "gap_counts": gap_counts,
        "parent_artifact_sha256": parent_metadata["cases_artifact_sha256"],
        "statistics_artifact_sha256": statistics_metadata["cases_artifact_sha256"],
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    gap_lines = [
        "factor_type\tfactor_value\tcase_count\tstatus",
        *(f"gap_id\t{key}\t{value}\t{'COVERED' if value else 'MISSING'}" for key, value in gap_counts.items()),
        *(f"semantic_check\t{key}\t{value}\t{'COVERED' if value else 'MISSING'}" for key, value in semantic_checks.items()),
    ]
    (report_dir / "coverage_gap_report.tsv").write_text("\n".join(gap_lines) + "\n", encoding="utf-8")
    summary = (
        "# Type-upgrade statistics audit\n\n"
        f"**Result:** {'PASS' if passed else 'FAIL'}\n\n"
        f"- Parent batch: `{parent_manifest['batch_id']}`\n"
        f"- Statistics batch: `{statistics_manifest['batch_id']}`\n"
        f"- Parent case count: {len(parent_cases)}\n"
        f"- Statistics case count: {len(statistics_cases)}\n"
        f"- Case ID overlap: {len(overlap)}\n"
        f"- Local COPY all PASS: {local_all_pass}\n"
        f"- Semantic coverage: {sum(value > 0 for value in semantic_checks.values())}/{len(semantic_checks)}\n"
    )
    (report_dir / "coverage_summary.md").write_text(summary, encoding="utf-8")
    return result
