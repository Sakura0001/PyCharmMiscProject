from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, Sequence

from mysql_case_factory.virtual_function_type_upgrade import (
    VIRTUAL_FUNCTION_BATCH_ID,
    VIRTUAL_FUNCTION_BATCH_KIND,
    VIRTUAL_FUNCTION_DATABASE,
    VIRTUAL_FUNCTION_PROFILES,
    VirtualFunctionScenario,
    build_create_table_sql,
    build_ddl_sql,
    iter_virtual_function_scenarios,
    smoke_virtual_function_scenarios,
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


def _execute(connection: Any, sql: str, params: Sequence[Any] | None = None) -> None:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())


def _query_all(connection: Any, sql: str, params: Sequence[Any] | None = None) -> list[tuple[Any, ...]]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        return list(cursor.fetchall())


def _query_one(connection: Any, sql: str, params: Sequence[Any] | None = None) -> Any:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def _server_version(connection: Any) -> str:
    return str(_query_one(connection, "SELECT VERSION()")[0])


def _integer_bounds(type_name: str) -> tuple[int, int]:
    unsigned = "UNSIGNED" in type_name
    base = type_name.replace(" UNSIGNED", "")
    signed = {
        "TINYINT": (-128, 127),
        "SMALLINT": (-32768, 32767),
        "MEDIUMINT": (-8388608, 8388607),
        "INT": (-2147483648, 2147483647),
        "BIGINT": (-(2**63), 2**63 - 1),
    }[base]
    unsigned_max = {
        "TINYINT": 255,
        "SMALLINT": 65535,
        "MEDIUMINT": 16777215,
        "INT": 4294967295,
        "BIGINT": 2**64 - 1,
    }[base]
    return (0, unsigned_max) if unsigned else signed


def _decimal_bounds(type_name: str) -> tuple[Decimal, Decimal, int]:
    match = re.search(r"\((\d+),(\d+)\)", type_name)
    if not match:
        return Decimal(-9999999999), Decimal(9999999999), 0
    precision, scale = int(match.group(1)), int(match.group(2))
    integer_digits = precision - scale
    digits = "9" * integer_digits + ("." + "9" * scale if scale else "")
    minimum = Decimal("-" + digits)
    maximum = Decimal(digits)
    return minimum, maximum, scale


def _bit_width(type_name: str) -> int:
    match = re.search(r"\((\d+)\)", type_name)
    return int(match.group(1)) if match else 1


def _type_length(type_name: str) -> int:
    match = re.search(r"\((\d+)\)", type_name)
    if match:
        return int(match.group(1))
    upper = type_name.upper()
    if upper in {"TINYTEXT", "TINYBLOB"}:
        return 255
    if upper in {"TEXT", "BLOB"}:
        return 1024
    if upper in {"MEDIUMTEXT", "MEDIUMBLOB"}:
        return 2048
    if upper in {"LONGTEXT", "LONGBLOB"}:
        return 4096
    if upper.startswith("CHAR") or upper.startswith("BINARY"):
        return 1
    return 0


def _decimal_string(value: Decimal, scale: int) -> str:
    return f"{value:.{scale}f}"


