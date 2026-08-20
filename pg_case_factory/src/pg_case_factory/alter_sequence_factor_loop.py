"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER SEQUENCE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER SEQUENCE``.  It must not enumerate a table/column cross product:
``alter_sequence.yaml`` marks ``column_type_coverage`` ``not_applicable``,
so there is no ``INV`` block.  Each local obligation will become exactly one
regress program; there are no delegated handoffs because every reachable
negative boundary is a real ``ALTER SEQUENCE`` error that belongs to this
statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_sequence_regress import (
    AlterSequenceRegressError,
    load_alter_sequence_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterSequenceFactorLoopError(ValueError):
    """Raised when a frozen ALTER SEQUENCE obligation input drifts."""


@dataclass(frozen=True)
class AlterSequenceFactorObligation:
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
class AlterSequenceFactorCase:
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
class AlterSequenceFactorLoopPlan:
    obligations: tuple[AlterSequenceFactorObligation, ...]
    cases: tuple[AlterSequenceFactorCase, ...]
    delegated: tuple[AlterSequenceFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches.
_BRANCH_ALTER_PARAMETERS = "branch_alter_parameters"
_BRANCH_SET_LOGGED_UNLOGGED = "branch_set_logged_unlogged"
_BRANCH_OWNER = "branch_owner"
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_SCHEMA = "branch_set_schema"

# A representative action used as the baseline consumer for canonical
# factors that are not bound to one specific sub-clause.
_REPRESENTATIVE_ACTION = "alter_parameters"

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "expected_status": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "alter_parameter_type": _REPRESENTATIVE_ACTION,
    "logged_unlogged_clause": "set_logged_unlogged",
    "role_specification": "owner",
    "sequence_name_shape": _REPRESENTATIVE_ACTION,
    "new_data_type": _REPRESENTATIVE_ACTION,
    "new_owner_shape": "owner",
    "new_schema_name": "set_schema",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "owned_by_table_dependency": _REPRESENTATIVE_ACTION,
    "schema_privilege": "set_schema",
    "owner_change_privilege": "owner",
    "new_owner_schema_privilege": "owner",
    "non_existent_sequence": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "data_type_incompatible_values": _REPRESENTATIVE_ACTION,
    "logged_unlogged_on_temporary": "set_logged_unlogged",
    "owned_by_different_owner": _REPRESENTATIVE_ACTION,
    "owned_by_different_schema": _REPRESENTATIVE_ACTION,
    "restart_value_out_of_range": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_ALTER_PARAMETERS: "alter_parameters",
    _BRANCH_SET_LOGGED_UNLOGGED: "set_logged_unlogged",
    _BRANCH_OWNER: "owner",
    _BRANCH_RENAME: "rename",
    _BRANCH_SET_SCHEMA: "set_schema",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (provisional sqlstates -- DB phase will verify on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("non_existent_sequence", "target_not_exists_no_if_exists"),
        ("insufficient_privilege", "non_owner"),
        ("insufficient_privilege", "cannot_SET_ROLE_to_owner"),
        ("insufficient_privilege", "no_CREATE_on_new_schema"),
        ("data_type_incompatible_values", "values_exceed_new_type_range"),
        ("logged_unlogged_on_temporary", "logged_unlogged_on_temp_illegal"),
        ("owned_by_different_owner", "table_different_owner"),
        ("owned_by_different_schema", "table_different_schema"),
        ("restart_value_out_of_range", "restart_exceeds_bounds"),
        ("privilege_level", "non_owner"),
        ("new_owner_shape", "non_existing_role"),
        ("new_schema_name", "non_existing_schema"),
    }
)


_GRM_SUB_ACTIONS = frozenset(
    {
        "change_increment",
        "change_start",
        "restart_with",
        "change_cycle",
    }
)


def _axis_consumer(action_id: str) -> str:
    """Resolve the baseline action that witnesses an outer/axis modifier.

    All four GRM axes are sub-actions of ``branch_alter_parameters``; their
    sub-action IDs (change_increment, change_start, restart_with,
    change_cycle) map to the branch-level consumer action
    ``alter_parameters`` so they resolve in :func:`_consumer_branch_map`.
    """

    if action_id == "__outer_action__":
        return _REPRESENTATIVE_ACTION
    if action_id in _GRM_SUB_ACTIONS:
        return _REPRESENTATIVE_ACTION
    return action_id


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterSequenceFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterSequenceFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterSequenceFactorObligation]:
    rows: list[AlterSequenceFactorObligation] = []
    for axis in load_alter_sequence_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id == "__outer_action__"
            else f"local:{axis.axis_id}"
        )
        consumer = _axis_consumer(axis.action_id)
        for value in axis.values:
            rows.append(
                AlterSequenceFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"ALTSEQ-GRM|{axis.grammar_branch_id}|"
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
    if len(rows) != 8:
        raise AlterSequenceFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterSequenceFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_sequence")
    if len(catalog_rows) != 69:
        raise AlterSequenceFactorLoopError("canonical obligation count drift")
    rows: list[AlterSequenceFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterSequenceFactorObligation(
                ordinal=0,
                obligation_id=f"ALTERSEQUENCE-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterSequenceFactorObligation]:
    return [
        AlterSequenceFactorObligation(
            ordinal=0,
            obligation_id=f"ALTERSEQUENCE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-altersequence:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterSequenceFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-sequence-factor-obligations-v1\n")
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
        action: branch
        for branch, action in (
            (_BRANCH_ALTER_PARAMETERS, "alter_parameters"),
            (_BRANCH_SET_LOGGED_UNLOGGED, "set_logged_unlogged"),
            (_BRANCH_OWNER, "owner"),
            (_BRANCH_RENAME, "rename"),
            (_BRANCH_SET_SCHEMA, "set_schema"),
        )
    }


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# These will be verified against an isolated 18.4 instance in the DB phase.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "sequence_does_not_exist",
    ),
    ("object_state", "not_exists"): (
        "42P01",
        "sequence_does_not_exist",
    ),
    ("non_existent_sequence", "target_not_exists_no_if_exists"): (
        "42P01",
        "sequence_does_not_exist",
    ),
    ("insufficient_privilege", "non_owner"): (
        "42501",
        "privilege_denied_for_sequence",
    ),
    ("insufficient_privilege", "cannot_SET_ROLE_to_owner"): (
        "42501",
        "privilege_denied_for_role",
    ),
    ("insufficient_privilege", "no_CREATE_on_new_schema"): (
        "42501",
        "privilege_denied_for_schema",
    ),
    ("data_type_incompatible_values", "values_exceed_new_type_range"): (
        "22023",
        "invalid_parameter_value",
    ),
    ("logged_unlogged_on_temporary", "logged_unlogged_on_temp_illegal"): (
        "0A000",
        "feature_not_supported",
    ),
    ("owned_by_different_owner", "table_different_owner"): (
        "42501",
        "owned_by_different_owner",
    ),
    ("owned_by_different_schema", "table_different_schema"): (
        "42501",
        "owned_by_different_schema",
    ),
    ("restart_value_out_of_range", "restart_exceeds_bounds"): (
        "22023",
        "restart_value_out_of_range",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "privilege_denied_for_sequence",
    ),
    ("new_owner_shape", "non_existing_role"): (
        "42704",
        "role_does_not_exist",
    ),
    ("new_schema_name", "non_existing_schema"): (
        "3F000",
        "schema_does_not_exist",
    ),
    # Extension-attributed failures (crossed T4 factor values).
    ("owned_by_table_dependency", "different_owner"): (
        "42501",
        "owned_by_different_owner",
    ),
    ("owned_by_table_dependency", "different_schema"): (
        "42501",
        "owned_by_different_schema",
    ),
    # Sentinel attribution key for the SESSION_USER owner-transfer membership
    # wall.  Under a non-superuser sequence owner, OWNER TO <explicit role>
    # requires SET ROLE membership (PG 18.4: "must be able to SET ROLE");
    # SESSION_USER is a provisional no-op escape (modelled as success here;
    # the DB phase verifies whether it truly escapes 42501 for a sequence
    # owner who is NOT a member of the session user role).
    ("role_specification", "membership_required_under_owner"): (
        "42501",
        "owner_change_requires_membership",
    ),
}


def _expected_failure_details(
    obligation: AlterSequenceFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterSequenceFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


_BRANCH_BASELINE_PARAMETER = {
    _BRANCH_ALTER_PARAMETERS: "change_data_type",
    _BRANCH_SET_LOGGED_UNLOGGED: "LOGGED",
    _BRANCH_OWNER: "new_owner_role",
    _BRANCH_RENAME: "simple",
    _BRANCH_SET_SCHEMA: "existing_schema",
}


def _baseline_assignments(
    obligation: AlterSequenceFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "statement_branch": branch,
        "target_action": obligation.consumer_action_id,
        "object_state": "exists",
        "expected_status": "success",
        "if_exists_clause": "absent",
        "alter_parameter_type": "change_data_type",
        "logged_unlogged_clause": "LOGGED",
        "role_specification": "new_owner_role",
        "sequence_name_shape": "simple",
        "new_data_type": "smallint",
        "new_owner_shape": "existing_role",
        "new_schema_name": "existing_schema",
        "privilege_level": "superuser",
        "owned_by_table_dependency": "same_owner_same_schema",
        "schema_privilege": "has_CREATE",
        "owner_change_privilege": "can_SET_ROLE",
        "new_owner_schema_privilege": "has_CREATE",
        "non_existent_sequence": "target_not_exists_no_if_exists",
        "insufficient_privilege": "non_owner",
        "data_type_incompatible_values": "values_exceed_new_type_range",
        "logged_unlogged_on_temporary": "logged_unlogged_on_temp_illegal",
        "owned_by_different_owner": "table_different_owner",
        "owned_by_different_schema": "table_different_schema",
        "restart_value_out_of_range": "restart_exceeds_bounds",
        "verification_mode": "pg_class_catalog_query",
        "cleanup_mode": "DROP_SEQUENCE",
        # GRM-axis baselines (minimal / absent form).
        "increment_by_keyword": "absent",
        "start_with_keyword": "absent",
        "restart_with_keyword": "absent",
        "cycle_no_keyword": "absent",
    }
    if branch == _BRANCH_RENAME:
        assignments["sequence_name_shape"] = "simple"
    elif branch == _BRANCH_OWNER:
        assignments["role_specification"] = "new_owner_role"
        assignments["new_owner_shape"] = "existing_role"
    elif branch == _BRANCH_SET_SCHEMA:
        assignments["new_schema_name"] = "existing_schema"
    elif branch == _BRANCH_SET_LOGGED_UNLOGGED:
        assignments["logged_unlogged_clause"] = "LOGGED"
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterSequenceFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_sequence_factor_loop_plan(
    repository_root: Path,
) -> AlterSequenceFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_sequence_factor_loop_obligations(root)
    cases: list[AlterSequenceFactorCase] = []
    delegated: list[AlterSequenceFactorObligation] = []
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
            AlterSequenceFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERSEQUENCE{ordinal:05d}",
                sql_filename=f"ALTERSEQUENCE{ordinal:05d}.sql",
                object_prefix=f"altersequence_{ordinal:05d}_",
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
    plan = AlterSequenceFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 79 or len(plan.delegated) != 0:
        raise AlterSequenceFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 79:
        raise AlterSequenceFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 79:
        raise AlterSequenceFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_sequence_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterSequenceFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterSequenceFactorObligation(
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
    if len(rows) != 79:
        raise AlterSequenceFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterSequenceFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 8, "SFV": 69, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterSequenceFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterSequenceFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 79:
        raise AlterSequenceFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterSequenceFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterSequenceFactorLoopError",
    "AlterSequenceFactorObligation",
    "AlterSequenceFactorCase",
    "AlterSequenceFactorLoopPlan",
    "compile_alter_sequence_factor_loop_obligations",
    "build_alter_sequence_factor_loop_plan",
    "_obligation_multiset_sha256",
]
