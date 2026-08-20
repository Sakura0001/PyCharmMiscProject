"""Bounded post-coverage extension plan for CREATE OPERATOR factor regress.

The baseline :mod:`create_operator_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE OPERATOR is a catalog row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_operator`` catalog row (not a ``pg_class`` relation) is
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
from .create_operator_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateOperatorFactorExtensionError(ValueError):
    """Raised when CREATE OPERATOR extension input drifts."""


@dataclass(frozen=True)
class CreateOperatorFactorExtensionCase:
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
class CreateOperatorFactorExtensionPlan:
    cases: tuple[CreateOperatorFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 56
_CAP = 20000

_VERIFICATION_MODES = ("catalog_query", "effect_query", "error_assertion")
_CLEANUP_MODES = ("drop_objects", "reset_state")

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "target_object_state": ("absent", "exists", "exists_conflict"),
    "operand_type_shape": ("binary_operator", "prefix_operator"),
    "privilege_context": ("schema_create_privilege", "insufficient_privilege"),
}

_CORE_CLAUSE_AXES: dict[str, tuple[str, ...]] = {
    "function_clause": ("function_keyword", "procedure_keyword"),
    "commutator_clause": ("absent", "present"),
    "negator_clause": ("absent", "present"),
}

_ESTIMATOR_CLAUSE_AXES: dict[str, tuple[str, ...]] = {
    "restrict_clause": ("absent", "present"),
    "join_clause": ("absent", "present"),
    "hashes_clause": ("absent", "present"),
    "merges_clause": ("absent", "present"),
}

_DEPENDENCY_AXES: dict[str, tuple[str, ...]] = {
    "dependency_state": ("ready", "missing_function", "wrong_signature"),
    "operator_type_compatibility": ("compatible", "incompatible"),
    "invalid_combination": ("none", "syntax_valid_semantic_error", "object_type_mismatch"),
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("target_object_state", "exists"),
        ("target_object_state", "exists_conflict"),
        ("privilege_context", "insufficient_privilege"),
        ("dependency_state", "missing_function"),
        ("dependency_state", "wrong_signature"),
        ("operator_type_compatibility", "incompatible"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("ownership_boundary", "non_privileged"),
    }
)

_COMBINATION_GROUP = "create_operator_required_factor_value_matrix"

_CONSUMER_ACTION = "define_operator"


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    ots = assignment.get("operand_type_shape", "binary_operator")
    expected_lac = (
        "absent_prefix_operator" if ots == "prefix_operator" else "present"
    )
    lac = assignment.get("leftarg_clause", expected_lac)
    if ots == "binary_operator" and lac == "absent_prefix_operator":
        return False
    if ots == "prefix_operator" and lac == "present":
        return False

    otc = assignment.get("operator_type_compatibility", "compatible")
    ic = assignment.get("invalid_combination", "none")
    if otc == "incompatible" and ic == "none":
        return False
    if otc == "compatible" and ic != "none":
        return False

    failures = [
        pair
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    ]
    return len(failures) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors from primary values."""

    ots = a.get("operand_type_shape", "binary_operator")
    if ots == "binary_operator":
        a["leftarg_clause"] = "present"
    elif ots == "prefix_operator":
        a["leftarg_clause"] = "absent_prefix_operator"

    lac = a.get("leftarg_clause", "present")
    if lac == "absent_prefix_operator":
        a["operand_type_shape"] = "prefix_operator"
    elif lac == "present" and ots == "prefix_operator":
        a["operand_type_shape"] = "binary_operator"

    pc = a.get("privilege_context", "schema_create_privilege")
    if pc == "insufficient_privilege":
        a["ownership_boundary"] = "non_privileged"
    ob = a.get("ownership_boundary", "schema_owner")
    if ob == "non_privileged":
        a["privilege_context"] = "insufficient_privilege"

    fns = a.get("function_name_shape", "plain_function")
    if fns == "missing_function":
        a["dependency_state"] = "missing_function"
    ds = a.get("dependency_state", "ready")
    if ds == "missing_function":
        a["function_name_shape"] = "missing_function"

    otc = a.get("operator_type_compatibility", "compatible")
    ic = a.get("invalid_combination", "none")
    if otc == "incompatible" and ic == "none":
        a["invalid_combination"] = "syntax_valid_semantic_error"
    if ic != "none" and otc == "compatible":
        a["operator_type_compatibility"] = "incompatible"

    tos = a.get("target_object_state", "absent")
    if tos in ("exists", "exists_conflict"):
        a["expected_status"] = "failure"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    tos = a.get("target_object_state", "absent")
    if tos in ("exists", "exists_conflict"):
        conditions.append("duplicate")
    ds = a.get("dependency_state", "ready")
    if ds == "missing_function":
        conditions.append("missing_function")
    if ds == "wrong_signature":
        conditions.append("wrong_signature")
    otc = a.get("operator_type_compatibility", "compatible")
    if otc == "incompatible":
        conditions.append("incompatible_types")
    ic = a.get("invalid_combination", "none")
    if ic != "none":
        conditions.append("invalid_definition")
    pc = a.get("privilege_context", "schema_create_privilege")
    if pc == "insufficient_privilege":
        conditions.append("insufficient_privilege")
    return conditions


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_operator_signature_provisional"),
    "missing_function": ("42883", "missing_operator_function_provisional"),
    "wrong_signature": ("42809", "wrong_operator_function_signature_provisional"),
    "incompatible_types": ("42809", "incompatible_operand_types_provisional"),
    "invalid_definition": ("42601", "invalid_operator_definition_provisional"),
    "insufficient_privilege": ("42501", "insufficient_operator_privilege_provisional"),
}