def seed_values(family: str, type_name: str, data_state: str) -> list[Any]:
    if family == "integer":
        minimum, maximum = _integer_bounds(type_name)
        if data_state == "normal":
            values: list[Any] = [0, 1, 2, 3, 4, 5, 6, 7]
        else:
            values = [
                minimum,
                maximum,
                0,
                1,
                -1 if minimum < 0 else 2,
                minimum + 1,
                maximum - 1,
                (minimum + maximum) // 2,
            ]
    elif family == "decimal":
        minimum, maximum, scale = _decimal_bounds(type_name)
        if data_state == "normal":
            raw = [Decimal(0), Decimal(1), Decimal(2), Decimal(3), Decimal(4), Decimal(5), Decimal(6), Decimal(7)]
        else:
            with localcontext() as context:
                context.prec = 100
                increment = Decimal(1).scaleb(-scale)
                raw = [
                    minimum,
                    maximum,
                    Decimal(0),
                    Decimal(1),
                    Decimal(-1),
                    minimum + increment,
                    maximum - increment,
                    (minimum + maximum) / 2,
                ]
        values = [_decimal_string(value, scale) for value in raw]
    elif family == "bit":
        width = _bit_width(type_name)
        maximum = (1 << width) - 1
        if data_state == "normal":
            values = [0, 1, 2, 3, 4, 5, 6, 7]
        else:
            values = [0, 1, maximum, maximum - 1, 0b10101010, 0b01010101, 0b11110000, 0b00001111]
        values = [value & maximum for value in values]
    elif family in {"character", "text"}:
        length = min(_type_length(type_name), 255)
        fixed = type_name.upper().startswith("CHAR")
        def exact_text(pattern: str) -> str:
            if length <= 0:
                return ""
            repeated = pattern * (length // len(pattern))
            return repeated + pattern[: length % len(pattern)]

        if data_state == "normal":
            values = [chr(ord("a") + index) * (length if fixed else min(index + 1, max(length, 1))) for index in range(8)]
        else:
            values = [
                exact_text("a"),
                exact_text("b"),
                exact_text("A"),
                exact_text("B"),
                exact_text("a"),
                exact_text("A"),
                exact_text("abc"),
                exact_text("XYZ"),
            ]
            if not fixed:
                values[0] = ""
    elif family in {"binary", "blob"}:
        length = min(_type_length(type_name), 255)
        fixed = type_name.upper().startswith("BINARY")
        def exact_binary(pattern: bytes) -> bytes:
            if length <= 0:
                return b""
            repeated = pattern * (length // len(pattern))
            return repeated + pattern[: length % len(pattern)]

        if data_state == "normal":
            values = [bytes([index + 1]) * (length if fixed else min(index + 1, max(length, 1))) for index in range(8)]
        else:
            values = [
                exact_binary(b"\x01"),
                exact_binary(b"\x02"),
                exact_binary(b"\xff"),
                exact_binary(b"\xfe"),
                exact_binary(b"\x00"),
                exact_binary(b"\xff"),
                exact_binary(b"\x01\x02\x03"),
                exact_binary(b"\xfe\xfd\xfc"),
            ]
            if not fixed:
                values[0] = b""
    else:
        raise AssertionError(family)
    return values


def _insert_rows(
    connection: Any,
    table: str,
    values: Sequence[Any],
    scenario: VirtualFunctionScenario,
    start_id: int = 1,
) -> None:
    if scenario.dependency_mode in {"virtual_generated", "stored_generated"}:
        sql = f"INSERT INTO `{table}` (id, base) VALUES (%s, %s)"
    else:
        sql = f"INSERT INTO `{table}` (id, base) VALUES (%s, %s)"
    with connection.cursor() as cursor:
        cursor.executemany(sql, [(index, value) for index, value in enumerate(values, start_id)])


def _select_rows(
    connection: Any,
    table: str,
    scenario: VirtualFunctionScenario,
) -> list[tuple[Any, ...]]:
    if scenario.dependency_mode in {"virtual_generated", "stored_generated"}:
        sql = f"SELECT id, base, gen FROM `{table}` ORDER BY id"
    elif scenario.dependency_mode == "functional_index":
        sql = f"SELECT id, base, {scenario.expression} AS gen FROM `{table}` ORDER BY id"
    else:
        sql = f"SELECT id, base FROM `{table}` ORDER BY id"
    return _query_all(connection, sql)


def _normalize_rows(rows: Sequence[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    normalized: list[tuple[Any, ...]] = []
    for row in rows:
        normalized.append(tuple(value.hex() if isinstance(value, bytes) else value for value in row))
    return normalized


def _run_dml(
    connection: Any,
    table: str,
    scenario: VirtualFunctionScenario,
    target_values: Sequence[Any],
) -> None:
    _insert_rows(connection, table, target_values, scenario, start_id=9)
    with connection.cursor() as cursor:
        for index, value in enumerate(target_values, start=9):
            cursor.execute(f"UPDATE `{table}` SET base = %s WHERE id = %s", (value, index))
        cursor.execute(f"DELETE FROM `{table}` WHERE id IN (1, 2, 3)")
    _insert_rows(connection, table, target_values[:3], scenario, start_id=1)


def _column_type(connection: Any, database: str, table: str, column: str) -> str | None:
    row = _query_one(
        connection,
        "SELECT COLUMN_TYPE FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        (database, table, column),
    )
    return str(row[0]) if row else None


def _index_exists(connection: Any, database: str, table: str, index_name: str) -> bool:
    row = _query_one(
        connection,
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_NAME=%s",
        (database, table, index_name),
    )
    return bool(row and row[0])


def classify_virtual_function_execution(
    *,
    control_succeeded: bool,
    candidate_succeeded: bool,
    control_error: str | None,
    candidate_error: str | None,
    data_match: bool | None,
    unchanged_match: bool | None,
) -> str:
    if candidate_error and any(marker in candidate_error.lower() for marker in CRASH_MARKERS):
        return "FAIL_CRASH"
    if control_succeeded != candidate_succeeded:
        return "FAIL_ALGORITHM"
    if candidate_succeeded:
        return "PASS" if data_match is True else "FAIL_DATA"
    return "PASS" if unchanged_match is True else "FAIL_UNCHANGED"


def run_scenario(
    scenario: VirtualFunctionScenario,
    connection: Any,
    database: str,
) -> dict[str, Any]:
    started_at = _utc_now()
    control_table = scenario.control_table
    candidate_table = scenario.candidate_table
    reference_table = scenario.reference_table

    for table in (control_table, candidate_table, reference_table):
        _execute(connection, f"DROP TABLE IF EXISTS `{table}`")

    _execute(connection, build_create_table_sql(scenario, control_table, scenario.source_type))
    _execute(connection, build_create_table_sql(scenario, candidate_table, scenario.source_type))
    _execute(connection, build_create_table_sql(scenario, reference_table, scenario.target_type))

    values = seed_values(scenario.family, scenario.source_type, scenario.data_state)
    if scenario.family == "integer" and "UNSIGNED" in scenario.target_type and any(
        isinstance(value, int) and value < 0 for value in values
    ):
        _, source_maximum = _integer_bounds(scenario.source_type)
        values = [0, 1, 2, 3, source_maximum, source_maximum - 1, source_maximum // 2, source_maximum // 3]
    if scenario.nullability == "nullable":
        values = values[:-1] + [None]
    target_values = seed_values(scenario.family, scenario.target_type, scenario.data_state)
    if scenario.nullability == "nullable":
        target_values = target_values[:-1] + [None]

    _insert_rows(connection, control_table, values, scenario)
    _insert_rows(connection, candidate_table, values, scenario)
    _insert_rows(connection, reference_table, values, scenario)

    before_candidate = _normalize_rows(_select_rows(connection, candidate_table, scenario))
    before_candidate_type = _column_type(connection, database, candidate_table, "base")

    control_ddl = build_ddl_sql(scenario, control_table)
    candidate_ddl = build_ddl_sql(scenario, candidate_table)

    control_succeeded = True
    control_error = None
    try:
        _execute(connection, control_ddl)
    except Exception as error:
        control_succeeded = False
        control_error = str(error)

    candidate_succeeded = True
    candidate_error = None
    try:
        _execute(connection, candidate_ddl)
    except Exception as error:
        candidate_succeeded = False
        candidate_error = str(error)

    data_match: bool | None = None
    unchanged_match: bool | None = None
    if candidate_succeeded:
        _run_dml(connection, candidate_table, scenario, target_values)
        _run_dml(connection, reference_table, scenario, target_values)
        candidate_rows = _normalize_rows(_select_rows(connection, candidate_table, scenario))
        reference_rows = _normalize_rows(_select_rows(connection, reference_table, scenario))
        data_match = candidate_rows == reference_rows
    else:
        after_candidate = _normalize_rows(_select_rows(connection, candidate_table, scenario))
        after_candidate_type = _column_type(connection, database, candidate_table, "base")
        unchanged_match = (
            after_candidate == before_candidate
            and after_candidate_type == before_candidate_type
        )

    classification = classify_virtual_function_execution(
        control_succeeded=control_succeeded,
        candidate_succeeded=candidate_succeeded,
        control_error=control_error,
        candidate_error=candidate_error,
        data_match=data_match,
        unchanged_match=unchanged_match,
    )

    result = {
        "batch_id": VIRTUAL_FUNCTION_BATCH_ID,
        "batch_kind": VIRTUAL_FUNCTION_BATCH_KIND,
        "case_id": scenario.case_id,
        "case_no": scenario.case_no,
        "family": scenario.family,
        "source_type": scenario.source_type,
        "target_type": scenario.target_type,
        "transition_key": scenario.transition_key,
        "dependency_mode": scenario.dependency_mode,
        "algorithm": scenario.algorithm,
        "data_state": scenario.data_state,
        "nullability": scenario.nullability,
        "control_ddl_succeeded": control_succeeded,
        "candidate_ddl_succeeded": candidate_succeeded,
        "control_error": control_error,
        "candidate_error": candidate_error,
        "data_match": data_match,
        "unchanged_match": unchanged_match,
        "classification": classification,
        "started_at": started_at,
        "finished_at": _utc_now(),
    }

    for table in (control_table, candidate_table, reference_table):
        _execute(connection, f"DROP TABLE IF EXISTS `{table}`")
    return result


def select_scenarios(
    *,
    smoke: bool = False,
    all_cases: bool = False,
    case_ids: set[str] | None = None,
    profile: str | None = None,
) -> list[VirtualFunctionScenario]:
    if sum(bool(value) for value in (smoke, all_cases, bool(case_ids))) != 1:
        raise ValueError("select exactly one of --smoke, --all, or --case-id")
    if smoke:
        selected = smoke_virtual_function_scenarios()
    elif case_ids:
        selected = [scenario for scenario in iter_virtual_function_scenarios() if scenario.case_id in case_ids]
        missing = case_ids - {scenario.case_id for scenario in selected}
        if missing:
            raise ValueError(f"Unknown case IDs: {', '.join(sorted(missing))}")
    else:
        selected = list(iter_virtual_function_scenarios())
    if profile:
        selected = [scenario for scenario in selected if scenario.algorithm == profile]
    return selected


def run_local(
    scenarios: Sequence[VirtualFunctionScenario],
    config: ConnectionConfig,
) -> list[dict[str, Any]]:
    root = _connect(
        ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=None,
        )
    )
    _execute(root, f"DROP DATABASE IF EXISTS `{VIRTUAL_FUNCTION_DATABASE}`")
    _execute(
        root,
        f"CREATE DATABASE `{VIRTUAL_FUNCTION_DATABASE}` "
        "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci",
    )
    root.close()

    connection = _connect(
        ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=VIRTUAL_FUNCTION_DATABASE,
        )
    )
    mysqld_version = _server_version(connection)
    results: list[dict[str, Any]] = []
    try:
        for scenario in scenarios:
            try:
                result = run_scenario(scenario, connection, VIRTUAL_FUNCTION_DATABASE)
            except Exception as error:
                result = {
                    "batch_id": VIRTUAL_FUNCTION_BATCH_ID,
                    "batch_kind": VIRTUAL_FUNCTION_BATCH_KIND,
                    "case_id": scenario.case_id,
                    "case_no": scenario.case_no,
                    "family": scenario.family,
                    "source_type": scenario.source_type,
                    "target_type": scenario.target_type,
                    "transition_key": scenario.transition_key,
                    "dependency_mode": scenario.dependency_mode,
                    "algorithm": scenario.algorithm,
                    "data_state": scenario.data_state,
                    "nullability": scenario.nullability,
                    "classification": "FAIL_RUNNER",
                    "runner_error": str(error),
                    "started_at": _utc_now(),
                    "finished_at": _utc_now(),
                }
            result["mysqld_version"] = mysqld_version
            results.append(result)
    finally:
        _execute(connection, f"DROP DATABASE IF EXISTS `{VIRTUAL_FUNCTION_DATABASE}`")
        connection.close()
    return results


def render_summary_markdown(summary: dict[str, Any]) -> str:
    counts = summary.get("counts", {})
    count_lines = "\n".join(f"- {name}: {count}" for name, count in sorted(counts.items()))
    return (
        "# Virtual/function type-upgrade summary\n\n"
        f"- Batch: `{summary.get('batch_id', VIRTUAL_FUNCTION_BATCH_ID)}`\n"
        f"- Profile: `{summary.get('profile', '-')}`\n"
        f"- Selected: {summary.get('selected_count', 0)}\n"
        f"- MySQL: `{summary.get('mysqld_version', '-')}`\n"
        f"- Result: **{'ALL PASS' if summary.get('all_pass') else 'FAIL'}**\n\n"
        "## Classifications\n\n"
        f"{count_lines}\n"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TUCVF virtual/function type-upgrade scenarios")
    parser.add_argument("--profile", choices=VIRTUAL_FUNCTION_PROFILES, default="copy")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--case-id", action="append", default=None)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password-env", default=None)
    parser.add_argument("--database", default=VIRTUAL_FUNCTION_DATABASE)
    parser.add_argument("--external", action="store_true")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    if sum(bool(value) for value in (args.smoke, args.all, bool(args.case_id))) != 1:
        parser.error("select exactly one of --smoke, --all, or --case-id")
    case_ids = set(args.case_id or [])
    scenarios = select_scenarios(
        smoke=args.smoke,
        all_cases=args.all,
        case_ids=case_ids,
        profile=args.profile,
    )
    if not scenarios:
        parser.error("no scenarios selected")
    password = os.environ.get(args.password_env, "") if args.password_env else ""
    config = ConnectionConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        database=None,
    )

    started_at = _utc_now()
    results = run_local(scenarios, config)
    counts = Counter(result["classification"] for result in results)
    all_pass = all(result["classification"] == "PASS" for result in results)
    mysqld_version = next(
        (result.get("mysqld_version") for result in results if result.get("mysqld_version")),
        "-",
    )
    summary = {
        "all_pass": all_pass,
        "batch_id": VIRTUAL_FUNCTION_BATCH_ID,
        "batch_kind": VIRTUAL_FUNCTION_BATCH_KIND,
        "profile": args.profile,
        "selected_count": len(scenarios),
        "executed_count": len(results),
        "counts": dict(sorted(counts.items())),
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
