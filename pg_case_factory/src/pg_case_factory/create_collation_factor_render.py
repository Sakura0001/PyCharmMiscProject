"""Render complete PostgreSQL 18.4 CREATE COLLATION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE COLLATION is a catalog-row DDL statement: the target is a
``pg_catalog.pg_collation`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_collation`` (exempt
from the file-prefix style gate).  No case creates a TABLE, so the
bookend (DROP TABLE IF EXISTS) is never emitted.  Every catalog SELECT
carries a top-level ``ORDER BY count(*)`` so the catalog-observability
gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_collation_factor_extension import (
    CreateCollationFactorExtensionCase,
    _present_failure_pair,
)
from .create_collation_factor_loop import (
    CreateCollationFactorCase,
    CreateCollationFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/collation/"
    "create_collation.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/collation/"
    "create_collation.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateCollationFactorRenderError(ValueError):
    """Raised when a CREATE COLLATION case cannot be rendered."""


@dataclass(frozen=True)
class CreateCollationFactorWitness:
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
    ext: CreateCollationFactorExtensionCase,
) -> CreateCollationFactorCase:
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
    return CreateCollationFactorCase(
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
    case: CreateCollationFactorCase
    | CreateCollationFactorExtensionCase,
) -> CreateCollationFactorCase:
    if isinstance(case, CreateCollationFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateCollationFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _collation_name(a: dict[str, str], p: str) -> str:
    """The collation identifier in CREATE COLLATION and fixtures."""

    shape = a.get("collation_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}QCol"'
    if shape == "schema_qualified":
        return f"public.{p}col"
    return f"{p}col"


def _collation_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("collation_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}QCol"
    return f"{p}col"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "already_exists"
        and a.get("if_not_exists_clause") == "absent"
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _present(a: dict[str, str]) -> bool:
    """Whether the collation exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _build_params(
    a: dict[str, str], consumer: str
) -> str:
    """The params clause for define_with_params and builtin forms."""

    if consumer == "pg18_builtin_c":
        return "provider = builtin, locale = 'C'"
    if consumer == "pg18_builtin_c_utf8":
        return "provider = builtin, locale = 'C.UTF-8'"
    if consumer == "pg18_builtin_pg_unicode_fast":
        return "provider = builtin, locale = 'PG_UNICODE_FAST'"

    # define_with_params — check T5 failure factors first
    llc = a.get("locale_and_lc_conflict", "")
    if llc == "locale_with_lc_collate":
        return "LOCALE = 'C', LC_COLLATE = 'C'"
    if llc == "locale_with_lc_ctype":
        return "LOCALE = 'C', LC_CTYPE = 'C'"

    if a.get("locale_validity") == "invalid_locale_for_encoding":
        return "LOCALE = 'NOT_A_LOCALE'"

    # Build from T1-T4 factor values
    locale_setting = a.get("locale_setting", "LOCALE_only")
    provider = a.get("provider", "libc_default")
    det = a.get("deterministic_option", "true_default")
    rules = a.get("rules_setting", "no_rules")

    parts: list[str] = []
    if locale_setting == "LOCALE_only":
        parts.append("LOCALE = 'C'")
    elif locale_setting == "LC_COLLATE_LC_CTYPE_separate":
        parts.append("LC_COLLATE = 'C'")
        parts.append("LC_CTYPE = 'C'")
    elif locale_setting == "LOCALE_with_provider":
        parts.append("LOCALE = 'C'")

    if provider == "icu":
        parts.append("PROVIDER = icu")
    elif provider == "libc_default" and locale_setting == "LOCALE_with_provider":
        parts.append("PROVIDER = libc")

    if det == "false_icu_only":
        parts.append("DETERMINISTIC = false")

    if rules == "with_rules":
        parts.append("RULES = ''")

    return ", ".join(parts) if parts else "LOCALE = 'C'"


