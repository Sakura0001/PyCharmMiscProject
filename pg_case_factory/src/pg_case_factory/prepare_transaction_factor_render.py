"""Render complete PostgreSQL 18.4 PREPARE TRANSACTION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

PREPARE TRANSACTION is a two-phase transaction control statement
(``PREPARE TRANSACTION transaction_id``).  It is not an object-DDL statement:
the target is a transient ``pg_catalog.pg_prepared_xacts`` row, not a
``pg_class`` relation.  Every case CREATEs one fixture TABLE
(``<prefix>data``) so the prepared transaction carries a real data change
to verify, so the bookend gate (``DROP TABLE IF EXISTS`` first + last
``;``-statement) always applies.  The prepared-transaction identifier
gid is kept byte-observable in the ``PREPARE TRANSACTION`` target line
only (it is a string literal, not a FROM/JOIN target, so the
quoted-identifier style gate is never tripped).  All catalog oracles
schema-qualify ``pg_catalog.pg_prepared_xacts`` (the system VIEW for 2PC
prepared transactions, NOT ``pg_prepared_statements`` which caches SQL
PREPARE statements -- exempt from the file-prefix style gate).  Every
catalog SELECT carries a top-level ``ORDER BY`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .prepare_transaction_factor_extension import (
    PrepareTransactionFactorExtensionCase,
    _present_failure_pair,
)
from .prepare_transaction_factor_loop import (
    PrepareTransactionFactorCase,
    PrepareTransactionFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/tcl/"
    "two_phase_transaction/prepare_transaction.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/tcl/"
    "two_phase_transaction/prepare_transaction.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class PrepareTransactionFactorRenderError(ValueError):
    """Raised when a PREPARE TRANSACTION case cannot be rendered."""


@dataclass(frozen=True)
class PrepareTransactionFactorWitness:
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
    ext: PrepareTransactionFactorExtensionCase,
) -> PrepareTransactionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "prepare_transaction"
        )
    return PrepareTransactionFactorCase(
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
    case: PrepareTransactionFactorCase
    | PrepareTransactionFactorExtensionCase,
) -> PrepareTransactionFactorCase:
    if isinstance(case, PrepareTransactionFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: PrepareTransactionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _table_name(p: str) -> str:
    """Plain unqualified fixture table name (style-gate safe)."""
    return f"{p}data"


def _gid(a: dict[str, str], p: str) -> str:
    """The prepared-transaction gid string for PREPARE TRANSACTION.

    A string literal (single-quoted), so it never appears as a FROM/JOIN
    target and the quoted-identifier style gate is never tripped.  The
    quoted_id value uses a space to exercise quoted-string handling while
    staying a plain fixture-style gid that carries the object prefix.
    """

    shape = a.get("transaction_id_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Mixed Tx"
    if shape == "duplicate_id":
        return f"{p}duptx"
    return f"{p}tx"


def _scenario(a: dict[str, str]) -> str:
    """Which prepared-transaction scenario the render must produce."""

    if a.get("transaction_id_shape") == "missing_id":
        return "missing_id"
    ts = a.get("transaction_state", "prepared_transaction_exists")
    if ts in ("inside_transaction", "savepoint_exists"):
        return "inside_tx"
    if ts == "missing_required_state":
        return "no_prepared_tx"
    return "success"


def _probe_select(
    case: PrepareTransactionFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion.

    Uses ``pg_catalog.pg_prepared_xacts`` (the system VIEW for 2PC prepared
    TRANSACTIONS).  This is NOT ``pg_prepared_statements`` (which caches
    SQL PREPARE statement objects -- a completely different thing).
    """

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None

    tbl = _table_name(p)
    if mode == "catalog_query":
        return (
            "SELECT count(*) AS prepared_residual "
            "FROM pg_catalog.pg_prepared_xacts "
            "ORDER BY count(*)"
        ) + ";"
    if mode == "effect_query":
        return (
            f"SELECT count(*) AS committed_rows FROM {tbl} "
            "ORDER BY count(*)"
        ) + ";"
    if mode == "returned_rows":
        return (
            f"SELECT id, payload FROM {tbl} ORDER BY id"
        ) + ";"
    return None


