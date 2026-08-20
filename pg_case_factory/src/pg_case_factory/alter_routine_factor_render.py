"""Render complete PostgreSQL 18.4 ALTER ROUTINE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator can re-render and compare without divergence.

ALTER ROUTINE is the generic routine wrapper: it resolves to ALTER FUNCTION /
ALTER PROCEDURE / ALTER AGGREGATE by object kind.  The fixture kind (function /
procedure / aggregate) is driven by ``routine_type`` (extension) or
``routine_state`` (baseline), and the action clause is the 16-value
``branch_action`` set plus the 4 outer-branch operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_routine_factor_extension import (
    AlterRoutineFactorExtensionCase,
)
from .alter_routine_factor_loop import (
    AlterRoutineFactorCase,
    AlterRoutineFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/routine/"
    "alter_routine.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/routine/"
    "alter_routine.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_ACTION_FORM = "branch_action_form"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_DEPENDS_EXTENSION = "branch_depends_extension"

_NO_FIXTURE_PRIMARIES = {
    ("expected_status", "failure"),
    ("routine_state", "non_existent"),
    ("routine_name_shape", "non_existent_name"),
    ("nonexistent_routine", "routine_does_not_exist"),
}


def _synthetic_case(
    ext: AlterRoutineFactorExtensionCase,
) -> AlterRoutineFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .alter_routine_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif ext.outcome == "success":
        factor_key = "routine_state"
        factor_value = "exists"
    else:
        factor_key = "routine_state"
        factor_value = "exists"
    return AlterRoutineFactorCase(
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
    case: AlterRoutineFactorCase | AlterRoutineFactorExtensionCase,
) -> AlterRoutineFactorCase:
    if isinstance(case, AlterRoutineFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterRoutineFactorRenderError(ValueError):
    """Raised when an ALTER ROUTINE case cannot be rendered."""


@dataclass(frozen=True)
class AlterRoutineFactorWitness:
    primary_obligation_id: str
    target_sql_fragment: str
    outcome: str
    expected_sqlstate: str
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, str]
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


def _baseline(case: AlterRoutineFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _routine_name(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    """The target routine name as referenced inside ALTER ROUTINE."""

    shape = a.get("routine_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}Mixed Routine"'
    if shape == "schema_qualified_name":
        return f"{p}src_schema.{p}routine"
    if shape == "non_existent_name":
        return f"{p}no_such_routine"
    return f"{p}routine"


def _fixture_name(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    shape = a.get("routine_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}Mixed Routine"'
    return f"{p}routine"


def _fixture_args(a: dict[str, str]) -> str:
    spec = a.get("arg_signature", "no_args")
    if spec == "multiple_args":
        return "(integer, text)"
    return "(integer)"


def _target_args(case: AlterRoutineFactorCase, a: dict[str, str]) -> str:
    spec = a.get("arg_signature", "no_args")
    if spec == "no_args":
        return ""
    if spec == "multiple_args":
        return "(integer, text)"
    if spec == "mismatched_signature":
        return "(text)"
    return "(integer)"


def _config_guc(a: dict[str, str], p: str) -> str:
    return f"{p}work_mem"


def _action_clause(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    action = case.consumer_action_id
    ext = "EXTERNAL " if a.get("external_keyword") == "present" else ""
    form = a.get("set_assignment_form", "to_value")
    guc = _config_guc(a, p)
    clauses = {
        "immutable": "IMMUTABLE",
        "stable": "STABLE",
        "volatile": "VOLATILE",
        "leakproof": "LEAKPROOF",
        "not_leakproof": "NOT LEAKPROOF",
        "security_invoker": f"{ext}SECURITY INVOKER",
        "security_definer": f"{ext}SECURITY DEFINER",
        "parallel_unsafe": "PARALLEL UNSAFE",
        "parallel_restricted": "PARALLEL RESTRICTED",
        "parallel_safe": "PARALLEL SAFE",
        "cost": "COST 100",
        "rows": "ROWS 100",
        "set_config_from_current": f"SET {guc} FROM CURRENT",
        "reset_config_parameter": f"RESET {guc}",
        "reset_all": "RESET ALL",
    }
    if action in clauses:
        clause = clauses[action]
    elif action == "set_config_parameter":
        if form == "equals_value":
            clause = f"SET {guc} = 100"
        elif form == "to_default":
            clause = f"SET {guc} TO DEFAULT"
        else:
            clause = f"SET {guc} TO 100"
    else:
        raise AlterRoutineFactorRenderError(
            f"no branch_action clause for {action}"
        )
    if a.get("action_list_cardinality") == "multiple_actions":
        clause = f"{clause} SECURITY INVOKER"
    if a.get("restrict_clause") == "restrict":
        clause = f"{clause} RESTRICT"
    return clause


def _new_name(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    if case.factor_key == "new_name_shape":
        form = case.factor_value
    else:
        form = a.get("new_name_shape", "simple_name")
    if form == "quoted_name":
        return f'"{p}Mixed Name"'
    if form == "existing_name_conflict":
        return f"{p}dup_routine"
    return f"{p}renamed"


def _owner_target(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    if case.factor_key == "owner_to_shape":
        value = case.factor_value
    elif case.factor_key == "nonexistent_owner":
        return f"{p}no_such_owner"
    else:
        value = a.get("owner_to_shape", "explicit_role_name")
    if value == "current_role_keyword":
        return "CURRENT_ROLE"
    if value == "current_user_keyword":
        return "CURRENT_USER"
    if value == "session_user_keyword":
        return "SESSION_USER"
    return f"{p}new_owner"


def _schema_target(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    if case.factor_key in ("schema_change", "new_schema_shape"):
        value = case.factor_value
    elif case.factor_key == "nonexistent_schema":
        return f"{p}no_such_schema"
    else:
        value = a.get("schema_change", "existing_schema")
    if value == "nonexistent_schema":
        return f"{p}no_such_schema"
    return f"{p}dst_schema"


def _ext_clause(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    polarity = a.get("depends_polarity", "depends")
    if case.factor_key == "extension_dependency":
        if case.factor_value == "depends_on_nonexistent_extension":
            ext = f"{p}no_such_ext"
        else:
            ext = "plpgsql"
    elif case.factor_key == "nonexistent_extension":
        ext = f"{p}no_such_ext"
    else:
        ext = "plpgsql"
    if case.factor_key == "depends_polarity" and case.factor_value == "no_depends":
        polarity = "no_depends"
    if polarity == "no_depends":
        return f"NO DEPENDS ON EXTENSION {ext}"
    return f"DEPENDS ON EXTENSION {ext}"


def _effective_role(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target ALTER ROUTINE runs."""

    level = a.get("executor_privilege", "superuser")
    if level == "owner_of_routine":
        return f"{p}owner"
    if level == "non_owner_with_grant_option":
        return f"{p}alter"
    if level == "non_owner_no_privilege":
        return f"{p}actor"
    return ""


