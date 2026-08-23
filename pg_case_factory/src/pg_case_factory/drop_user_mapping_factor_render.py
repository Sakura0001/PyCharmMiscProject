"""Render complete PostgreSQL 18.4 DROP USER MAPPING factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator can never diverge from the bytes actually
written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_user_mapping um JOIN
pg_catalog.pg_authid a ON um.umuser = a.oid JOIN
pg_catalog.pg_foreign_server s ON um.umserver = s.oid WHERE ... ORDER BY
count(*) LIMIT 1``.  ``pg_user_mapping`` has NO name column — a mapping is
identified by the (role, server) pair, so the probe always JOINs to
``pg_authid`` (for the role name) and ``pg_foreign_server`` (for the server
name).  For PUBLIC (``um.umuser = 0``) the probe uses ``um.umuser = 0``
directly since no ``pg_authid`` row has ``oid = 0``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import (
    DropSpec,
    UserMappingDropSpec,
    build_cleanup,
    build_pre_cleanup,
)
from .drop_user_mapping_factor_extension import (
    DropUserMappingFactorExtensionCase,
)
from .drop_user_mapping_factor_loop import (
    DropUserMappingFactorCase,
    DropUserMappingFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/user_mapping/"
    "drop_user_mapping.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/user_mapping/"
    "drop_user_mapping.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target mapping is intentionally absent.
_ABSENT_MAPPING_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("nonexistent_mapping", "mapping_missing_without_if_exists"),
        ("user_name_shape", "nonexistent_name"),
    }
)

# Baseline primaries whose target server is intentionally absent.
_SERVER_MISSING_PRIMARIES = frozenset(
    {
        ("nonexistent_server", "server_missing"),
        ("server_existence", "server_not_exists"),
        ("server_name_shape", "nonexistent_name"),
    }
)

# Baseline primaries that imply a non-privileged session role.
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("authorization_path", "non_privileged"),
        ("privilege_context", "non_privileged_session"),
        ("insufficient_privilege", "lacks_privilege"),
        ("self_mapping_only", "attempting_other_user_mapping"),
    }
)

# For an extension SUCCESS case the synthetic primary must be a neutral
# success primary; the mapping always exists in extensions unless
# object_state=absent.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropUserMappingFactorExtensionCase,
) -> DropUserMappingFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_user_mapping_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropUserMappingFactorCase(
        ordinal=ext.ordinal,
        case_id=ext.case_id,
        sql_filename=ext.sql_filename,
        object_prefix=ext.object_prefix,
        primary_obligation_id=ext.derivation_id,
        kind="EXT",
        factor_key=factor_key,
        factor_value=factor_value,
        consumer_action_id=ext.consumer_action_id,
        outcome=ext.outcome,
        expected_sqlstate=ext.expected_sqlstate,
        expected_failure_reason=ext.expected_failure_reason,
        baseline_assignments=ext.factor_assignment,
        execution_profile="default",
    )


def _as_render_case(
    case: DropUserMappingFactorCase | DropUserMappingFactorExtensionCase,
) -> DropUserMappingFactorCase:
    if isinstance(case, DropUserMappingFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropUserMappingFactorRenderError(ValueError):
    """Raised when a DROP USER MAPPING case cannot be rendered."""


@dataclass(frozen=True)
class DropUserMappingFactorWitness:
    primary_obligation_id: str
    target_sql_fragment: str
    outcome: str
    expected_sqlstate: str
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


@dataclass(frozen=True)
class _CasePlan:
    target_fragment: str
    setup_lines: tuple[str, ...]
    assert_lines: tuple[str, ...]
    pre_cleanup_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    on_error_off: bool
    semantic_locus: str


def _baseline(case: DropUserMappingFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


# ---------------------------------------------------------------------------
# Server fixture helpers
# ---------------------------------------------------------------------------

def _server_created(case: DropUserMappingFactorCase, a: dict[str, str]) -> bool:
    """Whether the foreign server fixture should be created."""

    if case.kind == "EXT":
        return (
            a.get("server_existence") == "server_exists"
            and a.get("server_name_shape") == "simple_id"
        )
    if (case.factor_key, case.factor_value) in _SERVER_MISSING_PRIMARIES:
        return False
    return (
        a.get("server_existence") == "server_exists"
        and a.get("server_name_shape") == "simple_id"
    )


def _target_server_ref(
    case: DropUserMappingFactorCase, a: dict[str, str], p: str
) -> str:
    """The server name as referenced inside DROP USER MAPPING."""

    shape = a.get("server_name_shape", "simple_id")
    if shape == "nonexistent_name":
        return f"{p}nosrv"
    return f"{p}srv"


def _probe_server(
    case: DropUserMappingFactorCase, a: dict[str, str], p: str
) -> str:
    """The bare server name for the catalog probe."""

    return _target_server_ref(case, a, p)


# ---------------------------------------------------------------------------
# Role / mapping fixture helpers
# ---------------------------------------------------------------------------

def _effective_role(
    case: DropUserMappingFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP runs ('' = superuser)."""

    auth = a.get("authorization_path", "server_owner")
    if auth in ("non_privileged", "user_with_usage"):
        return f"{p}actor"
    return ""


