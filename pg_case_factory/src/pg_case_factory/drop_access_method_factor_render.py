"""Render complete PostgreSQL 18.4 DROP ACCESS METHOD factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_am ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_access_method_factor_extension import (
    DropAccessMethodFactorExtensionCase,
)
from .drop_access_method_factor_loop import (
    DropAccessMethodFactorCase,
    DropAccessMethodFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/access_method/"
    "drop_access_method.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/access_method/"
    "drop_access_method.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target access method is
# intentionally absent, so the drop surfaces a not-found error (or a notice
# under IF EXISTS) and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("nonexistent_am", "without_if_exists"),
        ("nonexistent_am", "with_if_exists"),
        ("expected_status", "failure"),
        ("am_name_shape", "nonexistent_name"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the access method always exists in extensions (object_state
# held at already_exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "already_exists")


def _synthetic_case(
    ext: DropAccessMethodFactorExtensionCase,
) -> DropAccessMethodFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case.

    The v1 helpers are primary-driven (they read ``case.factor_key`` /
    ``case.factor_value``), so an extension case is rendered by constructing a
    synthetic :class:`DropAccessMethodFactorCase` whose primary is the
    extension's single attributable failure pair (for failures) or the neutral
    success primary (for successes), with ``kind = "EXT"`` so the patched
    helpers (_effective_role, _if_exists_present) read the crossed privilege /
    IF EXISTS axes from the assignment instead of the primary.  Baseline cases
    (kind in GRM/SFV/RISK) are never routed through here, so their bytes are
    untouched.
    """

    from .drop_access_method_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropAccessMethodFactorCase(
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
    case: DropAccessMethodFactorCase | DropAccessMethodFactorExtensionCase,
) -> DropAccessMethodFactorCase:
    """Return the case to feed to the v1 helpers: unchanged for baseline,
    or a byte-safe synthetic for an extension case."""

    if isinstance(case, DropAccessMethodFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropAccessMethodFactorRenderError(ValueError):
    """Raised when a DROP ACCESS METHOD case cannot be rendered."""


@dataclass(frozen=True)
class DropAccessMethodFactorWitness:
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


def _baseline(case: DropAccessMethodFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _am_name(case: DropAccessMethodFactorCase, a: dict[str, str], p: str) -> str:
    """The access method name as referenced inside DROP ACCESS METHOD."""

    shape = a.get("am_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}Quoted"'
    if shape == "schema_qualified":
        return f"{p}schema.{p}am"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_am"
    return f"{p}am"


def _probe_name(case: DropAccessMethodFactorCase, a: dict[str, str], p: str) -> str:
    """The bare amname (no quotes/schema) for the catalog probe."""

    shape = a.get("am_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}Quoted"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_am"
    return f"{p}am"


def _needs_schema(a: dict[str, str]) -> bool:
    return a.get("am_name_shape") == "schema_qualified"


def _fixture_kind(case: DropAccessMethodFactorCase) -> str:
    if case.kind in ("EXT", "RISK"):
        return "access_method"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "access_method"


def _needs_dependent(
    case: DropAccessMethodFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if (
        case.factor_key == "dependent_objects_exist"
        and case.factor_value == "restrict_with_dependencies"
    ):
        return True
    dep = a.get("dependency_state", "no_dependencies")
    return dep in ("has_dependent_opclass", "has_dependent_index")


def _dependent_kind(a: dict[str, str]) -> str:
    dep = a.get("dependency_state", "no_dependencies")
    if dep == "has_dependent_index":
        return "index"
    return "opclass"


def _if_exists_present(
    case: DropAccessMethodFactorCase, a: dict[str, str]
) -> bool:
    """Whether the DROP ACCESS METHOD statement carries IF EXISTS.

    For a missing access method (fixture_kind == none) the IF EXISTS clause is
    driven by ``nonexistent_am`` (with_if_exists -> present); for an existing
    access method it is driven by ``if_exists_clause``.
    """

    if _fixture_kind(case) == "none":
        return a.get("nonexistent_am") == "with_if_exists"
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "RESTRICT_default")
    if cascade == "CASCADE":
        return "CASCADE"
    if cascade == "RESTRICT_explicit":
        return "RESTRICT"
    return ""  # RESTRICT_default: omitted (RESTRICT is the default)


def _effective_role(
    case: DropAccessMethodFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP ACCESS METHOD runs.

    Only a non-superuser (privilege_level=non_superuser /
    insufficient_privilege=non_superuser_drop) arms a separate actor role; the
    superuser runs as themselves (empty effective role).  The SET-ROLE fixture
    (CREATE ROLE NOSUPERUSER) is calibrated by the DB doublerun fork; this
    renderer arms a best-effort non-superuser actor.
    """

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_superuser" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_superuser" else ""
    if case.factor_key == "insufficient_privilege":
        return (
            f"{p}actor"
            if case.factor_value == "non_superuser_drop"
            else ""
        )
    return ""


def _am_absent_after(
    case: DropAccessMethodFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target access method is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case) == "none":
        return True  # access method never existed
    if case.outcome == "success":
        return True  # drop succeeded
    return False  # failure: access method still present


def _probe_select(
    case: DropAccessMethodFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _am_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "access_method_absent" if absent else "access_method_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_am "
        f"WHERE amname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropAccessMethodFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropAccessMethodFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case)
    am_ref = _am_name(case, a, p)
    needs_schema = _needs_schema(a)
    needs_dep = _needs_dependent(case, a)
    dep_kind = _dependent_kind(a) if needs_dep else ""

    setup: list[str] = []
    locus = "target.access_method"

    # --- schema fixture -------------------------------------------------
    if needs_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}schema;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # access method and dependent fixtures so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        if needs_schema:
            setup.append(f"GRANT USAGE ON SCHEMA {p}schema TO {p}actor;")
        locus = "fixture.privilege_state"

    # --- the target access method fixture (as superuser, before SET ROLE) -
    if fixture_kind == "access_method":
        setup.append(
            f"CREATE FUNCTION {p}amhandler(internal) "
            "RETURNS table_am_handler AS 'MODULE_PATHNAME' LANGUAGE C;"
        )
        setup.append(
            f"CREATE ACCESS METHOD {am_ref} "
            f"TYPE TABLE HANDLER {p}amhandler;"
        )
    else:
        # No access method is created: the target is expected to fail (or
        # notice) because the named access method does not exist.
        setup.append("SELECT 1 AS target_access_method_intentionally_absent;")
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        setup.append(f"CREATE TABLE {p}t (c integer);")
        if dep_kind == "index":
            setup.append(
                f"CREATE INDEX {p}idx ON {p}t USING {am_ref} (c);"
            )
        else:
            setup.append(
                f"CREATE OPERATOR CLASS {p}opc DEFAULT "
                f"FOR TYPE integer USING {am_ref} AS STORAGE integer;"
            )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER AM/dependent creation) -------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP ACCESS METHOD {if_exists}{am_ref}"
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
    drop_mode = a.get("cleanup_mode", "DROP_ACCESS_METHOD_CASCADE")
    if case.factor_key == "cleanup_mode":
        drop_mode = case.factor_value
    if drop_mode == "DROP_DEPENDENT_OBJECTS_FIRST":
        am_drop = f"DROP ACCESS METHOD IF EXISTS {am_ref};"
    else:
        am_drop = f"DROP ACCESS METHOD IF EXISTS {am_ref} CASCADE;"
    cleanup_am_drop = f"DROP ACCESS METHOD IF EXISTS {am_ref} CASCADE;"
    roles = _role_names(case, p, effective)
    schema_drop = (
        [f"DROP SCHEMA IF EXISTS {p}schema CASCADE;"] if needs_schema else []
    )
    func_drop = (
        [f"DROP FUNCTION IF EXISTS {p}amhandler;"]
        if fixture_kind == "access_method"
        else []
    )
    dep_drops = (
        [f"DROP TABLE IF EXISTS {p}t CASCADE;"] if needs_dep else []
    )
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: DROP TABLE first (table audit requires it as the first
    # executable statement / bookend gate), then AM, function, schema, roles.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(dep_drops)
    pre_cleanup.append(am_drop)
    pre_cleanup.extend(func_drop)
    pre_cleanup.extend(schema_drop)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then AM/function/schema/role drops, then DROP
    # TABLE last (the table audit requires the final executable statement
    # to be DROP TABLE IF EXISTS for scripts that create tables / bookend).
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(cleanup_am_drop)
    cleanup.extend(func_drop)
    cleanup.extend(schema_drop)
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


def resolve_drop_access_method_factor_witness(
    case: DropAccessMethodFactorCase | DropAccessMethodFactorExtensionCase,
    repository_root: Path,
) -> DropAccessMethodFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropAccessMethodFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_access_method(sql: str) -> int:
    """Count the single credited DROP ACCESS METHOD inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+ACCESS\s+METHOD\b", region)
    )


def _header(case: DropAccessMethodFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP ACCESS METHOD {case.factor_key}={case.factor_value}",
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


def render_drop_access_method_factor_case(
    case: DropAccessMethodFactorCase | DropAccessMethodFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP ACCESS METHOD regress program.

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
    lines.append("-- 2. 创建完整本地访问方法和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP ACCESS METHOD。")
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


def generate_drop_access_method_factor_programs(
    baseline_plan: DropAccessMethodFactorLoopPlan,
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
    case: DropAccessMethodFactorCase | DropAccessMethodFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_access_method_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropAccessMethodFactorRenderError",
    "DropAccessMethodFactorWitness",
    "count_primary_drop_access_method",
    "generate_drop_access_method_factor_programs",
    "render_drop_access_method_factor_case",
    "resolve_drop_access_method_factor_witness",
]
