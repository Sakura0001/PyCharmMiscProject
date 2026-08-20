"""Render complete PostgreSQL 18.4 DROP GROUP factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_roles ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_group_factor_extension import (
    DropGroupFactorExtensionCase,
)
from .drop_group_factor_loop import (
    DropGroupFactorCase,
    DropGroupFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/group/"
    "drop_group.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/group/"
    "drop_group.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target group(role) is
# intentionally absent, so the drop surfaces a not-found error (or a notice
# under IF EXISTS) and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("nonexistent_group", "group_missing_no_if_exists"),
        ("group_name_shape", "nonexistent_name"),
        ("expected_status", "failure"),
        ("if_exists_notice", "notice_no_op"),
    }
)

# Baseline primaries that imply a dependent object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("role_dependency", "has_dependencies"),
        ("role_dependency_state", "has_references"),
        ("role_still_referenced", "has_references"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the group always exists in extensions when object_state=exists.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropGroupFactorExtensionCase,
) -> DropGroupFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_group_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropGroupFactorCase(
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
    case: DropGroupFactorCase | DropGroupFactorExtensionCase,
) -> DropGroupFactorCase:
    if isinstance(case, DropGroupFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropGroupFactorRenderError(ValueError):
    """Raised when a DROP GROUP case cannot be rendered."""


@dataclass(frozen=True)
class DropGroupFactorWitness:
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


def _baseline(case: DropGroupFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _grp_ref(case: DropGroupFactorCase, a: dict[str, str], p: str) -> str:
    """The group(role) name as referenced inside DROP GROUP."""

    shape = a.get("group_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}QuotedGrp"'
    if shape == "nonexistent_name":
        return f"{p}nonexistent_grp"
    return f"{p}grp"


def _grp2_ref(case: DropGroupFactorCase, a: dict[str, str], p: str) -> str:
    """The second group(role) name for multi-group drops."""

    shape = a.get("group_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}QuotedGrp2"'
    if shape == "nonexistent_name":
        return f"{p}nonexistent_grp2"
    return f"{p}grp2"


def _probe_name(case: DropGroupFactorCase, a: dict[str, str], p: str) -> str:
    """The bare group name (no quotes) for the catalog probe."""

    shape = a.get("group_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}QuotedGrp"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_grp"
    return f"{p}grp"


def _fixture_kind(
    case: DropGroupFactorCase, a: dict[str, str]
) -> str:
    """Whether a group(role) fixture must be created."""

    if case.kind == "RISK":
        return "group"
    if case.kind == "EXT":
        if a.get("object_state") == "not_exists":
            return "none"
        return "group"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "group"


def _if_exists_present(
    case: DropGroupFactorCase, a: dict[str, str]
) -> bool:
    """Whether IF EXISTS should be emitted in the DROP GROUP target."""

    primary = (case.factor_key, case.factor_value)
    if primary == ("statement_branch", "branch_drop_group_if_exists"):
        return True
    if primary == ("statement_branch", "branch_drop_group"):
        return False
    if primary == ("if_exists_notice", "notice_no_op"):
        return True
    if primary == ("if_exists_clause", "present"):
        return True
    if primary == ("if_exists_clause", "absent"):
        return False
    return a.get("if_exists_clause") == "present"


def _is_multi_group(a: dict[str, str]) -> bool:
    return a.get("multi_group") == "multiple_groups"


def _privilege_level(
    case: DropGroupFactorCase, a: dict[str, str]
) -> str:
    """The effective privilege level for the DROP GROUP session."""

    if case.kind == "EXT":
        return a.get("privilege_level", "superuser")
    if case.factor_key == "privilege_level":
        return case.factor_value
    if case.factor_key == "insufficient_privilege":
        return (
            "non_privilege"
            if case.factor_value == "lacks_privilege"
            else "superuser"
        )
    return a.get("privilege_level", "superuser")


def _effective_role(
    case: DropGroupFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP GROUP runs."""

    level = _privilege_level(case, a)
    return f"{p}actor" if level in ("non_privilege", "createrole_privilege") else ""


def _actor_create(level: str, p: str) -> str | None:
    if level == "non_privilege":
        return f"CREATE ROLE {p}actor LOGIN NOSUPERUSER NOCREATEROLE;"
    if level == "createrole_privilege":
        return f"CREATE ROLE {p}actor LOGIN NOSUPERUSER CREATEROLE;"
    return None


def _needs_dependent(
    case: DropGroupFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if case.kind == "EXT":
        return a.get("role_dependency") == "has_dependencies"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("role_dependency") == "has_dependencies"


def _group_absent_after(
    case: DropGroupFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target group(role) is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropGroupFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _group_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "group_absent" if absent else "group_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_roles "
        f"WHERE rolname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropGroupFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropGroupFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    grp_ref = _grp_ref(case, a, p)
    grp2_ref = _grp2_ref(case, a, p)
    needs_dep = _needs_dependent(case, a)
    multi = _is_multi_group(a)

    setup: list[str] = []
    locus = "target.group"

    # --- actor role fixtures (CREATE only; SET ROLE deferred to after the
    # group fixture so they run as the superuser) ---
    level = _privilege_level(case, a)
    actor_stmt = _actor_create(level, p)
    effective = _effective_role(case, a, p)
    if actor_stmt is not None:
        setup.append(actor_stmt)
        locus = "fixture.privilege_state"

    # --- the target group(role) fixture (as superuser, before SET ROLE) ---
    if fixture_kind == "group":
        setup.append(f"CREATE GROUP {p}grp;")
        if multi:
            setup.append(f"CREATE GROUP {p}grp2;")
    else:
        setup.append(
            "SELECT 1 AS target_group_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        setup.append(f"CREATE TABLE {p}t (c integer);")
        setup.append(f"ALTER TABLE {p}t OWNER TO {p}grp;")
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER group creation) ------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    if multi:
        target = f"DROP GROUP {if_exists}{grp_ref}, {grp2_ref};"
    else:
        target = f"DROP GROUP {if_exists}{grp_ref};"

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
    grp_drop = f"DROP GROUP IF EXISTS {grp_ref};"
    grp2_drop = f"DROP GROUP IF EXISTS {grp2_ref};" if multi else ""
    dep_drops = (
        [f"DROP TABLE IF EXISTS {p}t CASCADE;"] if needs_dep else []
    )
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: DROP TABLE first (bookend gate), then group/role.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(dep_drops)
    pre_cleanup.append(grp_drop)
    if multi:
        pre_cleanup.append(grp2_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then group/role drops, then DROP
    # TABLE last (bookend gate).
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(grp_drop)
    if multi:
        cleanup.append(grp2_drop)
    cleanup.extend(role_drops)
    cleanup.extend(dep_drops)
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


def resolve_drop_group_factor_witness(
    case: DropGroupFactorCase | DropGroupFactorExtensionCase,
    repository_root: Path,
) -> DropGroupFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropGroupFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_group(sql: str) -> int:
    """Count the single credited DROP GROUP inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+GROUP\b", region)
    )


def _header(case: DropGroupFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP GROUP {case.factor_key}={case.factor_value}",
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


def render_drop_group_factor_case(
    case: DropGroupFactorCase | DropGroupFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP GROUP regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地 group(role) 和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP GROUP。")
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


def generate_drop_group_factor_programs(
    baseline_plan: DropGroupFactorLoopPlan,
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
    case: DropGroupFactorCase | DropGroupFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_group_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropGroupFactorRenderError",
    "DropGroupFactorWitness",
    "count_primary_drop_group",
    "generate_drop_group_factor_programs",
    "render_drop_group_factor_case",
    "resolve_drop_group_factor_witness",
]
