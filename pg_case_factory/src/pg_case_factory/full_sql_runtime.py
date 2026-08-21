"""Resumable PostgreSQL 18.4 validation for the formal SQL corpus."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Mapping, Sequence


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
_PSQL_ERROR = re.compile(rb"\bERROR:\s+(?:[A-Z]+:\s+)?([0-9A-Z]{5})\b")


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
        return Path("/tmp/pgcf-fsv1-sockets") / (
            f"w{self.config.worker_id:02d}-p{self.config.port}-g{self.generation:04d}"
        )

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

    def server_environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        environment["PGHOST"] = str(self.socket_dir)
        environment["PGPORT"] = str(self.config.port)
        environment["PGUSER"] = self.config.role
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
    def _checked(
        command: list[str],
        *,
        timeout: int = 60,
        environment: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=environment,
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
                environment=self.server_environment(),
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
                environment=self.server_environment(),
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
        previous_root = self.generation_root
        previous_socket = self.socket_dir
        previous_log = self.log_path
        self.stop()
        if previous_log.is_file():
            archive = (
                self.config.worker_root
                / "rebuild-logs"
                / f"generation-{self.generation:04d}.log"
            )
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(previous_log, archive)
        if previous_root.is_dir():
            shutil.rmtree(previous_root)
        if previous_socket.is_dir():
            shutil.rmtree(previous_socket)
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


def _normalize_transcript(
    payload: bytes,
    *,
    normalize_dynamic_oids: bool = False,
) -> bytes:
    normalized = payload.replace(b"\r\n", b"\n")
    normalized = re.sub(rb"(?m)^psql \([^\n]+\)\n", b"", normalized)
    normalized = re.sub(
        rb"(?m)psql:[^:\n]+:\d+:", b"psql:<SQL_PATH>:<LINE>:", normalized
    )
    if normalize_dynamic_oids:
        def replace_numeric_field(match: re.Match[bytes]) -> bytes:
            prefix, value = match.groups()
            return prefix + (b"<OID>" if int(value) >= 16384 else value)

        normalized = re.sub(
            rb"(?m)(^|\|)([0-9]{4,})(?=\||$)",
            replace_numeric_field,
            normalized,
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
    normalize_dynamic_oids = case.evidence_level != EVIDENCE_STRICT
    stdout = _normalize_transcript(
        execution.stdout, normalize_dynamic_oids=normalize_dynamic_oids
    )
    stderr = _normalize_transcript(
        execution.stderr, normalize_dynamic_oids=normalize_dynamic_oids
    )
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


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_runtime_manifest(
    path: Path,
    cases: Sequence[RuntimeManifestCase],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(
                json.dumps(case.to_dict(), ensure_ascii=False, sort_keys=True)
                + "\n"
            )
    temporary.replace(target)


def load_runtime_manifest(path: Path) -> tuple[RuntimeManifestCase, ...]:
    cases: list[RuntimeManifestCase] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                cases.append(RuntimeManifestCase(**json.loads(line)))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise FullSqlRuntimeError(
                    f"invalid manifest line {line_number}: {exc}"
                ) from exc
    expected = list(range(1, len(cases) + 1))
    observed = [case.ordinal for case in cases]
    if observed != expected:
        raise FullSqlRuntimeError("manifest ordinals must be continuous from 1")
    return tuple(cases)


def partition_cases(
    cases: Sequence[RuntimeManifestCase],
    batch_size: int,
) -> tuple[tuple[RuntimeManifestCase, ...], ...]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    return tuple(
        tuple(cases[start : start + batch_size])
        for start in range(0, len(cases), batch_size)
    )


def calibration_cases(
    cases: Sequence[RuntimeManifestCase],
) -> tuple[RuntimeManifestCase, ...]:
    """Select both outcome poles per statement plus every external case."""

    selected: dict[int, RuntimeManifestCase] = {
        case.ordinal: case for case in cases if case.external
    }
    seen: set[tuple[str, str | None]] = set()
    seen_levels: set[str] = set()
    for case in cases:
        outcome_key = (case.statement_key, case.expected_outcome)
        if outcome_key not in seen:
            selected[case.ordinal] = case
            seen.add(outcome_key)
        if case.evidence_level not in seen_levels:
            selected[case.ordinal] = case
            seen_levels.add(case.evidence_level)
    return tuple(selected[index] for index in sorted(selected))


def run_case_pair(
    worker: Any,
    repository_root: Path,
    case: RuntimeManifestCase,
) -> dict[str, Any]:
    sql_path = Path(repository_root) / case.sql_path
    execution_01 = worker.execute(sql_path)
    run_01 = evaluate_case_execution(case, execution_01, run_ordinal=1)
    if execution_01.timed_out or execution_01.exit_code == 2:
        worker.rebuild()
    execution_02 = worker.execute(sql_path)
    run_02 = evaluate_case_execution(case, execution_02, run_ordinal=2)
    comparison = compare_case_runs(run_01, run_02)
    if execution_02.timed_out or execution_02.exit_code == 2:
        worker.rebuild()
    include_transcript = not comparison.passed
    return {
        "schema_version": 1,
        "case": case.to_dict(),
        "run_01": run_01.to_dict(include_transcript=include_transcript),
        "run_02": run_02.to_dict(include_transcript=include_transcript),
        "comparison": comparison.to_dict(),
        "worker_id": getattr(getattr(worker, "config", None), "worker_id", None),
        "worker_generation": getattr(worker, "generation", None),
    }


def _verify_case_bytes(repository_root: Path, case: RuntimeManifestCase) -> None:
    path = repository_root / case.sql_path
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError as exc:
        raise FullSqlRuntimeError(f"manifest SQL is missing: {path}") from exc
    if digest != case.sql_sha256:
        raise FullSqlRuntimeError(f"manifest SQL SHA drift: {case.sql_path}")


def run_runtime_batch(
    workers: Sequence[PostgresWorker],
    repository_root: Path,
    cases: Sequence[RuntimeManifestCase],
) -> tuple[dict[str, Any], ...]:
    if not workers:
        raise ValueError("at least one worker is required")
    root = Path(repository_root).resolve(strict=True)
    for case in cases:
        _verify_case_bytes(root, case)
    assignments = [list() for _ in workers]
    for index, case in enumerate(cases):
        assignments[index % len(workers)].append(case)

    def execute_slice(index: int) -> list[dict[str, Any]]:
        worker = workers[index]
        return [run_case_pair(worker, root, case) for case in assignments[index]]

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(workers)) as pool:
        for worker_results in pool.map(execute_slice, range(len(workers))):
            results.extend(worker_results)
    results.sort(key=lambda item: int(item["case"]["ordinal"]))
    return tuple(results)


def _batch_result_path(output_root: Path, batch_id: int) -> Path:
    return output_root / "results" / f"batch-{batch_id:05d}.jsonl"


def _write_batch_results(path: Path, results: Sequence[Mapping[str, Any]]) -> None:
    payload = "".join(
        json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
        for result in results
    )
    _atomic_write_text(path, payload)


def _load_batch_results(path: Path) -> tuple[dict[str, Any], ...]:
    return tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _batch_is_complete(
    path: Path,
    cases: Sequence[RuntimeManifestCase],
) -> bool:
    if not path.is_file():
        return False
    try:
        records = _load_batch_results(path)
    except (OSError, json.JSONDecodeError):
        return False
    expected = [(case.ordinal, case.sql_sha256) for case in cases]
    observed = [
        (int(record["case"]["ordinal"]), str(record["case"]["sql_sha256"]))
        for record in records
    ]
    return observed == expected and all(
        "run_01" in record and "run_02" in record and "comparison" in record
        for record in records
    )


def _write_checkpoint(
    output_root: Path,
    *,
    mode: str,
    total_cases: int,
    completed_cases: int,
    completed_batches: int,
    batch_count: int,
) -> None:
    payload = {
        "schema_version": 1,
        "mode": mode,
        "server_version_num": 180004,
        "total_cases": total_cases,
        "completed_cases": completed_cases,
        "completed_executions": completed_cases * 2,
        "completed_batches": completed_batches,
        "batch_count": batch_count,
    }
    _atomic_write_text(
        output_root / "checkpoint.json",
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def run_runtime_batches(
    *,
    workers: Sequence[PostgresWorker],
    repository_root: Path,
    output_root: Path,
    cases: Sequence[RuntimeManifestCase],
    batch_size: int,
    mode: str,
    resume: bool,
) -> dict[str, Any]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    batches = partition_cases(cases, batch_size)
    completed_cases = 0
    completed_batches = 0
    classifications: Counter[str] = Counter()
    for batch_id, batch in enumerate(batches, start=1):
        path = _batch_result_path(output, batch_id)
        if resume and _batch_is_complete(path, batch):
            results = _load_batch_results(path)
        else:
            results = run_runtime_batch(workers, repository_root, batch)
            _write_batch_results(path, results)
        completed_batches += 1
        completed_cases += len(batch)
        classifications.update(
            str(result["comparison"]["classification"]) for result in results
        )
        _write_checkpoint(
            output,
            mode=mode,
            total_cases=len(cases),
            completed_cases=completed_cases,
            completed_batches=completed_batches,
            batch_count=len(batches),
        )
        print(
            json.dumps(
                {
                    "event": "batch_complete",
                    "mode": mode,
                    "batch_id": batch_id,
                    "batch_count": len(batches),
                    "completed_cases": completed_cases,
                    "total_cases": len(cases),
                    "classifications": dict(sorted(classifications.items())),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    summary = {
        "schema_version": 1,
        "mode": mode,
        "server_version_num": 180004,
        "case_count": len(cases),
        "execution_count": len(cases) * 2,
        "batch_count": len(batches),
        "classifications": dict(sorted(classifications.items())),
    }
    return summary


def report_runtime_results(output_root: Path) -> dict[str, Any]:
    output = Path(output_root)
    manifest_path = output / "manifest.jsonl"
    manifest = load_runtime_manifest(manifest_path)
    expected_by_ordinal = {case.ordinal: case for case in manifest}
    classifications: Counter[str] = Counter()
    levels: Counter[str] = Counter()
    evidence_classifications: dict[str, Counter[str]] = {}
    outcome_classifications: dict[str, Counter[str]] = {}
    statements: dict[str, Counter[str]] = {}
    statement_details: dict[str, dict[str, Any]] = {}
    expected_to_actual: dict[str, Counter[str]] = {}
    error_sqlstates: Counter[str] = Counter()
    failure_examples: dict[str, list[dict[str, Any]]] = {}
    case_count = 0
    passed_count = 0
    paired_case_count = 0
    execution_count = 0
    duplicate_ordinal_count = 0
    unknown_ordinal_count = 0
    sql_sha_mismatch_count = 0
    case_metadata_mismatch_count = 0
    result_schema_mismatch_count = 0
    seen_ordinals: set[int] = set()
    transcript_mismatch_count = 0
    structured_mismatch_count = 0
    duration_ms = 0
    result_paths = sorted((output / "results").glob("batch-*.jsonl"))
    for path in result_paths:
        for record in _load_batch_results(path):
            case_count += 1
            comparison = record["comparison"]
            case = record["case"]
            ordinal = int(case["ordinal"])
            if ordinal in seen_ordinals:
                duplicate_ordinal_count += 1
            seen_ordinals.add(ordinal)
            expected = expected_by_ordinal.get(ordinal)
            if expected is None:
                unknown_ordinal_count += 1
            else:
                if str(case.get("sql_sha256")) != expected.sql_sha256:
                    sql_sha_mismatch_count += 1
                if case != expected.to_dict():
                    case_metadata_mismatch_count += 1
            if int(record.get("schema_version", -1)) != 1:
                result_schema_mismatch_count += 1
            has_pair = "run_01" in record and "run_02" in record
            paired_case_count += has_pair
            execution_count += int("run_01" in record) + int("run_02" in record)
            if not has_pair:
                continue
            for run_name in ("run_01", "run_02"):
                duration_ms += int(record[run_name].get("duration_ms", 0))
            classification = str(comparison["classification"])
            statement = str(case["statement_key"])
            evidence = str(case["evidence_level"])
            outcome = str(case.get("expected_outcome"))
            classifications[classification] += 1
            levels[evidence] += 1
            evidence_classifications.setdefault(evidence, Counter())[classification] += 1
            outcome_classifications.setdefault(outcome, Counter())[classification] += 1
            statements.setdefault(statement, Counter())[classification] += 1
            passed = bool(comparison["passed"])
            passed_count += passed
            details = statement_details.setdefault(
                statement,
                {
                    "case_count": 0,
                    "passed_count": 0,
                    "not_passed_count": 0,
                    "classifications": Counter(),
                    "evidence_levels": Counter(),
                    "expected_outcomes": Counter(),
                },
            )
            details["case_count"] += 1
            details["passed_count"] += passed
            details["not_passed_count"] += not passed
            details["classifications"][classification] += 1
            details["evidence_levels"][evidence] += 1
            details["expected_outcomes"][outcome] += 1
            transcript_mismatch_count += not bool(
                comparison.get("transcript_matches", False)
            )
            structured_mismatch_count += not bool(
                comparison.get("structured_matches", False)
            )
            run_01 = record["run_01"]
            expected_state = str(case.get("expected_sqlstate") or "<undefined>")
            actual_state = str(run_01.get("target_sqlstate") or "<missing>")
            expected_to_actual.setdefault(expected_state, Counter())[actual_state] += 1
            error_sqlstates.update(
                str(value) for value in run_01.get("error_sqlstates", [])
            )
            if not passed and len(failure_examples.setdefault(classification, [])) < 20:
                failure_examples[classification].append(
                    {
                        "ordinal": ordinal,
                        "case_id": str(case["case_id"]),
                        "statement_key": statement,
                        "sql_path": str(case["sql_path"]),
                        "expected_sqlstate": case.get("expected_sqlstate"),
                        "actual_target_sqlstate": run_01.get("target_sqlstate"),
                        "error_sqlstates": run_01.get("error_sqlstates", []),
                    }
                )
    missing_ordinals = sorted(set(expected_by_ordinal) - seen_ordinals)
    checkpoint_path = output / "checkpoint.json"
    checkpoint = (
        json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint_path.is_file()
        else {}
    )
    server_version_num = checkpoint.get("server_version_num")
    run_metadata_path = output / "run.json"
    run_metadata = (
        json.loads(run_metadata_path.read_text(encoding="utf-8"))
        if run_metadata_path.is_file()
        else {}
    )
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    integrity = {
        "complete": False,
        "manifest_case_count": len(manifest),
        "result_case_count": case_count,
        "paired_case_count": paired_case_count,
        "execution_count": execution_count,
        "missing_ordinal_count": len(missing_ordinals),
        "missing_ordinal_examples": missing_ordinals[:20],
        "duplicate_ordinal_count": duplicate_ordinal_count,
        "unknown_ordinal_count": unknown_ordinal_count,
        "sql_sha_mismatch_count": sql_sha_mismatch_count,
        "case_metadata_mismatch_count": case_metadata_mismatch_count,
        "result_schema_mismatch_count": result_schema_mismatch_count,
        "server_version_num": server_version_num,
        "manifest_sha256": manifest_sha256,
        "manifest_sha_matches_run_metadata": (
            run_metadata.get("manifest_sha256") in (None, manifest_sha256)
        ),
        "checkpoint_total_cases": checkpoint.get("total_cases"),
        "checkpoint_completed_cases": checkpoint.get("completed_cases"),
        "checkpoint_completed_executions": checkpoint.get("completed_executions"),
        "checkpoint_batch_count": checkpoint.get("batch_count"),
        "checkpoint_completed_batches": checkpoint.get("completed_batches"),
        "result_batch_file_count": len(result_paths),
    }
    integrity["complete"] = all(
        (
            case_count == len(manifest),
            paired_case_count == len(manifest),
            execution_count == len(manifest) * 2,
            not missing_ordinals,
            duplicate_ordinal_count == 0,
            unknown_ordinal_count == 0,
            sql_sha_mismatch_count == 0,
            case_metadata_mismatch_count == 0,
            result_schema_mismatch_count == 0,
            server_version_num == 180004,
            checkpoint.get("total_cases") == len(manifest),
            checkpoint.get("completed_cases") == len(manifest),
            checkpoint.get("completed_executions") == len(manifest) * 2,
            checkpoint.get("completed_batches") == len(result_paths),
            run_metadata.get("manifest_sha256") in (None, manifest_sha256),
        )
    )
    payload = {
        "schema_version": 1,
        "server_version_num": server_version_num,
        "case_count": case_count,
        "execution_count": execution_count,
        "passed_count": passed_count,
        "not_passed_count": case_count - passed_count,
        "classifications": dict(sorted(classifications.items())),
        "evidence_levels": dict(sorted(levels.items())),
        "evidence_classifications": {
            key: dict(sorted(value.items()))
            for key, value in sorted(evidence_classifications.items())
        },
        "expected_outcome_classifications": {
            key: dict(sorted(value.items()))
            for key, value in sorted(outcome_classifications.items())
        },
        "determinism": {
            "transcript_mismatch_count": transcript_mismatch_count,
            "structured_mismatch_count": structured_mismatch_count,
        },
        "total_duration_ms": duration_ms,
        "integrity": integrity,
        "statements": {
            key: dict(sorted(value.items()))
            for key, value in sorted(statements.items())
        },
        "failure_examples": {
            key: value for key, value in sorted(failure_examples.items())
        },
    }
    reports = output / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    statement_payload = {
        "schema_version": 1,
        "server_version_num": server_version_num,
        "statement_count": len(statement_details),
        "statements": {
            key: {
                name: dict(sorted(value.items()))
                if isinstance(value, Counter)
                else value
                for name, value in details.items()
            }
            for key, details in sorted(statement_details.items())
        },
    }
    sqlstate_payload = {
        "schema_version": 1,
        "server_version_num": server_version_num,
        "expected_to_actual": {
            key: dict(sorted(value.items()))
            for key, value in sorted(expected_to_actual.items())
        },
        "run_01_error_sqlstates": dict(sorted(error_sqlstates.items())),
    }
    _atomic_write_text(
        reports / "final-summary.json",
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write_text(
        reports / "statement-summary.json",
        json.dumps(statement_payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
    )
    _atomic_write_text(
        reports / "sqlstate-summary.json",
        json.dumps(sqlstate_payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
    )
    return payload


def _manifest_summary(cases: Sequence[RuntimeManifestCase]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case_count": len(cases),
        "execution_count": len(cases) * 2,
        "statement_count": len({case.statement_key for case in cases}),
        "evidence_levels": dict(
            sorted(Counter(case.evidence_level for case in cases).items())
        ),
        "expected_outcomes": {
            str(key): value
            for key, value in sorted(
                Counter(case.expected_outcome for case in cases).items(),
                key=lambda item: str(item[0]),
            )
        },
        "external_case_count": sum(case.external for case in cases),
    }


def _start_workers(
    *,
    output_root: Path,
    bin_dir: Path,
    worker_count: int,
    base_port: int,
    timeout_seconds: int,
) -> tuple[PostgresWorker, ...]:
    workers = tuple(
        PostgresWorker(config, timeout_seconds=timeout_seconds)
        for config in build_worker_configs(
            output_root, bin_dir, workers=worker_count, base_port=base_port
        )
    )
    started: list[PostgresWorker] = []
    try:
        for worker in workers:
            worker.start()
            started.append(worker)
    except BaseException:
        for worker in reversed(started):
            worker.stop()
        raise
    return workers


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pg_case_factory.full_sql_runtime"
    )
    parser.add_argument("--repository-root", default=".")
    parser.add_argument(
        "--output", default="artifacts/runtime/pg18-full-sql-validation-v1"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("compile")
    for name in ("calibrate", "run"):
        command = commands.add_parser(name)
        command.add_argument("--workers", type=int, default=4)
        command.add_argument("--batch-size", type=int, default=500)
        command.add_argument("--timeout-seconds", type=int, default=30)
        command.add_argument("--base-port", type=int, default=55720)
        command.add_argument(
            "--bin-dir", default="/tmp/pgcf-postgresql-18.4-install/bin"
        )
        command.add_argument("--resume", action="store_true")
    commands.add_parser("report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    repository_root = Path(arguments.repository_root).resolve(strict=True)
    output = Path(arguments.output)
    if not output.is_absolute():
        output = repository_root / output
    manifest_path = output / "manifest.jsonl"
    if arguments.command == "compile":
        cases = compile_runtime_manifest(repository_root)
        write_runtime_manifest(manifest_path, cases)
        summary = _manifest_summary(cases)
        summary["manifest_sha256"] = hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest()
        _atomic_write_text(
            output / "run.json",
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
        )
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
        return 0
    if arguments.command == "report":
        payload = report_runtime_results(output)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        return 0
    cases = load_runtime_manifest(manifest_path)
    selected = calibration_cases(cases) if arguments.command == "calibrate" else cases
    destination = output / "calibration" if arguments.command == "calibrate" else output
    workers = _start_workers(
        output_root=output,
        bin_dir=Path(arguments.bin_dir),
        worker_count=arguments.workers,
        base_port=arguments.base_port,
        timeout_seconds=arguments.timeout_seconds,
    )
    try:
        summary = run_runtime_batches(
            workers=workers,
            repository_root=repository_root,
            output_root=destination,
            cases=selected,
            batch_size=arguments.batch_size,
            mode=arguments.command,
            resume=arguments.resume,
        )
    finally:
        for worker in reversed(workers):
            worker.stop()
    report_path = (
        output / "reports" / "calibration.json"
        if arguments.command == "calibrate"
        else output / "reports" / "run-summary.json"
    )
    _atomic_write_text(
        report_path,
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


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
    "build_argument_parser",
    "build_worker_configs",
    "calibration_cases",
    "compare_case_runs",
    "compile_runtime_manifest",
    "evaluate_case_execution",
    "load_runtime_manifest",
    "main",
    "partition_cases",
    "report_runtime_results",
    "run_case_pair",
    "run_runtime_batch",
    "run_runtime_batches",
    "write_runtime_manifest",
]
