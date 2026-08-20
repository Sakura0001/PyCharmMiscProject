"""Bounded post-coverage extension plan for CREATE OPERATOR FAMILY factor regress.

The baseline :mod:`create_operator_family_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE OPERATOR FAMILY is a catalog row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_opfamily`` catalog row (not a ``pg_class`` relation) is
the semantic witness target.

The extension is deterministic: given the same repository root, it always
produces the same frozen multiset SHA-256 and the same contiguous case
ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_operator_family_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateOperatorFamilyFactorExtensionError(ValueError):
    """Raised when CREATE OPERATOR FAMILY extension input drifts."""


@dataclass(frozen=True)
class CreateOperatorFamilyFactorExtensionCase:
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
class CreateOperatorFamilyFactorExtensionPlan:
    cases: tuple[CreateOperatorFamilyFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 31
_CAP = 20000

_VERIFICATION_MODES = ("catalog_query", "effect_query", "error_assertion")
_CLEANUP_MODES = ("drop_objects", "reset_state")

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "target_object_state": ("absent", "exists", "exists_conflict"),
    "privilege_context": (
        "superuser",
        "schema_create_privilege",
        "insufficient_privilege",
    ),
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
    ),
}

_BRANCH_AXES: dict[str, tuple[str, ...]] = {
    "index_method_shape": ("btree", "hash", "gist", "gin", "spgist", "brin"),
    "dependency_state": ("ready", "missing_dependency"),
    "invalid_combination": ("none", "syntax_valid_semantic_error"),
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("target_object_state", "exists"),
        ("target_object_state", "exists_conflict"),
        ("privilege_context", "insufficient_privilege"),
        ("dependency_state", "missing_dependency"),
        ("invalid_combination", "syntax_valid_semantic_error"),
    }
)

_COMBINATION_GROUP = "create_operator_family_required_factor_value_matrix"

_CONSUMER_ACTION = "create_opfamily"


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    failures = [
        pair
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    ]
    return len(failures) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive boundary factors from primary values in extension."""

    tos = a.get("target_object_state", "absent")
    if tos in ("exists", "exists_conflict"):
        a["expected_status"] = "failure"
    else:
        a["expected_status"] = "success"

    priv = a.get("privilege_context", "superuser")
    if priv == "insufficient_privilege":
        a["ownership_boundary"] = "non_privileged"
    else:
        a["ownership_boundary"] = priv


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    tos = a.get("target_object_state", "absent")
    if tos in ("exists", "exists_conflict"):
        conditions.append("duplicate")
    if a.get("dependency_state") == "missing_dependency":
        conditions.append("missing_schema")
    if a.get("invalid_combination") == "syntax_valid_semantic_error":
        conditions.append("invalid_am")
    if a.get("privilege_context") == "insufficient_privilege":
        conditions.append("insufficient_privilege")
    return conditions


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_operator_family_provisional"),
    "missing_schema": ("3F000", "invalid_schema_name_provisional"),
    "invalid_am": ("42704", "undefined_access_method_provisional"),
    "insufficient_privilege": (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _behavior_combinations() -> list[dict[str, str]]:
    """Cartesian product of general + branch axes, filtered."""

    general_items = list(_GENERAL_AXES.items())
    branch_items = list(_BRANCH_AXES.items())

    all_keys = [k for k, _ in general_items] + [k for k, _ in branch_items]
    all_value_lists = (
        [v for _, v in general_items] + [v for _, v in branch_items]
    )

    combos: list[dict[str, str]] = []
    for values in itertools.product(*all_value_lists):
        assignment = dict(zip(all_keys, values))
        if _is_valid_combination(assignment):
            combos.append(assignment)
    return combos


def _full_assignment(
    behavior: dict[str, str],
    verification: str,
    cleanup: str,
) -> dict[str, str]:
    a: dict[str, str] = dict(_BASELINE_DEFAULTS)
    for key, value in behavior.items():
        a[key] = value
    a["verification_mode"] = verification
    a["cleanup_mode"] = cleanup
    _derive_t5_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _extension_multiset_sha256(
    cases: tuple[CreateOperatorFamilyFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-operator-family-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "ordinal": case.ordinal,
                    "case_id": case.case_id,
                    "derivation_id": case.derivation_id,
                    "derived_from_combination_group": (
                        case.derived_from_combination_group
                    ),
                    "derivation_reason": case.derivation_reason,
                    "factor_assignment": [
                        list(item) for item in case.factor_assignment
                    ],
                    "consumer_action_id": case.consumer_action_id,
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": (
                        case.expected_failure_reason
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    tos = a.get("target_object_state", "absent")
    if tos == "exists":
        return ("target_object_state", "exists")
    if tos == "exists_conflict":
        return ("target_object_state", "exists_conflict")
    if a.get("dependency_state") == "missing_dependency":
        return ("dependency_state", "missing_dependency")
    if a.get("invalid_combination") == "syntax_valid_semantic_error":
        return ("invalid_combination", "syntax_valid_semantic_error")
    if a.get("privilege_context") == "insufficient_privilege":
        return ("privilege_context", "insufficient_privilege")
    return None


def build_create_operator_family_factor_extension_plan(
    repository_root: Path,
) -> CreateOperatorFamilyFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_operator_family")
    if len(catalog_rows) != 30:
        raise CreateOperatorFamilyFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateOperatorFamilyFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    for behavior in _behavior_combinations():
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw_count += 1
                full = _full_assignment(behavior, verification, cleanup)
                failures = _failure_conditions(full)
                if len(failures) > 1:
                    continue
                if failures:
                    condition = failures[0]
                    sqlstate, reason = _FAILURE_SQLSTATE[condition]
                    outcome = "expected_failure"
                else:
                    sqlstate = "00000"
                    reason = None
                    outcome = "success"
                ordinal += 1
                sorted_assignment = tuple(sorted(full.items()))
                derivation_id = (
                    f"COF-EXT|{ordinal:05d}|"
                    f"{verification}|{cleanup}"
                )
                cases.append(
                    CreateOperatorFamilyFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATEOPERATORFAMILY{ordinal:05d}",
                        sql_filename=(
                            f"CREATEOPERATORFAMILY{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createoperatorfamily_{ordinal:05d}_"
                        ),
                        derivation_id=derivation_id,
                        derived_from_combination_group=_COMBINATION_GROUP,
                        derivation_reason=(
                            f"CREATE OPERATOR FAMILY extension: "
                            f"verification={verification}, "
                            f"cleanup={cleanup}"
                        ),
                        factor_assignment=sorted_assignment,
                        consumer_action_id=_CONSUMER_ACTION,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                    )
                )

    dropped = max(0, raw_count - _CAP)
    if dropped > 0:
        cases = cases[: _CAP]

    plan = CreateOperatorFamilyFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateOperatorFamilyFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateOperatorFamilyFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(
        range(
            _BASELINE_COUNT + 1,
            _BASELINE_COUNT + 1 + len(plan.cases),
        )
    ):
        raise CreateOperatorFamilyFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateOperatorFamilyFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateOperatorFamilyFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome == "success" or case.outcome == "expected_failure"
        for case in plan.cases
    ):
        raise CreateOperatorFamilyFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("COF-EXT|")
        for case in plan.cases
    ):
        raise CreateOperatorFamilyFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateOperatorFamilyFactorExtensionError",
    "CreateOperatorFamilyFactorExtensionCase",
    "CreateOperatorFamilyFactorExtensionPlan",
    "build_create_operator_family_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
