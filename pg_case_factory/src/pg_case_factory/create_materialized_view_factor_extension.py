"""Bounded post-coverage cross-factor extension expander for CREATE MATERIALIZED VIEW.

The marginal factor-value-loop (:mod:`create_materialized_view_factor_loop`)
is the required baseline: one program per factor value, 48 local cases
(GRM 1 + SFV 47).  This module adds the bounded post-coverage extension
phase allowed by ``create_materialized_view.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the single
grammar branch, with at most one failure-causing value per case so
attribution stays clean, and ``verification_mode``/``cleanup_mode``
crossed so every declared T6 value is exercised.

The concrete failure values (target_object_state exists/exists_conflict,
dependency_state missing_dependency, query_source_state
source_table_missing, privilege_context insufficient_privilege,
constraint_boundary security_restricted_operation) are crossed one at a
time with the positive axes.  ``constraint_boundary=unscannable_state``
is a covered (success) value — WITH NO DATA creates the matview
successfully; only a later scan surfaces the unscannable error, which the
DB phase verifies — so it appears in the positive axes, not the negatives.

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

from .create_materialized_view_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_materialized_view_factor_loop_plan,
)


class CreateMaterializedViewFactorExtensionError(ValueError):
    """Raised when a frozen CREATE MATERIALIZED VIEW extension input drifts."""


@dataclass(frozen=True)
class CreateMaterializedViewFactorExtensionCase:
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
class CreateMaterializedViewFactorExtensionPlan:
    cases: tuple[CreateMaterializedViewFactorExtensionCase, ...]
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
    "drop_objects",
    "reset_state",
)

# General positive axes crossed for the single branch.  search_path_sandbox
# is a PG18-specific test point (adapted) and is not crossed here.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "query_shape": (
        "minimal_query",
        "explicit_values",
        "select_from_table",
        "cte_source",
    ),
    "if_not_exists_clause": ("absent", "present"),
    "column_list_clause": ("absent", "present"),
    "using_clause": ("absent", "present"),
    "storage_parameter_clause": ("absent", "present"),
    "tablespace_clause": ("absent", "present"),
    "data_clause": ("with_data", "with_no_data"),
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
    ),
    "column_type_coverage": (
        "representative_types",
        "derived_from_query",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action are overridden per branch (here always create_matview).
# Every declared factor has a default so negative crosses (which only
# override query_shape/name_shape + the one negative) stay complete.
_BASELINE: dict[str, str] = {
    "target_object_state": "absent",
    "query_shape": "minimal_query",
    "expected_status": "success",
    "if_not_exists_clause": "absent",
    "column_list_clause": "absent",
    "using_clause": "absent",
    "storage_parameter_clause": "absent",
    "tablespace_clause": "absent",
    "data_clause": "with_data",
    "privilege_context": "owner",
    "name_shape": "plain_identifier",
    "column_type_coverage": "representative_types",
    "dependency_state": "ready",
    "query_source_state": "source_table_exists",
    "invalid_combination": "none",
    "constraint_boundary": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Each is crossed one at a time so at-most-one
# failure attribution holds.
_CROSSED_NEGATIVES = (
    ("target_object_state", "exists"),
    ("target_object_state", "exists_conflict"),
    ("dependency_state", "missing_dependency"),
    ("query_source_state", "source_table_missing"),
    ("privilege_context", "insufficient_privilege"),
    ("constraint_boundary", "security_restricted_operation"),
)

# Axes crossed alongside each negative value (kept small so the negative
# stays the sole failure attribution).
_NEGATIVE_CROSS_AXES: dict[str, tuple[str, ...]] = {
    "query_shape": (
        "minimal_query",
        "explicit_values",
        "select_from_table",
        "cte_source",
    ),
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
    ),
}


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return sum(
        1
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    )


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive invalid_combination and expected_status from concrete values."""

    tos = a.get("target_object_state", "absent")
    ic = a.get("invalid_combination", "none")
    ds = a.get("dependency_state", "ready")
    qss = a.get("query_source_state", "source_table_exists")
    pc = a.get("privilege_context", "owner")
    cb = a.get("constraint_boundary", "none")

    if tos in ("exists", "exists_conflict"):
        a["invalid_combination"] = "object_type_mismatch"
    elif (
        ds == "missing_dependency"
        or qss == "source_table_missing"
        or cb == "security_restricted_operation"
        or pc == "insufficient_privilege"
    ):
        if ic == "none":
            a["invalid_combination"] = "syntax_valid_semantic_error"

    # constraint_boundary=unscannable_state is created by WITH NO DATA.
    if cb == "unscannable_state":
        a["data_clause"] = "with_no_data"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    tos = assignment.get("target_object_state", "absent")
    ifne = assignment.get("if_not_exists_clause", "absent")
    # IF NOT EXISTS + exists is a no-op success; keep it as a success
    # bearing combo only when it is NOT the sole failure attribution.
    if ifne == "present" and tos == "exists":
        return False
    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    names = list(_GENERAL_AXES)
    for values in itertools.product(
        *[_GENERAL_AXES[n] for n in names]
    ):
        assignment: dict[str, str] = dict(_BASELINE)
        assignment["statement_branch"] = "branch_1"
        assignment["target_action"] = "create_matview"
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_overlapping_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise CreateMaterializedViewFactorExtensionError(
                "duplicate factor key in extension assignment"
            )
        combos.append(assignment)
    return combos


