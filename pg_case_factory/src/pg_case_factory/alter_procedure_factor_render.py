"""Render complete PostgreSQL 18.4 ALTER PROCEDURE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_procedure_factor_extension import (
    AlterProcedureFactorExtensionCase,
)
from .alter_procedure_factor_loop import (
    AlterProcedureFactorCase,
    AlterProcedureFactorLoopPlan,
)


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/procedure/"
    "alter_procedure.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/procedure/"
    "alter_procedure.yaml"
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

# Canonical factor values that reach the target check and are rejected because
# the resolved routine signature does not match (SQLSTATE 42883).
_SIGNATURE_MISMATCH_PRIMARIES = {
    ("object_state", "different_signature_exists"),
    ("target_procedure_not_exists", "procedure_signature_not_found"),
    ("argtype_specification", "with_partial_signature"),
}

# For an extension SUCCESS case the synthetic primary must be the factor each
# branch's success probe depends on.  branch_rename needs (new_name_shape,
# <crossed value>) so _probe_name returns the renamed name; every other
# branch uses (object_state, "exists") as a neutral success primary.
_BRANCH_RENAME_SUCCESS_KEY = "new_name_shape"
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: AlterProcedureFactorExtensionCase,
) -> AlterProcedureFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .alter_procedure_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    branch = assignment["grammar_branch"]
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif branch == _BRANCH_RENAME and ext.outcome == "success":
        factor_key = _BRANCH_RENAME_SUCCESS_KEY
        factor_value = assignment["new_name_shape"]
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return AlterProcedureFactorCase(
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
    case: AlterProcedureFactorCase | AlterProcedureFactorExtensionCase,
) -> AlterProcedureFactorCase:
    if isinstance(case, AlterProcedureFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterProcedureFactorRenderError(ValueError):
    """Raised when an ALTER PROCEDURE case cannot be rendered."""


@dataclass(frozen=True)
class AlterProcedureFactorWitness:
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


def _baseline(case: AlterProcedureFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _proc_name(case: AlterProcedureFactorCase, a: dict[str, str], p: str) -> str:
    """The target routine name as referenced inside ALTER PROCEDURE."""

    shape = a.get("procedure_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Procedure"'
    if shape == "reserved_word":
        return f'"{p}select"'
    if shape == "schema_qualified":
        return f"{p}src_schema.{p}proc"
    return f"{p}proc"


def _fixture_name(case: AlterProcedureFactorCase, a: dict[str, str], p: str) -> str:
    """The name used in the fixture CREATE, before any RENAME/SET SCHEMA."""

    shape = a.get("procedure_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Procedure"'
    if shape == "reserved_word":
        return f'"{p}select"'
    return f"{p}proc"


def _target_args(case: AlterProcedureFactorCase, a: dict[str, str]) -> str:
    # The function fixture for same_name_is_function is created with (integer);
    # ALTER PROCEDURE must resolve to that signature to surface 42809.
    if (
        case.factor_key == "target_procedure_different_type"
        and case.factor_value == "same_name_is_function"
    ):
        return "(integer)"
    primary = (case.factor_key, case.factor_value)
    if primary in _SIGNATURE_MISMATCH_PRIMARIES:
        return "(integer, text)"
    spec = a.get("argtype_specification", "with_full_signature")
    if spec == "with_partial_signature":
        return "(integer, text)"
    if spec == "without_signature":
        return ""
    return "(integer)"


def _config_guc(case: AlterProcedureFactorCase, a: dict[str, str], p: str) -> str:
    if a.get("configuration_parameter_shape") == "invalid_parameter":
        return f"{p}no_such_guc"
    return "work_mem"


def _action_clause(
    case: AlterProcedureFactorCase, a: dict[str, str], p: str
) -> str:
    action = case.consumer_action_id
    if case.factor_key == "conflicting_action":
        return "SECURITY INVOKER SECURITY DEFINER"
    ext = "EXTERNAL " if a.get("external_keyword") == "present" else ""
    form = a.get("set_assignment_form", "to_value")
    guc = _config_guc(case, a, p)
    clauses = {
        "security_invoker": f"{ext}SECURITY INVOKER",
        "security_definer": f"{ext}SECURITY DEFINER",
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
        raise AlterProcedureFactorRenderError(
            f"no branch_1 action clause for {action}"
        )
    # invalid_parameter crossed with reset_all: RESET ALL ignores the guc and
    # succeeds (00000); reference the unrecognized guc so 42704 surfaces.
    if (
        action == "reset_all"
        and a.get("configuration_parameter_shape") == "invalid_parameter"
    ):
        clause = f"RESET {guc}"
    if a.get("action_list_cardinality") == "multiple_actions":
        # Append a DISTINCT action so the combination succeeds (00000); a
        # bare " SECURITY INVOKER" duplicates when the base is already
        # security_invoker/definer, surfacing 42601.
        if "SECURITY INVOKER" in clause or "SECURITY DEFINER" in clause:
            clause = f"{clause} SET work_mem = 100"
        else:
            clause = f"{clause} SECURITY INVOKER"
    if a.get("restrict_clause") == "present":
        clause = f"{clause} RESTRICT"
    return clause


def _new_name(case: AlterProcedureFactorCase, a: dict[str, str], p: str) -> str:
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
        return f'"{p}from"'
    if form == "duplicate_name":
        return f"{p}dup_proc"
    return f"{p}renamed"


def _owner_target(case: AlterProcedureFactorCase, a: dict[str, str], p: str) -> str:
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


def _schema_target(case: AlterProcedureFactorCase, a: dict[str, str], p: str) -> str:
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


def _ext_clause(case: AlterProcedureFactorCase, a: dict[str, str], p: str) -> str:
    if case.kind == "EXT":
        target = a.get("extension_target", "extension_exists")
        dep = a.get("extension_dependency", "extension_installed")
        if target == "extension_not_exists" or dep == "extension_not_installed":
            ext = f"{p}no_such_ext"
        else:
            ext = "plpgsql"
        if target == "NO_DEPENDS":
            return f"NO DEPENDS ON EXTENSION {ext}"
        return f"DEPENDS ON EXTENSION {ext}"

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
    case: AlterProcedureFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target ALTER PROCEDURE runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        if level == "procedure_owner":
            return f"{p}owner"
        if level == "non_owner_with_alter":
            return f"{p}alter"
        if level == "non_owner_no_privilege":
            return f"{p}actor"
        return ""  # superuser

    primary = (case.factor_key, case.factor_value)
    if case.factor_key == "privilege_level":
        if case.factor_value == "procedure_owner":
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


def _probe_name(case: AlterProcedureFactorCase, a: dict[str, str], p: str) -> str:
    if case.kind == "RISK":
        return f"{p}proc"
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
    case: AlterProcedureFactorCase, a: dict[str, str], p: str
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
        "SELECT p.prokind, p.prosecdef "
        "FROM pg_catalog.pg_proc AS p "
        f"WHERE p.proname = '{name}' ORDER BY p.proname, p.oid;"
    )


def _fixture_kind(case: AlterProcedureFactorCase) -> str:
    if case.factor_key == "target_procedure_different_type":
        return "function"
    primary = (case.factor_key, case.factor_value)
    if primary in {
        ("object_state", "not_exists"),
        ("target_procedure_not_exists", "procedure_name_not_found"),
        ("expected_status", "failure"),
    }:
        return "none"
    return "procedure"


def _routine_candidates(
    case: AlterProcedureFactorCase,
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
    if fixture_kind == "function":
        return (("FUNCTION", f"{name}(integer)"),)
    if fixture_kind != "procedure":
        return ()
    candidates: list[tuple[str, str]] = []
    orig_prefix = f"{p}src_schema." if needs_src_schema else ""
    candidates.append(("PROCEDURE", f"{orig_prefix}{name}(integer)"))
    if branch == _BRANCH_RENAME:
        new = _new_name(case, a, p)
        short = new[:63] if case.factor_key == "identifier_length_exceeded" else new
        candidates.append(("PROCEDURE", f"{orig_prefix}{short}(integer)"))
    if needs_dst_schema:
        candidates.append(("PROCEDURE", f"{p}dst_schema.{name}(integer)"))
    if (
        case.factor_key == "rename_target"
        and case.factor_value == "duplicate_name"
    ):
        candidates.append(("PROCEDURE", f"{p}dup_proc(integer)"))
    return tuple(candidates)


def _surviving_target(
    case: AlterProcedureFactorCase,
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
    if fixture_kind == "function":
        return ("FUNCTION", f"{name}(integer)")
    if fixture_kind != "procedure":
        return ("", "")
    orig_prefix = f"{p}src_schema." if needs_src_schema else ""
    if case.kind == "RISK":
        return ("PROCEDURE", f"{name}(integer)")
    if branch == _BRANCH_RENAME and case.outcome == "success":
        new = _new_name(case, a, p)
        short = new[:63] if case.factor_key == "identifier_length_exceeded" else new
        return ("PROCEDURE", f"{orig_prefix}{short}(integer)")
    if needs_dst_schema and case.outcome == "success":
        return ("PROCEDURE", f"{p}dst_schema.{name}(integer)")
    if needs_src_schema:
        return ("PROCEDURE", f"{p}src_schema.{name}(integer)")
    return ("PROCEDURE", f"{name}(integer)")


def _role_names(
    case: AlterProcedureFactorCase,
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


def _resolve_case(case: AlterProcedureFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    fixture_kind = _fixture_kind(case)
    ref = _proc_name(case, a, p)
    args = _target_args(case, a)
    name = _fixture_name(case, a, p)

    setup: list[str] = []
    locus = "target.procedure"

    # --- schema fixtures -------------------------------------------------
    needs_src_schema = a.get("procedure_name_shape") == "schema_qualified"
    needs_dst_schema = branch == _BRANCH_SET_SCHEMA and _schema_target(
        case, a, p
    ) == f"{p}dst_schema"
    if needs_src_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}src_schema;")
    if needs_dst_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}dst_schema;")

    # --- role fixtures ---------------------------------------------------
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

    # --- the target routine fixture -------------------------------------
    if fixture_kind == "procedure":
        schema_prefix = f"{p}src_schema." if needs_src_schema else ""
        setup.append(
            f"CREATE PROCEDURE {schema_prefix}{name}(integer) "
            "LANGUAGE sql AS $$ SELECT 1 $$;"
        )
    elif fixture_kind == "function":
        # wrong-object fixture: a function with the same name+signature
        schema_prefix = f"{p}src_schema." if needs_src_schema else ""
        setup.append(
            f"CREATE FUNCTION {schema_prefix}{name}(integer) RETURNS integer "
            "AS $$ SELECT 1 $$ LANGUAGE sql;"
        )
        locus = "fixture.object_type"
    else:
        setup.append("SELECT 1 AS target_routine_intentionally_absent;")

    # --- duplicate-name fixture for RENAME failure -----------------------
    if case.factor_key == "rename_target" and case.factor_value == "duplicate_name":
        dup_schema = f"{p}src_schema." if needs_src_schema else ""
        setup.append(
            f"CREATE PROCEDURE {dup_schema}{p}dup_proc(integer) "
            "LANGUAGE sql AS $$ SELECT 1 $$;"
        )

    # --- close the owner fixture and arm the effective role --------------
    if effective:
        if effective == f"{p}alter":
            # Procedures only grant EXECUTE; a non-owner granted EXECUTE
            # still cannot ALTER PROCEDURE (only the owner can), surfacing
            # 42501.  Skip the GRANT when no procedure fixture exists: a
            # GRANT on an absent (not_exists) or wrong-object routine errors
            # in setup and aborts the run before the target is reached.
            if fixture_kind == "procedure":
                grant_schema = (
                    f"{p}src_schema." if needs_src_schema else ""
                )
                setup.append(
                    f"GRANT EXECUTE ON PROCEDURE {grant_schema}{name}(integer) "
                    f"TO {p}alter;"
                )
        setup.append("RESET ROLE;")
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement -----------------------------------
    if branch == _BRANCH_ACTION_FORM:
        action_clause = _action_clause(case, a, p)
        target = f"ALTER PROCEDURE {ref}{args} {action_clause};"
    elif branch == _BRANCH_RENAME:
        target = f"ALTER PROCEDURE {ref}{args} RENAME TO {_new_name(case, a, p)};"
    elif branch == _BRANCH_OWNER:
        target = f"ALTER PROCEDURE {ref}{args} OWNER TO {_owner_target(case, a, p)};"
    elif branch == _BRANCH_SET_SCHEMA:
        target = f"ALTER PROCEDURE {ref}{args} SET SCHEMA {_schema_target(case, a, p)};"
    elif branch == _BRANCH_DEPENDS_EXTENSION:
        target = f"ALTER PROCEDURE {ref}{args} {_ext_clause(case, a, p)};"
    else:
        raise AlterProcedureFactorRenderError(f"unknown branch {branch}")

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
    drop_mode = a.get("cleanup_mode", "DROP_PROCEDURE_IF_EXISTS")
    if case.factor_key == "cleanup_mode":
        drop_mode = case.factor_value
    cascade = " CASCADE" if drop_mode == "DROP_PROCEDURE_CASCADE" else ""
    if_exists = "IF EXISTS " if drop_mode == "DROP_PROCEDURE_IF_EXISTS" else ""
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
    idempotent_object_drops = [
        f"DROP {cand_kind} IF EXISTS {cand_name} CASCADE;"
        for cand_kind, cand_name in candidates
    ]
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


def resolve_alter_procedure_factor_witness(
    case: AlterProcedureFactorCase | AlterProcedureFactorExtensionCase,
    repository_root: Path,
) -> AlterProcedureFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterProcedureFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_procedure(sql: str) -> int:
    """Count the single credited ALTER PROCEDURE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+PROCEDURE\b", region))


def _header(case: AlterProcedureFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER PROCEDURE {case.factor_key}={case.factor_value}",
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


def render_alter_procedure_factor_case(
    case: AlterProcedureFactorCase | AlterProcedureFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER PROCEDURE regress program."""

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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER PROCEDURE。")
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


def generate_alter_procedure_factor_programs(
    baseline_plan: AlterProcedureFactorLoopPlan,
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
    case: AlterProcedureFactorCase | AlterProcedureFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_procedure_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterProcedureFactorRenderError",
    "AlterProcedureFactorWitness",
    "count_primary_alter_procedure",
    "generate_alter_procedure_factor_programs",
    "render_alter_procedure_factor_case",
    "resolve_alter_procedure_factor_witness",
]
