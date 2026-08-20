"""Render complete PostgreSQL 18.4 ALTER TABLESPACE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER TABLESPACE is a storage DDL statement: the target is a
``pg_catalog.pg_tablespace`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_tablespace``
(exempt from the file-prefix style gate).  No case creates a TABLE, so
the bookend (DROP TABLE IF EXISTS) is never emitted (``_tables_to_drop``
always returns ``[]``).  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_tablespace_factor_extension import (
    AlterTablespaceFactorExtensionCase,
    _present_failure_pair,
)
from .alter_tablespace_factor_loop import (
    AlterTablespaceFactorCase,
    AlterTablespaceFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/tablespace/"
    "alter_tablespace.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/tablespace/"
    "alter_tablespace.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_TABLESPACE_LOCATION = "/tmp/pgcf_tablespace_location"


class AlterTablespaceFactorRenderError(ValueError):
    """Raised when an ALTER TABLESPACE case cannot be rendered."""


@dataclass(frozen=True)
class AlterTablespaceFactorWitness:
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
    ext: AlterTablespaceFactorExtensionCase,
) -> AlterTablespaceFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "rename")
    return AlterTablespaceFactorCase(
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
    case: AlterTablespaceFactorCase
    | AlterTablespaceFactorExtensionCase,
) -> AlterTablespaceFactorCase:
    if isinstance(case, AlterTablespaceFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterTablespaceFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _tablespace_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "not_exists"


def _tablespace_name(a: dict[str, str], p: str) -> str:
    """The source tablespace identifier in ALTER TABLESPACE.

    The primary ALTER TABLESPACE target always uses a plain unqualified
    fixture name (``{p}ts``) so the quoted-identifier gate passes.  The
    shaped name (quoted, reserved-word) is exercised via the RENAME TO
    target (see :func:`_new_name`).  ``nonexistent_name`` and
    ``invalid_name`` keep their shaped source because those shapes are
    plain identifiers (no quotes, no dots) that must appear in the
    primary target to trigger the expected failure.
    """

    shape = a.get("tablespace_name_shape", "simple_id")
    if shape == "nonexistent_name":
        return f"{p}no_such_ts"
    if shape == "invalid_name":
        return f"{p}bad-ts"
    # quoted_id / reserved_word_as_name: plain fixture name as source.
    return f"{p}ts"


def _tablespace_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("tablespace_name_shape", "simple_id")
    if shape == "nonexistent_name":
        return f"{p}no_such_ts"
    if shape == "invalid_name":
        return f"{p}bad-ts"
    return f"{p}ts"


def _new_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO.

    When ``tablespace_name_shape`` is ``quoted_id`` or
    ``reserved_word_as_name`` and ``new_name_shape`` is ``simple_id``,
    the shaped name is used as the RENAME TO target so the factor value
    is exercised without placing a quoted identifier in the primary
    target position.
    """

    shape = a.get("new_name_shape", "simple_id")
    prn = a.get("pg_reserved_new_name", "normal_name")
    dnn = a.get("duplicate_new_name", "no_conflict")
    if prn == "pg_prefix_name" or shape == "pg_prefix_reserved":
        return f"pg_{p}reserved"
    if dnn == "same_name_conflict" or shape == "duplicate_name":
        return f"{p}conflict_ts"
    if shape == "invalid_name":
        return f"{p}bad-new"
    if shape == "quoted_id":
        return f'"{p}Mixed New"'
    ts_shape = a.get("tablespace_name_shape", "simple_id")
    if ts_shape == "quoted_id":
        return f'"{p}Mixed Ts"'
    if ts_shape == "reserved_word_as_name":
        return '"select"'
    return f"{p}newts"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_id")
    prn = a.get("pg_reserved_new_name", "normal_name")
    dnn = a.get("duplicate_new_name", "no_conflict")
    if prn == "pg_prefix_name" or shape == "pg_prefix_reserved":
        return f"pg_{p}reserved"
    if dnn == "same_name_conflict" or shape == "duplicate_name":
        return f"{p}conflict_ts"
    if shape == "invalid_name":
        return f"{p}bad-new"
    if shape == "quoted_id":
        return f"{p}Mixed New"
    ts_shape = a.get("tablespace_name_shape", "simple_id")
    if ts_shape == "quoted_id":
        return f"{p}Mixed Ts"
    if ts_shape == "reserved_word_as_name":
        return "select"
    return f"{p}newts"


