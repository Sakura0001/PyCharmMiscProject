"""Bounded post-coverage cross-factor extension expander for CREATE CAST.

The marginal factor-value-loop (:mod:`create_cast_factor_loop`) is the
required baseline: one program per factor value, 63 local cases
(GRM 3 + SFV 60).  This module adds the bounded post-coverage extension
phase allowed by ``create_cast.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 3 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode``/``cleanup_mode`` crossed so every
declared T6 value is exercised.

WITHOUT FUNCTION requires superuser privilege, so
``privilege_level=non_owner`` is an unconditional failure on every branch.
The T5 single-value factors (binary_coercible_non_superuser,
function_signature_mismatch, insufficient_privilege) are derived from
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

from .create_cast_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_cast_factor_loop_plan,
)


class CreateCastFactorExtensionError(ValueError):
    """Raised when a frozen CREATE CAST extension input drifts."""


@dataclass(frozen=True)
class CreateCastFactorExtensionCase:
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
class CreateCastFactorExtensionPlan:
    cases: tuple[CreateCastFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 63
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_cast_catalog_query",
    "actual_cast_execution",
)
_CLEANUP_MODES = (
    "DROP_CAST",
    "DROP_CAST_IF_EXISTS",
)

# General axes crossed for ALL 3 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "implicit_context": (
        "explicit_only_default",
        "as_assignment",
        "as_implicit",
    ),
    "privilege_level": (
        "superuser",
        "type_owner_source",
        "type_owner_target",
        "non_owner",
    ),
    "source_type": (
        "integer",
        "bigint",
        "text",
        "numeric",
        "boolean",
        "date",
        "timestamp",
        "custom_type",
    ),
    "target_type": (
        "integer",
        "bigint",
        "text",
        "numeric",
        "float8",
        "boolean",
        "timestamp",
        "custom_type",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / cast_implementation are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "not_exists",
    "expected_status": "success",
    "implicit_context": "explicit_only_default",
    "source_type": "integer",
    "target_type": "bigint",
    "source_type_shape": "plain_type",
    "target_type_shape": "plain_type",
    "function_name_shape": "plain_identifier",
    "privilege_level": "superuser",
    "function_dependency": "function_exists_correct_signature",
    "type_ownership": "owns_both",
    "duplicate_cast": "reverse_direction_exists",
    "same_source_and_target": "same_type_multiarg_function",
    "verification_mode": "pg_cast_catalog_query",
    "cleanup_mode": "DROP_CAST",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_with_function",
        "with_function",
        {
            "function_dependency": (
                "function_exists_correct_signature",
                "function_exists_wrong_signature",
                "function_not_exists",
            ),
            "function_name_shape": (
                "plain_identifier",
                "schema_qualified",
            ),
        },
    ),
    (
        "branch_without_function",
        "without_function",
        {},
    ),
    (
        "branch_with_inout",
        "with_inout",
        {},
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T5 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("privilege_level", "non_owner"),
        ("function_dependency", "function_not_exists"),
        ("function_dependency", "function_exists_wrong_signature"),
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

    src = assignment.get("source_type", "integer")
    tgt = assignment.get("target_type", "bigint")
    if src == tgt:
        return False

    pl = assignment.get("privilege_level", "superuser")
    to = assignment.get("type_ownership", "owns_both")
    if pl == "non_owner" and to != "owns_neither":
        return False
    if pl != "non_owner" and to == "owns_neither":
        return False

    ci = assignment.get("cast_implementation", "with_function")
    fd = assignment.get("function_dependency", "")
    if ci != "with_function" and fd not in (
        "",
        "function_exists_correct_signature",
    ):
        return False

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    ci = a.get("cast_implementation", "with_function")
    pl = a.get("privilege_level", "superuser")
    to = a.get("type_ownership", "owns_both")
    fd = a.get("function_dependency", "function_exists_correct_signature")
    ip = a.get("insufficient_privilege", "")
    src = a.get("source_type", "integer")
    tgt = a.get("target_type", "bigint")

    if (
        pl == "non_owner"
        or to == "owns_neither"
        or ip in ("owns_no_type", "no_usage_on_other_type")
    ):
        a["privilege_level"] = "non_owner"
        a["type_ownership"] = "owns_neither"
        a["insufficient_privilege"] = "owns_no_type"
    elif pl == "type_owner_source" or to == "owns_source_type":
        a["privilege_level"] = "type_owner_source"
        a["type_ownership"] = "owns_source_type"
    elif pl == "type_owner_target" or to == "owns_target_type":
        a["privilege_level"] = "type_owner_target"
        a["type_ownership"] = "owns_target_type"

    if ci == "without_function" and pl != "superuser":
        a["binary_coercible_non_superuser"] = (
            "non_superuser_without_function"
        )

    if (
        fd == "function_exists_wrong_signature"
    ):
        a["function_signature_mismatch"] = "wrong_first_arg_type"

    if src == tgt:
        if ci == "with_function":
            a["same_source_and_target"] = "same_type_multiarg_function"
        else:
            a["same_source_and_target"] = "same_type_no_function"

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
            assignment["cast_implementation"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateCastFactorExtensionError(
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
    cases: tuple[CreateCastFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"create-cast-factor-extension-v1\n")
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
    cases: tuple[CreateCastFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE CAST extension {case.ordinal:05d}: "
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
                        "create_cast_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE CAST",
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


def build_create_cast_factor_extension_plan(
    repository_root: Path,
) -> CreateCastFactorExtensionPlan:
    """Build the bounded CREATE CAST post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_cast_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateCastFactorExtensionCase] = []
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
                    CreateCastFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATECAST{ordinal:05d}",
                        sql_filename=(
                            f"CREATECAST{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createcast_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CCAST-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_cast_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"cast_implementation="
                            f"{assignment['cast_implementation']} "
                            f"x implicit_context="
                            f"{assignment['implicit_context']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x source_type="
                            f"{assignment['source_type']} "
                            f"x target_type="
                            f"{assignment['target_type']} "
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
    return CreateCastFactorExtensionPlan(
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
    "CreateCastFactorExtensionError",
    "CreateCastFactorExtensionCase",
    "CreateCastFactorExtensionPlan",
    "build_create_cast_factor_extension_plan",
]
