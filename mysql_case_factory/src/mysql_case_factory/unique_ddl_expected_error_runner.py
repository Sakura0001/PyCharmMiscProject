from __future__ import annotations

import argparse
import json
import os
import threading
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from mysql_case_factory.unique_ddl_expected_error import (
    UNIQUE_DDL_ERROR_BATCH_ID,
    UNIQUE_DDL_ERROR_BATCH_KIND,
    UNIQUE_DDL_ERROR_DATABASE,
    UNIQUE_DDL_ERROR_PROFILE,
    UniqueDDLErrorScenario,
    create_table_sql,
    index_expression,
    iter_unique_ddl_error_scenarios,
    render_ddl_sql,
    render_dml_sql,
    seed_row,
    smoke_unique_ddl_error_scenarios,
)

CRASH_MARKERS = (
    "lost connection",
    "server has gone away",
    "2013",
    "2006",
    "signal",
    "crash",
)


@dataclass(frozen=True)
class ConnectionConfig:
    host: str
    port: int
    user: str
    password: str
    database: str | None = None


def _connect(config: ConnectionConfig):
    import pymysql

    return pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        charset="utf8mb4",
        autocommit=True,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _execute(connection: Any, sql: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(sql)


def _query_one(connection: Any, sql: str, params: Sequence[Any] | None = None) -> Any:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def _server_version(connection: Any) -> str:
    return str(_query_one(connection, "SELECT VERSION()")[0])


def _index_exists(connection: Any, database: str, table: str, index_name: str) -> bool:
    row = _query_one(
        connection,
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_NAME=%s",
        (database, table, index_name),
    )
    return bool(row and row[0])


def _drop_index_if_exists(connection: Any, database: str, table: str, index_name: str) -> None:
    if _index_exists(connection, database, table, index_name):
        _execute(connection, f"ALTER TABLE `{table}` DROP INDEX `{index_name}`")


def _seed_shape(connection: Any, scenario_shape: str, table: str, rows: int) -> None:
    _execute(connection, f"DROP TABLE IF EXISTS `{table}`")
    _execute(connection, create_table_sql(scenario_shape, table))
    if scenario_shape == "composite":
        insert_sql = f"INSERT INTO `{table}` (id,a,b) VALUES (%s,%s,%s)"
    elif scenario_shape == "generated":
        insert_sql = f"INSERT INTO `{table}` (id,v) VALUES (%s,%s)"
    else:
        insert_sql = f"INSERT INTO `{table}` (id,v) VALUES (%s,%s)"

    batch_size = 1000
    with connection.cursor() as cursor:
        for start in range(1, rows + 1, batch_size):
            end = min(start + batch_size - 1, rows)
            values = [seed_row(scenario_shape, row_no) for row_no in range(start, end + 1)]
            cursor.executemany(insert_sql, values)


def _reset_shape(connection: Any, scenario_shape: str, table: str, rows: int, index_name: str) -> None:
    database = connection.db
    _drop_index_if_exists(connection, database, table, index_name)
    _execute(connection, f"DELETE FROM `{table}` WHERE id > {rows}")
    _execute(connection, f"DELETE FROM `{table}` WHERE id = {rows}")
    row = seed_row(scenario_shape, rows)
    if scenario_shape == "composite":
        _execute(
            connection,
            f"INSERT INTO `{table}` (id,a,b) VALUES ({row[0]},{row[1]},{row[2]})",
        )
    else:
        value = row[1]
        if isinstance(value, str):
            value = "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
        _execute(connection, f"INSERT INTO `{table}` (id,v) VALUES ({row[0]},{value})")


def select_scenarios(
    *,
    smoke: bool = False,
    all_cases: bool = False,
    case_ids: set[str] | None = None,
) -> list[UniqueDDLErrorScenario]:
    if sum(bool(value) for value in (smoke, all_cases, bool(case_ids))) != 1:
        raise ValueError("select exactly one of --smoke, --all, or --case-id")
    if smoke:
        return smoke_unique_ddl_error_scenarios()
    if case_ids:
        selected = [scenario for scenario in iter_unique_ddl_error_scenarios() if scenario.case_id in case_ids]
        missing = case_ids - {scenario.case_id for scenario in selected}
        if missing:
            raise ValueError(f"Unknown case IDs: {', '.join(sorted(missing))}")
        return selected
    return list(iter_unique_ddl_error_scenarios())


def _ddl_worker(
    connection: Any,
    ddl_sql: str,
    result: dict[str, Any],
) -> None:
    result["ddl_start"] = time.monotonic()
    try:
        _execute(connection, ddl_sql)
        result["ddl_succeeded"] = True
        result["ddl_error"] = None
        result["ddl_error_code"] = None
    except Exception as error:
        result["ddl_succeeded"] = False
        result["ddl_error"] = str(error)
        result["ddl_error_code"] = error.args[0] if error.args and isinstance(error.args[0], int) else None
    finally:
        result["ddl_end"] = time.monotonic()


def _execute_dml(connection: Any, dml_sql: str) -> tuple[bool, str | None]:
    try:
        for statement in dml_sql.split(";"):
            if statement.strip():
                _execute(connection, statement)
        return True, None
    except Exception as error:
        return False, str(error)


def classify_scenario_execution(
    *,
    overlap: bool,
    ddl_succeeded: bool,
    ddl_error_code: int | None,
    ddl_error: str | None,
    dml_succeeded: bool,
) -> str:
    if ddl_error and any(marker in ddl_error.lower() for marker in CRASH_MARKERS):
        return "FAIL_CRASH"
    if not overlap:
        return "NO_OVERLAP"
    if ddl_succeeded:
        return "FAIL_DDL_SUCCESS"
    if ddl_error_code not in {1062, 1859}:
        return "FAIL_DDL_ERROR"
    if not dml_succeeded:
        return "FAIL_DML"
    return "PASS"


def run_scenario(
    scenario: UniqueDDLErrorScenario,
    control: Any,
    ddl_connection: Any,
    dml_connection: Any,
    *,
    rows: int,
    dml_delay: float,
) -> dict[str, Any]:
    started_at = _utc_now()
    _reset_shape(control, scenario.shape, scenario.table, rows, scenario.index_name)
    ddl_sql = render_ddl_sql(scenario)
    dml_sql = render_dml_sql(scenario, rows)

    ddl_result: dict[str, Any] = {}
    worker = threading.Thread(
        target=_ddl_worker,
        args=(ddl_connection, ddl_sql, ddl_result),
        daemon=True,
    )
    worker.start()
    time.sleep(dml_delay)
    dml_start = time.monotonic()
    dml_succeeded, dml_error = _execute_dml(dml_connection, dml_sql)
    dml_end = time.monotonic()
    worker.join()

    ddl_start = ddl_result.get("ddl_start")
    ddl_end = ddl_result.get("ddl_end")
    overlap = bool(
        ddl_start is not None
        and ddl_end is not None
        and dml_start is not None
        and dml_start < ddl_end
        and dml_end < ddl_end
        and dml_end > ddl_start
    )
    classification = classify_scenario_execution(
        overlap=overlap,
        ddl_succeeded=bool(ddl_result.get("ddl_succeeded")),
        ddl_error_code=ddl_result.get("ddl_error_code"),
        ddl_error=ddl_result.get("ddl_error"),
        dml_succeeded=dml_succeeded,
    )
    return {
        "batch_id": UNIQUE_DDL_ERROR_BATCH_ID,
        "batch_kind": UNIQUE_DDL_ERROR_BATCH_KIND,
        "case_id": scenario.case_id,
        "case_no": scenario.case_no,
        "profile": UNIQUE_DDL_ERROR_PROFILE,
        "ddl_form": scenario.ddl_form,
        "shape": scenario.shape,
        "dml_type": scenario.dml_type,
        "table": scenario.table,
        "index_expression": index_expression(scenario.shape),
        "ddl_sql": ddl_sql,
        "dml_sql": dml_sql,
        "ddl_succeeded": bool(ddl_result.get("ddl_succeeded")),
        "ddl_error": ddl_result.get("ddl_error"),
        "ddl_error_code": ddl_result.get("ddl_error_code"),
        "dml_succeeded": dml_succeeded,
        "dml_error": dml_error,
        "overlap": overlap,
        "ddl_start": ddl_start,
        "ddl_end": ddl_end,
        "dml_start": dml_start,
        "dml_end": dml_end,
        "classification": classification,
        "started_at": started_at,
        "finished_at": _utc_now(),
    }


def run_local(
    scenarios: Sequence[UniqueDDLErrorScenario],
    config: ConnectionConfig,
    *,
    rows: int,
    dml_delay: float,
    database: str = UNIQUE_DDL_ERROR_DATABASE,
) -> list[dict[str, Any]]:
    root_connection = _connect(
        ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=None,
        )
    )
    _execute(root_connection, f"DROP DATABASE IF EXISTS `{database}`")
    _execute(
        root_connection,
        f"CREATE DATABASE `{database}` "
        "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci",
    )
    root_connection.close()

    control = _connect(
        ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=database,
        )
    )
    ddl_connection = _connect(
        ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=database,
        )
    )
    dml_connection = _connect(
        ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=database,
        )
    )

    shapes = sorted({scenario.shape for scenario in scenarios})
    for shape in shapes:
        table = f"tab_tucud_{shape}_target"
        _seed_shape(control, shape, table, rows)

    results: list[dict[str, Any]] = []
    mysqld_version = _server_version(control)
    try:
        for scenario in scenarios:
            result = run_scenario(
                scenario,
                control,
                ddl_connection,
                dml_connection,
                rows=rows,
                dml_delay=dml_delay,
            )
            result["mysqld_version"] = mysqld_version
            results.append(result)
            _reset_shape(control, scenario.shape, scenario.table, rows, scenario.index_name)
    finally:
        ddl_connection.close()
        dml_connection.close()
        _execute(control, f"DROP DATABASE IF EXISTS `{database}`")
        control.close()
    return results


