"""Bounded post-coverage cross-factor extension expander for DROP INDEX.

The marginal factor-value-loop (:mod:`drop_index_factor_loop`) is the required
baseline: one program per factor value, 56 local cases (GRM 1 + SFV 53 +
Risk 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed
so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``permission=non_owner``,
``object_state=not_exists`` when ``if_exists=false``,
``dependency_type=unique_pk_constraint`` under RESTRICT) are crossed here with
at-most-one-failure attribution; the privilege boundary fires first (42501),
then the not-exist boundary (42704), then the dependency boundary (2BP01).

The single official synopsis branch is crossed:

* ``drop_single`` — ``permission`` x ``object_state`` x ``if_exists`` x
  ``cascade_restrict`` x ``dependency_type``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_index_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_index_factor_loop_plan,
)


class DropIndexFactorExtensionError(ValueError):
    """Raised when a frozen DROP INDEX extension input drifts."""


@dataclass(frozen=True)
class DropIndexFactorExtensionCase:
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
class DropIndexFactorExtensionPlan:
    cases: tuple[DropIndexFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 56
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_absence_check",
    "constraint_integrity_check",
    "error_assertion",
)
_CLEANUP_MODES = (
    "explicit_drop",
    "cascade_auto_cleanup",
    "rollback",
)

# Dense baseline assignment (all positive values).  The negative factors
# (permission=non_owner, object_state=not_exists with if_exists=false,
# dependency_type=unique_pk_constraint under RESTRICT) are crossed here with
# at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "drop_single",
    "grammar_branch": "branch_1",
    "target_action": "drop_index",
    "object_state": "exists",
    "expected_status": "success",
    "concurrently": "false",
    "if_exists": "false",
    "cascade_restrict": "restrict",
    "multi_index": "single",
    "permission": "owner",
    "name_shape": "plain_identifier",
    "dependency_type": "no_dependency",
    "index_method": "btree",
    "invalid_combination": "none",
    "syntax_error": "none",
    "permission_insufficient": "none",
    "verification_mode": "catalog_absence_check",
    "cleanup_mode": "explicit_drop",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "drop_single": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "drop_single": "drop_index",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "drop_single": {
        "permission": (
            "non_owner",
            "owner",
            "superuser",
        ),
        "object_state": ("exists", "not_exists"),
        "if_exists": ("false", "true"),
        "cascade_restrict": ("restrict", "cascade"),
        "dependency_type": ("no_dependency", "unique_pk_constraint"),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> lookup ->
# dependency).  The privilege boundary (42501) fires first.  The not-exist
# boundary (42704) fires when the index is absent and IF EXISTS is omitted.
# The dependency boundary (2BP01) fires when RESTRICT is used with a unique/PK
# constraint depending on the index.
_PRIVILEGE_NEGATIVE = ("permission", "non_owner")
_NOT_EXIST_NEGATIVE = ("object_state", "not_exists")
_DEPENDENCY_NEGATIVE = ("dependency_type", "unique_pk_constraint")
_RESTRICT_VALUES = frozenset({"restrict"})
_IF_EXISTS_OMITTED = "false"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("permission") == "non_owner"


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    """object_state=not_exists fires only when IF EXISTS is omitted."""

    return (
        assignment.get("object_state") == "not_exists"
        and assignment.get("if_exists") == _IF_EXISTS_OMITTED
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """unique_pk_constraint fires only under a non-CASCADE drop policy."""

    return (
        assignment.get("dependency_type") == "unique_pk_constraint"
        and assignment.get("cascade_restrict") in _RESTRICT_VALUES
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
    attributed first.  The not-exist boundary (42704) fires next when the index
    is absent and IF EXISTS is omitted.  The dependency boundary (2BP01) fires
    last under RESTRICT with a dependent constraint.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
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
    cases: tuple[DropIndexFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-index-factor-extension-v1\n")
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
    cases: tuple[DropIndexFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP INDEX extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_index_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP INDEX",
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


def build_drop_index_factor_extension_plan(
    repository_root: Path,
) -> DropIndexFactorExtensionPlan:
    """Build the bounded DROP INDEX post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_index_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropIndexFactorExtensionCase] = []
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
                    DropIndexFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPINDEX{ordinal:05d}",
                        sql_filename=f"DROPINDEX{ordinal:05d}.sql",
                        object_prefix=f"dropindex_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPINDEX-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_index_required_baseline_factor_space"
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
    return DropIndexFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropIndexFactorExtensionError",
    "DropIndexFactorExtensionCase",
    "DropIndexFactorExtensionPlan",
    "build_drop_index_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
