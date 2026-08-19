"""Render complete PostgreSQL 18.4 ALTER FUNCTION factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_function_factor_loop import (
    AlterFunctionFactorCase,
    AlterFunctionFactorLoopPlan,
)


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/function/"
    "alter_function.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/function/"
    "alter_function.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_ACTION_FORM = "branch_action_form"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_DEPENDS_EXTENSION = "branch_depends_extension"

# Canonical factor values that reach the target check and are rejected because
# the resolved routine signature does not match (SQLSTATE 42883).
_SIGNATURE_MISMATCH_PRIMARIES = {
    ("object_state", "different_signature_exists"),
    ("target_function_not_exists", "function_signature_not_found"),
    ("argtype_specification", "with_partial_signature"),
}


class AlterFunctionFactorRenderError(ValueError):
    """Raised when an ALTER FUNCTION case cannot be rendered."""


@dataclass(frozen=True)
class AlterFunctionFactorWitness:
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


def _baseline(case: AlterFunctionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _fn_name(case: AlterFunctionFactorCase, a: dict[str, str], p: str) -> str:
    """The target routine name as referenced inside ALTER FUNCTION."""

    shape = a.get("function_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Function"'
    if shape == "reserved_word":
        return f'"{p}select"'
    if shape == "schema_qualified":
        return f"{p}src_schema.{p}fn"
    return f"{p}fn"


def _fixture_name(case: AlterFunctionFactorCase, a: dict[str, str], p: str) -> str:
    """The name used in the fixture CREATE, before any RENAME/SET SCHEMA."""

    shape = a.get("function_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Function"'
    if shape == "reserved_word":
        return f'"{p}select"'
    return f"{p}fn"


def _target_args(case: AlterFunctionFactorCase, a: dict[str, str]) -> str:
    # The procedure fixture is created with no parameters; ALTER FUNCTION
    # must resolve to that empty signature to surface 42809 (not a function).
    if (
        case.factor_key == "target_function_different_type"
        and case.factor_value == "same_name_is_procedure"
    ):
        return "()"
    primary = (case.factor_key, case.factor_value)
    if primary in _SIGNATURE_MISMATCH_PRIMARIES:
        return "(integer, text)"
    spec = a.get("argtype_specification", "with_full_signature")
    if spec == "with_partial_signature":
        return "(integer, text)"
    if spec == "without_signature":
        return ""
    return "(integer)"


def _config_guc(case: AlterFunctionFactorCase, a: dict[str, str], p: str) -> str:
    if a.get("configuration_parameter_shape") == "invalid_parameter":
        return f"{p}no_such_guc"
    return "work_mem"


def _action_clause(
    case: AlterFunctionFactorCase, a: dict[str, str], p: str
) -> str:
    action = case.consumer_action_id
    if case.factor_key == "conflicting_action":
        return "IMMUTABLE VOLATILE"
    ext = "EXTERNAL " if a.get("external_keyword") == "present" else ""
    form = a.get("set_assignment_form", "to_value")
    guc = _config_guc(case, a, p)
    clauses = {
        "called_on_null_input": "CALLED ON NULL INPUT",
        "returns_null_on_null_input": "RETURNS NULL ON NULL INPUT",
        "strict": "STRICT",
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
        "support": f"SUPPORT {p}support_fn",
        "reset_all": "RESET ALL",
    }
    if action in clauses:
        clause = clauses[action]
    elif action == "set_parameter":
        if form == "equals_value":
            clause = f"SET {guc} = 100"
        elif form == "to_default":
            clause = f"SET {guc} TO DEFAULT"
        else:
            clause = f"SET {guc} TO 100"
    elif action == "reset_parameter":
        clause = f"RESET {guc}"
    else:
        raise AlterFunctionFactorRenderError(
            f"no branch_1 action clause for {action}"
        )
    if a.get("action_list_cardinality") == "multiple_actions":
        clause = f"{clause} STRICT"
    if a.get("restrict_clause") == "present":
        clause = f"{clause} RESTRICT"
    return clause


def _new_name(case: AlterFunctionFactorCase, a: dict[str, str], p: str) -> str:
    if case.factor_key == "rename_target":
        form = case.factor_value
    elif case.factor_key == "new_name_shape":
        form = case.factor_value
    elif case.factor_key == "identifier_length_exceeded":
        return f"{p}over_sixty_three_characters_identifier_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    else:
        form = a.get("new_name_shape", "simple")
    if form == "quoted":
        return f'"{p}Mixed Name"'
    if form == "reserved_word":
        return f'"{p}select"'
    if form == "duplicate_name":
        return f"{p}dup_fn"
    return f"{p}renamed"


def _owner_target(case: AlterFunctionFactorCase, a: dict[str, str], p: str) -> str:
    if case.factor_key == "owner_target":
        value = case.factor_value
    elif case.factor_key == "role_dependency":
        if case.factor_value == "owner_role_not_exists":
            return f"{p}nonexistent_role"
        return f"{p}new_owner"
    else:
        value = a.get("owner_target", "new_owner_role")
    if value in {"CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"}:
        return value
    if value == "nonexistent_role":
        return f"{p}nonexistent_role"
    return f"{p}new_owner"


def _schema_target(case: AlterFunctionFactorCase, a: dict[str, str], p: str) -> str:
    if case.factor_key == "schema_target":
        value = case.factor_value
    elif case.factor_key == "schema_dependency":
        if case.factor_value == "target_schema_not_exists":
            return f"{p}no_such_schema"
        if case.factor_value == "reserved_schema":
            return "pg_catalog"
        return f"{p}dst_schema"
    else:
        value = a.get("schema_target", "schema_exists")
    if value == "schema_not_exists":
        return f"{p}no_such_schema"
    if value == "pg_catalog_reserved":
        return "pg_catalog"
    if value == "information_schema_reserved":
        return "information_schema"
    return f"{p}dst_schema"


def _ext_clause(case: AlterFunctionFactorCase, a: dict[str, str], p: str) -> str:
    polarity = a.get("depends_polarity", "depends")
    if case.factor_key == "extension_target":
        if case.factor_value == "extension_not_exists":
            ext = f"{p}no_such_ext"
        else:
            ext = "plpgsql"
    elif case.factor_key == "extension_dependency":
        ext = f"{p}no_such_ext" if case.factor_value == "extension_not_installed" else "plpgsql"
    else:
        ext = "plpgsql"
    if case.factor_key == "depends_polarity" and case.factor_value == "no_depends":
        polarity = "no_depends"
    if polarity == "no_depends":
        return f"NO DEPENDS ON EXTENSION {ext}"
    return f"DEPENDS ON EXTENSION {ext}"


def _effective_role(
    case: AlterFunctionFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target ALTER FUNCTION runs."""

    primary = (case.factor_key, case.factor_value)
    if case.factor_key == "privilege_level":
        if case.factor_value == "function_owner":
            return f"{p}owner"
        if case.factor_value == "non_owner_with_alter":
            return f"{p}alter"
        if case.factor_value == "non_owner_no_privilege":
            return f"{p}actor"
        return ""  # superuser
    if case.factor_key == "permission_insufficient":
        return f"{p}actor"
    if primary in {
        ("schema_target", "pg_catalog_reserved"),
        ("schema_target", "information_schema_reserved"),
        ("schema_dependency", "reserved_schema"),
    }:
        return f"{p}owner"
    return ""