def render_summary_markdown(summary: dict[str, Any]) -> str:
    counts = summary.get("counts", {})
    count_lines = "\n".join(f"- {name}: {count}" for name, count in sorted(counts.items()))
    return (
        "# Unique-DDL expected-error summary\n\n"
        f"- Batch: `{summary.get('batch_id', UNIQUE_DDL_ERROR_BATCH_ID)}`\n"
        f"- Profile: `{summary.get('profile', UNIQUE_DDL_ERROR_PROFILE)}`\n"
        f"- Selected: {summary.get('selected_count', 0)}\n"
        f"- Rows per shape: {summary.get('rows_per_shape', '-')}\n"
        f"- MySQL: `{summary.get('mysqld_version', '-')}`\n"
        f"- Result: **{'ALL PASS' if summary.get('all_pass') else 'FAIL'}**\n\n"
        "## Classifications\n\n"
        f"{count_lines}\n"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TUCUD unique-DDL expected-error scenarios")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--case-id", action="append", default=None)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password-env", default=None)
    parser.add_argument("--database", default=UNIQUE_DDL_ERROR_DATABASE)
    parser.add_argument("--rows", type=int, default=200_000)
    parser.add_argument("--dml-delay", type=float, default=0.01)
    parser.add_argument("--external", action="store_true")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    if sum(bool(value) for value in (args.smoke, args.all, bool(args.case_id))) != 1:
        parser.error("select exactly one of --smoke, --all, or --case-id")
    case_ids = set(args.case_id or [])
    scenarios = select_scenarios(smoke=args.smoke, all_cases=args.all, case_ids=case_ids)
    password = os.environ.get(args.password_env, "") if args.password_env else ""
    config = ConnectionConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        database=None,
    )

    started_at = _utc_now()
    results = run_local(
        scenarios,
        config,
        rows=args.rows,
        dml_delay=args.dml_delay,
        database=args.database,
    )
    counts = Counter(result["classification"] for result in results)
    all_pass = all(result["classification"] == "PASS" for result in results)
    mysqld_version = next(
        (result.get("mysqld_version") for result in results if result.get("mysqld_version")),
        "-",
    )
    summary = {
        "all_pass": all_pass,
        "batch_id": UNIQUE_DDL_ERROR_BATCH_ID,
        "batch_kind": UNIQUE_DDL_ERROR_BATCH_KIND,
        "profile": UNIQUE_DDL_ERROR_PROFILE,
        "selected_count": len(scenarios),
        "executed_count": len(results),
        "counts": dict(sorted(counts.items())),
        "rows_per_shape": args.rows,
        "mysqld_version": mysqld_version,
        "started_at": started_at,
        "finished_at": _utc_now(),
    }

    args.results.parent.mkdir(parents=True, exist_ok=True)
    with args.results.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.with_suffix(".md").write_text(
        render_summary_markdown(summary),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
