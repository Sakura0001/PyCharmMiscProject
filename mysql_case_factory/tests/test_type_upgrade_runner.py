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
        explain_value: str = '{"query_block":{"table":{"key":"idx_target"}}}',
        invalid_statements: set[str] | None = None,
    ) -> None:
        self.executed: list[str] = []
        self.ddl_error = ddl_error
        self.check_value = check_value
        self.explain_value = explain_value
        self.invalid_statements = invalid_statements or set()

    def execute(self, sql: str) -> None:
        self.executed.append(sql)
        if sql in self.invalid_statements:
            raise Exception("invalid value rejected")
        if sql.startswith("ALTER TABLE") and self.ddl_error is not None:
            raise self.ddl_error

    def fetchone(self) -> tuple[str]:
        if self.executed and self.executed[-1].startswith("EXPLAIN"):
            return (self.explain_value,)
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


def test_verify_case_artifacts_accepts_extension_batch(tmp_path: Path) -> None:
    import subprocess
    import sys

    from mysql_case_factory.type_upgrade_extension import EXTENSION_BATCH_ID, EXTENSION_BATCH_KIND, PARENT_BATCH_ID

    output = tmp_path / "type_upgrade_consistency_extension_v1"
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_extension.py"
    subprocess.run([sys.executable, str(tool), "--output", str(output)], check=True)
    from mysql_case_factory.type_upgrade_runner import verify_case_artifacts

    metadata = verify_case_artifacts(output / "cases.jsonl.gz")

    assert metadata["batch_id"] == EXTENSION_BATCH_ID
    assert metadata["batch_kind"] == EXTENSION_BATCH_KIND
    assert metadata["parent_batch_id"] == PARENT_BATCH_ID
    assert metadata["case_count"] > 0


def test_local_mysql_server_cleans_owned_directory_when_startup_fails() -> None:
    from mysql_case_factory.type_upgrade_runner import LocalMySQLServer

    server = LocalMySQLServer(mysqld="/opt/homebrew/opt/mysql@8.0/bin/mysqld")
    server.data_dir.write_text("not a directory", encoding="utf-8")

    with pytest.raises(FileExistsError):
        server.start()

    assert not server.base_dir.exists()


def test_execute_case_parses_nested_explain_json_key() -> None:
    case = _case("success")
    object.__setattr__(
        case,
        "query_plans",
        (("EXPLAIN FORMAT=JSON SELECT 1", "idx_target"),),
    )
    connection = FakeConnection(
        explain_value='{"query_block":{"table":{"key":"idx_target","rows_examined_per_scan":1,"rows_produced_per_join":1}}}',
        invalid_statements=set(case.invalid_post_ddl_sql),
    )
    result = execute_case(case, connection, "copy")
    assert result.outcome is CaseOutcome.PASS


def test_execute_case_runs_pre_ddl_stats_and_analyze_in_order() -> None:
    case = _case("success")
    object.__setattr__(case, "pre_ddl_sql", ("ALTER TABLE chain MODIFY c INT",))
    object.__setattr__(case, "stats_pre_analyze_sql", ("SELECT 'PRE_STATS_OK'",))
    object.__setattr__(case, "analyze_sql", ("ANALYZE TABLE chain",))
    object.__setattr__(case, "stats_post_analyze_sql", ("SELECT 'POST_STATS_OK'",))
    object.__setattr__(case, "invalid_post_ddl_sql", ())
    connection = FakeConnection()

    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.PASS
    order = {
        "pre": connection.executed.index("ALTER TABLE chain MODIFY c INT"),
        "ddl": connection.executed.index(case.ddl_sql.replace("${ALGORITHM}", "COPY")),
        "pre_stats": connection.executed.index("SELECT 'PRE_STATS_OK'"),
        "analyze": connection.executed.index("ANALYZE TABLE chain"),
        "post_stats": connection.executed.index("SELECT 'POST_STATS_OK'"),
    }
    assert order["pre"] < order["ddl"] < order["pre_stats"] < order["analyze"] < order["post_stats"]


