from __future__ import annotations

import difflib
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterator, Mapping

from .artifact_store import (
    ensure_contained_directory,
    load_run_execution_profile,
    load_run_manifest,
    write_json,
    write_text,
)
from .sql_safety import validate_sql_for_basic_runner
from .regression_style import ExecutionTranscript, compare_two_run_transcripts


CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
EXPECTED_SERVER_VERSION_NUM = 180004
EXECUTION_PROFILE_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SESSION_IDENTITY_SENTINEL = "__PG_CASE_FACTORY_ENDPOINT_V2__"
_VERBOSE_TERMINAL_DIAGNOSTIC_PATTERN = re.compile(
    r"(?m)^(?:psql:[^\r\n]*?:[ \t]*)?"
    r"(?P<severity>ERROR|FATAL|PANIC):[ \t]+"
    r"(?P<sqlstate>[0-9A-Z]{5}):(?:[ \t]|$)"
)


def _session_identity_query() -> str:
    """Return a one-row identity probe suitable for the SQL execution session."""

    return (
        "SELECT '"
        + _SESSION_IDENTITY_SENTINEL
        + "' || pg_catalog.json_build_object("
        "'server_version_num', pg_catalog.current_setting('server_version_num')::integer, "
        "'system_identifier', control.system_identifier::text, "
        "'server_address', COALESCE(pg_catalog.inet_server_addr()::text, 'local'), "
        "'server_port', COALESCE(pg_catalog.inet_server_port()::text, ''), "
        "'current_user', CURRENT_USER::text, "
        "'is_superuser', roles.rolsuper, "
        "'can_createdb', roles.rolcreatedb, "
        "'can_createrole', roles.rolcreaterole, "
        "'can_replication', roles.rolreplication, "
        "'can_bypassrls', roles.rolbypassrls, "
        "'pg_read_server_files', "
        "pg_catalog.pg_has_role(CURRENT_USER, 'pg_read_server_files', 'MEMBER'), "
        "'pg_write_server_files', "
        "pg_catalog.pg_has_role(CURRENT_USER, 'pg_write_server_files', 'MEMBER'), "
        "'pg_execute_server_program', "
        "pg_catalog.pg_has_role(CURRENT_USER, 'pg_execute_server_program', 'MEMBER'), "
        "'privileged_role_memberships', COALESCE(("
        "SELECT pg_catalog.json_agg(candidate.rolname ORDER BY candidate.rolname) "
        "FROM pg_catalog.pg_roles AS candidate "
        "WHERE candidate.rolname <> CURRENT_USER "
        "AND pg_catalog.pg_has_role(CURRENT_USER, candidate.oid, 'MEMBER') "
        "AND (candidate.rolsuper OR candidate.rolcreatedb OR candidate.rolcreaterole "
        "OR candidate.rolreplication OR candidate.rolbypassrls)"
        "), '[]'::json)"
        ")::text "
        "FROM pg_catalog.pg_control_system() AS control "
        "JOIN pg_catalog.pg_roles AS roles ON roles.rolname = CURRENT_USER;"
    )


@dataclass(frozen=True)
class NormalizationProfile:
    drop_line_patterns: tuple[str, ...] = ()
    replacements: tuple[tuple[str, str], ...] = ()
    strip_trailing_whitespace: bool = False


@dataclass(frozen=True)
class DifferentialResult:
    identical: bool
    reference_sha256: str
    dut_sha256: str
    normalized_reference: str
    normalized_dut: str
    unified_diff: str
    normalization_profile: dict[str, Any]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PsqlTarget:
    name: str
    service: str
    database: str

    def __post_init__(self) -> None:
        if not self.name or any(character.isspace() for character in self.name):
            raise ValueError("target name must be a non-empty token")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", self.service or ""):
            raise ValueError("service must be a bare libpq service name")
        database = self.database or ""
        lowered = database.lower()
        if (
            not database
            or "=" in database
            or lowered.startswith("postgresql://")
            or lowered.startswith("postgres://")
            or any(ord(character) < 32 or ord(character) == 127 for character in database)
        ):
            raise ValueError(
                "database must be a bare database name, not a URI or conninfo; "
                "put connection settings in the libpq service"
            )


@dataclass(frozen=True)
class EndpointIdentity:
    target_name: str
    service: str
    database: str
    server_version_num: int
    system_identifier: str
    server_address: str
    server_port: str
    current_user: str = ""
    is_superuser: bool = False
    can_createdb: bool = False
    can_createrole: bool = False
    can_replication: bool = False
    can_bypassrls: bool = False
    dangerous_role_memberships: tuple[str, ...] = ()
    privileged_role_memberships: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)


