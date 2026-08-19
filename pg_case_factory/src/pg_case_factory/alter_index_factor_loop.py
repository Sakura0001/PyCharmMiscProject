"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER INDEX.

This module compiles the marginal GRM/SFV obligation ledger for
``ALTER INDEX``.  The marginal baseline is the *required coverage*: exactly
one stable local SQL program per canonical factor value, derived 1:1 from the
shipped applicability matrix so that the shared conservation contract
(``f"|{row_id}|" in obligation.obligation_id``) credits every matrix row
exactly once.  This mirrors the proven
:mod:`alter_function_factor_loop` convention.

The ledger deliberately does NOT enumerate the historical
grammar/index/column cross product in the baseline (that bounded cross-factor
work is owned by the downstream :mod:`alter_index_factor_extension` phase).
GRM obligations witness the grammar action skeletons (one per compiled branch
action); they are additional to the matrix-1:1 SFV obligations and are not
matrix-credited (they carry no ``row_id``).

Each obligation carries a declared compatibility attribution
(success / expected-failure) and the expected sqlstate bound to its failure
reason.  The downstream PG18.4 serial two-run calibration verifies and refines
these sqlstates against the live catalog.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .alter_index_regress import (
    EXPECTED_SQLSTATE_BY_REASON,
    AlterIndexGrammarAction,
    evaluate_condition,
    load_alter_index_grammar_actions,
    load_alter_index_grammar_axes,
    load_alter_index_type_witnesses,
)
from .applicability import load_shipped_applicability_universe


class AlterIndexFactorLoopError(ValueError):
    """Raised when a frozen ALTER INDEX obligation input drifts."""


@dataclass(frozen=True)
class AlterIndexFactorObligation:
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
class AlterIndexFactorCase:
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
class AlterIndexFactorLoopPlan:
    obligations: tuple[AlterIndexFactorObligation, ...]
    cases: tuple[AlterIndexFactorCase, ...]
    delegated: tuple[AlterIndexFactorObligation, ...]
    obligation_multiset_sha256: str


# A representative success branch used as the witnessing consumer for factors
# that are not bound to one sub-clause (meta / ownership / verification axes).
_REPRESENTATIVE_ACTION = "rename"

