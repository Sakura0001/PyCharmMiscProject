"""Bounded post-coverage cross-factor extension expander for ALTER LANGUAGE.

The marginal factor-value-loop (:mod:`alter_language_factor_loop`) is the
required baseline: one program per factor value, 42 local cases
(GRM 2 + SFV 38 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_language.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive T1-T4 behaviour axes across the two official synopsis
branches (at most one failure-causing value per case, so attribution stays
clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed so
every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The T5 negative factors (``invalid_combination``, ``ownership_boundary``) are
owned one-per-value by the marginal baseline and are never crossed here, so
the at-most-one-failure attribution stays clean.

The two official synopsis branches are crossed independently:

* ``branch_rename`` — ``new_name_shape`` x ``name_shape`` x
  ``target_object_state`` x ``privilege_context`` x ``rename_conflict``.
* ``branch_owner`` — ``new_owner_shape`` x ``name_shape`` x
  ``target_object_state`` x ``privilege_context``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_language_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_language_factor_loop_plan,
)


class AlterLanguageFactorExtensionError(ValueError):
    """Raised when a frozen ALTER LANGUAGE extension input drifts."""


@dataclass(frozen=True)
class AlterLanguageFactorExtensionCase:
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
class AlterLanguageFactorExtensionPlan:
    cases: tuple[AlterLanguageFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 42
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The exact
# frozen count is asserted in the companion test.
_CAP = 20000

_VERIFICATION_MODES = ("catalog_query", "effect_query", "error_assertion")
_CLEANUP_MODES = ("drop_objects", "reset_state")

# Privilege cluster: both non-owner privilege values model the same
# must_be_owner_of_language (42501) boundary and are counted as a single
# attributable failure unit.
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner", "insufficient_privilege"})

# Dense baseline assignment (all positive T1-T4 + T6 baselines).  The T5
# negative factors (invalid_combination, ownership_boundary) are intentionally
# absent: they are owned one-per-value by the marginal baseline and are never
# crossed here, so the at-most-one-failure attribution stays clean.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_rename",
    "grammar_branch": "branch_rename",
    "target_action": "rename",
    "target_object_state": "exists",
    "expected_status": "success",
    "name_shape": "plain_identifier",
    "new_name_shape": "plain_identifier",
    "new_owner_shape": "plain_role",
    "privilege_context": "owner",
    "ownership_boundary": "owner",
    "dependency_state": "ready",
    "rename_conflict": "new_name_available",
    "invalid_combination": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}

# Official synopsis branch -> grammar_branch id used by the renderer.
_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_rename": "branch_rename",
    "branch_owner": "branch_owner",
}

# Fixed consumer action per branch (the synopsis action form).
_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_rename": "rename",
    "branch_owner": "owner_change",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_rename": {
        "new_name_shape": (
            "plain_identifier",
            "quoted_identifier",
            "existing_name_conflict",
        ),
        "name_shape": (
            "plain_identifier",
            "quoted_identifier",
            "missing_object",
        ),
        "target_object_state": ("exists", "missing"),
        "privilege_context": (
            "superuser",
            "owner",
            "non_owner",
            "insufficient_privilege",
        ),
        "rename_conflict": ("new_name_available", "new_name_conflict"),
    },
    "branch_owner": {
        "new_owner_shape": (
            "plain_role",
            "current_role",
            "current_user",
            "session_user",
            "missing_role",
        ),
        "name_shape": (
            "plain_identifier",
            "quoted_identifier",
            "missing_object",
        ),
        "target_object_state": ("exists", "missing"),
        "privilege_context": (
            "superuser",
            "owner",
            "non_owner",
            "insufficient_privilege",
        ),
    },
}

# Crossed behaviour-negative (factor, value) pairs.  The privilege cluster
# (privilege_context=non_owner/insufficient_privilege) is counted as a single
# unit via _PRIVILEGE_CLUSTER_VALUES and is therefore not duplicated here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("target_object_state", "missing"),
        ("name_shape", "missing_object"),
        ("new_name_shape", "existing_name_conflict"),
        ("rename_conflict", "new_name_conflict"),
        ("new_owner_shape", "missing_role"),
    }
)


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + behaviour negatives; must stay at most one."""

    cluster = (
        1
        if assignment.get("privilege_context") in _PRIVILEGE_CLUSTER_VALUES
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

    ALTER LANGUAGE has no superuser-only action or role-membership wall (the
    only privilege boundary is must_be_owner_of_language, modelled by the
    privilege cluster), so the privilege cluster is attributed first when
    present, then any single co-occurring behaviour-negative (the at-most-one
    rule has already excluded double-failure cases from the kept set).
    """

    level = assignment.get("privilege_context")
    if level in _PRIVILEGE_CLUSTER_VALUES:
        return ("privilege_context", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
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
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = _BRANCH_GRAMMAR[branch]
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
    cases: tuple[AlterLanguageFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-language-factor-extension-v1\n")
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
    cases: tuple[AlterLanguageFactorExtensionCase, ...],
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
                    f"ALTER LANGUAGE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_language_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER LANGUAGE",
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


def build_alter_language_factor_extension_plan(
    repository_root: Path,
) -> AlterLanguageFactorExtensionPlan:
    """Build the bounded ALTER LANGUAGE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_language_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    # Stable sort so any cap truncation is deterministic and interleaves
    # branches rather than favouring the first branch.
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterLanguageFactorExtensionCase] = []
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
                    AlterLanguageFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERLANGUAGE{ordinal:05d}",
                        sql_filename=f"ALTERLANGUAGE{ordinal:05d}.sql",
                        object_prefix=f"alterlanguage_{ordinal:05d}_",
                        derivation_id=(
                            f"AL-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_language_required_baseline_factor_space"
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
    return AlterLanguageFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterLanguageFactorExtensionError",
    "AlterLanguageFactorExtensionCase",
    "AlterLanguageFactorExtensionPlan",
    "build_alter_language_factor_extension_plan",
]
