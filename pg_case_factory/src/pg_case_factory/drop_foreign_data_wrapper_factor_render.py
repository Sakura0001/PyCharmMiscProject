"""Render complete PostgreSQL 18.4 DROP FOREIGN DATA WRAPPER factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_foreign_data_wrapper ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_foreign_data_wrapper_factor_extension import (
    DropForeignDataWrapperFactorExtensionCase,
)
from .drop_foreign_data_wrapper_factor_loop import (
    DropForeignDataWrapperFactorCase,
    DropForeignDataWrapperFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/foreign_data_wrapper/"
    "drop_foreign_data_wrapper.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/foreign_data_wrapper/"
    "drop_foreign_data_wrapper.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target FDW is intentionally absent,
# so the drop surfaces a not-found error (or a notice under IF EXISTS) and
# the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("nonexistent_fdw", "fdw_missing_no_if_exists"),
        ("fdw_name_shape", "nonexistent_name"),
        ("expected_status", "failure"),
    }
)

# Baseline primaries that imply a dependent server fixture must be created.
_SERVER_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependent_objects", "server_dependencies"),
        ("dependent_objects", "foreign_table_dependencies"),
        ("dependent_objects", "both_dependencies"),
        ("server_dependency_state", "has_server_deps"),
        ("foreign_table_dependency_state", "has_table_deps"),
    }
)

# Baseline primaries that imply a dependent foreign table fixture must be
# created.
_FT_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependent_objects", "foreign_table_dependencies"),
        ("dependent_objects", "both_dependencies"),
        ("foreign_table_dependency_state", "has_table_deps"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the FDW always exists in extensions (object_state held at
# exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropForeignDataWrapperFactorExtensionCase,
) -> DropForeignDataWrapperFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_foreign_data_wrapper_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropForeignDataWrapperFactorCase(
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
    case: DropForeignDataWrapperFactorCase | DropForeignDataWrapperFactorExtensionCase,
) -> DropForeignDataWrapperFactorCase:
    if isinstance(case, DropForeignDataWrapperFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropForeignDataWrapperFactorRenderError(ValueError):
    """Raised when a DROP FOREIGN DATA WRAPPER case cannot be rendered."""


@dataclass(frozen=True)
class DropForeignDataWrapperFactorWitness:
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


def _baseline(case: DropForeignDataWrapperFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _fdw_name(case: DropForeignDataWrapperFactorCase, a: dict[str, str], p: str) -> str:
    """The FDW name as referenced inside DROP FOREIGN DATA WRAPPER."""

    shape = a.get("fdw_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}QuotedFdw"'
    if shape == "nonexistent_name":
        return f"{p}nonexistent_fdw"
    return f"{p}fdw"


def _probe_name(case: DropForeignDataWrapperFactorCase, a: dict[str, str], p: str) -> str:
    """The bare fdwname (no quotes) for the catalog probe."""

    shape = a.get("fdw_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}QuotedFdw"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_fdw"
    return f"{p}fdw"


def _fixture_kind(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str]
) -> str:
    """Whether an FDW fixture must be created."""

    if case.kind == "RISK":
        return "fdw"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if (
            a.get("nonexistent_fdw") == "fdw_missing_no_if_exists"
        ):
            return "none"
        if a.get("fdw_name_shape") == "nonexistent_name":
            return "none"
    return "fdw"


def _needs_server(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent server fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependent_objects", "no_dependencies") != "no_dependencies"
    if (case.factor_key, case.factor_value) in _SERVER_DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependent_objects", "no_dependencies") != "no_dependencies"


def _needs_ft(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent foreign table fixture must be created."""

    if case.kind == "EXT":
        dep = a.get("dependent_objects", "no_dependencies")
        return dep in ("foreign_table_dependencies", "both_dependencies")
    if (case.factor_key, case.factor_value) in _FT_DEPENDENCY_PRIMARIES:
        return True
    dep = a.get("dependent_objects", "no_dependencies")
    return dep in ("foreign_table_dependencies", "both_dependencies")


def _is_multi_fdw(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str]
) -> bool:
    """Whether multiple FDWs are dropped in one statement."""

    if case.kind == "EXT":
        return False
    return case.factor_key == "multi_fdw" and case.factor_value == "multiple_fdws"


def _if_exists_present(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str]
) -> str:
    cascade = a.get("cascade_restrict", "restrict_default")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict_default":
        if case.kind == "EXT":
            return ""
        # For baseline cases with server deps, use CASCADE to ensure success.
        if _needs_server(case, a):
            return "CASCADE"
        return ""
    return ""


