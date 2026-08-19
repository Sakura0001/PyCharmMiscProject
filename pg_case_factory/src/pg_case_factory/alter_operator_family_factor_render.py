"""Five-section byte-contract renderer for ALTER OPERATOR FAMILY factor-loop SQL.

Every case is rendered into one deterministic ``.sql`` program with the
canonical sections:

    1. pre-cleanup (best-effort DROP IF EXISTS)
    2. \\set ON_ERROR_STOP on / setup fixtures (schema, operator family, roles,
       SET ROLE)
    3. \\set ON_ERROR_STOP off (when expected_failure) /
       -- primary-target-begin / ALTER OPERATOR FAMILY ... ; /
       -- primary-target-end /
       \\set target_sqlstate :SQLSTATE / \\echo PGCF_TARGET_SQLSTATE=...
    4. oracle (catalog-audit ``SELECT count(*) <op> AS alias ... ORDER BY
       count(*) LIMIT 1;`` + sqlstate assertion)
    5. cleanup (DROP OPERATOR FAMILY / schema / roles)

The five synopsis branches map to ``target_action``: ``add_elements`` /
``drop_elements`` render the operator/function membership clause; ``rename``,
``owner_change``, and ``set_schema`` reuse the rename-conflict, SESSION_USER
no-op-transfer salvage, and schema-migration fixtures from
``alter_operator_class`` / ``alter_large_object``.  An operator family is
identified by ``(name, index_method)``; the ``USING index_method`` clause is
therefore always present in the target.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_operator_family_factor_loop import (
    AlterOperatorFamilyFactorCase,
    AlterOperatorFamilyFactorLoopPlan,
    build_alter_operator_family_factor_loop_plan,
)


class AlterOperatorFamilyFactorRenderError(ValueError):
    """Raised when a case cannot be rendered to canonical bytes."""


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alteropfamily"
_VERSION = "1.0.0"
_AUTHOR = "pg_case_factory"
_COPYRIGHT = "Copyright (c) 2026 pg_case_factory"


def _index_method(case_assignments: dict[str, str]) -> str:
    method = case_assignments.get("index_method_shape", "btree")
    if method not in ("btree", "hash", "gist", "gin", "spgist", "brin"):
        raise AlterOperatorFamilyFactorRenderError(f"unknown index method: {method}")
    return method


def _family_name(case_assignments: dict[str, str], prefix: str) -> str:
    shape = case_assignments.get("name_shape", "plain_identifier")
    raw = f"{prefix}opf"
    if shape == "quoted_identifier":
        return f'"{raw}"'
    if shape == "schema_qualified":
        return f"{prefix}sch.{raw}"
    return raw


def _family_base_name(family_name: str) -> str:
    """Return the unqualified, unquoted operator family name for catalog probes."""

    tail = family_name.split(".")[-1]
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
        return f"{prefix}conflict_opf"
    return f"{prefix}new_opf"


def _type_name(op_type: str, prefix: str) -> str:
    if op_type == "text":
        return "text"
    if op_type == "custom_type":
        return f"{prefix}custype"
    return "integer"


def _element_add_clause(
    case_assignments: dict[str, str],
    prefix: str,
) -> str:
    add_type = case_assignments.get("add_element_type", "add_operator_for_search")
    op_type = case_assignments.get("element_op_type", "integer")
    dep = case_assignments.get("dependency_state", "ready")
    compat = case_assignments.get("index_method_compatibility", "compatible")
    typ = _type_name(op_type, prefix)
    is_none = op_type == "none_prefix_operator"
    if add_type == "add_function":
        fn = (
            f"{prefix}missingfn"
            if dep == "missing_function"
            else f"{prefix}supportfn"
        )
        return f"FUNCTION 1 {fn}({typ})"
    if add_type == "add_operator_for_order_by":
        op = "<"
        mode = "FOR ORDER BY"
    else:
        op = "=" if compat == "compatible" else "<>"
        mode = "FOR SEARCH"
    if dep == "missing_operator":
        op = "~#"
    if is_none:
        return f"OPERATOR 1 {op}(NONE, integer) {mode}"
    return f"OPERATOR 1 {op}({typ}, {typ}) {mode}"


def _element_drop_clause(
    case_assignments: dict[str, str],
    prefix: str,
) -> str:
    drop_type = case_assignments.get("drop_element_type", "drop_operator")
    op_type = case_assignments.get("element_op_type", "integer")
    typ = _type_name(op_type, prefix)
    is_none = op_type == "none_prefix_operator"
    if drop_type == "drop_function":
        return f"FUNCTION 1 ({typ})"
    if is_none:
        return "OPERATOR 1 (NONE, integer)"
    return f"OPERATOR 1 ({typ}, {typ})"


def _alter_clause(
    case_assignments: dict[str, str],
    prefix: str,
) -> str:
    branch = case_assignments.get("target_action", "add_elements")
    if branch == "owner_change":
        owner_shape = case_assignments.get("new_owner_shape", "plain_role")
        return f"OWNER TO {_owner_target(owner_shape, prefix)}"
    if branch == "set_schema":
        return f"SET SCHEMA {prefix}target_sch"
    if branch == "rename":
        return f"RENAME TO {_rename_target(case_assignments, prefix)}"
    if branch == "drop_elements":
        return f"DROP {_element_drop_clause(case_assignments, prefix)}"
    if branch == "add_elements":
        return f"ADD {_element_add_clause(case_assignments, prefix)}"
    raise AlterOperatorFamilyFactorRenderError(f"unknown branch: {branch}")


@dataclass(frozen=True)
class _CasePlan:
    setup_lines: tuple[str, ...]
    target_sql: str
    oracle_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    expected_failure: bool


def _family_present(case_assignments: dict[str, str]) -> bool:
    """Whether the target operator family is created (exists) in the fixture."""

    if case_assignments.get("expected_status") == "failure":
        return False
    if case_assignments.get("target_object_state") == "missing":
        return False
    if case_assignments.get("dependency_state") == "missing_family":
        return False
    if case_assignments.get("invalid_combination") == "object_type_mismatch":
        return False
    return True


def _preadd_element_for_drop(
    case_assignments: dict[str, str],
    family_name: str,
    method: str,
) -> str | None:
    """For the DROP branch with a present family + ready element, pre-add it."""

    if case_assignments.get("target_action") != "drop_elements":
        return None
    if not _family_present(case_assignments):
        return None
    if case_assignments.get("dependency_state") != "ready":
        return None
    clause = _element_drop_clause(case_assignments, "")
    return f"ALTER OPERATOR FAMILY {family_name} USING {method} ADD {clause};"


def _fixture_lines(
    case_assignments: dict[str, str],
    prefix: str,
    family_name: str,
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
        pass  # family already lives in op_schema via the qualified name.
    target_sch = f"{prefix}target_sch"
    schema_state = case_assignments.get("schema_migration_state", "target_schema_exists")
    if schema_state in ("target_schema_exists", "target_schema_conflict"):
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {target_sch};")
    cleanup.append(f"DROP SCHEMA IF EXISTS {target_sch} CASCADE;")
    if schema_state == "target_schema_conflict":
        setup.append(
            f"CREATE OPERATOR FAMILY {target_sch}.{prefix}opf USING {method};"
        )
    if case_assignments.get("rename_conflict") == "new_name_conflict":
        setup.append(f"CREATE OPERATOR FAMILY {prefix}conflict_opf USING {method};")
    owner_shape = case_assignments.get("new_owner_shape", "plain_role")
    if case_assignments.get("target_action") == "owner_change":
        if owner_shape == "plain_role":
            setup.append(f"CREATE ROLE {prefix}new_owner LOGIN;")
            cleanup.append(f"DROP ROLE IF EXISTS {prefix}new_owner;")
    if effective:
        setup.append(f"CREATE ROLE {effective} LOGIN;")
        setup.append(f"GRANT USAGE ON SCHEMA {op_schema} TO {effective};")
        cleanup.append(f"DROP OWNED BY {effective};")
        cleanup.append(f"DROP ROLE IF EXISTS {effective};")
    if case_assignments.get("element_op_type") == "custom_type":
        setup.append(f"CREATE DOMAIN IF NOT EXISTS {prefix}custype AS integer;")
        cleanup.append(f"DROP DOMAIN IF EXISTS {prefix}custype;")
    if case_assignments.get("add_element_type") == "add_function":
        if case_assignments.get("dependency_state") != "missing_function":
            setup.append(
                f"CREATE FUNCTION IF NOT EXISTS {prefix}supportfn(integer) "
                f"RETURNS integer AS 'SELECT $1' LANGUAGE SQL;"
            )
            cleanup.append(f"DROP FUNCTION IF EXISTS {prefix}supportfn(integer);")
    if case_assignments.get("invalid_combination") == "object_type_mismatch":
        setup.append(f"CREATE TABLE IF NOT EXISTS {prefix}mismatch_obj (id int);")
        cleanup.append(f"DROP TABLE IF EXISTS {prefix}mismatch_obj;")
    if _family_present(case_assignments):
        setup.append(f"CREATE OPERATOR FAMILY {family_name} USING {method};")
        preadd = _preadd_element_for_drop(case_assignments, family_name, method)
        if preadd is not None:
            setup.append(preadd)
    return (tuple(setup), tuple(cleanup))


def _oracle_lines(
    case_assignments: dict[str, str],
    family_name: str,
    method: str,
    sqlstate: str,
) -> tuple[str, ...]:
    mode = case_assignments.get("verification_mode", "catalog_query")
    target_action = case_assignments.get("target_action", "add_elements")
    base_name = _family_base_name(family_name)
    method_oid = (
        f"(SELECT oid FROM pg_catalog.pg_am WHERE amname = '{method}')"
    )
    base = (
        f"SELECT count(*) AS opf_present FROM pg_catalog.pg_opfamily "
        f"WHERE opfname = '{base_name}' "
        f"AND opfmethod = {method_oid} ORDER BY count(*) LIMIT 1;"
    )
    if mode == "error_assertion":
        return (
            base,
            f"SELECT :'target_sqlstate' = '{sqlstate}' "
            f"AS target_sqlstate_matches_expected;",
        )
    if target_action == "rename":
        new_name = _family_base_name(_rename_target(case_assignments, ""))
        probe = (
            f"SELECT count(*) AS opf_renamed FROM pg_catalog.pg_opfamily "
            f"WHERE opfname = '{new_name}' "
            f"AND opfmethod = {method_oid} ORDER BY count(*) LIMIT 1;"
        )
    elif target_action == "owner_change":
        owner_shape = case_assignments.get("new_owner_shape", "plain_role")
        if owner_shape in ("current_role", "current_user"):
            owner_clause = (
                "opfowner = (SELECT oid FROM pg_roles "
                "WHERE rolname = current_role)"
            )
        elif owner_shape == "session_user":
            owner_clause = (
                "opfowner = (SELECT oid FROM pg_roles "
                "WHERE rolname = session_user)"
            )
        elif owner_shape == "plain_role":
            owner_clause = (
                f"opfowner = (SELECT oid FROM pg_roles "
                f"WHERE rolname = '{case_assignments.get('object_prefix', '')}new_owner')"
            )
        else:
            owner_clause = "opfowner IS NOT NULL"
        probe = (
            f"SELECT count(*) AS opf_owner_changed FROM pg_catalog.pg_opfamily "
            f"WHERE opfname = '{base_name}' "
            f"AND opfmethod = {method_oid} "
            f"AND {owner_clause} ORDER BY count(*) LIMIT 1;"
        )
    elif target_action == "set_schema":
        prefix = case_assignments.get("object_prefix", "")
        probe = (
            f"SELECT count(*) AS opf_schema_changed FROM pg_catalog.pg_opfamily "
            f"WHERE opfname = '{base_name}' "
            f"AND opfmethod = {method_oid} "
            f"AND opfnamespace = (SELECT oid FROM pg_namespace "
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
    assignment["object_prefix"] = prefix
    effective = _effective_role(assignment, prefix)
    method = _index_method(assignment)
    family_name = _family_name(assignment, prefix)
    setup_lines, cleanup_lines = _fixture_lines(
        assignment, prefix, family_name, method, effective
    )
    if effective:
        setup_lines = setup_lines + (f"SET ROLE {effective};",)
        cleanup_lines = ("RESET ROLE;",) + cleanup_lines
    clause = _alter_clause(assignment, prefix)
    invalid = assignment.get("invalid_combination", "none")
    if invalid == "syntax_valid_semantic_error":
        target_sql = (
            f"ALTER OPERATOR FAMILY {family_name} USING {method} "
            f"ADD {clause}, ADD {clause};"
        )
    elif invalid == "object_type_mismatch":
        target_sql = (
            f"ALTER OPERATOR FAMILY {prefix}mismatch_obj USING {method} "
            f"{clause};"
        )
    else:
        target_sql = (
            f"ALTER OPERATOR FAMILY {family_name} USING {method} {clause};"
        )
    oracle = _oracle_lines(assignment, family_name, method, case.expected_sqlstate)
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


def _header(case, plan: AlterOperatorFamilyFactorLoopPlan | None) -> str:
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
        f"-- feature: alter_operator_family",
        f"-- source: {_DOC_SOURCE}",
        f"-- case_id: {case.case_id}",
        f"-- source_md: {primary}",
        f"-- factor_md: {factor_key}={factor_value}",
        f"-- primary_obligation_id: {primary}",
        f"-- expected_outcome: {case.outcome}",
        f"-- expected_sqlstate: {case.expected_sqlstate}",
    ]
    del plan
    return "\n".join(lines) + "\n"


def render_alter_operator_family_factor_case(
    case, repository_root: Path | None = None
) -> str:
    """Render one case to its canonical 5-section SQL program."""

    del repository_root  # cases are self-describing; root reserved for API parity
    plan = _resolve_case(case)
    sections: list[str] = []
    sections.append(_header(case, None))
    sections.append("-- 1. 预清理本编号对象。")
    sections.append(plan.cleanup_lines[0] if plan.cleanup_lines else "")
    sections.append("\\set ON_ERROR_STOP on")
    sections.append("-- 2. 构造本编号对象与角色。")
    sections.extend(plan.setup_lines)
    if plan.expected_failure:
        sections.append("\\set ON_ERROR_STOP off")
    sections.append(_PRIMARY_BEGIN)
    sections.append(plan.target_sql)
    sections.append(_PRIMARY_END)
    sections.append("\\set target_sqlstate :SQLSTATE")
    sections.append(
        f"\\echo PGCF_TARGET_SQLSTATE={_escape_sqlstate(case.expected_sqlstate)}"
    )
    sections.append("-- 4. 断言与目录审计。")
    sections.extend(plan.oracle_lines)
    sections.append("\\set ON_ERROR_STOP off")
    sections.append("-- 5. 清理全部本编号对象。")
    sections.extend(plan.cleanup_lines)
    return "\n".join(sections) + "\n"


def _escape_sqlstate(sqlstate: str) -> str:
    if not re.fullmatch(r"[0-9A-Z]{5}", sqlstate):
        raise AlterOperatorFamilyFactorRenderError(
            f"invalid sqlstate: {sqlstate}"
        )
    return sqlstate


_PRIMARY_RE = re.compile(r"(?im)^\s*ALTER\s+OPERATOR\s+FAMILY\b")


def count_primary_alter_operator_family(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, after_end = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end or _PRIMARY_BEGIN in after_end:
        return 0
    target = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(_PRIMARY_RE.findall(target))


@dataclass(frozen=True)
class AlterOperatorFamilyFactorWitness:
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


def resolve_alter_operator_family_factor_witness(
    case, repository_root: Path | None = None
):
    plan = _resolve_case(case)
    return AlterOperatorFamilyFactorWitness(
        setup_sql=plan.setup_lines,
        oracle_sql=plan.oracle_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=case.case_id,
    )


def _synthetic_case(ext_case, repository_root: Path):
    """Lift an extension case into a baseline-shaped case for rendering."""

    assignment = dict(ext_case.factor_assignment)
    primary = ext_case.derivation_id
    return AlterOperatorFamilyFactorCase(
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


def generate_alter_operator_family_factor_programs(
    baseline_plan: AlterOperatorFamilyFactorLoopPlan,
    extension_plan,
    out_dir: Path,
) -> int:
    """Write one .sql per case; return the file count."""

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        sql = render_alter_operator_family_factor_case(case)
        (out / case.sql_filename).write_text(sql, encoding="utf-8")
        count += 1
    for case in extension_plan.cases:
        render_case = _as_render_case(case, out)
        sql = render_alter_operator_family_factor_case(render_case)
        (out / case.sql_filename).write_text(sql, encoding="utf-8")
        count += 1
    return count


__all__ = [
    "AlterOperatorFamilyFactorRenderError",
    "AlterOperatorFamilyFactorWitness",
    "count_primary_alter_operator_family",
    "render_alter_operator_family_factor_case",
    "resolve_alter_operator_family_factor_witness",
    "generate_alter_operator_family_factor_programs",
]
