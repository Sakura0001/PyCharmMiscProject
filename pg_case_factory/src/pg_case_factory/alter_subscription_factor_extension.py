"""Bounded post-coverage cross-factor extension expander for ALTER SUBSCRIPTION.

The marginal factor-value-loop (:mod:`alter_subscription_factor_loop`) is
the required baseline: one program per factor value, 81 local cases
(GRM 11 + SFV 70).  This module adds the bounded post-coverage extension
phase allowed by ``alter_subscription.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 11 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode`` crossed so every declared T6 value
is exercised.

ALTER SUBSCRIPTION requires superuser privilege on every branch, so
``executor_privilege=non_superuser`` is an unconditional failure.  The
T5 single-value factors (nonexistent_subscription,
privilege_insufficient, replication_connection_failure,
publication_not_exists_on_remote, disable_while_enabled,
drop_all_publications) are derived from their T1-T4 counterparts, not
crossed as axes.

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

from .alter_subscription_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_subscription_factor_loop_plan,
)


class AlterSubscriptionFactorExtensionError(ValueError):
    """Raised when a frozen ALTER SUBSCRIPTION extension input drifts."""


@dataclass(frozen=True)
class AlterSubscriptionFactorExtensionCase:
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
class AlterSubscriptionFactorExtensionPlan:
    cases: tuple[AlterSubscriptionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 81
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_subscription_catalog",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_subscription",
)

# General axes crossed for ALL 11 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "subscription_state": (
        "exists",
        "exists_enabled",
        "exists_disabled",
        "non_existent",
    ),
    "subscription_name_shape": (
        "simple_name",
        "quoted_name",
        "non_existent_name",
    ),
    "executor_privilege": ("superuser", "non_superuser"),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch are overridden per branch.
_BASELINE: dict[str, str] = {
    "subscription_state": "exists_enabled",
    "expected_status": "success",
    "publication_operation": "set_publication_single",
    "refresh_publication_option": "without_with_clause",
    "enable_disable_behavior": "enable_from_disabled",
    "subscription_parameter": "single_parameter",
    "skip_option": "skip_lsn",
    "owner_to_shape": "explicit_role_name",
    "rename_behavior": "rename_to_new_name",
    "connection_change": "valid_new_conninfo",
    "subscription_name_shape": "simple_name",
    "publication_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "conninfo_string_shape": "valid_conninfo",
    "executor_privilege": "superuser",
    "replication_connection": "connection_available",
    "publication_dependency": "publication_exists_on_remote",
    "verification_mode": "pg_subscription_catalog",
    "cleanup_mode": "drop_subscription",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_connection",
        "connection",
        {
            "connection_change": (
                "valid_new_conninfo",
                "invalid_new_conninfo",
            ),
            "conninfo_string_shape": (
                "valid_conninfo",
                "invalid_conninfo",
            ),
        },
    ),
    (
        "branch_set_publication",
        "set_publication",
        {
            "publication_operation": (
                "set_publication_single",
                "set_publication_multiple",
            ),
            "publication_name_shape": (
                "simple_name",
                "quoted_name",
            ),
        },
    ),
    (
        "branch_add_publication",
        "add_publication",
        {
            "publication_operation": (
                "add_publication_single",
                "add_publication_multiple",
            ),
            "publication_name_shape": (
                "simple_name",
                "quoted_name",
            ),
        },
    ),
    (
        "branch_drop_publication",
        "drop_publication",
        {
            "publication_operation": (
                "drop_publication_single",
                "drop_publication_multiple",
            ),
            "publication_name_shape": (
                "simple_name",
                "quoted_name",
            ),
        },
    ),
    (
        "branch_refresh_publication",
        "refresh_publication",
        {
            "refresh_publication_option": (
                "without_with_clause",
                "with_copy_data_true",
                "with_copy_data_false",
            ),
            "replication_connection": (
                "connection_available",
                "connection_unavailable",
            ),
            "publication_dependency": (
                "publication_exists_on_remote",
                "publication_not_exists_on_remote",
            ),
        },
    ),
    (
        "branch_enable",
        "enable",
        {
            "enable_disable_behavior": (
                "enable_from_disabled",
                "enable_already_enabled_no_effect",
            ),
            "replication_connection": (
                "connection_available",
                "connection_unavailable",
            ),
        },
    ),
    (
        "branch_disable",
        "disable",
        {
            "enable_disable_behavior": ("disable_from_enabled",),
        },
    ),
    (
        "branch_set_parameters",
        "set_parameters",
        {
            "subscription_parameter": (
                "single_parameter",
                "multiple_parameters",
                "synchronous_commit",
                "binary",
                "stream",
                "failover",
                "two_phase",
            ),
        },
    ),
    (
        "branch_skip",
        "skip",
        {
            "skip_option": ("skip_lsn",),
        },
    ),
    (
        "branch_owner_to",
        "owner_to",
        {
            "owner_to_shape": (
                "explicit_role_name",
                "current_role_keyword",
                "current_user_keyword",
                "session_user_keyword",
            ),
        },
    ),
    (
        "branch_rename",
        "rename",
        {
            "new_name_shape": (
                "simple_name",
                "quoted_name",
                "existing_name_conflict",
            ),
            "rename_behavior": (
                "rename_to_new_name",
                "rename_to_existing_name_conflict",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T5/T3 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("subscription_state", "non_existent"),
        ("executor_privilege", "non_superuser"),
        ("conninfo_string_shape", "invalid_conninfo"),
        ("publication_dependency", "publication_not_exists_on_remote"),
        ("replication_connection", "connection_unavailable"),
        ("rename_behavior", "rename_to_existing_name_conflict"),
    }
)


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

    ss = assignment.get("subscription_state", "exists_enabled")
    sns = assignment.get("subscription_name_shape", "simple_name")
    if ss == "non_existent" and sns != "non_existent_name":
        return False
    if ss != "non_existent" and sns == "non_existent_name":
        return False

    cc = assignment.get("connection_change")
    cs = assignment.get("conninfo_string_shape")
    if cc is not None and cs is not None:
        if cc == "invalid_new_conninfo" and cs != "invalid_conninfo":
            return False
        if cc != "invalid_new_conninfo" and cs == "invalid_conninfo":
            return False

    nns = assignment.get("new_name_shape")
    rb = assignment.get("rename_behavior")
    if nns is not None and rb is not None:
        conflict = nns == "existing_name_conflict"
        if conflict and rb != "rename_to_existing_name_conflict":
            return False
        if not conflict and rb == "rename_to_existing_name_conflict":
            return False

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    ss = a.get("subscription_state", "exists_enabled")
    sns = a.get("subscription_name_shape", "simple_name")
    ep = a.get("executor_privilege", "superuser")
    rc = a.get("replication_connection", "connection_available")
    pd = a.get("publication_dependency", "publication_exists_on_remote")
    cs = a.get("conninfo_string_shape", "valid_conninfo")
    cc = a.get("connection_change", "valid_new_conninfo")
    nns = a.get("new_name_shape", "simple_name")
    rb = a.get("rename_behavior", "rename_to_new_name")
    edb = a.get("enable_disable_behavior", "enable_from_disabled")
    po = a.get("publication_operation", "")

    if (
        ss == "non_existent"
        or sns == "non_existent_name"
    ):
        a["nonexistent_subscription"] = "subscription_does_not_exist"
    else:
        a["nonexistent_subscription"] = "subscription_does_not_exist"

    if ep == "non_superuser":
        a["privilege_insufficient"] = (
            "non_superuser_altering_subscription"
        )
    else:
        a["privilege_insufficient"] = (
            "non_superuser_altering_subscription"
        )

    if rc == "connection_unavailable":
        a["replication_connection_failure"] = (
            "connection_refused_on_refresh"
        )
    else:
        a["replication_connection_failure"] = (
            "connection_refused_on_refresh"
        )

    if pd == "publication_not_exists_on_remote":
        a["publication_not_exists_on_remote"] = (
            "remote_publication_not_exists"
        )
    else:
        a["publication_not_exists_on_remote"] = (
            "remote_publication_not_exists"
        )

    if cs == "invalid_conninfo" or cc == "invalid_new_conninfo":
        a["conninfo_string_shape"] = "invalid_conninfo"
        a["connection_change"] = "invalid_new_conninfo"

    if (
        nns == "existing_name_conflict"
        or rb == "rename_to_existing_name_conflict"
    ):
        a["new_name_shape"] = "existing_name_conflict"
        a["rename_behavior"] = "rename_to_existing_name_conflict"

    if edb == "disable_from_enabled":
        a["disable_while_enabled"] = "disable_active_subscription"
    else:
        a["disable_while_enabled"] = "disable_active_subscription"

    if po == "drop_publication_single":
        a["drop_all_publications"] = "dropping_last_publication"
    else:
        a["drop_all_publications"] = "dropping_last_publication"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


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
                raise AlterSubscriptionFactorExtensionError(
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
    cases: tuple[AlterSubscriptionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-subscription-factor-extension-v1\n"
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
    cases: tuple[AlterSubscriptionFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER SUBSCRIPTION extension "
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
                        "alter_subscription_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER SUBSCRIPTION",
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


def build_alter_subscription_factor_extension_plan(
    repository_root: Path,
) -> AlterSubscriptionFactorExtensionPlan:
    """Build the bounded ALTER SUBSCRIPTION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_subscription_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterSubscriptionFactorExtensionCase] = []
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
                    AlterSubscriptionFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"ALTERSUBSCRIPTION{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"ALTERSUBSCRIPTION{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"alter_subscription_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"ASUB-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_subscription_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x subscription_state="
                            f"{assignment['subscription_state']} "
                            f"x executor_privilege="
                            f"{assignment['executor_privilege']} "
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
    return AlterSubscriptionFactorExtensionPlan(
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
    "AlterSubscriptionFactorExtensionError",
    "AlterSubscriptionFactorExtensionCase",
    "AlterSubscriptionFactorExtensionPlan",
    "build_alter_subscription_factor_extension_plan",
]
