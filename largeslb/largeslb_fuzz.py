#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import hashlib
import json
import logging
import random
import signal
import sys
import threading
import time
import traceback
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, unquote, urlparse


TWO_MB = 2 * 1024 * 1024
DEFAULT_RUN_ID_PREFIX = "largeslb"
DISCONNECT_ERROR_CODES = {2002, 2003, 2006, 2013, 2055}
RETRYABLE_TXN_ERROR_CODES = {1205, 1213}
CORRUPTION_HINTS = (
    "corrupt",
    "corruption",
    "checksum",
    "assert",
    "panic",
    "page is",
    "page corruption",
    "tablespace",
)
ENGINE_METRIC_NAMES = (
    "large_mtr",
    "large_mtr_size",
    "cv_lsn",
    "persist_lsn",
    "slice_persist_lsn",
    "slice_cv_lsn",
)


@dataclass(frozen=True)
class FieldSpec:
    key: str
    column: str
    sql_type: str
    safe_lengths: Tuple[int, ...]
    safe_max_len: int
    is_binary: bool = False


FIELD_SPECS: Dict[str, FieldSpec] = {
    "payload": FieldSpec(
        key="payload",
        column="payload",
        sql_type="LONGTEXT NULL",
        safe_lengths=(8192, 16384, 32768, 262144, 1048576),
        safe_max_len=1048576,
    ),
    "char_255": FieldSpec(
        key="char_255",
        column="char_255",
        sql_type="CHAR(255) NOT NULL DEFAULT ''",
        safe_lengths=(255,),
        safe_max_len=255,
    ),
    "varchar_16383": FieldSpec(
        key="varchar_16383",
        column="varchar_16383",
        sql_type="VARCHAR(16383) CHARACTER SET latin1 COLLATE latin1_bin NOT NULL DEFAULT ''",
        safe_lengths=(1024, 4096, 8192, 16383),
        safe_max_len=16383,
    ),
    "text_col": FieldSpec(
        key="text_col",
        column="text_col",
        sql_type="TEXT NULL",
        safe_lengths=(4096, 32768, 60000),
        safe_max_len=60000,
    ),
    "mediumtext_col": FieldSpec(
        key="mediumtext_col",
        column="mediumtext_col",
        sql_type="MEDIUMTEXT NULL",
        safe_lengths=(65536, 262144, 524288, 1048576),
        safe_max_len=1048576,
    ),
    "longtext_col": FieldSpec(
        key="longtext_col",
        column="longtext_col",
        sql_type="LONGTEXT NULL",
        safe_lengths=(65536, 262144, 524288, 1048576),
        safe_max_len=1048576,
    ),
    "blob_col": FieldSpec(
        key="blob_col",
        column="blob_col",
        sql_type="BLOB NULL",
        safe_lengths=(4096, 32768, 60000),
        safe_max_len=60000,
        is_binary=True,
    ),
    "mediumblob_col": FieldSpec(
        key="mediumblob_col",
        column="mediumblob_col",
        sql_type="MEDIUMBLOB NULL",
        safe_lengths=(65536, 262144, 524288, 1048576),
        safe_max_len=1048576,
        is_binary=True,
    ),
    "longblob_col": FieldSpec(
        key="longblob_col",
        column="longblob_col",
        sql_type="LONGBLOB NULL",
        safe_lengths=(65536, 262144, 524288, 1048576),
        safe_max_len=1048576,
        is_binary=True,
    ),
}

DEFAULT_TARGET_FIELDS = tuple(key for key in FIELD_SPECS if key != "payload")


@dataclass(frozen=True)
class Dsn:
    user: str
    password: str
    host: str
    port: int
    database: str
    charset: str = "utf8mb4"
    connect_timeout: int = 10
    read_timeout: int = 60
    write_timeout: int = 60

    @classmethod
    def parse(cls, value: str) -> "Dsn":
        if value.startswith("mysql://"):
            parsed = urlparse(value)
            query = parse_qs(parsed.query)
            database = parsed.path.lstrip("/")
            if not parsed.username or not database:
                raise ValueError("DSN must include username and database")
            return cls(
                user=unquote(parsed.username),
                password=unquote(parsed.password or ""),
                host=parsed.hostname or "127.0.0.1",
                port=parsed.port or 3306,
                database=database,
                charset=query.get("charset", ["utf8mb4"])[0],
                connect_timeout=int(query.get("connect_timeout", ["10"])[0]),
                read_timeout=int(query.get("read_timeout", ["60"])[0]),
                write_timeout=int(query.get("write_timeout", ["60"])[0]),
            )

        parts: Dict[str, str] = {}
        for item in value.split(","):
            if not item.strip():
                continue
            if "=" not in item:
                raise ValueError("key=value DSN items must contain '='")
            key, raw = item.split("=", 1)
            parts[key.strip()] = raw.strip()
        if "user" not in parts or "database" not in parts:
            raise ValueError("key=value DSN must include user and database")
        return cls(
            user=parts["user"],
            password=parts.get("password", ""),
            host=parts.get("host", "127.0.0.1"),
            port=int(parts.get("port", "3306")),
            database=parts["database"],
            charset=parts.get("charset", "utf8mb4"),
            connect_timeout=int(parts.get("connect_timeout", "10")),
            read_timeout=int(parts.get("read_timeout", "60")),
            write_timeout=int(parts.get("write_timeout", "60")),
        )

    def redacted(self) -> str:
        return (
            f"mysql://{self.user}:***@{self.host}:{self.port}/{self.database}"
            f"?charset={self.charset}"
        )

    def connect_kwargs(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "charset": self.charset,
            "connect_timeout": self.connect_timeout,
            "read_timeout": self.read_timeout,
            "write_timeout": self.write_timeout,
            "autocommit": True,
        }


