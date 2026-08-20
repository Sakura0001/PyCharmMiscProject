"""Render complete PostgreSQL 18.4 VALUES factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

VALUES is a DML read-only query statement: a table-value constructor
(``VALUES (expr, ...), ...``) with no ``FROM`` clause.  The combination
matrix declares ``target_relation_coverage`` as ``not_applicable``
("VALUES has no FROM target relation") and ``table_coverage`` as
``not_applicable`` ("VALUES does not read or mutate a table unless
embedded by another statement").  Consequently VALUES renders as a
**pure literal query**: no ``CREATE TABLE`` fixtures, no ``CREATE ROLE``
fixtures, no catalog probe.  The verification oracle is the SQLSTATE
assertion only (``verification_query_template`` is empty in the matrix).

Factor → SQL mapping (observable in target bytes):

  * ``data_or_query_shape`` — row structure (minimal / explicit_values /
    query_source / cte_source).
  * ``expression_shape`` — expression type in each row (literal /
    column_reference / function_call / subquery_expression).
  * ``result_shape`` — column count (none=1, returning_expression=2,
    returning_star=3, rowset_projection=2 with 3 rows).
  * ``with_clause`` — WITH prefix (absent / non_recursive / recursive).
  * ``condition_shape`` — ORDER BY clause (none / simple_predicate /
    join_or_match_condition / cursor_or_conflict_target).
  * ``cleanup_mode`` — cleanup phase (rollback / drop_objects /
    reset_state).

Factors not observable in target bytes (metadata-only, provisional):
``target_relation_state``, ``name_shape``, ``privilege_context``,
``constraint_boundary``, ``dependency_state``,
``invalid_combination``, ``expected_status``, ``statement_branch``,
``verification_mode``.  SQLSTATEs are provisional (no-DB static phase).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .values_factor_extension import (
    ValuesFactorExtensionCase,
    _present_failure_pair,
)
from .values_factor_loop import (
    ValuesFactorCase,
    ValuesFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/dml/query/"
    "values.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/dml/query/"
    "values.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class ValuesFactorRenderError(ValueError):
    """Raised when a VALUES case cannot be rendered."""


@dataclass(frozen=True)
class ValuesFactorWitness:
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
    ext: ValuesFactorExtensionCase,
) -> ValuesFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "values")
    return ValuesFactorCase(
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
    case: ValuesFactorCase | ValuesFactorExtensionCase,
) -> ValuesFactorCase:
    if isinstance(case, ValuesFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: ValuesFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _with_prefix(a: dict[str, str], p: str) -> str:
    """The WITH clause prefix for the VALUES statement."""

    doqs = a.get("data_or_query_shape", "explicit_values")
    wc = a.get("with_clause", "absent")

    if doqs == "cte_source" or wc != "absent":
        if wc == "recursive":
            return (
                f"WITH RECURSIVE {p}cte AS ("
                f"SELECT 1 AS val "
                f"UNION ALL "
                f"SELECT val + 1 FROM {p}cte WHERE val < 5)\n"
            )
        # non_recursive and cte_source both declare a simple CTE.
        return f"WITH {p}cte AS (SELECT 1 AS val)\n"
    return ""


def _values_expression(a: dict[str, str], p: str) -> str:
    """The expression type in a VALUES row column."""

    es = a.get("expression_shape", "literal")
    if es == "literal":
        return "1"
    if es == "column_reference":
        # Standalone VALUES cannot reference input columns; map to a
        # literal.  The factor value is recorded in case metadata.
        return "1"
    if es == "function_call":
        return "abs(1)"
    if es == "subquery_expression":
        return "(SELECT 1)"
    return "1"


def _column_count(a: dict[str, str]) -> int:
    """Column count governed by result_shape."""

    rs = a.get("result_shape", "none")
    if rs == "returning_star":
        return 3
    if rs == "returning_expression":
        return 2
    if rs == "rowset_projection":
        return 2
    return 1  # none


def _values_row(a: dict[str, str], p: str) -> str:
    """One VALUES row: (expr, expr, ...)."""

    expr = _values_expression(a, p)
    count = _column_count(a)
    return "(" + ", ".join([expr] * count) + ")"


def _values_rows(a: dict[str, str], p: str) -> str:
    """The VALUES rows governed by data_or_query_shape."""

    doqs = a.get("data_or_query_shape", "explicit_values")
    if doqs == "query_source":
        return "((SELECT 1 AS val))"
    if doqs == "cte_source":
        return f"((SELECT val FROM {p}cte))"
    row = _values_row(a, p)
    if doqs == "minimal":
        return row
    # explicit_values: two rows (three for rowset_projection).
    if a.get("result_shape") == "rowset_projection":
        return f"{row}, {row}, {row}"
    return f"{row}, {row}"


def _order_by_clause(a: dict[str, str]) -> str:
    """ORDER BY clause governed by condition_shape."""

    cs = a.get("condition_shape", "simple_predicate")
    if cs == "none":
        return ""
    if cs == "cursor_or_conflict_target":
        return "ORDER BY column1 DESC LIMIT 1"
    if cs == "join_or_match_condition":
        if _column_count(a) >= 2:
            return "ORDER BY column1, column2"
        return "ORDER BY column1"
    # simple_predicate
    return "ORDER BY column1"


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary VALUES statement."""

    with_prefix = _with_prefix(a, p)
    rows = _values_rows(a, p)
    order_by = _order_by_clause(a)
    parts: list[str] = [f"{with_prefix}VALUES {rows}"]
    if order_by:
        parts.append(f" {order_by}")
    parts.append(";")
    return "".join(parts)


