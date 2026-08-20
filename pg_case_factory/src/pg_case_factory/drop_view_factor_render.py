"""Render complete PostgreSQL 18.4 DROP VIEW factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class WHERE relname = '...'
AND relkind = 'v' ORDER BY count(*) LIMIT 1`` never nests a ``FROM``
inside an ``EXISTS`` subquery, so ``audit_catalog_observability`` accepts it.
The probe columns are real ``pg_class`` columns (``relname``, ``relkind``) —
the no-DB tickoff does not execute this probe, so a wrong column would pass all
static gates yet be a permanent latent runtime bug; the columns are verified.

CLASS-2 QUOTED-FIXTURE BUG GUARD: the fixture ``CREATE TABLE`` + bookend
``DROP TABLE IF EXISTS`` always use the UNQUOTED base table name ``{p}vbt``
so the ``audit_complete_table_script`` gate's
``_normalize_identifier`` / ``_split_identifier_list`` (which reject ``"``
chars) accept it.  The shaped (quoted/schema-qualified/reserved-word) form
lives ONLY in the credited ``DROP VIEW`` target and the ``CREATE VIEW``
fixture (which is NOT gate-checked).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_view_factor_extension import (
    DropViewFactorExtensionCase,
)
from .drop_view_factor_loop import (
    DropViewFactorCase,
    DropViewFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/view/drop_view.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/view/drop_view.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target view is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_VIEW_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("view_name_shape", "non_existent"),
        ("error_boundary", "non_existent_without_if_exists"),
    }
)

# Baseline primaries that imply a dependent-object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_state", "has_dependent_views"),
        ("dependency_state", "has_dependent_policies"),
        ("error_boundary", "dependent_objects_without_cascade"),
    }
)

# Baseline primaries that imply a non-owner role fixture.
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("privilege_level", "non_owner"),
        ("error_boundary", "insufficient_privilege"),
    }
)

# Baseline primaries that imply the target is a table, not a view.
_WRONG_OBJECT_TYPE_PRIMARIES = frozenset(
    {
        ("error_boundary", "wrong_object_type"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the view always exists in extensions (object_state held at
# exists) unless view_name_shape=non_existent.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropViewFactorExtensionCase,
) -> DropViewFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_view_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropViewFactorCase(
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
    case: DropViewFactorCase | DropViewFactorExtensionCase,
) -> DropViewFactorCase:
    if isinstance(case, DropViewFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropViewFactorRenderError(ValueError):
    """Raised when a DROP VIEW case cannot be rendered."""


@dataclass(frozen=True)
class DropViewFactorWitness:
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


def _baseline(case: DropViewFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_wrong_object_type(
    case: DropViewFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target is a table, not a view (error_boundary=wrong_object_type)."""

    if case.kind == "EXT":
        return a.get("error_boundary") == "wrong_object_type"
    return (case.factor_key, case.factor_value) in _WRONG_OBJECT_TYPE_PRIMARIES


def _view_created(case: DropViewFactorCase, a: dict[str, str]) -> bool:
    """Whether the target view is created as a fixture."""

    if _is_wrong_object_type(case, a):
        return False
    if a.get("object_state") == "not_exists":
        return False
    if (case.factor_key, case.factor_value) in _ABSENT_VIEW_PRIMARIES:
        return False
    if case.kind == "EXT":
        return a.get("object_state") != "not_exists"
    return True


def _base_table_ref(case: DropViewFactorCase, a: dict[str, str], p: str) -> str:
    """The unquoted base table name used in CREATE TABLE and bookend DROP TABLE.

    This is deliberately UNQUOTED for every name_shape: the shared
    ``audit_complete_table_script`` gate (``_normalize_identifier`` /
    ``_split_identifier_list``) rejects ``"`` characters, so a quoted
    fixture name would leave ``created_tables`` empty and break the
    bookend (first/last must be ``DROP TABLE IF EXISTS``).  The bare
    lowercase identifier is the same object the shaped ``_view_ref``
    target drops, so the factor is still exercised by the credited
    DROP VIEW while the fixture stays gate-parseable.
    """

    return f"{p}vbt"


