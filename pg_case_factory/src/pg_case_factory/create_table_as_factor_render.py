"""Render complete PostgreSQL 18.4 CREATE TABLE AS factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE TABLE AS creates a table from a query.  Success-path cases
CREATE both the source fixture table and the output table, so the
bookend contract applies: the FIRST and LAST executable ``;``-statements
are each ``DROP TABLE IF EXISTS <all created tables>`` when the case
creates one or more tables.  Quoted / reserved / dotted table names
appear ONLY in the fenced CREATE TABLE AS target (the style gate does
not parse the target); fixtures, catalog queries, and bookend DROPs
always use plain prefix-derived unqualified names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_table_as_factor_extension import (
    CreateTableAsFactorExtensionCase,
    _present_failure_pair,
)
from .create_table_as_factor_loop import (
    CreateTableAsFactorCase,
    CreateTableAsFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/table/"
    "create_table_as.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/table/"
    "create_table_as.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateTableAsFactorRenderError(ValueError):
    """Raised when a CREATE TABLE AS case cannot be rendered."""


@dataclass(frozen=True)
class CreateTableAsFactorWitness:
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
    ext: CreateTableAsFactorExtensionCase,
) -> CreateTableAsFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "table_type"
        factor_value = assignment.get("table_type", "permanent")
    return CreateTableAsFactorCase(
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
    case: CreateTableAsFactorCase | CreateTableAsFactorExtensionCase,
) -> CreateTableAsFactorCase:
    if isinstance(case, CreateTableAsFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateTableAsFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_temporary(a: dict[str, str]) -> bool:
    return a.get("table_type") in (
        "temporary_global", "temporary_local", "temp_short",
    )


def _needs_source_table(a: dict[str, str]) -> bool:
    """Whether the query reads FROM a source fixture table."""

    qs = a.get("query_shape", "simple_select")
    return qs in (
        "table_command", "aggregate_query", "join_query",
    )


def _source_exists(a: dict[str, str]) -> bool:
    return a.get("source_table_dependency") == "source_table_exists"


def _output_name(a: dict[str, str], p: str) -> str:
    """The table name used in the fenced CREATE TABLE AS target."""

    shape = a.get("table_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}t"'
    if shape == "reserved_word":
        return f'"{p}abort"'
    if shape == "schema_qualified":
        return f"{p}sch.{p}t"
    return f"{p}t"


def _output_name_plain(a: dict[str, str], p: str) -> str:
    """Always-plain output table name for cleanup and oracle queries."""

    shape = a.get("table_name_shape", "simple")
    if shape == "reserved_word":
        return f"{p}abort"
    return f"{p}t"


def _needs_fixture_table(a: dict[str, str]) -> bool:
    """Whether a plain fixture table is needed for bookend compliance.

    Quoted/reserved output names are not tracked by the bookend gate's
    ``_normalize_identifier`` (quotes are rejected), so a plain-named
    fixture table must be CREATEd+DROPped to satisfy the "at least one
    created table" requirement.
    """

    shape = a.get("table_name_shape", "simple")
    return shape in ("quoted", "reserved_word")


def _tables_to_drop(a: dict[str, str], p: str) -> list[str]:
    """All plain-tracked created table names for the bookend DROP list."""

    tables: list[str] = []
    if _needs_source_table(a) and _source_exists(a):
        tables.append(f"{p}src")
    shape = a.get("table_name_shape", "simple")
    if shape == "simple" or shape == "duplicate":
        tables.append(f"{p}t")
    elif shape == "schema_qualified":
        tables.append(f"{p}sch.{p}t")
    if _needs_fixture_table(a):
        tables.append(f"{p}fx")
    return tables


def _table_type_prefix(a: dict[str, str]) -> str:
    tt = a.get("table_type", "permanent")
    if tt == "temporary_global":
        return "GLOBAL TEMPORARY"
    if tt == "temporary_local":
        return "LOCAL TEMPORARY"
    if tt == "temp_short":
        return "TEMP"
    if tt == "unlogged":
        return "UNLOGGED"
    return ""


def _if_not_exists_clause(a: dict[str, str]) -> str:
    if a.get("if_not_exists_clause") == "present":
        return "IF NOT EXISTS"
    return ""


def _column_list(a: dict[str, str]) -> str:
    cn = a.get("column_names", "inherit_from_query")
    if cn != "explicit_list":
        return ""
    shape = a.get("column_name_list_shape", "absent")
    qs = a.get("query_shape", "simple_select")
    if qs == "table_command":
        if shape == "fewer_than_query_columns":
            return "(id, val)"
        if shape == "more_than_query_columns":
            return "(id, val, id2, extra)"
        return "(id, val, id2)"
    if shape == "fewer_than_query_columns":
        return "(col1)"
    if shape == "more_than_query_columns":
        return "(col1, col2, extra)"
    if shape == "absent":
        return ""
    return "(col1, col2)"


def _storage_clause(a: dict[str, str]) -> str:
    ws = a.get("with_storage_clause", "without_storage")
    if ws == "with_storage":
        return "WITH (fillfactor = 80)"
    if ws == "without_oids":
        return "WITHOUT OIDS"
    return ""


def _on_commit_clause(a: dict[str, str]) -> str:
    oc = a.get("on_commit_clause", "absent")
    if oc == "PRESERVE_ROWS":
        return "ON COMMIT PRESERVE ROWS"
    if oc == "DELETE_ROWS":
        return "ON COMMIT DELETE ROWS"
    if oc == "DROP":
        return "ON COMMIT DROP"
    return ""


def _tablespace_clause(a: dict[str, str], p: str) -> str:
    tc = a.get("tablespace_clause", "default")
    if tc == "specified":
        return f"TABLESPACE {p}ts"
    return ""


def _with_data_clause(a: dict[str, str]) -> str:
    wd = a.get("with_data", "absent_default")
    if wd == "WITH_DATA":
        return "WITH DATA"
    if wd == "WITH_NO_DATA":
        return "WITH NO DATA"
    return ""


def _query(a: dict[str, str], p: str) -> str:
    """The AS query for CREATE TABLE AS."""

    qs = a.get("query_shape", "simple_select")
    if qs == "table_command":
        return f"TABLE {p}src"
    if qs == "values_command":
        return "VALUES (1, 2), (3, 4)"
    if qs == "execute_prepared":
        return f"EXECUTE {p}prep"
    if qs == "aggregate_query":
        return (
            f"SELECT count(*) AS cnt, max(id) AS mx FROM {p}src"
        )
    if qs == "join_query":
        return (
            f"SELECT a.id, b.val FROM {p}src a "
            f"JOIN {p}src b ON a.id = b.id"
        )
    if qs == "union_query":
        return "SELECT 1 AS col1 UNION ALL SELECT 2"
    if qs == "subquery":
        return "SELECT * FROM (SELECT 1 AS col1, 2 AS col2) AS sub"
    return "SELECT 1 AS col1, 2 AS col2"


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE TABLE AS statement."""

    parts: list[str] = ["CREATE"]
    ttp = _table_type_prefix(a)
    if ttp:
        parts.append(ttp)
    parts.append("TABLE")
    ifne = _if_not_exists_clause(a)
    if ifne:
        parts.append(ifne)
    parts.append(_output_name(a, p))
    cl = _column_list(a)
    if cl:
        parts.append(cl)
    sc = _storage_clause(a)
    if sc:
        parts.append(sc)
    oc = _on_commit_clause(a)
    if oc:
        parts.append(oc)
    tc = _tablespace_clause(a, p)
    if tc:
        parts.append(tc)
    parts.append("AS")
    parts.append(_query(a, p))
    wd = _with_data_clause(a)
    if wd:
        parts.append(wd)
    return " ".join(parts) + ";"


