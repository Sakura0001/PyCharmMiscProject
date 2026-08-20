"""Bounded post-coverage cross-factor extension expander for VALUES.

The marginal factor-value-loop (:mod:`values_factor_loop`) is the
required baseline: one program per factor value, 49 local cases (GRM 1 +
SFV 48).  This module adds the bounded post-coverage extension phase
allowed by ``values.yaml`` ``post_coverage_extension_policy.enabled:
true``: cross-factor combinations of the positive T1-T4 behaviour axes
across the single ``branch_1`` grammar branch, with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode`` x ``cleanup_mode`` crossed so every declared T6
value is exercised.

VALUES mirrors SELECT's extension: both are DML 15-factor query
statements.  The failure-causing values are:
``target_relation_state=missing``,
``target_relation_state=wrong_object_type``,
``privilege_context=insufficient_privilege``, and
``constraint_boundary=constraint_violation``.  The T5 single-value
factors (invalid_combination, dependency_state) are derived from their
T1-T4 counterparts, not crossed as axes.

VALUES differs from SELECT only in the baseline count (49 vs 51) and
two factor value sets (name_shape has 4 values without
row_lock_of_alias; with_clause has 3 values without merge_cte).  The
extension general axes are identical to SELECT's (4 name_shape values
are crossed in both), so the extension produces the same 17664 cases.

The extension phase never replaces a required-baseline obligation.
Each extension case carries a derivation record (per yaml
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

from .values_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_values_factor_loop_plan,
)


class ValuesFactorExtensionError(ValueError):
    """Raised when a frozen VALUES extension input drifts."""


@dataclass(frozen=True)
class ValuesFactorExtensionCase:
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
class ValuesFactorExtensionPlan:
    cases: tuple[ValuesFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 49
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

# General axes crossed for the single branch.  VALUES shares SELECT's
# DML 15-factor schema; the extension crosses the same 4 name_shape
# values (row_lock_of_alias is not a VALUES factor — VALUES has no
# FOR UPDATE clause).
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "target_relation_state": (
        "exists",
        "missing",
        "wrong_object_type",
    ),
    "data_or_query_shape": (
        "minimal",
        "explicit_values",
        "query_source",
        "cte_source",
    ),
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
        "alias_used",
    ),
    "expression_shape": (
        "literal",
        "column_reference",
        "function_call",
        "subquery_expression",
    ),
    "privilege_context": (
        "owner",
        "granted_role",
        "insufficient_privilege",
    ),
    "constraint_boundary": (
        "none",
        "constraint_satisfied",
        "constraint_violation",
        "empty_input",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch are overridden per branch.
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "expected_status": "success",
    "target_relation_state": "exists",
    "data_or_query_shape": "explicit_values",
    "condition_shape": "simple_predicate",
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

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_1",
        "values",
        {},
    ),
)

# Crossed behaviour-negative (factor, value) pairs -- one representative
# per failure scenario.  Overlapping T5/T3 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("target_relation_state", "missing"),
        ("target_relation_state", "wrong_object_type"),
        ("privilege_context", "insufficient_privilege"),
        ("constraint_boundary", "constraint_violation"),
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
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    trs = a.get("target_relation_state", "exists")

    if trs == "missing":
        a["dependency_state"] = "missing_dependency"
        a["invalid_combination"] = "syntax_valid_semantic_error"
    elif trs == "wrong_object_type":
        a["dependency_state"] = "ready"
        a["invalid_combination"] = "object_type_mismatch"
    else:
        a["dependency_state"] = "ready"
        a["invalid_combination"] = "none"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, action, axes in _BRANCH_CONFIG:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(
            *[all_axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            assignment["target_action"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise ValuesFactorExtensionError(
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
    cases: tuple[ValuesFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"values-factor-extension-v1\n")
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
    cases: tuple[ValuesFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"VALUES extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "values_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "VALUES",
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


def build_values_factor_extension_plan(
    repository_root: Path,
) -> ValuesFactorExtensionPlan:
    """Build the bounded VALUES post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_values_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[ValuesFactorExtensionCase] = []
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
                    ValuesFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"VALUES{ordinal:05d}",
                        sql_filename=f"VALUES{ordinal:05d}.sql",
                        object_prefix=f"values_{ordinal:05d}_",
                        derivation_id=(
                            f"VALUES-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "values_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x target_relation_state="
                            f"{assignment['target_relation_state']} "
                            f"x data_or_query_shape="
                            f"{assignment['data_or_query_shape']} "
                            f"x name_shape="
                            f"{assignment['name_shape']} "
                            f"x expression_shape="
                            f"{assignment['expression_shape']} "
                            f"x privilege_context="
                            f"{assignment['privilege_context']} "
                            f"x constraint_boundary="
                            f"{assignment['constraint_boundary']} "
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
    return ValuesFactorExtensionPlan(
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
    "ValuesFactorExtensionError",
    "ValuesFactorExtensionCase",
    "ValuesFactorExtensionPlan",
    "build_values_factor_extension_plan",
]