# Canonical factor -> the statement_branch action where the value is
# observable.  ``statement_branch`` is value-resolved (each branch witnesses
# itself); ``invalid_combination`` is value-resolved because each declared
# invalid boundary belongs to a specific branch's failure contract.
_FACTOR_ACTION_CONSUMER = {
    "storage_parameter_set": "set_storage",
    "storage_parameter_reset": "reset_storage",
    "statistics_value": "set_statistics",
    "column_number_value": "set_statistics",
    "column_keyword": "set_statistics",
    "index_method": "set_storage",
    "syntax_error": "set_storage",
    "expected_status": "set_storage",
    "name_shape": "rename",
    "object_state": "rename",
    "if_exists": "rename",
    "no_keyword": "depends_on_extension",
    "nowait": "all_in_tablespace",
    "permission_boundary": "all_in_tablespace",
    "owned_by": "all_in_tablespace",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_INVALID_COMBINATION_CONSUMER = {
    "already_attached_partition_parent_invalid": "attach_partition",
    "attach_partition_definition_mismatch": "attach_partition",
    "nonexistent_index_no_if_exists": "rename",
    "statistics_column_out_of_range": "set_statistics",
    "system_catalog_index": "set_storage",
    "none": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and are
# rejected (attribution curated from the combination matrix failure_when
# contract; sqlstates are verified/refined by the downstream PG18.4 double-run).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "22023",
        "alter_index_negative_boundary",
    ),
    ("object_state", "not_exists"): ("42P01", "relation_does_not_exist"),
    ("syntax_error", "invalid_syntax"): (
        "42601",
        "alter_index_syntax_is_invalid",
    ),
    ("invalid_combination", "already_attached_partition_parent_invalid"): (
        "0A000",
        "pg18_revalidate_attached_parent_reference_failure",
    ),
    ("invalid_combination", "attach_partition_definition_mismatch"): (
        "42P17",
        "partition_index_definition_mismatch",
    ),
    ("invalid_combination", "nonexistent_index_no_if_exists"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("invalid_combination", "statistics_column_out_of_range"): (
        "42703",
        "index_column_out_of_range",
    ),
    ("invalid_combination", "system_catalog_index"): (
        "42501",
        "cannot_alter_system_catalog_index",
    ),
    ("permission_boundary", "non_owner"): ("42501", "must_own_index"),
    ("permission_boundary", "insufficient_tablespace_privilege"): (
        "42501",
        "tablespace_permission_denied",
    ),
    ("column_number_value", "zero"): (
        "22023",
        "index_column_zero",
    ),
    ("column_number_value", "out_of_range"): (
        "42703",
        "index_column_out_of_range",
    ),
    ("statistics_value", "out_of_range"): (
        "22023",
        "invalid_statistics_target",
    ),
    ("name_shape", "missing_object"): ("42P01", "relation_does_not_exist"),
}

_SFV_FAILURE_VALUES = frozenset(_SFV_FAILURE_SQLSTATE.keys())


def _canonical_consumer(row) -> str:
    """Resolve the statement_branch action that witnesses a matrix factor value.

    ``statement_branch`` values witness themselves.  ``invalid_combination``
    values are dispatched to the branch whose failure contract owns that
    boundary.  Every other factor maps to its declared observing branch.
    """

    if row.factor == "statement_branch":
        return str(row.value)
    if row.factor == "invalid_combination":
        try:
            return _INVALID_COMBINATION_CONSUMER[str(row.value)]
        except KeyError as exc:
            raise AlterIndexFactorLoopError(
                f"unknown invalid_combination value: {row.value}"
            ) from exc
    try:
        return _FACTOR_ACTION_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterIndexFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _expected_failure_details(
    obligation: AlterIndexFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterIndexFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _action_index(
    actions: tuple[AlterIndexGrammarAction, ...],
) -> dict[str, AlterIndexGrammarAction]:
    by_id: dict[str, AlterIndexGrammarAction] = {}
    for action in actions:
        by_id.setdefault(action.action_id, action)
    return by_id


def _axes_by_action(
    repository_root: Path,
) -> dict[str, dict[str, tuple[str, ...]]]:
    axes = load_alter_index_grammar_axes(repository_root)
    grouped: dict[str, dict[str, tuple[str, ...]]] = {}
    for axis in axes:
        grouped.setdefault(axis.action_id, {})[axis.axis_id] = axis.values
    return grouped


def _baseline_assignments(
    action: AlterIndexGrammarAction,
    axes_for_action: dict[str, tuple[str, ...]],
    obligation: AlterIndexFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """Baseline factor bindings for one obligation.

    The baseline is the group's declared success bindings, augmented with the
    first value of every expansion axis that the group does not pin in its
    baseline ``factors`` block.  The obligation's own factor is then overlaid
    with its varied value so that exactly one axis differs from the baseline.
    The tuple is sorted by factor key for a deterministic, cross-statement
    uniform baseline shape.
    """
    assignments: dict[str, str] = dict(action.baseline_factors)
    assignments["statement_branch"] = action.action_id
    for axis_id, values in axes_for_action.items():
        if axis_id not in assignments and values:
            assignments[axis_id] = values[0]
    assignments[obligation.factor_key] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterIndexFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _resolve_disposition(
    action: AlterIndexGrammarAction,
    bindings: dict[str, str],
) -> tuple[str, str, str | None]:
    """Return (disposition, sqlstate, failure_reason) for one obligation.

    The declared ``failure_when`` conditions are evaluated against the
    obligation's bindings; the first matching rule attributes the failure.
    Absent a match, the group's declared default expected status decides.
    """
    for condition, reason in action.failure_when:
        verdict = evaluate_condition(condition, bindings)
        if verdict is True:
            sqlstate = EXPECTED_SQLSTATE_BY_REASON.get(reason, "42601")
            return ("expected_failure", sqlstate, reason)
    status = action.default_expected_status
    if status == "failure":
        reason = action.default_failure_reason
        sqlstate = EXPECTED_SQLSTATE_BY_REASON.get(reason, "42601")
        return ("expected_failure", sqlstate, reason or "alter_index_failure")
    if status == "no_op":
        return ("no_op", "00000", None)
    return ("covered", "00000", None)


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterIndexFactorObligation]:
    """Compile the 66 matrix-1:1 SFV obligations (required coverage baseline).

    Exactly one SFV obligation per canonical matrix factor value, embedding the
    matrix ``row_id`` so the shared conservation contract credits each row
    exactly once.  Mirrors ``alter_function_factor_loop._compile_canonical``.
    """
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_index")
    if len(catalog_rows) != 66:
        raise AlterIndexFactorLoopError("canonical obligation count drift")
    rows: list[AlterIndexFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        disposition = (
            "expected_failure"
            if (row.factor, row.value) in _SFV_FAILURE_VALUES
            else "covered"
        )
        rows.append(
            AlterIndexFactorObligation(
                ordinal=0,
                obligation_id=f"AI-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=disposition,
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _compile_grammar_obligations(
    repository_root: Path,
) -> list[AlterIndexFactorObligation]:
    """Compile the GRM action-skeleton obligations (one per branch action).

    These are additional to the matrix-1:1 SFV baseline; they carry no
    ``row_id`` (they are not matrix-credited) and witness each compiled grammar
    action's statement_branch skeleton.
    """
    actions = load_alter_index_grammar_actions(repository_root)
    rows: list[AlterIndexFactorObligation] = []
    for action in actions:
        rows.append(
            AlterIndexFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AI-GRM|{action.group_id}|{action.action_id}|"
                    f"statement_branch|{action.action_id}"
                ),
                kind="GRM",
                factor_key="statement_branch",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    return rows


def compile_alter_index_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterIndexFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order.

    Two obligation kinds mirror the proven taxonomy:

    * ``SFV`` — a single factor-value obligation: one per canonical matrix factor
      value, derived 1:1 from the applicability matrix and embedding the matrix
      ``row_id`` (66 total) so the shared conservation contract credits each row
      exactly once.
    * ``GRM`` — the grammar action skeleton: one obligation per compiled branch
      action (21 total), additional to the SFV baseline and not matrix-credited.

    There are no ``INV`` obligations (ALTER INDEX column-type coverage is
    ``conditional`` with representative types, owned by CREATE INDEX) and no
    ``RISK`` obligations (T5 negative controls are realized as expected-failure
    SFV values, not a separate risk section).
    """
    root = Path(repository_root).resolve(strict=True)
    unordered_rows: list[AlterIndexFactorObligation] = (
        _compile_canonical_obligations(root)
        + _compile_grammar_obligations(root)
    )
    rows = tuple(
        AlterIndexFactorObligation(
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
    _assert_frozen_ledger(rows)
    return rows


def _assert_frozen_ledger(
    rows: tuple[AlterIndexFactorObligation, ...],
) -> None:
    """Fail fast at build time if the frozen obligation ledger drifts."""
    expected_count = 87
    if len(rows) != expected_count:
        raise AlterIndexFactorLoopError(
            f"obligation count drift: {len(rows)} != {expected_count}"
        )
    expected_kind_counts = {"GRM": 21, "SFV": 66}
    if Counter(r.kind for r in rows) != expected_kind_counts:
        raise AlterIndexFactorLoopError(
            f"obligation kind count drift: "
            f"{Counter(r.kind for r in rows)} != {expected_kind_counts}"
        )
    if len({r.obligation_id for r in rows}) != len(rows):
        raise AlterIndexFactorLoopError("duplicate obligation id")
    if sum(r.disposition == "delegated" for r in rows) != 0:
        raise AlterIndexFactorLoopError("delegated obligation count drift")
    local = sum(r.disposition in {"covered", "expected_failure"} for r in rows)
    if local != expected_count:
        raise AlterIndexFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(r.disposition not in allowed_dispositions for r in rows):
        raise AlterIndexFactorLoopError("unknown obligation disposition")
    if sum(r.disposition == "expected_failure" for r in rows) != 14:
        raise AlterIndexFactorLoopError(
            "expected-failure count drift"
        )


def _obligation_multiset_sha256(
    obligations: tuple[AlterIndexFactorObligation, ...],
) -> str:
    """Deterministic multiset hash of the obligation ledger."""
    counter = Counter(
        (o.obligation_id, o.kind, o.factor_key, o.value) for o in obligations
    )
    payload = "\n".join(
        f"{key[0]}|{key[1]}|{key[2]}|{key[3]}|{count}"
        for key, count in sorted(counter.items())
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_alter_index_factor_loop_plan(
    repository_root: Path,
) -> AlterIndexFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""
    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_index_factor_loop_obligations(root)
    actions = _action_index(load_alter_index_grammar_actions(root))
    axes_by_action = _axes_by_action(root)
    # Touch the type witnesses so the representative-type contract is loaded
    # and any drift in the combination matrix surfaces at plan-build time.
    load_alter_index_type_witnesses(root)

    cases: list[AlterIndexFactorCase] = []
    delegated: list[AlterIndexFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        action = actions.get(obligation.consumer_action_id)
        if action is None:
            raise AlterIndexFactorLoopError(
                f"obligation {obligation.obligation_id} has no action"
            )
        axes_for_action = axes_by_action.get(action.action_id, {})
        bindings = _baseline_assignments(action, axes_for_action, obligation)
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(obligation)
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        ordinal = len(cases) + 1
        cases.append(
            AlterIndexFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERINDEX{ordinal:05d}",
                sql_filename=f"ALTERINDEX{ordinal:05d}.sql",
                object_prefix=f"alterindex_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=tuple(bindings),
                execution_profile="same_session_multiphase",
            )
        )
    obligation_multiset = _obligation_multiset_sha256(tuple(obligations))
    plan = AlterIndexFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=obligation_multiset,
    )
    if len(plan.cases) != 87 or len(plan.delegated) != 0:
        raise AlterIndexFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 87:
        raise AlterIndexFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 87:
        raise AlterIndexFactorLoopError("duplicate SQL filename")
    return plan


__all__ = [
    "AlterIndexFactorLoopError",
    "AlterIndexFactorObligation",
    "AlterIndexFactorCase",
    "AlterIndexFactorLoopPlan",
    "compile_alter_index_factor_loop_obligations",
    "build_alter_index_factor_loop_plan",
]
