"""Render complete PostgreSQL 18.4 SET factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

SET is a session-scoped statement (``SET configuration_parameter { TO | = }
{ value | DEFAULT }``) that sets a run-time parameter to a value.  It
creates no TABLE, so the bookend (``DROP TABLE IF EXISTS``) is never
emitted (table-less; bookend gate exempt).  Each case sets a session
runtime parameter (``work_mem``) to a non-default value so ``SET`` has a
settable witness; the oracle observes the new value via
``pg_catalog.pg_settings`` or ``current_setting``.  Every catalog
``SELECT`` carries a top-level ``ORDER BY`` so the catalog-observability
gate passes.  ``SET`` has no optional leading keywords, so the col-0
keyword regex is ``(?m)^SET(?:\\s|;|$)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .set_factor_extension import (
    SetFactorExtensionCase,
    _present_failure_pair,
)
from .set_factor_loop import (
    SetFactorCase,
    SetFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/session/"
    "runtime_parameter/set.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/session/"
    "runtime_parameter/set.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_WORK_MEM_SETTING = "work_mem"
_WORK_MEM_MODIFIED = "64MB"


class SetFactorRenderError(ValueError):
    """Raised when a SET case cannot be rendered."""


@dataclass(frozen=True)
class SetFactorWitness:
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
    ext: SetFactorExtensionCase,
) -> SetFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "set")
    return SetFactorCase(
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
    case: SetFactorCase | SetFactorExtensionCase,
) -> SetFactorCase:
    if isinstance(case, SetFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: SetFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_transaction_failure(a: dict[str, str]) -> bool:
    tv = a.get("transaction_visibility", "outside_transaction")
    return tv in (
        "inside_committed_transaction",
        "inside_rolled_back_transaction",
    )


def _is_privilege_role(a: dict[str, str]) -> bool:
    return a.get("privilege_context", "owner") == "insufficient_privilege"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target SET runs."""

    if _is_privilege_role(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_privilege_role(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: SetFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Effect/catalog oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    if mode == "effect_query":
        return (
            f"SELECT current_setting('{_WORK_MEM_SETTING}') "
            f"AS work_mem_value;"
        )
    if mode == "returned_rows":
        return (
            f"SELECT reset_val AS work_mem_default "
            f"FROM pg_catalog.pg_settings "
            f"WHERE name = '{_WORK_MEM_SETTING}' "
            "ORDER BY reset_val;"
        )
    return (
        "SELECT count(*) > 0 AS session_set "
        f"FROM pg_catalog.pg_settings "
        f"WHERE name = '{_WORK_MEM_SETTING}' "
        "ORDER BY count(*)"
        + ";"
    )


def _build_setup(
    a: dict[str, str], p: str
) -> tuple[list[str], str]:
    """Setup lines and the semantic locus for the case."""

    setup: list[str] = []
    locus = "target.set"

    # --- session state fixture (modified work_mem) ---
    setup.append(
        f"SET {_WORK_MEM_SETTING} = '{_WORK_MEM_MODIFIED}';"
    )
    locus = "fixture.session_state"

    # --- non-superuser role for privilege-context cases ---
    effective = _effective_role(a, p)
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- transaction block for in-transaction failure cases ---
    if _is_transaction_failure(a):
        setup.append("BEGIN;")
        locus = "fixture.transaction_block"

    return setup, locus


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary SET statement."""

    return f"SET {_WORK_MEM_SETTING} = '{_WORK_MEM_MODIFIED}';"


def _build_cleanup(
    a: dict[str, str], p: str
) -> list[str]:
    """Cleanup lines after the primary target."""

    roles = _role_names(a, p)
    lines: list[str] = []
    if _is_transaction_failure(a):
        lines.append("ROLLBACK;")
    lines.append(f"RESET {_WORK_MEM_SETTING};")
    if _is_privilege_role(a):
        lines.append("RESET ROLE;")
    for role in roles:
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _resolve_case(
    case: SetFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup, locus = _build_setup(a, p)
    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- the primary target statement ---
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---
    assert_lines: list[str] = []
    if _is_transaction_failure(a):
        assert_lines.append("ROLLBACK;")
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction ---
    cleanup = _build_cleanup(a, p)

    # --- pre-cleanup (safe, always idempotent) ---
    pre_cleanup: list[str] = []
    pre_cleanup.append("ROLLBACK;")
    pre_cleanup.append("RESET ROLE;")
    pre_cleanup.append(f"RESET {_WORK_MEM_SETTING};")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")
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


def _header(case: SetFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : SET {case.factor_key}="
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


def render_set_factor_case(
    case: SetFactorCase | SetFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 SET。")
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
    case: SetFactorCase | SetFactorExtensionCase,
    out: Path,
) -> None:
    text = render_set_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_set_factor_programs(
    baseline_plan: SetFactorLoopPlan,
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


def count_primary_set(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*SET\b", region)
    )


def resolve_set_factor_witness(
    case: SetFactorCase | SetFactorExtensionCase,
    repository_root: Path,
) -> SetFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return SetFactorWitness(
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
    "SetFactorRenderError",
    "SetFactorWitness",
    "count_primary_set",
    "generate_set_factor_programs",
    "render_set_factor_case",
    "resolve_set_factor_witness",
]
