"""Bounded post-coverage extension plan for SET TRANSACTION factor regress.

The baseline :mod:`set_transaction_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1, 44 local
cases).  This module crosses the main-axis factor values with
verification/cleanup axes under an at-most-one-failure attribution
policy, producing a bounded set of additional regress programs that
exercise pairwise factor interactions.

SET TRANSACTION is a session/transaction-scoped TCL statement that
creates no tables, so the bookend (``DROP TABLE IF EXISTS``) is never
emitted.  The transaction-characteristic GUC state (``transaction_isolation``,
``transaction_read_only``, ``transaction_deferrable``) is the semantic
witness target, observed via ``pg_catalog.pg_settings``.  SET
TRANSACTION's only declared failure trigger is the meta-declared
``expected_status=failure``, which is not a physical axis that combines
with others; the extension therefore carries no crossed negatives and
every extension case is a success.

The extension is deterministic: given the same repository root, it
always produces the same frozen multiset SHA-256 and the same contiguous
case ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .set_transaction_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_set_transaction_factor_loop_plan,
)


class SetTransactionFactorExtensionError(ValueError):
    """Raised when SET TRANSACTION extension input drifts."""


@dataclass(frozen=True)
class SetTransactionFactorExtensionCase:
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
class SetTransactionFactorExtensionPlan:
    cases: tuple[SetTransactionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 44
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "reset_state",
    "rollback",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "transaction_state": (
        "outside_transaction",
        "inside_transaction",
        "savepoint_exists",
        "prepared_transaction_exists",
        "missing_required_state",
    ),
}

_MODE_CHAIN_AXES: dict[str, tuple[str, ...]] = {
    "transaction_mode": (
        "default",
        "isolation_level",
        "read_write",
        "read_only",
        "deferrable",
    ),
    "chain_behavior": (
        "none",
        "and_chain",
        "and_no_chain",
    ),
}

_ID_SAVEPOINT_AXES: dict[str, tuple[str, ...]] = {
    "transaction_id_shape": (
        "simple_id",
        "quoted_id",
        "missing_id",
        "duplicate_id",
    ),
    "savepoint_name_shape": (
        "simple_name",
        "quoted_name",
        "missing_name",
        "released_name",
    ),
}

_ENV_FRAMEWORK_AXES: dict[str, tuple[str, ...]] = {
    "environment_context": (
        "normal_session",
        "transaction_block",
        "outside_transaction_required",
        "external_resource_required",
    ),
    "framework_context": (
        "no_outer_transaction",
        "outer_transaction_present",
    ),
}

_INVALID_BOUNDARY_AXES: dict[str, tuple[str, ...]] = {
    "invalid_combination": (
        "none",
        "syntax_valid_semantic_error",
        "object_type_mismatch",
    ),
    "state_boundary": (
        "no_open_transaction",
        "nested_savepoint",
        "prepared_transaction_leftover",
    ),
}

_MODE_ID_AXES: dict[str, tuple[str, ...]] = {
    "transaction_mode": (
        "default",
        "isolation_level",
        "read_write",
        "read_only",
        "deferrable",
    ),
    "transaction_id_shape": (
        "simple_id",
        "quoted_id",
        "missing_id",
        "duplicate_id",
    ),
}

_CHAIN_SAVEPOINT_AXES: dict[str, tuple[str, ...]] = {
    "chain_behavior": (
        "none",
        "and_chain",
        "and_no_chain",
    ),
    "savepoint_name_shape": (
        "simple_name",
        "quoted_name",
        "missing_name",
        "released_name",
    ),
}

_ENV_INVALID_AXES: dict[str, tuple[str, ...]] = {
    "environment_context": (
        "normal_session",
        "transaction_block",
        "outside_transaction_required",
        "external_resource_required",
    ),
    "invalid_combination": (
        "none",
        "syntax_valid_semantic_error",
        "object_type_mismatch",
    ),
}

_FRAMEWORK_BOUNDARY_AXES: dict[str, tuple[str, ...]] = {
    "framework_context": (
        "no_outer_transaction",
        "outer_transaction_present",
    ),
    "state_boundary": (
        "no_open_transaction",
        "nested_savepoint",
        "prepared_transaction_leftover",
    ),
}

# SET TRANSACTION's only declared failure trigger is the meta-declared
# expected_status=failure, which is derived (not crossed).  There are
# therefore no crossed physical negatives; every extension combination
# is a success.
_CROSSED_NEGATIVES: frozenset[tuple[str, str]] = frozenset()

_COMBINATION_GROUP = "set_transaction_required_factor_value_matrix"

_CONSUMER_ACTION = "set_transaction"


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


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Reconcile expected_status with the declared failure surface."""

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


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
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"
    return a


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[SetTransactionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"set-transaction-factor-extension-v1\n")
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


def build_set_transaction_factor_extension_plan(
    repository_root: Path,
) -> SetTransactionFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_set_transaction_factor_loop_plan(root)

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("mode_chain", _MODE_CHAIN_AXES),
        ("id_savepoint", _ID_SAVEPOINT_AXES),
        ("env_framework", _ENV_FRAMEWORK_AXES),
        ("invalid_boundary", _INVALID_BOUNDARY_AXES),
        ("mode_id", _MODE_ID_AXES),
        ("chain_savepoint", _CHAIN_SAVEPOINT_AXES),
        ("env_invalid", _ENV_INVALID_AXES),
        ("framework_boundary", _FRAMEWORK_BOUNDARY_AXES),
    ]

    cases: list[SetTransactionFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    for group_name, behavior_axes in cross_groups:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(behavior_axes)
        behavior_combos = _behavior_combinations(all_axes)
        for behavior in behavior_combos:
            for verification in _VERIFICATION_MODES:
                for cleanup in _CLEANUP_MODES:
                    raw_count += 1
                    full = _full_assignment(
                        behavior, verification, cleanup
                    )
                    if not _is_valid_combination(full):
                        continue
                    if len(full) != len(set(full)):
                        raise SetTransactionFactorExtensionError(
                            "duplicate factor key in assignment"
                        )
                    outcome, sqlstate, reason = _outcome_for(full)
                    ordinal += 1
                    sorted_assignment = tuple(sorted(full.items()))
                    derivation_id = (
                        f"SETTRANSACTION-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        SetTransactionFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"SETTRANSACTION{ordinal:05d}",
                            sql_filename=(
                                f"SETTRANSACTION{ordinal:05d}.sql"
                            ),
                            object_prefix=(
                                f"settransaction_{ordinal:05d}_"
                            ),
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"SET TRANSACTION extension: "
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

    plan = SetTransactionFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise SetTransactionFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise SetTransactionFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    expected_ordinals = list(
        range(
            _BASELINE_COUNT + 1,
            _BASELINE_COUNT + 1 + len(plan.cases),
        )
    )
    if ordinals != expected_ordinals:
        raise SetTransactionFactorExtensionError("extension ordinal gap")
    if (
        len({case.case_id for case in plan.cases})
        != len(plan.cases)
    ):
        raise SetTransactionFactorExtensionError(
            "duplicate extension case_id"
        )
    if (
        len({case.sql_filename for case in plan.cases})
        != len(plan.cases)
    ):
        raise SetTransactionFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise SetTransactionFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("SETTRANSACTION-EXT|")
        for case in plan.cases
    ):
        raise SetTransactionFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "SetTransactionFactorExtensionError",
    "SetTransactionFactorExtensionCase",
    "SetTransactionFactorExtensionPlan",
    "build_set_transaction_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
