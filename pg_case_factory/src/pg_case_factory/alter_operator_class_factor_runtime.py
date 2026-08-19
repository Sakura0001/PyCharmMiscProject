"""Serial PG 18.4 runtime executor and two-run comparison for ALTER OPERATOR CLASS.

Runs each generated ``.sql`` program twice against a per-statement PG 18.4
cluster and compares the structured projections for idempotency.  When the
cluster is not reachable (the no-DB phase ships without a live server) the
runtime test suite skips rather than errors, mirroring the sibling statement
runtimes.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import tempfile
import time
from typing import Protocol


class AlterOperatorClassRuntimeError(RuntimeError):
    """Raised when the ALTER OPERATOR CLASS runtime detects a hard failure."""


PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-aoc-sock-20260820")
PG18_PORT = 55493
PG18_DATABASE = "pgcf_aoc"
PG18_SUPERUSER = "pgcf_superuser"
PER_FILE_TIMEOUT_SECONDS = 30
MAX_PARALLELISM = 1

_TARGET_SQLSTATE = re.compile(
    rb"(?m)^PGCF_TARGET_SQLSTATE=([0-9A-Z]{5})\s*$"
)
_FALSE_ORACLE_RE = re.compile(
    rb"(?m)^\s*(?:f|false)\s*$"
)


@dataclass(frozen=True)
class AlterOperatorClassCaseRuntimeResult:
    case_id: str
    sql_filename: str
    expected_sqlstate: str
    target_sqlstate: str | None
    exit_code: int
    timed_out: bool
    normalized_stdout: str
    stderr: str
    boolean_oracle_failure_count: int
    pre_clean: bool
    post_clean: bool
    cleanup_exit_code: int

    def structured_projection(self) -> tuple:
        return (
            self.case_id,
            self.exit_code,
            self.timed_out,
            self.target_sqlstate,
            self.boolean_oracle_failure_count,
            self.pre_clean,
            self.post_clean,
            self.cleanup_exit_code,
        )

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "sql_filename": self.sql_filename,
            "expected_sqlstate": self.expected_sqlstate,
            "target_sqlstate": self.target_sqlstate,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "stderr": self.stderr,
            "boolean_oracle_failure_count": self.boolean_oracle_failure_count,
            "pre_clean": self.pre_clean,
            "post_clean": self.post_clean,
            "cleanup_exit_code": self.cleanup_exit_code,
        }


@dataclass(frozen=True)
class AlterOperatorClassSuiteRun:
    run_ordinal: int
    results: tuple[AlterOperatorClassCaseRuntimeResult, ...]


@dataclass(frozen=True)
class AlterOperatorClassTwoRunComparison:
    passed: bool
    issues: tuple[str, ...]
    execution_count: int
    order_mismatch_count: int
    transcript_mismatch_count: int
    projection_mismatch_count: int
    sqlstate_mismatch_count: int
    cleanup_mismatch_count: int


class AlterOperatorClassRuntimeCase(Protocol):
    case_id: str
    sql_filename: str
    object_prefix: str
    expected_sqlstate: str
    ordinal: int


def build_alter_operator_class_runtime_case_set(
    repository_root: Path,
    sql_dir: Path,
):
    """Build the ordered runtime case set from committed SQL files."""

    from .alter_operator_class_factor_loop import (
        build_alter_operator_class_factor_loop_plan,
    )
    from .alter_operator_class_factor_extension import (
        build_alter_operator_class_factor_extension_plan,
    )

    del repository_root
    baseline_plan = build_alter_operator_class_factor_loop_plan(Path("."))
    extension_plan = build_alter_operator_class_factor_extension_plan(Path("."))
    sql_dir = Path(sql_dir)
    sql_paths = {}
    cases = []
    for case in baseline_plan.cases:
        path = sql_dir / case.sql_filename
        if path.exists():
            sql_paths[case.sql_filename] = path
            cases.append(case)
    for case in extension_plan.cases:
        path = sql_dir / case.sql_filename
        if path.exists():
            sql_paths[case.sql_filename] = path
            cases.append(case)
    cases.sort(key=lambda c: c.ordinal)
    return tuple(cases), sql_paths


class AlterOperatorClassPg18Runner:
    def __init__(
        self,
        *,
        timeout_seconds: int = PER_FILE_TIMEOUT_SECONDS,
    ):
        if not 1 <= timeout_seconds <= 300:
            raise AlterOperatorClassRuntimeError("timeout out of range")
        self._timeout = timeout_seconds

    @property
    def psql(self) -> Path:
        return PG18_BIN / "psql"

    def _base_command(self) -> list[str]:
        return [
            str(self.psql),
            "-X",
            "-h",
            str(PG18_SOCKET),
            "-p",
            str(PG18_PORT),
            "-d",
            PG18_DATABASE,
            "-U",
            PG18_SUPERUSER,
            "-A",
            "-t",
            "-q",
            "-v",
            "VERBOSITY=sqlstate",
            "-v",
            "ON_ERROR_STOP=1",
        ]

    def _cleanup_command(self) -> list[str]:
        cmd = self._base_command()
        cmd[-1] = "ON_ERROR_STOP=0"
        return cmd

    def _environment(self) -> dict[str, str]:
        import os

        env = dict(os.environ)
        env["PGOPTIONS"] = "-c client_min_messages=warning"
        return env

    def verify_server(self) -> bool:
        try:
            proc = subprocess.run(
                self._base_command() + ["-c", "SHOW server_version_num;"],
                capture_output=True,
                timeout=15,
                env=self._environment(),
            )
        except (OSError, subprocess.SubprocessError):
            return False
        if proc.returncode != 0:
            return False
        text = proc.stdout.decode("utf-8", errors="replace").strip()
        if text not in ("180004", "180005"):
            return False
        return True

    def _clean_probe(self, object_prefix: str) -> bool:
        probe = (
            "SELECT NOT EXISTS ("
            "SELECT 1 FROM pg_catalog.pg_opclass WHERE "
            f"opcname LIKE '{object_prefix}%'"
            ") AND NOT EXISTS ("
            "SELECT 1 FROM pg_catalog.pg_namespace WHERE "
            f"nspname LIKE '{object_prefix}%'"
            ") AND NOT EXISTS ("
            "SELECT 1 FROM pg_catalog.pg_roles WHERE "
            f"rolname LIKE '{object_prefix}%'"
            ") AND NOT EXISTS ("
            "SELECT 1 FROM pg_catalog.pg_type WHERE "
            f"typname LIKE '{object_prefix}%'"
            ");"
        )
        proc = subprocess.run(
            self._base_command() + ["-c", probe],
            capture_output=True,
            timeout=15,
            env=self._environment(),
        )
        return proc.returncode == 0 and b"t" in proc.stdout

    def _cleanup_sql(self, sql: str) -> str:
        marker = "-- 5. 清理全部本编号对象。"
        if marker not in sql:
            return ""
        return sql.split(marker, 1)[1]

    def _normalize(self, payload: str, sql_path: Path) -> str:
        return payload.replace(str(sql_path), "SQL_PATH").lstrip()

    def _execute_case(
        self,
        case,
        sql_path: Path,
    ) -> AlterOperatorClassCaseRuntimeResult:
        pre_clean = self._clean_probe(case.object_prefix)
        run_proc = subprocess.run(
            self._base_command() + ["-f", str(sql_path)],
            capture_output=True,
            timeout=self._timeout,
            env=self._environment(),
        )
        cleanup_sql = self._cleanup_sql(sql_path.read_text(encoding="utf-8"))
        cleanup_exit = 0
        post_clean = False
        if cleanup_sql:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".sql", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(cleanup_sql)
                tmp_path = Path(tmp.name)
            try:
                subprocess.run(
                    self._cleanup_command() + ["-f", str(tmp_path)],
                    capture_output=True,
                    timeout=self._timeout,
                    env=self._environment(),
                )
            finally:
                tmp_path.unlink(missing_ok=True)
            post_clean = self._clean_probe(case.object_prefix)
        stdout = run_proc.stdout.decode("utf-8", errors="replace")
        stderr = run_proc.stderr.decode("utf-8", errors="replace")
        match = _TARGET_SQLSTATE.search(run_proc.stdout)
        target_sqlstate = match.group(1).decode("ascii") if match else None
        oracle_failures = len(_FALSE_ORACLE_RE.findall(run_proc.stdout))
        return AlterOperatorClassCaseRuntimeResult(
            case_id=case.case_id,
            sql_filename=case.sql_filename,
            expected_sqlstate=case.expected_sqlstate,
            target_sqlstate=target_sqlstate,
            exit_code=run_proc.returncode,
            timed_out=False,
            normalized_stdout=self._normalize(stdout, sql_path),
            stderr=stderr,
            boolean_oracle_failure_count=oracle_failures,
            pre_clean=pre_clean,
            post_clean=post_clean,
            cleanup_exit_code=cleanup_exit,
        )

    def run_cases(
        self,
        cases,
        sql_paths,
        run_ordinal: int,
        selected_case_ids: set[str] | None = None,
    ) -> AlterOperatorClassSuiteRun:
        results = []
        for case in cases:
            if selected_case_ids and case.case_id not in selected_case_ids:
                continue
            result = self._execute_case(case, sql_paths[case.sql_filename])
            results.append(result)
        return AlterOperatorClassSuiteRun(run_ordinal=run_ordinal, results=tuple(results))


def compare_alter_operator_class_runs(
    run_01: AlterOperatorClassSuiteRun,
    run_02: AlterOperatorClassSuiteRun,
) -> AlterOperatorClassTwoRunComparison:
    issues: list[str] = []
    order_01 = [r.case_id for r in run_01.results]
    order_02 = [r.case_id for r in run_02.results]
    if order_01 != order_02:
        issues.append(f"case order mismatch: {len(order_01)} vs {len(order_02)}")
    by_01 = {r.case_id: r for r in run_01.results}
    by_02 = {r.case_id: r for r in run_02.results}
    transcript = 0
    projection = 0
    sqlstate = 0
    cleanup = 0
    for cid in order_01:
        r1 = by_01.get(cid)
        r2 = by_02.get(cid)
        if r1 is None or r2 is None:
            continue
        if r1.normalized_stdout != r2.normalized_stdout or r1.stderr != r2.stderr:
            transcript += 1
        if r1.structured_projection() != r2.structured_projection():
            projection += 1
        if r1.target_sqlstate != r2.target_sqlstate:
            sqlstate += 1
        if r1.post_clean != r2.post_clean or r1.cleanup_exit_code != r2.cleanup_exit_code:
            cleanup += 1
    if transcript:
        issues.append(f"{transcript} transcript mismatches")
    if projection:
        issues.append(f"{projection} projection mismatches")
    if sqlstate:
        issues.append(f"{sqlstate} sqlstate mismatches")
    if cleanup:
        issues.append(f"{cleanup} cleanup mismatches")
    return AlterOperatorClassTwoRunComparison(
        passed=not issues,
        issues=tuple(dict.fromkeys(issues)),
        execution_count=len(run_01.results) + len(run_02.results),
        order_mismatch_count=0 if order_01 == order_02 else 1,
        transcript_mismatch_count=transcript,
        projection_mismatch_count=projection,
        sqlstate_mismatch_count=sqlstate,
        cleanup_mismatch_count=cleanup,
    )


def run_alter_operator_class_two_run_comparison(
    cases,
    sql_paths,
    *,
    timeout_seconds: int = PER_FILE_TIMEOUT_SECONDS,
) -> AlterOperatorClassTwoRunComparison:
    runner = AlterOperatorClassPg18Runner(timeout_seconds=timeout_seconds)
    if not runner.verify_server():
        raise AlterOperatorClassRuntimeError("PG 18.4 cluster not reachable")
    run_01 = runner.run_cases(cases, sql_paths, run_ordinal=1)
    time.sleep(0)
    run_02 = runner.run_cases(cases, sql_paths, run_ordinal=2)
    return compare_alter_operator_class_runs(run_01, run_02)


__all__ = [
    "AlterOperatorClassRuntimeError",
    "AlterOperatorClassCaseRuntimeResult",
    "AlterOperatorClassSuiteRun",
    "AlterOperatorClassTwoRunComparison",
    "AlterOperatorClassRuntimeCase",
    "build_alter_operator_class_runtime_case_set",
    "AlterOperatorClassPg18Runner",
    "compare_alter_operator_class_runs",
    "run_alter_operator_class_two_run_comparison",
]
