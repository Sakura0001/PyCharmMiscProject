from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mysql_case_factory.type_upgrade_runner import CaseOutcome, execute_case
from mysql_case_factory.type_upgrade_consistency import generate_cases


class FakeConnection:
    def __init__(
        self,
        *,
        ddl_error: Exception | None = None,
        check_value: str = "OK",
        invalid_statements: set[str] | None = None,
    ) -> None:
        self.executed: list[str] = []
        self.ddl_error = ddl_error
        self.check_value = check_value
        self.invalid_statements = invalid_statements or set()

    def execute(self, sql: str) -> None:
        self.executed.append(sql)
        if sql in self.invalid_statements:
            raise Exception("invalid value rejected")
        if sql.startswith("ALTER TABLE") and self.ddl_error is not None:
            raise self.ddl_error

    def fetchone(self) -> tuple[str]:
        return (self.check_value,)

    def close(self) -> None:
        return None


def _case(expected: str) -> Any:
    case = generate_cases()[0]
    if expected == case.expected_outcome:
        return case
    object.__setattr__(case, "expected_outcome", expected)
    return case


def test_execute_case_passes_expected_success_and_runs_cleanup() -> None:
    case = _case("success")
    connection = FakeConnection(invalid_statements=set(case.invalid_post_ddl_sql))
    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.PASS
    assert result.case_id == case.case_id
    assert result.error is None
    assert connection.executed[1] in case.cleanup_sql
    assert connection.executed[-2] in case.cleanup_sql
    assert case.ddl_sql.replace("${ALGORITHM}", "COPY") in connection.executed


def test_execute_case_fails_when_expected_success_ddl_errors() -> None:
    case = _case("success")
    connection = FakeConnection(ddl_error=Exception("copy rejected"))
    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.FAIL_DDL
    assert result.error == "copy rejected"
    assert connection.executed[-2] in case.cleanup_sql


def test_execute_case_passes_expected_reject() -> None:
    case = _case("reject")
    connection = FakeConnection(ddl_error=Exception("expected reject"))
    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.PASS
    assert result.error == "expected reject"


def test_execute_case_fails_when_expected_reject_succeeds() -> None:
    case = _case("reject")
    connection = FakeConnection()
    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.FAIL_DDL
    assert result.error == "expected reject, but DDL succeeded"


def test_execute_case_fails_when_oracle_returns_fail() -> None:
    case = _case("success")
    connection = FakeConnection(check_value="FAIL", invalid_statements=set(case.invalid_post_ddl_sql))
    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.FAIL_ORACLE
    assert "verification" in result.error


def test_execute_case_fails_when_invalid_post_ddl_succeeds() -> None:
    case = _case("success")
    object.__setattr__(case, "invalid_post_ddl_sql", ("INSERT INTO should_fail VALUES (1)",))
    connection = FakeConnection()
    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.FAIL_POST_DML
    assert "invalid" in result.error


def test_result_json_round_trip() -> None:
    case = _case("success")
    result = execute_case(case, FakeConnection(invalid_statements=set(case.invalid_post_ddl_sql)), "copy")
    payload = json.loads(json.dumps(result.to_json()))
    assert payload["case_id"] == case.case_id
    assert payload["outcome"] == "PASS"


def test_execute_case_keeps_strict_mode_when_adding_non_strict_sql_mode() -> None:
    case = _case("success")
    object.__setattr__(case, "sql_mode", "NO_BACKSLASH_ESCAPES")
    object.__setattr__(case, "invalid_post_ddl_sql", ("INSERT INTO should_fail VALUES (1)",))
    connection = FakeConnection(invalid_statements={"INSERT INTO should_fail VALUES (1)"})
    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.PASS
    assert "SET SESSION sql_mode='STRICT_ALL_TABLES,NO_BACKSLASH_ESCAPES'" in connection.executed


def test_load_cases_supports_deterministic_gzip_cases(tmp_path: Path) -> None:
    import gzip

    from mysql_case_factory.type_upgrade_consistency import generate_cases
    from mysql_case_factory.type_upgrade_runner import _load_cases

    case = generate_cases()[0]
    path = tmp_path / "cases.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(case.to_json()) + "\n")
    loaded = _load_cases(path)
    assert list(loaded) == [case.case_id]
    assert loaded[case.case_id] == case


def test_summary_markdown_reports_full_run_and_counts() -> None:
    from mysql_case_factory.type_upgrade_runner import render_summary_markdown

    summary = {
        "profile": "copy",
        "selected_count": 3,
        "executed_count": 3,
        "counts": {"PASS": 3},
        "all_pass": True,
        "stopped_early": False,
        "mysqld_version": "8.0.45",
    }
    markdown = render_summary_markdown(summary)
    assert "# MySQL type-upgrade COPY local verification" in markdown
    assert "**Result:** ALL PASS" in markdown
    assert "**Selected cases:** 3" in markdown
    assert "**Executed cases:** 3" in markdown
    assert "**MySQL version:** 8.0.45" in markdown


def test_connection_loss_is_fail_crash_even_when_reject_was_expected() -> None:
    case = _case("reject")
    connection = FakeConnection(ddl_error=Exception("(2013, 'Lost connection to MySQL server during query')"))
    result = execute_case(case, connection, "copy")
    assert result.outcome is CaseOutcome.FAIL_CRASH
    assert result.errno == 2013


def test_execute_case_does_not_swallow_keyboard_interrupt() -> None:
    case = _case("success")

    class InterruptingConnection(FakeConnection):
        def execute(self, sql: str) -> None:
            if sql.startswith("ALTER TABLE"):
                raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execute_case(case, InterruptingConnection(), "copy")


def test_select_cases_rejects_empty_unknown_and_invalid_limit() -> None:
    from mysql_case_factory.type_upgrade_runner import select_cases

    cases = {_case("success").case_id: _case("success")}
    with pytest.raises(ValueError, match="case input is empty"):
        select_cases({}, None, None)
    with pytest.raises(ValueError, match="Unknown case IDs"):
        select_cases(cases, {"NO_SUCH_CASE"}, None)
    with pytest.raises(ValueError, match="limit must be a positive integer"):
        select_cases(cases, None, 0)
    with pytest.raises(ValueError, match="limit must be a positive integer"):
        select_cases(cases, None, -1)
    assert select_cases(cases, None, 1) == list(cases.values())


def test_verify_case_artifacts_checks_manifest_hash_and_count() -> None:
    from mysql_case_factory.type_upgrade_runner import verify_case_artifacts

    cases_path = Path(__file__).parents[1] / "generated" / "type_upgrade_consistency" / "cases.jsonl.gz"
    metadata = verify_case_artifacts(cases_path)
    assert metadata["case_count"] > 0
    assert metadata["case_manifest_sha256"]
    assert metadata["cases_artifact_sha256"]


def test_case_results_include_new_merge_batch_id() -> None:
    case = _case("success")
    connection = FakeConnection(invalid_statements=set(case.invalid_post_ddl_sql))
    result = execute_case(case, connection, "copy")

    assert result.batch_id == "2026-10-13-type-upgrade-consistency"
    assert result.batch_kind == "new_merge"
    payload = json.loads(json.dumps(result.to_json()))
    assert payload["batch_id"] == "2026-10-13-type-upgrade-consistency"
    assert payload["batch_kind"] == "new_merge"