def validate_endpoint_identity(identity: EndpointIdentity) -> None:
    """Validate the durable PostgreSQL 18.4 endpoint identity structure.

    Privilege policy is deliberately separate.  External isolated harnesses
    may require superuser or one of PostgreSQL's server-file/program roles,
    but they still have to prove a well-formed PostgreSQL 18.4 identity.
    """

    token_fields = {
        "target_name": identity.target_name,
        "service": identity.service,
        "database": identity.database,
        "current_user": identity.current_user,
    }
    for field_name, value in token_fields.items():
        if (
            not isinstance(value, str)
            or not value
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ValueError(
                f"endpoint identity {field_name} must be a non-empty string "
                "without control characters"
            )
    if (
        type(identity.server_version_num) is not int
        or identity.server_version_num != EXPECTED_SERVER_VERSION_NUM
    ):
        raise ValueError(
            f"{identity.target_name} reports server_version_num="
            f"{identity.server_version_num}, expected {EXPECTED_SERVER_VERSION_NUM}"
        )
    if (
        not isinstance(identity.system_identifier, str)
        or not identity.system_identifier.isdigit()
        or int(identity.system_identifier) < 1
    ):
        raise ValueError(
            f"{identity.target_name} endpoint preflight returned an invalid system identifier"
        )
    if not isinstance(identity.server_address, str) or not identity.server_address:
        raise ValueError(
            f"{identity.target_name} endpoint preflight returned an invalid server address"
        )
    if not isinstance(identity.server_port, str) or (
        identity.server_port
        and (
            not identity.server_port.isdigit()
            or not 1 <= int(identity.server_port) <= 65535
        )
    ):
        raise ValueError(
            f"{identity.target_name} endpoint preflight returned an invalid server port"
        )
    privilege_flags = {
        "is_superuser": identity.is_superuser,
        "can_createdb": identity.can_createdb,
        "can_createrole": identity.can_createrole,
        "can_replication": identity.can_replication,
        "can_bypassrls": identity.can_bypassrls,
    }
    for flag_name, flag_value in privilege_flags.items():
        if type(flag_value) is not bool:
            raise ValueError(
                f"{identity.target_name} endpoint preflight returned an invalid "
                f"{flag_name} flag"
            )
    allowed_dangerous_roles = {
        "pg_read_server_files",
        "pg_write_server_files",
        "pg_execute_server_program",
    }
    if (
        not isinstance(identity.dangerous_role_memberships, tuple)
        or any(
            not isinstance(role, str) or role not in allowed_dangerous_roles
            for role in identity.dangerous_role_memberships
        )
        or len(identity.dangerous_role_memberships)
        != len(set(identity.dangerous_role_memberships))
    ):
        raise ValueError(
            f"{identity.target_name} endpoint preflight returned invalid role memberships"
        )
    if (
        not isinstance(identity.privileged_role_memberships, tuple)
        or any(
            not isinstance(role, str)
            or not role
            or any(ord(character) < 32 or ord(character) == 127 for character in role)
            for role in identity.privileged_role_memberships
        )
        or tuple(sorted(identity.privileged_role_memberships))
        != identity.privileged_role_memberships
        or len(identity.privileged_role_memberships)
        != len(set(identity.privileged_role_memberships))
    ):
        raise ValueError(
            f"{identity.target_name} endpoint preflight returned invalid privileged "
            "role memberships"
        )


def validate_basic_endpoint_identity(identity: EndpointIdentity) -> None:
    """Require the structural identity plus the basic runner's least privilege."""

    validate_endpoint_identity(identity)
    direct_capabilities = [
        name
        for name, enabled in (
            ("superuser", identity.is_superuser),
            ("createdb", identity.can_createdb),
            ("createrole", identity.can_createrole),
            ("replication", identity.can_replication),
            ("bypassrls", identity.can_bypassrls),
        )
        if enabled
    ]
    if (
        direct_capabilities
        or identity.dangerous_role_memberships
        or identity.privileged_role_memberships
    ):
        roles = list(identity.dangerous_role_memberships)
        roles.extend(identity.privileged_role_memberships)
        roles[0:0] = direct_capabilities
        raise ValueError(
            f"{identity.target_name} basic runner role is over-privileged: "
            + ", ".join(roles)
            + "; use an isolated external harness for privileged cases"
        )


def validate_comparable_endpoint_pair(
    reference: EndpointIdentity,
    dut: EndpointIdentity,
    *,
    require_basic_privileges: bool = False,
) -> None:
    """Require the formal pair to differ physically but share visible identity."""

    validate_endpoint_identity(reference)
    validate_endpoint_identity(dut)
    if require_basic_privileges:
        validate_basic_endpoint_identity(reference)
        validate_basic_endpoint_identity(dut)
    if reference.system_identifier == dut.system_identifier:
        raise ValueError(
            "reference and DUT resolve to the same PostgreSQL system identifier"
        )
    if reference.database != dut.database:
        raise ValueError(
            "reference and DUT must use the same database name for formal comparison"
        )
    if reference.current_user != dut.current_user:
        raise ValueError(
            "reference and DUT must use the same current_user for formal comparison"
        )


def _validate_endpoint_pair_anchors(
    reference: EndpointIdentity,
    dut: EndpointIdentity,
    *,
    expected_reference_system_identifier: str,
    expected_dut_system_identifier: str,
    expected_current_user: str,
) -> None:
    if reference.system_identifier != expected_reference_system_identifier:
        raise ValueError(
            "reference system_identifier does not match the immutable execution profile"
        )
    if dut.system_identifier != expected_dut_system_identifier:
        raise ValueError(
            "DUT system_identifier does not match the immutable execution profile"
        )
    if (
        reference.current_user != expected_current_user
        or dut.current_user != expected_current_user
    ):
        raise ValueError(
            "reference/DUT current_user does not match the immutable execution profile"
        )


def _identity_from_mapping(
    raw: Mapping[str, Any],
    target: PsqlTarget,
) -> EndpointIdentity:
    """Parse a durable/session identity without accepting missing target fields."""

    try:
        dangerous_roles = tuple(
            str(role) for role in raw.get("dangerous_role_memberships", ())
        )
        privileged_roles = tuple(
            str(role) for role in raw.get("privileged_role_memberships", ())
        )
        identity = EndpointIdentity(
            target_name=str(raw.get("target_name", target.name)),
            service=str(raw.get("service", target.service)),
            database=str(raw.get("database", target.database)),
            server_version_num=int(raw["server_version_num"]),
            system_identifier=str(raw["system_identifier"]),
            server_address=str(raw["server_address"]),
            server_port=str(raw["server_port"]),
            current_user=str(raw["current_user"]),
            is_superuser=raw["is_superuser"],
            can_createdb=raw["can_createdb"],
            can_createrole=raw["can_createrole"],
            can_replication=raw["can_replication"],
            can_bypassrls=raw["can_bypassrls"],
            dangerous_role_memberships=dangerous_roles,
            privileged_role_memberships=privileged_roles,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"execution session returned malformed identity for {target.name}"
        ) from exc
    if any(
        type(flag) is not bool
        for flag in (
            identity.is_superuser,
            identity.can_createdb,
            identity.can_createrole,
            identity.can_replication,
            identity.can_bypassrls,
        )
    ):
        raise ValueError(
            f"execution session returned malformed privilege identity for {target.name}"
        )
    if (
        identity.target_name != target.name
        or identity.service != target.service
        or identity.database != target.database
    ):
        raise ValueError(
            f"execution session identity target does not match {target.name}"
        )
    validate_endpoint_identity(identity)
    return identity


def _parse_session_identity(
    stdout: str,
    target: PsqlTarget,
) -> tuple[EndpointIdentity, str]:
    """Remove the runner-owned first-row probe and retain SQL stdout exactly."""

    lines = stdout.splitlines(keepends=True)
    marker_indexes = [
        index
        for index, line in enumerate(lines)
        if line.startswith(_SESSION_IDENTITY_SENTINEL)
    ]
    if len(marker_indexes) != 1:
        raise ValueError(
            f"execution session for {target.name} returned "
            f"{len(marker_indexes)} identity rows, expected 1"
        )
    marker_index = marker_indexes[0]
    if any(line.strip() for line in lines[:marker_index]):
        raise ValueError(
            f"execution session for {target.name} emitted output before its identity row"
        )
    identity_line = lines[marker_index].rstrip("\r\n")
    try:
        raw = json.loads(identity_line.removeprefix(_SESSION_IDENTITY_SENTINEL))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(
            f"execution session returned malformed identity JSON for {target.name}"
        ) from exc
    if not isinstance(raw, Mapping):
        raise ValueError(
            f"execution session returned non-object identity for {target.name}"
        )
    dangerous_roles = tuple(
        role
        for role in (
            "pg_read_server_files",
            "pg_write_server_files",
            "pg_execute_server_program",
        )
        if raw.get(role) is True
    )
    for role in (
        "pg_read_server_files",
        "pg_write_server_files",
        "pg_execute_server_program",
    ):
        if type(raw.get(role)) is not bool:
            raise ValueError(
                f"execution session returned malformed role membership for {target.name}"
            )
    privileged_roles = raw.get("privileged_role_memberships")
    if (
        not isinstance(privileged_roles, list)
        or any(not isinstance(role, str) for role in privileged_roles)
    ):
        raise ValueError(
            f"execution session returned malformed privileged role memberships "
            f"for {target.name}"
        )
    for flag in (
        "is_superuser",
        "can_createdb",
        "can_createrole",
        "can_replication",
        "can_bypassrls",
    ):
        if type(raw.get(flag)) is not bool:
            raise ValueError(
                f"execution session returned malformed {flag} for {target.name}"
            )
    identity = _identity_from_mapping(
        {
            **raw,
            "target_name": target.name,
            "service": target.service,
            "database": target.database,
            "dangerous_role_memberships": dangerous_roles,
            "privileged_role_memberships": tuple(privileged_roles),
        },
        target,
    )
    return identity, "".join(lines[marker_index + 1 :])


def _record_identity(
    record: ExecutionRecord,
    target: PsqlTarget,
) -> EndpointIdentity | None:
    if record.endpoint_identity is None:
        return None
    if not isinstance(record.endpoint_identity, Mapping):
        raise ValueError(f"execution record identity for {target.name} must be an object")
    return _identity_from_mapping(record.endpoint_identity, target)


def _require_stable_identity(
    before: EndpointIdentity,
    after: EndpointIdentity,
    *,
    require_basic_privileges: bool,
) -> None:
    validate_endpoint_identity(after)
    if require_basic_privileges:
        validate_basic_endpoint_identity(after)
    if before != after:
        raise ValueError(
            f"{before.target_name} endpoint identity changed between preflight and postflight"
        )


@dataclass(frozen=True)
class ExecutionRecord:
    target_name: str
    sql_file: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    endpoint_identity: dict[str, Any] | None = None
    sql_sha256: str | None = None
    execution_profile_sha256: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DifferentialExecutionResult:
    reference: ExecutionRecord
    dut: ExecutionRecord
    comparison: DifferentialResult
    expected_outcome: str | None = None
    expected_sqlstate: str | None = None
    reference_oracle_valid: bool = True
    reference_oracle_error: str | None = None
    execution_profile_sha256: str | None = None
    reference_replay: ExecutionRecord | None = None
    dut_replay: ExecutionRecord | None = None
    reference_determinism: Mapping[str, Any] | None = None
    dut_determinism: Mapping[str, Any] | None = None

    @property
    def passed(self) -> bool:
        replay_deterministic = (
            self.reference_determinism is None
            and self.dut_determinism is None
        ) or (
            self.reference_determinism is not None
            and self.dut_determinism is not None
            and self.reference_determinism.get("deterministic") is True
            and self.dut_determinism.get("deterministic") is True
        )
        return (
            self.reference_oracle_valid
            and self.comparison.identical
            and replay_deterministic
        )

    def to_dict(self) -> dict:
        return {
            "reference": self.reference.to_dict(),
            "dut": self.dut.to_dict(),
            "comparison": self.comparison.to_dict(),
            "expected_outcome": self.expected_outcome,
            "expected_sqlstate": self.expected_sqlstate,
            "reference_oracle_valid": self.reference_oracle_valid,
            "reference_oracle_error": self.reference_oracle_error,
            "execution_profile_sha256": self.execution_profile_sha256,
            "reference_replay": (
                self.reference_replay.to_dict()
                if self.reference_replay is not None
                else None
            ),
            "dut_replay": (
                self.dut_replay.to_dict() if self.dut_replay is not None else None
            ),
            "reference_determinism": (
                dict(self.reference_determinism)
                if self.reference_determinism is not None
                else None
            ),
            "dut_determinism": (
                dict(self.dut_determinism)
                if self.dut_determinism is not None
                else None
            ),
            "passed": self.passed,
        }


def attach_two_run_replay(
    first: DifferentialExecutionResult,
    replay: DifferentialExecutionResult,
) -> DifferentialExecutionResult:
    """Bind an independently executed replay and exact per-endpoint reports."""

    if (
        first.execution_profile_sha256 != replay.execution_profile_sha256
        or first.expected_outcome != replay.expected_outcome
        or first.expected_sqlstate != replay.expected_sqlstate
    ):
        raise ValueError("replay differential settings differ from the first run")
    for side, primary, repeated in (
        ("reference", first.reference, replay.reference),
        ("dut", first.dut, replay.dut),
    ):
        if (
            primary.target_name != repeated.target_name
            or primary.sql_file != repeated.sql_file
            or primary.sql_sha256 != repeated.sql_sha256
            or primary.execution_profile_sha256
            != repeated.execution_profile_sha256
            or primary.endpoint_identity != repeated.endpoint_identity
        ):
            raise ValueError(f"{side} replay identity/SQL/profile binding changed")

    def report(primary: ExecutionRecord, repeated: ExecutionRecord) -> dict[str, Any]:
        return compare_two_run_transcripts(
            ExecutionTranscript(
                primary.returncode,
                primary.stdout.encode("utf-8"),
                primary.stderr.encode("utf-8"),
            ),
            ExecutionTranscript(
                repeated.returncode,
                repeated.stdout.encode("utf-8"),
                repeated.stderr.encode("utf-8"),
            ),
        ).to_dict()

    return replace(
        first,
        reference_replay=replay.reference,
        dut_replay=replay.dut,
        reference_determinism=report(first.reference, replay.reference),
        dut_determinism=report(first.dut, replay.dut),
    )


@dataclass(frozen=True)
class DifferentialArtifactReservation:
    """An exclusive case-id reservation held across execution and publication."""

    run_root: Path
    case_id: str
    paths: Mapping[str, Path]
    overwrite: bool


def normalize_output(content: str, profile: NormalizationProfile | None = None) -> str:
    selected = profile or NormalizationProfile()
    drop_patterns = tuple(re.compile(pattern) for pattern in selected.drop_line_patterns)
    output: list[str] = []
    canonical_newlines = content.replace("\r\n", "\n").replace("\r", "\n")
    for raw_line in canonical_newlines.splitlines(keepends=True):
        has_newline = raw_line.endswith("\n")
        line = raw_line[:-1] if has_newline else raw_line
        if any(pattern.search(line) for pattern in drop_patterns):
            continue
        normalized = line.rstrip() if selected.strip_trailing_whitespace else line
        for pattern, replacement in selected.replacements:
            normalized = re.sub(pattern, replacement, normalized)
        output.append(normalized + ("\n" if has_newline else ""))
    return "".join(output)


def compare_outputs(
    reference_output: str,
    dut_output: str,
    profile: NormalizationProfile | None = None,
) -> DifferentialResult:
    selected_profile = profile or NormalizationProfile()
    normalized_reference = normalize_output(reference_output, selected_profile)
    normalized_dut = normalize_output(dut_output, selected_profile)
    return _compare_normalized(
        normalized_reference,
        normalized_dut,
        selected_profile,
    )


def _compare_normalized(
    normalized_reference: str,
    normalized_dut: str,
    profile: NormalizationProfile,
) -> DifferentialResult:
    diff = "".join(
        difflib.unified_diff(
            normalized_reference.splitlines(keepends=True),
            normalized_dut.splitlines(keepends=True),
            fromfile="reference",
            tofile="dut",
        )
    )
    return DifferentialResult(
        identical=normalized_reference == normalized_dut,
        reference_sha256=hashlib.sha256(normalized_reference.encode("utf-8")).hexdigest(),
        dut_sha256=hashlib.sha256(normalized_dut.encode("utf-8")).hexdigest(),
        normalized_reference=normalized_reference,
        normalized_dut=normalized_dut,
        unified_diff=diff,
        normalization_profile=asdict(profile),
    )


def compare_execution_records(
    reference: ExecutionRecord,
    dut: ExecutionRecord,
    profile: NormalizationProfile | None = None,
) -> DifferentialResult:
    """Compare execution structure while normalizing only stream contents.

    Return codes and stdout/stderr boundaries are added after normalization, so
    a user-supplied regular expression cannot erase structural differences.
    """

    selected = profile or NormalizationProfile()

    def transcript(record: ExecutionRecord) -> str:
        stdout = normalize_output(record.stdout, selected)
        stderr = normalize_output(record.stderr, selected)
        return _structured_transcript(record.returncode, stdout, stderr)

    return _compare_normalized(transcript(reference), transcript(dut), selected)


def observable_transcript(record: ExecutionRecord) -> str:
    """Serialize all stable, user-visible execution outcomes for comparison."""

    return _structured_transcript(record.returncode, record.stdout, record.stderr)


def _structured_transcript(returncode: int, stdout: str, stderr: str) -> str:
    """Encode streams injectively while keeping their contents readable.

    Lengths are added after optional content normalization.  They preserve a
    missing final newline and prevent stream data that resembles a delimiter
    from shifting the stdout/stderr boundary.
    """

    return (
        f"returncode: {returncode}\n"
        f"stdout_utf8_bytes: {len(stdout.encode('utf-8'))}\n"
        f"stderr_utf8_bytes: {len(stderr.encode('utf-8'))}\n"
        "--- stdout ---\n"
        f"{stdout}"
        "--- stderr ---\n"
        f"{stderr}"
    )


def parse_verbose_terminal_diagnostics(
    stderr: str,
) -> tuple[tuple[str, str], ...]:
    """Extract psql verbose terminal diagnostics as ``(severity, SQLSTATE)``.

    Only server termination severities are accepted.  NOTICE and WARNING rows
    deliberately do not participate in the outcome oracle, even when their
    message text contains a five-character SQLSTATE.  Callers must require
    exactly one result for a formal stop-on-error execution; doing so also
    rejects a message that tries to inject a second error-looking line.
    """

    if not isinstance(stderr, str):
        raise ValueError("execution stderr must be a string")
    return tuple(
        (match.group("severity"), match.group("sqlstate"))
        for match in _VERBOSE_TERMINAL_DIAGNOSTIC_PATTERN.finditer(stderr)
    )


def validate_expected_failure_oracle(
    returncode: int,
    stderr: str,
    expected_sqlstate: str,
) -> tuple[bool, str | None]:
    """Validate the one terminating server diagnostic for an expected failure."""

    if (
        not isinstance(expected_sqlstate, str)
        or re.fullmatch(r"[0-9A-Z]{5}", expected_sqlstate) is None
    ):
        raise ValueError(
            "expected_failure differential execution requires a five-character SQLSTATE"
        )
    if returncode == 0:
        return (
            False,
            "reference execution succeeded although the case outcome is expected_failure",
        )
    diagnostics = parse_verbose_terminal_diagnostics(stderr)
    if len(diagnostics) != 1:
        return (
            False,
            "reference execution must contain exactly one verbose terminal "
            f"ERROR/FATAL/PANIC SQLSTATE; found {len(diagnostics)}, expected "
            f"{expected_sqlstate}",
        )
    severity, actual_sqlstate = diagnostics[0]
    if actual_sqlstate != expected_sqlstate:
        return (
            False,
            f"reference execution terminated with {severity} SQLSTATE "
            f"{actual_sqlstate}, expected {expected_sqlstate}",
        )
    return True, None


def execute_differential(
    sql_path: str | Path,
    reference_target: PsqlTarget,
    dut_target: PsqlTarget,
    *,
    runner: Any | None = None,
    profile: NormalizationProfile | None = None,
    stop_on_error: bool = True,
    expected_outcome: str | None = None,
    expected_sqlstate: str | None = None,
    expected_sql_sha256: str | None = None,
    execution_profile: str = "basic_psql",
    execution_profile_sha256: str | None = None,
    expected_reference_system_identifier: str | None = None,
    expected_dut_system_identifier: str | None = None,
    expected_current_user: str | None = None,
) -> DifferentialExecutionResult:
    """Execute the same SQL on upstream and DUT, then compare every outcome."""

    if execution_profile not in {"basic_psql", "external_isolated"}:
        raise ValueError("execution_profile must be basic_psql or external_isolated")
    require_basic_privileges = execution_profile == "basic_psql"
    if execution_profile_sha256 is not None and (
        not isinstance(execution_profile_sha256, str)
        or EXECUTION_PROFILE_SHA256_PATTERN.fullmatch(execution_profile_sha256) is None
    ):
        raise ValueError(
            "execution profile SHA256 must be null or 64 lowercase hex characters"
        )
    anchor_values = (
        expected_reference_system_identifier,
        expected_dut_system_identifier,
        expected_current_user,
    )
    if any(value is not None for value in anchor_values) and not all(
        value is not None for value in anchor_values
    ):
        raise ValueError("execution profile identity anchors must be supplied together")
    identity_anchors_bound = expected_current_user is not None
    if identity_anchors_bound:
        assert expected_reference_system_identifier is not None
        assert expected_dut_system_identifier is not None
        if (
            re.fullmatch(r"[1-9][0-9]*", expected_reference_system_identifier)
            is None
            or re.fullmatch(r"[1-9][0-9]*", expected_dut_system_identifier)
            is None
            or expected_reference_system_identifier
            == expected_dut_system_identifier
            or not isinstance(expected_current_user, str)
            or not expected_current_user
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in expected_current_user
            )
        ):
            raise ValueError("execution profile identity anchors are invalid")
    if (
        reference_target.service == dut_target.service
        and reference_target.database == dut_target.database
    ):
        raise ValueError("reference and DUT must not use the same service/database")
    selected_runner = runner or PsqlRunner()
    run_content = getattr(selected_runner, "run_content", None)
    snapshot_path: Path | None = None
    sql_content: str | None = None
    sql_sha256: str | None = None
    if expected_sql_sha256 is not None and (
        not isinstance(expected_sql_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected_sql_sha256) is None
    ):
        raise ValueError("expected SQL SHA256 must be 64 lowercase hex characters")
    if callable(run_content) or expected_sql_sha256 is not None:
        snapshot_path = Path(sql_path).resolve(strict=True)
        if not snapshot_path.is_file():
            raise FileNotFoundError(snapshot_path)
        try:
            sql_bytes = snapshot_path.read_bytes()
            sql_content = sql_bytes.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError(f"SQL file must be valid UTF-8: {snapshot_path}") from exc
        if require_basic_privileges:
            validate_sql_for_basic_runner(sql_content)
        sql_sha256 = hashlib.sha256(sql_bytes).hexdigest()
        if (
            expected_sql_sha256 is not None
            and sql_sha256 != expected_sql_sha256
        ):
            raise ValueError(
                "immutable SQL snapshot SHA256 mismatch: "
                f"declared {expected_sql_sha256}, actual {sql_sha256}"
            )

    # Snapshot and hash validation intentionally happen before endpoint
    # inspection: preflight is already a database call.
    reference_identity = None
    dut_identity = None
    inspect = getattr(selected_runner, "inspect", None)
    if callable(inspect):
        reference_identity = inspect(reference_target)
        dut_identity = inspect(dut_target)
        validate_comparable_endpoint_pair(
            reference_identity,
            dut_identity,
            require_basic_privileges=require_basic_privileges,
        )
        if identity_anchors_bound:
            _validate_endpoint_pair_anchors(
                reference_identity,
                dut_identity,
                expected_reference_system_identifier=(
                    expected_reference_system_identifier
                ),
                expected_dut_system_identifier=expected_dut_system_identifier,
                expected_current_user=expected_current_user,
            )
    if callable(run_content):
        assert snapshot_path is not None and sql_content is not None
        reference = run_content(
            sql_content,
            snapshot_path,
            reference_target,
            stop_on_error=stop_on_error,
        )
        dut = run_content(
            sql_content,
            snapshot_path,
            dut_target,
            stop_on_error=stop_on_error,
        )
    else:
        # Custom runners are trusted adapters used by tests/external harnesses.
        # The built-in PsqlRunner always takes the immutable-content branch.
        reference = selected_runner.run(
            sql_path,
            reference_target,
            stop_on_error=stop_on_error,
        )
        dut = selected_runner.run(
            sql_path,
            dut_target,
            stop_on_error=stop_on_error,
        )
    if sql_sha256 is not None:
        for side, record in (("reference", reference), ("dut", dut)):
            if record.sql_sha256 not in (None, sql_sha256):
                raise ValueError(
                    f"{side} execution record contains a conflicting SQL SHA256"
                )
        reference = replace(reference, sql_sha256=sql_sha256)
        dut = replace(dut, sql_sha256=sql_sha256)
    if callable(inspect):
        _require_stable_identity(
            reference_identity,
            inspect(reference_target),
            require_basic_privileges=require_basic_privileges,
        )
        _require_stable_identity(
            dut_identity,
            inspect(dut_target),
            require_basic_privileges=require_basic_privileges,
        )
    session_reference_identity = _record_identity(reference, reference_target)
    session_dut_identity = _record_identity(dut, dut_target)
    if reference_identity is not None and session_reference_identity is not None:
        if reference_identity != session_reference_identity:
            raise ValueError(
                "reference execution-session identity differs from endpoint preflight"
            )
    if dut_identity is not None and session_dut_identity is not None:
        if dut_identity != session_dut_identity:
            raise ValueError("DUT execution-session identity differs from endpoint preflight")
    effective_reference_identity = session_reference_identity or reference_identity
    effective_dut_identity = session_dut_identity or dut_identity
    if (
        effective_reference_identity is not None
        and effective_dut_identity is not None
    ):
        validate_comparable_endpoint_pair(
            effective_reference_identity,
            effective_dut_identity,
            require_basic_privileges=require_basic_privileges,
        )
        if identity_anchors_bound:
            _validate_endpoint_pair_anchors(
                effective_reference_identity,
                effective_dut_identity,
                expected_reference_system_identifier=(
                    expected_reference_system_identifier
                ),
                expected_dut_system_identifier=expected_dut_system_identifier,
                expected_current_user=expected_current_user,
            )
    elif identity_anchors_bound:
        raise ValueError(
            "execution profile identity anchors require both endpoint identities"
        )
    if effective_reference_identity is not None:
        reference = replace(
            reference,
            endpoint_identity=effective_reference_identity.to_dict(),
        )
    if effective_dut_identity is not None:
        dut = replace(dut, endpoint_identity=effective_dut_identity.to_dict())
    for side, record in (("reference", reference), ("dut", dut)):
        if record.execution_profile_sha256 not in (
            None,
            execution_profile_sha256,
        ):
            raise ValueError(
                f"{side} execution record contains a conflicting execution profile SHA256"
            )
    reference = replace(
        reference,
        execution_profile_sha256=execution_profile_sha256,
    )
    dut = replace(
        dut,
        execution_profile_sha256=execution_profile_sha256,
    )
    comparison = compare_execution_records(reference, dut, profile)
    oracle_valid = True
    oracle_error = None
    if expected_outcome is not None:
        if expected_outcome == "success":
            oracle_valid = reference.returncode == 0
            if not oracle_valid:
                oracle_error = (
                    "reference execution failed although the case outcome is success"
                )
        elif expected_outcome == "expected_failure":
            oracle_valid, oracle_error = validate_expected_failure_oracle(
                reference.returncode,
                reference.stderr,
                expected_sqlstate,
            )
        else:
            raise ValueError(
                "expected_outcome must be success or expected_failure when supplied"
            )
    return DifferentialExecutionResult(
        reference,
        dut,
        comparison,
        expected_outcome=expected_outcome,
        expected_sqlstate=expected_sqlstate,
        reference_oracle_valid=oracle_valid,
        reference_oracle_error=oracle_error,
        execution_profile_sha256=execution_profile_sha256,
    )


