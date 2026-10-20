from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from mysql_case_factory.inplace_unique_conflict import (
    INPLACE_UNIQUE_BATCH_ID,
    INPLACE_UNIQUE_BATCH_KIND,
    INPLACE_UNIQUE_DATABASE,
    INPLACE_UNIQUE_PROFILES,
    InplaceUniqueScenario,
    inplace_unique_operations,
    iter_inplace_unique_scenarios,
    smoke_inplace_unique_scenarios,
)

INSTANT_SUPPORTED_OPERATIONS = {
    "add_column",
    "drop_column",
    "rename_column",
    "drop_check",
    "drop_generated",
}
CRASH_MARKERS = (
    "lost connection",
    "server has gone away",
    "2013",
    "2006",
    "signal",
    "crash",
)
STABLE_COLUMNS = (
    "id",
    "existing_unique",
    "new_unique",
    "composite_a",
    "composite_b",
    "nullable_unique",
    "value",
    "stable_value",
    "parent_id",
)
INSERT_COLUMNS = STABLE_COLUMNS[1:]
OBJECT_NAMES = {
    "add_index": ("index", "idx_tucui_value"),
    "drop_index": ("index", "idx_tucui_value"),
    "add_unique": ("index", "uk_tucui_value"),
    "drop_unique": ("index", "uk_tucui_value"),
    "rename_index": ("index", "idx_tucui_value_renamed"),
    "add_column": ("column", "extra_value"),
    "drop_column": ("column", "extra_value"),
    "rename_column": ("column", "extra_value_renamed"),
    "add_foreign_key": ("foreign_key", "fk_tucui_parent"),
    "drop_foreign_key": ("foreign_key", "fk_tucui_parent"),
    "drop_check": ("check", "chk_tucui_value"),
    "drop_generated": ("column", "generated_value"),
}


@dataclass(frozen=True)
class ConnectionConfig:
    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    charset: str = "utf8mb4"


@dataclass(frozen=True)
class RunNamespace:
    database: str
    target_table: str
    parent_table: str
    token: str


