"""Bounded post-coverage cross-factor extension expander for REFRESH MATERIALIZED VIEW.

The marginal factor-value-loop
(:mod:`refresh_materialized_view_factor_loop`) is the required baseline:
one program per factor value, 38 local SFV cases.  This module adds the
bounded post-coverage extension phase: cross-factor combinations of the
positive behaviour axes across the single statement branch, with at
most one failure-causing unit per case so attribution stays clean, and
``verification_mode`` / ``cleanup_mode`` crossed so every declared T6
value is exercised.

REFRESH operates on a ``pg_class`` materialized-view relation
(``relkind='m'``).  Success-path cases CREATE a fixture source table and
materialized view as setup, so the bookend contract applies.  The
CONCURRENTLY restriction failures are *combination* failures
(concurrently_clause=present x unique_index_state / target_object_state
/ data_clause), detected in :func:`_failure_unit_count` so a single
failure is not double-counted.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .refresh_materialized_view_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_refresh_materialized_view_factor_loop_plan,
)


class RefreshMaterializedViewFactorExtensionError(ValueError):
    """Raised when a frozen extension input drifts."""


@dataclass(frozen=True)
class RefreshMaterializedViewFactorExtensionCase:
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
class RefreshMaterializedViewFactorExtensionPlan:
    cases: tuple[RefreshMaterializedViewFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 38
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

# General axes crossed for every case.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
    ),
    "privilege_context": (
        "owner",
        "granted_role",
        "maintain_privilege",
        "insufficient_privilege",
    ),
}

# Branch axes crossed for the single statement branch.
_BRANCH_AXES: dict[str, tuple[str, ...]] = {
    "target_object_state": (
        "exists_populated",
        "exists_unpopulated",
        "missing",
    ),
    "concurrently_clause": ("absent", "present"),
    "data_clause": ("with_data", "with_no_data"),
    "unique_index_state": (
        "has_unique_index",
        "no_unique_index",
    ),
}

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "target_object_state": "exists_populated",
    "expected_status": "success",
    "concurrently_clause": "absent",
    "data_clause": "with_data",
    "unique_index_state": "has_unique_index",
    "privilege_context": "owner",
    "name_shape": "plain_identifier",
    "dependency_state": "ready",
    "concurrently_restriction": "all_conditions_met",
    "invalid_combination": "none",
    "constraint_boundary": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}


def _failure_unit_count(a: dict[str, str]) -> int:
    """Count distinct failure units (at-most-one keeps attribution clean)."""

    count = 0
    tos = a.get("target_object_state")
    pc = a.get("privilege_context")
    cc = a.get("concurrently_clause")
    uis = a.get("unique_index_state")
    dc = a.get("data_clause")
    if tos == "missing":
        count += 1
    if pc == "insufficient_privilege":
        count += 1
    # Combination failures only apply when the matview exists.
    if tos != "missing" and cc == "present":
        if uis == "no_unique_index":
            count += 1
        if tos == "exists_unpopulated":
            count += 1
        if dc == "with_no_data":
            count += 1
    return count


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributed (factor, value) for a valid failure."""

    tos = a.get("target_object_state")
    pc = a.get("privilege_context")
    cc = a.get("concurrently_clause")
    uis = a.get("unique_index_state")
    dc = a.get("data_clause")
    if tos == "missing":
        return ("target_object_state", "missing")
    if pc == "insufficient_privilege":
        return ("privilege_context", "insufficient_privilege")
    if cc == "present" and uis == "no_unique_index":
        return ("concurrently_restriction", "no_unique_index")
    if cc == "present" and tos == "exists_unpopulated":
        return ("concurrently_restriction", "unpopulated_view")
    if cc == "present" and dc == "with_no_data":
        return ("concurrently_restriction", "with_no_data_conflict")
    return None


def _is_valid_combination(a: dict[str, str]) -> bool:
    return _failure_unit_count(a) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T4/T5 boundary factors and expected_status."""

    cc = a.get("concurrently_clause", "absent")
    uis = a.get("unique_index_state", "has_unique_index")
    tos = a.get("target_object_state", "exists_populated")
    dc = a.get("data_clause", "with_data")

    if tos == "missing":
        a["dependency_state"] = "missing_dependency"
    else:
        a["dependency_state"] = "ready"

    if tos != "missing" and cc == "present":
        if uis == "no_unique_index":
            a["concurrently_restriction"] = "no_unique_index"
            a["invalid_combination"] = "concurrently_without_unique_index"
        elif tos == "exists_unpopulated":
            a["concurrently_restriction"] = "unpopulated_view"
            a["invalid_combination"] = "none"
        elif dc == "with_no_data":
            a["concurrently_restriction"] = "with_no_data_conflict"
            a["invalid_combination"] = "concurrently_with_no_data"
        else:
            a["concurrently_restriction"] = "all_conditions_met"
            a["invalid_combination"] = "none"
    else:
        a["concurrently_restriction"] = "all_conditions_met"
        a["invalid_combination"] = "none"

    a["constraint_boundary"] = "none"
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments passing the at-most-one filter."""

    all_axes: dict[str, tuple[str, ...]] = {}
    all_axes.update(_GENERAL_AXES)
    all_axes.update(_BRANCH_AXES)
    names = list(all_axes)
    combos: list[dict[str, str]] = []
    for values in itertools.product(*[all_axes[n] for n in names]):
        assignment: dict[str, str] = dict(_BASELINE)
        assignment["statement_branch"] = "branch_1"
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_t5_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise RefreshMaterializedViewFactorExtensionError(
                "duplicate factor key in extension assignment"
            )
        combos.append(assignment)
    return combos


def _outcome_for(
    a: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(a)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[RefreshMaterializedViewFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"refreshmaterializedview-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(case.factor_assignment),
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
    cases: tuple[RefreshMaterializedViewFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    "REFRESH MATERIALIZED VIEW extension "
                    f"{case.ordinal:06d}: {case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": (
                        "refresh_materialized_view_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "REFRESH MATERIALIZED VIEW",
                    "primary_fence": "primary-target-begin/end",
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment["verification_mode"],
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


def build_refresh_materialized_view_factor_extension_plan(
    repository_root: Path,
) -> RefreshMaterializedViewFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_refresh_materialized_view_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[RefreshMaterializedViewFactorExtensionCase] = []
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
                    RefreshMaterializedViewFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"REFRESHMATERIALIZEDVIEW{ordinal:06d}"
                        ),
                        sql_filename=(
                            f"REFRESHMATERIALIZEDVIEW{ordinal:06d}.sql"
                        ),
                        object_prefix=(
                            f"refreshmaterializedview_{ordinal:06d}_"
                        ),
                        derivation_id=(
                            f"REFRESHMATERIALIZEDVIEW-EXT|{ordinal:06d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "refresh_materialized_view_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_object_state="
                            f"{assignment['target_object_state']} "
                            f"x concurrently_clause="
                            f"{assignment['concurrently_clause']} "
                            f"x privilege_context="
                            f"{assignment['privilege_context']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=(
                            "refresh_materialized_view_branch_1"
                        ),
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return RefreshMaterializedViewFactorExtensionPlan(
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
    "RefreshMaterializedViewFactorExtensionError",
    "RefreshMaterializedViewFactorExtensionCase",
    "RefreshMaterializedViewFactorExtensionPlan",
    "build_refresh_materialized_view_factor_extension_plan",
]
