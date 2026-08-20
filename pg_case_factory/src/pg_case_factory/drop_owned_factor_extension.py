"""Bounded post-coverage cross-factor extension expander for DROP OWNED.

The marginal factor-value-loop (:mod:`drop_owned_factor_loop`) is the required
baseline: one program per factor value, 44 local cases (GRM 1 + SFV 41 +
Risk 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed
so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``executor_privilege=normal_user_no_privilege``,
``role_existence=role_not_exists``, ``dependent_objects=
has_dependent_objects_restrict_fails`` under RESTRICT) are crossed here with
at-most-one-failure attribution; the privilege boundary fires first (42501),
then the role-lookup boundary (42704), then the dependency boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_drop_owned_by`` — ``executor_privilege`` x ``role_existence`` x
  ``cascade_restrict_clause`` x ``dependent_objects`` x ``multi_role`` x
  ``role_shape``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_owned_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_owned_factor_loop_plan,
)


class DropOwnedFactorExtensionError(ValueError):
    """Raised when a frozen DROP OWNED extension input drifts."""


@dataclass(frozen=True)
class DropOwnedFactorExtensionCase:
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
class DropOwnedFactorExtensionPlan:
    cases: tuple[DropOwnedFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 44
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "pg_roles_catalog_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_owned_cascade",
    "drop_role_cascade",
    "reassign_owned_then_drop_role",
)

# Dense baseline assignment (all positive values).  The negative factors
# (executor_privilege=normal_user_no_privilege,
# role_existence=role_not_exists,
# dependent_objects=has_dependent_objects_restrict_fails) are crossed here
# with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_owned_by",
    "grammar_branch": "branch_1",
    "target_action": "drop_owned",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "cleanup_mode": "drop_owned_cascade",
    "cross_database_limitation": "only_current_database_objects",
    "dependent_objects": "no_dependent_objects",
    "executor_privilege": "superuser",
    "expected_status": "success",
    "multi_role": "single_role",
    "nonexistent_role": "role_does_not_exist",
    "owned_objects_state": "owns_tables",
    "privilege_insufficient": "non_superuser_dropping_other_role_objects",
    "role_existence": "role_exists",
    "role_name_shape": "simple_name",
    "role_shape": "explicit_role_name",
    "verification_mode": "pg_class_catalog_query",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_owned_by": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_owned_by": "drop_owned",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_owned_by": {
        "executor_privilege": (
            "normal_user_no_privilege",
            "superuser",
            "createrole_privilege",
        ),
        "role_existence": (
            "role_exists",
            "role_not_exists",
            "role_is_current_user",
        ),
        "cascade_restrict_clause": (
            "cascade",
            "no_clause_default_restrict",
            "restrict",
        ),
        "dependent_objects": (
            "no_dependent_objects",
            "has_dependent_objects_cascade_succeeds",
            "has_dependent_objects_restrict_fails",
        ),
        "multi_role": ("single_role", "multiple_roles"),
        "role_shape": (
            "explicit_role_name",
            "current_role_keyword",
            "current_user_keyword",
            "session_user_keyword",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> lookup ->
# dependency).  The privilege boundary (42501) fires first.  The role-lookup
# boundary (42704) fires when the role does not exist.  The dependency
# boundary (2BP01) fires when RESTRICT is used with dependent objects.
_PRIVILEGE_NEGATIVE = ("executor_privilege", "normal_user_no_privilege")
_ROLE_NOT_EXIST_NEGATIVE = ("role_existence", "role_not_exists")
_DEPENDENCY_NEGATIVE = (
    "dependent_objects",
    "has_dependent_objects_restrict_fails",
)
_RESTRICT_VALUES = frozenset({"no_clause_default_restrict", "restrict"})


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("executor_privilege") == "normal_user_no_privilege"


def _role_not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("role_existence") == "role_not_exists"


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has_dependent_objects_restrict_fails fires under non-CASCADE."""

    return (
        assignment.get("dependent_objects")
        == "has_dependent_objects_restrict_fails"
        and assignment.get("cascade_restrict_clause") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _role_not_exist_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the role lookup, so it is
    attributed first.  The role-lookup boundary (42704) fires next when the
    role does not exist.  The dependency boundary (2BP01) fires last under
    RESTRICT with dependent objects.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _role_not_exist_failure_fires(assignment):
        return _ROLE_NOT_EXIST_NEGATIVE
    if _dependency_failure_fires(assignment):
        return _DEPENDENCY_NEGATIVE
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
    cases: tuple[DropOwnedFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-owned-factor-extension-v1\n")
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
    cases: tuple[DropOwnedFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP OWNED extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_owned_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP OWNED",
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


def build_drop_owned_factor_extension_plan(
    repository_root: Path,
) -> DropOwnedFactorExtensionPlan:
    """Build the bounded DROP OWNED post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_owned_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropOwnedFactorExtensionCase] = []
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
                    DropOwnedFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPOWNED{ordinal:05d}",
                        sql_filename=f"DROPOWNED{ordinal:05d}.sql",
                        object_prefix=f"dropowned_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPOWNED-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_owned_declared_factor_baseline"
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
    return DropOwnedFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropOwnedFactorExtensionError",
    "DropOwnedFactorExtensionCase",
    "DropOwnedFactorExtensionPlan",
    "build_drop_owned_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