def _differential_artifact_paths(root: Path, case_id: str) -> dict[str, Path]:
    reference_root = ensure_contained_directory(root, "executions/reference")
    dut_root = ensure_contained_directory(root, "executions/dut")
    comparison_root = ensure_contained_directory(root, "comparisons")
    return {
        "reference_record": reference_root / f"{case_id}.json",
        "reference_stdout": reference_root / f"{case_id}.stdout",
        "reference_stderr": reference_root / f"{case_id}.stderr",
        "reference_replay_record": reference_root / f"{case_id}.replay.json",
        "reference_replay_stdout": reference_root / f"{case_id}.replay.stdout",
        "reference_replay_stderr": reference_root / f"{case_id}.replay.stderr",
        "dut_record": dut_root / f"{case_id}.json",
        "dut_stdout": dut_root / f"{case_id}.stdout",
        "dut_stderr": dut_root / f"{case_id}.stderr",
        "dut_replay_record": dut_root / f"{case_id}.replay.json",
        "dut_replay_stdout": dut_root / f"{case_id}.replay.stdout",
        "dut_replay_stderr": dut_root / f"{case_id}.replay.stderr",
        # This file is the completion marker and must be published last.
        "comparison": comparison_root / f"{case_id}.json",
        "diff": comparison_root / f"{case_id}.diff",
    }