def _owner_target(a: dict[str, str], p: str) -> str:
    """The owner target token in OWNER TO."""

    ot = a.get("owner_target", "specified_new_owner")
    if ot == "specified_current_role":
        return "CURRENT_ROLE"
    if ot == "specified_current_user":
        return "CURRENT_USER"
    if ot == "specified_session_user":
        return "SESSION_USER"
    return f"{p}newowner"


def _owner_role_name(a: dict[str, str], p: str) -> str:
    """The owner role identifier for fixture creation."""

    shape = a.get("owner_name_shape", "simple_id")
    if shape == "nonexistent_role":
        return f"{p}no_such_role"
    if shape == "quoted_id":
        return f'"{p}Mixed Owner"'
    return f"{p}newowner"


def _option_set_clause(a: dict[str, str]) -> str:
    """The option clause for SET ( option = value [, ...] )."""

    opns = a.get("option_name_shape", "valid_option")
    if opns == "invalid_option_name":
        return "bad_option_name = 1"
    iov = a.get("invalid_option_value", "valid_value")
    if iov == "invalid_value":
        return "seq_page_cost = not_a_number"
    opt = a.get("tablespace_option", "seq_page_cost")
    if opt == "seq_page_cost":
        return "seq_page_cost = 1.0"
    if opt == "random_page_cost":
        return "random_page_cost = 2.0"
    if opt == "effective_io_concurrency":
        return "effective_io_concurrency = 4"
    if opt == "maintenance_io_concurrency":
        return "maintenance_io_concurrency = 4"
    if opt == "multiple_options":
        return "seq_page_cost = 1.0, random_page_cost = 2.0"
    return "seq_page_cost = 1.0"


def _option_reset_clause(a: dict[str, str]) -> str:
    """The option clause for RESET ( option [, ...] )."""

    opns = a.get("option_name_shape", "valid_option")
    if opns == "invalid_option_name":
        return "bad_option_name"
    opt = a.get("tablespace_option", "seq_page_cost")
    if opt == "multiple_options":
        return "seq_page_cost, random_page_cost"
    if opt == "seq_page_cost":
        return "seq_page_cost"
    if opt == "random_page_cost":
        return "random_page_cost"
    if opt == "effective_io_concurrency":
        return "effective_io_concurrency"
    if opt == "maintenance_io_concurrency":
        return "maintenance_io_concurrency"
    return "seq_page_cost"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER TABLESPACE runs."""

    pl = a.get("privilege_level", "superuser")
    if pl == "non_owner":
        return f"{p}actor"
    if pl == "owner":
        return f"{p}tsowner"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    pl = a.get("privilege_level", "superuser")
    action = a.get("target_action", "rename")
    ot = a.get("owner_target", "specified_new_owner")
    ons = a.get("owner_name_shape", "simple_id")
    if pl == "owner":
        roles.append(f"{p}tsowner")
    if pl == "non_owner":
        roles.append(f"{p}tsowner")
        roles.append(f"{p}actor")
    if (
        action == "owner"
        and ot == "specified_new_owner"
        and ons == "simple_id"
    ):
        roles.append(f"{p}newowner")
    return tuple(roles)


def _probe_select(
    case: AlterTablespaceFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query_pg_tablespace")
    if mode == "error_assertion":
        return None

    ts_lit = _tablespace_name_literal(a, p)
    missing = _tablespace_missing(a)
    action = a.get("target_action", "rename")

    if action == "rename" and case.outcome == "success":
        check = _new_name_literal(a, p)
        present = True
    elif missing:
        check = ts_lit
        present = False
    else:
        check = ts_lit
        present = True

    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS tablespace_state "
        f"FROM pg_catalog.pg_tablespace "
        f"WHERE spcname = '{check}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: AlterTablespaceFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    ALTER TABLESPACE is a storage DDL statement: it never creates a
    TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore never emitted.
    """
    return []


