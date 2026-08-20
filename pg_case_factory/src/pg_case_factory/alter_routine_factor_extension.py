"""Bounded post-coverage cross-factor extension expander for ALTER ROUTINE.

The marginal factor-value-loop (:mod:`alter_routine_factor_loop`) is the
required baseline: one program per factor value, 115 local cases
(GRM 33 + SFV 80 + RISK 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the positive behaviour axes
with ``routine_type`` crossed (the key axis the generic wrapper adds over
its specialised siblings) and ``verification_mode``/``cleanup_mode`` crossed
so every declared T6 value is exercised.

At most one failure-causing value per case keeps attribution clean.  The
extension never replaces a required-baseline obligation.

SESSION_USER owner-transfer is **routine-type-aware** (the key gotcha):
``OWNER TO SESSION_USER`` escapes the membership wall when the resolved kind
is function/aggregate (PG 18.4 allows even for non-owners) but requires
membership when the resolved kind is procedure.  ``CURRENT_ROLE`` /
``CURRENT_USER`` always require membership under a non-superuser owner.
LEAKPROOF is superuser-only (42501); SECURITY DEFINER is owner-settable (no
wall).  DB phase verifies the per-kind behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_routine_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_routine_factor_loop_plan,
)


class AlterRoutineFactorExtensionError(ValueError):
    """Raised when a frozen ALTER ROUTINE extension input drifts."""


@dataclass(frozen=True)
class AlterRoutineFactorExtensionCase:
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
class AlterRoutineFactorExtensionPlan:
    cases: tuple[AlterRoutineFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 115
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_proc_catalog",
    "pg_aggregate_catalog",
    "effect_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_routine",
    "drop_function",
    "drop_procedure",
    "drop_aggregate",
    "reset_config_parameter",
)

# Action -> applicable routine kinds.  Volatility/leakproof/parallel/cost/rows
# are function+aggregate (not procedure).  SECURITY is function+procedure (not
# aggregate).  SET/RESET is function+procedure (not aggregate).  LEAKPROOF is
# function-only (aggregates do not support it).
_ACTION_ROUTINE_TYPES: dict[str, tuple[str, ...]] = {
    "security_invoker": ("function", "procedure"),
    "security_definer": ("function", "procedure"),
    "volatile": ("function", "aggregate"),
    "set_config_parameter": ("function", "procedure"),
    "leakproof": ("function",),
}

# Privilege cluster: both non-owner privilege levels model the same
# must_be_owner_of_routine (42501) boundary and are counted as one unit.
_PRIVILEGE_CLUSTER_VALUES = frozenset(
    {"non_owner_with_grant_option", "non_owner_no_privilege"}
)

_BRANCH_ACTION = "branch_action"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER_TO = "branch_owner_to"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_DEPENDS = "branch_depends_on_extension"

_BRANCH_GRAMMAR = {
    _BRANCH_ACTION: "branch_action_form",
    _BRANCH_RENAME: "branch_rename",
    _BRANCH_OWNER_TO: "branch_owner",
    _BRANCH_SET_SCHEMA: "branch_set_schema",
    _BRANCH_DEPENDS: "branch_depends_extension",
}

_BRANCH_FIXED_ACTION = {
    _BRANCH_RENAME: "rename",
    _BRANCH_OWNER_TO: "owner",
    _BRANCH_SET_SCHEMA: "set_schema",
    _BRANCH_DEPENDS: "depends_on_extension",
}

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_ACTION,
    "grammar_branch": "branch_action_form",
    "target_action": "security_invoker",
    "routine_type": "function",
    "routine_state": "exists",
    "expected_status": "success",
    "action_option": "security_invoker",
    "restrict_clause": "omitted",
    "routine_name_shape": "simple_name",
    "arg_signature": "no_args",
    "new_name_shape": "simple_name",
    "new_schema_shape": "existing_schema",
    "owner_to_shape": "explicit_role_name",
    "schema_change": "existing_schema",
    "extension_dependency": "depends_on_existing_extension",
    "executor_privilege": "superuser",
    "extension_dependency_state": "extension_exists",
    "verification_mode": "pg_proc_catalog",
    "cleanup_mode": "drop_routine",
    "set_assignment_form": "to_value",
    "external_keyword": "omitted",
    "depends_polarity": "depends",
    "action_list_cardinality": "one_action",
}

_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    _BRANCH_ACTION: {
        "target_action": (
            "security_invoker",
            "security_definer",
            "volatile",
            "set_config_parameter",
            "leakproof",
        ),
        "routine_type": ("function", "procedure", "aggregate"),
        "routine_state": ("exists", "non_existent"),
        "executor_privilege": (
            "superuser",
            "owner_of_routine",
            "non_owner_with_grant_option",
            "non_owner_no_privilege",
        ),
        "restrict_clause": ("omitted", "restrict"),
    },
    _BRANCH_RENAME: {
        "new_name_shape": ("simple_name", "quoted_name", "existing_name_conflict"),
        "routine_type": ("function", "procedure", "aggregate"),
        "routine_state": ("exists", "non_existent"),
        "executor_privilege": (
            "superuser",
            "owner_of_routine",
            "non_owner_with_grant_option",
            "non_owner_no_privilege",
        ),
    },
    _BRANCH_OWNER_TO: {
        "owner_to_shape": (
            "explicit_role_name",
            "current_role_keyword",
            "current_user_keyword",
            "session_user_keyword",
        ),
        "routine_type": ("function", "procedure", "aggregate"),
        "routine_state": ("exists", "non_existent"),
        "executor_privilege": (
            "superuser",
            "owner_of_routine",
            "non_owner_with_grant_option",
            "non_owner_no_privilege",
        ),
    },
    _BRANCH_SET_SCHEMA: {
        "schema_change": ("existing_schema", "nonexistent_schema"),
        "routine_type": ("function", "procedure", "aggregate"),
        "routine_state": ("exists", "non_existent"),
        "executor_privilege": (
            "superuser",
            "owner_of_routine",
            "non_owner_with_grant_option",
            "non_owner_no_privilege",
        ),
    },
    _BRANCH_DEPENDS: {
        "extension_dependency": (
            "depends_on_existing_extension",
            "no_depends_removing_dependency",
            "depends_on_nonexistent_extension",
        ),
        "routine_type": ("function", "procedure", "aggregate"),
        "routine_state": ("exists", "non_existent"),
        "executor_privilege": (
            "superuser",
            "owner_of_routine",
            "non_owner_with_grant_option",
            "non_owner_no_privilege",
        ),
    },
}

_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("routine_state", "non_existent"),
        ("new_name_shape", "existing_name_conflict"),
        ("schema_change", "nonexistent_schema"),
        ("extension_dependency", "depends_on_nonexistent_extension"),
    }
)


def _owner_target_requires_membership(
    routine_type: str, owner_to_shape: str
) -> bool:
    """Resolution-aware SESSION_USER escape (the key alter_routine gotcha).

    Returns True when the owner-transfer requires role membership under a
    non-superuser routine owner.  SESSION_USER escapes (False) when the
    resolved kind is function/aggregate; requires membership (True) when
    procedure.  CURRENT_ROLE / CURRENT_USER always require membership.
    explicit_role_name always requires membership (the target role is not
    the issuer).

    NOTE: this follows the task prompt's explicit design sentence.  It
    INVERTS both specialised siblings (alter_function: SESSION_USER requires
    membership for functions; alter_procedure: SESSION_USER escapes for
    procedures).  The DB phase verifies the per-kind behavior; the helper is
    trivially flippable if calibration inverts it.
    """

    if owner_to_shape == "explicit_role_name":
        return True
    if owner_to_shape in ("current_role_keyword", "current_user_keyword"):
        return True
    if owner_to_shape == "session_user_keyword":
        return routine_type == "procedure"
    return False


def _leakproof_wall_fires(assignment: dict[str, str]) -> bool:
    """LEAKPROOF is superuser-only (42501) under a non-superuser owner."""

    if assignment.get("target_action") != "leakproof":
        return False
    return assignment.get("executor_privilege") != "superuser"


def _owner_membership_wall_fires(
    assignment: dict[str, str],
) -> bool:
    """OWNER TO <role> membership wall under a non-superuser routine owner."""

    if assignment.get("executor_privilege") != "owner_of_routine":
        return False
    if assignment.get("target_action") != "owner":
        return False
    routine_type = assignment.get("routine_type", "function")
    owner_to_shape = assignment.get("owner_to_shape", "explicit_role_name")
    return _owner_target_requires_membership(routine_type, owner_to_shape)


def _privilege_cluster_fires(assignment: dict[str, str]) -> bool:
    """Non-owner privilege wall (42501 must_be_owner), except where shadowed."""

    level = assignment.get("executor_privilege")
    if level not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    return True


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + LEAKPROOF wall (1) + membership wall (1) + negatives."""

    cluster = 1 if _privilege_cluster_fires(assignment) else 0
    leakproof = 1 if _leakproof_wall_fires(assignment) else 0
    membership = 1 if _owner_membership_wall_fires(assignment) else 0
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    return cluster + leakproof + membership + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    if _leakproof_wall_fires(assignment):
        return ("target_action", "leakproof_under_routine_owner")
    if _owner_membership_wall_fires(assignment):
        return ("owner_to_shape", "membership_required_under_routine_owner")
    if _privilege_cluster_fires(assignment):
        level = assignment.get("executor_privilege")
        return ("executor_privilege", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Branch-local applicability + at-most-one-failure attribution."""

    action = assignment.get("target_action")
    routine_type = assignment.get("routine_type")
    if action in _ACTION_ROUTINE_TYPES:
        if routine_type not in _ACTION_ROUTINE_TYPES[action]:
            return False
    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, axes in _BRANCH_AXES.items():
        names = list(axes)
        for values in itertools.product(*(axes[name] for name in names)):
            assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = _BRANCH_GRAMMAR[branch]
            if branch != _BRANCH_ACTION:
                assignment["target_action"] = _BRANCH_FIXED_ACTION[branch]
            for name, value in zip(names, values):
                assignment[name] = value
            if not _is_valid_combination(assignment):
                continue
            unit = _failure_unit_count(assignment)
            assignment["expected_status"] = (
                "failure" if unit == 1 else "success"
            )
            combos.append(assignment)
    return combos


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    """Derive (outcome, expected_sqlstate, expected_failure_reason)."""

    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[AlterRoutineFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-routine-factor-extension-v1\n")
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
    cases: tuple[AlterRoutineFactorExtensionCase, ...],
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
                    f"ALTER ROUTINE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_routine_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER ROUTINE",
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


def build_alter_routine_factor_extension_plan(
    repository_root: Path,
) -> AlterRoutineFactorExtensionPlan:
    """Build the bounded ALTER ROUTINE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_routine_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterRoutineFactorExtensionCase] = []
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
                    AlterRoutineFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERROUTINE{ordinal:05d}",
                        sql_filename=f"ALTERROUTINE{ordinal:05d}.sql",
                        object_prefix=f"alterroutine_{ordinal:05d}_",
                        derivation_id=(
                            f"AR-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_routine_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: statement_branch="
                            f"{assignment['statement_branch']} "
                            f"routine_type={assignment['routine_type']} "
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
    return AlterRoutineFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterRoutineFactorExtensionError",
    "AlterRoutineFactorExtensionCase",
    "AlterRoutineFactorExtensionPlan",
    "build_alter_routine_factor_extension_plan",
]
