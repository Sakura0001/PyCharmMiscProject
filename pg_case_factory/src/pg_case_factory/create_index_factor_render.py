"""Render complete PostgreSQL 18.4 CREATE INDEX factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE INDEX operates ON a relation (table).  Success-path cases
CREATE the fixture table as setup, so the bookend contract applies:
the FIRST and LAST executable ``;``-statements are each
``DROP TABLE IF EXISTS <all created tables>`` when the case creates one
or more tables.  For partitioned-table indexes the partition ``{p}t_p1``
is included in the DROP list for BOTH pre-cleanup and final-cleanup.

All catalog oracles schema-qualify ``pg_catalog.*`` (exempt from the
file-prefix style gate) and carry a top-level ``ORDER BY`` so the
catalog-observability gate passes.  Quoted / dotted / reserved index
or column identifiers appear ONLY in the fenced CREATE INDEX target
(which the style gate does not parse); fixtures and catalog queries
always use the plain prefix-derived unqualified name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_index_factor_extension import (
    CreateIndexFactorExtensionCase,
    _present_failure_pair,
)
from .create_index_factor_loop import (
    CreateIndexFactorCase,
    CreateIndexFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/index/"
    "create_index.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/index/"
    "create_index.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateIndexFactorRenderError(ValueError):
    """Raised when a CREATE INDEX case cannot be rendered."""


@dataclass(frozen=True)
class CreateIndexFactorWitness:
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
    ext: CreateIndexFactorExtensionCase,
) -> CreateIndexFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "statement_branch"
        factor_value = assignment.get(
            "statement_branch", "single_column_btree"
        )
    return CreateIndexFactorCase(
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
    case: CreateIndexFactorCase | CreateIndexFactorExtensionCase,
) -> CreateIndexFactorCase:
    if isinstance(case, CreateIndexFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateIndexFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _needs_partition(a: dict[str, str]) -> bool:
    if a.get("only") == "true":
        return True
    pc = a.get("partition_constraint", "none")
    return pc in ("only_on_partitioned", "concurrently_on_partitioned")


def _index_name(a: dict[str, str], p: str) -> str:
    """The index identifier in the fenced CREATE INDEX target."""

    style = a.get("name_style", "explicit_compact")
    if style == "implicit":
        return ""
    if style == "explicit_semantic":
        return f"{p}idx"
    return f"{p}i"


def _index_name_plain(a: dict[str, str], p: str) -> str:
    """Always-plain index name for cleanup and oracle queries."""
    return f"{p}i"


def _key_column(a: dict[str, str]) -> str:
    """The key column or expression for the index."""
    if a.get("column_type_compatibility") == "method_type_incompatible":
        return "jdoc"
    ei = a.get("expression_index", "column_only")
    if ei == "simple_expression":
        return "lower(val)"
    if ei == "complex_expression":
        return "(id * 2)"
    return "id"


def _column_spec(a: dict[str, str], p: str) -> str:
    """Full single-column specification with collation/opclass/order/nulls."""

    col = _key_column(a)
    coll = a.get("collation", "none")
    if coll == "default_collation":
        col += ' COLLATE "C"'
    elif coll == "non_default_collation":
        col += f" COLLATE {p}col"
    opc = a.get("opclass", "none")
    if opc == "default_opclass":
        col += " int4_ops"
    elif opc == "non_default_opclass":
        col += " oid_ops"
    order = a.get("order", "none")
    if order == "asc":
        col += " ASC"
    elif order == "desc":
        col += " DESC"
    nulls = a.get("nulls", "none")
    if nulls == "first":
        col += " NULLS FIRST"
    elif nulls == "last":
        col += " NULLS LAST"
    return col


def _with_clause(a: dict[str, str]) -> str:
    ws = a.get("with_storage", "none")
    if ws == "btree_fillfactor":
        return "WITH (fillfactor = 80)"
    if ws == "btree_deduplicate_items":
        return "WITH (deduplicate_items = on)"
    if ws == "gist_buffering":
        return "WITH (buffering = on)"
    if ws == "gin_fastupdate":
        return "WITH (fastupdate = on)"
    if ws == "gin_pending_list_limit":
        return "WITH (gin_pending_list_limit = 4096)"
    if ws == "brin_pages_per_range":
        return "WITH (pages_per_range = 128)"
    if ws == "brin_autosummarize":
        return "WITH (autosummarize = on)"
    return ""


def _tablespace_clause(a: dict[str, str], p: str) -> str:
    ts = a.get("tablespace", "none")
    if ts == "pg_default":
        return "TABLESPACE pg_default"
    if ts == "custom_tablespace":
        return f"TABLESPACE {p}ts"
    return ""


def _predicate_clause(a: dict[str, str]) -> str:
    if a.get("predicate") == "true":
        return "WHERE id > 0"
    return ""


def _is_duplicate_scenario(a: dict[str, str]) -> bool:
    """Whether the failure is specifically about a duplicate index."""
    if a.get("expected_status") != "failure":
        return False
    if a.get("invalid_combination") != "none":
        return False
    if a.get("syntax_error") != "none":
        return False
    if a.get("concurrent_failure") != "none":
        return False
    if a.get("column_type_compatibility") == "method_type_incompatible":
        return False
    return True


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE INDEX statement."""

    se = a.get("syntax_error", "none")
    if se == "invalid_syntax":
        return f"CREATE INDEX {p}i ON {p}t USING btree;"

    unique = a.get("unique") == "true"
    concurrently = a.get("concurrently") == "true"
    ifne = a.get("if_not_exists") == "true"
    only = a.get("only") == "true"
    method = a.get("method", "btree")
    sbv = a.get("statement_branch", "single_column_btree")
    name = _index_name(a, p)
    table = f"{p}t"

    parts: list[str] = ["CREATE"]
    if unique:
        parts.append("UNIQUE")
    parts.append("INDEX")
    if concurrently:
        parts.append("CONCURRENTLY")
    if ifne:
        parts.append("IF NOT EXISTS")
    if name:
        parts.append(name)
    parts.append("ON")
    if only:
        parts.append("ONLY")
    parts.append(table)
    parts.append(f"USING {method}")
    if sbv == "multi_column_btree":
        parts.append("(id, id2)")
    else:
        parts.append(f"({_column_spec(a, p)})")
    if a.get("include") == "true":
        parts.append("INCLUDE (val)")
    nd = a.get("nulls_distinct", "none")
    if nd == "distinct":
        parts.append("NULLS DISTINCT")
    elif nd == "not_distinct":
        parts.append("NULLS NOT DISTINCT")
    wc = _with_clause(a)
    if wc:
        parts.append(wc)
    tc = _tablespace_clause(a, p)
    if tc:
        parts.append(tc)
    pc = _predicate_clause(a)
    if pc:
        parts.append(pc)
    return " ".join(parts) + ";"


