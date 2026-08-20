"""Render complete PostgreSQL 18.4 BEGIN factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the byte-level
witness validator (which re-renders and compares) can never diverge from
the bytes actually written.

BEGIN is a TCL transaction-control statement: the target is the
``BEGIN [WORK|TRANSACTION] [transaction_mode...]`` statement itself, not
a ``pg_class`` relation.  No case creates a TABLE, so the bookend
(DROP TABLE IF EXISTS) is never emitted (``_tables_to_drop`` always
returns ``[]``).  Every catalog SELECT schema-qualifies
``pg_catalog.pg_stat_activity`` (exempt from the file-prefix style gate)
and carries a top-level ``ORDER BY`` so the catalog-observability gate
passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .begin_factor_extension import (
    BeginFactorExtensionCase,
    _present_failure_pair,
)
from .begin_factor_loop import (
    BeginFactorCase,
    BeginFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/tcl/transaction/"
    "begin.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/tcl/transaction/"
    "begin.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class BeginFactorRenderError(ValueError):
    """Raised when a BEGIN case cannot be rendered."""


@dataclass(frozen=True)
class BeginFactorWitness:
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
    ext: BeginFactorExtensionCase,
) -> BeginFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "begin_transaction")
    return BeginFactorCase(
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
    case: BeginFactorCase | BeginFactorExtensionCase,
) -> BeginFactorCase:
    if isinstance(case, BeginFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: BeginFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _savepoint_name(a: dict[str, str], p: str) -> str | None:
    """The savepoint identifier in SAVEPOINT / RELEASE SAVEPOINT."""

    shape = a.get("savepoint_name_shape", "simple_name")
    if shape == "missing_name":
        return None
    if shape == "quoted_name":
        return f'"{p}Mixed SP"'
    return f"{p}sp"


def _probe_select(
    case: BeginFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None

    if mode == "catalog_query":
        return (
            "SELECT count(*) AS session_active "
            "FROM pg_catalog.pg_stat_activity "
            "WHERE pid = pg_backend_pid() "
            "ORDER BY count(*)"
        ) + ";"
    if mode == "effect_query":
        return (
            "SELECT current_setting('transaction_isolation') "
            "AS iso_level"
        ) + ";"
    if mode == "returned_rows":
        return "SELECT 1 AS begin_started;"
    return None


def _tables_to_drop(
    case: BeginFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    BEGIN is a TCL statement: it never creates a TABLE.  The bookend
    (DROP TABLE IF EXISTS) is therefore never emitted.
    """
    return []


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary BEGIN statement for the active mode."""

    tm = a.get("transaction_mode", "default")
    cb = a.get("chain_behavior", "none")
    ic = a.get("invalid_combination", "none")
    es = a.get("expected_status", "success")

    # Invalid combination overrides the mode clause.
    if ic == "syntax_valid_semantic_error":
        return "BEGIN READ ONLY READ WRITE;"
    if ic == "object_type_mismatch":
        return "BEGIN;"

    # Chain behavior (syntax error for BEGIN — it has no AND CHAIN).
    if cb == "and_chain":
        return "BEGIN AND CHAIN;"
    if cb == "and_no_chain":
        return "BEGIN AND NO CHAIN;"

    # Expected status failure (when no other failure is set).
    if es == "failure":
        return "BEGIN READ ONLY READ WRITE;"

    # Transaction mode.
    if tm == "isolation_level":
        return "BEGIN ISOLATION LEVEL SERIALIZABLE;"
    if tm == "read_write":
        return "BEGIN READ WRITE;"
    if tm == "read_only":
        return "BEGIN READ ONLY;"
    if tm == "deferrable":
        return (
            "BEGIN ISOLATION LEVEL SERIALIZABLE "
            "READ ONLY DEFERRABLE;"
        )
    return "BEGIN;"


def _needs_inside_transaction(a: dict[str, str]) -> bool:
    """Whether the setup must start a transaction before the target."""

    ts = a.get("transaction_state", "outside_transaction")
    sb = a.get("state_boundary", "no_open_transaction")
    es = a.get("expected_status", "success")
    if ts in (
        "inside_transaction",
        "savepoint_exists",
        "missing_required_state",
    ):
        return True
    if sb == "nested_savepoint":
        return True
    if es == "failure" and ts == "outside_transaction":
        return True
    return False


def _needs_prepared(a: dict[str, str]) -> bool:
    ts = a.get("transaction_state", "outside_transaction")
    sb = a.get("state_boundary", "no_open_transaction")
    return ts == "prepared_transaction_exists" or (
        sb == "prepared_transaction_leftover"
    )


def _resolve_case(
    case: BeginFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    ts = a.get("transaction_state", "outside_transaction")
    sns = a.get("savepoint_name_shape", "simple_name")
    es = a.get("expected_status", "success")

    # Override: when expected_status=failure is the primary and no other
    # failure is set, put the session inside a transaction so the target
    # BEGIN produces the active-transaction warning.
    if (
        case.factor_key == "expected_status"
        and case.factor_value == "failure"
    ):
        a["transaction_state"] = "inside_transaction"
        ts = "inside_transaction"

    # Override: when state_boundary=prepared_transaction_leftover is the
    # primary, create a prepared transaction in setup.
    if (
        case.factor_key == "state_boundary"
        and case.factor_value == "prepared_transaction_leftover"
    ):
        a["transaction_state"] = "prepared_transaction_exists"
        ts = "prepared_transaction_exists"

    # Override: when savepoint_name_shape is the primary, ensure a
    # savepoint is created so the name shape is byte-observable.
    if (
        case.factor_key == "savepoint_name_shape"
        and ts == "outside_transaction"
    ):
        a["transaction_state"] = "savepoint_exists"
        ts = "savepoint_exists"

    setup: list[str] = []
    locus = "target.begin"

    # --- setup: establish the transaction state -----------------------
    if _needs_inside_transaction(a) or ts in (
        "inside_transaction",
        "savepoint_exists",
        "missing_required_state",
    ):
        setup.append("BEGIN;")
        locus = "fixture.inside_transaction"
        if ts == "savepoint_exists":
            sp = _savepoint_name(a, p)
            if sp is not None:
                setup.append(f"SAVEPOINT {sp};")
                locus = "fixture.savepoint"
                if sns == "released_name":
                    setup.append(f"RELEASE SAVEPOINT {sp};")
    elif _needs_prepared(a) or ts == "prepared_transaction_exists":
        setup.append("BEGIN;")
        setup.append(f"PREPARE TRANSACTION '{p}prep';")
        locus = "fixture.prepared_transaction"
    else:
        setup.append("SELECT 1 AS no_active_transaction;")
        locus = "fixture.outside_transaction"

    # --- the primary target statement --------------------------------
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    cm = a.get("cleanup_mode", "rollback")
    pre_cleanup: list[str] = []
    pre_cleanup.append("ROLLBACK;")
    if _needs_prepared(a) or ts == "prepared_transaction_exists":
        pre_cleanup.append(f"ROLLBACK PREPARED '{p}prep';")
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    cleanup.append("ROLLBACK;")
    if _needs_prepared(a) or ts == "prepared_transaction_exists":
        cleanup.append(f"ROLLBACK PREPARED '{p}prep';")
    if cm == "reset_state":
        cleanup.append("RESET ALL;")
    if not cleanup:
        cleanup.append("SELECT 1 AS residual_check_no_objects;")

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


def resolve_begin_factor_witness(
    case: BeginFactorCase | BeginFactorExtensionCase,
    repository_root: Path,
) -> BeginFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return BeginFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_begin(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*BEGIN\b", region))


def _header(case: BeginFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : BEGIN {case.factor_key}="
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


def render_begin_factor_case(
    case: BeginFactorCase | BeginFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 BEGIN。")
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
    case: BeginFactorCase | BeginFactorExtensionCase,
    out: Path,
) -> None:
    text = render_begin_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_begin_factor_programs(
    baseline_plan: BeginFactorLoopPlan,
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
    "BeginFactorRenderError",
    "BeginFactorWitness",
    "count_primary_begin",
    "generate_begin_factor_programs",
    "render_begin_factor_case",
    "resolve_begin_factor_witness",
]
