"""Bounded post-coverage cross-factor extension for CREATE SUBSCRIPTION.

The marginal factor-value-loop (:mod:`create_subscription_factor_loop`) is
the required baseline: one program per factor value, 55 local cases
(GRM 1 + SFV 54).  This module adds the bounded post-coverage extension
phase: cross-factor combinations of the positive T1-T4 behaviour axes,
with at most one failure-causing value per case so attribution stays
clean, and ``verification_mode`` crossed so every declared T6 value is
exercised.

CREATE SUBSCRIPTION requires superuser privilege, so
``executor_privilege=non_superuser`` is an unconditional failure.  The T5
single-value factors (duplicate_subscription_name, invalid_conninfo,
privilege_insufficient, publication_not_exists_on_remote,
replication_connection_failure) are derived from their T1-T4 counterparts,
not crossed as axes.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension``.
Filtering happens BEFORE counting, so ``raw_combination_count`` equals the
number of accepted combinations and ``dropped_count`` is 0 (no
over-pruning) unless the hard cap is hit.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .create_subscription_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    build_create_subscription_factor_loop_plan,
)


class CreateSubscriptionFactorExtensionError(ValueError):
    """Raised when a frozen CREATE SUBSCRIPTION extension input drifts."""


@dataclass(frozen=True)
class CreateSubscriptionFactorExtensionCase:
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
class CreateSubscriptionFactorExtensionPlan:
    cases: tuple[CreateSubscriptionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 55
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_subscription_catalog",
    "error_assertion",
)
_CLEANUP_MODES = ("drop_subscription",)

# General axes crossed for ALL groups.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "subscription_identity": (
        "not_exists",
        "exists",
        "quoted_duplicate",
        "reserved_word_name",
    ),
    "executor_privilege": ("superuser", "non_superuser"),
}

# Cross groups: each group crosses general axes + group-specific axes.
_CONNECTION_AXES: dict[str, tuple[str, ...]] = {
    "connection_info": ("minimal_conninfo", "valid_conninfo"),
    "conninfo_string_shape": (
        "valid_conninfo_string",
        "invalid_conninfo_string",
    ),
    "replication_connection": (
        "connection_available",
        "connection_unavailable",
    ),
}

_PUBLICATION_AXES: dict[str, tuple[str, ...]] = {
    "publication_list": ("single_publication", "multiple_publications"),
    "publication_name_shape": ("simple_name", "quoted_name"),
    "publication_dependency": (
        "publication_exists_on_remote",
        "publication_not_exists_on_remote",
    ),
}

_PARAMETER_AXES: dict[str, tuple[str, ...]] = {
    "with_parameter_clause": (
        "omitted",
        "binary_true",
        "connect_false_enabled_false",
        "connect_true_enabled_true",
        "copy_data_false",
        "copy_data_true",
        "create_slot_false",
        "disable_on_error_true",
        "failover_true",
        "multiple_parameters",
        "run_as_owner_true",
        "slot_name_explicit",
        "stream_true",
        "streaming_parallel_default",
        "synchronous_commit_on",
        "two_phase_true",
    ),
    "slot_name_behavior": (
        "default_auto_slot",
        "explicit_slot_name",
    ),
    "copy_data_behavior": ("copy_data_false", "copy_data_true"),
}

_NAME_AXES: dict[str, tuple[str, ...]] = {
    "subscription_name_shape": (
        "simple_name",
        "quoted_name",
        "reserved_word_name",
        "non_existing_name",
    ),
    "publication_name_shape": ("simple_name", "quoted_name"),
}

_SLOT_COPY_AXES: dict[str, tuple[str, ...]] = {
    "slot_name_behavior": ("default_auto_slot", "explicit_slot_name"),
    "copy_data_behavior": ("copy_data_false", "copy_data_true"),
    "connection_info": ("minimal_conninfo", "valid_conninfo"),
}

# Crossed behaviour-negative (factor, value) pairs — one representative per
# failure scenario.  T5 single-value factors are NOT listed here (they are
# derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("subscription_identity", "exists"),
        ("subscription_identity", "quoted_duplicate"),
        ("executor_privilege", "non_superuser"),
        ("conninfo_string_shape", "invalid_conninfo_string"),
        ("replication_connection", "connection_unavailable"),
        ("publication_dependency", "publication_not_exists_on_remote"),
    }
)

_COMBINATION_GROUP = "create_subscription_required_factor_value_matrix"

_CONSUMER_ACTION = "create_subscription"


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

    si = assignment.get("subscription_identity", "not_exists")
    sns = assignment.get("subscription_name_shape", "simple_name")
    if si in ("exists", "quoted_duplicate"):
        if sns == "non_existing_name":
            return False
    if si == "not_exists" and sns == "non_existing_name":
        return True
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    si = a.get("subscription_identity", "not_exists")
    ep = a.get("executor_privilege", "superuser")
    rc = a.get("replication_connection", "connection_available")
    cs = a.get("conninfo_string_shape", "valid_conninfo_string")
    pd = a.get("publication_dependency", "publication_exists_on_remote")

    if si in ("exists", "quoted_duplicate"):
        a["duplicate_subscription_name"] = "same_name_exists"
    else:
        a["duplicate_subscription_name"] = "same_name_exists"

    if ep == "non_superuser":
        a["privilege_insufficient"] = (
            "non_superuser_creating_subscription"
        )
    else:
        a["privilege_insufficient"] = (
            "non_superuser_creating_subscription"
        )

    if rc == "connection_unavailable":
        a["replication_connection_failure"] = "connection_refused"
    else:
        a["replication_connection_failure"] = "connection_refused"

    if cs == "invalid_conninfo_string":
        a["invalid_conninfo"] = "malformed_conninfo"
    else:
        a["invalid_conninfo"] = "malformed_conninfo"

    if pd == "publication_not_exists_on_remote":
        a["publication_not_exists_on_remote"] = (
            "remote_publication_not_exists"
        )
    else:
        a["publication_not_exists_on_remote"] = (
            "remote_publication_not_exists"
        )

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations(
    axes: dict[str, tuple[str, ...]],
) -> list[dict[str, str]]:
    """Full positive-axis assignments passing the filter."""

    keys = list(axes.keys())
    value_lists = [axes[k] for k in keys]
    combos: list[dict[str, str]] = []
    for values in itertools.product(*value_lists):
        assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
        for name, value in zip(keys, values):
            assignment[name] = value
        _derive_t5_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise CreateSubscriptionFactorExtensionError(
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
    cases: tuple[CreateSubscriptionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-subscription-factor-extension-v1\n"
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


_CROSS_GROUPS: tuple[tuple[str, dict[str, tuple[str, ...]]], ...] = (
    ("connection", _CONNECTION_AXES),
    ("publication", _PUBLICATION_AXES),
    ("parameter", _PARAMETER_AXES),
    ("name", _NAME_AXES),
    ("slot_copy", _SLOT_COPY_AXES),
)


def build_create_subscription_factor_extension_plan(
    repository_root: Path,
) -> CreateSubscriptionFactorExtensionPlan:
    """Build the bounded CREATE SUBSCRIPTION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_subscription_factor_loop_plan(root)
    cases: list[CreateSubscriptionFactorExtensionCase] = []
    raw = 0
    ordinal = _BASELINE_COUNT
    for group_name, group_axes in _CROSS_GROUPS:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(group_axes)
        behaviors = _behavior_combinations(all_axes)
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
                        CreateSubscriptionFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=(
                                f"CREATESUBSCRIPTION{ordinal:05d}"
                            ),
                            sql_filename=(
                                f"CREATESUBSCRIPTION{ordinal:05d}.sql"
                            ),
                            object_prefix=(
                                f"createsubscription_{ordinal:05d}_"
                            ),
                            derivation_id=(
                                f"CSUB-EXT|{ordinal:05d}|"
                                f"{verification}|{cleanup}|{group_name}"
                            ),
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                "cross-factor extension: "
                                f"group={group_name} "
                                f"x subscription_identity="
                                f"{assignment['subscription_identity']} "
                                f"x executor_privilege="
                                f"{assignment['executor_privilege']} "
                                f"x verification_mode="
                                f"{verification} "
                                f"x cleanup_mode={cleanup}"
                            ),
                            factor_assignment=tuple(
                                sorted(assignment.items())
                            ),
                            consumer_action_id=_CONSUMER_ACTION,
                            outcome=outcome,
                            expected_sqlstate=sqlstate,
                            expected_failure_reason=reason,
                            is_extension=True,
                        )
                    )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    expected_min = 1000 - _BASELINE_COUNT
    if len(cases_tuple) < expected_min:
        raise CreateSubscriptionFactorExtensionError(
            f"extension case count below threshold: {len(cases_tuple)}"
        )
    if len(cases_tuple) > _CAP:
        raise CreateSubscriptionFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in cases_tuple]
    if ordinals != list(
        range(
            _BASELINE_COUNT + 1,
            _BASELINE_COUNT + 1 + len(cases_tuple),
        )
    ):
        raise CreateSubscriptionFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in cases_tuple}) != len(cases_tuple):
        raise CreateSubscriptionFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in cases_tuple}) != len(
        cases_tuple
    ):
        raise CreateSubscriptionFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in cases_tuple
    ):
        raise CreateSubscriptionFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("CSUB-EXT|")
        for case in cases_tuple
    ):
        raise CreateSubscriptionFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return CreateSubscriptionFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(
            cases_tuple
        ),
        raw_combination_count=raw,
        dropped_combination_count=dropped,
    )


__all__ = [
    "CreateSubscriptionFactorExtensionError",
    "CreateSubscriptionFactorExtensionCase",
    "CreateSubscriptionFactorExtensionPlan",
    "build_create_subscription_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