@contextmanager
def reserve_differential_artifacts(
    run_root: str | Path,
    case_id: str,
    *,
    overwrite: bool = False,
) -> Iterator[DifferentialArtifactReservation]:
    """Lock and reserve a case before either database receives its SQL.

    A comparison JSON is the completion marker.  If a prior process crashed
    before publishing that marker, the next lock holder may safely repair the
    known partial files.  A completed case requires explicit ``overwrite``.
    """

    if not CASE_ID_PATTERN.fullmatch(case_id):
        raise ValueError(f"invalid case_id: {case_id!r}")
    root_candidate = Path(run_root)
    if root_candidate.is_symlink():
        raise ValueError(f"run_root must not be a symbolic link: {root_candidate}")
    root = root_candidate.resolve(strict=True)
    manifest = root / "run.json"
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError(f"run_root has no run.json: {root}")
    load_run_manifest(root)
    paths = _differential_artifact_paths(root, case_id)
    locks_root = ensure_contained_directory(root, "comparisons/.locks")
    lock_path = locks_root / f"{case_id}.lock"
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            if paths["comparison"].exists() and not overwrite:
                raise FileExistsError(
                    "completed differential artifacts already exist; use explicit overwrite: "
                    + str(paths["comparison"])
                )
            if overwrite and paths["comparison"].exists():
                # Remove the old completion marker before execution.  A crash
                # can then leave only an honestly incomplete artifact set.
                paths["comparison"].unlink()
            yield DifferentialArtifactReservation(
                run_root=root,
                case_id=case_id,
                paths=paths,
                overwrite=overwrite,
            )
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _publish_differential_artifacts(
    reservation: DifferentialArtifactReservation,
    result: DifferentialExecutionResult,
) -> dict[str, Path]:
    run_manifest = load_run_manifest(reservation.run_root)
    expected_profile_digest = run_manifest["metadata"]["execution_profile_sha256"]
    formal_run = run_manifest["metadata"].get("formal_run") is True
    if formal_run and (
        result.reference_replay is None
        or result.dut_replay is None
        or result.reference_determinism is None
        or result.dut_determinism is None
    ):
        raise ValueError("formal differential result requires two-run replay evidence")
    if (
        result.execution_profile_sha256 != expected_profile_digest
        or result.reference.execution_profile_sha256 != expected_profile_digest
        or result.dut.execution_profile_sha256 != expected_profile_digest
    ):
        raise ValueError(
            "differential result execution_profile_sha256 does not match the run"
        )
    run_profile = load_run_execution_profile(reservation.run_root)
    if run_profile is not None:
        identities: list[EndpointIdentity] = []
        for side, record, endpoint in (
            ("reference", result.reference, run_profile.reference),
            ("dut", result.dut, run_profile.dut),
        ):
            identity = _record_identity(
                record,
                PsqlTarget(side, endpoint.service, endpoint.database),
            )
            if identity is None:
                raise ValueError(
                    f"{side} execution is missing its profile-bound endpoint identity"
                )
            if (
                identity.system_identifier != endpoint.expected_system_identifier
                or identity.current_user != endpoint.expected_current_user
            ):
                raise ValueError(
                    f"{side} execution identity does not match the run profile anchor"
                )
            identities.append(identity)
        validate_comparable_endpoint_pair(identities[0], identities[1])
    paths = dict(reservation.paths)
    staging_parent = ensure_contained_directory(
        reservation.run_root,
        "comparisons/.staging",
    )
    staging_root = Path(
        tempfile.mkdtemp(prefix=f"{reservation.case_id}.", dir=staging_parent)
    )
    staged = {key: staging_root / key for key in paths}
    try:
        write_json(staged["reference_record"], result.reference.to_dict())
        write_text(staged["reference_stdout"], result.reference.stdout)
        write_text(staged["reference_stderr"], result.reference.stderr)
        if result.reference_replay is not None:
            write_json(
                staged["reference_replay_record"],
                result.reference_replay.to_dict(),
            )
            write_text(
                staged["reference_replay_stdout"], result.reference_replay.stdout
            )
            write_text(
                staged["reference_replay_stderr"], result.reference_replay.stderr
            )
        write_json(staged["dut_record"], result.dut.to_dict())
        write_text(staged["dut_stdout"], result.dut.stdout)
        write_text(staged["dut_stderr"], result.dut.stderr)
        if result.dut_replay is not None:
            write_json(staged["dut_replay_record"], result.dut_replay.to_dict())
            write_text(staged["dut_replay_stdout"], result.dut_replay.stdout)
            write_text(staged["dut_replay_stderr"], result.dut_replay.stderr)
        write_text(staged["diff"], result.comparison.unified_diff)
        write_json(staged["comparison"], result.to_dict())
        publish_order = tuple(
            key
            for key in paths
            if key != "comparison" and staged[key].exists()
        ) + (
            "comparison",
        )
        for key in publish_order:
            os.replace(staged[key], paths[key])
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    return paths


