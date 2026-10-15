"""Independent audit for the TUCZ boundary extension artifacts."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from mysql_case_factory.type_upgrade_boundary import BOUNDARY_PROFILES

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


def _load_cases(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sql_files(output: Path, profile: str) -> list[Path]:
    return sorted((output / profile).glob("TUCZ-*.sql"))


def _parent_case_ids(paths: Iterable[Path]) -> set[str]:
    result: set[str] = set()
    for path in paths:
        for payload in _load_cases(path):
            result.add(payload["case_id"])
    return result


def audit_boundary_artifacts(
    output: Path,
    *,
    parent_case_paths: Iterable[Path] = (),
    require_local: bool = True,
) -> dict[str, Any]:
    manifest = _load_json(output / "manifest.json")
    cases = _load_cases(output / "cases.jsonl.gz")
    case_ids = [case["case_id"] for case in cases]
    parent_ids = _parent_case_ids(parent_case_paths)
    overlap = sorted(set(case_ids) & parent_ids)

    profile_files = {profile: _sql_files(output, profile) for profile in BOUNDARY_PROFILES}
    profile_counts = {profile: len(files) for profile, files in profile_files.items()}
    profile_counts_match = profile_counts == {profile: 750 for profile in BOUNDARY_PROFILES}
    case_ids_match = case_ids == [f"TUCZ-{number:06d}" for number in range(1, 751)]
    unique_case_ids = len(case_ids) == len(set(case_ids))

    expected_by_case = {
        path.stem: path.read_text(encoding="utf-8").splitlines()
        for path in sorted((output / "expected").glob("TUCZ-*.tsv"))
    }
    expected_global = (output / "expected_output.tsv").read_text(encoding="utf-8").splitlines()
    expected_concat = [line for case_id in case_ids for line in expected_by_case.get(case_id, [])]
    expected_output_ok = expected_global == expected_concat and bool(expected_global)
    expected_no_fail = all("|FAIL" not in line for line in expected_global)

    category_counts: dict[str, int] = {}
    for case in cases:
        category = case["scenario"]["category"]
        category_counts[category] = category_counts.get(category, 0) + 1
    expected_category_counts = {
        "zero_core": 512,
        "zero_cross": 112,
        "decimal_max": 64,
        "variable_max": 20,
        "variable_overflow": 10,
        "alias_normalization": 32,
    }

    table_names_by_profile: dict[str, set[str]] = {}
    duplicate_table_names: list[str] = []
    structural_ok = True
    two_stage_with_intermediate_insert = True
    algorithm_counts_ok = True
    forbidden_absent = True
    sql_line_counts: dict[str, list[int]] = {}

    for profile, files in profile_files.items():
        table_names_by_profile[profile] = set()
        sql_line_counts[profile] = []
        for path in files:
            sql = path.read_text(encoding="utf-8")
            lines = sql.splitlines()
            sql_line_counts[profile].append(len(lines))
            executable = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("--")]
            if (
                len(lines) < 160
                or len(lines) > 420
                or not executable
                or not executable[0].startswith("DROP TABLE IF EXISTS tab_tucz_")
                or not executable[-1].startswith("DROP TABLE IF EXISTS tab_tucz_")
                or "SET SESSION" in sql
                or "SET GLOBAL" in sql
                or "DELIMITER" in sql
            ):
                structural_ok = False
            if any(token in sql.upper() for token in FORBIDDEN_TOKENS):
                forbidden_absent = False
            if sql.count(f"ALGORITHM={profile.upper()}") != 2:
                algorithm_counts_ok = False

            alter_indexes = [
                index for index, line in enumerate(lines) if f"ALGORITHM={profile.upper()}" in line
            ]
            if len(alter_indexes) != 2:
                two_stage_with_intermediate_insert = False
            else:
                between = "\n".join(lines[alter_indexes[0] + 1 : alter_indexes[1]])
                if "INSERT INTO" not in between or "post-first-upgrade target-boundary data" not in between:
                    two_stage_with_intermediate_insert = False

            for match in re.finditer(r"^CREATE TABLE\s+([A-Za-z0-9_]+)", sql, flags=re.MULTILINE):
                table_name = match.group(1)
                if table_name in table_names_by_profile[profile]:
                    duplicate_table_names.append(table_name)
                table_names_by_profile[profile].add(table_name)

    table_sets_match = len({frozenset(names) for names in table_names_by_profile.values()}) == 1
    table_names = next(iter(table_names_by_profile.values()), set())
    artifact_hashes_ok = bool(manifest.get("artifacts_sha256")) and all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest["artifacts_sha256"].items()
    )

    local_all_pass = False
    local_result_count = 0
    local_result_counts: dict[str, int] = {}
    local_metadata_ok = False
    if require_local:
        local_summary = _load_json(output / "local_summary.json")
        local_results = [
            json.loads(line)
            for line in (output / "local_results.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        local_result_count = len(local_results)
        for result in local_results:
            local_result_counts[result["outcome"]] = local_result_counts.get(result["outcome"], 0) + 1
        local_all_pass = bool(local_summary.get("all_pass")) and all(
            result["outcome"] == "PASS" for result in local_results
        )
        local_metadata_ok = (
            local_summary.get("batch_id") == manifest.get("batch_id")
            and local_summary.get("profile") == "copy"
            and local_summary.get("selected_count") == 750
            and local_summary.get("executed_count") == 750
            and local_summary.get("counts") == {"PASS": 752}
            and str(local_summary.get("mysqld_version", "")).startswith("8.0.45")
            and local_results[-1]["case_id"] == "FINAL_CLEANUP"
            and local_results[-2]["case_id"] == "COMBINED_OUTPUT"
        )
    else:
        local_metadata_ok = True

    scenarios = [case["scenario"] for case in cases]
    semantic_checks = {
        "four_zero_sources": {
            "CHAR(0)",
            "VARCHAR(0)",
            "BINARY(0)",
            "VARBINARY(0)",
        } <= {scenario["source_type"] for scenario in scenarios},
        "binary_zero_chain": any(
            scenario["source_type"] == "BINARY(0)"
            and scenario["intermediate_type"] == "BINARY(1)"
            and scenario["target_type"] == "BINARY(2)"
            for scenario in scenarios
        ),
        "zero_cross_and_lob": any(
            scenario["source_type"] == "CHAR(0)" and scenario["target_type"] == "BINARY(2)"
            for scenario in scenarios
        )
        and any(scenario["target_type"] == "TEXT" for scenario in scenarios)
        and any(scenario["target_type"] == "BLOB" for scenario in scenarios),
        "decimal_63_64_65_scale_30": any(
            scenario["source_type"] == "DECIMAL(63,30)"
            and scenario["intermediate_type"] == "DECIMAL(64,30)"
            and scenario["target_type"] == "DECIMAL(65,30)"
            for scenario in scenarios
        ),
        "decimal_numeric_cross": any(
            scenario["source_type"] == "DECIMAL(63,30)" and scenario["target_type"] == "NUMERIC(65,30)"
            for scenario in scenarios
        ),
        "variable_max_matrix": {
            "VARCHAR(16305)",
            "VARCHAR(21741)",
            "VARCHAR(65229)",
            "VARBINARY(65229)",
        } <= {scenario["source_type"] for scenario in scenarios},
        "variable_overflow": any(scenario["category"] == "variable_overflow" for scenario in scenarios),
        "alias_sources": {
            "BOOL",
            "BOOLEAN",
            "TINYINT(1)",
            "INT(0)",
            "INT UNSIGNED ZEROFILL",
            "DEC",
            "FIXED",
            "DECIMAL",
            "NUMERIC",
            "BIT",
            "BINARY",
            "CHAR",
            "NCHAR(0)",
            "NVARCHAR(0)",
            "CHARACTER(0)",
            "CHARACTER VARYING(0)",
        } <= {scenario["source_type"] for scenario in scenarios},
        "position_matrix": {"none", "noop_after", "actual_after", "first"}
        <= {scenario["position"] for scenario in scenarios},
        "attribute_matrix": {
            "not_null_default_to_null",
            "not_null_default_preserve",
            "not_null_no_default",
            "nullable",
        } <= {scenario["attribute_transition"] for scenario in scenarios},
        "row_format_matrix": {"DYNAMIC", "COMPACT", "COMPRESSED", "REDUNDANT"}
        <= {scenario["row_format"] for scenario in scenarios},
        "index_modes": {"none", "add_after_first"} <= {scenario["index_mode"] for scenario in scenarios},
        "stats_subset": sum(scenario["stats_profile"] for scenario in scenarios) > 0,
        "fk_subset": sum(scenario["foreign_key"] for scenario in scenarios) > 0,
    }
    semantic_coverage_ok = all(semantic_checks.values()) and category_counts == expected_category_counts

    passed = bool(
        manifest.get("batch_id") == "2026-10-15-type-upgrade-boundary-v1"
        and manifest.get("case_count") == 750
        and profile_counts_match
        and case_ids_match
        and unique_case_ids
        and not overlap
        and expected_output_ok
        and expected_no_fail
        and structural_ok
        and algorithm_counts_ok
        and two_stage_with_intermediate_insert
        and not duplicate_table_names
        and table_sets_match
        and forbidden_absent
        and manifest.get("forbidden_types_absent") is True
        and artifact_hashes_ok
        and (local_all_pass or not require_local)
        and local_metadata_ok
        and semantic_coverage_ok
    )

    report: dict[str, Any] = {
        "passed": passed,
        "batch_id": manifest.get("batch_id"),
        "case_count": len(cases),
        "case_ids_match": case_ids_match,
        "unique_case_ids": unique_case_ids,
        "parent_case_id_overlap_count": len(overlap),
        "parent_case_id_overlap": overlap,
        "profile_counts": profile_counts,
        "profile_counts_match": profile_counts_match,
        "category_counts": category_counts,
        "expected_category_counts": expected_category_counts,
        "expected_output_ok": expected_output_ok,
        "expected_no_fail": expected_no_fail,
        "structural_ok": structural_ok,
        "algorithm_counts_ok": algorithm_counts_ok,
        "two_stage_with_intermediate_insert": two_stage_with_intermediate_insert,
        "unique_table_count": len(table_names),
        "table_sets_match": table_sets_match,
        "duplicate_table_names": duplicate_table_names,
        "sql_line_count_min": min((min(counts) for counts in sql_line_counts.values() if counts), default=0),
        "sql_line_count_max": max((max(counts) for counts in sql_line_counts.values() if counts), default=0),
        "forbidden_types_absent": forbidden_absent,
        "artifact_hashes_ok": artifact_hashes_ok,
        "local_required": require_local,
        "local_all_pass": local_all_pass,
        "local_result_count": local_result_count,
        "local_result_counts": local_result_counts,
        "local_metadata_ok": local_metadata_ok,
        "semantic_checks": semantic_checks,
        "semantic_coverage_ok": semantic_coverage_ok,
    }
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    failed_checks = [key for key, value in semantic_checks.items() if not value]
    summary = f"""# Type-upgrade boundary audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Case count:** {len(cases)}
- **Profiles:** {', '.join(f'{profile}={count}' for profile, count in profile_counts.items())}
- **Parent case overlap:** {len(overlap)}
- **Unique table count:** {len(table_names)}
- **SQL line range:** {report['sql_line_count_min']}-{report['sql_line_count_max']}
- **Two-stage with intermediate insert:** {two_stage_with_intermediate_insert}
- **Local COPY all PASS:** {local_all_pass if require_local else 'not required'}
- **Semantic coverage:** {sum(semantic_checks.values())}/{len(semantic_checks)}
- **Missing semantic checks:** {', '.join(failed_checks) if failed_checks else 'none'}
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
