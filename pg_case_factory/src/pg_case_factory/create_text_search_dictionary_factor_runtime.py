"""Bounded PostgreSQL 18.4 runtime for CREATE TEXT SEARCH DICTIONARY factor programs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import subprocess
from typing import Any, Mapping, Protocol, Sequence

from .create_text_search_dictionary_factor_loop import (
    CreateTextSearchDictionaryFactorCase,
)

PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-ctsd-sock-20260820")
PG18_PORT = 55500
PG18_DATABASE = "pgcf_ctsd"
PG18_SUPERUSER = "pgcf_superuser"
PER_FILE_TIMEOUT_SECONDS = 30
MAX_PARALLELISM = 1

_TARGET_SQLSTATE = re.compile(
    rb"(?m)^PGCF_TARGET_SQLSTATE=([0-9A-Z]{5})\s*$"
)
_PREFIX = re.compile(r"^[a-z][a-z0-9_]*_$")
_CLEANUP_MARKER = "-- 5. 清理全部本编号对象。"


class CreateTextSearchDictionaryRuntimeError(RuntimeError):
    """Raised when the frozen PostgreSQL runtime is unavailable or drifts."""


@dataclass(frozen=True)
class CreateTextSearchDictionaryCaseRuntimeResult:
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
            "boolean_oracle_failure_count": (
                self.boolean_oracle_failure_count
            ),
            "pre_clean": self.pre_clean,
            "post_clean": self.post_clean,
            "cleanup_exit_code": self.cleanup_exit_code,
        }


@dataclass(frozen=True)
class CreateTextSearchDictionarySuiteRun:
    run_ordinal: int
    cases: tuple[
        CreateTextSearchDictionaryCaseRuntimeResult, ...
    ]

    def __post_init__(self) -> None:
        if self.run_ordinal not in (1, 2):
            raise CreateTextSearchDictionaryRuntimeError(
                "run_ordinal must be 1 or 2"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": (
                "create_text_search_dictionary_pg18_suite_run"
            ),
            "run_ordinal": self.run_ordinal,
            "cases": [c.to_dict() for c in self.cases],
        }


@dataclass(frozen=True)
class CreateTextSearchDictionaryTwoRunComparison:
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
                "create_text_search_dictionary_pg18_two_run_"
                "comparison"
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


class CreateTextSearchDictionaryRuntimeCase(Protocol):
    """Structural contract for a case the runner can execute."""

    case_id: str
    sql_filename: str
    object_prefix: str
    expected_sqlstate: str
    ordinal: int


class CreateTextSearchDictionaryPg18Runner:
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
        if not (1 <= timeout_seconds <= 300):
            raise CreateTextSearchDictionaryRuntimeError(
                "timeout_seconds must be between 1 and 300"
            )
        self._bin_dir = bin_dir
        self._socket_dir = socket_dir
        self._port = port
        self._database = database
        self._role = role
        self._timeout = timeout_seconds

    @property
    def port(self) -> int:
        return self._port

    @property
    def database(self) -> str:
        return self._database

    @property
    def psql(self) -> Path:
        return self._bin_dir / "psql"

    def _base_command(self) -> list[str]:
        return [
            str(self.psql),
            "-X",
            "-h",
            str(self._socket_dir),
            "-p",
            str(self._port),
            "-d",
            self._database,
            "-U",
            self._role,
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
        cmd[cmd.index("ON_ERROR_STOP=1")] = "ON_ERROR_STOP=0"
        return cmd

    @staticmethod
    def _environment() -> dict[str, str]:
        env = dict(os.environ)
        env["PGOPTIONS"] = "-c client_min_messages=warning"
        return env

    def verify_server(self) -> int:
        cmd = self._base_command() + ["-c", "SHOW server_version_num;"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=self._timeout,
            env=self._environment(),
        )
        if result.returncode != 0:
            raise CreateTextSearchDictionaryRuntimeError(
                "cannot verify server: "
                + result.stderr.decode("utf-8", "replace")
            )
        version = int(result.stdout.strip())
        if not (180004 <= version < 180005):
            raise CreateTextSearchDictionaryRuntimeError(
                f"server version drift: {version}"
            )
        return version

    def _clean_probe(self, object_prefix: str) -> bool:
        probe = (
            "SELECT "
            "NOT EXISTS (SELECT 1 FROM pg_catalog.pg_class "
            f"WHERE relname LIKE '{object_prefix}%') "
            "AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace "
            f"WHERE nspname LIKE '{object_prefix}%') "
            "AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_type "
            f"WHERE typname LIKE '{object_prefix}%') "
            "AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc "
            f"WHERE proname LIKE '{object_prefix}%') "
            "AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles "
            f"WHERE rolname LIKE '{object_prefix}%') "
            "AND NOT EXISTS (SELECT 1 FROM "
            f"pg_catalog.pg_ts_dict "
            f"WHERE dictname LIKE '{object_prefix}%') "
            "AND NOT EXISTS (SELECT 1 FROM "
            f"pg_catalog.pg_ts_template "
            f"WHERE tmplname LIKE '{object_prefix}%') "
            "AS clean;"
        )
        cmd = self._base_command() + ["-c", probe]
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=self._timeout,
            env=self._environment(),
        )
        if result.returncode != 0:
            return False
        return result.stdout.strip() == b"t"

    @staticmethod
    def _cleanup_sql(sql: str) -> str:
        parts = sql.split(_CLEANUP_MARKER, 1)
        if len(parts) == 2:
            return parts[1]
        return ""

    @staticmethod
    def _normalize(payload: bytes, sql_path: Path) -> bytes:
        placeholder = b"<SQL_PATH>"
        normalized = payload.replace(
            str(sql_path).encode("utf-8"), placeholder
        )
        lines = [
            line
            for line in normalized.split(b"\n")
            if not line.strip().startswith(b"psql (")
        ]
        return b"\n".join(lines)

    def _execute_case(
        self,
        case: CreateTextSearchDictionaryRuntimeCase,
        sql_path: Path,
    ) -> CreateTextSearchDictionaryCaseRuntimeResult:
        sql = sql_path.read_bytes()
        pre_clean = self._clean_probe(case.object_prefix)

        if pre_clean:
            cmd = self._base_command() + ["-f", str(sql_path)]
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=self._timeout,
                    env=self._environment(),
                )
                exit_code = result.returncode
                stdout = result.stdout
                stderr = result.stderr
                timed_out = False
            except subprocess.TimeoutExpired:
                exit_code = 124
                stdout = b""
                stderr = b"timeout\n"
                timed_out = True
        else:
            exit_code = 125
            stdout = b""
            stderr = b"pre-run clean-state probe failed\n"
            timed_out = False

        cleanup_sql = self._cleanup_sql(
            sql.decode("utf-8", "replace")
        )
        if cleanup_sql:
            cmd = self._cleanup_command() + ["-f", "-"]
            try:
                cleanup_result = subprocess.run(
                    cmd,
                    input=cleanup_sql.encode("utf-8"),
                    capture_output=True,
                    timeout=self._timeout,
                    env=self._environment(),
                )
                cleanup_exit_code = cleanup_result.returncode
            except subprocess.TimeoutExpired:
                cleanup_exit_code = 124
        else:
            cleanup_exit_code = 0

        post_clean = self._clean_probe(case.object_prefix)

        match = _TARGET_SQLSTATE.search(stdout)
        target_sqlstate = (
            match.group(1).decode("ascii")
            if match is not None
            else None
        )
        boolean_oracle_failure_count = sum(
            1
            for line in stdout.split(b"\n")
            if line.strip() == b"f"
        )
        normalized_stdout = self._normalize(stdout, sql_path)
        normalized_stderr = self._normalize(stderr, sql_path)

        return CreateTextSearchDictionaryCaseRuntimeResult(
            case_id=case.case_id,
            sql_filename=case.sql_filename,
            expected_sqlstate=case.expected_sqlstate,
            target_sqlstate=target_sqlstate,
            exit_code=exit_code,
            timed_out=timed_out,
            normalized_stdout=normalized_stdout,
            normalized_stderr=normalized_stderr,
            boolean_oracle_failure_count=(
                boolean_oracle_failure_count
            ),
            pre_clean=pre_clean,
            post_clean=post_clean,
            cleanup_exit_code=cleanup_exit_code,
        )

    def run_cases(
        self,
        cases: Sequence[CreateTextSearchDictionaryRuntimeCase],
        sql_paths: Mapping[str, Path],
        *,
        run_ordinal: int,
        selected_case_ids: Sequence[str] | None = None,
    ) -> CreateTextSearchDictionarySuiteRun:
        self.verify_server()
        results: list[
            CreateTextSearchDictionaryCaseRuntimeResult
        ] = []
        for case in cases:
            if (
                selected_case_ids is not None
                and case.case_id not in selected_case_ids
            ):
                continue
            path = sql_paths[case.case_id]
            if path.name != case.sql_filename:
                raise CreateTextSearchDictionaryRuntimeError(
                    f"sql_filename mismatch: {path.name} vs "
                    f"{case.sql_filename}"
                )
            if not path.exists():
                raise CreateTextSearchDictionaryRuntimeError(
                    f"sql file not found: {path}"
                )
            results.append(self._execute_case(case, path))
        return CreateTextSearchDictionarySuiteRun(
            run_ordinal=run_ordinal,
            cases=tuple(results),
        )


def _case_ordinal(
    case: CreateTextSearchDictionaryRuntimeCase,
) -> int:
    return case.ordinal


def compare_create_text_search_dictionary_runs(
    run_01: CreateTextSearchDictionarySuiteRun,
    run_02: CreateTextSearchDictionarySuiteRun,
) -> CreateTextSearchDictionaryTwoRunComparison:
    issues: list[str] = []

    ids_01 = [r.case_id for r in run_01.cases]
    ids_02 = [r.case_id for r in run_02.cases]
    if ids_01 != ids_02:
        issues.append("case id order mismatch between runs")

    seen_02: set[str] = set()
    dup_02: list[str] = []
    for cid in ids_02:
        if cid in seen_02:
            dup_02.append(cid)
        seen_02.add(cid)
    if dup_02:
        issues.append(f"duplicate case ids in run 2: {dup_02}")

    r02_by_id = {r.case_id: r for r in run_02.cases}
    transcript_mismatch: list[str] = []
    structured_mismatch: list[str] = []
    sqlstate_mismatch: list[str] = []
    cleanup_failure: list[str] = []
    execution_failure: list[str] = []

    for r01 in run_01.cases:
        r02 = r02_by_id.get(r01.case_id)
        if r02 is None:
            transcript_mismatch.append(r01.case_id)
            continue
        if (
            r01.normalized_stdout != r02.normalized_stdout
            or r01.normalized_stderr != r02.normalized_stderr
        ):
            transcript_mismatch.append(r01.case_id)
        if r01.structured_projection() != r02.structured_projection():
            structured_mismatch.append(r01.case_id)
        if (
            r01.expected_sqlstate != r02.expected_sqlstate
            or r01.target_sqlstate != r02.target_sqlstate
        ):
            sqlstate_mismatch.append(r01.case_id)
        if r02.cleanup_exit_code != 0 or not r02.post_clean:
            cleanup_failure.append(r01.case_id)
        if (
            r02.exit_code != r01.exit_code
            or r02.timed_out
            or r02.boolean_oracle_failure_count > 0
            or not r02.pre_clean
        ):
            execution_failure.append(r01.case_id)

    all_mismatch = list(
        dict.fromkeys(
            transcript_mismatch
            + structured_mismatch
            + sqlstate_mismatch
            + cleanup_failure
            + execution_failure
        )
    )
    if issues or all_mismatch:
        issues.extend(all_mismatch)

    return CreateTextSearchDictionaryTwoRunComparison(
        passed=not issues,
        issues=tuple(dict.fromkeys(issues)),
        execution_count=len(run_02.cases),
        transcript_mismatch_case_ids=tuple(
            dict.fromkeys(transcript_mismatch)
        ),
        structured_mismatch_case_ids=tuple(
            dict.fromkeys(structured_mismatch)
        ),
        sqlstate_mismatch_case_ids=tuple(
            dict.fromkeys(sqlstate_mismatch)
        ),
        cleanup_failure_case_ids=tuple(
            dict.fromkeys(cleanup_failure)
        ),
        execution_failure_case_ids=tuple(
            dict.fromkeys(execution_failure)
        ),
    )


def build_create_text_search_dictionary_runtime_case_set(
    repository_root: Path,
    sql_dir: Path,
) -> tuple[
    tuple[CreateTextSearchDictionaryRuntimeCase, ...],
    dict[str, Path],
]:
    from .create_text_search_dictionary_factor_extension import (
        build_create_text_search_dictionary_factor_extension_plan,
    )
    from .create_text_search_dictionary_factor_loop import (
        build_create_text_search_dictionary_factor_loop_plan,
    )
    from .create_text_search_dictionary_factor_render import (
        generate_create_text_search_dictionary_factor_programs,
    )

    root = Path(repository_root).resolve(strict=True)
    baseline_plan = (
        build_create_text_search_dictionary_factor_loop_plan(root)
    )
    extension_plan = (
        build_create_text_search_dictionary_factor_extension_plan(root)
    )
    generate_create_text_search_dictionary_factor_programs(
        baseline_plan, extension_plan, sql_dir
    )
    cases: list[CreateTextSearchDictionaryRuntimeCase] = []
    cases.extend(baseline_plan.cases)
    cases.extend(extension_plan.cases)
    cases.sort(key=_case_ordinal)
    sql_paths = {
        case.case_id: sql_dir / case.sql_filename for case in cases
    }
    return tuple(cases), sql_paths


__all__ = [
    "CreateTextSearchDictionaryCaseRuntimeResult",
    "CreateTextSearchDictionaryPg18Runner",
    "CreateTextSearchDictionaryRuntimeCase",
    "CreateTextSearchDictionaryRuntimeError",
    "CreateTextSearchDictionarySuiteRun",
    "CreateTextSearchDictionaryTwoRunComparison",
    "MAX_PARALLELISM",
    "PER_FILE_TIMEOUT_SECONDS",
    "PG18_BIN",
    "PG18_DATABASE",
    "PG18_PORT",
    "PG18_SOCKET",
    "PG18_SUPERUSER",
    "build_create_text_search_dictionary_runtime_case_set",
    "compare_create_text_search_dictionary_runs",
]
