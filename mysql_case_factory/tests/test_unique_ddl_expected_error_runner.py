from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mysql_case_factory.unique_ddl_expected_error import smoke_unique_ddl_error_scenarios
from mysql_case_factory.unique_ddl_expected_error_runner import (
    build_arg_parser,
    classify_scenario_execution,
    select_scenarios,
)


def test_classification_requires_overlap_ddl_1062_and_successful_dml() -> None:
    assert (
        classify_scenario_execution(
            overlap=True,
            ddl_succeeded=False,
            ddl_error_code=1062,
            ddl_error="(1062, Duplicate entry)",
            dml_succeeded=True,
        )
        == "PASS"
    )


def test_classification_rejects_missing_overlap() -> None:
    assert (
        classify_scenario_execution(
            overlap=False,
            ddl_succeeded=False,
            ddl_error_code=1062,
            ddl_error="(1062, Duplicate entry)",
            dml_succeeded=True,
        )
        == "NO_OVERLAP"
    )


def test_classification_rejects_unexpected_ddl_success() -> None:
    assert (
        classify_scenario_execution(
            overlap=True,
            ddl_succeeded=True,
            ddl_error_code=None,
            ddl_error=None,
            dml_succeeded=True,
        )
        == "FAIL_DDL_SUCCESS"
    )


def test_classification_accepts_1062_and_1859_duplicate_errors() -> None:
    for code in (1062, 1859):
        assert (
            classify_scenario_execution(
                overlap=True,
                ddl_succeeded=False,
                ddl_error_code=code,
                ddl_error=f"({code}, Duplicate entry)",
                dml_succeeded=True,
            )
            == "PASS"
        )


def test_classification_rejects_non_duplicate_ddl_error() -> None:
    assert (
        classify_scenario_execution(
            overlap=True,
            ddl_succeeded=False,
            ddl_error_code=1846,
            ddl_error="(1846, unsupported)",
            dml_succeeded=True,
        )
        == "FAIL_DDL_ERROR"
    )


def test_classification_rejects_failed_dml() -> None:
    assert (
        classify_scenario_execution(
            overlap=True,
            ddl_succeeded=False,
            ddl_error_code=1062,
            ddl_error="(1062, Duplicate entry)",
            dml_succeeded=False,
        )
        == "FAIL_DML"
    )


def test_classification_detects_crash() -> None:
    assert (
        classify_scenario_execution(
            overlap=True,
            ddl_succeeded=False,
            ddl_error_code=2013,
            ddl_error="Lost connection to MySQL server",
            dml_succeeded=True,
        )
        == "FAIL_CRASH"
    )


def test_selection_is_deterministic_and_rejects_unknown_ids() -> None:
    smoke = select_scenarios(smoke=True)
    assert [case.case_id for case in smoke] == [
        case.case_id for case in smoke_unique_ddl_error_scenarios()
    ]

    selected = select_scenarios(case_ids={"TUCUD-000001", "TUCUD-000192"})
    assert [case.case_id for case in selected] == ["TUCUD-000001", "TUCUD-000192"]

    with pytest.raises(ValueError, match="Unknown case IDs: TUCUD-999999"):
        select_scenarios(case_ids={"TUCUD-999999"})


def test_cli_parser_supports_safe_execution_options() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--all",
            "--results",
            "results.jsonl",
            "--summary",
            "summary.json",
            "--host",
            "127.0.0.1",
            "--port",
            "3306",
            "--user",
            "tester",
            "--password-env",
            "UNIQUE_DDL_MYSQL_PASSWORD",
            "--rows",
            "250000",
            "--dml-delay",
            "0.1",
            "--external",
        ]
    )
    assert args.all is True
    assert args.rows == 250_000
    assert args.dml_delay == 0.1
    assert args.external is True
    assert args.password_env == "UNIQUE_DDL_MYSQL_PASSWORD"


def test_cli_help_runs_without_database_or_credentials() -> None:
    tool = Path(__file__).parents[1] / "tools" / "run_unique_ddl_expected_error.py"
    completed = subprocess.run(
        [sys.executable, str(tool), "--help"],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[1],
    )
    for option in (
        "--smoke",
        "--all",
        "--case-id",
        "--results",
        "--summary",
        "--host",
        "--port",
        "--user",
        "--password-env",
        "--rows",
        "--dml-delay",
        "--external",
    ):
        assert option in completed.stdout


@pytest.mark.skipif(
    os.environ.get("MYSQL_CASE_FACTORY_TUCUD_SMOKE") != "1",
    reason="set MYSQL_CASE_FACTORY_TUCUD_SMOKE=1 to run an authorized database smoke test",
)
def test_authorized_external_smoke_run(tmp_path: Path) -> None:
    password_env = os.environ.get("MYSQL_CASE_FACTORY_TUCUD_PASSWORD_ENV")
    command = [
        sys.executable,
        str(Path(__file__).parents[1] / "tools" / "run_unique_ddl_expected_error.py"),
        "--smoke",
        "--external",
        "--host",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUD_HOST", "127.0.0.1"),
        "--port",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUD_PORT", "3306"),
        "--user",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUD_USER", "root"),
        "--results",
        str(tmp_path / "results.jsonl"),
        "--summary",
        str(tmp_path / "summary.json"),
        "--rows",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUD_ROWS", "100000"),
        "--dml-delay",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUD_DML_DELAY", "0.05"),
    ]
    if password_env:
        command.extend(["--password-env", password_env])
    subprocess.run(command, check=True, cwd=Path(__file__).parents[1])

    results = [
        json.loads(line)
        for line in (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(results) == 6
    assert all(result["classification"] == "PASS" for result in results)
    assert all(result["overlap"] is True for result in results)
    assert all(result["ddl_error_code"] == 1062 for result in results)

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["all_pass"] is True
    assert (tmp_path / "summary.md").exists()
