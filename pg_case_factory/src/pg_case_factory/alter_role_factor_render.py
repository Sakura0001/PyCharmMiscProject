"""Render complete PostgreSQL 18.4 ALTER ROLE factor-loop regress programs.

Every planned case -- whether a frozen baseline obligation
(:class:`AlterRoleFactorCase`) or a bounded post-coverage extension
(:class:`AlterRoleFactorExtensionCase`) -- becomes one self-contained,
deterministic SQL file assembled from a single :func:`_resolve_case` plan.
The byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

The 5-phase byte contract mirrors :mod:`alter_group_factor_render`: (1)
idempotent pre-clean superset; ``\\set ON_ERROR_STOP on``; (2) role fixture
setup (CREATE ROLE target + executor with the needed CREATEROLE flag, GRANT
... WITH ADMIN OPTION where needed, SET ROLE before the target); [
``\\set ON_ERROR_STOP off`` when expected_failure]; (3) the single credited
``ALTER ROLE`` wrapped in ``-- primary-target-begin`` / ``-- primary-target-end``;
``\\set target_sqlstate :SQLSTATE`` / ``\\echo PGCF_TARGET_SQLSTATE=...``; [
``\\set ON_ERROR_STOP on``]; (4) oracle/assert; (5) unconditional cleanup
(RESET ROLE, labeled cleanup step, DROP ROLE).

``ALTER ROLE`` creates NO TABLES, so ``contains_create_table_statement`` is
False and the DROP-TABLE bookend gate is skipped; roles are ``DROP ROLE``'d
in cleanup.  All catalog relations are schema-qualified
(``pg_catalog.pg_roles`` / ``pg_catalog.pg_authid`` / ``pg_catalog.pg_settings``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_role_factor_extension import AlterRoleFactorExtensionCase
from .alter_role_factor_loop import AlterRoleFactorCase


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/role/"
    "alter_role.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/role/"
    "alter_role.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

# The bootstrap superuser whose SUPERUSER property is immutable (PG18 test
# point PG18-ALTER-ROLE-BOOTSTRAP-SUPERUSER).  It pre-exists as the cluster
# initdb superuser; the DB phase verifies the actual SQLSTATE.
_BOOTSTRAP_SUPERUSER = "pgcf_superuser"

# Behaviour assertions (SUCCESS paths with state-checking oracles).
_MD5_CLEARED = ("rename_clears_password", "md5_password_cleared_on_rename")
_SCRAM_PRESERVED = ("rename_clears_password", "scram_password_preserved_on_rename")
_PWD_NULL_REMOVES = ("password_security", "password_null_removes_password")
_PLAINTEXT_IN_SQL = ("password_security", "plaintext_password_in_sql")


class AlterRoleFactorRenderError(ValueError):
    """Raised when an ALTER ROLE case cannot be rendered."""


@dataclass(frozen=True)
class AlterRoleFactorWitness:
    primary_obligation_id: str
    target_sql_fragment: str
    outcome: str
    expected_sqlstate: str
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


@dataclass(frozen=True)
class AlterRoleRenderCase:
    """Adapter normalising baseline + extension cases for the renderer."""

    case_id: str
    sql_filename: str
    object_prefix: str
    primary_identifier: str
    description: str
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    assignment: tuple[tuple[str, str], ...]
    is_extension: bool

    @classmethod
    def from_case(cls, case: object) -> "AlterRoleRenderCase":
        if isinstance(case, AlterRoleFactorCase):
            assignment = case.baseline_assignments
            primary = case.primary_obligation_id
            desc = f"{case.factor_key}={case.factor_value}"
            is_ext = False
        elif isinstance(case, AlterRoleFactorExtensionCase):
            assignment = case.factor_assignment
            primary = case.derivation_id
            desc = case.derivation_reason
            is_ext = True
        else:  # pragma: no cover - defensive
            raise AlterRoleFactorRenderError(
                f"unknown case type: {type(case).__name__}"
            )
        return cls(
            case_id=case.case_id,
            sql_filename=case.sql_filename,
            object_prefix=case.object_prefix,
            primary_identifier=primary,
            description=desc,
            consumer_action_id=case.consumer_action_id,
            outcome=case.outcome,
            expected_sqlstate=case.expected_sqlstate,
            expected_failure_reason=case.expected_failure_reason,
            assignment=assignment,
            is_extension=is_ext,
        )


@dataclass(frozen=True)
class _CasePlan:
    target_fragment: str
    setup_lines: tuple[str, ...]
    assert_lines: tuple[str, ...]
    pre_cleanup_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    on_error_off: bool
    semantic_locus: str


def _a(rc: AlterRoleRenderCase) -> dict[str, str]:
    return dict(rc.assignment)


def _behavior_primary(rc: AlterRoleRenderCase) -> tuple[str, str] | None:
    """The behaviour-assertion pair this case witnesses, if any."""

    a = _a(rc)
    # Extension cases carry no single primary; only baseline behaviour cases.
    if rc.is_extension:
        return None
    for factor, value in (
        _MD5_CLEARED,
        _SCRAM_PRESERVED,
        _PWD_NULL_REMOVES,
        _PLAINTEXT_IN_SQL,
    ):
        if a.get(factor) == value:
            return (factor, value)
    return None


def _role_spec(a: dict[str, str], p: str) -> str:
    """The role_specification literal referenced inside ALTER ROLE."""

    shape = a.get("role_name_shape", "simple_name")
    if shape == "current_role_keyword":
        return "CURRENT_ROLE"
    if shape == "current_user_keyword":
        return "CURRENT_USER"
    if shape == "session_user_keyword":
        return "SESSION_USER"
    if shape == "all_keyword":
        return "ALL"
    if shape == "quoted_name":
        return f'"{p}Target"'
    if shape == "reserved_word_name":
        return f'"{p}select"'
    if shape == "non_existent_name":
        return f"{p}missing"
    return f"{p}target"


def _target_role_name(a: dict[str, str], p: str) -> str | None:
    """The creatable target role literal, or None (keyword/all/absent)."""

    shape = a.get("role_name_shape", "simple_name")
    if shape in (
        "current_role_keyword",
        "current_user_keyword",
        "session_user_keyword",
        "all_keyword",
    ):
        return None
    if shape == "quoted_name":
        return f'"{p}Target"'
    if shape == "reserved_word_name":
        return f'"{p}select"'
    if shape == "non_existent_name":
        return f"{p}missing"
    return f"{p}target"


def _target_exists(a: dict[str, str]) -> bool:
    """Whether the target role is an existing creatable role."""

    return (
        a.get("role_state") == "exists"
        and _target_role_name(a, "") is not None
    )


def _is_bootstrap(a: dict[str, str]) -> bool:
    return a.get("privilege_insufficient") == "bootstrap_superuser_property_change"


def _new_name(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}Renamed"'
    if shape == "reserved_word_name":
        return f'"{p}from"'
    if shape == "existing_name_conflict":
        return f"{p}conflict"
    if shape == "non_existent_name":
        return f"{p}fresh"
    return f"{p}renamed"


def _new_name_creatable(a: dict[str, str], p: str) -> str | None:
    shape = a.get("new_name_shape", "simple_name")
    if shape == "existing_name_conflict":
        return f"{p}conflict"
    return _new_name(a, p)


def _attribute_clause(a: dict[str, str], p: str) -> str:
    """The branch_1 option clause (one or many options)."""

    opt = a.get("attribute_option", "login")
    clause = _single_attribute(opt, a, p)
    if a.get("action_list_cardinality") == "multiple_actions":
        clause = f"{clause} LOGIN"
    return clause


def _single_attribute(opt: str, a: dict[str, str], p: str) -> str:
    single = {
        "superuser": "SUPERUSER",
        "nosuperuser": "NOSUPERUSER",
        "createdb": "CREATEDB",
        "nocreatedb": "NOCREATEDB",
        "createrole": "CREATEROLE",
        "nocreaterole": "NOCREATEROLE",
        "inherit": "INHERIT",
        "noinherit": "NOINHERIT",
        "login": "LOGIN",
        "nologin": "NOLOGIN",
        "replication": "REPLICATION",
        "noreplication": "NOREPLICATION",
        "bypassrls": "BYPASSRLS",
        "nobypassrls": "NOBYPASSRLS",
        "connection_limit": "CONNECTION LIMIT 5",
        "valid_until": "VALID UNTIL '2026-12-31'",
        "password_null": "PASSWORD NULL",
    }
    if opt in single:
        return single[opt]
    if opt == "encrypted_password":
        enc = "ENCRYPTED " if a.get("encrypted_keyword") == "present" else ""
        return f"{enc}PASSWORD '{p}secret'"
    raise AlterRoleFactorRenderError(f"no attribute clause for {opt}")


def _config_guc(a: dict[str, str], p: str) -> str:
    shape = a.get("config_parameter_shape", "valid_parameter")
    if shape == "invalid_parameter":
        return f"{p}no_such_guc"
    if shape == "superuser_only_parameter":
        return "log_statement"
    return "work_mem"


def _config_value(a: dict[str, str]) -> str:
    return "100"


def _db_clause(a: dict[str, str], p: str) -> str:
    shape = a.get("database_name_shape", "omitted_no_database_clause")
    if shape == "existing_database":
        return f"IN DATABASE {p}db "
    if shape == "non_existent_database":
        return f"IN DATABASE {p}nodb "
    return ""


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER ROLE runs."""

    level = a.get("privilege_level", "superuser")
    if level == "createrole_with_admin_option":
        return f"{p}admin"
    if level == "createrole_without_admin_option":
        return f"{p}admin"
    if level == "ordinary_role_self":
        return f"{p}self"
    if level == "ordinary_role_other":
        return f"{p}actor"
    return ""  # superuser: run as pgcf_superuser


