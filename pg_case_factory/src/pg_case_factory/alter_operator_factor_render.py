"""Five-section byte-contract renderer for ALTER OPERATOR factor-loop SQL.

Every case is rendered into one deterministic ``.sql`` program with the
canonical sections:

    1. pre-cleanup (best-effort DROP IF EXISTS)
    2. \set ON_ERROR_STOP on / setup fixtures (schema, type, procs, operator,
       roles, SET ROLE)
    3. \set ON_ERROR_STOP off (when expected_failure) /
       -- primary-target-begin / ALTER OPERATOR ... ; /
       -- primary-target-end /
       \set target_sqlstate :SQLSTATE / \echo PGCF_TARGET_SQLSTATE=...
    4. oracle (catalog-audit ``SELECT count(*) <op> AS alias ... ORDER BY
       count(*) LIMIT 1;`` + sqlstate assertion)
    5. cleanup (DROP OPERATOR / functions / type / schema / roles)

The owner-transfer branch reuses the SESSION_USER no-op transfer salvage and
the SET-ROLE / RESET-ROLE privilege fixture from ``alter_large_object``.
Extension cases are lifted into a baseline-shaped synthetic case so the
renderer reads the crossed privilege axis from the assignment.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_operator_factor_loop import (
    AlterOperatorFactorCase,
    AlterOperatorFactorLoopPlan,
    build_alter_operator_factor_loop_plan,
)


class AlterOperatorFactorRenderError(ValueError):
    """Raised when a case cannot be rendered to canonical bytes."""


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alteroperator"
_VERSION = "1.0.0"
_AUTHOR = "pg_case_factory"
_COPYRIGHT = "Copyright (c) 2026 pg_case_factory"

_TYPE_MAP: dict[str, str] = {
    "integer": "integer",
    "text": "text",
    "boolean": "boolean",
    "custom_type": "custom_type",  # rewritten with prefix by _operand_type
}


def _operand_type(data_type: str, prefix: str) -> str:
    if data_type == "custom_type":
        return f"{prefix}custom_type"
    return _TYPE_MAP[data_type]


def _operator_signature(case_assignments: dict[str, str], prefix: str) -> tuple[str, str]:
    shape = case_assignments.get("operand_type_shape", "binary_operator")
    data_type = case_assignments.get("operand_data_type", "integer")
    right = _operand_type(data_type, prefix)
    if shape == "prefix_operator":
        return ("NONE", right)
    left = right
    return (left, right)


def _operator_name(case_assignments: dict[str, str], prefix: str) -> str:
    shape = case_assignments.get("name_shape", "plain_identifier")
    raw = f"{prefix}op"
    if shape == "quoted_identifier":
        return f'"{raw}"'
    if shape == "schema_qualified":
        return f"{prefix}sch.{raw}"
    return raw


def _owner_target(shape: str, prefix: str) -> str:
    if shape == "current_role":
        return "CURRENT_ROLE"
    if shape == "current_user":
        return "CURRENT_USER"
    if shape == "session_user":
        return "SESSION_USER"
    if shape == "missing_role":
        return f"{prefix}nonexistent_role"
    return f"{prefix}new_owner"


def _effective_role(case_assignments: dict[str, str], prefix: str) -> str:
    privilege = case_assignments.get("privilege_context", "owner")
    if privilege in ("non_owner", "insufficient_privilege"):
        return f"{prefix}actor"
    return ""


def _alter_clause(
    case_assignments: dict[str, str],
    prefix: str,
) -> str:
    branch = case_assignments.get("target_action", "owner_change")
    if branch == "owner_change":
        owner_shape = case_assignments.get("new_owner_shape", "plain_role")
        return f"OWNER TO {_owner_target(owner_shape, prefix)}"
    if branch == "set_schema":
        schema = case_assignments.get("schema_migration_state", "target_schema_exists")
        return f"SET SCHEMA {prefix}target_sch"
    if branch == "set_estimator":
        restrict = case_assignments.get("restrict_estimator", "none_value")
        if restrict == "none_value":
            return "SET RESTRICT = NONE"
        if restrict == "res_proc_name":
            return f"SET RESTRICT = {prefix}res_proc"
        if restrict == "missing_proc":
            return f"SET RESTRICT = {prefix}missing_res_proc"
        join = case_assignments.get("join_estimator", "none_value")
        if join == "none_value":
            return "SET JOIN = NONE"
        if join == "join_proc_name":
            return f"SET JOIN = {prefix}join_proc"
        if join == "missing_proc":
            return f"SET JOIN = {prefix}missing_join_proc"
    if branch == "set_commutator":
        return f"SET COMMUTATOR = {prefix}comm_op"
    if branch == "set_negator":
        return f"SET NEGATOR = {prefix}neg_op"
    if branch == "set_hashes":
        return "SET HASHES"
    if branch == "set_merges":
        return "SET MERGES"
    raise AlterOperatorFactorRenderError(f"unknown branch: {branch}")


@dataclass(frozen=True)
class _CasePlan:
    setup_lines: tuple[str, ...]
    target_sql: str
    oracle_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    expected_failure: bool


def _fixture_lines(
    case_assignments: dict[str, str],
    prefix: str,
    left_type: str,
    right_type: str,
    op_name: str,
    effective: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    setup: list[str] = []
    cleanup: list[str] = []
    op_schema = f"{prefix}sch"
    setup.append(f"CREATE SCHEMA IF NOT EXISTS {op_schema};")
    cleanup.append(f"DROP SCHEMA IF EXISTS {op_schema} CASCADE;")
    if case_assignments.get("operand_data_type") == "custom_type":
        setup.append(f"CREATE TYPE {prefix}custom_type AS (val integer);")
        cleanup.append(f"DROP TYPE IF EXISTS {prefix}custom_type CASCADE;")
    target_sch = f"{prefix}target_sch"
    if case_assignments.get("schema_migration_state") == "target_schema_exists":
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {target_sch};")
    cleanup.append(f"DROP SCHEMA IF EXISTS {target_sch} CASCADE;")
    proc_name = f"{op_schema}.{prefix}op_proc"
    setup.append(
        f"CREATE FUNCTION {proc_name}(l {left_type}, r {right_type}) "
        f"RETURNS boolean LANGUAGE SQL IMMUTABLE AS $$ SELECT false $$;"
    )
    cleanup.append(f"DROP FUNCTION IF EXISTS {proc_name} CASCADE;")
    restrict = case_assignments.get("restrict_estimator", "none_value")
    if restrict == "res_proc_name":
        res_proc = f"{op_schema}.{prefix}res_proc"
        setup.append(
            f"CREATE FUNCTION {res_proc}(internal, oid, internal, integer) "
            f"RETURNS double precision LANGUAGE SQL IMMUTABLE AS $$ SELECT 1.0 $$;"
        )
        cleanup.append(f"DROP FUNCTION IF EXISTS {res_proc} CASCADE;")
    join = case_assignments.get("join_estimator", "none_value")
    if join == "join_proc_name":
        join_proc = f"{op_schema}.{prefix}join_proc"
        setup.append(
            f"CREATE FUNCTION {join_proc}(internal, oid, internal, internal, "
            f"internal, internal, internal, internal, oid, internal) "
            f"RETURNS double precision LANGUAGE SQL IMMUTABLE AS $$ SELECT 1.0 $$;"
        )
        cleanup.append(f"DROP FUNCTION IF EXISTS {join_proc} CASCADE;")
    # Roles for the owner-transfer / privilege fixture.
    owner_shape = case_assignments.get("new_owner_shape", "plain_role")
    if case_assignments.get("target_action") == "owner_change":
        if owner_shape == "plain_role":
            setup.append(f"CREATE ROLE {prefix}new_owner LOGIN;")
            cleanup.append(f"DROP ROLE IF EXISTS {prefix}new_owner;")
        if owner_shape == "missing_role":
            setup.append(f"CREATE ROLE {prefix}nonexistent_role LOGIN;")
            cleanup.append(f"DROP ROLE IF EXISTS {prefix}nonexistent_role;")
    if effective:
        setup.append(f"CREATE ROLE {effective} LOGIN;")
        setup.append(f"GRANT {op_schema} ON SCHEMA {op_schema} TO {effective};")
        cleanup.append(f"DROP OWNED BY {effective};")
        cleanup.append(f"DROP ROLE IF EXISTS {effective};")
    object_state = case_assignments.get("target_object_state", "exists")
    if object_state == "exists":
        if case_assignments.get("operand_type_shape") == "prefix_operator":
            op_def = (
                f"CREATE OPERATOR {op_name} ( "
                f"PROCEDURE = {proc_name}, RIGHTARG = {right_type}"
            )
        else:
            op_def = (
                f"CREATE OPERATOR {op_name} ( "
                f"PROCEDURE = {proc_name}, LEFTARG = {left_type}, "
                f"RIGHTARG = {right_type}"
            )
        if restrict == "res_proc_name":
            op_def += f", RESTRICT = {op_schema}.{prefix}res_proc"
        if join == "join_proc_name":
            op_def += f", JOIN = {op_schema}.{prefix}join_proc"
        op_def += " );"
        setup.append(op_def)
    return (tuple(setup), tuple(cleanup))


def _oracle_lines(
    case_assignments: dict[str, str],
    prefix: str,
    left_type: str,
    right_type: str,
    op_name: str,
    sqlstate: str,
) -> tuple[str, ...]:
    mode = case_assignments.get("verification_mode", "catalog_query")
    target_action = case_assignments.get("target_action", "owner_change")
    # catalog-audit probe (always present for semantic locus).
    base = (
        f"SELECT count(*) AS op_present FROM pg_catalog.pg_operator "
        f"WHERE oprname = '{op_name.split('.')[-1].strip(chr(34))}' "
        f"AND oprleft = '{left_type}'::regtype "
        f"AND oprright = '{right_type}'::regtype ORDER BY count(*) LIMIT 1;"
    )
    if mode == "error_assertion":
        return (
            base,
            f"SELECT :'target_sqlstate' = '{sqlstate}' "
            f"AS target_sqlstate_matches_expected;",
        )
    if target_action == "owner_change":
        owner_shape = case_assignments.get("new_owner_shape", "plain_role")
        if owner_shape in ("current_role", "current_user"):
            owner_clause = "oprowner = (SELECT oid FROM pg_roles WHERE rolname = current_role)"
        elif owner_shape == "session_user":
            owner_clause = "oprowner = (SELECT oid FROM pg_roles WHERE rolname = session_user)"
        elif owner_shape == "plain_role":
            owner_clause = f"oprowner = (SELECT oid FROM pg_roles WHERE rolname = '{prefix}new_owner')"
        else:
            owner_clause = "oprowner IS NOT NULL"
        probe = (
            f"SELECT count(*) AS op_owner_changed FROM pg_catalog.pg_operator "
            f"WHERE oprname = '{op_name.split('.')[-1].strip(chr(34))}' "
            f"AND oprleft = '{left_type}'::regtype "
            f"AND oprright = '{right_type}'::regtype "
            f"AND {owner_clause} ORDER BY count(*) LIMIT 1;"
        )
    elif target_action == "set_schema":
        probe = (
            f"SELECT count(*) AS op_schema_changed FROM pg_catalog.pg_operator "
            f"WHERE oprname = '{op_name.split('.')[-1].strip(chr(34))}' "
            f"AND oprnamespace = (SELECT oid FROM pg_namespace "
            f"WHERE nspname = '{prefix}target_sch') ORDER BY count(*) LIMIT 1;"
        )
    else:
        probe = base
    return (
        probe,
        f"SELECT :'target_sqlstate' = '{sqlstate}' "
        f"AS target_sqlstate_matches_expected;",
    )


def _resolve_case(case) -> _CasePlan:
    if getattr(case, "is_extension", False):
        assignment = dict(case.factor_assignment)
    else:
        assignment = dict(case.baseline_assignments)
    prefix = case.object_prefix
    effective = _effective_role(assignment, prefix)
    left_type, right_type = _operator_signature(assignment, prefix)
    op_name = _operator_name(assignment, prefix)
    setup_lines, cleanup_lines = _fixture_lines(
        assignment, prefix, left_type, right_type, op_name, effective
    )
    if effective:
        setup_lines = setup_lines + (f"SET ROLE {effective};",)
        cleanup_lines = ("RESET ROLE;",) + cleanup_lines
    clause = _alter_clause(assignment, prefix)
    invalid = assignment.get("invalid_combination", "none")
    if invalid == "syntax_valid_semantic_error":
        target_sql = (
            f"ALTER OPERATOR {op_name} ({left_type}, {right_type}) "
            f"{clause}, {clause};"
        )
    elif invalid == "object_type_mismatch":
        target_sql = (
            f"ALTER OPERATOR {prefix}mismatch_obj ({left_type}, {right_type}) "
            f"{clause};"
        )
    else:
        target_sql = (
            f"ALTER OPERATOR {op_name} ({left_type}, {right_type}) {clause};"
        )
    oracle = _oracle_lines(
        assignment, prefix, left_type, right_type, op_name, case.expected_sqlstate
    )
    expected_failure = case.outcome == "expected_failure"
    return _CasePlan(
        setup_lines=setup_lines,
        target_sql=target_sql,
        oracle_lines=oracle,
        cleanup_lines=cleanup_lines,
        expected_failure=expected_failure,
    )


def _primary_id(case) -> str:
    if getattr(case, "is_extension", False):
        return getattr(case, "derivation_id")
    return getattr(case, "primary_obligation_id")


def _header(case, plan: AlterOperatorFactorLoopPlan | None) -> str:
    primary = _primary_id(case)
    factor_key = getattr(
        case, "factor_key", getattr(case, "derived_from_combination_group", "")
    )
    factor_value = getattr(
        case, "factor_value", getattr(case, "derivation_reason", "")
    )
    lines = [
        f"-- copyright: {_COPYRIGHT}",
        f"-- author: {_AUTHOR}",
        f"-- create_at: 2026-08-20",
        f"-- version: {_VERSION}",
        f"-- feature: alter_operator",
        f"-- source: {_DOC_SOURCE}",
        f"-- case_id: {case.case_id}",
        f"-- source_md: {primary}",
        f"-- factor_md: {factor_key}={factor_value}",
        f"-- primary_obligation_id: {primary}",
        f"-- expected_outcome: {case.outcome}",
        f"-- expected_sqlstate: {case.expected_sqlstate}",
    ]
    return "\n".join(lines) + "\n"


def render_alter_operator_factor_case(case, repository_root: Path | None = None) -> str:
    """Render one case to its canonical 5-section SQL program."""

    del repository_root  # cases are self-describing; root reserved for API parity
    plan = _resolve_case(case)
    sections: list[str] = []
    sections.append(_header(case, None))
    # Section 1: pre-cleanup.
    sections.append("-- 1. 预清理本编号对象。")
    sections.append(plan.cleanup_lines[0] if plan.cleanup_lines else "")
    # Section 2: ON_ERROR_STOP on + setup.
    sections.append("\\set ON_ERROR_STOP on")
    sections.append("-- 2. 构造本编号对象与角色。")
    sections.extend(plan.setup_lines)
    # Section 3: primary target.
    if plan.expected_failure:
        sections.append("\\set ON_ERROR_STOP off")
    sections.append(_PRIMARY_BEGIN)
    sections.append(plan.target_sql)
    sections.append(_PRIMARY_END)
    sections.append(f"\\set target_sqlstate :SQLSTATE")
    sections.append(
        f"\\echo PGCF_TARGET_SQLSTATE={_escape_sqlstate(case.expected_sqlstate)}"
    )
    # Section 4: oracle.
    sections.append("-- 4. 断言与目录审计。")
    sections.extend(plan.oracle_lines)
    # Section 5: cleanup.
    sections.append("\\set ON_ERROR_STOP off")
    sections.append("-- 5. 清理全部本编号对象。")
    sections.extend(plan.cleanup_lines)
    return "\n".join(sections) + "\n"


def _escape_sqlstate(sqlstate: str) -> str:
    if not re.fullmatch(r"[0-9A-Z]{5}", sqlstate):
        raise AlterOperatorFactorRenderError(f"invalid sqlstate: {sqlstate}")
    return sqlstate


_PRIMARY_RE = re.compile(r"(?im)^\s*ALTER\s+OPERATOR\b")


def count_primary_alter_operator(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, after_end = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end or _PRIMARY_BEGIN in after_end:
        return 0
    target = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(_PRIMARY_RE.findall(target))


@dataclass(frozen=True)
class AlterOperatorFactorWitness:
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


def resolve_alter_operator_factor_witness(case, repository_root: Path | None = None):
    plan = _resolve_case(case)
    return AlterOperatorFactorWitness(
        setup_sql=plan.setup_lines,
        oracle_sql=plan.oracle_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=case.case_id,
    )


def _synthetic_case(ext_case, repository_root: Path):
    """Lift an extension case into a baseline-shaped case for rendering."""

    assignment = dict(ext_case.factor_assignment)
    primary = ext_case.derivation_id
    return AlterOperatorFactorCase(
        ordinal=ext_case.ordinal,
        case_id=ext_case.case_id,
        sql_filename=ext_case.sql_filename,
        object_prefix=ext_case.object_prefix,
        primary_obligation_id=primary,
        kind="EXT",
        factor_key=ext_case.derived_from_combination_group,
        factor_value=ext_case.derivation_reason,
        consumer_action_id=ext_case.consumer_action_id,
        outcome=ext_case.outcome,
        expected_sqlstate=ext_case.expected_sqlstate,
        expected_failure_reason=ext_case.expected_failure_reason,
        baseline_assignments=tuple(sorted(assignment.items())),
        execution_profile="serial_sql",
    )


def _as_render_case(case, repository_root: Path):
    if getattr(case, "is_extension", False):
        return _synthetic_case(case, repository_root)
    return case


def generate_alter_operator_factor_programs(
    baseline_plan: AlterOperatorFactorLoopPlan,
    extension_plan,
    out_dir: Path,
) -> int:
    """Write one .sql per case; return the file count."""

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        sql = render_alter_operator_factor_case(case)
        (out / case.sql_filename).write_text(sql, encoding="utf-8")
        count += 1
    for case in extension_plan.cases:
        render_case = _as_render_case(case, out)
        sql = render_alter_operator_factor_case(render_case)
        (out / case.sql_filename).write_text(sql, encoding="utf-8")
        count += 1
    return count


__all__ = [
    "AlterOperatorFactorRenderError",
    "AlterOperatorFactorWitness",
    "count_primary_alter_operator",
    "render_alter_operator_factor_case",
    "resolve_alter_operator_factor_witness",
    "generate_alter_operator_factor_programs",
]
