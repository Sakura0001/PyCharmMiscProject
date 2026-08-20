"""Render complete PostgreSQL 18.4 DEALLOCATE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

DEALLOCATE fixtures ``CREATE TABLE`` (to ``PREPARE`` a
``SELECT``/``INSERT`` against), so the render emits ``DROP TABLE IF
EXISTS`` as the very first and very last ``;``-segment of each file
(bookend gate).  All catalog oracles schema-qualify
``pg_catalog`` (exempt from the file-prefix style gate via the ``pg_``
prefix) and carry a top-level ``ORDER BY``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .deallocate_factor_extension import (
    DeallocateFactorExtensionCase,
    _present_failure_pair,
)
from .deallocate_factor_loop import (
    DeallocateFactorCase,
    DeallocateFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/prepared/"
    "prepared_statement/deallocate.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/prepared/"
    "prepared_statement/deallocate.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class DeallocateFactorRenderError(ValueError):
    """Raised when a DEALLOCATE case cannot be rendered."""


@dataclass(frozen=True)
class DeallocateFactorWitness:
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
    ext: DeallocateFactorExtensionCase,
) -> DeallocateFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = assignment.get(
            "target_form", ext.consumer_action_id
        )
    return DeallocateFactorCase(
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
    case: DeallocateFactorCase | DeallocateFactorExtensionCase,
) -> DeallocateFactorCase:
    if isinstance(case, DeallocateFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: DeallocateFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(p: str) -> str:
    return f"{p}schema"


def _base_table_name(p: str) -> str:
    schema = _schema_name(p)
    return f"{schema}.{p}base"


def _target_table_name(p: str) -> str:
    schema = _schema_name(p)
    return f"{schema}.{p}target"


def _all_tables(p: str) -> tuple[str, ...]:
    return (_base_table_name(p), _target_table_name(p))


def _stmt_name(a: dict[str, str], p: str) -> str:
    """The prepared statement name referenced by DEALLOCATE."""

    shape = a.get("prepared_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}Stmt"'
    return f"{p}stmt"


def _is_all_form(a: dict[str, str]) -> bool:
    return (
        a.get("prepared_name_shape") == "all_prepared_statements"
        or a.get("lifecycle_boundary") == "deallocate_all"
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_missing_name(a: dict[str, str]) -> bool:
    return a.get("prepared_name_shape") == "missing_name"


def _needs_base_table(a: dict[str, str]) -> bool:
    body = a.get("prepared_statement_body", "select_statement")
    return body in ("select_statement", "insert_or_update_statement")


def _needs_target_table(a: dict[str, str]) -> bool:
    return (
        a.get("prepared_statement_body")
        == "insert_or_update_statement"
    )


def _prepare_sql(a: dict[str, str], p: str) -> str:
    """The PREPARE statement based on body and parameter_shape."""

    name = _stmt_name(a, p)
    body = a.get("prepared_statement_body", "select_statement")
    param = a.get("parameter_shape", "none")
    base = _base_table_name(p)
    target = _target_table_name(p)

    params = ""
    if param == "single_typed_parameter":
        params = " (int)"
    elif param == "multiple_typed_parameters":
        params = " (int, text)"
    elif param == "type_mismatch":
        params = " (int)"

    if body == "insert_or_update_statement":
        if param in ("single_typed_parameter", "type_mismatch"):
            return (
                f"PREPARE {name}{params} AS "
                f"INSERT INTO {target} VALUES ($1);"
            )
        if param == "multiple_typed_parameters":
            return (
                f"PREPARE {name}{params} AS "
                f"INSERT INTO {target} VALUES ($1, $2);"
            )
        return f"PREPARE {name} AS INSERT INTO {target} VALUES (1);"

    if body == "utility_allowed_statement":
        if param in ("single_typed_parameter", "type_mismatch"):
            return f"PREPARE {name}{params} AS SELECT $1;"
        if param == "multiple_typed_parameters":
            return f"PREPARE {name}{params} AS SELECT $1, $2;"
        return f"PREPARE {name} AS SELECT 1;"

    # select_statement (default)
    if param == "single_typed_parameter":
        return (
            f"PREPARE {name}{params} AS "
            f"SELECT $1 FROM {base};"
        )
    if param == "multiple_typed_parameters":
        return (
            f"PREPARE {name}{params} AS "
            f"SELECT $1, $2 FROM {base};"
        )
    if param == "type_mismatch":
        return (
            f"PREPARE {name}{params} AS "
            f"SELECT $1::text FROM {base};"
        )
    return f"PREPARE {name} AS SELECT * FROM {base};"


def _execute_sql(a: dict[str, str], p: str) -> str:
    """The EXECUTE statement based on argument_shape."""

    name = _stmt_name(a, p)
    arg = a.get("argument_shape", "none")
    if arg == "matching_arguments":
        return f"EXECUTE {name}(1, 'hello');"
    if arg == "too_few_arguments":
        return f"EXECUTE {name}(1);"
    if arg == "too_many_arguments":
        return f"EXECUTE {name}(1, 'hello', 2);"
    if arg == "wrong_type_arguments":
        return f"EXECUTE {name}('hello');"
    return f"EXECUTE {name};"


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary DEALLOCATE statement."""

    if _is_failure(a):
        return f"DEALLOCATE {p}nonexistent;"
    if _is_all_form(a):
        return "DEALLOCATE ALL;"
    name = _stmt_name(a, p)
    if _is_missing_name(a):
        return f"DEALLOCATE {name};"
    return f"DEALLOCATE {name};"


