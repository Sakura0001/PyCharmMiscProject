"""Render complete PostgreSQL 18.4 CREATE OPERATOR factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE OPERATOR is a catalog-row DDL statement: the target is a
``pg_catalog.pg_operator`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_operator`` (exempt
from the file-prefix style gate).  No case creates a TABLE, so the
bookend (DROP TABLE IF EXISTS) is never emitted.  Every catalog SELECT
carries a top-level ``ORDER BY`` so the catalog-observability gate
passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_operator_factor_extension import (
    CreateOperatorFactorExtensionCase,
    _present_failure_pair,
)
from .create_operator_factor_loop import (
    CreateOperatorFactorCase,
    CreateOperatorFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/operator/"
    "create_operator.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/operator/"
    "create_operator.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateOperatorFactorRenderError(ValueError):
    """Raised when a CREATE OPERATOR case cannot be rendered."""


@dataclass(frozen=True)
class CreateOperatorFactorWitness:
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
    ext: CreateOperatorFactorExtensionCase,
) -> CreateOperatorFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = assignment.get(
            "target_form", ext.consumer_action_id
        )
    return CreateOperatorFactorCase(
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
    case: CreateOperatorFactorCase
    | CreateOperatorFactorExtensionCase,
) -> CreateOperatorFactorCase:
    if isinstance(case, CreateOperatorFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateOperatorFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


_PgType = {
    "integer": "integer",
    "text": "text",
    "boolean": "boolean",
    "numeric": "numeric",
    "custom_type": None,  # filled per-case
}


def _operand_type(a: dict[str, str], p: str) -> str:
    """The PG type name used for LEFTARG/RIGHTARG and the function."""

    odt = a.get("operand_data_type", "integer")
    if odt == "custom_type":
        return f"{p}dtype"
    return _PgType.get(odt, "integer")


def _operator_name(a: dict[str, str], p: str) -> str:
    """The operator identifier in CREATE OPERATOR."""

    shape = a.get("name_shape", "plain_identifier")
    schema = f"{p}schema"
    if shape == "quoted_identifier":
        return f'"{schema}".==='
    # plain_identifier and schema_qualified both use a plain
    # schema-qualified operator name; quoted_identifier quotes
    # the schema to keep the factor byte-observable in the target.
    return f"{schema}.==="


def _function_name(a: dict[str, str], p: str) -> str:
    """The function name referenced by FUNCTION = ..."""

    shape = a.get("function_name_shape", "plain_function")
    schema = f"{p}schema"
    fn = f"{p}opfn"
    if shape == "missing_function":
        return f"{schema}.{p}nofn"
    # plain_function and schema_qualified_function both use a
    # schema-qualified reference so the function resolves without
    # relying on search_path.
    return f"{schema}.{fn}"


def _schema_name(a: dict[str, str], p: str) -> str:
    return f"{p}schema"


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("target_object_state") in ("exists", "exists_conflict")


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _present(a: dict[str, str]) -> bool:
    """Whether the operator exists after the target statement."""
    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _is_binary(a: dict[str, str]) -> bool:
    return a.get("operand_type_shape") == "binary_operator"


def _effective_role(a: dict[str, str], p: str) -> str:
    priv = a.get("privilege_context", "schema_create_privilege")
    if priv == "insufficient_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _effective_role(a, p):
        roles.append(f"{p}actor")
    return tuple(roles)


def _build_function_setup(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup lines for the operator function fixture."""

    ds = a.get("dependency_state", "ready")
    fns = a.get("function_name_shape", "plain_function")
    if fns == "missing_function" or ds == "missing_function":
        return []

    schema = _schema_name(a, p)
    fn = f"{p}opfn"
    otype = _operand_type(a, p)
    is_binary = _is_binary(a)

    if ds == "wrong_signature":
        if is_binary:
            return [
                f"CREATE FUNCTION {schema}.{fn}({otype}, {otype}) "
                f"RETURNS integer AS 'SELECT 1' LANGUAGE SQL IMMUTABLE;"
            ]
        return [
            f"CREATE FUNCTION {schema}.{fn}({otype}) "
            f"RETURNS integer AS 'SELECT 1' LANGUAGE SQL IMMUTABLE;"
        ]

    if is_binary:
        return [
            f"CREATE FUNCTION {schema}.{fn}({otype}, {otype}) "
            f"RETURNS boolean AS 'SELECT true' LANGUAGE SQL IMMUTABLE;"
        ]
    return [
        f"CREATE FUNCTION {schema}.{fn}({otype}) "
        f"RETURNS boolean AS 'SELECT true' LANGUAGE SQL IMMUTABLE;"
    ]


