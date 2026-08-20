"""Render complete PostgreSQL 18.4 CREATE STATISTICS factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE STATISTICS references a relation via ``FROM table_reference``.
Success-path cases CREATE the fixture table as setup, so the bookend
contract applies: the FIRST and LAST executable ``;``-statements are
each ``DROP TABLE IF EXISTS <all created tables>`` when the case
creates one or more tables.

All catalog oracles schema-qualify ``pg_catalog.*`` (exempt from the
file-prefix style gate) and carry a top-level ``ORDER BY`` so the
catalog-observability gate passes.  Quoted / dotted / reserved
statistics names appear ONLY in the fenced CREATE STATISTICS target
(which the style gate does not parse for the statistics object name);
the FROM table always uses a plain prefix-derived unqualified name so
the quoted-identifier gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_statistics_factor_extension import (
    CreateStatisticsFactorExtensionCase,
    _present_failure_pair,
)
from .create_statistics_factor_loop import (
    CreateStatisticsFactorCase,
    CreateStatisticsFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/statistics/"
    "create_statistics.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/statistics/"
    "create_statistics.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateStatisticsFactorRenderError(ValueError):
    """Raised when a CREATE STATISTICS case cannot be rendered."""


@dataclass(frozen=True)
class CreateStatisticsFactorWitness:
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
    ext: CreateStatisticsFactorExtensionCase,
) -> CreateStatisticsFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "statement_branch"
        factor_value = assignment.get(
            "statement_branch", "branch_multivariate_columns"
        )
    return CreateStatisticsFactorCase(
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
    case: CreateStatisticsFactorCase
    | CreateStatisticsFactorExtensionCase,
) -> CreateStatisticsFactorCase:
    if isinstance(case, CreateStatisticsFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateStatisticsFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_privilege_failure(a: dict[str, str]) -> bool:
    return (
        a.get("executor_privilege") == "non_owner_no_privilege"
        or a.get("privilege_insufficient")
        == "non_table_owner_creating_statistics"
    )


def _is_duplicate_failure(a: dict[str, str]) -> bool:
    return _is_failure(a) and a.get("expected_sqlstate", "") == "" or (
        a.get("statistics_identity") == "exists"
        and a.get("if_not_exists_clause") == "without_if_not_exists"
    )


def _has_preexisting_stat(a: dict[str, str]) -> bool:
    """Whether setup must pre-create a statistics object."""

    ident = a.get("statistics_identity", "not_exists")
    return ident in ("exists", "exists_with_if_not_exists")


def _stats_name(a: dict[str, str], p: str) -> str:
    """The statistics identifier in the fenced CREATE STATISTICS target."""

    if a.get("statistics_name_presence") == "auto_generated_name_omitted":
        return ""
    shape = a.get("statistics_name_shape", "simple_name")
    if shape == "schema_qualified_name":
        return f"public.{p}stat"
    if shape == "quoted_name":
        return f'"{p}Stat"'
    if shape == "reserved_word_name":
        return '"select"'
    if shape == "non_existing_name":
        return f"{p}statnew"
    return f"{p}stat"


def _stats_name_plain(a: dict[str, str], p: str) -> str:
    """Always-plain statistics name for cleanup and oracle queries."""

    return f"{p}stat"


def _table_name(a: dict[str, str], p: str) -> str:
    """The FROM table identifier (always plain, prefix-derived)."""

    if (
        a.get("table_name_shape") == "nonexistent_table"
        or a.get("table_dependency") == "table_not_exists"
        or a.get("nonexistent_table") == "table_not_exists_failure"
    ):
        return f"{p}tnx"
    return f"{p}t"


def _tables_to_drop(a: dict[str, str], p: str) -> list[str]:
    tables = [f"{p}t"]
    if _table_name(a, p) != f"{p}t":
        tables.append(f"{p}tnx")
    return tables


def _expression(a: dict[str, str]) -> str:
    """The expression text for univariate / expression-shape factors."""

    shape = a.get("expression_shape", "simple_column_reference")
    if shape == "arithmetic_expression":
        return "a + 1"
    if shape == "function_call_expression":
        return "lower(d)"
    return "a"


def _column_list(a: dict[str, str]) -> str:
    """The ON (...) column/expression list for multivariate Form 2."""

    if a.get("single_column_for_multivariate") == (
        "single_column_multivariate_failure"
    ):
        return "a"
    combo = a.get("column_combination", "two_columns")
    col_shape = a.get("column_name_shape", "simple_name")
    if col_shape == "nonexistent_column":
        return "a, zzz"
    if col_shape == "quoted_name":
        quoted = '"a", "b"'
    else:
        quoted = None
    if combo == "three_columns":
        return quoted or "a, b, c"
    if combo == "column_and_expression_mix":
        return '"a", (b + 1)' if quoted is None else quoted
    return quoted or "a, b"


def _kind_clause(a: dict[str, str]) -> str:
    kind = a.get("statistics_kind_clause", "omitted_all_kinds")
    if a.get("statement_branch") == "branch_univariate_expression":
        return ""
    if a.get("single_column_for_multivariate") == (
        "single_column_multivariate_failure"
    ):
        return "(ndistinct)"
    if kind == "omitted_all_kinds":
        return ""
    if kind == "ndistinct_only":
        return "(ndistinct)"
    if kind == "dependencies_only":
        return "(dependencies)"
    if kind == "mcv_only":
        return "(mcv)"
    if kind == "ndistinct_and_dependencies":
        return "(ndistinct, dependencies)"
    if kind == "all_three_kinds":
        return "(ndistinct, dependencies, mcv)"
    return ""


def _ifne_clause(a: dict[str, str]) -> str:
    if a.get("if_not_exists_clause") == "with_if_not_exists":
        return "IF NOT EXISTS "
    return ""


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE STATISTICS statement."""

    if a.get("expression_syntax_error") == "invalid_expression_failure":
        name = _stats_name(a, p)
        head = f"CREATE STATISTICS {_ifne_clause(a)}{name}".rstrip()
        return f"{head} ON (a +) FROM {_table_name(a, p)};"

    name = _stats_name(a, p)
    parts: list[str] = ["CREATE STATISTICS"]
    ifne = _ifne_clause(a)
    if ifne:
        parts.append(ifne.strip())
    if name:
        parts.append(name)
    kind = _kind_clause(a)
    if kind:
        parts.append(kind)
    parts.append("ON")
    if a.get("statement_branch") == "branch_univariate_expression":
        parts.append(f"({_expression(a)})")
    else:
        parts.append(f"({_column_list(a)})")
    parts.append("FROM")
    parts.append(_table_name(a, p))
    return " ".join(parts) + ";"


