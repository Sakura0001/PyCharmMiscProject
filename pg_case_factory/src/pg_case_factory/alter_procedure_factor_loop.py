"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER PROCEDURE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER PROCEDURE``.  It must not enumerate a signature/type cross product:
``alter_procedure.yaml`` marks column/table/relation coverage
``not_applicable``, so there is no ``INV`` block.  Each local obligation will
become exactly one regress program; there are no delegated handoffs because
every reachable negative boundary is a real ``ALTER PROCEDURE`` error that
belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_procedure_regress import (
    AlterProcedureRegressError,
    load_alter_procedure_grammar_actions,
    load_alter_procedure_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterProcedureFactorLoopError(ValueError):
    """Raised when a frozen ALTER PROCEDURE obligation input drifts."""


@dataclass(frozen=True)
class AlterProcedureFactorObligation:
    ordinal: int
    obligation_id: str
    kind: str
    factor_key: str
    value: str
    consumer_action_id: str
    disposition: str
    source_locator: str
    delegated_statement_key: str | None = None


@dataclass(frozen=True)
class AlterProcedureFactorCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    primary_obligation_id: str
    kind: str
    factor_key: str
    factor_value: str
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    baseline_assignments: tuple[tuple[str, str], ...]
    execution_profile: str


@dataclass(frozen=True)
class AlterProcedureFactorLoopPlan:
    obligations: tuple[AlterProcedureFactorObligation, ...]
    cases: tuple[AlterProcedureFactorCase, ...]
    delegated: tuple[AlterProcedureFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches.
_BRANCH_ACTION_FORM = "branch_action_form"

# A representative branch_1 action used as the baseline consumer for
# signature-level / outer modifiers that are not bound to one sub-clause.
_REPRESENTATIVE_ACTION = "security_invoker"

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, action_type,
# permission_insufficient) are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "restrict_clause": _REPRESENTATIVE_ACTION,
    "rename_target": "rename",
    "owner_target": "owner",
    "schema_target": "set_schema",
    "extension_target": "depends_on_extension",
    "argtype_specification": _REPRESENTATIVE_ACTION,
    "procedure_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "configuration_parameter_shape": "set_parameter",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "schema_dependency": "set_schema",
    "role_dependency": "owner",
    "extension_dependency": "depends_on_extension",
    "target_procedure_not_exists": _REPRESENTATIVE_ACTION,
    "target_procedure_different_type": _REPRESENTATIVE_ACTION,
    "conflicting_action": _REPRESENTATIVE_ACTION,
    "identifier_length_exceeded": "rename",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER = {
    "branch_1": _REPRESENTATIVE_ACTION,
    "branch_2": "rename",
    "branch_3": "owner",
    "branch_4": "set_schema",
    "branch_5": "depends_on_extension",
}

_ACTION_TYPE_CONSUMER = {
    "SECURITY_INVOKER": "security_invoker",
    "SECURITY_DEFINER": "security_definer",
    "SET_parameter": "set_parameter",
    "RESET_parameter": "reset_parameter",
    "RESET_ALL": "reset_all",
}

_PERMISSION_INSUFFICIENT_CONSUMER = {
    "no_alter_privilege": _REPRESENTATIVE_ACTION,
    "not_owner_for_OWNER_TO": "owner",
    "not_owner_for_SET_SCHEMA": "set_schema",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (verified against PG 18.4).  ``without_signature`` is a legal
# success for a unique-name procedure, and ``over_63_chars`` succeeds via
# NAMEDATALEN truncation, so neither is an expected failure.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("object_state", "different_signature_exists"),
        ("rename_target", "duplicate_name"),
        ("owner_target", "nonexistent_role"),
        ("schema_target", "schema_not_exists"),
        ("schema_target", "pg_catalog_reserved"),
        ("schema_target", "information_schema_reserved"),
        ("extension_target", "extension_not_exists"),
        ("argtype_specification", "with_partial_signature"),
        ("configuration_parameter_shape", "invalid_parameter"),
        ("privilege_level", "non_owner_no_privilege"),
        # A non-owner cannot ALTER PROCEDURE: only the owner can (procedures
        # have no grantable ALTER privilege; EXECUTE does not suffice).
        ("privilege_level", "non_owner_with_alter"),
        ("schema_dependency", "target_schema_not_exists"),
        ("schema_dependency", "reserved_schema"),
        ("role_dependency", "owner_role_not_exists"),
        ("extension_dependency", "extension_not_installed"),
        ("target_procedure_not_exists", "procedure_name_not_found"),
        ("target_procedure_not_exists", "procedure_signature_not_found"),
        ("target_procedure_different_type", "same_name_is_function"),
        ("permission_insufficient", "no_alter_privilege"),
        ("permission_insufficient", "not_owner_for_OWNER_TO"),
        ("permission_insufficient", "not_owner_for_SET_SCHEMA"),
        ("conflicting_action", "conflicting_security_modes"),
    }
)


def _axis_consumer(action_id: str) -> str:
    """Resolve the baseline action that witnesses an outer/axis modifier."""

    if action_id == "__outer_action__":
        return _REPRESENTATIVE_ACTION
    return action_id


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterProcedureFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "action_type":
        try:
            return _ACTION_TYPE_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterProcedureFactorLoopError(
                f"unknown action_type value: {row.value}"
            ) from exc
    if row.factor == "permission_insufficient":
        try:
            return _PERMISSION_INSUFFICIENT_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterProcedureFactorLoopError(
                f"unknown permission_insufficient value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterProcedureFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterProcedureFactorObligation]:
    rows: list[AlterProcedureFactorObligation] = []
    for action in load_alter_procedure_grammar_actions():
        rows.append(
            AlterProcedureFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AP-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    for axis in load_alter_procedure_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id == "__outer_action__"
            else f"local:{axis.axis_id}"
        )
        consumer = _axis_consumer(axis.action_id)
        for value in axis.values:
            rows.append(
                AlterProcedureFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"AP-GRM|{axis.grammar_branch_id}|"
                        f"{axis.action_id}|{axis.axis_id}|{value}"
                    ),
                    kind="GRM",
                    factor_key=factor_key,
                    value=value,
                    consumer_action_id=consumer,
                    disposition="covered",
                    source_locator=axis.source_locator,
                )
            )
    if len(rows) != 22:
        raise AlterProcedureFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterProcedureFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_procedure")
    if len(catalog_rows) != 70:
        raise AlterProcedureFactorLoopError("canonical obligation count drift")
    rows: list[AlterProcedureFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterProcedureFactorObligation(
                ordinal=0,
                obligation_id=f"AP-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure"
                    if (row.factor, row.value) in _SFV_FAILURE_VALUES
                    else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _compile_risk_obligations() -> list[AlterProcedureFactorObligation]:
    return [
        AlterProcedureFactorObligation(
            ordinal=0,
            obligation_id=f"AP-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterprocedure:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterProcedureFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-procedure-factor-obligations-v1\n")
    for row in rows:
        digest.update(
            json.dumps(
                {
                    "obligation_id": row.obligation_id,
                    "kind": row.kind,
                    "factor_key": row.factor_key,
                    "value": row.value,
                    "consumer_action_id": row.consumer_action_id,
                    "disposition": row.disposition,
                    "delegated_statement_key": row.delegated_statement_key,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _consumer_branch_map() -> dict[str, str]:
    return {
        action.action_id: action.grammar_branch_id
        for action in load_alter_procedure_grammar_actions()
    }


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Verified PG 18.4 SQLSTATE for each reachable expected-failure value.  These
# were probed against an isolated 18.4 instance under the procedure-owner
# baseline (reserved-schema rejections surface as 42501 under a non-superuser
# owner, not as a superuser-only success).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42883",
        "expected_status_failure_procedure_not_found",
    ),
    ("object_state", "not_exists"): ("42883", "procedure_does_not_exist"),
    ("object_state", "different_signature_exists"): (
        "42883",
        "procedure_signature_does_not_exist",
    ),
    ("rename_target", "duplicate_name"): (
        "42710",
        "duplicate_object",
    ),
    ("owner_target", "nonexistent_role"): ("42704", "role_does_not_exist"),
    ("schema_target", "schema_not_exists"): ("3F000", "schema_does_not_exist"),
    ("schema_target", "pg_catalog_reserved"): (
        "42501",
        "permission_denied_for_reserved_schema",
    ),
    ("schema_target", "information_schema_reserved"): (
        "42501",
        "permission_denied_for_reserved_schema",
    ),
    ("extension_target", "extension_not_exists"): (
        "42704",
        "extension_does_not_exist",
    ),
    ("argtype_specification", "with_partial_signature"): (
        "42883",
        "procedure_signature_does_not_exist",
    ),
    ("configuration_parameter_shape", "invalid_parameter"): (
        "42704",
        "unrecognized_configuration_parameter",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "must_be_owner_of_procedure",
    ),
    ("privilege_level", "non_owner_with_alter"): (
        "42501",
        "must_be_owner_of_procedure",
    ),
    # Sentinel attribution key (not a real crossed-axis (factor, value)) for
    # the role-membership privilege wall that fires only under a non-superuser
    # procedure owner: OWNER TO <role> requires the issuer to be a member of
    # that role.  SESSION_USER is a permitted no-op transfer (PG 18.4) and
    # does NOT fire this wall.  Surfaced by _present_failure_pair in the
    # extension expander.
    ("owner_target", "membership_required_under_procedure_owner"): (
        "42501",
        "owner_change_requires_role_membership",
    ),
    ("schema_dependency", "target_schema_not_exists"): (
        "3F000",
        "schema_does_not_exist",
    ),
    ("schema_dependency", "reserved_schema"): (
        "42501",
        "permission_denied_for_reserved_schema",
    ),
    ("role_dependency", "owner_role_not_exists"): (
        "42704",
        "role_does_not_exist",
    ),
    ("extension_dependency", "extension_not_installed"): (
        "42704",
        "extension_does_not_exist",
    ),
    ("target_procedure_not_exists", "procedure_name_not_found"): (
        "42883",
        "procedure_does_not_exist",
    ),
    ("target_procedure_not_exists", "procedure_signature_not_found"): (
        "42883",
        "procedure_signature_does_not_exist",
    ),
    ("target_procedure_different_type", "same_name_is_function"): (
        "42809",
        "not_a_procedure_is_function",
    ),
    ("permission_insufficient", "no_alter_privilege"): (
        "42501",
        "must_be_owner_of_procedure",
    ),
    ("permission_insufficient", "not_owner_for_OWNER_TO"): (
        "42501",
        "must_be_owner_of_procedure",
    ),
    ("permission_insufficient", "not_owner_for_SET_SCHEMA"): (
        "42501",
        "must_be_owner_of_procedure",
    ),
    ("conflicting_action", "conflicting_security_modes"): (
        "42601",
        "conflicting_or_redundant_options",
    ),
}


def _expected_failure_details(
    obligation: AlterProcedureFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterProcedureFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: AlterProcedureFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "object_state": "exists",
        "privilege_level": "procedure_owner",
        "procedure_name_shape": "simple",
        "argtype_specification": "with_full_signature",
        "expected_status": "success",
        "verification_mode": "pg_proc_catalog_query",
        "cleanup_mode": "DROP_PROCEDURE_IF_EXISTS",
        # GRM axis baselines (minimal / absent form).
        "restrict_clause": "absent",
        "action_list_cardinality": "one_action",
        "set_assignment_form": "to_value",
        "external_keyword": "omitted",
        "depends_polarity": "depends",
    }
    if branch == "branch_rename":
        assignments["new_name_shape"] = "simple"
    elif branch == "branch_owner":
        assignments["owner_target"] = "new_owner_role"
        assignments["role_dependency"] = "owner_role_exists"
    elif branch == "branch_set_schema":
        assignments["schema_target"] = "schema_exists"
        assignments["schema_dependency"] = "target_schema_exists"
    elif branch == "branch_depends_extension":
        assignments["extension_target"] = "extension_exists"
        assignments["extension_dependency"] = "extension_installed"
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterProcedureFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_procedure_factor_loop_plan(
    repository_root: Path,
) -> AlterProcedureFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_procedure_factor_loop_obligations(root)
    cases: list[AlterProcedureFactorCase] = []
    delegated: list[AlterProcedureFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(obligation)
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            AlterProcedureFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERPROCEDURE{ordinal:05d}",
                sql_filename=f"ALTERPROCEDURE{ordinal:05d}.sql",
                object_prefix=f"alterprocedure_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=_renderer_factor_key(obligation.factor_key),
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = AlterProcedureFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 94 or len(plan.delegated) != 0:
        raise AlterProcedureFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 94:
        raise AlterProcedureFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 94:
        raise AlterProcedureFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_procedure_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterProcedureFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterProcedureFactorObligation(
            ordinal=ordinal,
            obligation_id=row.obligation_id,
            kind=row.kind,
            factor_key=row.factor_key,
            value=row.value,
            consumer_action_id=row.consumer_action_id,
            disposition=row.disposition,
            source_locator=row.source_locator,
            delegated_statement_key=row.delegated_statement_key,
        )
        for ordinal, row in enumerate(unordered_rows, start=1)
    )
    if len(rows) != 94:
        raise AlterProcedureFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterProcedureFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 22, "SFV": 70, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterProcedureFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterProcedureFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 94:
        raise AlterProcedureFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterProcedureFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterProcedureFactorLoopError",
    "AlterProcedureFactorObligation",
    "AlterProcedureFactorCase",
    "AlterProcedureFactorLoopPlan",
    "compile_alter_procedure_factor_loop_obligations",
    "build_alter_procedure_factor_loop_plan",
    "_obligation_multiset_sha256",
]
