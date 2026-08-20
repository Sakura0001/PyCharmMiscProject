"""Render complete PostgreSQL 18.4 CREATE TABLESPACE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE TABLESPACE is a storage-level DDL statement: the target is a
``pg_catalog.pg_tablespace`` catalog row plus a filesystem directory
marker, not a ``pg_class`` relation.  All catalog oracles schema-qualify
``pg_catalog.pg_tablespace`` (exempt from the file-prefix style gate).
No case creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is never
emitted (``_tables_to_drop`` always returns ``[]``) — table-less-exempt.
Every catalog SELECT carries a top-level ``ORDER BY count(*)`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_tablespace_factor_extension import (
    CreateTablespaceFactorExtensionCase,
    _present_failure_pair,
)
from .create_tablespace_factor_loop import (
    CreateTablespaceFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/tablespace/"
    "create_tablespace.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/tablespace/"
    "create_tablespace.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_TEST_DIR_ROOT = "/tmp/pgcf_ctsp"


class CreateTablespaceFactorRenderError(ValueError):
    """Raised when a CREATE TABLESPACE case cannot be rendered."""


@dataclass(frozen=True)
class CreateTablespaceFactorWitness:
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
    ext: CreateTablespaceFactorExtensionCase,
) -> CreateTablespaceFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "create")
    return CreateTablespaceFactorCase(
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
    case: CreateTablespaceFactorCase
    | CreateTablespaceFactorExtensionCase,
) -> CreateTablespaceFactorCase:
    if isinstance(
        case, CreateTablespaceFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateTablespaceFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _tablespace_name(a: dict[str, str], p: str) -> str:
    """The tablespace identifier in CREATE TABLESPACE."""

    shape = a.get("tablespace_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Mixed Ts"'
    if shape == "duplicate_name":
        return f"{p}ts"
    if shape == "invalid_name":
        return '""'
    if shape == "pg_prefix_reserved":
        return f"pg_{p}ts"
    return f"{p}ts"


def _tablespace_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("tablespace_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Mixed Ts"
    if shape == "invalid_name":
        return ""
    if shape == "pg_prefix_reserved":
        return f"pg_{p}ts"
    return f"{p}ts"


def _directory_path(a: dict[str, str], p: str) -> str:
    """The LOCATION directory path."""

    shape = a.get("directory_path_shape", "absolute_path")
    if shape == "relative_path":
        return f"pg_tblspc/{p}rel"
    if shape == "empty_path":
        return ""
    if shape == "special_path":
        return f"{_TEST_DIR_ROOT}/{p}dir with spaces"
    return f"{_TEST_DIR_ROOT}/{p}dir"


def _owner_clause(a: dict[str, str], p: str) -> str:
    """The OWNER clause, or empty string if omitted."""

    clause = a.get("owner_clause", "omitted")
    if clause == "specified_new_owner":
        shape = a.get("owner_name_shape", "simple_id")
        if shape == "quoted_id":
            return f' OWNER "{p}Mixed Owner"'
        if shape == "nonexistent_role":
            return f" OWNER {p}no_such_role"
        return f" OWNER {p}owner"
    if clause == "specified_current_role":
        return " OWNER CURRENT_ROLE"
    if clause == "specified_current_user":
        return " OWNER CURRENT_USER"
    if clause == "specified_session_user":
        return " OWNER SESSION_USER"
    return ""


def _with_clause(a: dict[str, str]) -> str:
    """The WITH (tablespace_option) clause, or empty string if omitted."""

    clause = a.get("with_clause", "omitted")
    if clause == "single_option_seq_page_cost":
        return " WITH (seq_page_cost = 1.0)"
    if clause == "single_option_random_page_cost":
        return " WITH (random_page_cost = 4.0)"
    if clause == "single_option_effective_io_concurrency":
        return " WITH (effective_io_concurrency = 16)"
    if clause == "single_option_maintenance_io_concurrency":
        return " WITH (maintenance_io_concurrency = 16)"
    if clause == "multiple_options":
        return (
            " WITH (seq_page_cost = 1.0, "
            "random_page_cost = 4.0)"
        )
    if a.get("invalid_option") == "invalid_option_name":
        return " WITH (invalid_option_name = 1)"
    return ""


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target CREATE TABLESPACE runs."""

    ep = a.get("privilege_level", "superuser")
    if ep == "non_superuser":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    ep = a.get("privilege_level", "superuser")
    oc = a.get("owner_clause", "omitted")
    ons = a.get("owner_name_shape", "simple_id")
    if ep == "non_superuser":
        roles.append(f"{p}actor")
    if oc == "specified_new_owner" and ons != "nonexistent_role":
        roles.append(f"{p}owner")
    return tuple(roles)


