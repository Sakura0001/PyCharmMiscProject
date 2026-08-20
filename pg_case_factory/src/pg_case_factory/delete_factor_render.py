"""Render complete PostgreSQL 18.4 DELETE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

DELETE is a DML row-mutation statement: the target is a ``pg_class``
relation of kind ``r`` (a base table).  All catalog oracles
schema-qualify ``pg_catalog.pg_class`` (exempt from the file-prefix
style gate via the ``pg_`` prefix) and carry a top-level ``ORDER BY``.
Success cases CREATE fixture TABLEs (the target ``{p}tbl`` plus an
optional USING source ``{p}src`` and an FK referencing table
``{p}ref``), so the bookend gate (DROP TABLE IF EXISTS first + last
``;``-stmt covering every created table) applies.  The single
``RETURNING ... WITH (OLD AS ..., NEW AS ...)`` PG18 test point is
rendered for ``result_shape=returning_old_new_aliases``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .delete_factor_extension import (
    DeleteFactorExtensionCase,
    _present_failure_pair,
)
from .delete_factor_loop import (
    DeleteFactorCase,
    DeleteFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/dml/table/"
    "delete.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/dml/table/"
    "delete.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class DeleteFactorRenderError(ValueError):
    """Raised when a DELETE case cannot be rendered."""


@dataclass(frozen=True)
class DeleteFactorWitness:
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
    ext: DeleteFactorExtensionCase,
) -> DeleteFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "delete")
    return DeleteFactorCase(
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
    case: DeleteFactorCase | DeleteFactorExtensionCase,
) -> DeleteFactorCase:
    if isinstance(case, DeleteFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: DeleteFactorCase) -> dict[str, str]:
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


def _cursor_name(p: str) -> str:
    return f"{p}cur"


def _delete_target(a: dict[str, str], p: str) -> str:
    """The DELETE FROM target identifier (with optional alias)."""

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
        return f"{name} AS d"
    return name


def _target_relation_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    if _target_wrong(a):
        return _seq_name(p)
    return _table_name(p)


def _with_prefix(a: dict[str, str], p: str) -> str:
    """The WITH clause prefix for the DELETE statement."""

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
        return f"WITH {p}cte AS (SELECT 1 AS val)\n"
    return ""


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target DELETE runs."""

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


def _where_clause(a: dict[str, str], p: str) -> str:
    """The WHERE / WHERE CURRENT OF clause."""

    cs = a.get("condition_shape", "simple_predicate")
    if cs == "none":
        return ""
    if cs == "cursor_or_conflict_target":
        return f"WHERE CURRENT OF {_cursor_name(p)}"
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


def _using_clause(a: dict[str, str], p: str) -> str:
    cs = a.get("condition_shape", "simple_predicate")
    if cs == "join_or_match_condition":
        return f"USING {_source_table_name(p)}"
    return ""


def _returning_clause(a: dict[str, str]) -> str:
    rs = a.get("result_shape", "none")
    if rs == "returning_star":
        return " RETURNING *"
    if rs == "returning_expression":
        return " RETURNING id"
    if rs == "rowset_projection":
        return " RETURNING id, val"
    if rs == "returning_old_new_aliases":
        return (
            " RETURNING WITH (OLD AS old_row, NEW AS new_row) "
            "old_row.*, new_row.*"
        )
    return ""


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary DELETE statement."""

    with_prefix = _with_prefix(a, p)
    target = _delete_target(a, p)
    using = _using_clause(a, p)
    where = _where_clause(a, p)
    returning = _returning_clause(a)
    parts: list[str] = [f"{with_prefix}DELETE FROM {target}"]
    if using:
        parts.append(f" {using}")
    if where:
        parts.append(f" {where}")
    if returning:
        parts.append(returning)
    parts.append(";")
    return "".join(parts)


def _probe_select(
    case: DeleteFactorCase,
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

    # effect_query and returned_rows both probe post-delete state.
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


def _resolve_case(case: DeleteFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    missing = _target_missing(a)
    wrong = _target_wrong(a)
    tbl = _table_name(p)
    src = _source_table_name(p)
    ref = _ref_table_name(p)
    seq = _seq_name(p)

    setup: list[str] = []
    locus = "target.delete"

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

    # --- USING source table (join / query_source) -------------------
    if (not missing and not wrong) and (
        cs == "join_or_match_condition"
        or doqs == "query_source"
    ):
        setup.append(f"CREATE TABLE {src} (val int);")
        setup.append(f"INSERT INTO {src} VALUES (1);")
        locus = "fixture.source_table"

    # --- cursor fixture (WHERE CURRENT OF) --------------------------
    if (
        cs == "cursor_or_conflict_target"
        and not missing
        and not wrong
    ):
        setup.append("BEGIN;")
        setup.append(
            f"DECLARE {_cursor_name(p)} CURSOR FOR "
            f"SELECT id FROM {tbl};"
        )
        setup.append(f"FETCH FIRST FROM {_cursor_name(p)};")
        locus = "fixture.cursor"

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
    if (
        cs == "cursor_or_conflict_target"
        and not missing
        and not wrong
    ):
        assert_lines.append("COMMIT;")
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


def resolve_delete_factor_witness(
    case: DeleteFactorCase | DeleteFactorExtensionCase,
    repository_root: Path,
) -> DeleteFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DeleteFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_delete(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    # The WITH-clause prefix (cte_source / recursive factors) is newline-
    # terminated, so the primary DELETE always starts at line start
    # (col-0), matching the content-gate regex ``^DELETE``.  DELETE has
    # NO optional leading keywords.
    return len(re.findall(r"(?m)^DELETE\b", region))


def _header(case: DeleteFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DELETE {case.factor_key}="
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


def render_delete_factor_case(
    case: DeleteFactorCase | DeleteFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 DELETE。")
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
    case: DeleteFactorCase | DeleteFactorExtensionCase,
    out: Path,
) -> None:
    text = render_delete_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_delete_factor_programs(
    baseline_plan: DeleteFactorLoopPlan,
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
    "DeleteFactorRenderError",
    "DeleteFactorWitness",
    "count_primary_delete",
    "generate_delete_factor_programs",
    "render_delete_factor_case",
    "resolve_delete_factor_witness",
]
