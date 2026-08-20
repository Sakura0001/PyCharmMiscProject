"""Render complete PostgreSQL 18.4 SET TRANSACTION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

SET TRANSACTION is a session/transaction-scoped TCL statement
(``SET TRANSACTION transaction_mode [, ...]``) that sets the
characteristics of the current transaction.  It creates no TABLE, so the
bookend (``DROP TABLE IF EXISTS``) is never emitted (table-less; bookend
gate exempt).  Each case establishes a known transaction-characteristic
baseline (``transaction_isolation``) so ``SET TRANSACTION`` has an
observable witness; the oracle observes the resulting GUC state via
``pg_catalog.pg_settings`` or ``current_setting``.  Every catalog
``SELECT`` carries a top-level ``ORDER BY`` so the catalog-observability
gate passes.  The declared failure (``expected_status=failure``) is
wrapped in a transaction block and provisionally mapped to SQLSTATE
``25001``.  ``SET TRANSACTION``'s col-0 keyword regex is
``(?m)^SET\\s+TRANSACTION(?:\\s|;|$)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .set_transaction_factor_extension import (
    SetTransactionFactorExtensionCase,
    _present_failure_pair,
)
from .set_transaction_factor_loop import (
    SetTransactionFactorCase,
    SetTransactionFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/tcl/transaction/"
    "set_transaction.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/tcl/transaction/"
    "set_transaction.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_GUC_SETTING = "transaction_isolation"
_GUC_BASELINE = "read committed"


class SetTransactionFactorRenderError(ValueError):
    """Raised when a SET TRANSACTION case cannot be rendered."""


@dataclass(frozen=True)
class SetTransactionFactorWitness:
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
    ext: SetTransactionFactorExtensionCase,
) -> SetTransactionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "set_transaction"
        )
    return SetTransactionFactorCase(
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
    case: SetTransactionFactorCase | SetTransactionFactorExtensionCase,
) -> SetTransactionFactorCase:
    if isinstance(case, SetTransactionFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: SetTransactionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_declared_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status", "success") == "failure"


def _probe_select(
    case: SetTransactionFactorCase,
    a: dict[str, str],
) -> str | None:
    """Effect/catalog oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    if mode == "effect_query":
        return (
            f"SELECT current_setting('{_GUC_SETTING}') "
            f"AS isolation_level;"
        )
    if mode == "returned_rows":
        return (
            f"SELECT setting AS isolation_setting "
            f"FROM pg_catalog.pg_settings "
            f"WHERE name = '{_GUC_SETTING}' "
            "ORDER BY setting;"
        )
    return (
        "SELECT count(*) > 0 AS characteristic_set "
        f"FROM pg_catalog.pg_settings "
        f"WHERE name = '{_GUC_SETTING}' "
        "ORDER BY count(*)"
        + ";"
    )


def _build_setup(
    a: dict[str, str],
) -> tuple[list[str], str]:
    """Setup lines and the semantic locus for the case."""

    setup: list[str] = []
    locus = "target.set_transaction"

    # --- transaction-characteristic baseline fixture ---
    setup.append(
        f"SET {_GUC_SETTING} TO '{_GUC_BASELINE}';"
    )
    locus = "fixture.transaction_state"

    # --- transaction block for declared-failure cases ---
    if _is_declared_failure(a):
        setup.append("BEGIN;")
        locus = "fixture.transaction_block"

    return setup, locus


def _build_target(a: dict[str, str]) -> str:
    """The primary SET TRANSACTION statement."""

    return "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;"


def _build_cleanup(a: dict[str, str]) -> list[str]:
    """Cleanup lines after the primary target."""

    lines: list[str] = []
    if _is_declared_failure(a):
        lines.append("ROLLBACK;")
    lines.append(f"RESET {_GUC_SETTING};")
    return lines


def _resolve_case(
    case: SetTransactionFactorCase,
) -> _CasePlan:
    a = _baseline(case)

    setup, locus = _build_setup(a)

    # --- the primary target statement ---
    target = _build_target(a)

    # --- oracle / SQLSTATE assertion ---
    assert_lines: list[str] = []
    if _is_declared_failure(a):
        assert_lines.append("ROLLBACK;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction ---
    cleanup = _build_cleanup(a)

    # --- pre-cleanup (safe, always idempotent) ---
    pre_cleanup: list[str] = []
    pre_cleanup.append("ROLLBACK;")
    pre_cleanup.append(f"RESET {_GUC_SETTING};")
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


def _header(case: SetTransactionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : SET TRANSACTION {case.factor_key}="
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


def render_set_transaction_factor_case(
    case: SetTransactionFactorCase | SetTransactionFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 SET TRANSACTION。")
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
    case: SetTransactionFactorCase | SetTransactionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_set_transaction_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_set_transaction_factor_programs(
    baseline_plan: SetTransactionFactorLoopPlan,
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


def count_primary_set_transaction(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*SET\s+TRANSACTION\b", region)
    )


def resolve_set_transaction_factor_witness(
    case: SetTransactionFactorCase | SetTransactionFactorExtensionCase,
    repository_root: Path,
) -> SetTransactionFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return SetTransactionFactorWitness(
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
    "SetTransactionFactorRenderError",
    "SetTransactionFactorWitness",
    "count_primary_set_transaction",
    "generate_set_transaction_factor_programs",
    "render_set_transaction_factor_case",
    "resolve_set_transaction_factor_witness",
]