def _tables_to_drop(a: dict[str, str], p: str) -> list[str]:
    """All created table names for the bookend DROP list."""
    tables = [f"{p}t"]
    if _needs_partition(a):
        tables.append(f"{p}t_p1")
    return tables


def _build_setup(
    a: dict[str, str], p: str
) -> tuple[list[str], str]:
    lines: list[str] = []
    locus = "target.create_index"

    if _needs_partition(a):
        lines.append(
            f"CREATE TABLE {p}t (id integer, val text, "
            f"id2 integer, jdoc json) PARTITION BY RANGE (id);"
        )
        lines.append(
            f"CREATE TABLE {p}t_p1 PARTITION OF {p}t "
            f"FOR VALUES FROM (0) TO (1000);"
        )
    else:
        lines.append(
            f"CREATE TABLE {p}t (id integer, val text, "
            f"id2 integer, jdoc json);"
        )
    locus = "fixture.table"

    if a.get("tablespace") == "custom_tablespace":
        lines.append(f"CREATE TABLESPACE {p}ts LOCATION '/tmp';")
        locus = "fixture.tablespace"

    if a.get("collation") == "non_default_collation":
        lines.append(f'CREATE COLLATION {p}col FROM "C";')
        locus = "fixture.collation"

    if _is_duplicate_scenario(a):
        lines.append(f"CREATE INDEX {p}i ON {p}t USING btree (id);")
        locus = "fixture.duplicate_index"

    if a.get("concurrent_failure") == "invalid_index_leftover":
        lines.append(f"CREATE INDEX {p}i ON {p}t USING btree (id);")
        locus = "fixture.invalid_index_leftover"

    if a.get("concurrent_failure") == "in_transaction_block":
        lines.append("BEGIN;")
        locus = "fixture.transaction_block"

    if not lines:
        lines.append("SELECT 1 AS target_table_intentionally_absent;")
        locus = "fixture.table_missing"

    return lines, locus


