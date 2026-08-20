"""Bounded post-coverage cross-factor extension expander for DROP ROLE.

The marginal factor-value-loop (:mod:`drop_role_factor_loop`) is the
required baseline: one program per factor value, 59 local cases
(GRM 1 + SFV 56 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across the
single official synopsis branch (at most one failure-causing value per case,
so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_context`` in {no_privilege,
createrole_without_admin}, ``role_name_shape`` in {non_existing_name,
invalid_name}, ``role_existence=role_not_exists`` when
``if_exists_clause=without_if_exists``, ``owned_objects`` != no_owned_objects,
``active_session=has_active_session``) are crossed here with at-most-one-
failure attribution; the privilege boundary fires first (42501), then the
name/lookup boundary (42704/42601), then the existence boundary (42704),
then the dependency boundary (2BP01), then the active-session boundary
(55006).

The single official synopsis branch is crossed:

* ``branch_drop_role`` — ``privilege_context`` x ``role_existence`` x
  ``if_exists_clause`` x ``owned_objects`` x ``active_session`` x
  ``role_name_shape``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_role_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_role_factor_loop_plan,
)


class DropRoleFactorExtensionError(ValueError):
    """Raised when a frozen DROP ROLE extension input drifts."""


@dataclass(frozen=True)
class DropRoleFactorExtensionCase:
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
class DropRoleFactorExtensionPlan:
    cases: tuple[DropRoleFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 59
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_roles",
    "catalog_query_pg_authid",
    "effect_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_owned_then_drop_role",
    "reassign_owned_then_drop_role",
    "revoke_privileges_then_drop_role",
    "cascade_cleanup",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_context in {no_privilege, createrole_without_admin},
# role_name_shape in {non_existing_name, invalid_name},
# role_existence=role_not_exists under without_if_exists,
# owned_objects != no_owned_objects, active_session=has_active_session) are
# crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_role",
    "grammar_branch": "branch_1",
    "target_action": "drop_role",
    "role_existence": "role_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "privilege_context": "superuser",
    "multi_target": "single_target",
    "role_name_shape": "simple_name",
    "owned_objects": "no_owned_objects",
    "membership_state": "no_memberships",
    "active_session": "no_active_session",
    "dependency_conflict": "no_conflict",
    "privilege_insufficient": "sufficient_privilege",
    "boundary_case": "none",
    "verification_mode": "catalog_query_pg_roles",
    "cleanup_mode": "drop_owned_then_drop_role",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_role": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_role": "drop_role",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_role": {
        "privilege_context": (
            "createrole_with_admin",
            "createrole_without_admin",
            "no_privilege",
            "superuser",
        ),
        "role_existence": (
            "role_exists",
            "role_exists_as_nonsuperuser",
            "role_exists_as_superuser",
            "role_not_exists",
        ),
        "if_exists_clause": ("with_if_exists", "without_if_exists"),
        "owned_objects": (
            "no_owned_objects",
            "owns_functions",
            "owns_multiple_objects",
            "owns_sequences",
            "owns_tables",
            "owns_views",
        ),
        "active_session": (
            "has_active_session",
            "no_active_session",
        ),
        "role_name_shape": (
            "case_sensitive_name",
            "invalid_name",
            "non_existing_name",
            "quoted_name",
            "reserved_word_name",
            "simple_name",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: name/parse → privilege →
# lookup/existence → dependency → active session).  The name boundary (42601
# for invalid_name, 42704 for non_existing_name) fires at parse/lookup.  The
# privilege boundary (42501) fires for no_privilege / createrole_without_admin.
# The existence boundary (42704) fires when the role is absent and IF EXISTS
# is omitted.  The dependency boundary (2BP01) fires when the role owns
# objects.  The active-session boundary (55006) fires last.
_PRIVILEGE_FAILURES = frozenset({"no_privilege", "createrole_without_admin"})
_NAME_FAILURES = frozenset({"non_existing_name", "invalid_name"})
_OWNED_FAILURES = frozenset(
    {
        "owns_tables",
        "owns_sequences",
        "owns_views",
        "owns_functions",
        "owns_multiple_objects",
    }
)
_IF_EXISTS_OMITTED = "without_if_exists"


def _name_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("role_name_shape") in _NAME_FAILURES


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_context") in _PRIVILEGE_FAILURES


def _existence_failure_fires(assignment: dict[str, str]) -> bool:
    """role_not_exists fires only when IF EXISTS is omitted."""

    return (
        assignment.get("role_existence") == "role_not_exists"
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """owned objects block DROP ROLE regardless of cleanup policy."""

    return assignment.get("owned_objects") in _OWNED_FAILURES


def _active_session_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("active_session") == "has_active_session"


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _name_failure_fires(assignment):
        count += 1
    if _privilege_failure_fires(assignment):
        count += 1
    if _existence_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    if _active_session_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The name boundary (42601/42704) fires at parse/lookup, before the
    privilege check.  The privilege boundary (42501) fires next.  The
    existence boundary (42704) fires when the role is absent and IF EXISTS is
    omitted.  The dependency boundary (2BP01) fires when the role owns
    objects.  The active-session boundary (55006) fires last.
    """

    shape = assignment.get("role_name_shape")
    if shape in _NAME_FAILURES:
        return ("role_name_shape", shape)
    priv = assignment.get("privilege_context")
    if priv in _PRIVILEGE_FAILURES:
        return ("privilege_context", priv)
    if _existence_failure_fires(assignment):
        return ("role_existence", "role_not_exists")
    owned = assignment.get("owned_objects")
    if owned in _OWNED_FAILURES:
        return ("owned_objects", owned)
    if _active_session_failure_fires(assignment):
        return ("active_session", "has_active_session")
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
    cases: tuple[DropRoleFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-role-factor-extension-v1\n")
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
    cases: tuple[DropRoleFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP ROLE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_role_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP ROLE",
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


def build_drop_role_factor_extension_plan(
    repository_root: Path,
) -> DropRoleFactorExtensionPlan:
    """Build the bounded DROP ROLE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_role_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropRoleFactorExtensionCase] = []
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
                    DropRoleFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPROLE{ordinal:05d}",
                        sql_filename=f"DROPROLE{ordinal:05d}.sql",
                        object_prefix=f"droprole_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPROLE-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_role_required_baseline_factor_space"
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
    return DropRoleFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropRoleFactorExtensionError",
    "DropRoleFactorExtensionCase",
    "DropRoleFactorExtensionPlan",
    "build_drop_role_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
