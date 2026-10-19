"""Concurrency runner for the TUCPK primary-key type-upgrade batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import threading
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from mysql_case_factory.type_upgrade_primary_key import (
    PRIMARY_KEY_DATABASE,
    PRIMARY_KEY_PROFILES,
    PrimaryKeyScenario,
    iter_primary_key_scenarios,
    smoke_primary_key_scenarios,
)
from mysql_case_factory.type_upgrade_runner import LocalMySQLServer

ALL_COLUMN_NAMES = (
    "row_no",
    "tenant_id",
    "worker_id",
    "seq_no",
    "phase",
    "c_tinyint",
    "c_smallint",
    "c_mediumint",
    "c_int",
    "c_bigint",
    "c_utinyint",
    "c_usmallint",
    "c_umediumint",
    "c_uint",
    "c_ubigint",
    "c_char",
    "c_varchar",
    "c_binary",
    "c_varbinary",
    "c_decimal",
    "c_bit",
    "c_text",
    "c_blob",
)

_COLUMN_DEFINITIONS = {
    "row_no": "BIGINT NOT NULL",
    "tenant_id": "BIGINT NOT NULL",
    "worker_id": "INT NOT NULL",
    "seq_no": "BIGINT NOT NULL",
    "phase": "VARCHAR(32) NOT NULL",
    "c_tinyint": "TINYINT NULL",
    "c_smallint": "SMALLINT NULL",
    "c_mediumint": "MEDIUMINT NULL",
    "c_int": "INT NULL",
    "c_bigint": "BIGINT NULL",
    "c_utinyint": "TINYINT UNSIGNED NULL",
    "c_usmallint": "SMALLINT UNSIGNED NULL",
    "c_umediumint": "MEDIUMINT UNSIGNED NULL",
    "c_uint": "INT UNSIGNED NULL",
    "c_ubigint": "BIGINT UNSIGNED NULL",
    "c_char": "CHAR(32) NULL",
    "c_varchar": "VARCHAR(128) NULL",
    "c_binary": "BINARY(16) NULL",
    "c_varbinary": "VARBINARY(32) NULL",
    "c_decimal": "DECIMAL(20,4) NULL",
    "c_bit": "BIT(16) NULL",
    "c_text": "TEXT NULL",
    "c_blob": "BLOB NULL",
}


@dataclass(frozen=True)
class WorkerResult:
    worker_id: int
    row_no: int
    committed: bool
    pk_value: Any
    last_insert_id: int | None
    error: str | None
    started_at: str
    finished_at: str
    started_monotonic: float = 0.0
    finished_monotonic: float = 0.0
    secondary_row_no: int | None = None
    secondary_pk_value: Any = None


@dataclass(frozen=True)
class ConnectionConfig:
    socket_path: Path | None = None
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str | None = None


def _connect(config: ConnectionConfig, *, with_database: bool = True):
    import pymysql

    kwargs: dict[str, Any] = {
        "user": config.user,
        "autocommit": True,
        "charset": "utf8mb4",
    }
    if config.socket_path is not None:
        kwargs["unix_socket"] = str(config.socket_path)
    else:
        kwargs.update({"host": config.host, "port": config.port})
    if config.password is not None:
        kwargs["password"] = config.password
    if with_database:
        kwargs["database"] = PRIMARY_KEY_DATABASE
    return pymysql.connect(**kwargs)


@dataclass(frozen=True)
class ScenarioResult:
    case_id: str
    profile: str
    outcome: str
    error: str | None = None
    overlap: bool = False
    worker_results: tuple[WorkerResult, ...] = ()
    source_range_retries: int = 0
    elapsed_ms: int = 0

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["worker_results"] = [_json_safe(asdict(worker)) for worker in self.worker_results]
        return _json_safe(payload)


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _table_name(scenario: PrimaryKeyScenario, profile: str) -> str:
    prefix = "tucpks" if scenario.smoke else "tucpk"
    return f"tab_{prefix}_{scenario.case_no:06d}_{profile}"


def _pk_expression(scenario: PrimaryKeyScenario) -> str:
    if scenario.pk_prefix_length is None:
        return "pk"
    return f"pk({scenario.pk_prefix_length})"


def build_create_table_sql(
    scenario: PrimaryKeyScenario,
    table: str,
    type_name: str,
    *,
    auto_increment_start: int | None,
) -> str:
    pk = f"pk {type_name} NOT NULL"
    if scenario.auto_increment:
        pk += " AUTO_INCREMENT"
    columns = [pk]
    columns.extend(f"{name} {definition}" for name, definition in _COLUMN_DEFINITIONS.items())

    indexes: list[str] = []
    if scenario.key_shape == "single_pk":
        indexes.append(f"PRIMARY KEY({_pk_expression(scenario)})")
    elif scenario.key_shape == "composite_pk_pk_first":
        indexes.append(f"PRIMARY KEY({_pk_expression(scenario)}, tenant_id)")
    else:
        indexes.append(f"PRIMARY KEY(tenant_id, {_pk_expression(scenario)})")
        indexes.append(f"KEY idx_pk ({_pk_expression(scenario)})")
    indexes.append("UNIQUE KEY uk_row_no (row_no)")

    options = [f"ENGINE=InnoDB ROW_FORMAT={scenario.row_format}"]
    if scenario.family == "character":
        options.extend(["DEFAULT CHARSET=ascii", "COLLATE=ascii_general_ci"])
    if auto_increment_start is not None:
        options.append(f"AUTO_INCREMENT={auto_increment_start}")
    return f"CREATE TABLE {table} ({', '.join([*columns, *indexes])}) {' '.join(options)};"


def build_insert_sql(
    scenario: PrimaryKeyScenario,
    table: str,
    *,
    include_pk: bool,
    style: str,
    positional: bool = False,
) -> tuple[str, tuple[str, ...]]:
    columns = ("pk", *ALL_COLUMN_NAMES) if include_pk else ALL_COLUMN_NAMES
    if positional:
        return f"INSERT INTO {table} VALUES ({', '.join(['%s'] * len(columns))});", columns
    if style.startswith("insert_select"):
        return f"INSERT INTO {table} ({','.join(columns)}) SELECT {', '.join(['%s'] * len(columns))};", columns
    return f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))});", columns


def classify_scenario_execution(
    scenario: PrimaryKeyScenario,
    profile: str,
    ddl_succeeded: bool,
    error: str | None,
) -> str:
    lowered = (error or "").lower()
    if "lost connection" in lowered or "server has gone away" in lowered or "error 2013" in lowered:
        return "FAIL_CRASH"
    expected_success = (profile == "inplace" and scenario.inplace_expected) or (
        profile == "instant" and scenario.instant_expected
    )
    if profile == "copy":
        expected_success = True
    if expected_success and ddl_succeeded:
        return "PASS"
    if not expected_success and not ddl_succeeded:
        return "EXPECTED_REJECT"
    if expected_success and not ddl_succeeded:
        return "FAIL_DDL"
    return "FAIL_UNEXPECTED_DDL_SUCCESS"


def _integer_range(type_name: str) -> tuple[int, int]:
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


def _type_length(type_name: str) -> int:
    match = re.search(r"\((\d+)", type_name)
    if match:
        return int(match.group(1))
    if type_name in {"CHAR", "BINARY", "BIT"}:
        return 1
    return 0


def _decimal_max(type_name: str) -> str:
    match = re.search(r"\((\d+),(\d+)\)", type_name)
    if not match:
        return "9999999999"
    precision, scale = int(match.group(1)), int(match.group(2))
    return "9" * (precision - scale) + ("." + "9" * scale if scale else "")


def _source_pk_value(scenario: PrimaryKeyScenario, index: int, *, boundary: bool = False) -> Any:
    family, source = scenario.family, scenario.source_type
    if family == "integer":
        _, maximum = _integer_range(source)
        return maximum if boundary else max(0, index - 1)
    if family == "decimal":
        return _decimal_max(source) if boundary else str(index)
    if family == "bit":
        width = _type_length(source)
        value = (1 << width) - 1 if boundary else index
        return value.to_bytes(max(1, (width + 7) // 8), "big")
    if family == "character":
        length = _type_length(source)
        if source.startswith("CHAR"):
            length = min(length, 32)
        value = ("z" if boundary else "p") + f"{index:08d}"
        return value[:length] if length else value
    if family == "binary":
        length = _type_length(source)
        size = min(length, 32) or 1
        return (b"\xff" * size if boundary else index.to_bytes(size, "big"))
    if family in {"text", "blob"}:
        prefix = ("z" if boundary else "p") + f"{index:08d}"
        suffix = "-" + ("z" if boundary else "s") + f"{index:08d}"
        value = prefix + suffix
        return value.encode("ascii") if family == "blob" else value
    raise AssertionError(family)


def _target_pk_value(scenario: PrimaryKeyScenario, index: int) -> Any:
    if scenario.family == "integer":
        _, source_max = _integer_range(scenario.source_type)
        return source_max + index

    target = scenario.target_type
    if scenario.family == "decimal":
        match = re.search(r"\((\d+),(\d+)\)", target)
        if not match:
            return str(index)
        precision, scale = int(match.group(1)), int(match.group(2))
        integer_digits = precision - scale
        capacity = 10**integer_digits
        # Keep values comfortably inside the target range while remaining
        # unique for the maximum canonical worker count (16) and final inserts.
        modulus = max(17, min(capacity - 11, 10**9))
        value = 10 + (index % modulus)
        return f"{value}.{(index % (10**scale)):0{scale}d}" if scale else str(value)

    if scenario.family == "bit":
        width = _type_length(target)
        modulus = min(1 << width, 10**9)
        value = index % modulus
        return value.to_bytes(max(1, (width + 7) // 8), "big")

    if scenario.family == "character":
        length = _type_length(target)
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
        value = index
        encoded = ""
        while value:
            value, remainder = divmod(value, 36)
            encoded = alphabet[remainder] + encoded
        encoded = ("t" + encoded)[:length]
        return encoded.ljust(length, "0") if target.startswith("CHAR") else encoded

    if scenario.family == "binary":
        length = _type_length(target)
        return (10 + index).to_bytes(length, "big")

    if scenario.family in {"text", "blob"}:
        value = f"target-{index:08d}-unique-suffix"
        return value.encode("ascii") if scenario.family == "blob" else value

    raise AssertionError(scenario.family)


def _canary_values(
    row_no: int,
    worker_id: int,
    seq_no: int,
    phase: str,
    *,
    updated: bool = False,
) -> dict[str, Any]:
    suffix = "-updated" if updated else ""
    return {
        "row_no": row_no,
        "tenant_id": 7000 + (worker_id % 13),
        "worker_id": worker_id,
        "seq_no": seq_no,
        "phase": phase,
        "c_tinyint": (row_no % 128) - 64,
        "c_smallint": (row_no % 32768) - 16384,
        "c_mediumint": (row_no % 100000) - 50000,
        "c_int": (row_no % 1000000) - 500000,
        "c_bigint": row_no * 1000003,
        "c_utinyint": row_no % 256,
        "c_usmallint": row_no % 65536,
        "c_umediumint": row_no % 1000000,
        "c_uint": row_no % 4294967295,
        "c_ubigint": row_no * 1000000007,
        "c_char": (f"c{row_no % 100000}" + suffix)[:32],
        "c_varchar": (f"varchar-{row_no}-{phase}{suffix}")[:128],
        "c_binary": (row_no % 4294967295).to_bytes(16, "big"),
        "c_varbinary": (row_no % 4294967295).to_bytes(8, "big"),
        "c_decimal": f"{row_no % 100000}.{row_no % 10000:04d}",
        "c_bit": (row_no % 65536).to_bytes(2, "big"),
        "c_text": f"text-{row_no}-{phase}{suffix}",
        "c_blob": (f"blob-{row_no}-{phase}{suffix}").encode("ascii"),
    }


def _execute_insert(
    connection: Any,
    scenario: PrimaryKeyScenario,
    table: str,
    values: Sequence[Any],
) -> int | None:
    mapping = dict(zip(ALL_COLUMN_NAMES, values, strict=True))
    row_no = int(mapping["row_no"])
    second_row_no = row_no + 1
    second_values = _worker_values_from_mapping(
        scenario,
        mapping,
        second_row_no,
    )

    if scenario.family == "integer":
        columns = ALL_COLUMN_NAMES
        if scenario.insert_style == "null_pk_positional":
            sql = f"INSERT INTO {table} VALUES ({', '.join(['%s'] * (len(columns) + 1))});"
            parameters = (None, *values)
        elif scenario.insert_style == "insert_select_omit_pk":
            sql = (
                f"INSERT INTO {table} ({','.join(columns)}) "
                f"SELECT {', '.join(['%s'] * len(columns))};"
            )
            parameters = tuple(values)
        elif scenario.insert_style == "multi_row_omit_pk":
            placeholders = ", ".join(["%s"] * len(columns))
            sql = (
                f"INSERT INTO {table} ({','.join(columns)}) "
                f"VALUES ({placeholders}), ({placeholders});"
            )
            parameters = (*values, *second_values)
        else:
            sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))});"
            parameters = tuple(values)
    else:
        columns = ("pk", *ALL_COLUMN_NAMES)
        if scenario.insert_style == "explicit_pk_partial_columns":
            selected = ("row_no", "tenant_id", "worker_id", "seq_no", "phase", "c_int", "c_char")
            selected_columns = ("pk", *selected)
            sql = (
                f"INSERT INTO {table} ({','.join(selected_columns)}) "
                f"VALUES ({', '.join(['%s'] * len(selected_columns))});"
            )
            parameters = (
                _target_pk_value(scenario, row_no),
                *(mapping[name] for name in selected),
            )
            with connection.cursor() as cursor:
                cursor.execute(sql, parameters)
                return cursor.lastrowid or None

        if scenario.insert_style == "insert_select_explicit_pk":
            sql = (
                f"INSERT INTO {table} ({','.join(columns)}) "
                f"SELECT {', '.join(['%s'] * len(columns))};"
            )
            parameters = (_target_pk_value(scenario, row_no), *values)
        elif scenario.insert_style == "multi_row_explicit_pk":
            placeholders = ", ".join(["%s"] * len(columns))
            sql = (
                f"INSERT INTO {table} ({','.join(columns)}) "
                f"VALUES ({placeholders}), ({placeholders});"
            )
            parameters = (
                _target_pk_value(scenario, row_no),
                *values,
                _target_pk_value(scenario, second_row_no),
                *second_values,
            )
        else:
            sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))});"
            parameters = (_target_pk_value(scenario, row_no), *values)

    with connection.cursor() as cursor:
        cursor.execute(sql, parameters)
        return cursor.lastrowid or None


def _worker_values_from_mapping(
    scenario: PrimaryKeyScenario,
    mapping: Mapping[str, Any],
    row_no: int,
) -> list[Any]:
    values = _canary_values(
        row_no,
        int(mapping["worker_id"]),
        row_no,
        str(mapping["phase"]),
        updated=scenario.dml_mode == "insert_update_all_canaries",
    )
    return [values[column] for column in ALL_COLUMN_NAMES]


def _worker_values(scenario: PrimaryKeyScenario, worker_id: int, row_no: int, phase: str) -> list[Any]:
    values = _canary_values(row_no, worker_id, row_no, phase)
    return [values[column] for column in ALL_COLUMN_NAMES]


def _worker_run(
    connection_config: ConnectionConfig,
    scenario: PrimaryKeyScenario,
    table: str,
    worker_id: int,
    row_no: int,
    phase: str,
    *,
    hold_transaction: bool = False,
    start_event: threading.Event | None = None,
) -> WorkerResult:
    import pymysql

    connection = _connect(connection_config)
    connection.autocommit(False)
    if start_event is not None:
        start_event.wait()
    started_at = datetime.now(timezone.utc).isoformat()
    started_monotonic = time.monotonic()
    committed = False
    pk_value = None
    secondary_pk_value = None
    last_insert_id = None
    error = None
    is_multi_row = scenario.insert_style in {"multi_row_omit_pk", "multi_row_explicit_pk"}
    try:
        values = _worker_values(scenario, worker_id, row_no, phase)
        if scenario.dml_mode == "insert_update_all_canaries":
            updated_values = _canary_values(row_no, worker_id, row_no, phase, updated=True)
            values = [updated_values[column] for column in ALL_COLUMN_NAMES]
        last_insert_id = _execute_insert(connection, scenario, table, values)
        if scenario.family != "integer":
            pk_value = _target_pk_value(scenario, row_no)
            if is_multi_row:
                secondary_pk_value = _target_pk_value(scenario, row_no + 1)
        if hold_transaction:
            time.sleep(0.1)
        if scenario.dml_mode == "commit_rollback_mix" and worker_id % 2 == 0:
            connection.rollback()
        else:
            connection.commit()
            committed = True
    except Exception as exc:  # Concurrency errors are evidence, not runner crashes.
        error = f"{type(exc).__name__}: {exc}"
        connection.rollback()
    finally:
        connection.close()
    return WorkerResult(
        worker_id=worker_id,
        row_no=row_no,
        committed=committed,
        pk_value=pk_value,
        last_insert_id=last_insert_id,
        error=error,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc).isoformat(),
        started_monotonic=started_monotonic,
        finished_monotonic=time.monotonic(),
        secondary_row_no=row_no + 1 if is_multi_row else None,
        secondary_pk_value=secondary_pk_value,
    )


def _seed_row(connection: Any, scenario: PrimaryKeyScenario, table: str, row_no: int, pk_value: Any, phase: str) -> None:
    values = _canary_values(row_no, -1, row_no, phase)
    columns = ("pk", *ALL_COLUMN_NAMES)
    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
    with connection.cursor() as cursor:
        cursor.execute(sql, (pk_value, *(values[column] for column in ALL_COLUMN_NAMES)))


def _auto_increment_start(scenario: PrimaryKeyScenario) -> int | None:
    if not scenario.auto_increment:
        return None
    _, maximum = _integer_range(scenario.source_type)
    state = scenario.initial_state
    if state == "empty_counter_1":
        return 1
    if state == "empty_counter_max_minus_16":
        return maximum - 15
    if state == "empty_counter_max_minus_1":
        return maximum
    if state == "empty_counter_max":
        return maximum + 1
    if state in {"one_row_max_minus_1", "tail_16_to_max_minus_1"}:
        return maximum
    if state in {"one_row_max", "tail_16_to_max", "all_deleted_high_counter", "mixed_explicit_generated_max"}:
        return maximum + 1
    return 1


def _seed_state(
    connection: Any,
    scenario: PrimaryKeyScenario,
    table: str,
    *,
    filler_rows: int,
) -> set[int]:
    seeded_rows: set[int] = set()
    if scenario.family == "integer":
        _, maximum = _integer_range(scenario.source_type)
        state = scenario.initial_state
        if state == "one_row_max_minus_1":
            _seed_row(connection, scenario, table, 1, maximum - 1, "seed")
            seeded_rows.add(1)
        elif state == "one_row_max":
            _seed_row(connection, scenario, table, 1, maximum, "seed")
            seeded_rows.add(1)
        elif state == "tail_16_to_max_minus_1":
            for index in range(16):
                _seed_row(connection, scenario, table, index + 1, maximum - 16 + index, "seed")
                seeded_rows.add(index + 1)
        elif state == "tail_16_to_max":
            for index in range(16):
                _seed_row(connection, scenario, table, index + 1, maximum - 15 + index, "seed")
                seeded_rows.add(index + 1)
        elif state == "all_deleted_high_counter":
            _seed_row(connection, scenario, table, 1, maximum, "seed")
            seeded_rows.add(1)
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table}")
        elif state == "mixed_explicit_generated_max":
            _seed_row(connection, scenario, table, 1, maximum, "seed")
            seeded_rows.add(1)
        else:
            pass
        if filler_rows and state not in {"one_row_max", "tail_16_to_max", "mixed_explicit_generated_max"}:
            with connection.cursor() as cursor:
                for index in range(min(filler_rows, max(0, maximum - 20))):
                    values = _canary_values(1000 + index, -1, index, "filler")
                    columns = ALL_COLUMN_NAMES
                    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
                    cursor.execute(sql, [values[column] for column in columns])
                    seeded_rows.add(1000 + index)
    else:
        state = scenario.initial_state
        if state == "one_row":
            _seed_row(connection, scenario, table, 1, _source_pk_value(scenario, 1), "seed")
            seeded_rows.add(1)
        elif state == "normal_24_rows":
            for index in range(24):
                _seed_row(connection, scenario, table, index + 1, _source_pk_value(scenario, index + 1), "seed")
                seeded_rows.add(index + 1)
        elif state == "boundary_or_near_boundary":
            _seed_row(connection, scenario, table, 1, _source_pk_value(scenario, 1, boundary=True), "seed")
            seeded_rows.add(1)
        elif state == "prefix_or_collation_conflict":
            _seed_row(connection, scenario, table, 1, _source_pk_value(scenario, 1), "seed")
            seeded_rows.add(1)
        elif state == "high_value_all_deleted":
            _seed_row(connection, scenario, table, 1, _source_pk_value(scenario, 1, boundary=True), "seed")
            seeded_rows.add(1)
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table}")
        if filler_rows and state not in {"boundary_or_near_boundary", "high_value_all_deleted"}:
            with connection.cursor() as cursor:
                for index in range(filler_rows):
                    values = _canary_values(1000 + index, -1, index, "filler")
                    columns = ALL_COLUMN_NAMES
                    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
                    cursor.execute(sql, [values[column] for column in columns])
                    seeded_rows.add(1000 + index)
    connection.commit()
    return seeded_rows


def _ddl_sql(scenario: PrimaryKeyScenario, table: str, profile: str) -> str:
    target = f"pk {scenario.target_type} NOT NULL"
    if scenario.auto_increment:
        target += " AUTO_INCREMENT"
    return f"ALTER TABLE {table} MODIFY {target}, ALGORITHM={profile.upper()};"


def _expected_column_type(scenario: PrimaryKeyScenario) -> str:
    value = scenario.target_type
    if value.startswith("NUMERIC"):
        value = "DECIMAL" + value[len("NUMERIC"):]
    return value.lower()


def _validate_schema(
    connection: Any,
    scenario: PrimaryKeyScenario,
    table: str,
    expected_type: str | None = None,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_type, extra FROM information_schema.COLUMNS "
            "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='pk'",
            (table,),
        )
        row = cursor.fetchone()
        if row is None:
            raise AssertionError("pk column missing after DDL")
        column_type, extra = row
        expected_column_type = _expected_column_type(scenario)
        if expected_type is not None:
            expected_column_type = expected_type.lower()
        if column_type.lower() != expected_column_type:
            raise AssertionError(f"unexpected pk type: {column_type!r} != {expected_column_type!r}")
        if scenario.auto_increment and "auto_increment" not in (extra or "").lower():
            raise AssertionError("AUTO_INCREMENT metadata lost")
        cursor.execute(
            "SELECT sub_part FROM information_schema.STATISTICS "
            "WHERE table_schema=DATABASE() AND table_name=%s AND index_name='PRIMARY' AND column_name='pk'",
            (table,),
        )
        index_row = cursor.fetchone()
        if index_row is None:
            raise AssertionError("primary key missing after DDL")
        actual_prefix = index_row[0]
        expected_prefix = scenario.pk_prefix_length
        if actual_prefix != expected_prefix:
            raise AssertionError(f"primary-key prefix changed: {actual_prefix!r} != {expected_prefix!r}")


def _expected_duplicate_conflict(
    scenario: PrimaryKeyScenario,
    error: str | None,
    seed_rows: set[int],
) -> bool:
    if not error or "1062" not in error or "Duplicate entry" not in error:
        return False
    if scenario.family != "bit":
        return False
    target_width = _type_length(scenario.target_type)
    capacity = 1 << target_width
    return scenario.workers + len(seed_rows) > capacity


def _query_all_rows(connection: Any, table: str) -> tuple[tuple[Any, ...], ...]:
    columns = ("pk", *ALL_COLUMN_NAMES)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {','.join(columns)} FROM {table} ORDER BY row_no")
        return tuple(cursor.fetchall())


def _normalized_column_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return Decimal(str(value))
    return value


def _snapshot_rows(connection: Any, table: str) -> tuple[tuple[Any, ...], ...]:
    return _query_all_rows(connection, table)


def _validate_snapshot(
    scenario: PrimaryKeyScenario,
    current_rows: Sequence[tuple[Any, ...]],
    snapshot_rows: Sequence[tuple[Any, ...]],
) -> None:
    current_by_row_no = {row[1]: row for row in current_rows}
    for snapshot_row in snapshot_rows:
        row_no = snapshot_row[1]
        if row_no not in current_by_row_no:
            raise AssertionError(f"pre-DDL row missing after DDL: {row_no}")
        current_row = current_by_row_no[row_no]
        if len(current_row) != len(snapshot_row):
            raise AssertionError("row column count changed")
        for column_index, (actual, expected) in enumerate(
            zip(current_row, snapshot_row, strict=True)
        ):
            if isinstance(actual, Decimal) or isinstance(expected, Decimal):
                actual = Decimal(str(actual))
                expected = Decimal(str(expected))
            elif column_index == 0 and scenario.family == "bit":
                actual = int.from_bytes(actual, "big") if isinstance(actual, bytes) else int(actual)
                expected = int.from_bytes(expected, "big") if isinstance(expected, bytes) else int(expected)
            elif (
                column_index == 0
                and scenario.family == "binary"
                and scenario.source_type.startswith("BINARY")
                and scenario.target_type.startswith("BINARY")
            ):
                actual = actual.rstrip(b"\x00")
                expected = expected.rstrip(b"\x00")
            if _normalized_column_value(actual) != _normalized_column_value(expected):
                raise AssertionError(
                    f"pre-DDL row changed: row_no={row_no}, "
                    f"{actual!r} != {expected!r}"
                )


def _table_auto_increment(connection: Any, table: str) -> int | None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT AUTO_INCREMENT FROM information_schema.TABLES "
            "WHERE table_schema=DATABASE() AND table_name=%s",
            (table,),
        )
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else None


def _validate_rows(
    connection: Any,
    scenario: PrimaryKeyScenario,
    table: str,
    worker_results: Sequence[WorkerResult],
    final_known_bug_row: int | None,
    seed_rows: set[int],
    phase: str,
    new_row_phases: Mapping[int, tuple[int, str]],
) -> None:
    rows = _query_all_rows(connection, table)
    by_row_no = {row[1]: row for row in rows}
    if len(by_row_no) != len(rows):
        raise AssertionError("row_no duplicated")

    expected_row_nos = set(seed_rows)
    for worker in worker_results:
        if worker.committed:
            expected_row_nos.add(worker.row_no)
            if worker.secondary_row_no is not None:
                expected_row_nos.add(worker.secondary_row_no)
    expected_row_nos.update(new_row_phases)
    if set(by_row_no) != expected_row_nos:
        raise AssertionError(f"row set mismatch: {set(by_row_no)} != {expected_row_nos}")

    def validate_row(
        row_no: int,
        worker_id: int,
        row_phase: str,
        *,
        updated: bool,
        expected_pk: Any = None,
    ) -> None:
        row = by_row_no[row_no]
        values = dict(zip(ALL_COLUMN_NAMES, row[1:], strict=True))
        expected = _canary_values(row_no, worker_id, row_no, row_phase, updated=updated)
        for column in ALL_COLUMN_NAMES:
            actual_value = values[column]
            expected_value = expected[column]
            if isinstance(actual_value, Decimal) or isinstance(expected_value, Decimal):
                actual_value = Decimal(str(actual_value))
                expected_value = Decimal(str(expected_value))
            if actual_value != expected_value:
                raise AssertionError(
                    f"column mismatch {column}: {actual_value!r} != {expected_value!r}"
                )
        if scenario.family == "integer":
            if row[0] is None:
                raise AssertionError("AUTO_INCREMENT generated NULL")
        else:
            actual_pk = row[0]
            comparison_pk = expected_pk if expected_pk is not None else _target_pk_value(scenario, row_no)
            if scenario.family == "decimal":
                actual_pk = Decimal(str(actual_pk))
                comparison_pk = Decimal(str(comparison_pk))
            elif scenario.family == "bit":
                actual_pk = int.from_bytes(actual_pk, "big") if isinstance(actual_pk, bytes) else int(actual_pk)
                comparison_pk = (
                    int.from_bytes(comparison_pk, "big")
                    if isinstance(comparison_pk, bytes)
                    else int(comparison_pk)
                )
            if actual_pk != comparison_pk:
                raise AssertionError(f"non-integer pk mismatch: {actual_pk!r} != {comparison_pk!r}")

    updated = scenario.dml_mode == "insert_update_all_canaries"
    for worker in worker_results:
        if worker.error and not _expected_duplicate_conflict(scenario, worker.error, seed_rows):
            raise AssertionError(f"worker {worker.worker_id} failed: {worker.error}")
        if not worker.committed:
            if worker.row_no in by_row_no or (
                worker.secondary_row_no is not None and worker.secondary_row_no in by_row_no
            ):
                raise AssertionError("failed or rolled-back row visible")
            continue
        validate_row(
            worker.row_no,
            worker.worker_id,
            phase,
            updated=updated,
            expected_pk=worker.pk_value,
        )
        if worker.secondary_row_no is not None:
            validate_row(
                worker.secondary_row_no,
                worker.worker_id,
                phase,
                updated=updated,
                expected_pk=worker.secondary_pk_value,
            )

    for row_no, (row_worker_id, row_phase) in new_row_phases.items():
        validate_row(row_no, row_worker_id, row_phase, updated=False)

    if final_known_bug_row is not None and scenario.family == "integer":
        if by_row_no[final_known_bug_row][0] is None:
            raise AssertionError("known-bug insert did not generate AUTO_INCREMENT")

    pk_values = [row[0] for row in rows]
    if len(pk_values) != len(set(pk_values)):
        raise AssertionError("duplicate primary key")


def _validate_expected_reject_rows(
    connection: Any,
    scenario: PrimaryKeyScenario,
    table: str,
    worker_results: Sequence[WorkerResult],
    phase: str,
) -> None:
    columns = ("pk", *ALL_COLUMN_NAMES)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {','.join(columns)} FROM {table} ORDER BY row_no")
        rows = cursor.fetchall()
    by_row_no = {row[1]: row for row in rows}
    for worker in worker_results:
        if worker.committed:
            if worker.row_no not in by_row_no:
                raise AssertionError("committed row missing after expected DDL reject")
            row = by_row_no[worker.row_no]
            values = dict(zip(ALL_COLUMN_NAMES, row[1:], strict=True))
            updated = scenario.dml_mode == "insert_update_all_canaries"
            expected = _canary_values(worker.row_no, worker.worker_id, worker.row_no, phase, updated=updated)
            for column in ALL_COLUMN_NAMES:
                actual_value = values[column]
                expected_value = expected[column]
                if column == "c_decimal":
                    actual_value = Decimal(str(actual_value))
                    expected_value = Decimal(str(expected_value))
                if actual_value != expected_value:
                    raise AssertionError(
                        f"column mismatch after expected reject {column}: "
                        f"{actual_value!r} != {expected_value!r}"
                    )
        elif worker.row_no in by_row_no:
            raise AssertionError("failed/rolled-back row visible after expected DDL reject")


def _run_across_ddl(
    connection_config: ConnectionConfig,
    scenario: PrimaryKeyScenario,
    table: str,
    profile: str,
) -> tuple[WorkerResult, bool, str | None, bool]:
    import pymysql

    worker_future_row_no = 20001
    worker_started = time.monotonic()
    connection = _connect(connection_config)
    connection.autocommit(False)
    ddl_error = None
    ddl_succeeded = False
    try:
        values = _worker_values(scenario, 99, worker_future_row_no, "across_ddl")
        _execute_insert(connection, scenario, table, values)
        with ThreadPoolExecutor(max_workers=1) as executor:
            ddl_future = executor.submit(_run_ddl_on_new_connection, connection_config, scenario, table, profile)
            time.sleep(0.1)
            connection.commit()
            ddl_succeeded, ddl_error, ddl_started, ddl_finished = ddl_future.result()
        worker = WorkerResult(
            worker_id=99,
            row_no=worker_future_row_no,
            committed=True,
            pk_value=None if scenario.family == "integer" else _target_pk_value(scenario, worker_future_row_no),
            last_insert_id=None,
            error=None,
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=datetime.now(timezone.utc).isoformat(),
            started_monotonic=worker_started,
            finished_monotonic=time.monotonic(),
        )
        overlap = worker.started_monotonic < ddl_finished and worker.finished_monotonic > ddl_started
        return worker, overlap, ddl_error, ddl_succeeded
    except Exception as exc:
        connection.rollback()
        worker = WorkerResult(
            worker_id=99,
            row_no=worker_future_row_no,
            committed=False,
            pk_value=None,
            last_insert_id=None,
            error=str(exc),
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        return worker, False, ddl_error, ddl_succeeded
    finally:
        connection.close()


def _run_ddl_on_new_connection(
    connection_config: ConnectionConfig,
    scenario: PrimaryKeyScenario,
    table: str,
    profile: str,
    started_event: threading.Event | None = None,
) -> tuple[bool, str | None, float, float]:
    import pymysql

    connection = _connect(connection_config)
    started = time.monotonic()
    if started_event is not None:
        started_event.set()
    try:
        with connection.cursor() as cursor:
            cursor.execute(_ddl_sql(scenario, table, profile))
        return True, None, started, time.monotonic()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}", started, time.monotonic()
    finally:
        connection.close()


def run_scenario(
    connection_config: ConnectionConfig,
    scenario: PrimaryKeyScenario,
    profile: str,
    *,
    filler_rows: int = 64,
    phase_override: str | None = None,
    workers_first: bool = False,
) -> ScenarioResult:
    started = time.monotonic()
    table = _table_name(scenario, profile)
    phase = phase_override or scenario.phase
    connection = _connect(connection_config)
    worker_results: list[WorkerResult] = []
    final_known_bug_row: int | None = None
    new_row_phases: dict[int, tuple[int, str]] = {}
    overlap = False
    source_range_retries = 0
    initial_auto_increment: int | None = None

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        cursor = connection.cursor()
        cursor.execute(
            build_create_table_sql(
                scenario,
                table,
                scenario.source_type,
                auto_increment_start=_auto_increment_start(scenario),
            )
        )
        seed_rows = _seed_state(connection, scenario, table, filler_rows=filler_rows)

        if phase == "pre_during_post":
            _seed_row(
                connection,
                scenario,
                table,
                10001,
                _source_pk_value(scenario, 1, boundary=True),
                "pre_ddl",
            )
            seed_rows.add(10001)
            connection.commit()

        snapshot = _snapshot_rows(connection, table)
        if scenario.auto_increment:
            initial_auto_increment = _table_auto_increment(connection, table)

        if phase == "across_ddl":
            worker, overlap, ddl_error, ddl_succeeded = _run_across_ddl(
                connection_config,
                scenario,
                table,
                profile,
            )
            worker_results.append(worker)
        elif phase == "post_ddl":
            # Strict post-DDL semantics: complete the DDL before creating or
            # submitting any DML worker.
            ddl_succeeded, ddl_error, ddl_started, ddl_finished = _run_ddl_on_new_connection(
                connection_config,
                scenario,
                table,
                profile,
            )
            with ThreadPoolExecutor(max_workers=scenario.workers) as executor:
                futures = [
                    executor.submit(
                        _worker_run,
                        connection_config,
                        scenario,
                        table,
                        worker_id,
                        30000 + worker_id * 10,
                        phase,
                    )
                    for worker_id in range(scenario.workers)
                ]
                for future in as_completed(futures):
                    worker_results.append(future.result())
            overlap = False
        else:
            with ThreadPoolExecutor(max_workers=scenario.workers + 1) as executor:
                if workers_first and phase == "during_ddl":
                    ddl_started_event = threading.Event()
                    futures = [
                        executor.submit(
                            _worker_run,
                            connection_config,
                            scenario,
                            table,
                            worker_id,
                            30000 + worker_id * 10,
                            phase,
                            start_event=ddl_started_event,
                        )
                        for worker_id in range(scenario.workers)
                    ]
                    ddl_future = executor.submit(
                        _run_ddl_on_new_connection,
                        connection_config,
                        scenario,
                        table,
                        profile,
                        started_event=ddl_started_event,
                    )
                else:
                    ddl_future = executor.submit(
                        _run_ddl_on_new_connection,
                        connection_config,
                        scenario,
                        table,
                        profile,
                    )
                    time.sleep(0.001)
                    futures = [
                        executor.submit(
                            _worker_run,
                            connection_config,
                            scenario,
                            table,
                            worker_id,
                            30000 + worker_id * 10,
                            phase,
                        )
                        for worker_id in range(scenario.workers)
                    ]
                ddl_succeeded, ddl_error, ddl_started, ddl_finished = ddl_future.result()
                for future in as_completed(futures):
                    worker_results.append(future.result())
            overlap = any(
                max(ddl_started, worker.started_monotonic)
                < min(ddl_finished, worker.finished_monotonic)
                for worker in worker_results
            )

        worker_results.sort(key=lambda worker: worker.worker_id)
        classification = classify_scenario_execution(scenario, profile, ddl_succeeded, ddl_error)

        if classification == "EXPECTED_REJECT":
            _validate_schema(connection, scenario, table, scenario.source_type)
            _validate_snapshot(scenario, _query_all_rows(connection, table), snapshot)
            _validate_expected_reject_rows(
                connection,
                scenario,
                table,
                worker_results,
                phase,
            )
            return ScenarioResult(
                scenario.case_id,
                profile,
                "EXPECTED_REJECT",
                ddl_error,
                overlap,
                tuple(worker_results),
                0,
                int((time.monotonic() - started) * 1000),
            )

        if classification != "PASS":
            return ScenarioResult(
                scenario.case_id,
                profile,
                classification,
                ddl_error,
                overlap,
                tuple(worker_results),
                0,
                int((time.monotonic() - started) * 1000),
            )

        if phase in {"during_ddl", "pre_during_post", "across_ddl"} and not overlap:
            return ScenarioResult(
                scenario.case_id,
                profile,
                "NO_OVERLAP",
                "DDL and DML did not overlap; increase --filler-rows or retry",
                overlap,
                tuple(worker_results),
                0,
                int((time.monotonic() - started) * 1000),
            )

        _validate_schema(connection, scenario, table)
        _validate_snapshot(scenario, _query_all_rows(connection, table), snapshot)

        if phase in {"during_ddl", "pre_during_post"}:
            for index, worker in enumerate(worker_results):
                if worker.error and (
                    ("1264" in worker.error and "Out of range" in worker.error)
                    or ("1467" in worker.error and "Failed to read auto-increment" in worker.error)
                ):
                    worker_results[index] = _worker_run(
                        connection_config,
                        scenario,
                        table,
                        worker.worker_id,
                        worker.row_no,
                        phase,
                    )
                    source_range_retries += 1

        known_bug_last_insert_id: int | None = None
        if scenario.auto_increment:
            final_known_bug_row = 50001
            known_bug_scenario = replace(
                scenario,
                insert_style="omit_pk_explicit_columns",
            )
            known_bug_values = _worker_values(
                known_bug_scenario,
                999,
                final_known_bug_row,
                "known_bug_omit_pk",
            )
            known_bug_last_insert_id = _execute_insert(
                connection,
                known_bug_scenario,
                table,
                known_bug_values,
            )
            connection.commit()
            new_row_phases[final_known_bug_row] = (999, "known_bug_omit_pk")
            if (
                initial_auto_increment is not None
                and known_bug_last_insert_id is not None
                and known_bug_last_insert_id < initial_auto_increment
            ):
                raise AssertionError(
                    "AUTO_INCREMENT regressed: "
                    f"{known_bug_last_insert_id} < {initial_auto_increment}"
                )

        if phase == "pre_during_post":
            post_row_no = 50002
            post_scenario = replace(
                scenario,
                insert_style=(
                    "omit_pk_explicit_columns"
                    if scenario.auto_increment
                    else "explicit_pk_all_columns"
                ),
            )
            post_values = _worker_values(post_scenario, 998, post_row_no, "post_ddl")
            _execute_insert(connection, post_scenario, table, post_values)
            connection.commit()
            new_row_phases[post_row_no] = (998, "post_ddl")

        if scenario.auto_increment:
            _, source_max = _integer_range(scenario.source_type)
            _, target_max = _integer_range(scenario.target_type)
            boundary_values = (
                (51001, source_max + 1),
                (51002, target_max - 1),
                (51003, target_max),
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE pk=%s",
                    (source_max + 1,),
                )
                source_max_plus_one_exists = int(cursor.fetchone()[0]) > 0
            for row_no, pk_value in boundary_values:
                if row_no == 51001 and source_max_plus_one_exists:
                    continue
                _seed_row(
                    connection,
                    scenario,
                    table,
                    row_no,
                    pk_value,
                    "boundary_insert",
                )
                new_row_phases[row_no] = (-1, "boundary_insert")
            connection.commit()

        _validate_rows(
            connection,
            scenario,
            table,
            worker_results,
            final_known_bug_row,
            seed_rows,
            phase,
            new_row_phases,
        )
        return ScenarioResult(
            scenario.case_id,
            profile,
            "PASS",
            None,
            overlap,
            tuple(worker_results),
            source_range_retries,
            int((time.monotonic() - started) * 1000),
        )
    except Exception as exc:
        return ScenarioResult(
            scenario.case_id,
            profile,
            "FAIL_VALIDATION",
            f"{type(exc).__name__}: {exc}",
            overlap,
            tuple(worker_results),
            source_range_retries,
            int((time.monotonic() - started) * 1000),
        )
    finally:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
        finally:
            connection.close()


def _selected_scenarios(
    *,
    smoke: bool,
    all_scenarios: bool,
    limit: int | None,
    case_ids: set[str],
) -> Iterable[PrimaryKeyScenario]:
    if smoke:
        scenarios: Iterable[PrimaryKeyScenario] = smoke_primary_key_scenarios()
    elif all_scenarios:
        scenarios = iter_primary_key_scenarios()
    else:
        scenarios = iter_primary_key_scenarios()
    selected = 0
    for scenario in scenarios:
        if case_ids and scenario.case_id not in case_ids:
            continue
        yield scenario
        selected += 1
        if limit is not None and selected >= limit:
            return


def run_local(
    cases_dir: Path,
    results_path: Path,
    summary_path: Path,
    *,
    profile: str = "copy",
    smoke: bool = False,
    all_scenarios: bool = False,
    limit: int | None = None,
    case_ids: set[str] | None = None,
    filler_rows: int = 64,
    phase_override: str | None = None,
    workers_first: bool = False,
    mysqld: str = "/opt/homebrew/opt/mysql@8.0/bin/mysqld",
    external: bool = False,
    host: str = "127.0.0.1",
    port: int = 3306,
    user: str = "root",
    password: str | None = None,
) -> dict[str, Any]:
    if profile not in PRIMARY_KEY_PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("PyMySQL is required; install '.[runner]'") from exc

    manifest = json.loads((cases_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("batch_id") != "2026-10-19-type-upgrade-primary-key-concurrency-v1":
        raise RuntimeError(f"unexpected manifest: {cases_dir / 'manifest.json'}")

    results: list[ScenarioResult] = []
    started_at = datetime.now(timezone.utc).isoformat()
    server_version = "unknown"
    server: LocalMySQLServer | None = None
    connection_config = (
        ConnectionConfig(host=host, port=port, user=user, password=password)
        if external
        else None
    )
    try:
        if external:
            assert connection_config is not None
        else:
            server = LocalMySQLServer(mysqld=mysqld)
            server.start()
            connection_config = ConnectionConfig(socket_path=server.socket_path)

        connection = _connect(connection_config, with_database=False)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                server_version = str(cursor.fetchone()[0])
                cursor.execute(f"DROP DATABASE IF EXISTS {PRIMARY_KEY_DATABASE}")
                cursor.execute(
                    f"CREATE DATABASE {PRIMARY_KEY_DATABASE} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
                )
        finally:
            connection.close()

        for scenario in _selected_scenarios(
            smoke=smoke,
            all_scenarios=all_scenarios,
            limit=limit,
            case_ids=case_ids or set(),
        ):
            result = run_scenario(
                connection_config,
                scenario,
                profile,
                filler_rows=filler_rows,
                phase_override=phase_override,
                workers_first=workers_first,
            )
            results.append(result)
    finally:
        if server is not None:
            server.stop()

    counts: dict[str, int] = {}
    for result in results:
        counts[result.outcome] = counts.get(result.outcome, 0) + 1
    selected_count = len(results)
    summary = {
        "format_version": 1,
        "batch_id": manifest["batch_id"],
        "batch_kind": manifest["batch_kind"],
        "profile": profile,
        "selected_count": selected_count,
        "executed_count": selected_count,
        "counts": counts,
        "all_pass": bool(results)
        and counts.get("PASS", 0) + counts.get("EXPECTED_REJECT", 0) == selected_count,
        "mysqld_version": server_version,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": hashlib.sha256((cases_dir / "manifest.json").read_bytes()).hexdigest(),
    }
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8", newline="\n") as handle:
        for result in results:
            handle.write(json.dumps(result.to_json(), sort_keys=True, separators=(",", ":")) + "\n")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.with_suffix(".md").write_text(render_summary_markdown(summary), encoding="utf-8")
    return summary


def render_summary_markdown(summary: dict[str, Any]) -> str:
    counts = ", ".join(f"{key}: {value}" for key, value in sorted(summary.get("counts", {}).items())) or "none"
    return (
        "# Primary-key type-upgrade concurrency local verification\n\n"
        f"**Result:** {'ALL PASS' if summary.get('all_pass') else 'FAIL OR INCOMPLETE'}\n\n"
        f"- **Batch ID:** `{summary.get('batch_id')}`\n"
        f"- **Profile:** `{summary.get('profile')}`\n"
        f"- **Selected scenarios:** {summary.get('selected_count')}\n"
        f"- **Outcome counts:** {counts}\n"
        f"- **MySQL version:** {summary.get('mysqld_version')}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TUCPK primary-key type-upgrade concurrency scenarios")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--profile", choices=PRIMARY_KEY_PROFILES, default="copy")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--filler-rows", type=int, default=64)
    parser.add_argument("--phase", choices=["during_ddl", "post_ddl", "pre_during_post", "across_ddl"])
    parser.add_argument("--workers-first", action="store_true", help="Start DML workers before submitting the DDL; useful for source-range boundary cases")
    parser.add_argument("--mysqld", default="/opt/homebrew/opt/mysql@8.0/bin/mysqld")
    parser.add_argument("--external", action="store_true", help="Use an existing MySQL server instead of starting a local mysqld")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password-env", default=None, help="Environment variable containing the MySQL password; the value is not logged")
    args = parser.parse_args()
    summary = run_local(
        args.cases,
        args.results,
        args.summary,
        profile=args.profile,
        smoke=args.smoke,
        all_scenarios=args.all,
        limit=args.limit,
        case_ids=set(args.case_id),
        filler_rows=args.filler_rows,
        phase_override=args.phase,
        workers_first=args.workers_first,
        mysqld=args.mysqld,
        external=args.external,
        host=args.host,
        port=args.port,
        user=args.user,
        password=__import__("os").environ.get(args.password_env) if args.password_env else None,
    )
    print(render_summary_markdown(summary))


if __name__ == "__main__":
    main()
