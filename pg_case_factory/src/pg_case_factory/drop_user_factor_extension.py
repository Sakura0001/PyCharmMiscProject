"""Bounded post-coverage cross-factor extension expander for DROP USER.

The marginal factor-value-loop (:mod:`drop_user_factor_loop`) is the required
baseline: one program per factor value, 39 local cases (GRM 1 + SFV 36 +
Risk 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with ``verification_mode`` crossed and ``cleanup_mode``
crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``authorization_path=non_createrole``,
``object_state=absent`` / ``role_name_shape=non_existent_name`` when
``if_exists_clause=absent``, ``dependency_context`` in
``role_owns_objects``/``role_has_active_sessions``) are crossed here with
at-most-one-failure attribution; the privilege boundary fires first (42501),
then the object-lookup boundary (42704), then the dependency boundary
(2BP01).  The privilege twin (``privilege_context``) and dependency twin
(``role_dependency``) are *derived* from the crossed ``authorization_path``
and ``dependency_context`` axes (not crossed independently) to avoid a
redundant cartesian blow-up; both twin values remain fully covered by the
baseline.  ``error_type`` (a T5 negative-boundary *classification*, not an
independent behaviour axis) is derived from the present failure pair.

The single official synopsis branch is crossed:

* ``branch_drop_user`` — ``authorization_path`` x ``object_state`` x
  ``if_exists_clause`` x ``multi_user_clause`` x ``role_name_shape`` x
  ``dependency_context``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_user_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_user_factor_loop_plan,
)


class DropUserFactorExtensionError(ValueError):
    """Raised when a frozen DROP USER extension input drifts."""


@dataclass(frozen=True)
class DropUserFactorExtensionCase:
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
class DropUserFactorExtensionPlan:
    cases: tuple[DropUserFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 39
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "reassign_objects_then_drop",
    "drop_role",
    "terminate_sessions",
)

# Dense baseline assignment (all positive values).  The negative factors
# (authorization_path=non_createrole, object_state=absent /
# role_name_shape=non_existent_name under if_exists_clause=absent,
# dependency_context in role_owns_objects/role_has_active_sessions) are
# crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_user",
    "grammar_branch": "branch_1",
    "target_action": "drop_user",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "multi_user_clause": "single_role",
    "authorization_path": "createrole",
    "role_dependency": "no_dependencies",
    "role_name_shape": "simple_id",
    "privilege_context": "createrole_session",
    "dependency_context": "no_dependencies",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "reassign_objects_then_drop",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_user": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_user": "drop_user",
}

# Crossed positive behaviour axes per branch.  The privilege twin
# (privilege_context) and dependency twin (role_dependency) are derived from
# authorization_path / dependency_context respectively (not crossed
# independently) so the cartesian product stays well under the cap without
# truncation while every twin value remains baseline-covered.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_user": {
        "object_state": ("exists", "absent"),
        "if_exists_clause": ("present", "absent"),
        "multi_user_clause": ("single_role", "multiple_roles"),
        "authorization_path": (
            "createrole",
            "superuser",
            "non_createrole",
        ),
        "role_name_shape": (
            "simple_id",
            "quoted_id",
            "reserved_word_id",
            "non_existent_name",
        ),
        "dependency_context": (
            "no_dependencies",
            "role_owns_objects",
            "role_has_active_sessions",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> object
# lookup -> dependency).  The privilege boundary (42501) fires first.  The
# object-lookup boundary (42704) fires when the target role is absent
# (object_state=absent or role_name_shape=non_existent_name) and IF EXISTS is
# omitted.  The dependency boundary (2BP01) fires when the role still owns
# objects or holds an active-session boundary (provisional).
_PRIVILEGE_NEGATIVE = ("authorization_path", "non_createrole")
_OBJECT_MISSING_OBJECT = ("object_state", "absent")
_OBJECT_MISSING_NAME = ("role_name_shape", "non_existent_name")
_DEPENDENCY_OWNS = ("dependency_context", "role_owns_objects")
_DEPENDENCY_SESSION = ("dependency_context", "role_has_active_sessions")
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("authorization_path") == "non_createrole"


def _object_lookup_failure_fires(assignment: dict[str, str]) -> bool:
    """role-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("object_state") == "absent"
        or assignment.get("role_name_shape") == "non_existent_name"
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("dependency_context") in (
        "role_owns_objects",
        "role_has_active_sessions",
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
    target role is absent and IF EXISTS is omitted.  The dependency boundary
    (2BP01) fires last (owns objects or active-session boundary).
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _object_lookup_failure_fires(assignment):
        if assignment.get("object_state") == "absent":
            return _OBJECT_MISSING_OBJECT
        return _OBJECT_MISSING_NAME
    if _dependency_failure_fires(assignment):
        if assignment.get("dependency_context") == "role_has_active_sessions":
            return _DEPENDENCY_SESSION
        return _DEPENDENCY_OWNS
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    return _failure_unit_count(assignment) <= 1


def _derive_privilege_context(authorization_path: str) -> str:
    if authorization_path == "superuser":
        return "superuser_session"
    if authorization_path == "non_createrole":
        return "non_createrole_session"
    return "createrole_session"


def _derive_role_dependency(dependency_context: str) -> str:
    if dependency_context == "role_owns_objects":
        return "owns_objects"
    if dependency_context == "role_has_active_sessions":
        return "has_active_connections"
    return "no_dependencies"


def _derive_error_type(pair: tuple[str, str] | None) -> str:
    if pair is None:
        return "none"
    if pair == _PRIVILEGE_NEGATIVE:
        return "insufficient_privilege"
    if pair in (_OBJECT_MISSING_OBJECT, _OBJECT_MISSING_NAME):
        return "non_existent_without_if_exists"
    return "role_owns_objects"


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
            # Derive the twin factors so the assignment stays semantically
            # consistent without an independent cartesian blow-up.
            assignment["privilege_context"] = _derive_privilege_context(
                assignment["authorization_path"]
            )
            assignment["role_dependency"] = _derive_role_dependency(
                assignment["dependency_context"]
            )
            if not _is_valid_combination(assignment):
                continue
            pair = _present_failure_pair(assignment)
            assignment["expected_status"] = (
                "failure" if pair is not None else "success"
            )
            assignment["error_type"] = _derive_error_type(pair)
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
    cases: tuple[DropUserFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-user-factor-extension-v1\n")
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
    cases: tuple[DropUserFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP USER extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_user_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP USER",
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


def build_drop_user_factor_extension_plan(
    repository_root: Path,
) -> DropUserFactorExtensionPlan:
    """Build the bounded DROP USER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_user_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropUserFactorExtensionCase] = []
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
                    DropUserFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPUSER{ordinal:05d}",
                        sql_filename=f"DROPUSER{ordinal:05d}.sql",
                        object_prefix=f"dropuser_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPUSER-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_user_required_baseline_factor_space"
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
    return DropUserFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropUserFactorExtensionError",
    "DropUserFactorExtensionCase",
    "DropUserFactorExtensionPlan",
    "build_drop_user_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
