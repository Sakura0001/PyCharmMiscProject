"""PG18 runtime executor for ALTER TABLE factor-loop regress programs.

This module combines baseline + extension cases and maps each to its SQL
file, then provides a psql-based runner that executes each program against
an isolated PG 18.4 instance and compares two deterministic runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import subprocess
from typing import Any, Mapping, Protocol, Sequence


PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-alttbl-sock")
PG18_PORT = 55495
PG18_DATABASE = "pgcf_ap"
PG18_SUPERUSER = "pgcf_superuser"
PER_FILE_TIMEOUT_SECONDS = 30
MAX_PARALLELISM = 1

_TARGET_SQLSTATE = re.compile(rb"(?m)^PGCF_TARGET_SQLSTATE=([0-9A-Z]{5})\s*$")
_PREFIX = re.compile(r"^[a-z][a-z0-9_]*_$")
_CLEANUP_MARKER = "-- 5. 清理全部本编号对象。"


class AlterTableRuntimeCase(Protocol):
    case_id: str
    sql_filename: str
    object_prefix: str
    expected_sqlstate: str
    ordinal: int


@dataclass(frozen=True)
class AlterTableCaseRuntimeResult:
    case_id: str
    sql_filename: str
    expected_sqlstate: str
    target_sqlstate: str | None
    exit_code: int
    timed_out: bool
    normalized_stdout: bytes
    normalized_stderr: bytes
    boolean_oracle_failure_count: int
    pre_clean: bool
    post_clean: bool
    cleanup_exit_code: int

    def structured_projection(self) -> tuple[Any, ...]:
        return (
            self.exit_code,
            self.timed_out,
            self.boolean_oracle_failure_count,
            self.target_sqlstate,
            self.pre_clean,
            self.post_clean,
            self.cleanup_exit_code,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "sql_filename": self.sql_filename,
            "expected_sqlstate": self.expected_sqlstate,
            "target_sqlstate": self.target_sqlstate,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "boolean_oracle_failure_count": self.boolean_oracle_failure_count,
            "pre_clean": self.pre_clean,
            "post_clean": self.post_clean,
            "cleanup_exit_code": self.cleanup_exit_code,
        }


@dataclass(frozen=True)
class AlterTableSuiteRun:
    run_ordinal: int
    cases: tuple[AlterTableCaseRuntimeResult, ...]

    def __post_init__(self) -> None:
        if self.run_ordinal not in (1, 2):
            raise ValueError("run_ordinal must be 1 or 2")


@dataclass(frozen=True)
class AlterTableTwoRunComparison:
    passed: bool
    issues: tuple[str, ...]
    execution_count: int
    transcript_mismatch_case_ids: tuple[str, ...]
    structured_mismatch_case_ids: tuple[str, ...]
    sqlstate_mismatch_case_ids: tuple[str, ...]
    cleanup_failure_case_ids: tuple[str, ...]
    execution_failure_case_ids: tuple[str, ...]


def _case_ordinal(case: object) -> int:
    return getattr(case, "ordinal", 0)


def build_alter_table_runtime_case_set(
    repository_root: Path,
    sql_dir: Path,
) -> tuple[tuple[AlterTableRuntimeCase, ...], dict[str, Path]]:
    """Combine baseline + extension cases and map each to its SQL file."""

    root = Path(repository_root).resolve(strict=True)
    from .alter_table_factor_extension import (
        build_alter_table_factor_extension_plan,
    )
    from .alter_table_factor_loop import (
        build_alter_table_factor_loop_plan,
    )

    baseline = build_alter_table_factor_loop_plan(root).cases
    extensions = build_alter_table_factor_extension_plan(root).cases
    cases = [*baseline, *extensions]
    cases.sort(key=_case_ordinal)
    sql_paths = {
        case.case_id: sql_dir / case.sql_filename for case in cases
    }
    return tuple(cases), sql_paths


class AlterTablePg18Runner:
    """Execute ALTER TABLE regress programs against an isolated PG 18.4."""

    def __init__(
        self,
        *,
        bin_dir: Path = PG18_BIN,
        socket_dir: Path = PG18_SOCKET,
        port: int = PG18_PORT,
        database: str = PG18_DATABASE,
        role: str = PG18_SUPERUSER,
        timeout_seconds: int = PER_FILE_TIMEOUT_SECONDS,
    ) -> None:
        if not 1 <= timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be in [1, 300]")
        self._bin = Path(bin_dir)
        self._socket = Path(socket_dir)
        self._port = port
        self._db = database
        self._role = role
        self._timeout = timeout_seconds

    @property
    def psql(self) -> Path:
        return self._bin / "psql"

    def _base_command(self) -> list[str]:
        return [
            str(self.psql), "-X",
            "-h", str(self._socket), "-p", str(self._port),
            "-d", self._db, "-U", self._role,
            "-A", "-t", "-q",
            "-v", "VERBOSITY=sqlstate",
            "-v", "ON_ERROR_STOP=1",
        ]

    def _cleanup_command(self) -> list[str]:
        cmd = self._base_command()
        idx = cmd.index("ON_ERROR_STOP=1")
        cmd[idx] = "ON_ERROR_STOP=0"
        return cmd

    @staticmethod
    def _environment() -> dict[str, str]:
        env = dict(os.environ)
        env["PGOPTIONS"] = "-c client_min_messages=warning"
        return env

    def verify_server(self) -> None:
        if not self.psql.is_file():
            raise FileNotFoundError(f"psql not found: {self.psql}")
        result = subprocess.run(
            [*self._base_command(), "-c", "SHOW server_version_num;"],
            capture_output=True,
            timeout=self._timeout,
            env=self._environment(),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"server version probe failed: {result.stderr.decode()}"
            )
        version = int(result.stdout.strip())
        if not 180004 <= version < 180005:
            raise RuntimeError(f"unexpected server version: {version}")

    def _clean_probe(self, object_prefix: str) -> bool:
        if not _PREFIX.match(object_prefix):
            return False
        probe = (
            "SELECT NOT EXISTS ("
            " SELECT 1 FROM pg_class WHERE relname LIKE %s"
            " UNION ALL"
            " SELECT 1 FROM pg_namespace WHERE nspname LIKE %s"
            " UNION ALL"
            " SELECT 1 FROM pg_type WHERE typname LIKE %s"
            " UNION ALL"
            " SELECT 1 FROM pg_roles WHERE rolname LIKE %s"
            ");"
        )
        like = f"{object_prefix}%"
        result = subprocess.run(
            [*self._base_command(), "-c", probe, "-v", f"p1={like}"],
            capture_output=True,
            timeout=self._timeout,
            env=self._environment(),
        )
        return (
            result.returncode == 0
            and result.stdout.strip() == b"t"
        )

    @staticmethod
    def _cleanup_sql(sql: str) -> str:
        markers = sql.count(_CLEANUP_MARKER)
        if markers != 1:
            raise ValueError(
                f"expected 1 cleanup marker, found {markers}"
            )
        return sql.split(_CLEANUP_MARKER, 1)[1]

    @staticmethod
    def _normalize(payload: bytes, sql_path: Path) -> bytes:
        text = payload
        for needle in (str(sql_path.resolve()), str(sql_path)):
            text = text.replace(needle.encode(), b"<SQL_PATH>")
        return text

    def _execute_case(
        self,
        case: AlterTableRuntimeCase,
        sql_path: Path,
    ) -> AlterTableCaseRuntimeResult:
        sql_text = sql_path.read_text(encoding="utf-8")
        pre_clean = self._clean_probe(case.object_prefix)
        if pre_clean:
            result = subprocess.run(
                [*self._base_command(), "-f", str(sql_path)],
                capture_output=True,
                timeout=self._timeout,
                env=self._environment(),
            )
            exit_code = result.returncode
            timed_out = False
            stdout = result.stdout
            stderr = result.stderr
        else:
            exit_code = 125
            stdout = b""
            stderr = b"pre-run clean-state probe failed\n"
            timed_out = False
        cleanup_sql = self._cleanup_sql(sql_text)
        try:
            cleanup_result = subprocess.run(
                [*self._cleanup_command()],
                input=cleanup_sql.encode("utf-8"),
                capture_output=True,
                timeout=self._timeout,
                env=self._environment(),
            )
            cleanup_exit_code = cleanup_result.returncode
        except subprocess.TimeoutExpired:
            cleanup_exit_code = 124
        post_clean = self._clean_probe(case.object_prefix)
        match = _TARGET_SQLSTATE.search(stdout)
        target_sqlstate = (
            match.group(1).decode("ascii") if match else None
        )
        boolean_fail = sum(
            1 for line in stdout.splitlines() if line.strip() == b"f"
        )
        return AlterTableCaseRuntimeResult(
            case_id=case.case_id,
            sql_filename=case.sql_filename,
            expected_sqlstate=case.expected_sqlstate,
            target_sqlstate=target_sqlstate,
            exit_code=exit_code,
            timed_out=timed_out,
            normalized_stdout=self._normalize(stdout, sql_path),
            normalized_stderr=self._normalize(stderr, sql_path),
            boolean_oracle_failure_count=boolean_fail,
            pre_clean=pre_clean,
            post_clean=post_clean,
            cleanup_exit_code=cleanup_exit_code,
        )

    def run_cases(
        self,
        cases: Sequence[AlterTableRuntimeCase],
        sql_paths: Mapping[str, Path],
        *,
        run_ordinal: int,
        selected_case_ids: set[str] | None = None,
    ) -> AlterTableSuiteRun:
        self.verify_server()
        selected = cases
        if selected_case_ids is not None:
            selected = [
                c for c in cases if c.case_id in selected_case_ids
            ]
        results: list[AlterTableCaseRuntimeResult] = []
        for case in selected:
            path = sql_paths[case.case_id]
            if path.name != case.sql_filename:
                raise ValueError(
                    f"sql filename mismatch: {path.name} vs {case.sql_filename}"
                )
            if not path.is_file():
                raise FileNotFoundError(f"sql file not found: {path}")
            results.append(self._execute_case(case, path))
        return AlterTableSuiteRun(
            run_ordinal=run_ordinal, cases=tuple(results)
        )


def compare_alter_table_runs(
    run_01: AlterTableSuiteRun,
    run_02: AlterTableSuiteRun,
) -> AlterTableTwoRunComparison:
    """Require identical transcripts, structure, SQLSTATEs, and clean state."""

    issues: list[str] = []
    transcript_mismatch: list[str] = []
    structured_mismatch: list[str] = []
    sqlstate_mismatch: list[str] = []
    cleanup_failure: list[str] = []
    execution_failure: list[str] = []
    if len(run_01.cases) != len(run_02.cases):
        issues.append("run case counts differ")
        return AlterTableTwoRunComparison(
            passed=False,
            issues=tuple(dict.fromkeys(issues)),
            execution_count=len(run_01.cases),
            transcript_mismatch_case_ids=(),
            structured_mismatch_case_ids=(),
            sqlstate_mismatch_case_ids=(),
            cleanup_failure_case_ids=(),
            execution_failure_case_ids=(),
        )
    for r1, r2 in zip(run_01.cases, run_02.cases):
        cid = r1.case_id
        if r1.normalized_stdout != r2.normalized_stdout:
            transcript_mismatch.append(cid)
        if r1.structured_projection() != r2.structured_projection():
            structured_mismatch.append(cid)
        for result in (r1, r2):
            if result.target_sqlstate != result.expected_sqlstate:
                sqlstate_mismatch.append(cid)
            if result.cleanup_exit_code != 0 or not result.post_clean:
                cleanup_failure.append(cid)
            if (
                result.exit_code != 0
                or result.timed_out
                or result.boolean_oracle_failure_count != 0
                or not result.pre_clean
            ):
                execution_failure.append(cid)
    if transcript_mismatch:
        issues.append(
            f"transcript mismatches: {len(transcript_mismatch)}"
        )
    if structured_mismatch:
        issues.append(
            f"structured mismatches: {len(structured_mismatch)}"
        )
    if sqlstate_mismatch:
        issues.append(
            f"sqlstate mismatches: {len(sqlstate_mismatch)}"
        )
    if cleanup_failure:
        issues.append(
            f"cleanup failures: {len(cleanup_failure)}"
        )
    if execution_failure:
        issues.append(
            f"execution failures: {len(execution_failure)}"
        )
    return AlterTableTwoRunComparison(
        passed=not issues,
        issues=tuple(dict.fromkeys(issues)),
        execution_count=len(run_01.cases),
        transcript_mismatch_case_ids=tuple(dict.fromkeys(transcript_mismatch)),
        structured_mismatch_case_ids=tuple(dict.fromkeys(structured_mismatch)),
        sqlstate_mismatch_case_ids=tuple(dict.fromkeys(sqlstate_mismatch)),
        cleanup_failure_case_ids=tuple(dict.fromkeys(cleanup_failure)),
        execution_failure_case_ids=tuple(dict.fromkeys(execution_failure)),
    )


__all__ = [
    "AlterTableCaseRuntimeResult",
    "AlterTableSuiteRun",
    "AlterTableTwoRunComparison",
    "AlterTablePg18Runner",
    "build_alter_table_runtime_case_set",
    "compare_alter_table_runs",
]
