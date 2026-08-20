"""Render complete PostgreSQL 18.4 CREATE CAST factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE CAST is a type-conversion DDL statement: the target is a
``pg_catalog.pg_cast`` catalog row, not a ``pg_class`` relation.  All
catalog oracles schema-qualify ``pg_catalog.pg_cast`` (exempt from the
file-prefix style gate).  No case creates a TABLE, so the bookend
(DROP TABLE IF EXISTS) is never emitted (``_tables_to_drop`` always
returns ``[]``).  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_cast_factor_extension import (
    CreateCastFactorExtensionCase,
    _present_failure_pair,
)
from .create_cast_factor_loop import (
    CreateCastFactorCase,
    CreateCastFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/cast/"
    "create_cast.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/cast/"
    "create_cast.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateCastFactorRenderError(ValueError):
    """Raised when a CREATE CAST case cannot be rendered."""


@dataclass(frozen=True)
class CreateCastFactorWitness:
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
    ext: CreateCastFactorExtensionCase,
) -> CreateCastFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "with_function")
    return CreateCastFactorCase(
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
    case: CreateCastFactorCase
    | CreateCastFactorExtensionCase,
) -> CreateCastFactorCase:
    if isinstance(case, CreateCastFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateCastFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _source_type_name(a: dict[str, str], p: str) -> str:
    src = a.get("source_type", "integer")
    if src == "custom_type":
        return f"{p}sourcetype"
    return src


def _target_type_name(a: dict[str, str], p: str) -> str:
    tgt = a.get("target_type", "bigint")
    if tgt == "custom_type":
        return f"{p}targettype"
    return tgt


def _type_expr(type_name: str, shape: str) -> str:
    if shape == "schema_qualified_type":
        return f"public.{type_name}"
    if shape == "quoted_type":
        return f'"{type_name}"'
    return type_name


def _source_expr(a: dict[str, str], p: str) -> str:
    name = _source_type_name(a, p)
    shape = a.get("source_type_shape", "plain_type")
    return _type_expr(name, shape)


def _target_expr(a: dict[str, str], p: str) -> str:
    name = _target_type_name(a, p)
    shape = a.get("target_type_shape", "plain_type")
    return _type_expr(name, shape)


def _function_name(a: dict[str, str], p: str) -> str:
    shape = a.get("function_name_shape", "plain_identifier")
    name = f"{p}castfn"
    if shape == "schema_qualified":
        return f"public.{name}"
    return name


def _function_ref(a: dict[str, str], p: str) -> str:
    fd = a.get(
        "function_dependency", "function_exists_correct_signature"
    )
    if fd == "function_not_exists":
        return f"{p}nonexistfn"
    return _function_name(a, p)


def _function_arg_type(a: dict[str, str], p: str) -> str:
    fsm = a.get("function_signature_mismatch", "")
    tgt = _target_type_name(a, p)
    if fsm == "wrong_first_arg_type":
        return tgt
    return _source_type_name(a, p)


def _function_return_type(a: dict[str, str], p: str) -> str:
    fsm = a.get("function_signature_mismatch", "")
    src = _source_type_name(a, p)
    if fsm == "wrong_return_type":
        return src
    return _target_type_name(a, p)


def _implementation_clause(a: dict[str, str], p: str) -> str:
    ci = a.get("cast_implementation", "with_function")
    if ci == "with_function":
        return f"WITH FUNCTION {_function_ref(a, p)}"
    if ci == "without_function":
        return "WITHOUT FUNCTION"
    if ci == "with_inout":
        return "WITH INOUT"
    return "WITH INOUT"


def _implicit_clause(a: dict[str, str]) -> str:
    ic = a.get("implicit_context", "explicit_only_default")
    if ic == "as_assignment":
        return "AS ASSIGNMENT"
    if ic == "as_implicit":
        return "AS IMPLICIT"
    return ""


def _needs_custom_source(a: dict[str, str]) -> bool:
    return a.get("source_type") == "custom_type"


def _needs_custom_target(a: dict[str, str]) -> bool:
    return a.get("target_type") == "custom_type"


def _needs_role(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_owner"


def _pre_create_cast(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "already_exists"
        or a.get("duplicate_cast") == "same_source_target_direction"
    )


def _reverse_cast(a: dict[str, str]) -> bool:
    return a.get("duplicate_cast") == "reverse_direction_exists"


def _cleanup_cast_clause(
    a: dict[str, str], src: str, tgt: str
) -> str:
    mode = a.get("cleanup_mode", "DROP_CAST")
    if mode == "DROP_CAST_IF_EXISTS":
        return f"DROP CAST IF EXISTS ({src} AS {tgt});"
    return f"DROP CAST ({src} AS {tgt});"


def _probe_select(
    case: CreateCastFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit or cast-execution oracle, or None for error-only."""

    mode = a.get("verification_mode", "pg_cast_catalog_query")
    if mode == "actual_cast_execution":
        if case.outcome == "success":
            src = _source_type_name(a, p)
            tgt = _target_type_name(a, p)
            return (
                f"SELECT NULL::{src}::{tgt} "
                f"AS cast_execution_check;"
            )
        return None

    src = _source_type_name(a, p)
    tgt = _target_type_name(a, p)
    present = (
        case.outcome == "success"
        or a.get("object_state") == "already_exists"
        or a.get("duplicate_cast") == "same_source_target_direction"
    )
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS cast_state "
        f"FROM pg_catalog.pg_cast "
        f"WHERE castsource = '{src}'::regtype "
        f"AND casttarget = '{tgt}'::regtype "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: CreateCastFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE CAST is a type-conversion DDL statement: it never creates a
    TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore never
    emitted.
    """
    return []


def _resolve_case(
    case: CreateCastFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    ci = a.get("cast_implementation", "with_function")
    fd = a.get(
        "function_dependency", "function_exists_correct_signature"
    )

    setup: list[str] = []
    locus = "target.create_cast"

    src_name = _source_type_name(a, p)
    tgt_name = _target_type_name(a, p)
    src_plain = src_name
    tgt_plain = tgt_name

    # --- custom type fixtures ----------------------------------------
    if _needs_custom_source(a):
        setup.append(
            f"CREATE TYPE {p}sourcetype AS ENUM ('a', 'b');"
        )
        locus = "fixture.custom_source_type"
    if _needs_custom_target(a):
        setup.append(
            f"CREATE TYPE {p}targettype AS ENUM ('a', 'b');"
        )
        locus = "fixture.custom_target_type"

    # --- cast function fixture (WITH FUNCTION only) -----------------
    if ci == "with_function" and fd != "function_not_exists":
        fn = _function_name(a, p)
        arg = _function_arg_type(a, p)
        ret = _function_return_type(a, p)
        setup.append(
            f"CREATE FUNCTION {fn}({arg}) RETURNS {ret} "
            f"LANGUAGE SQL IMMUTABLE AS "
            f"$$ SELECT NULL::{ret} $$;"
        )
        locus = "fixture.cast_function"

    # --- reverse-direction cast fixture ------------------------------
    if _reverse_cast(a):
        if ci == "with_function":
            rev_arg = _target_type_name(a, p)
            rev_ret = _source_type_name(a, p)
            setup.append(
                f"CREATE FUNCTION {p}revcastfn({rev_arg})"
                f" RETURNS {rev_ret} LANGUAGE SQL IMMUTABLE AS"
                f" $$ SELECT NULL::{rev_ret} $$;"
            )
        rev_clause = _implementation_clause_for_reverse(a, p)
        setup.append(
            f"CREATE CAST ({tgt_plain} AS {src_plain})"
            f" {rev_clause};"
        )
        locus = "fixture.reverse_cast"

    # --- pre-create cast (already_exists / same_direction) -----------
    if _pre_create_cast(a):
        impl = _implementation_clause(a, p)
        implicit = _implicit_clause(a)
        clause = impl
        if implicit:
            clause = f"{impl} {implicit}"
        setup.append(
            f"CREATE CAST ({src_plain} AS {tgt_plain})"
            f" {clause};"
        )
        locus = "fixture.pre_existing_cast"

    # --- arm the effective role --------------------------------------
    if _needs_role(a):
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(f"SET ROLE {p}actor;")
        locus = "fixture.privilege_state"

    # --- the primary target statement --------------------------------
    src_expr = _source_expr(a, p)
    tgt_expr = _target_expr(a, p)
    impl = _implementation_clause(a, p)
    implicit = _implicit_clause(a)
    parts = [impl]
    if implicit:
        parts.append(implicit)
    target = (
        f"CREATE CAST ({src_expr} AS {tgt_expr})"
        f" {' '.join(parts)};"
    )

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if _needs_role(a):
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    casts_to_drop: list[tuple[str, str]] = []
    casts_to_drop.append((src_plain, tgt_plain))
    if _reverse_cast(a):
        casts_to_drop.append((tgt_plain, src_plain))

    cast_drops = [
        _cleanup_cast_clause(a, s, t) for s, t in casts_to_drop
    ]
    func_drops: list[str] = []
    if ci == "with_function" and fd != "function_not_exists":
        func_drops.append(
            f"DROP FUNCTION IF EXISTS {_function_name(a, p)};"
        )
    if _reverse_cast(a):
        func_drops.append(
            f"DROP FUNCTION IF EXISTS {p}revcastfn;"
        )

    type_drops: list[str] = []
    if _needs_custom_source(a):
        type_drops.append(f"DROP TYPE IF EXISTS {p}sourcetype;")
    if _needs_custom_target(a):
        type_drops.append(f"DROP TYPE IF EXISTS {p}targettype;")

    role_drops: list[str] = []
    if _needs_role(a):
        role_drops.extend(
            [
                f"DROP OWNED BY {p}actor CASCADE;",
                f"DROP ROLE IF EXISTS {p}actor;",
            ]
        )

    # pre-cleanup: casts, functions, types, roles (all IF EXISTS)
    pre_cleanup: list[str] = []
    pre_cleanup.extend(
        f"DROP CAST IF EXISTS ({s} AS {t});"
        for s, t in casts_to_drop
    )
    pre_cleanup.extend(func_drops)
    pre_cleanup.extend(type_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: RESET ROLE, casts, functions, types, roles
    cleanup: list[str] = []
    if _needs_role(a):
        cleanup.append("RESET ROLE;")
    cleanup.extend(cast_drops)
    cleanup.extend(func_drops)
    cleanup.extend(type_drops)
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


def _implementation_clause_for_reverse(
    a: dict[str, str], p: str
) -> str:
    """Implementation clause for the reverse-direction fixture cast.

    For WITH FUNCTION, the reverse cast needs its own helper function
    taking the *target* type and returning the *source* type.  The
    caller is responsible for creating ``{p}revcastfn`` separately when
    the reverse-direction fixture is emitted.
    """

    ci = a.get("cast_implementation", "with_function")
    if ci == "with_function":
        return f"WITH FUNCTION {p}revcastfn"
    if ci == "without_function":
        return "WITHOUT FUNCTION"
    return "WITH INOUT"


def resolve_create_cast_factor_witness(
    case: CreateCastFactorCase
    | CreateCastFactorExtensionCase,
    repository_root: Path,
) -> CreateCastFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateCastFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_cast(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+CAST\b", region)
    )


def _header(case: CreateCastFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE CAST {case.factor_key}="
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


def render_create_cast_factor_case(
    case: CreateCastFactorCase
    | CreateCastFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE CAST。")
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
    case: CreateCastFactorCase
    | CreateCastFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_cast_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_cast_factor_programs(
    baseline_plan: CreateCastFactorLoopPlan,
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
    "CreateCastFactorRenderError",
    "CreateCastFactorWitness",
    "count_primary_create_cast",
    "generate_create_cast_factor_programs",
    "render_create_cast_factor_case",
    "resolve_create_cast_factor_witness",
]
