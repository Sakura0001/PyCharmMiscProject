"""Bounded post-coverage cross-factor extension expander for CREATE TRIGGER.

The marginal factor-value-loop (:mod:`create_trigger_factor_loop`) is
the required baseline: one program per factor value, 91 local cases
(GRM 3 + SFV 88).  This module adds the bounded post-coverage extension
phase allowed by ``create_trigger.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all three
grammar branches (BEFORE, AFTER, INSTEAD OF), with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode``/``cleanup_mode`` crossed so every declared T6
value is exercised.

Structurally invalid combinations (TRUNCATE + FOR EACH ROW, INSTEAD OF
+ non-ROW, CONSTRAINT + INSTEAD OF, etc.) are filtered BEFORE counting
so ``raw_combination_count == len(cases)`` and ``dropped_count == 0``.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``post_coverage_extension_policy.required_fields``) and is marked
``is_extension``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .create_trigger_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_trigger_factor_loop_plan,
)


class CreateTriggerFactorExtensionError(ValueError):
    """Raised when a frozen CREATE TRIGGER extension input drifts."""


@dataclass(frozen=True)
class CreateTriggerFactorExtensionCase:
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
class CreateTriggerFactorExtensionPlan:
    cases: tuple[CreateTriggerFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 91
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_trigger_catalog_query",
    "information_schema_triggers",
    "SELECT_trigger_test",
)
_CLEANUP_MODES = (
    "DROP_TRIGGER",
    "DROP_TRIGGER_IF_EXISTS",
    "DROP_TRIGGER_ON_TABLE",
)

# General axes crossed for ALL 3 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "or_replace_clause": ("present", "absent"),
    "when_clause": ("with_WHEN_condition", "without_WHEN"),
    "execute_clause": ("FUNCTION", "PROCEDURE"),
    "object_state": ("not_exists", "already_exists"),
}

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "trigger_timing": "BEFORE",
    "trigger_event": "INSERT",
    "object_state": "not_exists",
    "expected_status": "success",
    "or_replace_clause": "absent",
    "constraint_trigger": "absent",
    "for_each_clause": "ROW",
    "deferrable_clause": "absent",
    "when_clause": "without_WHEN",
    "referencing_clause": "absent",
    "from_clause": "absent",
    "update_of_columns": "without_column_list",
    "execute_clause": "FUNCTION",
    "trigger_name_shape": "simple",
    "table_name_shape": "simple",
    "function_name_shape": "simple",
    "event_column_list": "single_column",
    "privilege_level": "superuser",
    "table_dependency": "table_exists",
    "function_dependency": "trigger_function_exists",
    "referenced_table_dependency": "referenced_table_exists",
    "schema_dependency": "schema_exists",
    "verification_mode": "pg_trigger_catalog_query",
    "cleanup_mode": "DROP_TRIGGER",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_1",
        "before_trigger",
        {
            "trigger_event": (
                "INSERT",
                "UPDATE",
                "DELETE",
                "TRUNCATE",
            ),
            "for_each_clause": ("ROW", "STATEMENT", "absent"),
            "constraint_trigger": ("present", "absent"),
        },
    ),
    (
        "branch_2",
        "after_trigger",
        {
            "trigger_event": (
                "INSERT",
                "UPDATE",
                "DELETE",
                "TRUNCATE",
            ),
            "for_each_clause": ("ROW", "STATEMENT", "absent"),
            "constraint_trigger": ("present", "absent"),
            "referencing_clause": (
                "with_BOTH",
                "absent",
            ),
        },
    ),
    (
        "branch_3",
        "instead_of_trigger",
        {
            "trigger_event": (
                "INSERT",
                "UPDATE",
                "DELETE",
            ),
        },
    ),
)


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair causing a clean failure, or None.

    object_state=already_exists is only a failure when or_replace is
    absent (duplicate without OR REPLACE).  When or_replace=present the
    trigger is replaced (success).
    """
    if (
        assignment.get("object_state") == "already_exists"
        and assignment.get("or_replace_clause") == "absent"
    ):
        return ("duplicate_trigger", "without_OR_REPLACE_error")
    return None


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return 1 if _present_failure_pair(assignment) is not None else 0


def _is_structurally_valid(assignment: dict[str, str]) -> bool:
    """Filter out structurally invalid combinations."""

    timing = assignment.get("trigger_timing")
    event = assignment.get("trigger_event")
    for_each = assignment.get("for_each_clause")
    constraint = assignment.get("constraint_trigger")

    if timing == "INSTEAD_OF":
        if event == "TRUNCATE":
            return False
        if for_each != "ROW":
            return False
        if constraint == "present":
            return False

    if event == "TRUNCATE" and for_each == "ROW":
        return False

    if constraint == "present":
        if for_each != "ROW":
            return False
        if event == "TRUNCATE":
            return False

    return True


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    return _is_structurally_valid(assignment) and (
        _failure_unit_count(assignment) <= 1
    )


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    if a.get("object_state") == "already_exists":
        a["duplicate_trigger"] = "without_OR_REPLACE_error"
    else:
        a["duplicate_trigger"] = "with_OR_REPLACE_replace"

    a["INSTEAD_OF_on_table"] = "INSTEAD_OF_INSERT_on_regular_table"
    a["BEFORE_INSTEAD_OF_on_view"] = "BEFORE_INSERT_on_view"
    a["TRUNCATE_with_FOR_EACH_ROW"] = "TRUNCATE_FOR_EACH_ROW"
    a["UPDATE_OF_nonexistent_column"] = "UPDATE_OF_missing_column"
    a["constraint_trigger_on_non_constraint_event"] = (
        "CONSTRAINT_with_INSTEAD_OF"
    )
    a["permission_insufficient"] = "no_create_trigger_privilege"
    a["referenced_table_not_exists"] = "FROM_table_not_found"
    a["identifier_length_exceeded"] = "over_63_chars"

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
            assignment["trigger_timing"] = {
                "branch_1": "BEFORE",
                "branch_2": "AFTER",
                "branch_3": "INSTEAD_OF",
            }[branch]
            assignment["target_action"] = action
            if branch == "branch_3":
                assignment["table_dependency"] = (
                    "view_exists_for_INSTEAD_OF"
                )
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateTriggerFactorExtensionError(
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
    cases: tuple[CreateTriggerFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-trigger-factor-extension-v1\n"
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
    cases: tuple[CreateTriggerFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE TRIGGER extension "
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
                        "create_trigger_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE TRIGGER",
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


def build_create_trigger_factor_extension_plan(
    repository_root: Path,
) -> CreateTriggerFactorExtensionPlan:
    """Build the bounded CREATE TRIGGER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_trigger_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateTriggerFactorExtensionCase] = []
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
                    CreateTriggerFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATETRIGGER{ordinal:05d}",
                        sql_filename=(
                            f"CREATETRIGGER{ordinal:05d}.sql"
                        ),
                        object_prefix=f"createtrigger_{ordinal:05d}_",
                        derivation_id=(
                            f"CTRG-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_trigger_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x trigger_event="
                            f"{assignment['trigger_event']} "
                            f"x for_each_clause="
                            f"{assignment['for_each_clause']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
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
    return CreateTriggerFactorExtensionPlan(
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
    "CreateTriggerFactorExtensionError",
    "CreateTriggerFactorExtensionCase",
    "CreateTriggerFactorExtensionPlan",
    "build_create_trigger_factor_extension_plan",
]
