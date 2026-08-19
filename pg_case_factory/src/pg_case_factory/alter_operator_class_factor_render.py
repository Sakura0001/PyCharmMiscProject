"""Five-section byte-contract renderer for ALTER OPERATOR CLASS factor-loop SQL.

Every case is rendered into one deterministic ``.sql`` program with the
canonical sections:

    1. pre-cleanup (best-effort DROP IF EXISTS)
    2. \\set ON_ERROR_STOP on / setup fixtures (schema, operator class, roles,
       SET ROLE)
    3. \\set ON_ERROR_STOP off (when expected_failure) /
       -- primary-target-begin / ALTER OPERATOR CLASS ... ; /
       -- primary-target-end /
       \\set target_sqlstate :SQLSTATE / \\echo PGCF_TARGET_SQLSTATE=...
    4. oracle (catalog-audit ``SELECT count(*) <op> AS alias ... ORDER BY
       count(*) LIMIT 1;`` + sqlstate assertion)
    5. cleanup (DROP OPERATOR CLASS / schema / roles)

The owner-transfer branch reuses the SESSION_USER no-op transfer salvage and
the SET-ROLE / RESET-ROLE privilege fixture from ``alter_large_object`` /
``alter_operator``.  Extension cases are lifted into a baseline-shaped
synthetic case so the renderer reads the crossed privilege axis from the
assignment.  An operator class is identified by ``(name, index_method)``; the
``USING index_method`` clause is therefore always present in the target.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_operator_class_factor_loop import (
    AlterOperatorClassFactorCase,
    AlterOperatorClassFactorLoopPlan,
    build_alter_operator_class_factor_loop_plan,
)


class AlterOperatorClassFactorRenderError(ValueError):
    """Raised when a case cannot be rendered to canonical bytes."""


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alteropclass"
_VERSION = "1.0.0"
_AUTHOR = "pg_case_factory"
_COPYRIGHT = "Copyright (c) 2026 pg_case_factory"


def _index_method(case_assignments: dict[str, str]) -> str:
    method = case_assignments.get("index_method_shape", "btree")
    if method not in ("btree", "hash", "gist", "gin", "spgist", "brin"):
        raise AlterOperatorClassFactorRenderError(f"unknown index method: {method}")
    return method


def _opclass_name(case_assignments: dict[str, str], prefix: str) -> str:
    shape = case_assignments.get("name_shape", "plain_identifier")
    raw = f"{prefix}opc"
    if shape == "quoted_identifier":
        return f'"{raw}"'
    if shape == "schema_qualified":
        return f"{prefix}sch.{raw}"
    return raw


def _opclass_base_name(opclass_name: str) -> str:
    """Return the unqualified, unquoted operator class name for catalog probes."""

    tail = opclass_name.split(".")[-1]
    return tail.strip('"')


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
    privilege = case_assignments.get("privilege_context", "superuser")
    if privilege in ("non_owner", "insufficient_privilege"):
        return f"{prefix}actor"
    return ""


def _rename_target(case_assignments: dict[str, str], prefix: str) -> str:
    conflict = case_assignments.get("rename_conflict", "new_name_available")
    if conflict == "new_name_conflict":
        return f"{prefix}conflict_opc"
    return f"{prefix}new_opc"


def _alter_clause(
    case_assignments: dict[str, str],
    prefix: str,
) -> str:
    branch = case_assignments.get("target_action", "rename")
    if branch == "owner_change":
        owner_shape = case_assignments.get("new_owner_shape", "plain_role")
        return f"OWNER TO {_owner_target(owner_shape, prefix)}"
    if branch == "set_schema":
        return f"SET SCHEMA {prefix}target_sch"
    if branch == "rename":
        return f"RENAME TO {_rename_target(case_assignments, prefix)}"
    raise AlterOperatorClassFactorRenderError(f"unknown branch: {branch}")


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
    opclass_name: str,
    method: str,
    effective: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    setup: list[str] = []
    cleanup: list[str] = []
    op_schema = f"{prefix}sch"
    setup.append(f"CREATE SCHEMA IF NOT EXISTS {op_schema};")
    cleanup.append(f"DROP SCHEMA IF EXISTS {op_schema} CASCADE;")
    name_shape = case_assignments.get("name_shape", "plain_identifier")
    if name_shape == "schema_qualified":
        # opclass already lives in op_schema via the qualified name.
        pass
    # Target schema for the SET SCHEMA branch.
    target_sch = f"{prefix}target_sch"
    schema_state = case_assignments.get("schema_migration_state", "target_schema_exists")
    if schema_state in ("target_schema_exists", "target_schema_conflict"):
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {target_sch};")
    cleanup.append(f"DROP SCHEMA IF EXISTS {target_sch} CASCADE;")
    # A conflicting operator class in the target schema (SET SCHEMA conflict).
    if schema_state == "target_schema_conflict":
        setup.append(
            f"CREATE OPERATOR CLASS {target_sch}.{prefix}opc "
            f"FOR TYPE integer USING {method} AS STORAGE integer;"
        )
    # A conflicting operator class for the RENAME conflict.
    if case_assignments.get("rename_conflict") == "new_name_conflict":
        setup.append(
            f"CREATE OPERATOR CLASS {prefix}conflict_opc "
            f"FOR TYPE integer USING {method} AS STORAGE integer;"
        )
    # Roles for the owner-transfer / privilege fixture.
    owner_shape = case_assignments.get("new_owner_shape", "plain_role")
    if case_assignments.get("target_action") == "owner_change":
        if owner_shape == "plain_role":
            setup.append(f"CREATE ROLE {prefix}new_owner LOGIN;")
            cleanup.append(f"DROP ROLE IF EXISTS {prefix}new_owner;")
        # missing_role: the role is intentionally absent (genuine 42704).
    if effective:
        setup.append(f"CREATE ROLE {effective} LOGIN;")
        setup.append(f"GRANT USAGE ON SCHEMA {op_schema} TO {effective};")
        cleanup.append(f"DROP OWNED BY {effective};")
        cleanup.append(f"DROP ROLE IF EXISTS {effective};")
    object_state = case_assignments.get("target_object_state", "exists")
    invalid = case_assignments.get("invalid_combination", "none")
    if object_state == "exists" and invalid != "object_type_mismatch":
        setup.append(
            f"CREATE OPERATOR CLASS {opclass_name} "
            f"FOR TYPE integer USING {method} AS STORAGE integer;"
        )
    return (tuple(setup), tuple(cleanup))


def _oracle_lines(
    case_assignments: dict[str, str],
    prefix: str,
    opclass_name: str,
    method: str,
    sqlstate: str,
) -> tuple[str, ...]:
    mode = case_assignments.get("verification_mode", "catalog_query")
    target_action = case_assignments.get("target_action", "rename")
    base_name = _opclass_base_name(opclass_name)
    method_oid = (
        f"(SELECT oid FROM pg_catalog.pg_am WHERE amname = '{method}')"
    )
    base = (
        f"SELECT count(*) AS opc_present FROM pg_catalog.pg_opclass "
        f"WHERE opcname = '{base_name}' "
        f"AND opcmethod = {method_oid} ORDER BY count(*) LIMIT 1;"
    )
    if mode == "error_assertion":
        return (
            base,
            f"SELECT :'target_sqlstate' = '{sqlstate}' "
            f"AS target_sqlstate_matches_expected;",
        )
    if target_action == "rename":
        new_name = _opclass_base_name(_rename_target(case_assignments, prefix))
        probe = (
            f"SELECT count(*) AS opc_renamed FROM pg_catalog.pg_opclass "
            f"WHERE opcname = '{new_name}' "
            f"AND opcmethod = {method_oid} ORDER BY count(*) LIMIT 1;"
        )
    elif target_action == "owner_change":
        owner_shape = case_assignments.get("new_owner_shape", "plain_role")
        if owner_shape in ("current_role", "current_user"):
            owner_clause = (
                "opcowner = (SELECT oid FROM pg_roles "
                "WHERE rolname = current_role)"
            )
        elif owner_shape == "session_user":
            owner_clause = (
                "opcowner = (SELECT oid FROM pg_roles "
                "WHERE rolname = session_user)"
            )
        elif owner_shape == "plain_role":
            owner_clause = (
                f"opcowner = (SELECT oid FROM pg_roles "
                f"WHERE rolname = '{prefix}new_owner')"
            )
        else:
            owner_clause = "opcowner IS NOT NULL"
        probe = (
            f"SELECT count(*) AS opc_owner_changed FROM pg_catalog.pg_opclass "
            f"WHERE opcname = '{base_name}' "
            f"AND opcmethod = {method_oid} "
            f"AND {owner_clause} ORDER BY count(*) LIMIT 1;"
        )
    elif target_action == "set_schema":
        probe = (
            f"SELECT count(*) AS opc_schema_changed FROM pg_catalog.pg_opclass "
            f"WHERE opcname = '{base_name}' "
            f"AND opcmethod = {method_oid} "
            f"AND opcnamespace = (SELECT oid FROM pg_namespace "
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
    method = _index_method(assignment)
    opclass_name = _opclass_name(assignment, prefix)
    setup_lines, cleanup_lines = _fixture_lines(
        assignment, prefix, opclass_name, method, effective
    )
    if effective:
        setup_lines = setup_lines + (f"SET ROLE {effective};",)
        cleanup_lines = ("RESET ROLE;",) + cleanup_lines
    clause = _alter_clause(assignment, prefix)
    invalid = assignment.get("invalid_combination", "none")
    if invalid == "syntax_valid_semantic_error":
        target_sql = (
            f"ALTER OPERATOR CLASS {opclass_name} USING {method} "
            f"{clause}, {clause};"
        )
    elif invalid == "object_type_mismatch":
        target_sql = (
            f"ALTER OPERATOR CLASS {prefix}mismatch_obj USING {method} "
            f"{clause};"
        )
    else:
        target_sql = (
            f"ALTER OPERATOR CLASS {opclass_name} USING {method} {clause};"
        )
    oracle = _oracle_lines(
        assignment, prefix, opclass_name, method, case.expected_sqlstate
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


def _header(case, plan: AlterOperatorClassFactorLoopPlan | None) -> str:
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
        f"-- feature: alter_operator_class",
        f"-- source: {_DOC_SOURCE}",
        f"-- case_id: {case.case_id}",
        f"-- source_md: {primary}",
        f"-- factor_md: {factor_key}={factor_value}",
        f"-- primary_obligation_id: {primary}",
        f"-- expected_outcome: {case.outcome}",
        f"-- expected_sqlstate: {case.expected_sqlstate}",
    ]
    return "\n".join(lines) + "\n"


def render_alter_operator_class_factor_case(
    case, repository_root: Path | None = None
) -> str:
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
    sections.append("\\set target_sqlstate :SQLSTATE")
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
        raise AlterOperatorClassFactorRenderError(
            f"invalid sqlstate: {sqlstate}"
        )
    return sqlstate


_PRIMARY_RE = re.compile(r"(?im)^\s*ALTER\s+OPERATOR\s+CLASS\b")


def count_primary_alter_operator_class(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, after_end = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end or _PRIMARY_BEGIN in after_end:
        return 0
    target = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(_PRIMARY_RE.findall(target))


@dataclass(frozen=True)
class AlterOperatorClassFactorWitness:
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


def resolve_alter_operator_class_factor_witness(
    case, repository_root: Path | None = None
):
    plan = _resolve_case(case)
    return AlterOperatorClassFactorWitness(
        setup_sql=plan.setup_lines,
        oracle_sql=plan.oracle_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=case.case_id,
    )


def _synthetic_case(ext_case, repository_root: Path):
    """Lift an extension case into a baseline-shaped case for rendering."""

    assignment = dict(ext_case.factor_assignment)
    primary = ext_case.derivation_id
    return AlterOperatorClassFactorCase(
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


def generate_alter_operator_class_factor_programs(
    baseline_plan: AlterOperatorClassFactorLoopPlan,
    extension_plan,
    out_dir: Path,
) -> int:
    """Write one .sql per case; return the file count."""

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        sql = render_alter_operator_class_factor_case(case)
        (out / case.sql_filename).write_text(sql, encoding="utf-8")
        count += 1
    for case in extension_plan.cases:
        render_case = _as_render_case(case, out)
        sql = render_alter_operator_class_factor_case(render_case)
        (out / case.sql_filename).write_text(sql, encoding="utf-8")
        count += 1
    return count


__all__ = [
    "AlterOperatorClassFactorRenderError",
    "AlterOperatorClassFactorWitness",
    "count_primary_alter_operator_class",
    "render_alter_operator_class_factor_case",
    "resolve_alter_operator_class_factor_witness",
    "generate_alter_operator_class_factor_programs",
]