def _needs_grant(case: DropUserMappingFactorCase, a: dict[str, str]) -> bool:
    return a.get("authorization_path") == "user_with_usage"


def _is_public(a: dict[str, str]) -> bool:
    return a.get("user_specification") == "public"


def _is_keyword_user(a: dict[str, str]) -> bool:
    return a.get("user_specification") in (
        "current_user",
        "current_role",
        "user_keyword",
    )


def _target_role_ref(
    case: DropUserMappingFactorCase, a: dict[str, str], p: str
) -> str:
    """The role reference inside DROP USER MAPPING FOR <role>."""

    user_spec = a.get("user_specification", "named_user")
    if user_spec == "public":
        return "PUBLIC"
    if user_spec == "current_user":
        return "CURRENT_USER"
    if user_spec == "current_role":
        return "CURRENT_ROLE"
    if user_spec == "user_keyword":
        return "USER"
    # named_user
    auth = a.get("authorization_path", "server_owner")
    shape = a.get("user_name_shape", "simple_id")
    if auth == "user_with_usage":
        return f"{p}actor"
    if shape == "quoted_id":
        return f'"{p}qrole"'
    if shape == "nonexistent_name":
        return f"{p}norole"
    return f"{p}role"


def _fixture_role_ref(
    case: DropUserMappingFactorCase, a: dict[str, str], p: str
) -> str | None:
    """The role for which the mapping is CREATEd (None = skip mapping)."""

    user_spec = a.get("user_specification", "named_user")
    if user_spec == "public":
        return "PUBLIC"
    if user_spec in ("current_user", "current_role", "user_keyword"):
        return "CURRENT_USER"
    # named_user
    auth = a.get("authorization_path", "server_owner")
    shape = a.get("user_name_shape", "simple_id")
    if auth == "user_with_usage":
        return f"{p}actor"
    if shape == "nonexistent_name":
        return None
    if shape == "quoted_id":
        return f'"{p}qrole"'
    return f"{p}role"


def _mapping_created(
    case: DropUserMappingFactorCase, a: dict[str, str]
) -> bool:
    """Whether the user mapping fixture should be created."""

    if not _server_created(case, a):
        return False
    if a.get("object_state") == "absent":
        return False
    if a.get("nonexistent_mapping") == "mapping_missing_without_if_exists":
        return False
    if _fixture_role_ref(case, a, "") is None:
        return False
    return True


def _probe_role_condition(
    case: DropUserMappingFactorCase,
    a: dict[str, str],
    p: str,
    effective: str,
) -> str:
    """The WHERE condition for the role in the catalog probe."""

    if _is_public(a):
        return "um.umuser = 0"
    if _is_keyword_user(a):
        if effective:
            return f"a.rolname = '{p}actor'"
        keyword = {
            "current_user": "CURRENT_USER",
            "current_role": "CURRENT_ROLE",
            "user_keyword": "CURRENT_USER",
        }
        return f"a.rolname = {keyword[a['user_specification']]}"
    # named_user
    auth = a.get("authorization_path", "server_owner")
    shape = a.get("user_name_shape", "simple_id")
    if auth == "user_with_usage":
        return f"a.rolname = '{p}actor'"
    if shape == "quoted_id":
        return f"a.rolname = '{p}qrole'"
    if shape == "nonexistent_name":
        return f"a.rolname = '{p}norole'"
    return f"a.rolname = '{p}role'"


