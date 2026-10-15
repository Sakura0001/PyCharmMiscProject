from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_boundary import (
    BOUNDARY_BATCH_ID,
    BOUNDARY_BATCH_KIND,
    BOUNDARY_CASE_PREFIX,
    BOUNDARY_PROFILES,
    generate_boundary_cases,
    render_boundary_case,
)


def test_boundary_batch_identity_and_scale() -> None:
    assert BOUNDARY_BATCH_ID == "2026-10-15-type-upgrade-boundary-v1"
    assert BOUNDARY_BATCH_KIND == "boundary_extension"
    assert BOUNDARY_CASE_PREFIX == "TUCZ"
    assert BOUNDARY_PROFILES == ("copy", "inplace", "instant")

    cases = generate_boundary_cases()
    assert len(cases) == 750
    assert len({case.case_id for case in cases}) == 750
    assert cases[0].case_id == "TUCZ-000001"
    assert cases[-1].case_id == "TUCZ-000750"
    assert all(case.batch_id == BOUNDARY_BATCH_ID for case in cases)


def test_boundary_matrix_covers_zero_decimal_max_and_alias_factors() -> None:
    cases = generate_boundary_cases()
    categories = {case.category for case in cases}
    assert {
        "zero_core",
        "zero_cross",
        "decimal_max",
        "variable_max",
        "variable_overflow",
        "alias_normalization",
    } == categories

    counts: dict[str, int] = {}
    for case in cases:
        counts[case.category] = counts.get(case.category, 0) + 1
    assert counts == {
        "zero_core": 512,
        "zero_cross": 112,
        "decimal_max": 64,
        "variable_max": 20,
        "variable_overflow": 10,
        "alias_normalization": 32,
    }

    sources = {case.source_type for case in cases}
    assert {
        "CHAR(0)",
        "VARCHAR(0)",
        "BINARY(0)",
        "VARBINARY(0)",
        "DECIMAL(63,30)",
        "NUMERIC(63,30)",
        "BOOL",
        "BOOLEAN",
        "TINYINT(1)",
        "DEC",
        "FIXED",
        "NCHAR(0)",
        "NVARCHAR(0)",
        "CHARACTER(0)",
        "CHARACTER VARYING(0)",
        "INT UNSIGNED ZEROFILL",
    } <= sources

    assert {case.position for case in cases} == {
        "none",
        "noop_after",
        "actual_after",
        "first",
    }
    assert {case.attribute_transition for case in cases} == {
        "not_null_default_to_null",
        "not_null_default_preserve",
        "not_null_no_default",
        "nullable",
    }
    assert {case.row_format for case in cases} == {
        "DYNAMIC",
        "COMPACT",
        "COMPRESSED",
        "REDUNDANT",
    }


def test_every_boundary_case_upgrades_seed_data_then_inserts_before_second_upgrade() -> None:
    cases = generate_boundary_cases()
    for case in cases:
        sql = render_boundary_case(case, "copy").split("-- @@@EXPECTED@@@")[0]
        ddl_lines = [line.strip() for line in sql.splitlines() if "ALTER TABLE" in line and "ALGORITHM=COPY" in line]
        assert len(ddl_lines) == 2, case.case_id
        first_ddl_index = next(
            index for index, line in enumerate(sql.splitlines()) if "ALGORITHM=COPY" in line
        )
        second_ddl_index = next(
            index for index, line in enumerate(sql.splitlines()) if "ALGORITHM=COPY" in line and index > first_ddl_index
        )
        between = "\n".join(sql.splitlines()[first_ddl_index + 1 : second_ddl_index])
        assert "INSERT INTO" in between, case.case_id
        assert "-- post-first-upgrade target-boundary data" in between, case.case_id