def _resolve_case(case: ValuesFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    # No fixtures: VALUES is a pure literal query (no CREATE TABLE,
    # no CREATE ROLE, no CREATE SEQUENCE).  The combination matrix
    # declares target_relation_coverage and table_coverage as
    # not_applicable.
    setup: list[str] = []
    locus = "target.values"

    target = _build_target(a, p)

    # Oracle / SQLSTATE assertion (no catalog probe for pure literal).
    assert_lines: list[str] = [
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    ]

    # Cleanup construction governed by cleanup_mode (mirrors COPY).
    cm = a.get("cleanup_mode", "drop_objects")
    cleanup: list[str] = []
    if cm == "rollback":
        cleanup.append("ROLLBACK;")
    elif cm == "reset_state":
        cleanup.append("RESET search_path;")
    # drop_objects: nothing to drop (no objects created).
    if not cleanup:
        cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Pre-cleanup: residual check only (no objects to clean upfront).
    pre_cleanup: list[str] = [
        "SELECT 1 AS residual_check_no_objects;"
    ]

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


def resolve_values_factor_witness(
    case: ValuesFactorCase | ValuesFactorExtensionCase,
    repository_root: Path,
) -> ValuesFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return ValuesFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_values(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    # The WITH-clause prefix (cte_source / recursive factors) is
    # newline-terminated, so the primary VALUES always starts at line
    # start (col-0), matching the content-gate regex ``^VALUES``.
    # Subquery SELECTs ((SELECT 1), (SELECT val FROM cte)) are inline
    # and never at line start, so they do not match.
    return len(re.findall(r"(?m)^VALUES\b", region))


def _header(case: ValuesFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : VALUES {case.factor_key}="
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


def render_values_factor_case(
    case: ValuesFactorCase | ValuesFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 VALUES。")
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
    case: ValuesFactorCase | ValuesFactorExtensionCase,
    out: Path,
) -> None:
    text = render_values_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_values_factor_programs(
    baseline_plan: ValuesFactorLoopPlan,
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
    "ValuesFactorRenderError",
    "ValuesFactorWitness",
    "count_primary_values",
    "generate_values_factor_programs",
    "render_values_factor_case",
    "resolve_values_factor_witness",
]
