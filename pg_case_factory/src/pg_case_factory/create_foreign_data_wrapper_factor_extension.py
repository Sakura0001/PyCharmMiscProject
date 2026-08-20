"""Bounded post-coverage cross-factor extension expander for CREATE FOREIGN DATA WRAPPER.

The marginal factor-value-loop
(:mod:`create_foreign_data_wrapper_factor_loop`) is the required
baseline: one program per factor value, 58 local cases (GRM 1 + SFV
57).  This module adds the bounded post-coverage extension phase
allowed by ``create_foreign_data_wrapper.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the single
grammar branch (``branch_create_fdw``), with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode`` / ``cleanup_mode`` crossed so every declared T6
value is exercised.

CREATE FOREIGN DATA WRAPPER requires superuser privilege, so
``privilege_level=non_superuser`` is an unconditional failure
(SQLSTATE 42501).  The T5 single-value factors
(duplicate_fdw_name, nonexistent_handler_function,
nonexistent_validator_function, invalid_handler_return_type,
non_superuser_attempt, duplicate_option_name,
no_handler_access_limit) overlap with their T1-T4 counterparts.
Overlapping T5 values are derived in :func:`_derive_t5_factors`, not
crossed, so counting both would double-count a single failure and
break at-most-one attribution.

The extension phase never replaces a required-baseline obligation.
Each extension case carries a derivation record (per yaml
``post_coverage_extension_policy.required_fields``) and is marked
``is_extension``.  Filtering happens BEFORE counting (``raw += 1``),
so ``raw_combination_count == len(cases)`` and ``dropped_count == 0``
(no over-pruning).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .create_foreign_data_wrapper_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_foreign_data_wrapper_factor_loop_plan,
)


class CreateForeignDataWrapperFactorExtensionError(ValueError):
    """Raised when a frozen CREATE FOREIGN DATA WRAPPER extension input drifts."""


@dataclass(frozen=True)
class CreateForeignDataWrapperFactorExtensionCase:
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
class CreateForeignDataWrapperFactorExtensionPlan:
    cases: tuple[CreateForeignDataWrapperFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 58
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_foreign_data_wrapper_catalog",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_fdw",
    "drop_handler_function",
    "drop_validator_function",
    "role_cleanup",
)

# General axes crossed for the single branch_create_fdw.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "already_exists",
    ),
    "handler_clause": (
        "omitted",
        "specified_handler_function",
        "no_handler",
    ),
    "validator_clause": (
        "omitted",
        "specified_validator_function",
        "no_validator",
    ),
    "options_clause": (
        "omitted",
        "single_option",
        "multiple_options",
    ),
    "fdw_name_shape": (
        "simple_id",
        "quoted_id",
        "reserved_word_name",
        "duplicate_name",
        "nonexistent_name",
    ),
    "privilege_level": (
        "superuser",
        "non_superuser",
    ),
}

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_create_fdw",
    "grammar_branch": "branch_create_fdw",
    "target_action": "create_foreign_data_wrapper",
    "object_state": "not_exists",
    "expected_status": "success",
    "handler_clause": "omitted",
    "validator_clause": "omitted",
    "options_clause": "omitted",
    "handler_function_type": "correct_fdw_handler",
    "fdw_name_shape": "simple_id",
    "handler_name_shape": "simple_id",
    "validator_name_shape": "simple_id",
    "option_name_shape": "valid_option",
    "privilege_level": "superuser",
    "handler_function_existence": "function_exists",
    "validator_function_existence": "function_exists",
    "handler_function_return_type": "matches_fdw_handler",
    "duplicate_fdw_name": "no_conflict",
    "nonexistent_handler_function": "function_exists",
    "nonexistent_validator_function": "function_exists",
    "invalid_handler_return_type": "correct_type",
    "non_superuser_attempt": "superuser_execution",
    "duplicate_option_name": "unique_options",
    "no_handler_access_limit": "with_handler_accessible",
    "verification_mode": "pg_foreign_data_wrapper_catalog",
    "cleanup_mode": "drop_fdw",
}

# Crossed behaviour-negative (factor, value) pairs -- one
# representative per failure scenario.  Overlapping T5 values are
# NOT listed here (they are derived in
# :func:`_derive_t5_factors`) so counting both would double-count a
# single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("privilege_level", "non_superuser"),
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

    os_ = assignment.get("object_state", "not_exists")
    fns = assignment.get("fdw_name_shape", "simple_id")

    # Rule 1: fdw_name_shape / object_state consistency.
    if fns == "duplicate_name" and os_ != "already_exists":
        return False
    if fns == "nonexistent_name" and os_ != "not_exists":
        return False

    # Rule 2: at-most-one-failure attribution.
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive overlapping T5 factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "not_exists")
    hc = a.get("handler_clause", "omitted")
    pl = a.get("privilege_level", "superuser")

    # duplicate_fdw_name cluster
    if os_ == "already_exists":
        a["duplicate_fdw_name"] = "same_name_conflict"
    else:
        a["duplicate_fdw_name"] = "no_conflict"

    # no_handler_access_limit cluster
    if hc == "no_handler":
        a["no_handler_access_limit"] = "no_handler_not_accessible"
    else:
        a["no_handler_access_limit"] = "with_handler_accessible"

    # non_superuser_attempt cluster
    if pl == "non_superuser":
        a["non_superuser_attempt"] = "non_superuser_execution"
    else:
        a["non_superuser_attempt"] = "superuser_execution"

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
        assignment["statement_branch"] = "branch_create_fdw"
        assignment["grammar_branch"] = "branch_create_fdw"
        assignment["target_action"] = "create_foreign_data_wrapper"
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_t5_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise CreateForeignDataWrapperFactorExtensionError(
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
    cases: tuple[CreateForeignDataWrapperFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-foreign-data-wrapper-factor-extension-v1\n"
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
    cases: tuple[CreateForeignDataWrapperFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE FOREIGN DATA WRAPPER extension "
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
                        "create_foreign_data_wrapper_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE FOREIGN DATA WRAPPER",
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


def build_create_foreign_data_wrapper_factor_extension_plan(
    repository_root: Path,
) -> CreateForeignDataWrapperFactorExtensionPlan:
    """Build the bounded CREATE FOREIGN DATA WRAPPER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_foreign_data_wrapper_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateForeignDataWrapperFactorExtensionCase] = []
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
                    CreateForeignDataWrapperFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATEFOREIGNDATAWRAPPER{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATEFOREIGNDATAWRAPPER{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createforeigndatawrapper_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CFDW-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_foreign_data_wrapper_declared_"
                            "factor_baseline"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"object_state="
                            f"{assignment['object_state']} "
                            f"handler_clause="
                            f"{assignment['handler_clause']} "
                            f"validator_clause="
                            f"{assignment['validator_clause']} "
                            f"options_clause="
                            f"{assignment['options_clause']} "
                            f"fdw_name_shape="
                            f"{assignment['fdw_name_shape']} "
                            f"privilege_level="
                            f"{assignment['privilege_level']} "
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
    return CreateForeignDataWrapperFactorExtensionPlan(
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
    "CreateForeignDataWrapperFactorExtensionError",
    "CreateForeignDataWrapperFactorExtensionCase",
    "CreateForeignDataWrapperFactorExtensionPlan",
    "build_create_foreign_data_wrapper_factor_extension_plan",
]
