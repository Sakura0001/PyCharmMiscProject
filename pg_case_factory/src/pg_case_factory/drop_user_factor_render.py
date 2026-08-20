"""Render complete PostgreSQL 18.4 DROP USER factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_roles WHERE rolname = '...'
ORDER BY count(*) LIMIT 1`` never nests a ``FROM`` inside an ``EXISTS``
subquery, so ``audit_catalog_observability`` accepts it.  The probe column is
the real ``pg_roles.rolname`` (``DROP USER`` is a deprecated alias for
``DROP ROLE``; ``rolname`` is the verified catalog column — a no-DB static
gate cannot catch a wrong column name, so it is pinned exactly).

``DROP USER`` is table-less for bookend purposes: it drops a role, and the
dependent-object (2BP01) fixture uses a VIEW owned by the target role so no
``CREATE TABLE`` ever appears and the bookend gate is N/A.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_user_factor_extension import (
    DropUserFactorExtensionCase,
)
from .drop_user_factor_loop import (
    DropUserFactorCase,
    DropUserFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/user/drop_user.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/user/drop_user.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target role is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_USER_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("role_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
    }
)

# Baseline primaries that imply an owned-object fixture (a VIEW owned by the
# target role) so the DROP surfaces a 2BP01 dependency error.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("role_dependency", "owns_objects"),
        ("dependency_context", "role_owns_objects"),
        ("error_type", "role_owns_objects"),
    }
)

# Baseline primaries that imply an active-session boundary fixture
# (provisional 2BP01; no live session can be armed in a static SQL program).
_ACTIVE_SESSION_PRIMARIES = frozenset(
    {
        ("role_dependency", "has_active_connections"),
        ("dependency_context", "role_has_active_sessions"),
    }
)

# Baseline primaries that imply a non-CREATEROLE executor fixture (42501).
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("authorization_path", "non_createrole"),
        ("privilege_context", "non_createrole_session"),
        ("error_type", "insufficient_privilege"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the role always exists in extensions (object_state held at
# exists) unless object_state=absent / role_name_shape=non_existent_name.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropUserFactorExtensionCase,
) -> DropUserFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_user_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropUserFactorCase(
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
    case: DropUserFactorCase | DropUserFactorExtensionCase,
) -> DropUserFactorCase:
    if isinstance(case, DropUserFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropUserFactorRenderError(ValueError):
    """Raised when a DROP USER case cannot be rendered."""


@dataclass(frozen=True)
class DropUserFactorWitness:
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


def _baseline(case: DropUserFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _role_ref(case: DropUserFactorCase, a: dict[str, str], p: str) -> str:
    """The target role name as referenced inside DROP USER (quoted if needed)."""

    shape = a.get("role_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}qrole"'
    if shape == "reserved_word_id":
        return '"order"'
    if shape == "non_existent_name":
        return f"{p}norole"
    return f"{p}role"


def _role_probe(case: DropUserFactorCase, a: dict[str, str], p: str) -> str:
    """The bare rolname (no quotes) for the catalog probe."""

    shape = a.get("role_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}qrole"
    if shape == "reserved_word_id":
        return "order"
    if shape == "non_existent_name":
        return f"{p}norole"
    return f"{p}role"


def _role_created(case: DropUserFactorCase, a: dict[str, str]) -> bool:
    """Whether a target role fixture must be created."""

    if a.get("object_state") == "absent":
        return False
    if a.get("role_name_shape") == "non_existent_name":
        return False
    return True


def _if_exists_present(case: DropUserFactorCase, a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _multi_user(a: dict[str, str]) -> bool:
    return a.get("multi_user_clause") == "multiple_roles"


def _needs_owned_view(case: DropUserFactorCase, a: dict[str, str]) -> bool:
    """Whether an owned-VIEW fixture must be created (2BP01 dependency)."""

    if case.kind == "EXT":
        return a.get("dependency_context") == "role_owns_objects"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependency_context") == "role_owns_objects"


def _needs_active_session(
    case: DropUserFactorCase, a: dict[str, str]
) -> bool:
    """Whether an active-session boundary marker is needed (provisional)."""

    if case.kind == "EXT":
        return a.get("dependency_context") == "role_has_active_sessions"
    if (case.factor_key, case.factor_value) in _ACTIVE_SESSION_PRIMARIES:
        return True
    return a.get("dependency_context") == "role_has_active_sessions"


def _effective_role(
    case: DropUserFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP USER runs."""

    if case.kind == "EXT":
        level = a.get("authorization_path", "createrole")
        return f"{p}actor" if level == "non_createrole" else ""
    if case.factor_key == "authorization_path":
        return f"{p}actor" if case.factor_value == "non_createrole" else ""
    if case.factor_key == "privilege_context":
        return (
            f"{p}actor"
            if case.factor_value == "non_createrole_session"
            else ""
        )
    if case.factor_key == "error_type":
        return (
            f"{p}actor"
            if case.factor_value == "insufficient_privilege"
            else ""
        )
    return ""