def _role_set(
    rc: AlterRoleRenderCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    """Every role literal this case may touch, for idempotent DROP ROLE."""

    roles: list[str] = []
    if _is_bootstrap(a):
        return ()  # bootstrap superuser is never dropped
    name = _target_role_name(a, p)
    if name and _target_exists(a):
        roles.append(name)
    if rc.consumer_action_id == "rename":
        new = _new_name_creatable(a, p)
        if new and a.get("new_name_shape") == "existing_name_conflict":
            roles.append(new)
        fresh = _new_name(a, p)
        roles.append(fresh)
    eff = _effective_role(a, p)
    if eff:
        roles.append(eff)
    seen: set[str] = set()
    unique: list[str] = []
    for role in roles:
        if role not in seen:
            seen.add(role)
            unique.append(role)
    return tuple(unique)


def _setup_fixture(
    rc: AlterRoleRenderCase, a: dict[str, str], p: str
) -> tuple[tuple[str, ...], str]:
    """Build the role fixture; return (setup_lines, semantic_locus)."""

    lines: list[str] = []
    locus = "target.role_attribute"
    action = rc.consumer_action_id
    eff = _effective_role(a, p)
    if _is_bootstrap(a):
        # The bootstrap superuser pre-exists; no fixture, no SET ROLE.
        locus = "target.bootstrap_superuser"
        return tuple(lines), locus
    # database fixture (IN DATABASE clause)
    if a.get("database_name_shape") == "existing_database":
        lines.append(f"CREATE DATABASE {p}db;")
    # target role
    name = _target_role_name(a, p)
    if name and _target_exists(a):
        create_flags = _target_create_flags(a)
        lines.append(f"CREATE ROLE {name}{create_flags};")
    # rename conflict target (pre-create to surface 42710)
    if (
        action == "rename"
        and a.get("new_name_shape") == "existing_name_conflict"
    ):
        lines.append(f"CREATE ROLE {p}conflict;")
    # password fixture for behaviour assertions
    beh = _behavior_primary(rc)
    if beh == _MD5_CLEARED or beh == _SCRAM_PRESERVED:
        target = name or eff
        if target:
            lines.append(f"ALTER ROLE {target} PASSWORD '{p}secret';")
    if beh == _PLAINTEXT_IN_SQL:
        pass  # the target itself carries the plaintext password
    # privilege fixture
    if eff == f"{p}admin":
        lines.append(f"CREATE ROLE {p}admin LOGIN CREATEROLE;")
        if name and _target_exists(a):
            if a.get("role_membership_dependency") == "admin_option_not_granted":
                pass  # no ADMIN OPTION -> 42501
            else:
                lines.append(f"GRANT {name} TO {p}admin WITH ADMIN OPTION;")
        lines.append(f"SET ROLE {p}admin;")
        locus = "fixture.privilege_state"
    elif eff == f"{p}actor":
        lines.append(f"CREATE ROLE {p}actor LOGIN;")
        lines.append(f"SET ROLE {p}actor;")
        locus = "fixture.privilege_state"
    elif eff == f"{p}self":
        lines.append(f"CREATE ROLE {p}self LOGIN;")
        lines.append(f"SET ROLE {p}self;")
        locus = "fixture.privilege_state"
    return tuple(lines), locus


def _target_create_flags(a: dict[str, str]) -> str:
    """Minimal LOGIN flag so the target role is usable."""

    return " LOGIN"


def _target_fragment(
    rc: AlterRoleRenderCase, a: dict[str, str], p: str
) -> str:
    branch = a.get("grammar_branch", "branch_1_with_option")
    spec = _role_spec(a, p)
    if _is_bootstrap(a):
        return f"ALTER ROLE {_BOOTSTRAP_SUPERUSER} NOSUPERUSER;"
    if branch == "branch_1_with_option":
        with_kw = "WITH " if a.get("with_keyword") == "present" else ""
        return f"ALTER ROLE {spec} {with_kw}{_attribute_clause(a, p)};"
    if branch == "branch_2_rename":
        return f"ALTER ROLE {spec} RENAME TO {_new_name(a, p)};"
    return _set_reset_fragment(branch, a, p, spec)


def _set_reset_fragment(
    branch: str, a: dict[str, str], p: str, spec: str
) -> str:
    db = _db_clause(a, p)
    guc = _config_guc(a, p)
    if branch == "branch_3_set_value":
        form = a.get("set_assignment_form", "to_value")
        if form == "equals_value":
            return f"ALTER ROLE {spec} {db}SET {guc} = {_config_value(a)};"
        return f"ALTER ROLE {spec} {db}SET {guc} TO {_config_value(a)};"
    if branch == "branch_4_set_from_current":
        return f"ALTER ROLE {spec} {db}SET {guc} FROM CURRENT;"
    if branch == "branch_5_reset_parameter":
        return f"ALTER ROLE {spec} {db}RESET {guc};"
    if branch == "branch_6_reset_all":
        return f"ALTER ROLE {spec} {db}RESET ALL;"
    raise AlterRoleFactorRenderError(f"unknown branch {branch}")


def _probe_name(rc: AlterRoleRenderCase, a: dict[str, str], p: str) -> str:
    """The role name the oracle probes (stripped of quotes)."""

    if rc.consumer_action_id == "rename" and rc.outcome == "success":
        return _new_name(a, p).strip('"')
    name = _target_role_name(a, p)
    if name is None:
        return ""
    return name.strip('"')


def _oracle(
    rc: AlterRoleRenderCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    lines: list[str] = [
        f"SELECT :'target_sqlstate' = '{rc.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    ]
    mode = a.get("verification_mode", "pg_roles_catalog")
    beh = _behavior_primary(rc)
    if mode == "effect_query" or beh is not None:
        lines.extend(_behavior_oracle(rc, a, p, beh))
        return tuple(lines)
    if mode == "error_assertion":
        lines.append("SELECT :'target_sqlstate' AS asserted_sqlstate;")
        return tuple(lines)
    if mode == "pg_settings_catalog":
        guc = _config_guc(a, p)
        lines.append(
            "SELECT name, setting, source "
            f"FROM pg_catalog.pg_settings WHERE name = '{guc}' "
            "ORDER BY name;"
        )
        return tuple(lines)
    if mode == "pg_authid_catalog":
        name = _probe_name(rc, a, p)
        if name:
            lines.append(
                "SELECT rolname, rolpassword "
                f"FROM pg_catalog.pg_authid WHERE rolname = '{name}' "
                "ORDER BY oid;"
            )
        else:
            lines.append(
                "SELECT :'target_sqlstate' AS asserted_sqlstate;"
            )
        return tuple(lines)
    # pg_roles_catalog (default)
    name = _probe_name(rc, a, p)
    if name:
        lines.append(
            "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, "
            "rolcanlogin, rolreplication, rolbypassrls, rolconnlimit, "
            "rolvaliduntil "
            f"FROM pg_catalog.pg_roles WHERE rolname = '{name}' "
            "ORDER BY oid;"
        )
    else:
        lines.append(
            "SELECT :'target_sqlstate' AS asserted_sqlstate;"
        )
    return tuple(lines)


def _behavior_oracle(
    rc: AlterRoleRenderCase,
    a: dict[str, str],
    p: str,
    beh: tuple[str, str] | None,
) -> list[str]:
    """State-checking oracle for the four BEHAVIOR assertions."""

    name = _probe_name(rc, a, p)
    if beh == _MD5_CLEARED:
        return [
            "SELECT rolpassword IS NULL AS md5_password_cleared_on_rename "
            f"FROM pg_catalog.pg_authid WHERE rolname = '{name}' "
            "ORDER BY oid;"
        ]
    if beh == _SCRAM_PRESERVED:
        return [
            "SELECT rolpassword IS NOT NULL "
            "AS scram_password_preserved_on_rename "
            f"FROM pg_catalog.pg_authid WHERE rolname = '{name}' "
            "ORDER BY oid;"
        ]
    if beh == _PWD_NULL_REMOVES:
        return [
            "SELECT rolpassword IS NULL AS password_null_removes_password "
            f"FROM pg_catalog.pg_authid WHERE rolname = '{name}' "
            "ORDER BY oid;"
        ]
    if beh == _PLAINTEXT_IN_SQL:
        return [
            "SELECT rolpassword IS NOT NULL AS plaintext_password_present "
            f"FROM pg_catalog.pg_authid WHERE rolname = '{name}' "
            "ORDER BY oid;"
        ]
    # effect_query with no behaviour pair: a generic catalog probe.
    if name:
        return [
            "SELECT rolname FROM pg_catalog.pg_roles "
            f"WHERE rolname = '{name}' ORDER BY oid;"
        ]
    return ["SELECT :'target_sqlstate' AS asserted_sqlstate;"]


def _labeled_cleanup(
    rc: AlterRoleRenderCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    """The cleanup_mode-driven teardown step, only when provably safe."""

    mode = a.get("cleanup_mode", "drop_role")
    action = rc.consumer_action_id
    if _is_bootstrap(a):
        return ()
    spec = _role_spec(a, p)
    guc = _config_guc(a, p)
    if mode == "reset_config_parameter" and action in (
        "set_value",
        "set_from_current",
    ):
        return (f"ALTER ROLE {spec} RESET {guc};",)
    if mode == "revert_attribute_change" and action == "with_option":
        if rc.outcome == "success":
            return (f"ALTER ROLE {spec} NOLOGIN;",)
    return ()


def _resolve_case(rc: AlterRoleRenderCase) -> _CasePlan:
    a = _a(rc)
    p = rc.object_prefix
    setup, locus = _setup_fixture(rc, a, p)
    target = _target_fragment(rc, a, p)
    eff = _effective_role(a, p)
    # RISK transaction wrapper: BEGIN before the target so the credited
    # ALTER ROLE runs inside a transaction whose outcome (commit/rollback)
    # is then asserted.
    txn = a.get("transaction_outcome")
    if txn:
        setup = (*setup, "BEGIN;")
        locus = "target.transaction_boundary"
    assert_lines = _oracle(rc, a, p)
    if txn:
        assert_lines = (
            "COMMIT;" if txn == "commit" else "ROLLBACK;",
        ) + assert_lines
    # RESET ROLE before the oracle so pg_authid (superuser-read-only) and
    # every catalog probe succeed as the connection superuser.
    if eff:
        assert_lines = ("RESET ROLE;",) + assert_lines
    roles = _role_set(rc, a, p)
    pre_clean = tuple(
        f"DROP ROLE IF EXISTS {role};" for role in roles
    ) or ("SELECT 1 AS residual_check_no_objects;",)
    if a.get("database_name_shape") == "existing_database":
        pre_clean = pre_clean + (f"DROP DATABASE IF EXISTS {p}db;",)
    cleanup: list[str] = []
    if eff:
        cleanup.append("RESET ROLE;")
    cleanup.extend(_labeled_cleanup(rc, a, p))
    cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    if a.get("database_name_shape") == "existing_database":
        cleanup.append(f"DROP DATABASE IF EXISTS {p}db;")
    if not cleanup:
        cleanup.append("SELECT 1 AS residual_check_no_objects;")
    on_error_off = rc.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=setup,
        assert_lines=assert_lines,
        pre_cleanup_lines=pre_clean,
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def _to_render_case(case: object) -> AlterRoleRenderCase:
    return AlterRoleRenderCase.from_case(case)


def resolve_alter_role_factor_witness(
    case: object, repository_root: Path
) -> AlterRoleFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _to_render_case(case)
    plan = _resolve_case(rc)
    return AlterRoleFactorWitness(
        primary_obligation_id=rc.primary_identifier,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_role(sql: str) -> int:
    """Count the single credited ALTER ROLE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+ROLE\b", region))


def _header(rc: AlterRoleRenderCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER ROLE {rc.description}",
        f"-- FE           : {_FE}",
        "-- ++",
        "-- --------------------------------------------------------",
        f"-- case_id: {rc.case_id}",
        f"-- source_md: {_DOC_SOURCE}",
        f"-- factor_md: {_FACTOR_SOURCE}",
        f"-- primary_obligation_id: {rc.primary_identifier}",
        f"-- expected_outcome: {rc.outcome}",
        f"-- expected_sqlstate: {rc.expected_sqlstate}",
    ]


def render_alter_role_factor_case(case: object, repository_root: Path) -> str:
    """Render one complete, deterministic ALTER ROLE regress program."""

    rc = _to_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地角色和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER ROLE。")
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


def generate_alter_role_factor_programs(
    baseline_plan: object, extension_plan: object, out_dir: Path
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


def _write_program(case: object, out: Path) -> None:
    rc = _to_render_case(case)
    text = render_alter_role_factor_case(case, Path("."))
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterRoleFactorRenderError",
    "AlterRoleFactorWitness",
    "AlterRoleRenderCase",
    "count_primary_alter_role",
    "generate_alter_role_factor_programs",
    "render_alter_role_factor_case",
    "resolve_alter_role_factor_witness",
]
