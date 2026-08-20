"""Bounded post-coverage cross-factor extension expander for EXPLAIN.

The marginal factor-value-loop (:mod:`explain_factor_loop`) is the
required baseline: one program per factor value, 48 local cases (GRM 1
+ SFV 47).  This module adds the bounded post-coverage extension phase
allowed by ``explain.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes, with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode``/``cleanup_mode`` crossed so every declared T6
value is exercised.

EXPLAIN has a single synopsis branch (``branch_1``), so every crossed
axis is observable through the ``explain`` action.  The T5 boundary
factors (``invalid_combination``, ``resource_boundary``) are derived
from their T1-T4 counterparts, not crossed as axes.  The
``syntax_valid_semantic_error`` value is a baseline-only failure (a
specific bad-options combo) and is not derivable from the T1-T4 axes,
so it is not produced here.

Consistency rules:
  1. ``target_state == database_wide`` IFF
     ``target_name_shape == all_or_database_wide``.
  2. ``privilege_context == insufficient_privilege`` is invalid when
     ``target_state == database_wide`` (DB-wide EXPLAIN with insufficient
     privilege silently skips — no error, so it cannot be an expected
     failure).
  3. At most one failure-causing value per case (at-most-one-failure
     attribution).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .explain_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_explain_factor_loop_plan,
)


class ExplainFactorExtensionError(ValueError):
    """Raised when a frozen EXPLAIN extension input drifts."""


@dataclass(frozen=True)
class ExplainFactorExtensionCase:
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
class ExplainFactorExtensionPlan:
    cases: tuple[ExplainFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 48
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

# Main-axis factors crossed for the single EXPLAIN branch.
_MAIN_AXES: dict[str, tuple[str, ...]] = {
    "target_state": (
        "target_exists",
        "target_missing",
        "database_wide",
        "wrong_object_type",
    ),
    "target_name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
        "all_or_database_wide",
    ),
    "privilege_context": (
        "owner",
        "granted_role",
        "insufficient_privilege",
    ),
    "option_shape": (
        "minimal",
        "verbose_or_format",
        "boolean_options",
        "resource_options",
        "serialize",
        "memory",
    ),
    "execution_mode": (
        "metadata_only",
        "executes_statement",
        "locks_or_rewrites",
        "server_side_io",
    ),
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    ("branch_1", "explain", _MAIN_AXES),
)

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "explain",
    "expected_status": "success",
    "target_state": "target_exists",
    "option_shape": "minimal",
    "execution_mode": "metadata_only",
    "target_name_shape": "plain_identifier",
    "input_output_shape": "none",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "resource_boundary": "small_relation",
    "verification_mode": "catalog_query",
    "cleanup_mode": "rollback",
}

# Crossed behaviour-negative (factor, value) pairs.
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

    ts = assignment.get("target_state", "target_exists")
    tns = assignment.get(
        "target_name_shape", "plain_identifier"
    )

    # Rule 1: database_wide IFF all_or_database_wide.
    if ts == "database_wide" and tns != "all_or_database_wide":
        return False
    if ts != "database_wide" and tns == "all_or_database_wide":
        return False

    # Rule 2: insufficient_privilege invalid with database_wide.
    pc = assignment.get("privilege_context", "owner")
    if pc == "insufficient_privilege" and ts == "database_wide":
        return False

    # Rule 3: at-most-one-failure attribution.
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    ts = a.get("target_state", "target_exists")

    if ts == "wrong_object_type":
        a["invalid_combination"] = "object_type_mismatch"
    else:
        a["invalid_combination"] = "none"

    a["resource_boundary"] = "small_relation"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, action, axes in _BRANCH_CONFIG:
        names = list(axes)
        for values in itertools.product(
            *[axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = branch
            assignment["target_action"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise ExplainFactorExtensionError(
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
    cases: tuple[ExplainFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"explain-factor-extension-v1\n"
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
    cases: tuple[ExplainFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"EXPLAIN extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "explain_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "EXPLAIN",
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


def build_explain_factor_extension_plan(
    repository_root: Path,
) -> ExplainFactorExtensionPlan:
    """Build the bounded EXPLAIN post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_explain_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[ExplainFactorExtensionCase] = []
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
                    ExplainFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"EXPLAIN{ordinal:05d}",
                        sql_filename=(
                            f"EXPLAIN{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"explain_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"EXPLAIN-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "explain_declared_factor_baseline"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x target_state="
                            f"{assignment['target_state']} "
                            f"x target_name_shape="
                            f"{assignment['target_name_shape']} "
                            f"x privilege_context="
                            f"{assignment['privilege_context']} "
                            f"x option_shape="
                            f"{assignment['option_shape']} "
                            f"x execution_mode="
                            f"{assignment['execution_mode']} "
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
    return ExplainFactorExtensionPlan(
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
    "ExplainFactorExtensionError",
    "ExplainFactorExtensionCase",
    "ExplainFactorExtensionPlan",
    "build_explain_factor_extension_plan",
]
