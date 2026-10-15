from __future__ import annotations

from mysql_case_factory.type_upgrade_boundary_runner import classify_execution


def test_boundary_exact_output_is_pass() -> None:
    result = classify_execution(
        0,
        "TUCZ-000001|SCHEMA|OK\n",
        "TUCZ-000001|SCHEMA|OK\n",
        "",
    )
    assert result.outcome == "PASS"
    assert result.error is None


def test_boundary_output_mismatch_and_connection_loss_are_distinct() -> None:
    mismatch = classify_execution(
        0,
        "TUCZ-000001|SCHEMA|FAIL\n",
        "TUCZ-000001|SCHEMA|OK\n",
        "",
    )
    crash = classify_execution(
        1,
        "",
        "TUCZ-000001|SCHEMA|OK\n",
        "ERROR 2013 (HY000): Lost connection",
    )
    assert mismatch.outcome == "FAIL_OUTPUT"
    assert crash.outcome == "FAIL_CRASH"