# ---------------------------------------------------------------------------
# Outcome / probe helpers
# ---------------------------------------------------------------------------

def _if_exists_present(
    case: DropUserMappingFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "present"


def _mapping_absent_after(
    case: DropUserMappingFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target mapping is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _mapping_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropUserMappingFactorCase,
    a: dict[str, str],
    p: str,
    effective: str,
) -> str:
    """Build the catalog probe SELECT for the (role, server) pair."""

    server = _probe_server(case, a, p)
    role_cond = _probe_role_condition(case, a, p, effective)
    absent = _mapping_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "mapping_absent" if absent else "mapping_present"
    if _is_public(a):
        return (
            f"SELECT count(*) {comparator} AS {alias} "
            "FROM pg_catalog.pg_user_mapping um "
            "JOIN pg_catalog.pg_foreign_server s "
            "ON um.umserver = s.oid "
            f"WHERE um.umuser = 0 AND s.srvname = '{server}' "
            "ORDER BY count(*) LIMIT 1;"
        )
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_user_mapping um "
        "JOIN pg_catalog.pg_authid a ON um.umuser = a.oid "
        "JOIN pg_catalog.pg_foreign_server s ON um.umserver = s.oid "
        f"WHERE {role_cond} AND s.srvname = '{server}' "
        "ORDER BY count(*) LIMIT 1;"
    )


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------

def _cleanup_role_names(
    case: DropUserMappingFactorCase,
    a: dict[str, str],
    p: str,
    effective: str,
) -> tuple[str, ...]:
    """Distinct unquoted role names to DROP in cleanup."""

    names: list[str] = []
    if effective == f"{p}actor":
        names.append(f"{p}actor")
    shape = a.get("user_name_shape", "simple_id")
    auth = a.get("authorization_path", "server_owner")
    if auth != "user_with_usage" and shape != "nonexistent_name":
        if shape == "quoted_id":
            names.append(f"{p}qrole")
        else:
            names.append(f"{p}role")
    if shape == "nonexistent_name":
        pass  # no role was created
    return tuple(dict.fromkeys(names))


def _mapping_drop_specs(
    a: dict[str, str],
    p: str,
    roles: tuple[str, ...],
) -> tuple[UserMappingDropSpec, ...]:
    """Build the shape-E ``DROP USER MAPPING`` specs (FOR <user> SERVER <s>).

    The fixture server is always ``{p}srv``.  PG18 ``DROP USER MAPPING IF
    EXISTS`` is a lenient NOTICE-only no-op when the server (or role) is
    absent, so the spec is emitted unconditionally for every created role plus
    ``PUBLIC`` when the target mapped the PUBLIC role -- ``IF EXISTS`` makes a
    ``server_created`` gate redundant (the Fix-A improvement).
    """
    specs: list[UserMappingDropSpec] = [
        UserMappingDropSpec(role, f"{p}srv") for role in roles
    ]
    if _is_public(a):
        specs.append(UserMappingDropSpec("PUBLIC", f"{p}srv"))
    return tuple(specs)


