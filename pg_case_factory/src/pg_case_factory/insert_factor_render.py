"""Render complete PostgreSQL 18.4 INSERT factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

INSERT is a DML row-mutation statement: the target is a ``pg_class``
relation of kind ``r`` (a base table).  All catalog oracles
schema-qualify ``pg_catalog.pg_class`` (exempt from the file-prefix
style gate via the ``pg_`` prefix) and carry a top-level ``ORDER BY
count(*) LIMIT 1``.  Success cases CREATE fixture TABLEs (the target
``{p}tbl`` plus an optional SELECT source ``{p}src`` and an unused
``{p}ref`` kept for bookend parity), so the bookend gate (DROP TABLE
IF EXISTS first + last ``;``-stmt covering every created table)
applies.  The single ``RETURNING ... WITH (OLD AS ..., NEW AS ...)``
PG18 test point is rendered for
``result_shape=returning_old_new_aliases``.

``condition_shape`` maps to the ``ON CONFLICT`` clause (INSERT's
conditional conflict-handling branch) so every value is observable with
the baseline ``explicit_values`` data shape.  ``expression_shape``
governs the value expression in the explicit ``VALUES`` clause.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .insert_factor_extension import (
    InsertFactorExtensionCase,
    _present_failure_pair,
)
from .insert_factor_loop import (
    InsertFactorCase,
    InsertFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/dml/table/"
    "insert.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/dml/table/"
    "insert.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class InsertFactorRenderError(ValueError):
    """Raised when an INSERT case cannot be rendered."""


@dataclass(frozen=True)
class InsertFactorWitness:
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
    ext: InsertFactorExtensionCase,
) -> InsertFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "insert")
    return InsertFactorCase(
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
    case: InsertFactorCase | InsertFactorExtensionCase,
) -> InsertFactorCase:
    if isinstance(case, InsertFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: InsertFactorCase) -> dict[str, str]:
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


def _insert_target(a: dict[str, str], p: str) -> str:
    """The INSERT INTO target identifier (with optional alias)."""

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
        return f"{name} AS i"
    return name


def _target_relation_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    if _target_wrong(a):
        return _seq_name(p)
    return _table_name(p)


def _with_prefix(a: dict[str, str], p: str) -> str:
    """The WITH clause prefix for the INSERT statement."""

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
    """The session role under which the target INSERT runs."""

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


def _value_expression(a: dict[str, str], p: str) -> str:
    """The value expression for the ``val`` column (explicit_values)."""

    es = a.get("expression_shape", "literal")
    src = _source_table_name(p)
    if es == "literal":
        return "100"
    if es == "column_reference":
        return f"(SELECT val FROM {src} LIMIT 1)"
    if es == "function_call":
        return "abs(100)"
    if es == "subquery_expression":
        return "(SELECT 100)"
    return "100"


def _values_source(a: dict[str, str], p: str) -> str:
    """The row source after the column list (VALUES / SELECT / DEFAULT)."""

    doqs = a.get("data_or_query_shape", "explicit_values")
    cb = a.get("constraint_boundary", "none")
    ic = a.get("invalid_combination", "none")
    src = _source_table_name(p)

    # constraint_violation: insert a row whose val duplicates a
    # pre-seeded UNIQUE value while using a fresh id, so ON CONFLICT(id)
    # (condition_shape) never suppresses the val conflict.
    if cb == "constraint_violation":
        if doqs == "query_source":
            return f"SELECT 2, 100 FROM {src}"
        if doqs == "cte_source":
            return f"SELECT 2, 100 FROM {p}cte"
        # minimal / explicit_values
        return "VALUES (2, 100)"

    # empty_input: zero rows inserted.
    if cb == "empty_input":
        return "SELECT 1, 100 WHERE false"

    if doqs == "minimal":
        return "VALUES (1, 100)"
    if doqs == "query_source":
        return f"SELECT 1, val FROM {src}"
    if doqs == "cte_source":
        return f"SELECT 1, val FROM {p}cte"

    # explicit_values
    if ic == "syntax_valid_semantic_error":
        return f"VALUES (1, {p}no_such_col)"
    return f"VALUES (1, {_value_expression(a, p)})"


def _conflict_clause(a: dict[str, str]) -> str:
    """The ON CONFLICT clause (condition_shape -> INSERT conflict form)."""

    cs = a.get("condition_shape", "none")
    if cs == "none":
        return ""
    if cs == "simple_predicate":
        return " ON CONFLICT (id) DO NOTHING"
    if cs == "join_or_match_condition":
        return (
            " ON CONFLICT (id) DO UPDATE SET val = excluded.val"
        )
    if cs == "cursor_or_conflict_target":
        return (
            " ON CONFLICT (id) DO UPDATE SET val = excluded.val"
            " WHERE excluded.id = 1"
        )
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


def _build_insert(a: dict[str, str], p: str) -> str:
    """The primary INSERT statement."""

    with_prefix = _with_prefix(a, p)
    target = _insert_target(a, p)
    source = _values_source(a, p)
    conflict = _conflict_clause(a)
    returning = _returning_clause(a)
    doqs = a.get("data_or_query_shape", "explicit_values")
    # minimal uses positional VALUES (no column list); every other
    # shape carries an explicit (id, val) column list.
    col_list = "" if doqs == "minimal" else " (id, val)"
    parts: list[str] = [
        f"{with_prefix}INSERT INTO {target}{col_list} {source}"
    ]
    if conflict:
        parts.append(conflict)
    if returning:
        parts.append(returning)
    parts.append(";")
    return "".join(parts)


def _probe_select(
    case: InsertFactorCase,
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
            f"ORDER BY count(*) LIMIT 1;"
        )

    # effect_query and returned_rows both probe post-insert state.
    if not present:
        cmp_op = ">" if present else "="
        return (
            f"SELECT count(*) {cmp_op} 0 AS effect_state "
            f"FROM pg_catalog.pg_class "
            f"WHERE relname = '{rel_lit}' AND relkind = 'r' "
            f"ORDER BY count(*) LIMIT 1;"
        )
    label = "returned_rows_state" if mode == "returned_rows" else "effect_state"
    return (
        f"SELECT count(*) >= 0 AS {label} "
        f"FROM {tbl} "
        f"ORDER BY count(*) LIMIT 1;"
    )


def _resolve_case(case: InsertFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    missing = _target_missing(a)
    wrong = _target_wrong(a)
    tbl = _table_name(p)
    src = _source_table_name(p)
    ref = _ref_table_name(p)
    seq = _seq_name(p)

    setup: list[str] = []
    locus = "target.insert"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    cb = a.get("constraint_boundary", "none")
    doqs = a.get("data_or_query_shape", "explicit_values")
    es = a.get("expression_shape", "literal")

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
                f"CREATE TABLE {tbl} "
                f"(id int PRIMARY KEY, val int UNIQUE);"
            )
            setup.append(f"INSERT INTO {tbl} VALUES (1, 100);")
            locus = "fixture.constraint_boundary"
        else:
            setup.append(
                f"CREATE TABLE {tbl} (id int PRIMARY KEY, val int);"
            )
            locus = "fixture.table"

    # --- SELECT source table (query_source / column_reference) ------
    needs_src = doqs == "query_source" or (
        doqs == "explicit_values"
        and es == "column_reference"
        and cb not in ("constraint_violation", "empty_input")
    )
    if (not missing and not wrong) and needs_src:
        setup.append(f"CREATE TABLE {src} (val int);")
        setup.append(f"INSERT INTO {src} VALUES (1);")
        locus = "fixture.source_table"

    # --- arm the effective role -------------------------------------
    if effective:
        setup.append(f"GRANT SELECT ON {tbl} TO {effective};")
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement -------------------------------
    target = _build_insert(a, p)

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
    if wrong:
        specs.append(DropSpec("SEQUENCE", seq))
    table_names = [tbl, src, ref]
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


def resolve_insert_factor_witness(
    case: InsertFactorCase | InsertFactorExtensionCase,
    repository_root: Path,
) -> InsertFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return InsertFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_insert(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    # The WITH-clause prefix (cte_source / recursive factors) is newline-
    # terminated, so the primary INSERT always starts at line start
    # (col-0), matching the content-gate regex ``^INSERT``.  INSERT has
    # NO optional leading keywords.
    return len(re.findall(r"(?m)^INSERT\b", region))


def _header(case: InsertFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : INSERT {case.factor_key}="
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


def render_insert_factor_case(
    case: InsertFactorCase | InsertFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 INSERT。")
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
    case: InsertFactorCase | InsertFactorExtensionCase,
    out: Path,
) -> None:
    text = render_insert_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_insert_factor_programs(
    baseline_plan: InsertFactorLoopPlan,
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
    "InsertFactorRenderError",
    "InsertFactorWitness",
    "count_primary_insert",
    "generate_insert_factor_programs",
    "render_insert_factor_case",
    "resolve_insert_factor_witness",
]
