"""Render complete PostgreSQL 18.4 SELECT INTO factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the byte-level
witness validator (which re-renders and compares) can never diverge from
the bytes actually written.

SELECT INTO creates a table from a query.  Success-path cases CREATE both
the source fixture table and the output table.  The bookend gate
(``audit_complete_table_script``) triggers on raw ``CREATE TABLE``;
``SELECT INTO`` does not contain the ``CREATE`` keyword, so the bookend
gate does **not** fire.  The source fixture tables (created via
``CREATE TABLE`` unquoted) still need cleanup ``DROP TABLE IF EXISTS`` in
the render's fixture management.  Quoted / reserved / dotted target names
appear ONLY in the fenced SELECT INTO target (the style gate does not
parse the target); fixtures, catalog queries, and cleanup DROPs always
use plain prefix-derived unqualified names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .select_into_factor_extension import (
    SelectIntoFactorExtensionCase,
    _present_failure_pair,
)
from .select_into_factor_loop import (
    SelectIntoFactorCase,
    SelectIntoFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/table/"
    "select_into.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/table/"
    "select_into.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class SelectIntoFactorRenderError(ValueError):
    """Raised when a SELECT INTO case cannot be rendered."""


@dataclass(frozen=True)
class SelectIntoFactorWitness:
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
    ext: SelectIntoFactorExtensionCase,
) -> SelectIntoFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "table_type"
        factor_value = assignment.get("table_type", "permanent")
    return SelectIntoFactorCase(
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
    case: SelectIntoFactorCase | SelectIntoFactorExtensionCase,
) -> SelectIntoFactorCase:
    if isinstance(case, SelectIntoFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: SelectIntoFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_temporary(a: dict[str, str]) -> bool:
    return a.get("table_type") == "temporary"


def _source_exists(a: dict[str, str]) -> bool:
    return a.get("source_table_dependency") == "source_table_exists"


def _output_name(a: dict[str, str], p: str) -> str:
    """The table name used in the fenced SELECT INTO target."""

    shape = a.get("table_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}t"'
    if shape == "reserved_word":
        return f'"{p}abort"'
    if shape == "schema_qualified":
        return f"{p}sch.{p}t"
    if shape == "non_existent_schema":
        return f"{p}nonsch.{p}t"
    if shape == "long_identifier":
        return f"{p}t" + "a" * 60
    return f"{p}t"


def _output_name_plain(a: dict[str, str], p: str) -> str:
    """Always-plain output table name for cleanup and oracle queries."""

    shape = a.get("table_name_shape", "simple")
    if shape == "reserved_word":
        return f"{p}abort"
    if shape == "long_identifier":
        return f"{p}t" + "a" * 60
    return f"{p}t"


def _table_type_prefix(a: dict[str, str]) -> str:
    tt = a.get("table_type", "permanent")
    if tt == "temporary":
        tm = a.get("temp_modifier", "TEMPORARY")
        if tm == "TEMP":
            return "TEMP"
        return "TEMPORARY"
    if tt == "unlogged":
        return "UNLOGGED"
    return ""


def _keyword_table_clause(a: dict[str, str]) -> str:
    return "TABLE" if a.get("keyword_table") == "present" else ""


def _select_modifier(a: dict[str, str]) -> str:
    sm = a.get("select_modifier", "default")
    if sm == "ALL":
        return "ALL"
    if sm == "DISTINCT":
        return "DISTINCT"
    return ""


def _select_list(
    a: dict[str, str], p: str
) -> str:
    """The select-list expression based on column_name_shape and query_shape."""

    cns = a.get("column_name_shape", "inherited_from_query")
    qs = a.get("query_shape", "simple_select")

    # Failure overrides for query_error
    qe = a.get("query_error", "none")
    if qe == "expression_invalid":
        return "1 + AS col1"
    if qe == "type_mismatch":
        return "CASE WHEN true THEN 1 ELSE 'abc' END AS col1"

    if cns == "aliased_with_AS":
        return "id AS col1, val AS col2"
    if cns == "expression_derived":
        return "id + 1 AS computed"
    return "*"


def _from_clause(
    a: dict[str, str], p: str
) -> str:
    """The FROM/WHERE/JOIN body based on query_shape."""

    qs = a.get("query_shape", "simple_select")
    qe = a.get("query_error", "none")

    # query_error=source_table_not_exists: reference a non-existent table
    if qe == "source_table_not_exists":
        return f"FROM {p}nonexistent"

    if qs == "select_with_from_where":
        return f"FROM {p}src WHERE id > 0"
    if qs == "select_with_join":
        return (
            f"FROM {p}src a JOIN {p}src b ON a.id = b.id"
        )
    if qs == "select_with_subquery":
        return (
            "FROM (SELECT id AS col1, val AS col2 "
            f"FROM {p}src) AS sub"
        )
    if qs == "select_with_aggregate":
        return f"FROM {p}src"
    return f"FROM {p}src"


def _with_clause(a: dict[str, str], p: str) -> str:
    """The WITH clause prefix, or empty."""

    wc = a.get("with_clause", "without_with")
    if wc == "with_simple":
        return f"WITH cte AS (SELECT 1 AS x) "
    if wc == "with_recursive":
        return (
            "WITH RECURSIVE cte AS ("
            "SELECT 1 AS x "
            "UNION ALL "
            f"SELECT x + 1 FROM cte WHERE x < 5) "
        )
    return ""


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary SELECT INTO statement."""

    parts: list[str] = []
    with_prefix = _with_clause(a, p)
    if with_prefix:
        parts.append(with_prefix.rstrip())
    select_kw = "SELECT"
    sm = _select_modifier(a)
    if sm:
        select_kw = f"SELECT {sm}"
    parts.append(select_kw)
    parts.append(_select_list(a, p))
    parts.append("INTO")
    ttp = _table_type_prefix(a)
    if ttp:
        parts.append(ttp)
    kt = _keyword_table_clause(a)
    if kt:
        parts.append(kt)
    parts.append(_output_name(a, p))
    from_body = _from_clause(a, p)
    if from_body:
        parts.append(from_body)
    return " ".join(parts) + ";"


