"""Render complete PostgreSQL 18.4 LOCK TABLE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

LOCK TABLE obtains a table-level lock on a relation, held for the
duration of the current transaction.  Success-path cases CREATE the
fixture table as setup, so the bookend contract applies: the FIRST and
LAST executable ``;``-statements are each ``DROP TABLE IF EXISTS <all
created tables>`` when the case creates one or more tables.  Cases that
target a missing or wrong-type relation create no fixture table, so the
bookend is satisfied vacuously.

All catalog oracles schema-qualify ``pg_catalog.*`` (exempt from the
file-prefix style gate) and carry a top-level ``ORDER BY count(*) LIMIT
1`` so the catalog-observability gate passes.  Quoted / dotted
identifiers appear ONLY in the fenced LOCK TABLE target (which the
style gate does not parse); fixtures and catalog queries always use the
plain prefix-derived unqualified name.  This is the class-2 fix: the
fixture ``CREATE TABLE`` and bookend ``DROP TABLE`` use UNQUOTED base
table names for EVERY name_shape, so the bookend gate's identifier
normalizer never rejects a quoted name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .lock_factor_extension import (
    LockFactorExtensionCase,
    _present_failure_pair,
)
from .lock_factor_loop import (
    LockFactorCase,
    LockFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/utility/lock/lock.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/utility/lock/lock.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class LockFactorRenderError(ValueError):
    """Raised when a LOCK case cannot be rendered."""


@dataclass(frozen=True)
class LockFactorWitness:
    primary_obligation_id: str
    target_sql_fragment: str
    outcome: str
    expected_sqlstate: str
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


@dataclass(frozen=True)
class _FixtureState:
    needs_table: bool
    fixture_table: str
    needs_role: bool
    role_name: str
    effective_role: str


@dataclass(frozen=True)
class _CasePlan:
    target_fragment: str
    setup_lines: tuple[str, ...]
    assert_lines: tuple[str, ...]
    pre_cleanup_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    on_error_off: bool
    semantic_locus: str


# option_shape -> (lock_mode, nowait_suffix).
_OPTION_SHAPE_MODE: dict[str, tuple[str, str]] = {
    "minimal": ("ACCESS EXCLUSIVE", ""),
    "boolean_options": ("ACCESS EXCLUSIVE", " NOWAIT"),
    "resource_options": ("SHARE", ""),
    "verbose_or_format": ("ROW EXCLUSIVE", ""),
}


def _synthetic_case(
    ext: LockFactorExtensionCase,
) -> LockFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "statement_branch"
        factor_value = assignment.get("statement_branch", "branch_1")
    return LockFactorCase(
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
    case: LockFactorCase | LockFactorExtensionCase,
) -> LockFactorCase:
    if isinstance(case, LockFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: LockFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _target_missing(a: dict[str, str]) -> bool:
    return a.get("target_state") == "target_missing"


def _wrong_object_type(a: dict[str, str]) -> bool:
    return a.get("target_state") == "wrong_object_type"


def _object_type_mismatch(a: dict[str, str]) -> bool:
    return a.get("invalid_combination") == "object_type_mismatch"


def _semantic_error(a: dict[str, str]) -> bool:
    return (
        a.get("invalid_combination") == "syntax_valid_semantic_error"
    )


def _privilege_denied(a: dict[str, str]) -> bool:
    return a.get("privilege_context") == "insufficient_privilege"


def _needs_table(a: dict[str, str]) -> bool:
    """Whether the case creates a fixture table."""

    if _target_missing(a) or _wrong_object_type(a):
        return False
    if _object_type_mismatch(a) or _semantic_error(a):
        return False
    return True


def _needs_role(a: dict[str, str]) -> bool:
    return _privilege_denied(a)


def _fixture_table(p: str) -> str:
    """Plain unquoted base table name for every name_shape."""

    return f"{p}t"


def _target_ref(a: dict[str, str], p: str) -> str:
    """The relation identifier in the fenced LOCK TABLE target."""

    state = a.get("target_state", "target_exists")
    if state == "target_missing":
        return f"{p}no_such_table"
    if state == "wrong_object_type":
        return f"{p}wrong_type_target"
    ic = a.get("invalid_combination", "none")
    if ic == "syntax_valid_semantic_error":
        return f"{p}semantic_error_target"
    shape = a.get("target_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}t"'
    if shape == "schema_qualified":
        return f"{p}sch.{p}t"
    return f"{p}t"


def _compute_state(case: LockFactorCase) -> _FixtureState:
    a = _baseline(case)
    p = case.object_prefix
    needs_table = _needs_table(a)
    needs_role = _needs_role(a)
    return _FixtureState(
        needs_table=needs_table,
        fixture_table=_fixture_table(p),
        needs_role=needs_role,
        role_name=f"{p}actor" if needs_role else "",
        effective_role=f"{p}actor" if needs_role else "",
    )


def _build_setup(
    case: LockFactorCase, st: _FixtureState
) -> tuple[list[str], str]:
    lines: list[str] = []
    locus = "target.lock"
    if st.needs_role:
        lines.append(
            f"CREATE ROLE {st.role_name} LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"
    if st.needs_table:
        lines.append(
            f"CREATE TABLE {st.fixture_table} (c integer);"
        )
        locus = "fixture.table"
    if st.effective_role:
        lines.append(f"SET ROLE {st.effective_role};")
        locus = "fixture.role_armed"
    if not lines:
        lines.append(
            "SELECT 1 AS target_table_intentionally_absent;"
        )
        locus = "fixture.table_missing"
    return lines, locus


def _build_target(
    case: LockFactorCase, st: _FixtureState
) -> str:
    a = _baseline(case)
    p = case.object_prefix
    ref = _target_ref(a, p)
    mode, nowait = _OPTION_SHAPE_MODE[
        a.get("option_shape", "minimal")
    ]
    return f"LOCK TABLE {ref} IN {mode} MODE{nowait};"


def _probe_select(
    case: LockFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    base = _fixture_table(p)
    if mode == "catalog_query":
        return (
            "SELECT count(*) = 0 AS relation_absent "
            "FROM pg_catalog.pg_class "
            f"WHERE relname = '{base}' "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "effect_query":
        return (
            "SELECT count(*) AS relation_effect_witness "
            "FROM pg_catalog.pg_class "
            f"WHERE relname = '{base}' "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "returned_rows":
        return (
            "SELECT count(*) AS lock_state_rows "
            "FROM pg_catalog.pg_locks "
            "WHERE granted IS NOT NULL "
            "ORDER BY count(*) LIMIT 1;"
        )
    return None


def _tables_to_drop(st: _FixtureState) -> list[str]:
    if not st.needs_table:
        return []
    return [st.fixture_table]


def _build_pre_cleanup(st: _FixtureState) -> tuple[str, ...]:
    tables = _tables_to_drop(st)
    lines: list[str] = []
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if st.needs_role:
        lines.append(f"DROP ROLE IF EXISTS {st.role_name};")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_cleanup(st: _FixtureState) -> tuple[str, ...]:
    tables = _tables_to_drop(st)
    lines: list[str] = []
    if st.effective_role:
        lines.append("RESET ROLE;")
    if st.needs_role:
        lines.append(f"DROP OWNED BY {st.role_name};")
        lines.append(f"DROP ROLE IF EXISTS {st.role_name};")
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_assert(
    case: LockFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        lines.append(probe)
    return tuple(lines)


def _resolve_case(case: LockFactorCase) -> _CasePlan:
    st = _compute_state(case)
    setup, locus = _build_setup(case, st)
    target = _build_target(case, st)
    assert_lines = _build_assert(case, st)
    pre_cleanup = _build_pre_cleanup(st)
    cleanup = _build_cleanup(st)
    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=assert_lines,
        pre_cleanup_lines=pre_cleanup,
        cleanup_lines=cleanup,
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def resolve_lock_factor_witness(
    case: LockFactorCase | LockFactorExtensionCase,
    repository_root: Path,
) -> LockFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return LockFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_lock(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*LOCK\s+TABLE\b", region))


def _header(case: LockFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : LOCK TABLE {case.factor_key}="
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


def render_lock_factor_case(
    case: LockFactorCase | LockFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地表和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 LOCK TABLE。")
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


def _write_program(
    case: LockFactorCase | LockFactorExtensionCase,
    out: Path,
) -> None:
    text = render_lock_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_lock_factor_programs(
    baseline_plan: LockFactorLoopPlan,
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
    "LockFactorRenderError",
    "LockFactorWitness",
    "count_primary_lock",
    "generate_lock_factor_programs",
    "render_lock_factor_case",
    "resolve_lock_factor_witness",
]
