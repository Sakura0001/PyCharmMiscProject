"""Bounded post-coverage cross-factor extension expander for ALTER GROUP.

The marginal factor-value-loop (:mod:`alter_group_factor_loop`) is the
required baseline: one program per factor value, 59 local cases.  This
module adds the bounded post-coverage extension phase allowed by
``alter_group.yaml`` ``post_coverage_extension_policy.enabled: true``:
cross-factor combinations of the positive T1-T4 behaviour axes (at most
one failure-causing value per case, so attribution stays clean), with
``verification_mode`` crossed and ``cleanup_mode`` rotated so every
declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
It does **not** emit the 2.7M cartesian interaction universe (that stays a
diagnostic-only resolver artifact); it emits only the at-most-one-failure
cross, which is the bounded, attributed subset.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_group_factor_loop import (
    _ACTION_BRANCH,
    _BASELINE_DEFAULTS,
    _BRANCH_DEPRECATED_EQUIVALENCE,
    _PRIVILEGE_INSUFFICIENT,
    _PRIVILEGE_SUFFICIENT,
    _SFV_FAILURE_SQLSTATE,
    build_alter_group_factor_loop_plan,
)


class AlterGroupFactorExtensionError(ValueError):
    """Raised when a frozen ALTER GROUP extension input drifts."""


@dataclass(frozen=True)
class AlterGroupFactorExtensionCase:
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
class AlterGroupFactorExtensionPlan:
    cases: tuple[AlterGroupFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 59
_CAP = 5000

_VERIFICATION_MODES = (
    "pg_auth_members_catalog",
    "pg_authid_catalog",
    "error_assertion",
)
_CLEANUP_MODES = (
    "revoke_membership",
    "grant_membership",
    "revert_rename",
    "drop_role",
)

# branch canonical value -> target action (inverse of the baseline map).
_BRANCH_ACTION = {branch: action for action, branch in _ACTION_BRANCH.items()}

# Crossed positive behaviour axes per branch.  multi_user / user_name_shape
# apply only to ADD/DROP USER; new_name_shape / rename_to_existing_name
# apply only to RENAME; duplicate_add_user is ADD-only; drop_non_member_user
# is DROP-only.  role_specification is NOT crossed: its keyword forms
# (CURRENT_ROLE/CURRENT_USER/SESSION_USER) always resolve to the *existing*
# current role, so they cannot produce the "group missing" (42704) failure
# that object_state/group_name_shape negatives predict -- those combos are
# semantically invalid.  The baseline owns all four role_specification
# values one-per-value, so the factor stays fully covered.  expected_status
# is NOT crossed (it is a meta flag derived from the failure-unit count).
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_add_user": {
        "multi_user": ("single_user", "multiple_users"),
        "group_name_shape": ("simple_id", "quoted_id", "nonexistent_name"),
        "user_name_shape": ("simple_id", "quoted_id", "nonexistent_user"),
        "privilege_level": ("group_role_admin", "non_admin", "superuser"),
        "user_existence": ("user_exists", "user_not_exists"),
        "object_state": ("exists", "not_exists"),
        "duplicate_add_user": ("new_member", "existing_member"),
    },
    "branch_drop_user": {
        "multi_user": ("single_user", "multiple_users"),
        "group_name_shape": ("simple_id", "quoted_id", "nonexistent_name"),
        "user_name_shape": ("simple_id", "quoted_id", "nonexistent_user"),
        "privilege_level": ("group_role_admin", "non_admin", "superuser"),
        "user_existence": ("user_exists", "user_not_exists"),
        "object_state": ("exists", "not_exists"),
        "drop_non_member_user": ("existing_member", "non_member"),
    },
    "branch_rename": {
        "new_name_shape": ("simple_id", "quoted_id", "duplicate_name"),
        "rename_to_existing_name": ("no_conflict", "same_name_conflict"),
        "group_name_shape": ("simple_id", "quoted_id", "nonexistent_name"),
        "privilege_level": ("group_role_admin", "non_admin", "superuser"),
        "object_state": ("exists", "not_exists"),
    },
}

# Crossed behaviour-negative (factor, value) pairs.  The privilege cluster
# (privilege_level=non_admin + its three derived members) is counted as a
# single unit, so only the primary signal is listed here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("group_name_shape", "nonexistent_name"),
        ("user_name_shape", "nonexistent_user"),
        ("user_existence", "user_not_exists"),
        ("new_name_shape", "duplicate_name"),
        ("rename_to_existing_name", "same_name_conflict"),
    }
)
_PRIVILEGE_CLUSTER_KEY = ("privilege_level", "non_admin")


def _apply_privilege_cluster(assignment: dict[str, str]) -> None:
    """Keep the four privilege factors consistent with the primary value."""

    if assignment["privilege_level"] == "non_admin":
        assignment.update(_PRIVILEGE_INSUFFICIENT)
    else:
        assignment.update(
            {k: v for k, v in _PRIVILEGE_SUFFICIENT.items() if k != "privilege_level"}
        )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + crossed behaviour negatives present."""

    cluster = 1 if assignment.get("privilege_level") == "non_admin" else 0
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    return cluster + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    if assignment.get("privilege_level") == "non_admin":
        return _PRIVILEGE_CLUSTER_KEY
    for pair in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(pair[0]) == pair[1]:
            return pair
    return None


