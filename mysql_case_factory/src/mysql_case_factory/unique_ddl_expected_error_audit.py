from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CASE_COUNT = 192
EXPECTED_SMOKE_COUNT = 6
EXPECTED_DDL_FORMS = 4
EXPECTED_SHAPES = 6
EXPECTED_DML_TYPES = 8
EXPECTED_DUPLICATE_ERROR_CODES = {1062, 1859}


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


def audit_unique_ddl_error_artifacts(output: Path, *, require_local: bool = True) -> dict[str, Any]:
    manifest = _load_json(output / "manifest.json")
    cases = _load_jsonl_gzip(output / "cases.jsonl.gz")
    smoke = _load_jsonl_gzip(output / "smoke_cases.jsonl.gz")
    with (output / "coverage.tsv").open(encoding="utf-8", newline="") as handle:
        coverage = list(csv.DictReader(handle, delimiter="\t"))

    case_ids = [case["case_id"] for case in cases]
    unique_case_ids = len(case_ids) == len(set(case_ids)) == EXPECTED_CASE_COUNT
    prefix_ok = all(case_id.startswith("TUCUD-") for case_id in case_ids)
    ddl_forms = {case["ddl_form"] for case in cases}
    shapes = {case["shape"] for case in cases}
    dml_types = {case["dml_type"] for case in cases}
    matrix_ok = (
        len(ddl_forms) == EXPECTED_DDL_FORMS
        and len(shapes) == EXPECTED_SHAPES
        and len(dml_types) == EXPECTED_DML_TYPES
        and len(coverage) == EXPECTED_CASE_COUNT
    )
    expected_codes_ok = all(
        case.get("expected_error_codes") == [1062, 1859] for case in cases
    )
    smoke_ok = len(smoke) == EXPECTED_SMOKE_COUNT and {
        case["shape"] for case in smoke
    } == shapes

    artifact_hashes_ok = all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest.get("artifacts_sha256", {}).items()
    )

    readme = (output / "README.md").read_text(encoding="utf-8")
    usage_documented = all(
        token in readme
        for token in (
            "run_unique_ddl_expected_error.py",
            "--all",
            "--smoke",
            "--rows",
            "NO_OVERLAP",
        )
    )

    local_results = _load_jsonl(output / "local_results.jsonl")
    local_summary = _load_json(output / "local_summary.json") if (output / "local_summary.json").exists() else {}
    local_result_count = len(local_results)
    local_pass_count = sum(1 for result in local_results if result.get("classification") == "PASS")
    local_overlap_count = sum(1 for result in local_results if result.get("overlap") is True)
    local_duplicate_error_count = sum(
        1
        for result in local_results
        if result.get("ddl_error_code") in EXPECTED_DUPLICATE_ERROR_CODES
    )
    local_all_pass = bool(local_results) and local_pass_count == local_result_count
    local_metadata_ok = True
    if require_local:
        local_metadata_ok = (
            local_summary.get("all_pass") is True
            and local_summary.get("selected_count") == EXPECTED_CASE_COUNT
            and local_result_count == EXPECTED_CASE_COUNT
            and local_pass_count == EXPECTED_CASE_COUNT
            and local_overlap_count == EXPECTED_CASE_COUNT
            and local_duplicate_error_count == EXPECTED_CASE_COUNT
            and str(local_summary.get("mysqld_version", "")).startswith("8.0.45")
            and local_summary.get("rows_per_shape") == manifest.get("rows_per_shape")
        )

    passed = bool(
        manifest.get("batch_id") == "2026-10-20-unique-ddl-expected-error-v1"
        and manifest.get("batch_kind") == "unique_ddl_expected_error"
        and manifest.get("case_count") == EXPECTED_CASE_COUNT
        and manifest.get("smoke_case_count") == EXPECTED_SMOKE_COUNT
        and manifest.get("materialization") == "virtual_runner"
        and manifest.get("expected_error_codes") == [1062, 1859]
        and unique_case_ids
        and prefix_ok
        and matrix_ok
        and expected_codes_ok
        and smoke_ok
        and artifact_hashes_ok
        and usage_documented
        and local_metadata_ok
    )

    report: dict[str, Any] = {
        "passed": passed,
        "batch_id": manifest.get("batch_id"),
        "batch_kind": manifest.get("batch_kind"),
        "case_count": len(cases),
        "smoke_case_count": len(smoke),
        "ddl_form_count": len(ddl_forms),
        "shape_count": len(shapes),
        "dml_type_count": len(dml_types),
        "unique_case_ids": unique_case_ids,
        "case_prefix_ok": prefix_ok,
        "matrix_ok": matrix_ok,
        "expected_codes_ok": expected_codes_ok,
        "smoke_ok": smoke_ok,
        "artifact_hashes_ok": artifact_hashes_ok,
        "usage_documented": usage_documented,
        "local_required": require_local,
        "local_result_count": local_result_count,
        "local_pass_count": local_pass_count,
        "local_overlap_count": local_overlap_count,
        "local_duplicate_error_count": local_duplicate_error_count,
        "local_all_pass": local_all_pass,
        "local_metadata_ok": local_metadata_ok,
        "mysqld_version": local_summary.get("mysqld_version"),
        "rows_per_shape": manifest.get("rows_per_shape"),
    }
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = f"""# Unique-DDL expected-error audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Cases:** {len(cases)}
- **Smoke cases:** {len(smoke)}
- **DDL forms:** {len(ddl_forms)}
- **Index shapes:** {len(shapes)}
- **DML types:** {len(dml_types)}
- **Expected duplicate errors:** 1062 or 1859
- **Local results:** {local_pass_count}/{local_result_count} PASS
- **True overlaps:** {local_overlap_count}/{local_result_count}
- **MySQL:** `{local_summary.get('mysqld_version', '-')}`
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
