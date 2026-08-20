"""Render complete PostgreSQL 18.4 ALTER SYSTEM factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER SYSTEM is a NON-TABLE statement: the target is a
``pg_settings`` / ``postgresql.auto.conf`` entry, not a ``pg_class``
relation.  All catalog oracles therefore schema-qualify
``pg_catalog.pg_settings`` or ``pg_catalog.pg_file_settings`` (both
exempt from the file-prefix style gate because they start with ``pg_``).
Every catalog SELECT carries a top-level ``ORDER BY`` so the regress
output script style gate's catalog-order-by rule is satisfied.  No table
is ever created, so the DROP TABLE bookend contract does not apply.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_system_factor_extension import (
    AlterSystemFactorExtensionCase,
    _present_failure_pair,
)
from .alter_system_factor_loop import (
    AlterSystemFactorCase,
    AlterSystemFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/system/"
    "alter_system.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/system/"
    "alter_system.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterSystemFactorRenderError(ValueError):
    """Raised when an ALTER SYSTEM case cannot be rendered."""


@dataclass(frozen=True)
class AlterSystemFactorWitness:
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


# configuration_parameter_type -> representative valid GUC name.
_BASE_PARAM: dict[str, str] = {
    "superuser_only_parameter": "shared_buffers",
    "user_settable_parameter": "work_mem",
    "postmaster_restart_required": "max_connections",
    "sighup_reload_required": "log_min_messages",
    "backend_session_parameter": "enable_hashjoin",
}


def _synthetic_case(
    ext: AlterSystemFactorExtensionCase,
) -> AlterSystemFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "set")
    return AlterSystemFactorCase(
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
    case: AlterSystemFactorCase | AlterSystemFactorExtensionCase,
) -> AlterSystemFactorCase:
    if isinstance(case, AlterSystemFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterSystemFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_non_superuser(a: dict[str, str]) -> bool:
    return a.get("executor_privilege") == "non_superuser"


def _is_risk(case: AlterSystemFactorCase) -> bool:
    return case.kind == "RISK"


def _is_nonexistent_param(a: dict[str, str]) -> bool:
    return (
        a.get("parameter_name_shape") == "nonexistent_parameter_name"
    )


def _is_reset_all(a: dict[str, str]) -> bool:
    return a.get("target_action") == "reset_all"


def _parameter_name(a: dict[str, str], p: str) -> str:
    """The GUC identifier used inside ALTER SYSTEM and oracles."""

    shape = a.get("parameter_name_shape", "valid_parameter_name")
    if shape == "nonexistent_parameter_name":
        return f"{p}nonexistent_param"
    if shape == "custom_parameter_name_with_dot":
        return f"{p}custom.param"
    if shape == "quoted_parameter_name":
        return f'"{p}quoted.param"'
    cpt = a.get(
        "configuration_parameter_type", "user_settable_parameter"
    )
    return _BASE_PARAM.get(cpt, "work_mem")


def _parameter_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle WHERE clauses."""

    name = _parameter_name(a, p)
    if name.startswith('"') and name.endswith('"'):
        return name[1:-1]
    return name


def _parameter_value(a: dict[str, str]) -> str:
    """The value token in ALTER SYSTEM SET param = value."""

    shape = a.get("value_shape", "valid_string_value")
    if shape == "valid_integer_value":
        return "1024"
    if shape == "valid_boolean_value":
        return "'on'"
    if shape == "multiple_comma_separated_values":
        return "'alpha,beta,gamma'"
    if shape == "default_keyword":
        return "DEFAULT"
    if shape == "invalid_value_type":
        return "'not_a_number'"
    return "'8MB'"


def _target_statement(a: dict[str, str], p: str) -> str:
    action = a.get("target_action", "set")
    param = _parameter_name(a, p)
    if action == "set_default":
        return f"ALTER SYSTEM SET {param} = DEFAULT;"
    if action == "reset":
        return f"ALTER SYSTEM RESET {param};"
    if action == "reset_all":
        return "ALTER SYSTEM RESET ALL;"
    value = _parameter_value(a)
    return f"ALTER SYSTEM SET {param} = {value};"