def _probe_name(case: AlterFunctionFactorCase, a: dict[str, str], p: str) -> str:
    if case.kind == "RISK":
        return f"{p}fn"
    if case.factor_key == "rename_target" and case.outcome == "success":
        return _new_name(case, a, p).strip('"')
    if case.factor_key == "new_name_shape" and case.outcome == "success":
        return _new_name(case, a, p).strip('"')
    if case.factor_key == "identifier_length_exceeded":
        long_name = _new_name(case, a, p)
        return long_name[:63]
    name = _fixture_name(case, a, p)
    return name.strip('"')


def _probe_select(
    case: AlterFunctionFactorCase, a: dict[str, str], p: str
) -> str:
    mode = a.get("verification_mode", "pg_proc_catalog_query")
    if case.factor_key == "verification_mode":
        mode = case.factor_value
    name = _probe_name(case, a, p)
    if mode == "information_schema_routines":
        return (
            "SELECT r.routine_schema, r.routine_name, r.routine_type "
            "FROM information_schema.routines AS r "
            f"WHERE r.routine_name = '{name}' "
            "ORDER BY r.routine_schema, r.routine_name;"
        )
    if mode == "pg_get_functiondef":
        return (
            "SELECT pg_get_functiondef(p.oid) "
            "FROM pg_catalog.pg_proc AS p "
            f"WHERE p.proname = '{name}' ORDER BY p.oid;"
        )
    return (
        "SELECT p.provolatile, p.prokind, p.prosecdef, p.proleakproof, "
        "p.proparallel, p.procost, p.prorows "
        "FROM pg_catalog.pg_proc AS p "
        f"WHERE p.proname = '{name}' ORDER BY p.proname, p.oid;"
    )


