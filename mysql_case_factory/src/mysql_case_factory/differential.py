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
EXPECTED_SERVER_VERSION_NUM = 80022
EXECUTION_PROFILE_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SESSION_IDENTITY_SENTINEL = "__MYSQL_CASE_FACTORY_ENDPOINT_V1__"
_VERBOSE_TERMINAL_DIAGNOSTIC_PATTERN = re.compile(
    r"(?m)^(?P<severity>ERROR)[ \t]+[0-9]+[ \t]+"
    r"\((?P<sqlstate>[0-9A-Z]{5})\)(?:[ \t]+at[ \t]+line[ \t]+[0-9]+)?:"
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



_MYSQL_VERSION_PATTERN = re.compile(r"^8\.0\.(?P<patch>[0-9]{1,2})(?:[-+][^\r\n]+)?$")
_MYSQL_SERVER_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_DANGEROUS_GLOBAL_PRIVILEGES = frozenset(
    {
        "BACKUP_ADMIN",
        "BINLOG_ADMIN",
        "BINLOG_ENCRYPTION_ADMIN",
        "CLONE_ADMIN",
        "CONNECTION_ADMIN",
        "CREATE USER",
        "ENCRYPTION_KEY_ADMIN",
        "FILE",
        "GRANT OPTION",
        "GROUP_REPLICATION_ADMIN",
        "INNODB_REDO_LOG_ARCHIVE",
        "INNODB_REDO_LOG_ENABLE",
        "PERSIST_RO_VARIABLES_ADMIN",
        "PROCESS",
        "RELOAD",
        "REPLICATION_APPLIER",
        "REPLICATION CLIENT",
        "REPLICATION_SLAVE_ADMIN",
        "REPLICATION SLAVE",
        "RESOURCE_GROUP_ADMIN",
        "RESOURCE_GROUP_USER",
        "ROLE_ADMIN",
        "SESSION_VARIABLES_ADMIN",
        "SET_USER_ID",
        "SHUTDOWN",
        "SUPER",
        "SYSTEM_USER",
        "SYSTEM_VARIABLES_ADMIN",
        "TABLE_ENCRYPTION_ADMIN",
        "XA_RECOVER_ADMIN",
    }
)


def parse_mysql_version_num(version: str) -> int:
    if not isinstance(version, str):
        raise ValueError("server version must be a MySQL 8.0 patch string")
    match = _MYSQL_VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError(f"server version must be a MySQL 8.0 patch string: {version!r}")
    return 80000 + int(match.group("patch"))


@dataclass(frozen=True)
class MysqlTarget:
    name: str
    login_path: str
    database: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", self.name or ""):
            raise ValueError("target name must be a non-empty token")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", self.login_path or ""):
            raise ValueError("login_path must be a bare mysql_config_editor name")
        lowered = (self.database or "").lower()
        if (
            not re.fullmatch(r"[A-Za-z0-9_$.-]+", self.database or "")
            or lowered.startswith("mysql://")
            or "=" in self.database
        ):
            raise ValueError("database must be a bare database name")


PsqlTarget = MysqlTarget


@dataclass(frozen=True)
class EndpointIdentity:
    target_name: str
    login_path: str
    database: str
    server_version: str
    server_version_num: int
    server_uuid: str
    server_hostname: str
    server_port: int
    current_user: str
    version_comment: str
    granted_global_privileges: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        document = asdict(self)
        document["granted_global_privileges"] = list(self.granted_global_privileges)
        return document


def validate_endpoint_identity(
    identity: EndpointIdentity,
    *,
    expected_version_num: int | None = None,
) -> None:
    for field_name in (
        "target_name",
        "login_path",
        "database",
        "server_version",
        "server_uuid",
        "server_hostname",
        "current_user",
        "version_comment",
    ):
        value = getattr(identity, field_name)
        if not isinstance(value, str) or not value or any(
            ord(character) < 32 or ord(character) == 127 for character in value
        ):
            raise ValueError(f"endpoint identity {field_name} must be a non-empty safe string")
    parsed_version = parse_mysql_version_num(identity.server_version)
    if type(identity.server_version_num) is not int or identity.server_version_num != parsed_version:
        raise ValueError("endpoint server_version_num does not match server_version")
    if expected_version_num is not None and identity.server_version_num != expected_version_num:
        raise ValueError(
            f"{identity.target_name} reports server_version_num={identity.server_version_num}, "
            f"expected {expected_version_num}"
        )
    if _MYSQL_SERVER_UUID_PATTERN.fullmatch(identity.server_uuid) is None:
        raise ValueError(f"{identity.target_name} returned an invalid MySQL server UUID")
    if type(identity.server_port) is not int or not 1 <= identity.server_port <= 65535:
        raise ValueError(f"{identity.target_name} returned an invalid MySQL server port")
    privileges = identity.granted_global_privileges
    if (
        not isinstance(privileges, tuple)
        or any(not isinstance(item, str) or not item for item in privileges)
        or tuple(sorted(set(privileges))) != privileges
    ):
        raise ValueError(f"{identity.target_name} returned invalid global privileges")


def validate_basic_endpoint_identity(
    identity: EndpointIdentity,
    *,
    expected_version_num: int | None = None,
) -> None:
    validate_endpoint_identity(identity, expected_version_num=expected_version_num)
    dangerous = sorted(_DANGEROUS_GLOBAL_PRIVILEGES.intersection(identity.granted_global_privileges))
    if dangerous:
        raise ValueError(
            f"{identity.target_name} basic runner account is over-privileged: "
            + ", ".join(dangerous)
            + "; use an isolated external harness for privileged cases"
        )


def validate_comparable_endpoint_pair(
    reference: EndpointIdentity,
    dut: EndpointIdentity,
    *,
    require_basic_privileges: bool = False,
    expected_version_num: int | None = None,
) -> None:
    validator = validate_basic_endpoint_identity if require_basic_privileges else validate_endpoint_identity
    validator(reference, expected_version_num=expected_version_num)
    validator(dut, expected_version_num=expected_version_num)
    if reference.server_uuid.lower() == dut.server_uuid.lower():
        raise ValueError("reference and DUT resolve to the same MySQL server UUID")
    if reference.database != dut.database:
        raise ValueError("reference and DUT must use the same database name")
    if reference.current_user != dut.current_user:
        raise ValueError("reference and DUT must use the same current_user")


def _identity_from_mapping(raw: Mapping[str, Any], target: MysqlTarget) -> EndpointIdentity:
    try:
        raw_privileges = raw.get("granted_global_privileges", [])
        if not isinstance(raw_privileges, (list, tuple)):
            raise TypeError("global privileges must be a list")
        identity = EndpointIdentity(
            target_name=str(raw.get("target_name", target.name)),
            login_path=str(raw.get("login_path", target.login_path)),
            database=str(raw.get("database", target.database)),
            server_version=str(raw["server_version"]),
            server_version_num=int(raw.get("server_version_num", parse_mysql_version_num(str(raw["server_version"])))),
            server_uuid=str(raw["server_uuid"]),
            server_hostname=str(raw["server_hostname"]),
            server_port=int(raw["server_port"]),
            current_user=str(raw["current_user"]),
            version_comment=str(raw["version_comment"]),
            granted_global_privileges=tuple(sorted(set(str(item) for item in raw_privileges))),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"execution session returned malformed identity for {target.name}") from exc
    if (
        identity.target_name != target.name
        or identity.login_path != target.login_path
        or identity.database != target.database
    ):
        raise ValueError(f"execution session identity target does not match {target.name}")
    validate_endpoint_identity(identity)
    return identity


def _parse_mysql_session_identity(
    stdout: str,
    target: MysqlTarget,
    *,
    expected_version_num: int,
) -> tuple[EndpointIdentity, str]:
    lines = stdout.splitlines(keepends=True)
    indexes = [index for index, line in enumerate(lines) if line.startswith(_SESSION_IDENTITY_SENTINEL)]
    if len(indexes) != 1:
        raise ValueError(f"execution session for {target.name} returned {len(indexes)} identity rows")
    index = indexes[0]
    if any(line.strip() for line in lines[:index]):
        raise ValueError(f"execution session for {target.name} emitted output before identity")
    try:
        raw = json.loads(lines[index].rstrip("\r\n").removeprefix(_SESSION_IDENTITY_SENTINEL))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"execution session returned malformed identity JSON for {target.name}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"execution session returned non-object identity for {target.name}")
    identity = _identity_from_mapping(raw, target)
    validate_basic_endpoint_identity(identity, expected_version_num=expected_version_num)
    return identity, "".join(lines[index + 1 :])


def _record_identity(record: "ExecutionRecord", target: MysqlTarget) -> EndpointIdentity | None:
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
    expected_version_num: int | None = None,
) -> None:
    validator = validate_basic_endpoint_identity if require_basic_privileges else validate_endpoint_identity
    validator(after, expected_version_num=expected_version_num)
    if before != after:
        raise ValueError(f"{before.target_name} endpoint identity changed between preflight and postflight")


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
    """Extract mysql client terminal diagnostics as ``(severity, SQLSTATE)``.

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
            "reference execution must contain exactly one terminal "
            f"MySQL ERROR SQLSTATE; found {len(diagnostics)}, expected "
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
    execution_profile: str = "basic_mysql",
    execution_profile_sha256: str | None = None,
    expected_reference_server_uuid: str | None = None,
    expected_dut_server_uuid: str | None = None,
    expected_current_user: str | None = None,
    expected_version_num: int = 80022,
) -> DifferentialExecutionResult:
    """Execute the same SQL on upstream and DUT, then compare every outcome."""

    if execution_profile not in {"basic_mysql", "external_isolated"}:
        raise ValueError("execution_profile must be basic_mysql or external_isolated")
    require_basic_privileges = execution_profile == "basic_mysql"
    if execution_profile_sha256 is not None and (
        not isinstance(execution_profile_sha256, str)
        or EXECUTION_PROFILE_SHA256_PATTERN.fullmatch(execution_profile_sha256) is None
    ):
        raise ValueError(
            "execution profile SHA256 must be null or 64 lowercase hex characters"
        )
    anchor_values = (
        expected_reference_server_uuid,
        expected_dut_server_uuid,
        expected_current_user,
    )
    if any(value is not None for value in anchor_values) and not all(
        value is not None for value in anchor_values
    ):
        raise ValueError("execution profile identity anchors must be supplied together")
    identity_anchors_bound = expected_current_user is not None
    if identity_anchors_bound:
        assert expected_reference_server_uuid is not None
        assert expected_dut_server_uuid is not None
        if (
            _MYSQL_SERVER_UUID_PATTERN.fullmatch(expected_reference_server_uuid)
            is None
            or _MYSQL_SERVER_UUID_PATTERN.fullmatch(expected_dut_server_uuid)
            is None
            or expected_reference_server_uuid
            == expected_dut_server_uuid
            or not isinstance(expected_current_user, str)
            or not expected_current_user
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in expected_current_user
            )
        ):
            raise ValueError("execution profile identity anchors are invalid")
    if (
        reference_target.login_path == dut_target.login_path
        and reference_target.database == dut_target.database
    ):
        raise ValueError("reference and DUT must not use the same login_path/database")
    if expected_version_num not in {80022, 80041}:
        raise ValueError("expected_version_num must be 80022 or 80041")
    selected_runner = runner or MysqlRunner(expected_version_num=expected_version_num)
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
            expected_version_num=expected_version_num,
        )
        if identity_anchors_bound:
            _validate_endpoint_pair_anchors(
                reference_identity,
                dut_identity,
                expected_reference_server_uuid=(
                    expected_reference_server_uuid
                ),
                expected_dut_server_uuid=expected_dut_server_uuid,
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
            expected_version_num=expected_version_num,
        )
        _require_stable_identity(
            dut_identity,
            inspect(dut_target),
            require_basic_privileges=require_basic_privileges,
            expected_version_num=expected_version_num,
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
            expected_version_num=expected_version_num,
        )
        if identity_anchors_bound:
            _validate_endpoint_pair_anchors(
                effective_reference_identity,
                effective_dut_identity,
                expected_reference_server_uuid=(
                    expected_reference_server_uuid
                ),
                expected_dut_server_uuid=expected_dut_server_uuid,
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
                PsqlTarget(side, endpoint.login_path, endpoint.database),
            )
            if identity is None:
                raise ValueError(
                    f"{side} execution is missing its profile-bound endpoint identity"
                )
            if (
                identity.server_uuid != endpoint.expected_server_uuid
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



def _mysql_global_privileges_expression() -> str:
    return (
        "COALESCE((SELECT JSON_ARRAYAGG(PRIVILEGE_TYPE) "
        "FROM information_schema.USER_PRIVILEGES "
        "WHERE GRANTEE = CONCAT(QUOTE(SUBSTRING_INDEX(CURRENT_USER(), '@', 1)), "
        "'@', QUOTE(SUBSTRING_INDEX(CURRENT_USER(), '@', -1)))), JSON_ARRAY())"
    )


def _session_identity_query() -> str:
    return (
        "SELECT CONCAT('"
        + _SESSION_IDENTITY_SENTINEL
        + "', JSON_OBJECT("
        "'server_version', VERSION(), "
        "'server_uuid', @@server_uuid, "
        "'server_hostname', @@hostname, "
        "'server_port', @@port, "
        "'current_user', CURRENT_USER(), "
        "'version_comment', @@version_comment, "
        "'granted_global_privileges', "
        + _mysql_global_privileges_expression()
        + "));"
    )


class MysqlRunner:
    def __init__(
        self,
        executable: str = "mysql",
        timeout_seconds: int = 300,
        *,
        expected_version_num: int,
    ) -> None:
        if expected_version_num not in {80022, 80041}:
            raise ValueError("expected_version_num must be 80022 or 80041")
        self.executable = executable
        self.timeout_seconds = timeout_seconds
        self.expected_version_num = expected_version_num

    def _resolved_executable(self) -> str:
        if Path(self.executable).is_absolute():
            return self.executable
        resolved = shutil.which(self.executable)
        if resolved is None:
            raise FileNotFoundError(f"mysql executable not found: {self.executable}")
        return resolved

    def _environment(self) -> dict[str, str]:
        allowed = ("HOME", "PATH", "TMPDIR", "MYSQL_TEST_LOGIN_FILE")
        environment = {key: os.environ[key] for key in allowed if key in os.environ}
        environment["LC_ALL"] = "C"
        environment["LANG"] = "C"
        return environment

    def _base_command(self, target: MysqlTarget) -> list[str]:
        return [
            self._resolved_executable(),
            f"--login-path={target.login_path}",
            f"--database={target.database}",
            "--batch",
            "--raw",
            "--skip-column-names",
            "--show-warnings",
            "--binary-mode",
            "--default-character-set=utf8mb4",
        ]

    def inspect(self, target: MysqlTarget) -> EndpointIdentity:
        query = (
            "SELECT VERSION(), @@server_uuid, @@hostname, @@port, CURRENT_USER(), "
            "@@version_comment, "
            + _mysql_global_privileges_expression()
            + ";"
        )
        completed = subprocess.run(
            [*self._base_command(target), f"--execute={query}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout_seconds,
            env=self._environment(),
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
        if len(columns) != 7:
            raise ValueError(f"endpoint preflight returned malformed identity for {target.name}")
        try:
            raw_privileges = json.loads(columns[6])
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"endpoint preflight returned malformed privilege JSON for {target.name}"
            ) from exc
        identity = _identity_from_mapping(
            {
                "server_version": columns[0],
                "server_uuid": columns[1],
                "server_hostname": columns[2],
                "server_port": columns[3],
                "current_user": columns[4],
                "version_comment": columns[5],
                "granted_global_privileges": raw_privileges,
            },
            target,
        )
        validate_endpoint_identity(identity, expected_version_num=self.expected_version_num)
        return identity

    def run(
        self,
        sql_path: str | Path,
        target: MysqlTarget,
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
        return self.run_content(sql_content, path, target, stop_on_error=stop_on_error)

    def run_content(
        self,
        sql_content: str,
        sql_label: str | Path,
        target: MysqlTarget,
        *,
        stop_on_error: bool = True,
    ) -> ExecutionRecord:
        validate_sql_for_basic_runner(sql_content)
        path = Path(sql_label).resolve()
        command = self._base_command(target)
        if not stop_on_error:
            command.append("--force")
        wrapped_sql = _session_identity_query() + "\n" + sql_content
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=wrapped_sql,
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout_seconds,
            env=self._environment(),
        )
        session_identity, user_stdout = _parse_mysql_session_identity(
            completed.stdout or "",
            target,
            expected_version_num=self.expected_version_num,
        )
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


PsqlRunner = MysqlRunner
