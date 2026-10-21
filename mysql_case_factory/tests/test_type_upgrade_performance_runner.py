from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mysql_case_factory.type_upgrade_performance import type_performance_scenarios
from mysql_case_factory.type_upgrade_performance_runner import (
    build_arg_parser,
    classify_performance_execution,
    select_scenarios,
)


def test_classification_passes_source_and_reference_without_ddl() -> None:
    for scenario in ("source_baseline", "reference"):
        assert (
            classify_performance_execution(
                scenario=scenario,
                ddl_succeeded=True,
                ddl_error=None,
                aggregate_match=None,
            )
            == "PASS"
        )


def test_classification_passes_successful_ddl_with_matching_aggregates() -> None:
    assert (
        classify_performance_execution(
            scenario="all_inplace",
            ddl_succeeded=True,
            ddl_error=None,
            aggregate_match=True,
        )
        == "PASS"
    )


def test_classification_fails_ddl() -> None:
    assert (
        classify_performance_execution(
            scenario="all_instant",
            ddl_succeeded=False,
            ddl_error="ERROR 1846 unsupported",
            aggregate_match=None,
        )
        == "FAIL_DDL"
    )


def test_classification_fails_data_mismatch() -> None:
    assert (
        classify_performance_execution(
            scenario="mixed_inplace_first",
            ddl_succeeded=True,
            ddl_error=None,
            aggregate_match=False,
        )
        == "FAIL_DATA"
    )


def test_classification_detects_crash() -> None:
    assert (
        classify_performance_execution(
            scenario="all_inplace",
            ddl_succeeded=False,
            ddl_error="Lost connection to MySQL server",
            aggregate_match=None,
        )
        == "FAIL_CRASH"
    )


def test_selection_is_deterministic_and_rejects_unknown_scenarios() -> None:
    selected = select_scenarios(all_scenarios=True)
    assert [scenario.case_id for scenario in selected] == [
        scenario.case_id for scenario in type_performance_scenarios()
    ]

    chosen = select_scenarios(scenario_names={"source_baseline", "reference"})
    assert [scenario.scenario for scenario in chosen] == ["source_baseline", "reference"]

    with pytest.raises(ValueError, match="Unknown scenarios: not_a_scenario"):
        select_scenarios(scenario_names={"not_a_scenario"})


def test_cli_parser_supports_performance_options() -> None:
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
            "TYPE_PERFORMANCE_MYSQL_PASSWORD",
            "--rows",
            "0",
            "--calibration-rows",
            "100000",
            "--target-scan-seconds",
            "300",
            "--max-rows",
            "20000000",
            "--dml-rows",
            "100000",
            "--external",
        ]
    )
    assert args.all is True
    assert args.rows == 0
    assert args.calibration_rows == 100_000
    assert args.target_scan_seconds == 300.0
    assert args.max_rows == 20_000_000
    assert args.dml_rows == 100_000
    assert args.external is True
    assert args.password_env == "TYPE_PERFORMANCE_MYSQL_PASSWORD"


def test_cli_help_runs_without_database_or_credentials() -> None:
    tool = Path(__file__).parents[1] / "tools" / "run_type_upgrade_performance.py"
    completed = subprocess.run(
        [sys.executable, str(tool), "--help"],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[1],
    )
    for option in (
        "--all",
        "--scenario",
        "--results",
        "--summary",
        "--host",
        "--port",
        "--user",
        "--password-env",
        "--rows",
        "--calibration-rows",
        "--target-scan-seconds",
        "--max-rows",
        "--dml-rows",
        "--external",
    ):
        assert option in completed.stdout


@pytest.mark.skipif(
    os.environ.get("MYSQL_CASE_FACTORY_TUCPF_SMOKE") != "1",
    reason="set MYSQL_CASE_FACTORY_TUCPF_SMOKE=1 to run an authorized database smoke test",
)
def test_authorized_external_smoke_run(tmp_path: Path) -> None:
    password_env = os.environ.get("MYSQL_CASE_FACTORY_TUCPF_PASSWORD_ENV")
    command = [
        sys.executable,
        str(Path(__file__).parents[1] / "tools" / "run_type_upgrade_performance.py"),
        "--scenario",
        "source_baseline",
        "--scenario",
        "all_inplace",
        "--scenario",
        "reference",
        "--external",
        "--host",
        os.environ.get("MYSQL_CASE_FACTORY_TUCPF_HOST", "127.0.0.1"),
        "--port",
        os.environ.get("MYSQL_CASE_FACTORY_TUCPF_PORT", "3306"),
        "--user",
        os.environ.get("MYSQL_CASE_FACTORY_TUCPF_USER", "root"),
        "--results",
        str(tmp_path / "results.jsonl"),
        "--summary",
        str(tmp_path / "summary.json"),
        "--rows",
        os.environ.get("MYSQL_CASE_FACTORY_TUCPF_ROWS", "1000"),
        "--dml-rows",
        os.environ.get("MYSQL_CASE_FACTORY_TUCPF_DML_ROWS", "100"),
    ]
    if password_env:
        command.extend(["--password-env", password_env])
    subprocess.run(command, check=True, cwd=Path(__file__).parents[1])

    results = [
        json.loads(line)
        for line in (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(results) == 3
    assert all(result["classification"] == "PASS" for result in results)

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["all_pass"] is True
    assert (tmp_path / "summary.md").exists()
