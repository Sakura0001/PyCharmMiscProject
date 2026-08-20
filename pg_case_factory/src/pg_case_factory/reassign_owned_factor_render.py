"""Render complete PostgreSQL 18.4 REASSIGN OWNED factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.  The ownership-transfer probe joins
``pg_class.relowner`` (an OID column) to ``pg_roles.oid`` and filters by
``pg_roles.rolname``, matching the verified PG 18.4 catalog schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .reassign_owned_factor_extension import (
    ReassignOwnedFactorExtensionCase,
)
from .reassign_owned_factor_loop import (
    ReassignOwnedFactorCase,
    ReassignOwnedFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/ownership/"
    "reassign_owned.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/ownership/"
    "reassign_owned.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where a referenced role is intentionally
# absent, so the reassign surfaces a not-found error and the oracle asserts
# the ownership did not transfer.
_ABSENT_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("old_role_identity", "role_not_exists"),
        ("new_role_identity", "role_not_exists"),
        ("nonexistent_old_role", "old_role_does_not_exist"),
        ("nonexistent_new_role", "new_role_does_not_exist"),
        ("role_name_shape", "non_existing_name"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the roles always exist in extensions.
_BRANCH_NEUTRAL_SUCCESS = ("owned_objects_state", "owns_tables")


def _synthetic_case(
    ext: ReassignOwnedFactorExtensionCase,
) -> ReassignOwnedFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .reassign_owned_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return ReassignOwnedFactorCase(
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
    case: ReassignOwnedFactorCase | ReassignOwnedFactorExtensionCase,
) -> ReassignOwnedFactorCase:
    if isinstance(case, ReassignOwnedFactorExtensionCase):
        return _synthetic_case(case)
    return case


class ReassignOwnedFactorRenderError(ValueError):
    """Raised when a REASSIGN OWNED case cannot be rendered."""


@dataclass(frozen=True)
class ReassignOwnedFactorWitness:
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


def _baseline(case: ReassignOwnedFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _explicit_name(a: dict[str, str], p: str, which: str) -> str:
    """The explicit role name for the ``which`` ('old'/'new') role.

    ``quoted_identifier`` (when not ``unquoted``) takes precedence over
    ``role_name_shape`` because it is the dedicated quoting factor.  The
    fixture role (CREATE ROLE) and the probe (pg_roles.rolname) use the same
    name so the catalog audit is self-consistent.
    """

    base = f"{p}{which}"
    qi = a.get("quoted_identifier", "unquoted")
    rns = a.get("role_name_shape", "simple_name")
    if qi == "double_quoted":
        return f'"{base}"'
    if qi == "mixed_case_quoted":
        return f'"{base}Mix"'
    if rns == "quoted_name":
        return f'"{base}q"'
    if rns == "reserved_word_name":
        return '"user"'
    if rns == "case_sensitive_name":
        return f'"{base}cs"'
    if rns == "non_existing_name":
        return f"{base}nope"
    return base


def _role_ref(a: dict[str, str], p: str, which: str) -> str:
    """The role reference as it appears inside REASSIGN OWNED.

    ``which`` is 'old' (the ``BY`` role) or 'new' (the ``TO`` role).  Keyword
    shapes resolve to the session-identity keywords; explicit shapes resolve
    to the shaped name from :func:`_explicit_name`.
    """

    shape = a.get(f"{which}_role_shape", "explicit_role_name")
    if shape == "current_role_keyword":
        return "CURRENT_ROLE"
    if shape == "current_user_keyword":
        return "CURRENT_USER"
    if shape == "session_user_keyword":
        return "SESSION_USER"
    return _explicit_name(a, p, which)


def _fixture_role_name(a: dict[str, str], p: str, which: str) -> str:
    """The role name for CREATE ROLE.

    Keyword shapes use the plain base name (the keyword is satisfied by a
    prior ``SET ROLE``).  Explicit shapes use the shaped name so the created
    role matches the target reference.
    """

    shape = a.get(f"{which}_role_shape", "explicit_role_name")
    if shape != "explicit_role_name":
        return f"{p}{which}"
    return _explicit_name(a, p, which)


def _fixture_kind(
    case: ReassignOwnedFactorCase, a: dict[str, str]
) -> str:
    """Whether the role/table fixture must be created."""

    if case.kind == "RISK":
        return "role_with_table"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a.get("old_role_identity") == "role_not_exists":
            return "none"
        if a.get("new_role_identity") == "role_not_exists":
            return "none"
        if a.get("role_name_shape") == "non_existing_name":
            return "none"
    return "role_with_table"


def _needs_table(
    case: ReassignOwnedFactorCase, a: dict[str, str]
) -> bool:
    """Whether a table fixture must be created."""

    if case.kind == "RISK":
        return True
    if _fixture_kind(case, a) == "none":
        return False
    if case.kind == "EXT":
        return True
    state = a.get("owned_objects_state", "owns_no_objects")
    if state in ("owns_tables", "owns_multiple_objects"):
        return True
    return False


def _needs_second_object(
    case: ReassignOwnedFactorCase, a: dict[str, str]
) -> bool:
    """Whether a second owned object (view) must be created."""

    if _fixture_kind(case, a) == "none":
        return False
    if case.kind == "EXT":
        return a.get("owned_objects_state") == "owns_multiple_objects"
    return a.get("owned_objects_state") == "owns_multiple_objects"


def _effective_role(
    case: ReassignOwnedFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target REASSIGN OWNED runs."""

    if case.kind == "EXT":
        priv = a.get("executor_privilege", "superuser")
        return f"{p}executor" if priv == "normal_user_no_privilege" else ""
    if case.factor_key == "executor_privilege":
        return (
            f"{p}executor"
            if case.factor_value == "normal_user_no_privilege"
            else ""
        )
    if case.factor_key == "privilege_insufficient":
        return (
            f"{p}executor"
            if case.factor_value in (
                "non_superuser_reassigning_other_role",
                "no_createrole_privilege",
            )
            else ""
        )
    return ""


