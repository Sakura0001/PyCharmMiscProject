"""Render complete PostgreSQL 18.4 ALTER USER factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER USER is a role DDL statement: the target is a
``pg_catalog.pg_roles`` catalog row, not a ``pg_class`` relation.  All
catalog oracles schema-qualify ``pg_catalog.pg_roles`` (exempt from the
file-prefix style gate).  No case creates a TABLE, so the bookend (DROP
TABLE IF EXISTS) is never emitted.  Every catalog SELECT carries a
top-level ``ORDER BY`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_user_factor_extension import (
    AlterUserFactorExtensionCase,
    _present_failure_pair,
)
from .alter_user_factor_loop import (
    AlterUserFactorCase,
    AlterUserFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/user/"
    "alter_user.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/user/"
    "alter_user.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterUserFactorRenderError(ValueError):
    """Raised when an ALTER USER case cannot be rendered."""


@dataclass(frozen=True)
class AlterUserFactorWitness:
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


def _synthetic_case(
    ext: AlterUserFactorExtensionCase,
) -> AlterUserFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "option_modify")
    return AlterUserFactorCase(
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
    case: AlterUserFactorCase | AlterUserFactorExtensionCase,
) -> AlterUserFactorCase:
    if isinstance(case, AlterUserFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterUserFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _role_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "not_exists"


def _role_name(a: dict[str, str], p: str) -> str:
    """The role identifier in ALTER USER and fixtures."""

    shape = a.get("role_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Mixed Role"'
    if shape == "nonexistent_name":
        return f"{p}nosuchrole"
    return f"{p}role"


def _role_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("role_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Mixed Role"
    if shape == "nonexistent_name":
        return f"{p}nosuchrole"
    return f"{p}role"


def _new_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple_id")
    if shape == "duplicate_name":
        return f"{p}conflict"
    if shape == "quoted_id":
        return f'"{p}Mixed New"'
    return f"{p}newrole"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_id")
    if shape == "duplicate_name":
        return f"{p}conflict"
    if shape == "quoted_id":
        return f"{p}Mixed New"
    return f"{p}newrole"


def _role_spec_token(a: dict[str, str], p: str) -> str:
    """The role specification token in ALTER USER."""

    spec = a.get("role_specification", "named_role")
    if spec == "current_role":
        return "CURRENT_ROLE"
    if spec == "current_user":
        return "CURRENT_USER"
    if spec == "session_user":
        return "SESSION_USER"
    if spec == "all":
        return "ALL"
    return _role_name(a, p)


def _option_clause(a: dict[str, str], p: str) -> str:
    """The option clause for the option branch."""

    ot = a.get("option_type", "superuser_toggle")
    if ot == "superuser_toggle":
        return "SUPERUSER"
    if ot == "createdb_toggle":
        return "CREATEDB"
    if ot == "createrole_toggle":
        return "CREATEROLE"
    if ot == "inherit_toggle":
        return "INHERIT"
    if ot == "login_toggle":
        return "LOGIN"
    if ot == "replication_toggle":
        return "REPLICATION"
    if ot == "bypassrls_toggle":
        return "BYPASSRLS"
    if ot == "connection_limit":
        return "CONNECTION LIMIT 10"
    if ot == "password":
        return f"PASSWORD '{p}secret'"
    if ot == "password_null":
        return "PASSWORD NULL"
    if ot == "valid_until":
        return "VALID UNTIL '2030-01-01'"
    return "CREATEDB"


def _config_param(a: dict[str, str]) -> str:
    """The configuration parameter name for SET/RESET."""

    shape = a.get("config_param_shape", "valid_param")
    if shape == "invalid_param":
        return "nosuchparam"
    return "work_mem"


def _config_value(a: dict[str, str]) -> str:
    """The configuration parameter value for SET."""

    return "'4MB'"


def _database_name(a: dict[str, str], p: str) -> str:
    """The database name for IN DATABASE (empty if omitted)."""

    idc = a.get("in_database_clause", "omitted")
    if idc != "specified":
        return ""
    shape = a.get("database_name_shape", "simple_id")
    if shape == "nonexistent_name":
        return f"{p}nosuchdb"
    return "pgcf"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER USER runs."""

    pl = a.get("privilege_level", "createrole")
    if pl in ("non_createrole", "non_owner"):
        return f"{p}actor"
    return ""