def _fixture_kind(case: AlterFunctionFactorCase) -> str:
    if case.factor_key == "target_function_different_type":
        return "aggregate" if case.factor_value == "same_name_is_aggregate" else "procedure"
    primary = (case.factor_key, case.factor_value)
    if primary in {
        ("object_state", "not_exists"),
        ("target_function_not_exists", "function_name_not_found"),
        ("expected_status", "failure"),
    }:
        return "none"
    return "function"


def _routine_candidates(
    case: AlterFunctionFactorCase,
    a: dict[str, str],
    p: str,
    fixture_kind: str,
    branch: str,
    needs_src_schema: bool,
    needs_dst_schema: bool,
) -> tuple[tuple[str, str], ...]:
    """Every (drop_kind, qualified_name_with_args) the target routine could
    be found under before or after the target, for idempotent re-drops."""

    name = _fixture_name(case, a, p)
    if fixture_kind == "aggregate":
        return (("AGGREGATE", f"{name}(integer)"),)
    if fixture_kind == "procedure":
        return (("PROCEDURE", f"{name}()"),)
    if fixture_kind != "function":
        return ()
    candidates: list[tuple[str, str]] = []
    orig_prefix = f"{p}src_schema." if needs_src_schema else ""
    candidates.append(("FUNCTION", f"{orig_prefix}{name}(integer)"))
    if branch == _BRANCH_RENAME:
        new = _new_name(case, a, p)
        if case.factor_key == "identifier_length_exceeded":
            candidates.append(("FUNCTION", f"{new[:63]}(integer)"))
        else:
            candidates.append(("FUNCTION", f"{new}(integer)"))
    if needs_dst_schema:
        candidates.append(("FUNCTION", f"{p}dst_schema.{name}(integer)"))
    if (
        case.factor_key == "rename_target"
        and case.factor_value == "duplicate_name"
    ):
        candidates.append(("FUNCTION", f"{p}dup_fn(integer)"))
    return tuple(candidates)


def _surviving_target(
    case: AlterFunctionFactorCase,
    a: dict[str, str],
    p: str,
    fixture_kind: str,
    branch: str,
    needs_src_schema: bool,
    needs_dst_schema: bool,
) -> tuple[str, str]:
    """The (drop_kind, qualified_name_with_args) the target routine is under
    AFTER the target statement, for the factor-form teardown witness."""

    name = _fixture_name(case, a, p)
    if fixture_kind == "aggregate":
        return ("AGGREGATE", f"{name}(integer)")
    if fixture_kind == "procedure":
        return ("PROCEDURE", f"{name}()")
    if fixture_kind != "function":
        return ("", "")
    if case.kind == "RISK":
        return ("FUNCTION", f"{name}(integer)")
    if branch == _BRANCH_RENAME and case.outcome == "success":
        new = _new_name(case, a, p)
        if case.factor_key == "identifier_length_exceeded":
            return ("FUNCTION", f"{new[:63]}(integer)")
        return ("FUNCTION", f"{new}(integer)")
    if needs_dst_schema:
        return ("FUNCTION", f"{p}dst_schema.{name}(integer)")
    if needs_src_schema:
        return ("FUNCTION", f"{p}src_schema.{name}(integer)")
    return ("FUNCTION", f"{name}(integer)")


