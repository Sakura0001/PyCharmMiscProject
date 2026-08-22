"""Render complete PostgreSQL 18.4 ALTER STATISTICS factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER STATISTICS targets a ``pg_catalog.pg_statistic_ext`` row, not a
``pg_class`` relation.  All catalog oracles therefore schema-qualify
``pg_catalog.pg_statistic_ext`` (exempt from the file-prefix style gate).
The statement requires an underlying TABLE fixture (every extended
statistics object depends on a table), so every case CREATEs a TABLE
and the bookend gate wraps it: the FIRST and LAST executable ``;``-stmts
are ``DROP TABLE IF EXISTS <created tables>``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .alter_statistics_factor_extension import (
    AlterStatisticsFactorExtensionCase,
    _present_failure_pair,
)
from .alter_statistics_factor_loop import (
    AlterStatisticsFactorCase,
    AlterStatisticsFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/statistics/"
    "alter_statistics.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/statistics/"
    "alter_statistics.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_DB_PLACEHOLDER = "pgcf"


class AlterStatisticsFactorRenderError(ValueError):
    """Raised when an ALTER STATISTICS case cannot be rendered."""


@dataclass(frozen=True)
class AlterStatisticsFactorWitness:
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
    ext: AlterStatisticsFactorExtensionCase,
) -> AlterStatisticsFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "set_statistics")
    return AlterStatisticsFactorCase(
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
    case: AlterStatisticsFactorCase | AlterStatisticsFactorExtensionCase,
) -> AlterStatisticsFactorCase:
    if isinstance(case, AlterStatisticsFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterStatisticsFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_set_statistics(a: dict[str, str]) -> bool:
    return a.get("target_action") == "set_statistics"


def _is_rename(a: dict[str, str]) -> bool:
    return a.get("target_action") == "rename"


def _is_owner_to(a: dict[str, str]) -> bool:
    return a.get("target_action") == "owner_to"


def _is_set_schema(a: dict[str, str]) -> bool:
    return a.get("target_action") == "set_schema"


def _stats_missing(a: dict[str, str]) -> bool:
    return a.get("statistics_state") == "non_existent"


def _stats_name(a: dict[str, str], p: str) -> str:
    """The statistics object identifier used inside ALTER STATISTICS."""

    shape = a.get("statistics_name_shape", "simple_name")
    if shape == "schema_qualified_name":
        return f"{p}stxsch.{p}stx"
    if shape == "quoted_name":
        return f'"{p}Mix Stx"'
    if shape == "non_existent_name":
        return f"{p}nostx"
    return f"{p}stx"


def _stats_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("statistics_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}Mix Stx"
    if shape == "non_existent_name":
        return f"{p}nostx"
    return f"{p}stx"


def _new_name(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}New Mix"'
    if shape == "existing_name_conflict":
        return f"{p}existstx"
    return f"{p}newstx"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}New Mix"
    if shape == "existing_name_conflict":
        return f"{p}existstx"
    return f"{p}newstx"


def _new_schema(a: dict[str, str], p: str) -> str:
    if a.get("new_schema_shape") == "nonexistent_schema":
        return f"{p}nosch"
    return f"{p}newsch"


def _owner_target(a: dict[str, str], p: str) -> str:
    shape = a.get("owner_to_shape", "explicit_role_name")
    if shape == "current_role_keyword":
        return "CURRENT_ROLE"
    if shape == "current_user_keyword":
        return "CURRENT_USER"
    if shape == "session_user_keyword":
        return "SESSION_USER"
    if a.get("new_owner_shape") == "nonexistent_role":
        return f"{p}nosuchrole"
    return f"{p}newowner"


def _target_value(a: dict[str, str]) -> str:
    val = a.get("statistics_target_value", "zero")
    if val == "positive_integer":
        return "1"
    if val == "maximum_value_10000":
        return "10000"
    if val == "negative_one_default":
        return "-1"
    if val == "default_keyword":
        return "DEFAULT"
    if val == "out_of_range":
        return "99999"
    return "0"


def _effective_role(a: dict[str, str], p: str) -> str:
    level = a.get("executor_privilege", "superuser")
    if level == "table_owner":
        return f"{p}tabowner"
    if level == "non_owner_no_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_owner_to(a) and a.get("new_owner_shape") == "existing_role":
        roles.append(f"{p}newowner")
    level = a.get("executor_privilege", "superuser")
    if level == "non_owner_no_privilege":
        roles.append(f"{p}actor")
    if level in ("table_owner", "non_owner_no_privilege"):
        roles.append(f"{p}tabowner")
    return tuple(roles)


def _schema_fixtures(a: dict[str, str], p: str) -> list[str]:
    schemas: list[str] = []
    if a.get("statistics_name_shape") == "schema_qualified_name":
        schemas.append(f"{p}stxsch")
    if _is_set_schema(a) and a.get("new_schema_shape") == "existing_schema":
        schemas.append(f"{p}newsch")
    return schemas


def _probe_select(
    case: AlterStatisticsFactorCase, a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_statistic_ext_catalog")
    if mode == "error_assertion":
        return None
    sch_lit = _stats_name_literal(a, p)
    missing = _stats_missing(a)
    if _is_rename(a) and case.outcome == "success":
        check = _new_name_literal(a, p)
        present = True
    elif missing:
        check = sch_lit
        present = False
    else:
        check = sch_lit
        present = True
    cmp_op = ">" if present else "="
    label = "stats_state"
    if mode == "stxstattarget_query":
        label = "stats_target_state"
    return (
        f"SELECT count(*) {cmp_op} 0 AS {label} "
        f"FROM pg_catalog.pg_statistic_ext "
        f"WHERE stxname = '{check}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(case: AlterStatisticsFactorCase) -> list[str]:
    """Fixture tables the case CREATEs, as the bookend gate must drop them.

    Every ALTER STATISTICS case CREATEs the underlying TABLE fixture
    ``{p}tab`` (table_dependency is always ``underlying_table_exists``),
    so every case is table-based and the bookend wraps it.
    """
    p = case.object_prefix
    return [f"{p}tab"]


def _resolve_case(case: AlterStatisticsFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    set_stats = _is_set_statistics(a)
    rename = _is_rename(a)
    owner = _is_owner_to(a)
    set_schema = _is_set_schema(a)
    missing = _stats_missing(a)

    setup: list[str] = []
    locus = "target.alter_statistics"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    stx = _stats_name(a, p)
    new = _new_name(a, p)
    new_schema = _new_schema(a, p)
    owner_target = _owner_target(a, p)
    target_value = _target_value(a)
    schemas = _schema_fixtures(a, p)

    # --- role fixtures -------------------------------------------------
    if effective == f"{p}tabowner":
        setup.append(f"CREATE ROLE {p}tabowner LOGIN;")
        locus = "fixture.privilege_state"
    elif effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}tabowner LOGIN;")
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
    if owner and a.get("new_owner_shape") == "existing_role":
        setup.append(f"CREATE ROLE {p}newowner LOGIN;")

    # --- the underlying table fixture ---------------------------------
    setup.append(
        f"CREATE TABLE {p}tab ({p}c1 integer, {p}c2 integer);"
    )
    locus = "fixture.table"
    if effective in (f"{p}tabowner", f"{p}actor"):
        setup.append(f"ALTER TABLE {p}tab OWNER TO {p}tabowner;")

    # --- schema fixtures for qualified stats / set-schema target ------
    for schema in schemas:
        setup.append(f"CREATE SCHEMA {schema};")
    if schemas:
        locus = "fixture.schema"

    # --- create statistics as the table owner (or superuser) ----------
    if effective == f"{p}actor":
        setup.append(f"SET ROLE {p}tabowner;")
    elif effective == f"{p}tabowner":
        setup.append(f"SET ROLE {p}tabowner;")

    if not missing:
        setup.append(
            f"CREATE STATISTICS {stx} ON {p}tab ({p}c1, {p}c2);"
        )
        locus = "fixture.statistics"
        if (
            rename
            and a.get("rename_behavior")
            == "rename_to_existing_name_conflict"
        ):
            setup.append(
                f"CREATE STATISTICS {p}existstx "
                f"ON {p}tab ({p}c1, {p}c2);"
            )
    else:
        setup.append(
            "SELECT 1 AS target_statistics_intentionally_absent;"
        )
        locus = "fixture.statistics_missing"

    # --- switch to the alter-execution role ----------------------------
    if effective == f"{p}actor":
        setup.append("RESET ROLE;")
        setup.append(f"SET ROLE {p}actor;")

    # --- the primary target statement ---------------------------------
    if set_stats:
        target = f"ALTER STATISTICS {stx} SET STATISTICS {target_value};"
    elif rename:
        target = f"ALTER STATISTICS {stx} RENAME TO {new};"
    elif owner:
        target = f"ALTER STATISTICS {stx} OWNER TO {owner_target};"
    else:  # set_schema
        target = f"ALTER STATISTICS {stx} SET SCHEMA {new_schema};"

    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the role fixtures are
    # created by setup, so on a fresh database the roles do not exist yet
    # at pre-cleanup time and DROP OWNED BY would crash (ON_ERROR_STOP=1)
    # before the target statement reaches execution.  Pre-cleanup drops
    # roles via DROP ROLE IF EXISTS only; the post-target cleanup runs
    # DROP OWNED BY then DROP ROLE IF EXISTS once setup has created them.
    # The DROP TABLE IF EXISTS anchor is first in pre-cleanup and last in
    # cleanup, satisfying the table-bookend gate.  Extended-statistics
    # objects depend on the underlying TABLE fixture, so the CASCADE table
    # drop removes them; no explicit DROP STATISTICS is needed.
    specs: list[DropSpec] = []
    table_names = _tables_to_drop(case)
    schema_names = list(schemas)
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(specs),
        schemas=schema_names,
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
        specs=tuple(specs),
        schemas=schema_names,
        roles=role_list,
        drop_owned=bool(role_list),
        reset_role=bool(effective),
    )
    pre_cleanup = list(pre_bookend.statements)
    cleanup = list(cln_bookend.statements)

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


def resolve_alter_statistics_factor_witness(
    case: AlterStatisticsFactorCase | AlterStatisticsFactorExtensionCase,
    repository_root: Path,
) -> AlterStatisticsFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterStatisticsFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_statistics(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+STATISTICS\b", region))


def _header(case: AlterStatisticsFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER STATISTICS {case.factor_key}="
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


def render_alter_statistics_factor_case(
    case: AlterStatisticsFactorCase | AlterStatisticsFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。")
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
    case: AlterStatisticsFactorCase | AlterStatisticsFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_statistics_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_statistics_factor_programs(
    baseline_plan: AlterStatisticsFactorLoopPlan,
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
    "AlterStatisticsFactorRenderError",
    "AlterStatisticsFactorWitness",
    "count_primary_alter_statistics",
    "generate_alter_statistics_factor_programs",
    "render_alter_statistics_factor_case",
    "resolve_alter_statistics_factor_witness",
]
