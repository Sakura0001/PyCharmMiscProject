"""Bounded post-coverage extension plan for CREATE OPERATOR CLASS factor regress.

The baseline :mod:`create_operator_class_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE OPERATOR CLASS is a catalog row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_opclass`` catalog row (not a ``pg_class`` relation) is
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
from .create_operator_class_factor_loop import (
    _BASELINE_DEFAULTS,
    _DATA_TYPE_METHOD,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateOperatorClassFactorExtensionError(ValueError):
    """Raised when CREATE OPERATOR CLASS extension input drifts."""


@dataclass(frozen=True)
class CreateOperatorClassFactorExtensionCase:
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
class CreateOperatorClassFactorExtensionPlan:
    cases: tuple[CreateOperatorClassFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 54
_CAP = 20000

_VERIFICATION_MODES = ("catalog_query", "effect_query", "error_assertion")
_CLEANUP_MODES = ("drop_objects", "reset_state")

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "target_object_state": ("absent", "exists"),
    "privilege_context": (
        "superuser",
        "schema_create_privilege",
        "insufficient_privilege",
    ),
    "name_shape": ("plain_identifier", "schema_qualified"),
}

_BEHAVIOR_AXES: dict[str, tuple[str, ...]] = {
    "data_type_index_method": (
        "btree_integer",
        "hash_text",
        "gist_geometry",
    ),
    "operator_entry": (
        "for_search",
        "for_order_by",
        "with_op_type",
        "without_op_type",
    ),
    "storage_entry": (
        "absent",
        "present_gist",
        "present_gin",
        "present_spgist",
        "present_brin",
    ),
    "family_clause": (
        "absent_auto_created",
        "present_existing",
        "present_missing",
    ),
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("target_object_state", "exists"),
        ("privilege_context", "insufficient_privilege"),
        ("family_clause", "present_missing"),
    }
)

_COMBINATION_GROUP = "create_operator_class_required_factor_value_matrix"

_CONSUMER_ACTION = "create_with_entries"


def _is_storage_not_allowed(assignment: dict[str, str]) -> bool:
    """STORAGE clause with btree/hash method (not allowed)."""

    storage = assignment.get("storage_entry", "absent")
    method = assignment.get("data_type_index_method", "btree_integer")
    return storage != "absent" and method in (
        "btree_integer",
        "hash_text",
    )


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    failures = _failure_conditions(assignment)
    return len(failures) <= 1


def _failure_conditions(
    assignment: dict[str, str]
) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    if assignment.get("target_object_state") == "exists":
        conditions.append("duplicate")
    if assignment.get("privilege_context") == "insufficient_privilege":
        conditions.append("insufficient_privilege")
    if assignment.get("family_clause") == "present_missing":
        conditions.append("missing_family")
    if _is_storage_not_allowed(assignment):
        conditions.append("storage_not_allowed")
    return conditions


def _derive_boundary_factors(a: dict[str, str]) -> None:
    """Derive T4/T5 boundary factors from T1-T3 values in extension."""

    # storage + method -> index_method_compatibility
    if _is_storage_not_allowed(a):
        a["index_method_compatibility"] = (
            "storage_not_allowed_btree_hash"
        )
        a["invalid_combination"] = "syntax_valid_semantic_error"
    else:
        a["index_method_compatibility"] = "compatible"
        a["invalid_combination"] = "none"

    # data_type_index_method -> data_type_shape
    dtim = a.get("data_type_index_method", "btree_integer")
    _DTIM_TO_DTS = {
        "btree_integer": "integer",
        "hash_text": "text",
        "gist_geometry": "custom_type",
    }
    if dtim in _DTIM_TO_DTS:
        a["data_type_shape"] = _DTIM_TO_DTS[dtim]

    # family_clause -> dependency_state
    fc = a.get("family_clause", "absent_auto_created")
    if fc == "present_missing":
        a["dependency_state"] = "missing_family"
    else:
        a["dependency_state"] = "ready"

    # privilege_context -> ownership_boundary
    pc = a.get("privilege_context", "superuser")
    _PC_TO_OB = {
        "superuser": "superuser",
        "schema_create_privilege": "schema_owner",
        "insufficient_privilege": "non_privileged",
    }
    if pc in _PC_TO_OB:
        a["ownership_boundary"] = _PC_TO_OB[pc]


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_operator_class_provisional"),
    "insufficient_privilege": (
        "42501",
        "insufficient_privilege_provisional",
    ),
    "missing_family": ("42704", "missing_family_provisional"),
    "storage_not_allowed": (
        "42601",
        "storage_not_allowed_provisional",
    ),
}


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
    _derive_boundary_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _behavior_combinations() -> list[dict[str, str]]:
    """Cartesian product of general + behavior axes, filtered."""

    general_items = list(_GENERAL_AXES.items())
    behavior_items = list(_BEHAVIOR_AXES.items())

    all_keys = [k for k, _ in general_items] + [
        k for k, _ in behavior_items
    ]
    all_value_lists = (
        [v for _, v in general_items] + [v for _, v in behavior_items]
    )

    combos: list[dict[str, str]] = []
    for values in itertools.product(*all_value_lists):
        assignment = dict(zip(all_keys, values))
        if _is_valid_combination(assignment):
            combos.append(assignment)
    return combos


def _extension_multiset_sha256(
    cases: tuple[CreateOperatorClassFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-operator-class-factor-extension-v1\n"
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

    if a.get("target_object_state") == "exists":
        return ("target_object_state", "exists")
    if a.get("family_clause") == "present_missing":
        return ("family_clause", "present_missing")
    if a.get("privilege_context") == "insufficient_privilege":
        return ("privilege_context", "insufficient_privilege")
    if _is_storage_not_allowed(a):
        return ("index_method_compatibility", "storage_not_allowed_btree_hash")
    return None


def build_create_operator_class_factor_extension_plan(
    repository_root: Path,
) -> CreateOperatorClassFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_operator_class")
    if len(catalog_rows) != 53:
        raise CreateOperatorClassFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateOperatorClassFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    behavior_combos = _behavior_combinations()
    for behavior in behavior_combos:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw_count += 1
                full = _full_assignment(
                    behavior, verification, cleanup
                )
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
                    f"COPC-EXT|{ordinal:05d}|"
                    f"{verification}|{cleanup}"
                )
                cases.append(
                    CreateOperatorClassFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATEOPERATORCLASS{ordinal:05d}",
                        sql_filename=(
                            f"CREATEOPERATORCLASS{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createoperatorclass_{ordinal:05d}_"
                        ),
                        derivation_id=derivation_id,
                        derived_from_combination_group=_COMBINATION_GROUP,
                        derivation_reason=(
                            f"CREATE OPERATOR CLASS extension: "
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

    plan = CreateOperatorClassFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateOperatorClassFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateOperatorClassFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(
        range(
            _BASELINE_COUNT + 1,
            _BASELINE_COUNT + 1 + len(plan.cases),
        )
    ):
        raise CreateOperatorClassFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in plan.cases}) != len(
        plan.cases
    ):
        raise CreateOperatorClassFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(
        plan.cases
    ):
        raise CreateOperatorClassFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome == "success"
        or case.outcome == "expected_failure"
        for case in plan.cases
    ):
        raise CreateOperatorClassFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("COPC-EXT|")
        for case in plan.cases
    ):
        raise CreateOperatorClassFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateOperatorClassFactorExtensionError",
    "CreateOperatorClassFactorExtensionCase",
    "CreateOperatorClassFactorExtensionPlan",
    "build_create_operator_class_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
