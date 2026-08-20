"""Bounded post-coverage cross-factor extension expander for ROLLBACK PREPARED.

The marginal factor-value-loop (:mod:`rollback_prepared_factor_loop`) is the
required baseline: one program per factor value, 44 local cases
(GRM 1 + SFV 43).  This module adds the bounded post-coverage extension
phase allowed by ``rollback_prepared.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the single
grammar branch (``branch_1``), with at most one failure-causing value
per case so attribution stays clean, and ``verification_mode`` /
``cleanup_mode`` crossed so every declared T6 value is exercised.

ROLLBACK PREPARED reaches four failure surfaces: the
no-prepared-transaction cluster
(``transaction_state=missing_required_state``, 42704), the
cannot-run-inside-a-transaction-block surface
(``transaction_state=inside_transaction`` /
``transaction_state=savepoint_exists``, 25001), and the missing-identifier
syntax surface (``transaction_id_shape=missing_id``, 42601).  These are
the only crossed behaviour-negative values; the declared meta-failure
``expected_status=failure`` and ``invalid_combination`` are NOT crossed
(``expected_status`` is derived, ``invalid_combination`` stays at the
baseline ``none``).

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

from .rollback_prepared_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_rollback_prepared_factor_loop_plan,
)


class RollbackPreparedFactorExtensionError(ValueError):
    """Raised when a frozen ROLLBACK PREPARED extension input drifts."""


@dataclass(frozen=True)
class RollbackPreparedFactorExtensionCase:
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
class RollbackPreparedFactorExtensionPlan:
    cases: tuple[RollbackPreparedFactorExtensionCase, ...]
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

# General behaviour axes crossed for the single branch_1.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "transaction_state": (
        "outside_transaction",
        "prepared_transaction_exists",
        "missing_required_state",
        "inside_transaction",
        "savepoint_exists",
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
    "transaction_id_shape": (
        "simple_id",
        "quoted_id",
        "duplicate_id",
        "missing_id",
    ),
    "environment_context": (
        "normal_session",
        "transaction_block",
        "outside_transaction_required",
        "external_resource_required",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch are fixed for the single branch.
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "rollback_prepared",
    "expected_status": "success",
    "transaction_state": "prepared_transaction_exists",
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

# Crossed behaviour-negative (factor, value) pairs -- the only failure
# surfaces for ROLLBACK PREPARED that appear in the crossed axes.  The
# declared meta-failure ``expected_status=failure`` and
# ``invalid_combination=syntax_valid_semantic_error`` are NOT crossed
# (expected_status is derived; invalid_combination stays at baseline none)
# so counting both would double-count a single failure and break
# at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("transaction_state", "missing_required_state"),
        ("transaction_state", "inside_transaction"),
        ("transaction_state", "savepoint_exists"),
        ("transaction_id_shape", "missing_id"),
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
    """Derive expected_status from the crossed failure pair (if any)."""

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


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
        assignment["target_action"] = "rollback_prepared"
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise RollbackPreparedFactorExtensionError(
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
    cases: tuple[RollbackPreparedFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"rollback-prepared-factor-extension-v1\n"
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
    cases: tuple[RollbackPreparedFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ROLLBACK PREPARED extension "
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
                    "resolver": (
                        "rollback_prepared_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ROLLBACK PREPARED",
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


def build_rollback_prepared_factor_extension_plan(
    repository_root: Path,
) -> RollbackPreparedFactorExtensionPlan:
    """Build the bounded ROLLBACK PREPARED post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_rollback_prepared_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[RollbackPreparedFactorExtensionCase] = []
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
                    RollbackPreparedFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"ROLLBACKPREPARED{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"ROLLBACKPREPARED{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"rollbackprepared_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"ROLLBACKPREPARED-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "rollback_prepared_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"transaction_state="
                            f"{assignment['transaction_state']} "
                            f"transaction_mode="
                            f"{assignment['transaction_mode']} "
                            f"chain_behavior="
                            f"{assignment['chain_behavior']} "
                            f"transaction_id_shape="
                            f"{assignment['transaction_id_shape']} "
                            f"environment_context="
                            f"{assignment['environment_context']} "
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
    return RollbackPreparedFactorExtensionPlan(
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
    "RollbackPreparedFactorExtensionError",
    "RollbackPreparedFactorExtensionCase",
    "RollbackPreparedFactorExtensionPlan",
    "build_rollback_prepared_factor_extension_plan",
]
