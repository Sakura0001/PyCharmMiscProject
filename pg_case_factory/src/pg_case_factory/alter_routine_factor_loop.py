"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER ROUTINE.

This module compiles the marginal ``GRM``/``SFV``/``RISK`` obligation ledger
for ``ALTER ROUTINE``.  ``ALTER ROUTINE`` is the generic routine wrapper: it
resolves to ``ALTER FUNCTION`` / ``ALTER PROCEDURE`` / ``ALTER AGGREGATE``
depending on the target object kind.  ``alter_routine.yaml`` marks
column/table/relation coverage ``not_applicable``, so there is no ``INV``
block.  Each local obligation becomes exactly one regress program; there are
no delegated handoffs because every reachable negative boundary is a real
``ALTER ROUTINE`` error that belongs to this statement.

The 20 grammar actions (16 ``branch_action`` actions + 4 outer-branch
operations) and the 6 grammar axes are frozen in
:mod:`pg_case_factory.alter_routine_regress`; they are the GRM input here.
The 80 canonical ``SFV`` rows come from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``), embedded 1:1 via
``rows_for_statement("alter_routine")`` so the matrix-1:1 baseline holds (the
``alter_index`` anti-pattern of deriving obligations from a grammar
cross-product is avoided).

Provisional SQLSTATEs (tagged ``_provisional`` in the failure reason) are
verified against an isolated PG 18.4 instance in the DB phase; the no-DB
ledger freezes a starting point the DB fork calibrates.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_routine_regress import (
    AlterRoutineRegressError,
    load_alter_routine_grammar_actions,
    load_alter_routine_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterRoutineFactorLoopError(ValueError):
    """Raised when a frozen ALTER ROUTINE obligation input drifts."""


@dataclass(frozen=True)
class AlterRoutineFactorObligation:
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
class AlterRoutineFactorCase:
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
class AlterRoutineFactorLoopPlan:
    obligations: tuple[AlterRoutineFactorObligation, ...]
    cases: tuple[AlterRoutineFactorCase, ...]
    delegated: tuple[AlterRoutineFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches.
_BRANCH_ACTION_FORM = "branch_action_form"

# A representative branch_action action used as the baseline consumer for
# factors whose consumer does not depend on the value.  VOLATILE is
# function-applicable (the baseline routine_type is function).
_REPRESENTATIVE_ACTION = "volatile"

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, action_option,
# privilege_insufficient) are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "routine_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "routine_type": _REPRESENTATIVE_ACTION,
    "restrict_clause": _REPRESENTATIVE_ACTION,
    "owner_to_shape": "owner",
    "schema_change": "set_schema",
    "extension_dependency": "depends_on_extension",
    "routine_name_shape": _REPRESENTATIVE_ACTION,
    "arg_signature": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "new_schema_shape": "set_schema",
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "extension_dependency_state": "depends_on_extension",
    "nonexistent_routine": _REPRESENTATIVE_ACTION,
    "nonexistent_schema": "set_schema",
    "nonexistent_extension": "depends_on_extension",
    "nonexistent_owner": "owner",
    "conflicting_routine_signature": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER = {
    "branch_action": _REPRESENTATIVE_ACTION,
    "branch_rename": "rename",
    "branch_owner_to": "owner",
    "branch_set_schema": "set_schema",
    "branch_depends_on_extension": "depends_on_extension",
}

# privilege_insufficient canonical value -> the branch action it lives in.
# non_superuser_setting_security_definer is a SUCCESS path (SECURITY DEFINER is
# owner-settable, NOT superuser-only) so it is covered, not expected_failure.
_PRIVILEGE_INSUFFICIENT_CONSUMER = {
    "non_owner_altering_routine": _REPRESENTATIVE_ACTION,
    "non_superuser_setting_leakproof": "leakproof",
    "non_superuser_setting_security_definer": "security_definer",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected.  Provisional SQLSTATEs are mapped in ``_SFV_FAILURE_SQLSTATE``
# below and verified in the DB phase.  The ``non_superuser_setting_security_
# definer`` value is deliberately ABSENT: SECURITY DEFINER is owner-settable
# in PG 18.4 (not superuser-only), so it is a SUCCESS path, not 42501.  The DB
# phase decides definitively; if it is a failure, it is re-added here.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("routine_state", "non_existent"),
        ("routine_state", "exists_as_procedure"),
        ("routine_state", "exists_as_aggregate"),
        ("routine_name_shape", "non_existent_name"),
        ("arg_signature", "mismatched_signature"),
        ("schema_change", "nonexistent_schema"),
        ("new_schema_shape", "nonexistent_schema"),
        ("extension_dependency", "depends_on_nonexistent_extension"),
        ("extension_dependency_state", "extension_not_exists"),
        ("nonexistent_routine", "routine_does_not_exist"),
        ("nonexistent_schema", "schema_does_not_exist"),
        ("nonexistent_extension", "extension_does_not_exist"),
        ("nonexistent_owner", "owner_role_does_not_exist"),
        ("new_name_shape", "existing_name_conflict"),
        ("executor_privilege", "non_owner_no_privilege"),
        # A non-owner granted EXECUTE (the only grantable routine privilege)
        # still cannot ALTER ROUTINE: only the owner can.  Probed on PG 18.4
        # for functions (GRANT ALTER ON FUNCTION is not valid syntax).
        ("executor_privilege", "non_owner_with_grant_option"),
        ("privilege_insufficient", "non_owner_altering_routine"),
        ("privilege_insufficient", "non_superuser_setting_leakproof"),
        ("conflicting_routine_signature", "wrong_argument_types"),
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
            raise AlterRoutineFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "action_option":
        # action_option values are lowercase grammar action ids == consumer.
        return row.value
    if row.factor == "privilege_insufficient":
        try:
            return _PRIVILEGE_INSUFFICIENT_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterRoutineFactorLoopError(
                f"unknown privilege_insufficient value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterRoutineFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterRoutineFactorObligation]:
    rows: list[AlterRoutineFactorObligation] = []
    for action in load_alter_routine_grammar_actions():
        rows.append(
            AlterRoutineFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ALTERROUTINE-GRM|{action.grammar_branch_id}|"
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
    for axis in load_alter_routine_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id == "__outer_action__"
            else f"local:{axis.axis_id}"
        )
        consumer = _axis_consumer(axis.action_id)
        for value in axis.values:
            rows.append(
                AlterRoutineFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"ALTERROUTINE-GRM|{axis.grammar_branch_id}|"
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
    if len(rows) != 33:
        raise AlterRoutineFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterRoutineFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_routine")
    if len(catalog_rows) != 80:
        raise AlterRoutineFactorLoopError("canonical obligation count drift")
    rows: list[AlterRoutineFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterRoutineFactorObligation(
                ordinal=0,
                obligation_id=f"ALTERROUTINE-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterRoutineFactorObligation]:
    return [
        AlterRoutineFactorObligation(
            ordinal=0,
            obligation_id=f"ALTERROUTINE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterroutine:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterRoutineFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-routine-factor-obligations-v1\n")
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
        for action in load_alter_routine_grammar_actions()
    }


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# These are verified against an isolated 18.4 instance in the DB phase (the
# no-DB ledger freezes a starting point the DB fork calibrates).  Sentinel
# attribution keys (not real crossed-axis (factor, value)) for the two
# privilege walls that fire only under a non-superuser routine owner are
# included: LEAKPROOF requires superuser, and OWNER TO <role> requires the
# issuer to be a member of that role.  SESSION_USER membership is
# routine-type-aware (see alter_routine_factor_extension).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42883",
        "expected_status_failure_routine_not_found_provisional",
    ),
    ("routine_state", "non_existent"): (
        "42883",
        "routine_does_not_exist_provisional",
    ),
    ("routine_state", "exists_as_procedure"): (
        "42809",
        "wrong_object_type_is_procedure_provisional",
    ),
    ("routine_state", "exists_as_aggregate"): (
        "42809",
        "wrong_object_type_is_aggregate_provisional",
    ),
    ("routine_name_shape", "non_existent_name"): (
        "42883",
        "routine_does_not_exist_provisional",
    ),
    ("arg_signature", "mismatched_signature"): (
        "42883",
        "routine_signature_does_not_exist_provisional",
    ),
    ("schema_change", "nonexistent_schema"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("new_schema_shape", "nonexistent_schema"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("extension_dependency", "depends_on_nonexistent_extension"): (
        "42704",
        "extension_does_not_exist_provisional",
    ),
    ("extension_dependency_state", "extension_not_exists"): (
        "42704",
        "extension_does_not_exist_provisional",
    ),
    ("nonexistent_routine", "routine_does_not_exist"): (
        "42883",
        "routine_does_not_exist_provisional",
    ),
    ("nonexistent_schema", "schema_does_not_exist"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("nonexistent_extension", "extension_does_not_exist"): (
        "42704",
        "extension_does_not_exist_provisional",
    ),
    ("nonexistent_owner", "owner_role_does_not_exist"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("new_name_shape", "existing_name_conflict"): (
        "42723",
        "duplicate_function_provisional",
    ),
    ("executor_privilege", "non_owner_no_privilege"): (
        "42501",
        "must_be_owner_of_routine_provisional",
    ),
    ("executor_privilege", "non_owner_with_grant_option"): (
        "42501",
        "must_be_owner_of_routine_provisional",
    ),
    # Sentinel: LEAKPROOF under a non-superuser routine owner surfaces 42501
    # before the action takes effect (LEAKPROOF is superuser-only).
    ("target_action", "leakproof_under_routine_owner"): (
        "42501",
        "leakproof_requires_superuser_provisional",
    ),
    # Sentinel: OWNER TO <role> under a non-superuser routine owner requires
    # the issuer to be a member of that role; SESSION_USER membership is
    # routine-type-aware (see alter_routine_factor_extension).
    ("owner_to_shape", "membership_required_under_routine_owner"): (
        "42501",
        "owner_change_requires_role_membership_provisional",
    ),
    ("privilege_insufficient", "non_owner_altering_routine"): (
        "42501",
        "must_be_owner_of_routine_provisional",
    ),
    ("privilege_insufficient", "non_superuser_setting_leakproof"): (
        "42501",
        "leakproof_requires_superuser_provisional",
    ),
    ("conflicting_routine_signature", "wrong_argument_types"): (
        "42883",
        "routine_signature_does_not_exist_provisional",
    ),
}


def _expected_failure_details(
    obligation: AlterRoutineFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterRoutineFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


_BASELINE_DEFAULTS: dict[str, str] = {
    "routine_state": "exists",
    "expected_status": "success",
    "routine_type": "function",
    "action_option": _REPRESENTATIVE_ACTION,
    "restrict_clause": "omitted",
    "owner_to_shape": "explicit_role_name",
    "schema_change": "existing_schema",
    "extension_dependency": "depends_on_existing_extension",
    "routine_name_shape": "simple_name",
    "arg_signature": "no_args",
    "new_name_shape": "simple_name",
    "new_schema_shape": "existing_schema",
    "executor_privilege": "superuser",
    "extension_dependency_state": "extension_exists",
    "nonexistent_routine": "routine_does_not_exist",
    "nonexistent_schema": "schema_does_not_exist",
    "nonexistent_extension": "extension_does_not_exist",
    "nonexistent_owner": "owner_role_does_not_exist",
    "conflicting_routine_signature": "wrong_argument_types",
    "verification_mode": "pg_proc_catalog",
    "cleanup_mode": "drop_routine",
    # GRM axis baselines (minimal / absent form).
    "set_assignment_form": "to_value",
    "external_keyword": "omitted",
    "depends_polarity": "depends",
    "action_list_cardinality": "one_action",
}


def _branch_defaults(action: str) -> dict[str, str]:
    """Branch-specific canonical defaults beyond the shared baseline."""

    branch = _consumer_branch_map()[action]
    extras: dict[str, str] = {"grammar_branch": branch, "target_action": action}
    if branch == _BRANCH_ACTION_FORM:
        # branch_action: the action_option axis carries the action value.
        extras["action_option"] = action
    elif branch == "branch_rename":
        pass
    elif branch == "branch_owner":
        pass
    elif branch == "branch_set_schema":
        pass
    elif branch == "branch_depends_extension":
        pass
    return extras


def _baseline_assignments(
    obligation: AlterRoutineFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    action = obligation.consumer_action_id
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments.update(_branch_defaults(action))
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    # (expected_status, failure) is a meta flag with no concrete cause of its
    # own; give it the documented default failure cause (routine not found) so
    # the rendered target actually fails (42883).
    if (
        obligation.factor_key == "expected_status"
        and obligation.value == "failure"
    ):
        assignments["routine_state"] = "non_existent"
    if len(assignments) != len(set(assignments)):
        raise AlterRoutineFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_routine_factor_loop_plan(
    repository_root: Path,
) -> AlterRoutineFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_routine_factor_loop_obligations(root)
    cases: list[AlterRoutineFactorCase] = []
    delegated: list[AlterRoutineFactorObligation] = []
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
            AlterRoutineFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERROUTINE{ordinal:05d}",
                sql_filename=f"ALTERROUTINE{ordinal:05d}.sql",
                object_prefix=f"alterroutine_{ordinal:05d}_",
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
    plan = AlterRoutineFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 115 or len(plan.delegated) != 0:
        raise AlterRoutineFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 115:
        raise AlterRoutineFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 115:
        raise AlterRoutineFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_routine_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterRoutineFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterRoutineFactorObligation(
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
    if len(rows) != 115:
        raise AlterRoutineFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterRoutineFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 33, "SFV": 80, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterRoutineFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterRoutineFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 115:
        raise AlterRoutineFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterRoutineFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterRoutineFactorLoopError",
    "AlterRoutineFactorObligation",
    "AlterRoutineFactorCase",
    "AlterRoutineFactorLoopPlan",
    "compile_alter_routine_factor_loop_obligations",
    "build_alter_routine_factor_loop_plan",
    "_obligation_multiset_sha256",
]