@dataclass
class WorkerOutcome:
    worker_id: int
    attempts: int = 0
    duplicate_conflicts: int = 0
    other_errors: int = 0
    successful_inserts: int = 0
    transaction_intervals: list[tuple[float, float]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.transaction_intervals is None:
            self.transaction_intervals = []


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_run_namespace(base_database: str, run_token: str) -> RunNamespace:
    digest = _sha256_text(run_token)[:12]
    database = f"{base_database}__run_{digest}"[:64]
    return RunNamespace(
        database=database,
        target_table=f"tucui_target_{digest}",
        parent_table=f"tucui_parent_{digest}",
        token=run_token,
    )


def render_profile_ddl(canonical_ddl: str, profile: str) -> str:
    if profile == "inplace":
        return canonical_ddl
    if profile == "copy":
        return canonical_ddl.replace("ALGORITHM=INPLACE", "ALGORITHM=COPY").replace(
            "LOCK=NONE", "LOCK=SHARED"
        )
    if profile == "instant":
        ddl = re.sub(r",\s*LOCK=NONE\s*;", ";", canonical_ddl, count=1)
        return ddl.replace("ALGORITHM=INPLACE", "ALGORITHM=INSTANT")
    raise ValueError(f"unsupported profile: {profile}")


def classify_ddl_execution(
    operation_id: str,
    profile: str,
    ddl_succeeded: bool,
    ddl_error: str | None = None,
) -> str:
    if ddl_error and any(marker in ddl_error.lower() for marker in CRASH_MARKERS):
        return "FAIL_CRASH"
    expected_success = profile in {"copy", "inplace"} or operation_id in INSTANT_SUPPORTED_OPERATIONS
    if expected_success and ddl_succeeded:
        return "PASS"
    if not expected_success and not ddl_succeeded:
        return "EXPECTED_REJECT"
    return "FAIL_DDL"


def select_scenarios(
    *,
    smoke: bool = False,
    all_cases: bool = False,
    case_ids: set[str] | None = None,
    phase: str | None = None,
) -> list[InplaceUniqueScenario]:
    if sum(bool(value) for value in (smoke, all_cases, bool(case_ids))) != 1:
        raise ValueError("select exactly one of --smoke, --all, or --case-id")
    if smoke:
        selected = smoke_inplace_unique_scenarios()
    elif case_ids:
        selected = [case for case in iter_inplace_unique_scenarios() if case.case_id in case_ids]
        missing = case_ids - {case.case_id for case in selected}
        if missing:
            raise ValueError(f"Unknown case IDs: {', '.join(sorted(missing))}")
    else:
        selected = list(iter_inplace_unique_scenarios())
    if phase:
        selected = [case for case in selected if case.phase == phase]
    return selected


def build_parent_table_sql(parent_table: str) -> str:
    return (
        f"CREATE TABLE `{parent_table}` (\n"
        "  `id` BIGINT UNSIGNED NOT NULL,\n"
        "  PRIMARY KEY (`id`)\n"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;\n"
    )


def build_create_table_sql(
    target_table: str,
    parent_table: str,
    operation_id: str | None = None,
) -> str:
    lines = [
        f"CREATE TABLE `{target_table}` (",
        "  `id` BIGINT NOT NULL AUTO_INCREMENT,",
        "  `existing_unique` VARCHAR(128) NOT NULL,",
        "  `new_unique` VARCHAR(128) NOT NULL,",
        "  `composite_a` VARCHAR(128) NOT NULL,",
        "  `composite_b` VARCHAR(128) NOT NULL,",
        "  `nullable_unique` VARCHAR(128) NULL,",
        "  `value` VARCHAR(128) NOT NULL,",
        "  `stable_value` BIGINT UNSIGNED NOT NULL,",
        "  `parent_id` BIGINT UNSIGNED NOT NULL,",
    ]
    if operation_id in {"drop_column", "rename_column"}:
        lines.append("  `extra_value` VARCHAR(128) NOT NULL DEFAULT '',")
    if operation_id == "drop_generated":
        lines.append(
            "  `generated_value` BIGINT GENERATED ALWAYS AS (`stable_value` * 2) STORED,"
        )
    if operation_id == "drop_check":
        lines.append("  CONSTRAINT `chk_tucui_value` CHECK (`stable_value` >= 0),")
    lines.extend(
        [
            "  PRIMARY KEY (`id`),",
            "  UNIQUE KEY `uk_tucui_existing_unique` (`existing_unique`),",
            "  UNIQUE KEY `uk_tucui_new_unique` (`new_unique`),",
            "  UNIQUE KEY `uk_tucui_composite` (`composite_a`, `composite_b`),",
            "  UNIQUE KEY `uk_tucui_nullable_unique` (`nullable_unique`),",
        ]
    )
    if operation_id in {"drop_index", "rename_index"}:
        lines.append("  KEY `idx_tucui_value` (`value`),")
    if operation_id == "drop_unique":
        lines.append("  UNIQUE KEY `uk_tucui_value` (`value`),")
    if operation_id == "drop_foreign_key":
        lines.append(
            "  CONSTRAINT `fk_tucui_parent` FOREIGN KEY (`parent_id`) "
            f"REFERENCES `{parent_table}` (`id`),"
        )
    if lines and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;")
    return "\n".join(lines) + "\n"


def build_seed_values(
    scenario: InplaceUniqueScenario,
    row_no: int,
    data_state: str,
) -> dict[str, Any]:
    prefix = "BOUNDARY" if data_state == "boundary" else "SEED"
    return {
        "existing_unique": f"TUCUI-{prefix}-{row_no:06d}",
        "new_unique": f"TUCUI-NEW-{prefix}-{row_no:06d}",
        "composite_a": f"TUCUI-A-{prefix}-{row_no:06d}",
        "composite_b": f"TUCUI-B-{prefix}-{row_no:06d}",
        "nullable_unique": f"TUCUI-NULL-{prefix}-{row_no:06d}",
        "value": f"TUCUI-VALUE-{prefix}-{row_no:06d}",
        "stable_value": row_no,
        "parent_id": 1,
    }


def _surface_values(
    scenario: InplaceUniqueScenario,
    row: dict[str, Any],
    pattern: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    surface = scenario.conflict_surface
    if pattern == "seed_duplicate":
        base = row.copy()
        worker = row.copy()
    elif pattern == "concurrent_duplicate":
        base = row.copy()
        worker = row.copy()
    elif pattern == "semantic_collision":
        base = row.copy()
        worker = row.copy()
        if surface == "existing_unique":
            base["existing_unique"] = "Tucui-Semantic-Value"
            worker["existing_unique"] = "TUCUI-SEMANTIC-VALUE"
        elif surface == "new_unique":
            base["new_unique"] = "Tucui-Semantic-New"
            worker["new_unique"] = "TUCUI-SEMANTIC-NEW"
        elif surface == "composite_unique":
            base["composite_a"] = "Tucui-Semantic-A"
            base["composite_b"] = "Tucui-Semantic-B"
            worker["composite_a"] = "TUCUI-SEMANTIC-A"
            worker["composite_b"] = "TUCUI-SEMANTIC-B"
        elif surface == "nullable_unique":
            base["nullable_unique"] = "Tucui-Semantic-Nullable"
            worker["nullable_unique"] = "TUCUI-SEMANTIC-NULLABLE"
        else:
            raise AssertionError(surface)
    elif pattern == "boundary_duplicate":
        base = row.copy()
        worker = row.copy()
        if surface == "existing_unique":
            base["existing_unique"] = ""
            worker["existing_unique"] = ""
        elif surface == "new_unique":
            base["new_unique"] = ""
            worker["new_unique"] = ""
        elif surface == "composite_unique":
            base["composite_a"] = ""
            base["composite_b"] = ""
            worker["composite_a"] = ""
            worker["composite_b"] = ""
        elif surface == "nullable_unique":
            base["nullable_unique"] = ""
            worker["nullable_unique"] = ""
        else:
            raise AssertionError(surface)
    else:
        raise AssertionError(pattern)
    return base, worker


def build_case_rows(
    scenario: InplaceUniqueScenario,
    data_state: str,
    seed_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    seed_rows = [build_seed_values(scenario, row_no, data_state) for row_no in range(1, seed_count + 1)]
    base_template = build_seed_values(scenario, seed_count + 1, data_state)
    post_template = build_seed_values(scenario, seed_count + 2, data_state)
    base_row, worker_row = _surface_values(scenario, base_template, scenario.conflict_pattern)
    return seed_rows, base_row, worker_row, post_template


def duplicate_insert_sql(table: str) -> tuple[str, tuple[str, ...]]:
    columns = INSERT_COLUMNS
    placeholders = ", ".join(["%s"] * len(columns))
    quoted_columns = ", ".join(f"`{column}`" for column in columns)
    sql = f"INSERT INTO `{table}` ({quoted_columns}) VALUES ({placeholders})"
    return sql, columns


def expected_object_state(
    operation_id: str,
    ddl_succeeded: bool,
) -> list[dict[str, Any]]:
    if operation_id in {"add_index", "add_unique", "add_column", "add_foreign_key"}:
        kind, name = OBJECT_NAMES[operation_id]
        return [{"kind": kind, "name": name, "present": ddl_succeeded}]
    if operation_id in {"drop_index", "drop_unique", "drop_column", "drop_foreign_key", "drop_check", "drop_generated"}:
        kind, name = OBJECT_NAMES[operation_id]
        return [{"kind": kind, "name": name, "present": not ddl_succeeded}]
    if operation_id == "rename_index":
        return [
            {"kind": "index", "name": "idx_tucui_value_renamed", "present": ddl_succeeded},
            {"kind": "index", "name": "idx_tucui_value", "present": not ddl_succeeded},
        ]
    if operation_id == "rename_column":
        return [
            {"kind": "column", "name": "extra_value_renamed", "present": ddl_succeeded},
            {"kind": "column", "name": "extra_value", "present": not ddl_succeeded},
        ]
    raise AssertionError(operation_id)


def _connect(config: ConnectionConfig):
    import pymysql

    return pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        charset=config.charset,
        autocommit=True,
    )


def _server_version(connection: Any) -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        return str(cursor.fetchone()[0])


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


def _insert_row(connection: Any, table: str, row: dict[str, Any]) -> None:
    sql, columns = duplicate_insert_sql(table)
    params = tuple(row[column] for column in columns)
    _execute(connection, sql, params)


def _worker_thread(
    config: ConnectionConfig,
    table: str,
    worker_row: dict[str, Any],
    worker_id: int,
    start_barrier: threading.Barrier,
    ready_event: threading.Event,
    stop_event: threading.Event,
    outcome: WorkerOutcome,
    lock: threading.Lock,
    hold_seconds: float,
    max_attempts: int,
    hold_across_ddl: bool,
) -> None:
    connection = None
    try:
        connection = _connect(config)
        start_barrier.wait(timeout=30)
        for attempt in range(max_attempts):
            if stop_event.is_set() and not (hold_across_ddl and attempt == 0):
                break
            transaction_start = time.monotonic()
            try:
                connection.begin()
                _insert_row(connection, table, worker_row)
                with lock:
                    outcome.successful_inserts += 1
            except Exception as error:
                text = str(error)
                with lock:
                    if "1062" in text or "Duplicate entry" in text:
                        outcome.duplicate_conflicts += 1
                    else:
                        outcome.other_errors += 1
            finally:
                with lock:
                    outcome.attempts += 1
                    if not ready_event.is_set():
                        ready_event.set()
                if hold_across_ddl and attempt == 0:
                    stop_event.wait(timeout=30)
                else:
                    time.sleep(hold_seconds)
                try:
                    connection.commit()
                except Exception:
                    connection.rollback()
                transaction_end = time.monotonic()
                with lock:
                    outcome.transaction_intervals.append((transaction_start, transaction_end))
            if stop_event.is_set() and not (hold_across_ddl and attempt == 0):
                break
    except Exception:
        with lock:
            outcome.other_errors += 1
        if not ready_event.is_set():
            ready_event.set()
    finally:
        if not ready_event.is_set():
            ready_event.set()
        if connection is not None:
            connection.close()


def _ddl_thread(
    config: ConnectionConfig,
    ddl_sql: str,
    start_barrier: threading.Barrier,
    ready_events: Sequence[threading.Event],
    stop_event: threading.Event,
    phase: str,
    result: dict[str, Any],
) -> None:
    connection = None
    try:
        connection = _connect(config)
        start_barrier.wait(timeout=30)
        for event in ready_events:
            if not event.wait(timeout=30):
                result["ddl_error"] = "worker readiness timeout"
                result["ddl_succeeded"] = False
                stop_event.set()
                return
        if phase == "before_and_during_ddl":
            time.sleep(0.1)
        # Adding a foreign key with INPLACE requires this session setting.
        _execute(connection, "SET FOREIGN_KEY_CHECKS=OFF")
        result["ddl_start"] = time.monotonic()
        try:
            _execute(connection, ddl_sql)
            result["ddl_succeeded"] = True
            result["ddl_error"] = None
        except Exception as error:
            result["ddl_succeeded"] = False
            result["ddl_error"] = str(error)
        result["ddl_end"] = time.monotonic()
    except Exception as error:
        result["ddl_succeeded"] = False
        result["ddl_error"] = str(error)
    finally:
        stop_event.set()
        if connection is not None:
            connection.close()


def _validate_operation_schema(
    connection: Any,
    database: str,
    table: str,
    operation_id: str,
    ddl_succeeded: bool,
) -> list[str]:
    errors: list[str] = []
    for expectation in expected_object_state(operation_id, ddl_succeeded):
        kind = expectation["kind"]
        name = expectation["name"]
        present = expectation["present"]
        if kind == "column":
            row = _query_one(
                connection,
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
                (database, table, name),
            )
            actual = bool(row and row[0])
        elif kind == "index":
            row = _query_one(
                connection,
                "SELECT COUNT(*) FROM information_schema.STATISTICS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_NAME=%s",
                (database, table, name),
            )
            actual = bool(row and row[0])
        elif kind == "foreign_key":
            row = _query_one(
                connection,
                "SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND CONSTRAINT_NAME=%s "
                "AND REFERENCED_TABLE_NAME IS NOT NULL",
                (database, table, name),
            )
            actual = bool(row and row[0])
        elif kind == "check":
            row = _query_one(
                connection,
                "SELECT COUNT(*) FROM information_schema.CHECK_CONSTRAINTS "
                "WHERE CONSTRAINT_SCHEMA=%s AND CONSTRAINT_NAME=%s",
                (database, name),
            )
            actual = bool(row and row[0])
        else:
            errors.append(f"unknown schema object kind: {kind}")
            continue
        if actual != present:
            errors.append(f"{kind} {name} expected present={present}, actual={actual}")
    return errors


def _auto_increment(connection: Any, database: str, table: str) -> int | None:
    row = _query_one(
        connection,
        "SELECT AUTO_INCREMENT FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
        (database, table),
    )
    return int(row[0]) if row and row[0] is not None else None


def _stable_rows(connection: Any, table: str) -> list[tuple[Any, ...]]:
    columns = ", ".join(f"`{column}`" for column in STABLE_COLUMNS)
    return _query_all(connection, f"SELECT {columns} FROM `{table}` ORDER BY `id`")


def _expected_rows(seed_rows: list[dict[str, Any]], base_row: dict[str, Any], post_row: dict[str, Any]) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []
    for row in [*seed_rows, base_row, post_row]:
        # ID is generated by the server and may contain gaps after duplicate
        # attempts, so validation uses the stable non-ID columns.
        rows.append(tuple(row[column] for column in STABLE_COLUMNS[1:]))
    return rows


def run_scenario(
    scenario: InplaceUniqueScenario,
    config: ConnectionConfig,
    *,
    filler_rows: int,
    hold_seconds: float,
    max_attempts: int,
    profile: str = "inplace",
) -> dict[str, Any]:
    run_token = f"{scenario.case_id}-{time.time_ns()}"
    namespace = make_run_namespace(config.database or INPLACE_UNIQUE_DATABASE, run_token)
    connection_config = ConnectionConfig(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=namespace.database,
    )
    control = None
    started_at = _utc_now()
    result: dict[str, Any] = {
        "batch_id": INPLACE_UNIQUE_BATCH_ID,
        "batch_kind": INPLACE_UNIQUE_BATCH_KIND,
        "case_id": scenario.case_id,
        "case_no": scenario.case_no,
        "operation_id": scenario.operation_id,
        "conflict_surface": scenario.conflict_surface,
        "conflict_pattern": scenario.conflict_pattern,
        "phase": scenario.phase,
        "workers": scenario.workers,
        "data_state": scenario.data_state,
        "database": namespace.database,
        "target_table": namespace.target_table,
        "started_at": started_at,
    }
    try:
        root_config = ConnectionConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=None,
        )
        control = _connect(root_config)
        _execute(control, f"DROP DATABASE IF EXISTS `{namespace.database}`")
        _execute(
            control,
            f"CREATE DATABASE `{namespace.database}` "
            "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci",
        )
        control.select_db(namespace.database)
        _execute(control, build_parent_table_sql(namespace.parent_table))
        _execute(control, "INSERT INTO `%s` (`id`) VALUES (1)" % namespace.parent_table)
        _execute(
            control,
            build_create_table_sql(
                namespace.target_table,
                namespace.parent_table,
                scenario.operation_id,
            ),
        )
        seed_count = max(8, filler_rows)
        seed_rows, base_row, worker_row, post_row = build_case_rows(
            scenario,
            scenario.data_state,
            seed_count,
        )
        for row in seed_rows:
            _insert_row(control, namespace.target_table, row)
        _insert_row(control, namespace.target_table, base_row)
        auto_increment_before = _auto_increment(control, namespace.database, namespace.target_table)
        operation = next(
            operation
            for operation in inplace_unique_operations()
            if operation.operation_id == scenario.operation_id
        )
        ddl_sql = operation.ddl_sql.replace("`tucui_unique_target`", f"`{namespace.target_table}`")
        ddl_sql = ddl_sql.replace("`tucui_unique_parent`", f"`{namespace.parent_table}`")
        ddl_sql = render_profile_ddl(ddl_sql, profile)
        result["profile"] = profile
        result["ddl_sql"] = ddl_sql
        start_barrier = threading.Barrier(scenario.workers + 1)
        stop_event = threading.Event()
        ready_events = [threading.Event() for _ in range(scenario.workers)]
        outcomes = [WorkerOutcome(index) for index in range(scenario.workers)]
        lock = threading.Lock()
        ddl_result: dict[str, Any] = {}
        hold_across_ddl = scenario.phase == "across_ddl_transaction" and profile != "copy"
        with ThreadPoolExecutor(max_workers=scenario.workers + 1) as executor:
            futures = []
            ddl_future = executor.submit(
                _ddl_thread,
                connection_config,
                ddl_sql,
                start_barrier,
                ready_events,
                stop_event,
                scenario.phase,
                ddl_result,
            )
            futures.append(ddl_future)
            for index in range(scenario.workers):
                futures.append(
                    executor.submit(
                        _worker_thread,
                        connection_config,
                        namespace.target_table,
                        worker_row,
                        index,
                        start_barrier,
                        ready_events[index],
                        stop_event,
                        outcomes[index],
                        lock,
                        hold_seconds,
                        max_attempts,
                        hold_across_ddl and index == 0,
                    )
                )
            for future in as_completed(futures):
                future.result()
        ddl_succeeded = bool(ddl_result.get("ddl_succeeded"))
        ddl_error = ddl_result.get("ddl_error")
        result["ddl_succeeded"] = ddl_succeeded
        result["ddl_error"] = ddl_error
        result["ddl_start"] = ddl_result.get("ddl_start")
        result["ddl_end"] = ddl_result.get("ddl_end")
        result["worker_attempts"] = sum(outcome.attempts for outcome in outcomes)
        result["duplicate_conflicts"] = sum(outcome.duplicate_conflicts for outcome in outcomes)
        result["other_dml_errors"] = sum(outcome.other_errors for outcome in outcomes)
        result["successful_worker_inserts"] = sum(outcome.successful_inserts for outcome in outcomes)
        intervals = [interval for outcome in outcomes for interval in outcome.transaction_intervals]
        ddl_start = ddl_result.get("ddl_start")
        ddl_end = ddl_result.get("ddl_end")
        overlap = bool(
            ddl_start is not None
            and ddl_end is not None
            and any(start < ddl_end and end > ddl_start for start, end in intervals)
        )
        result["overlap"] = overlap
        _insert_row(control, namespace.target_table, post_row)
        auto_increment_after = _auto_increment(control, namespace.database, namespace.target_table)
        result["auto_increment_before"] = auto_increment_before
        result["auto_increment_after"] = auto_increment_after
        expected = _expected_rows(seed_rows, base_row, post_row)
        actual = [row[1:] for row in _stable_rows(control, namespace.target_table)]
        validation_errors: list[str] = []
        if len(actual) != len(expected):
            validation_errors.append(f"row count expected {len(expected)}, actual {len(actual)}")
        if actual != expected:
            validation_errors.append("stable column values differ from expected rows")
        if result["duplicate_conflicts"] < 1:
            validation_errors.append("no duplicate conflict was observed")
        if result["other_dml_errors"] > 0:
            validation_errors.append("unexpected non-duplicate DML error occurred")
        if result["successful_worker_inserts"] != 0:
            validation_errors.append("worker unexpectedly inserted a row")
        if auto_increment_before is not None and auto_increment_after is not None and auto_increment_after < auto_increment_before:
            validation_errors.append("AUTO_INCREMENT regressed")
        schema_errors = _validate_operation_schema(
            control,
            namespace.database,
            namespace.target_table,
            scenario.operation_id,
            ddl_succeeded,
        )
        validation_errors.extend(schema_errors)
        result["validation_errors"] = validation_errors
        classification = classify_ddl_execution(
            scenario.operation_id,
            result["profile"],
            ddl_succeeded,
            ddl_error,
        )
        if classification == "PASS" and not overlap:
            classification = "NO_OVERLAP"
        if classification == "PASS" and validation_errors:
            classification = "FAIL_VALIDATION"
        result["classification"] = classification
        result["finished_at"] = _utc_now()
        result["mysqld_version"] = _server_version(control)
        return result
    except Exception as error:
        result["ddl_succeeded"] = False
        result["ddl_error"] = str(error)
        result["classification"] = "FAIL_CRASH" if any(marker in str(error).lower() for marker in CRASH_MARKERS) else "FAIL_VALIDATION"
        result["validation_errors"] = [str(error)]
        result["finished_at"] = _utc_now()
        return result
    finally:
        if control is not None:
            try:
                _execute(control, f"DROP DATABASE IF EXISTS `{namespace.database}`")
            except Exception:
                pass
            control.close()


def run_local(
    scenarios: Sequence[InplaceUniqueScenario],
    config: ConnectionConfig,
    *,
    filler_rows: int,
    hold_seconds: float,
    max_attempts: int,
    profile: str,
) -> list[dict[str, Any]]:
    return [
        run_scenario(
            scenario,
            config,
            filler_rows=filler_rows,
            hold_seconds=hold_seconds,
            max_attempts=max_attempts,
            profile=profile,
        )
        for scenario in scenarios
    ]


def _write_results(path: Path, results: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")


def _write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path = path.with_suffix(".md")
    markdown_path.write_text(render_summary_markdown(summary), encoding="utf-8")


def render_summary_markdown(summary: dict[str, Any]) -> str:
    counts = summary.get("counts", {})
    count_lines = "\n".join(f"- {name}: {count}" for name, count in sorted(counts.items()))
    return (
        "# TUCUI execution summary\n\n"
        f"- Batch: `{summary.get('batch_id', INPLACE_UNIQUE_BATCH_ID)}`\n"
        f"- Profile: `{summary.get('profile', '-')}`\n"
        f"- Selected: {summary.get('selected_count', 0)}\n"
        f"- MySQL: `{summary.get('mysqld_version', '-')}`\n"
        f"- Result: **{'ALL PASS' if summary.get('all_pass') else 'FAIL'}**\n\n"
        "## Classifications\n\n"
        f"{count_lines}\n"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TUCUI INPLACE unique-conflict scenarios")
    parser.add_argument("--profile", choices=INPLACE_UNIQUE_PROFILES, default="copy")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--case-id", action="append", default=None)
    parser.add_argument("--phase", choices=("during_ddl", "before_and_during_ddl", "across_ddl_transaction"), default=None)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password-env", default=None)
    parser.add_argument("--database", default=INPLACE_UNIQUE_DATABASE)
    parser.add_argument("--filler-rows", type=int, default=128)
    parser.add_argument("--hold-seconds", type=float, default=1.0)
    parser.add_argument("--max-attempts", type=int, default=10000)
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
        phase=args.phase,
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
    results = run_local(
        scenarios,
        config,
        filler_rows=args.filler_rows,
        hold_seconds=args.hold_seconds,
        max_attempts=args.max_attempts,
        profile=args.profile,
    )
    counts = Counter(result["classification"] for result in results)
    all_pass = all(result["classification"] in {"PASS", "EXPECTED_REJECT"} for result in results)
    mysqld_version = next((result.get("mysqld_version") for result in results if result.get("mysqld_version")), "-")
    summary = {
        "all_pass": all_pass,
        "batch_id": INPLACE_UNIQUE_BATCH_ID,
        "batch_kind": INPLACE_UNIQUE_BATCH_KIND,
        "profile": args.profile,
        "selected_count": len(scenarios),
        "executed_count": len(results),
        "counts": dict(sorted(counts.items())),
        "mysqld_version": mysqld_version,
        "started_at": started_at,
        "finished_at": _utc_now(),
    }
    _write_results(args.results, results)
    _write_summary(args.summary, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
