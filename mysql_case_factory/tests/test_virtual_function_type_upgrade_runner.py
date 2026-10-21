from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mysql_case_factory.virtual_function_type_upgrade import smoke_virtual_function_scenarios
from mysql_case_factory.virtual_function_type_upgrade_runner import (
    build_arg_parser,
    classify_virtual_function_execution,
    seed_values,
    select_scenarios,
)


def test_classification_passes_when_candidate_matches_control_and_data() -> None:
    assert (
        classify_virtual_function_execution(
            control_succeeded=True,
            candidate_succeeded=True,
            control_error=None,
            candidate_error=None,
            data_match=True,
            unchanged_match=None,
        )
        == "PASS"
    )


def test_classification_passes_when_candidate_and_control_both_fail_unchanged() -> None:
    assert (
        classify_virtual_function_execution(
            control_succeeded=False,
            candidate_succeeded=False,
            control_error="ERROR 1846",
            candidate_error="ERROR 1846",
            data_match=None,
            unchanged_match=True,
        )
        == "PASS"
    )


def test_classification_fails_on_algorithm_change() -> None:
    assert (
        classify_virtual_function_execution(
            control_succeeded=True,
            candidate_succeeded=False,
            control_error=None,
            candidate_error="ERROR 1846",
            data_match=None,
            unchanged_match=True,
        )
        == "FAIL_ALGORITHM"
    )


def test_classification_fails_on_data_mismatch() -> None:
    assert (
        classify_virtual_function_execution(
            control_succeeded=True,
            candidate_succeeded=True,
            control_error=None,
            candidate_error=None,
            data_match=False,
            unchanged_match=None,
        )
        == "FAIL_DATA"
    )


def test_classification_fails_when_rejected_ddl_changes_data() -> None:
    assert (
        classify_virtual_function_execution(
            control_succeeded=False,
            candidate_succeeded=False,
            control_error="ERROR 1846",
            candidate_error="ERROR 1846",
            data_match=None,
            unchanged_match=False,
        )
        == "FAIL_UNCHANGED"
    )


def test_seed_values_cover_normal_and_boundary_states() -> None:
    assert seed_values("integer", "TINYINT", "normal") == [0, 1, 2, 3, 4, 5, 6, 7]
    boundary = seed_values("integer", "TINYINT", "boundary")
    assert -128 in boundary and 127 in boundary

    decimal_boundary = seed_values("decimal", "DECIMAL(10,2)", "boundary")
    assert "-99999999.99" in decimal_boundary and "99999999.99" in decimal_boundary

    character_boundary = seed_values("character", "VARCHAR(10)", "boundary")
    assert "" in character_boundary and "aaaaaaaaaa" in character_boundary

    binary_boundary = seed_values("binary", "VARBINARY(10)", "boundary")
    assert b"" in binary_boundary and b"\xff" * 10 in binary_boundary


def test_selection_is_deterministic_and_profile_filtered() -> None:
    smoke = select_scenarios(smoke=True)
    assert [case.case_id for case in smoke] == [
        case.case_id for case in smoke_virtual_function_scenarios()
    ]

    copy_smoke = select_scenarios(smoke=True, profile="copy")
    assert len(copy_smoke) == 28
    assert all(case.algorithm == "copy" for case in copy_smoke)

    selected = select_scenarios(case_ids={"TUCVF-000001", "TUCVF-005136"})
    assert [case.case_id for case in selected] == ["TUCVF-000001", "TUCVF-005136"]

    with pytest.raises(ValueError, match="Unknown case IDs: TUCVF-999999"):
        select_scenarios(case_ids={"TUCVF-999999"})


def test_cli_parser_supports_safe_execution_options() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--profile",
            "inplace",
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
            "VIRTUAL_FUNCTION_MYSQL_PASSWORD",
            "--external",
        ]
    )
    assert args.profile == "inplace"
    assert args.all is True
    assert args.external is True
    assert args.password_env == "VIRTUAL_FUNCTION_MYSQL_PASSWORD"


def test_cli_help_runs_without_database_or_credentials() -> None:
    tool = Path(__file__).parents[1] / "tools" / "run_virtual_function_type_upgrade.py"
    completed = subprocess.run(
        [sys.executable, str(tool), "--help"],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[1],
    )
    for option in (
        "--profile",
        "--smoke",
        "--all",
        "--case-id",
        "--results",
        "--summary",
        "--host",
        "--port",
        "--user",
        "--password-env",
        "--external",
    ):
        assert option in completed.stdout


@pytest.mark.skipif(
    os.environ.get("MYSQL_CASE_FACTORY_TUCVF_SMOKE") != "1",
    reason="set MYSQL_CASE_FACTORY_TUCVF_SMOKE=1 to run an authorized database smoke test",
)
def test_authorized_external_smoke_run(tmp_path: Path) -> None:
    password_env = os.environ.get("MYSQL_CASE_FACTORY_TUCVF_PASSWORD_ENV")
    command = [
        sys.executable,
        str(Path(__file__).parents[1] / "tools" / "run_virtual_function_type_upgrade.py"),
        "--profile",
        os.environ.get("MYSQL_CASE_FACTORY_TUCVF_PROFILE", "copy"),
        "--smoke",
        "--external",
        "--host",
        os.environ.get("MYSQL_CASE_FACTORY_TUCVF_HOST", "127.0.0.1"),
        "--port",
        os.environ.get("MYSQL_CASE_FACTORY_TUCVF_PORT", "3306"),
        "--user",
        os.environ.get("MYSQL_CASE_FACTORY_TUCVF_USER", "root"),
        "--results",
        str(tmp_path / "results.jsonl"),
        "--summary",
        str(tmp_path / "summary.json"),
    ]
    if password_env:
        command.extend(["--password-env", password_env])
    subprocess.run(command, check=True, cwd=Path(__file__).parents[1])

    results = [
        json.loads(line)
        for line in (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(results) == 28
    assert all(result["classification"] == "PASS" for result in results)

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["all_pass"] is True
    assert (tmp_path / "summary.md").exists()
