"""Render complete PostgreSQL 18.4 ALTER LARGE OBJECT factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_largeobject_metadata ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.

The owner-transfer mechanics (SESSION_USER/special-token owner targets,
RESET-ROLE before the catalog-audit oracle, idempotent cleanup) are salvaged
verbatim from ``alter_language_factor_render`` (commit 6b576686), because
``ALTER LARGE OBJECT`` is the same owner-transfer NON-TABLE shape with a
single ``OWNER TO`` branch instead of two.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_large_object_factor_extension import (
    AlterLargeObjectFactorExtensionCase,
)
from .alter_large_object_factor_loop import (
    AlterLargeObjectFactorCase,
    AlterLargeObjectFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/large_object/"
    "alter_large_object.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/large_object/"
    "alter_large_object.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_OWNER = "branch_owner"

# Deterministic large-object OID ranges.  The fixture creates a large object
# at the valid OID (created by the superuser); the nonexistent-OID shape
# references a distinct, never-created bogus OID so the target surfaces a
# not-found error while the fixture LO is still cleaned up.  Both ranges sit
# well above FirstNormalObjectId and below the int4 ceiling; the DB doublerun
# fork confirms they are unused on the isolated cluster.
_VALID_OID_BASE = 2000000
_BOGUS_OID_BASE = 4000000

# Primary (factor, value) pairs where the fixture intentionally creates NO
# large object, so the alter surfaces a not-found error and the oracle asserts
# absence of the valid OID (which was never created).
_NO_FIXTURE_PRIMARIES = frozenset(
    {
        ("target_object_state", "missing"),
        ("expected_status", "failure"),
    }
)

# Primary (factor, value) pairs where the oracle must assert ABSENCE.  This
# adds the nonexistent-OID shape (the bogus OID is never created) to the
# no-fixture set above.
_ABSENT_PROBE_PRIMARIES = frozenset(
    {
        ("target_object_state", "missing"),
        ("expected_status", "failure"),
        ("oid_shape", "nonexistent_oid"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be the factor the branch's success probe depends on.
_BRANCH_OWNER_SUCCESS_KEY = "new_owner_shape"
_BRANCH_NEUTRAL_SUCCESS = ("target_object_state", "exists")


def _synthetic_case(
    ext: AlterLargeObjectFactorExtensionCase,
) -> AlterLargeObjectFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case.

    The v1 helpers are primary-driven (they read ``case.factor_key`` /
    ``case.factor_value``), so an extension case is rendered by constructing a
    synthetic :class:`AlterLargeObjectFactorCase` whose primary is the
    extension's single attributable failure pair (for failures) or the
    branch's success primary (for successes), with ``kind = "EXT"`` so the
    patched helpers (_effective_role) read the crossed privilege axis from the
    assignment instead of the primary.  Baseline cases (kind in GRM/SFV/RISK)
    are never routed through here, so their bytes are untouched.
    """

    from .alter_large_object_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    branch = assignment["grammar_branch"]
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif branch == _BRANCH_OWNER and ext.outcome == "success":
        factor_key = _BRANCH_OWNER_SUCCESS_KEY
        factor_value = assignment["new_owner_shape"]
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return AlterLargeObjectFactorCase(
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
    case: AlterLargeObjectFactorCase | AlterLargeObjectFactorExtensionCase,
) -> AlterLargeObjectFactorCase:
    """Return the case to feed to the v1 helpers: unchanged for baseline,
    or a byte-safe synthetic for an extension case."""

    if isinstance(case, AlterLargeObjectFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterLargeObjectFactorRenderError(ValueError):
    """Raised when an ALTER LARGE OBJECT case cannot be rendered."""


@dataclass(frozen=True)
class AlterLargeObjectFactorWitness:
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


def _baseline(case: AlterLargeObjectFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _valid_oid(case: AlterLargeObjectFactorCase) -> int:
    """The OID the fixture creates (and the cleanup unlinks)."""

    return _VALID_OID_BASE + case.ordinal


def _bogus_oid(case: AlterLargeObjectFactorCase) -> int:
    """A never-created OID referenced only by the nonexistent-OID shape."""

    return _BOGUS_OID_BASE + case.ordinal


def _target_oid(case: AlterLargeObjectFactorCase, a: dict[str, str]) -> int:
    """The OID referenced inside ALTER LARGE OBJECT."""

    if a.get("oid_shape") == "nonexistent_oid":
        return _bogus_oid(case)
    return _valid_oid(case)


def _probe_oid(case: AlterLargeObjectFactorCase, a: dict[str, str]) -> int:
    """The OID the catalog-audit oracle queries (== target OID)."""

    return _target_oid(case, a)


def _owner_target(
    case: AlterLargeObjectFactorCase, a: dict[str, str], p: str
) -> str:
    if case.factor_key == "new_owner_shape":
        value = case.factor_value
    else:
        value = a.get("new_owner_shape", "plain_role")
    if value in ("CURRENT_ROLE", "current_role"):
        return "CURRENT_ROLE"
    if value in ("CURRENT_USER", "current_user"):
        return "CURRENT_USER"
    if value in ("SESSION_USER", "session_user"):
        return "SESSION_USER"
    if value == "missing_role":
        return f"{p}nonexistent_role"
    return f"{p}new_owner"


def _effective_role(
    case: AlterLargeObjectFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target ALTER LARGE OBJECT runs."""

    # Extension cases carry the privilege level as a crossed axis in `a`, not
    # as the primary, so read it directly.  Baseline cases (kind in
    # GRM/SFV/RISK) fall through to the primary-driven logic below unchanged.
    if case.kind == "EXT":
        level = a.get("privilege_context", "owner")
        if level in ("non_owner", "insufficient_privilege"):
            return f"{p}actor"
        return ""  # superuser / owner

    primary = (case.factor_key, case.factor_value)
    if case.factor_key == "privilege_context":
        if case.factor_value in ("non_owner", "insufficient_privilege"):
            return f"{p}actor"
        return ""
    if case.factor_key == "ownership_boundary":
        if case.factor_value == "non_owner":
            return f"{p}actor"
        return ""
    if primary in _NO_FIXTURE_PRIMARIES:
        return ""
    return ""


def _is_absent_probe(case: AlterLargeObjectFactorCase) -> bool:
    if case.kind == "RISK":
        return False
    return (case.factor_key, case.factor_value) in _ABSENT_PROBE_PRIMARIES


def _probe_select(
    case: AlterLargeObjectFactorCase, a: dict[str, str], p: str
) -> str:
    mode = a.get("verification_mode", "catalog_query")
    if case.factor_key == "verification_mode":
        mode = case.factor_value
    oid = _probe_oid(case, a)
    absent = _is_absent_probe(case)
    if (
        mode == "effect_query"
        and not absent
        and case.outcome == "success"
    ):
        owner = _owner_target(case, a, p)
        if owner in ("CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"):
            role_filter = f"r.rolname = {owner.lower()}"
        else:
            role_filter = f"r.rolname = '{owner}'"
        return (
            "SELECT count(*) > 0 AS owner_is_target "
            "FROM pg_catalog.pg_largeobject_metadata AS m "
            "JOIN pg_catalog.pg_roles AS r ON m.lomowner = r.oid "
            f"WHERE m.oid = {oid} AND {role_filter} "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "error_assertion":
        comparator = "= 0" if absent else "> 0"
        alias = "large_object_absent" if absent else "large_object_present"
        return (
            f"SELECT count(*) {comparator} AS {alias} "
            "FROM pg_catalog.pg_largeobject_metadata "
            f"WHERE oid = {oid} ORDER BY count(*) LIMIT 1;"
        )
    comparator = "= 0" if absent else "> 0"
    alias = "large_object_absent" if absent else "large_object_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_largeobject_metadata "
        f"WHERE oid = {oid} ORDER BY count(*) LIMIT 1;"
    )


def _fixture_kind(case: AlterLargeObjectFactorCase) -> str:
    if (case.factor_key, case.factor_value) in _NO_FIXTURE_PRIMARIES:
        return "none"
    return "large_object"


def _invalid_combination_primary(
    case: AlterLargeObjectFactorCase,
) -> bool:
    """The primary is an invalid-combination boundary (not ``none``).

    ALTER LARGE OBJECT has a single legal action form (``OWNER TO``); a
    duplicate ``OWNER TO`` clause in one statement is a syntax error (42601),
    which is the only way the matrix's declared
    ``invalid_large_object_alter_combination`` boundary is reachable in PG
    18.4.
    """

    return (
        case.factor_key == "invalid_combination"
        and case.factor_value != "none"
    )


def _role_names(
    case: AlterLargeObjectFactorCase,
    a: dict[str, str],
    p: str,
    effective: str,
) -> tuple[str, ...]:
    """Roles to tear down, ordered grantees before the new-owner role.

    The cluster superuser owns every fixture large object (lo_create needs
    superuser for a specific OID), so there is no separate fixture-owner role
    to drop; only the non-superuser actor (privilege boundary), the
    owner-transfer new-owner role, and the invalid-combination owner-target
    role are created and torn down.
    """

    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    if _invalid_combination_primary(case):
        roles.append(f"{p}icmb_owner")
    if _owner_target(case, a, p) == f"{p}new_owner":
        roles.append(f"{p}new_owner")
    return tuple(roles)


def _resolve_case(case: AlterLargeObjectFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case)
    valid = _valid_oid(case)

    setup: list[str] = []
    locus = "target.large_object"

    # --- role fixtures -------------------------------------------------
    effective = _effective_role(case, a, p)
    invalid_combo = _invalid_combination_primary(case)
    owner = _owner_target(case, a, p)
    if owner == f"{p}new_owner":
        setup.append(f"CREATE ROLE {p}new_owner LOGIN;")
    if invalid_combo:
        # The duplicate OWNER-TO clause needs an owner-target role so the
        # statement is a complete (but invalid) combination that parses far
        # enough to raise 42601.
        setup.append(f"CREATE ROLE {p}icmb_owner LOGIN;")
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN;")

    # --- the target large-object fixture ------------------------------
    # lo_create with a specific OID needs superuser, so the cluster superuser
    # creates the large object before any SET ROLE arms a non-superuser
    # actor.  (DB fork calibrates the privilege fixture for a real
    # non-superuser owner; the no-DB phase only needs deterministic bytes.)
    if fixture_kind == "large_object":
        setup.append(f"SELECT lo_create({valid});")
    else:
        # No large object is created: the target is expected to fail because
        # the referenced OID does not exist.  Emit a deterministic probe so
        # the program still carries an observable setup locus.
        setup.append("SELECT 1 AS target_large_object_intentionally_absent;")
        locus = "fixture.object_state"

    # --- arm the effective role (superuser is the default) -------------
    if effective:
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the primary target statement ---------------------------------
    target_oid = _target_oid(case, a)
    if invalid_combo:
        # A duplicate OWNER-TO clause is a syntax error (42601): the only
        # reachable form of the invalid_combination boundary.
        target = (
            f"ALTER LARGE OBJECT {target_oid} OWNER TO {owner} "
            f"OWNER TO {p}icmb_owner;"
        )
        locus = "fixture.invalid_combination"
    else:
        target = (
            f"ALTER LARGE OBJECT {target_oid} OWNER TO {owner};"
        )

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    # Reset to superuser before the catalog-audit oracle so it runs with full
    # visibility (privilege_context/ownership_boundary cases SET ROLE in setup).
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

    # --- cleanup construction ------------------------------------------
    drop_mode = a.get("cleanup_mode", "drop_objects")
    if case.factor_key == "cleanup_mode":
        drop_mode = case.factor_value
    # Large-object unlink is always idempotent: lo_unlink is only invoked for
    # rows that exist in pg_largeobject_metadata, so the pre-cleanup (section
    # 1, which runs under ON_ERROR_STOP) never aborts on an absent or
    # already-dropped large object.  cleanup_mode distinguishes the two modes
    # by CASCADE only on the role drops: drop_objects cascades dependents,
    # reset_state drops bare.
    cascade = "" if drop_mode == "reset_state" else " CASCADE"
    roles = _role_names(case, a, p, effective)

    object_drops = [
        f"SELECT lo_unlink(oid) FROM pg_catalog.pg_largeobject_metadata "
        f"WHERE oid = {valid} ORDER BY oid;"
    ]
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role}{cascade};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    pre_cleanup: list[str] = []
    pre_cleanup.extend(object_drops)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(object_drops)
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


def resolve_alter_large_object_factor_witness(
    case: AlterLargeObjectFactorCase | AlterLargeObjectFactorExtensionCase,
    repository_root: Path,
) -> AlterLargeObjectFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterLargeObjectFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_large_object(sql: str) -> int:
    """Count the single credited ALTER LARGE OBJECT inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+LARGE\s+OBJECT\b", region))


def _header(case: AlterLargeObjectFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER LARGE OBJECT {case.factor_key}={case.factor_value}",
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


def render_alter_large_object_factor_case(
    case: AlterLargeObjectFactorCase | AlterLargeObjectFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER LARGE OBJECT regress program.

    Baseline cases (kind in GRM/SFV/RISK) are rendered by the v1 path
    unchanged; extension cases are rendered via a byte-safe synthetic
    baseline-shaped case (see :func:`_as_render_case`).  ``repository_root``
    is accepted for API symmetry with the sibling statement renderers.
    """

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地大对象和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER LARGE OBJECT。")
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


def generate_alter_large_object_factor_programs(
    baseline_plan: AlterLargeObjectFactorLoopPlan,
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
    case: AlterLargeObjectFactorCase | AlterLargeObjectFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_large_object_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterLargeObjectFactorRenderError",
    "AlterLargeObjectFactorWitness",
    "count_primary_alter_large_object",
    "generate_alter_large_object_factor_programs",
    "render_alter_large_object_factor_case",
    "resolve_alter_large_object_factor_witness",
]