def _behavior_combinations() -> list[dict[str, str]]:
    """Full 23-factor assignments (T6 at baseline) passing at-most-one-failure."""

    combos: list[dict[str, str]] = []
    for branch in ("branch_add_user", "branch_drop_user", "branch_rename"):
        axes = _BRANCH_AXES[branch]
        names = list(axes)
        for values in itertools.product(*(axes[name] for name in names)):
            assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
            assignment["statement_branch"] = branch
            assignment["alter_action"] = _BRANCH_ACTION[branch]
            assignment["deprecated_equivalence"] = _BRANCH_DEPRECATED_EQUIVALENCE[branch]
            for name, value in zip(names, values):
                assignment[name] = value
            _apply_privilege_cluster(assignment)
            unit = _failure_unit_count(assignment)
            if unit > 1:
                continue
            assignment["expected_status"] = "failure" if unit == 1 else "success"
            combos.append(assignment)
    return combos


def _outcome_for(assignment: dict[str, str]) -> tuple[str, str, str | None]:
    """Derive (outcome, expected_sqlstate, expected_failure_reason)."""

    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[AlterGroupFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-group-factor-extension-v1\n")
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
    cases: tuple[AlterGroupFactorExtensionCase, ...],
) -> str:
    """Emit the derived-extension ledger with the yaml required fields."""

    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER GROUP extension {case.ordinal:04d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_group_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER GROUP",
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


def build_alter_group_factor_extension_plan(
    repository_root: Path,
) -> AlterGroupFactorExtensionPlan:
    """Build the bounded ALTER GROUP post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_group_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    cases: list[AlterGroupFactorExtensionCase] = []
    ordinal = _BASELINE_COUNT
    raw = 0
    for behavior in behaviors:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                assignment: dict[str, str] = dict(behavior)
                assignment["verification_mode"] = verification
                assignment["cleanup_mode"] = cleanup
                outcome, sqlstate, reason = _outcome_for(assignment)
                ordinal += 1
                action = assignment["alter_action"]
                cases.append(
                    AlterGroupFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERGROUP{ordinal:04d}",
                        sql_filename=f"ALTERGROUP{ordinal:04d}.sql",
                        object_prefix=f"altergroup_{ordinal:04d}_",
                        derivation_id=(
                            f"AG-EXT|{ordinal:04d}|{action}|{verification}"
                            f"|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_group_core_syntax_and_state_baseline"
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
    if dropped:
        cases = cases[:_CAP]
    cases_tuple = tuple(cases)
    return AlterGroupFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterGroupFactorExtensionError",
    "AlterGroupFactorExtensionCase",
    "AlterGroupFactorExtensionPlan",
    "build_alter_group_factor_extension_plan",
]
