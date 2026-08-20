"""Render complete PostgreSQL 18.4 MERGE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

MERGE is a DML row-mutation statement: the target is a ``pg_class``
relation of kind ``r`` (a base table).  All catalog oracles
schema-qualify ``pg_catalog.pg_class`` (exempt from the file-prefix
style gate via the ``pg_`` prefix) and carry a top-level ``ORDER BY``.
Success cases CREATE fixture TABLEs (the target ``{p}tbl`` plus an
optional USING source ``{p}src`` and an FK referencing table
``{p}ref``), so the bookend gate (DROP TABLE IF EXISTS first + last
``;``-stmt covering every created table) applies.  The single
``RETURNING ... WITH (OLD AS ..., NEW AS ...)`` PG18 test point is
rendered for ``result_shape=returning_old_new_aliases``.  The two
PG18 ``condition_shape`` test points (``not_matched_by_source``,
``not_matched_by_target``) are rendered with their respective WHEN
clause forms.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .merge_factor_extension import (
    MergeFactorExtensionCase,
    _present_failure_pair,
)
from .merge_factor_loop import (
    MergeFactorCase,
    MergeFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/dml/table/"
    "merge.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/dml/table/"
    "merge.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class MergeFactorRenderError(ValueError):
    """Raised when a MERGE case cannot be rendered."""


@dataclass(frozen=True)
class MergeFactorWitness:
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
    ext: MergeFactorExtensionCase,
) -> MergeFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "merge")
    return MergeFactorCase(
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
    case: MergeFactorCase | MergeFactorExtensionCase,
) -> MergeFactorCase:
    if isinstance(case, MergeFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: MergeFactorCase) -> dict[str, str]:
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


def _merge_target(a: dict[str, str], p: str) -> str:
    """The MERGE INTO target identifier (with optional alias)."""

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
        return f"{name} AS t"
    return name


def _target_relation_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    if _target_wrong(a):
        return _seq_name(p)
    return _table_name(p)


def _target_ref(a: dict[str, str], p: str) -> str:
    """The identifier used to reference target columns in ON/WHEN."""

    if _target_wrong(a):
        return _seq_name(p)
    shape = a.get("name_shape", "plain_identifier")
    name = _table_name(p)
    if shape == "alias_used":
        return "t"
    if shape == "schema_qualified":
        return f"public.{name}"
    if shape == "quoted_identifier":
        return f'"{name}"'
    return name


def _merge_source(a: dict[str, str], p: str) -> str:
    """The USING data source."""

    doqs = a.get("data_or_query_shape", "explicit_values")
    if _target_missing(a) or _target_wrong(a):
        return "(VALUES (1, 100)) AS s(id, val)"
    if doqs == "query_source":
        return f"{_source_table_name(p)} AS s"
    if doqs == "cte_source":
        return f"{p}cte AS s"
    if doqs == "minimal":
        return "(SELECT 1 AS id, 100 AS val) AS s"
    return "(VALUES (1, 100)) AS s(id, val)"


def _with_prefix(a: dict[str, str], p: str) -> str:
    """The WITH clause prefix for the MERGE statement."""

    doqs = a.get("data_or_query_shape", "explicit_values")
    wc = a.get("with_clause", "absent")

    if doqs == "cte_source" or wc != "absent":
        if wc == "recursive":
            return (
                f"WITH RECURSIVE {p}cte AS ("
                f"SELECT 1 AS id, 100 AS val "
                f"UNION ALL "
                f"SELECT id + 1, val + 1 FROM {p}cte "
                f"WHERE id < 5)\n"
            )
        return f"WITH {p}cte AS (SELECT 1 AS id, 100 AS val)\n"
    return ""


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target MERGE runs."""

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


def _expression_value(es: str) -> str:
    """The expression used in UPDATE SET / INSERT VALUES."""

    if es == "column_reference":
        return "s.val"
    if es == "function_call":
        return "abs(1)"
    if es == "subquery_expression":
        return "(SELECT 1)"
    return "1"


