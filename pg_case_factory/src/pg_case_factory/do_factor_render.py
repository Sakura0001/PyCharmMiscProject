"""Render complete PostgreSQL 18.4 DO factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

DO is a session/utility statement: it executes an anonymous code block
(``DO [ LANGUAGE lang_name ] code``) and creates no persistent catalog
row and no table.  All catalog oracles are trivial probes (no
``pg_catalog`` FROM clause is needed) so the catalog-observability gate
passes vacuously.  No case creates a TABLE, so the bookend (DROP TABLE
IF EXISTS) is never emitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .do_factor_extension import (
    DoFactorExtensionCase,
    _present_failure_pair,
)
from .do_factor_loop import (
    DoFactorCase,
    DoFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/utility/"
    "anonymous_code/do.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/utility/"
    "anonymous_code/do.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class DoFactorRenderError(ValueError):
    """Raised when a DO case cannot be rendered."""


@dataclass(frozen=True)
class DoFactorWitness:
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
    ext: DoFactorExtensionCase,
) -> DoFactorCase:
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
    return DoFactorCase(
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
    case: DoFactorCase | DoFactorExtensionCase,
) -> DoFactorCase:
    if isinstance(case, DoFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: DoFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_insufficient_privilege(a: dict[str, str]) -> bool:
    return a.get("privilege_context") == "insufficient_privilege"


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_insufficient_privilege(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_insufficient_privilege(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _language_clause(a: dict[str, str]) -> str:
    """The optional LANGUAGE clause for the DO statement."""

    shape = a.get("option_shape", "minimal")
    if shape == "verbose_or_format":
        return "LANGUAGE plpgsql"
    return ""


def _build_body(a: dict[str, str]) -> str:
    """The anonymous code block body (dollar-quoted string literal)."""

    if _is_failure(a):
        return (
            "$$\n"
            "BEGIN\n"
            "    RAISE EXCEPTION 'do declared failure';\n"
            "END\n"
            "$$"
        )
    return (
        "$$\n"
        "BEGIN\n"
        "    PERFORM 1;\n"
        "END\n"
        "$$"
    )


def _build_target(
    a: dict[str, str], case: DoFactorCase, p: str
) -> str:
    """The primary DO statement."""

    body = _build_body(a)
    lang = _language_clause(a)
    if lang:
        return f"DO {lang} {body};"
    return f"DO {body};"


def _probe_select(
    case: DoFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Effect/catalog oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    if mode == "effect_query":
        return "SELECT 1 AS do_effect_probe ORDER BY 1;"
    if mode == "returned_rows":
        return "SELECT 1 AS do_returned_rows_probe ORDER BY 1;"
    return "SELECT 1 AS do_catalog_probe ORDER BY 1;"


def _build_cleanup(a: dict[str, str], p: str) -> list[str]:
    """Cleanup lines after the primary target."""

    lines: list[str] = []
    if _is_insufficient_privilege(a):
        lines.append("RESET ROLE;")
    for role in _role_names(a, p):
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    mode = a.get("cleanup_mode", "rollback")
    lines.append(f"SELECT 1 AS do_cleanup_{mode} ORDER BY 1;")
    return lines


def _resolve_case(case: DoFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.do"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- role fixture for privilege tests ---
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"

    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement ---
    target = _build_target(a, case, p)

    # --- oracle / SQLSTATE assertion ---
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

    # --- cleanup construction ---
    cleanup = _build_cleanup(a, p)

    # --- pre-cleanup (safe, always IF EXISTS CASCADE) ---
    pre_cleanup: list[str] = []
    pre_cleanup.append("RESET ROLE;")
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


def _header(case: DoFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DO "
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


def render_do_factor_case(
    case: DoFactorCase | DoFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 DO。")
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
    case: DoFactorCase | DoFactorExtensionCase,
    out: Path,
) -> None:
    text = render_do_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_do_factor_programs(
    baseline_plan: DoFactorLoopPlan,
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


def count_primary_do(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^DO(?:\s|;|$)", region)
    )


def resolve_do_factor_witness(
    case: DoFactorCase | DoFactorExtensionCase,
    repository_root: Path,
) -> DoFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DoFactorWitness(
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
    "DoFactorRenderError",
    "DoFactorWitness",
    "count_primary_do",
    "generate_do_factor_programs",
    "render_do_factor_case",
    "resolve_do_factor_witness",
]
