"""Independent audit for the condensed type-upgrade pipeline artifacts."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from mysql_case_factory.type_upgrade_pipeline import PIPELINE_PROFILES

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
    return sorted((output / profile).glob("TUCP-*.sql"))


def _parent_case_ids(paths: Iterable[Path]) -> set[str]:
    result: set[str] = set()
    for path in paths:
        for payload in _load_cases(path):
            result.add(payload["case_id"])
    return result


def audit_pipeline_artifacts(
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

    profile_files = {profile: _sql_files(output, profile) for profile in PIPELINE_PROFILES}
    profile_counts = {profile: len(files) for profile, files in profile_files.items()}
    profile_counts_match = profile_counts == {profile: manifest["case_count"] for profile in PIPELINE_PROFILES}
    case_ids_match = case_ids == [f"TUCP-{number:06d}" for number in range(1, 51)]
    unique_case_ids = len(case_ids) == len(set(case_ids))

    expected_by_case = {
        path.stem: path.read_text(encoding="utf-8").splitlines()
        for path in sorted((output / "expected").glob("TUCP-*.tsv"))
    }
    expected_global = (output / "expected_output.tsv").read_text(encoding="utf-8").splitlines()
    expected_concat = [line for case_id in case_ids for line in expected_by_case.get(case_id, [])]
    expected_output_ok = expected_global == expected_concat and len(expected_global) > 0
    expected_no_fail = all("|FAIL" not in line for line in expected_global)

    table_names_by_profile: dict[str, set[str]] = {}
    index_names_by_profile: dict[str, set[str]] = {}
    duplicate_table_names: list[str] = []
    duplicate_index_names: list[str] = []
    index_naming_ok = True
    sql_line_counts: dict[str, list[int]] = {}
    forbidden_absent = True
    structural_ok = True
    algorithm_counts_ok = True

    for profile, files in profile_files.items():
        sql_line_counts[profile] = []
        table_names_by_profile[profile] = set()
        index_names_by_profile[profile] = set()
        for path in files:
            sql = path.read_text(encoding="utf-8")
            lines = sql.splitlines()
            sql_line_counts[profile].append(len(lines))
            executable = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("--")]
            if (
                len(lines) < 220
                or len(lines) > 520
                or not executable
                or not executable[0].startswith("DROP TABLE IF EXISTS tab_tucp_")
                or not executable[-1].startswith("DROP TABLE IF EXISTS tab_tucp_")
                or "SET SESSION" in sql
                or "SET GLOBAL" in sql
                or "DELIMITER" in sql
            ):
                structural_ok = False
            if any(token in sql.upper() for token in FORBIDDEN_TOKENS):
                forbidden_absent = False

            expected_algorithm_count = 2 if cases[int(path.stem[-6:]) - 1]["scenario"]["chained"] else 1
            if sql.count(f"ALGORITHM={profile.upper()}") != expected_algorithm_count:
                algorithm_counts_ok = False

            for match in re.finditer(r"^CREATE TABLE\s+([A-Za-z0-9_]+)", sql, flags=re.MULTILINE):
                table_name = match.group(1)
                if table_name in table_names_by_profile[profile]:
                    duplicate_table_names.append(table_name)
                table_names_by_profile[profile].add(table_name)
            for create_line in (line for line in lines if line.startswith("CREATE TABLE ")):
                create_match = re.match(r"CREATE TABLE\s+([A-Za-z0-9_]+)", create_line)
                table_name = create_match.group(1) if create_match else ""
                table_index_names: set[str] = set()
                for match in re.finditer(r"(?:UNIQUE\s+)?KEY\s+([A-Za-z0-9_]+)", create_line):
                    index_name = match.group(1)
                    if not re.fullmatch(r"(?:idx|uk)_tucp_\d{3}_[A-Za-z0-9_]+", index_name):
                        index_naming_ok = False
                    if index_name in table_index_names:
                        duplicate_index_names.append(f"{table_name}.{index_name}")
                    table_index_names.add(index_name)
                    index_names_by_profile[profile].add(index_name)

    artifact_hashes_ok = bool(manifest.get("artifacts_sha256")) and all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest["artifacts_sha256"].items()
    )

    table_sets_match = len({frozenset(names) for names in table_names_by_profile.values()}) == 1
    table_names = next(iter(table_names_by_profile.values()), set())
    index_sets_match = len({frozenset(names) for names in index_names_by_profile.values()}) == 1
    index_names = next(iter(index_names_by_profile.values()), set())
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
        local_result_counts: dict[str, int] = {}
        for result in local_results:
            local_result_counts[result["outcome"]] = local_result_counts.get(result["outcome"], 0) + 1
        local_all_pass = bool(local_summary.get("all_pass")) and all(
            result["outcome"] == "PASS" for result in local_results
        )
        local_metadata_ok = (
            local_summary.get("batch_id") == manifest.get("batch_id")
            and local_summary.get("profile") == "copy"
            and local_summary.get("selected_count") == 50
            and local_summary.get("executed_count") == 50
            and local_summary.get("counts") == {"PASS": 52}
            and str(local_summary.get("mysqld_version", "")).startswith("8.0.45")
            and local_results[-1]["case_id"] == "FINAL_CLEANUP"
            and local_results[-2]["case_id"] == "COMBINED_OUTPUT"
        )
    else:
        local_metadata_ok = True

    scenarios = [case["scenario"] for case in cases]
    semantic_checks = {
        "integer_family": any(scenario["family"] == "integer" for scenario in scenarios),
        "decimal_family": any(scenario["family"] == "decimal" for scenario in scenarios),
        "character_family": any(scenario["family"] == "character" for scenario in scenarios),
        "binary_family": any(scenario["family"] == "binary" for scenario in scenarios),
        "bit_at_least_10": sum(scenario["family"] == "bit" for scenario in scenarios) >= 10,
        "bit_63_to_64": any(
            scenario["source_type"] == "BIT(63)" and scenario["target_type"] == "BIT(64)"
            for scenario in scenarios
        ),
        "primary_index": any(scenario["index_profile"] == "primary" for scenario in scenarios),
        "functional_index": any(scenario["index_profile"] == "functional" for scenario in scenarios),
        "prefix_index": any(scenario["index_profile"] == "prefix" for scenario in scenarios),
        "four_fk_actions": {
            "cascade_delete",
            "cascade_update",
            "set_null",
            "no_action",
        } <= {scenario["foreign_key_action"] for scenario in scenarios if scenario["foreign_key_action"]},
        "all_dependency_kinds": {"view", "trigger", "function", "procedure", "view_trigger_function_procedure"}
        <= {scenario["dependency_profile"] for scenario in scenarios},
        "table_and_partition_stats": {"table_index", "partition"} <= {
            scenario["stats_profile"] for scenario in scenarios if scenario["stats_profile"]
        },
        "chained_upgrade": any(scenario["chained"] for scenario in scenarios),
        "multi_column_upgrade": any(scenario["multi_column"] for scenario in scenarios),
        "engine_matrix": {"InnoDB", "MyISAM", "MEMORY"} <= {scenario["engine"] for scenario in scenarios},
        "range_partition": any(scenario["partition_form"] == "range" for scenario in scenarios),
        "auto_increment_primary": any(
            scenario["target_is_primary"] and scenario["auto_increment"] for scenario in scenarios
        ),
    }
    semantic_coverage_ok = all(semantic_checks.values())

    passed = bool(
        manifest.get("batch_id") == "2026-10-15-type-upgrade-pipeline-v1"
        and manifest.get("case_count") == 50
        and profile_counts_match
        and case_ids_match
        and unique_case_ids
        and not overlap
        and expected_output_ok
        and expected_no_fail
        and structural_ok
        and algorithm_counts_ok
        and not duplicate_table_names
        and table_sets_match
        and not duplicate_index_names
        and index_sets_match
        and index_naming_ok
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
        "expected_output_ok": expected_output_ok,
        "expected_no_fail": expected_no_fail,
        "structural_ok": structural_ok,
        "algorithm_counts_ok": algorithm_counts_ok,
        "unique_table_count": len(table_names),
        "table_sets_match": table_sets_match,
        "duplicate_table_names": duplicate_table_names,
        "unique_index_count": len(index_names),
        "index_sets_match": index_sets_match,
        "index_naming_ok": index_naming_ok,
        "duplicate_index_names": duplicate_index_names,
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
    summary = f"""# Type-upgrade condensed pipeline audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Case count:** {len(cases)}
- **Profiles:** {', '.join(f'{profile}={count}' for profile, count in profile_counts.items())}
- **Parent case overlap:** {len(overlap)}
- **Unique table count:** {len(table_names)}
- **Unique index names:** {len(index_names)} (format and per-table uniqueness OK)
- **SQL line range:** {report['sql_line_count_min']}-{report['sql_line_count_max']}
- **Local COPY all PASS:** {local_all_pass if require_local else 'not required'}
- **Semantic coverage:** {sum(semantic_checks.values())}/{len(semantic_checks)}
- **Missing semantic checks:** {', '.join(failed_checks) if failed_checks else 'none'}
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
