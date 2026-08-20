"""Bounded post-coverage cross-factor extension expander for LOAD.

The marginal factor-value-loop (:mod:`load_factor_loop`) is the
required baseline: one program per factor value, 46 local cases
(GRM 1 + SFV 45).  This module adds the bounded post-coverage extension
phase allowed by ``load.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the single
grammar branch (``branch_1``), with at most one failure-causing value
per case so attribution stays clean, and ``verification_mode`` /
``cleanup_mode`` crossed so every declared T6 value is exercised.

LOAD requires superuser privilege, so
``privilege_context=insufficient_privilege`` is an unconditional failure
(SQLSTATE 42501).  Two further crossed-axis values are failures for
LOAD: ``target_state=target_missing`` (library not found, 42883) and
``target_state=wrong_object_type`` (file is not a shared library,
55000).  All other crossed-axis values are success-covered.

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

from .load_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_load_factor_loop_plan,
)


class LoadFactorExtensionError(ValueError):
    """Raised when a frozen LOAD extension input drifts."""


@dataclass(frozen=True)
class LoadFactorExtensionCase:
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
class LoadFactorExtensionPlan:
    cases: tuple[LoadFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 46
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

# General axes crossed for the single branch_1.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "target_state": (
        "target_exists",
        "target_missing",
        "database_wide",
        "wrong_object_type",
    ),
    "option_shape": (
        "minimal",
        "verbose_or_format",
        "boolean_options",
        "resource_options",
    ),
    "execution_mode": (
        "metadata_only",
        "executes_statement",
        "locks_or_rewrites",
        "server_side_io",
    ),
    "environment_context": (
        "normal_session",
        "transaction_block",
        "outside_transaction_required",
        "external_resource_required",
    ),
    "privilege_context": (
        "owner",
        "granted_role",
        "insufficient_privilege",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch are fixed for the single branch.
_BASELINE: dict[str, str] = {
    "expected_status": "success",
    "target_state": "database_wide",
    "option_shape": "minimal",
    "execution_mode": "server_side_io",
    "target_name_shape": "all_or_database_wide",
    "input_output_shape": "none",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "resource_boundary": "small_relation",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}

# Crossed behaviour-negative (factor, value) pairs that cause failures
# for LOAD within the general axes: privilege denial, missing library,
# and wrong object type.
_CROSSED_NEGATIVES = frozenset(
    {
        ("privilege_context", "insufficient_privilege"),
        ("target_state", "target_missing"),
        ("target_state", "wrong_object_type"),
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


def _derive_factors(a: dict[str, str]) -> None:
    """Derive expected_status from the crossed failure surfaces."""

    a["expected_status"] = (
        "failure" if _failure_unit_count(a) > 0 else "success"
    )


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    names = list(_GENERAL_AXES)
    for values in itertools.product(
        *[list(_GENERAL_AXES[n]) for n in names]
    ):
        assignment: dict[str, str] = dict(_BASELINE)
        assignment["statement_branch"] = "branch_1"
        assignment["grammar_branch"] = "branch_1"
        assignment["target_action"] = "load"
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise LoadFactorExtensionError(
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
    cases: tuple[LoadFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"load-factor-extension-v1\n"
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
    cases: tuple[LoadFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"LOAD extension "
                    f"{case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "load_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "LOAD",
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


def build_load_factor_extension_plan(
    repository_root: Path,
) -> LoadFactorExtensionPlan:
    """Build the bounded LOAD post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_load_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[LoadFactorExtensionCase] = []
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
                    LoadFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"LOAD{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"LOAD{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"load_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"LOAD-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "load_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"target_state="
                            f"{assignment['target_state']} "
                            f"option_shape="
                            f"{assignment['option_shape']} "
                            f"execution_mode="
                            f"{assignment['execution_mode']} "
                            f"environment_context="
                            f"{assignment['environment_context']} "
                            f"privilege_context="
                            f"{assignment['privilege_context']} "
                            f"verification_mode="
                            f"{verification} "
                            f"cleanup_mode={cleanup}"
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
    return LoadFactorExtensionPlan(
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
    "LoadFactorExtensionError",
    "LoadFactorExtensionCase",
    "LoadFactorExtensionPlan",
    "build_load_factor_extension_plan",
]