def _build_custom_type_setup(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup lines for the custom type fixture."""

    if a.get("operand_data_type") != "custom_type":
        return []
    schema = _schema_name(a, p)
    dtype = f"{p}dtype"
    return [
        f"CREATE TYPE {schema}.{dtype} AS ENUM ('a', 'b');"
    ]


def _build_duplicate_setup(
    a: dict[str, str], p: str
) -> list[str]:
    """Pre-create the operator for duplicate-signature tests."""

    if not _is_duplicate(a):
        return []

    schema = _schema_name(a, p)
    fn = f"{p}opfn"
    otype = _operand_type(a, p)
    is_binary = _is_binary(a)

    if is_binary:
        create = (
            f"CREATE OPERATOR {schema}.=== "
            f"(FUNCTION = {schema}.{fn}, "
            f"LEFTARG = {otype}, RIGHTARG = {otype});"
        )
    else:
        create = (
            f"CREATE OPERATOR {schema}.=== "
            f"(FUNCTION = {schema}.{fn}, "
            f"RIGHTARG = {otype});"
        )
    return [create]


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary CREATE OPERATOR statement."""

    name = _operator_name(a, p)
    schema = _schema_name(a, p)
    fn = _function_name(a, p)
    otype = _operand_type(a, p)
    is_binary = _is_binary(a)

    kw = "PROCEDURE" if a.get("function_clause") == "procedure_keyword" else "FUNCTION"
    parts: list[str] = [f"{kw} = {fn}"]
    if is_binary:
        parts.append(f"LEFTARG = {otype}")
    parts.append(f"RIGHTARG = {otype}")

    if a.get("commutator_clause") == "present":
        parts.append(f"COMMUTATOR = OPERATOR({schema}.===)")
    if a.get("negator_clause") == "present":
        parts.append(f"NEGATOR = OPERATOR({schema}.===)")
    if a.get("restrict_clause") == "present":
        parts.append("RESTRICT = pg_catalog.eqsel")
    if a.get("join_clause") == "present":
        parts.append("JOIN = pg_catalog.eqjoinsel")
    if a.get("hashes_clause") == "present":
        parts.append("HASHES")
    if a.get("merges_clause") == "present":
        parts.append("MERGES")

    return f"CREATE OPERATOR {name} ({', '.join(parts)});"


def _probe_select(
    case: CreateOperatorFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query")
    schema = _schema_name(a, p)
    otype = _operand_type(a, p)
    is_binary = _is_binary(a)

    if mode == "error_assertion":
        if _is_failure(a):
            return None
        return None

    if mode == "effect_query":
        if _present(a):
            if is_binary:
                return (
                    f"SELECT 1::integer OPERATOR({schema}.===) "
                    f"1::integer AS effect_check ORDER BY 1;"
                )
            return (
                f"SELECT OPERATOR({schema}.===) 1::{otype} "
                f"AS effect_check ORDER BY 1;"
            )
        return None

    # catalog_query
    if _present(a):
        cmp_op = ">"
    else:
        cmp_op = "="
    type_filter = (
        f"AND oprright = '{otype}'::regtype" if _present(a) else ""
    )
    return (
        f"SELECT count(*) {cmp_op} 0 AS operator_state "
        f"FROM pg_catalog.pg_operator "
        f"WHERE oprname = '===' "
        f"AND oprnamespace = '{schema}'::regnamespace "
        f"{type_filter} "
        f"ORDER BY count(*);"
    ).replace("  ", " ")


def _resolve_case(
    case: CreateOperatorFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _schema_name(a, p)

    setup: list[str] = []
    locus = "target.create_operator"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- schema fixture ---
    setup.append(f"CREATE SCHEMA {schema};")
    locus = "fixture.schema"

    # --- custom type fixture ---
    setup.extend(_build_custom_type_setup(a, p))

    # --- operator function fixture ---
    setup.extend(_build_function_setup(a, p))
    if a.get("dependency_state") in ("ready", "wrong_signature"):
        locus = "fixture.operator_function"

    # --- duplicate operator fixture ---
    setup.extend(_build_duplicate_setup(a, p))
    if _is_duplicate(a):
        locus = "fixture.duplicate_operator"

    # --- role fixture for privilege tests ---
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        setup.append(f"GRANT USAGE ON SCHEMA {schema} TO {p}actor;")
        locus = "fixture.privilege_state"

    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement ---
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction ---
    cleanup_mode = a.get("cleanup_mode", "drop_objects")
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    if cleanup_mode == "drop_objects":
        otype = _operand_type(a, p)
        is_binary = _is_binary(a)
        if is_binary:
            cleanup.append(
                f"DROP OPERATOR IF EXISTS {schema}.=== "
                f"({otype}, {otype}) CASCADE;"
            )
        else:
            cleanup.append(
                f"DROP OPERATOR IF EXISTS {schema}.=== "
                f"({otype}) CASCADE;"
            )
        cleanup.append(f"DROP FUNCTION IF EXISTS {schema}.{p}opfn CASCADE;")
        if a.get("operand_data_type") == "custom_type":
            cleanup.append(f"DROP TYPE IF EXISTS {schema}.{p}dtype CASCADE;")
        cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    else:  # reset_state
        if effective:
            cleanup.append("RESET ROLE;")
        cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")

    for role in roles:
        cleanup.append(f"DROP OWNED BY {role} CASCADE;")
        cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # --- pre-cleanup (safe, always IF EXISTS CASCADE) ---
    pre_cleanup: list[str] = []
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

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


def _header(case: CreateOperatorFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE OPERATOR {case.factor_key}="
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


def render_create_operator_factor_case(
    case: CreateOperatorFactorCase
    | CreateOperatorFactorExtensionCase,
    repository_root: Path,
) -> str:
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR。")
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
    case: CreateOperatorFactorCase
    | CreateOperatorFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_operator_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_operator_factor_programs(
    baseline_plan: CreateOperatorFactorLoopPlan,
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


def count_primary_create_operator(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+OPERATOR\b", region)
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str, case: object
) -> str:
    """Mutation helper: remove primary target SQL but keep comment lines."""

    if _PRIMARY_BEGIN not in sql or _PRIMARY_END not in sql:
        return sql
    before_begin, rest = sql.split(_PRIMARY_BEGIN, 1)
    target_and_after, after_end = rest.split(_PRIMARY_END, 1)
    comment_lines = [
        line
        for line in target_and_after.split("\n")
        if line.strip().startswith("--") or not line.strip()
    ]
    return (
        before_begin
        + _PRIMARY_BEGIN
        + "\n".join(comment_lines)
        + _PRIMARY_END
        + after_end
    )


def resolve_create_operator_factor_witness(
    case: CreateOperatorFactorCase
    | CreateOperatorFactorExtensionCase,
    repository_root: Path,
) -> CreateOperatorFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateOperatorFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


__all__ = [
    "CreateOperatorFactorRenderError",
    "CreateOperatorFactorWitness",
    "count_primary_create_operator",
    "generate_create_operator_factor_programs",
    "render_create_operator_factor_case",
    "resolve_create_operator_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