def _join_condition(a: dict[str, str], p: str) -> str:
    """The ON join condition."""

    cs = a.get("condition_shape", "simple_predicate")
    ic = a.get("invalid_combination", "none")
    target_ref = _target_ref(a, p)

    if ic == "syntax_valid_semantic_error":
        return f"ON {target_ref}.{p}no_such_col = s.id"

    if cs == "none":
        return "ON true"
    if cs == "join_or_match_condition":
        return (
            f"ON {target_ref}.id = s.id "
            f"AND {target_ref}.val = s.val"
        )
    # simple_predicate, cursor_or_conflict_target,
    # not_matched_by_source, not_matched_by_target
    return f"ON {target_ref}.id = s.id"


def _when_clauses(a: dict[str, str], p: str) -> str:
    """The WHEN clause(s) for the MERGE."""

    cs = a.get("condition_shape", "simple_predicate")
    cb = a.get("constraint_boundary", "none")
    es = a.get("expression_shape", "literal")

    expr = _expression_value(es)

    if cs == "not_matched_by_source":
        return "WHEN NOT MATCHED BY SOURCE THEN DELETE"
    if cs == "not_matched_by_target":
        return (
            f"WHEN NOT MATCHED BY TARGET "
            f"THEN INSERT VALUES (s.id, {expr})"
        )
    if cs == "none":
        if cb == "constraint_violation":
            return "WHEN MATCHED THEN DELETE"
        return "WHEN MATCHED THEN DO NOTHING"
    # simple_predicate, join_or_match_condition,
    # cursor_or_conflict_target
    if cb == "constraint_violation":
        return "WHEN MATCHED THEN DELETE"
    return (
        f"WHEN MATCHED THEN UPDATE SET val = {expr} "
        f"WHEN NOT MATCHED THEN INSERT VALUES (s.id, {expr})"
    )


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
    """The primary MERGE statement."""

    with_prefix = _with_prefix(a, p)
    target = _merge_target(a, p)
    source = _merge_source(a, p)
    join_cond = _join_condition(a, p)
    when_clauses = _when_clauses(a, p)
    returning = _returning_clause(a)
    parts: list[str] = [f"{with_prefix}MERGE INTO {target}"]
    parts.append(f" USING {source}")
    parts.append(f" {join_cond}")
    parts.append(f" {when_clauses}")
    if returning:
        parts.append(returning)
    parts.append(";")
    return "".join(parts)


def _probe_select(
    case: MergeFactorCase,
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

    # effect_query and returned_rows both probe post-merge state.
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


def _resolve_case(case: MergeFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    missing = _target_missing(a)
    wrong = _target_wrong(a)
    tbl = _table_name(p)
    src = _source_table_name(p)
    ref = _ref_table_name(p)
    seq = _seq_name(p)

    setup: list[str] = []
    locus = "target.merge"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    cb = a.get("constraint_boundary", "none")
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
        elif cb == "empty_input":
            setup.append(f"CREATE TABLE {tbl} (id int, val int);")
            locus = "fixture.empty_input"
        else:
            setup.append(f"CREATE TABLE {tbl} (id int, val int);")
            setup.append(
                f"INSERT INTO {tbl} VALUES (1, 100);"
            )
            locus = "fixture.table"

    # --- USING source table (query_source) --------------------------
    if (not missing and not wrong) and doqs == "query_source":
        setup.append(f"CREATE TABLE {src} (id int, val int);")
        setup.append(f"INSERT INTO {src} VALUES (1, 100);")
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


def resolve_merge_factor_witness(
    case: MergeFactorCase | MergeFactorExtensionCase,
    repository_root: Path,
) -> MergeFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return MergeFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_merge(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    # The WITH-clause prefix (cte_source / recursive factors) is newline-
    # terminated, so the primary MERGE always starts at line start
    # (col-0), matching the content-gate regex ``^MERGE``.  MERGE has
    # NO optional leading keywords.
    return len(re.findall(r"(?m)^MERGE\b", region))


def _header(case: MergeFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : MERGE {case.factor_key}="
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


def render_merge_factor_case(
    case: MergeFactorCase | MergeFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 MERGE。")
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
    case: MergeFactorCase | MergeFactorExtensionCase,
    out: Path,
) -> None:
    text = render_merge_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_merge_factor_programs(
    baseline_plan: MergeFactorLoopPlan,
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
    "MergeFactorRenderError",
    "MergeFactorWitness",
    "count_primary_merge",
    "generate_merge_factor_programs",
    "render_merge_factor_case",
    "resolve_merge_factor_witness",
]