def _build_target(
    a: dict[str, str], p: str, consumer: str
) -> str:
    """The primary CREATE COLLATION statement."""

    name = _collation_name(a, p)
    ifne = a.get("if_not_exists_clause", "absent")
    ifne_clause = "IF NOT EXISTS " if ifne != "absent" else ""

    if consumer == "from_existing":
        fcs = a.get(
            "from_collation_shape", "existing_builtin_collation"
        )
        if fcs == "existing_builtin_collation":
            source = '"C"'
        elif fcs == "existing_user_collation":
            source = f"{p}src"
        else:
            source = f"{p}nosuch"
        return f"CREATE COLLATION {ifne_clause}{name} FROM {source};"

    params = _build_params(a, consumer)
    return f"CREATE COLLATION {ifne_clause}{name} ({params});"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target runs."""

    priv = a.get("privilege_level", "schema_owner_with_create")
    if priv == "non_schema_owner":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    priv = a.get("privilege_level", "schema_owner_with_create")
    if priv == "non_schema_owner":
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: CreateCollationFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "pg_collation_catalog_query")
    literal = _collation_literal(a, p)
    name = _collation_name(a, p)

    if mode == "actual_collation_usage":
        if _present(a):
            return f"SELECT 'a' COLLATE {name} AS usage_check;"
        return None

    # pg_collation_catalog_query
    if _present(a):
        cmp_op = ">"
    else:
        cmp_op = "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS collation_state "
        f"FROM pg_catalog.pg_collation "
        f"WHERE collname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: CreateCollationFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    consumer = case.consumer_action_id

    setup: list[str] = []
    locus = "target.create_collation"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    name = _collation_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- duplicate collation fixture ---------------------------------
    if _is_duplicate(a):
        setup.append(f'CREATE COLLATION {name} FROM "C";')
        locus = "fixture.duplicate_collation"

    # --- source collation fixture (from_existing) -------------------
    if consumer == "from_existing":
        fcs = a.get(
            "from_collation_shape", "existing_builtin_collation"
        )
        if fcs == "existing_user_collation":
            setup.append(f'CREATE COLLATION {p}src FROM "C";')
            locus = "fixture.source_collation"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, consumer)

    # --- oracle / SQLSTATE assertion ---------------------------------
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

    # --- cleanup construction -----------------------------------------
    collations_to_drop: list[str] = [name]
    if consumer == "from_existing":
        fcs = a.get(
            "from_collation_shape", "existing_builtin_collation"
        )
        if fcs == "existing_user_collation":
            collations_to_drop.append(f"{p}src")

    cleanup_mode = a.get("cleanup_mode", "DROP_COLLATION_IF_EXISTS")
    if cleanup_mode == "DROP_COLLATION":
        coll_drops = [
            f"DROP COLLATION {c};" for c in collations_to_drop
        ]
    elif cleanup_mode == "DROP_COLLATION_CASCADE":
        coll_drops = [
            f"DROP COLLATION {c} CASCADE;" for c in collations_to_drop
        ]
    else:
        coll_drops = [
            f"DROP COLLATION IF EXISTS {c};" for c in collations_to_drop
        ]

    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: always use IF EXISTS CASCADE (safe)
    pre_cleanup: list[str] = []
    pre_cleanup.append(f"DROP COLLATION IF EXISTS {name} CASCADE;")
    pre_cleanup.append(f"DROP COLLATION IF EXISTS {p}src CASCADE;")
    pre_cleanup.append(f"DROP COLLATION IF EXISTS {p}nosuch CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # cleanup: RESET ROLE, collations, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(coll_drops)
    cleanup.extend(role_drops)

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


def _header(case: CreateCollationFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE COLLATION {case.factor_key}="
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


def render_create_collation_factor_case(
    case: CreateCollationFactorCase
    | CreateCollationFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE COLLATION。")
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
    case: CreateCollationFactorCase
    | CreateCollationFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_collation_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_collation_factor_programs(
    baseline_plan: CreateCollationFactorLoopPlan,
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


def count_primary_create_collation(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+COLLATION\b", region)
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


def resolve_create_collation_factor_witness(
    case: CreateCollationFactorCase
    | CreateCollationFactorExtensionCase,
    repository_root: Path,
) -> CreateCollationFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateCollationFactorWitness(
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
    "CreateCollationFactorRenderError",
    "CreateCollationFactorWitness",
    "count_primary_create_collation",
    "generate_create_collation_factor_programs",
    "render_create_collation_factor_case",
    "resolve_create_collation_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
