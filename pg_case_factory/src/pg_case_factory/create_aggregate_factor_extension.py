"""Bounded post-coverage cross-factor extension expander for CREATE AGGREGATE.

The marginal factor-value-loop (:mod:`create_aggregate_factor_loop`) is
the required baseline: one program per factor value, 69 local cases
(GRM 3 + SFV 66).  This module adds the bounded post-coverage extension
phase allowed by ``create_aggregate.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 3 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode`` / ``cleanup_mode`` crossed so
every declared T6 value is exercised.

CREATE AGGREGATE with ``privilege_level=non_owner`` is an unconditional
failure (insufficient privilege on the target schema).  The T5
single-value factors (sfunc_signature_mismatch,
or_replace_constraint_violation, invalid_ordered_set_variadic,
missing_required_sfunc, insufficient_privilege) are derived from their
T1-T4 counterparts, not crossed as axes.

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

from .create_aggregate_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_aggregate_factor_loop_plan,
)


class CreateAggregateFactorExtensionError(ValueError):
    """Raised when a frozen CREATE AGGREGATE extension input drifts."""


@dataclass(frozen=True)
class CreateAggregateFactorExtensionCase:
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
class CreateAggregateFactorExtensionPlan:
    cases: tuple[CreateAggregateFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 69
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_aggregate_catalog_query",
    "pg_proc_query",
    "actual_execution",
)
_CLEANUP_MODES = (
    "DROP_AGGREGATE",
    "DROP_AGGREGATE_IF_EXISTS",
    "DROP_AGGREGATE_CASCADE",
)

# General axes crossed for ALL 3 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "already_exists",
    ),
    "privilege_level": ("aggregate_owner", "non_owner"),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "not_exists",
    "expected_status": "success",
    "aggregate_form": "single_arg",
    "or_replace_clause": "absent",
    "parallel_option": "UNSAFE_default",
    "arg_data_type": "integer",
    "aggregate_name_shape": "plain_identifier",
    "argmode_shape": "IN_default",
    "argname_shape": "absent",
    "sfunc_name_shape": "plain",
    "privilege_level": "aggregate_owner",
    "support_function_dependency": "sfunc_exists",
    "combinefunc_dependency": "exists",
    "finalfunc_dependency": "exists",
    "duplicate_aggregate": "same_name_different_signature",
    "verification_mode": "pg_aggregate_catalog_query",
    "cleanup_mode": "DROP_AGGREGATE",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_regular",
        "regular",
        {
            "aggregate_form": (
                "single_arg",
                "multi_arg",
                "zero_arg",
            ),
            "or_replace_clause": (
                "absent",
                "present_replace_existing",
                "present_replace_with_constraint_violation",
            ),
            "arg_data_type": (
                "integer",
                "bigint",
                "numeric",
                "float8",
                "text",
                "boolean",
                "date",
                "timestamp",
                "anyelement",
                "internal",
            ),
            "aggregate_name_shape": (
                "plain_identifier",
                "quoted_identifier",
                "schema_qualified",
                "reserved_word",
            ),
            "sfunc_name_shape": (
                "plain",
                "schema_qualified",
            ),
        },
    ),
    (
        "branch_ordered_set",
        "ordered_set",
        {
            "or_replace_clause": (
                "absent",
                "present_replace_existing",
                "present_replace_with_constraint_violation",
            ),
            "arg_data_type": (
                "integer",
                "bigint",
                "numeric",
                "float8",
                "text",
                "boolean",
                "date",
                "timestamp",
                "anyelement",
                "internal",
            ),
        },
    ),
    (
        "branch_old_syntax",
        "old_syntax",
        {
            "or_replace_clause": (
                "absent",
                "present_replace_existing",
                "present_replace_with_constraint_violation",
            ),
            "arg_data_type": (
                "integer",
                "bigint",
                "numeric",
                "float8",
                "text",
                "boolean",
                "date",
                "timestamp",
                "anyelement",
                "internal",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs — ordered so the most
# specific failure is attributed first.  or_replace_constraint_violation
# implies object_state=already_exists, so it is checked before the
# duplicate failure.
_CROSSED_NEGATIVES = (
    ("or_replace_clause", "present_replace_with_constraint_violation"),
    ("privilege_level", "non_owner"),
    ("object_state", "already_exists"),
)


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Count independent failure causes (at-most-one attribution)."""

    count = 0
    orc = assignment.get("or_replace_clause", "absent")
    os_ = assignment.get("object_state", "not_exists")
    pl = assignment.get("privilege_level", "aggregate_owner")
    # Constraint violation implies already_exists; count as one unit.
    if orc == "present_replace_with_constraint_violation":
        count += 1
    elif os_ == "already_exists" and orc == "absent":
        count += 1  # duplicate (CREATE without OR REPLACE on existing)
    if pl == "non_owner":
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    orc = assignment.get("or_replace_clause", "absent")
    os_ = assignment.get("object_state", "not_exists")
    pl = assignment.get("privilege_level", "aggregate_owner")
    if orc == "present_replace_with_constraint_violation":
        return (
            "or_replace_clause",
            "present_replace_with_constraint_violation",
        )
    if os_ == "already_exists" and orc == "absent":
        return ("object_state", "already_exists")
    if pl == "non_owner":
        return ("privilege_level", "non_owner")
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    os_ = assignment.get("object_state", "not_exists")
    orc = assignment.get("or_replace_clause", "absent")

    # present_replace_with_constraint_violation requires already_exists
    # (can only violate constraints when replacing an existing aggregate)
    if (
        orc == "present_replace_with_constraint_violation"
        and os_ != "already_exists"
    ):
        return False

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "not_exists")
    orc = a.get("or_replace_clause", "absent")
    sfd = a.get("support_function_dependency", "sfunc_exists")
    pl = a.get("privilege_level", "aggregate_owner")

    # duplicate_aggregate: same_name_same_signature when already_exists,
    # same_name_different_signature when not_exists
    if os_ == "already_exists":
        a["duplicate_aggregate"] = "same_name_same_signature"
    else:
        a["duplicate_aggregate"] = "same_name_different_signature"

    # T5 single-value factors are always set to their declared value
    a["sfunc_signature_mismatch"] = "wrong_input_types"
    a["or_replace_constraint_violation"] = "changed_arg_types"
    a["invalid_ordered_set_variadic"] = "non_variadic_any"
    a["missing_required_sfunc"] = "sfunc_not_found"
    a["insufficient_privilege"] = "non_owner_create"

    # Derive support_function_dependency from T5 if needed
    if sfd == "sfunc_not_exists":
        a["missing_required_sfunc"] = "sfunc_not_found"
    if sfd == "sfunc_wrong_signature":
        a["sfunc_signature_mismatch"] = "wrong_input_types"

    # Derive privilege overlap
    if pl == "non_owner":
        a["insufficient_privilege"] = "non_owner_create"

    # Derive or_replace overlap
    if orc == "present_replace_with_constraint_violation":
        a["or_replace_constraint_violation"] = "changed_arg_types"

    a["expected_status"] = (
        "failure" if _failure_unit_count(a) > 0 else "success"
    )


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
                raise CreateAggregateFactorExtensionError(
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
    cases: tuple[CreateAggregateFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-aggregate-factor-extension-v1\n"
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
    cases: tuple[CreateAggregateFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE AGGREGATE extension "
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
                        "create_aggregate_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE AGGREGATE",
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


def build_create_aggregate_factor_extension_plan(
    repository_root: Path,
) -> CreateAggregateFactorExtensionPlan:
    """Build the bounded CREATE AGGREGATE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_aggregate_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateAggregateFactorExtensionCase] = []
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
                    CreateAggregateFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATEAGGREGATE{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATEAGGREGATE{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createaggregate_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CAGG-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_aggregate_required_factor_"
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
    return CreateAggregateFactorExtensionPlan(
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
    "CreateAggregateFactorExtensionError",
    "CreateAggregateFactorExtensionCase",
    "CreateAggregateFactorExtensionPlan",
    "build_create_aggregate_factor_extension_plan",
]
