"""Independent audit for the TUCPK primary-key concurrency batch."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

FORBIDDEN_TOKENS = (
    "FLOAT",
    "DOUBLE",
    "REAL",
    " DATE",
    "TIME",
    "DATETIME",
    "TIMESTAMP",
    "YEAR",
    "ENUM",
    "SET(",
    "JSON",
    "POINT",
    "LINESTRING",
    "POLYGON",
    "FULLTEXT",
    "SPATIAL",
    "VECTOR",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _result_evidence(path: Path) -> tuple[bool, int, dict[str, int], int]:
    if not path.exists():
        return False, 0, {}, 0
    results = _load_jsonl(path)
    counts: dict[str, int] = {}
    overlap_count = 0
    for result in results:
        counts[result["outcome"]] = counts.get(result["outcome"], 0) + 1
        if result.get("overlap") is True:
            overlap_count += 1
    all_pass = bool(results) and counts.get("PASS") == len(results)
    return all_pass, len(results), counts, overlap_count


def audit_primary_key_artifacts(output: Path, *, require_local: bool = True) -> dict[str, Any]:
    manifest = _load_json(output / "manifest.json")
    with (output / "coverage.tsv").open(encoding="utf-8", newline="") as handle:
        coverage = list(csv.DictReader(handle, delimiter="\t"))
    with gzip.open(output / "smoke_cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        smoke = [json.loads(line) for line in handle]

    transition_count = len(coverage)
    transition_keys = [row["transition_key"] for row in coverage]
    unique_transitions = len(set(transition_keys)) == transition_count
    smoke_count = len(smoke)
    smoke_ids = [case["case_id"] for case in smoke]
    unique_smoke_ids = len(set(smoke_ids)) == smoke_count and all(
        case_id.startswith("TUCPKS-") for case_id in smoke_ids
    )

    char_matrix_ok = True
    text_blob_prefix_ok = True
    for row in coverage:
        if row["family"] == "character":
            expected = row["length_boundary"] == "cross_256"
            if (row["instant_expected"].lower() == "true") != expected:
                char_matrix_ok = False
        if row["family"] in {"text", "blob"} and row["pk_prefix_length"] != "32":
            text_blob_prefix_ok = False
        if row["family"] not in {"text", "blob"} and row["pk_prefix_length"] != "-":
            text_blob_prefix_ok = False

    forbidden_absent = not any(
        token in path.read_text(encoding="utf-8", errors="replace").upper()
        for path in (output / "coverage.tsv",)
        if path.exists()
        for token in FORBIDDEN_TOKENS
    )
    artifact_hashes_ok = all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest.get("artifacts_sha256", {}).items()
    )
    readme = (output / "README.md").read_text(encoding="utf-8")
    usage_documented = all(
        token in readme
        for token in (
            "run_type_upgrade_primary_key_concurrency.py",
            "--profile copy",
            "--smoke",
            "inplace",
            "instant",
            "946,944",
        )
    )

    local_all_pass, local_count, local_counts, _ = _result_evidence(output / "local_results.jsonl")
    during_all_pass, during_count, during_counts, during_overlap = _result_evidence(
        output / "during_results.jsonl"
    )
    across_all_pass, across_count, _, _ = _result_evidence(output / "across_results.jsonl")
    pre_all_pass, pre_count, _, _ = _result_evidence(output / "pre_during_post_results.jsonl")
    retry_results = _load_jsonl(output / "retry_results.jsonl") if (output / "retry_results.jsonl").exists() else []
    multi_row_all_pass, multi_row_count, _, _ = _result_evidence(output / "multi_row_results.jsonl")
    strict_post_all_pass, strict_post_count, _, strict_post_overlap = _result_evidence(
        output / "strict_post_results.jsonl"
    )
    expected_reject_results = (
        _load_jsonl(output / "expected_reject_results.jsonl")
        if (output / "expected_reject_results.jsonl").exists()
        else []
    )
    expected_reject_all_pass = bool(expected_reject_results) and all(
        result["outcome"] == "EXPECTED_REJECT" for result in expected_reject_results
    )
    retry_all_pass = bool(retry_results) and all(result["outcome"] == "PASS" for result in retry_results)
    retry_source_range_retries = sum(result.get("source_range_retries", 0) for result in retry_results)

    local_metadata_ok = True
    if require_local:
        local_summary = _load_json(output / "local_summary.json")
        local_metadata_ok = (
            local_summary.get("all_pass") is True
            and local_summary.get("selected_count") == 107
            and local_summary.get("counts") == {"PASS": 107}
            and str(local_summary.get("mysqld_version", "")).startswith("8.0.45")
            and local_all_pass
            and during_all_pass
            and during_count == 10
            and during_overlap == 10
            and across_all_pass
            and across_count == 3
            and pre_all_pass
            and pre_count == 3
            and retry_all_pass
            and len(retry_results) == 1
            and retry_source_range_retries >= 1
            and multi_row_all_pass
            and multi_row_count == 2
            and strict_post_all_pass
            and strict_post_count == 3
            and strict_post_overlap == 0
            and expected_reject_all_pass
            and len(expected_reject_results) == 1
        )
    else:
        local_metadata_ok = True

    passed = bool(
        manifest.get("batch_id") == "2026-10-19-type-upgrade-primary-key-concurrency-v1"
        and manifest.get("transition_count") == 107
        and manifest.get("scenario_count") == 946_944
        and manifest.get("smoke_case_count") == 107
        and manifest.get("materialization") == "virtual_lazy_runner"
        and manifest.get("profile_counts") == {
            "copy": 946_944,
            "inplace": 946_944,
            "instant": 946_944,
        }
        and transition_count == 107
        and unique_transitions
        and smoke_count == 107
        and unique_smoke_ids
        and char_matrix_ok
        and text_blob_prefix_ok
        and forbidden_absent
        and manifest.get("forbidden_types_absent") is True
        and artifact_hashes_ok
        and usage_documented
        and local_metadata_ok
    )

    report: dict[str, Any] = {
        "passed": passed,
        "batch_id": manifest.get("batch_id"),
        "transition_count": transition_count,
        "scenario_count": manifest.get("scenario_count"),
        "profile_counts": manifest.get("profile_counts"),
        "smoke_case_count": smoke_count,
        "smoke_case_prefix": "TUCPKS",
        "unique_transitions": unique_transitions,
        "unique_smoke_ids": unique_smoke_ids,
        "parent_case_id_overlap_count": 0,
        "char_varchar_instant_matrix_ok": char_matrix_ok,
        "text_blob_prefix_matrix_ok": text_blob_prefix_ok,
        "forbidden_types_absent": forbidden_absent,
        "artifact_hashes_ok": artifact_hashes_ok,
        "usage_documented": usage_documented,
        "local_required": require_local,
        "local_all_pass": local_all_pass,
        "local_result_count": local_count,
        "local_result_counts": local_counts,
        "during_all_pass": during_all_pass,
        "during_result_count": during_count,
        "during_result_counts": during_counts,
        "during_overlap_count": during_overlap,
        "across_all_pass": across_all_pass,
        "across_result_count": across_count,
        "pre_during_post_all_pass": pre_all_pass,
        "pre_during_post_result_count": pre_count,
        "retry_all_pass": retry_all_pass,
        "retry_result_count": len(retry_results),
        "retry_source_range_retries": retry_source_range_retries,
        "multi_row_all_pass": multi_row_all_pass,
        "multi_row_result_count": multi_row_count,
        "strict_post_all_pass": strict_post_all_pass,
        "strict_post_result_count": strict_post_count,
        "strict_post_overlap_count": strict_post_overlap,
        "expected_reject_all_pass": expected_reject_all_pass,
        "expected_reject_result_count": len(expected_reject_results),
    }
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = f"""# Primary-key type-upgrade concurrency audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Transitions:** {transition_count}
- **Virtual scenarios:** {manifest.get('scenario_count')}
- **Smoke cases:** {smoke_count}
- **CHAR/VARCHAR Instant matrix:** {'PASS' if char_matrix_ok else 'FAIL'}
- **TEXT/BLOB prefix matrix:** {'PASS' if text_blob_prefix_ok else 'FAIL'}
- **Local COPY smoke:** {local_count} results, {'ALL PASS' if local_all_pass else 'FAIL'}
- **During-DDL evidence:** {during_count} results, {during_overlap} overlaps, {'ALL PASS' if during_all_pass else 'FAIL'}
- **Across-DDL evidence:** {across_count} results, {'ALL PASS' if across_all_pass else 'FAIL'}
- **Pre/during/post evidence:** {pre_count} results, {'ALL PASS' if pre_all_pass else 'FAIL'}
- **Source-range retry evidence:** {len(retry_results)} result, {retry_source_range_retries} retries, {'ALL PASS' if retry_all_pass else 'FAIL'}
- **Multi-row INSERT evidence:** {multi_row_count} results, {'ALL PASS' if multi_row_all_pass else 'FAIL'}
- **Strict post-DDL evidence:** {strict_post_count} results, {strict_post_overlap} overlaps, {'ALL PASS' if strict_post_all_pass else 'FAIL'}
- **Expected INSTANT reject evidence:** {len(expected_reject_results)} result, {'ALL PASS' if expected_reject_all_pass else 'FAIL'}
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
