"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CALL.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CALL``.  CALL is a PostgreSQL DML routine-invocation statement with a
single official synopsis branch: ``CALL name ( [ argument ] [, ...] )``.
It invokes a PROCEDURE object (not a relation), so
``target_relation_coverage`` is ``not_applicable`` and column/table
coverage is representative-by-type-category.  The ``target_relation_state``
factor (exists / missing / wrong_object_type) refers to the CALLed
procedure's existence, not a relation.

Each local obligation becomes exactly one regress program.  Because CALL
is a transactional DML statement (procedures may include transaction
control in allowed invocation contexts) and the inventory declares no
``transaction_outcome`` factor, there are no ``RISK`` obligations.

The grammar ledger is self-contained: the single ``branch_1`` action is
frozen inline.  The 48 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CallFactorLoopError(ValueError):
    """Raised when a frozen CALL obligation input drifts."""


@dataclass(frozen=True)
class CallGrammarAction:
    """One official target action form of the CALL synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CallFactorObligation:
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
class CallFactorCase:
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
class CallFactorLoopPlan:
    obligations: tuple[CallFactorObligation, ...]
    cases: tuple[CallFactorCase, ...]
    delegated: tuple[CallFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-call.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-call"

# The single consumer action for all CALL factors.
_REPRESENTATIVE_ACTION = "call"

# Canonical factor -> the action where the value is observable.  Since
# CALL has only one branch, every factor's consumer is "call".
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "target_relation_state": _REPRESENTATIVE_ACTION,
    "data_or_query_shape": _REPRESENTATIVE_ACTION,
    "condition_shape": _REPRESENTATIVE_ACTION,
    "result_shape": _REPRESENTATIVE_ACTION,
    "with_clause": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "expression_shape": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "constraint_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_relation_state", "missing"),
        ("target_relation_state", "wrong_object_type"),
        ("dependency_state", "missing_dependency"),
        ("privilege_context", "insufficient_privilege"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("constraint_boundary", "constraint_violation"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42883",
        "missing_target_procedure_provisional",
    ),
    ("target_relation_state", "missing"): (
        "42883",
        "missing_target_procedure_provisional",
    ),
    ("target_relation_state", "wrong_object_type"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("dependency_state", "missing_dependency"): (
        "42883",
        "missing_target_procedure_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42883",
        "syntax_valid_semantic_error_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("constraint_boundary", "constraint_violation"): (
        "23000",
        "constraint_violation_or_boundary_error_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CallGrammarAction, ...]:
    """Freeze every CALL synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "call",
            _BRANCH_1,
            "CALL name ( [ argument ] [, ...] )",
            "synopsis-call",
        ),
    )
    actions = [
        CallGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CallFactorLoopError("call action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CallFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CallFactorObligation]:
    rows: list[CallFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CallFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CALL-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise CallFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CallFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("call")
    if len(catalog_rows) != 48:
        raise CallFactorLoopError("canonical obligation count drift")
    rows: list[CallFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CallFactorObligation(
                ordinal=0,
                obligation_id=f"CALL-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _obligation_multiset_sha256(
    rows: tuple[CallFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"call-factor-obligations-v1\n")
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
                    "delegated_statement_key": (
                        row.delegated_statement_key
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Dense baseline defaults (all positive T1-T4 + T6 factor values).
# data_or_query_shape defaults to explicit_values (not minimal) so that
# expression_shape is observable in the CALL argument list.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "expected_status": "success",
    "target_relation_state": "exists",
    "data_or_query_shape": "explicit_values",
    "condition_shape": "none",
    "result_shape": "none",
    "with_clause": "absent",
    "name_shape": "plain_identifier",
    "expression_shape": "literal",
    "dependency_state": "ready",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "constraint_boundary": "none",
    "verification_mode": "effect_query",
    "cleanup_mode": "rollback",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive related factors and ensure baseline self-consistency.

    The T5 negative-axis factors (invalid_combination,
    constraint_boundary) describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value,
    the T1-T4 counterpart is derived.  expected_status=failure is a
    marker that requires a concrete failure cause.
    """

    trs = a.get("target_relation_state", "exists")
    ds = a.get("dependency_state", "ready")
    ic = a.get("invalid_combination", "none")
    es = a.get("expected_status", "success")

    # Missing target cluster: target_relation_state=missing /
    # dependency_state=missing_dependency
    if trs == "missing" or ds == "missing_dependency":
        a["target_relation_state"] = "missing"
        a["dependency_state"] = "missing_dependency"

    # Wrong type cluster: target_relation_state=wrong_object_type /
    # invalid_combination=object_type_mismatch
    if trs == "wrong_object_type" or ic == "object_type_mismatch":
        a["target_relation_state"] = "wrong_object_type"
        a["invalid_combination"] = "object_type_mismatch"

    # expected_status=failure is a marker; it needs a concrete failure
    # cause.  If no concrete failure value is present, default to a
    # missing-target scenario.
    if es == "failure":
        has_concrete = any(
            a.get(f) == v
            for f, v in _SFV_FAILURE_VALUES
            if f != "expected_status"
        )
        if not has_concrete:
            a["target_relation_state"] = "missing"
            a["dependency_state"] = "missing_dependency"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CallFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _BRANCH_1
    assignments["target_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CallFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CallFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CallFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_call_factor_loop_plan(
    repository_root: Path,
) -> CallFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_call_factor_loop_obligations(root)
    cases: list[CallFactorCase] = []
    delegated: list[CallFactorObligation] = []
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
            CallFactorCase(
                ordinal=ordinal,
                case_id=f"CALL{ordinal:05d}",
                sql_filename=f"CALL{ordinal:05d}.sql",
                object_prefix=f"call_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = CallFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 49 or len(plan.delegated) != 0:
        raise CallFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 49:
        raise CallFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 49:
        raise CallFactorLoopError("duplicate SQL filename")
    return plan


def compile_call_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CallFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CallFactorObligation(
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
    if len(rows) != 49:
        raise CallFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CallFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 48}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CallFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CallFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 49:
        raise CallFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CallFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CallFactorLoopError",
    "CallGrammarAction",
    "CallFactorObligation",
    "CallFactorCase",
    "CallFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_call_factor_loop_obligations",
    "build_call_factor_loop_plan",
    "_obligation_multiset_sha256",
]