def _object_missing(a: dict[str, str]) -> bool:
    os_ = a.get("object_state", "not_exists")
    return os_ != "not_exists"


def _probe_select(
    case: CreateTablespaceFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get(
        "verification_mode", "catalog_query_pg_tablespace"
    )
    if mode == "error_assertion":
        return None

    name_lit = _tablespace_name_literal(a, p)
    present = case.outcome == "success"
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS tablespace_state "
        f"FROM pg_catalog.pg_tablespace "
        f"WHERE spcname = '{name_lit}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: CreateTablespaceFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE TABLESPACE is a storage-level DDL statement: it never
    creates a TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore
    never emitted (table-less-exempt).
    """
    return []


def _build_target(
    a: dict[str, str], p: str, name: str
) -> str:
    """The primary CREATE TABLESPACE statement."""

    owner = _owner_clause(a, p)
    directory = _directory_path(a, p)
    with_clause = _with_clause(a)
    return (
        f"CREATE TABLESPACE {name}{owner} "
        f"LOCATION '{directory}'{with_clause};"
    )


def _resolve_case(
    case: CreateTablespaceFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    missing = _object_missing(a)

    setup: list[str] = []
    locus = "target.create_tablespace"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    name = _tablespace_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"
    if (
        a.get("owner_clause", "omitted") == "specified_new_owner"
        and a.get("owner_name_shape", "simple_id")
        != "nonexistent_role"
    ):
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        locus = "fixture.owner_role"

    # --- conflicting tablespace for duplicate ------------------------
    if (
        a.get("object_state", "not_exists") == "exists"
        and a.get("tablespace_name_shape", "simple_id")
        == "duplicate_name"
    ):
        setup_dir = f"{_TEST_DIR_ROOT}/{p}setup_dir"
        setup.append(
            f"CREATE TABLESPACE {name} "
            f"LOCATION '{setup_dir}';"
        )
        locus = "fixture.duplicate_tablespace"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, name)

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
    shape = a.get("tablespace_name_shape", "simple_id")
    tablespace_drops: list[str] = []
    # Always drop valid tablespace names; skip invalid/reserved names
    # that PostgreSQL would reject even in a DROP statement.
    if shape not in ("invalid_name", "pg_prefix_reserved"):
        tablespace_drops.append(name)

    ts_drops = [
        f"DROP TABLESPACE IF EXISTS {n};"
        for n in tablespace_drops
    ]

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    pre_cleanup: list[str] = []
    pre_cleanup.extend(ts_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(ts_drops)
    cleanup.extend(role_drops)
    if not cleanup:
        cleanup.append(
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


def resolve_create_tablespace_factor_witness(
    case: CreateTablespaceFactorCase
    | CreateTablespaceFactorExtensionCase,
    repository_root: Path,
) -> CreateTablespaceFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateTablespaceFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_tablespace(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+TABLESPACE\b", region
        )
    )


def _header(case: CreateTablespaceFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE TABLESPACE {case.factor_key}="
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


def render_create_tablespace_factor_case(
    case: CreateTablespaceFactorCase
    | CreateTablespaceFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE TABLESPACE。")
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
    case: CreateTablespaceFactorCase
    | CreateTablespaceFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_tablespace_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_tablespace_factor_programs(
    baseline_plan: object,
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
    "CreateTablespaceFactorRenderError",
    "CreateTablespaceFactorWitness",
    "count_primary_create_tablespace",
    "generate_create_tablespace_factor_programs",
    "render_create_tablespace_factor_case",
    "resolve_create_tablespace_factor_witness",
]
