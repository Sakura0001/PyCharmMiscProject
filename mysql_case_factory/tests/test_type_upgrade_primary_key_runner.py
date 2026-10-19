from __future__ import annotations

from mysql_case_factory.type_upgrade_primary_key import smoke_primary_key_scenarios
from mysql_case_factory.type_upgrade_primary_key_runner import (
    ALL_COLUMN_NAMES,
    build_create_table_sql,
    build_insert_sql,
    classify_scenario_execution,
)


def _smoke(family: str):
    return next(scenario for scenario in smoke_primary_key_scenarios() if scenario.family == family)


def test_create_table_sql_contains_all_columns_pk_prefix_and_auto_increment() -> None:
    integer = _smoke("integer")
    text = _smoke("text")

    integer_sql = build_create_table_sql(integer, "t_int", integer.source_type, auto_increment_start=1)
    assert "pk TINYINT NOT NULL AUTO_INCREMENT" in integer_sql
    assert "PRIMARY KEY(pk)" in integer_sql
    for column in ALL_COLUMN_NAMES:
        assert column in integer_sql

    text_sql = build_create_table_sql(text, "t_text", text.source_type, auto_increment_start=None)
    assert "pk TINYTEXT NOT NULL" in text_sql
    assert "PRIMARY KEY(pk(32))" in text_sql
    assert "ROW_FORMAT=DYNAMIC" in text_sql


def test_insert_sql_omits_auto_increment_pk_and_lists_every_other_column() -> None:
    integer = _smoke("integer")
    sql, columns = build_insert_sql(integer, "t_int", include_pk=False, style="omit_pk_explicit_columns")
    assert sql.startswith("INSERT INTO t_int (")
    assert "pk" not in columns
    assert columns == ALL_COLUMN_NAMES
    assert sql.count("%s") == len(columns)

    positional_sql, positional_columns = build_insert_sql(
        integer, "t_int", include_pk=True, style="null_pk_positional", positional=True
    )
    assert positional_sql.startswith("INSERT INTO t_int VALUES")
    assert positional_columns[0] == "pk"
    assert positional_columns[1:] == ALL_COLUMN_NAMES


def test_non_integer_insert_explicitly_includes_pk() -> None:
    decimal = _smoke("decimal")
    sql, columns = build_insert_sql(decimal, "t_dec", include_pk=True, style="explicit_pk_all_columns")
    assert columns[0] == "pk"
    assert columns[1:] == ALL_COLUMN_NAMES
    assert sql.count("%s") == len(columns)


def test_execution_classifier_distinguishes_expected_reject_and_crash() -> None:
    integer = _smoke("integer")
    char_pre = next(
        scenario
        for scenario in smoke_primary_key_scenarios()
        if scenario.family == "character" and scenario.length_boundary == "pre_256"
    )

    success = classify_scenario_execution(integer, "inplace", True, None)
    reject = classify_scenario_execution(char_pre, "instant", False, "ERROR 1846 unsupported")
    crash = classify_scenario_execution(integer, "instant", False, "ERROR 2013 lost connection")
    assert success == "PASS"
    assert reject == "EXPECTED_REJECT"
    assert crash == "FAIL_CRASH"
