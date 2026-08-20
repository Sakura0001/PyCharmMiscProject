"""Bounded post-coverage cross-factor extension expander for DROP FUNCTION.

The marginal factor-value-loop (:mod:`drop_function_factor_loop`) is the
required baseline: one program per factor value, 45 local cases
(GRM 1 + SFV 42 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across the
two official synopsis branches (at most one failure-causing value per case,
so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_level=non_owner_no_privilege``,
``object_state=not_exists`` or ``different_signature_exists`` when
``if_exists_clause=absent``, ``dependent_objects`` with has-dependents under
RESTRICT/absent) are crossed here with at-most-one-failure attribution; the
privilege boundary fires first (42501), then the not-found boundary (42704),
then the dependency boundary (2BP01).

The two official synopsis branches are crossed:

* ``branch_1`` — ``privilege_level`` x ``object_state`` x
  ``if_exists_clause`` x ``cascade_restrict_clause`` x ``dependent_objects``.
* ``branch_2`` — same axes.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_function_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_function_factor_loop_plan,
)


class DropFunctionFactorExtensionError(ValueError):
    """Raised when a frozen DROP FUNCTION extension input drifts."""


@dataclass(frozen=True)
class DropFunctionFactorExtensionCase:
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
class DropFunctionFactorExtensionPlan:
    cases: tuple[DropFunctionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 45
_CAP = 20000

_VERIFICATION_MODES = (
    "information_schema_routines",
    "pg_proc_catalog_query",
)
_CLEANUP_MODES = (
    "DROP_FUNCTION_cascade",
    "DROP_FUNCTION_if_exists_cascade",
    "no_cleanup_needed",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_level=non_owner_no_privilege, object_state=not_exists/
# different_signature_exists, dependent_objects has-dependents) are crossed
# here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_function",
    "argtype_specification": "without_signature_single",
    "cascade_destroys_dependents": "cascade_removes_trigger",
    "cascade_restrict_clause": "absent",
    "cleanup_mode": "DROP_FUNCTION_cascade",
    "dependent_objects": "no_dependencies",
    "expected_status": "success",
    "function_name_shape": "simple",
    "identifier_length_exceeded": "within_63_chars",
    "if_exists_clause": "absent",
    "multiple_objects": "single_function",
    "object_state": "exists",
    "permission_insufficient": "owner_success",
    "privilege_level": "superuser",
    "schema_dependency": "schema_exists",
    "target_function_different_type": "same_name_is_function",
    "target_function_not_exists": "with_IF_EXISTS_noop",
    "verification_mode": "pg_proc_catalog_query",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_1": "branch_1",
    "branch_2": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_1": "drop_function",
    "branch_2": "drop_function",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_1": {
        "privilege_level": (
            "function_owner",
            "non_owner_no_privilege",
            "superuser",
        ),
        "object_state": (
            "different_signature_exists",
            "exists",
            "not_exists",
        ),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict_clause": ("CASCADE", "RESTRICT", "absent"),
        "dependent_objects": (
            "has_dependents_cascade_removes",
            "has_dependents_restrict_blocks",
            "no_dependencies",
        ),
    },
    "branch_2": {
        "privilege_level": (
            "function_owner",
            "non_owner_no_privilege",
            "superuser",
        ),
        "object_state": (
            "different_signature_exists",
            "exists",
            "not_exists",
        ),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict_clause": ("CASCADE", "RESTRICT", "absent"),
        "dependent_objects": (
            "has_dependents_cascade_removes",
            "has_dependents_restrict_blocks",
            "no_dependencies",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> lookup ->
# dependency).  The privilege boundary (42501) fires first.  The not-found
# boundary (42704) fires when the function is absent (not_exists or
# different_signature_exists) and IF EXISTS is omitted.  The dependency
# boundary (2BP01) fires when RESTRICT/absent is used with dependents.
_PRIVILEGE_NEGATIVE_FACTOR = "privilege_level"
_PRIVILEGE_NEGATIVE_VALUE = "non_owner_no_privilege"
_NOT_EXIST_NEGATIVE_VALUES = frozenset({"not_exists", "different_signature_exists"})
_DEPENDENCY_NEGATIVE_VALUES = frozenset({
    "has_dependents_cascade_removes",
    "has_dependents_restrict_blocks",
})
_RESTRICT_VALUES = frozenset({"RESTRICT", "absent"})
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("privilege_level") == _PRIVILEGE_NEGATIVE_VALUE
    )


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    """not_found fires only when IF EXISTS is omitted."""

    return (
        assignment.get("object_state") in _NOT_EXIST_NEGATIVE_VALUES
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has-dependents fires only under a non-CASCADE drop policy."""

    return (
        assignment.get("dependent_objects") in _DEPENDENCY_NEGATIVE_VALUES
        and assignment.get("cascade_restrict_clause") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _not_exist_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the object lookup, so it is
    attributed first.  The not-found boundary (42704) fires next when the
    function is absent and IF EXISTS is omitted.  The dependency boundary
    (2BP01) fires last under RESTRICT/absent with dependents.
    """

    if _privilege_failure_fires(assignment):
        return ("privilege_level", assignment["privilege_level"])
    if _not_exist_failure_fires(assignment):
        return ("object_state", assignment["object_state"])
    if _dependency_failure_fires(assignment):
        return ("dependent_objects", assignment["dependent_objects"])
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
    cases: tuple[DropFunctionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-function-factor-extension-v1\n")
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
    cases: tuple[DropFunctionFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP FUNCTION extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_function_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP FUNCTION",
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


def build_drop_function_factor_extension_plan(
    repository_root: Path,
) -> DropFunctionFactorExtensionPlan:
    """Build the bounded DROP FUNCTION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_function_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropFunctionFactorExtensionCase] = []
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
                    DropFunctionFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPFUNCTION{ordinal:05d}",
                        sql_filename=f"DROPFUNCTION{ordinal:05d}.sql",
                        object_prefix=f"dropfunction_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPFUNCTION-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_function_required_baseline_factor_space"
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
    return DropFunctionFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropFunctionFactorExtensionError",
    "DropFunctionFactorExtensionCase",
    "DropFunctionFactorExtensionPlan",
    "build_drop_function_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
