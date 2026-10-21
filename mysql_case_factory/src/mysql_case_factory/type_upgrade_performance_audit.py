from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CASE_COUNT = 7
EXPECTED_UPGRADE_COLUMN_COUNT = 31
EXPECTED_NOISE_COLUMN_COUNT = 4
EXPECTED_SCENARIOS = {
    "source_baseline",
    "all_copy",
    "all_inplace",
    "all_instant",
    "mixed_inplace_first",
    "mixed_instant_first",
    "reference",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_gzip(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_type_performance_artifacts(output: Path, *, require_local: bool = True) -> dict[str, Any]:
    manifest = _load_json(output / "manifest.json")
    cases = _load_jsonl_gzip(output / "cases.jsonl.gz")
    with (output / "coverage.tsv").open(encoding="utf-8", newline="") as handle:
        coverage = list(csv.DictReader(handle, delimiter="\t"))

    case_ids = [case["case_id"] for case in cases]
    scenarios = {case["scenario"] for case in cases}
    unique_case_ids = len(case_ids) == len(set(case_ids)) == EXPECTED_CASE_COUNT
    scenario_ok = scenarios == EXPECTED_SCENARIOS
    coverage_ok = len(coverage) == EXPECTED_UPGRADE_COLUMN_COUNT
    type_families = {row["family"] for row in coverage}
    type_families_ok = type_families == {
        "integer", "decimal", "bit", "character", "binary", "text", "blob"
    }

    artifact_hashes_ok = all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest.get("artifacts_sha256", {}).items()
    )

    readme = (output / "README.md").read_text(encoding="utf-8")
    usage_documented = all(
        token in readme
        for token in (
            "run_type_upgrade_performance.py",
            "--all",
            "--external",
            "--password-env",
        )
    )

    local_results = _load_jsonl(output / "performance_results.jsonl")
    local_summary = _load_json(output / "performance_summary.json") if (output / "performance_summary.json").exists() else {}
    local_result_count = len(local_results)
    local_pass_count = sum(1 for result in local_results if result.get("classification") == "PASS")
    local_all_pass = bool(local_results) and local_pass_count == local_result_count
    local_metadata_ok = True
    if require_local:
        local_metadata_ok = (
            local_summary.get("all_pass") is True
            and local_summary.get("selected_count") == 3
            and local_result_count == 3
            and local_pass_count == 3
            and str(local_summary.get("mysqld_version", "")).startswith("8.0.45")
            and all(result.get("query_seconds") is not None for result in local_results)
        )

    passed = bool(
        manifest.get("batch_id") == "2026-10-21-type-upgrade-performance-v1"
        and manifest.get("batch_kind") == "type_upgrade_performance"
        and manifest.get("case_count") == EXPECTED_CASE_COUNT
        and manifest.get("scenario_count") == EXPECTED_CASE_COUNT
        and manifest.get("upgrade_column_count") == EXPECTED_UPGRADE_COLUMN_COUNT
        and manifest.get("noise_column_count") == EXPECTED_NOISE_COLUMN_COUNT
        and manifest.get("materialization") == "virtual_runner"
        and unique_case_ids
        and scenario_ok
        and coverage_ok
        and type_families_ok
        and artifact_hashes_ok
        and usage_documented
        and local_metadata_ok
    )

    report: dict[str, Any] = {
        "passed": passed,
        "batch_id": manifest.get("batch_id"),
        "batch_kind": manifest.get("batch_kind"),
        "case_count": len(cases),
        "scenario_count": len(scenarios),
        "upgrade_column_count": manifest.get("upgrade_column_count"),
        "noise_column_count": manifest.get("noise_column_count"),
        "unique_case_ids": unique_case_ids,
        "scenario_ok": scenario_ok,
        "coverage_ok": coverage_ok,
        "type_families_ok": type_families_ok,
        "artifact_hashes_ok": artifact_hashes_ok,
        "usage_documented": usage_documented,
        "local_required": require_local,
        "local_result_count": local_result_count,
        "local_pass_count": local_pass_count,
        "local_all_pass": local_all_pass,
        "local_metadata_ok": local_metadata_ok,
        "mysqld_version": local_summary.get("mysqld_version"),
        "rows": local_summary.get("rows"),
    }
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = f"""# Type-upgrade performance audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Scenarios:** {len(scenarios)}
- **Upgrade columns:** {manifest.get('upgrade_column_count')}
- **Noise columns:** {manifest.get('noise_column_count')}
- **Local results:** {local_pass_count}/{local_result_count} PASS
- **Rows:** {local_summary.get('rows', '-')}
- **MySQL:** `{local_summary.get('mysqld_version', '-')}`
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
