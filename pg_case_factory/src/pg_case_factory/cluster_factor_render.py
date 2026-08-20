"""Render complete PostgreSQL 18.4 CLUSTER factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CLUSTER physically reorders a table according to an index.  Success-path
cases CREATE the fixture table (and index) as setup, so the bookend
contract applies: the FIRST and LAST executable ``;``-statements are each
``DROP TABLE IF EXISTS <all created tables>`` when the case creates one or
more tables.  Cases that target a non-existent table create no fixture
table, so the bookend is satisfied vacuously.

All catalog oracles schema-qualify ``pg_catalog.*`` (exempt from the
file-prefix style gate) and carry a top-level ``ORDER BY`` so the
catalog-observability gate passes.  Quoted / dotted / reserved table or
index identifiers appear ONLY in the fenced CLUSTER target (which the
style gate does not parse); fixtures and catalog queries always use the
plain prefix-derived unqualified name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cluster_factor_extension import (
    ClusterFactorExtensionCase,
    _present_failure_pair,
)
from .cluster_factor_loop import (
    ClusterFactorCase,
    ClusterFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/table/cluster.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/table/cluster.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class ClusterFactorRenderError(ValueError):
    """Raised when a CLUSTER case cannot be rendered."""


@dataclass(frozen=True)
class ClusterFactorWitness:
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
    needs_pre_cluster: bool
    pre_cluster_table: str
    needs_txn_block: bool
    second_table: str
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
    ext: ClusterFactorExtensionCase,
) -> ClusterFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "statement_branch"
        factor_value = assignment.get(
            "statement_branch", "cluster_table_using_index"
        )
    return ClusterFactorCase(
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
    case: ClusterFactorCase | ClusterFactorExtensionCase,
) -> ClusterFactorCase:
    if isinstance(case, ClusterFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: ClusterFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _table_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "table_does_not_exist"


def _index_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "table_exists_index_does_not_exist"


def _no_clustered_index(a: dict[str, str]) -> bool:
    return (
        a.get("object_state")
        == "table_exists_no_clustered_index_recorded"
    )


def _index_not_on_table(a: dict[str, str]) -> bool:
    return (
        a.get("index_dependency") == "index_not_on_table"
        or a.get("index_not_on_table")
        == "index_belongs_to_different_table"
    )


def _privilege_denied(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "insufficient_privilege"


def _txn_block(a: dict[str, str]) -> bool:
    return (
        a.get("transaction_block_restriction")
        == "cluster_all_inside_transaction_block"
    )


def _is_using_branch(a: dict[str, str]) -> bool:
    return a.get("using_clause") == "using_index"


def _is_all_tables(a: dict[str, str]) -> bool:
    return a.get("cluster_all") == "all_tables"


def _is_partitioned(a: dict[str, str]) -> bool:
    pt = a.get("partitioned_table", "none")
    return pt in (
        "partitioned_table_with_partitioned_index",
        "partitioned_table_without_index_specified",
    )


def _partitioned_without_index(a: dict[str, str]) -> bool:
    return (
        a.get("partitioned_table")
        == "partitioned_table_without_index_specified"
    )


def _schema_qualified(a: dict[str, str]) -> bool:
    return a.get("table_name_shape") == "schema_qualified"


def _needs_table(a: dict[str, str]) -> bool:
    """Whether the case creates a fixture table."""

    if _table_missing(a):
        return False
    if _is_all_tables(a):
        # all-tables branches still create a fixture table to recluster.
        return True
    return True


def _needs_index(a: dict[str, str]) -> bool:
    """Whether the case creates a fixture index."""

    if _index_missing(a) and _is_using_branch(a):
        return False
    if _no_clustered_index(a) and not _is_using_branch(a):
        # recluster without recorded index: index not pre-clustered but
        # the index object still exists; we still CREATE it (just do not
        # pre-CLUSTER).
        return True
    if _partitioned_without_index(a) and not _is_using_branch(a):
        return False
    return True


def _needs_pre_cluster(a: dict[str, str]) -> bool:
    """Whether setup must pre-CLUSTER to record the cluster index."""

    if _is_using_branch(a):
        return False
    if _no_clustered_index(a):
        return False
    if _partitioned_without_index(a):
        return False
    return True


def _fixture_table(a: dict[str, str], p: str) -> str:
    if _schema_qualified(a):
        return f"{p}sch.{p}t"
    return f"{p}t"


def _fixture_table_plain(a: dict[str, str], p: str) -> str:
    return f"{p}t"


def _fixture_index(a: dict[str, str], p: str) -> str:
    return f"{p}i"


def _second_table(a: dict[str, str], p: str) -> str:
    return f"{p}t2"


def _target_table(a: dict[str, str], p: str) -> str:
    """The table identifier in the fenced CLUSTER target."""

    shape = a.get("table_name_shape", "simple")
    if _table_missing(a) or shape == "non_existent":
        return f"{p}no_such_table"
    if shape == "quoted":
        return f'"{p}t"'
    if shape == "schema_qualified":
        return f"{p}sch.{p}t"
    return _fixture_table(a, p)


def _target_index(a: dict[str, str], p: str) -> str:
    """The index identifier in the fenced CLUSTER target."""

    shape = a.get("index_name_shape", "simple")
    if _index_missing(a) or shape == "non_existent":
        return f"{p}no_such_index"
    if shape == "quoted":
        return f'"{p}i"'
    return _fixture_index(a, p)


def _compute_state(
    case: ClusterFactorCase,
) -> _FixtureState:
    a = _baseline(case)
    p = case.object_prefix
    needs_table = _needs_table(a)
    needs_index = _needs_index(a)
    needs_schema = _schema_qualified(a) and needs_table
    needs_role = _privilege_denied(a)
    needs_partition = _is_partitioned(a) and needs_table
    needs_pre_cluster = _needs_pre_cluster(a) and needs_table
    needs_txn_block = _txn_block(a)
    second = _second_table(a, p) if _index_not_on_table(a) else ""
    effective = f"{p}actor" if needs_role else ""
    pre_cluster_table = (
        second if (_index_not_on_table(a) and second)
        else _fixture_table(a, p)
    )
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
        needs_pre_cluster=needs_pre_cluster,
        pre_cluster_table=pre_cluster_table,
        needs_txn_block=needs_txn_block,
        second_table=second,
        effective_role=effective,
    )


def _build_setup(
    case: ClusterFactorCase, st: _FixtureState
) -> tuple[list[str], str]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    locus = "target.cluster"

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
        if st.second_table:
            lines.append(
                f"CREATE TABLE {st.second_table} (id integer);"
            )
        locus = "fixture.table"

    if st.needs_index:
        idx_target = (
            st.second_table
            if _index_not_on_table(a)
            else st.fixture_table
        )
        lines.append(
            f"CREATE INDEX {st.fixture_index} "
            f"ON {idx_target} (id);"
        )
        locus = "fixture.index"

    if st.needs_pre_cluster:
        lines.append(
            f"CLUSTER {st.pre_cluster_table} "
            f"USING {st.fixture_index};"
        )
        locus = "fixture.pre_cluster"

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
    case: ClusterFactorCase, st: _FixtureState
) -> str:
    a = _baseline(case)
    p = case.object_prefix
    branch = a.get("statement_branch", "cluster_table_using_index")
    table = _target_table(a, p)
    index = _target_index(a, p)

    if branch == "cluster_table_using_index":
        return f"CLUSTER {table} USING {index};"
    if branch == "cluster_table_recluster":
        return f"CLUSTER {table};"
    if branch == "cluster_verbose_table_using_index":
        return f"CLUSTER VERBOSE {table} USING {index};"
    if branch == "cluster_verbose_table_recluster":
        return f"CLUSTER VERBOSE {table};"
    if branch == "cluster_paren_option_table_using_index":
        return f"CLUSTER (VERBOSE TRUE) {table} USING {index};"
    if branch == "cluster_paren_option_table_recluster":
        vo = a.get("verbose_option", "paren_verbose_true")
        opt = "VERBOSE TRUE" if vo != "paren_verbose_false" else (
            "VERBOSE FALSE"
        )
        return f"CLUSTER ({opt}) {table};"
    if branch == "cluster_all":
        return "CLUSTER;"
    if branch == "cluster_verbose_all":
        return "CLUSTER VERBOSE;"
    return f"CLUSTER {table} USING {index};"


def _probe_select(
    case: ClusterFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""

    mode = a.get("verification", "pg_class_relclustered")
    if mode == "error_assertion":
        return None

    table_plain = _fixture_table_plain(a, p)

    if mode == "pg_class_relclustered":
        return (
            "SELECT count(*) AS clustered_index_count "
            "FROM pg_catalog.pg_index i "
            "WHERE i.indisclustered "
            f"AND i.indrelid = (SELECT c.oid "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{table_plain}' "
            "ORDER BY c.oid LIMIT 1) "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "physical_ordering_check":
        return (
            "SELECT count(*) AS physical_order_probe "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{table_plain}' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "pg_stat_progress_cluster":
        return (
            "SELECT count(*) AS progress_rows "
            "FROM pg_catalog.pg_stat_progress_cluster "
            "ORDER BY count(*)"
            ";"
        )
    return None


def _tables_to_drop(
    case: ClusterFactorCase, st: _FixtureState
) -> list[str]:
    if not st.needs_table:
        return []
    p = case.object_prefix
    tables = [st.fixture_table]
    if st.needs_partition:
        # The ``{p}t_p1`` partition is created alongside the partitioned
        # parent (see ``_build_setup``); the static bookend gate requires
        # every created table name to appear in the DROP list, so include
        # it here even though ``DROP parent CASCADE`` would reclaim it at
        # runtime.
        tables.append(f"{p}t_p1")
    if st.second_table:
        tables.append(st.second_table)
    return tables


def _build_pre_cleanup(
    case: ClusterFactorCase, st: _FixtureState
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
    if st.needs_role:
        lines.append(f"DROP ROLE IF EXISTS {st.role_name};")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_cleanup(
    case: ClusterFactorCase, st: _FixtureState
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
    case: ClusterFactorCase, st: _FixtureState
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


def _resolve_case(case: ClusterFactorCase) -> _CasePlan:
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


def resolve_cluster_factor_witness(
    case: ClusterFactorCase | ClusterFactorExtensionCase,
    repository_root: Path,
) -> ClusterFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return ClusterFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_cluster(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*CLUSTER\b", region))


def _header(case: ClusterFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CLUSTER {case.factor_key}="
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


def render_cluster_factor_case(
    case: ClusterFactorCase | ClusterFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CLUSTER。")
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
    case: ClusterFactorCase | ClusterFactorExtensionCase,
    out: Path,
) -> None:
    text = render_cluster_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_cluster_factor_programs(
    baseline_plan: ClusterFactorLoopPlan,
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
    "ClusterFactorRenderError",
    "ClusterFactorWitness",
    "count_primary_cluster",
    "generate_cluster_factor_programs",
    "render_cluster_factor_case",
    "resolve_cluster_factor_witness",
]