def _needs_source_table(a: dict[str, str]) -> bool:
    """Whether the query reads FROM a source fixture table."""

    qe = a.get("query_error", "none")
    if qe == "source_table_not_exists":
        return False
    return _source_exists(a)


def _needs_precreate_target(a: dict[str, str]) -> bool:
    """Whether the target table must be pre-created (already_exists)."""

    return a.get("object_state") == "already_exists"


def _needs_schema(a: dict[str, str]) -> bool:
    shape = a.get("table_name_shape", "simple")
    sd = a.get("schema_dependency", "schema_exists")
    return shape == "schema_qualified" and sd != "schema_not_exists"


def _tables_to_drop(a: dict[str, str], p: str) -> list[str]:
    """All plain-tracked created table names for the cleanup DROP list."""

    tables: list[str] = []
    if _needs_source_table(a):
        tables.append(f"{p}src")
    shape = a.get("table_name_shape", "simple")
    if shape == "schema_qualified":
        tables.append(f"{p}sch.{p}t")
    elif shape in ("simple", "quoted", "reserved_word",
                   "non_existent_schema", "long_identifier"):
        tables.append(_output_name_plain(a, p))
    if _needs_precreate_target(a):
        plain = _output_name_plain(a, p)
        if plain not in tables:
            tables.append(plain)
    return tables


def _build_setup(
    a: dict[str, str], p: str
) -> tuple[list[str], str]:
    lines: list[str] = []
    locus = "target.select_into"

    # Schema creation for schema_qualified with existing schema
    if _needs_schema(a):
        lines.append(f"CREATE SCHEMA IF NOT EXISTS {p}sch;")
        locus = "fixture.schema"

    # Source fixture table
    if _needs_source_table(a):
        lines.append(
            f"CREATE TABLE {p}src (id integer, val text);"
        )
        lines.append(
            f"INSERT INTO {p}src VALUES (1, 'a'), (2, 'b');"
        )
        locus = "fixture.source_table"

    # Pre-create target for already_exists / duplicate_table_name
    if _needs_precreate_target(a):
        plain = _output_name_plain(a, p)
        lines.append(
            f"CREATE TABLE {plain} (id integer, val text);"
        )
        locus = "fixture.duplicate_table"

    if not lines:
        lines.append("SELECT 1 AS target_table_intentionally_absent;")
        locus = "fixture.table_missing"

    return lines, locus