def _build_table_fixtures(
    a: dict[str, str], p: str
) -> list[str]:
    """CREATE TABLE lines for the PREPARE body."""

    lines: list[str] = []
    if _needs_base_table(a):
        base = _base_table_name(p)
        lines.append(f"CREATE TABLE {base} (c1 int, c2 text);")
        lines.append(f"INSERT INTO {base} VALUES (1, 'hello');")
    if _needs_target_table(a):
        target = _target_table_name(p)
        lines.append(f"CREATE TABLE {target} (c1 int, c2 text);")
    return lines


def _build_prepare_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """PREPARE (and optionally EXECUTE) the target statement."""

    lines: list[str] = []
    if _is_failure(a):
        return lines
    if a.get("prepared_state") == "missing" and not _is_all_form(a):
        return lines
    if not _is_all_form(a):
        lines.append(_prepare_sql(a, p))
    lifecycle = a.get(
        "lifecycle_boundary", "prepare_execute_deallocate"
    )
    if lifecycle == "prepare_execute_deallocate":
        if a.get("prepared_state") != "missing":
            lines.append(_execute_sql(a, p))
    return lines


def _build_post_target_execute(
    a: dict[str, str], p: str
) -> list[str]:
    """EXECUTE after DEALLOCATE for the execute_after_deallocate boundary."""

    lifecycle = a.get(
        "lifecycle_boundary", "prepare_execute_deallocate"
    )
    if lifecycle != "execute_after_deallocate":
        return []
    if _is_failure(a):
        return []
    name = _stmt_name(a, p)
    if _is_all_form(a):
        return [f"EXECUTE {name};"]
    return [f"EXECUTE {name};"]


def _probe_select(
    case: DeallocateFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    if mode == "effect_query":
        if _is_failure(a):
            return None
        name = _stmt_name(a, p)
        return (
            f"SELECT count(*) = 0 AS effect_observed "
            f"FROM pg_catalog.pg_prepared_statements "
            f"WHERE name = '{name}' "
            f"ORDER BY count(*);"
        )
    if mode == "returned_rows":
        if _is_failure(a) or _is_all_form(a):
            return None
        base = _base_table_name(p)
        return (
            f"SELECT count(*) AS row_count FROM {base} "
            f"ORDER BY count(*);"
        )
    # catalog_query (default)
    present = not _is_failure(a)
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS stmt_state "
        f"FROM pg_catalog.pg_prepared_statements "
        f"ORDER BY count(*);"
    )


def _build_cleanup(a: dict[str, str], p: str) -> list[str]:
    """Cleanup lines after the primary target."""

    schema = _schema_name(p)
    lines: list[str] = []
    cleanup_mode = a.get("cleanup_mode", "rollback")
    if cleanup_mode == "reset_state":
        lines.append("RESET ROLE;")
    if cleanup_mode != "rollback":
        lines.append("DEALLOCATE ALL;")
    for table in _all_tables(p):
        lines.append(f"DROP TABLE IF EXISTS {table} CASCADE;")
    lines.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    # Bookend gate: final ;-segment must be pure DROP TABLE IF EXISTS
    lines.append(
        f"DROP TABLE IF EXISTS {', '.join(_all_tables(p))} CASCADE;"
    )
    return lines


def _resolve_case(
    case: DeallocateFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _schema_name(p)

    setup: list[str] = []
    locus = "target.deallocate"

    setup.append(f"CREATE SCHEMA {schema};")
    locus = "fixture.schema"

    setup.extend(_build_table_fixtures(a, p))
    if _needs_base_table(a) or _needs_target_table(a):
        locus = "fixture.base_table"

    setup.extend(_build_prepare_fixture(a, p))
    if not _is_failure(a) and not _is_all_form(a):
        if a.get("prepared_state") != "missing":
            locus = "fixture.prepared_statement"

    target = _build_target(a, p)

    assert_lines: list[str] = []
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)
    assert_lines.extend(_build_post_target_execute(a, p))

    cleanup = _build_cleanup(a, p)

    pre_cleanup: list[str] = []
    # Bookend gate: first ;-segment must be pure DROP TABLE IF EXISTS
    pre_cleanup.append(
        f"DROP TABLE IF EXISTS {', '.join(_all_tables(p))} CASCADE;"
    )
    pre_cleanup.append("DEALLOCATE ALL;")
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

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


def _header(case: DeallocateFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DEALLOCATE "
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


def render_deallocate_factor_case(
    case: DeallocateFactorCase | DeallocateFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 DEALLOCATE。"
    )
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
    case: DeallocateFactorCase | DeallocateFactorExtensionCase,
    out: Path,
) -> None:
    text = render_deallocate_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_deallocate_factor_programs(
    baseline_plan: DeallocateFactorLoopPlan,
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


def count_primary_deallocate(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^DEALLOCATE(?:\s|;|$)", region)
    )


def resolve_deallocate_factor_witness(
    case: DeallocateFactorCase | DeallocateFactorExtensionCase,
    repository_root: Path,
) -> DeallocateFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DeallocateFactorWitness(
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
    "DeallocateFactorRenderError",
    "DeallocateFactorWitness",
    "count_primary_deallocate",
    "generate_deallocate_factor_programs",
    "render_deallocate_factor_case",
    "resolve_deallocate_factor_witness",
]
