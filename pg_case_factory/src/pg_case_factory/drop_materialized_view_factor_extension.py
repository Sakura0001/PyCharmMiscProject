"""Bounded post-coverage cross-factor extension expander for DROP MATERIALIZED VIEW.

The marginal factor-value-loop (:mod:`drop_materialized_view_factor_loop`) is
the required baseline: one program per factor value, 37 local cases
(GRM 1 + SFV 34 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across the
single official synopsis branch (at most one failure-causing value per case,
so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_context=insufficient_privilege``,
``ownership_boundary=non_owner``, ``target_object_state=missing`` when
``if_exists_clause=absent``, ``target_object_state=wrong_object_type``,
``dependency_state=has_dependents`` under RESTRICT) are crossed here with
at-most-one-failure attribution; the privilege boundary fires first (42501),
then the wrong-type boundary (42809), then the not-exist boundary (42704),
then the dependency boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_1`` — ``privilege_context`` x ``ownership_boundary`` x
  ``target_object_state`` x ``if_exists_clause`` x ``cascade_clause``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_materialized_view_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_materialized_view_factor_loop_plan,
)


class DropMaterializedViewFactorExtensionError(ValueError):
    """Raised when a frozen DROP MATERIALIZED VIEW extension input drifts."""


@dataclass(frozen=True)
class DropMaterializedViewFactorExtensionCase:
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
class DropMaterializedViewFactorExtensionPlan:
    cases: tuple[DropMaterializedViewFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 37
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
# (privilege_context=insufficient_privilege, ownership_boundary=non_owner,
# target_object_state=missing/wrong_object_type, dependency_state=
# has_dependents) are crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_materialized_view",
    "target_object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_clause": "restrict_default",
    "privilege_context": "owner",
    "name_shape": "plain_identifier",
    "dependency_state": "no_dependents",
    "cascade_behavior": "cascade_succeeds",
    "invalid_combination": "none",
    "ownership_boundary": "owner",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_1": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_1": "drop_materialized_view",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_1": {
        "privilege_context": (
            "insufficient_privilege",
            "owner",
            "granted_role",
        ),
        "ownership_boundary": (
            "non_owner",
            "owner",
            "member_role",
        ),
        "target_object_state": (
            "missing",
            "exists",
            "exists_with_dependents",
            "wrong_object_type",
        ),
        "if_exists_clause": ("absent", "present"),
        "cascade_clause": (
            "restrict_default",
            "restrict_explicit",
            "cascade",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> wrong-type
# -> not-exist -> dependency).  The privilege boundary (42501) fires first.
# The wrong-type boundary (42809) fires for wrong_object_type.  The not-exist
# boundary (42704) fires when the matview is missing and IF EXISTS is absent.
# The dependency boundary (2BP01) fires when RESTRICT is used with deps.
_PRIVILEGE_NEGATIVES = {
    ("privilege_context", "insufficient_privilege"),
    ("ownership_boundary", "non_owner"),
}
_WRONG_TYPE_NEGATIVE = ("target_object_state", "wrong_object_type")
_NOT_EXIST_NEGATIVE = ("target_object_state", "missing")
_DEPENDENCY_NEGATIVE = ("dependency_state", "has_dependents")
_RESTRICT_VALUES = frozenset({"restrict_default", "restrict_explicit"})
_IF_EXISTS_ABSENT = "absent"


def _derive_dependency_state(target_object_state: str) -> str:
    if target_object_state == "exists_with_dependents":
        return "has_dependents"
    return "no_dependents"


def _derive_cascade_behavior(
    cascade_clause: str, dependency_state: str
) -> str:
    if cascade_clause == "cascade":
        return "cascade_succeeds"
    if dependency_state == "has_dependents":
        return "restrict_blocks"
    return "cascade_succeeds"


def _derive_invalid_combination(target_object_state: str) -> str:
    if target_object_state == "wrong_object_type":
        return "object_type_mismatch"
    return "none"


def _derive_name_shape(target_object_state: str) -> str:
    if target_object_state == "missing":
        return "missing_object"
    return "plain_identifier"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("privilege_context") == "insufficient_privilege"
        or assignment.get("ownership_boundary") == "non_owner"
    )


def _wrong_type_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("target_object_state") == "wrong_object_type"


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    """missing fires only when IF EXISTS is absent."""

    return (
        assignment.get("target_object_state") == "missing"
        and assignment.get("if_exists_clause") == _IF_EXISTS_ABSENT
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has_dependents fires only under a non-CASCADE drop policy."""

    dep = _derive_dependency_state(
        assignment.get("target_object_state", "exists")
    )
    return (
        dep == "has_dependents"
        and assignment.get("cascade_clause") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if assignment.get("privilege_context") == "insufficient_privilege":
        count += 1
    if assignment.get("ownership_boundary") == "non_owner":
        count += 1
    if _wrong_type_failure_fires(assignment):
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
    attributed first.  The wrong-type boundary (42809) fires next for a
    wrong-type target.  The not-exist boundary (42704) fires next when the
    matview is absent and IF EXISTS is omitted.  The dependency boundary
    (2BP01) fires last under RESTRICT with dependencies.
    """

    if assignment.get("privilege_context") == "insufficient_privilege":
        return ("privilege_context", "insufficient_privilege")
    if assignment.get("ownership_boundary") == "non_owner":
        return ("ownership_boundary", "non_owner")
    if _wrong_type_failure_fires(assignment):
        return _WRONG_TYPE_NEGATIVE
    if _not_exist_failure_fires(assignment):
        return _NOT_EXIST_NEGATIVE
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
            tos = assignment["target_object_state"]
            assignment["dependency_state"] = _derive_dependency_state(tos)
            assignment["cascade_behavior"] = _derive_cascade_behavior(
                assignment["cascade_clause"],
                assignment["dependency_state"],
            )
            assignment["invalid_combination"] = (
                _derive_invalid_combination(tos)
            )
            assignment["name_shape"] = _derive_name_shape(tos)
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
    cases: tuple[DropMaterializedViewFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"drop-materialized-view-factor-extension-v1\n"
    )
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
    cases: tuple[DropMaterializedViewFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP MATERIALIZED VIEW extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_materialized_view_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP MATERIALIZED VIEW",
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


def build_drop_materialized_view_factor_extension_plan(
    repository_root: Path,
) -> DropMaterializedViewFactorExtensionPlan:
    """Build the bounded DROP MATERIALIZED VIEW post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_materialized_view_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropMaterializedViewFactorExtensionCase] = []
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
                    DropMaterializedViewFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPMATERIALIZEDVIEW{ordinal:05d}",
                        sql_filename=f"DROPMATERIALIZEDVIEW{ordinal:05d}.sql",
                        object_prefix=f"dropmaterializedview_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPMATERIALIZEDVIEW-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_materialized_view_required_baseline_factor_space"
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
    return DropMaterializedViewFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropMaterializedViewFactorExtensionError",
    "DropMaterializedViewFactorExtensionCase",
    "DropMaterializedViewFactorExtensionPlan",
    "build_drop_materialized_view_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
