from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.virtual_function_type_upgrade import (
    DATA_STATES,
    DEPENDENCY_MODES,
    NULLABILITY_STATES,
    SCENARIO_COUNT,
    VIRTUAL_FUNCTION_BATCH_ID,
    VIRTUAL_FUNCTION_CASE_PREFIX,
    VIRTUAL_FUNCTION_DATABASE,
    VIRTUAL_FUNCTION_PROFILES,
    build_create_table_sql,
    build_ddl_sql,
    iter_virtual_function_scenarios,
    smoke_virtual_function_scenarios,
)


def test_batch_identity_and_exact_scenario_space() -> None:
    assert VIRTUAL_FUNCTION_BATCH_ID == "2026-10-20-virtual-function-type-upgrade-v1"
    assert VIRTUAL_FUNCTION_CASE_PREFIX == "TUCVF"
    assert VIRTUAL_FUNCTION_DATABASE == "qa_virtual_function_type_upgrade"
    assert VIRTUAL_FUNCTION_PROFILES == ("copy", "inplace", "instant")
    assert SCENARIO_COUNT == 5_136

    scenarios = list(iter_virtual_function_scenarios())
    assert len(scenarios) == 5_136
    assert scenarios[0].case_id == "TUCVF-000001"
    assert scenarios[-1].case_id == "TUCVF-005136"
    assert [s.case_id for s in iter_virtual_function_scenarios()] == [
        s.case_id for s in iter_virtual_function_scenarios()
    ]


def test_factor_matrix_is_complete() -> None:
    scenarios = list(iter_virtual_function_scenarios())
    assert {s.dependency_mode for s in scenarios} == set(DEPENDENCY_MODES)
    assert {s.algorithm for s in scenarios} == set(VIRTUAL_FUNCTION_PROFILES)
    assert {s.data_state for s in scenarios} == set(DATA_STATES)
    assert {s.nullability for s in scenarios} == set(NULLABILITY_STATES)
    assert {s.family for s in scenarios} == {
        "integer", "decimal", "bit", "character", "binary", "text", "blob"
    }
    for profile in VIRTUAL_FUNCTION_PROFILES:
        assert sum(1 for s in scenarios if s.algorithm == profile) == 1_712
    for dependency in DEPENDENCY_MODES:
        assert sum(1 for s in scenarios if s.dependency_mode == dependency) == 1_284


def test_smoke_contains_all_family_dependency_and_algorithm_combinations() -> None:
    smoke = smoke_virtual_function_scenarios()
    assert len(smoke) == 84
    assert {s.family for s in smoke} == {
        "integer", "decimal", "bit", "character", "binary", "text", "blob"
    }
    assert {s.dependency_mode for s in smoke} == set(DEPENDENCY_MODES)
    assert {s.algorithm for s in smoke} == set(VIRTUAL_FUNCTION_PROFILES)
    assert len({s.case_id for s in smoke}) == 84


def test_create_table_sql_contains_dependencies() -> None:
    scenarios = list(iter_virtual_function_scenarios())
    virtual = next(s for s in scenarios if s.dependency_mode == "virtual_generated")
    stored = next(s for s in scenarios if s.dependency_mode == "stored_generated")
    functional = next(s for s in scenarios if s.dependency_mode == "functional_index")
    none = next(s for s in scenarios if s.dependency_mode == "none")

    virtual_sql = build_create_table_sql(virtual, virtual.candidate_table, virtual.source_type)
    stored_sql = build_create_table_sql(stored, stored.candidate_table, stored.source_type)
    functional_sql = build_create_table_sql(functional, functional.candidate_table, functional.source_type)
    none_sql = build_create_table_sql(none, none.candidate_table, none.source_type)

    assert "AS (" in virtual_sql and "VIRTUAL" in virtual_sql
    assert "AS (" in stored_sql and "STORED" in stored_sql
    assert "KEY `idx_tucvf_fn` ((" in functional_sql
    assert "gen" not in none_sql
    assert "PRIMARY KEY (id)" in virtual_sql


def test_ddl_sql_uses_selected_algorithm() -> None:
    scenarios = list(iter_virtual_function_scenarios())
    for scenario in scenarios:
        sql = build_ddl_sql(scenario, scenario.candidate_table)
        assert f"ALGORITHM={scenario.algorithm.upper()}" in sql
        assert scenario.target_type in sql


def test_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_virtual_function_type_upgrade.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == VIRTUAL_FUNCTION_BATCH_ID
    assert manifest["case_count"] == 5_136
    assert manifest["transition_count"] == 107
    assert manifest["dependency_mode_count"] == 4
    assert manifest["profile_counts"] == {
        "copy": 1_712,
        "inplace": 1_712,
        "instant": 1_712,
    }
    assert manifest["smoke_case_count"] == 84
    assert manifest["materialization"] == "virtual_runner"

    with gzip.open(first / "cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle]
    assert len(cases) == 5_136
    assert all(case["case_id"].startswith("TUCVF-") for case in cases)

    for name in ("manifest.json", "cases.jsonl.gz", "smoke_cases.jsonl.gz", "coverage.tsv", "README.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
