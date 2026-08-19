"""Bounded post-coverage cross-factor extension expander for ALTER ROLE.

The marginal factor-value-loop (:mod:`alter_role_factor_loop`) is the
required baseline: one program per factor value, 108 local cases
(GRM 8 + SFV 98 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_role.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive behaviour axes (at most one failure-causing
value per case, so attribution stays clean), with ``verification_mode``
crossed and ``cleanup_mode`` rotated so every declared T6 value is
exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension``.

Privilege cluster: ``privilege_level`` is crossed with three CLEAN levels
-- ``superuser`` (success), ``createrole_without_admin_option`` and
``ordinary_role_other`` (both 42501) -- so the privilege wall fires as a
single attributable unit.  ``ordinary_role_self`` is deliberately NOT
crossed here: it is the self-password SUCCESS path (an ordinary role may
ALTER its OWN password without CREATEROLE), modelled one-per-value by the
baseline.  ``all_keyword`` crossed with a non-superuser is the
``all_roles_requires_superuser`` boundary, which surfaces as the SAME 42501
privilege failure (ALL needs superuser), so it adds no second failure unit.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_role_factor_loop import (
    _PRIVILEGE_PROFILE,
    _PRIVILEGE_SUFFICIENT,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    _ACTION_BRANCH,
    build_alter_role_factor_loop_plan,
)


class AlterRoleFactorExtensionError(ValueError):
    """Raised when a frozen ALTER ROLE extension input drifts."""


@dataclass(frozen=True)
class AlterRoleFactorExtensionCase:
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
class AlterRoleFactorExtensionPlan:
    cases: tuple[AlterRoleFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 108
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The
# exact frozen count is asserted in the companion test.
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_roles_catalog",
    "pg_settings_catalog",
    "pg_authid_catalog",
    "effect_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "reset_config_parameter",
    "drop_role",
    "revert_attribute_change",
)

# privilege_level values crossed in the extension.  ordinary_role_self is
# the self-password SUCCESS path and is excluded (owned one-per-value by the
# baseline).  createrole_with_admin_option is excluded because it is
# conditionally success/failure depending on the attribute (a CREATEROLE
# holder can set LOGIN but not SUPERUSER), which would muddy attribution.
_CROSSED_PRIVILEGE_LEVELS = (
    "superuser",
    "createrole_without_admin_option",
    "ordinary_role_other",
)

# Non-keyword role_name_shape values safe to cross with any privilege (they
# never self-target, so no contradiction with ordinary_role_other).
_SAFE_ROLE_NAME_SHAPES = ("simple_name", "quoted_name", "reserved_word_name")

# Crossed positive behaviour axes per branch.  T5 negatives are owned
# one-per-value by the baseline and are never crossed here, so the
# at-most-one-failure attribution stays clean.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_1_with_option": {
        "role_name_shape": _SAFE_ROLE_NAME_SHAPES,
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_2_rename": {
        "new_name_shape": (
            "simple_name",
            "quoted_name",
            "reserved_word_name",
            "existing_name_conflict",
        ),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_3_set_value": {
        "config_parameter_behavior": (
            "set_value",
            "set_default",
            "set_from_current",
        ),
        "database_name_shape": (
            "existing_database",
            "non_existent_database",
            "omitted_no_database_clause",
        ),
        "role_name_shape": ("simple_name", "all_keyword"),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_4_set_from_current": {
        "database_name_shape": (
            "existing_database",
            "non_existent_database",
            "omitted_no_database_clause",
        ),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_5_reset_parameter": {
        "database_name_shape": (
            "existing_database",
            "non_existent_database",
            "omitted_no_database_clause",
        ),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_6_reset_all": {
        "database_name_shape": (
            "existing_database",
            "non_existent_database",
            "omitted_no_database_clause",
        ),
        "role_name_shape": ("simple_name", "all_keyword"),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
}

# Crossed behaviour-negative (factor, value) pairs.  The privilege cluster
# (the two failure privilege levels) is counted as a single unit.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("new_name_shape", "existing_name_conflict"),
    }
)
_PRIVILEGE_FAILURE_LEVELS = frozenset(
    {"createrole_without_admin_option", "ordinary_role_other"}
)

# branch canonical value -> target action (inverse of the baseline map).
_BRANCH_ACTION = {branch: action for action, branch in _ACTION_BRANCH.items()}

# Dense baseline assignment (all positive T1-T4 + T6 + GRM-axis baselines).
_BASELINE_DEFAULTS: dict[str, str] = {
    "attribute_option": "login",
    "role_state": "exists",
    "expected_status": "success",
    "rename_behavior": "rename_to_new_name",
    "privilege_level": "superuser",
    "privilege_requirement": "superuser_required",
    "role_membership_dependency": "admin_option_granted",
    "role_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "config_parameter_shape": "valid_parameter",
    "database_name_shape": "omitted_no_database_clause",
    "table_column_index_involvement": "not_involved",
    "config_parameter_dependency": "settable_by_any_role",
    "verification_mode": "pg_roles_catalog",
    "cleanup_mode": "drop_role",
    "with_keyword": "absent",
    "encrypted_keyword": "omitted",
    "action_list_cardinality": "one_action",
    "set_assignment_form": "to_value",
}


def _apply_privilege_cluster(assignment: dict[str, str]) -> None:
    """Keep the privilege factors consistent with the crossed level."""

    level = assignment["privilege_level"]
    profile = _PRIVILEGE_PROFILE.get(("privilege_level", level))
    if profile is None:
        profile = _PRIVILEGE_SUFFICIENT
    assignment.update(profile)


def _privilege_fires(assignment: dict[str, str]) -> bool:
    """The privilege wall firing for the two failure levels.

    ordinary_role_self is the self-password SUCCESS path and is excluded.
    all_keyword + non-superuser is the all_roles_requires_superuser
    boundary, which surfaces as the SAME 42501 privilege failure (ALL needs
    superuser), so it is absorbed here rather than counted separately.
    """

    return assignment.get("privilege_level") in _PRIVILEGE_FAILURE_LEVELS


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + crossed behaviour negatives present."""

    cluster = 1 if _privilege_fires(assignment) else 0
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

    if _privilege_fires(assignment):
        return ("privilege_level", assignment["privilege_level"])
    for pair in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(pair[0]) == pair[1]:
            return pair
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """At-most-one-failure attribution."""

    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, axes in _BRANCH_AXES.items():
        names = list(axes)
        for values in itertools.product(*(axes[name] for name in names)):
            assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
            action = _BRANCH_ACTION[branch]
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = branch
            assignment["target_action"] = action
            assignment["config_parameter_behavior"] = _branch_default_behavior(
                action
            )
            for name, value in zip(names, values):
                assignment[name] = value
            _apply_privilege_cluster(assignment)
            if not _is_valid_combination(assignment):
                continue
            unit = _failure_unit_count(assignment)
            assignment["expected_status"] = (
                "failure" if unit == 1 else "success"
            )
            combos.append(assignment)
    return combos


