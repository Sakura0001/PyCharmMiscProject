"""Audit the TUC baseline and independent TUCX extension artifacts."""

from __future__ import annotations

import gzip
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from mysql_case_factory.type_upgrade_extension import P0_GAPS
from mysql_case_factory.type_upgrade_runner import _load_cases, verify_case_artifacts


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_manifest_artifacts(directory: Path, manifest: dict[str, Any]) -> None:
    required_profiles = {"copy", "inplace", "instant"}
    profiles = manifest.get("profiles", {})
    missing_profiles = sorted(required_profiles - set(profiles))
    if missing_profiles:
        raise ValueError(f"manifest is missing required profiles: {', '.join(missing_profiles)}")

    required_artifacts = {
        "cases.jsonl.gz",
        "copy_suite.sql.gz",
        "inplace_suite.sql.gz",
        "instant_suite.sql.gz",
        "coverage.tsv",
        "README.md",
    }
    artifacts = manifest.get("artifacts", {})
    missing_artifacts = sorted(required_artifacts - set(artifacts))
    if missing_artifacts:
        raise ValueError(f"manifest is missing required artifacts: {', '.join(missing_artifacts)}")

    for name, expected in artifacts.items():
        path = directory / name
        if not path.exists():
            raise ValueError(f"manifest artifact does not exist: {name}")
        payload = path.read_bytes()
        if len(payload) != expected.get("bytes"):
            raise ValueError(f"artifact integrity check failed: {name}")
        if sha256(payload).hexdigest() != expected.get("sha256"):
            raise ValueError(f"artifact integrity check failed: {name}")

    for profile in required_profiles:
        if profiles[profile].get("case_count") != manifest.get("case_count"):
            raise ValueError(f"profile case count does not match manifest: {profile}")


def _read_results(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def audit_extension(baseline_dir: Path, extension_dir: Path, report_dir: Path) -> dict[str, Any]:
    baseline_manifest = _read_json(baseline_dir / "manifest.json")
    extension_manifest = _read_json(extension_dir / "manifest.json")
    _verify_manifest_artifacts(baseline_dir, baseline_manifest)
    _verify_manifest_artifacts(extension_dir, extension_manifest)

    baseline_metadata = verify_case_artifacts(baseline_dir / "cases.jsonl.gz")
    extension_metadata = verify_case_artifacts(extension_dir / "cases.jsonl.gz")
    baseline_cases = _load_cases(baseline_dir / "cases.jsonl.gz")
    extension_cases = _load_cases(extension_dir / "cases.jsonl.gz")

    baseline_ids = set(baseline_cases)
    extension_ids = set(extension_cases)
    overlap = sorted(baseline_ids & extension_ids)

    gap_counts: dict[str, int] = {}
    for case in extension_cases.values():
        if case.gap_id is None:
            raise ValueError(f"extension case missing gap_id: {case.case_id}")
        gap_counts[case.gap_id] = gap_counts.get(case.gap_id, 0) + 1
    missing_gaps = sorted(set(P0_GAPS) - set(gap_counts))

    profile_counts = {
        profile: manifest["case_count"]
        for profile, manifest in extension_manifest["profiles"].items()
    }
    profile_counts_match = all(count == len(extension_cases) for count in profile_counts.values())

    results = _read_results(extension_dir / "local_results.jsonl")
    result_ids = [result["case_id"] for result in results]
    local_all_pass = (
        len(results) == len(extension_cases)
        and set(result_ids) == extension_ids
        and len(result_ids) == len(set(result_ids))
        and all(result["outcome"] == "PASS" for result in results)
    )

    query_cases = [case for case in extension_cases.values() if case.gap_id == "GAP-QUERY-ORACLE"]
    semantic_checks = {
        "explain_query_plans": sum(bool(case.query_plans) for case in query_cases),
        "ordered_by_id_checks": sum(
            any("GROUP_CONCAT" in statement and "ORDER BY id" in statement for statement in case.verify_sql)
            for case in query_cases
        ),
        "prefix_order_checks": sum(case.reason.endswith("prefix_order") for case in query_cases),
        "descending_order_checks": sum(case.reason.endswith("descending_order") for case in query_cases),
        "delete_no_action_clauses": sum(
            "ON DELETE NO ACTION" in " ".join(case.post_ddl_sql)
            for case in extension_cases.values()
        ),
        "update_no_action_clauses": sum(
            "ON UPDATE NO ACTION" in " ".join(case.post_ddl_sql)
            for case in extension_cases.values()
        ),
    }
    semantic_coverage_ok = all(count > 0 for count in semantic_checks.values())

    parent_link_ok = (
        extension_manifest.get("parent_batch_id") == baseline_manifest.get("batch_id")
        and all(case.parent_batch_id == baseline_manifest["batch_id"] for case in extension_cases.values())
    )
    forbidden_absent = bool(
        baseline_manifest.get("forbidden_types_absent")
        and extension_manifest.get("forbidden_types_absent")
    )

    passed = bool(
        not overlap
        and not missing_gaps
        and profile_counts_match
        and parent_link_ok
        and forbidden_absent
        and local_all_pass
        and semantic_coverage_ok
    )
    result = {
        "passed": passed,
        "baseline_batch_id": baseline_manifest["batch_id"],
        "extension_batch_id": extension_manifest["batch_id"],
        "extension_parent_batch_id": extension_manifest.get("parent_batch_id"),
        "baseline_case_count": len(baseline_cases),
        "extension_case_count": len(extension_cases),
        "case_id_overlap_count": len(overlap),
        "case_id_overlap": overlap,
        "p0_gap_count": len(gap_counts),
        "p0_gap_counts": gap_counts,
        "p0_missing_gaps": missing_gaps,
        "profile_counts": profile_counts,
        "profile_counts_match": profile_counts_match,
        "parent_link_ok": parent_link_ok,
        "forbidden_types_absent": forbidden_absent,
        "local_all_pass": local_all_pass,
        "semantic_checks": semantic_checks,
        "semantic_coverage_ok": semantic_coverage_ok,
        "local_result_count": len(results),
        "baseline_artifact_sha256": baseline_metadata["cases_artifact_sha256"],
        "extension_artifact_sha256": extension_metadata["cases_artifact_sha256"],
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    gap_lines = [
        "gap_id\tcase_count\tstatus",
        *(f"{gap}\t{gap_counts.get(gap, 0)}\t{'COVERED' if gap_counts.get(gap, 0) else 'MISSING'}" for gap in P0_GAPS),
    ]
    (report_dir / "coverage_gap_report.tsv").write_text("\n".join(gap_lines) + "\n", encoding="utf-8")

    summary = (
        "# Type-upgrade extension coverage audit\n\n"
        f"**Result:** {'PASS' if passed else 'FAIL'}\n\n"
        f"- Baseline batch: `{baseline_manifest['batch_id']}`\n"
        f"- Extension batch: `{extension_manifest['batch_id']}`\n"
        f"- Parent link: `{extension_manifest.get('parent_batch_id')}`\n"
        f"- Baseline case count: {len(baseline_cases)}\n"
        f"- Extension case count: {len(extension_cases)}\n"
        f"- P0 gaps covered: {len(gap_counts) - len(missing_gaps)}/{len(P0_GAPS)}\n"
        f"- Case ID overlap: {len(overlap)}\n"
        f"- Local COPY all PASS: {local_all_pass}\n"
        f"- Forbidden types absent: {forbidden_absent}\n"
    )
    (report_dir / "coverage_summary.md").write_text(summary, encoding="utf-8")
    return result
