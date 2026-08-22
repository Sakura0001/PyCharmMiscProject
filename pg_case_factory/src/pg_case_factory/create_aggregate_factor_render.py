"""Render complete PostgreSQL 18.4 CREATE AGGREGATE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE AGGREGATE is a DDL statement that creates a routine
(``pg_proc``/``pg_aggregate`` catalog row), not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_proc`` /
``pg_catalog.pg_aggregate`` (exempt from the file-prefix style gate).  No
case creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is never
emitted (``_tables_to_drop`` always returns ``[]``).  Every catalog
SELECT carries a top-level ``ORDER BY`` so the catalog-observability gate
passes.

The quoted-identifier gate is respected: quoted / reserved-word /
schema-qualified aggregate names are byte-observable only in the
``CREATE AGGREGATE`` target line (a routine identifier, not a table).
All ``FROM``/``JOIN`` targets use plain unquoted ``pg_catalog.*`` names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_aggregate_factor_extension import (
    CreateAggregateFactorExtensionCase,
    _present_failure_pair,
)
from .create_aggregate_factor_loop import (
    CreateAggregateFactorCase,
    CreateAggregateFactorLoopPlan,
)
from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/aggregate/"
    "create_aggregate.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/aggregate/"
    "create_aggregate.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateAggregateFactorRenderError(ValueError):
    """Raised when a CREATE AGGREGATE case cannot be rendered."""


@dataclass(frozen=True)
class CreateAggregateFactorWitness:
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


def _synthetic_case(
    ext: CreateAggregateFactorExtensionCase,
) -> CreateAggregateFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "regular")
    return CreateAggregateFactorCase(
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
    case: CreateAggregateFactorCase
    | CreateAggregateFactorExtensionCase,
) -> CreateAggregateFactorCase:
    if isinstance(case, CreateAggregateFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateAggregateFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


# --- type mapping -------------------------------------------------------

_TYPE_MAP: dict[str, str] = {
    "integer": "integer",
    "bigint": "bigint",
    "numeric": "numeric",
    "float8": "float8",
    "text": "text",
    "boolean": "boolean",
    "date": "date",
    "timestamp": "timestamp",
    "anyelement": "anyelement",
    "internal": "internal",
}


def _arg_type(a: dict[str, str]) -> str:
    return _TYPE_MAP.get(a.get("arg_data_type", "integer"), "integer")


def _state_type(a: dict[str, str]) -> str:
    """STYPE (state data type) — mirrors arg_data_type for simplicity."""
    return _arg_type(a)


def _return_type(a: dict[str, str]) -> str:
    """The aggregate's return type (same as arg_data_type unless finalfunc)."""
    return _arg_type(a)


# --- name shapes --------------------------------------------------------

def _schema_name(p: str) -> str:
    return f"{p}nsp"


def _needs_schema(a: dict[str, str]) -> bool:
    return (
        a.get("aggregate_name_shape", "plain_identifier")
        == "schema_qualified"
        or a.get("sfunc_name_shape", "plain") == "schema_qualified"
    )


def _aggregate_name(a: dict[str, str], p: str) -> str:
    """The aggregate name token in CREATE AGGREGATE (may be quoted/dotted)."""

    shape = a.get("aggregate_name_shape", "plain_identifier")
    base = f"{p}agg"
    if shape == "quoted_identifier":
        return f'"{p}Mixed Agg"'
    if shape == "reserved_word":
        return '"order"'
    if shape == "schema_qualified":
        return f"{_schema_name(p)}.{base}"
    return base


