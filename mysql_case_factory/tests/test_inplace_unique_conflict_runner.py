from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mysql_case_factory.inplace_unique_conflict import (
    INPLACE_UNIQUE_PROFILES,
    iter_inplace_unique_scenarios,
    smoke_inplace_unique_scenarios,
)
from mysql_case_factory.inplace_unique_conflict_runner import (
    build_arg_parser,
    build_create_table_sql,
    build_seed_values,
    classify_ddl_execution,
    duplicate_insert_sql,
    expected_object_state,
    make_run_namespace,
    render_profile_ddl,
    render_summary_markdown,
    select_scenarios,
)

PROJECT_ROOT = Path(__file__).parents[1]
TOOL = PROJECT_ROOT / "tools" / "run_inplace_unique_conflict.py"


def test_profile_ddl_rendering_is_exact() -> None:
    canonical = (
        "ALTER TABLE `tucui_unique_target`\n"
        "  ADD INDEX `idx_tucui_value` (`value`),\n"
        "  ALGORITHM=INPLACE,\n"
        "  LOCK=NONE;\n"
    )
    assert render_profile_ddl(canonical, "copy") == (
        "ALTER TABLE `tucui_unique_target`\n"
        "  ADD INDEX `idx_tucui_value` (`value`),\n"
        "  ALGORITHM=COPY,\n"
        "  LOCK=SHARED;\n"
    )
    assert render_profile_ddl(canonical, "inplace") == canonical
    assert render_profile_ddl(canonical, "instant") == (
        "ALTER TABLE `tucui_unique_target`\n"
        "  ADD INDEX `idx_tucui_value` (`value`),\n"
        "  ALGORITHM=INSTANT;\n"
    )


def test_instant_expected_rejects_are_limited_to_non_instant_operations() -> None:
    instant_supported = {
        "add_column",
        "drop_column",
        "rename_column",
        "drop_check",
        "drop_generated",
    }
    for operation_id in {
        "add_index",
        "drop_index",
        "add_unique",
        "drop_unique",
        "rename_index",
        "add_column",
        "drop_column",
        "rename_column",
        "add_foreign_key",
        "drop_foreign_key",
        "drop_check",
        "drop_generated",
    }:
        assert classify_ddl_execution(operation_id, "copy", True) == "PASS"
        assert classify_ddl_execution(operation_id, "inplace", True) == "PASS"
        if operation_id in instant_supported:
            assert classify_ddl_execution(operation_id, "instant", True) == "PASS"
            assert classify_ddl_execution(operation_id, "instant", False, "reject") == "FAIL_DDL"
        else:
            assert classify_ddl_execution(operation_id, "instant", False, "reject") == "EXPECTED_REJECT"
            assert classify_ddl_execution(operation_id, "instant", True) == "FAIL_DDL"


def test_ddl_connection_loss_is_crash_classification() -> None:
    assert classify_ddl_execution("add_column", "inplace", False, "Lost connection to MySQL server") == "FAIL_CRASH"


def test_selection_is_deterministic_and_rejects_unknown_ids() -> None:
    smoke = select_scenarios(smoke=True)
    assert [case.case_id for case in smoke] == [
        case.case_id for case in smoke_inplace_unique_scenarios()
    ]

    selected = select_scenarios(case_ids={"TUCUI-000001", "TUCUI-002304"})
    assert [case.case_id for case in selected] == ["TUCUI-000001", "TUCUI-002304"]

    with pytest.raises(ValueError, match="Unknown case IDs: TUCUI-999999"):
        select_scenarios(case_ids={"TUCUI-999999"})


def test_run_namespace_is_unique_safe_and_short() -> None:
    first = make_run_namespace("qa_inplace_unique_conflict", "20261020T000000Z-ab12cd34")
    second = make_run_namespace("qa_inplace_unique_conflict", "20261020T000001Z-ef56cd78")
    assert first.database.startswith("qa_inplace_unique_conflict__run_")
    assert first.database != second.database
    assert len(first.database) <= 64
    assert first.target_table.startswith("tucui_target_")
    assert first.parent_table.startswith("tucui_parent_")
    assert first.database.isidentifier()


def test_create_table_keeps_conflict_surfaces_independent_of_ddl_target() -> None:
    namespace = make_run_namespace("qa_inplace_unique_conflict", "20261020T000000Z-ab12cd34")
    sql = build_create_table_sql(namespace.target_table, namespace.parent_table)
    for column in (
        "existing_unique",
        "new_unique",
        "composite_a",
        "composite_b",
        "nullable_unique",
        "value",
        "stable_value",
    ):
        assert f"`{column}`" in sql
    for unique_key in (
        "uk_tucui_existing_unique",
        "uk_tucui_new_unique",
        "uk_tucui_composite",
        "uk_tucui_nullable_unique",
    ):
        assert unique_key in sql
    assert "`id` BIGINT NOT NULL AUTO_INCREMENT" in sql
    assert "PRIMARY KEY (`id`)" in sql


