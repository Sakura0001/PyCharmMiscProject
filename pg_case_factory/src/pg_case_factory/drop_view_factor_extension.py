"""Bounded post-coverage cross-factor extension expander for DROP VIEW.

The marginal factor-value-loop (:mod:`drop_view_factor_loop`) is the required
baseline: one program per factor value, 40 local cases (GRM 1 + SFV 37 +
Risk 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with ``verification_mode`` crossed and ``cleanup_mode``
crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_level=non_owner``,
``view_name_shape=non_existent`` when ``if_exists_clause=absent``,
``dependency_state=has_dependent_views`` under RESTRICT) are crossed here
with at-most-one-failure attribution; the privilege boundary fires first
(42501), then the view-lookup boundary (42704), then the dependency
boundary (2BP01).  ``view_name_shape=non_existent`` is the existence axis
(no twin-redundancy with ``object_state`` — ``object_state`` is derived from
``view_name_shape``, not independently crossed).

The single official synopsis branch is crossed:

* ``branch_drop_view`` — ``view_name_shape`` x ``privilege_level`` x
  ``dependency_state`` x ``if_exists_clause`` x ``cascade_restrict``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_view_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_view_factor_loop_plan,
)


class DropViewFactorExtensionError(ValueError):
    """Raised when a frozen DROP VIEW extension input drifts."""


@dataclass(frozen=True)
class DropViewFactorExtensionCase:
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
class DropViewFactorExtensionPlan:
    cases: tuple[DropViewFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 40
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_query",
    "effect_query",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "manual_cleanup",
    "cascade_cleanup",
    "rollback",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_level=non_owner, view_name_shape=non_existent when
# if_exists_clause=absent, dependency_state=has_dependent_views under
# RESTRICT) are crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_view",
    "grammar_branch": "branch_1",
    "target_action": "drop_view",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "view_name_shape": "simple",
    "multi_view_drop": "single_view",
    "privilege_level": "owner",
    "dependency_state": "no_dependents",
    "error_boundary": "none",
    "verification_mode": "pg_class_query",
    "cleanup_mode": "cascade_cleanup",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_view": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_view": "drop_view",
}

# Crossed positive behaviour axes per branch.  view_name_shape=non_existent
# is the existence axis (no twin-redundancy with object_state — object_state
# is derived from view_name_shape, not independently crossed).
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_view": {
        "view_name_shape": (
            "simple",
            "quoted",
            "schema_qualified",
            "reserved_word",
            "non_existent",
        ),
        "privilege_level": (
            "owner",
            "superuser",
            "schema_owner",
            "non_owner",
        ),
        "dependency_state": (
            "no_dependents",
            "has_dependent_views",
            "has_dependent_policies",
        ),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict": ("none", "cascade", "restrict"),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> view
# lookup -> dependency).  The privilege boundary (42501) fires first.
# The view-lookup boundary (42704) fires when the view is absent
# (view_name_shape=non_existent) and IF EXISTS is omitted.  The dependency
# boundary (2BP01) fires when dependent views exist under RESTRICT (or
# default RESTRICT).  Note: has_dependent_policies are auto-removed by
# DROP VIEW and do NOT fire under RESTRICT.
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")
_VIEW_MISSING_NEGATIVE = ("view_name_shape", "non_existent")
_DEPENDENCY_NEGATIVES = frozenset(
    {
        ("dependency_state", "has_dependent_views"),
    }
)
_RESTRICT_VALUES = frozenset({"none", "restrict"})
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_level") == "non_owner"


def _view_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """view-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return assignment.get("view_name_shape") == "non_existent"


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has_dependent_views fires only under a non-CASCADE drop policy."""

    dep = assignment.get("dependency_state")
    if dep is None:
        return False
    pair = ("dependency_state", dep)
    if pair not in _DEPENDENCY_NEGATIVES:
        return False
    return assignment.get("cascade_restrict") in _RESTRICT_VALUES


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _view_missing_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the object lookup, so it is
    attributed first.  The view-lookup boundary (42704) fires next when the
    view is absent (view_name_shape=non_existent) and IF EXISTS is omitted.
    The dependency boundary (2BP01) fires last under RESTRICT with dependent
    views.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _view_missing_failure_fires(assignment):
        return _VIEW_MISSING_NEGATIVE
    if _dependency_failure_fires(assignment):
        return ("dependency_state", assignment["dependency_state"])
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
            # Derive object_state from view_name_shape (no twin-redundancy
            # with the object_state axis — view_name_shape=non_existent IS
            # the existence boundary).
            if assignment.get("view_name_shape") == "non_existent":
                assignment["object_state"] = "not_exists"
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
    cases: tuple[DropViewFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-view-factor-extension-v1\n")
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
    cases: tuple[DropViewFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP VIEW extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_view_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP VIEW",
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


def build_drop_view_factor_extension_plan(
    repository_root: Path,
) -> DropViewFactorExtensionPlan:
    """Build the bounded DROP VIEW post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_view_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropViewFactorExtensionCase] = []
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
                    DropViewFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPVIEW{ordinal:05d}",
                        sql_filename=f"DROPVIEW{ordinal:05d}.sql",
                        object_prefix=f"dropview_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPVIEW-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_view_required_baseline_factor_space"
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
    return DropViewFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropViewFactorExtensionError",
    "DropViewFactorExtensionCase",
    "DropViewFactorExtensionPlan",
    "build_drop_view_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