def _branch_default_behavior(action: str) -> str:
    """The config_parameter_behavior baseline for the branch."""

    defaults = {
        "with_option": "set_value",
        "rename": "set_value",
        "set_value": "set_value",
        "set_from_current": "set_from_current",
        "reset_parameter": "reset_parameter",
        "reset_all": "reset_all",
    }
    return defaults[action]


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
    cases: tuple[AlterRoleFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-role-factor-extension-v1\n")
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
    cases: tuple[AlterRoleFactorExtensionCase, ...],
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
                    f"ALTER ROLE extension {case.ordinal:04d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_role_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER ROLE",
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


def build_alter_role_factor_extension_plan(
    repository_root: Path,
) -> AlterRoleFactorExtensionPlan:
    """Build the bounded ALTER ROLE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_role_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    # Stable sort so any cap truncation is deterministic.
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterRoleFactorExtensionCase] = []
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
                    AlterRoleFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERROLE{ordinal:04d}",
                        sql_filename=f"ALTERROLE{ordinal:04d}.sql",
                        object_prefix=f"alterrole_{ordinal:04d}_",
                        derivation_id=(
                            f"ALTERROLE-EXT|{ordinal:04d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_role_core_syntax_and_state_baseline"
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
    return AlterRoleFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterRoleFactorExtensionError",
    "AlterRoleFactorExtensionCase",
    "AlterRoleFactorExtensionPlan",
    "build_alter_role_factor_extension_plan",
]
