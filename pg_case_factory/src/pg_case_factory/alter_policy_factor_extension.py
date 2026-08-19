"""Bounded post-coverage cross-factor extension expander for ALTER POLICY.

The marginal factor-value-loop (:mod:`alter_policy_factor_loop`) is the
required baseline: one program per factor value, 72 local cases (GRM 2 +
SFV 68 + RISK 2).  This module adds the bounded post-coverage extension
phase allowed by ``alter_policy.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive behaviour axes (``policy_name_shape``,
``table_name_shape``, ``privilege_level``, ``rls_enabled``) across all
five ``alter_action`` forms, with each action's signature sub-axis
crossed where it is observable (``new_name_shape`` for ``rename``,
``using_expression`` for ``modify_using``, ``with_check_expression`` for
``modify_with_check``, ``role_target`` for ``modify_roles``), at most one
failure-causing value per case so attribution stays clean, with
``verification_mode`` crossed and ``cleanup_mode`` crossed so every
declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.

``rls_not_enabled`` is NOT a failure for ALTER POLICY (the policy
definition can be altered with RLS off), so it is a success-variant axis
counted in the cross.  The privilege cluster (``privilege_level =
non_owner``) models the must_be_owner (42501) boundary and is counted as
a single attributable failure unit; the at-most-one-failure filter
excludes any combination where it co-occurs with a behaviour negative
(``nonexistent_table`` / ``nonexistent_name`` / ``duplicate_name`` /
``invalid_name``), so attribution stays clean.  ALTER POLICY has no
``OWNER TO`` clause, so there is no SESSION_USER no-op-transfer carve-out
(unlike ALTER MATERIALIZED VIEW); the privilege boundary fires simply
when ``privilege_level = non_owner``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import yaml

from .alter_policy_factor_loop import (
    _ACTION_TO_BRANCH,
    _SFV_FAILURE_SQLSTATE,
    build_alter_policy_factor_loop_plan,
)


class AlterPolicyFactorExtensionError(ValueError):
    """Raised when a frozen ALTER POLICY extension input drifts."""


@dataclass(frozen=True)
class AlterPolicyFactorExtensionCase:
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
class AlterPolicyFactorExtensionPlan:
    cases: tuple[AlterPolicyFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 72
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The exact
# frozen count is asserted in the companion test.
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_policy",
    "rls_behavior_test",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_policy",
    "revert_rename",
    "disable_rls_and_drop_policy",
    "drop_table",
)

# Privilege cluster: the non_owner value models the must_be_owner (42501)
# boundary and is counted as a single attributable failure unit.
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner"})

# Dense baseline assignment (all positive axes at success baselines).  The
# T5 negative factors (cannot_alter_command_type / cannot_alter_policy_type
# / privilege_denied / nonexistent_policy / nonexistent_table) are
# intentionally absent from the cross: they are owned one-per-value by the
# marginal baseline and are never crossed here, so the at-most-one-failure
# attribution stays clean.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_modify",
    "grammar_branch": "branch_modify",
    "target_action": "modify_combined",
    "alter_action": "modify_combined",
    "object_state": "exists",
    "expected_status": "success",
    "role_target": "single_role",
    "using_expression": "omitted_keep_original",
    "with_check_expression": "omitted_keep_original",
    "policy_name_shape": "simple_id",
    "table_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "role_name_shape": "simple_id",
    "privilege_level": "superuser",
    "privilege_denied": "owner_execution",
    "rls_enabled": "rls_enabled",
    "rls_not_enabled": "rls_enabled",
    "table_existence": "table_exists",
    "policy_existence": "policy_exists",
    "role_existence": "role_exists",
    "nonexistent_policy": "policy_exists",
    "nonexistent_table": "table_exists",
    "cannot_alter_command_type": "only_rename_and_modify_allowed",
    "cannot_alter_policy_type": "only_rename_and_modify_allowed",
    "verification_mode": "catalog_query_pg_policy",
    "cleanup_mode": "drop_policy",
}

# The five alter_action values (per the matrix).  Each action's signature
# sub-axis is crossed where it is observable; the other actions keep that
# axis at its baseline so the failure is never attributable where the
# sub-clause is not rendered.
_ALTER_ACTIONS = (
    "rename",
    "modify_combined",
    "modify_roles",
    "modify_using",
    "modify_with_check",
)

# Per-action signature sub-axis: (factor_key, values) or (None, (None,)).
_ACTION_CONDITIONAL: dict[str, tuple[str | None, tuple[str, ...]]] = {
    "rename": (
        "new_name_shape",
        ("simple_id", "quoted_id", "duplicate_name", "invalid_name"),
    ),
    "modify_using": (
        "using_expression",
        ("omitted_keep_original", "new_expression"),
    ),
    "modify_with_check": (
        "with_check_expression",
        ("omitted_keep_original", "new_expression"),
    ),
    "modify_roles": (
        "role_target",
        (
            "CURRENT_ROLE",
            "CURRENT_USER",
            "PUBLIC",
            "SESSION_USER",
            "multiple_roles",
            "single_role",
        ),
    ),
    "modify_combined": (None, (None,)),
}

_POLICY_NAME_SHAPES = (
    "simple_id",
    "quoted_id",
    "nonexistent_name",
    "existing_name",
)
_TABLE_NAME_SHAPES = (
    "simple_id",
    "quoted_id",
    "schema_qualified",
    "nonexistent_table",
)
_PRIVILEGE_LEVELS = ("superuser", "table_owner", "non_owner")
_RLS_STATES = ("rls_enabled", "rls_not_enabled")

# Crossed behaviour-negative (factor, value) pairs.  privilege_level =
# non_owner is counted as a single unit via _PRIVILEGE_CLUSTER_VALUES and is
# therefore not duplicated here.  new_name_shape = duplicate_name /
# invalid_name are only ever attributable where RENAME TO is actually
# rendered (the rename action), so they are conditional on the action.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("table_name_shape", "nonexistent_table"),
        ("policy_name_shape", "nonexistent_name"),
        ("new_name_shape", "duplicate_name"),
        ("new_name_shape", "invalid_name"),
    }
)


def _privilege_boundary_fires(assignment: dict[str, str]) -> bool:
    """Whether the must_be_owner check actually fires.

    ALTER POLICY has no ``OWNER TO`` clause, so there is no
    SESSION_USER no-op-transfer carve-out (unlike ALTER MATERIALIZED VIEW).
    The privilege boundary fires simply when ``privilege_level = non_owner``:
    a non-owner attempting to alter a policy on a table they do not own is
    rejected with 42501 (must_be_owner).  The at-most-one-failure filter
    already excludes any combination where this co-occurs with a behaviour
    negative (a missing table/policy/name), so the boundary is the sole
    attributable failure when it fires.
    """

    return assignment.get("privilege_level") == "non_owner"


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + behaviour negatives; must stay at most one."""

    cluster = (
        1
        if assignment.get("privilege_level") in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
        else 0
    )
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    return cluster + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege cluster is attributed when present and the boundary
    actually fires, then any single co-occurring behaviour-negative (the
    at-most-one rule has already excluded double-failure cases from the
    kept set).  Only one of these can match in the kept set.
    """

    level = assignment.get("privilege_level")
    if (
        level in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
    ):
        return ("privilege_level", level)
    if assignment.get("table_name_shape") == "nonexistent_table":
        return ("table_name_shape", "nonexistent_table")
    if assignment.get("policy_name_shape") == "nonexistent_name":
        return ("policy_name_shape", "nonexistent_name")
    if assignment.get("new_name_shape") == "duplicate_name":
        return ("new_name_shape", "duplicate_name")
    if assignment.get("new_name_shape") == "invalid_name":
        return ("new_name_shape", "invalid_name")
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """At-most-one-failure attribution."""

    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for action in _ALTER_ACTIONS:
        conditional_axis, conditional_values = _ACTION_CONDITIONAL[action]
        branch = _ACTION_TO_BRANCH[action]
        for cv in conditional_values:
            for policy_name in _POLICY_NAME_SHAPES:
                for table_name in _TABLE_NAME_SHAPES:
                    for privilege in _PRIVILEGE_LEVELS:
                        for rls in _RLS_STATES:
                            assignment: dict[str, str] = dict(
                                _BASELINE_DEFAULTS
                            )
                            assignment["alter_action"] = action
                            assignment["target_action"] = action
                            assignment["statement_branch"] = branch
                            assignment["grammar_branch"] = branch
                            if conditional_axis is not None:
                                assignment[conditional_axis] = cv
                            assignment["policy_name_shape"] = policy_name
                            assignment["table_name_shape"] = table_name
                            assignment["privilege_level"] = privilege
                            assignment["rls_enabled"] = rls
                            if not _is_valid_combination(assignment):
                                continue
                            # expected_status follows the ACTUAL outcome
                            # (from _present_failure_pair), not the
                            # filter's failure-unit count.
                            pair = _present_failure_pair(assignment)
                            assignment["expected_status"] = (
                                "failure" if pair is not None else "success"
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
    cases: tuple[AlterPolicyFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-policy-factor-extension-v1\n")
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
    cases: tuple[AlterPolicyFactorExtensionCase, ...],
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
                    f"ALTER POLICY extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_policy_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER POLICY",
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


def build_alter_policy_factor_extension_plan(
    repository_root: Path,
) -> AlterPolicyFactorExtensionPlan:
    """Build the bounded ALTER POLICY post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_policy_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    # Stable sort so any cap truncation is deterministic.
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterPolicyFactorExtensionCase] = []
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
                    AlterPolicyFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERPOLICY{ordinal:05d}",
                        sql_filename=f"ALTERPOLICY{ordinal:05d}.sql",
                        object_prefix=f"alterpolicy_{ordinal:05d}_",
                        derivation_id=(
                            f"AP-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_policy_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: alter_action="
                            f"{assignment['alter_action']} "
                            f"x policy_name_shape="
                            f"{assignment['policy_name_shape']} "
                            f"x table_name_shape="
                            f"{assignment['table_name_shape']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x rls_enabled={assignment['rls_enabled']} "
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
    return AlterPolicyFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterPolicyFactorExtensionError",
    "AlterPolicyFactorExtensionCase",
    "AlterPolicyFactorExtensionPlan",
    "build_alter_policy_factor_extension_plan",
]
