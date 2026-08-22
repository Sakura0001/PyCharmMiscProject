"""Render complete PostgreSQL 18.4 CREATE ACCESS METHOD factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE ACCESS METHOD is a DDL statement: the target is a
``pg_catalog.pg_am`` catalog row, not a ``pg_class`` relation.  All
catalog oracles schema-qualify ``pg_catalog.pg_am`` / ``pg_proc`` /
``pg_class`` (exempt from the file-prefix style gate — they start with
``pg_``).  Cases that exercise the AM via ``CREATE TABLE ... USING`` or
``CREATE INDEX ... USING`` create a PLAIN unquoted fixture table whose
name carries the object prefix; the bookend (DROP TABLE IF EXISTS as
first and last ``;``-statement) is satisfied for those cases.  The
access-method name itself may be quoted (quoted_identifier /
reserved_word shapes) — it appears only in CREATE ACCESS METHOD and
USING clauses, never as a table identifier in FROM/JOIN.  Every catalog
SELECT carries a top-level ``ORDER BY count(*)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .create_access_method_factor_extension import (
    CreateAccessMethodFactorExtensionCase,
    _present_failure_pair,
)
from .create_access_method_factor_loop import (
    CreateAccessMethodFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/access_method/"
    "create_access_method.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/access_method/"
    "create_access_method.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateAccessMethodFactorRenderError(ValueError):
    """Raised when a CREATE ACCESS METHOD case cannot be rendered."""


@dataclass(frozen=True)
class CreateAccessMethodFactorWitness:
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
    ext: CreateAccessMethodFactorExtensionCase,
) -> CreateAccessMethodFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "create_access_method"
        )
    return CreateAccessMethodFactorCase(
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
    case: CreateAccessMethodFactorCase
    | CreateAccessMethodFactorExtensionCase,
) -> CreateAccessMethodFactorCase:
    if isinstance(
        case, CreateAccessMethodFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateAccessMethodFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _am_name(a: dict[str, str], p: str) -> str:
    """The access-method identifier in CREATE ACCESS METHOD."""

    if a.get("duplicate_am_name") == "with_builtin_am":
        return "btree"
    shape = a.get("am_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}Mixed Am"'
    if shape == "reserved_word":
        return f'"{p}select"'
    return f"{p}am"


def _am_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    if a.get("duplicate_am_name") == "with_builtin_am":
        return "btree"
    shape = a.get("am_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}Mixed Am"
    if shape == "reserved_word":
        return f"{p}select"
    return f"{p}am"


def _handler_name(a: dict[str, str], p: str) -> str:
    """The handler function identifier."""

    shape = a.get("handler_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}Mixed Handler"'
    return f"{p}handler"


def _handler_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for handler oracle queries."""

    shape = a.get("handler_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}Mixed Handler"
    return f"{p}handler"


def _type_clause(a: dict[str, str]) -> str:
    """The TYPE clause value (may be invalid)."""

    iamt = a.get("invalid_access_method_type", "none")
    if iamt == "unknown_type_value":
        return "UNKNOWN"
    return a.get("access_method_type", "INDEX")


def _is_builtin_am(a: dict[str, str]) -> bool:
    return a.get("duplicate_am_name") == "with_builtin_am"


def _am_already_exists(a: dict[str, str]) -> bool:
    return a.get("object_state") == "already_exists"


def _handler_missing(a: dict[str, str]) -> bool:
    return a.get("handler_function_state") == "not_exists"


def _handler_wrong_return(a: dict[str, str]) -> bool:
    return a.get("handler_function_state") == "wrong_return_type"


def _is_non_superuser(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_superuser"


def _actual_usage(a: dict[str, str]) -> bool:
    return a.get("verification_mode") == "pg_am_actual_usage"


def _needs_fixture_table(a: dict[str, str]) -> bool:
    """Whether the case creates a fixture table (triggers bookend)."""

    return _actual_usage(a) and a.get("expected_status") == "success"


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_non_superuser(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_non_superuser(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _handler_returns_type(a: dict[str, str]) -> str:
    if _handler_wrong_return(a):
        return "text"
    return "internal"


def _probe_select(
    case: CreateAccessMethodFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_am_catalog_query")
    if mode == "error_assertion":
        return None

    am_lit = _am_name_literal(a, p)
    present = case.outcome == "success"

    if mode == "pg_am_handler_check":
        handler_lit = _handler_name_literal(a, p)
        handler_present = not _handler_missing(a)
        cmp_op = ">" if handler_present else "="
        return (
            f"SELECT count(*) {cmp_op} 0 AS handler_state "
            f"FROM pg_catalog.pg_proc "
            f"WHERE proname = '{handler_lit}' "
            f"ORDER BY count(*);"
        )

    if mode == "pg_am_actual_usage" and present:
        return None  # actual-usage probe is inline in assert_lines

    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS am_state "
        f"FROM pg_catalog.pg_am "
        f"WHERE amname = '{am_lit}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: CreateAccessMethodFactorCase,
    a: dict[str, str],
) -> list[str]:
    """Fixture tables the case CREATEs (for bookend gate)."""

    if _needs_fixture_table(a):
        return [f"{case.object_prefix}fixture"]
    return []


def _resolve_case(
    case: CreateAccessMethodFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_access_method"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    am = _am_name(a, p)
    handler = _handler_name(a, p)
    type_clause = _type_clause(a)
    tables = _tables_to_drop(case, a)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"

    # --- handler function fixture ------------------------------------
    if not _handler_missing(a):
        returns = _handler_returns_type(a)
        setup.append(
            f"CREATE FUNCTION {handler}(internal) RETURNS {returns} "
            f"AS 'MODULE_PATHNAME', 'cam_handler' LANGUAGE C;"
        )
        locus = "fixture.handler_function"

    # --- pre-existing AM for duplicate_am_name=with_existing_am ----
    if (
        _am_already_exists(a)
        and not _is_builtin_am(a)
    ):
        setup.append(
            f"CREATE ACCESS METHOD {am} TYPE {type_clause} "
            f"HANDLER {handler};"
        )
        locus = "fixture.duplicate_am"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, am, handler, type_clause)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )

    # actual-usage probe (creates table/index using the AM)
    if _needs_fixture_table(a):
        access_type = a.get("access_method_type", "INDEX")
        fixture = f"{p}fixture"
        if access_type == "INDEX":
            assert_lines.append(
                f"CREATE TABLE {fixture} (id integer);"
            )
            assert_lines.append(
                f"CREATE INDEX {p}idx ON {fixture} USING {am};"
            )
            assert_lines.append(
                f"SELECT count(*) > 0 AS am_usage "
                f"FROM pg_catalog.pg_class "
                f"WHERE relname = '{p}idx' "
                f"ORDER BY count(*);"
            )
        else:
            assert_lines.append(
                f"CREATE TABLE {fixture} (id integer) USING {am};"
            )
            assert_lines.append(
                f"SELECT count(*) > 0 AS am_usage "
                f"FROM pg_catalog.pg_class "
                f"WHERE relname = '{fixture}' "
                f"ORDER BY count(*);"
            )

    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the granted_role
    # fixture is created by setup, so on a fresh database the role does
    # not exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  The DROP TABLE IF EXISTS anchor is first in
    # pre-cleanup and last in cleanup, satisfying the table-bookend gate.
    specs: list[DropSpec] = []
    if not _is_builtin_am(a):
        specs.append(DropSpec("ACCESS METHOD", am))
    specs.append(DropSpec("FUNCTION", handler, "(internal)"))
    table_names = list(tables)
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
        drop_owned=bool(role_list),
        reset_role=bool(effective),
    )
    pre_cleanup = list(pre_bookend.statements)
    cleanup = list(cln_bookend.statements)

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
    a: dict[str, str],
    p: str,
    am: str,
    handler: str,
    type_clause: str,
) -> str:
    """The primary CREATE ACCESS METHOD statement."""

    return (
        f"CREATE ACCESS METHOD {am} TYPE {type_clause} "
        f"HANDLER {handler};"
    )


def resolve_create_access_method_factor_witness(
    case: CreateAccessMethodFactorCase
    | CreateAccessMethodFactorExtensionCase,
    repository_root: Path,
) -> CreateAccessMethodFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateAccessMethodFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_access_method(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+ACCESS\s+METHOD\b", region
        )
    )


def _header(case: CreateAccessMethodFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE ACCESS METHOD {case.factor_key}="
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


def render_create_access_method_factor_case(
    case: CreateAccessMethodFactorCase
    | CreateAccessMethodFactorExtensionCase,
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
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE ACCESS METHOD。"
    )
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
    case: CreateAccessMethodFactorCase
    | CreateAccessMethodFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_access_method_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_access_method_factor_programs(
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


__all__ = [
    "CreateAccessMethodFactorRenderError",
    "CreateAccessMethodFactorWitness",
    "count_primary_create_access_method",
    "generate_create_access_method_factor_programs",
    "render_create_access_method_factor_case",
    "resolve_create_access_method_factor_witness",
]