def _probe_select(
    a: dict[str, str], p: str
) -> str:
    """Catalog-audit oracle with top-level ORDER BY."""

    mode = a.get("verification_mode", "pg_class_catalog_query")
    name = _output_name_plain(a, p)
    shape = a.get("table_name_shape", "simple")

    if _is_failure(a):
        return (
            "SELECT count(*) AS target_created_count "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{name}' "
            "AND c.relkind = 'r' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "information_schema_tables":
        return (
            "SELECT count(*) AS table_count "
            "FROM information_schema.tables "
            f"WHERE table_name = '{name}' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "SELECT_count":
        return (
            f"SELECT count(*) AS row_count FROM {name} "
            "ORDER BY count(*)"
            ";"
        )
    return (
        "SELECT count(*) AS table_count "
        "FROM pg_catalog.pg_class c "
        f"WHERE c.relname = '{name}' "
        "AND c.relkind = 'r' "
        "ORDER BY count(*)"
        ";"
    )


def _build_pre_cleanup(
    a: dict[str, str], p: str
) -> tuple[str, ...]:
    tables = _tables_to_drop(a, p)
    lines: list[str] = []
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if _needs_schema(a):
        lines.append(f"DROP SCHEMA IF EXISTS {p}sch CASCADE;")
    if not lines:
        lines.append("SELECT 1 AS pre_cleanup_no_objects;")
    return tuple(lines)


def _build_cleanup(
    a: dict[str, str], p: str
) -> tuple[str, ...]:
    lines: list[str] = []
    # Drop the schema FIRST so the final executable statement is the DROP TABLE
    # (the bookend gate requires the LAST `;`-statement to be DROP TABLE IF EXISTS
    # <all created tables>; DROP SCHEMA CASCADE removes the schema-qualified target
    # as a side effect, and the trailing DROP TABLE IF EXISTS ... is a harmless
    # no-op for it while still dropping the source fixture in the default schema).
    if _needs_schema(a):
        lines.append(f"DROP SCHEMA IF EXISTS {p}sch CASCADE;")
    tables = _tables_to_drop(a, p)
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_assert(
    case: SelectIntoFactorCase,
    a: dict[str, str],
    p: str,
) -> tuple[str, ...]:
    lines: list[str] = []
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    lines.append(_probe_select(a, p))
    return tuple(lines)


def _resolve_case(case: SelectIntoFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    setup, locus = _build_setup(a, p)
    target = _build_target(a, p)
    assert_lines = _build_assert(case, a, p)
    pre_cleanup = _build_pre_cleanup(a, p)
    cleanup = _build_cleanup(a, p)
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


def _header(case: SelectIntoFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : SELECT INTO {case.factor_key}="
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


def render_select_into_factor_case(
    case: (
        SelectIntoFactorCase
        | SelectIntoFactorExtensionCase
    ),
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地表和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append("-- 3. 执行唯一获得覆盖信用的 SELECT INTO。")
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
    case: (
        SelectIntoFactorCase
        | SelectIntoFactorExtensionCase
    ),
    out: Path,
) -> None:
    text = render_select_into_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_select_into_factor_programs(
    baseline_plan: SelectIntoFactorLoopPlan,
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


def count_primary_select_into(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*(?:WITH\b[^\n]*?)?SELECT\b[^\n]*\bINTO\b",
            region,
        )
    )


def resolve_select_into_factor_witness(
    case: (
        SelectIntoFactorCase
        | SelectIntoFactorExtensionCase
    ),
    repository_root: Path,
) -> SelectIntoFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return SelectIntoFactorWitness(
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
    "SelectIntoFactorRenderError",
    "SelectIntoFactorWitness",
    "count_primary_select_into",
    "generate_select_into_factor_programs",
    "render_select_into_factor_case",
    "resolve_select_into_factor_witness",
]
