"""Render complete PostgreSQL 18.4 ALTER LANGUAGE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_language ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_language_factor_extension import (
    AlterLanguageFactorExtensionCase,
)
from .alter_language_factor_loop import (
    AlterLanguageFactorCase,
    AlterLanguageFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/language/"
    "alter_language.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/language/"
    "alter_language.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"

# Primary (factor, value) pairs where the target language is intentionally
# absent, so the alter surfaces a not-found error and the oracle asserts
# absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("target_object_state", "missing"),
        ("name_shape", "missing_object"),
        ("expected_status", "failure"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be the factor each branch's success probe depends on.
_BRANCH_RENAME_SUCCESS_KEY = "new_name_shape"
_BRANCH_OWNER_SUCCESS_KEY = "new_owner_shape"
_BRANCH_NEUTRAL_SUCCESS = ("target_object_state", "exists")


def _synthetic_case(
    ext: AlterLanguageFactorExtensionCase,
) -> AlterLanguageFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case.

    The v1 helpers are primary-driven (they read ``case.factor_key`` /
    ``case.factor_value``), so an extension case is rendered by constructing a
    synthetic :class:`AlterLanguageFactorCase` whose primary is the extension's
    single attributable failure pair (for failures) or the branch's success
    primary (for successes), with ``kind = "EXT"`` so the patched helpers
    (_effective_role) read the crossed privilege axis from the assignment
    instead of the primary.  Baseline cases (kind in GRM/SFV/RISK) are never
    routed through here, so their bytes are untouched.
    """

    from .alter_language_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    branch = assignment["grammar_branch"]
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif branch == _BRANCH_RENAME and ext.outcome == "success":
        factor_key = _BRANCH_RENAME_SUCCESS_KEY
        factor_value = assignment["new_name_shape"]
    elif branch == _BRANCH_OWNER and ext.outcome == "success":
        factor_key = _BRANCH_OWNER_SUCCESS_KEY
        factor_value = assignment["new_owner_shape"]
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return AlterLanguageFactorCase(
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
    case: AlterLanguageFactorCase | AlterLanguageFactorExtensionCase,
) -> AlterLanguageFactorCase:
    """Return the case to feed to the v1 helpers: unchanged for baseline,
    or a byte-safe synthetic for an extension case."""

    if isinstance(case, AlterLanguageFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterLanguageFactorRenderError(ValueError):
    """Raised when an ALTER LANGUAGE case cannot be rendered."""


@dataclass(frozen=True)
class AlterLanguageFactorWitness:
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


def _baseline(case: AlterLanguageFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _lang_name(case: AlterLanguageFactorCase, a: dict[str, str], p: str) -> str:
    """The target language name as referenced inside ALTER LANGUAGE."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}Mixed Lang"'
    if shape == "missing_object":
        return f"{p}missing_lang"
    return f"{p}lang"


def _fixture_name(case: AlterLanguageFactorCase, a: dict[str, str], p: str) -> str:
    """The name used in the fixture CREATE, before any RENAME."""

    return _lang_name(case, a, p)


def _new_name(case: AlterLanguageFactorCase, a: dict[str, str], p: str) -> str:
    if case.factor_key == "new_name_shape":
        form = case.factor_value
    elif case.factor_key == "rename_conflict":
        form = case.factor_value
    else:
        form = a.get("new_name_shape", "plain_identifier")
    if form == "quoted_identifier":
        return f'"{p}Mixed New"'
    if form in ("existing_name_conflict", "new_name_conflict"):
        return f"{p}conflict"
    return f"{p}renamed"


def _owner_target(case: AlterLanguageFactorCase, a: dict[str, str], p: str) -> str:
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
    case: AlterLanguageFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target ALTER LANGUAGE runs."""

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
    if primary in _ABSENT_PRIMARIES:
        return ""
    return ""


def _probe_name(case: AlterLanguageFactorCase, a: dict[str, str], p: str) -> str:
    branch = a["grammar_branch"]
    if case.kind == "RISK":
        # RISK wraps a RENAME in a transaction; commit persists the rename,
        # rollback undoes it.  Probe the surviving name either way.
        if case.factor_value == "commit":
            return _new_name(case, a, p).strip('"')
        return _fixture_name(case, a, p).strip('"')
    if branch == _BRANCH_RENAME and case.outcome == "success":
        return _new_name(case, a, p).strip('"')
    return _fixture_name(case, a, p).strip('"')


def _is_absent_probe(case: AlterLanguageFactorCase) -> bool:
    if case.kind == "RISK":
        return False
    return (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES


def _probe_select(
    case: AlterLanguageFactorCase, a: dict[str, str], p: str
) -> str:
    mode = a.get("verification_mode", "catalog_query")
    if case.factor_key == "verification_mode":
        mode = case.factor_value
    name = _probe_name(case, a, p)
    branch = a["grammar_branch"]
    absent = _is_absent_probe(case)
    if (
        mode == "effect_query"
        and not absent
        and case.outcome == "success"
        and branch == _BRANCH_OWNER
    ):
        owner = _owner_target(case, a, p)
        if owner in ("CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"):
            role_filter = f"r.rolname = {owner.lower()}"
        else:
            role_filter = f"r.rolname = '{owner}'"
        return (
            "SELECT count(*) > 0 AS owner_is_target "
            "FROM pg_catalog.pg_language AS l "
            "JOIN pg_catalog.pg_roles AS r ON l.lanowner = r.oid "
            f"WHERE l.lanname = '{name}' AND {role_filter} "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "error_assertion":
        comparator = "= 0" if absent else "> 0"
        alias = "language_absent" if absent else "language_present"
        return (
            f"SELECT count(*) {comparator} AS {alias} "
            "FROM pg_catalog.pg_language "
            f"WHERE lanname = '{name}' ORDER BY count(*) LIMIT 1;"
        )
    comparator = "= 0" if absent else "> 0"
    alias = "language_absent" if absent else "language_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_language "
        f"WHERE lanname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _fixture_kind(case: AlterLanguageFactorCase) -> str:
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "language"


def _conflict_fixture_needed(case: AlterLanguageFactorCase) -> bool:
    primary = (case.factor_key, case.factor_value)
    return primary in {
        ("new_name_shape", "existing_name_conflict"),
        ("rename_conflict", "new_name_conflict"),
    }


def _invalid_combination_primary(
    case: AlterLanguageFactorCase,
) -> bool:
    """The primary is an invalid-combination boundary (not ``none``).

    ALTER LANGUAGE has exactly two legal single-action forms (RENAME TO and
    OWNER TO); combining both clauses in one statement is a syntax error
    (42601), which is the only way the matrix's declared
    ``invalid_language_alter_combination`` boundary is reachable in PG 18.4
    (the declared 42809 wrong_object_type is unreachable because ALTER LANGUAGE
    only resolves names in pg_language).
    """

    return (
        case.factor_key == "invalid_combination"
        and case.factor_value != "none"
    )


def _role_names(
    case: AlterLanguageFactorCase,
    a: dict[str, str],
    p: str,
    branch: str,
    effective: str,
) -> tuple[str, ...]:
    """Roles to tear down, ordered grantees before the new-owner role.

    The cluster superuser owns every fixture language (CREATE LANGUAGE needs
    superuser), so there is no separate fixture-owner role to drop; only the
    non-superuser actor (privilege boundary), the OWNER-branch new-owner role,
    and the invalid-combination owner-target role are created and torn down.
    """

    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    if _invalid_combination_primary(case):
        roles.append(f"{p}icmb_owner")
    if branch == _BRANCH_OWNER and _owner_target(case, a, p) == f"{p}new_owner":
        roles.append(f"{p}new_owner")
    return tuple(roles)


def _resolve_case(case: AlterLanguageFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    fixture_kind = _fixture_kind(case)
    name = _fixture_name(case, a, p)

    setup: list[str] = []
    locus = "target.language"

    # --- role fixtures -------------------------------------------------
    effective = _effective_role(case, a, p)
    invalid_combo = _invalid_combination_primary(case)
    if branch == _BRANCH_OWNER:
        owner = _owner_target(case, a, p)
        if owner == f"{p}new_owner":
            setup.append(f"CREATE ROLE {p}new_owner LOGIN;")
    if invalid_combo:
        # The combined RENAME + OWNER clause needs an owner-target role so the
        # statement is a complete (but invalid) combination that parses far
        # enough to raise 42601.
        setup.append(f"CREATE ROLE {p}icmb_owner LOGIN;")
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN;")

    # --- the target language fixture ----------------------------------
    # A custom procedural language needs a C handler function; CREATE
    # LANGUAGE requires superuser, so the cluster superuser creates both the
    # handler and the language before any SET ROLE arms a non-superuser
    # actor.  (DB fork calibrates the handler symbol/library and the
    # privilege fixture for a real non-superuser owner.)
    if fixture_kind == "language":
        setup.append(
            f"CREATE FUNCTION {p}handler() RETURNS language_handler "
            "AS '$libdir/plpgsql', 'plpgsql_call_handler' LANGUAGE C;"
        )
        setup.append(
            f"CREATE LANGUAGE {name} HANDLER {p}handler;"
        )
    else:
        # No language is created: the target is expected to fail because the
        # named language does not exist.  Emit a deterministic probe so the
        # program still carries an observable setup locus.
        setup.append("SELECT 1 AS target_language_intentionally_absent;")
        locus = "fixture.object_state"

    # --- conflicting-name fixture for RENAME failure --------------------
    if _conflict_fixture_needed(case):
        setup.append(
            f"CREATE FUNCTION {p}conflict_handler() RETURNS language_handler "
            "AS '$libdir/plpgsql', 'plpgsql_call_handler' LANGUAGE C;"
        )
        setup.append(
            f"CREATE LANGUAGE {p}conflict HANDLER {p}conflict_handler;"
        )
        locus = "fixture.rename_conflict"

    # --- arm the effective role (superuser is the default) -------------
    if effective:
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the primary target statement ---------------------------------
    if invalid_combo:
        # A combined RENAME + OWNER clause is a syntax error (42601): the
        # only reachable form of the invalid_combination boundary.
        target = (
            f"ALTER LANGUAGE {name} RENAME TO {_new_name(case, a, p)} "
            f"OWNER TO {p}icmb_owner;"
        )
        locus = "fixture.invalid_combination"
    elif branch == _BRANCH_RENAME:
        target = f"ALTER LANGUAGE {name} RENAME TO {_new_name(case, a, p)};"
    elif branch == _BRANCH_OWNER:
        target = f"ALTER LANGUAGE {name} OWNER TO {_owner_target(case, a, p)};"
    else:
        raise AlterLanguageFactorRenderError(f"unknown branch {branch}")

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
    # Object drops are always idempotent (IF EXISTS) so the pre-cleanup
    # (section 1, which runs under ON_ERROR_STOP) never aborts on an absent
    # or renamed-away language.  cleanup_mode distinguishes the two modes by
    # CASCADE only: drop_objects cascades dependents, reset_state drops bare.
    cascade = "" if drop_mode == "reset_state" else " CASCADE"
    if_exists = "IF EXISTS "
    roles = _role_names(case, a, p, branch, effective)

    candidate_names: list[str] = [name]
    if branch == _BRANCH_RENAME:
        # Preserve quoting: a quoted identifier (e.g. "p_Mixed New") MUST
        # keep its double quotes when used as a SQL identifier in DROP, or the
        # embedded space breaks the parser.  The probe strips quotes because
        # it compares against a string literal (pg_language.lanname).
        candidate_names.append(_new_name(case, a, p))
    if _conflict_fixture_needed(case):
        candidate_names.append(f"{p}conflict")

    object_drops = [
        f"DROP LANGUAGE {if_exists}{cand}{cascade};"
        for cand in dict.fromkeys(candidate_names)
    ]
    handler_drops = []
    if fixture_kind == "language":
        handler_drops.append(
            f"DROP FUNCTION IF EXISTS {p}handler() CASCADE;"
        )
    if _conflict_fixture_needed(case):
        handler_drops.append(
            f"DROP FUNCTION IF EXISTS {p}conflict_handler() CASCADE;"
        )
    idempotent_object_drops = object_drops + handler_drops
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    pre_cleanup: list[str] = []
    pre_cleanup.extend(idempotent_object_drops)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(idempotent_object_drops)
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


def resolve_alter_language_factor_witness(
    case: AlterLanguageFactorCase | AlterLanguageFactorExtensionCase,
    repository_root: Path,
) -> AlterLanguageFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterLanguageFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_language(sql: str) -> int:
    """Count the single credited ALTER LANGUAGE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+LANGUAGE\b", region))


def _header(case: AlterLanguageFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER LANGUAGE {case.factor_key}={case.factor_value}",
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


def render_alter_language_factor_case(
    case: AlterLanguageFactorCase | AlterLanguageFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER LANGUAGE regress program.

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
    lines.append("-- 2. 创建完整本地语言和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER LANGUAGE。")
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


def generate_alter_language_factor_programs(
    baseline_plan: AlterLanguageFactorLoopPlan,
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
    case: AlterLanguageFactorCase | AlterLanguageFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_language_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterLanguageFactorRenderError",
    "AlterLanguageFactorWitness",
    "count_primary_alter_language",
    "generate_alter_language_factor_programs",
    "render_alter_language_factor_case",
    "resolve_alter_language_factor_witness",
]
