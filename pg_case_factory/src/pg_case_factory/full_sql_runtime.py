"""Resumable PostgreSQL 18.4 validation for the formal SQL corpus."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence


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
    "EVIDENCE_COMPATIBILITY",
    "EVIDENCE_OBSERVATIONAL",
    "EVIDENCE_STRICT",
    "FullSqlRuntimeError",
    "RuntimeManifestCase",
    "compile_runtime_manifest",
]
