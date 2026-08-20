"""Bounded post-coverage extension plan for LISTEN factor regress.

The baseline :mod:`listen_factor_loop` assigns one local SQL program to
every ``SFV``/``GRM`` obligation (marginal 1:1, 42 local cases).  This
module crosses the main-axis factor values with verification/cleanup axes
under an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

LISTEN is a session-scoped statement that creates no tables, so the
bookend (``DROP TABLE IF EXISTS``) is never emitted.  The session listening
set (observable via ``pg_listening_channels()``) is the semantic witness
target.  LISTEN is permissive inside transactions, so the only crossed
negative is ``payload_shape=boundary_length`` (too-long channel name,
SQLSTATE ``08P01``); ``expected_status=failure`` is derived (forced by the
failure count) and is therefore not crossed.

The extension is deterministic: given the same repository root, it always
produces the same frozen multiset SHA-256 and the same contiguous case
ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .listen_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_listen_factor_loop_plan,
)


class ListenFactorExtensionError(ValueError):
    """Raised when LISTEN extension input drifts."""


@dataclass(frozen=True)
class ListenFactorExtensionCase:
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
class ListenFactorExtensionPlan:
    cases: tuple[ListenFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 42
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
    "session_state": (
        "default_state",
        "modified_state",
        "missing_channel_or_role",
        "restored_state",
    ),
    "privilege_context": (
        "owner",
        "granted_role",
        "insufficient_privilege",
    ),
}

_SCOPE_VALUE_AXES: dict[str, tuple[str, ...]] = {
    "scope_shape": (
        "session",
        "local",
        "all",
        "default_or_reset",
    ),
    "value_shape": (
        "valid_value",
        "default_value",
        "invalid_value",
        "list_or_identifier_value",
    ),
}

_NAME_PAYLOAD_AXES: dict[str, tuple[str, ...]] = {
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
        "alias_used",
    ),
    "payload_shape": (
        "absent",
        "short_text",
        "boundary_length",
        "invalid_payload",
    ),
}

_DEPENDENCY_INVALID_AXES: dict[str, tuple[str, ...]] = {
    "dependency_state": (
        "ready",
        "missing_dependency",
    ),
    "invalid_combination": (
        "none",
        "syntax_valid_semantic_error",
        "object_type_mismatch",
    ),
}

_TRANSACTION_AXES: dict[str, tuple[str, ...]] = {
    "transaction_visibility": (
        "outside_transaction",
        "inside_committed_transaction",
        "inside_rolled_back_transaction",
    ),
}

_SCOPE_NAME_AXES: dict[str, tuple[str, ...]] = {
    "scope_shape": (
        "session",
        "local",
        "all",
        "default_or_reset",
    ),
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
        "alias_used",
    ),
}

_VALUE_PAYLOAD_AXES: dict[str, tuple[str, ...]] = {
    "value_shape": (
        "valid_value",
        "default_value",
        "invalid_value",
        "list_or_identifier_value",
    ),
    "payload_shape": (
        "absent",
        "short_text",
        "boundary_length",
        "invalid_payload",
    ),
}

_DEPENDENCY_TRANSACTION_AXES: dict[str, tuple[str, ...]] = {
    "dependency_state": (
        "ready",
        "missing_dependency",
    ),
    "transaction_visibility": (
        "outside_transaction",
        "inside_committed_transaction",
        "inside_rolled_back_transaction",
    ),
}

_INVALID_TRANSACTION_AXES: dict[str, tuple[str, ...]] = {
    "invalid_combination": (
        "none",
        "syntax_valid_semantic_error",
        "object_type_mismatch",
    ),
    "transaction_visibility": (
        "outside_transaction",
        "inside_committed_transaction",
        "inside_rolled_back_transaction",
    ),
}

# Representative failure (factor, value) pairs -- one per failure scenario.
# expected_status is derived (forced by the failure count), not crossed, so
# it is NOT listed here (would double-count a single failure and break
# attribution).  The only crossed negative is the too-long channel name.
_CROSSED_NEGATIVES = frozenset(
    {
        ("payload_shape", "boundary_length"),
    }
)

_COMBINATION_GROUP = "listen_required_factor_value_matrix"

_CONSUMER_ACTION = "listen"


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
    """LISTEN has no transaction<->expected_status coupling."""

    # No-op: expected_status is forced by the failure count below.


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
    cases: tuple[ListenFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"listen-factor-extension-v1\n")
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


def build_listen_factor_extension_plan(
    repository_root: Path,
) -> ListenFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_listen_factor_loop_plan(root)

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("scope_value", _SCOPE_VALUE_AXES),
        ("name_payload", _NAME_PAYLOAD_AXES),
        ("dependency_invalid", _DEPENDENCY_INVALID_AXES),
        ("transaction_shape", _TRANSACTION_AXES),
        ("scope_name", _SCOPE_NAME_AXES),
        ("value_payload", _VALUE_PAYLOAD_AXES),
        ("dependency_transaction", _DEPENDENCY_TRANSACTION_AXES),
        ("invalid_transaction", _INVALID_TRANSACTION_AXES),
    ]

    cases: list[ListenFactorExtensionCase] = []
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
                        raise ListenFactorExtensionError(
                            "duplicate factor key in assignment"
                        )
                    outcome, sqlstate, reason = _outcome_for(full)
                    ordinal += 1
                    sorted_assignment = tuple(sorted(full.items()))
                    derivation_id = (
                        f"LISTEN-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        ListenFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"LISTEN{ordinal:05d}",
                            sql_filename=(
                                f"LISTEN{ordinal:05d}.sql"
                            ),
                            object_prefix=(
                                f"listen_{ordinal:05d}_"
                            ),
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"LISTEN extension: "
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

    plan = ListenFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise ListenFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise ListenFactorExtensionError(
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
        raise ListenFactorExtensionError("extension ordinal gap")
    if (
        len({case.case_id for case in plan.cases})
        != len(plan.cases)
    ):
        raise ListenFactorExtensionError(
            "duplicate extension case_id"
        )
    if (
        len({case.sql_filename for case in plan.cases})
        != len(plan.cases)
    ):
        raise ListenFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise ListenFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("LISTEN-EXT|")
        for case in plan.cases
    ):
        raise ListenFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "ListenFactorExtensionError",
    "ListenFactorExtensionCase",
    "ListenFactorExtensionPlan",
    "build_listen_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