def _behavior_combinations(
    axes: dict[str, tuple[str, ...]],
) -> list[dict[str, str]]:
    """Cartesian product of given axes, filtered by consistency."""

    keys = list(axes.keys())
    value_lists = [axes[k] for k in keys]
    combos: list[dict[str, str]] = []
    for values in itertools.product(*value_lists):
        assignment = dict(zip(keys, values))
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
    _derive_overlapping_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _extension_multiset_sha256(
    cases: tuple[CreateOperatorFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-operator-factor-extension-v1\n"
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
    if tos in ("exists", "exists_conflict"):
        return ("target_object_state", tos)
    ds = a.get("dependency_state", "ready")
    if ds == "missing_function":
        return ("dependency_state", "missing_function")
    if ds == "wrong_signature":
        return ("dependency_state", "wrong_signature")
    otc = a.get("operator_type_compatibility", "compatible")
    if otc == "incompatible":
        return ("operator_type_compatibility", "incompatible")
    ic = a.get("invalid_combination", "none")
    if ic != "none":
        return ("invalid_combination", ic)
    pc = a.get("privilege_context", "schema_create_privilege")
    if pc == "insufficient_privilege":
        return ("privilege_context", "insufficient_privilege")
    return None


def build_create_operator_factor_extension_plan(
    repository_root: Path,
) -> CreateOperatorFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_operator")
    if len(catalog_rows) != 55:
        raise CreateOperatorFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateOperatorFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("core_clauses", _CORE_CLAUSE_AXES),
        ("estimator_clauses", _ESTIMATOR_CLAUSE_AXES),
        ("dependency", _DEPENDENCY_AXES),
    ]

    for group_name, behavior_axes in cross_groups:
        behavior_combos = _behavior_combinations(
            {**_GENERAL_AXES, **behavior_axes}
        )
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
                        f"COP-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        CreateOperatorFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"CREATEOPERATOR{ordinal:05d}",
                            sql_filename=f"CREATEOPERATOR{ordinal:05d}.sql",
                            object_prefix=f"createoperator_{ordinal:05d}_",
                            derivation_id=derivation_id,
                            derived_from_combination_group=_COMBINATION_GROUP,
                            derivation_reason=(
                                f"CREATE OPERATOR extension: "
                                f"group={group_name}, "
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

    plan = CreateOperatorFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateOperatorFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateOperatorFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))):
        raise CreateOperatorFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateOperatorFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateOperatorFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(case.outcome in ("success", "expected_failure") for case in plan.cases):
        raise CreateOperatorFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(case.derivation_id.startswith("COP-EXT|") for case in plan.cases):
        raise CreateOperatorFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateOperatorFactorExtensionError",
    "CreateOperatorFactorExtensionCase",
    "CreateOperatorFactorExtensionPlan",
    "build_create_operator_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
