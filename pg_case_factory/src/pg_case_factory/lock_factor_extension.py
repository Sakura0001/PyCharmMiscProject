"""Bounded post-coverage cross-factor extension expander for LOCK TABLE.

The marginal factor-value-loop (:mod:`lock_factor_loop`) is the required
baseline: one program per factor value, 46 local SFV cases.  This module
adds the bounded post-coverage extension phase allowed by
``lock.yaml`` ``post_coverage_extension_policy.enabled: true``:
cross-factor combinations of the positive behaviour axes across the
single statement branch, with at most one failure-causing value per case
so attribution stays clean, and ``verification_mode`` / ``cleanup_mode``
crossed so every declared T6 value is exercised.

LOCK TABLE operates on a ``pg_class`` table relation.  Success-path
cases CREATE the fixture table as setup, so the bookend contract (DROP
TABLE IF EXISTS first/last) applies to those cases.  The wrong-object-type
cluster (``target_state`` / ``invalid_combination``) is derived in
:func:`_derive_t5_factors`, not crossed as a pair, so a single failure
is not double-counted.

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

from .lock_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_lock_factor_loop_plan,
)


class LockFactorExtensionError(ValueError):
    """Raised when a frozen LOCK extension input drifts."""


@dataclass(frozen=True)
class LockFactorExtensionCase:
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
class LockFactorExtensionPlan:
    cases: tuple[LockFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 46
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "effect_query",
    "error_assertion",
    "returned_rows",
)
_CLEANUP_MODES = (
    "drop_objects",
    "reset_state",
    "rollback",
)

# General axes crossed for the single statement branch.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "target_name_shape": (
        "plain_identifier",
        "quoted_identifier",
        "schema_qualified",
    ),
    "privilege_context": (
        "owner",
        "maintain_privilege",
        "insufficient_privilege",
    ),
}

# Branch axes crossed for branch_1.
_BRANCH_AXES: dict[str, tuple[str, ...]] = {
    "target_state": (
        "target_exists",
        "target_missing",
        "wrong_object_type",
    ),
    "option_shape": (
        "minimal",
        "boolean_options",
        "resource_options",
    ),
    "resource_boundary": (
        "empty_relation",
        "small_relation",
        "locked_relation",
    ),
}

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "target_state": "target_exists",
    "expected_status": "success",
    "execution_mode": "executes_statement",
    "option_shape": "minimal",
    "input_output_shape": "none",
    "target_name_shape": "plain_identifier",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "resource_boundary": "small_relation",
    "cleanup_mode": "drop_objects",
    "verification_mode": "catalog_query",
}

# Crossed behaviour-negative (factor, value) pairs - one representative
# per failure scenario.  The wrong-object-type overlap
# (invalid_combination=object_type_mismatch) is derived from
# target_state=wrong_object_type in :func:`_derive_t5_factors`, so it is
# NOT listed here (counting both would double-count a single failure and
# break at-most-one attribution).
_CROSSED_NEGATIVES = frozenset(
    {
        ("target_state", "target_missing"),
        ("target_state", "wrong_object_type"),
        ("privilege_context", "insufficient_privilege"),
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


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive the wrong-object-type cluster and expected_status."""

    state = a.get("target_state", "target_exists")
    ic = a.get("invalid_combination", "none")
    if state == "wrong_object_type" or ic == "object_type_mismatch":
        a["target_state"] = "wrong_object_type"
        a["invalid_combination"] = "object_type_mismatch"
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    all_axes: dict[str, tuple[str, ...]] = {}
    all_axes.update(_GENERAL_AXES)
    all_axes.update(_BRANCH_AXES)
    names = list(all_axes)
    combos: list[dict[str, str]] = []
    for values in itertools.product(*[all_axes[n] for n in names]):
        assignment: dict[str, str] = dict(_BASELINE)
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_t5_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise LockFactorExtensionError(
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
    cases: tuple[LockFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"lock-factor-extension-v1\n")
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(case.factor_assignment),
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
    cases: tuple[LockFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"LOCK extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "lock_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "LOCK TABLE",
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


def build_lock_factor_extension_plan(
    repository_root: Path,
) -> LockFactorExtensionPlan:
    """Build the bounded LOCK post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_lock_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[LockFactorExtensionCase] = []
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
                outcome, sqlstate, reason = _outcome_for(assignment)
                ordinal += 1
                cases.append(
                    LockFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"LOCK{ordinal:05d}",
                        sql_filename=f"LOCK{ordinal:05d}.sql",
                        object_prefix=f"lock_{ordinal:05d}_",
                        derivation_id=(
                            f"LOCK-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "lock_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x target_state="
                            f"{assignment['target_state']} "
                            f"x privilege_context="
                            f"{assignment['privilege_context']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "statement_branch"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return LockFactorExtensionPlan(
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
    "LockFactorExtensionError",
    "LockFactorExtensionCase",
    "LockFactorExtensionPlan",
    "build_lock_factor_extension_plan",
]
