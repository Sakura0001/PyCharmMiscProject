"""Render complete PostgreSQL 18.4 DROP COLLATION factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_collation ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_collation_factor_extension import (
    DropCollationFactorExtensionCase,
)
from .drop_collation_factor_loop import (
    DropCollationFactorCase,
    DropCollationFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/collation/"
    "drop_collation.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/collation/"
    "drop_collation.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target collation is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("nonexistent_collation", "without_if_exists"),
        ("nonexistent_collation", "with_if_exists"),
        ("expected_status", "failure"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the collation always exists in extensions (object_state held at
# already_exists_no_deps).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "already_exists_no_deps")


def _synthetic_case(
    ext: DropCollationFactorExtensionCase,
) -> DropCollationFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case.

    The v1 helpers are primary-driven (they read ``case.factor_key`` /
    ``case.factor_value``), so an extension case is rendered by constructing a
    synthetic :class:`DropCollationFactorCase` whose primary is the extension's
    single attributable failure pair (for failures) or the neutral success
    primary (for successes), with ``kind = "EXT"`` so the patched helpers
    (_effective_role, _if_exists_present) read the crossed privilege / IF EXISTS
    axes from the assignment instead of the primary.  Baseline cases (kind in
    GRM/SFV/RISK) are never routed through here, so their bytes are untouched.
    """

    from .drop_collation_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropCollationFactorCase(
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
    case: DropCollationFactorCase | DropCollationFactorExtensionCase,
) -> DropCollationFactorCase:
    """Return the case to feed to the v1 helpers: unchanged for baseline,
    or a byte-safe synthetic for an extension case."""

    if isinstance(case, DropCollationFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropCollationFactorRenderError(ValueError):
    """Raised when a DROP COLLATION case cannot be rendered."""


@dataclass(frozen=True)
class DropCollationFactorWitness:
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


def _baseline(case: DropCollationFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _coll_name(case: DropCollationFactorCase, a: dict[str, str], p: str) -> str:
    """The collation name as referenced inside DROP COLLATION."""

    shape = a.get("collation_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}Quoted"'
    if shape == "schema_qualified":
        return f"{p}schema.{p}coll"
    return f"{p}coll"


def _probe_name(case: DropCollationFactorCase, a: dict[str, str], p: str) -> str:
    """The bare collname (no quotes/schema) for the catalog probe."""

    shape = a.get("collation_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}Quoted"
    return f"{p}coll"


def _needs_schema(a: dict[str, str]) -> bool:
    return a.get("collation_name_shape") == "schema_qualified"


def _fixture_kind(case: DropCollationFactorCase) -> str:
    if case.kind in ("EXT", "RISK"):
        return "collation"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "collation"


def _needs_dependent(case: DropCollationFactorCase, a: dict[str, str]) -> bool:
    """Whether a dependent object fixture must be created."""

    if (
        case.factor_key == "dependent_objects_exist"
        and case.factor_value == "restrict_with_dependencies"
    ):
        return True
    dep = a.get("dependency_state", "no_dependencies")
    return dep in ("referenced_by_table_column", "referenced_by_index")


def _dependent_kind(a: dict[str, str]) -> str:
    dep = a.get("dependency_state", "no_dependencies")
    if dep == "referenced_by_index":
        return "index"
    return "column"


def _if_exists_present(
    case: DropCollationFactorCase, a: dict[str, str]
) -> bool:
    """Whether the DROP COLLATION statement carries IF EXISTS.

    For a missing collation (fixture_kind == none) the IF EXISTS clause is
    driven by ``nonexistent_collation`` (with_if_exists -> present); for an
    existing collation it is driven by ``if_exists_clause``.
    """

    if _fixture_kind(case) == "none":
        return a.get("nonexistent_collation") == "with_if_exists"
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "RESTRICT_default")
    if cascade == "CASCADE":
        return "CASCADE"
    if cascade == "RESTRICT_explicit":
        return "RESTRICT"
    return ""  # RESTRICT_default: omitted (RESTRICT is the default)


def _effective_role(
    case: DropCollationFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP COLLATION runs.

    Only a non-owner (privilege_level=non_owner / insufficient_privilege=
    non_owner_drop) arms a separate actor role; the collation owner and
    superuser run as themselves (empty effective role).  The SET-ROLE fixture
    (CREATE ROLE NOSUPERUSER + ownership transfer) is calibrated by the DB
    doublerun fork; this renderer arms a best-effort non-superuser actor.
    """

    if case.kind == "EXT":
        level = a.get("privilege_level", "collation_owner")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "insufficient_privilege":
        return f"{p}actor" if case.factor_value == "non_owner_drop" else ""
    return ""


def _collation_absent_after(
    case: DropCollationFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target collation is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case) == "none":
        return True  # collation never existed
    if case.outcome == "success":
        return True  # drop succeeded
    return False  # failure: collation still present


def _probe_select(
    case: DropCollationFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _collation_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "collation_absent" if absent else "collation_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_collation "
        f"WHERE collname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropCollationFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropCollationFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case)
    coll_ref = _coll_name(case, a, p)
    needs_schema = _needs_schema(a)
    needs_dep = _needs_dependent(case, a)
    dep_kind = _dependent_kind(a) if needs_dep else ""

    setup: list[str] = []
    locus = "target.collation"

    # --- schema fixture -------------------------------------------------
    if needs_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}schema;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # collation and dependent fixtures so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        if needs_schema:
            setup.append(f"GRANT USAGE ON SCHEMA {p}schema TO {p}actor;")
        locus = "fixture.privilege_state"

    # --- the target collation fixture (as superuser, before SET ROLE) -
    if fixture_kind == "collation":
        setup.append(
            f"CREATE COLLATION {coll_ref} "
            "(LC_COLLATE = 'C', LC_CTYPE = 'C');"
        )
    else:
        # No collation is created: the target is expected to fail (or notice)
        # because the named collation does not exist.
        setup.append("SELECT 1 AS target_collation_intentionally_absent;")
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        if dep_kind == "index":
            setup.append(f"CREATE TABLE {p}t (c text);")
            setup.append(
                f"CREATE INDEX {p}idx ON {p}t (c COLLATE {coll_ref});"
            )
        else:
            setup.append(f"CREATE TABLE {p}t (c text COLLATE {coll_ref});")
        locus = "fixture.dependency_state"

    # --- arm the non-owner role (AFTER collation/dependent creation) -----
    # The collation and any dependents were created by the superuser; the
    # non-owner actor now attempts the DROP and is rejected with 42501
    # because only the owner (the superuser) may drop a collation.
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP COLLATION {if_exists}{coll_ref}"
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

    # --- cleanup construction (shared idempotent bookends) ------------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the non-owner actor
    # role is created by setup, so on a fresh database the role does not
    # exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  The DROP TABLE IF EXISTS anchor is first in
    # pre-cleanup and last in cleanup, satisfying the table-bookend gate.
    drop_mode = a.get("cleanup_mode", "DROP_COLLATION_CASCADE")
    if case.factor_key == "cleanup_mode":
        drop_mode = case.factor_value
    roles = _role_names(case, p, effective)
    role_list = list(roles)
    # The collation is always dropped in both bookends (IF EXISTS makes it
    # a harmless NOTICE when the collation never existed).  Pre-cleanup
    # honours the cleanup_mode axis (RESTRICT when dependents are dropped
    # first); the post-target safety net always uses CASCADE so the
    # collation is removed even when dependents persist.
    pre_cascade = drop_mode != "DROP_DEPENDENT_OBJECTS_FIRST"
    pre_specs: list[DropSpec] = [
        DropSpec("COLLATION", coll_ref, cascade=pre_cascade)
    ]
    cln_specs: list[DropSpec] = [
        DropSpec("COLLATION", coll_ref, cascade=True)
    ]
    table_names = [f"{p}t"] if needs_dep else []
    schemas = (f"{p}schema",) if needs_schema else ()
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(pre_specs),
        schemas=schemas,
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
        specs=tuple(cln_specs),
        schemas=schemas,
        roles=role_list,
        drop_owned=bool(role_list),
        reset_role=bool(effective),
    )
    pre_cleanup = list(pre_bookend.statements)
    cleanup = list(cln_bookend.statements)

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


def resolve_drop_collation_factor_witness(
    case: DropCollationFactorCase | DropCollationFactorExtensionCase,
    repository_root: Path,
) -> DropCollationFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropCollationFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_collation(sql: str) -> int:
    """Count the single credited DROP COLLATION inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*DROP\s+COLLATION\b", region))


def _header(case: DropCollationFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP COLLATION {case.factor_key}={case.factor_value}",
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


def render_drop_collation_factor_case(
    case: DropCollationFactorCase | DropCollationFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP COLLATION regress program.

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
    lines.append("-- 2. 创建完整本地排序规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP COLLATION。")
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


def generate_drop_collation_factor_programs(
    baseline_plan: DropCollationFactorLoopPlan,
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
    case: DropCollationFactorCase | DropCollationFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_collation_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropCollationFactorRenderError",
    "DropCollationFactorWitness",
    "count_primary_drop_collation",
    "generate_drop_collation_factor_programs",
    "render_drop_collation_factor_case",
    "resolve_drop_collation_factor_witness",
]
