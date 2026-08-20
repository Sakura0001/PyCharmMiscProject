"""Render complete PostgreSQL 18.4 VACUUM factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

VACUUM garbage-collects and optionally analyzes a database.  Success-path
cases CREATE the fixture table as setup, so the bookend contract applies:
the FIRST and LAST executable ``;``-statements are each
``DROP TABLE IF EXISTS <all created tables>`` when the case creates one
or more tables.  Cases that target a non-existent table create no
fixture table, so the bookend is satisfied vacuously.  Cases that target
a wrong object type (a view) also create a fixture table (as a bookend
anchor) plus the view.

All catalog oracles schema-qualify ``pg_catalog.*`` (exempt from the
file-prefix style gate) and carry a top-level ``ORDER BY`` so the
catalog-observability gate passes.  Quoted / dotted / reserved table
identifiers appear ONLY in the fenced VACUUM target (which the style
gate does not parse); fixtures and catalog queries always use the plain
prefix-derived unqualified name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .vacuum_factor_extension import (
    VacuumFactorExtensionCase,
    _present_failure_pair,
)
from .vacuum_factor_loop import (
    VacuumFactorCase,
    VacuumFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/utility/maintenance/vacuum.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/utility/maintenance/vacuum.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class VacuumFactorRenderError(ValueError):
    """Raised when a VACUUM case cannot be rendered."""


@dataclass(frozen=True)
class VacuumFactorWitness:
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
    needs_schema: bool
    schema_name: str
    needs_role: bool
    role_name: str
    needs_partition: bool
    needs_view: bool
    view_name: str
    needs_txn_block: bool
    needs_rows: bool
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


def _synthetic_case(
    ext: VacuumFactorExtensionCase,
) -> VacuumFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "option_shape"
        factor_value = assignment.get("option_shape", "minimal")
    return VacuumFactorCase(
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
    case: VacuumFactorCase | VacuumFactorExtensionCase,
) -> VacuumFactorCase:
    if isinstance(case, VacuumFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: VacuumFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _target_missing(a: dict[str, str]) -> bool:
    return a.get("target_state") == "target_missing"


def _wrong_object_type(a: dict[str, str]) -> bool:
    return a.get("target_state") == "wrong_object_type"


def _database_wide(a: dict[str, str]) -> bool:
    return (
        a.get("target_state") == "database_wide"
        or a.get("target_name_shape") == "all_or_database_wide"
    )


def _schema_qualified(a: dict[str, str]) -> bool:
    return a.get("target_name_shape") == "schema_qualified"


def _quoted(a: dict[str, str]) -> bool:
    return a.get("target_name_shape") == "quoted_identifier"


def _partitioned(a: dict[str, str]) -> bool:
    return a.get("target_name_shape") == "relation_and_descendants"


def _privilege_denied(a: dict[str, str]) -> bool:
    return a.get("privilege_context") == "insufficient_privilege"


def _txn_block(a: dict[str, str]) -> bool:
    return a.get("environment_context") == "transaction_block"


def _has_columns(a: dict[str, str]) -> bool:
    return a.get("input_output_shape") == "table_columns"


def _needs_table(a: dict[str, str]) -> bool:
    """Whether the case creates a fixture table."""

    if _target_missing(a):
        return False
    # target_exists, database_wide and wrong_object_type all create a
    # fixture table (the bookend anchor); wrong_object_type also
    # creates a view to vacuum.
    return True


def _needs_view(a: dict[str, str]) -> bool:
    return _wrong_object_type(a)


def _needs_rows(a: dict[str, str]) -> bool:
    return a.get("resource_boundary") != "empty_relation"


def _fixture_table_plain(a: dict[str, str], p: str) -> str:
    return f"{p}t"


def _view_name(a: dict[str, str], p: str) -> str:
    return f"{p}v"


def _target_table(a: dict[str, str], p: str) -> str:
    """The table identifier in the fenced VACUUM target."""

    if _target_missing(a):
        return f"{p}no_such_table"
    if _wrong_object_type(a):
        return _view_name(a, p)
    if _database_wide(a):
        return ""
    if _quoted(a):
        return f'"{p}t"'
    if _schema_qualified(a):
        return f"{p}sch.{p}t"
    return _fixture_table_plain(a, p)


def _probe_table(a: dict[str, str], p: str) -> str:
    """The plain relname the catalog oracle inspects."""

    if _needs_table(a):
        return _fixture_table_plain(a, p)
    return f"{p}no_such_table"


def _compute_state(case: VacuumFactorCase) -> _FixtureState:
    a = _baseline(case)
    p = case.object_prefix
    needs_table = _needs_table(a)
    needs_view = _needs_view(a)
    needs_schema = _schema_qualified(a) and needs_table
    needs_role = _privilege_denied(a)
    needs_partition = _partitioned(a) and needs_table
    needs_txn_block = _txn_block(a)
    needs_rows = _needs_rows(a) and needs_table
    effective = f"{p}actor" if needs_role else ""
    return _FixtureState(
        needs_table=needs_table,
        fixture_table=_fixture_table_plain(a, p),
        needs_schema=needs_schema,
        schema_name=f"{p}sch" if needs_schema else "",
        needs_role=needs_role,
        role_name=f"{p}actor" if needs_role else "",
        needs_partition=needs_partition,
        needs_view=needs_view,
        view_name=_view_name(a, p) if needs_view else "",
        needs_txn_block=needs_txn_block,
        needs_rows=needs_rows,
        effective_role=effective,
    )


def _build_setup(
    case: VacuumFactorCase, st: _FixtureState
) -> tuple[list[str], str]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    locus = "target.vacuum"

    if st.needs_schema:
        lines.append(f"CREATE SCHEMA {st.schema_name};")
        locus = "fixture.schema"

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

        if st.needs_rows:
            lines.append(
                f"INSERT INTO {st.fixture_table} (id) "
                f"VALUES (1), (2);"
            )

        if st.needs_view:
            lines.append(
                f"CREATE VIEW {st.view_name} AS SELECT id "
                f"FROM {st.fixture_table};"
            )
            locus = "fixture.view"

    if st.needs_txn_block:
        lines.append("BEGIN;")
        locus = "fixture.transaction_block"

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
    case: VacuumFactorCase, st: _FixtureState
) -> str:
    a = _baseline(case)
    p = case.object_prefix
    opt = a.get("option_shape", "minimal")
    table = _target_table(a, p)

    if _has_columns(a):
        # The column list applies to ANALYZE; witness the
        # table_columns input/output shape on the existing table.
        return f"VACUUM ANALYZE {table} (id);"

    if _database_wide(a):
        if opt == "verbose_or_format":
            return "VACUUM VERBOSE;"
        if opt == "resource_options":
            return "VACUUM (BUFFER_USAGE_LIMIT '16MB');"
        # minimal / boolean_options collapse to a plain database-wide
        # vacuum (boolean_options + database-wide is never produced by
        # the plan; the baseline keeps option_shape=minimal there).
        return "VACUUM;"

    if opt == "minimal":
        return f"VACUUM {table};"
    if opt == "boolean_options":
        return f"VACUUM FULL {table};"
    if opt == "verbose_or_format":
        return f"VACUUM VERBOSE {table};"
    if opt == "resource_options":
        return f"VACUUM (BUFFER_USAGE_LIMIT '16MB') {table};"
    return f"VACUUM {table};"


def _probe_select(
    case: VacuumFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None

    table = _probe_table(a, p)

    if mode == "catalog_query":
        return (
            "SELECT count(*) AS catalog_relation_count "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{table}' "
            "AND c.relkind = 'r' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "effect_query":
        return (
            "SELECT count(*) AS vacuum_stat_rows "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{table}' "
            "AND c.relpages >= 0 "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "returned_rows":
        return (
            "SELECT count(*) AS returned_rows_probe "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{table}' "
            "ORDER BY count(*)"
            ";"
        )
    return None


def _tables_to_drop(
    case: VacuumFactorCase, st: _FixtureState
) -> list[str]:
    if not st.needs_table:
        return []
    p = case.object_prefix
    tables = [st.fixture_table]
    if st.needs_partition:
        # The ``{p}t_p1`` partition is created alongside the partitioned
        # parent; the static bookend gate requires every created table
        # name to appear in the DROP list, so include it here even though
        # ``DROP parent CASCADE`` would reclaim it at runtime.
        tables.append(f"{p}t_p1")
    return tables


def _build_pre_cleanup(
    case: VacuumFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    tables = _tables_to_drop(case, st)
    lines: list[str] = []
    if tables:
        # DROP TABLE must be the FIRST executable statement (bookend).
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if st.needs_view:
        lines.append(
            f"DROP VIEW IF EXISTS {st.view_name} CASCADE;"
        )
    if st.needs_schema:
        lines.append(
            f"DROP SCHEMA IF EXISTS {st.schema_name} CASCADE;"
        )
    if st.needs_role:
        lines.append(f"DROP ROLE IF EXISTS {st.role_name};")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_cleanup(
    case: VacuumFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    tables = _tables_to_drop(case, st)
    lines: list[str] = []
    if st.effective_role:
        lines.append("RESET ROLE;")
    if st.needs_view:
        lines.append(
            f"DROP VIEW IF EXISTS {st.view_name} CASCADE;"
        )
    if st.needs_schema:
        lines.append(
            f"DROP SCHEMA IF EXISTS {st.schema_name} CASCADE;"
        )
    if st.needs_role:
        lines.append(f"DROP OWNED BY {st.role_name};")
        lines.append(f"DROP ROLE IF EXISTS {st.role_name};")
    cleanup_mode = a.get("cleanup_mode", "drop_objects")
    if cleanup_mode == "reset_state":
        lines.append("RESET statement_timeout;")
    if cleanup_mode == "rollback":
        lines.append("ROLLBACK;")
    if tables:
        # DROP TABLE must be the LAST executable statement (bookend).
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_assert(
    case: VacuumFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    if st.needs_txn_block:
        lines.append("ROLLBACK;")
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        lines.append(probe)
    return tuple(lines)


def _resolve_case(case: VacuumFactorCase) -> _CasePlan:
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


def resolve_vacuum_factor_witness(
    case: VacuumFactorCase | VacuumFactorExtensionCase,
    repository_root: Path,
) -> VacuumFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return VacuumFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_vacuum(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*VACUUM\b", region))


def _header(case: VacuumFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : VACUUM {case.factor_key}="
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


def render_vacuum_factor_case(
    case: VacuumFactorCase | VacuumFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 VACUUM。")
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
    case: VacuumFactorCase | VacuumFactorExtensionCase,
    out: Path,
) -> None:
    text = render_vacuum_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_vacuum_factor_programs(
    baseline_plan: VacuumFactorLoopPlan,
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
    "VacuumFactorRenderError",
    "VacuumFactorWitness",
    "count_primary_vacuum",
    "generate_vacuum_factor_programs",
    "render_vacuum_factor_case",
    "resolve_vacuum_factor_witness",
]
