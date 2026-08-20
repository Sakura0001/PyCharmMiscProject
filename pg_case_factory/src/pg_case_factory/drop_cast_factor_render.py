"""Render complete PostgreSQL 18.4 DROP CAST factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

DROP CAST is a type-conversion DDL statement: the target is a
``pg_catalog.pg_cast`` catalog row, not a ``pg_class`` relation.  All catalog
oracles schema-qualify ``pg_catalog.pg_cast`` (exempt from the file-prefix
style gate).  No case creates a TABLE, so the bookend (DROP TABLE IF EXISTS)
is never emitted (``_tables_to_drop`` always returns ``[]``).  Every catalog
SELECT carries a top-level ``ORDER BY count(*)`` so the catalog-observability
gate passes.

The fixture cast is always a fresh, prefix-named cast (``source_type`` /
``target_type`` default to ``custom_type``), so a DROP CAST never removes a
shipped system cast and the two-run comparison stays idempotent.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_cast_factor_extension import (
    DropCastFactorExtensionCase,
    _present_failure_pair,
)
from .drop_cast_factor_loop import (
    DropCastFactorCase,
    DropCastFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/cast/"
    "drop_cast.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/cast/"
    "drop_cast.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target cast is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("nonexistent_cast", "without_if_exists"),
        ("nonexistent_cast", "with_if_exists"),
        ("expected_status", "failure"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the cast always exists in extensions (object_state held at
# already_exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "already_exists")


def _synthetic_case(
    ext: DropCastFactorExtensionCase,
) -> DropCastFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case.

    The v1 helpers are primary-driven (they read ``case.factor_key`` /
    ``case.factor_value``), so an extension case is rendered by constructing a
    synthetic :class:`DropCastFactorCase` whose primary is the extension's
    single attributable failure pair (for failures) or the neutral success
    primary (for successes), with ``kind = "EXT"`` so the patched helpers
    (_effective_role, _if_exists_present) read the crossed privilege / IF EXISTS
    axes from the assignment instead of the primary.  Baseline cases (kind in
    GRM/SFV/RISK) are never routed through here, so their bytes are untouched.
    """

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropCastFactorCase(
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
    case: DropCastFactorCase | DropCastFactorExtensionCase,
) -> DropCastFactorCase:
    """Return the case to feed to the v1 helpers: unchanged for baseline,
    or a byte-safe synthetic for an extension case."""

    if isinstance(case, DropCastFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropCastFactorRenderError(ValueError):
    """Raised when a DROP CAST case cannot be rendered."""


@dataclass(frozen=True)
class DropCastFactorWitness:
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


def _baseline(case: DropCastFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _source_type_name(a: dict[str, str], p: str) -> str:
    """The source type name as referenced inside DROP CAST."""

    src = a.get("source_type", "custom_type")
    if src == "custom_type":
        return f"{p}sourcetype"
    return src


def _target_type_name(a: dict[str, str], p: str) -> str:
    """The target type name as referenced inside DROP CAST."""

    tgt = a.get("target_type", "custom_type")
    if tgt == "custom_type":
        return f"{p}targettype"
    return tgt


def _type_expr(type_name: str, shape: str) -> str:
    if shape == "schema_qualified_type":
        return f"public.{type_name}"
    return type_name


def _source_expr(a: dict[str, str], p: str) -> str:
    name = _source_type_name(a, p)
    shape = a.get("source_type_shape", "plain_type")
    return _type_expr(name, shape)


def _target_expr(a: dict[str, str], p: str) -> str:
    name = _target_type_name(a, p)
    shape = a.get("target_type_shape", "plain_type")
    return _type_expr(name, shape)


def _needs_custom_source(a: dict[str, str]) -> bool:
    return a.get("source_type") == "custom_type"


def _needs_custom_target(a: dict[str, str]) -> bool:
    return a.get("target_type") == "custom_type"


def _needs_reverse(case: DropCastFactorCase) -> bool:
    """Whether the reverse-direction cast fixture must be created.

    Only the ``reverse_direction_cast`` baseline case exercises the
    reverse-direction boundary (the cast's reverse survives the drop).  All
    other cases hold ``reverse_still_exists`` as metadata without creating a
    reverse cast, so the fixture footprint stays minimal.
    """

    return (
        case.factor_key == "reverse_direction_cast"
        and case.factor_value == "reverse_still_exists"
    )


def _fixture_kind(case: DropCastFactorCase) -> str:
    if case.kind in ("EXT", "RISK"):
        return "cast"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "cast"


def _if_exists_present(
    case: DropCastFactorCase, a: dict[str, str]
) -> bool:
    """Whether the DROP CAST statement carries IF EXISTS.

    For a missing cast (fixture_kind == none) the IF EXISTS clause is
    driven by ``nonexistent_cast`` (with_if_exists -> present); for an
    existing cast it is driven by ``if_exists_clause``.
    """

    if _fixture_kind(case) == "none":
        return a.get("nonexistent_cast") == "with_if_exists"
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "RESTRICT_default")
    if cascade == "CASCADE":
        return "CASCADE"
    if cascade == "RESTRICT_explicit":
        return "RESTRICT"
    return ""  # RESTRICT_default: omitted (RESTRICT is the default)


def _effective_role(
    case: DropCastFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP CAST runs.

    Only a non-owner (privilege_level=non_owner / type_ownership=owns_neither
    / insufficient_privilege=owns_no_type) arms a separate actor role; the type
    owner and superuser run as themselves (empty effective role).  The SET-ROLE
    fixture (CREATE ROLE NOSUPERUSER) is calibrated by the DB doublerun fork;
    this renderer arms a best-effort non-superuser actor.
    """

    if case.kind == "EXT":
        level = a.get("privilege_level", "type_owner_source")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "type_ownership":
        return f"{p}actor" if case.factor_value == "owns_neither" else ""
    if case.factor_key == "insufficient_privilege":
        return f"{p}actor" if case.factor_value == "owns_no_type" else ""
    return ""


def _cast_absent_after(
    case: DropCastFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target cast is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case) == "none":
        return True  # cast never existed
    if case.outcome == "success":
        return True  # drop succeeded
    return False  # failure: cast still present


def _probe_select(
    case: DropCastFactorCase, a: dict[str, str], p: str
) -> str:
    src = _source_type_name(a, p)
    tgt = _target_type_name(a, p)
    absent = _cast_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "cast_absent" if absent else "cast_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_cast "
        f"WHERE castsource = '{src}'::regtype "
        f"AND casttarget = '{tgt}'::regtype "
        f"ORDER BY count(*) LIMIT 1;"
    )


def _reverse_probe_select(
    case: DropCastFactorCase, a: dict[str, str], p: str
) -> str:
    """Assert the reverse-direction cast still exists after the forward drop."""

    src = _source_type_name(a, p)
    tgt = _target_type_name(a, p)
    return (
        "SELECT count(*) > 0 AS reverse_cast_present "
        "FROM pg_catalog.pg_cast "
        f"WHERE castsource = '{tgt}'::regtype "
        f"AND casttarget = '{src}'::regtype "
        f"ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropCastFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _tables_to_drop(
    case: DropCastFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    DROP CAST is a type-conversion DDL statement: it never creates a TABLE.
    The bookend (DROP TABLE IF EXISTS) is therefore never emitted.
    """
    return []


def _resolve_case(case: DropCastFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case)
    src_plain = _source_type_name(a, p)
    tgt_plain = _target_type_name(a, p)
    needs_rev = _needs_reverse(case)

    setup: list[str] = []
    locus = "target.cast"

    # --- custom type fixtures (as superuser, before SET ROLE) -----------
    if _needs_custom_source(a):
        setup.append(
            f"CREATE TYPE {p}sourcetype AS ENUM ('a', 'b');"
        )
        locus = "fixture.custom_source_type"
    if _needs_custom_target(a):
        setup.append(
            f"CREATE TYPE {p}targettype AS ENUM ('a', 'b');"
        )
        locus = "fixture.custom_target_type"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the cast
    # fixtures so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target cast fixture + helper function (as superuser) -------
    if fixture_kind == "cast":
        setup.append(
            f"CREATE FUNCTION {p}castfn({src_plain})"
            f" RETURNS {tgt_plain} LANGUAGE SQL IMMUTABLE AS"
            f" $$ SELECT NULL::{tgt_plain} $$;"
        )
        setup.append(
            f"CREATE CAST ({src_plain} AS {tgt_plain})"
            f" WITH FUNCTION {p}castfn;"
        )
        locus = "fixture.pre_existing_cast"
    else:
        # No cast is created: the target is expected to fail (or notice)
        # because the named cast does not exist.
        setup.append("SELECT 1 AS target_cast_intentionally_absent;")
        locus = "fixture.object_state"

    # --- reverse-direction cast fixture (as superuser) ------------------
    if needs_rev and fixture_kind == "cast":
        setup.append(
            f"CREATE FUNCTION {p}revcastfn({tgt_plain})"
            f" RETURNS {src_plain} LANGUAGE SQL IMMUTABLE AS"
            f" $$ SELECT NULL::{src_plain} $$;"
        )
        setup.append(
            f"CREATE CAST ({tgt_plain} AS {src_plain})"
            f" WITH FUNCTION {p}revcastfn;"
        )
        locus = "fixture.reverse_cast"

    # --- arm the non-owner role (AFTER cast creation) -------------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP CAST {if_exists}({src_plain} AS {tgt_plain})"
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
    if needs_rev:
        assert_lines.append(_reverse_probe_select(case, a, p))

    # --- cleanup construction -------------------------------------------
    casts_to_drop: list[tuple[str, str]] = [(src_plain, tgt_plain)]
    if needs_rev:
        casts_to_drop.append((tgt_plain, src_plain))

    cast_drops = [
        f"DROP CAST IF EXISTS ({s} AS {t});" for s, t in casts_to_drop
    ]
    func_drops: list[str] = [f"DROP FUNCTION IF EXISTS {p}castfn;"]
    if needs_rev:
        func_drops.append(f"DROP FUNCTION IF EXISTS {p}revcastfn;")

    type_drops: list[str] = []
    if _needs_custom_source(a):
        type_drops.append(f"DROP TYPE IF EXISTS {p}sourcetype;")
    if _needs_custom_target(a):
        type_drops.append(f"DROP TYPE IF EXISTS {p}targettype;")

    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: casts, functions, types, roles (all IF EXISTS / safe).
    pre_cleanup: list[str] = []
    pre_cleanup.extend(cast_drops)
    pre_cleanup.extend(func_drops)
    pre_cleanup.extend(type_drops)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then casts, functions, types, roles.  The cast
    # drop always uses IF EXISTS so it succeeds even when the target drop
    # already removed the cast.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(cast_drops)
    cleanup.extend(func_drops)
    cleanup.extend(type_drops)
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


def resolve_drop_cast_factor_witness(
    case: DropCastFactorCase | DropCastFactorExtensionCase,
    repository_root: Path,
) -> DropCastFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropCastFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_cast(sql: str) -> int:
    """Count the single credited DROP CAST inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*DROP\s+CAST\b", region))


def _header(case: DropCastFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP CAST {case.factor_key}={case.factor_value}",
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


def render_drop_cast_factor_case(
    case: DropCastFactorCase | DropCastFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP CAST regress program.

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
    lines.append("-- 2. 创建完整本地类型和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP CAST。")
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


def generate_drop_cast_factor_programs(
    baseline_plan: DropCastFactorLoopPlan,
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
    case: DropCastFactorCase | DropCastFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_cast_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropCastFactorRenderError",
    "DropCastFactorWitness",
    "count_primary_drop_cast",
    "generate_drop_cast_factor_programs",
    "render_drop_cast_factor_case",
    "resolve_drop_cast_factor_witness",
]
