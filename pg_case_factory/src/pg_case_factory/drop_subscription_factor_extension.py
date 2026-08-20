"""Bounded post-coverage cross-factor extension expander for DROP SUBSCRIPTION.

The marginal factor-value-loop (drop_subscription_factor_loop) is the required
baseline: one program per factor value, 36 local cases (GRM 1 + SFV 33 +
RISK 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with verification_mode crossed and cleanup_mode crossed so
every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked is_extension = True.
The negative factors (privilege_context=non_superuser_no_privilege,
executor_privilege=non_superuser, subscription_existence=subscription_not_exists
when IF EXISTS is omitted, replication_slot_dependency=slot_exists under
RESTRICT) are crossed here with at-most-one-failure attribution; the privilege
boundary fires first (42501), then the subscription-lookup boundary (42704),
then the replication-slot boundary (2BP01).

The single official synopsis branch is crossed: branch_drop_subscription -
privilege_context x executor_privilege x subscription_existence x
if_exists_clause x cascade_restrict_clause x replication_slot_state x
subscription_name_shape x replication_slot_dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_subscription_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_subscription_factor_loop_plan,
)


class DropSubscriptionFactorExtensionError(ValueError):
    """Raised when a frozen DROP SUBSCRIPTION extension input drifts."""


@dataclass(frozen=True)
class DropSubscriptionFactorExtensionCase:
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
class DropSubscriptionFactorExtensionPlan:
    cases: tuple[DropSubscriptionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 36
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_subscription_catalog",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_subscription_cascade",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_context=non_superuser_no_privilege,
# executor_privilege=non_superuser, subscription_existence=
# subscription_not_exists / subscription_name_shape=non_existing_name
# when if_exists_clause=without_if_exists, replication_slot_dependency=
# slot_exists under RESTRICT) are crossed here with at-most-one-failure
# attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_subscription",
    "grammar_branch": "branch_1",
    "target_action": "drop_subscription",
    "subscription_existence": "subscription_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "privilege_context": "superuser",
    "replication_slot_state": "has_replication_slot",
    "subscription_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "replication_slot_dependency": "slot_exists",
    "nonexistent_subscription": "subscription_exists",
    "privilege_insufficient": "superuser_sufficient",
    "replication_slot_conflict": "cascade_with_slot_succeeds",
    "verification_mode": "pg_subscription_catalog",
    "cleanup_mode": "drop_subscription_cascade",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_subscription": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_subscription": "drop_subscription",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_subscription": {
        "privilege_context": (
            "non_superuser_no_privilege",
            "superuser",
        ),
        "executor_privilege": ("non_superuser", "superuser"),
        "subscription_existence": (
            "subscription_exists",
            "subscription_not_exists",
        ),
        "if_exists_clause": (
            "with_if_exists",
            "without_if_exists",
        ),
        "cascade_restrict_clause": (
            "cascade",
            "no_clause_default_restrict",
            "restrict",
        ),
        "replication_slot_state": (
            "has_replication_slot",
            "no_replication_slot",
        ),
        "subscription_name_shape": (
            "simple_name",
            "quoted_name",
            "reserved_word_name",
            "non_existing_name",
        ),
        "replication_slot_dependency": (
            "slot_exists",
            "slot_not_exists",
            "slot_on_remote_only",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege ->
# subscription lookup -> replication slot).  The privilege boundary (42501)
# fires first.  The subscription-lookup boundary (42704) fires when the
# subscription is absent (subscription_existence=subscription_not_exists or
# subscription_name_shape=non_existing_name) and IF EXISTS is omitted.  The
# replication-slot boundary (2BP01) fires when RESTRICT (or default RESTRICT)
# is used with an active slot (replication_slot_dependency=slot_exists).
_PRIVILEGE_CONTEXT_NEGATIVE = ("privilege_context", "non_superuser_no_privilege")
_EXECUTOR_PRIVILEGE_NEGATIVE = ("executor_privilege", "non_superuser")
_SUBSCRIPTION_MISSING_EXISTENCE = ("subscription_existence", "subscription_not_exists")
_SUBSCRIPTION_MISSING_NAME = ("subscription_name_shape", "non_existing_name")
_SLOT_CONFLICT_NEGATIVE = ("replication_slot_dependency", "slot_exists")
_RESTRICT_VALUES = frozenset({"no_clause_default_restrict", "restrict"})
_IF_EXISTS_OMITTED = "without_if_exists"


def _privilege_context_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_context") == "non_superuser_no_privilege"


def _executor_privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("executor_privilege") == "non_superuser"


def _subscription_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """subscription-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("subscription_existence") == "subscription_not_exists"
        or assignment.get("subscription_name_shape") == "non_existing_name"
    )


def _slot_conflict_failure_fires(assignment: dict[str, str]) -> bool:
    """slot conflict fires when RESTRICT (or default) with an active slot."""

    return (
        assignment.get("replication_slot_dependency") == "slot_exists"
        and assignment.get("cascade_restrict_clause") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_context_failure_fires(assignment):
        count += 1
    if _executor_privilege_failure_fires(assignment):
        count += 1
    if _subscription_missing_failure_fires(assignment):
        count += 1
    if _slot_conflict_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    if _privilege_context_failure_fires(assignment):
        return _PRIVILEGE_CONTEXT_NEGATIVE
    if _executor_privilege_failure_fires(assignment):
        return _EXECUTOR_PRIVILEGE_NEGATIVE
    if _subscription_missing_failure_fires(assignment):
        if assignment.get("subscription_existence") == "subscription_not_exists":
            return _SUBSCRIPTION_MISSING_EXISTENCE
        return _SUBSCRIPTION_MISSING_NAME
    if _slot_conflict_failure_fires(assignment):
        return _SLOT_CONFLICT_NEGATIVE
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, axes in _BRANCH_AXES.items():
        names = list(axes)
        for values in itertools.product(*(axes[name] for name in names)):
            assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = _BRANCH_GRAMMAR[branch]
            assignment["target_action"] = _BRANCH_FIXED_ACTION[branch]
            for name, value in zip(names, values):
                assignment[name] = value
            if not _is_valid_combination(assignment):
                continue
            pair = _present_failure_pair(assignment)
            assignment["expected_status"] = (
                "failure" if pair is not None else "success"
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
    cases: tuple[DropSubscriptionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-subscription-factor-extension-v1\n")
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(case.factor_assignment),
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": case.expected_failure_reason,
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
    cases: tuple[DropSubscriptionFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP SUBSCRIPTION extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_subscription_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP SUBSCRIPTION",
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
    return yaml.safe_dump(entries, sort_keys=False, allow_unicode=True)


def build_drop_subscription_factor_extension_plan(
    repository_root: Path,
) -> DropSubscriptionFactorExtensionPlan:
    """Build the bounded DROP SUBSCRIPTION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_subscription_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropSubscriptionFactorExtensionCase] = []
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
                action = assignment["target_action"]
                cases.append(
                    DropSubscriptionFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPSUBSCRIPTION{ordinal:05d}",
                        sql_filename=f"DROPSUBSCRIPTION{ordinal:05d}.sql",
                        object_prefix=f"dropsubscription_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPSUBSCRIPTION-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_subscription_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(sorted(assignment.items())),
                        consumer_action_id=action,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return DropSubscriptionFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropSubscriptionFactorExtensionError",
    "DropSubscriptionFactorExtensionCase",
    "DropSubscriptionFactorExtensionPlan",
    "build_drop_subscription_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