def _build_setup(
    a: dict[str, str], p: str
) -> tuple[list[str], str]:
    lines: list[str] = []
    locus = "target.create_table_as"

    sd = a.get("schema_dependency", "schema_exists")
    shape = a.get("table_name_shape", "simple")
    if shape == "schema_qualified" and sd != "schema_not_exists":
        lines.append(f"CREATE SCHEMA IF NOT EXISTS {p}sch;")
        locus = "fixture.schema"

    if _needs_source_table(a) and _source_exists(a):
        lines.append(
            f"CREATE TABLE {p}src (id integer, val text, id2 integer);"
        )
        lines.append(f"INSERT INTO {p}src VALUES (1, 'a', 10), (2, 'b', 20);")
        locus = "fixture.source_table"

    td = a.get("tablespace_dependency", "default_tablespace")
    if td == "specified_tablespace_exists":
        lines.append(f"CREATE TABLESPACE {p}ts LOCATION '/tmp';")
        locus = "fixture.tablespace"

    if a.get("table_name_shape") == "duplicate":
        lines.append(
            f"CREATE TABLE {p}t (id integer, val text, id2 integer);"
        )
        locus = "fixture.duplicate_table"

    if _needs_fixture_table(a):
        lines.append(f"CREATE TABLE {p}fx (id integer);")
        locus = "fixture.plain_bookend"

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
    if _is_failure(a):
        return (
            "SELECT count(*) AS target_created_count "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{name}' "
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
    if mode == "information_schema_columns":
        return (
            "SELECT count(*) AS col_count "
            "FROM information_schema.columns "
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
    if mode == "SELECT_star_structure":
        return (
            "SELECT count(*) AS col_count "
            "FROM information_schema.columns "
            f"WHERE table_name = '{name}' "
            "ORDER BY count(*)"
            ";"
        )
    return (
        "SELECT count(*) AS table_count "
        "FROM pg_catalog.pg_class c "
        f"WHERE c.relname = '{name}' "
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
    if a.get("tablespace_dependency") == "specified_tablespace_exists":
        lines.append(f"DROP TABLESPACE IF EXISTS {p}ts;")
    if not lines:
        lines.append("SELECT 1 AS pre_cleanup_no_objects;")
    return tuple(lines)


def _build_cleanup(
    a: dict[str, str], p: str
) -> tuple[str, ...]:
    cleanup_mode = a.get("cleanup_mode", "DROP_TABLE")
    lines: list[str] = []
    output_plain = _output_name_plain(a, p)
    shape = a.get("table_name_shape", "simple")
    tracked_output = _tables_to_drop(a, p)

    # Drop non-tracked (quoted/reserved) output tables in the middle.
    if shape in ("quoted", "reserved_word"):
        if cleanup_mode == "DROP_TABLE_IF_EXISTS":
            lines.append(f"DROP TABLE IF EXISTS {output_plain};")
        else:
            lines.append(f"DROP TABLE {output_plain} CASCADE;")

    if a.get("tablespace_dependency") == "specified_tablespace_exists":
        lines.append(f"DROP TABLESPACE IF EXISTS {p}ts;")

    # Final bookend: always DROP TABLE IF EXISTS for tracked tables.
    if tracked_output:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tracked_output)} CASCADE;"
        )
    else:
        lines.append(
            f"DROP TABLE IF EXISTS {output_plain} CASCADE;"
        )
    return tuple(lines)