def _fixture_kind(case: AlterRoutineFactorCase) -> str:
    """function / procedure / aggregate / none based on routine kind."""

    primary = (case.factor_key, case.factor_value)
    if primary in _NO_FIXTURE_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a_state_none(case):
            return "none"
        return _ext_routine_type(case)
    if case.factor_key == "routine_state":
        if case.factor_value == "exists_as_procedure":
            return "procedure"
        if case.factor_value == "exists_as_aggregate":
            return "aggregate"
    return "function"


def a_state_none(case: AlterRoutineFactorCase) -> bool:
    a = _baseline(case)
    return a.get("routine_state") == "non_existent"


def _ext_routine_type(case: AlterRoutineFactorCase) -> str:
    a = _baseline(case)
    return a.get("routine_type", "function")


def _probe_name(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    if case.kind == "RISK":
        return f"{p}routine"
    if case.factor_key == "new_name_shape" and case.outcome == "success":
        return _new_name(case, a, p).strip('"')
    name = _fixture_name(case, a, p)
    return name.strip('"')


def _probe_select(
    case: AlterRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    mode = a.get("verification_mode", "pg_proc_catalog")
    if case.factor_key == "verification_mode":
        mode = case.factor_value
    name = _probe_name(case, a, p)
    if mode == "pg_aggregate_catalog":
        return (
            "SELECT p.proname, p.prokind "
            "FROM pg_catalog.pg_aggregate AS ag "
            "JOIN pg_catalog.pg_proc AS p ON p.oid = ag.aggfnoid "
            f"WHERE p.proname = '{name}' ORDER BY p.oid;"
        )
    if mode == "effect_query":
        return (
            "SELECT p.proname, p.prokind, p.proleakproof, p.prosecdef, "
            "p.proparallel, p.procost, p.prorows "
            "FROM pg_catalog.pg_proc AS p "
            f"WHERE p.proname = '{name}' ORDER BY p.proname, p.oid;"
        )
    if mode == "error_assertion":
        return (
            f"SELECT '{case.expected_sqlstate}' AS expected_sqlstate;"
        )
    return (
        "SELECT p.proname, p.prokind, p.proowner::regrole, "
        "p.proleakproof, p.prosecdef, p.proparallel "
        "FROM pg_catalog.pg_proc AS p "
        f"WHERE p.proname = '{name}' ORDER BY p.proname, p.oid;"
    )


def _routine_candidates(
    case: AlterRoutineFactorCase,
    a: dict[str, str],
    p: str,
    fixture_kind: str,
    branch: str,
    needs_src_schema: bool,
    needs_dst_schema: bool,
) -> tuple[tuple[str, str], ...]:
    """Every (drop_kind, qualified_name_with_args) the target could be found under."""

    name = _fixture_name(case, a, p)
    args = _fixture_args(a)
    if fixture_kind == "function":
        return (("FUNCTION", f"{name}{args}"),)
    if fixture_kind == "procedure":
        candidates: list[tuple[str, str]] = []
        orig = f"{p}src_schema." if needs_src_schema else ""
        candidates.append(("PROCEDURE", f"{orig}{name}{args}"))
        if branch == _BRANCH_RENAME:
            new = _new_name(case, a, p)
            candidates.append(("PROCEDURE", f"{orig}{new}{args}"))
        if needs_dst_schema:
            candidates.append(("PROCEDURE", f"{p}dst_schema.{name}{args}"))
        if (
            case.factor_key == "new_name_shape"
            and case.factor_value == "existing_name_conflict"
        ):
            candidates.append(("PROCEDURE", f"{p}dup_routine{args}"))
        return tuple(candidates)
    if fixture_kind == "aggregate":
        return (("AGGREGATE", f"{name}{args}"),)
    return ()


def _surviving_target(
    case: AlterRoutineFactorCase,
    a: dict[str, str],
    p: str,
    fixture_kind: str,
    branch: str,
    needs_src_schema: bool,
    needs_dst_schema: bool,
) -> tuple[str, str]:
    name = _fixture_name(case, a, p)
    args = _fixture_args(a)
    if fixture_kind == "function":
        return ("FUNCTION", f"{name}{args}")
    if fixture_kind == "aggregate":
        return ("AGGREGATE", f"{name}{args}")
    if fixture_kind != "procedure":
        return ("", "")
    orig = f"{p}src_schema." if needs_src_schema else ""
    if case.kind == "RISK":
        return ("PROCEDURE", f"{name}{args}")
    if branch == _BRANCH_RENAME and case.outcome == "success":
        new = _new_name(case, a, p)
        return ("PROCEDURE", f"{orig}{new}{args}")
    if needs_dst_schema and case.outcome == "success":
        return ("PROCEDURE", f"{p}dst_schema.{name}{args}")
    if needs_src_schema:
        return ("PROCEDURE", f"{p}src_schema.{name}{args}")
    return ("PROCEDURE", f"{name}{args}")


def _role_names(
    case: AlterRoutineFactorCase,
    a: dict[str, str],
    p: str,
    branch: str,
    effective: str,
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}alter":
        roles.append(f"{p}alter")
    elif effective == f"{p}actor":
        roles.append(f"{p}actor")
    if branch == _BRANCH_OWNER and _owner_target(case, a, p) == f"{p}new_owner":
        roles.append(f"{p}new_owner")
    if effective:
        roles.append(f"{p}owner")
    return tuple(roles)


def _fixture_create(
    fixture_kind: str,
    schema_prefix: str,
    name: str,
    args: str,
) -> str:
    if fixture_kind == "function":
        return (
            f"CREATE FUNCTION {schema_prefix}{name}{args} RETURNS integer "
            "AS $$ SELECT 1 $$ LANGUAGE sql;"
        )
    if fixture_kind == "procedure":
        return (
            f"CREATE PROCEDURE {schema_prefix}{name}{args} "
            "LANGUAGE sql AS $$ SELECT 1 $$;"
        )
    if fixture_kind == "aggregate":
        return (
            f"CREATE AGGREGATE {schema_prefix}{name}{args} "
            "(SFUNC = int4_sum, STYPE = bigint, INITCOND = '0');"
        )
    return "SELECT 1 AS target_routine_intentionally_absent;"


def _resolve_case(case: AlterRoutineFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    fixture_kind = _fixture_kind(case)
    ref = _routine_name(case, a, p)
    target_args = _target_args(case, a)
    name = _fixture_name(case, a, p)
    fixture_args = _fixture_args(a)

    setup: list[str] = []
    locus = "target.routine"

    needs_src_schema = a.get("routine_name_shape") == "schema_qualified_name"
    needs_dst_schema = (
        branch == _BRANCH_SET_SCHEMA
        and _schema_target(case, a, p) == f"{p}dst_schema"
    )
    if needs_src_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}src_schema;")
    if needs_dst_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}dst_schema;")

    effective = _effective_role(case, a, p)
    if branch == _BRANCH_OWNER:
        owner = _owner_target(case, a, p)
        if owner == f"{p}new_owner":
            setup.append(f"CREATE ROLE {p}new_owner LOGIN;")
    if effective:
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        setup.append(f"GRANT CREATE ON SCHEMA public TO {p}owner;")
        if needs_src_schema:
            setup.append(f"GRANT CREATE ON SCHEMA {p}src_schema TO {p}owner;")
            setup.append(f"GRANT USAGE ON SCHEMA {p}src_schema TO {p}owner;")
        if needs_dst_schema:
            setup.append(f"GRANT CREATE ON SCHEMA {p}dst_schema TO {p}owner;")
            setup.append(f"GRANT USAGE ON SCHEMA {p}dst_schema TO {p}owner;")
        if effective == f"{p}alter":
            setup.append(f"CREATE ROLE {p}alter LOGIN;")
        elif effective == f"{p}actor":
            setup.append(f"CREATE ROLE {p}actor LOGIN;")
            setup.append(f"GRANT USAGE ON SCHEMA public TO {p}actor;")
        setup.append(f"SET ROLE {p}owner;")
        locus = "fixture.privilege_state"

    schema_prefix = f"{p}src_schema." if needs_src_schema else ""
    setup.append(
        _fixture_create(fixture_kind, schema_prefix, name, fixture_args)
    )
    if fixture_kind != "function" and fixture_kind != "procedure" and fixture_kind != "aggregate":
        pass
    elif fixture_kind == "function":
        locus = "fixture.function"
    elif fixture_kind == "procedure":
        locus = "fixture.procedure"
    elif fixture_kind == "aggregate":
        locus = "fixture.aggregate"

    if (
        case.factor_key == "new_name_shape"
        and case.factor_value == "existing_name_conflict"
    ):
        dup_schema = f"{p}src_schema." if needs_src_schema else ""
        dup_kind = "PROCEDURE" if fixture_kind == "procedure" else (
            "FUNCTION" if fixture_kind == "function" else "AGGREGATE"
        )
        setup.append(
            f"CREATE {dup_kind} {dup_schema}{p}dup_routine{fixture_args} "
            "LANGUAGE sql AS $$ SELECT 1 $$;"
            if dup_kind != "AGGREGATE"
            else f"CREATE AGGREGATE {dup_schema}{p}dup_routine{fixture_args} "
            "(SFUNC = int4_sum, STYPE = bigint, INITCOND = '0');"
        )

    if effective:
        if effective == f"{p}alter":
            grant_schema = (
                f"{p}src_schema."
                if (needs_src_schema and fixture_kind != "none")
                else ""
            )
            grant_kind = {
                "function": "FUNCTION",
                "procedure": "PROCEDURE",
                "aggregate": "FUNCTION",
            }.get(fixture_kind, "FUNCTION")
            setup.append(
                f"GRANT EXECUTE ON {grant_kind} "
                f"{grant_schema}{name}{fixture_args} TO {p}alter;"
            )
        setup.append("RESET ROLE;")
        setup.append(f"SET ROLE {effective};")

    if branch == _BRANCH_ACTION_FORM:
        action_clause = _action_clause(case, a, p)
        target = f"ALTER ROUTINE {ref}{target_args} {action_clause};"
    elif branch == _BRANCH_RENAME:
        target = f"ALTER ROUTINE {ref}{target_args} RENAME TO {_new_name(case, a, p)};"
    elif branch == _BRANCH_OWNER:
        target = f"ALTER ROUTINE {ref}{target_args} OWNER TO {_owner_target(case, a, p)};"
    elif branch == _BRANCH_SET_SCHEMA:
        target = f"ALTER ROUTINE {ref}{target_args} SET SCHEMA {_schema_target(case, a, p)};"
    elif branch == _BRANCH_DEPENDS_EXTENSION:
        target = f"ALTER ROUTINE {ref}{target_args} {_ext_clause(case, a, p)};"
    else:
        raise AlterRoutineFactorRenderError(f"unknown branch {branch}")

    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    assert_lines: list[str] = []
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    assert_lines.append(
        f"SELECT :'target_sqlstate' = "
        f"'{case.expected_sqlstate}' AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p))

    drop_mode = a.get("cleanup_mode", "drop_routine")
    if case.factor_key == "cleanup_mode":
        drop_mode = case.factor_value
    kind, surviving = _surviving_target(
        case, a, p, fixture_kind, branch, needs_src_schema, needs_dst_schema
    )
    candidates = _routine_candidates(
        case, a, p, fixture_kind, branch, needs_src_schema, needs_dst_schema
    )
    roles = _role_names(case, a, p, branch, effective)
    schema_drops: list[str] = []
    if needs_src_schema:
        schema_drops.append(f"DROP SCHEMA IF EXISTS {p}src_schema CASCADE;")
    if needs_dst_schema:
        schema_drops.append(f"DROP SCHEMA IF EXISTS {p}dst_schema CASCADE;")
    idempotent_drops = [
        f"DROP {cand_kind} IF EXISTS {cand_name} CASCADE;"
        for cand_kind, cand_name in candidates
    ]
    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    pre_cleanup: list[str] = []
    pre_cleanup.extend(idempotent_drops)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    pre_cleanup.extend(schema_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    if kind:
        cleanup.append(f"DROP {kind} IF EXISTS {surviving} CASCADE;")
    cleanup.extend(idempotent_drops)
    cleanup.extend(role_drops)
    cleanup.extend(schema_drops)
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


def resolve_alter_routine_factor_witness(
    case: AlterRoutineFactorCase | AlterRoutineFactorExtensionCase,
    repository_root: Path,
) -> AlterRoutineFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterRoutineFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_routine(sql: str) -> int:
    """Count the single credited ALTER ROUTINE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+ROUTINE\b", region))


def _header(case: AlterRoutineFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER ROUTINE {case.factor_key}={case.factor_value}",
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


def render_alter_routine_factor_case(
    case: AlterRoutineFactorCase | AlterRoutineFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER ROUTINE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地过程和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER ROUTINE。")
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


def generate_alter_routine_factor_programs(
    baseline_plan: AlterRoutineFactorLoopPlan,
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
    case: AlterRoutineFactorCase | AlterRoutineFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_routine_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterRoutineFactorRenderError",
    "AlterRoutineFactorWitness",
    "count_primary_alter_routine",
    "generate_alter_routine_factor_programs",
    "render_alter_routine_factor_case",
    "resolve_alter_routine_factor_witness",
]