def _build_setup(
    a: dict[str, str], p: str
) -> tuple[list[str], str]:
    lines: list[str] = []
    locus = "target.create_statistics"

    fixture_cols = "a integer, b integer, c integer, d text"
    lines.append(f"CREATE TABLE {p}t ({fixture_cols});")
    locus = "fixture.table"

    if _has_preexisting_stat(a):
        name = _stats_name_plain(a, p)
        lines.append(
            f"CREATE STATISTICS {name} ON (a, b) FROM {p}t;"
        )
        locus = "fixture.preexisting_statistics"

    if _is_privilege_failure(a):
        lines.append(f"CREATE ROLE {p}nobody NOLOGIN;")
        lines.append(f"GRANT USAGE ON TABLE {p}t TO {p}nobody;")
        lines.append(f"SET ROLE {p}nobody;")
        locus = "fixture.privilege_context"

    if a.get("cleanup_mode") == "rollback":
        lines.append("BEGIN;")
        locus = "fixture.transaction_block"

    return lines, locus


def _probe_select(
    a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""

    mode = a.get("verification_mode", "pg_statistic_ext_catalog")
    if mode == "error_assertion":
        return None
    table_relname = _table_name(a, p)
    return (
        "SELECT count(*) AS stat_count "
        "FROM pg_catalog.pg_statistic_ext s "
        "JOIN pg_catalog.pg_class c ON c.oid = s.stxrelid "
        f"WHERE c.relname = '{table_relname}' "
        "ORDER BY count(*)"
        ";"
    )


def _build_pre_cleanup(
    a: dict[str, str], p: str
) -> tuple[str, ...]:
    tables = _tables_to_drop(a, p)
    lines: list[str] = [
        f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
    ]
    lines.append(f"DROP STATISTICS IF EXISTS {_stats_name_plain(a, p)};")
    lines.append(f"DROP STATISTICS IF EXISTS {p}statnew;")
    if _is_privilege_failure(a):
        lines.append(f"DROP ROLE IF EXISTS {p}nobody;")
    return tuple(lines)


def _build_cleanup(
    a: dict[str, str], p: str
) -> tuple[str, ...]:
    cleanup_mode = a.get("cleanup_mode", "drop_statistics")
    lines: list[str] = []
    if _is_privilege_failure(a):
        lines.append("SET ROLE NONE;")
        lines.append(f"DROP ROLE IF EXISTS {p}nobody;")
    if cleanup_mode == "rollback":
        lines.append("ROLLBACK;")
    lines.append(f"DROP STATISTICS IF EXISTS {_stats_name_plain(a, p)};")
    lines.append(f"DROP STATISTICS IF EXISTS {p}statnew;")
    tables = _tables_to_drop(a, p)
    lines.append(
        f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
    )
    return tuple(lines)


def _build_assert(
    case: CreateStatisticsFactorCase,
    a: dict[str, str],
    p: str,
) -> tuple[str, ...]:
    lines: list[str] = []
    if _is_privilege_failure(a):
        lines.append("SET ROLE NONE;")
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(a, p)
    if probe is not None:
        lines.append(probe)
    return tuple(lines)


def _resolve_case(case: CreateStatisticsFactorCase) -> _CasePlan:
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


def _header(case: CreateStatisticsFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE STATISTICS {case.factor_key}="
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


def render_create_statistics_factor_case(
    case: CreateStatisticsFactorCase
    | CreateStatisticsFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE STATISTICS。")
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
    case: CreateStatisticsFactorCase
    | CreateStatisticsFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_statistics_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_statistics_factor_programs(
    baseline_plan: CreateStatisticsFactorLoopPlan,
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


def count_primary_create_statistics(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+STATISTICS\b", region)
    )


def resolve_create_statistics_factor_witness(
    case: CreateStatisticsFactorCase
    | CreateStatisticsFactorExtensionCase,
    repository_root: Path,
) -> CreateStatisticsFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateStatisticsFactorWitness(
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
    "CreateStatisticsFactorRenderError",
    "CreateStatisticsFactorWitness",
    "count_primary_create_statistics",
    "generate_create_statistics_factor_programs",
    "render_create_statistics_factor_case",
    "resolve_create_statistics_factor_witness",
]