class PayloadFactory:
    def __init__(self, seed: int):
        self.seed = seed

    def make(self, op_id: str, length: int, salt: str = "") -> Tuple[str, str]:
        if length < 0:
            raise ValueError("payload length must be non-negative")
        material = f"{self.seed}:{op_id}:{salt}".encode("utf-8")
        digest = hashlib.sha256(material).hexdigest()
        chunk = f"{digest}:{op_id}:{salt}:"
        raw = (chunk * ((length // max(1, len(chunk))) + 2)).encode("ascii")[:length]
        payload = raw.decode("ascii")
        return payload, hashlib.sha256(raw).hexdigest()

    def make_bytes(self, op_id: str, length: int, salt: str = "") -> Tuple[bytes, str]:
        if length < 0:
            raise ValueError("payload length must be non-negative")
        material = f"{self.seed}:{op_id}:{salt}".encode("utf-8")
        digest = hashlib.sha256(material).digest()
        raw = (digest * ((length // max(1, len(digest))) + 2))[:length]
        return raw, hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class RowBefore:
    row_id: int
    bucket: int
    version: int


@dataclass(frozen=True)
class ExpectedRow:
    row_id: int
    bucket: int
    version: int
    last_op_id: str
    payload_len: int
    payload_sha: str
    target_field: str


@dataclass(frozen=True)
class OperationPlan:
    op_id: str
    kind: str
    worker_id: int
    sequence: int
    buckets: List[int]
    rows_per_bucket: int
    payload_len: int
    repeat_updates: int
    checkpoint: bool
    target_field: str = "longtext_col"

    @property
    def expected_row_count(self) -> int:
        return len(self.buckets) * self.rows_per_bucket

    @property
    def total_payload_bytes(self) -> int:
        return self.expected_row_count * self.payload_len * self.repeat_updates

    @property
    def unsupported_single_redo(self) -> bool:
        return self.payload_len >= TWO_MB

    def to_json(self) -> Dict[str, Any]:
        data = dataclasses.asdict(self)
        data.update(
            {
                "expected_row_count": self.expected_row_count,
                "total_payload_bytes": self.total_payload_bytes,
                "unsupported_single_redo": self.unsupported_single_redo,
            }
        )
        return data


class ScenarioGenerator:
    def __init__(
        self,
        seed: int,
        bucket_count: int,
        rng: Optional[random.Random] = None,
        checkpoint_rate: float = 0.05,
        op_prefix: Optional[str] = None,
        target_fields: Sequence[str] = DEFAULT_TARGET_FIELDS,
    ):
        if bucket_count < 1:
            raise ValueError("bucket_count must be positive")
        self.seed = seed
        self.bucket_count = bucket_count
        self.rng = rng or random.Random(seed)
        self.checkpoint_rate = checkpoint_rate
        self.op_prefix = op_prefix or f"{DEFAULT_RUN_ID_PREFIX}-{seed}"
        self.target_fields = tuple(target_fields) or DEFAULT_TARGET_FIELDS
        self.weighted_kinds = [
            ("large_single_bucket", 25),
            ("multi_batch_large", 20),
            ("multi_bucket_large", 15),
            ("same_page_hot", 10),
            ("boundary_2m", 10),
            ("char_varchar_boundary", 10),
            ("blob_family_large", 10),
            ("text_family_large", 10),
            ("small_fast_path", 20),
        ]

    def next_plan(self, worker_id: int, sequence: int) -> OperationPlan:
        kind = self._choose_kind()
        checkpoint = self.rng.random() < self.checkpoint_rate or sequence % 200 == 0
        op_id = f"{self.op_prefix}-w{worker_id}-{sequence:012d}-{kind}"
        target_field = self._choose_target_field(kind)
        payload_len = self._choose_payload_len(target_field, kind)

        if kind == "large_single_bucket":
            bucket = self.rng.randrange(self.bucket_count)
            return OperationPlan(
                op_id=op_id,
                kind=kind,
                worker_id=worker_id,
                sequence=sequence,
                buckets=[bucket],
                rows_per_bucket=self.rng.choice([160, 192, 256, 384, 512]),
                payload_len=payload_len,
                repeat_updates=1,
                checkpoint=checkpoint,
                target_field=target_field,
            )

        if kind == "multi_batch_large":
            bucket = self.rng.randrange(self.bucket_count)
            return OperationPlan(
                op_id=op_id,
                kind=kind,
                worker_id=worker_id,
                sequence=sequence,
                buckets=[bucket],
                rows_per_bucket=self.rng.choice([96, 128, 192]),
                payload_len=payload_len,
                repeat_updates=self.rng.choice([2, 3]),
                checkpoint=checkpoint,
                target_field=target_field,
            )

        if kind == "multi_bucket_large":
            width = min(self.bucket_count, self.rng.choice([2, 3, 4]))
            start = self.rng.randrange(self.bucket_count)
            buckets = sorted({(start + i) % self.bucket_count for i in range(width)})
            return OperationPlan(
                op_id=op_id,
                kind=kind,
                worker_id=worker_id,
                sequence=sequence,
                buckets=buckets,
                rows_per_bucket=self.rng.choice([64, 96, 128]),
                payload_len=payload_len,
                repeat_updates=1,
                checkpoint=checkpoint,
                target_field=target_field,
            )

        if kind == "same_page_hot":
            bucket = self.rng.randrange(self.bucket_count)
            return OperationPlan(
                op_id=op_id,
                kind=kind,
                worker_id=worker_id,
                sequence=sequence,
                buckets=[bucket],
                rows_per_bucket=1,
                payload_len=payload_len,
                repeat_updates=self.rng.choice([64, 96, 128]),
                checkpoint=True,
                target_field=target_field,
            )

        if kind == "boundary_2m":
            bucket = self.rng.randrange(self.bucket_count)
            return OperationPlan(
                op_id=op_id,
                kind=kind,
                worker_id=worker_id,
                sequence=sequence,
                buckets=[bucket],
                rows_per_bucket=self.rng.choice([511, 512, 513]),
                payload_len=4096,
                repeat_updates=1,
                checkpoint=True,
                target_field=target_field,
            )

        if kind == "char_varchar_boundary":
            field = self.rng.choice(["char_255", "varchar_16383"])
            return OperationPlan(
                op_id=op_id,
                kind=kind,
                worker_id=worker_id,
                sequence=sequence,
                buckets=[self.rng.randrange(self.bucket_count)],
                rows_per_bucket=self.rng.choice([128, 256, 512]),
                payload_len=FIELD_SPECS[field].safe_max_len,
                repeat_updates=1,
                checkpoint=True,
                target_field=field,
            )

        if kind == "blob_family_large":
            field = self.rng.choice(["blob_col", "mediumblob_col", "longblob_col"])
            return OperationPlan(
                op_id=op_id,
                kind=kind,
                worker_id=worker_id,
                sequence=sequence,
                buckets=[self.rng.randrange(self.bucket_count)],
                rows_per_bucket=self.rng.choice([64, 96, 128, 192]),
                payload_len=self._choose_payload_len(field, kind),
                repeat_updates=1,
                checkpoint=True,
                target_field=field,
            )

        if kind == "text_family_large":
            field = self.rng.choice(["text_col", "mediumtext_col", "longtext_col"])
            return OperationPlan(
                op_id=op_id,
                kind=kind,
                worker_id=worker_id,
                sequence=sequence,
                buckets=[self.rng.randrange(self.bucket_count)],
                rows_per_bucket=self.rng.choice([64, 96, 128, 192]),
                payload_len=self._choose_payload_len(field, kind),
                repeat_updates=1,
                checkpoint=True,
                target_field=field,
            )

        bucket = self.rng.randrange(self.bucket_count)
        small_field = self.rng.choice(["char_255", "varchar_16383", "text_col", "blob_col"])
        return OperationPlan(
            op_id=op_id,
            kind="small_fast_path",
            worker_id=worker_id,
            sequence=sequence,
            buckets=[bucket],
            rows_per_bucket=self.rng.choice([1, 4, 8, 16]),
            payload_len=min(FIELD_SPECS[small_field].safe_max_len, self.rng.choice([128, 255, 512, 1024, 2048])),
            repeat_updates=1,
            checkpoint=checkpoint,
            target_field=small_field,
        )

    def _choose_kind(self) -> str:
        total = sum(weight for _, weight in self.weighted_kinds)
        point = self.rng.uniform(0, total)
        cursor = 0.0
        for kind, weight in self.weighted_kinds:
            cursor += weight
            if point <= cursor:
                return kind
        return self.weighted_kinds[-1][0]

    def _choose_target_field(self, kind: str) -> str:
        if kind in ("blob_family_large",):
            candidates = [field for field in self.target_fields if FIELD_SPECS[field].is_binary]
            return self.rng.choice(candidates or list(self.target_fields))
        if kind in ("text_family_large", "large_single_bucket", "multi_batch_large", "multi_bucket_large", "same_page_hot"):
            candidates = [
                field
                for field in self.target_fields
                if not FIELD_SPECS[field].is_binary and FIELD_SPECS[field].safe_max_len >= 8192
            ]
            return self.rng.choice(candidates or list(self.target_fields))
        if kind == "boundary_2m":
            candidates = [
                field for field in self.target_fields if FIELD_SPECS[field].safe_max_len >= 4096
            ]
            return self.rng.choice(candidates or list(self.target_fields))
        if kind == "char_varchar_boundary":
            candidates = [field for field in ("char_255", "varchar_16383") if field in self.target_fields]
            return self.rng.choice(candidates or list(self.target_fields))
        return self.rng.choice(list(self.target_fields))

    def _choose_payload_len(self, target_field: str, kind: str) -> int:
        spec = FIELD_SPECS[target_field]
        if kind == "boundary_2m":
            return min(4096, spec.safe_max_len)
        return self.rng.choice(spec.safe_lengths)


class OracleState:
    def __init__(self):
        self._rows: Dict[int, ExpectedRow] = {}
        self._lock = threading.RLock()

    def apply_commit(
        self,
        plan: OperationPlan,
        rows: Sequence[RowBefore],
        final_payload_sha: str,
        final_payload_len: int,
    ) -> List[ExpectedRow]:
        expected: List[ExpectedRow] = []
        with self._lock:
            for row in rows:
                state = ExpectedRow(
                    row_id=row.row_id,
                    bucket=row.bucket,
                    version=row.version + plan.repeat_updates,
                    last_op_id=plan.op_id,
                    payload_len=final_payload_len,
                    payload_sha=final_payload_sha,
                    target_field=plan.target_field,
                )
                self._rows[row.row_id] = state
                expected.append(state)
        return expected

    def load_event(self, record: Dict[str, Any]) -> None:
        with self._lock:
            for item in record.get("rows", []):
                state = ExpectedRow(
                    row_id=int(item["row_id"]),
                    bucket=int(item["bucket"]),
                    version=int(item["version"]),
                    last_op_id=str(item["last_op_id"]),
                    payload_len=int(item["payload_len"]),
                    payload_sha=str(item["payload_sha"]),
                    target_field=str(item.get("target_field", "payload")),
                )
                self._rows[state.row_id] = state

    def expected_for_rows(self, row_ids: Iterable[int]) -> Dict[int, ExpectedRow]:
        with self._lock:
            return {row_id: self._rows[row_id] for row_id in row_ids if row_id in self._rows}

    def snapshot(self) -> Dict[int, ExpectedRow]:
        with self._lock:
            return dict(self._rows)


class ReplicaVisibility(str, Enum):
    LAGGING = "lagging"
    CONSISTENT = "consistent"
    HALF_VISIBLE = "half_visible"


def classify_replica_visibility(
    checkpoint_visible: int,
    visible_rows: int,
    expected_rows: int,
) -> ReplicaVisibility:
    if checkpoint_visible == 0 and visible_rows == 0:
        return ReplicaVisibility.LAGGING
    if checkpoint_visible == 1 and visible_rows == expected_rows:
        return ReplicaVisibility.CONSISTENT
    return ReplicaVisibility.HALF_VISIBLE


class FuzzFailure(Exception):
    def __init__(self, kind: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.kind = kind
        self.details = details or {}


class TransactionNotCommitted(Exception):
    def __init__(self, op_id: str, reason: str):
        super().__init__(reason)
        self.op_id = op_id
        self.reason = reason


class StateStore:
    def __init__(self, state_dir: Path, seed: int):
        self.state_dir = state_dir
        self.seed = seed
        self.failures_dir = state_dir / "failures"
        self.ops_path = state_dir / "ops.jsonl"
        self.oracle_path = state_dir / "oracle.jsonl"
        self.metrics_path = state_dir / "metrics.csv"
        self.engine_metrics_path = state_dir / "engine_metrics.jsonl"
        self.run_log_path = state_dir / "run.log"
        self.recent_ops: Deque[Dict[str, Any]] = deque(maxlen=200)
        self._lock = threading.RLock()

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.failures_dir.mkdir(parents=True, exist_ok=True)
        self._init_metrics()

    def _init_metrics(self) -> None:
        if self.metrics_path.exists():
            return
        with self.metrics_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    "ts",
                    "worker_id",
                    "scenario",
                    "target_field",
                    "op_id",
                    "status",
                    "row_count",
                    "payload_len",
                    "total_payload_bytes",
                    "latency_ms",
                    "primary_check_ms",
                    "readonly_check_ms",
                ]
            )

    def load_oracle(self, oracle: OracleState) -> int:
        if not self.oracle_path.exists():
            return 0
        count = 0
        with self.oracle_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                oracle.load_event(json.loads(line))
                count += 1
        return count

    def append_jsonl(self, path: Path, record: Dict[str, Any]) -> None:
        with self._lock:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def record_op(self, record: Dict[str, Any]) -> None:
        record = {"ts": utc_now(), "seed": self.seed, **record}
        self.recent_ops.append(record)
        self.append_jsonl(self.ops_path, record)

    def record_oracle(self, plan: OperationPlan, rows: Sequence[ExpectedRow]) -> None:
        record = {
            "ts": utc_now(),
            "seed": self.seed,
            "op_id": plan.op_id,
            "scenario": plan.kind,
            "rows": [dataclasses.asdict(row) for row in rows],
        }
        self.append_jsonl(self.oracle_path, record)

    def record_metric(
        self,
        plan: OperationPlan,
        status: str,
        latency_ms: float,
        primary_check_ms: float,
        readonly_check_ms: float,
    ) -> None:
        with self._lock:
            with self.metrics_path.open("a", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(
                    [
                        utc_now(),
                        plan.worker_id,
                        plan.kind,
                        plan.target_field,
                        plan.op_id,
                        status,
                        plan.expected_row_count,
                        plan.payload_len,
                        plan.total_payload_bytes,
                        f"{latency_ms:.3f}",
                        f"{primary_check_ms:.3f}",
                        f"{readonly_check_ms:.3f}",
                    ]
                )

    def record_engine_metrics(self, plan: OperationPlan, metrics: Dict[str, str]) -> None:
        if not metrics:
            return
        self.append_jsonl(
            self.engine_metrics_path,
            {
                "ts": utc_now(),
                "seed": self.seed,
                "op_id": plan.op_id,
                "scenario": plan.kind,
                "target_field": plan.target_field,
                "metrics": metrics,
            },
        )

    def record_failure(
        self,
        failure: FuzzFailure,
        plan: Optional[OperationPlan] = None,
        extra: Optional[Dict[str, Any]] = None,
        reproducer_sql: str = "",
    ) -> Path:
        stamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        safe_kind = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in failure.kind)
        failure_dir = self.failures_dir / f"{stamp}_{safe_kind}"
        failure_dir.mkdir(parents=True, exist_ok=False)

        details = {
            "ts": utc_now(),
            "seed": self.seed,
            "kind": failure.kind,
            "message": str(failure),
            "details": failure.details,
            "plan": plan.to_json() if plan else None,
            "extra": extra or {},
            "recent_ops": list(self.recent_ops),
            "traceback": traceback.format_exc(),
        }
        (failure_dir / "failure.json").write_text(
            json.dumps(details, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        if reproducer_sql:
            (failure_dir / "reproducer.sql").write_text(reproducer_sql, encoding="utf-8")
        return failure_dir


class MySqlClient:
    def __init__(
        self,
        dsn: Dsn,
        role: str,
        logger: logging.Logger,
        reconnect_sleep: float = 5.0,
        max_reconnect_seconds: float = 0.0,
    ):
        self.dsn = dsn
        self.role = role
        self.logger = logger
        self.reconnect_sleep = reconnect_sleep
        self.max_reconnect_seconds = max_reconnect_seconds
        self._conn: Any = None
        self._connect_lock = threading.RLock()

    def close(self) -> None:
        with self._connect_lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    def connect(self) -> Any:
        with self._connect_lock:
            if self._conn is not None:
                return self._conn
            pymysql = import_pymysql()
            kwargs = self.dsn.connect_kwargs()
            kwargs["cursorclass"] = pymysql.cursors.DictCursor
            started = time.monotonic()
            while True:
                try:
                    self._conn = pymysql.connect(**kwargs)
                    self.logger.info("connected role=%s dsn=%s", self.role, self.dsn.redacted())
                    return self._conn
                except Exception as exc:
                    elapsed = time.monotonic() - started
                    self.logger.warning(
                        "connect failed role=%s elapsed=%.1fs error=%s",
                        self.role,
                        elapsed,
                        exc,
                    )
                    if self.max_reconnect_seconds and elapsed >= self.max_reconnect_seconds:
                        raise FuzzFailure(
                            "reconnect_failed",
                            f"cannot reconnect to {self.role} after {elapsed:.1f}s",
                            {"dsn": self.dsn.redacted(), "error": repr(exc)},
                        ) from exc
                    time.sleep(self.reconnect_sleep)

    def reconnect(self) -> Any:
        self.close()
        return self.connect()

    def run(self, fn: Callable[[Any], Any]) -> Any:
        while True:
            conn = self.connect()
            try:
                return fn(conn)
            except Exception as exc:
                if is_disconnect_error(exc):
                    self.logger.warning("disconnect role=%s error=%s; reconnecting", self.role, exc)
                    self.reconnect()
                    continue
                raise

    def query(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        def _run(conn: Any) -> List[Dict[str, Any]]:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())

        return self.run(_run)

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        def _run(conn: Any) -> int:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return int(cur.rowcount)

        return self.run(_run)

    @contextmanager
    def transaction(self) -> Iterable[Any]:
        conn = self.connect()
        try:
            conn.begin()
            yield conn
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            if is_disconnect_error(sys.exc_info()[1]):
                self.close()
            raise


class BucketLocks:
    def __init__(self, bucket_count: int):
        self._locks = [threading.RLock() for _ in range(bucket_count)]

    @contextmanager
    def acquire(self, buckets: Sequence[int]) -> Iterable[None]:
        locks = [self._locks[bucket] for bucket in sorted(set(buckets))]
        for lock in locks:
            lock.acquire()
        try:
            yield
        finally:
            for lock in reversed(locks):
                lock.release()


class FuzzRunner:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.seed = int(args.seed if args.seed is not None else int(time.time()))
        self.run_id = args.run_id or f"{DEFAULT_RUN_ID_PREFIX}-{self.seed}"
        self.session_id = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        self.op_prefix = f"{self.run_id}-{self.session_id}"
        self.state = StateStore(Path(args.state_dir), self.seed)
        self.logger = setup_logging(self.state.run_log_path, args.verbose)
        self.primary_dsn = Dsn.parse(args.primary_dsn)
        self.readonly_dsn = Dsn.parse(args.readonly_dsn)
        self.payload_factory = PayloadFactory(self.seed)
        self.oracle = OracleState()
        self.bucket_locks = BucketLocks(args.bucket_count)
        self.stop_event = threading.Event()
        self.threads: List[threading.Thread] = []
        self._engine_metric_lock = threading.RLock()
        self._last_engine_metric_at = 0.0

    def run(self) -> int:
        self.logger.info(
            "LargeSLB fuzz start seed=%s run_id=%s session_id=%s",
            self.seed,
            self.run_id,
            self.session_id,
        )
        loaded = self.state.load_oracle(self.oracle)
        self.logger.info("loaded oracle events=%d", loaded)

        primary = self.make_client(self.primary_dsn, "primary-main")
        self.capture_config_snapshot(primary)
        self.init_schema(primary)
        self.ensure_seed_rows(primary)
        if self.args.init_only:
            self.logger.info("init-only requested; exiting")
            return 0

        self.install_signal_handlers()
        for worker_id in range(self.args.workers):
            thread = threading.Thread(
                target=self.worker_loop,
                args=(worker_id,),
                name=f"lslb-fuzz-worker-{worker_id}",
                daemon=True,
            )
            thread.start()
            self.threads.append(thread)

        deadline = compute_deadline(self.args.duration)
        try:
            while not self.stop_event.is_set():
                if deadline and time.monotonic() >= deadline:
                    self.logger.info("duration reached; stopping")
                    self.stop_event.set()
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("keyboard interrupt; stopping")
            self.stop_event.set()

        for thread in self.threads:
            thread.join(timeout=30)
        self.logger.info("LargeSLB fuzz stopped")
        return 0

    def make_client(self, dsn: Dsn, role: str) -> MySqlClient:
        return MySqlClient(
            dsn=dsn,
            role=role,
            logger=self.logger,
            reconnect_sleep=self.args.reconnect_sleep,
            max_reconnect_seconds=self.args.max_reconnect_seconds,
        )

    def install_signal_handlers(self) -> None:
        def _handler(signum: int, _frame: Any) -> None:
            self.logger.info("signal %s received; stopping", signum)
            self.stop_event.set()

        signal.signal(signal.SIGTERM, _handler)
        signal.signal(signal.SIGINT, _handler)

    def capture_config_snapshot(self, primary: MySqlClient) -> None:
        names = [
            "enable_large_slb",
            "innodb_log_write_max_size",
            "innodb_log_write_min_size",
            "innodb_log_write_min_time_interval",
            "sal_tlb_max_size",
            "slice_tlb_size",
            "slice_flush_size_threshold",
            "slice_tlb_size_max",
        ]
        placeholders = ",".join(["%s"] * len(names))
        try:
            rows = primary.query(
                f"SHOW VARIABLES WHERE Variable_name IN ({placeholders})",
                names,
            )
            snapshot = {row["Variable_name"]: row["Value"] for row in rows}
            path = self.state.state_dir / "config_snapshot.json"
            path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
            self.logger.info("config snapshot recorded keys=%s", sorted(snapshot))
        except Exception as exc:
            self.logger.warning("config snapshot skipped error=%s", exc)

    def init_schema(self, primary: MySqlClient) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS lslb_fuzz_rows (
              id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
              run_id VARCHAR(80) NOT NULL,
              bucket INT NOT NULL,
              payload LONGTEXT NULL,
              char_255 CHAR(255) NOT NULL DEFAULT '',
              varchar_16383 VARCHAR(16383) CHARACTER SET latin1 COLLATE latin1_bin NOT NULL DEFAULT '',
              text_col TEXT NULL,
              mediumtext_col MEDIUMTEXT NULL,
              longtext_col LONGTEXT NULL,
              blob_col BLOB NULL,
              mediumblob_col MEDIUMBLOB NULL,
              longblob_col LONGBLOB NULL,
              target_field VARCHAR(64) NOT NULL DEFAULT 'payload',
              payload_len INT UNSIGNED NOT NULL,
              version BIGINT UNSIGNED NOT NULL DEFAULT 0,
              last_op_id VARCHAR(160) NOT NULL,
              payload_sha CHAR(64) NOT NULL,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (id),
              KEY idx_run_bucket_id (run_id, bucket, id),
              KEY idx_run_last_op (run_id, last_op_id),
              KEY idx_run_bucket_op (run_id, bucket, last_op_id)
            ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC
            """,
            """
            CREATE TABLE IF NOT EXISTS lslb_fuzz_ops (
              op_id VARCHAR(160) NOT NULL,
              run_id VARCHAR(80) NOT NULL,
              seed BIGINT NOT NULL,
              worker_id INT NOT NULL,
              sequence_no BIGINT NOT NULL,
              scenario VARCHAR(64) NOT NULL,
              target_field VARCHAR(64) NOT NULL DEFAULT 'payload',
              buckets_json LONGTEXT NOT NULL,
              row_count INT UNSIGNED NOT NULL,
              payload_len INT UNSIGNED NOT NULL,
              repeat_updates INT UNSIGNED NOT NULL,
              total_payload_bytes BIGINT UNSIGNED NOT NULL,
              row_ids_json LONGTEXT NOT NULL,
              final_payload_sha CHAR(64) NOT NULL,
              primary_signature VARCHAR(128) NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (op_id),
              KEY idx_run_created (run_id, created_at),
              KEY idx_run_scenario (run_id, scenario)
            ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC
            """,
            """
            CREATE TABLE IF NOT EXISTS lslb_fuzz_checkpoints (
              checkpoint_id VARCHAR(160) NOT NULL,
              op_id VARCHAR(160) NOT NULL,
              run_id VARCHAR(80) NOT NULL,
              target_field VARCHAR(64) NOT NULL DEFAULT 'payload',
              expected_rows INT UNSIGNED NOT NULL,
              expected_signature VARCHAR(128) NOT NULL,
              row_ids_json LONGTEXT NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (checkpoint_id),
              KEY idx_run_op (run_id, op_id)
            ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC
            """,
        ]
        for sql in statements:
            primary.execute(sql)
        self.ensure_payload_columns(primary)
        self.ensure_auxiliary_columns(primary)

    def ensure_payload_columns(self, primary: MySqlClient) -> None:
        existing = {row["Field"] for row in primary.query("SHOW COLUMNS FROM lslb_fuzz_rows")}
        alters = []
        for spec in FIELD_SPECS.values():
            if spec.column not in existing:
                alters.append(f"ADD COLUMN {spec.column} {spec.sql_type}")
        if "target_field" not in existing:
            alters.append("ADD COLUMN target_field VARCHAR(64) NOT NULL DEFAULT 'payload'")
        if alters:
            primary.execute("ALTER TABLE lslb_fuzz_rows " + ", ".join(alters))

    def ensure_auxiliary_columns(self, primary: MySqlClient) -> None:
        for table in ("lslb_fuzz_ops", "lslb_fuzz_checkpoints"):
            existing = {row["Field"] for row in primary.query(f"SHOW COLUMNS FROM {table}")}
            if "target_field" not in existing:
                primary.execute(
                    f"ALTER TABLE {table} ADD COLUMN target_field VARCHAR(64) NOT NULL DEFAULT 'payload'"
                )

    def ensure_seed_rows(self, primary: MySqlClient) -> None:
        seed_payload, seed_sha = self.payload_factory.make("seed", self.args.seed_payload_len)
        seed_blob, _seed_blob_sha = self.payload_factory.make_bytes("seed", self.args.seed_payload_len)
        batch_size = min(500, self.args.rows_per_bucket)
        for bucket in range(self.args.bucket_count):
            rows = primary.query(
                "SELECT COUNT(*) AS cnt FROM lslb_fuzz_rows WHERE run_id=%s AND bucket=%s",
                (self.run_id, bucket),
            )
            current = int(rows[0]["cnt"])
            missing = self.args.rows_per_bucket - current
            while missing > 0:
                count = min(batch_size, missing)

                def _insert(conn: Any) -> None:
                    with conn.cursor() as cur:
                        cur.executemany(
	                            """
	                            INSERT INTO lslb_fuzz_rows
	                              (run_id, bucket, payload, char_255, varchar_16383,
                                   text_col, mediumtext_col, longtext_col,
                                   blob_col, mediumblob_col, longblob_col,
                                   target_field, payload_len, version, last_op_id, payload_sha)
	                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 'seed', %s)
	                            """,
	                            [
	                                (
	                                    self.run_id,
	                                    bucket,
	                                    seed_payload,
                                        "",
                                        "",
                                        seed_payload,
                                        seed_payload,
                                        seed_payload,
                                        seed_blob,
                                        seed_blob,
                                        seed_blob,
                                        "payload",
	                                    self.args.seed_payload_len,
	                                    seed_sha,
	                                )
                                for _ in range(count)
                            ],
                        )

                primary.run(_insert)
                missing -= count
                current += count
                self.logger.info(
                    "seed rows bucket=%s current=%s target=%s",
                    bucket,
                    current,
                    self.args.rows_per_bucket,
                )

    def worker_loop(self, worker_id: int) -> None:
        rng = random.Random(self.seed + worker_id * 7919)
        generator = ScenarioGenerator(
            seed=self.seed,
            bucket_count=self.args.bucket_count,
            rng=rng,
            checkpoint_rate=self.args.readonly_check_rate,
            op_prefix=self.op_prefix,
            target_fields=parse_target_fields(self.args.target_fields),
        )
        primary = self.make_client(self.primary_dsn, f"primary-worker-{worker_id}")
        readonly = self.make_client(self.readonly_dsn, f"readonly-worker-{worker_id}")
        sequence = 0
        while not self.stop_event.is_set():
            sequence += 1
            plan = generator.next_plan(worker_id=worker_id, sequence=sequence)
            if plan.unsupported_single_redo:
                self.logger.warning("unsupported plan skipped op_id=%s", plan.op_id)
                continue
            with self.bucket_locks.acquire(plan.buckets):
                self.execute_one_plan(primary, readonly, plan, rng)
            if self.args.sleep_ms > 0:
                time.sleep(self.args.sleep_ms / 1000.0)

    def execute_one_plan(
        self,
        primary: MySqlClient,
        readonly: MySqlClient,
        plan: OperationPlan,
        rng: random.Random,
    ) -> None:
        started = time.monotonic()
        primary_check_ms = 0.0
        readonly_check_ms = 0.0
        status = "unknown"
        selected_rows: List[RowBefore] = []
        final_sha = ""
        try:
            selected_rows, final_sha, primary_signature = self.commit_plan(primary, plan, rng)
            expected = self.oracle.apply_commit(
                plan=plan,
                rows=selected_rows,
                final_payload_sha=final_sha,
                final_payload_len=plan.payload_len,
            )
            self.state.record_oracle(plan, expected)
            self.state.record_op(
                {
                    "op_id": plan.op_id,
                    "status": "committed",
                    "plan": plan.to_json(),
                    "row_ids": [row.row_id for row in selected_rows],
                    "primary_signature": primary_signature,
                }
            )

            check_started = time.monotonic()
            self.verify_primary_rows(primary, plan, selected_rows)
            primary_check_ms = elapsed_ms(check_started)

            if plan.checkpoint:
                check_started = time.monotonic()
                self.verify_readonly_checkpoint(
                    readonly=readonly,
                    plan=plan,
                    row_ids=[row.row_id for row in selected_rows],
                    expected_signature=primary_signature,
                )
                readonly_check_ms = elapsed_ms(check_started)
            status = "committed"
        except TransactionNotCommitted as skipped:
            status = "not_committed"
            self.state.record_op(
                {
                    "op_id": plan.op_id,
                    "status": status,
                    "reason": skipped.reason,
                    "plan": plan.to_json(),
                    "row_ids": [row.row_id for row in selected_rows],
                }
            )
            self.logger.info("transaction not committed op_id=%s reason=%s", plan.op_id, skipped.reason)
        except FuzzFailure as failure:
            status = f"failure:{failure.kind}"
            failure_dir = self.state.record_failure(
                failure,
                plan=plan,
                extra={"selected_rows": [dataclasses.asdict(row) for row in selected_rows]},
                reproducer_sql=make_reproducer_sql(self.run_id, plan, selected_rows),
            )
            self.logger.error("fuzz failure saved path=%s kind=%s error=%s", failure_dir, failure.kind, failure)
        except Exception as exc:
            status = "error"
            failure = FuzzFailure("unexpected_exception", str(exc), {"error": repr(exc)})
            failure_dir = self.state.record_failure(
                failure,
                plan=plan,
                extra={"selected_rows": [dataclasses.asdict(row) for row in selected_rows]},
                reproducer_sql=make_reproducer_sql(self.run_id, plan, selected_rows),
            )
            self.logger.error("unexpected error saved path=%s error=%s", failure_dir, exc)
        finally:
            self.state.record_metric(
                plan=plan,
                status=status,
                latency_ms=elapsed_ms(started),
                primary_check_ms=primary_check_ms,
                readonly_check_ms=readonly_check_ms,
            )
            self.maybe_record_engine_metrics(primary, plan)

    def maybe_record_engine_metrics(self, primary: MySqlClient, plan: OperationPlan) -> None:
        if self.args.engine_metric_interval <= 0:
            return
        now = time.monotonic()
        with self._engine_metric_lock:
            if now - self._last_engine_metric_at < self.args.engine_metric_interval:
                return
            self._last_engine_metric_at = now
        placeholders = ",".join(["%s"] * len(ENGINE_METRIC_NAMES))
        try:
            rows = primary.query(
                f"SHOW GLOBAL STATUS WHERE Variable_name IN ({placeholders})",
                ENGINE_METRIC_NAMES,
            )
            self.state.record_engine_metrics(plan, normalize_variable_rows(rows))
        except Exception as exc:
            self.logger.debug("engine metric sample skipped error=%s", exc)

    def commit_plan(
        self,
        primary: MySqlClient,
        plan: OperationPlan,
        rng: random.Random,
    ) -> Tuple[List[RowBefore], str, str]:
        selected_rows: List[RowBefore] = []
        final_sha = ""
        primary_signature = ""
        try:
            with primary.transaction() as conn:
                selected_rows = self.select_rows_for_update(conn, plan, rng)
                row_ids = [row.row_id for row in selected_rows]
                if len(row_ids) != plan.expected_row_count:
                    raise FuzzFailure(
                        "insufficient_seed_rows",
                        f"expected {plan.expected_row_count} rows, selected {len(row_ids)}",
                        {"plan": plan.to_json()},
                    )

                for round_no in range(plan.repeat_updates):
                    payload, payload_sha = self.make_plan_payload(plan, round_no)
                    final_sha = payload_sha
                    self.update_rows(conn, row_ids, payload, plan, payload_sha)

                primary_signature = self.compute_signature(conn, row_ids, plan.op_id, plan.target_field)
                self.insert_op(conn, plan, row_ids, final_sha, primary_signature)
                if plan.checkpoint:
                    self.insert_checkpoint(conn, plan, row_ids, primary_signature)
            return selected_rows, final_sha, primary_signature
        except Exception as exc:
            if is_retryable_txn_error(exc):
                raise TransactionNotCommitted(
                    plan.op_id,
                    f"retryable transaction rollback: {exc}",
                ) from exc
            if is_disconnect_error(exc):
                self.logger.warning("ambiguous disconnect op_id=%s error=%s", plan.op_id, exc)
                return self.resolve_ambiguous_commit(primary, plan, selected_rows, final_sha)
            if is_corruption_error(exc):
                raise FuzzFailure(
                    "sql_corruption_error",
                    "SQL returned corruption/assertion-like error",
                    {"op_id": plan.op_id, "error": repr(exc)},
                ) from exc
            raise

    def make_plan_payload(self, plan: OperationPlan, round_no: int) -> Tuple[Any, str]:
        spec = FIELD_SPECS[plan.target_field]
        salt = f"{plan.target_field}-round-{round_no}"
        if spec.is_binary:
            return self.payload_factory.make_bytes(plan.op_id, plan.payload_len, salt=salt)
        return self.payload_factory.make(plan.op_id, plan.payload_len, salt=salt)

    def resolve_ambiguous_commit(
        self,
        primary: MySqlClient,
        plan: OperationPlan,
        selected_rows: Sequence[RowBefore],
        final_sha: str,
    ) -> Tuple[List[RowBefore], str, str]:
        primary.reconnect()
        rows = primary.query(
            "SELECT COUNT(*) AS cnt FROM lslb_fuzz_ops WHERE run_id=%s AND op_id=%s",
            (self.run_id, plan.op_id),
        )
        committed = int(rows[0]["cnt"]) == 1
        visible = primary.query(
            "SELECT COUNT(*) AS cnt FROM lslb_fuzz_rows WHERE run_id=%s AND last_op_id=%s",
            (self.run_id, plan.op_id),
        )
        visible_rows = int(visible[0]["cnt"])
        if committed:
            if not selected_rows:
                selected_rows = self.fetch_rows_before_from_db(primary, plan)
            row_ids = [row.row_id for row in selected_rows]

            def _signature(conn: Any) -> str:
                return self.compute_signature(conn, row_ids, plan.op_id, plan.target_field)

            signature = primary.run(_signature)
            return list(selected_rows), final_sha, signature
        if visible_rows > 0:
            raise FuzzFailure(
                "orphan_rows_without_op",
                "data rows contain op_id but lslb_fuzz_ops has no committed op",
                {"op_id": plan.op_id, "visible_rows": visible_rows},
            )
        raise TransactionNotCommitted(
            plan.op_id,
            "transaction disappeared after disconnect; no op row and no data rows were visible",
        )

    def select_rows_for_update(
        self,
        conn: Any,
        plan: OperationPlan,
        rng: random.Random,
    ) -> List[RowBefore]:
        rows: List[RowBefore] = []
        with conn.cursor() as cur:
            for bucket in plan.buckets:
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM lslb_fuzz_rows WHERE run_id=%s AND bucket=%s",
                    (self.run_id, bucket),
                )
                count = int(cur.fetchone()["cnt"])
                if count < plan.rows_per_bucket:
                    raise FuzzFailure(
                        "insufficient_bucket_rows",
                        "bucket does not contain enough seed rows",
                        {"bucket": bucket, "count": count, "needed": plan.rows_per_bucket},
                    )
                offset = rng.randint(0, max(0, count - plan.rows_per_bucket))
                cur.execute(
                    """
                    SELECT id, bucket, version
                    FROM lslb_fuzz_rows
                    WHERE run_id=%s AND bucket=%s
                    ORDER BY id
                    LIMIT %s OFFSET %s
                    FOR UPDATE
                    """,
                    (self.run_id, bucket, plan.rows_per_bucket, offset),
                )
                rows.extend(
                    RowBefore(
                        row_id=int(item["id"]),
                        bucket=int(item["bucket"]),
                        version=int(item["version"]),
                    )
                    for item in cur.fetchall()
                )
        return rows

    def update_rows(
        self,
        conn: Any,
        row_ids: Sequence[int],
        payload: Any,
        plan: OperationPlan,
        payload_sha: str,
    ) -> None:
        spec = FIELD_SPECS[plan.target_field]
        for chunk in chunks(list(row_ids), self.args.update_chunk_size):
            placeholders = ",".join(["%s"] * len(chunk))
            sql = f"""
                UPDATE lslb_fuzz_rows
                SET {spec.column}=%s,
                    target_field=%s,
                    payload_len=%s,
                    version=version + 1,
                    last_op_id=%s,
                    payload_sha=%s
                WHERE run_id=%s AND id IN ({placeholders})
            """
            params: List[Any] = [
                payload,
                plan.target_field,
                plan.payload_len,
                plan.op_id,
                payload_sha,
                self.run_id,
            ] + list(chunk)
            with conn.cursor() as cur:
                cur.execute(sql, params)

    def insert_op(
        self,
        conn: Any,
        plan: OperationPlan,
        row_ids: Sequence[int],
        final_sha: str,
        primary_signature: str,
    ) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lslb_fuzz_ops
                  (op_id, run_id, seed, worker_id, sequence_no, scenario,
                   target_field, buckets_json, row_count, payload_len, repeat_updates,
                   total_payload_bytes, row_ids_json, final_payload_sha, primary_signature)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    plan.op_id,
                    self.run_id,
                    self.seed,
                    plan.worker_id,
                    plan.sequence,
                    plan.kind,
                    plan.target_field,
                    json.dumps(plan.buckets, separators=(",", ":")),
                    len(row_ids),
                    plan.payload_len,
                    plan.repeat_updates,
                    plan.total_payload_bytes,
                    json.dumps(list(row_ids), separators=(",", ":")),
                    final_sha,
                    primary_signature,
                ),
            )

    def insert_checkpoint(
        self,
        conn: Any,
        plan: OperationPlan,
        row_ids: Sequence[int],
        primary_signature: str,
    ) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lslb_fuzz_checkpoints
                  (checkpoint_id, op_id, run_id, target_field, expected_rows, expected_signature, row_ids_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    plan.op_id,
                    plan.op_id,
                    self.run_id,
                    plan.target_field,
                    len(row_ids),
                    primary_signature,
                    json.dumps(list(row_ids), separators=(",", ":")),
                ),
            )

    def compute_signature(
        self,
        conn: Any,
        row_ids: Sequence[int],
        op_id: str,
        target_field: str,
    ) -> str:
        spec = FIELD_SPECS[target_field]
        total_count = 0
        total_crc_sum = 0
        total_crc_xor = 0
        total_version_sum = 0
        for chunk in chunks(list(row_ids), self.args.query_chunk_size):
            placeholders = ",".join(["%s"] * len(chunk))
            sql = f"""
                SELECT
                  COUNT(*) AS cnt,
                  COALESCE(SUM(CAST(CRC32(CONCAT_WS('#',
                    id, version, last_op_id, target_field, payload_len, payload_sha,
                    IFNULL(OCTET_LENGTH({spec.column}), 0),
                    IFNULL(SHA2({spec.column}, 256), '')
                  )) AS UNSIGNED)), 0) AS crc_sum,
                  COALESCE(BIT_XOR(CAST(CRC32(CONCAT_WS('#',
                    id, version, last_op_id, target_field, payload_len, payload_sha,
                    IFNULL(OCTET_LENGTH({spec.column}), 0),
                    IFNULL(SHA2({spec.column}, 256), '')
                  )) AS UNSIGNED)), 0) AS crc_xor,
                  COALESCE(SUM(version), 0) AS version_sum
                FROM lslb_fuzz_rows
                WHERE run_id=%s AND last_op_id=%s AND target_field=%s AND id IN ({placeholders})
            """
            with conn.cursor() as cur:
                cur.execute(sql, [self.run_id, op_id, target_field] + list(chunk))
                row = cur.fetchone()
            total_count += int(row["cnt"])
            total_crc_sum += int(row["crc_sum"])
            total_crc_xor ^= int(row["crc_xor"])
            total_version_sum += int(row["version_sum"])
        return f"{total_count}:{total_crc_sum}:{total_crc_xor}:{total_version_sum}"

    def fetch_rows_before_from_db(self, primary: MySqlClient, plan: OperationPlan) -> List[RowBefore]:
        rows = primary.query(
            """
            SELECT id, bucket, version
            FROM lslb_fuzz_rows
            WHERE run_id=%s AND last_op_id=%s
            ORDER BY id
            """,
            (self.run_id, plan.op_id),
        )
        return [
            RowBefore(
                row_id=int(row["id"]),
                bucket=int(row["bucket"]),
                version=max(0, int(row["version"]) - plan.repeat_updates),
            )
            for row in rows
        ]

    def verify_primary_rows(
        self,
        primary: MySqlClient,
        plan: OperationPlan,
        rows: Sequence[RowBefore],
    ) -> None:
        expected = self.oracle.expected_for_rows(row.row_id for row in rows)
        if len(expected) != len(rows):
            raise FuzzFailure(
                "oracle_missing_rows",
                "oracle does not contain every touched row",
                {"op_id": plan.op_id, "expected": len(rows), "actual": len(expected)},
            )
        actual = self.fetch_current_rows(primary, [row.row_id for row in rows], plan.target_field)
        for row_id, exp in expected.items():
            item = actual.get(row_id)
            if item is None:
                raise FuzzFailure(
                    "primary_row_missing",
                    "committed row is missing on primary",
                    {"op_id": plan.op_id, "row_id": row_id},
                )
            mismatches = {}
            for key in ("version", "last_op_id", "target_field", "payload_len", "payload_sha"):
                if item[key] != getattr(exp, key):
                    mismatches[key] = {"expected": getattr(exp, key), "actual": item[key]}
            if item["actual_payload_len"] != exp.payload_len:
                mismatches["actual_payload_len"] = {
                    "expected": exp.payload_len,
                    "actual": item["actual_payload_len"],
                }
            if item["actual_payload_sha"] != exp.payload_sha:
                mismatches["actual_payload_sha"] = {
                    "expected": exp.payload_sha,
                    "actual": item["actual_payload_sha"],
                }
            if mismatches:
                raise FuzzFailure(
                    "primary_oracle_mismatch",
                    "primary row differs from Python oracle",
                    {"op_id": plan.op_id, "row_id": row_id, "mismatches": mismatches},
                )

    def fetch_current_rows(
        self,
        client: MySqlClient,
        row_ids: Sequence[int],
        target_field: str,
    ) -> Dict[int, Dict[str, Any]]:
        spec = FIELD_SPECS[target_field]
        result: Dict[int, Dict[str, Any]] = {}
        for chunk in chunks(list(row_ids), self.args.query_chunk_size):
            placeholders = ",".join(["%s"] * len(chunk))
            sql = f"""
                SELECT
                  id,
                  bucket,
                  version,
                  last_op_id,
                  target_field,
                  payload_len,
                  payload_sha,
                  OCTET_LENGTH({spec.column}) AS actual_payload_len,
                  SHA2({spec.column}, 256) AS actual_payload_sha
                FROM lslb_fuzz_rows
                WHERE run_id=%s AND target_field=%s AND id IN ({placeholders})
            """
            rows = client.query(sql, [self.run_id, target_field] + list(chunk))
            for row in rows:
                result[int(row["id"])] = {
                    "bucket": int(row["bucket"]),
                    "version": int(row["version"]),
                    "last_op_id": str(row["last_op_id"]),
                    "target_field": str(row["target_field"]),
                    "payload_len": int(row["payload_len"]),
                    "payload_sha": str(row["payload_sha"]),
                    "actual_payload_len": int(row["actual_payload_len"]),
                    "actual_payload_sha": str(row["actual_payload_sha"]),
                }
        return result

    def verify_readonly_checkpoint(
        self,
        readonly: MySqlClient,
        plan: OperationPlan,
        row_ids: Sequence[int],
        expected_signature: str,
    ) -> None:
        deadline = time.monotonic() + self.args.replica_timeout
        last_state: Dict[str, Any] = {}
        while time.monotonic() < deadline and not self.stop_event.is_set():
            checkpoint_visible, visible_rows, signature = self.read_replica_checkpoint_state(
                readonly,
                plan,
                row_ids,
            )
            visibility = classify_replica_visibility(
                checkpoint_visible=checkpoint_visible,
                visible_rows=visible_rows,
                expected_rows=len(row_ids),
            )
            last_state = {
                "checkpoint_visible": checkpoint_visible,
                "visible_rows": visible_rows,
                "signature": signature,
                "expected_signature": expected_signature,
                "visibility": visibility.value,
            }
            if visibility == ReplicaVisibility.HALF_VISIBLE:
                raise FuzzFailure(
                    "readonly_half_visible",
                    "readonly replica sees only part of checkpoint transaction",
                    {"op_id": plan.op_id, **last_state},
                )
            if visibility == ReplicaVisibility.CONSISTENT:
                if signature != expected_signature:
                    raise FuzzFailure(
                        "readonly_signature_mismatch",
                        "readonly checkpoint is visible but signature differs from primary",
                        {"op_id": plan.op_id, **last_state},
                    )
                return
            time.sleep(self.args.replica_poll_interval)
        raise FuzzFailure(
            "readonly_checkpoint_timeout",
            "readonly replica did not reach checkpoint before timeout",
            {"op_id": plan.op_id, **last_state},
        )

    def read_replica_checkpoint_state(
        self,
        readonly: MySqlClient,
        plan: OperationPlan,
        row_ids: Sequence[int],
    ) -> Tuple[int, int, str]:
        def _read(conn: Any) -> Tuple[int, int, str]:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                      (SELECT COUNT(*) FROM lslb_fuzz_checkpoints
                       WHERE run_id=%s AND checkpoint_id=%s AND target_field=%s) AS checkpoint_visible,
                      (SELECT COUNT(*) FROM lslb_fuzz_rows
                       WHERE run_id=%s AND last_op_id=%s AND target_field=%s) AS visible_rows
                    """,
                    (
                        self.run_id,
                        plan.op_id,
                        plan.target_field,
                        self.run_id,
                        plan.op_id,
                        plan.target_field,
                    ),
                )
                state = cur.fetchone()
                signature = self.compute_signature(conn, row_ids, plan.op_id, plan.target_field)
                return int(state["checkpoint_visible"]), int(state["visible_rows"]), signature

        return readonly.run(_read)


def import_pymysql() -> Any:
    try:
        import pymysql  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyMySQL is required. Install it with: python3 -m pip install PyMySQL"
        ) from exc
    return pymysql


def is_disconnect_error(exc: BaseException) -> bool:
    code = mysql_error_code(exc)
    if code in DISCONNECT_ERROR_CODES:
        return True
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "server has gone away",
            "lost connection",
            "connection refused",
            "can't connect",
            "broken pipe",
            "connection reset",
        )
    )


def is_retryable_txn_error(exc: BaseException) -> bool:
    return mysql_error_code(exc) in RETRYABLE_TXN_ERROR_CODES


def is_corruption_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in CORRUPTION_HINTS)


def mysql_error_code(exc: BaseException) -> Optional[int]:
    args = getattr(exc, "args", ())
    if args and isinstance(args[0], int):
        return int(args[0])
    return None


def chunks(items: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def utc_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def elapsed_ms(started: float) -> float:
    return (time.monotonic() - started) * 1000.0


def compute_deadline(duration: str) -> Optional[float]:
    seconds = parse_duration_seconds(duration)
    if seconds <= 0:
        return None
    return time.monotonic() + seconds


def parse_duration_seconds(value: str) -> float:
    text = str(value).strip().lower()
    if text in ("", "0", "forever", "infinite"):
        return 0.0
    multiplier = 1.0
    if text[-1] == "s":
        text = text[:-1]
    elif text[-1] == "m":
        text = text[:-1]
        multiplier = 60.0
    elif text[-1] == "h":
        text = text[:-1]
        multiplier = 3600.0
    elif text[-1] == "d":
        text = text[:-1]
        multiplier = 86400.0
    return float(text) * multiplier


def parse_target_fields(value: str) -> Tuple[str, ...]:
    if not value.strip():
        return DEFAULT_TARGET_FIELDS
    fields = tuple(item.strip() for item in value.split(",") if item.strip())
    unknown = [field for field in fields if field not in FIELD_SPECS]
    if unknown:
        raise ValueError(f"unknown target fields: {','.join(unknown)}")
    return fields or DEFAULT_TARGET_FIELDS


def normalize_variable_rows(rows: Sequence[Dict[str, Any]]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for row in rows:
        lower = {str(key).lower(): value for key, value in row.items()}
        name = lower.get("variable_name")
        value = lower.get("value", lower.get("variable_value"))
        if name is not None and value is not None:
            normalized[str(name)] = str(value)
    return normalized


def sql_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def make_reproducer_sql(run_id: str, plan: OperationPlan, rows: Sequence[RowBefore]) -> str:
    spec = FIELD_SPECS[plan.target_field]
    row_ids = [row.row_id for row in rows]
    if not row_ids:
        row_ids_sql = "/* rows were not selected before failure */"
    else:
        row_ids_sql = ",".join(str(row_id) for row_id in row_ids)
    lines = [
        "-- LargeSLB fuzz failure reproducer.",
        f"-- op_id: {plan.op_id}",
        f"-- scenario: {plan.kind}",
        f"-- rows: {len(row_ids)} payload_len: {plan.payload_len} repeat_updates: {plan.repeat_updates}",
        "START TRANSACTION;",
    ]
    if row_ids:
        for round_no in range(plan.repeat_updates):
            marker = f"{plan.op_id}_round_{round_no}"
            if spec.is_binary:
                value_expr = (
                    "UNHEX(LEFT(REPEAT(SHA2("
                    f"{sql_quote(marker)}, 256), "
                    f"({plan.payload_len * 2} DIV 64) + 2), {plan.payload_len * 2}))"
                )
            else:
                value_expr = (
                    f"LEFT(REPEAT({sql_quote(marker)}, "
                    f"({plan.payload_len} DIV GREATEST(1, CHAR_LENGTH({sql_quote(marker)}))) + 2), "
                    f"{plan.payload_len})"
                )
            lines.append(
                "UPDATE lslb_fuzz_rows "
                f"SET {spec.column}={value_expr}, "
                f"target_field={sql_quote(plan.target_field)}, "
                f"payload_len={plan.payload_len}, version=version+1, "
                f"last_op_id={sql_quote(plan.op_id)}, "
                f"payload_sha=SHA2({spec.column}, 256) "
                f"WHERE run_id={sql_quote(run_id)} AND id IN ({row_ids_sql});"
            )
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def setup_logging(run_log_path: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger("largeslb_fuzz")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(threadName)s %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(run_log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Long-running SQL-only LargeSLB fuzz and correctness checker."
    )
    parser.add_argument("--primary-dsn", required=True, help="Primary MySQL DSN.")
    parser.add_argument("--readonly-dsn", required=True, help="Readonly replica MySQL DSN.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed. Defaults to current time.")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent writer workers.")
    parser.add_argument("--state-dir", required=True, help="Directory for logs, oracle, metrics, failures.")
    parser.add_argument("--duration", default="0", help="Run duration: 0/forever, 60s, 30m, 72h, 7d.")

    parser.add_argument("--run-id", default="", help="Logical run id. Defaults to largeslb-<seed>.")
    parser.add_argument("--bucket-count", type=int, default=16, help="Logical buckets for slice pressure.")
    parser.add_argument("--rows-per-bucket", type=int, default=2048, help="Seed rows per bucket.")
    parser.add_argument("--seed-payload-len", type=int, default=128, help="Payload length for seed rows.")
    parser.add_argument(
        "--target-fields",
        default=",".join(DEFAULT_TARGET_FIELDS),
        help="Comma-separated target fields: " + ",".join(FIELD_SPECS),
    )
    parser.add_argument("--readonly-check-rate", type=float, default=0.05, help="Checkpoint rate per op.")
    parser.add_argument("--replica-timeout", type=float, default=300.0, help="Readonly checkpoint timeout.")
    parser.add_argument("--replica-poll-interval", type=float, default=1.0, help="Readonly poll interval.")
    parser.add_argument("--update-chunk-size", type=int, default=256, help="Rows per UPDATE statement.")
    parser.add_argument("--query-chunk-size", type=int, default=512, help="Rows per verification query.")
    parser.add_argument("--sleep-ms", type=int, default=0, help="Optional sleep between worker operations.")
    parser.add_argument(
        "--engine-metric-interval",
        type=float,
        default=60.0,
        help="Seconds between best-effort SHOW GLOBAL STATUS samples. 0 disables sampling.",
    )
    parser.add_argument("--reconnect-sleep", type=float, default=5.0, help="Reconnect retry sleep seconds.")
    parser.add_argument(
        "--max-reconnect-seconds",
        type=float,
        default=0.0,
        help="0 means retry forever; positive value records reconnect_failed after this many seconds.",
    )
    parser.add_argument("--init-only", action="store_true", help="Create schema/seed rows and exit.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    runner = FuzzRunner(args)
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
