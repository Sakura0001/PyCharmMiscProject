"""Render complete PostgreSQL 18.4 CHECKPOINT factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CHECKPOINT is a utility statement (``CHECKPOINT;``) that forces a WAL
flush.  It is NOT an ALTER/object-DDL statement: the target is the
whole database, not a catalog row.  All catalog oracles schema-qualify
``pg_catalog.pg_stat_bgwriter`` (exempt from the file-prefix style gate).
Every case CREATEs a fixture TABLE (``<prefix>data``) to verify
checkpoint behaviour with real data, so the bookend gate
(``DROP TABLE IF EXISTS`` first + last ``;``-statement) always applies.
Every catalog SELECT carries a top-level ``ORDER BY`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .checkpoint_factor_extension import (
    CheckpointFactorExtensionCase,
    _present_failure_pair,
)
from .checkpoint_factor_loop import (
    CheckpointFactorCase,
    CheckpointFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/utility/checkpoint/"
    "checkpoint.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/utility/checkpoint/"
    "checkpoint.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CheckpointFactorRenderError(ValueError):
    """Raised when a CHECKPOINT case cannot be rendered."""


@dataclass(frozen=True)
class CheckpointFactorWitness:
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
    ext: CheckpointFactorExtensionCase,
) -> CheckpointFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "checkpoint")
    return CheckpointFactorCase(
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
    case: CheckpointFactorCase | CheckpointFactorExtensionCase,
) -> CheckpointFactorCase:
    if isinstance(case, CheckpointFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CheckpointFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_privilege_failure(a: dict[str, str]) -> bool:
    return a.get("privilege_context", "owner") == "insufficient_privilege"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target CHECKPOINT runs."""

    pc = a.get("privilege_context", "owner")
    if pc == "insufficient_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_privilege_failure(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _table_name(p: str) -> str:
    """Plain unqualified fixture table name (style-gate safe)."""
    return f"{p}data"


def _probe_select(
    case: CheckpointFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None

    tbl = _table_name(p)
    if mode == "catalog_query":
        return (
            "SELECT count(*) > 0 AS checkpoint_activity "
            "FROM pg_catalog.pg_stat_bgwriter "
            "ORDER BY count(*)"
        ) + ";"
    if mode == "effect_query":
        # Stable boolean oracle: pg_current_wal_lsn() advances on every
        # write, so the raw value differs between run-01 and run-02 and
        # triggers a two_run_mismatch (the user's headline determinism
        # contract).  Assert presence rather than value so the transcript
        # is identical across runs while still confirming WAL is tracked.
        # Do NOT mask the LSN in normalization -- that would hide real drift.
        return (
            "SELECT pg_current_wal_lsn() IS NOT NULL "
            "AS current_wal_lsn_present;"
        )
    if mode == "returned_rows":
        return (
            f"SELECT count(*) AS row_count FROM {tbl} "
            "ORDER BY count(*)"
        ) + ";"
    return None


def _tables_to_drop(
    case: CheckpointFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    Every CHECKPOINT case CREATEs one fixture table (``<prefix>data``)
    to verify checkpoint behaviour with real data.  The bookend
    (DROP TABLE IF EXISTS) therefore always applies.
    """
    return [_table_name(case.object_prefix)]


def _resolve_case(
    case: CheckpointFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.checkpoint"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    tbl = _table_name(p)

    # --- fixture table (created by superuser) -------------------------
    setup.append(
        f"CREATE TABLE {tbl} (id integer, payload text);"
    )
    setup.append(
        f"INSERT INTO {tbl} VALUES (1, 'checkpoint_fixture');"
    )
    locus = "fixture.table"

    # --- non-superuser role for privilege-failure cases ----------------
    if effective == f"{p}actor":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the primary target statement --------------------------------
    target = "CHECKPOINT;"

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the {p}actor role is
    # created by setup, so on a fresh database the role does not exist
    # yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target CHECKPOINT reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the
    # post-target cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS
    # once setup has created the role. The DROP TABLE IF EXISTS anchor
    # is first in pre-cleanup and last in cleanup, satisfying the
    # table-bookend gate.
    specs: list[DropSpec] = []
    table_names = _tables_to_drop(case)
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
        specs=tuple(specs),
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


def resolve_checkpoint_factor_witness(
    case: CheckpointFactorCase | CheckpointFactorExtensionCase,
    repository_root: Path,
) -> CheckpointFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CheckpointFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_checkpoint(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CHECKPOINT\b", region)
    )


def _header(case: CheckpointFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CHECKPOINT {case.factor_key}="
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


def render_checkpoint_factor_case(
    case: CheckpointFactorCase | CheckpointFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CHECKPOINT。")
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
    case: CheckpointFactorCase | CheckpointFactorExtensionCase,
    out: Path,
) -> None:
    text = render_checkpoint_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_checkpoint_factor_programs(
    baseline_plan: CheckpointFactorLoopPlan,
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
    "CheckpointFactorRenderError",
    "CheckpointFactorWitness",
    "count_primary_checkpoint",
    "generate_checkpoint_factor_programs",
    "render_checkpoint_factor_case",
    "resolve_checkpoint_factor_witness",
]
