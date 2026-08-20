"""Bounded post-coverage cross-factor extension expander for CREATE EVENT TRIGGER.

The marginal factor-value-loop (:mod:`create_event_trigger_factor_loop`)
is the required baseline: one program per factor value, 62 local cases
(GRM 1 + SFV 61).  This module adds the bounded post-coverage extension
phase allowed by ``create_event_trigger.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T3 behaviour axes across the single
grammar branch (``branch_create_event_trigger``), with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode`` / ``cleanup_mode`` crossed so every declared T6
value is exercised.

CREATE EVENT TRIGGER requires superuser privilege, so
``privilege_level=non_superuser`` is an unconditional failure
(SQLSTATE 42501).  The other crossed failure surfaces are a duplicate
trigger name (``object_state=exists``, 42710), a missing handler
function (``trigger_function_state=function_not_exists``, 42883), a
wrong-return-type handler (42804) and a wrong-arity handler (42804).
Overlapping T3-T5 values are derived, not crossed as axes.

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

from .create_event_trigger_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_event_trigger_factor_loop_plan,
)


class CreateEventTriggerFactorExtensionError(ValueError):
    """Raised when a frozen CREATE EVENT TRIGGER extension input drifts."""


@dataclass(frozen=True)
class CreateEventTriggerFactorExtensionCase:
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
class CreateEventTriggerFactorExtensionPlan:
    cases: tuple[CreateEventTriggerFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 62
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_event_trigger",
    "error_assertion",
    "trigger_firing_test",
)
_CLEANUP_MODES = (
    "drop_event_trigger",
    "drop_function",
    "cascade_cleanup",
)

# General axes crossed for the single branch_create_event_trigger.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "event_type": (
        "ddl_command_start",
        "ddl_command_end",
        "table_rewrite",
    ),
    "when_filter_clause": (
        "omitted",
        "single_tag_in_condition",
        "multiple_tag_in_values",
        "and_connected_multiple_conditions",
    ),
    "execute_keyword": ("FUNCTION", "PROCEDURE"),
    "privilege_level": ("superuser", "non_superuser"),
    "object_state": ("not_exists", "exists"),
    "trigger_function_state": (
        "function_exists_valid_signature",
        "function_not_exists",
        "function_exists_wrong_return_type",
        "function_exists_with_parameters",
    ),
    "filter_value_shape": (
        "single_command_tag",
        "multiple_command_tags",
        "representative_tags_drop_function",
        "representative_tags_alter_table",
        "representative_tags_create_table",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action are fixed for the single branch.
_BASELINE: dict[str, str] = {
    "expected_status": "success",
    "trigger_name_shape": "simple_id",
    "function_name_shape": "simple_id",
    "function_existence": "function_exists",
    "function_return_type": "event_trigger_return_type",
    "function_parameter_count": "zero_parameters",
    "single_user_mode": "normal_mode",
    "duplicate_trigger_name": "no_conflict",
    "privilege_denied_non_superuser": "superuser_success",
    "nonexistent_function": "function_exists",
    "function_wrong_return_type": "correct_return_type",
    "function_wrong_parameter_count": "zero_parameters",
    "invalid_event_type": "valid_event_type",
    "invalid_filter_variable": "tag_variable",
    "verification_mode": "catalog_query_pg_event_trigger",
    "cleanup_mode": "drop_event_trigger",
}

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T3-T5 values are NOT listed here
# (they are derived in :func:`_derive_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("privilege_level", "non_superuser"),
        ("object_state", "exists"),
        ("trigger_function_state", "function_not_exists"),
        (
            "trigger_function_state",
            "function_exists_wrong_return_type",
        ),
        (
            "trigger_function_state",
            "function_exists_with_parameters",
        ),
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
    """Derive overlapping T3-T5 factors and expected_status from axes."""

    # privilege cluster
    pl = a.get("privilege_level", "superuser")
    if pl == "non_superuser":
        a["privilege_denied_non_superuser"] = "non_superuser_failure"
    else:
        a["privilege_denied_non_superuser"] = "superuser_success"

    # object existence cluster
    os_ = a.get("object_state", "not_exists")
    if os_ == "exists":
        a["duplicate_trigger_name"] = "same_name_conflict"
    else:
        a["duplicate_trigger_name"] = "no_conflict"

    # function state cluster
    tfs = a.get(
        "trigger_function_state",
        "function_exists_valid_signature",
    )
    if tfs == "function_not_exists":
        a["function_existence"] = "function_not_exists"
        a["nonexistent_function"] = "function_not_exists"
        a["function_name_shape"] = "nonexistent_name"
        a["function_return_type"] = "event_trigger_return_type"
        a["function_parameter_count"] = "zero_parameters"
        a["function_wrong_return_type"] = "correct_return_type"
        a["function_wrong_parameter_count"] = "zero_parameters"
    elif tfs == "function_exists_wrong_return_type":
        a["function_existence"] = "function_exists"
        a["nonexistent_function"] = "function_exists"
        a["function_name_shape"] = "simple_id"
        a["function_return_type"] = "non_event_trigger_return_type"
        a["function_wrong_return_type"] = "wrong_return_type"
        a["function_parameter_count"] = "zero_parameters"
        a["function_wrong_parameter_count"] = "zero_parameters"
    elif tfs == "function_exists_with_parameters":
        a["function_existence"] = "function_exists"
        a["nonexistent_function"] = "function_exists"
        a["function_name_shape"] = "simple_id"
        a["function_return_type"] = "event_trigger_return_type"
        a["function_wrong_return_type"] = "correct_return_type"
        a["function_parameter_count"] = "nonzero_parameters"
        a["function_wrong_parameter_count"] = "nonzero_parameters"
    else:
        a["function_existence"] = "function_exists"
        a["nonexistent_function"] = "function_exists"
        a["function_name_shape"] = "simple_id"
        a["function_return_type"] = "event_trigger_return_type"
        a["function_parameter_count"] = "zero_parameters"
        a["function_wrong_return_type"] = "correct_return_type"
        a["function_wrong_parameter_count"] = "zero_parameters"

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
        assignment["statement_branch"] = "branch_create_event_trigger"
        assignment["target_action"] = "create_event_trigger"
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise CreateEventTriggerFactorExtensionError(
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
    cases: tuple[CreateEventTriggerFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-event-trigger-factor-extension-v1\n"
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
    cases: tuple[CreateEventTriggerFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE EVENT TRIGGER extension "
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
                        "create_event_trigger_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE EVENT TRIGGER",
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


def build_create_event_trigger_factor_extension_plan(
    repository_root: Path,
) -> CreateEventTriggerFactorExtensionPlan:
    """Build the bounded CREATE EVENT TRIGGER extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_event_trigger_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateEventTriggerFactorExtensionCase] = []
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
                    CreateEventTriggerFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATEEVENTTRIGGER{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATEEVENTTRIGGER{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createeventtrigger_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CET-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_event_trigger_required_"
                            "factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"event_type="
                            f"{assignment['event_type']} "
                            f"when_filter_clause="
                            f"{assignment['when_filter_clause']} "
                            f"execute_keyword="
                            f"{assignment['execute_keyword']} "
                            f"privilege_level="
                            f"{assignment['privilege_level']} "
                            f"object_state="
                            f"{assignment['object_state']} "
                            f"trigger_function_state="
                            f"{assignment['trigger_function_state']} "
                            f"filter_value_shape="
                            f"{assignment['filter_value_shape']} "
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
    return CreateEventTriggerFactorExtensionPlan(
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
    "CreateEventTriggerFactorExtensionError",
    "CreateEventTriggerFactorExtensionCase",
    "CreateEventTriggerFactorExtensionPlan",
    "build_create_event_trigger_factor_extension_plan",
]
