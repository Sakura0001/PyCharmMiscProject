"""Render complete PostgreSQL 18.4 REFRESH MATERIALIZED VIEW factor programs.

Every planned obligation becomes one self-contained, deterministic SQL file
assembled from a single :func:`_resolve_case` plan so the byte-level witness
validator (which re-renders and compares) can never diverge from the bytes
actually written.

REFRESH replaces the contents of a materialized view.  Success-path cases
CREATE a fixture source table and a fixture materialized view (and an
optional unique index) as setup, so the bookend contract applies: the FIRST
and LAST executable ``;``-statements are each ``DROP TABLE IF EXISTS`` when
the case creates a source table.  Cases that target a missing matview create
no fixture table, so the bookend is satisfied vacuously.

The catalog oracle checks ``pg_catalog.pg_class`` with ``relkind='m'``
(materialized view).  All catalog oracles schema-qualify ``pg_catalog.*``
(exempt from the file-prefix style gate) and carry a top-level ``ORDER BY``
so the catalog-observability gate passes.  Quoted / schema-qualified matview
identifiers appear ONLY in the fenced REFRESH target; the fixture CREATE
TABLE / CREATE MATERIALIZED VIEW and bookend DROP always use the plain
prefix-derived unqualified name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .refresh_materialized_view_factor_extension import (
    RefreshMaterializedViewFactorExtensionCase,
    _present_failure_pair,
)
from .refresh_materialized_view_factor_loop import (
    RefreshMaterializedViewFactorCase,
    RefreshMaterializedViewFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/materialized_view/"
    "refresh_materialized_view.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/materialized_view/"
    "refresh_materialized_view.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class RefreshMaterializedViewFactorRenderError(ValueError):
    """Raised when a REFRESH case cannot be rendered."""


@dataclass(frozen=True)
class RefreshMaterializedViewFactorWitness:
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
    needs_source_table: bool
    fixture_source: str
    needs_matview: bool
    fixture_matview: str
    needs_unique_index: bool
    fixture_index: str
    needs_role: bool
    role_name: str
    needs_grant_maintain: bool
    needs_pre_drop_source: bool
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
    ext: RefreshMaterializedViewFactorExtensionCase,
) -> RefreshMaterializedViewFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "statement_branch"
        factor_value = assignment.get("statement_branch", "branch_1")
    return RefreshMaterializedViewFactorCase(
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
    case: RefreshMaterializedViewFactorCase
    | RefreshMaterializedViewFactorExtensionCase,
) -> RefreshMaterializedViewFactorCase:
    if isinstance(
        case, RefreshMaterializedViewFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: RefreshMaterializedViewFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _target_missing(a: dict[str, str]) -> bool:
    return a.get("target_object_state") == "missing"


def _missing_dependency(a: dict[str, str]) -> bool:
    return a.get("dependency_state") == "missing_dependency"


def _privilege_denied(a: dict[str, str]) -> bool:
    return a.get("privilege_context") == "insufficient_privilege"


def _needs_role(a: dict[str, str]) -> bool:
    return a.get("privilege_context") in {
        "insufficient_privilege",
        "granted_role",
        "maintain_privilege",
    }


def _needs_grant_maintain(a: dict[str, str]) -> bool:
    return a.get("privilege_context") in {
        "granted_role",
        "maintain_privilege",
    }


def _is_concurrent(a: dict[str, str]) -> bool:
    return a.get("concurrently_clause") == "present"


def _has_unique_index(a: dict[str, str]) -> bool:
    return a.get("unique_index_state") == "has_unique_index"


def _is_unpopulated(a: dict[str, str]) -> bool:
    return a.get("target_object_state") == "exists_unpopulated"


def _needs_source_table(a: dict[str, str]) -> bool:
    return not _target_missing(a)


def _fixture_source(p: str) -> str:
    return f"{p}src"


def _fixture_matview(p: str) -> str:
    return f"{p}mv"


def _fixture_index(p: str) -> str:
    return f"{p}uidx"


def _target_mv(a: dict[str, str], p: str) -> str:
    """The matview identifier in the fenced REFRESH target (shaped)."""

    shape = a.get("name_shape", "plain_identifier")
    if _target_missing(a):
        return f"{p}no_such_mv"
    if shape == "quoted_identifier":
        return f'"{_fixture_matview(p)}"'
    if shape == "schema_qualified":
        return f"{p}sch.{_fixture_matview(p)}"
    return _fixture_matview(p)


def _data_clause_sql(a: dict[str, str]) -> str:
    return "WITH NO DATA" if a.get(
        "data_clause", "with_data"
    ) == "with_no_data" else "WITH DATA"


def _compute_state(
    case: RefreshMaterializedViewFactorCase,
) -> _FixtureState:
    a = _baseline(case)
    p = case.object_prefix
    needs_source = _needs_source_table(a)
    needs_mv = not _target_missing(a)
    needs_idx = _has_unique_index(a) and needs_mv
    needs_role = _needs_role(a)
    needs_grant = _needs_grant_maintain(a) and needs_mv
    needs_drop_src = _missing_dependency(a) and needs_mv
    effective = f"{p}actor" if needs_role else ""
    return _FixtureState(
        needs_source_table=needs_source,
        fixture_source=_fixture_source(p),
        needs_matview=needs_mv,
        fixture_matview=_fixture_matview(p),
        needs_unique_index=needs_idx,
        fixture_index=_fixture_index(p),
        needs_role=needs_role,
        role_name=f"{p}actor" if needs_role else "",
        needs_grant_maintain=needs_grant,
        needs_pre_drop_source=needs_drop_src,
        effective_role=effective,
    )


def _build_setup(
    case: RefreshMaterializedViewFactorCase, st: _FixtureState
) -> tuple[list[str], str]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    locus = "target.refresh_materialized_view"

    if st.needs_role:
        lines.append(
            f"CREATE ROLE {st.role_name} LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"

    if st.needs_source_table:
        lines.append(
            f"CREATE TABLE {st.fixture_source} (id integer);"
        )
        lines.append(
            f"INSERT INTO {st.fixture_source} VALUES (1), (2), (3);"
        )
        locus = "fixture.source_table"

    if st.needs_matview:
        if _is_unpopulated(a):
            lines.append(
                f"CREATE MATERIALIZED VIEW {st.fixture_matview} "
                f"AS SELECT id FROM {st.fixture_source} "
                f"WITH NO DATA;"
            )
        else:
            lines.append(
                f"CREATE MATERIALIZED VIEW {st.fixture_matview} "
                f"AS SELECT id FROM {st.fixture_source};"
            )
        locus = "fixture.materialized_view"

    if st.needs_unique_index:
        lines.append(
            f"CREATE UNIQUE INDEX {st.fixture_index} "
            f"ON {st.fixture_matview} (id);"
        )
        locus = "fixture.unique_index"

    if st.needs_grant_maintain:
        lines.append(
            f"GRANT MAINTAIN ON {st.fixture_matview} "
            f"TO {st.role_name};"
        )
        locus = "fixture.privilege_state"

    if st.needs_pre_drop_source:
        lines.append(
            f"DROP TABLE {st.fixture_source} CASCADE;"
        )
        locus = "fixture.broken_dependency"

    if st.effective_role:
        lines.append(f"SET ROLE {st.effective_role};")
        locus = "fixture.role_armed"

    if not lines:
        lines.append(
            "SELECT 1 AS target_materialized_view_intentionally_absent;"
        )
        locus = "fixture.materialized_view_missing"

    return lines, locus


def _build_target(
    case: RefreshMaterializedViewFactorCase, st: _FixtureState
) -> str:
    a = _baseline(case)
    p = case.object_prefix
    target = _target_mv(a, p)
    data_clause = _data_clause_sql(a)
    if _is_concurrent(a):
        return (
            f"REFRESH MATERIALIZED VIEW CONCURRENTLY {target} "
            f"{data_clause};"
        )
    return f"REFRESH MATERIALIZED VIEW {target} {data_clause};"


def _probe_select(
    case: RefreshMaterializedViewFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None

    mv_plain = _fixture_matview(p)

    if mode == "catalog_query":
        return (
            "SELECT count(*) AS matview_relation_count "
            "FROM pg_catalog.pg_class c "
            f"WHERE c.relname = '{mv_plain}' "
            "AND c.relkind = 'm' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "effect_query":
        return (
            "SELECT count(*) AS refreshed_row_count "
            f"FROM {mv_plain} "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "returned_rows":
        return (
            "SELECT count(*) AS returned_row_count "
            f"FROM {mv_plain} "
            "ORDER BY count(*)"
            ";"
        )
    return None


def _tables_to_drop(
    case: RefreshMaterializedViewFactorCase, st: _FixtureState
) -> list[str]:
    if not st.needs_source_table:
        return []
    return [st.fixture_source]


def _build_pre_cleanup(
    case: RefreshMaterializedViewFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    lines: list[str] = []
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if st.needs_matview:
        lines.append(
            f"DROP MATERIALIZED VIEW IF EXISTS {st.fixture_matview};"
        )
    if st.needs_role:
        lines.append(f"DROP ROLE IF EXISTS {st.role_name};")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_cleanup(
    case: RefreshMaterializedViewFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    lines: list[str] = []
    if st.effective_role:
        lines.append("RESET ROLE;")
    if st.needs_role:
        lines.append(f"DROP OWNED BY {st.role_name};")
        lines.append(f"DROP ROLE IF EXISTS {st.role_name};")
    if st.needs_matview:
        lines.append(
            f"DROP MATERIALIZED VIEW IF EXISTS {st.fixture_matview};"
        )
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_assert(
    case: RefreshMaterializedViewFactorCase, st: _FixtureState
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


def _resolve_case(case: RefreshMaterializedViewFactorCase) -> _CasePlan:
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


def resolve_refresh_materialized_view_factor_witness(
    case: RefreshMaterializedViewFactorCase
    | RefreshMaterializedViewFactorExtensionCase,
    repository_root: Path,
) -> RefreshMaterializedViewFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return RefreshMaterializedViewFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_refresh_materialized_view(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*REFRESH\s+MATERIALIZED\s+VIEW\b", region
        )
    )


def _header(case: RefreshMaterializedViewFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : REFRESH MATERIALIZED VIEW "
        f"{case.factor_key}={case.factor_value}",
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


def render_refresh_materialized_view_factor_case(
    case: RefreshMaterializedViewFactorCase
    | RefreshMaterializedViewFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 REFRESH MATERIALIZED VIEW。")
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
    case: RefreshMaterializedViewFactorCase
    | RefreshMaterializedViewFactorExtensionCase,
    out: Path,
) -> None:
    text = render_refresh_materialized_view_factor_case(
        case, Path(".")
    )
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_refresh_materialized_view_factor_programs(
    baseline_plan: RefreshMaterializedViewFactorLoopPlan,
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
    "RefreshMaterializedViewFactorRenderError",
    "RefreshMaterializedViewFactorWitness",
    "count_primary_refresh_materialized_view",
    "generate_refresh_materialized_view_factor_programs",
    "render_refresh_materialized_view_factor_case",
    "resolve_refresh_materialized_view_factor_witness",
]