def _negative_combinations() -> list[dict[str, str]]:
    """One-negative-at-a-time crosses with the small positive cross axes."""

    combos: list[dict[str, str]] = []
    names = list(_NEGATIVE_CROSS_AXES)
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        for values in itertools.product(
            *[_NEGATIVE_CROSS_AXES[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = "branch_1"
            assignment["target_action"] = "create_matview"
            assignment[neg_factor] = neg_value
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_overlapping_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateMaterializedViewFactorExtensionError(
                    "duplicate factor key in negative extension assignment"
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
    cases: tuple[CreateMaterializedViewFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-materialized-view-factor-extension-v1\n"
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
    cases: tuple[CreateMaterializedViewFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE MATERIALIZED VIEW extension "
                    f"{case.ordinal:05d}: {case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": (
                        "create_materialized_view_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE MATERIALIZED VIEW",
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


def _assignment_summary(assignment: dict[str, str]) -> str:
    return (
        f"query_shape={assignment['query_shape']} "
        f"x if_not_exists_clause="
        f"{assignment['if_not_exists_clause']} "
        f"x column_list_clause="
        f"{assignment['column_list_clause']} "
        f"x using_clause={assignment['using_clause']} "
        f"x storage_parameter_clause="
        f"{assignment['storage_parameter_clause']} "
        f"x tablespace_clause="
        f"{assignment['tablespace_clause']} "
        f"x data_clause={assignment['data_clause']} "
        f"x name_shape={assignment['name_shape']} "
        f"x column_type_coverage="
        f"{assignment['column_type_coverage']}"
    )


def build_create_materialized_view_factor_extension_plan(
    repository_root: Path,
) -> CreateMaterializedViewFactorExtensionPlan:
    """Build the bounded CREATE MATERIALIZED VIEW post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_materialized_view_factor_loop_plan(root)
    behaviors = _behavior_combinations() + _negative_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateMaterializedViewFactorExtensionCase] = []
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
                _derive_overlapping_factors(assignment)
                outcome, sqlstate, reason = _outcome_for(
                    assignment
                )
                ordinal += 1
                pair = _present_failure_pair(assignment)
                if pair is not None:
                    reason_suffix = (
                        f" x {pair[0]}={pair[1]}"
                    )
                else:
                    reason_suffix = ""
                cases.append(
                    CreateMaterializedViewFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATEMATERIALIZEDVIEW{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATEMATERIALIZEDVIEW{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"creatematerializedview_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CMATVIEW-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_materialized_view_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            + _assignment_summary(assignment)
                            + f" x verification_mode={verification}"
                            + f" x cleanup_mode={cleanup}"
                            + reason_suffix
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
    return CreateMaterializedViewFactorExtensionPlan(
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
    "CreateMaterializedViewFactorExtensionError",
    "CreateMaterializedViewFactorExtensionCase",
    "CreateMaterializedViewFactorExtensionPlan",
    "build_create_materialized_view_factor_extension_plan",
]
