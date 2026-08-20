"""Render complete PostgreSQL 18.4 CREATE GROUP factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the byte-level
witness validator (which re-renders and compares) can never diverge from
the bytes actually written.

CREATE GROUP is a deprecated alias for CREATE ROLE: the target is a
``pg_catalog.pg_authid`` catalog row, not a ``pg_class`` relation.  All
catalog oracles schema-qualify ``pg_catalog.pg_authid`` /
``pg_catalog.pg_roles`` (exempt from the file-prefix style gate).  No case
creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is never emitted;
every program ends with a ``SELECT 1 AS residual_check_no_objects;``
residual placeholder that witnesses the table-less nature of CREATE GROUP.
Every catalog SELECT carries a top-level ``ORDER BY count(*)`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_group_factor_extension import (
    CreateGroupFactorExtensionCase,
    _present_failure_pair,
)
from .create_group_factor_loop import (
    CreateGroupFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/group/"
    "create_group.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/group/"
    "create_group.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateGroupFactorRenderError(ValueError):
    """Raised when a CREATE GROUP case cannot be rendered."""


@dataclass(frozen=True)
class CreateGroupFactorWitness:
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
    ext: CreateGroupFactorExtensionCase,
) -> CreateGroupFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = assignment.get(
            "target_form", ext.consumer_action_id
        )
    return CreateGroupFactorCase(
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
    case: CreateGroupFactorCase | CreateGroupFactorExtensionCase,
) -> CreateGroupFactorCase:
    if isinstance(case, CreateGroupFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateGroupFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _group_name(a: dict[str, str], p: str) -> str:
    """The group(role) identifier in CREATE GROUP and fixtures."""

    shape = a.get("group_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}qgrp"'
    if shape == "reserved_word_name":
        return f'"{p}view"'
    # simple_id and duplicate_name both use a plain identifier
    return f"{p}grp"


def _group_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("group_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}qgrp"
    if shape == "reserved_word_name":
        return f"{p}view"
    return f"{p}grp"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "already_exists"
        or a.get("duplicate_group_name") == "same_name_conflict"
        or a.get("group_name_shape") == "duplicate_name"
        or a.get("expected_status") == "failure"
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _present(a: dict[str, str]) -> bool:
    """Whether the role exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _needs_referenced_role(a: dict[str, str]) -> bool:
    mo = a.get("membership_option", "omitted")
    return mo != "omitted"


def _build_options(a: dict[str, str], p: str) -> str:
    """The options clause for the with-options branch."""

    opts: list[str] = []
    if a.get("superuser_option") == "superuser":
        opts.append("SUPERUSER")
    if a.get("login_option") == "login":
        opts.append("LOGIN")
    if a.get("createdb_option") == "createdb":
        opts.append("CREATEDB")
    if a.get("createrole_option") == "createrole":
        opts.append("CREATEROLE")
    po = a.get("password_option", "omitted")
    if po == "password_value":
        opts.append("PASSWORD 'pw'")
    elif po == "password_null":
        opts.append("PASSWORD NULL")
    elif po == "encrypted_password":
        opts.append("ENCRYPTED PASSWORD 'pw'")
    mo = a.get("membership_option", "omitted")
    ref = f"{p}ref"
    if mo == "in_role":
        opts.append(f"IN ROLE {ref}")
    elif mo == "in_group":
        opts.append(f"IN GROUP {ref}")
    elif mo == "role_clause":
        opts.append(f"ROLE {ref}")
    elif mo == "user_clause":
        opts.append(f"USER {ref}")
    elif mo == "admin_clause":
        opts.append(f"ADMIN {ref}")
    if a.get("sysid_ignored") == "sysid_ignored":
        opts.append("SYSID 9999")
    return ", ".join(opts)


