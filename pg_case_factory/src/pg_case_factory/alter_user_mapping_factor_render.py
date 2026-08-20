"""Render complete PostgreSQL 18.4 ALTER USER MAPPING factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER USER MAPPING is a foreign-data DDL statement: the target is a
``pg_catalog.pg_user_mapping`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_user_mapping`` /
``pg_catalog.pg_foreign_server`` (exempt from the file-prefix style gate).
No case creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is never
emitted.  Every catalog SELECT carries a top-level ``ORDER BY count(*)``
so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_user_mapping_factor_extension import (
    AlterUserMappingFactorExtensionCase,
    _present_failure_pair,
)
from .alter_user_mapping_factor_loop import (
    AlterUserMappingFactorCase,
    AlterUserMappingFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/user_mapping/"
    "alter_user_mapping.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/user_mapping/"
    "alter_user_mapping.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterUserMappingFactorRenderError(ValueError):
    """Raised when an ALTER USER MAPPING case cannot be rendered."""


@dataclass(frozen=True)
class AlterUserMappingFactorWitness:
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
    ext: AlterUserMappingFactorExtensionCase,
) -> AlterUserMappingFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "options")
    return AlterUserMappingFactorCase(
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
    case: AlterUserMappingFactorCase
    | AlterUserMappingFactorExtensionCase,
) -> AlterUserMappingFactorCase:
    if isinstance(case, AlterUserMappingFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterUserMappingFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _mapping_missing(a: dict[str, str]) -> bool:
    return a.get("object_state", "exists") == "not_exists"


def _server_missing(a: dict[str, str]) -> bool:
    return a.get("server_dependency") == "server_missing"


def _is_failure(a: dict[str, str]) -> bool:
    return _present_failure_pair(a) is not None


def _server_name(a: dict[str, str], p: str) -> str:
    """The server identifier in the ALTER USER MAPPING and fixtures."""

    if _server_missing(a):
        return f"{p}no_such_server"
    return f"{p}server"


def _keyword_token(user_spec: str) -> str:
    return {
        "user_keyword": "USER",
        "current_role": "CURRENT_ROLE",
        "current_user": "CURRENT_USER",
        "session_user": "SESSION_USER",
        "public": "PUBLIC",
    }.get(user_spec, user_spec)


def _for_clause(a: dict[str, str], p: str) -> str:
    """The FOR clause in the target ALTER USER MAPPING."""

    us = a.get("user_specification", "named_user")
    if us == "named_user":
        if _mapping_missing(a):
            return f"{p}no_such_user"
        return _mapping_target(a, p)
    return _keyword_token(us)


def _mapping_target(a: dict[str, str], p: str) -> str:
    """The explicit role the fixture user mapping is created for."""

    us = a.get("user_specification", "named_user")
    if us == "public":
        return "PUBLIC"
    pl = a.get("privilege_level", "server_owner")
    if pl == "server_owner":
        return f"{p}mappeduser"
    return f"{p}actor"


def _fixture_for(a: dict[str, str], p: str) -> str:
    """The FOR clause used by the fixture CREATE USER MAPPING."""

    us = a.get("user_specification", "named_user")
    if us == "named_user":
        if _mapping_missing(a):
            return f"{p}no_such_user"
        return _mapping_target(a, p)
    if us == "public":
        return "PUBLIC"
    pl = a.get("privilege_level", "server_owner")
    if pl == "server_owner":
        return _keyword_token(us)
    return f"{p}actor"


def _option_name(a: dict[str, str], p: str) -> str:
    """The option name token in the OPTIONS clause."""

    if a.get("option_name_shape") == "invalid_option":
        return f"{p}bogus_opt"
    return f"{p}opt"


def _options_clause(a: dict[str, str], p: str) -> str:
    """The OPTIONS ( ... ) body for the target ALTER USER MAPPING."""

    if a.get("duplicate_option_name") == "duplicate_option":
        return f"ADD {p}opt 'val1', ADD {p}opt 'val2'"
    opt = _option_name(a, p)
    clause = a.get("option_clause", "single_option_add")
    if clause == "single_option_set":
        return f"SET {opt} 'val'"
    if clause == "single_option_drop":
        return f"DROP {opt}"
    if clause == "multiple_options_mixed":
        return (
            f"ADD {opt}1 'val1', SET {opt}2 'val2', DROP {opt}3"
        )
    return f"ADD {opt} 'val'"


def _fixture_options(a: dict[str, str], p: str) -> str:
    """The OPTIONS body for the fixture CREATE USER MAPPING."""

    return f"ADD {p}opt 'initial'"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER USER MAPPING runs."""

    pl = a.get("privilege_level", "server_owner")
    if pl == "user_with_usage":
        return f"{p}actor"
    if pl == "non_privileged":
        return f"{p}actor"
    return ""


