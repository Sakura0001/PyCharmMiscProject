from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CASE_COUNT = 568
EXPECTED_TRANSITION_COUNT = 71
EXPECTED_PROFILE_COUNTS = {"inplace": 284, "instant": 284}
EXPECTED_FAMILY_COUNTS = {
    "integer": 176,
    "character": 112,
    "binary": 96,
    "decimal": 80,
    "bit": 104,
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_gzip(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _load_text_gzip(path: Path) -> str:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return handle.read()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_fk_type_expansion_artifacts(output: Path, *, require_local: bool = True) -> dict[str, Any]:
    manifest = _load_json(output / "manifest.json")
    cases = _load_jsonl_gzip(output / "cases.jsonl.gz")
    coverage_rows = list(csv.DictReader((output / "coverage.tsv").open(encoding="utf-8", newline=""), delimiter="\t"))

    case_ids = [case["case_id"] for case in cases]
    unique_case_ids = len(case_ids) == len(set(case_ids)) == EXPECTED_CASE_COUNT
    case_prefix_ok = all(case_id.startswith("TUCFK-") for case_id in case_ids)
    families = [case["family"] for case in cases]
    family_counts = {family: families.count(family) for family in set(families)}
    family_counts_ok = family_counts == EXPECTED_FAMILY_COUNTS

    transition_keys = {
        (case["family"], case["source_type"], case["target_type"]) for case in cases
    }
    transitions_ok = len(transition_keys) == EXPECTED_TRANSITION_COUNT
    coverage_ok = len(coverage_rows) == EXPECTED_TRANSITION_COUNT and {
        (row["family"], row["source_type"], row["target_type"]) for row in coverage_rows
    } == transition_keys

    expected_output_ok = True
    for profile, expected_count in EXPECTED_PROFILE_COUNTS.items():
        path = output / f"expected_output_{profile}.tsv"
        lines = path.read_text(encoding="utf-8").splitlines()
        expected_output_ok = expected_output_ok and len(lines) == expected_count
        expected_output_ok = expected_output_ok and all(line.split("\t")[-1] == "PASS" for line in lines)

    sql_oracle_ok = True
    for profile in EXPECTED_PROFILE_COUNTS:
        sql = _load_text_gzip(output / f"{profile}_suite.sql.gz")
        sql_oracle_ok = sql_oracle_ok and all(
            token in sql
            for token in (
                "INSERT INTO",
                "UPDATE",
                "DELETE FROM",
                "LEFT JOIN",
                "information_schema.COLUMNS",
                "information_schema.KEY_COLUMN_USAGE",
                "DROP TABLE IF EXISTS",
            )
        )

    artifact_hashes_ok = all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest.get("artifacts_sha256", {}).items()
    )

    readme = (output / "README.md").read_text(encoding="utf-8")
    usage_documented = all(
        token in readme
        for token in (
            "inplace_suite.sql.gz",
            "instant_suite.sql.gz",
            "expected_output_inplace.tsv",
            "expected_output_instant.tsv",
            "--force",
            "diff -u",
        )
    )

    local_metadata_ok = True
    if require_local:
        local_summary_path = output / "local_summary.json"
        local_metadata_ok = local_summary_path.exists() and _load_json(local_summary_path).get("all_pass") is True

    passed = bool(
        manifest.get("batch_id") == "2026-10-20-fk-type-expansion-consistency-v1"
        and manifest.get("batch_kind") == "fk_type_expansion_consistency"
        and manifest.get("case_count") == EXPECTED_CASE_COUNT
        and manifest.get("transition_count") == EXPECTED_TRANSITION_COUNT
        and manifest.get("profile_counts") == EXPECTED_PROFILE_COUNTS
        and manifest.get("materialization") == "sql_suite"
        and unique_case_ids
        and case_prefix_ok
        and family_counts_ok
        and transitions_ok
        and coverage_ok
        and expected_output_ok
        and sql_oracle_ok
        and artifact_hashes_ok
        and usage_documented
        and local_metadata_ok
    )

    report: dict[str, Any] = {
        "passed": passed,
        "batch_id": manifest.get("batch_id"),
        "batch_kind": manifest.get("batch_kind"),
        "case_count": len(cases),
        "transition_count": len(transition_keys),
        "profile_counts": manifest.get("profile_counts"),
        "family_counts": family_counts,
        "unique_case_ids": unique_case_ids,
        "case_prefix_ok": case_prefix_ok,
        "coverage_ok": coverage_ok,
        "expected_output_ok": expected_output_ok,
        "sql_oracle_ok": sql_oracle_ok,
        "artifact_hashes_ok": artifact_hashes_ok,
        "usage_documented": usage_documented,
        "local_required": require_local,
        "local_metadata_ok": local_metadata_ok,
    }
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = f"""# FK type-expansion audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Cases:** {len(cases)}
- **Transitions:** {len(transition_keys)}
- **Profiles:** `inplace`, `instant`
- **Family counts:** {family_counts}
- **Expected output:** {'PASS' if expected_output_ok else 'FAIL'}
- **SQL oracle:** {'PASS' if sql_oracle_ok else 'FAIL'}
- **Artifact hashes:** {'PASS' if artifact_hashes_ok else 'FAIL'}
- **Usage documentation:** {'PASS' if usage_documented else 'FAIL'}
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