def _role_absent_after(
    case: DropUserFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target role is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _role_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropUserFactorCase, a: dict[str, str], p: str
) -> str:
    role_probe = _role_probe(case, a, p)
    absent = _role_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "user_absent" if absent else "user_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_roles "
        f"WHERE rolname = '{role_probe}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _resolve_case(case: DropUserFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    role_ref = _role_ref(case, a, p)
    role_created = _role_created(case, a)
    needs_view = _needs_owned_view(case, a)
    needs_session = _needs_active_session(case, a)
    multi = _multi_user(a)

    setup: list[str] = []
    locus = "target.role"

    # --- the target role fixture (as superuser, before SET ROLE) ----------
    if role_created:
        setup.append(f"CREATE ROLE {role_ref} LOGIN;")
        locus = "fixture.target_role"

    # --- multi-user secondary role fixture (always a plain id) ------------
    if multi:
        setup.append(f"CREATE ROLE {p}role2 LOGIN;")
        locus = "fixture.multi_user"

    # --- owned-VIEW fixture (VIEW owned by the target role -> 2BP01) ------
    if needs_view:
        setup.append(f"CREATE VIEW {p}ownv AS SELECT 1 AS c;")
        setup.append(f"ALTER VIEW {p}ownv OWNER TO {role_ref};")
        locus = "fixture.dependency_state"

    # --- active-session boundary marker (provisional; no live fixture) ----
    if needs_session:
        setup.append(
            "SELECT 1 AS active_session_boundary_provisional;"
        )
        locus = "fixture.active_session_boundary"

    # --- non-CREATEROLE executor fixture (42501) --------------------------
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER NOCREATEROLE;"
        )
        locus = "fixture.privilege_state"

    # --- arm the non-CREATEROLE executor (AFTER target fixture) ----------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    target = f"DROP USER {if_exists}{role_ref}"
    if multi:
        target += f", {p}role2"
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
    view_drop = (
        [f"DROP VIEW IF EXISTS {p}ownv CASCADE;"] if needs_view else []
    )
    # Always include the target-role DROP (a harmless no-op when the role
    # was intentionally absent) so cleanup is uniform across shapes.
    role_drops: list[str] = [f"DROP ROLE IF EXISTS {role_ref};"]
    if multi:
        role_drops.append(f"DROP ROLE IF EXISTS {p}role2;")
    actor_drops = (
        [f"DROP ROLE IF EXISTS {p}actor;"] if effective else []
    )

    # Pre-cleanup: VIEW first (releases ownership), then roles.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(view_drop)
    pre_cleanup.extend(role_drops)
    pre_cleanup.extend(actor_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then VIEW, then roles.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(view_drop)
    cleanup.extend(role_drops)
    cleanup.extend(actor_drops)
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


def resolve_drop_user_factor_witness(
    case: DropUserFactorCase | DropUserFactorExtensionCase,
    repository_root: Path,
) -> DropUserFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropUserFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_user(sql: str) -> int:
    """Count the single credited DROP USER inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+USER\b", region)
    )


def _header(case: DropUserFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP USER {case.factor_key}={case.factor_value}",
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


def render_drop_user_factor_case(
    case: DropUserFactorCase | DropUserFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP USER regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地角色和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP USER。")
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


def generate_drop_user_factor_programs(
    baseline_plan: DropUserFactorLoopPlan,
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
    case: DropUserFactorCase | DropUserFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_user_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropUserFactorRenderError",
    "DropUserFactorWitness",
    "count_primary_drop_user",
    "generate_drop_user_factor_programs",
    "render_drop_user_factor_case",
    "resolve_drop_user_factor_witness",
]