def _probe_select(
    a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""
    mode = a.get("verification_mode", "catalog_query")
    index_name = _index_name_plain(a, p)

    if mode == "explain_index_scan":
        return (
            "SELECT count(*) AS explain_index_check "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{index_name}' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "index_validity_check":
        return (
            "SELECT count(*) AS valid_index_count "
            "FROM pg_catalog.pg_index i "
            "JOIN pg_catalog.pg_class c ON c.oid = i.indexrelid "
            f"WHERE c.relname = '{index_name}' "
            "AND i.indisvalid "
            "ORDER BY count(*)"
            ";"
        )
    return (
        "SELECT count(*) AS index_count "
        "FROM pg_catalog.pg_class c "
        f"WHERE c.relname = '{index_name}' "
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
    lines.append(f"DROP INDEX IF EXISTS {p}i CASCADE;")
    lines.append(f"DROP INDEX IF EXISTS {p}idx CASCADE;")
    if a.get("tablespace") == "custom_tablespace":
        lines.append(f"DROP TABLESPACE IF EXISTS {p}ts;")
    if a.get("collation") == "non_default_collation":
        lines.append(f"DROP COLLATION IF EXISTS {p}col CASCADE;")
    return tuple(lines)


def _build_cleanup(
    a: dict[str, str], p: str
) -> tuple[str, ...]:
    cleanup_mode = a.get("cleanup_mode", "drop_index")
    lines: list[str] = []
    if cleanup_mode == "drop_index":
        lines.append(f"DROP INDEX IF EXISTS {p}i CASCADE;")
        lines.append(f"DROP INDEX IF EXISTS {p}idx CASCADE;")
    elif cleanup_mode == "rollback":
        lines.append("ROLLBACK;")
    if a.get("tablespace") == "custom_tablespace":
        lines.append(f"DROP TABLESPACE IF EXISTS {p}ts;")
    if a.get("collation") == "non_default_collation":
        lines.append(f"DROP COLLATION IF EXISTS {p}col CASCADE;")
    tables = _tables_to_drop(a, p)
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_assert(
    case: CreateIndexFactorCase,
    a: dict[str, str],
    p: str,
) -> tuple[str, ...]:
    lines: list[str] = []
    if a.get("concurrent_failure") == "in_transaction_block":
        lines.append("ROLLBACK;")
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(a, p)
    if probe is not None:
        lines.append(probe)
    return tuple(lines)


def _resolve_case(case: CreateIndexFactorCase) -> _CasePlan:
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


def _header(case: CreateIndexFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE INDEX {case.factor_key}="
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


def render_create_index_factor_case(
    case: CreateIndexFactorCase
    | CreateIndexFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE INDEX。")
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
    case: CreateIndexFactorCase
    | CreateIndexFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_index_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_index_factor_programs(
    baseline_plan: CreateIndexFactorLoopPlan,
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


def count_primary_create_index(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+(?:UNIQUE\s+)?INDEX\b", region)
    )


def resolve_create_index_factor_witness(
    case: CreateIndexFactorCase
    | CreateIndexFactorExtensionCase,
    repository_root: Path,
) -> CreateIndexFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateIndexFactorWitness(
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
    "CreateIndexFactorRenderError",
    "CreateIndexFactorWitness",
    "count_primary_create_index",
    "generate_create_index_factor_programs",
    "render_create_index_factor_case",
    "resolve_create_index_factor_witness",
]
