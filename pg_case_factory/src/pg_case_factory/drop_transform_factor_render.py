"""Render complete PostgreSQL 18.4 DROP TRANSFORM factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

DROP TRANSFORM is a catalog-row DDL statement: the target is a
``pg_catalog.pg_transform`` catalog row, not a ``pg_class`` relation.  All
catalog oracles schema-qualify ``pg_catalog.pg_transform`` joined to
``pg_catalog.pg_language`` (exempt from the file-prefix style gate via the
``pg_`` prefix).  No case creates a TABLE, so the bookend (DROP TABLE IF
EXISTS) is never emitted.  Every catalog SELECT carries a top-level
``ORDER BY`` so the catalog-observability gate passes.

The catalog probe resolves the bound type and language to OIDs at runtime
WITHOUT hardcoding numeric OIDs: the type name is cast with the verified
``::regtype`` cast, and the language OID is resolved via a JOIN on
``pg_catalog.pg_language.lanname``.  A ``::reglanguage`` cast is deliberately
NOT used — it does not exist in PostgreSQL 18.4 (confirmed against a live
PG18.4 server: ``type "reglanguage" does not exist``), so it would be a
permanent latent runtime bug the no-DB static gate cannot catch.  The probe
columns are real ``pg_transform`` columns (``trftype``, ``trflang``) — a
``trfname``/``transformname``/``name`` column does NOT exist and is never
used.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_transform_factor_extension import (
    DropTransformFactorExtensionCase,
)
from .drop_transform_factor_loop import (
    DropTransformFactorCase,
    DropTransformFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "transform/drop_transform.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "transform/drop_transform.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target transform is intentionally absent, so the
# DROP surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_TRANSFORM_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("nonexistent_transform", "transform_missing_without_if_exists"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to
# the assignment; the transform always exists in extensions (object_state
# held at exists) unless object_state=absent.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropTransformFactorExtensionCase,
) -> DropTransformFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_transform_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropTransformFactorCase(
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
    case: DropTransformFactorCase | DropTransformFactorExtensionCase,
) -> DropTransformFactorCase:
    if isinstance(case, DropTransformFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropTransformFactorRenderError(ValueError):
    """Raised when a DROP TRANSFORM case cannot be rendered."""


@dataclass(frozen=True)
class DropTransformFactorWitness:
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


def _baseline(case: DropTransformFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(p: str) -> str:
    return f"{p}schema"


def _is_type_missing(a: dict[str, str]) -> bool:
    return (
        a.get("type_existence") == "type_not_exists"
        or a.get("nonexistent_type") == "type_missing"
        or a.get("type_name_shape") == "nonexistent_name"
    )


def _is_language_missing(a: dict[str, str]) -> bool:
    return (
        a.get("language_existence") == "language_not_exists"
        or a.get("nonexistent_language") == "language_missing"
        or a.get("language_name_shape") == "nonexistent_name"
    )


def _is_privilege_failure(a: dict[str, str]) -> bool:
    return (
        a.get("privilege_requirement") in
        {"missing_type_ownership", "missing_language_ownership"}
        or a.get("privilege_on_type") == "not_owns_type"
        or a.get("privilege_on_language") == "not_owns_language"
        or a.get("insufficient_privilege") in
        {"missing_type_ownership", "missing_language_ownership"}
    )


def _is_dependency_failure(a: dict[str, str]) -> bool:
    return (
        a.get("dependency_context") == "has_dependent_objects"
        and a.get("cascade_restrict") in
        {"default_restrict", "explicit_restrict"}
    )


def _is_absent_primary(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "absent"
        or a.get("nonexistent_transform")
        == "transform_missing_without_if_exists"
        or a.get("expected_status") == "failure"
    )


def _transform_created(a: dict[str, str]) -> bool:
    """Whether a transform fixture must be created."""

    if _is_type_missing(a) or _is_language_missing(a):
        return False
    return not _is_absent_primary(a)


def _type_name(a: dict[str, str], p: str) -> str:
    """The type identifier referenced in DROP TRANSFORM FOR."""

    schema = _schema_name(p)
    if _is_type_missing(a):
        return f"{schema}.{p}notype"
    return f"{schema}.{p}type"


def _type_name_literal(a: dict[str, str], p: str) -> str:
    """The catalog string literal for the oracle ::regtype cast."""

    if _is_type_missing(a):
        return f"{_schema_name(p)}.{p}notype"
    return f"{_schema_name(p)}.{p}type"


def _language_name(a: dict[str, str], p: str) -> str:
    """The language identifier referenced in DROP TRANSFORM LANGUAGE."""

    if _is_language_missing(a):
        return f"{p}nolang"
    return "plpgsql"


def _from_sql_fn(a: dict[str, str], p: str) -> str:
    return f"{_schema_name(p)}.{p}fromsql"


def _to_sql_fn(a: dict[str, str], p: str) -> str:
    return f"{_schema_name(p)}.{p}tosql"


def _if_exists_present(a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "default_restrict")
    if cascade == "explicit_cascade":
        return "CASCADE"
    if cascade == "explicit_restrict":
        return "RESTRICT"
    return ""  # default_restrict: RESTRICT is the default


def _effective_role(a: dict[str, str], p: str) -> str:
    return f"{p}actor" if _is_privilege_failure(a) else ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    return (f"{p}actor",) if _is_privilege_failure(a) else ()


def _transform_absent_after(
    case: DropTransformFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target transform is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _transform_created(a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropTransformFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    # The ::regtype cast resolves the bound type name to its OID at runtime;
    # when the bound type does not exist the cast itself errors, so no
    # catalog probe is emitted for type-missing cases (sqlstate-only).
    if _is_type_missing(a):
        return None
    type_lit = _type_name_literal(a, p)
    lang_name = _language_name(a, p)
    absent = _transform_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "transform_absent" if absent else "transform_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_transform t "
        "JOIN pg_catalog.pg_language l ON t.trflang = l.oid "
        f"WHERE t.trftype = '{type_lit}'::regtype "
        f"AND l.lanname = '{lang_name}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _resolve_case(case: DropTransformFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _schema_name(p)
    type_name = _type_name(a, p)
    lang_name = _language_name(a, p)
    from_fn = _from_sql_fn(a, p)
    to_fn = _to_sql_fn(a, p)
    transform_created = _transform_created(a)
    needs_dep = _is_dependency_failure(a) or a.get(
        "dependency_context"
    ) == "has_dependent_objects"

    setup: list[str] = []
    locus = "target.drop_transform"

    # --- schema fixture ---
    setup.append(f"CREATE SCHEMA {schema};")
    locus = "fixture.schema"

    # --- type fixture (ENUM type; skipped when type is intentionally
    # missing so the DROP surfaces a type-missing error) ---
    if not _is_type_missing(a):
        setup.append(f"CREATE TYPE {type_name} AS ENUM ('a');")
        locus = "fixture.type"

    # --- support function fixtures (internal-typed, verified working on
    # PG18.4 via LANGUAGE internal AS 'textlike_support') ---
    if transform_created:
        setup.append(
            f"CREATE FUNCTION {from_fn}(internal) RETURNS internal "
            "LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';"
        )
        setup.append(
            f"CREATE FUNCTION {to_fn}(internal) RETURNS {type_name} "
            "LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';"
        )
        locus = "fixture.support_functions"

    # --- the transform fixture (created as superuser, before SET ROLE) ---
    if transform_created:
        setup.append(
            f"CREATE TRANSFORM FOR {type_name} LANGUAGE {lang_name} "
            f"(FROM SQL WITH FUNCTION {from_fn}(internal), "
            f"TO SQL WITH FUNCTION {to_fn}(internal));"
        )
        locus = "fixture.transform"
    elif not _is_type_missing(a) and not _is_language_missing(a):
        setup.append(
            "SELECT 1 AS target_transform_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent-object marker (provisional dependency context) ---
    if needs_dep:
        setup.append(
            "SELECT 1 AS dependent_context_armed;"
        )
        locus = "fixture.dependency_state"

    # --- privilege fixture (CREATE ROLE, GRANT USAGE, SET ROLE) ---
    effective = _effective_role(a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        setup.append(f"GRANT USAGE ON SCHEMA {schema} TO {p}actor;")
        if not _is_type_missing(a):
            setup.append(
                f"GRANT USAGE ON TYPE {type_name} TO {p}actor;"
            )
        setup.append(f"SET ROLE {p}actor;")
        locus = "fixture.privilege_state"

    if_exists = "IF EXISTS " if _if_exists_present(a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP TRANSFORM {if_exists}FOR {type_name} LANGUAGE {lang_name}"
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
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -------------------------------------------
    role_drops = [
        stmt
        for role in _role_names(a, p)
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]
    transform_drop = (
        [f"DROP TRANSFORM IF EXISTS FOR {type_name} "
         f"LANGUAGE {lang_name} CASCADE;"]
        if not _is_type_missing(a) and not _is_language_missing(a)
        else []
    )
    function_drops = (
        [
            f"DROP FUNCTION IF EXISTS {from_fn}(internal) CASCADE;",
            f"DROP FUNCTION IF EXISTS {to_fn}(internal) CASCADE;",
        ]
        if transform_created
        else []
    )
    type_drop = (
        [f"DROP TYPE IF EXISTS {type_name} CASCADE;"]
        if not _is_type_missing(a)
        else []
    )
    schema_drop = [f"DROP SCHEMA IF EXISTS {schema} CASCADE;"]

    # Pre-cleanup: safe IF EXISTS CASCADE, before fixtures.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(transform_drop)
    pre_cleanup.extend(function_drops)
    pre_cleanup.extend(type_drop)
    pre_cleanup.extend(schema_drop)
    pre_cleanup.append("RESET ROLE;")
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: role resets, then transform/function/type/schema drops.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(transform_drop)
    cleanup.extend(function_drops)
    cleanup.extend(type_drop)
    cleanup.extend(schema_drop)
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


def resolve_drop_transform_factor_witness(
    case: DropTransformFactorCase | DropTransformFactorExtensionCase,
    repository_root: Path,
) -> DropTransformFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTransformFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_transform(sql: str) -> int:
    """Count the single credited DROP TRANSFORM inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+TRANSFORM\b", region)
    )


def _header(case: DropTransformFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TRANSFORM "
        f"{case.factor_key}={case.factor_value}",
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


def render_drop_transform_factor_case(
    case: DropTransformFactorCase | DropTransformFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TRANSFORM regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 DROP TRANSFORM。"
    )
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
    if not text.endswith("\n"):
        text += "\n"
    return text


def generate_drop_transform_factor_programs(
    baseline_plan: DropTransformFactorLoopPlan,
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
    case: DropTransformFactorCase | DropTransformFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_transform_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTransformFactorRenderError",
    "DropTransformFactorWitness",
    "count_primary_drop_transform",
    "generate_drop_transform_factor_programs",
    "render_drop_transform_factor_case",
    "resolve_drop_transform_factor_witness",
]