def test_seed_and_duplicate_sql_is_deterministic_and_guarantees_conflict() -> None:
    scenario = next(iter_inplace_unique_scenarios())
    namespace = make_run_namespace("qa_inplace_unique_conflict", "20261020T000000Z-ab12cd34")
    normal = build_seed_values(scenario, row_no=1, data_state="normal")
    boundary = build_seed_values(scenario, row_no=1, data_state="boundary")
    assert normal != boundary
    assert normal["existing_unique"] == "TUCUI-SEED-000001"
    assert boundary["existing_unique"] == "TUCUI-BOUNDARY-000001"
    assert normal["nullable_unique"] is not None
    assert boundary["nullable_unique"] is not None

    sql, columns = duplicate_insert_sql(namespace.target_table)
    assert sql.startswith(f"INSERT INTO `{namespace.target_table}`")
    assert "existing_unique" in columns
    assert "new_unique" in columns
    assert "nullable_unique" in columns


@pytest.mark.parametrize("operation_id", [case.operation_id for case in smoke_inplace_unique_scenarios()])
def test_operation_specific_schema_expectations_are_complete(operation_id: str) -> None:
    expected = expected_object_state(operation_id, ddl_succeeded=True)
    assert expected, operation_id
    assert expected_object_state(operation_id, ddl_succeeded=False), operation_id


def test_summary_markdown_reports_all_pass_and_counts() -> None:
    markdown = render_summary_markdown(
        {
            "all_pass": True,
            "batch_id": "batch",
            "profile": "copy",
            "selected_count": 2,
            "counts": {"PASS": 1, "EXPECTED_REJECT": 1},
            "mysqld_version": "8.0.41-test",
        }
    )
    assert "ALL PASS" in markdown
    assert "EXPECTED_REJECT: 1" in markdown
    assert "8.0.41-test" in markdown


def test_cli_parser_supports_required_safe_options() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--profile",
            "instant",
            "--smoke",
            "--results",
            "results.jsonl",
            "--summary",
            "summary.json",
            "--host",
            "127.0.0.1",
            "--port",
            "3307",
            "--user",
            "tester",
            "--password-env",
            "MYSQL_PASSWORD",
            "--database",
            "qa_custom",
            "--filler-rows",
            "17",
            "--hold-seconds",
            "0.5",
            "--max-attempts",
            "9",
            "--external",
        ]
    )
    assert args.profile == "instant"
    assert args.smoke and args.external
    assert args.results == Path("results.jsonl")
    assert args.summary == Path("summary.json")
    assert args.host == "127.0.0.1"
    assert args.port == 3307
    assert args.user == "tester"
    assert args.password_env == "MYSQL_PASSWORD"
    assert args.database == "qa_custom"
    assert args.filler_rows == 17
    assert args.hold_seconds == 0.5
    assert args.max_attempts == 9


def test_cli_help_runs_without_database_or_credentials() -> None:
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        check=True,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
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
        "--database",
        "--filler-rows",
        "--hold-seconds",
        "--max-attempts",
        "--external",
    ):
        assert option in completed.stdout


@pytest.mark.skipif(
    os.environ.get("MYSQL_CASE_FACTORY_TUCUI_SMOKE") != "1",
    reason="set MYSQL_CASE_FACTORY_TUCUI_SMOKE=1 to run an authorized database smoke test",
)
def test_authorized_external_smoke_run(tmp_path: Path) -> None:
    password_env = os.environ.get("MYSQL_CASE_FACTORY_TUCUI_PASSWORD_ENV")
    command = [
        sys.executable,
        str(TOOL),
        "--profile",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUI_PROFILE", "copy"),
        "--smoke",
        "--external",
        "--host",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUI_HOST", "127.0.0.1"),
        "--port",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUI_PORT", "3306"),
        "--user",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUI_USER", "root"),
        "--database",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUI_DATABASE", "qa_inplace_unique_conflict"),
        "--results",
        str(tmp_path / "results.jsonl"),
        "--summary",
        str(tmp_path / "summary.json"),
        "--filler-rows",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUI_FILLER_ROWS", "128"),
        "--hold-seconds",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUI_HOLD_SECONDS", "1"),
        "--max-attempts",
        os.environ.get("MYSQL_CASE_FACTORY_TUCUI_MAX_ATTEMPTS", "10000"),
    ]
    if password_env:
        command.extend(["--password-env", password_env])
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)

    results = [json.loads(line) for line in (tmp_path / "results.jsonl").read_text().splitlines()]
    assert len(results) == 12
    assert {result["classification"] for result in results} <= {"PASS", "EXPECTED_REJECT"}
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["all_pass"] is True
    assert (tmp_path / "summary.md").exists()
