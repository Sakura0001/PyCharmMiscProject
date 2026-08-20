"""Bounded post-coverage cross-factor extension expander for DROP OPERATOR FAMILY.

The marginal factor-value-loop (:mod:`drop_operator_family_factor_loop`) is the
required baseline: one program per factor value, 45 local cases
(GRM 1 + SFV 42 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across the
single official synopsis branch (at most one failure-causing boundary per
case, so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_context`` in
``{non_owner, insufficient_privilege}``, ``target_object_state=missing`` when
``if_exists_clause=absent``, dependents under a non-CASCADE drop policy) are
crossed here with at-most-one-failure attribution; the privilege boundary
fires first (42501), then the object-lookup boundary (42704), then the
dependency boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_1`` — ``privilege_context`` x ``target_object_state`` x
  ``if_exists_clause`` x ``cascade_clause`` x ``dependency_state`` x
  ``contained_opclass_state``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_operator_family_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_operator_family_factor_loop_plan,
)


class DropOperatorFamilyFactorExtensionError(ValueError):
    """Raised when a frozen DROP OPERATOR FAMILY extension input drifts."""


@dataclass(frozen=True)
class DropOperatorFamilyFactorExtensionCase:
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
class DropOperatorFamilyFactorExtensionPlan:
    cases: tuple[DropOperatorFamilyFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 45
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "effect_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_objects",
    "reset_state",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_context in {non_owner, insufficient_privilege},
# target_object_state=missing when if_exists_clause=absent, dependents under
# RESTRICT) are crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_operator_family",
    "target_object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_clause": "restrict_default",
    "privilege_context": "superuser",
    "name_shape": "plain_identifier",
    "index_method_shape": "btree",
    "dependency_state": "no_dependents",
    "cascade_behavior": "cascade_succeeds",
    "contained_opclass_state": "no_contained_opclass",
    "invalid_combination": "none",
    "ownership_boundary": "superuser",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_1": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_1": "drop_operator_family",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_1": {
        "privilege_context": (
            "insufficient_privilege",
            "non_owner",
            "owner",
            "superuser",
        ),
        "target_object_state": (
            "exists",
            "exists_with_contained_opclass",
            "exists_with_dependents",
            "missing",
        ),
        "if_exists_clause": ("absent", "present"),
        "cascade_clause": (
            "cascade",
            "restrict_default",
            "restrict_explicit",
        ),
        "dependency_state": ("has_dependents", "no_dependents"),
        "contained_opclass_state": (
            "contained_opclass_with_dependents",
            "has_contained_opclass",
            "no_contained_opclass",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> lookup ->
# dependency).  The privilege boundary (42501) fires first.  The object-lookup
# boundary (42704) fires when the family is absent and IF EXISTS is omitted.
# The dependency boundary (2BP01) fires when dependents are present under a
# non-CASCADE drop policy.
_PRIVILEGE_FAILURE_VALUES = frozenset({"non_owner", "insufficient_privilege"})
_RESTRICT_VALUES = frozenset({"restrict_default", "restrict_explicit"})
_IF_EXISTS_OMITTED = "absent"
_MISSING = "missing"
_DEPENDENT_OBJECT_STATES = frozenset(
    {"exists_with_dependents", "exists_with_contained_opclass"}
)
_DEPENDENT_OPCLASS_STATES = frozenset(
    {"has_contained_opclass", "contained_opclass_with_dependents"}
)


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_context") in _PRIVILEGE_FAILURE_VALUES


def _object_lookup_failure_fires(assignment: dict[str, str]) -> bool:
    """missing fires only when IF EXISTS is absent."""

    return (
        assignment.get("target_object_state") == _MISSING
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _has_dependents_present(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("dependency_state") == "has_dependents"
        or assignment.get("contained_opclass_state") in _DEPENDENT_OPCLASS_STATES
        or assignment.get("target_object_state") in _DEPENDENT_OBJECT_STATES
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """dependents block the drop only under a non-CASCADE policy."""

    return (
        _has_dependents_present(assignment)
        and assignment.get("cascade_clause") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _object_lookup_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the object lookup, so it is
    attributed first.  The object-lookup boundary (42704) fires next when the
    family is absent and IF EXISTS is omitted.  The dependency boundary
    (2BP01) fires last under RESTRICT with dependents.
    """

    if _privilege_failure_fires(assignment):
        return ("privilege_context", assignment["privilege_context"])
    if _object_lookup_failure_fires(assignment):
        return ("target_object_state", _MISSING)
    if _dependency_failure_fires(assignment):
        if assignment["dependency_state"] == "has_dependents":
            return ("dependency_state", "has_dependents")
        if assignment["contained_opclass_state"] in _DEPENDENT_OPCLASS_STATES:
            return (
                "contained_opclass_state",
                assignment["contained_opclass_state"],
            )
        return ("target_object_state", assignment["target_object_state"])
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
            assignment["cascade_behavior"] = (
                "restrict_blocks"
                if _dependency_failure_fires(assignment)
                else "cascade_succeeds"
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
    cases: tuple[DropOperatorFamilyFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-operator-family-factor-extension-v1\n")
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
    cases: tuple[DropOperatorFamilyFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP OPERATOR FAMILY extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_operator_family_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP OPERATOR FAMILY",
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


def build_drop_operator_family_factor_extension_plan(
    repository_root: Path,
) -> DropOperatorFamilyFactorExtensionPlan:
    """Build the bounded DROP OPERATOR FAMILY post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_operator_family_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropOperatorFamilyFactorExtensionCase] = []
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
                    DropOperatorFamilyFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPOPERATORFAMILY{ordinal:05d}",
                        sql_filename=f"DROPOPERATORFAMILY{ordinal:05d}.sql",
                        object_prefix=f"dropoperatorfamily_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPOPERATORFAMILY-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_operator_family_required_baseline_factor_space"
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
    return DropOperatorFamilyFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropOperatorFamilyFactorExtensionError",
    "DropOperatorFamilyFactorExtensionCase",
    "DropOperatorFamilyFactorExtensionPlan",
    "build_drop_operator_family_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
