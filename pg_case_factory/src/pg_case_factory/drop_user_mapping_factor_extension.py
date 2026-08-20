"""Bounded post-coverage cross-factor extension expander for DROP USER MAPPING.

The marginal factor-value-loop (:mod:`drop_user_mapping_factor_loop`) is the
required baseline: one program per factor value, 46 local cases (GRM 1 +
SFV 43 + Risk 2).  This module adds the bounded post-coverage extension
phase: cross-factor combinations of the behaviour axes across the single
official synopsis branch (at most one failure-causing value per case, so
attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``authorization_path=non_privileged`` when dropping
another's or a PUBLIC mapping, ``object_state=absent`` when
``if_exists_clause=absent``, ``server_existence=server_not_exists``,
``server_name_shape=nonexistent_name``) are crossed here with
at-most-one-failure attribution; the privilege boundary fires first
(42501), then the server-lookup boundary (42704), then the mapping-lookup
boundary (42704).

The single official synopsis branch is crossed:

* ``branch_drop_user_mapping`` — ``authorization_path`` x ``server_existence``
  x ``object_state`` x ``if_exists_clause`` x ``user_specification`` x
  ``server_name_shape``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_user_mapping_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_user_mapping_factor_loop_plan,
)


class DropUserMappingFactorExtensionError(ValueError):
    """Raised when a frozen DROP USER MAPPING extension input drifts."""


@dataclass(frozen=True)
class DropUserMappingFactorExtensionCase:
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
class DropUserMappingFactorExtensionPlan:
    cases: tuple[DropUserMappingFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 46
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "drop_user_mapping",
    "drop_server",
    "drop_fdw",
)

# Dense baseline assignment (all positive values).  The negative factors
# (authorization_path=non_privileged, object_state=absent,
# server_existence=server_not_exists, server_name_shape=nonexistent_name)
# are crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_user_mapping",
    "grammar_branch": "branch_1",
    "target_action": "drop_user_mapping",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "user_specification": "named_user",
    "user_name_shape": "simple_id",
    "server_name_shape": "simple_id",
    "server_existence": "server_exists",
    "authorization_path": "server_owner",
    "privilege_context": "server_owner_session",
    "insufficient_privilege": "has_privilege",
    "self_mapping_only": "deleting_own_mapping",
    "nonexistent_mapping": "mapping_exists",
    "nonexistent_server": "server_exists",
    "server_dependency": "server_exists_and_valid",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_user_mapping",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_user_mapping": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_user_mapping": "drop_user_mapping",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_user_mapping": {
        "authorization_path": (
            "non_privileged",
            "server_owner",
            "user_with_usage",
        ),
        "server_existence": ("server_exists", "server_not_exists"),
        "object_state": ("exists", "absent"),
        "if_exists_clause": ("present", "absent"),
        "user_specification": (
            "named_user",
            "public",
            "current_user",
            "current_role",
            "user_keyword",
        ),
        "server_name_shape": ("simple_id", "nonexistent_name"),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> server
# lookup -> mapping lookup).  The privilege boundary (42501) fires for a
# non-privileged user dropping another's or a PUBLIC mapping — but NOT when
# the user drops their own mapping (current_user/current_role/user_keyword).
# The server-lookup boundary (42704) fires when the server is absent.
# The mapping-lookup boundary (42704) fires when the mapping is absent and
# IF EXISTS is omitted.
_PRIVILEGE_NEGATIVE = ("authorization_path", "non_privileged")
_SERVER_MISSING_NEGATIVE = ("server_existence", "server_not_exists")
_SERVER_NAME_NEGATIVE = ("server_name_shape", "nonexistent_name")
_MAPPING_MISSING = ("object_state", "absent")
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    """Privilege fires for any non-privileged session (provisional no-DB)."""

    return assignment.get("authorization_path") == "non_privileged"


def _server_missing_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("server_existence") == "server_not_exists"


def _server_name_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("server_name_shape") == "nonexistent_name"


def _mapping_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """mapping-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return assignment.get("object_state") == "absent"


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _server_missing_failure_fires(assignment):
        count += 1
    if _server_name_failure_fires(assignment):
        count += 1
    if _mapping_missing_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _server_missing_failure_fires(assignment):
        return _SERVER_MISSING_NEGATIVE
    if _server_name_failure_fires(assignment):
        return _SERVER_NAME_NEGATIVE
    if _mapping_missing_failure_fires(assignment):
        return _MAPPING_MISSING
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    return _failure_unit_count(assignment) <= 1


def _derive_factors(assignment: dict[str, str]) -> dict[str, str]:
    """Derive held-constant/redundant factors from the crossed axes."""

    a = dict(assignment)
    pair = _present_failure_pair(a)
    a["expected_status"] = "failure" if pair is not None else "success"
    # insufficient_privilege / privilege_context derived from authorization_path
    if a["authorization_path"] == "non_privileged":
        a["insufficient_privilege"] = "lacks_privilege"
        a["privilege_context"] = "non_privileged_session"
    elif a["authorization_path"] == "server_owner":
        a["insufficient_privilege"] = "has_privilege"
        a["privilege_context"] = "server_owner_session"
    else:  # user_with_usage
        a["insufficient_privilege"] = "has_privilege"
        a["privilege_context"] = "user_with_usage_session"
    # self_mapping_only derived from authorization_path + user_specification
    if a["authorization_path"] == "non_privileged" and a[
        "user_specification"
    ] not in ("current_user", "current_role", "user_keyword"):
        a["self_mapping_only"] = "attempting_other_user_mapping"
    else:
        a["self_mapping_only"] = "deleting_own_mapping"
    # nonexistent_mapping derived from object_state + if_exists_clause
    if a["object_state"] == "absent" and a["if_exists_clause"] == "absent":
        a["nonexistent_mapping"] = "mapping_missing_without_if_exists"
    else:
        a["nonexistent_mapping"] = "mapping_exists"
    # nonexistent_server / server_dependency derived from server_existence + name
    if (
        a["server_existence"] == "server_not_exists"
        or a["server_name_shape"] == "nonexistent_name"
    ):
        a["nonexistent_server"] = "server_missing"
    else:
        a["nonexistent_server"] = "server_exists"
    if a["server_existence"] == "server_not_exists":
        a["server_dependency"] = "server_missing"
    else:
        a["server_dependency"] = "server_exists_and_valid"
    # user_name_shape derived from user_specification
    if a["user_specification"] == "public":
        a["user_name_shape"] = "public_keyword"
    else:
        a["user_name_shape"] = "simple_id"
    return a


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
            assignment = _derive_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
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
    cases: tuple[DropUserMappingFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-user-mapping-factor-extension-v1\n")
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
    cases: tuple[DropUserMappingFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP USER MAPPING extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_user_mapping_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP USER MAPPING",
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


def build_drop_user_mapping_factor_extension_plan(
    repository_root: Path,
) -> DropUserMappingFactorExtensionPlan:
    """Build the bounded DROP USER MAPPING post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_user_mapping_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropUserMappingFactorExtensionCase] = []
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
                    DropUserMappingFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPUSERMAPPING{ordinal:05d}",
                        sql_filename=f"DROPUSERMAPPING{ordinal:05d}.sql",
                        object_prefix=f"dropusermapping_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPUSERMAPPING-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_user_mapping_required_baseline_factor_space"
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
    return DropUserMappingFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropUserMappingFactorExtensionError",
    "DropUserMappingFactorExtensionCase",
    "DropUserMappingFactorExtensionPlan",
    "build_drop_user_mapping_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