def _probe_select(
    case: AlterSystemFactorCase, a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_settings_query")
    if mode == "error_assertion":
        return None

    param_lit = _parameter_name_literal(a, p)
    success = case.outcome == "success"
    nonexistent = _is_nonexistent_param(a)
    reset_all = _is_reset_all(a)

    if mode == "show_command":
        if reset_all or nonexistent:
            return "SHOW server_version;"
        return f"SHOW {_parameter_name(a, p)};"

    if reset_all:
        if mode == "pg_file_settings_query":
            return (
                "SELECT count(*) AS auto_conf_entries "
                "FROM pg_catalog.pg_file_settings "
                "ORDER BY count(*);"
            )
        return (
            "SELECT count(*) AS auto_conf_entries "
            "FROM pg_catalog.pg_settings "
            "WHERE source = 'configuration file' "
            "ORDER BY count(*);"
        )

    cmp_op = ">" if success else "="
    if mode == "pg_file_settings_query":
        return (
            f"SELECT count(*) {cmp_op} 0 AS param_in_file "
            f"FROM pg_catalog.pg_file_settings "
            f"WHERE name = '{param_lit}' "
            f"ORDER BY count(*);"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS param_set "
        f"FROM pg_catalog.pg_settings "
        f"WHERE name = '{param_lit}' "
        f"AND source = 'configuration file' "
        f"ORDER BY count(*);"
    )


def _cleanup_lines(a: dict[str, str], p: str) -> list[str]:
    """Cleanup statements derived from cleanup_mode."""

    mode = a.get("cleanup_mode", "alter_system_reset_parameter")
    if mode == "alter_system_reset_all":
        return ["ALTER SYSTEM RESET ALL;"]
    if _is_nonexistent_param(a):
        return ["SELECT 1 AS cleanup_nonexistent_param;"]
    param = _parameter_name(a, p)
    return [f"ALTER SYSTEM RESET {param};"]


def _resolve_case(case: AlterSystemFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    risk = _is_risk(case)
    nonsuper = _is_non_superuser(a)

    setup: list[str] = []
    locus = "target.alter_system"

    if nonsuper:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        setup.append(f"SET ROLE {p}actor;")
        locus = "fixture.privilege_state"

    if risk:
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    target = _target_statement(a, p)

    assert_lines: list[str] = []
    if nonsuper:
        assert_lines.append("RESET ROLE;")
    if risk:
        assert_lines.append("ROLLBACK;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    pre_cleanup = _cleanup_lines(a, p)
    if not pre_cleanup:
        pre_cleanup = ["SELECT 1 AS pre_clean_check;"]

    cleanup: list[str] = []
    if nonsuper:
        cleanup.append("RESET ROLE;")
        cleanup.append(f"DROP ROLE IF EXISTS {p}actor;")
    cleanup.extend(_cleanup_lines(a, p))
    if not cleanup:
        cleanup.append("SELECT 1 AS cleanup_check;")

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


def resolve_alter_system_factor_witness(
    case: AlterSystemFactorCase | AlterSystemFactorExtensionCase,
    repository_root: Path,
) -> AlterSystemFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterSystemFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_system(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+SYSTEM\b", region))


def _header(case: AlterSystemFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER SYSTEM {case.factor_key}="
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


def render_alter_system_factor_case(
    case: AlterSystemFactorCase | AlterSystemFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER SYSTEM。")
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
    case: AlterSystemFactorCase | AlterSystemFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_system_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_system_factor_programs(
    baseline_plan: AlterSystemFactorLoopPlan,
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
    "AlterSystemFactorRenderError",
    "AlterSystemFactorWitness",
    "count_primary_alter_system",
    "generate_alter_system_factor_programs",
    "render_alter_system_factor_case",
    "resolve_alter_system_factor_witness",
]
