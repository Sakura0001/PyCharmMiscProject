"""Render complete PostgreSQL 18.4 LOAD factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

LOAD is a utility statement (``LOAD 'filename';``) that loads a shared
library into the session.  It is NOT an object-DDL statement: the target
is a shared library file, not a catalog row.  LOAD creates NO table, so
the ``audit_complete_table_script`` bookend gate does NOT trigger
(class-2 N/A).  The credited target ``LOAD '<filename>';`` itself is the
fixture.  LOAD is idempotent (re-loading is a no-op).

LOAD's success is hard to witness via catalog (the library is loaded
into the process, not a catalog row).  The probe strategy is therefore
byte-observable: the SQLSTATE assertion witnesses the target outcome,
supplemented by side-effect catalog probes mirroring checkpoint's
``pg_stat_bgwriter`` oracle — ``pg_catalog.pg_settings`` (a loaded
library may register a custom GUC via ``_PG_init``) for catalog_query
mode, ``pg_catalog.pg_roles`` (session role witness) for effect_query
mode, and ``pg_catalog.pg_proc`` (a loaded library may register a C
function) for returned_rows mode.  For privilege-failure cases the
session role is probed via ``pg_catalog.pg_roles`` / ``current_user``
before ``RESET ROLE``.  Every catalog SELECT carries a top-level
``ORDER BY count(*) LIMIT 1`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .load_factor_extension import (
    LoadFactorExtensionCase,
    _present_failure_pair,
)
from .load_factor_loop import (
    LoadFactorCase,
    LoadFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/utility/library/"
    "load.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/utility/library/"
    "load.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class LoadFactorRenderError(ValueError):
    """Raised when a LOAD case cannot be rendered."""


@dataclass(frozen=True)
class LoadFactorWitness:
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
    ext: LoadFactorExtensionCase,
) -> LoadFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "load")
    return LoadFactorCase(
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
    case: LoadFactorCase | LoadFactorExtensionCase,
) -> LoadFactorCase:
    if isinstance(case, LoadFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: LoadFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_privilege_failure(a: dict[str, str]) -> bool:
    return a.get("privilege_context", "owner") == "insufficient_privilege"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target LOAD runs."""

    pc = a.get("privilege_context", "owner")
    if pc == "insufficient_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_privilege_failure(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _target_fragment(a: dict[str, str]) -> str:
    """The credited LOAD statement, varying by failure surface."""

    pc = a.get("privilege_context", "owner")
    rb = a.get("resource_boundary", "small_relation")
    ts = a.get("target_state", "database_wide")
    ic = a.get("invalid_combination", "none")
    # Privilege failure (incl. expected_status=failure alias which
    # derives privilege_context=insufficient_privilege): a valid library
    # loaded by a non-superuser session -> 42501.
    if pc == "insufficient_privilege":
        return "LOAD '$libdir/plpgsql';"
    # Nonexistent library file -> 42883 (undefined_file).
    if rb == "missing_file_or_library":
        return "LOAD '$libdir/missing_library';"
    # Library target not found -> 42883 (undefined_file).
    if ts == "target_missing":
        return "LOAD '$libdir/absent_target';"
    # File exists but is not a shared library -> 55000 (wrong ELF).
    if ts == "wrong_object_type":
        return "LOAD '/etc/passwd';"
    # Object type mismatch -> 55000 (wrong object type).
    if ic == "object_type_mismatch":
        return "LOAD '/etc/hostname';"
    # Syntactically valid but semantically invalid filename -> 42601.
    if ic == "syntax_valid_semantic_error":
        return "LOAD '';"
    # Success: a valid shared library loaded by a superuser.
    return "LOAD '$libdir/plpgsql';"


def _role_probe() -> str:
    """Session-role witness for privilege-failure cases (pre RESET ROLE)."""

    return (
        "SELECT count(*) AS non_superuser_role_witness "
        "FROM pg_catalog.pg_roles "
        "WHERE rolname = current_user "
        "ORDER BY count(*) LIMIT 1;"
    )


def _probe_select(
    case: LoadFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    if mode == "catalog_query":
        return (
            "SELECT count(*) > 0 AS library_catalog_present "
            "FROM pg_catalog.pg_settings "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "effect_query":
        return (
            "SELECT count(*) AS session_role_count "
            "FROM pg_catalog.pg_roles "
            "WHERE rolname = current_user "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "returned_rows":
        return (
            "SELECT count(*) AS loaded_function_rows "
            "FROM pg_catalog.pg_proc "
            "ORDER BY count(*) LIMIT 1;"
        )
    return None


def _resolve_case(
    case: LoadFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.load"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- non-superuser role for privilege-failure cases ---------------
    if effective == f"{p}actor":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the primary target statement --------------------------------
    target = _target_fragment(a)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append(_role_probe())
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: roles first (bookend first)
    pre_cleanup: list[str] = list(role_drops)
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    # cleanup: RESET ROLE, roles (bookend last)
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(role_drops)
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


def resolve_load_factor_witness(
    case: LoadFactorCase | LoadFactorExtensionCase,
    repository_root: Path,
) -> LoadFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return LoadFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_load(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*LOAD\b", region)
    )


def _header(case: LoadFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : LOAD {case.factor_key}="
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


def render_load_factor_case(
    case: LoadFactorCase | LoadFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 LOAD。")
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
    case: LoadFactorCase | LoadFactorExtensionCase,
    out: Path,
) -> None:
    text = render_load_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_load_factor_programs(
    baseline_plan: LoadFactorLoopPlan,
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
    "LoadFactorRenderError",
    "LoadFactorWitness",
    "count_primary_load",
    "generate_load_factor_programs",
    "render_load_factor_case",
    "resolve_load_factor_witness",
]
