"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER INDEX.

This module compiles the marginal factor-value obligation ledger: exactly one
stable local SQL program per non-delegated obligation value.  It deliberately
does NOT enumerate the historical grammar/index/column cross product, and it
does NOT emit the bounded post-coverage extensions (those are a separate,
downstream phase that must not replace required coverage).

The ledger is the required-coverage baseline.  Each obligation carries a
declared compatibility attribution (success / expected-failure / no-op) and
the expected sqlstate bound to its failure reason.  The downstream PG18.4
serial two-run calibration verifies and refines these sqlstates against the
live catalog.
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


def compile_alter_index_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterIndexFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order.

    Two obligation kinds mirror the proven taxonomy:

    * ``GRM`` — the grammar action skeleton: one obligation per branch action,
      witnessing that branch's ``statement_branch`` value (9 total, one per
      ALTER INDEX branch).
    * ``SFV`` — a single factor-value obligation: one per (action, axis,
      value), witnessing each declared expansion value for that branch's
      factors (763 total).

    There are no ``INV`` obligations (ALTER INDEX column-type coverage is
    ``conditional`` with representative types, owned by CREATE INDEX) and no
    ``RISK`` obligations (T5 negative controls are realized as expected-failure
    SFV values, not a separate risk section).
    """
    actions = load_alter_index_grammar_actions(repository_root)
    axes_by_action = _axes_by_action(repository_root)
    unordered_rows: list[AlterIndexFactorObligation] = []
    for action in actions:
        unordered_rows.append(
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
        for axis_id, values in axes_by_action.get(action.action_id, {}).items():
            for value in values:
                unordered_rows.append(
                    AlterIndexFactorObligation(
                        ordinal=0,
                        obligation_id=(
                            f"AI-SFV|{action.group_id}|{action.action_id}|"
                            f"{axis_id}|{value}"
                        ),
                        kind="SFV",
                        factor_key=axis_id,
                        value=value,
                        consumer_action_id=action.action_id,
                        disposition="covered",
                        source_locator=f"{action.source_locator}#{axis_id}",
                    )
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
    expected_count = 772
    if len(rows) != expected_count:
        raise AlterIndexFactorLoopError(
            f"obligation count drift: {len(rows)} != {expected_count}"
        )
    expected_kind_counts = {"GRM": 21, "SFV": 751}
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
        action = actions.get(obligation.consumer_action_id)
        if action is None:
            raise AlterIndexFactorLoopError(
                f"obligation {obligation.obligation_id} has no action"
            )
        axes_for_action = axes_by_action.get(action.action_id, {})
        bindings = dict(_baseline_assignments(action, axes_for_action, obligation))
        disposition, sqlstate, failure_reason = _resolve_disposition(
            action, bindings
        )
        if disposition == "delegated":
            delegated.append(obligation)
            continue
        if disposition == "expected_failure":
            outcome = "expected_failure"
        elif disposition == "no_op":
            outcome = "no_op"
        else:
            outcome = "success"
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
                baseline_assignments=tuple(bindings.items()),
                execution_profile="same_session_multiphase",
            )
        )
    obligation_multiset = _obligation_multiset_sha256(tuple(obligations))
    return AlterIndexFactorLoopPlan(
        obligations=tuple(obligations),
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=obligation_multiset,
    )


__all__ = [
    "AlterIndexFactorLoopError",
    "AlterIndexFactorObligation",
    "AlterIndexFactorCase",
    "AlterIndexFactorLoopPlan",
    "compile_alter_index_factor_loop_obligations",
    "build_alter_index_factor_loop_plan",
]
