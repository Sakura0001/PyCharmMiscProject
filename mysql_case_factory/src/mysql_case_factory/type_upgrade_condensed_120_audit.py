from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CASE_COUNT = 120
EXPECTED_SQL_COUNT = 120
EXPECTED_OUTPUT_LINES = 240
EXPECTED_ALGORITHMS = {"INPLACE", "INSTANT"}
EXPECTED_CATEGORY_COUNTS = {
    "integer": 16,
    "decimal": 10,
    "bit": 10,
    "character": 12,
    "binary": 12,
    "text_blob": 8,
    "zero_length": 10,
    "auto_increment": 6,
    "foreign_key": 8,
    "dependency": 8,
    "table_form": 10,
    "chain": 1,
    "multi_column": 4,
    "statistics": 4,
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_gzip(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_condensed_120_artifacts(output: Path, *, require_local: bool = True) -> dict[str, Any]:
    manifest = _load_json(output / "manifest.json")
    with (output / "coverage.tsv").open(encoding="utf-8", newline="") as handle:
        coverage = list(csv.DictReader(handle, delimiter="\t"))

    sql_dir = output / "sql"
    sql_files = sorted(sql_dir.glob("TUCR-*.sql")) if sql_dir.exists() else []
    case_ids = [row["case_id"] for row in coverage]
    unique_case_ids = len(case_ids) == len(set(case_ids)) == EXPECTED_CASE_COUNT
    sql_count_ok = len(sql_files) == EXPECTED_SQL_COUNT
    sql_case_ids = [path.stem for path in sql_files]
    sql_case_ids_ok = sql_case_ids == case_ids

    expected_lines = (output / "expected_output.tsv").read_text(encoding="utf-8").splitlines()
    expected_output_ok = len(expected_lines) == EXPECTED_OUTPUT_LINES
    expected_output_ok = expected_output_ok and all(line.split("\t")[-1] == "PASS" for line in expected_lines)
    expected_algorithms_ok = all(
        line.split("\t")[1] in EXPECTED_ALGORITHMS for line in expected_lines
    )

    sql_contract_ok = all(
        "ALGORITHM=INPLACE" in path.read_text(encoding="utf-8")
        and "ALGORITHM=INSTANT" in path.read_text(encoding="utf-8")
        and "SET SESSION" not in path.read_text(encoding="utf-8")
        and path.read_text(encoding="utf-8").count("-- INPLACE stable result") == 1
        and path.read_text(encoding="utf-8").count("-- INSTANT stable result") == 1
        for path in sql_files
    )

    artifact_hashes_ok = all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest.get("artifacts_sha256", {}).items()
    )

    readme = (output / "README.md").read_text(encoding="utf-8")
    usage_documented = all(
        token in readme
        for token in (
            "--force",
            "expected_output.tsv",
            "TUCR-000001.sql",
            "INPLACE",
            "INSTANT",
        )
    )

    local_copy_summary = (
        _load_json(output / "local_copy_summary.json")
        if (output / "local_copy_summary.json").exists()
        else {}
    )
    local_copy_lines = (
        (output / "local_copy_results.tsv").read_text(encoding="utf-8").splitlines()
        if (output / "local_copy_results.tsv").exists()
        else []
    )
    local_copy_pass_count = sum(line.split("\t")[-1] == "PASS" for line in local_copy_lines)
    local_metadata_ok = True
    if require_local:
        local_metadata_ok = (
            local_copy_summary.get("all_pass") is True
            and local_copy_summary.get("result_line_count") == 224
            and local_copy_summary.get("pass_count") == 224
            and len(local_copy_lines) == 224
            and local_copy_pass_count == 224
            and str(local_copy_summary.get("mysqld_version", "")).startswith("8.0.45")
        )

    passed = bool(
        manifest.get("batch_id") == "2026-10-27-type-upgrade-condensed-120-v1"
        and manifest.get("batch_kind") == "type_upgrade_condensed_sql"
        and manifest.get("case_count") == EXPECTED_CASE_COUNT
        and manifest.get("sql_file_count") == EXPECTED_SQL_COUNT
        and manifest.get("expected_output_line_count") == EXPECTED_OUTPUT_LINES
        and manifest.get("materialization") == "sql_directory"
        and unique_case_ids
        and sql_count_ok
        and sql_case_ids_ok
        and expected_output_ok
        and expected_algorithms_ok
        and sql_contract_ok
        and artifact_hashes_ok
        and usage_documented
        and local_metadata_ok
    )

    report: dict[str, Any] = {
        "passed": passed,
        "batch_id": manifest.get("batch_id"),
        "batch_kind": manifest.get("batch_kind"),
        "case_count": len(case_ids),
        "sql_file_count": len(sql_files),
        "expected_output_line_count": len(expected_lines),
        "unique_case_ids": unique_case_ids,
        "sql_count_ok": sql_count_ok,
        "sql_case_ids_ok": sql_case_ids_ok,
        "expected_output_ok": expected_output_ok,
        "expected_algorithms_ok": expected_algorithms_ok,
        "sql_contract_ok": sql_contract_ok,
        "artifact_hashes_ok": artifact_hashes_ok,
        "usage_documented": usage_documented,
        "local_required": require_local,
        "local_metadata_ok": local_metadata_ok,
        "local_copy_result_line_count": len(local_copy_lines),
        "local_copy_pass_count": local_copy_pass_count,
        "mysqld_version": local_copy_summary.get("mysqld_version"),
    }
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = f"""# Condensed 120 SQL audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Cases:** {len(case_ids)}
- **SQL files:** {len(sql_files)}
- **Expected output lines:** {len(expected_lines)}
- **INPLACE and INSTANT in every file:** {'PASS' if sql_contract_ok else 'FAIL'}
- **Local COPY non-FK evidence:** {local_copy_pass_count}/{len(local_copy_lines)} PASS
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
