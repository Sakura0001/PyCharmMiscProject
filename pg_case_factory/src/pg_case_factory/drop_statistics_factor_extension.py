"""Bounded post-coverage cross-factor extension expander for DROP STATISTICS.

The marginal factor-value-loop (:mod:`drop_statistics_factor_loop`) is the
required baseline: one program per factor value, 35 local cases (GRM 1 +
SFV 32 + Risk 2).  This module adds the bounded post-coverage extension
phase: cross-factor combinations of the behaviour axes across the single
official synopsis branch (at most one failure-causing value per case, so
attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_context=non_owner_no_privilege``,
``executor_privilege=non_owner_no_privilege``,
``statistics_existence=statistics_not_exists`` /
``statistics_name_shape=non_existing_name`` /
``multi_target=multi_target_some_not_exist`` when
``if_exists_clause=without_if_exists``) are crossed here with
at-most-one-failure attribution; the privilege boundary fires first (42501),
then the statistics-lookup boundary (42704).

The single official synopsis branch is crossed:

* ``branch_drop_statistics`` — ``privilege_context`` x
  ``statistics_existence`` x ``if_exists_clause`` x
  ``cascade_restrict_clause`` x ``multi_target`` x
  ``statistics_name_shape`` x ``executor_privilege``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_statistics_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_statistics_factor_loop_plan,
)


class DropStatisticsFactorExtensionError(ValueError):
    """Raised when a frozen DROP STATISTICS extension input drifts."""


@dataclass(frozen=True)
class DropStatisticsFactorExtensionCase:
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
class DropStatisticsFactorExtensionPlan:
    cases: tuple[DropStatisticsFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 35
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_statistic_ext_catalog",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_statistics",
)

# Dense baseline assignment (all positive values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_statistics",
    "grammar_branch": "branch_1",
    "target_action": "drop_statistics",
    "statistics_existence": "statistics_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "privilege_context": "superuser",
    "multi_target": "single_target",
    "statistics_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "nonexistent_statistics": "statistics_does_not_exist",
    "privilege_insufficient": "non_table_owner_dropping_statistics",
    "verification_mode": "pg_statistic_ext_catalog",
    "cleanup_mode": "drop_statistics",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_statistics": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_statistics": "drop_statistics",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_statistics": {
        "privilege_context": (
            "superuser",
            "table_owner",
            "non_owner_no_privilege",
        ),
        "statistics_existence": (
            "statistics_exists",
            "statistics_not_exists",
        ),
        "if_exists_clause": ("with_if_exists", "without_if_exists"),
        "cascade_restrict_clause": (
            "no_clause_default_restrict",
            "cascade",
            "restrict",
        ),
        "multi_target": (
            "single_target",
            "multi_target_all_exist",
            "multi_target_some_not_exist",
        ),
        "statistics_name_shape": (
            "simple_name",
            "schema_qualified_name",
            "quoted_name",
            "reserved_word_name",
            "non_existing_name",
        ),
        "executor_privilege": (
            "superuser",
            "table_owner",
            "non_owner_no_privilege",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> statistics
# lookup).  The privilege boundary (42501) fires first — when either
# privilege_context or executor_privilege is non_owner.  The statistics-lookup
# boundary (42704) fires when the statistics is absent (statistics_existence=
# statistics_not_exists, or statistics_name_shape=non_existing_name, or
# multi_target=multi_target_some_not_exist) AND if_exists_clause=
# without_if_exists (IF EXISTS omitted so a missing statistics surfaces a
# hard error rather than a notice).
_PRIVILEGE_NEGATIVE_CTX = ("privilege_context", "non_owner_no_privilege")
_PRIVILEGE_NEGATIVE_EXE = ("executor_privilege", "non_owner_no_privilege")
_STATS_MISSING_EXIST = ("statistics_existence", "statistics_not_exists")
_STATS_MISSING_NAME = ("statistics_name_shape", "non_existing_name")
_STATS_MISSING_MULTI = ("multi_target", "multi_target_some_not_exist")
_IF_EXISTS_OMITTED = "without_if_exists"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("privilege_context") == "non_owner_no_privilege"
        or assignment.get("executor_privilege") == "non_owner_no_privilege"
    )


def _stats_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """stats-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("statistics_existence") == "statistics_not_exists"
        or assignment.get("statistics_name_shape") == "non_existing_name"
        or assignment.get("multi_target") == "multi_target_some_not_exist"
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _stats_missing_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the statistics lookup, so it
    is attributed first.  The statistics-lookup boundary (42704) fires next
    when the statistics is absent and IF EXISTS is omitted.
    """

    if _privilege_failure_fires(assignment):
        if assignment.get("privilege_context") == "non_owner_no_privilege":
            return _PRIVILEGE_NEGATIVE_CTX
        return _PRIVILEGE_NEGATIVE_EXE
    if _stats_missing_failure_fires(assignment):
        if assignment.get("statistics_existence") == "statistics_not_exists":
            return _STATS_MISSING_EXIST
        if assignment.get("statistics_name_shape") == "non_existing_name":
            return _STATS_MISSING_NAME
        return _STATS_MISSING_MULTI
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
    cases: tuple[DropStatisticsFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-statistics-factor-extension-v1\n")
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
    cases: tuple[DropStatisticsFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP STATISTICS extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_statistics_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP STATISTICS",
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


def build_drop_statistics_factor_extension_plan(
    repository_root: Path,
) -> DropStatisticsFactorExtensionPlan:
    """Build the bounded DROP STATISTICS post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_statistics_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropStatisticsFactorExtensionCase] = []
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
                    DropStatisticsFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPSTATISTICS{ordinal:05d}",
                        sql_filename=f"DROPSTATISTICS{ordinal:05d}.sql",
                        object_prefix=f"dropstatistics_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPSTATISTICS-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_statistics_required_baseline_factor_space"
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
    return DropStatisticsFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropStatisticsFactorExtensionError",
    "DropStatisticsFactorExtensionCase",
    "DropStatisticsFactorExtensionPlan",
    "build_drop_statistics_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