def write_differential_artifacts(
    run_root: str | Path,
    case_id: str,
    result: DifferentialExecutionResult,
    *,
    overwrite: bool = False,
    reservation: DifferentialArtifactReservation | None = None,
) -> dict[str, Path]:
    """Atomically publish a result, using comparison JSON as the final marker."""

    if reservation is not None:
        root = Path(run_root).resolve(strict=True)
        if reservation.run_root != root or reservation.case_id != case_id:
            raise ValueError("differential reservation does not match run_root/case_id")
        return _publish_differential_artifacts(reservation, result)
    with reserve_differential_artifacts(
        run_root,
        case_id,
        overwrite=overwrite,
    ) as acquired:
        return _publish_differential_artifacts(acquired, result)


class PsqlRunner:
    def __init__(self, executable: str = "psql", timeout_seconds: int = 300) -> None:
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def _resolved_executable(self) -> str:
        executable = self.executable
        if Path(executable).is_absolute():
            return executable
        resolved = shutil.which(executable)
        if resolved is None:
            raise FileNotFoundError(f"psql executable not found: {executable}")
        return resolved

    def _environment(self, target: PsqlTarget) -> dict[str, str]:
        allowed_environment = (
            "HOME",
            "PATH",
            "TMPDIR",
            "PGSERVICEFILE",
            "PGPASSFILE",
            "PGSYSCONFDIR",
            "PGSSLROOTCERT",
            "PGSSLCERT",
            "PGSSLKEY",
            "PGSSLCRL",
            "PGSSLCRLDIR",
            "PGCONNECT_TIMEOUT",
        )
        environment = {
            key: os.environ[key]
            for key in allowed_environment
            if key in os.environ
        }
        environment["PGSERVICE"] = target.service
        environment["PGAPPNAME"] = "pg-case"
        environment["PG_COLOR"] = "never"
        environment["PGCLIENTENCODING"] = "UTF8"
        environment["LC_ALL"] = "C"
        return environment

    def inspect(self, target: PsqlTarget) -> EndpointIdentity:
        """Verify version and collect a non-secret endpoint fingerprint."""

        query = (
            "SELECT pg_catalog.current_setting('server_version_num'), "
            "control.system_identifier::text, "
            "COALESCE(pg_catalog.inet_server_addr()::text, 'local'), "
            "COALESCE(pg_catalog.inet_server_port()::text, ''), "
            "CURRENT_USER::text, roles.rolsuper::text, "
            "roles.rolcreatedb::text, roles.rolcreaterole::text, "
            "roles.rolreplication::text, roles.rolbypassrls::text, "
            "pg_catalog.pg_has_role(CURRENT_USER, 'pg_read_server_files', 'MEMBER')::text, "
            "pg_catalog.pg_has_role(CURRENT_USER, 'pg_write_server_files', 'MEMBER')::text, "
            "pg_catalog.pg_has_role(CURRENT_USER, 'pg_execute_server_program', 'MEMBER')::text, "
            "pg_catalog.array_to_json(ARRAY("
            "SELECT candidate.rolname FROM pg_catalog.pg_roles AS candidate "
            "WHERE candidate.rolname <> CURRENT_USER "
            "AND pg_catalog.pg_has_role(CURRENT_USER, candidate.oid, 'MEMBER') "
            "AND (candidate.rolsuper OR candidate.rolcreatedb OR candidate.rolcreaterole "
            "OR candidate.rolreplication OR candidate.rolbypassrls) "
            "ORDER BY candidate.rolname))::text "
            "FROM pg_catalog.pg_control_system() AS control "
            "JOIN pg_catalog.pg_roles AS roles ON roles.rolname = CURRENT_USER;"
        )
        completed = subprocess.run(
            [
                self._resolved_executable(),
                "-X",
                "--no-psqlrc",
                "--tuples-only",
                "--no-align",
                "--field-separator",
                "\t",
                "-d",
                target.database,
                "--command",
                query,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout_seconds,
            env=self._environment(target),
        )
        if completed.returncode != 0:
            raise ValueError(
                f"endpoint preflight failed for {target.name}: "
                f"{(completed.stderr or completed.stdout or '').strip()}"
            )
        lines = [line for line in (completed.stdout or "").splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError(
                f"endpoint preflight for {target.name} returned {len(lines)} rows, expected 1"
            )
        columns = lines[0].split("\t")
        if (
            len(columns) != 14
            or not columns[0].isdigit()
            or any(value not in ("t", "f") for value in columns[5:13])
        ):
            raise ValueError(f"endpoint preflight returned malformed identity for {target.name}")
        dangerous_roles = tuple(
            role
            for role, enabled in zip(
                (
                    "pg_read_server_files",
                    "pg_write_server_files",
                    "pg_execute_server_program",
                ),
                columns[10:13],
            )
            if enabled == "t"
        )
        try:
            privileged_roles_raw = json.loads(columns[13])
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"endpoint preflight returned malformed privileged role memberships "
                f"for {target.name}"
            ) from exc
        if not isinstance(privileged_roles_raw, list) or any(
            not isinstance(role, str) for role in privileged_roles_raw
        ):
            raise ValueError(
                f"endpoint preflight returned malformed privileged role memberships "
                f"for {target.name}"
            )
        identity = EndpointIdentity(
            target_name=target.name,
            service=target.service,
            database=target.database,
            server_version_num=int(columns[0]),
            system_identifier=columns[1],
            server_address=columns[2],
            server_port=columns[3],
            current_user=columns[4],
            is_superuser=columns[5] == "t",
            can_createdb=columns[6] == "t",
            can_createrole=columns[7] == "t",
            can_replication=columns[8] == "t",
            can_bypassrls=columns[9] == "t",
            dangerous_role_memberships=dangerous_roles,
            privileged_role_memberships=tuple(privileged_roles_raw),
        )
        validate_basic_endpoint_identity(identity)
        return identity

    def run(
        self,
        sql_path: str | Path,
        target: PsqlTarget,
        *,
        stop_on_error: bool = True,
    ) -> ExecutionRecord:
        path = Path(sql_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        try:
            sql_content = path.read_bytes().decode("utf-8")
        except UnicodeError as exc:
            raise ValueError(f"SQL file must be valid UTF-8: {path}") from exc
        validate_sql_for_basic_runner(sql_content)
        return self.run_content(
            sql_content,
            path,
            target,
            stop_on_error=stop_on_error,
        )

    def run_content(
        self,
        sql_content: str,
        sql_label: str | Path,
        target: PsqlTarget,
        *,
        stop_on_error: bool = True,
    ) -> ExecutionRecord:
        """Execute already-validated immutable SQL bytes through psql stdin."""

        validate_sql_for_basic_runner(sql_content)
        path = Path(sql_label).resolve()
        command = [
            self._resolved_executable(),
            "-X",
            "--no-psqlrc",
            "--pset",
            "pager=off",
            "--set",
            f"ON_ERROR_STOP={1 if stop_on_error else 0}",
            "--set",
            "VERBOSITY=verbose",
            "-d",
            target.database,
            "-f",
            "-",
        ]
        wrapped_sql = (
            "\\set QUIET 1\n"
            "\\pset format unaligned\n"
            "\\pset tuples_only on\n"
            f"{_session_identity_query()}\n"
            "\\pset format aligned\n"
            "\\pset tuples_only off\n"
            "\\unset QUIET\n"
            f"{sql_content}"
        )
        # Pass a minimal environment.  In particular, never expose arbitrary
        # host secrets or PGPASSWORD to generated SQL through psql.  Authentication
        # remains external via a service file and .pgpass/PGPASSFILE.
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=wrapped_sql,
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout_seconds,
            env=self._environment(target),
        )
        session_identity, user_stdout = _parse_session_identity(
            completed.stdout or "",
            target,
        )
        validate_basic_endpoint_identity(session_identity)
        return ExecutionRecord(
            target_name=target.name,
            sql_file=str(path),
            returncode=int(completed.returncode),
            stdout=user_stdout,
            stderr=completed.stderr or "",
            duration_seconds=time.monotonic() - started,
            endpoint_identity=session_identity.to_dict(),
            sql_sha256=hashlib.sha256(sql_content.encode("utf-8")).hexdigest(),
        )
