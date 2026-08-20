"""Render complete PostgreSQL 18.4 REINDEX factor-loop programs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .reindex_factor_extension import (
    ReindexFactorExtensionCase,
    _present_failure_pair,
)
from .reindex_factor_loop import (
    ReindexFactorCase,
    ReindexFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/index/reindex.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/index/reindex.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class ReindexFactorRenderError(ValueError):
    """Raised when a REINDEX case cannot be rendered."""


@dataclass(frozen=True)
class ReindexFactorWitness:
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
    needs_index: bool
    fixture_index: str
    needs_schema: bool
    schema_name: str
    needs_role: bool
    role_name: str
    needs_partition: bool
    needs_tablespace: bool
    tablespace_name: str
    effective_role: str
    target_type: str


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
    ext: ReindexFactorExtensionCase,
) -> ReindexFactorCase:
    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "statement_branch"
        factor_value = assignment.get(
            "statement_branch", "reindex_index"
        )
    return ReindexFactorCase(
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
    case: ReindexFactorCase | ReindexFactorExtensionCase,
) -> ReindexFactorCase:
    if isinstance(case, ReindexFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: ReindexFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _object_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "not_exists"


def _privilege_denied(a: dict[str, str]) -> bool:
    return a.get("permission") in (
        "insufficient_privilege",
        "non_owner",
    )


def _is_system_branch(a: dict[str, str]) -> bool:
    return a.get("statement_branch") == "reindex_system"


def _is_database_branch(a: dict[str, str]) -> bool:
    return a.get("statement_branch") == "reindex_database"


def _needs_table(a: dict[str, str]) -> bool:
    if _object_missing(a):
        return False
    if _is_system_branch(a):
        return False
    return True


def _needs_index(a: dict[str, str]) -> bool:
    branch = a.get("statement_branch", "reindex_index")
    if branch == "reindex_table":
        return False
    if _object_missing(a):
        return False
    if _is_system_branch(a):
        return False
    return True


def _needs_schema(a: dict[str, str]) -> bool:
    return a.get("name_shape") == "schema_qualified"


def _needs_partition(a: dict[str, str]) -> bool:
    return (
        a.get("partition_behavior")
        == "partitioned_separate_transaction"
    )


def _needs_tablespace(a: dict[str, str]) -> bool:
    return a.get("option_tablespace") == "present_custom"


def _fixture_table(a: dict[str, str], p: str) -> str:
    return f"{p}t"


def _fixture_index(a: dict[str, str], p: str) -> str:
    return f"{p}i"


def _target_name(a: dict[str, str], p: str) -> str:
    shape = a.get("name_shape", "plain_identifier")
    branch = a.get("statement_branch", "reindex_index")
    if _object_missing(a) or shape == "missing_object":
        return f"{p}no_such_obj"
    if branch in ("reindex_database", "reindex_system"):
        return f"{p}db"
    if shape == "quoted_identifier":
        return f'"{p}t"'
    if shape == "schema_qualified":
        return f"{p}sch.{p}t"
    if shape == "reserved_word":
        return '"user"'
    return _fixture_table(a, p)


def _build_options_clause(a: dict[str, str], p: str) -> str:
    parts: list[str] = []
    oc = a.get("option_concurrently", "absent")
    ov = a.get("option_verbose", "absent")
    ot = a.get("option_tablespace", "absent")
    bv = a.get("boolean_value", "omitted_default")
    bool_map = {
        "true_keyword": "TRUE",
        "false_keyword": "FALSE",
        "on_keyword": "ON",
        "off_keyword": "OFF",
        "one_numeric": "1",
        "zero_numeric": "0",
        "omitted_default": "",
    }
    if oc == "present_true":
        parts.append("CONCURRENTLY TRUE")
    elif oc == "present_false":
        parts.append("CONCURRENTLY FALSE")
    elif oc == "present_boolean_keyword":
        parts.append("CONCURRENTLY")
    if ov == "present_true":
        parts.append("VERBOSE TRUE")
    elif ov == "present_false":
        parts.append("VERBOSE FALSE")
    elif a.get("option_verbose") == "absent" and bv != "omitted_default":
        pass
    if ot == "present_custom":
        parts.append(f"TABLESPACE {p}ts")
    elif ot == "present_default":
        parts.append("TABLESPACE pg_default")
    if parts:
        return f"({', '.join(parts)})"
    return ""


def _build_target(
    case: ReindexFactorCase, st: _FixtureState
) -> str:
    a = _baseline(case)
    p = case.object_prefix
    branch = a.get("statement_branch", "reindex_index")
    name = _target_name(a, p)
    opts = _build_options_clause(a, p)
    verbose_kw = ""
    if a.get("option_verbose", "absent") == "present_true":
        pass
    concurrently_kw = ""
    if a.get("concurrently_keyword", "false") == "true":
        concurrently_kw = "CONCURRENTLY "
    type_map = {
        "reindex_index": "INDEX",
        "reindex_table": "TABLE",
        "reindex_schema": "SCHEMA",
        "reindex_database": "DATABASE",
        "reindex_system": "SYSTEM",
    }
    obj_type = type_map.get(branch, "INDEX")
    prefix = "REINDEX "
    if a.get("option_verbose", "absent") == "present_true" and not opts:
        prefix += "VERBOSE "
    if opts:
        prefix += f"{opts} "
    if branch in ("reindex_database", "reindex_system"):
        return f"{prefix}{obj_type} {concurrently_kw}{name};"
    return f"{prefix}{obj_type} {concurrently_kw}{name};"


def _probe_select(
    case: ReindexFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    mode = a.get("verification_mode", "catalog_validity_check")
    if mode == "verbose_output_check":
        return None
    branch = a.get("statement_branch", "reindex_index")
    table_plain = _fixture_table(a, p)
    index_plain = _fixture_index(a, p)
    if mode == "catalog_validity_check":
        if branch == "reindex_table" and not _object_missing(a):
            return (
                "SELECT count(*) AS table_exists_count "
                "FROM pg_catalog.pg_class c "
                f"WHERE c.relname = '{table_plain}' "
                "AND c.relkind = 'r' "
                "ORDER BY count(*) LIMIT 1;"
            )
        if _object_missing(a) or _is_system_branch(a):
            return None
        return (
            "SELECT count(*) AS index_validity_count "
            "FROM pg_catalog.pg_class c "
            "JOIN pg_catalog.pg_index i "
            "ON i.indexrelid = c.oid "
            f"WHERE c.relname = '{index_plain}' "
            "AND c.relkind = 'i' "
            "AND i.indisvalid "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "invalid_index_detection":
        if _object_missing(a) or _is_system_branch(a):
            return None
        return (
            "SELECT count(*) AS invalid_index_count "
            "FROM pg_catalog.pg_class c "
            "JOIN pg_catalog.pg_index i "
            "ON i.indexrelid = c.oid "
            f"WHERE c.relname LIKE '{p}%' "
            "AND c.relkind = 'i' "
            "AND NOT i.indisvalid "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "search_path_sandbox":
        return (
            "SELECT count(*) AS search_path_count "
            "FROM pg_catalog.pg_settings "
            "WHERE name = 'search_path' "
            "ORDER BY count(*) LIMIT 1;"
        )
    return None


def _compute_state(
    case: ReindexFactorCase,
) -> _FixtureState:
    a = _baseline(case)
    p = case.object_prefix
    needs_table = _needs_table(a)
    needs_index = _needs_index(a)
    needs_schema = _needs_schema(a) and needs_table
    needs_role = _privilege_denied(a)
    needs_partition = _needs_partition(a) and needs_table
    needs_tablespace = _needs_tablespace(a)
    effective = f"{p}actor" if needs_role else ""
    type_map = {
        "reindex_index": "INDEX",
        "reindex_table": "TABLE",
        "reindex_schema": "SCHEMA",
        "reindex_database": "DATABASE",
        "reindex_system": "SYSTEM",
    }
    return _FixtureState(
        needs_table=needs_table,
        fixture_table=_fixture_table(a, p),
        needs_index=needs_index,
        fixture_index=_fixture_index(a, p),
        needs_schema=needs_schema,
        schema_name=f"{p}sch" if needs_schema else "",
        needs_role=needs_role,
        role_name=f"{p}actor" if needs_role else "",
        needs_partition=needs_partition,
        needs_tablespace=needs_tablespace,
        tablespace_name=f"{p}ts" if needs_tablespace else "",
        effective_role=effective,
        target_type=type_map.get(
            a.get("statement_branch", "reindex_index"), "INDEX"
        ),
    )


def _build_setup(
    case: ReindexFactorCase, st: _FixtureState
) -> tuple[list[str], str]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    locus = "target.reindex"

    if st.needs_schema:
        lines.append(f"CREATE SCHEMA {st.schema_name};")
        locus = "fixture.schema"

    if st.needs_tablespace:
        lines.append(
            f"CREATE TABLESPACE {st.tablespace_name} "
            f"LOCATION '/tmp/{p}ts';"
        )
        locus = "fixture.tablespace"

    if st.needs_role:
        lines.append(
            f"CREATE ROLE {st.role_name} LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"

    if st.needs_table:
        if st.needs_partition:
            lines.append(
                f"CREATE TABLE {st.fixture_table} "
                f"(id integer) PARTITION BY RANGE (id);"
            )
            lines.append(
                f"CREATE TABLE {p}t_p1 PARTITION OF "
                f"{st.fixture_table} "
                f"FOR VALUES FROM (0) TO (1000);"
            )
        else:
            lines.append(
                f"CREATE TABLE {st.fixture_table} "
                f"(id integer);"
            )
        locus = "fixture.table"

    if st.needs_index:
        lines.append(
            f"CREATE INDEX {st.fixture_index} "
            f"ON {st.fixture_table} (id);"
        )
        locus = "fixture.index"

    if st.effective_role:
        lines.append(f"SET ROLE {st.effective_role};")
        locus = "fixture.role_armed"

    if not lines:
        lines.append(
            "SELECT 1 AS target_object_intentionally_absent;"
        )
        locus = "fixture.object_missing"

    return lines, locus


def _tables_to_drop(
    case: ReindexFactorCase, st: _FixtureState
) -> list[str]:
    if not st.needs_table:
        return []
    p = case.object_prefix
    tables = [st.fixture_table]
    if st.needs_partition:
        tables.append(f"{p}t_p1")
    return tables


def _build_pre_cleanup(
    case: ReindexFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    lines: list[str] = []
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if st.needs_schema:
        lines.append(
            f"DROP SCHEMA IF EXISTS {st.schema_name} CASCADE;"
        )
    if st.needs_tablespace:
        lines.append(
            f"DROP TABLESPACE IF EXISTS {st.tablespace_name};"
        )
    if st.needs_role:
        lines.append(f"DROP ROLE IF EXISTS {st.role_name};")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_cleanup(
    case: ReindexFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    lines: list[str] = []
    if st.effective_role:
        lines.append("RESET ROLE;")
    if st.needs_schema:
        lines.append(
            f"DROP SCHEMA IF EXISTS {st.schema_name} CASCADE;"
        )
    if st.needs_tablespace:
        lines.append(
            f"DROP TABLESPACE IF EXISTS {st.tablespace_name};"
        )
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
    case: ReindexFactorCase, st: _FixtureState
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


def _resolve_case(case: ReindexFactorCase) -> _CasePlan:
    st = _compute_state(case)
    setup, locus = _build_setup(case, st)
    target = _build_target(case, st)
    assert_lines = _build_assert(case, st)
    pre_cleanup = _build_pre_cleanup(case, st)
    cleanup = _build_cleanup(case, st)
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


def resolve_reindex_factor_witness(
    case: ReindexFactorCase | ReindexFactorExtensionCase,
    repository_root: Path,
) -> ReindexFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return ReindexFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_reindex(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*REINDEX\b", region))


def _header(case: ReindexFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : REINDEX {case.factor_key}="
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


def render_reindex_factor_case(
    case: ReindexFactorCase | ReindexFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 REINDEX。")
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
    case: ReindexFactorCase | ReindexFactorExtensionCase,
    out: Path,
) -> None:
    text = render_reindex_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_reindex_factor_programs(
    baseline_plan: ReindexFactorLoopPlan,
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
    "ReindexFactorRenderError",
    "ReindexFactorWitness",
    "count_primary_reindex",
    "generate_reindex_factor_programs",
    "render_reindex_factor_case",
    "resolve_reindex_factor_witness",
]
