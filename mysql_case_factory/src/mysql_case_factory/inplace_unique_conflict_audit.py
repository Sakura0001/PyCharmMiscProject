from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from mysql_case_factory.inplace_unique_conflict import inplace_unique_operations

FORBIDDEN_DDL_TOKENS = ("MODIFY", "CHANGE")
EXPECTED_OPERATION_COUNT = 12
EXPECTED_SCENARIO_COUNT = 2_304
EXPECTED_SMOKE_COUNT = 12


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _result_evidence(path: Path) -> tuple[bool, int, dict[str, int], int, int]:
    results = _load_jsonl(path)
    counts: dict[str, int] = {}
    overlap_count = 0
    conflict_count = 0
    for result in results:
        classification = result.get("classification", result.get("outcome"))
        counts[classification] = counts.get(classification, 0) + 1
        if result.get("overlap") is True:
            overlap_count += 1
        if result.get("duplicate_conflicts", 0) >= 1:
            conflict_count += 1
    all_pass = bool(results) and counts.get("PASS") == len(results)
    return all_pass, len(results), counts, overlap_count, conflict_count


def audit_inplace_unique_artifacts(output: Path, *, require_local: bool = True) -> dict[str, Any]:
    manifest = _load_json(output / "manifest.json")
    with (output / "coverage.tsv").open(encoding="utf-8", newline="") as handle:
        coverage = list(csv.DictReader(handle, delimiter="\t"))
    with gzip.open(output / "smoke_cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        smoke = [json.loads(line) for line in handle]

    operation_count = len(coverage)
    operation_ids = [row["operation_id"] for row in coverage]
    unique_operations = len(set(operation_ids)) == operation_count == EXPECTED_OPERATION_COUNT
    scenario_count = int(manifest.get("scenario_count", 0))
    smoke_count = len(smoke)
    smoke_ids = [case["case_id"] for case in smoke]
    unique_smoke_ids = len(set(smoke_ids)) == smoke_count == EXPECTED_SMOKE_COUNT
    profile_counts = manifest.get("profile_counts", {})

    ddl_sql_ok = True
    forbidden_tokens_absent = True
    for operation in inplace_unique_operations():
        ddl_sql = operation.ddl_sql
        if "ALGORITHM=INPLACE" not in ddl_sql or "LOCK=NONE" not in ddl_sql:
            ddl_sql_ok = False
        if any(token in ddl_sql.upper() for token in FORBIDDEN_DDL_TOKENS):
            forbidden_tokens_absent = False

    artifact_hashes_ok = all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest.get("artifacts_sha256", {}).items()
    )
    usage_documented = all(
        token in (output / "README.md").read_text(encoding="utf-8")
        for token in (
            "run_inplace_unique_conflict.py",
            "--profile copy",
            "--profile inplace",
            "--profile instant",
            "--smoke",
            "--all",
            "2,304",
        )
    )

    local_all_pass, local_count, local_counts, local_overlap, local_conflicts = _result_evidence(
        output / "local_results.jsonl"
    )
    local_summary = _load_json(output / "local_summary.json") if (output / "local_summary.json").exists() else {}
    local_metadata_ok = True
    if require_local:
        local_metadata_ok = (
            local_summary.get("all_pass") is True
            and local_summary.get("profile") == "copy"
            and local_summary.get("selected_count") == EXPECTED_SMOKE_COUNT
            and local_count == EXPECTED_SMOKE_COUNT
            and local_all_pass
            and local_overlap == EXPECTED_SMOKE_COUNT
            and local_conflicts == EXPECTED_SMOKE_COUNT
            and str(local_summary.get("mysqld_version", "")).startswith("8.0.45")
        )

    passed = bool(
        manifest.get("batch_id") == "2026-10-20-inplace-ddl-unique-conflict-v1"
        and manifest.get("batch_kind") == "inplace_unique_conflict_extension"
        and manifest.get("case_id_prefix") == "TUCUI"
        and manifest.get("database") == "qa_inplace_unique_conflict"
        and manifest.get("materialization") == "virtual_lazy_runner"
        and manifest.get("forbidden_types_absent") is True
        and scenario_count == EXPECTED_SCENARIO_COUNT
        and profile_counts == {"copy": EXPECTED_SCENARIO_COUNT, "inplace": EXPECTED_SCENARIO_COUNT, "instant": EXPECTED_SCENARIO_COUNT}
        and unique_operations
        and unique_smoke_ids
        and ddl_sql_ok
        and forbidden_tokens_absent
        and artifact_hashes_ok
        and usage_documented
        and local_metadata_ok
    )

    report: dict[str, Any] = {
        "passed": passed,
        "batch_id": manifest.get("batch_id"),
        "batch_kind": manifest.get("batch_kind"),
        "operation_count": operation_count,
        "scenario_count": scenario_count,
        "profile_counts": profile_counts,
        "smoke_case_count": smoke_count,
        "unique_operations": unique_operations,
        "unique_smoke_ids": unique_smoke_ids,
        "ddl_sql_ok": ddl_sql_ok,
        "forbidden_tokens_absent": forbidden_tokens_absent,
        "artifact_hashes_ok": artifact_hashes_ok,
        "usage_documented": usage_documented,
        "local_required": require_local,
        "local_all_pass": local_all_pass,
        "local_result_count": local_count,
        "local_result_counts": local_counts,
        "local_overlap_count": local_overlap,
        "local_conflict_count": local_conflicts,
        "local_profile": local_summary.get("profile"),
        "mysqld_version": local_summary.get("mysqld_version"),
    }
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = f"""# INPLACE DDL unique-conflict audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Operations:** {operation_count}
- **Virtual scenarios:** {scenario_count}
- **Smoke cases:** {smoke_count}
- **Canonical DDL:** {'PASS' if ddl_sql_ok else 'FAIL'}
- **Forbidden MODIFY/CHANGE:** {'ABSENT' if forbidden_tokens_absent else 'PRESENT'}
- **Local COPY smoke:** {local_count} results, {'ALL PASS' if local_all_pass else 'FAIL'}
- **True DDL/DML overlap:** {local_overlap}/{local_count}
- **Duplicate-conflict evidence:** {local_conflicts}/{local_count}
- **MySQL:** `{local_summary.get('mysqld_version', '-')}`
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