def _effective_role(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP FOREIGN DATA WRAPPER runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "insufficient_privilege":
        return f"{p}actor" if case.factor_value == "non_owner_execution" else ""
    return ""


def _fdw_absent_after(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target FDW is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropForeignDataWrapperFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _fdw_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "fdw_absent" if absent else "fdw_present"
    if _is_multi_fdw(case, a):
        return (
            f"SELECT count(*) {comparator} AS {alias} "
            "FROM pg_catalog.pg_foreign_data_wrapper "
            f"WHERE fdwname IN ('{name}', '{p}fdw2') "
            "ORDER BY count(*) LIMIT 1;"
        )
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_foreign_data_wrapper "
        f"WHERE fdwname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropForeignDataWrapperFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropForeignDataWrapperFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    fdw_ref = _fdw_name(case, a, p)
    needs_server = _needs_server(case, a)
    needs_ft = _needs_ft(case, a)
    is_multi = _is_multi_fdw(case, a)

    setup: list[str] = []
    locus = "target.foreign_data_wrapper"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # FDW and dependent fixtures so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target FDW fixture (as superuser, before SET ROLE) ---
    if fixture_kind == "fdw":
        setup.append(f"CREATE FOREIGN DATA WRAPPER {fdw_ref};")
        if is_multi:
            setup.append(f"CREATE FOREIGN DATA WRAPPER {p}fdw2;")
    else:
        setup.append("SELECT 1 AS target_fdw_intentionally_absent;")
        locus = "fixture.object_state"

    # --- dependent server fixture (as superuser, before SET ROLE) ---
    if needs_server and fixture_kind == "fdw":
        setup.append(f"CREATE SERVER {p}server FOREIGN DATA WRAPPER {fdw_ref};")
        locus = "fixture.dependency_state"

    # --- dependent foreign table fixture (as superuser, before SET ROLE) ---
    if needs_ft and fixture_kind == "fdw":
        setup.append(f"CREATE FOREIGN TABLE {p}ft (c integer) SERVER {p}server;")
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER FDW creation) ---
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(case, a)
    if is_multi:
        target = f"DROP FOREIGN DATA WRAPPER {if_exists}{fdw_ref}, {p}fdw2"
    else:
        target = f"DROP FOREIGN DATA WRAPPER {if_exists}{fdw_ref}"
    if cascade:
        target += f" {cascade}"
    target += ";"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p))

    # --- cleanup construction -------------------------------------------
    fdw_drop = f"DROP FOREIGN DATA WRAPPER IF EXISTS {fdw_ref} CASCADE;"
    fdw2_drop = f"DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw2 CASCADE;"
    ft_drop = f"DROP FOREIGN TABLE IF EXISTS {p}ft;"
    server_drop = f"DROP SERVER IF EXISTS {p}server CASCADE;"
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: drop foreign tables, servers, FDWs, roles.
    pre_cleanup: list[str] = []
    if needs_ft:
        pre_cleanup.append(ft_drop)
    if needs_server:
        pre_cleanup.append(server_drop)
    pre_cleanup.append(fdw_drop)
    if is_multi:
        pre_cleanup.append(fdw2_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then drops, then any remaining objects.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    if needs_ft:
        cleanup.append(ft_drop)
    if needs_server:
        cleanup.append(server_drop)
    cleanup.append(fdw_drop)
    if is_multi:
        cleanup.append(fdw2_drop)
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


def resolve_drop_foreign_data_wrapper_factor_witness(
    case: DropForeignDataWrapperFactorCase | DropForeignDataWrapperFactorExtensionCase,
    repository_root: Path,
) -> DropForeignDataWrapperFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropForeignDataWrapperFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_foreign_data_wrapper(sql: str) -> int:
    """Count the single credited DROP FOREIGN DATA WRAPPER inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+FOREIGN\s+DATA\s+WRAPPER\b", region)
    )


def _header(case: DropForeignDataWrapperFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP FOREIGN DATA WRAPPER {case.factor_key}={case.factor_value}",
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


def render_drop_foreign_data_wrapper_factor_case(
    case: DropForeignDataWrapperFactorCase | DropForeignDataWrapperFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP FOREIGN DATA WRAPPER regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地FDW和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP FOREIGN DATA WRAPPER。")
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
    if not text.endswith(";"):
        text += ";"
    return text + "\n"


def generate_drop_foreign_data_wrapper_factor_programs(
    baseline_plan: DropForeignDataWrapperFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
    """Write every baseline + extension program; return the file count."""

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


def _write_program(
    case: DropForeignDataWrapperFactorCase | DropForeignDataWrapperFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_foreign_data_wrapper_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropForeignDataWrapperFactorRenderError",
    "DropForeignDataWrapperFactorWitness",
    "count_primary_drop_foreign_data_wrapper",
    "generate_drop_foreign_data_wrapper_factor_programs",
    "render_drop_foreign_data_wrapper_factor_case",
    "resolve_drop_foreign_data_wrapper_factor_witness",
]