def test_execute_case_classifies_pre_ddl_failure_as_ddl_failure() -> None:
    case = _case("success")
    object.__setattr__(case, "pre_ddl_sql", ("ALTER TABLE chain MODIFY c INT",))
    object.__setattr__(case, "invalid_post_ddl_sql", ())
    connection = FakeConnection(ddl_error=Exception("pre-ddl rejected"))

    result = execute_case(case, connection, "copy")

    assert result.outcome is CaseOutcome.FAIL_DDL
    assert result.error == "pre-ddl rejected"


def test_case_json_and_suite_include_new_phase_fields() -> None:
    from mysql_case_factory.type_upgrade_consistency import render_suite

    case = _case("success")
    object.__setattr__(case, "pre_ddl_sql", ("ALTER TABLE chain MODIFY c INT",))
    object.__setattr__(case, "stats_pre_analyze_sql", ("SELECT 'PRE_STATS_OK'",))
    object.__setattr__(case, "analyze_sql", ("ANALYZE TABLE chain",))
    object.__setattr__(case, "stats_post_analyze_sql", ("SELECT 'POST_STATS_OK'",))

    payload = case.to_json()
    assert payload["pre_ddl_sql"] == ["ALTER TABLE chain MODIFY c INT"]
    assert payload["stats_pre_analyze_sql"] == ["SELECT 'PRE_STATS_OK'"]
    assert payload["analyze_sql"] == ["ANALYZE TABLE chain"]
    assert payload["stats_post_analyze_sql"] == ["SELECT 'POST_STATS_OK'"]

    suite = render_suite([case], "copy")
    assert "ALTER TABLE chain MODIFY c INT" in suite
    assert "SELECT 'PRE_STATS_OK'" in suite
    assert "ANALYZE TABLE chain" in suite
    assert "SELECT 'POST_STATS_OK'" in suite


def test_execute_case_requires_positive_explain_row_estimates() -> None:
    case = _case("success")
    object.__setattr__(
        case,
        "query_plans",
        (("EXPLAIN FORMAT=JSON SELECT 1", "idx_target"),),
    )
    connection = FakeConnection(
        explain_value='{"query_block":{"table":{"key":"idx_target","rows_examined_per_scan":0,"rows_produced_per_join":0}}}',
        invalid_statements=set(case.invalid_post_ddl_sql),
    )
    result = execute_case(case, connection, "copy")
    assert result.outcome is CaseOutcome.FAIL_ORACLE
    assert "positive EXPLAIN row estimates" in result.error


def test_connection_loss_during_setup_is_fail_crash() -> None:
    case = _case("success")

    class SetupLossConnection(FakeConnection):
        def execute(self, sql: str) -> None:
            if sql.startswith("DROP TABLE"):
                raise Exception("(2013, 'Lost connection to MySQL server during query')")
            super().execute(sql)

    result = execute_case(case, SetupLossConnection(), "copy")
    assert result.outcome is CaseOutcome.FAIL_CRASH
    assert result.errno == 2013


def test_connection_loss_during_cleanup_is_fail_crash() -> None:
    case = _case("success")

    class CleanupLossConnection(FakeConnection):
        def __init__(self) -> None:
            super().__init__(invalid_statements=set(case.invalid_post_ddl_sql))

        def execute(self, sql: str) -> None:
            if sql.startswith("SET SESSION sql_mode=DEFAULT"):
                raise Exception("(2013, 'Lost connection to MySQL server during query')")
            super().execute(sql)

    result = execute_case(case, CleanupLossConnection(), "copy")
    assert result.outcome is CaseOutcome.FAIL_CRASH
    assert result.errno == 2013


def test_verify_case_artifacts_validates_every_profile_hash_and_identity(tmp_path: Path) -> None:
    import shutil

    import pytest

    from mysql_case_factory.type_upgrade_statistics import STATISTICS_BATCH_ID
    from mysql_case_factory.type_upgrade_runner import verify_case_artifacts

    source = Path(__file__).parents[1] / "generated" / "type_upgrade_statistics_v1"
    copied = tmp_path / "statistics"
    shutil.copytree(source, copied)
    manifest_path = copied / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["profiles"]["inplace"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="profile SHA-256 does not match cases payload: inplace"):
        verify_case_artifacts(copied / "cases.jsonl.gz")