def _roles_to_create(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to CREATE in setup (before any SET ROLE)."""

    roles: list[str] = []
    pl = a.get("privilege_level", "server_owner")
    us = a.get("user_specification", "named_user")
    if pl in ("user_with_usage", "non_privileged"):
        roles.append(f"{p}actor")
    if (
        us == "named_user"
        and not _mapping_missing(a)
        and pl == "server_owner"
    ):
        roles.append(f"{p}mappeduser")
    return tuple(roles)


def _probe_select(
    case: AlterUserMappingFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query_pg_user_mapping")
    if mode == "error_assertion":
        return None

    server = _server_name(a, p)
    missing = _mapping_missing(a) or _server_missing(a)
    present = not missing

    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS mapping_state "
        f"FROM pg_catalog.pg_user_mapping "
        f"WHERE umserver = (SELECT oid FROM "
        f"pg_catalog.pg_foreign_server "
        f"WHERE srvname = '{server}') "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: AlterUserMappingFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    ALTER USER MAPPING is a foreign-data DDL statement: it never creates
    a TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore never
    emitted.
    """
    return []


def _resolve_case(
    case: AlterUserMappingFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    missing = _mapping_missing(a)
    server_missing = _server_missing(a)

    setup: list[str] = []
    locus = "target.alter_user_mapping"

    effective = _effective_role(a, p)
    roles = _roles_to_create(a, p)
    server = _server_name(a, p)
    for_clause = _for_clause(a, p)
    fixture_for = _fixture_for(a, p)

    # --- FDW + foreign server fixtures --------------------------------
    if not server_missing:
        setup.append(
            f"CREATE FOREIGN DATA WRAPPER {p}fdw;"
        )
        setup.append(
            f"CREATE SERVER {p}server "
            f"FOREIGN DATA WRAPPER {p}fdw;"
        )
        locus = "fixture.foreign_server"
    else:
        setup.append(
            "SELECT 1 AS target_foreign_server_intentionally_absent;"
        )
        locus = "fixture.foreign_server_missing"

    # --- role fixtures --------------------------------------------------
    for role in roles:
        if role == f"{p}actor":
            setup.append(
                f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
            )
        else:
            setup.append(f"CREATE ROLE {role} LOGIN;")
    if roles:
        locus = "fixture.privilege_state"

    # --- USAGE grant for user_with_usage --------------------------------
    if a.get("privilege_level") == "user_with_usage" and not server_missing:
        setup.append(
            f"GRANT USAGE ON FOREIGN SERVER {p}server "
            f"TO {p}actor;"
        )
        locus = "fixture.privilege_usage"

    # --- the target user mapping fixture --------------------------------
    if not missing and not server_missing:
        setup.append(
            f"CREATE USER MAPPING FOR {fixture_for} "
            f"SERVER {p}server "
            f"OPTIONS ({_fixture_options(a, p)});"
        )
        locus = "fixture.user_mapping"
    elif not server_missing:
        setup.append(
            "SELECT 1 AS target_user_mapping_intentionally_absent;"
        )
        locus = "fixture.user_mapping_missing"

    # --- arm the effective role -----------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_armed"

    # --- the primary target statement -----------------------------------
    target = _build_target(a, p, for_clause, server)

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -------------------------------------------
    cleanup_mode = a.get("cleanup_mode", "revert_option")
    user_mappings_to_drop = []
    if not missing and not server_missing:
        user_mappings_to_drop.append(fixture_for)

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    mapping_drops = [
        f"DROP USER MAPPING IF EXISTS FOR {target} "
        f"SERVER {p}server;"
        for target in user_mappings_to_drop
    ]
    server_drop = (
        f"DROP SERVER IF EXISTS {p}server CASCADE;"
        if not server_missing
        else f"DROP SERVER IF EXISTS {server} CASCADE;"
    )
    fdw_drop = f"DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw;"

    # pre-cleanup: mode-specific leading statement then teardown
    pre_cleanup: list[str] = []
    if cleanup_mode == "revert_option" and user_mappings_to_drop:
        pre_cleanup.append(
            f"ALTER USER MAPPING FOR {user_mappings_to_drop[0]} "
            f"SERVER {p}server OPTIONS (DROP {p}opt);"
        )
    elif cleanup_mode == "drop_user_mapping":
        pre_cleanup.extend(mapping_drops)
    # drop_server: no extra leading statement; CASCADE handles it

    pre_cleanup.extend(mapping_drops)
    pre_cleanup.append(server_drop)
    pre_cleanup.append(fdw_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: RESET ROLE, mappings, server, fdw, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(mapping_drops)
    cleanup.append(server_drop)
    cleanup.append(fdw_drop)
    cleanup.extend(role_drops)
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
    a: dict[str, str], p: str, for_clause: str, server: str
) -> str:
    """The primary ALTER USER MAPPING statement."""

    options = _options_clause(a, p)
    return (
        f"ALTER USER MAPPING FOR {for_clause} "
        f"SERVER {server} OPTIONS ({options});"
    )


def resolve_alter_user_mapping_factor_witness(
    case: AlterUserMappingFactorCase
    | AlterUserMappingFactorExtensionCase,
    repository_root: Path,
) -> AlterUserMappingFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterUserMappingFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_user_mapping(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*ALTER\s+USER\s+MAPPING\b", region)
    )


def _header(case: AlterUserMappingFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER USER MAPPING {case.factor_key}="
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


def render_alter_user_mapping_factor_case(
    case: AlterUserMappingFactorCase
    | AlterUserMappingFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER USER MAPPING。")
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
    case: AlterUserMappingFactorCase
    | AlterUserMappingFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_user_mapping_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_user_mapping_factor_programs(
    baseline_plan: AlterUserMappingFactorLoopPlan,
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
    "AlterUserMappingFactorRenderError",
    "AlterUserMappingFactorWitness",
    "count_primary_alter_user_mapping",
    "generate_alter_user_mapping_factor_programs",
    "render_alter_user_mapping_factor_case",
    "resolve_alter_user_mapping_factor_witness",
]
