"""Bounded post-coverage cross-factor extension expander for DROP TABLESPACE.

The marginal factor-value-loop (:mod:`drop_tablespace_factor_loop`) is the
required baseline: one program per factor value, 45 local cases (GRM 1 +
SFV 42 + Risk 2).  This module adds the bounded post-coverage extension
phase: cross-factor combinations of the behaviour axes across the single
official synopsis branch (at most one failure-causing value per case, so
attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.

The single official synopsis branch is crossed:

* ``branch_drop_tablespace`` — ``authorization_path`` x ``object_state`` x
  ``if_exists_clause`` x ``object_occupancy`` x ``tablespace_name_shape`` x
  ``environment_context`` x ``dependency_context``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_tablespace_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_tablespace_factor_loop_plan,
)


class DropTablespaceFactorExtensionError(ValueError):
    """Raised when a frozen DROP TABLESPACE extension input drifts."""


@dataclass(frozen=True)
class DropTablespaceFactorExtensionCase:
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
class DropTablespaceFactorExtensionPlan:
    cases: tuple[DropTablespaceFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 45
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "remove_objects_first",
    "drop_tablespace",
    "reset_temp_tablespaces",
)

# Dense baseline assignment (all positive values).  The negative factors
# (authorization_path=non_owner_non_superuser, object_state=absent /
# tablespace_name_shape=non_existent_name when if_exists_clause=absent,
# object_occupancy!=empty / dependency_context!=no_dependencies /
# environment_context=active_temp_tablespaces) are crossed here with
# at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_tablespace",
    "grammar_branch": "branch_1",
    "target_action": "drop_tablespace",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "authorization_path": "superuser",
    "object_occupancy": "empty",
    "tablespace_name_shape": "simple_id",
    "privilege_context": "superuser_session",
    "dependency_context": "no_dependencies",
    "environment_context": "outside_transaction_block",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "remove_objects_first",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_tablespace": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_tablespace": "drop_tablespace",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_tablespace": {
        "authorization_path": (
            "superuser",
            "owner",
            "non_owner_non_superuser",
        ),
        "object_state": ("exists", "absent"),
        "if_exists_clause": ("present", "absent"),
        "object_occupancy": (
            "empty",
            "has_objects_in_current_db",
            "has_objects_in_other_db",
            "has_temp_files",
        ),
        "tablespace_name_shape": (
            "simple_id",
            "quoted_id",
            "reserved_word_id",
            "non_existent_name",
            "existing_name",
        ),
        "environment_context": (
            "outside_transaction_block",
            "inside_transaction_block",
            "active_temp_tablespaces",
        ),
        "dependency_context": (
            "no_dependencies",
            "objects_in_current_db",
            "objects_in_other_db",
            "temp_tablespace_active",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: transaction block ->
# privilege -> object lookup -> occupied/temp).  The transaction-block
# boundary (25001) fires when the statement runs inside a txn.  The privilege
# boundary (42501) fires when the executor is a non-owner non-superuser.
# The object-lookup boundary (42704) fires when the tablespace is absent
# (object_state=absent or tablespace_name_shape=non_existent_name) and IF
# EXISTS is omitted.  The occupied boundary (55006) fires when the tablespace
# is occupied (object_occupancy != empty, or dependency_context !=
# no_dependencies, or environment_context=active_temp_tablespaces).
_TRANSACTION_NEGATIVE = ("environment_context", "inside_transaction_block")
_PRIVILEGE_NEGATIVE = ("authorization_path", "non_owner_non_superuser")
_OBJECT_MISSING_STATE = ("object_state", "absent")
_OBJECT_MISSING_NAME = ("tablespace_name_shape", "non_existent_name")
_OCCUPIED_OCCUPANCY_VALUES = frozenset(
    {"has_objects_in_current_db", "has_objects_in_other_db", "has_temp_files"}
)
_OCCUPIED_DEPENDENCY_VALUES = frozenset(
    {"objects_in_current_db", "objects_in_other_db", "temp_tablespace_active"}
)
_TEMP_ENVIRONMENT = "active_temp_tablespaces"
_TEMP_DEPENDENCY = "temp_tablespace_active"
_TEMP_OCCUPANCY = "has_temp_files"
_IF_EXISTS_OMITTED = "absent"


def _transaction_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("environment_context") == "inside_transaction_block"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("authorization_path") == "non_owner_non_superuser"


def _object_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """object-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("object_state") == "absent"
        or assignment.get("tablespace_name_shape") == "non_existent_name"
    )


