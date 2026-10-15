from __future__ import annotations

from mysql_case_factory.type_upgrade_pipeline_runner import classify_execution


def test_exact_expected_output_is_pass() -> None:
    result = classify_execution(0, "TUCP-000001|SCHEMA|OK\n", "TUCP-000001|SCHEMA|OK\n", "")
    assert result.outcome == "PASS"
    assert result.error is None


def test_output_mismatch_is_failure_even_when_mysql_force_returns_zero() -> None:
    result = classify_execution(
        0,
        "TUCP-000001|SCHEMA|FAIL\n",
        "TUCP-000001|SCHEMA|OK\n",
        "",
    )
    assert result.outcome == "FAIL_OUTPUT"
    assert "expected 1 line(s), actual 1 line(s)" in result.error


def test_sql_error_and_connection_loss_are_distinct_failures() -> None:
    sql_error = classify_execution(1, "", "TUCP-000001|SCHEMA|OK\n", "ERROR 1064 (42000)")
    crash = classify_execution(1, "", "TUCP-000001|SCHEMA|OK\n", "ERROR 2013 (HY000): Lost connection")
    assert sql_error.outcome == "FAIL_SQL"
    assert crash.outcome == "FAIL_CRASH"
