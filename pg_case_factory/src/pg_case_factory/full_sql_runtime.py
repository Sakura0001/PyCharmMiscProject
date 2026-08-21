"""Resumable PostgreSQL 18.4 validation for the formal SQL corpus."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Mapping


EVIDENCE_STRICT = "strict-contract"
EVIDENCE_COMPATIBILITY = "compatibility-contract"
EVIDENCE_OBSERVATIONAL = "observational-legacy"

_HEADER = re.compile(r"(?m)^-- (?P<key>[a-z_]+):\s*(?P<value>\S+)\s*$")
_FACTOR_EXPECTED = re.compile(
    r"(?m)^-- factor expected_status=(?P<value>success|failure)\s*$"
)
_RETAINED_STATEMENT = re.compile(
    r"Verify PostgreSQL 18\.4 (?P<statement>CLOSE|DECLARE|FETCH|MOVE|GRANT|REVOKE)\b"
)
_TARGET_SQLSTATE = re.compile(
    rb"(?m)^PGCF_TARGET_SQLSTATE=([0-9A-Z]{5})\s*$"
)
_COMPATIBILITY_TARGET_SQLSTATE = re.compile(
    rb"(?mi)^target_sqlstate(?:=|\s+|:\s*)([0-9A-Z]{5})\s*$"
)
_PSQL_ERROR = re.compile(rb"(?m)^ERROR:\s+(?:[A-Z]+:\s+)?([0-9A-Z]{5})\b")


class FullSqlRuntimeError(RuntimeError):
    """Raised when the frozen runtime corpus or execution contract drifts."""


@dataclass(frozen=True)
class RuntimeManifestCase:
    ordinal: int
    statement_key: str
    case_id: str
    sql_path: str
    sql_sha256: str
    package_path: str
    evidence_level: str
    expected_outcome: str | None
    expected_sqlstate: str | None
    object_prefix: str | None
    external: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaseExecution:
    exit_code: int
    timed_out: bool
    stdout: bytes
    stderr: bytes
    duration_ms: int


@dataclass(frozen=True)
class CaseRunResult:
    case_id: str
    run_ordinal: int
    passed: bool
    classification: str
    strictly_judgeable: bool
    target_sqlstate: str | None
    expected_sqlstate: str | None
    exit_code: int
    timed_out: bool
    boolean_oracle_failure_count: int
    error_sqlstates: tuple[str, ...]
    duration_ms: int
    normalized_stdout: bytes
    normalized_stderr: bytes

    def structured_projection(self) -> tuple[Any, ...]:
        return (
            self.case_id,
            self.passed,
            self.classification,
            self.strictly_judgeable,
            self.target_sqlstate,
            self.expected_sqlstate,
            self.exit_code,
            self.timed_out,
            self.boolean_oracle_failure_count,
            self.error_sqlstates,
        )

    def to_dict(self, *, include_transcript: bool = False) -> dict[str, Any]:
        payload = {
            "case_id": self.case_id,
            "run_ordinal": self.run_ordinal,
            "passed": self.passed,
            "classification": self.classification,
            "strictly_judgeable": self.strictly_judgeable,
            "target_sqlstate": self.target_sqlstate,
            "expected_sqlstate": self.expected_sqlstate,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "boolean_oracle_failure_count": self.boolean_oracle_failure_count,
            "error_sqlstates": list(self.error_sqlstates),
            "duration_ms": self.duration_ms,
            "stdout_sha256": hashlib.sha256(self.normalized_stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(self.normalized_stderr).hexdigest(),
        }
        if include_transcript:
            payload["stdout"] = self.normalized_stdout.decode(
                "utf-8", errors="replace"
            )
            payload["stderr"] = self.normalized_stderr.decode(
                "utf-8", errors="replace"
            )
        return payload


@dataclass(frozen=True)
class CaseTwoRunComparison:
    case_id: str
    passed: bool
    classification: str
    transcript_matches: bool
    structured_matches: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkerConfig:
    worker_id: int
    bin_dir: Path
    worker_root: Path
    port: int
    database: str = "pgcf_cop"
    role: str = "pgcf_superuser"

    def __post_init__(self) -> None:
        if self.worker_id < 1 or self.worker_id > 4:
            raise ValueError("worker_id must be between 1 and 4")
        if self.port < 1024 or self.port > 65535:
            raise ValueError("worker port must be between 1024 and 65535")


def build_worker_configs(
    runtime_root: Path,
    bin_dir: Path,
    *,
    workers: int,
    base_port: int = 55720,
) -> tuple[WorkerConfig, ...]:
    if workers < 1 or workers > 4:
        raise ValueError("workers must be between 1 and 4")
    root = Path(runtime_root).resolve()
    return tuple(
        WorkerConfig(
            worker_id=index,
            bin_dir=Path(bin_dir),
            worker_root=root / "workers" / f"worker-{index:02d}",
            port=base_port + index - 1,
        )
        for index in range(1, workers + 1)
    )


class PostgresWorker:
    """One serial psql worker backed by its own PostgreSQL cluster."""

    def __init__(self, config: WorkerConfig, *, timeout_seconds: int = 30) -> None:
        if timeout_seconds < 1 or timeout_seconds > 300:
            raise ValueError("timeout_seconds must be between 1 and 300")
        self.config = config
        self.timeout_seconds = timeout_seconds
        self.generation = 1
        self.started = False

    @property
    def generation_root(self) -> Path:
        return self.config.worker_root / f"generation-{self.generation:04d}"

    @property
    def data_dir(self) -> Path:
        return self.generation_root / "data"

    @property
    def socket_dir(self) -> Path:
        return self.generation_root / "socket"

    @property
    def log_path(self) -> Path:
        return self.generation_root / "postgres.log"

    @property
    def psql(self) -> Path:
        return self.config.bin_dir / "psql"

    def _environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        existing = environment.get("PGOPTIONS", "").strip()
        setting = "-c client_min_messages=warning"
        environment["PGOPTIONS"] = f"{existing} {setting}".strip()
        return environment

    def psql_command(self, sql_path: Path | None = None) -> list[str]:
        command = [
            str(self.psql),
            "-X",
            "-h",
            str(self.socket_dir),
            "-p",
            str(self.config.port),
            "-d",
            self.config.database,
            "-U",
            self.config.role,
            "-A",
            "-t",
            "-q",
            "-v",
            "VERBOSITY=sqlstate",
            "-v",
            "ON_ERROR_STOP=1",
        ]
        if sql_path is not None:
            command.extend(["-f", str(sql_path)])
        return command

    @staticmethod
    def _checked(command: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            raise FullSqlRuntimeError(
                f"command failed ({result.returncode}): {' '.join(command)}\n"
                + result.stderr.decode("utf-8", errors="replace")
            )
        return result

    def start(self) -> None:
        for executable in ("initdb", "pg_ctl", "createdb", "psql"):
            path = self.config.bin_dir / executable
            if not path.is_file():
                raise FullSqlRuntimeError(f"missing PostgreSQL executable: {path}")
        self.generation_root.mkdir(parents=True, exist_ok=True)
        self.socket_dir.mkdir(parents=True, exist_ok=True)
        if not (self.data_dir / "PG_VERSION").is_file():
            self._checked(
                [
                    str(self.config.bin_dir / "initdb"),
                    "-D",
                    str(self.data_dir),
                    "-A",
                    "trust",
                    "--no-locale",
                    "--encoding=UTF8",
                    "-U",
                    self.config.role,
                ],
                timeout=120,
            )
        status = subprocess.run(
            [
                str(self.config.bin_dir / "pg_ctl"),
                "-D",
                str(self.data_dir),
                "status",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if status.returncode != 0:
            options = " ".join(
                [
                    f"-k {self.socket_dir}",
                    f"-p {self.config.port}",
                    "-c listen_addresses=''",
                    "-c fsync=off",
                    "-c synchronous_commit=off",
                    "-c full_page_writes=off",
                    "-c max_connections=30",
                    "-c log_min_messages=warning",
                ]
            )
            self._checked(
                [
                    str(self.config.bin_dir / "pg_ctl"),
                    "-D",
                    str(self.data_dir),
                    "-w",
                    "-l",
                    str(self.log_path),
                    "-o",
                    options,
                    "start",
                ],
                timeout=120,
            )
        probe_database = "postgres"
        exists = self._checked(
            [
                str(self.psql),
                "-X",
                "-h",
                str(self.socket_dir),
                "-p",
                str(self.config.port),
                "-d",
                probe_database,
                "-U",
                self.config.role,
                "-Atqc",
                "SELECT 1 FROM pg_database WHERE datname = "
                + "'"
                + self.config.database.replace("'", "''")
                + "'",
            ]
        )
        if exists.stdout.strip() != b"1":
            self._checked(
                [
                    str(self.config.bin_dir / "createdb"),
                    "-h",
                    str(self.socket_dir),
                    "-p",
                    str(self.config.port),
                    "-U",
                    self.config.role,
                    self.config.database,
                ]
            )
        version = self._checked(
            [*self.psql_command(), "-c", "SHOW server_version_num"]
        ).stdout.strip()
        if version != b"180004":
            raise FullSqlRuntimeError(
                f"expected PostgreSQL 18.4, observed server_version_num={version!r}"
            )
        self._bootstrap_extensions()
        self.started = True

    def _bootstrap_extensions(self) -> None:
        extension_dir = self.config.bin_dir.parent / "share" / "extension"
        available = [
            name
            for name in ("dblink", "file_fdw", "postgres_fdw")
            if (extension_dir / f"{name}.control").is_file()
        ]
        if not available:
            return
        sql = "; ".join(
            f"CREATE EXTENSION IF NOT EXISTS {name}" for name in available
        )
        self._checked([*self.psql_command(), "-c", sql])

    def stop(self) -> None:
        if not (self.data_dir / "PG_VERSION").is_file():
            self.started = False
            return
        subprocess.run(
            [
                str(self.config.bin_dir / "pg_ctl"),
                "-D",
                str(self.data_dir),
                "-w",
                "-m",
                "fast",
                "stop",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        self.started = False

    def rebuild(self) -> None:
        self.stop()
        self.generation += 1
        self.start()

    def execute(self, sql_path: Path) -> CaseExecution:
        started_at = time.monotonic()
        try:
            result = subprocess.run(
                self.psql_command(sql_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
                check=False,
                env=self._environment(),
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            timed_out = True
        duration_ms = max(0, round((time.monotonic() - started_at) * 1000))
        return CaseExecution(
            exit_code=exit_code,
            timed_out=timed_out,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
        )


def _normalize_transcript(payload: bytes) -> bytes:
    normalized = payload.replace(b"\r\n", b"\n")
    normalized = re.sub(rb"(?m)^psql \([^\n]+\)\n", b"", normalized)
    normalized = re.sub(
        rb"(?m)psql:[^:\n]+:\d+:", b"psql:<SQL_PATH>:<LINE>:", normalized
    )
    return normalized


def _target_sqlstate(payload: bytes, *, compatibility: bool) -> str | None:
    matches = _TARGET_SQLSTATE.findall(payload)
    if len(matches) == 1:
        return matches[0].decode("ascii")
    if compatibility:
        legacy = _COMPATIBILITY_TARGET_SQLSTATE.findall(payload)
        if len(legacy) == 1:
            return legacy[0].decode("ascii")
    return None


def evaluate_case_execution(
    case: RuntimeManifestCase,
    execution: CaseExecution,
    *,
    run_ordinal: int,
) -> CaseRunResult:
    """Evaluate one psql execution without overstating legacy evidence."""

    if run_ordinal not in {1, 2}:
        raise FullSqlRuntimeError("run ordinal must be 1 or 2")
    stdout = _normalize_transcript(execution.stdout)
    stderr = _normalize_transcript(execution.stderr)
    compatibility = case.evidence_level == EVIDENCE_COMPATIBILITY
    target_sqlstate = _target_sqlstate(stdout, compatibility=compatibility)
    false_count = sum(line.strip() == b"f" for line in stdout.splitlines())
    errors = tuple(value.decode("ascii") for value in _PSQL_ERROR.findall(stderr))
    strictly_judgeable = case.evidence_level == EVIDENCE_STRICT

    if execution.timed_out:
        passed = False
        classification = "timeout"
    elif execution.exit_code != 0:
        passed = False
        classification = "unexpected_psql_error"
    elif false_count:
        passed = False
        classification = "oracle_failure"
    elif case.evidence_level == EVIDENCE_STRICT:
        if target_sqlstate is None:
            passed = False
            classification = "missing_target_sqlstate"
        elif target_sqlstate != case.expected_sqlstate:
            passed = False
            classification = "sqlstate_mismatch"
        else:
            passed = True
            classification = "strict_pass"
    elif case.evidence_level == EVIDENCE_COMPATIBILITY:
        if (
            target_sqlstate is not None
            and case.expected_sqlstate is not None
            and target_sqlstate != case.expected_sqlstate
        ):
            passed = False
            classification = "sqlstate_mismatch"
        elif case.expected_outcome == "success" and errors:
            passed = False
            classification = "unexpected_psql_error"
        elif case.expected_outcome == "expected_failure" and not (
            errors or target_sqlstate
        ):
            passed = False
            classification = "observed_mismatch"
        else:
            passed = True
            classification = "compatibility_pass"
    elif case.evidence_level == EVIDENCE_OBSERVATIONAL:
        if case.expected_outcome == "success" and errors:
            passed = False
            classification = "observed_mismatch"
        elif case.expected_outcome == "expected_failure" and not errors:
            passed = False
            classification = "observed_mismatch"
        else:
            passed = True
            classification = "not_strictly_judgeable"
    else:
        raise FullSqlRuntimeError(
            f"unknown evidence level: {case.evidence_level}"
        )

    return CaseRunResult(
        case_id=case.case_id,
        run_ordinal=run_ordinal,
        passed=passed,
        classification=classification,
        strictly_judgeable=strictly_judgeable,
        target_sqlstate=target_sqlstate,
        expected_sqlstate=case.expected_sqlstate,
        exit_code=execution.exit_code,
        timed_out=execution.timed_out,
        boolean_oracle_failure_count=false_count,
        error_sqlstates=errors,
        duration_ms=execution.duration_ms,
        normalized_stdout=stdout,
        normalized_stderr=stderr,
    )


def compare_case_runs(
    run_01: CaseRunResult,
    run_02: CaseRunResult,
) -> CaseTwoRunComparison:
    if run_01.case_id != run_02.case_id:
        raise FullSqlRuntimeError("cannot compare different case IDs")
    transcript_matches = (
        run_01.normalized_stdout == run_02.normalized_stdout
        and run_01.normalized_stderr == run_02.normalized_stderr
    )
    structured_matches = (
        run_01.structured_projection() == run_02.structured_projection()
    )
    passed = (
        run_01.passed
        and run_02.passed
        and transcript_matches
        and structured_matches
    )
    if not run_01.passed:
        classification = run_01.classification
    elif not run_02.passed:
        classification = run_02.classification
    elif not transcript_matches or not structured_matches:
        classification = "two_run_mismatch"
    else:
        classification = run_01.classification
    return CaseTwoRunComparison(
        case_id=run_01.case_id,
        passed=passed,
        classification=classification,
        transcript_matches=transcript_matches,
        structured_matches=structured_matches,
    )


def _schedule_names(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    names: set[str] = set()
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            line = line.split(":", 1)[1]
        names.update(line.split())
    return names


def _load_compatibility_plan(
    repository_root: Path,
    statement_key: str,
) -> dict[str, Mapping[str, Any]]:
    path = (
        repository_root
        / "artifacts/intermediates/remaining-statement-factor-cycle"
        / statement_key
        / "plan.json"
    )
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    return {
        str(case["sql_filename"]): case
        for case in cases
        if isinstance(case, Mapping) and "sql_filename" in case
    }


def _header_values(sql: str) -> dict[str, str]:
    return {
        match.group("key"): match.group("value")
        for match in _HEADER.finditer(sql)
    }


def _retained_statement(sql: str, fallback: str) -> str:
    match = _RETAINED_STATEMENT.search(sql)
    return match.group("statement").lower() if match else fallback


def _manifest_case(
    *,
    repository_root: Path,
    package: Path,
    sql_path: Path,
    statement_key: str,
    retained: bool,
    external_names: set[str],
    compatibility_plan: Mapping[str, Mapping[str, Any]],
) -> RuntimeManifestCase:
    raw = sql_path.read_bytes()
    sql = raw.decode("utf-8", errors="replace")
    headers = _header_values(sql)
    case_id = headers.get("case_id", sql_path.stem)
    planned = compatibility_plan.get(sql_path.name, {})
    expected_outcome: str | None
    expected_sqlstate: str | None
    object_prefix = (
        str(planned["object_prefix"])
        if "object_prefix" in planned
        else None
    )
    if "expected_outcome" in headers and "expected_sqlstate" in headers:
        evidence_level = EVIDENCE_STRICT
        expected_outcome = headers["expected_outcome"]
        expected_sqlstate = headers["expected_sqlstate"]
    elif retained:
        evidence_level = EVIDENCE_OBSERVATIONAL
        statement_key = _retained_statement(sql, statement_key)
        match = _FACTOR_EXPECTED.search(sql)
        expected_outcome = (
            "success"
            if match is not None and match.group("value") == "success"
            else "expected_failure"
            if match is not None
            else None
        )
        expected_sqlstate = None
    else:
        evidence_level = EVIDENCE_COMPATIBILITY
        expected_outcome = (
            str(planned["outcome"]) if "outcome" in planned else None
        )
        derived = planned.get("derived_axes", {})
        expected_sqlstate = (
            str(derived["expected_sqlstate"])
            if isinstance(derived, Mapping) and "expected_sqlstate" in derived
            else None
        )
    return RuntimeManifestCase(
        ordinal=0,
        statement_key=statement_key,
        case_id=case_id,
        sql_path=sql_path.relative_to(repository_root).as_posix(),
        sql_sha256=hashlib.sha256(raw).hexdigest(),
        package_path=package.relative_to(repository_root).as_posix(),
        evidence_level=evidence_level,
        expected_outcome=expected_outcome,
        expected_sqlstate=expected_sqlstate,
        object_prefix=object_prefix,
        external=sql_path.stem in external_names,
    )


def compile_runtime_manifest(
    repository_root: Path,
    progress_path: Path | None = None,
) -> tuple[RuntimeManifestCase, ...]:
    """Compile the unique formal execution scope from statement-cycle progress."""

    root = Path(repository_root).resolve(strict=True)
    progress = (
        Path(progress_path)
        if progress_path is not None
        else root
        / "artifacts/intermediates/remaining-statement-factor-cycle/progress.json"
    )
    if not progress.is_absolute():
        progress = root / progress
    payload = json.loads(progress.read_text(encoding="utf-8"))
    statements = payload.get("statements")
    if not isinstance(statements, Mapping):
        raise FullSqlRuntimeError("progress statements must be an object")

    seen: set[Path] = set()
    collected: list[RuntimeManifestCase] = []
    for statement_key, entry in statements.items():
        if not isinstance(entry, Mapping):
            raise FullSqlRuntimeError(f"invalid progress entry for {statement_key}")
        status = entry.get("status")
        if status not in {"completed", "retained_existing"}:
            continue
        package = root / str(entry["package_path"])
        retained = status == "retained_existing"
        sql_paths = (
            sorted(package.rglob("*.sql"))
            if retained
            else sorted(package.glob("*.sql"))
        )
        external_names = _schedule_names(package / "external_schedule")
        compatibility = (
            {} if retained else _load_compatibility_plan(root, str(statement_key))
        )
        for sql_path in sql_paths:
            identity = sql_path.resolve(strict=True)
            if identity in seen:
                continue
            seen.add(identity)
            collected.append(
                _manifest_case(
                    repository_root=root,
                    package=package,
                    sql_path=sql_path,
                    statement_key=str(statement_key),
                    retained=retained,
                    external_names=external_names,
                    compatibility_plan=compatibility,
                )
            )

    return tuple(
        RuntimeManifestCase(**{**case.to_dict(), "ordinal": ordinal})
        for ordinal, case in enumerate(collected, start=1)
    )


__all__ = [
    "CaseExecution",
    "CaseRunResult",
    "CaseTwoRunComparison",
    "EVIDENCE_COMPATIBILITY",
    "EVIDENCE_OBSERVATIONAL",
    "EVIDENCE_STRICT",
    "FullSqlRuntimeError",
    "PostgresWorker",
    "RuntimeManifestCase",
    "WorkerConfig",
    "build_worker_configs",
    "compare_case_runs",
    "compile_runtime_manifest",
    "evaluate_case_execution",
]