def _role_names(
    case: AlterFunctionFactorCase,
    a: dict[str, str],
    p: str,
    branch: str,
    effective: str,
) -> tuple[str, ...]:
    """Roles to tear down, ordered members/grantees before the owner role."""

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


def _resolve_case(case: AlterFunctionFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    fixture_kind = _fixture_kind(case)
    ref = _fn_name(case, a, p)
    args = _target_args(case, a)
    name = _fixture_name(case, a, p)

    setup: list[str] = []
    locus = "target.function"

    # --- schema fixtures -------------------------------------------------
    needs_src_schema = a.get("function_name_shape") == "schema_qualified"
    needs_dst_schema = branch == _BRANCH_SET_SCHEMA and _schema_target(
        case, a, p
    ) == f"{p}dst_schema"
    if needs_src_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}src_schema;")
    if needs_dst_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}dst_schema;")

    # --- role fixtures ---------------------------------------------------
    effective = _effective_role(case, a, p)
    # The OWNER-branch new_owner role must be created by the superuser:
    # a plain LOGIN owner role lacks CREATEROLE and would reject
    # CREATE ROLE with 42501 once SET ROLE owner has taken effect.
    if branch == _BRANCH_OWNER:
        owner = _owner_target(case, a, p)
        if owner == f"{p}new_owner":
            setup.append(f"CREATE ROLE {p}new_owner LOGIN;")
    if effective:
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        setup.append(f"GRANT CREATE ON SCHEMA public TO {p}owner;")
        if effective == f"{p}alter":
            setup.append(f"CREATE ROLE {p}alter LOGIN;")
        elif effective == f"{p}actor":
            setup.append(f"CREATE ROLE {p}actor LOGIN;")
            setup.append(f"GRANT USAGE ON SCHEMA public TO {p}actor;")
        setup.append(f"SET ROLE {p}owner;")
        locus = "fixture.privilege_state"

    # --- the target routine fixture -------------------------------------
    if fixture_kind == "function":
        volatility = " IMMUTABLE" if case.kind == "RISK" else ""
        schema_prefix = f"{p}src_schema." if needs_src_schema else ""
        # ROWS is only applicable to set-returning functions; a scalar
        # RETURNS integer fixture would reject ROWS with SQLSTATE 22023.
        returns_clause = (
            "RETURNS SETOF integer"
            if case.consumer_action_id == "rows"
            else "RETURNS integer"
        )
        setup.append(
            f"CREATE FUNCTION {schema_prefix}{name}(integer) {returns_clause} "
            f"AS $$ SELECT $1 $$ LANGUAGE sql{volatility};"
        )
    elif fixture_kind == "aggregate":
        setup.append(
            f"CREATE AGGREGATE {name}(integer) "
            "(SFUNC = int4_sum, STYPE = bigint, INITCOND = '0');"
        )
        locus = "fixture.object_type"
    elif fixture_kind == "procedure":
        setup.append(
            f"CREATE PROCEDURE {name}() "
            "LANGUAGE sql AS $$ SELECT 1 $$;"
        )
        locus = "fixture.object_type"
    else:
        # No routine is created: the target is expected to fail because the
        # named function does not exist.  Emit a deterministic probe so the
        # program still carries an observable setup locus.
        setup.append("SELECT 1 AS target_routine_intentionally_absent;")

    # --- support function fixture (SUPPORT action, superuser only) -------
    if case.consumer_action_id == "support":
        setup.append(
            f"CREATE FUNCTION {p}support_fn(internal) RETURNS internal "
            "LANGUAGE internal AS 'int4inc';"
        )

    # --- duplicate-name fixture for RENAME failure -----------------------
    if case.factor_key == "rename_target" and case.factor_value == "duplicate_name":
        setup.append(
            f"CREATE FUNCTION {p}dup_fn(integer) RETURNS integer "
            "AS $$ SELECT 1 $$ LANGUAGE sql;"
        )

    # --- close the owner fixture and arm the effective role --------------
    if effective:
        if effective == f"{p}alter":
            # Functions only grant EXECUTE; GRANT ALTER ON FUNCTION is not
            # valid syntax.  A non-owner granted EXECUTE still cannot ALTER
            # FUNCTION (only the owner can), surfacing 42501.
            setup.append(
                f"GRANT EXECUTE ON FUNCTION {name}(integer) TO {p}alter;"
            )
        setup.append("RESET ROLE;")
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement -----------------------------------
    if branch == _BRANCH_ACTION_FORM:
        action_clause = _action_clause(case, a, p)
        target = f"ALTER FUNCTION {ref}{args} {action_clause};"
    elif branch == _BRANCH_RENAME:
        target = f"ALTER FUNCTION {ref}{args} RENAME TO {_new_name(case, a, p)};"
    elif branch == _BRANCH_OWNER:
        target = f"ALTER FUNCTION {ref}{args} OWNER TO {_owner_target(case, a, p)};"
    elif branch == _BRANCH_SET_SCHEMA:
        target = f"ALTER FUNCTION {ref}{args} SET SCHEMA {_schema_target(case, a, p)};"
    elif branch == _BRANCH_DEPENDS_EXTENSION:
        target = f"ALTER FUNCTION {ref}{args} {_ext_clause(case, a, p)};"
    else:
        raise AlterFunctionFactorRenderError(f"unknown branch {branch}")

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if case.kind == "RISK":
        assert_lines.append("COMMIT;" if case.factor_value == "commit" else "ROLLBACK;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p))

    # --- cleanup construction ------------------------------------------
    # Section 1 (pre-cleanup) is a fully idempotent superset so the file is
    # re-runnable from a clean state under ON_ERROR_STOP=on.  Section 5
    # (final cleanup) keeps the factor-form teardown as the byte-level witness
    # and follows it with the same idempotent re-drops; the runtime re-runs
    # section 5 as a best-effort safety net with ON_ERROR_STOP=off, so the
    # non-idempotent bare / CASCADE factor forms are tolerated on re-run.
    drop_mode = a.get("cleanup_mode", "DROP_FUNCTION_IF_EXISTS")
    if case.factor_key == "cleanup_mode":
        drop_mode = case.factor_value
    cascade = " CASCADE" if drop_mode == "DROP_FUNCTION_CASCADE" else ""
    if_exists = "IF EXISTS " if drop_mode == "DROP_FUNCTION_IF_EXISTS" else ""
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
    support_drop = (
        [f"DROP FUNCTION IF EXISTS {p}support_fn(internal) CASCADE;"]
        if case.consumer_action_id == "support"
        else []
    )
    idempotent_object_drops = [
        f"DROP {cand_kind} IF EXISTS {cand_name} CASCADE;"
        for cand_kind, cand_name in candidates
    ] + support_drop
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    pre_cleanup: list[str] = []
    pre_cleanup.extend(idempotent_object_drops)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    pre_cleanup.extend(schema_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    if kind:
        cleanup.append(f"DROP {kind} {if_exists}{surviving}{cascade};")
    cleanup.extend(idempotent_object_drops)
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


def resolve_alter_function_factor_witness(
    case: AlterFunctionFactorCase,
    repository_root: Path,
) -> AlterFunctionFactorWitness:
    """Return the byte-level witness fragments for one case."""

    plan = _resolve_case(case)
    return AlterFunctionFactorWitness(
        primary_obligation_id=case.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=case.outcome,
        expected_sqlstate=case.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_function(sql: str) -> int:
    """Count the single credited ALTER FUNCTION inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+FUNCTION\b", region))


def _header(case: AlterFunctionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER FUNCTION {case.factor_key}={case.factor_value}",
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


def render_alter_function_factor_case(
    plan: AlterFunctionFactorLoopPlan,
    case: AlterFunctionFactorCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER FUNCTION regress program."""

    resolved = _resolve_case(case)
    lines: list[str] = list(_header(case))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地函数和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER FUNCTION。")
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


__all__ = [
    "AlterFunctionFactorRenderError",
    "AlterFunctionFactorWitness",
    "count_primary_alter_function",
    "render_alter_function_factor_case",
    "resolve_alter_function_factor_witness",
]
