"""Bounded post-coverage cross-factor extension expander for DROP ROUTINE.

The marginal factor-value-loop (:mod:`drop_routine_factor_loop`) is the
required baseline: one program per factor value, 63 local cases
(GRM 1 + SFV 60 + RISK 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across
the single official synopsis branch (at most one failure-causing value
per case, so attribution stays clean), with ``verification_mode`` crossed
and ``cleanup_mode`` crossed so every declared T6 value is exercised.

``DROP ROUTINE`` is generic over functions, procedures, and aggregates,
so ``routine_type`` is a crossed axis (the defining semantic of this
statement).  The negative boundaries (privilege_context=
non_owner_no_privilege, routine_existence=routine_not_exists under
without_if_exists, dependent_objects=has_dependent_routine under a
non-CASCADE policy) are crossed here with at-most-one-failure
attribution: the privilege boundary fires first (42501), then the
not-exist boundary (42704), then the dependency boundary (2BP01).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_routine_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_routine_factor_loop_plan,
)


class DropRoutineFactorExtensionError(ValueError):
    """Raised when a frozen DROP ROUTINE extension input drifts."""


@dataclass(frozen=True)
class DropRoutineFactorExtensionCase:
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
class DropRoutineFactorExtensionPlan:
    cases: tuple[DropRoutineFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 63
_CAP = 20000

_VERIFICATION_MODES = ("pg_proc_catalog", "error_assertion")
_CLEANUP_MODES = (
    "drop_routine",
    "drop_function",
    "drop_procedure",
    "drop_aggregate",
    "cascade_drop_with_dependents",
)

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_routine",
    "grammar_branch": "branch_1",
    "target_action": "drop_routine",
    "routine_existence": "routine_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "routine_type": "function",
    "arg_signature_disambiguation": "no_args_no_ambiguity",
    "privilege_context": "superuser",
    "multi_target": "single_target",
    "routine_name_shape": "simple_name",
    "arg_signature_shape": "no_args",
    "executor_privilege": "superuser",
    "dependent_objects": "no_dependent_objects",
    "nonexistent_routine": "routine_does_not_exist",
    "privilege_insufficient": "non_owner_dropping_routine",
    "dependent_object_conflict": "restrict_with_dependent_fails",
    "overloaded_routine_ambiguity": "ambiguous_without_signature",
    "wrong_argument_types": "signature_does_not_match_any_routine",
    "verification_mode": "pg_proc_catalog",
    "cleanup_mode": "drop_routine",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_routine": "branch_1",
    "branch_drop_routine_if_exists": "branch_1",
    "branch_drop_routine_cascade": "branch_1",
    "branch_drop_routine_restrict": "branch_1",
}
_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_routine": "drop_routine",
    "branch_drop_routine_if_exists": "drop_routine",
    "branch_drop_routine_cascade": "drop_routine",
    "branch_drop_routine_restrict": "drop_routine",
}

# Crossed positive behaviour axes.  routine_existence's ``as_*`` values pin
# routine_type (a generic DROP ROUTINE resolves the fixture kind from the
# existence state); routine_exists / routine_not_exists leave routine_type
# as the crossed selector.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_routine": {
        "privilege_context": (
            "non_owner_no_privilege",
            "owner_of_routine",
            "superuser",
        ),
        "routine_existence": (
            "routine_exists",
            "routine_exists_as_function",
            "routine_exists_as_procedure",
            "routine_exists_as_aggregate",
            "routine_not_exists",
        ),
        "if_exists_clause": ("without_if_exists", "with_if_exists"),
        "cascade_restrict_clause": (
            "no_clause_default_restrict",
            "cascade",
            "restrict",
        ),
        "dependent_objects": ("no_dependent_objects", "has_dependent_routine"),
        "routine_type": ("function", "procedure", "aggregate"),
    },
}

_PRIVILEGE_NEGATIVE = ("privilege_context", "non_owner_no_privilege")
_NOT_EXIST_NEGATIVE = ("routine_existence", "routine_not_exists")
_DEPENDENCY_NEGATIVE = ("dependent_objects", "has_dependent_routine")
_RESTRICT_VALUES = frozenset({"no_clause_default_restrict", "restrict"})
_IF_EXISTS_OMITTED = "without_if_exists"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_context") == "non_owner_no_privilege"


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    """routine_not_exists surfaces a 42704 only when IF EXISTS is omitted."""

    return (
        assignment.get("routine_existence") == "routine_not_exists"
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has_dependent_routine fails under a non-CASCADE drop policy."""

    return (
        assignment.get("dependent_objects") == "has_dependent_routine"
        and assignment.get("cascade_restrict_clause") in _RESTRICT_VALUES
    )


def _is_contradictory(assignment: dict[str, str]) -> bool:
    """A non-existent routine cannot have a dependent routine."""

    return (
        assignment.get("routine_existence") == "routine_not_exists"
        and assignment.get("dependent_objects") == "has_dependent_routine"
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

    Privilege boundary (42501) fires before object lookup; the not-exist
    boundary (42704) fires next when the routine is absent and IF EXISTS
    is omitted; the dependency boundary (2BP01) fires last under a
    non-CASCADE policy with dependents.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _not_exist_failure_fires(assignment):
        return _NOT_EXIST_NEGATIVE
    if _dependency_failure_fires(assignment):
        return _DEPENDENCY_NEGATIVE
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    if _is_contradictory(assignment):
        return False
    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments passing the validity filter."""

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
            # Reconcile routine_existence with routine_type: the ``as_*``
            # existence values pin the routine kind, overriding the crossed
            # routine_type selector.
            existence = assignment["routine_existence"]
            if existence == "routine_exists_as_function":
                assignment["routine_type"] = "function"
            elif existence == "routine_exists_as_procedure":
                assignment["routine_type"] = "procedure"
            elif existence == "routine_exists_as_aggregate":
                assignment["routine_type"] = "aggregate"
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
    cases: tuple[DropRoutineFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-routine-factor-extension-v1\n")
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
    cases: tuple[DropRoutineFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP ROUTINE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_routine_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP ROUTINE",
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


def build_drop_routine_factor_extension_plan(
    repository_root: Path,
) -> DropRoutineFactorExtensionPlan:
    """Build the bounded DROP ROUTINE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_routine_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropRoutineFactorExtensionCase] = []
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
                    DropRoutineFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPROUTINE{ordinal:05d}",
                        sql_filename=f"DROPROUTINE{ordinal:05d}.sql",
                        object_prefix=f"droproutine_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPROUTINE-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_routine_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x routine_type={assignment['routine_type']} "
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
    return DropRoutineFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropRoutineFactorExtensionError",
    "DropRoutineFactorExtensionCase",
    "DropRoutineFactorExtensionPlan",
    "build_drop_routine_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
