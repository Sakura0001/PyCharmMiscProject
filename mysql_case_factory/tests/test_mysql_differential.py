from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from mysql_case_factory.differential import (
    EndpointIdentity,
    MysqlRunner,
    MysqlTarget,
    execute_differential,
    parse_mysql_version_num,
    parse_verbose_terminal_diagnostics,
    validate_basic_endpoint_identity,
    validate_comparable_endpoint_pair,
    validate_endpoint_identity,
    validate_expected_failure_oracle,
)


UUID_1 = "11111111-1111-1111-1111-111111111111"
UUID_2 = "22222222-2222-2222-2222-222222222222"


def identity(
    name: str,
    uuid: str,
    *,
    version: str = "8.0.22",
    privileges: tuple[str, ...] = (),
) -> EndpointIdentity:
    return EndpointIdentity(
        target_name=name,
        login_path=f"{name}_login",
        database="regression",
        server_version=version,
        server_version_num=parse_mysql_version_num(version),
        server_uuid=uuid,
        server_hostname=f"{name}-host",
        server_port=3306,
        current_user="regression_user@%",
        version_comment="MySQL Community Server - GPL",
        granted_global_privileges=privileges,
    )


@pytest.mark.parametrize(
    ("version", "number"),
    [
        ("8.0.22", 80022),
        ("8.0.22-commercial", 80022),
        ("8.0.41-custom-build", 80041),
    ],
)
def test_parses_exact_mysql_patch_prefix(version: str, number: int) -> None:
    assert parse_mysql_version_num(version) == number


@pytest.mark.parametrize("version", ["8.0", "mysql-8.0.41", "8.0.41.1", "", "9.0.1"])
def test_rejects_non_8_0_patch_versions(version: str) -> None:
    with pytest.raises(ValueError, match="MySQL 8.0 patch"):
        parse_mysql_version_num(version)


def test_target_accepts_only_bare_login_path_and_database() -> None:
    assert MysqlTarget("reference", "mysql8022_reference", "regression").login_path == "mysql8022_reference"
    with pytest.raises(ValueError, match="login_path"):
        MysqlTarget("reference", "--password=secret", "regression")
    with pytest.raises(ValueError, match="database"):
        MysqlTarget("reference", "safe", "mysql://user:secret@host/db")


def test_identity_is_bound_to_requested_patch() -> None:
    validate_endpoint_identity(identity("reference", UUID_1), expected_version_num=80022)
    with pytest.raises(ValueError, match="expected 80041"):
        validate_endpoint_identity(identity("reference", UUID_1), expected_version_num=80041)


def test_basic_identity_rejects_dangerous_global_privileges() -> None:
    with pytest.raises(ValueError, match="over-privileged.*FILE.*SYSTEM_USER"):
        validate_basic_endpoint_identity(
            identity("reference", UUID_1, privileges=("FILE", "SYSTEM_USER")),
            expected_version_num=80022,
        )


def test_pair_requires_distinct_uuid_same_patch_database_and_user() -> None:
    reference = identity("reference", UUID_1)
    dut = identity("dut", UUID_2)
    validate_comparable_endpoint_pair(reference, dut, expected_version_num=80022)
    with pytest.raises(ValueError, match="same MySQL server UUID"):
        validate_comparable_endpoint_pair(reference, identity("dut", UUID_1), expected_version_num=80022)
    with pytest.raises(ValueError, match="expected 80022"):
        validate_comparable_endpoint_pair(
            reference,
            identity("dut", UUID_2, version="8.0.41"),
            expected_version_num=80022,
        )


def test_parses_one_mysql_terminal_sqlstate() -> None:
    stderr = "ERROR 1064 (42000) at line 1: You have an error in your SQL syntax\n"
    assert parse_verbose_terminal_diagnostics(stderr) == (("ERROR", "42000"),)
    assert validate_expected_failure_oracle(1, stderr, "42000") == (True, None)


def test_warning_does_not_satisfy_expected_failure_oracle() -> None:
    valid, reason = validate_expected_failure_oracle(
        1,
        "Warning (Code 1064): text containing 42000\n",
        "42000",
    )
    assert valid is False
    assert "exactly one" in reason


def test_mysql_runner_inspect_uses_login_path_without_credentials() -> None:
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            "8.0.22\t11111111-1111-1111-1111-111111111111\tref-host\t3306\t"
            "regression_user@%\tMySQL Community Server - GPL\t[]\n"
        ),
        stderr="",
    )
    target = MysqlTarget("reference", "mysql8022_reference", "regression")
    with patch("mysql_case_factory.differential.shutil.which", return_value="/usr/bin/mysql"), patch(
        "mysql_case_factory.differential.subprocess.run", return_value=completed
    ) as run:
        inspected = MysqlRunner(expected_version_num=80022).inspect(target)

    command = run.call_args.args[0]
    assert "--login-path=mysql8022_reference" in command
    assert "--database=regression" in command
    assert not any("password" in part.lower() or "secret" in part.lower() for part in command)
    assert inspected.server_uuid == UUID_1
    assert inspected.server_version_num == 80022


def test_runner_executes_utf8_sql_and_strips_owned_identity_row(tmp_path: Path) -> None:
    sql = tmp_path / "case.sql"
    sql.write_text("SELECT '中文';\n", encoding="utf-8")
    session_row = (
        '__MYSQL_CASE_FACTORY_ENDPOINT_V1__'
        '{"server_version":"8.0.22","server_uuid":"11111111-1111-1111-1111-111111111111",'
        '"server_hostname":"ref-host","server_port":3306,"current_user":"regression_user@%",'
        '"version_comment":"MySQL Community Server - GPL","granted_global_privileges":[]}\n'
        "中文\n"
    )
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=session_row, stderr="")
    target = MysqlTarget("reference", "mysql8022_reference", "regression")
    with patch("mysql_case_factory.differential.shutil.which", return_value="/usr/bin/mysql"), patch(
        "mysql_case_factory.differential.subprocess.run", return_value=completed
    ) as run:
        record = MysqlRunner(expected_version_num=80022).run(sql, target)

    command = run.call_args.args[0]
    assert {"--batch", "--raw", "--skip-column-names", "--show-warnings"}.issubset(command)
    assert record.stdout == "中文\n"
    assert record.endpoint_identity["server_uuid"] == UUID_1
    assert "SELECT '中文';" in run.call_args.kwargs["input"]


def test_execute_differential_passes_expected_patch_to_pair_validation(tmp_path: Path) -> None:
    sql = tmp_path / "case.sql"
    sql.write_text("SELECT 1;\n", encoding="utf-8")

    class Runner:
        def inspect(self, target: MysqlTarget) -> EndpointIdentity:
            uuid = UUID_1 if target.name == "reference" else UUID_2
            return identity(target.name, uuid, version="8.0.41")

        def run(self, sql_path: Path, target: MysqlTarget, *, stop_on_error: bool = True):
            from mysql_case_factory.differential import ExecutionRecord

            return ExecutionRecord(target.name, str(sql_path), 0, "1\n", "", 0.01)

    result = execute_differential(
        sql,
        MysqlTarget("reference", "ref", "regression"),
        MysqlTarget("dut", "dut", "regression"),
        runner=Runner(),
        expected_version_num=80041,
        expected_outcome="success",
    )
    assert result.passed is True