def _resolve_case(case: DropUserMappingFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    server_created = _server_created(case, a)
    mapping_created = _mapping_created(case, a)
    fixture_role = _fixture_role_ref(case, a, p)
    target_role = _target_role_ref(case, a, p)
    target_server = _target_server_ref(case, a, p)
    effective = _effective_role(case, a, p)
    needs_grant = _needs_grant(case, a)

    setup: list[str] = []
    locus = "target.user_mapping"

    # --- setup boundary SELECT ---
    setup.append("SELECT 1 AS setup_boundary;")

    # --- file_fdw extension (shared across cases) ---
    setup.append("CREATE EXTENSION IF NOT EXISTS file_fdw;")

    # --- foreign server fixture (as superuser) ---
    if server_created:
        setup.append(
            f"CREATE SERVER {p}srv FOREIGN DATA WRAPPER file_fdw;"
        )
        locus = "fixture.foreign_server"

    # --- role fixtures ---
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
    if (
        a.get("authorization_path") == "server_owner"
        or a.get("authorization_path") == "non_privileged"
    ):
        shape = a.get("user_name_shape", "simple_id")
        if shape == "quoted_id":
            setup.append(f'CREATE ROLE "{p}qrole" LOGIN;')
        elif shape != "nonexistent_name":
            setup.append(f"CREATE ROLE {p}role LOGIN;")

    # --- GRANT USAGE for user_with_usage ---
    if needs_grant and server_created:
        setup.append(
            f"GRANT USAGE ON FOREIGN SERVER {p}srv TO {p}actor;"
        )

    # --- arm the session role (before mapping creation for keywords) ---
    if effective:
        setup.append(f"SET ROLE {p}actor;")

    # --- user mapping fixture ---
    if mapping_created and fixture_role is not None:
        setup.append(
            f"CREATE USER MAPPING FOR {fixture_role} SERVER {p}srv;"
        )
        if locus == "target.user_mapping":
            locus = "fixture.user_mapping"
    elif server_created and not mapping_created:
        setup.append(
            "SELECT 1 AS target_mapping_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- disarm role before the target (target runs as the session role) ---
    # For user_with_usage, the DROP runs as {p}actor (own mapping).
    # For non_privileged, the DROP runs as {p}actor (privilege failure).
    # For server_owner, the DROP runs as superuser (no RESET needed).

    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    target = f"DROP USER MAPPING {if_exists}FOR {target_role} SERVER {target_server};"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p, effective))

    # --- cleanup construction (idempotent bookends via cleanup_bookend) ---
    roles = _cleanup_role_names(case, a, p, effective)
    server_specs = (DropSpec("SERVER", f"{p}srv"),) if server_created else ()
    mapping_specs = _mapping_drop_specs(a, p, roles)
    pre_cleanup_bk = build_pre_cleanup(
        specs=server_specs,
        complex_specs=mapping_specs,
        roles=roles,
    )
    cleanup_bk = build_cleanup(
        specs=server_specs,
        complex_specs=mapping_specs,
        roles=roles,
        drop_owned=bool(roles),
        reset_role=effective,
    )
    pre_cleanup = list(pre_cleanup_bk.statements)
    cleanup = list(cleanup_bk.statements)

    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def resolve_drop_user_mapping_factor_witness(
    case: DropUserMappingFactorCase | DropUserMappingFactorExtensionCase,
    repository_root: Path,
) -> DropUserMappingFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropUserMappingFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_user_mapping(sql: str) -> int:
    """Count the single credited DROP USER MAPPING inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+USER\s+MAPPING\b", region)
    )


def _header(case: DropUserMappingFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP USER MAPPING {case.factor_key}={case.factor_value}",
        f"-- FE           : {_FE}",
        "-- ++",
        "-- --------------------------------------------------------",
        f"-- case_id: {case.case_id}",
        f"-- source_md: {_DOC_SOURCE}",
        f"-- factor_md: {_FACTOR_SOURCE}",
        f"-- primary_obligation_id: {case.primary_obligation_id}",
        f"-- expected_outcome: {case.outcome}",
        f"-- expected_sqlstate: {case.expected_sqlstate}",
    ]


def render_drop_user_mapping_factor_case(
    case: DropUserMappingFactorCase | DropUserMappingFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP USER MAPPING regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地映射和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP USER MAPPING。")
    lines.append(_PRIMARY_BEGIN)
    lines.append(resolved.target_fragment)
    lines.append(_PRIMARY_END)
    lines.append("\\set target_sqlstate :SQLSTATE")
    lines.append("\\echo PGCF_TARGET_SQLSTATE=:target_sqlstate")
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 4. 验证 SQLSTATE、目录状态和数据行为。")
    lines.extend(resolved.assert_lines)
    lines.append("-- 5. 清理全部本编号对象。")
    lines.extend(resolved.cleanup_lines)
    text = "\n".join(lines)
    if not text.endswith(";"):
        text += ";"
    return text + "\n"


def generate_drop_user_mapping_factor_programs(
    baseline_plan: DropUserMappingFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
    """Write every baseline + extension program; return the file count."""

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        _write_program(case, out)
        count += 1
    for case in extension_plan.cases:
        _write_program(case, out)
        count += 1
    return count


def _write_program(
    case: DropUserMappingFactorCase | DropUserMappingFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_user_mapping_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropUserMappingFactorRenderError",
    "DropUserMappingFactorWitness",
    "count_primary_drop_user_mapping",
    "generate_drop_user_mapping_factor_programs",
    "render_drop_user_mapping_factor_case",
    "resolve_drop_user_mapping_factor_witness",
]