def test_boundary_sql_is_safe_deterministic_and_exact_output_capable() -> None:
    cases = generate_boundary_cases()
    table_names: set[str] = set()
    for case in cases:
        sql = render_boundary_case(case, "copy").split("-- @@@EXPECTED@@@")[0]
        lines = sql.splitlines()
        executable = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("--")]
        assert 160 <= len(lines) <= 420, (case.case_id, len(lines))
        assert executable[0].startswith("DROP TABLE IF EXISTS tab_tucz_")
        assert executable[-1].startswith("DROP TABLE IF EXISTS tab_tucz_")
        assert "SET SESSION" not in sql
        assert "SET GLOBAL" not in sql
        assert "DELIMITER" not in sql
        assert sql.count("-- CASE_ID: ") == 1
        assert sql.count("-- PROFILE: copy") == 1
        assert sql.count("ALGORITHM=COPY") == 2

        for line in lines:
            if line.startswith("CREATE TABLE "):
                table_name = line.split()[2]
                assert table_name not in table_names, table_name
                table_names.add(table_name)

        expected = render_boundary_case(case, "copy").split("-- @@@EXPECTED@@@")[1].strip().splitlines()
        assert expected
        assert all(line.endswith("|OK") or line.endswith("\tanalyze\tstatus\tOK") for line in expected)

    assert len(table_names) >= 750
    assert [render_boundary_case(case, "copy") for case in cases] == [
        render_boundary_case(case, "copy") for case in generate_boundary_cases()
    ]


def test_boundary_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_boundary.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    for profile in BOUNDARY_PROFILES:
        first_files = sorted((first / profile).glob("TUCZ-*.sql"))
        second_files = sorted((second / profile).glob("TUCZ-*.sql"))
        assert len(first_files) == 750
        assert [path.read_bytes() for path in first_files] == [path.read_bytes() for path in second_files]

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == BOUNDARY_BATCH_ID
    assert manifest["case_count"] == 750
    assert manifest["profile_counts"] == {profile: 750 for profile in BOUNDARY_PROFILES}
    assert manifest["forbidden_types_absent"] is True

    with gzip.open(first / "cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        payloads = [json.loads(line) for line in handle]
    assert len(payloads) == 750
    assert all(payload["case_id"].startswith("TUCZ-") for payload in payloads)


def test_boundary_zero_binary_default_and_fk_actual_after_layout_are_valid() -> None:
    cases = generate_boundary_cases()
    by_id = {case.case_id: case for case in cases}

    binary_zero = next(case for case in cases if case.scenario.source_type == "BINARY(0)")
    assert "NOT NULL DEFAULT x''" in binary_zero.scenario.source_attribute

    fk_actual = next(
        case
        for case in cases
        if case.scenario.foreign_key and case.scenario.position == "actual_after"
    )
    sql = render_boundary_case(fk_actual, "copy").split("-- @@@EXPECTED@@@")[0]
    ref_create = next(line for line in sql.splitlines() if f"CREATE TABLE {fk_actual.scenario.ref_table} " in line)
    assert ref_create.index("fk_col BIGINT NULL") < ref_create.index("c VARCHAR(50)")
    assert ref_create.index("c VARCHAR(50)") < ref_create.index("v ")
    assert ref_create.count("c VARCHAR(50)") == 1


def test_boundary_overflow_values_fit_text_and_unsigned_chain() -> None:
    cases = generate_boundary_cases()
    overflow = [case for case in cases if case.category == "variable_overflow"]
    assert overflow
    for case in overflow:
        scenario = case.scenario
        if "TEXT" in scenario.target_type.upper():
            bytes_per_char = {"utf8mb4": 4, "utf8mb3": 3}.get(scenario.charset, 1)
            for expression in scenario.final_values:
                if "RPAD" in expression:
                    length = int(expression.split(",", 1)[1].split(",", 1)[0])
                    assert length * bytes_per_char <= 65535, case.case_id
        if "BLOB" in scenario.target_type.upper():
            for expression in scenario.final_values:
                if "RPAD" in expression:
                    length = int(expression.split(",", 1)[1].split(",", 1)[0])
                    assert length <= 65535, case.case_id

    int_zero = next(case for case in cases if case.scenario.source_type == "INT(0)")
    assert all(not value.startswith("-") for value in int_zero.scenario.intermediate_values)
    assert all(not value.startswith("-") for value in int_zero.scenario.final_values)