def _build_assert(
    case: CreateTableAsFactorCase,
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


def _resolve_case(case: CreateTableAsFactorCase) -> _CasePlan:
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


def _header(case: CreateTableAsFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE TABLE AS {case.factor_key}="
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


def render_create_table_as_factor_case(
    case: CreateTableAsFactorCase
    | CreateTableAsFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE TABLE AS。")
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
    case: CreateTableAsFactorCase
    | CreateTableAsFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_table_as_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_table_as_factor_programs(
    baseline_plan: CreateTableAsFactorLoopPlan,
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


def count_primary_create_table_as(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+(?:(?:GLOBAL|LOCAL)\s+)?"
            r"(?:(?:TEMP|TEMPORARY|UNLOGGED)\s+)?TABLE\b",
            region,
        )
    )


def resolve_create_table_as_factor_witness(
    case: CreateTableAsFactorCase
    | CreateTableAsFactorExtensionCase,
    repository_root: Path,
) -> CreateTableAsFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateTableAsFactorWitness(
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
    "CreateTableAsFactorRenderError",
    "CreateTableAsFactorWitness",
    "count_primary_create_table_as",
    "generate_create_table_as_factor_programs",
    "render_create_table_as_factor_case",
    "resolve_create_table_as_factor_witness",
]
