"""Bounded post-coverage cross-factor extension expander for DROP POLICY.

The marginal factor-value-loop (:mod:`drop_policy_factor_loop`) is the
required baseline: one program per factor value, 48 local cases
(GRM 1 + SFV 45 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across the
single official synopsis branch (at most one failure-causing value per case,
so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_level=non_owner``,
``object_state=absent`` when ``if_exists_clause=absent``,
``table_existence=table_not_exists``) are crossed here with at-most-one-failure
attribution; the privilege boundary fires first (42501), then the table lookup
boundary (42P01), then the policy lookup boundary (42704).

The single official synopsis branch is crossed:

* ``branch_drop_policy`` — ``privilege_level`` x ``object_state`` x
  ``if_exists_clause`` x ``cascade_restrict`` x ``table_existence`` x
  ``last_policy_effect``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_policy_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_policy_factor_loop_plan,
)


class DropPolicyFactorExtensionError(ValueError):
    """Raised when a frozen DROP POLICY extension input drifts."""


@dataclass(frozen=True)
class DropPolicyFactorExtensionCase:
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
class DropPolicyFactorExtensionPlan:
    cases: tuple[DropPolicyFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 48
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_policy",
    "error_assertion",
    "notice_assertion",
    "rls_behavior_test",
)
_CLEANUP_MODES = (
    "disable_rls_drop_policy",
    "drop_table",
    "role_cleanup",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_level=non_owner, object_state=absent with if_exists_clause=absent,
# table_existence=table_not_exists) are crossed here with at-most-one-failure
# attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_policy",
    "grammar_branch": "branch_1",
    "target_action": "drop_policy",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "omitted",
    "last_policy_effect": "not_last_policy",
    "policy_name_shape": "simple_id",
    "table_name_shape": "simple_id",
    "privilege_level": "superuser",
    "rls_state": "rls_enabled",
    "table_existence": "table_exists",
    "nonexistent_policy": "policy_exists",
    "nonexistent_table": "table_exists",
    "privilege_denied": "owner_execution",
    "last_policy_default_deny": "other_policies_remain",
    "verification_mode": "catalog_query_pg_policy",
    "cleanup_mode": "disable_rls_drop_policy",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_policy": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_policy": "drop_policy",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_policy": {
        "privilege_level": (
            "non_owner",
            "superuser",
            "table_owner",
        ),
        "object_state": ("exists", "absent"),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict": ("cascade", "omitted", "restrict"),
        "table_existence": ("table_exists", "table_not_exists"),
        "last_policy_effect": (
            "not_last_policy",
            "last_policy_remaining",
            "table_has_multiple_policies",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> table
# lookup -> policy lookup).  The privilege boundary (42501) fires first.
# The table lookup boundary (42P01) fires when the host table does not exist.
# The policy lookup boundary (42704) fires when the policy is absent and IF
# EXISTS is omitted.  CASCADE/RESTRICT has no effect on policies (no
# dependent objects), so there is no 2BP01 dependency boundary.
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")
_TABLE_NEGATIVE = ("table_existence", "table_not_exists")
_POLICY_NEGATIVE = ("object_state", "absent")
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_level") == "non_owner"


def _table_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("table_existence") == "table_not_exists"


def _policy_failure_fires(assignment: dict[str, str]) -> bool:
    """object_state=absent fires only when IF EXISTS is omitted."""

    return (
        assignment.get("object_state") == "absent"
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _table_failure_fires(assignment):
        count += 1
    if _policy_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the table lookup, so it is
    attributed first.  The table lookup boundary (42P01) fires next when the
    host table does not exist.  The policy lookup boundary (42704) fires last
    when the policy is absent and IF EXISTS is omitted.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _table_failure_fires(assignment):
        return _TABLE_NEGATIVE
    if _policy_failure_fires(assignment):
        return _POLICY_NEGATIVE
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
    cases: tuple[DropPolicyFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-policy-factor-extension-v1\n")
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
    cases: tuple[DropPolicyFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP POLICY extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_policy_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP POLICY",
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


def build_drop_policy_factor_extension_plan(
    repository_root: Path,
) -> DropPolicyFactorExtensionPlan:
    """Build the bounded DROP POLICY post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_policy_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropPolicyFactorExtensionCase] = []
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
                    DropPolicyFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPPOLICY{ordinal:05d}",
                        sql_filename=f"DROPPOLICY{ordinal:05d}.sql",
                        object_prefix=f"droppolicy_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPPOLICY-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_policy_required_baseline_factor_space"
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
    return DropPolicyFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropPolicyFactorExtensionError",
    "DropPolicyFactorExtensionCase",
    "DropPolicyFactorExtensionPlan",
    "build_drop_policy_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
