"""Resumable PostgreSQL 18.4 validation for the formal SQL corpus."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
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
    expected_outcome: str | None
    expected_sqlstate: str | None
    object_prefix: str | None = None
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
        planned = compatibility_plan.get(sql_path.name, {})
        expected_outcome = (
            str(planned["outcome"]) if "outcome" in planned else None
        )
        derived = planned.get("derived_axes", {})
        expected_sqlstate = (
            str(derived["expected_sqlstate"])
            if isinstance(derived, Mapping) and "expected_sqlstate" in derived
            else None
        )
        object_prefix = (
            str(planned["object_prefix"])
            if "object_prefix" in planned
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
            {}
            if retained
            else _load_compatibility_plan(root, str(statement_key))
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
    "RuntimeManifestCase",
    "compare_case_runs",
    "compile_runtime_manifest",
    "evaluate_case_execution",
]