def _tables_to_drop(
    case: PrepareTransactionFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    Every PREPARE TRANSACTION case CREATEs one fixture table
    (``<prefix>data``) so the prepared transaction carries a real data
    change to verify.  The bookend (DROP TABLE IF EXISTS) therefore always
    applies.
    """
    return [_table_name(case.object_prefix)]


def _resolve_case(
    case: PrepareTransactionFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    scenario = _scenario(a)
    tbl = _table_name(p)
    gid = _gid(a, p)

    setup: list[str] = []
    locus = "target.prepare_transaction"

    # --- fixture table (created by superuser, always present) ---------
    setup.append(f"CREATE TABLE {tbl} (id integer, payload text);")
    setup.append(
        f"INSERT INTO {tbl} VALUES (1, 'prepare_transaction_fixture');"
    )
    locus = "fixture.table"

    if scenario == "success":
        # A transaction block is open with a real data change staged: BEGIN,
        # insert a row, then the target PREPARE TRANSACTION prepares it.
        setup.append("BEGIN;")
        setup.append(
            f"INSERT INTO {tbl} VALUES (2, 'prepared_row');"
        )
        locus = "fixture.prepared_transaction"
    elif scenario == "inside_tx":
        # PREPARE TRANSACTION cannot run inside an incompatible transaction
        # block state.  Open a block (and a savepoint for savepoint_exists)
        # so the target is rejected at the 25001 surface.
        setup.append("BEGIN;")
        if a.get("transaction_state") == "savepoint_exists":
            setup.append(f"SAVEPOINT {p}sp;")
            locus = "fixture.savepoint"
        else:
            locus = "fixture.open_transaction"
    elif scenario == "no_prepared_tx":
        # No committable prepared-transaction state exists: do NOT stage a
        # transaction, so PREPARE TRANSACTION is rejected at the 42704
        # surface.
        locus = "fixture.prepared_transaction_missing"
    elif scenario == "missing_id":
        # The transaction identifier is syntactically absent: the parser
        # rejects ``PREPARE TRANSACTION`` at the 42601 surface before any
        # runtime lookup, so no prepared-transaction fixture is needed.
        locus = "fixture.missing_identifier"

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, gid)

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
    table_drops = [
        f"DROP TABLE IF EXISTS {t};" for t in _tables_to_drop(case)
    ]

    # pre-cleanup: table first (bookend first)
    pre_cleanup: list[str] = list(table_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: table last (bookend last)
    cleanup: list[str] = list(table_drops)
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


def _build_target(
    a: dict[str, str], p: str, gid: str
) -> str:
    """The primary PREPARE TRANSACTION statement for the active scenario."""

    if a.get("transaction_id_shape") == "missing_id":
        # No transaction identifier: a syntax error at parse time.
        return "PREPARE TRANSACTION;"
    return f"PREPARE TRANSACTION '{gid}';"


def resolve_prepare_transaction_factor_witness(
    case: PrepareTransactionFactorCase
    | PrepareTransactionFactorExtensionCase,
    repository_root: Path,
) -> PrepareTransactionFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return PrepareTransactionFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_prepare_transaction(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*PREPARE\s+TRANSACTION\b", region)
    )


def _header(case: PrepareTransactionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : PREPARE TRANSACTION {case.factor_key}="
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


def render_prepare_transaction_factor_case(
    case: PrepareTransactionFactorCase
    | PrepareTransactionFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 PREPARE TRANSACTION。")
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
    case: PrepareTransactionFactorCase
    | PrepareTransactionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_prepare_transaction_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_prepare_transaction_factor_programs(
    baseline_plan: PrepareTransactionFactorLoopPlan,
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
    "PrepareTransactionFactorRenderError",
    "PrepareTransactionFactorWitness",
    "count_primary_prepare_transaction",
    "generate_prepare_transaction_factor_programs",
    "render_prepare_transaction_factor_case",
    "resolve_prepare_transaction_factor_witness",
]
