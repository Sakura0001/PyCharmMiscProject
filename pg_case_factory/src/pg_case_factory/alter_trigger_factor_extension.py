"""Bounded post-coverage cross-factor extension expander for ALTER TRIGGER.

The marginal factor-value-loop (:mod:`alter_trigger_factor_loop`) is
the required baseline: one program per factor value, 43 local cases
(GRM 2 + SFV 41).  This module adds the bounded post-coverage extension
phase allowed by ``alter_trigger.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across both grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode``/``cleanup_mode`` crossed so every
declared T6 value is exercised.

ALTER TRIGGER requires table ownership on every branch, so
``privilege_level=non_owner_no_privilege`` is an unconditional failure.
The T5 single-value factors (target_trigger_not_exists,
permission_insufficient, target_extension_not_exists,
identifier_length_exceeded, trigger_name_duplicate) are derived from
their T1-T4 counterparts, not crossed as axes.

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

from .alter_trigger_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_trigger_factor_loop_plan,
)


class AlterTriggerFactorExtensionError(ValueError):
    """Raised when a frozen ALTER TRIGGER extension input drifts."""


@dataclass(frozen=True)
class AlterTriggerFactorExtensionCase:
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
class AlterTriggerFactorExtensionPlan:
    cases: tuple[AlterTriggerFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 43
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_trigger_catalog_query",
    "information_schema_triggers",
)
_CLEANUP_MODES = (
    "DROP_TRIGGER",
    "DROP_TRIGGER_IF_EXISTS",
)

# General axes crossed for ALL 2 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "exists",
        "not_exists",
    ),
    "partitioned_table_effect": (
        "partitioned_table",
        "regular_table",
    ),
    "privilege_level": (
        "superuser",
        "table_owner",
        "non_owner_no_privilege",
    ),
    "trigger_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
    ),
    "table_name_shape": (
        "simple",
        "quoted",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "exists",
    "expected_status": "success",
    "rename_target": "simple",
    "extension_target": "extension_exists",
    "partitioned_table_effect": "regular_table",
    "trigger_name_shape": "simple",
    "table_name_shape": "simple",
    "new_name_shape": "simple",
    "privilege_level": "superuser",
    "extension_dependency": "extension_installed",
    "table_dependency": "table_exists",
    "verification_mode": "pg_trigger_catalog_query",
    "cleanup_mode": "DROP_TRIGGER",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_1",
        "rename",
        {
            "rename_target": (
                "simple",
                "quoted",
                "reserved_word",
                "duplicate_name",
            ),
            "new_name_shape": (
                "simple",
                "quoted",
                "reserved_word",
            ),
        },
    ),
    (
        "branch_2",
        "depends_on_extension",
        {
            "extension_target": (
                "extension_exists",
                "extension_not_exists",
                "NO_DEPENDS",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T5/T3 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("privilege_level", "non_owner_no_privilege"),
        ("rename_target", "duplicate_name"),
        ("extension_target", "extension_not_exists"),
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

    os = a.get("object_state", "exists")
    pl = a.get("privilege_level", "superuser")
    et = a.get("extension_target", "extension_exists")
    rt = a.get("rename_target", "simple")
    td = a.get("table_dependency", "table_exists")

    if os == "not_exists":
        a["target_trigger_not_exists"] = "trigger_not_found"
    else:
        a["target_trigger_not_exists"] = "trigger_not_found"

    if pl == "non_owner_no_privilege":
        a["permission_insufficient"] = "not_table_owner"
    else:
        a["permission_insufficient"] = "not_table_owner"

    if et == "extension_not_exists":
        a["target_extension_not_exists"] = "extension_name_not_found"
    else:
        a["target_extension_not_exists"] = "extension_name_not_found"

    if rt == "duplicate_name":
        a["trigger_name_duplicate"] = "same_table_same_name"
    else:
        a["trigger_name_duplicate"] = "same_table_same_name"

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
            assignment["grammar_branch"] = branch
            assignment["target_action"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise AlterTriggerFactorExtensionError(
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
    cases: tuple[AlterTriggerFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-trigger-factor-extension-v1\n"
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
    cases: tuple[AlterTriggerFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER TRIGGER extension "
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
                        "alter_trigger_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER TRIGGER",
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


def build_alter_trigger_factor_extension_plan(
    repository_root: Path,
) -> AlterTriggerFactorExtensionPlan:
    """Build the bounded ALTER TRIGGER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_trigger_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterTriggerFactorExtensionCase] = []
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
                    AlterTriggerFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERTRIGGER{ordinal:05d}",
                        sql_filename=(
                            f"ALTERTRIGGER{ordinal:05d}.sql"
                        ),
                        object_prefix=f"altertrigger_{ordinal:05d}_",
                        derivation_id=(
                            f"ATRG-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_trigger_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
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
    return AlterTriggerFactorExtensionPlan(
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
    "AlterTriggerFactorExtensionError",
    "AlterTriggerFactorExtensionCase",
    "AlterTriggerFactorExtensionPlan",
    "build_alter_trigger_factor_extension_plan",
]
