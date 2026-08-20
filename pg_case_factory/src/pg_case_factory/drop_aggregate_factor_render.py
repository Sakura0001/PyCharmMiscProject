"""Render complete PostgreSQL 18.4 DROP AGGREGATE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_aggregate ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_aggregate_factor_extension import (
    DropAggregateFactorExtensionCase,
)
from .drop_aggregate_factor_loop import (
    DropAggregateFactorCase,
    DropAggregateFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/aggregate/"
    "drop_aggregate.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/aggregate/"
    "drop_aggregate.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target aggregate is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("nonexistent_aggregate", "without_if_exists"),
        ("nonexistent_aggregate", "with_if_exists"),
        ("expected_status", "failure"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the aggregate always exists in extensions (object_state held at
# already_exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "already_exists")


def _synthetic_case(
    ext: DropAggregateFactorExtensionCase,
) -> DropAggregateFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_aggregate_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropAggregateFactorCase(
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
    case: DropAggregateFactorCase | DropAggregateFactorExtensionCase,
) -> DropAggregateFactorCase:
    """Return the case to feed to the v1 helpers: unchanged for baseline,
    or a byte-safe synthetic for an extension case."""

    if isinstance(case, DropAggregateFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropAggregateFactorRenderError(ValueError):
    """Raised when a DROP AGGREGATE case cannot be rendered."""


@dataclass(frozen=True)
class DropAggregateFactorWitness:
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


def _baseline(case: DropAggregateFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _agg_name(case: DropAggregateFactorCase, a: dict[str, str], p: str) -> str:
    """The aggregate name as referenced inside DROP AGGREGATE."""

    shape = a.get("aggregate_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}QuotedAgg"'
    if shape == "schema_qualified":
        return f"{p}schema.{p}agg"
    return f"{p}agg"


def _agg2_name(a: dict[str, str], p: str) -> str:
    """A second aggregate name for multiple_aggregates cases."""

    shape = a.get("aggregate_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}QuotedAgg2"'
    if shape == "schema_qualified":
        return f"{p}schema.{p}agg2"
    return f"{p}agg2"


def _probe_name(case: DropAggregateFactorCase, a: dict[str, str], p: str) -> str:
    """The bare aggname (no quotes/schema) for the catalog probe."""

    shape = a.get("aggregate_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}QuotedAgg"
    return f"{p}agg"


def _needs_schema(a: dict[str, str]) -> bool:
    return a.get("aggregate_name_shape") == "schema_qualified"


def _fixture_kind(case: DropAggregateFactorCase) -> str:
    if case.kind in ("EXT", "RISK"):
        return "aggregate"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "aggregate"


def _needs_dependent(
    case: DropAggregateFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if (
        case.factor_key == "dependent_objects_exist"
        and case.factor_value == "restrict_with_dependencies"
    ):
        return True
    dep = a.get("dependency_state", "no_dependencies")
    if dep in ("has_dependent_view", "has_dependent_function"):
        return True
    if a.get("object_state") == "exists_with_dependencies":
        return True
    return False


def _dependent_kind(a: dict[str, str]) -> str:
    dep = a.get("dependency_state", "no_dependencies")
    if dep == "has_dependent_function":
        return "function"
    return "view"


def _if_exists_present(
    case: DropAggregateFactorCase, a: dict[str, str]
) -> bool:
    """Whether the DROP AGGREGATE statement carries IF EXISTS."""

    if _fixture_kind(case) == "none":
        return a.get("nonexistent_aggregate") == "with_if_exists"
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "RESTRICT_default")
    if cascade == "CASCADE":
        return "CASCADE"
    if cascade == "RESTRICT_explicit":
        return "RESTRICT"
    return ""


def _effective_role(
    case: DropAggregateFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP AGGREGATE runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "aggregate_owner")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "insufficient_privilege":
        return f"{p}actor" if case.factor_value == "non_owner_drop" else ""
    return ""


def _agg_absent_after(
    case: DropAggregateFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target aggregate is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropAggregateFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _agg_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "aggregate_absent" if absent else "aggregate_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_aggregate a "
        "JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid "
        f"WHERE p.proname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropAggregateFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _sig_text(sig: str, a: dict[str, str]) -> str:
    """The signature text for CREATE/DROP AGGREGATE."""

    argtype = a.get("signature_argtype_shape", "plain_type")
    int_t = "pg_catalog.int4" if argtype == "schema_qualified_type" else "int"
    text_t = "pg_catalog.text" if argtype == "schema_qualified_type" else "text"
    if sig == "star_zero_arg":
        return "*"
    if sig == "single_argtype":
        return int_t
    if sig == "multi_argtype":
        return f"{int_t}, {text_t}"
    if sig == "ordered_set_signature":
        return f"{int_t} ORDER BY {text_t}"
    return int_t


def _drop_sig_text(
    case: DropAggregateFactorCase, a: dict[str, str]
) -> str:
    """The signature used in DROP AGGREGATE (may be wrong for mismatch)."""

    sig = a.get("aggregate_signature", "star_zero_arg")
    if case.kind == "EXT":
        return _sig_text(sig, a)
    if case.factor_key == "signature_mismatch":
        if case.factor_value == "wrong_arg_count":
            return "text"
        if case.factor_value == "wrong_arg_type":
            return "bigint"
    return _sig_text(sig, a)


def _sfunc_create(sig: str, p: str) -> str:
    """CREATE FUNCTION for the support function matching the signature."""

    if sig == "star_zero_arg":
        return (
            f"CREATE FUNCTION {p}sfunc(int) RETURNS int "
            "AS $$ SELECT COALESCE($1, 0) + 1 $$ LANGUAGE SQL;"
        )
    if sig == "single_argtype":
        return (
            f"CREATE FUNCTION {p}sfunc(int, int) RETURNS int "
            "AS $$ SELECT COALESCE($1, 0) + $2 $$ LANGUAGE SQL;"
        )
    return (
        f"CREATE FUNCTION {p}sfunc(int, int, text) RETURNS int "
        "AS $$ SELECT COALESCE($1, 0) + $2 $$ LANGUAGE SQL;"
    )


def _create_agg(
    sig: str, agg_ref: str, p: str, a: dict[str, str]
) -> str:
    sig_text = _sig_text(sig, a)
    return (
        f"CREATE AGGREGATE {agg_ref}({sig_text}) "
        f"(SFUNC = {p}sfunc, STYPE = int);"
    )


def _dependent_view_sql(
    case: DropAggregateFactorCase,
    a: dict[str, str],
    p: str,
    agg_ref: str,
) -> str:
    sig = a.get("aggregate_signature", "star_zero_arg")
    if sig == "star_zero_arg":
        return f"CREATE VIEW {p}depv AS SELECT {agg_ref}(*) FROM {p}t;"
    if sig == "single_argtype":
        return f"CREATE VIEW {p}depv AS SELECT {agg_ref}(c1) FROM {p}t;"
    if sig == "multi_argtype":
        return (
            f"CREATE VIEW {p}depv AS SELECT {agg_ref}(c1, c2) FROM {p}t;"
        )
    return (
        f"CREATE VIEW {p}depv AS SELECT {agg_ref}(c1 ORDER BY c2) "
        f"FROM {p}t;"
    )


def _dependent_function_sql(
    case: DropAggregateFactorCase,
    a: dict[str, str],
    p: str,
    agg_ref: str,
) -> str:
    sig = a.get("aggregate_signature", "star_zero_arg")
    if sig == "star_zero_arg":
        return (
            f"CREATE FUNCTION {p}depfn() RETURNS int "
            f"AS $$ SELECT {agg_ref}(*) FROM {p}t $$ LANGUAGE SQL;"
        )
    if sig == "single_argtype":
        return (
            f"CREATE FUNCTION {p}depfn() RETURNS int "
            f"AS $$ SELECT {agg_ref}(c1) FROM {p}t $$ LANGUAGE SQL;"
        )
    if sig == "multi_argtype":
        return (
            f"CREATE FUNCTION {p}depfn() RETURNS int "
            f"AS $$ SELECT {agg_ref}(c1, c2) FROM {p}t $$ LANGUAGE SQL;"
        )
    return (
        f"CREATE FUNCTION {p}depfn() RETURNS int "
        f"AS $$ SELECT {agg_ref}(c1 ORDER BY c2) FROM {p}t $$ "
        "LANGUAGE SQL;"
    )


def _resolve_case(case: DropAggregateFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case)
    agg_ref = _agg_name(case, a, p)
    needs_schema = _needs_schema(a)
    needs_dep = _needs_dependent(case, a)
    dep_kind = _dependent_kind(a) if needs_dep else ""
    sig = a.get("aggregate_signature", "star_zero_arg")
    multiple = a.get("multiple_aggregates", "single")

    setup: list[str] = []
    locus = "target.aggregate"

    # --- schema fixture -------------------------------------------------
    if needs_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}schema;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # aggregate and dependent fixtures so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        if needs_schema:
            setup.append(f"GRANT USAGE ON SCHEMA {p}schema TO {p}actor;")
        locus = "fixture.privilege_state"

    # --- sfunc + target aggregate fixture (as superuser, before SET ROLE)
    if fixture_kind == "aggregate":
        setup.append(_sfunc_create(sig, p))
        setup.append(_create_agg(sig, agg_ref, p, a))
        if (
            multiple == "multiple_comma_separated"
            and case.kind not in ("EXT", "RISK")
        ):
            agg2 = _agg2_name(a, p)
            setup.append(_create_agg(sig, agg2, p, a))
        locus = "fixture.object_state"
    else:
        setup.append(
            "SELECT 1 AS target_aggregate_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        setup.append(f"CREATE TABLE {p}t (c1 int, c2 text);")
        if dep_kind == "function":
            setup.append(
                _dependent_function_sql(case, a, p, agg_ref)
            )
        else:
            setup.append(_dependent_view_sql(case, a, p, agg_ref))
        locus = "fixture.dependency_state"

    # --- arm the non-owner role (AFTER aggregate/dependent creation) -----
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    drop_sig = _drop_sig_text(case, a)
    if (
        multiple == "multiple_comma_separated"
        and case.kind not in ("EXT", "RISK")
        and fixture_kind == "aggregate"
    ):
        agg2 = _agg2_name(a, p)
        target = (
            f"DROP AGGREGATE {if_exists}{agg_ref}({drop_sig}), "
            f"{agg2}({drop_sig})"
        )
    else:
        target = f"DROP AGGREGATE {if_exists}{agg_ref}({drop_sig})"
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
    correct_sig = _sig_text(sig, a)
    drop_mode = a.get("cleanup_mode", "DROP_AGGREGATE_CASCADE")
    if case.factor_key == "cleanup_mode":
        drop_mode = case.factor_value
    if drop_mode == "DROP_DEPENDENT_OBJECTS_FIRST":
        aggregate_drop = f"DROP AGGREGATE IF EXISTS {agg_ref}({correct_sig});"
    else:
        aggregate_drop = (
            f"DROP AGGREGATE IF EXISTS {agg_ref}({correct_sig}) CASCADE;"
        )
    cleanup_aggregate_drop = (
        f"DROP AGGREGATE IF EXISTS {agg_ref}({correct_sig}) CASCADE;"
    )
    sfunc_drop = f"DROP FUNCTION IF EXISTS {p}sfunc CASCADE;"
    roles = _role_names(case, p, effective)
    schema_drop = (
        [f"DROP SCHEMA IF EXISTS {p}schema CASCADE;"] if needs_schema else []
    )
    dep_drops: list[str] = []
    if needs_dep:
        if dep_kind == "function":
            dep_drops.append(f"DROP FUNCTION IF EXISTS {p}depfn CASCADE;")
        else:
            dep_drops.append(f"DROP VIEW IF EXISTS {p}depv CASCADE;")
        dep_drops.append(f"DROP TABLE IF EXISTS {p}t CASCADE;")
    if multiple == "multiple_comma_separated" and fixture_kind == "aggregate":
        agg2 = _agg2_name(a, p)
        cleanup_aggregate2_drop = (
            f"DROP AGGREGATE IF EXISTS {agg2}({correct_sig}) CASCADE;"
        )
    else:
        cleanup_aggregate2_drop = ""
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: DROP TABLE first (bookend first segment when tables exist),
    # then dependent objects, aggregate, sfunc, schema, and role drops.
    pre_cleanup: list[str] = []
    if needs_dep:
        pre_cleanup.append(f"DROP TABLE IF EXISTS {p}t CASCADE;")
    pre_cleanup.extend(
        d for d in dep_drops if "DROP TABLE" not in d
    )
    pre_cleanup.append(aggregate_drop)
    if cleanup_aggregate2_drop:
        pre_cleanup.append(cleanup_aggregate2_drop)
    pre_cleanup.append(sfunc_drop)
    pre_cleanup.extend(schema_drop)
    pre_cleanup.extend(
        f"DROP ROLE IF EXISTS {role};" for role in roles
    )
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then aggregate/sfunc/dependent/schema/role drops,
    # then DROP TABLE last (bookend last segment when tables exist).
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(cleanup_aggregate_drop)
    if cleanup_aggregate2_drop:
        cleanup.append(cleanup_aggregate2_drop)
    cleanup.append(sfunc_drop)
    cleanup.extend(
        d for d in dep_drops if "DROP TABLE" not in d
    )
    cleanup.extend(schema_drop)
    cleanup.extend(role_drops)
    if needs_dep:
        cleanup.append(f"DROP TABLE IF EXISTS {p}t CASCADE;")
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


def resolve_drop_aggregate_factor_witness(
    case: DropAggregateFactorCase | DropAggregateFactorExtensionCase,
    repository_root: Path,
) -> DropAggregateFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropAggregateFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_aggregate(sql: str) -> int:
    """Count the single credited DROP AGGREGATE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*DROP\s+AGGREGATE\b", region))


def _header(case: DropAggregateFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP AGGREGATE {case.factor_key}={case.factor_value}",
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


def render_drop_aggregate_factor_case(
    case: DropAggregateFactorCase | DropAggregateFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP AGGREGATE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地聚合和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP AGGREGATE。")
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


def generate_drop_aggregate_factor_programs(
    baseline_plan: DropAggregateFactorLoopPlan,
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
    case: DropAggregateFactorCase | DropAggregateFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_aggregate_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropAggregateFactorRenderError",
    "DropAggregateFactorWitness",
    "count_primary_drop_aggregate",
    "generate_drop_aggregate_factor_programs",
    "render_drop_aggregate_factor_case",
    "resolve_drop_aggregate_factor_witness",
]
