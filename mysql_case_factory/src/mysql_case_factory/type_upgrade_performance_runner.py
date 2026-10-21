from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from mysql_case_factory.type_upgrade_performance import (
    NOISE_COLUMNS,
    TYPE_PERFORMANCE_BATCH_ID,
    TYPE_PERFORMANCE_BATCH_KIND,
    TYPE_PERFORMANCE_DATABASE,
    TYPE_PERFORMANCE_PROFILE,
    UPGRADE_COLUMNS,
    TypePerformanceScenario,
    build_copy_source_sql,
    build_ddl_sql,
    build_full_scan_query,
    build_generate_source_sql,
    build_insert_numbers_sql,
    build_numbers_table_sql,
    build_reference_table_sql,
    build_source_table_sql,
    type_performance_scenarios,
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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _execute(connection: Any, sql: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(sql)


def _query_all(connection: Any, sql: str) -> list[tuple[Any, ...]]:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return list(cursor.fetchall())


def _query_one(connection: Any, sql: str, params: Sequence[Any] | None = None) -> tuple[Any, ...]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        row = cursor.fetchone()
        return tuple(row) if row else ()


def _server_version(connection: Any) -> str:
    return str(_query_one(connection, "SELECT VERSION()")[0])


def _drop_tables(connection: Any, *tables: str) -> None:
    for table in tables:
        _execute(connection, f"DROP TABLE IF EXISTS `{table}`")


def _fill_numbers_table(connection: Any, table: str, rows: int) -> None:
    values: list[tuple[int]] = []
    for number in range(1, rows + 1):
        values.append((number,))
        if len(values) == 10_000:
            with connection.cursor() as cursor:
                cursor.executemany(f"INSERT INTO `{table}` (n) VALUES (%s)", values)
            values.clear()
    if values:
        with connection.cursor() as cursor:
            cursor.executemany(f"INSERT INTO `{table}` (n) VALUES (%s)", values)


def _create_numbers_tables(connection: Any, rows: int) -> None:
    _drop_tables(connection, "tab_tucpf_numbers", "tab_tucpf_multiplier")
    _execute(connection, build_numbers_table_sql("tab_tucpf_numbers"))
    _fill_numbers_table(connection, "tab_tucpf_numbers", min(rows, 100_000))
    multiplier_rows = max(1, math.ceil(rows / 100_000))
    _execute(connection, build_numbers_table_sql("tab_tucpf_multiplier"))
    _fill_numbers_table(connection, "tab_tucpf_multiplier", multiplier_rows)


def _create_source_and_reference(
    connection: Any,
    rows: int,
    source_table: str = "tab_tucpf_source",
    reference_table: str = "tab_tucpf_reference",
) -> None:
    _drop_tables(connection, source_table, reference_table)
    _execute(connection, build_source_table_sql(source_table))
    _execute(connection, build_reference_table_sql(reference_table))
    _create_numbers_tables(connection, rows)
    _execute(
        connection,
        build_generate_source_sql(
            source_table,
            "tab_tucpf_numbers",
            "tab_tucpf_multiplier",
            rows,
        ),
    )
    _execute(connection, build_copy_source_sql(source_table, reference_table))


def _run_full_scan(connection: Any, table: str) -> tuple[float, tuple[Any, ...], str]:
    query = build_full_scan_query(table)
    start = time.perf_counter()
    row = _query_one(connection, query)
    elapsed = time.perf_counter() - start
    explain = _query_one(connection, f"EXPLAIN ANALYZE {query}")
    explain_text = "\n".join(str(value) for value in explain)
    return elapsed, row, explain_text


def _table_size(connection: Any, database: str, table: str) -> tuple[int, int, int]:
    row = _query_one(
        connection,
        "SELECT TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH "
        "FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
        (database, table),
    )
    return tuple(int(value) if value is not None else 0 for value in row)


def _create_candidate_from_source(connection: Any, rows: int) -> float:
    _drop_tables(connection, "tab_tucpf_candidate")
    start = time.perf_counter()
    _execute(connection, "CREATE TABLE tab_tucpf_candidate LIKE tab_tucpf_source")
    columns = ["id", *[column[0] for column in UPGRADE_COLUMNS], *[column[0] for column in NOISE_COLUMNS]]
    quoted = ", ".join(f"`{column}`" for column in columns)
    _execute(connection, f"INSERT INTO tab_tucpf_candidate ({quoted}) SELECT {quoted} FROM tab_tucpf_source")
    return time.perf_counter() - start


def _execute_ddl(connection: Any, statements: Sequence[str]) -> tuple[float, bool, str | None]:
    start = time.perf_counter()
    try:
        for statement in statements:
            _execute(connection, statement)
        return time.perf_counter() - start, True, None
    except Exception as error:
        return time.perf_counter() - start, False, str(error)


def _dml_benchmark(connection: Any, rows: int, dml_rows: int) -> dict[str, float]:
    columns = ["id", *[column[0] for column in UPGRADE_COLUMNS], *[column[0] for column in NOISE_COLUMNS]]
    quoted = ", ".join(f"`{column}`" for column in columns)
    non_id = [column for column in columns if column != "id"]
    quoted_non_id = ", ".join(f"`{column}`" for column in non_id)
    selected_non_id = ", ".join(f"`{column}`" for column in non_id)

    insert_start = time.perf_counter()
    _execute(
        connection,
        f"INSERT INTO tab_tucpf_candidate ({quoted}) "
        f"SELECT id + {rows}, {selected_non_id} FROM tab_tucpf_reference LIMIT {dml_rows}",
    )
    insert_seconds = time.perf_counter() - insert_start

    update_start = time.perf_counter()
    _execute(
        connection,
        f"UPDATE tab_tucpf_candidate SET varchar_255 = REPEAT('z', 255) "
        f"WHERE id > {rows}",
    )
    update_seconds = time.perf_counter() - update_start

    delete_start = time.perf_counter()
    _execute(connection, f"DELETE FROM tab_tucpf_candidate WHERE id > {rows}")
    delete_seconds = time.perf_counter() - delete_start

    reinsert_start = time.perf_counter()
    _execute(
        connection,
        f"INSERT INTO tab_tucpf_candidate ({quoted}) "
        f"SELECT id + {rows}, {selected_non_id} FROM tab_tucpf_reference LIMIT {dml_rows}",
    )
    reinsert_seconds = time.perf_counter() - reinsert_start

    return {
        "insert_seconds": insert_seconds,
        "update_seconds": update_seconds,
        "delete_seconds": delete_seconds,
        "reinsert_seconds": reinsert_seconds,
    }


def calibrate_rows(
    connection: Any,
    *,
    calibration_rows: int,
    target_scan_seconds: float,
    max_rows: int,
) -> tuple[int, float, float]:
    _drop_tables(connection, "tab_tucpf_calibration")
    _execute(connection, build_source_table_sql("tab_tucpf_calibration"))
    _create_numbers_tables(connection, calibration_rows)
    _execute(
        connection,
        build_generate_source_sql(
            "tab_tucpf_calibration",
            "tab_tucpf_numbers",
            "tab_tucpf_multiplier",
            calibration_rows,
        ),
    )
    elapsed, _, _ = _run_full_scan(connection, "tab_tucpf_calibration")
    estimated_rows = int(calibration_rows * target_scan_seconds / elapsed) if elapsed else max_rows
    final_rows = min(max(1, estimated_rows), max_rows)
    _drop_tables(connection, "tab_tucpf_calibration")
    return final_rows, elapsed, target_scan_seconds


def classify_performance_execution(
    *,
    scenario: str,
    ddl_succeeded: bool,
    ddl_error: str | None,
    aggregate_match: bool | None,
) -> str:
    if ddl_error and any(marker in ddl_error.lower() for marker in CRASH_MARKERS):
        return "FAIL_CRASH"
    if scenario in {"source_baseline", "reference"}:
        return "PASS"
    if not ddl_succeeded:
        return "FAIL_DDL"
    return "PASS" if aggregate_match is True else "FAIL_DATA"


def run_scenario(
    scenario: TypePerformanceScenario,
    connection: Any,
    database: str,
    *,
    rows: int,
    dml_rows: int,
) -> dict[str, Any]:
    started_at = _utc_now()
    result: dict[str, Any] = {
        "batch_id": TYPE_PERFORMANCE_BATCH_ID,
        "batch_kind": TYPE_PERFORMANCE_BATCH_KIND,
        "case_id": scenario.case_id,
        "case_no": scenario.case_no,
        "profile": TYPE_PERFORMANCE_PROFILE,
        "scenario": scenario.scenario,
        "rows": rows,
        "dml_rows": dml_rows,
        "started_at": started_at,
    }

    if scenario.scenario == "source_baseline":
        table = "tab_tucpf_source"
    elif scenario.scenario == "reference":
        table = "tab_tucpf_reference"
    else:
        table = "tab_tucpf_candidate"

    if scenario.scenario not in {"source_baseline", "reference"}:
        result["candidate_copy_seconds"] = _create_candidate_from_source(connection, rows)

    ddl_statements = build_ddl_sql(scenario.scenario)
    if ddl_statements:
        ddl_seconds, ddl_succeeded, ddl_error = _execute_ddl(connection, ddl_statements)
        result.update(
            {
                "ddl_seconds": ddl_seconds,
                "ddl_succeeded": ddl_succeeded,
                "ddl_error": ddl_error,
                "ddl_statement_count": len(ddl_statements),
            }
        )
    else:
        result.update(
            {
                "ddl_seconds": 0.0,
                "ddl_succeeded": True,
                "ddl_error": None,
                "ddl_statement_count": 0,
            }
        )

    if not result["ddl_succeeded"]:
        result["classification"] = classify_performance_execution(
            scenario=scenario.scenario,
            ddl_succeeded=False,
            ddl_error=result["ddl_error"],
            aggregate_match=None,
        )
        result["finished_at"] = _utc_now()
        _drop_tables(connection, "tab_tucpf_candidate")
        return result

    query_seconds, aggregates, explain = _run_full_scan(connection, table)
    result.update(
        {
            "query_seconds": query_seconds,
            "aggregates": list(aggregates),
            "explain_analyze": explain,
        }
    )

    aggregate_match: bool | None = None
    if scenario.scenario not in {"source_baseline", "reference"}:
        reference_seconds, reference_aggregates, _ = _run_full_scan(connection, "tab_tucpf_reference")
        aggregate_match = aggregates == reference_aggregates
        result["reference_query_seconds"] = reference_seconds
        result["aggregate_match"] = aggregate_match
    else:
        result["aggregate_match"] = None

    if scenario.scenario not in {"source_baseline", "reference"}:
        result.update(_dml_benchmark(connection, rows, dml_rows))

    table_rows, data_length, index_length = _table_size(connection, database, table)
    result.update(
        {
            "table_rows": table_rows,
            "data_length": data_length,
            "index_length": index_length,
            "classification": classify_performance_execution(
                scenario=scenario.scenario,
                ddl_succeeded=True,
                ddl_error=None,
                aggregate_match=aggregate_match,
            ),
            "finished_at": _utc_now(),
        }
    )

    if scenario.scenario not in {"source_baseline", "reference"}:
        _drop_tables(connection, "tab_tucpf_candidate")
    return result


def select_scenarios(
    *,
    all_scenarios: bool = False,
    scenario_names: set[str] | None = None,
) -> list[TypePerformanceScenario]:
    if all_scenarios == bool(scenario_names):
        raise ValueError("select exactly one of --all or --scenario")
    if all_scenarios:
        return list(type_performance_scenarios())
    selected = [
        scenario for scenario in type_performance_scenarios() if scenario.scenario in scenario_names
    ]
    missing = scenario_names - {scenario.scenario for scenario in selected}
    if missing:
        raise ValueError(f"Unknown scenarios: {', '.join(sorted(missing))}")
    return selected


def run_local(
    scenarios: Sequence[TypePerformanceScenario],
    config: ConnectionConfig,
    *,
    rows: int,
    calibration_rows: int,
    target_scan_seconds: float,
    max_rows: int,
    dml_rows: int,
) -> tuple[list[dict[str, Any]], int, float, float]:
    root = _connect(
        ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=None,
        )
    )
    _execute(root, f"DROP DATABASE IF EXISTS `{TYPE_PERFORMANCE_DATABASE}`")
    _execute(
        root,
        f"CREATE DATABASE `{TYPE_PERFORMANCE_DATABASE}` "
        "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci",
    )
    root.close()

    connection = _connect(
        ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=TYPE_PERFORMANCE_DATABASE,
        )
    )
    mysqld_version = _server_version(connection)

    if rows <= 0:
        rows, calibration_seconds, target_seconds = calibrate_rows(
            connection,
            calibration_rows=calibration_rows,
            target_scan_seconds=target_scan_seconds,
            max_rows=max_rows,
        )
    else:
        calibration_seconds = 0.0
        target_seconds = target_scan_seconds

    _create_source_and_reference(connection, rows)
    results: list[dict[str, Any]] = []
    try:
        for scenario in scenarios:
            result = run_scenario(
                scenario,
                connection,
                TYPE_PERFORMANCE_DATABASE,
                rows=rows,
                dml_rows=dml_rows,
            )
            result["mysqld_version"] = mysqld_version
            result["calibration_seconds"] = calibration_seconds
            result["target_scan_seconds"] = target_seconds
            results.append(result)
    finally:
        _drop_tables(
            connection,
            "tab_tucpf_candidate",
            "tab_tucpf_source",
            "tab_tucpf_reference",
            "tab_tucpf_numbers",
            "tab_tucpf_multiplier",
        )
        _execute(connection, f"DROP DATABASE IF EXISTS `{TYPE_PERFORMANCE_DATABASE}`")
        connection.close()
    return results, rows, calibration_seconds, target_seconds


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def render_summary_markdown(summary: dict[str, Any]) -> str:
    counts = summary.get("counts", {})
    count_lines = "\n".join(f"- {name}: {count}" for name, count in sorted(counts.items()))
    return (
        "# Type-upgrade performance summary\n\n"
        f"- Batch: `{summary.get('batch_id', TYPE_PERFORMANCE_BATCH_ID)}`\n"
        f"- Rows: {summary.get('rows', 0):,}\n"
        f"- Target scan: {summary.get('target_scan_seconds', 0)}s\n"
        f"- MySQL: `{summary.get('mysqld_version', '-')}`\n"
        f"- Result: **{'ALL PASS' if summary.get('all_pass') else 'FAIL'}**\n\n"
        "## Classifications\n\n"
        f"{count_lines}\n"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TUCPF type-upgrade performance scenarios")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--scenario", action="append", default=None)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password-env", default=None)
    parser.add_argument("--rows", type=int, default=0, help="0 means auto-calibrate")
    parser.add_argument("--calibration-rows", type=int, default=100_000)
    parser.add_argument("--target-scan-seconds", type=float, default=300.0)
    parser.add_argument("--max-rows", type=int, default=20_000_000)
    parser.add_argument("--dml-rows", type=int, default=100_000)
    parser.add_argument("--external", action="store_true")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    scenario_names = set(args.scenario or [])
    if bool(args.all) == bool(scenario_names):
        parser.error("select exactly one of --all or --scenario")
    scenarios = select_scenarios(all_scenarios=args.all, scenario_names=scenario_names)
    password = os.environ.get(args.password_env, "") if args.password_env else ""
    config = ConnectionConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        database=None,
    )

    started_at = _utc_now()
    results, rows, calibration_seconds, target_seconds = run_local(
        scenarios,
        config,
        rows=args.rows,
        calibration_rows=args.calibration_rows,
        target_scan_seconds=args.target_scan_seconds,
        max_rows=args.max_rows,
        dml_rows=args.dml_rows,
    )
    counts = Counter(result["classification"] for result in results)
    all_pass = all(result["classification"] == "PASS" for result in results)
    mysqld_version = next(
        (result.get("mysqld_version") for result in results if result.get("mysqld_version")),
        "-",
    )
    summary = {
        "all_pass": all_pass,
        "batch_id": TYPE_PERFORMANCE_BATCH_ID,
        "batch_kind": TYPE_PERFORMANCE_BATCH_KIND,
        "profile": TYPE_PERFORMANCE_PROFILE,
        "selected_count": len(scenarios),
        "executed_count": len(results),
        "counts": dict(sorted(counts.items())),
        "rows": rows,
        "calibration_rows": args.calibration_rows,
        "calibration_seconds": calibration_seconds,
        "target_scan_seconds": target_seconds,
        "mysqld_version": mysqld_version,
        "started_at": started_at,
        "finished_at": _utc_now(),
    }

    args.results.parent.mkdir(parents=True, exist_ok=True)
    with args.results.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True, default=_json_default) + "\n")
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    args.summary.with_suffix(".md").write_text(
        render_summary_markdown(summary),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default))
    raise SystemExit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
