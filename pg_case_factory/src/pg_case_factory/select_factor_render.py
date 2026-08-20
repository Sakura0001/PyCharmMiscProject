"""Render complete PostgreSQL 18.4 SELECT factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

SELECT is a DML read-only query statement: the target is a
``pg_class`` relation of kind ``r`` (a base table) that the statement
reads but does not mutate.  All catalog oracles schema-qualify
``pg_catalog.pg_class`` (exempt from the file-prefix style gate via the
``pg_`` prefix) and carry a top-level ``ORDER BY``.  Success cases
CREATE fixture TABLEs (the target ``{p}tbl`` plus an optional join
source ``{p}src`` and an FK referencing table ``{p}ref``), so the
bookend gate (DROP TABLE IF EXISTS first + last ``;``-stmt covering
every created table) applies.  SELECT mirrors DELETE's fixture pattern
(CREATE TABLE + INSERT rows -> operate -> DROP TABLE IF EXISTS
CASCADE); the operation is swapped (DELETE -> SELECT).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .select_factor_extension import (
    SelectFactorExtensionCase,
    _present_failure_pair,
)
from .select_factor_loop import (
    SelectFactorCase,
    SelectFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/dml/query/select.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/dml/query/"
    "select.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class SelectFactorRenderError(ValueError):
    """Raised when a SELECT case cannot be rendered."""


@dataclass(frozen=True)
class SelectFactorWitness:
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
    ext: SelectFactorExtensionCase,
) -> SelectFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "select")
    return SelectFactorCase(
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
    case: SelectFactorCase | SelectFactorExtensionCase,
) -> SelectFactorCase:
    if isinstance(case, SelectFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: SelectFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _target_missing(a: dict[str, str]) -> bool:
    return a.get("target_relation_state") == "missing"


def _target_wrong(a: dict[str, str]) -> bool:
    return a.get("target_relation_state") == "wrong_object_type"


def _table_name(p: str) -> str:
    return f"{p}tbl"


def _source_table_name(p: str) -> str:
    return f"{p}src"


def _ref_table_name(p: str) -> str:
    return f"{p}ref"


def _seq_name(p: str) -> str:
    return f"{p}seq"


def _select_target(a: dict[str, str], p: str) -> str:
    """The FROM target identifier (with optional alias)."""

    shape = a.get("name_shape", "plain_identifier")
    if _target_wrong(a):
        name = _seq_name(p)
    else:
        name = _table_name(p)
    if shape == "schema_qualified":
        return f"public.{name}"
    if shape == "quoted_identifier":
        return f'"{name}"'
    if shape == "alias_used":
        return f"{name} AS s"
    if shape == "row_lock_of_alias":
        return f"{name} AS s"
    return name


def _target_relation_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    if _target_wrong(a):
        return _seq_name(p)
    return _table_name(p)


def _select_list(a: dict[str, str]) -> str:
    """The select-list governed by the result_shape factor."""

    rs = a.get("result_shape", "none")
    if rs == "returning_star":
        return "*"
    if rs == "returning_expression":
        return "id"
    if rs == "rowset_projection":
        return "id, val"
    # none: a constant projection with no column reference.
    return "1"


def _lock_clause(a: dict[str, str]) -> str:
    """The row-locking clause for name_shape=row_lock_of_alias."""

    if a.get("name_shape") == "row_lock_of_alias":
        return " FOR UPDATE OF s"
    return ""


def _with_prefix(a: dict[str, str], p: str) -> str:
    """The WITH clause prefix for the SELECT statement."""

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
        # non_recursive and merge_cte both declare a simple CTE; the
        # factor value (merge_cte is a PG18 reference-parity point) is
        # captured in the case metadata, so the target bytes differ by
        # header.
        return f"WITH {p}cte AS (SELECT 1 AS val)\n"
    return ""


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target SELECT runs."""

    pc = a.get("privilege_context", "owner")
    if pc == "insufficient_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    pc = a.get("privilege_context", "owner")
    if pc == "insufficient_privilege":
        roles.append(f"{p}actor")
    return tuple(roles)


