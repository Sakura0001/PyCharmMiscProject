"""Bounded post-coverage cross-factor extension expander for DROP SERVER.

The marginal factor-value-loop (:mod:`drop_server_factor_loop`) is the
required baseline: one program per factor value, 39 local cases
(GRM 1 + SFV 36 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across the
single official synopsis branch (at most one failure-causing value per case,
so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_context=non_owner_no_privilege``, a
non-existent server when ``if_exists_clause=without_if_exists``, and
``user_mapping_dependency=has_user_mapping_dependency`` under a non-CASCADE
drop policy) are crossed here with at-most-one-failure attribution; the
privilege boundary fires first (42501), then the not-exist boundary (42704),
then the dependency boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_drop_server`` — ``privilege_context`` x ``server_existence`` x
  ``server_name_shape`` x ``if_exists_clause`` x ``cascade_restrict_clause`` x
  ``user_mapping_dependency`` x ``multi_target``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_server_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_server_factor_loop_plan,
)


class DropServerFactorExtensionError(ValueError):
    """Raised when a frozen DROP SERVER extension input drifts."""


@dataclass(frozen=True)
class DropServerFactorExtensionCase:
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
class DropServerFactorExtensionPlan:
    cases: tuple[DropServerFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 39
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_foreign_server_catalog",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_server_cascade",
    "drop_user_mapping_then_drop_server",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_context=non_owner_no_privilege, server_existence=server_not_exists,
# server_name_shape=non_existing_name, user_mapping_dependency=
# has_user_mapping_dependency) are crossed here with at-most-one-failure
# attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_server",
    "grammar_branch": "branch_1",
    "target_action": "drop_server",
    "server_existence": "server_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "privilege_context": "superuser",
    "multi_target": "single_target",
    "server_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "user_mapping_dependency": "no_user_mapping_dependency",
    "nonexistent_server": "server_does_not_exist",
    "privilege_insufficient": "non_owner_dropping_server",
    "dependent_user_mapping": "restrict_with_user_mapping_fails",
    "verification_mode": "pg_foreign_server_catalog",
    "cleanup_mode": "drop_server_cascade",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_server": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_server": "drop_server",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_server": {
        "privilege_context": (
            "non_owner_no_privilege",
            "owner_of_server",
            "superuser",
        ),
        "server_existence": (
            "server_exists",
            "server_not_exists",
        ),
        "server_name_shape": (
            "non_existing_name",
            "quoted_name",
            "reserved_word_name",
            "simple_name",
        ),
        "if_exists_clause": ("without_if_exists", "with_if_exists"),
        "cascade_restrict_clause": (
            "cascade",
            "no_clause_default_restrict",
            "restrict",
        ),
        "user_mapping_dependency": (
            "has_user_mapping_dependency",
            "no_user_mapping_dependency",
        ),
        "multi_target": (
            "multi_target_all_exist",
            "multi_target_some_not_exist",
            "single_target",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege → lookup →
# dependency).  The privilege boundary (42501) fires first.  The not-exist
# boundary (42704) fires when the target server is absent (server does not
# exist, the name is non-existing, or a multi-target list names a missing
# server) AND IF EXISTS is omitted.  The dependency boundary (2BP01) fires
# when a user mapping depends on the server and the drop policy is not
# CASCADE.
_PRIVILEGE_NEGATIVE = ("privilege_context", "non_owner_no_privilege")
_IF_EXISTS_OMITTED = "without_if_exists"
_ABSENT_NAME_SHAPES = frozenset({"non_existing_name"})
_RESTRICT_VALUES = frozenset({"no_clause_default_restrict", "restrict"})


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_context") == "non_owner_no_privilege"


def _server_absent(assignment: dict[str, str]) -> bool:
    """Whether the target server is absent before the drop."""

    if assignment.get("server_existence") == "server_not_exists":
        return True
    if assignment.get("server_name_shape") in _ABSENT_NAME_SHAPES:
        return True
    if assignment.get("multi_target") == "multi_target_some_not_exist":
        return True
    return False


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    """A not-exist error fires only when IF EXISTS is omitted."""

    return (
        _server_absent(assignment)
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has_user_mapping_dependency fires only under a non-CASCADE drop."""

    return (
        assignment.get("user_mapping_dependency") == "has_user_mapping_dependency"
        and assignment.get("cascade_restrict_clause") in _RESTRICT_VALUES
        and not _server_absent(assignment)
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
    attributed first.  The not-exist boundary (42704) fires next when the
    server is absent and IF EXISTS is omitted.  The dependency boundary
    (2BP01) fires last under a non-CASCADE drop with a user mapping.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _not_exist_failure_fires(assignment):
        if assignment.get("server_existence") == "server_not_exists":
            return ("server_existence", "server_not_exists")
        if assignment.get("server_name_shape") in _ABSENT_NAME_SHAPES:
            return ("server_name_shape", "non_existing_name")
        return ("multi_target", "multi_target_some_not_exist")
    if _dependency_failure_fires(assignment):
        return ("user_mapping_dependency", "has_user_mapping_dependency")
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
    cases: tuple[DropServerFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-server-factor-extension-v1\n")
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
    cases: tuple[DropServerFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP SERVER extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_server_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP SERVER",
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


def build_drop_server_factor_extension_plan(
    repository_root: Path,
) -> DropServerFactorExtensionPlan:
    """Build the bounded DROP SERVER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_server_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropServerFactorExtensionCase] = []
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
                    DropServerFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPSERVER{ordinal:05d}",
                        sql_filename=f"DROPSERVER{ordinal:05d}.sql",
                        object_prefix=f"dropserver_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPSERVER-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_server_required_baseline_factor_space"
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
    return DropServerFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropServerFactorExtensionError",
    "DropServerFactorExtensionCase",
    "DropServerFactorExtensionPlan",
    "build_drop_server_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