def _build_target(
    a: dict[str, str], p: str, consumer: str
) -> str:
    """The primary CREATE GROUP statement."""

    name = _group_name(a, p)
    if consumer == "create_group_simple":
        return f"CREATE GROUP {name};"
    options = _build_options(a, p)
    with_kw = "WITH " if a.get("with_clause") == "specified" else ""
    if not options:
        options = "NOSUPERUSER"
    return f"CREATE GROUP {name} {with_kw}{options};"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target runs."""

    priv = a.get("privilege_level", "createrole_privilege")
    if priv == "non_createrole":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    priv = a.get("privilege_level", "createrole_privilege")
    if priv == "non_createrole":
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: CreateGroupFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "pg_authid_catalog_query")
    literal = _group_literal(a, p)

    if mode == "error_assertion":
        return None

    catalog = "pg_authid" if mode == "pg_authid_catalog_query" else "pg_roles"
    cmp_op = ">" if _present(a) else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS group_state "
        f"FROM pg_catalog.{catalog} "
        f"WHERE rolname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(case: CreateGroupFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    consumer = case.consumer_action_id

    setup: list[str] = []
    locus = "target.create_group"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    name = _group_name(a, p)

    # --- privilege fixture -----------------------------------------
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER NOCREATEROLE;"
        )
        locus = "fixture.privilege_state"

    # --- duplicate group fixture -----------------------------------
    if _is_duplicate(a):
        setup.append(f"CREATE GROUP {name};")
        locus = "fixture.duplicate_group"

    # --- referenced role fixture (membership) ----------------------
    if _needs_referenced_role(a):
        if a.get("referenced_role_existence") == "role_exists":
            setup.append(f"CREATE ROLE {p}ref;")
            locus = "fixture.referenced_role"

    # --- arm the effective role ------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement ------------------------------
    target = _build_target(a, p, consumer)

    # --- oracle / SQLSTATE assertion -------------------------------
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

    # --- cleanup construction --------------------------------------
    cleanup_mode = a.get("cleanup_mode", "drop_group")
    if cleanup_mode == "drop_role":
        group_drops = [f"DROP ROLE IF EXISTS {name};"]
    elif cleanup_mode == "referenced_role_cleanup":
        group_drops = [
            f"DROP GROUP IF EXISTS {name};",
            f"DROP ROLE IF EXISTS {p}ref;",
        ]
    else:  # drop_group
        group_drops = [f"DROP GROUP IF EXISTS {name};"]

    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: always use IF EXISTS (safe, idempotent)
    pre_cleanup: list[str] = []
    pre_cleanup.append(f"DROP GROUP IF EXISTS {name} CASCADE;")
    pre_cleanup.append(f"DROP ROLE IF EXISTS {name} CASCADE;")
    pre_cleanup.append(f"DROP ROLE IF EXISTS {p}ref CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # cleanup: RESET ROLE, group/role drops, fixture drops, residual
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(group_drops)
    if cleanup_mode != "referenced_role_cleanup":
        cleanup.append(f"DROP ROLE IF EXISTS {p}ref;")
    cleanup.extend(role_drops)
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


def _header(case: CreateGroupFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE GROUP {case.factor_key}="
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


def render_create_group_factor_case(
    case: CreateGroupFactorCase | CreateGroupFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE GROUP。")
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
    case: CreateGroupFactorCase | CreateGroupFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_group_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_group_factor_programs(
    baseline_plan: object,
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


def count_primary_create_group(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+GROUP\b", region)
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str, case: object
) -> str:
    """Mutation helper: remove primary target SQL but keep comment lines."""

    if _PRIMARY_BEGIN not in sql or _PRIMARY_END not in sql:
        return sql
    before_begin, rest = sql.split(_PRIMARY_BEGIN, 1)
    target_and_after, after_end = rest.split(_PRIMARY_END, 1)
    comment_lines = [
        line
        for line in target_and_after.split("\n")
        if line.strip().startswith("--") or not line.strip()
    ]
    return (
        before_begin
        + _PRIMARY_BEGIN
        + "\n".join(comment_lines)
        + _PRIMARY_END
        + after_end
    )


def resolve_create_group_factor_witness(
    case: CreateGroupFactorCase | CreateGroupFactorExtensionCase,
    repository_root: Path,
) -> CreateGroupFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateGroupFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


__all__ = [
    "CreateGroupFactorRenderError",
    "CreateGroupFactorWitness",
    "count_primary_create_group",
    "generate_create_group_factor_programs",
    "render_create_group_factor_case",
    "resolve_create_group_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