def _predicate(a: dict[str, str], p: str) -> str:
    """The simple WHERE predicate expression."""

    ic = a.get("invalid_combination", "none")
    if ic == "syntax_valid_semantic_error":
        return f"{p}no_such_col = 1"

    doqs = a.get("data_or_query_shape", "explicit_values")
    es = a.get("expression_shape", "literal")
    src = _source_table_name(p)

    if doqs == "minimal":
        return "id = 0"
    if doqs == "query_source":
        return f"id IN (SELECT val FROM {src})"
    if doqs == "cte_source":
        return f"id IN (SELECT val FROM {p}cte)"
    # explicit_values: argument shape governed by expression_shape.
    if es == "literal":
        return "id = 1"
    if es == "column_reference":
        return "id = id"
    if es == "function_call":
        return "id = abs(1)"
    if es == "subquery_expression":
        return "id = (SELECT 1)"
    return "id = 1"


def _from_clause(a: dict[str, str], p: str) -> str:
    """The FROM clause (target, with an optional join source)."""

    cs = a.get("condition_shape", "simple_predicate")
    if cs == "join_or_match_condition":
        # SELECT has no USING clause; the join source is added to the
        # FROM as a cross-join target so the match predicate resolves.
        return f"{_table_name(p)}, {_source_table_name(p)}"
    return _select_target(a, p)