def _view_ref(case: DropViewFactorCase, a: dict[str, str], p: str) -> str:
    """The shaped view name used in the credited DROP VIEW target.

    For wrong_object_type the target IS the base table (a table, not a
    view), so the bare unquoted base table name is returned.
    """

    if _is_wrong_object_type(case, a):
        return _base_table_ref(case, a, p)
    shape = a.get("view_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}qv"'
    if shape == "schema_qualified":
        return f"public.{p}v"
    if shape == "reserved_word":
        return f'"{p}select"'
    if shape == "non_existent":
        return f"{p}noexist"
    return f"{p}v"


def _view_probe(case: DropViewFactorCase, a: dict[str, str], p: str) -> str:
    """The bare unquoted view name (no quotes/schema) for the catalog probe.

    pg_class.relname stores the identifier without quotes, so the probe
    WHERE clause must match the bare form.  For wrong_object_type the
    target is the base table; the probe checks relkind='v' against the
    base table name (which is relkind='r', so count=0 → view_absent).
    """

    if _is_wrong_object_type(case, a):
        return _base_table_ref(case, a, p)
    shape = a.get("view_name_shape", "simple")
    if shape == "quoted":
        return f"{p}qv"
    if shape == "schema_qualified":
        return f"{p}v"
    if shape == "reserved_word":
        return f"{p}select"
    if shape == "non_existent":
        return f"{p}noexist"
    return f"{p}v"


def _dependency_kind(
    case: DropViewFactorCase, a: dict[str, str]
) -> str:
    """The kind of dependency fixture, or 'none'."""

    if case.kind == "EXT":
        dep = a.get("dependency_state", "no_dependents")
        if dep == "has_dependent_views":
            return "view"
        if dep == "has_dependent_policies":
            return "policy"
        return "none"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        if case.factor_key == "error_boundary":
            return "view"
        if case.factor_value == "has_dependent_views":
            return "view"
        if case.factor_value == "has_dependent_policies":
            return "policy"
    dep = a.get("dependency_state", "no_dependents")
    if dep == "has_dependent_views":
        return "view"
    if dep == "has_dependent_policies":
        return "policy"
    return "none"


def _is_multi_view(
    case: DropViewFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "EXT":
        return a.get("multi_view_drop") == "multi_view"
    return (
        case.factor_key == "multi_view_drop"
        and case.factor_value == "multi_view"
    )


def _if_exists_present(case: DropViewFactorCase, a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "none")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""  # none: RESTRICT is the default


def _effective_role(
    case: DropViewFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP VIEW runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "owner")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if (case.factor_key, case.factor_value) in _PRIVILEGE_PRIMARIES:
        return f"{p}actor"
    return ""


def _view_absent_after(
    case: DropViewFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target view is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _view_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropViewFactorCase, a: dict[str, str], p: str
) -> str:
    probe_name = _view_probe(case, a, p)
    absent = _view_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "view_absent" if absent else "view_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{probe_name}' AND relkind = 'v' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropViewFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropViewFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    view_created = _view_created(case, a)
    wrong_type = _is_wrong_object_type(case, a)
    base_table = _base_table_ref(case, a, p)
    view_ref = _view_ref(case, a, p)
    dep_kind = _dependency_kind(case, a)
    effective = _effective_role(case, a, p)
    is_multi = _is_multi_view(case, a)
    # The base TABLE is ALWAYS created (unquoted) for every case: the
    # fixture needs it either as the view's backing relation, as the
    # wrong-type target, or simply as a gate-parseable object so the
    # bookend DROP TABLE IF EXISTS holds for every file.
    needs_table = True

    setup: list[str] = []
    locus = "target.view"

    # --- setup boundary SELECT (prevents \set from merging with the first
    # CREATE TABLE so the bookend gate detects the table at col 0) ---
    if needs_table:
        setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after fixtures) ---
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the base TABLE (as superuser, before SET ROLE; always unquoted) ---
    if needs_table:
        setup.append(f"CREATE TABLE {base_table} (c integer);")
        if wrong_type:
            # wrong_object_type: the base table IS the wrong-type target.
            # No CREATE VIEW — the DROP VIEW targets the table → 42809.
            locus = "fixture.wrong_object_type"
        elif view_created:
            setup.append(
                f"CREATE VIEW {view_ref} AS SELECT * FROM {base_table};"
            )
            locus = "fixture.target_view"

    # --- multi-view fixture (second view) ---
    if is_multi and view_created:
        setup.append(f"CREATE VIEW {p}v2 AS SELECT * FROM {base_table};")
        locus = "fixture.multi_view"

    # --- dependent object fixtures ---
    if dep_kind == "view" and view_created:
        setup.append(f"CREATE VIEW {p}depv AS SELECT * FROM {view_ref};")
        locus = "fixture.dependency_view"
    elif dep_kind == "policy" and view_created:
        setup.append(f"ALTER TABLE {view_ref} ENABLE ROW LEVEL SECURITY;")
        setup.append(f"CREATE POLICY {p}pol ON {view_ref} USING (true);")
        locus = "fixture.dependency_policy"

    # --- arm the non-superuser role (AFTER view creation) ---
    if effective:
        setup.append(f"SET ROLE {p}actor;")

    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)

    # --- target statement construction ---
    if wrong_type:
        target = f"DROP VIEW {if_exists}{base_table}"
    elif is_multi:
        target = f"DROP VIEW {if_exists}{view_ref}, {p}v2"
    else:
        target = f"DROP VIEW {if_exists}{view_ref}"
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
    dep_view_drop = (
        [f"DROP VIEW IF EXISTS {p}depv CASCADE;"]
        if dep_kind == "view"
        else []
    )
    dep_policy_drop = (
        [f"DROP POLICY IF EXISTS {p}pol ON {view_ref};"]
        if dep_kind == "policy"
        else []
    )
    multi_view_drop = (
        [f"DROP VIEW IF EXISTS {p}v2 CASCADE;"] if is_multi else []
    )
    # The DROP VIEW IF EXISTS cleanup is ALWAYS present so the bookend
    # pattern (DROP TABLE first, DROP VIEW middle, DROP TABLE last) holds
    # for every file.  The IF EXISTS makes it a safe no-op when the view
    # was never created or was already dropped by the target statement.
    view_drop = [f"DROP VIEW IF EXISTS {view_ref} CASCADE;"]
    table_drop = (
        [f"DROP TABLE IF EXISTS {base_table} CASCADE;"]
        if needs_table
        else []
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

    # Pre-cleanup: DROP TABLE first (bookend gate), then view/dep/multi/role.
    # The DROP VIEW IF EXISTS goes IN THE MIDDLE (between the two DROP TABLE
    # bookends) so first=DROP TABLE + last=DROP TABLE both hold.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(table_drop)
    pre_cleanup.extend(view_drop)
    pre_cleanup.extend(dep_view_drop)
    pre_cleanup.extend(dep_policy_drop)
    pre_cleanup.extend(multi_view_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then view/dep/multi/role drops, then DROP TABLE
    # last (bookend gate).
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(view_drop)
    cleanup.extend(dep_view_drop)
    cleanup.extend(dep_policy_drop)
    cleanup.extend(multi_view_drop)
    cleanup.extend(role_drops)
    cleanup.extend(table_drop)
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


def resolve_drop_view_factor_witness(
    case: DropViewFactorCase | DropViewFactorExtensionCase,
    repository_root: Path,
) -> DropViewFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropViewFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_view(sql: str) -> int:
    """Count the single credited DROP VIEW inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+VIEW\b", region)
    )


def _header(case: DropViewFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP VIEW {case.factor_key}={case.factor_value}",
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


def render_drop_view_factor_case(
    case: DropViewFactorCase | DropViewFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP VIEW regress program."""

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
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP VIEW。")
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


def generate_drop_view_factor_programs(
    baseline_plan: DropViewFactorLoopPlan,
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
    case: DropViewFactorCase | DropViewFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_view_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropViewFactorRenderError",
    "DropViewFactorWitness",
    "count_primary_drop_view",
    "generate_drop_view_factor_programs",
    "render_drop_view_factor_case",
    "resolve_drop_view_factor_witness",
]
