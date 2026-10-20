from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.fk_type_expansion import (
    FK_ACTIONS,
    FK_EXPANSION_BATCH_ID,
    FK_EXPANSION_CASE_PREFIX,
    FK_EXPANSION_DATABASE,
    FK_EXPANSION_PROFILES,
    fk_type_transitions,
    expected_fk_expansion_output,
    iter_fk_expansion_scenarios,
    render_fk_expansion_sql,
    smoke_fk_expansion_scenarios,
)


def test_batch_identity_and_transition_scale() -> None:
    assert FK_EXPANSION_BATCH_ID == "2026-10-20-fk-type-expansion-consistency-v1"
    assert FK_EXPANSION_CASE_PREFIX == "TUCFK"
    assert FK_EXPANSION_DATABASE == "qa_fk_type_expansion"
    assert FK_EXPANSION_PROFILES == ("inplace", "instant")
    assert FK_ACTIONS == ("RESTRICT", "NO ACTION", "CASCADE", "SET NULL")

    transitions = fk_type_transitions()
    assert len(transitions) == 71
    assert len({transition.key for transition in transitions}) == 71
    for family, minimum in (
        ("integer", 22),
        ("character", 14),
        ("binary", 12),
        ("decimal", 10),
        ("bit", 13),
    ):
        actual = sum(1 for transition in transitions if transition.family == family)
        assert actual == minimum, (family, actual)


def test_scenario_space_is_exact_lazy_and_deterministic() -> None:
    scenarios = iter_fk_expansion_scenarios()
    first = next(scenarios)
    assert first.case_id == "TUCFK-000001"
    assert first.family == "integer"
    assert first.algorithm == "inplace"
    assert first.fk_action == "RESTRICT"

    count = 0
    last = None
    for scenario in iter_fk_expansion_scenarios():
        last = scenario
        count += 1
    assert count == 568
    assert last is not None
    assert last.case_id == "TUCFK-000568"

    assert [s.case_id for s in iter_fk_expansion_scenarios()] == [
        s.case_id for s in iter_fk_expansion_scenarios()
    ]


def test_algorithm_and_fk_action_matrix_is_complete() -> None:
    scenarios = list(iter_fk_expansion_scenarios())
    assert {scenario.algorithm for scenario in scenarios} == set(FK_EXPANSION_PROFILES)
    assert {scenario.fk_action for scenario in scenarios} == set(FK_ACTIONS)
    for algorithm in FK_EXPANSION_PROFILES:
        assert sum(1 for scenario in scenarios if scenario.algorithm == algorithm) == 284
    for action in FK_ACTIONS:
        assert sum(1 for scenario in scenarios if scenario.fk_action == action) == 142


def test_expected_outcomes_follow_internal_matrix() -> None:
    scenarios = list(iter_fk_expansion_scenarios())

    integer_cross = next(
        scenario
        for scenario in scenarios
        if scenario.family == "integer"
        and scenario.source_type != scenario.target_type
        and scenario.algorithm == "inplace"
    )
    assert integer_cross.expected_ddl_success is False
    assert integer_cross.expected_error_code == 3780

    integer_same = next(
        scenario
        for scenario in scenarios
        if scenario.family == "integer"
        and scenario.source_type == scenario.target_type
        and scenario.algorithm == "inplace"
    )
    assert integer_same.expected_ddl_success is True
    assert integer_same.expected_error_code is None

    character_inplace = next(
        scenario
        for scenario in scenarios
        if scenario.family == "character" and scenario.algorithm == "inplace"
    )
    assert character_inplace.expected_ddl_success is True

    character_instant = next(
        scenario
        for scenario in scenarios
        if scenario.family == "character" and scenario.algorithm == "instant"
    )
    assert character_instant.expected_ddl_success is False
    assert character_instant.expected_error_code == 1845

    fixed_binary_inplace = next(
        scenario
        for scenario in scenarios
        if scenario.family == "binary"
        and scenario.source_type.startswith("BINARY")
        and scenario.algorithm == "inplace"
    )
    assert fixed_binary_inplace.expected_ddl_success is False
    assert fixed_binary_inplace.expected_error_code == 1846


def test_sql_contains_full_dml_fk_oracle_and_cleanup() -> None:
    scenario = next(iter_fk_expansion_scenarios())
    sql = render_fk_expansion_sql(scenario)
    assert sql.startswith("-- --------------------------------------------------------")
    assert "author       : yuzhengwen y00938623" in sql
    assert "DROP TABLE IF EXISTS" in sql
    assert "CREATE TABLE" in sql
    assert "INSERT INTO" in sql
    assert "UPDATE" in sql
    assert "DELETE FROM" in sql
    assert "LEFT JOIN" in sql
    assert "information_schema.COLUMNS" in sql
    assert "information_schema.KEY_COLUMN_USAGE" in sql
    assert "ALGORITHM=INPLACE" in sql
    assert "ON DELETE RESTRICT" in sql
    assert "PASS" in sql and "FAIL" in sql


def test_expected_output_is_deterministic_tsv() -> None:
    scenario = next(iter_fk_expansion_scenarios())
    output = expected_fk_expansion_output(scenario)
    fields = output.split("\t")
    assert len(fields) == 10
    assert fields[0] == scenario.case_id
    assert fields[-1] == "PASS"
    assert expected_fk_expansion_output(scenario) == expected_fk_expansion_output(scenario)


def test_smoke_contains_one_scenario_per_family() -> None:
    smoke = smoke_fk_expansion_scenarios()
    assert len(smoke) == 5
    assert {scenario.family for scenario in smoke} == {
        "integer", "character", "binary", "decimal", "bit"
    }


def test_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_fk_type_expansion.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == FK_EXPANSION_BATCH_ID
    assert manifest["case_count"] == 568
    assert manifest["transition_count"] == 71
    assert manifest["profile_counts"] == {"inplace": 284, "instant": 284}
    assert manifest["materialization"] == "sql_suite"

    with gzip.open(first / "cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle]
    assert len(cases) == 568
    assert all(case["case_id"].startswith("TUCFK-") for case in cases)

    for name in (
        "manifest.json",
        "cases.jsonl.gz",
        "inplace_suite.sql.gz",
        "instant_suite.sql.gz",
        "expected_output_inplace.tsv",
        "expected_output_instant.tsv",
        "coverage.tsv",
        "README.md",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()