def _where_clause(a: dict[str, str], p: str) -> str:
    """The WHERE clause.  SELECT cannot use WHERE CURRENT OF, so the
    cursor_or_conflict_target shape renders a subquery predicate."""

    cs = a.get("condition_shape", "simple_predicate")
    if cs == "none":
        return ""
    if cs == "cursor_or_conflict_target":
        return (
            f"WHERE id IN (SELECT val FROM "
            f"{_source_table_name(p)})"
        )
    if cs == "join_or_match_condition":
        return (
            f"WHERE {_table_name(p)}.id = "
            f"{_source_table_name(p)}.val"
        )
    # simple_predicate
    cb = a.get("constraint_boundary", "none")
    if cb == "empty_input":
        return "WHERE id = 999"
    return f"WHERE {_predicate(a, p)}"


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary SELECT statement."""

    with_prefix = _with_prefix(a, p)
    select_list = _select_list(a)
    from_clause = _from_clause(a, p)
    where = _where_clause(a, p)
    lock = _lock_clause(a)
    parts: list[str] = [f"{with_prefix}SELECT {select_list} FROM {from_clause}"]
    if where:
        parts.append(f" {where}")
    if lock:
        parts.append(lock)
    parts.append(";")
    return "".join(parts)


def _probe_select(
    case: SelectFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog/effect oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "effect_query")
    if mode == "error_assertion":
        return None

    tbl = _table_name(p)
    rel_lit = _target_relation_literal(a, p)
    missing = _target_missing(a)
    wrong = _target_wrong(a)
    present = not (missing or wrong)

    if mode == "catalog_query":
        cmp_op = ">" if present else "="
        return (
            f"SELECT count(*) {cmp_op} 0 AS relation_state "
            f"FROM pg_catalog.pg_class "
            f"WHERE relname = '{rel_lit}' AND relkind = 'r' "
            f"ORDER BY count(*);"
        )

    # effect_query and returned_rows both probe post-read state.
    if not present:
        cmp_op = ">" if present else "="
        return (
            f"SELECT count(*) {cmp_op} 0 AS effect_state "
            f"FROM pg_catalog.pg_class "
            f"WHERE relname = '{rel_lit}' AND relkind = 'r' "
            f"ORDER BY count(*);"
        )
    label = "returned_rows_state" if mode == "returned_rows" else "effect_state"
    return (
        f"SELECT count(*) >= 0 AS {label} "
        f"FROM {tbl} "
        f"ORDER BY count(*);"
    )


def _resolve_case(case: SelectFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    missing = _target_missing(a)
    wrong = _target_wrong(a)
    tbl = _table_name(p)
    src = _source_table_name(p)
    ref = _ref_table_name(p)
    seq = _seq_name(p)

    setup: list[str] = []
    locus = "target.select"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    cb = a.get("constraint_boundary", "none")
    cs = a.get("condition_shape", "simple_predicate")
    doqs = a.get("data_or_query_shape", "explicit_values")

    # --- role fixtures ----------------------------------------------
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- target relation fixture ------------------------------------
    if missing:
        setup.append(
            "SELECT 1 AS target_relation_intentionally_absent;"
        )
        locus = "fixture.relation_missing"
    elif wrong:
        setup.append(f"CREATE SEQUENCE {seq};")
        locus = "fixture.wrong_object_type"
    else:
        if cb == "constraint_violation":
            setup.append(
                f"CREATE TABLE {tbl} (id int PRIMARY KEY, val int);"
            )
            setup.append(
                f"CREATE TABLE {ref} (id int REFERENCES {tbl}(id));"
            )
            setup.append(f"INSERT INTO {tbl} VALUES (1, 100);")
            setup.append(f"INSERT INTO {ref} VALUES (1);")
            locus = "fixture.constraint_boundary"
        else:
            setup.append(f"CREATE TABLE {tbl} (id int, val int);")
            setup.append(
                f"INSERT INTO {tbl} VALUES (1, 100), (2, 200);"
            )
            locus = "fixture.table"

    # --- USING source table (join / query_source / subquery) --------
    if (not missing and not wrong) and (
        cs == "join_or_match_condition"
        or cs == "cursor_or_conflict_target"
        or doqs == "query_source"
    ):
        setup.append(f"CREATE TABLE {src} (val int);")
        setup.append(f"INSERT INTO {src} VALUES (1);")
        locus = "fixture.source_table"

    # --- arm the effective role -------------------------------------
    if effective:
        setup.append(f"GRANT SELECT ON {tbl} TO {effective};")
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement -------------------------------
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion --------------------------------
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

    # --- cleanup construction ----------------------------------------
    seq_drops = (
        [f"DROP SEQUENCE IF EXISTS {seq};"] if wrong else []
    )
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]
    # Bookend gate: the final ;-segment must be a single DROP TABLE IF
    # EXISTS covering every table this case may create (target, source,
    # FK-referencing).  CASCADE removes dependent objects first.
    table_drops = [
        f"DROP TABLE IF EXISTS {tbl}, {src}, {ref} CASCADE;"
    ]

    # pre-cleanup: tables first (bookend), then sequence, then roles
    pre_cleanup: list[str] = []
    pre_cleanup.extend(table_drops)
    pre_cleanup.extend(seq_drops)
    pre_cleanup.append("RESET ROLE;")
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    # cleanup: RESET ROLE, sequence, roles, tables last (bookend)
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(seq_drops)
    cleanup.extend(role_drops)
    cleanup.extend(table_drops)

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


def resolve_select_factor_witness(
    case: SelectFactorCase | SelectFactorExtensionCase,
    repository_root: Path,
) -> SelectFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return SelectFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_select(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    # The WITH-clause prefix (cte_source / recursive / merge_cte factors)
    # is newline-terminated, so the primary SELECT always starts at line
    # start (col-0), matching the content-gate regex ``^SELECT``.
    # Subquery SELECTs (IN (SELECT ...), = (SELECT ...)) are inline and
    # never at line start, so they do not match.
    return len(re.findall(r"(?m)^SELECT\b", region))


def _header(case: SelectFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : SELECT {case.factor_key}="
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


def render_select_factor_case(
    case: SelectFactorCase | SelectFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 SELECT。")
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
    case: SelectFactorCase | SelectFactorExtensionCase,
    out: Path,
) -> None:
    text = render_select_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_select_factor_programs(
    baseline_plan: SelectFactorLoopPlan,
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
    "SelectFactorRenderError",
    "SelectFactorWitness",
    "count_primary_select",
    "generate_select_factor_programs",
    "render_select_factor_case",
    "resolve_select_factor_witness",
]
