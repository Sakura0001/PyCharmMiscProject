"""Bounded PostgreSQL 18.4 runtime for CREATE TEXT SEARCH TEMPLATE factor programs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import subprocess
from typing import Any, Mapping, Protocol, Sequence

from .create_text_search_template_factor_loop import (
    CreateTextSearchTemplateFactorCase,
)


PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-ctst-sock-20260820")
PG18_PORT = 55615
PG18_DATABASE = "pgcf_ctst"
PG18_SUPERUSER = "pgcf_superuser"
PER_FILE_TIMEOUT_SECONDS = 30
MAX_PARALLELISM = 1

_TARGET_SQLSTATE = re.compile(
    rb"(?m)^PGCF_TARGET_SQLSTATE=([0-9A-Z]{5})\s*$"
)
_PREFIX = re.compile(r"^[a-z][a-z0-9_]*_$")
_CLEANUP_MARKER = "-- 5. 清理全部本编号对象。"


class CreateTextSearchTemplateRuntimeError(RuntimeError):
    """Raised when the frozen PostgreSQL runtime is unavailable or drifts."""


@dataclass(frozen=True)
class CreateTextSearchTemplateCaseRuntimeResult:
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
            self.case_id,
            self.sql_filename,
            self.expected_sqlstate,
            self.target_sqlstate,
            self.exit_code,
            self.timed_out,
            self.boolean_oracle_failure_count,
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
            "normalized_stdout": self.normalized_stdout.decode(
                "utf-8", errors="replace"
            ),
            "normalized_stderr": self.normalized_stderr.decode(
                "utf-8", errors="replace"
            ),
            "boolean_oracle_failure_count": (
                self.boolean_oracle_failure_count
            ),
            "pre_clean": self.pre_clean,
            "post_clean": self.post_clean,
            "cleanup_exit_code": self.cleanup_exit_code,
        }


@dataclass(frozen=True)
class CreateTextSearchTemplateSuiteRun:
    run_ordinal: int
    cases: tuple[CreateTextSearchTemplateCaseRuntimeResult, ...]

    def __post_init__(self) -> None:
        if self.run_ordinal not in {1, 2}:
            raise CreateTextSearchTemplateRuntimeError(
                "run ordinal must be 1 or 2"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "create_text_search_template_pg18_suite_run",
            "run_ordinal": self.run_ordinal,
            "case_count": len(self.cases),
            "cases": [case.to_dict() for case in self.cases],
        }


@dataclass(frozen=True)
class CreateTextSearchTemplateTwoRunComparison:
    passed: bool
    issues: tuple[str, ...]
    execution_count: int
    transcript_mismatch_case_ids: tuple[str, ...]
    structured_mismatch_case_ids: tuple[str, ...]
    sqlstate_mismatch_case_ids: tuple[str, ...]
    cleanup_failure_case_ids: tuple[str, ...]
    execution_failure_case_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": (
                "create_text_search_template_pg18_two_run_comparison"
            ),
            "passed": self.passed,
            "issues": list(self.issues),
            "execution_count": self.execution_count,
            "transcript_mismatch_case_ids": list(
                self.transcript_mismatch_case_ids
            ),
            "structured_mismatch_case_ids": list(
                self.structured_mismatch_case_ids
            ),
            "sqlstate_mismatch_case_ids": list(
                self.sqlstate_mismatch_case_ids
            ),
            "cleanup_failure_case_ids": list(
                self.cleanup_failure_case_ids
            ),
            "execution_failure_case_ids": list(
                self.execution_failure_case_ids
            ),
        }


def compare_create_text_search_template_runs(
    run_01: CreateTextSearchTemplateSuiteRun,
    run_02: CreateTextSearchTemplateSuiteRun,
) -> CreateTextSearchTemplateTwoRunComparison:
    """Require identical transcripts, structure, SQLSTATEs, and clean state."""

    issues: list[str] = []
    transcripts: list[str] = []
    structured: list[str] = []
    sqlstates: list[str] = []
    cleanup: list[str] = []
    execution: list[str] = []
    ids_01 = tuple(case.case_id for case in run_01.cases)
    ids_02 = tuple(case.case_id for case in run_02.cases)
    if ids_01 != ids_02:
        issues.append("run case order or identity differs")
    by_id_02 = {case.case_id: case for case in run_02.cases}
    if len(by_id_02) != len(run_02.cases):
        issues.append("run 2 contains duplicate case IDs")

    for first in run_01.cases:
        second = by_id_02.get(first.case_id)
        pairs = (first,) if second is None else (first, second)
        if second is None:
            structured.append(first.case_id)
            continue
        if (
            first.normalized_stdout != second.normalized_stdout
            or first.normalized_stderr != second.normalized_stderr
        ):
            transcripts.append(first.case_id)
        if first.structured_projection() != second.structured_projection():
            structured.append(first.case_id)
        for result in pairs:
            if result.target_sqlstate != result.expected_sqlstate:
                sqlstates.append(result.case_id)
            if result.cleanup_exit_code != 0 or not result.post_clean:
                cleanup.append(result.case_id)
            if (
                result.exit_code != 0
                or result.timed_out
                or result.boolean_oracle_failure_count != 0
                or not result.pre_clean
            ):
                execution.append(result.case_id)

    transcript_ids = tuple(dict.fromkeys(transcripts))
    structured_ids = tuple(dict.fromkeys(structured))
    sqlstate_ids = tuple(dict.fromkeys(sqlstates))
    cleanup_ids = tuple(dict.fromkeys(cleanup))
    execution_ids = tuple(dict.fromkeys(execution))
    if transcript_ids:
        issues.append(f"{len(transcript_ids)} transcript mismatches")
    if structured_ids:
        issues.append(
            f"{len(structured_ids)} structured result mismatches"
        )
    if sqlstate_ids:
        issues.append(f"{len(sqlstate_ids)} SQLSTATE mismatches")
    if cleanup_ids:
        issues.append(f"{len(cleanup_ids)} cleanup failures")
    if execution_ids:
        issues.append(f"{len(execution_ids)} execution failures")
    return CreateTextSearchTemplateTwoRunComparison(
        passed=not issues,
        issues=tuple(issues),
        execution_count=len(run_01.cases) + len(run_02.cases),
        transcript_mismatch_case_ids=transcript_ids,
        structured_mismatch_case_ids=structured_ids,
        sqlstate_mismatch_case_ids=sqlstate_ids,
        cleanup_failure_case_ids=cleanup_ids,
        execution_failure_case_ids=execution_ids,
    )


class CreateTextSearchTemplateRuntimeCase(Protocol):
    """Structural contract for a case the runner can execute."""

    case_id: str
    sql_filename: str
    object_prefix: str
    expected_sqlstate: str
    ordinal: int


def build_create_text_search_template_runtime_case_set(
    repository_root: Path,
    sql_dir: Path,
) -> tuple[
    tuple[CreateTextSearchTemplateRuntimeCase, ...],
    dict[str, Path],
]:
    """Combine baseline + extension cases and map each to its SQL file."""

    from .create_text_search_template_factor_extension import (
        build_create_text_search_template_factor_extension_plan,
    )
    from .create_text_search_template_factor_loop import (
        build_create_text_search_template_factor_loop_plan,
    )

    root = Path(repository_root).resolve(strict=True)
    sql_dir = Path(sql_dir)
    baseline = (
        build_create_text_search_template_factor_loop_plan(root).cases
    )
    extensions = (
        build_create_text_search_template_factor_extension_plan(root).cases
    )
    cases: list[CreateTextSearchTemplateRuntimeCase] = [
        *baseline,
        *extensions,
    ]
    cases.sort(key=lambda case: _case_ordinal(case))
    sql_paths = {
        case.case_id: sql_dir / case.sql_filename for case in cases
    }
    return tuple(cases), sql_paths


def _case_ordinal(
    case: CreateTextSearchTemplateRuntimeCase,
) -> int:
    return getattr(case, "ordinal")  # type: ignore[no-any-return]


class CreateTextSearchTemplatePg18Runner:
    """Serial, bounded psql executor for an isolated PostgreSQL 18.4 server."""

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
        self.bin_dir = Path(bin_dir)
        self.socket_dir = Path(socket_dir)
        self.port = port
        self.database = database
        self.role = role
        self.timeout_seconds = timeout_seconds
        if timeout_seconds <= 0 or timeout_seconds > 300:
            raise CreateTextSearchTemplateRuntimeError(
                "per-file timeout must be between 1 and 300 seconds"
            )

    @property
    def psql(self) -> Path:
        return self.bin_dir / "psql"

    def _base_command(self) -> list[str]:
        return [
            str(self.psql),
            "-X",
            "-h",
            str(self.socket_dir),
            "-p",
            str(self.port),
            "-d",
            self.database,
            "-U",
            self.role,
            "-A",
            "-t",
            "-q",
            "-v",
            "VERBOSITY=sqlstate",
            "-v",
            "ON_ERROR_STOP=1",
        ]

    def _cleanup_command(self) -> list[str]:
        command = self._base_command()
        for index, argument in enumerate(command):
            if argument == "ON_ERROR_STOP=1":
                command[index] = "ON_ERROR_STOP=0"
                break
        return command

    @staticmethod
    def _environment() -> dict[str, str]:
        environment = dict(os.environ)
        existing = environment.get("PGOPTIONS", "").strip()
        setting = "-c client_min_messages=warning"
        environment["PGOPTIONS"] = f"{existing} {setting}".strip()
        return environment

    def verify_server(self) -> int:
        if not self.psql.is_file():
            raise CreateTextSearchTemplateRuntimeError(
                f"PostgreSQL 18.4 psql is missing: {self.psql}"
            )
        result = subprocess.run(
            [*self._base_command(), "-c", "SHOW server_version_num"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=min(self.timeout_seconds, 10),
            check=False,
            env=self._environment(),
        )
        if result.returncode != 0:
            raise CreateTextSearchTemplateRuntimeError(
                "cannot inspect PostgreSQL server version: "
                + result.stderr.decode("utf-8", errors="replace").strip()
            )
        try:
            version = int(result.stdout.strip())
        except ValueError as exc:
            raise CreateTextSearchTemplateRuntimeError(
                "server_version_num is not an integer"
            ) from exc
        if not 180004 <= version < 180005:
            raise CreateTextSearchTemplateRuntimeError(
                f"expected PostgreSQL 18.4, "
                f"observed server_version_num={version}"
            )
        return version

    def _clean_probe(self, object_prefix: str) -> bool:
        if _PREFIX.fullmatch(object_prefix) is None:
            raise CreateTextSearchTemplateRuntimeError(
                "unsafe object prefix"
            )
        literal = object_prefix.replace("'", "''") + "%"
        query = (
            "SELECT NOT EXISTS ("
            "SELECT 1 FROM pg_catalog.pg_class WHERE relname LIKE '"
            + literal
            + "' "
            "UNION ALL SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname LIKE '"
            + literal
            + "' "
            "UNION ALL SELECT 1 FROM pg_catalog.pg_type WHERE typname LIKE '"
            + literal
            + "' "
            "UNION ALL SELECT 1 FROM pg_catalog.pg_proc WHERE proname LIKE '"
            + literal
            + "' "
            "UNION ALL SELECT 1 FROM pg_catalog.pg_roles WHERE rolname LIKE '"
            + literal
            + "' "
            "UNION ALL SELECT 1 FROM pg_catalog.pg_ts_template WHERE tmplname LIKE '"
            + literal
            + "');"
        )
        try:
            result = subprocess.run(
                [*self._base_command(), "-c", query],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=min(self.timeout_seconds, 10),
                check=False,
                env=self._environment(),
            )
        except subprocess.TimeoutExpired:
            return False
        return result.returncode == 0 and result.stdout.strip() == b"t"

    @staticmethod
    def _cleanup_sql(sql: str) -> str:
        if sql.count(_CLEANUP_MARKER) != 1:
            raise CreateTextSearchTemplateRuntimeError(
                "cleanup phase marker is not unique"
            )
        return sql.split(_CLEANUP_MARKER, 1)[1].lstrip()

    @staticmethod
    def _normalize(payload: bytes, sql_path: Path) -> bytes:
        normalized = payload.replace(
            str(sql_path).encode("utf-8"), b"<SQL_PATH>"
        )
        normalized = normalized.replace(
            str(sql_path.resolve()).encode("utf-8"),
            b"<SQL_PATH>",
        )
        normalized = re.sub(
            rb"(?m)^psql \([^\n]+\)\n",
            b"",
            normalized,
        )
        return normalized

    def _execute_case(
        self,
        case: CreateTextSearchTemplateRuntimeCase,
        sql_path: Path,
    ) -> CreateTextSearchTemplateCaseRuntimeResult:
        sql = sql_path.read_text(encoding="utf-8")
        pre_clean = self._clean_probe(case.object_prefix)
        timed_out = False
        if pre_clean:
            try:
                execution = subprocess.run(
                    [*self._base_command(), "-f", str(sql_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout_seconds,
                    check=False,
                    env=self._environment(),
                )
                exit_code = execution.returncode
                stdout = execution.stdout
                stderr = execution.stderr
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                exit_code = 124
                stdout = exc.stdout or b""
                stderr = exc.stderr or b""
        else:
            exit_code = 125
            stdout = b""
            stderr = b"pre-run clean-state probe failed\n"

        cleanup_sql = self._cleanup_sql(sql)
        try:
            cleanup = subprocess.run(
                [*self._cleanup_command(), "-f", "-"],
                input=cleanup_sql.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
                check=False,
                env=self._environment(),
            )
            cleanup_exit_code = cleanup.returncode
        except subprocess.TimeoutExpired:
            cleanup_exit_code = 124
        post_clean = self._clean_probe(case.object_prefix)
        sqlstate_matches = _TARGET_SQLSTATE.findall(stdout)
        target_sqlstate = (
            sqlstate_matches[0].decode("ascii")
            if len(sqlstate_matches) == 1
            else None
        )
        false_lines = sum(
            line.strip() == b"f" for line in stdout.splitlines()
        )
        return CreateTextSearchTemplateCaseRuntimeResult(
            case_id=case.case_id,
            sql_filename=case.sql_filename,
            expected_sqlstate=case.expected_sqlstate,
            target_sqlstate=target_sqlstate,
            exit_code=exit_code,
            timed_out=timed_out,
            normalized_stdout=self._normalize(stdout, sql_path),
            normalized_stderr=self._normalize(stderr, sql_path),
            boolean_oracle_failure_count=false_lines,
            pre_clean=pre_clean,
            post_clean=post_clean,
            cleanup_exit_code=cleanup_exit_code,
        )

    def run_cases(
        self,
        cases: Sequence[CreateTextSearchTemplateRuntimeCase],
        sql_paths: Mapping[str, Path],
        *,
        run_ordinal: int,
        selected_case_ids: Sequence[str] | None = None,
    ) -> CreateTextSearchTemplateSuiteRun:
        self.verify_server()
        selected = (
            set(selected_case_ids)
            if selected_case_ids is not None
            else None
        )
        results: list[CreateTextSearchTemplateCaseRuntimeResult] = []
        for case in cases:
            if selected is not None and case.case_id not in selected:
                continue
            try:
                path = Path(sql_paths[case.case_id])
            except KeyError as exc:
                raise CreateTextSearchTemplateRuntimeError(
                    f"missing SQL path for {case.case_id}"
                ) from exc
            if path.name != case.sql_filename or not path.is_file():
                raise CreateTextSearchTemplateRuntimeError(
                    f"invalid SQL path for {case.case_id}: {path}"
                )
            results.append(self._execute_case(case, path))
        return CreateTextSearchTemplateSuiteRun(
            run_ordinal=run_ordinal,
            cases=tuple(results),
        )


__all__ = [
    "CreateTextSearchTemplateCaseRuntimeResult",
    "CreateTextSearchTemplatePg18Runner",
    "CreateTextSearchTemplateRuntimeCase",
    "CreateTextSearchTemplateRuntimeError",
    "CreateTextSearchTemplateSuiteRun",
    "CreateTextSearchTemplateTwoRunComparison",
    "MAX_PARALLELISM",
    "PER_FILE_TIMEOUT_SECONDS",
    "PG18_BIN",
    "PG18_DATABASE",
    "PG18_PORT",
    "PG18_SOCKET",
    "PG18_SUPERUSER",
    "build_create_text_search_template_runtime_case_set",
    "compare_create_text_search_template_runs",
]