def _needs_role_switch(
    case: ReassignOwnedFactorCase, a: dict[str, str], effective: str
) -> bool:
    """Whether SET ROLE is needed (for keyword shapes or privilege tests)."""

    if effective:
        return True
    if case.kind != "RISK":
        old_shape = a.get("old_role_shape", "explicit_role_name")
        new_shape = a.get("new_role_shape", "explicit_role_name")
        if (old_shape != "explicit_role_name"
                or new_shape != "explicit_role_name"):
            if _fixture_kind(case, a) != "none":
                return True
    return False


def _ownership_transferred(
    case: ReassignOwnedFactorCase, a: dict[str, str]
) -> bool:
    """Whether ownership transfers to the new role AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return False
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: ReassignOwnedFactorCase, a: dict[str, str], p: str
) -> str:
    vm = a.get("verification_mode", "pg_class_owner_query")
    transferred = _ownership_transferred(case, a)
    if vm == "error_assertion":
        return "SELECT 1 AS error_assertion_oracle;"
    if vm == "pg_roles_catalog_query":
        role_present = _fixture_kind(case, a) != "none"
        if role_present:
            comparator = "> 0"
            alias = "role_present"
        else:
            comparator = "= 0"
            alias = "role_absent"
        old_name = _fixture_role_name(a, p, "old")
        return (
            f"SELECT count(*) {comparator} AS {alias} "
            "FROM pg_catalog.pg_roles "
            f"WHERE rolname = '{old_name}' ORDER BY count(*) LIMIT 1;"
        )
    comparator = "> 0" if transferred else "= 0"
    alias = "ownership_transferred" if transferred else "ownership_not_transferred"
    new_name = _fixture_role_name(a, p, "new")
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_class AS c "
        "JOIN pg_catalog.pg_roles AS r ON c.relowner = r.oid "
        f"WHERE c.relname = '{p}t' AND r.rolname = '{new_name}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: ReassignOwnedFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}executor":
        roles.append(f"{p}executor")
    return tuple(roles)


def _resolve_case(case: ReassignOwnedFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    old_ref = _role_ref(a, p, "old")
    new_ref = _role_ref(a, p, "new")
    old_fixture = _fixture_role_name(a, p, "old")
    new_fixture = _fixture_role_name(a, p, "new")
    needs_table = _needs_table(case, a)
    needs_second = _needs_second_object(case, a)
    multi = a.get("multi_old_role", "single_old_role")

    setup: list[str] = []
    locus = "target.reassign_owned"

    # --- role fixture (CREATE only; SET ROLE deferred) ----------------
    effective = _effective_role(case, a, p)
    if fixture_kind != "none":
        setup.append(f"CREATE ROLE {old_fixture} LOGIN;")
        if multi == "multiple_old_roles":
            setup.append(f"CREATE ROLE {p}old2 LOGIN;")
        setup.append(f"CREATE ROLE {new_fixture} LOGIN;")
        locus = "fixture.role_state"

    # --- table fixture (as superuser, before SET ROLE) -----------------
    if needs_table:
        setup.append(f"CREATE TABLE {p}t (c integer);")
        setup.append(f"ALTER TABLE {p}t OWNER TO {old_fixture};")
        locus = "fixture.owned_objects_state"

    # --- second owned object (for owns_multiple_objects) -------------
    if needs_second:
        setup.append(f"CREATE VIEW {p}v2 AS SELECT * FROM {p}t;")
        setup.append(f"ALTER VIEW {p}v2 OWNER TO {old_fixture};")
        locus = "fixture.owned_objects_state"

    # --- arm the executor role (AFTER fixture creation) --------------
    if effective:
        setup.append(f"CREATE ROLE {p}executor LOGIN NOSUPERUSER;")
        setup.append(f"SET ROLE {p}executor;")
    elif _needs_role_switch(case, a, effective):
        setup.append(f"SET ROLE {new_fixture};")

    target = f"REASSIGN OWNED BY {old_ref}"
    if multi == "multiple_old_roles":
        target += f", {p}old2"
    target += f" TO {new_ref};"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective or _needs_role_switch(case, a, effective):
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
    table_drop = f"DROP TABLE IF EXISTS {p}t CASCADE;"
    view_drops: list[str] = []
    if needs_second:
        view_drops.append(f"DROP VIEW IF EXISTS {p}v2;")
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]
    if fixture_kind != "none":
        role_drops.extend(
            [
                f"DROP OWNED BY {old_fixture};",
                f"DROP OWNED BY {new_fixture};",
                f"DROP ROLE IF EXISTS {old_fixture};",
                f"DROP ROLE IF EXISTS {new_fixture};",
            ]
        )
        if multi == "multiple_old_roles":
            role_drops.extend(
                [
                    f"DROP OWNED BY {p}old2;",
                    f"DROP ROLE IF EXISTS {p}old2;",
                ]
            )

    # Pre-cleanup: DROP TABLE first (bookend gate), then views, then roles.
    pre_cleanup: list[str] = []
    if needs_table:
        pre_cleanup.append(table_drop)
    pre_cleanup.extend(view_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: views, roles, then DROP TABLE last (bookend gate).
    cleanup: list[str] = []
    if effective or _needs_role_switch(case, a, effective):
        cleanup.append("RESET ROLE;")
    cleanup.extend(view_drops)
    cleanup.extend(role_drops)
    if needs_table:
        cleanup.append(table_drop)
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


def resolve_reassign_owned_factor_witness(
    case: ReassignOwnedFactorCase | ReassignOwnedFactorExtensionCase,
    repository_root: Path,
) -> ReassignOwnedFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return ReassignOwnedFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_reassign_owned(sql: str) -> int:
    """Count the single credited REASSIGN OWNED inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*REASSIGN\s+OWNED\b", region)
    )


def _header(case: ReassignOwnedFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : REASSIGN OWNED {case.factor_key}={case.factor_value}",
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


def render_reassign_owned_factor_case(
    case: ReassignOwnedFactorCase | ReassignOwnedFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic REASSIGN OWNED regress program."""

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
    lines.append("-- 3. 执行唯一获得覆盖信用的 REASSIGN OWNED。")
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


def generate_reassign_owned_factor_programs(
    baseline_plan: ReassignOwnedFactorLoopPlan,
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
    case: ReassignOwnedFactorCase | ReassignOwnedFactorExtensionCase,
    out: Path,
) -> None:
    text = render_reassign_owned_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "ReassignOwnedFactorRenderError",
    "ReassignOwnedFactorWitness",
    "count_primary_reassign_owned",
    "generate_reassign_owned_factor_programs",
    "render_reassign_owned_factor_case",
    "resolve_reassign_owned_factor_witness",
]
