"""Bounded post-coverage cross-factor extension expander for CREATE ACCESS METHOD.

The marginal factor-value-loop (:mod:`create_access_method_factor_loop`)
is the required baseline: one program per factor value, 31 local cases
(GRM 1 + SFV 30).  This module adds the bounded post-coverage
extension phase allowed by ``create_access_method.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the single
grammar branch (``branch_1``), with at most one failure-causing value
per case so attribution stays clean, and ``verification_mode`` /
``cleanup_mode`` crossed so every declared T6 value is exercised.

CREATE ACCESS METHOD requires superuser privilege, so
``privilege_level=non_superuser`` is an unconditional failure (SQLSTATE
42501).  The T5 single-value factors (duplicate_am_name,
invalid_access_method_type, handler_wrong_return_type,
insufficient_privilege) overlap with their T1-T4 counterparts:
duplicate_am_name with object_state, handler_wrong_return_type with
handler_function_state, insufficient_privilege with privilege_level.
The non-overlapping T5 factor invalid_access_method_type is crossed
as a binary axis (none / unknown_type_value).  Overlapping T5 values
are derived in :func:`_derive_t5_factors`, not crossed, so counting
both would double-count a single failure and break at-most-one
attribution.

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

from .create_access_method_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_access_method_factor_loop_plan,
)


class CreateAccessMethodFactorExtensionError(ValueError):
    """Raised when a frozen CREATE ACCESS METHOD extension input drifts."""


@dataclass(frozen=True)
class CreateAccessMethodFactorExtensionCase:
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
class CreateAccessMethodFactorExtensionPlan:
    cases: tuple[CreateAccessMethodFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 31
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_am_catalog_query",
    "pg_am_actual_usage",
    "error_assertion",
    "pg_am_handler_check",
)
_CLEANUP_MODES = (
    "DROP_ACCESS_METHOD",
    "DROP_ACCESS_METHOD_IF_EXISTS",
    "DROP_ACCESS_METHOD_CASCADE",
)

# General axes crossed for the single branch_1.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "already_exists",
    ),
    "access_method_type": (
        "INDEX",
        "TABLE",
    ),
    "handler_function_state": (
        "exists",
        "not_exists",
        "wrong_return_type",
    ),
    "am_name_shape": (
        "plain_identifier",
        "quoted_identifier",
        "reserved_word",
    ),
    "handler_name_shape": (
        "plain_identifier",
        "quoted_identifier",
    ),
    "privilege_level": (
        "superuser",
        "non_superuser",
    ),
    "invalid_access_method_type": (
        "none",
        "unknown_type_value",
    ),
    "duplicate_am_name": (
        "none",
        "with_existing_am",
        "with_builtin_am",
    ),
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    ("branch_1", "create_access_method", _GENERAL_AXES),
)

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "create_access_method",
    "object_state": "not_exists",
    "expected_status": "success",
    "access_method_type": "INDEX",
    "handler_function_state": "exists",
    "am_name_shape": "plain_identifier",
    "handler_name_shape": "plain_identifier",
    "privilege_level": "superuser",
    "handler_dependency": "handler_exists_returns_internal",
    "duplicate_am_name": "none",
    "invalid_access_method_type": "none",
    "handler_wrong_return_type": "correct",
    "insufficient_privilege": "sufficient",
    "verification_mode": "pg_am_catalog_query",
    "cleanup_mode": "DROP_ACCESS_METHOD",
}

# Crossed behaviour-negative (factor, value) pairs -- one representative
# per failure scenario.  Overlapping T5 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both
# would double-count a single failure and break at-most-one
# attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("handler_function_state", "not_exists"),
        ("handler_function_state", "wrong_return_type"),
        ("privilege_level", "non_superuser"),
        ("invalid_access_method_type", "unknown_type_value"),
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
    dan = assignment.get("duplicate_am_name", "none")

    # Rule 1: object_state / duplicate_am_name consistency.
    if os_ == "not_exists" and dan != "none":
        return False
    if os_ == "already_exists" and dan == "none":
        return False

    # Rule 2: at-most-one-failure attribution.
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive overlapping T5 factors and expected_status from T1-T4 values."""

    hfs = a.get("handler_function_state", "exists")
    pl = a.get("privilege_level", "superuser")

    # handler cluster: handler_function_state /
    # handler_dependency / handler_wrong_return_type
    if hfs == "not_exists":
        a["handler_dependency"] = "handler_not_exists"
        a["handler_wrong_return_type"] = "correct"
    elif hfs == "wrong_return_type":
        a["handler_dependency"] = "handler_exists_wrong_return_type"
        a["handler_wrong_return_type"] = "returns_non_internal"
    else:
        a["handler_dependency"] = "handler_exists_returns_internal"
        a["handler_wrong_return_type"] = "correct"

    # privilege cluster: privilege_level / insufficient_privilege
    if pl == "non_superuser":
        a["insufficient_privilege"] = "non_superuser_create"
    else:
        a["insufficient_privilege"] = "sufficient"

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
                raise CreateAccessMethodFactorExtensionError(
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
    cases: tuple[CreateAccessMethodFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-access-method-factor-extension-v1\n"
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
    cases: tuple[CreateAccessMethodFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE ACCESS METHOD extension "
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
                        "create_access_method_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE ACCESS METHOD",
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


def build_create_access_method_factor_extension_plan(
    repository_root: Path,
) -> CreateAccessMethodFactorExtensionPlan:
    """Build the bounded CREATE ACCESS METHOD post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_access_method_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateAccessMethodFactorExtensionCase] = []
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
                    CreateAccessMethodFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATEACCESSMETHOD{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATEACCESSMETHOD{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createaccessmethod_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CAM-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_access_method_declared_"
                            "factor_baseline"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"object_state="
                            f"{assignment['object_state']} "
                            f"access_method_type="
                            f"{assignment['access_method_type']} "
                            f"handler_function_state="
                            f"{assignment['handler_function_state']} "
                            f"am_name_shape="
                            f"{assignment['am_name_shape']} "
                            f"privilege_level="
                            f"{assignment['privilege_level']} "
                            f"invalid_access_method_type="
                            f"{assignment['invalid_access_method_type']} "
                            f"duplicate_am_name="
                            f"{assignment['duplicate_am_name']} "
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
    return CreateAccessMethodFactorExtensionPlan(
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
    "CreateAccessMethodFactorExtensionError",
    "CreateAccessMethodFactorExtensionCase",
    "CreateAccessMethodFactorExtensionPlan",
    "build_create_access_method_factor_extension_plan",
]
