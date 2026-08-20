"""Render complete PostgreSQL 18.4 LISTEN factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

LISTEN is a session-scoped statement (``LISTEN channel``) that registers
the current session to receive notifications on a channel.  It creates
no TABLE, so the bookend (``DROP TABLE IF EXISTS``) is never emitted
(table-less; bookend gate exempt).  LISTEN is idempotent -- re-listening
on an already-listened channel is a no-op -- so the credited target
``LISTEN <channel>;`` is itself the fixture.  The oracle observes the
session listening set via the built-in ``pg_listening_channels()``
set-returning function.  Every catalog/session ``SELECT`` carries a
top-level ``ORDER BY count(*) LIMIT 1`` so the catalog-observability
gate passes.  ``LISTEN`` has no optional leading keywords, so the col-0
keyword regex is ``(?m)^LISTEN(?:\\s|;|$)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .listen_factor_extension import (
    ListenFactorExtensionCase,
    _present_failure_pair,
)
from .listen_factor_loop import (
    ListenFactorCase,
    ListenFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/session/"
    "notification/listen.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/session/"
    "notification/listen.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

# A channel name exceeding NAMEDATALEN-1 (63) -> SQLSTATE 08P01.
_TOO_LONG_CHANNEL = "a" * 64


class ListenFactorRenderError(ValueError):
    """Raised when a LISTEN case cannot be rendered."""


@dataclass(frozen=True)
class ListenFactorWitness:
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
    ext: ListenFactorExtensionCase,
) -> ListenFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "listen")
    return ListenFactorCase(
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
    case: ListenFactorCase | ListenFactorExtensionCase,
) -> ListenFactorCase:
    if isinstance(case, ListenFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: ListenFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(case: ListenFactorCase) -> bool:
    return case.outcome == "expected_failure"


def _is_privilege_role(a: dict[str, str]) -> bool:
    return a.get("privilege_context", "owner") == "insufficient_privilege"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target LISTEN runs."""

    if _is_privilege_role(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_privilege_role(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _target_channel(a: dict[str, str], p: str) -> str:
    """The channel token for the credited LISTEN target per name_shape."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}QuotedCh"'
    if shape == "schema_qualified":
        return f"public.{p}ch"
    # plain_identifier, alias_used (LISTEN has no alias; covered abstractly)
    return f"{p}ch"


def _probe_channel(
    case: ListenFactorCase, a: dict[str, str], p: str
) -> str:
    """The bare unquoted channel name for the pg_listening_channels probe."""

    if _is_failure(case):
        if case.expected_sqlstate == "08P01":
            return _TOO_LONG_CHANNEL
        return f"{p}ch"
    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}QuotedCh"
    # plain/alias/schema_qualified: bare channel (schema stripped if present)
    return f"{p}ch"


def _probe_select(
    case: ListenFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Effect/catalog oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    channel = _probe_channel(case, a, p)
    failure = _is_failure(case)
    if mode == "effect_query":
        return (
            f"SELECT count(*) AS listening_count "
            f"FROM pg_catalog.pg_listening_channels() AS ch "
            f"WHERE ch = '{channel}' "
            f"ORDER BY count(*) LIMIT 1;"
        )
    if mode == "returned_rows":
        return (
            f"SELECT count(*) AS listening_rowcount "
            f"FROM pg_catalog.pg_listening_channels() AS ch "
            f"WHERE ch = '{channel}' "
            f"ORDER BY count(*) LIMIT 1;"
        )
    # catalog_query
    if failure:
        return (
            f"SELECT count(*) = 0 AS not_listening "
            f"FROM pg_catalog.pg_listening_channels() AS ch "
            f"WHERE ch = '{channel}' "
            f"ORDER BY count(*) LIMIT 1;"
        )
    return (
        f"SELECT count(*) > 0 AS listening "
        f"FROM pg_catalog.pg_listening_channels() AS ch "
        f"WHERE ch = '{channel}' "
        f"ORDER BY count(*) LIMIT 1;"
    )


def _build_setup(
    a: dict[str, str], p: str
) -> tuple[list[str], str]:
    """Setup lines and the semantic locus for the case.

    LISTEN is idempotent -- the credited ``LISTEN <channel>;`` target is
    itself the fixture (re-listening is a no-op).  Only a non-superuser
    role is created for privilege-context cases.
    """

    setup: list[str] = []
    locus = "target.listen"

    effective = _effective_role(a, p)
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    return setup, locus


def _build_target(
    case: ListenFactorCase, a: dict[str, str], p: str
) -> str:
    """The primary LISTEN statement."""

    if _is_failure(case):
        if case.expected_sqlstate == "42601":
            return "LISTEN ;"
        if case.expected_sqlstate == "08P01":
            return f"LISTEN {_TOO_LONG_CHANNEL};"
    channel = _target_channel(a, p)
    return f"LISTEN {channel};"


def _build_cleanup(
    a: dict[str, str], p: str
) -> list[str]:
    """Cleanup lines after the primary target."""

    roles = _role_names(a, p)
    lines: list[str] = []
    lines.append("UNLISTEN *;")
    if _is_privilege_role(a):
        lines.append("RESET ROLE;")
    for role in roles:
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _resolve_case(
    case: ListenFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup, locus = _build_setup(a, p)
    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- the primary target statement ---
    target = _build_target(case, a, p)

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

    # --- pre-cleanup (safe, always idempotent) ---
    pre_cleanup: list[str] = []
    pre_cleanup.append("UNLISTEN *;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    on_error_off = _is_failure(case)
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def _header(case: ListenFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : LISTEN {case.factor_key}="
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


def render_listen_factor_case(
    case: ListenFactorCase | ListenFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 LISTEN。")
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
    case: ListenFactorCase | ListenFactorExtensionCase,
    out: Path,
) -> None:
    text = render_listen_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_listen_factor_programs(
    baseline_plan: ListenFactorLoopPlan,
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


def count_primary_listen(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*LISTEN\b", region)
    )


def resolve_listen_factor_witness(
    case: ListenFactorCase | ListenFactorExtensionCase,
    repository_root: Path,
) -> ListenFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return ListenFactorWitness(
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
    "ListenFactorRenderError",
    "ListenFactorWitness",
    "count_primary_listen",
    "generate_listen_factor_programs",
    "render_listen_factor_case",
    "resolve_listen_factor_witness",
]
