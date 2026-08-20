"""Bounded post-coverage cross-factor extension expander for REASSIGN OWNED.

The marginal factor-value-loop (:mod:`reassign_owned_factor_loop`) is the
required baseline: one program per factor value, 49 local cases (GRM 1 +
SFV 46 + Risk 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed
so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``executor_privilege=normal_user_no_privilege``,
``old_role_identity=role_not_exists``, ``new_role_identity=role_not_exists``)
are crossed here with at-most-one-failure attribution; the privilege boundary
fires first (42501), then the old-role-lookup boundary (42704), then the
new-role-lookup boundary (42704).

The single official synopsis branch is crossed:

* ``branch_reassign_owned`` — ``executor_privilege`` x ``old_role_identity`` x
  ``new_role_identity`` x ``old_role_shape`` x ``new_role_shape``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .reassign_owned_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_reassign_owned_factor_loop_plan,
)


class ReassignOwnedFactorExtensionError(ValueError):
    """Raised when a frozen REASSIGN OWNED extension input drifts."""


@dataclass(frozen=True)
class ReassignOwnedFactorExtensionCase:
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
class ReassignOwnedFactorExtensionPlan:
    cases: tuple[ReassignOwnedFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 49
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_owner_query",
    "pg_roles_catalog_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_owned_then_drop_role",
    "drop_role_cascade",
    "reassign_owned_then_drop_role",
)

# Dense baseline assignment (all positive values).  The negative factors
# (executor_privilege=normal_user_no_privilege,
# old_role_identity=role_not_exists,
# new_role_identity=role_not_exists) are crossed here with at-most-one-failure
# attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_reassign_owned",
    "grammar_branch": "branch_1",
    "target_action": "reassign_owned",
    "cleanup_mode": "reassign_owned_then_drop_role",
    "cross_database_limitation": "only_current_database_objects",
    "executor_privilege": "superuser",
    "expected_status": "success",
    "multi_old_role": "single_old_role",
    "new_role_identity": "role_exists",
    "new_role_shape": "explicit_role_name",
    "nonexistent_new_role": "new_role_does_not_exist",
    "nonexistent_old_role": "old_role_does_not_exist",
    "old_role_identity": "role_exists",
    "old_role_shape": "explicit_role_name",
    "owned_objects_state": "owns_tables",
    "privilege_insufficient": "non_superuser_reassigning_other_role",
    "quoted_identifier": "unquoted",
    "role_name_shape": "simple_name",
    "self_reassign": "same_role_no_effect",
    "verification_mode": "pg_class_owner_query",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_reassign_owned": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_reassign_owned": "reassign_owned",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_reassign_owned": {
        "executor_privilege": (
            "normal_user_no_privilege",
            "superuser",
            "createrole_privilege",
        ),
        "old_role_identity": (
            "role_exists",
            "role_is_current_user",
            "role_is_superuser",
            "role_not_exists",
        ),
        "new_role_identity": (
            "role_exists",
            "role_is_current_user",
            "role_not_exists",
        ),
        "old_role_shape": (
            "explicit_role_name",
            "current_role_keyword",
            "current_user_keyword",
            "session_user_keyword",
        ),
        "new_role_shape": (
            "explicit_role_name",
            "current_role_keyword",
            "current_user_keyword",
            "session_user_keyword",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> old lookup
# -> new lookup).  The privilege boundary (42501) fires first.  The
# old-role-lookup boundary (42704) fires when the source role does not exist.
# The new-role-lookup boundary (42704) fires when the destination role does not
# exist.  REASSIGN OWNED has no CASCADE/RESTRICT clause and no dependency
# boundary.
_PRIVILEGE_NEGATIVE = ("executor_privilege", "normal_user_no_privilege")
_OLD_ROLE_NOT_EXIST_NEGATIVE = ("old_role_identity", "role_not_exists")
_NEW_ROLE_NOT_EXIST_NEGATIVE = ("new_role_identity", "role_not_exists")


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("executor_privilege") == "normal_user_no_privilege"


def _old_role_not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("old_role_identity") == "role_not_exists"


def _new_role_not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("new_role_identity") == "role_not_exists"


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _old_role_not_exist_failure_fires(assignment):
        count += 1
    if _new_role_not_exist_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the role lookups, so it is
    attributed first.  The old-role-lookup boundary (42704) fires next when the
    source role does not exist.  The new-role-lookup boundary (42704) fires
    last when the destination role does not exist.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _old_role_not_exist_failure_fires(assignment):
        return _OLD_ROLE_NOT_EXIST_NEGATIVE
    if _new_role_not_exist_failure_fires(assignment):
        return _NEW_ROLE_NOT_EXIST_NEGATIVE
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
    cases: tuple[ReassignOwnedFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"reassign-owned-factor-extension-v1\n")
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
    cases: tuple[ReassignOwnedFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"REASSIGN OWNED extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "reassign_owned_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "REASSIGN OWNED",
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


def build_reassign_owned_factor_extension_plan(
    repository_root: Path,
) -> ReassignOwnedFactorExtensionPlan:
    """Build the bounded REASSIGN OWNED post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_reassign_owned_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[ReassignOwnedFactorExtensionCase] = []
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
                    ReassignOwnedFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"REASSIGNOWNED{ordinal:05d}",
                        sql_filename=f"REASSIGNOWNED{ordinal:05d}.sql",
                        object_prefix=f"reassignowned_{ordinal:05d}_",
                        derivation_id=(
                            f"REASSIGNOWNED-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "reassign_owned_declared_factor_baseline"
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
    return ReassignOwnedFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "ReassignOwnedFactorExtensionError",
    "ReassignOwnedFactorExtensionCase",
    "ReassignOwnedFactorExtensionPlan",
    "build_reassign_owned_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