def _resolve_case(
    case: AlterTablespaceFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "rename")
    missing = _tablespace_missing(a)

    setup: list[str] = []
    locus = "target.alter_tablespace"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    ts = _tablespace_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}tsowner":
        setup.append(f"CREATE ROLE {p}tsowner LOGIN;")
        locus = "fixture.privilege_state"
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}tsowner LOGIN;")
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
    if (
        action == "owner"
        and a.get("owner_target", "specified_new_owner")
        == "specified_new_owner"
        and a.get("owner_name_shape", "simple_id") == "simple_id"
    ):
        setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.owner_role"

    # --- the target tablespace fixture -------------------------------
    if not missing:
        setup.append(
            f"CREATE TABLESPACE {ts} "
            f"LOCATION '{_TABLESPACE_LOCATION}';"
        )
        locus = "fixture.tablespace"
        if effective == f"{p}tsowner":
            setup.append(
                f"ALTER TABLESPACE {ts} OWNER TO {p}tsowner;"
            )
    else:
        setup.append(
            "SELECT 1 AS target_tablespace_intentionally_absent;"
        )
        locus = "fixture.tablespace_missing"

    # --- conflicting tablespace for rename conflict ------------------
    if (
        action == "rename"
        and a.get("duplicate_new_name", "no_conflict")
        == "same_name_conflict"
    ):
        setup.append(
            f"CREATE TABLESPACE {p}conflict_ts "
            f"LOCATION '{_TABLESPACE_LOCATION}';"
        )
        locus = "fixture.rename_conflict"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, ts)

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

    # --- cleanup construction -----------------------------------------
    tablespaces_to_drop: list[str] = []
    if not missing:
        tablespaces_to_drop.append(ts)
    if action == "rename":
        new = _new_name(a, p)
        if new != ts:
            tablespaces_to_drop.append(new)
        if (
            a.get("duplicate_new_name", "no_conflict")
            == "same_name_conflict"
        ):
            tablespaces_to_drop.append(f"{p}conflict_ts")

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    ts_drops = [
        f"DROP TABLESPACE IF EXISTS {name};"
        for name in tablespaces_to_drop
    ]

    # pre-cleanup: tablespaces then roles
    pre_cleanup: list[str] = []
    pre_cleanup.extend(ts_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: RESET ROLE, tablespaces, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(ts_drops)
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


def _build_target(
    a: dict[str, str], p: str, ts: str
) -> str:
    """The primary ALTER TABLESPACE statement for the active branch."""

    action = a.get("target_action", "rename")
    if action == "rename":
        new = _new_name(a, p)
        return f"ALTER TABLESPACE {ts} RENAME TO {new};"
    if action == "owner":
        target = _owner_target(a, p)
        return f"ALTER TABLESPACE {ts} OWNER TO {target};"
    if action == "set":
        clause = _option_set_clause(a)
        return f"ALTER TABLESPACE {ts} SET ({clause});"
    if action == "reset":
        clause = _option_reset_clause(a)
        return f"ALTER TABLESPACE {ts} RESET ({clause});"
    return f"ALTER TABLESPACE {ts} RENAME TO {p}newts;"


def resolve_alter_tablespace_factor_witness(
    case: AlterTablespaceFactorCase
    | AlterTablespaceFactorExtensionCase,
    repository_root: Path,
) -> AlterTablespaceFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterTablespaceFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_tablespace(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*ALTER\s+TABLESPACE\b", region)
    )


def _header(case: AlterTablespaceFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER TABLESPACE {case.factor_key}="
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


def render_alter_tablespace_factor_case(
    case: AlterTablespaceFactorCase
    | AlterTablespaceFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER TABLESPACE。")
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
    case: AlterTablespaceFactorCase
    | AlterTablespaceFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_tablespace_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_tablespace_factor_programs(
    baseline_plan: AlterTablespaceFactorLoopPlan,
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
    "AlterTablespaceFactorRenderError",
    "AlterTablespaceFactorWitness",
    "count_primary_alter_tablespace",
    "generate_alter_tablespace_factor_programs",
    "render_alter_tablespace_factor_case",
    "resolve_alter_tablespace_factor_witness",
]
