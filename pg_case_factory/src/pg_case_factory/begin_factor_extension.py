"""Bounded post-coverage cross-factor extension expander for BEGIN.

The marginal factor-value-loop (:mod:`begin_factor_loop`) is the required
baseline: one program per factor value, 44 local cases (GRM 1 + SFV 43).
This module adds the bounded post-coverage extension phase allowed by
``begin.yaml`` ``post_coverage_extension_policy.enabled: true``:
cross-factor combinations of the positive T1-T2 behaviour axes across
the single BEGIN synopsis branch, with at most one failure-causing value
per case so attribution stays clean, and ``verification_mode`` crossed so
every declared T6 value is exercised.

BEGIN is a TCL transaction-control statement with one synopsis branch.
The T5 factors (invalid_combination, state_boundary) are derived from
their T1-T2 counterparts, not crossed as axes.  The T3/T4 rotate-attach
factors (transaction_id_shape, savepoint_name_shape, environment_context)
are covered in the baseline and set to defaults in the extension.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``post_coverage_extension_policy.required_fields``) and is marked
``is_extension``.  Filtering happens BEFORE counting (``raw += 1``), so
``raw_combination_count == len(cases)`` and ``dropped_count == 0``
(no over-pruning).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .begin_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_begin_factor_loop_plan,
)


class BeginFactorExtensionError(ValueError):
    """Raised when a frozen BEGIN extension input drifts."""


@dataclass(frozen=True)
class BeginFactorExtensionCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    derivation_id: str
    derived_from_combination_group: str
    derivation_reason: str
    factor_assignment: tuple[tuple[str, str], ...]
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    is_extension: bool


@dataclass(frozen=True)
class BeginFactorExtensionPlan:
    cases: tuple[BeginFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 44
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "effect_query",
    "returned_rows",
    "error_assertion",
)
_CLEANUP_MODES = (
    "rollback",
    "drop_objects",
    "reset_state",
)

# General axes crossed for the single BEGIN branch.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "transaction_state": (
        "outside_transaction",
        "inside_transaction",
        "savepoint_exists",
        "prepared_transaction_exists",
        "missing_required_state",
    ),
    "transaction_mode": (
        "default",
        "isolation_level",
        "read_write",
        "read_only",
        "deferrable",
    ),
    "chain_behavior": (
        "none",
        "and_chain",
        "and_no_chain",
    ),
    "framework_context": (
        "no_outer_transaction",
        "outer_transaction_present",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action are overridden per branch.
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "target_action": "begin_transaction",
    "expected_status": "success",
    "transaction_state": "outside_transaction",
    "transaction_mode": "default",
    "chain_behavior": "none",
    "transaction_id_shape": "simple_id",
    "savepoint_name_shape": "simple_name",
    "environment_context": "normal_session",
    "framework_context": "no_outer_transaction",
    "invalid_combination": "none",
    "state_boundary": "no_open_transaction",
    "verification_mode": "catalog_query",
    "cleanup_mode": "rollback",
}

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T5 values are NOT listed here
# (they are derived in :func:`_derive_overlapping_factors`) so counting
# both would double-count a single failure and break at-most-one
# attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("transaction_state", "missing_required_state"),
        ("chain_behavior", "and_chain"),
        ("chain_behavior", "and_no_chain"),
    }
)


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return sum(
        1
        for factor, value in _CROSSED_NEGATIVES
        if assignment.get(factor) == value
    )


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    return _failure_unit_count(assignment) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    cb = a.get("chain_behavior", "none")
    ts = a.get("transaction_state", "outside_transaction")

    if cb in ("and_chain", "and_no_chain"):
        a["invalid_combination"] = "syntax_valid_semantic_error"
    else:
        a["invalid_combination"] = "none"

    if ts == "prepared_transaction_exists":
        a["state_boundary"] = "prepared_transaction_leftover"
    elif ts in ("inside_transaction", "savepoint_exists"):
        a["state_boundary"] = "nested_savepoint"
    elif ts == "missing_required_state":
        a["state_boundary"] = "no_open_transaction"
    else:
        a["state_boundary"] = "no_open_transaction"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    names = list(_GENERAL_AXES)
    for values in itertools.product(
        *[_GENERAL_AXES[n] for n in names]
    ):
        assignment: dict[str, str] = dict(_BASELINE)
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_overlapping_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise BeginFactorExtensionError(
                "duplicate factor key in extension assignment"
            )
        combos.append(assignment)
    return combos


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[BeginFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"begin-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(
                        case.factor_assignment
                    ),
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": (
                        case.expected_failure_reason
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _derived_combinations_yaml(
    cases: tuple[BeginFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"BEGIN extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": (
                        "begin_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "BEGIN",
                    "primary_fence": (
                        "primary-target-begin/end"
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment[
                        "verification_mode"
                    ],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment["cleanup_mode"],
                },
            }
        )
    return yaml.safe_dump(
        entries, sort_keys=False, allow_unicode=True
    )


def build_begin_factor_extension_plan(
    repository_root: Path,
) -> BeginFactorExtensionPlan:
    """Build the bounded BEGIN post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_begin_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[BeginFactorExtensionCase] = []
    ordinal = _BASELINE_COUNT
    raw = 0
    for behavior in behaviors:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                if len(cases) >= _CAP:
                    continue
                assignment: dict[str, str] = dict(behavior)
                assignment["verification_mode"] = verification
                assignment["cleanup_mode"] = cleanup
                outcome, sqlstate, reason = _outcome_for(
                    assignment
                )
                ordinal += 1
                cases.append(
                    BeginFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"BEGIN{ordinal:05d}",
                        sql_filename=(
                            f"BEGIN{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"begin_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"BEGIN-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "begin_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"transaction_state="
                            f"{assignment['transaction_state']} "
                            f"x transaction_mode="
                            f"{assignment['transaction_mode']} "
                            f"x chain_behavior="
                            f"{assignment['chain_behavior']} "
                            f"x framework_context="
                            f"{assignment['framework_context']} "
                            f"x verification_mode="
                            f"{verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "target_action"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return BeginFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(
            cases_tuple
        ),
        derived_combinations_yaml=_derived_combinations_yaml(
            cases_tuple
        ),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "BeginFactorExtensionError",
    "BeginFactorExtensionCase",
    "BeginFactorExtensionPlan",
    "build_begin_factor_extension_plan",
]