def _occupied_failure_fires(assignment: dict[str, str]) -> bool:
    """occupied/temp fires when the tablespace holds objects or temp files."""

    if assignment.get("object_occupancy") in _OCCUPIED_OCCUPANCY_VALUES:
        return True
    if assignment.get("dependency_context") in _OCCUPIED_DEPENDENCY_VALUES:
        return True
    if assignment.get("environment_context") == _TEMP_ENVIRONMENT:
        return True
    return False


def _is_temp_occupied(assignment: dict[str, str]) -> bool:
    """Whether the occupied failure is the temp-tablespace variant."""

    return (
        assignment.get("object_occupancy") == _TEMP_OCCUPANCY
        or assignment.get("dependency_context") == _TEMP_DEPENDENCY
        or assignment.get("environment_context") == _TEMP_ENVIRONMENT
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _transaction_failure_fires(assignment):
        count += 1
    if _privilege_failure_fires(assignment):
        count += 1
    if _object_missing_failure_fires(assignment):
        count += 1
    if _occupied_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The transaction-block boundary (25001) fires first.  The privilege
    boundary (42501) fires next.  The object-lookup boundary (42704) fires
    next when the tablespace is absent and IF EXISTS is omitted.  The
    occupied boundary (55006) fires last when the tablespace holds objects
    or temp files.
    """

    if _transaction_failure_fires(assignment):
        return _TRANSACTION_NEGATIVE
    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _object_missing_failure_fires(assignment):
        if assignment.get("object_state") == "absent":
            return _OBJECT_MISSING_STATE
        return _OBJECT_MISSING_NAME
    if _occupied_failure_fires(assignment):
        if _is_temp_occupied(assignment):
            return ("dependency_context", _TEMP_DEPENDENCY)
        return ("object_occupancy", "has_objects_in_current_db")
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    return _failure_unit_count(assignment) <= 1


_AUTH_PRIVILEGE_MAP: dict[str, str] = {
    "superuser": "superuser_session",
    "owner": "owner_session",
    "non_owner_non_superuser": "non_owner_session",
}
_OCCUPANCY_DEPENDENCY_MAP: dict[str, str] = {
    "empty": "no_dependencies",
    "has_objects_in_current_db": "objects_in_current_db",
    "has_objects_in_other_db": "objects_in_other_db",
    "has_temp_files": "temp_tablespace_active",
}


def _derive_correlated(assignment: dict[str, str]) -> None:
    """Derive privilege_context, dependency_context, error_type in place."""

    auth = assignment.get("authorization_path", "superuser")
    assignment["privilege_context"] = _AUTH_PRIVILEGE_MAP.get(
        auth, assignment["privilege_context"]
    )
    occ = assignment.get("object_occupancy", "empty")
    dep = _OCCUPANCY_DEPENDENCY_MAP.get(occ)
    if dep is not None:
        assignment["dependency_context"] = dep
    pair = _present_failure_pair(assignment)
    if pair is None:
        assignment["error_type"] = "none"
    elif pair == _TRANSACTION_NEGATIVE:
        assignment["error_type"] = "inside_transaction_block"
    elif pair == _PRIVILEGE_NEGATIVE:
        assignment["error_type"] = "insufficient_privilege"
    elif pair in (_OBJECT_MISSING_STATE, _OBJECT_MISSING_NAME):
        assignment["error_type"] = "non_existent_without_if_exists"
    else:
        assignment["error_type"] = (
            "temp_tablespace_in_use"
            if _is_temp_occupied(assignment)
            else "occupied_tablespace"
        )


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
            _derive_correlated(assignment)
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
    cases: tuple[DropTablespaceFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-tablespace-factor-extension-v1\n")
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
    cases: tuple[DropTablespaceFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP TABLESPACE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_tablespace_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP TABLESPACE",
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


def build_drop_tablespace_factor_extension_plan(
    repository_root: Path,
) -> DropTablespaceFactorExtensionPlan:
    """Build the bounded DROP TABLESPACE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_tablespace_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropTablespaceFactorExtensionCase] = []
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
                    DropTablespaceFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPTABLESPACE{ordinal:05d}",
                        sql_filename=f"DROPTABLESPACE{ordinal:05d}.sql",
                        object_prefix=f"droptablespace_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPTABLESPACE-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_tablespace_required_baseline_factor_space"
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
    return DropTablespaceFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropTablespaceFactorExtensionError",
    "DropTablespaceFactorExtensionCase",
    "DropTablespaceFactorExtensionPlan",
    "build_drop_tablespace_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
