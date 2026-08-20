"""Bounded post-coverage cross-factor extension expander for SELECT INTO.

The marginal factor-value-loop (:mod:`select_into_factor_loop`) is the
required baseline: one program per factor value, 57 local cases (GRM 1 +
SFV 56).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the positive T1-T2 behaviour axes across the
single SELECT INTO synopsis branch, with at most one failure-causing value
per case so attribution stays clean, and ``verification_mode`` crossed so
every declared T6 value is exercised.

SELECT INTO is a DDL statement with one synopsis branch.  The T5 factors
(duplicate_table_name, privilege_insufficient, query_error,
schema_not_exists, reserved_schema_name) are derived from their T1-T4
counterparts, not crossed as axes.  The T3/T4 rotate-attach factors
(table_name_shape, column_name_shape, privilege_level,
source_table_dependency, schema_dependency) are covered in the baseline
and set to defaults in the extension.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension``.
Filtering happens BEFORE counting (``raw += 1``), so
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

from .select_into_factor_loop import (
    _BASELINE_DEFAULTS,
    _BRANCH_TO_TABLE_TYPE,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    _TABLE_TYPE_TO_BRANCH,
    _count_baseline_failures,
    _derive_overlapping_factors,
)


class SelectIntoFactorExtensionError(ValueError):
    """Raised when a frozen SELECT INTO extension input drifts."""


@dataclass(frozen=True)
class SelectIntoFactorExtensionCase:
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
    is_extension: bool = True


@dataclass(frozen=True)
class SelectIntoFactorExtensionPlan:
    cases: tuple[SelectIntoFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 57
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "SELECT_count",
    "information_schema_tables",
)
_CLEANUP_MODES = ("DROP_TABLE_IF_EXISTS",)

# General positive axes crossed for the single SELECT INTO branch.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "table_type": (
        "permanent",
        "temporary",
        "unlogged",
    ),
    "keyword_table": (
        "present",
        "absent",
    ),
    "query_shape": (
        "simple_select",
        "select_with_from_where",
        "select_with_join",
        "select_with_subquery",
        "select_with_aggregate",
    ),
    "with_clause": (
        "without_with",
        "with_simple",
        "with_recursive",
    ),
    "select_modifier": (
        "default",
        "ALL",
        "DISTINCT",
    ),
}

# Dense positive baseline (all success values).  statement_branch is
# overridden per table_type derivation.  SELECT INTO's success default for
# object_state is not_exists and for table_type is permanent.
_BASELINE: dict[str, str] = dict(_BASELINE_DEFAULTS)

# Crossed behaviour-negative (factor, value) pairs -- one representative
# per failure scenario.  SELECT INTO's positive axes carry no failure
# values, so this set is empty: every extension case is a success case.
_CROSSED_NEGATIVES: frozenset[tuple[str, str]] = frozenset()


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


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    names = list(_GENERAL_AXES)
    for values in itertools.product(
        *[_GENERAL_AXES[n] for n in names]
    ):
        assignment: dict[str, str] = dict(_BASELINE)
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_overlapping_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise SelectIntoFactorExtensionError(
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
    cases: tuple[SelectIntoFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"select-into-factor-extension-v1\n"
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
    cases: tuple[SelectIntoFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"SELECT INTO extension {case.ordinal:05d}: "
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
                        "select_into_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "SELECT INTO",
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


def build_select_into_factor_extension_plan(
    repository_root: Path,
) -> SelectIntoFactorExtensionPlan:
    """Build the bounded SELECT INTO post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    # Ensure the baseline plan compiles (invariant check).
    from .select_into_factor_loop import (
        build_select_into_factor_loop_plan,
    )
    build_select_into_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[SelectIntoFactorExtensionCase] = []
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
                cases.append(
                    SelectIntoFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"SELECTINTO{ordinal:05d}",
                        sql_filename=(
                            f"SELECTINTO{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"selectinto_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"SELECTINTO-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "select_into_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"table_type="
                            f"{assignment.get('table_type')} "
                            f"x keyword_table="
                            f"{assignment.get('keyword_table')} "
                            f"x query_shape="
                            f"{assignment.get('query_shape')} "
                            f"x with_clause="
                            f"{assignment.get('with_clause')} "
                            f"x select_modifier="
                            f"{assignment.get('select_modifier')} "
                            f"x verification_mode="
                            f"{verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment.get(
                            "target_action",
                            "select_into",
                        )
                        if "target_action" in assignment
                        else "select_into",
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return SelectIntoFactorExtensionPlan(
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
    "SelectIntoFactorExtensionError",
    "SelectIntoFactorExtensionCase",
    "SelectIntoFactorExtensionPlan",
    "build_select_into_factor_extension_plan",
]