def _aggregate_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("aggregate_name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}Mixed Agg"
    if shape == "reserved_word":
        return "order"
    return f"{p}agg"


def _sfunc_name(a: dict[str, str], p: str) -> str:
    """The sfunc name token (may be schema-qualified)."""

    shape = a.get("sfunc_name_shape", "plain")
    base = f"{p}sfunc"
    if shape == "schema_qualified":
        return f"{_schema_name(p)}.{base}"
    return base


def _ffunc_name(p: str) -> str:
    return f"{p}ffunc"


def _combinefunc_name(p: str) -> str:
    return f"{p}combine"


# --- argument spec -----------------------------------------------------

def _arg_spec(a: dict[str, str]) -> str:
    """The argument spec inside the parentheses of CREATE AGGREGATE."""

    action = a.get("target_action", "regular")
    form = a.get("aggregate_form", "single_arg")
    argmode = a.get("argmode_shape", "IN_default")
    argname = a.get("argname_shape", "absent")
    atype = _arg_type(a)
    iosv = a.get("invalid_ordered_set_variadic", "")

    # argname token
    if argname == "plain":
        name_tok = f"{argmode_prefix(argmode)}v "
    elif argname == "quoted":
        name_tok = f'{argmode_prefix(argmode)}"arg name" '
    else:
        name_tok = argmode_prefix(argmode)

    if action == "old_syntax" or form == "old_syntax":
        return f"BASETYPE = {atype}"

    if form == "zero_arg":
        return ""

    if action == "ordered_set" or form == "ordered_set":
        if iosv == "non_variadic_any":
            return f"ORDER BY VARIADIC {atype}"
        return f"ORDER BY {atype}"

    if form == "multi_arg":
        return f"{name_tok}{atype}, {name_tok}{atype}"

    # single_arg (default)
    return f"{name_tok}{atype}"


def argmode_prefix(argmode: str) -> str:
    if argmode == "IN_explicit":
        return "IN "
    if argmode == "VARIADIC":
        return "VARIADIC "
    return ""


# --- sfunc signature ---------------------------------------------------

def _sfunc_sig(a: dict[str, str]) -> str:
    """The sfunc function signature for CREATE FUNCTION."""

    form = a.get("aggregate_form", "single_arg")
    atype = _arg_type(a)
    stype = _state_type(a)
    sfd = a.get("support_function_dependency", "sfunc_exists")
    ssm = a.get("sfunc_signature_mismatch", "")

    # Wrong-signature sfunc
    if sfd == "sfunc_wrong_signature" or ssm == "wrong_input_types":
        return f"text, text"
    if ssm == "wrong_return_type":
        return f"{stype}, {atype}"

    if form == "zero_arg":
        return stype
    if form == "multi_arg":
        return f"{stype}, {atype}, {atype}"
    return f"{stype}, {atype}"


def _sfunc_return(a: dict[str, str]) -> str:
    """The sfunc return type for CREATE FUNCTION."""

    ssm = a.get("sfunc_signature_mismatch", "")
    stype = _state_type(a)
    if ssm == "wrong_return_type":
        return "text"
    return stype


def _sfunc_body(a: dict[str, str]) -> str:
    return "$$ SELECT $1 $$"


# --- aggregate options --------------------------------------------------

def _aggregate_options(a: dict[str, str], p: str) -> str:
    """The options clause: SFUNC, STYPE, and optional extras."""

    parts: list[str] = []
    sfunc = _sfunc_name(a, p)
    stype = _state_type(a)
    action = a.get("target_action", "regular")
    form = a.get("aggregate_form", "single_arg")

    if action == "old_syntax" or form == "old_syntax":
        atype = _arg_type(a)
        parts.append(f"BASETYPE = {atype}")
        parts.append(f"SFUNC = {sfunc}")
        parts.append(f"STYPE = {stype}")
    else:
        parts.append(f"SFUNC = {sfunc}")
        parts.append(f"STYPE = {stype}")

    ffd = a.get("finalfunc_dependency", "not_exists")
    if ffd == "exists":
        parts.append(f"FINALFUNC = {_ffunc_name(p)}")
    if ffd == "wrong_return_type":
        parts.append(f"FINALFUNC = {_ffunc_name(p)}")

    cfd = a.get("combinefunc_dependency", "not_exists")
    if cfd == "exists":
        parts.append(f"COMBINEFUNC = {_combinefunc_name(p)}")

    parallel = a.get("parallel_option", "UNSAFE_default")
    if parallel == "SAFE":
        parts.append("PARALLEL = SAFE")
    elif parallel == "RESTRICTED":
        parts.append("PARALLEL = RESTRICTED")

    return ", ".join(parts)


def _or_replace(a: dict[str, str]) -> str:
    orc = a.get("or_replace_clause", "absent")
    if orc in (
        "present_replace_existing",
        "present_replace_with_constraint_violation",
    ):
        return "OR REPLACE "
    return ""


# --- target statement ---------------------------------------------------

def _build_target(
    a: dict[str, str], p: str, agg_name: str
) -> str:
    """The primary CREATE AGGREGATE statement."""

    or_rep = _or_replace(a)
    spec = _arg_spec(a)
    options = _aggregate_options(a, p)
    return (
        f"CREATE {or_rep}AGGREGATE {agg_name} ({spec}) "
        f"({options});"
    )


# --- probe / verification ----------------------------------------------

def _probe_select(
    case: CreateAggregateFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_aggregate_catalog_query")
    name_lit = _aggregate_name_literal(a, p)
    action = a.get("target_action", "regular")
    form = a.get("aggregate_form", "single_arg")

    if mode == "actual_execution":
        if case.outcome == "expected_failure":
            return None
        atype = _arg_type(a)
        if form == "zero_arg":
            call = f"{_aggregate_name(a, p)}()"
        elif action == "ordered_set" or form == "ordered_set":
            call = f"{_aggregate_name(a, p)}(NULL::{atype} ORDER BY NULL::{atype})"
        else:
            call = f"{_aggregate_name(a, p)}(NULL::{atype})"
        return (
            f"SELECT count(*) AS agg_executable "
            f"FROM (SELECT {call} AS r) s "
            f"ORDER BY count(*);"
        )

    if mode == "pg_proc_query":
        return (
            f"SELECT count(*) AS proc_exists "
            f"FROM pg_catalog.pg_proc "
            f"WHERE proname = '{name_lit}' "
            f"ORDER BY count(*);"
        )

    # pg_aggregate_catalog_query (default)
    return (
        f"SELECT count(*) AS agg_exists "
        f"FROM pg_catalog.pg_aggregate a "
        f"JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid "
        f"WHERE p.proname = '{name_lit}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: CreateAggregateFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE AGGREGATE is a DDL statement that creates a routine, not a
    table.  The bookend (DROP TABLE IF EXISTS) is therefore never emitted.
    """
    return []


# --- case resolution ----------------------------------------------------

def _resolve_case(
    case: CreateAggregateFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "regular")
    os_ = a.get("object_state", "not_exists")
    sfd = a.get("support_function_dependency", "sfunc_exists")
    ffd = a.get("finalfunc_dependency", "not_exists")
    cfd = a.get("combinefunc_dependency", "not_exists")
    pl = a.get("privilege_level", "aggregate_owner")
    orc = a.get("or_replace_clause", "absent")

    setup: list[str] = []
    locus = "target.create_aggregate"

    # --- schema fixture ------------------------------------------------
    if _needs_schema(a):
        setup.append(
            f"CREATE SCHEMA IF NOT EXISTS {_schema_name(p)};"
        )
        locus = "fixture.schema"

    # --- role fixture (non-owner) --------------------------------------
    if pl == "non_owner":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(
            f"GRANT USAGE ON SCHEMA public TO {p}actor;"
        )
        if _needs_schema(a):
            setup.append(
                f"GRANT USAGE ON SCHEMA {_schema_name(p)} TO {p}actor;"
            )
        locus = "fixture.privilege_state"

    # --- sfunc fixture -------------------------------------------------
    if sfd != "sfunc_not_exists" and sfd != "sfunc_not_found":
        sfunc = _sfunc_name(a, p)
        sig = _sfunc_sig(a)
        ret = _sfunc_return(a)
        body = _sfunc_body(a)
        setup.append(
            f"CREATE FUNCTION {sfunc}({sig}) "
            f"RETURNS {ret} AS {body} LANGUAGE SQL;"
        )
        locus = "fixture.sfunc"

    # --- ffunc fixture -------------------------------------------------
    if ffd == "exists":
        stype = _state_type(a)
        rtype = _return_type(a)
        setup.append(
            f"CREATE FUNCTION {_ffunc_name(p)}({stype}) "
            f"RETURNS {rtype} AS $$ SELECT $1 $$ LANGUAGE SQL;"
        )
        locus = "fixture.ffunc"
    elif ffd == "wrong_return_type":
        stype = _state_type(a)
        setup.append(
            f"CREATE FUNCTION {_ffunc_name(p)}({stype}) "
            f"RETURNS text AS $$ SELECT $1::text $$ LANGUAGE SQL;"
        )
        locus = "fixture.ffunc_wrong"

    # --- combinefunc fixture -------------------------------------------
    if cfd == "exists":
        stype = _state_type(a)
        setup.append(
            f"CREATE FUNCTION {_combinefunc_name(p)}({stype}, {stype}) "
            f"RETURNS {stype} AS $$ SELECT $1 $$ LANGUAGE SQL;"
        )
        locus = "fixture.combinefunc"

    # --- pre-existing aggregate (already_exists) -----------------------
    if os_ == "already_exists":
        agg_name = _aggregate_name(a, p)
        spec = _arg_spec(a)
        options = _aggregate_options(a, p)
        setup.append(
            f"CREATE AGGREGATE {agg_name} ({spec}) ({options});"
        )
        locus = "fixture.pre_existing_aggregate"

    # --- OR REPLACE constraint violation fixture ------------------------
    if orc == "present_replace_with_constraint_violation":
        # The existing aggregate has a DIFFERENT signature so OR REPLACE
        # with changed arg types fails.  Create a different-arg aggregate
        # first, then try to OR REPLACE with the primary arg type.
        agg_name = _aggregate_name(a, p)
        sfunc = _sfunc_name(a, p)
        stype = _state_type(a)
        atype = _arg_type(a)
        # Use a different arg type for the pre-existing aggregate
        existing_type = "text" if atype != "text" else "bigint"
        setup.append(
            f"CREATE FUNCTION {sfunc}({stype}, {existing_type}) "
            f"RETURNS {stype} AS $$ SELECT $1 $$ LANGUAGE SQL;"
        )
        setup.append(
            f"CREATE AGGREGATE {agg_name} ({existing_type}) "
            f"(SFUNC = {sfunc}, STYPE = {stype});"
        )
        locus = "fixture.or_replace_conflict"

    # --- arm the effective role ----------------------------------------
    if pl == "non_owner":
        setup.append(f"SET ROLE {p}actor;")

    # --- the primary target statement ---------------------------------
    target = _build_target(a, p, _aggregate_name(a, p))

    # --- oracle / SQLSTATE assertion ----------------------------------
    assert_lines: list[str] = []
    if pl == "non_owner":
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction ------------------------------------------
    agg_name = _aggregate_name(a, p)
    atype = _arg_type(a)
    stype = _state_type(a)

    # The aggregate signature for DROP
    form = a.get("aggregate_form", "single_arg")
    action = a.get("target_action", "regular")
    if form == "zero_arg":
        drop_sig = ""
    elif action == "ordered_set" or form == "ordered_set":
        drop_sig = f"({atype})"
    else:
        drop_sig = f"({atype})"

    # Idempotent bookends via the shared cleanup_bookend helper. Every DROP
    # carries IF EXISTS (safe on a fresh database AND on run-02, where run-01's
    # cleanup already dropped the objects), and DROP OWNED BY is unreachable in
    # pre-cleanup -- the role may not exist yet on a fresh database, which
    # previously crashed the run before the target statement. Post-target
    # cleanup drops owned objects then the role.
    sfunc = _sfunc_name(a, p)
    specs: list[DropSpec] = [DropSpec("AGGREGATE", agg_name, drop_sig)]
    specs.append(DropSpec("FUNCTION", sfunc, f"({_sfunc_sig(a)})"))
    if ffd == "exists" or ffd == "wrong_return_type":
        specs.append(DropSpec("FUNCTION", _ffunc_name(p), f"({stype})"))
    if cfd == "exists":
        specs.append(DropSpec("FUNCTION", _combinefunc_name(p), f"({stype}, {stype})"))

    schemas = (_schema_name(p),) if _needs_schema(a) else ()
    roles = (f"{p}actor",) if pl == "non_owner" else ()

    pre_bookend = build_pre_cleanup(specs=specs, schemas=schemas, roles=roles)
    cln_bookend = build_cleanup(
        specs=specs,
        schemas=schemas,
        roles=roles,
        drop_owned=bool(roles),
        reset_role=bool(roles),
    )
    pre_cleanup = pre_bookend.statements
    cleanup = cln_bookend.statements

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


def resolve_create_aggregate_factor_witness(
    case: CreateAggregateFactorCase
    | CreateAggregateFactorExtensionCase,
    repository_root: Path,
) -> CreateAggregateFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateAggregateFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_aggregate(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+(?:OR\s+REPLACE\s+)?AGGREGATE\b", region)
    )


def _header(case: CreateAggregateFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE AGGREGATE {case.factor_key}="
        f"{case.factor_value}",
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


def render_create_aggregate_factor_case(
    case: CreateAggregateFactorCase
    | CreateAggregateFactorExtensionCase,
    repository_root: Path,
) -> str:
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。")
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


def _write_program(
    case: CreateAggregateFactorCase
    | CreateAggregateFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_aggregate_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_aggregate_factor_programs(
    baseline_plan: CreateAggregateFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
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


__all__ = [
    "CreateAggregateFactorRenderError",
    "CreateAggregateFactorWitness",
    "count_primary_create_aggregate",
    "generate_create_aggregate_factor_programs",
    "render_create_aggregate_factor_case",
    "resolve_create_aggregate_factor_witness",
]