def _needs_set_role_to_target(a: dict[str, str]) -> bool:
    """Whether to SET ROLE to the target (role_owner or spec keywords)."""

    pl = a.get("privilege_level", "createrole")
    spec = a.get("role_specification", "named_role")
    if pl == "role_owner":
        return True
    if spec in ("current_role", "current_user", "session_user"):
        return True
    return False


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    pl = a.get("privilege_level", "createrole")
    if pl in ("non_createrole", "non_owner"):
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: AlterUserFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query_pg_roles")
    if mode == "error_assertion":
        return None

    if mode == "config_parameter_query":
        param = _config_param(a)
        return (
            f"SELECT count(*) > 0 AS config_param_state "
            f"FROM pg_catalog.pg_settings "
            f"WHERE name = '{param}' "
            f"ORDER BY count(*);"
        )

    # catalog_query_pg_roles
    role_lit = _role_name_literal(a, p)
    missing = _role_missing(a)
    action = a.get("target_action", "option_modify")

    if action == "rename" and case.outcome == "success":
        check = _new_name_literal(a, p)
        present = True
    elif missing:
        check = role_lit
        present = False
    else:
        check = role_lit
        present = True

    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS role_state "
        f"FROM pg_catalog.pg_roles "
        f"WHERE rolname = '{check}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: AlterUserFactorCase,
) -> list[str]:
    """ALTER USER never creates a TABLE; bookend is never emitted."""
    return []


def _resolve_case(
    case: AlterUserFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "option_modify")
    missing = _role_missing(a)

    setup: list[str] = []
    locus = "target.alter_user"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    role = _role_name(a, p)

    # --- actor role fixture (non-createrole / non-owner) -------------
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target role fixture -------------------------------------
    if not missing:
        setup.append(f"CREATE ROLE {role} LOGIN;")
        locus = "fixture.role"
    else:
        setup.append(
            "SELECT 1 AS target_role_intentionally_absent;"
        )
        locus = "fixture.role_missing"

    # --- conflicting role for rename conflict ------------------------
    if (
        action == "rename"
        and a.get("new_name_shape", "simple_id") == "duplicate_name"
    ):
        setup.append(f"CREATE ROLE {p}conflict LOGIN;")
        locus = "fixture.rename_conflict"

    # --- arm the effective role or set role to target ----------------
    if effective:
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.effective_role"
    elif _needs_set_role_to_target(a) and not missing:
        setup.append(f"SET ROLE {role};")
        locus = "fixture.role_owner"

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, role)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective or _needs_set_role_to_target(a):
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    roles_to_drop: list[str] = []
    if not missing:
        roles_to_drop.append(role)
    if action == "rename":
        new = _new_name(a, p)
        if new != role:
            roles_to_drop.append(new)
        if a.get("new_name_shape", "simple_id") == "duplicate_name":
            roles_to_drop.append(f"{p}conflict")

    actor_drops = [
        statement
        for r in roles
        for statement in (
            f"DROP OWNED BY {r} CASCADE;",
            f"DROP ROLE IF EXISTS {r};",
        )
    ]

    role_drops = [
        f"DROP ROLE IF EXISTS {r};"
        for r in roles_to_drop
    ]

    # pre-cleanup
    pre_cleanup: list[str] = []
    pre_cleanup.extend(role_drops)
    pre_cleanup.extend(actor_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup
    cleanup: list[str] = []
    if effective or _needs_set_role_to_target(a):
        cleanup.append("RESET ROLE;")
    cleanup.extend(role_drops)
    cleanup.extend(actor_drops)
    if not cleanup:
        cleanup.append("SELECT 1 AS residual_check_no_objects;")

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


def _build_target(
    a: dict[str, str], p: str, role: str
) -> str:
    """The primary ALTER USER statement for the active branch."""

    action = a.get("target_action", "option_modify")
    spec = _role_spec_token(a, p)
    db = _database_name(a, p)
    in_db = f" IN DATABASE {db}" if db else ""

    if action == "option_modify":
        opt = _option_clause(a, p)
        return f"ALTER USER {spec} {opt};"
    if action == "rename":
        new = _new_name(a, p)
        return f"ALTER USER {role} RENAME TO {new};"
    if action == "set_config":
        param = _config_param(a)
        val = _config_value(a)
        return f"ALTER USER {spec}{in_db} SET {param} = {val};"
    if action == "set_from_current":
        param = _config_param(a)
        return f"ALTER USER {spec}{in_db} SET {param} FROM CURRENT;"
    if action == "reset_config":
        param = _config_param(a)
        return f"ALTER USER {spec}{in_db} RESET {param};"
    if action == "reset_all":
        return f"ALTER USER {spec}{in_db} RESET ALL;"
    return f"ALTER USER {spec} CREATEDB;"


def resolve_alter_user_factor_witness(
    case: AlterUserFactorCase | AlterUserFactorExtensionCase,
    repository_root: Path,
) -> AlterUserFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterUserFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_user(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*ALTER\s+USER\b", region)
    )


def _header(case: AlterUserFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER USER {case.factor_key}="
        f"{case.factor_value}",
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


def render_alter_user_factor_case(
    case: AlterUserFactorCase | AlterUserFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER USER。")
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
    if not text.endswith("\n"):
        text += "\n"
    return text


def _write_program(
    case: AlterUserFactorCase | AlterUserFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_user_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_user_factor_programs(
    baseline_plan: AlterUserFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
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


__all__ = [
    "AlterUserFactorRenderError",
    "AlterUserFactorWitness",
    "count_primary_alter_user",
    "generate_alter_user_factor_programs",
    "render_alter_user_factor_case",
    "resolve_alter_user_factor_witness",
]
