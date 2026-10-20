from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.unique_ddl_expected_error import (
    DDL_FORMS,
    DML_TYPES,
    INDEX_SHAPES,
    UNIQUE_DDL_ERROR_BATCH_ID,
    UNIQUE_DDL_ERROR_CASE_PREFIX,
    UNIQUE_DDL_ERROR_DATABASE,
    UNIQUE_DDL_ERROR_PROFILE,
    SCENARIO_COUNT,
    iter_unique_ddl_error_scenarios,
    render_ddl_sql,
    render_dml_sql,
    smoke_unique_ddl_error_scenarios,
)


def test_batch_identity_and_exact_scenario_space() -> None:
    assert UNIQUE_DDL_ERROR_BATCH_ID == "2026-10-20-unique-ddl-expected-error-v1"
    assert UNIQUE_DDL_ERROR_CASE_PREFIX == "TUCUD"
    assert UNIQUE_DDL_ERROR_DATABASE == "qa_unique_ddl_expected_error"
    assert UNIQUE_DDL_ERROR_PROFILE == "inplace"
    assert SCENARIO_COUNT == 192

    scenarios = list(iter_unique_ddl_error_scenarios())
    assert len(scenarios) == 192
    assert scenarios[0].case_id == "TUCUD-000001"
    assert scenarios[-1].case_id == "TUCUD-000192"
    assert [s.case_id for s in iter_unique_ddl_error_scenarios()] == [
        s.case_id for s in iter_unique_ddl_error_scenarios()
    ]


def test_factor_matrix_is_complete() -> None:
    scenarios = list(iter_unique_ddl_error_scenarios())
    assert {s.ddl_form for s in scenarios} == set(DDL_FORMS)
    assert {s.shape for s in scenarios} == set(INDEX_SHAPES)
    assert {s.dml_type for s in scenarios} == set(DML_TYPES)
    for ddl_form in DDL_FORMS:
        assert sum(1 for s in scenarios if s.ddl_form == ddl_form) == 48
    for shape in INDEX_SHAPES:
        assert sum(1 for s in scenarios if s.shape == shape) == 32
    for dml_type in DML_TYPES:
        assert sum(1 for s in scenarios if s.dml_type == dml_type) == 24


def test_smoke_has_one_case_per_shape() -> None:
    smoke = smoke_unique_ddl_error_scenarios()
    assert len(smoke) == 6
    assert {s.shape for s in smoke} == set(INDEX_SHAPES)
    assert all(s.ddl_form == "add_unique_index" for s in smoke)
    assert all(s.dml_type == "insert" for s in smoke)


def test_ddl_sql_covers_all_forms_and_uses_inplace() -> None:
    scenarios = list(iter_unique_ddl_error_scenarios())
    for scenario in scenarios:
        sql = render_ddl_sql(scenario)
        assert "ALGORITHM=INPLACE" in sql
        if scenario.ddl_form != "create_unique_index":
            assert "LOCK=NONE" in sql
        assert "UNIQUE" in sql.upper()

    create_index = next(s for s in scenarios if s.ddl_form == "create_unique_index")
    assert render_ddl_sql(create_index).startswith("CREATE UNIQUE INDEX")

    add_constraint = next(s for s in scenarios if s.ddl_form == "add_constraint_unique")
    assert "ADD CONSTRAINT" in render_ddl_sql(add_constraint)


def test_dml_sql_covers_all_duplicate_mechanisms() -> None:
    scenarios = list(iter_unique_ddl_error_scenarios())
    for scenario in scenarios:
        sql = render_dml_sql(scenario, 200_000)
        assert scenario.table in sql
        if scenario.dml_type == "insert":
            assert sql.startswith("INSERT INTO")
        elif scenario.dml_type == "insert_ignore":
            assert sql.startswith("INSERT IGNORE INTO")
        elif scenario.dml_type == "insert_on_duplicate":
            assert "ON DUPLICATE KEY UPDATE" in sql
        elif scenario.dml_type == "insert_select":
            assert "SELECT" in sql and "INSERT INTO" in sql
        elif scenario.dml_type == "multi_row_insert":
            assert sql.count("),(") >= 1
        elif scenario.dml_type == "update":
            assert sql.startswith("UPDATE")
        elif scenario.dml_type == "update_join":
            assert "JOIN" in sql
        elif scenario.dml_type == "delete_insert":
            assert "DELETE FROM" in sql and "INSERT INTO" in sql


def test_shape_specific_semantic_conflicts_are_distinct() -> None:
    scenarios = list(iter_unique_ddl_error_scenarios())
    prefix = next(s for s in scenarios if s.shape == "prefix")
    prefix_sql = render_dml_sql(prefix, 200_000)
    assert "00001Y99999999" in prefix_sql

    ci = next(s for s in scenarios if s.shape == "case_insensitive")
    ci_sql = render_dml_sql(ci, 200_000)
    assert "abc00000001" in ci_sql

    generated = next(s for s in scenarios if s.shape == "generated")
    generated_sql = render_dml_sql(generated, 200_000)
    assert "abc00000001" in generated_sql

    composite = next(s for s in scenarios if s.shape == "composite")
    composite_sql = render_dml_sql(composite, 200_000)
    assert ",1,1)" in composite_sql


def test_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_unique_ddl_expected_error.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == UNIQUE_DDL_ERROR_BATCH_ID
    assert manifest["case_count"] == 192
    assert manifest["ddl_form_count"] == 4
    assert manifest["index_shape_count"] == 6
    assert manifest["dml_type_count"] == 8
    assert manifest["smoke_case_count"] == 6
    assert manifest["materialization"] == "virtual_runner"

    with gzip.open(first / "cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle]
    assert len(cases) == 192
    assert all(case["case_id"].startswith("TUCUD-") for case in cases)
    assert all(case["expected_error_codes"] == [1062, 1859] for case in cases)

    for name in ("manifest.json", "cases.jsonl.gz", "smoke_cases.jsonl.gz", "coverage.tsv", "README.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
