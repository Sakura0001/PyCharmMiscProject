"""Bounded post-coverage cross-factor extension expander for ALTER TEXT SEARCH DICTIONARY.

The marginal factor-value-loop (:mod:`alter_text_search_dictionary_factor_loop`) is
the required baseline: one program per factor value, 64 local cases
(GRM 4 + SFV 60).  This module adds the bounded post-coverage extension
phase allowed by ``alter_text_search_dictionary.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 4 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode``/``cleanup_mode`` crossed so every
declared T6 value is exercised.

The T5 single-value factors (nonexistent_dict, duplicate_new_name,
nonexistent_owner_role, nonexistent_target_schema, non_owner_attempt,
cannot_set_role) are derived from their T1-T4 counterparts, not crossed
as axes.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``post_coverage_extension_policy.required_fields``) and is marked
``is_extension``.  Filtering happens BEFORE counting (``raw += 1``), so
``raw_combination_count == len(cases)`` and ``dropped_count == 0``
(no over-pruning).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_text_search_dictionary_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_text_search_dictionary_factor_loop_plan,
)


class AlterTextSearchDictionaryFactorExtensionError(ValueError):
    """Raised when a frozen ALTER TEXT SEARCH DICTIONARY extension input drifts."""


@dataclass(frozen=True)
class AlterTextSearchDictionaryFactorExtensionCase:
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
class AlterTextSearchDictionaryFactorExtensionPlan:
    cases: tuple[AlterTextSearchDictionaryFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 64
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_ts_dict",
    "option_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "revert_option",
    "revert_rename",
    "revert_owner",
    "drop_text_search_dictionary",
    "role_cleanup",
)

# General axes crossed for ALL 4 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "exists",
        "not_exists",
    ),
    "dict_name_shape": (
        "simple_id",
        "quoted_id",
        "nonexistent_name",
    ),
    "privilege_level": (
        "owner",
        "non_owner",
        "superuser",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch / alter_action are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "exists",
    "expected_status": "success",
    "alter_action": "option_modify",
    "option_action": "set_new_value",
    "owner_target": "specified_new_owner",
    "dict_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "schema_name_shape": "simple_id",
    "privilege_level": "owner",
    "role_existence": "role_exists",
    "set_role_capability": "can_set_role",
    "schema_existence": "schema_exists",
    "nonexistent_dict": "dict_exists",
    "duplicate_new_name": "no_conflict",
    "nonexistent_owner_role": "role_exists",
    "nonexistent_target_schema": "schema_exists",
    "non_owner_attempt": "owner_execution",
    "cannot_set_role": "can_set_role",
    "verification_mode": "catalog_query_pg_ts_dict",
    "cleanup_mode": "revert_option",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_option",
        "option_modify",
        {
            "option_action": (
                "set_new_value",
                "remove_option_restore_default",
                "dummy_refresh",
            ),
        },
    ),
    (
        "branch_rename",
        "rename",
        {
            "new_name_shape": (
                "simple_id",
                "quoted_id",
                "duplicate_name",
            ),
        },
    ),
    (
        "branch_owner",
        "owner",
        {
            "owner_target": (
                "specified_new_owner",
                "specified_current_role",
                "specified_current_user",
                "specified_session_user",
            ),
        },
    ),
    (
        "branch_set_schema",
        "set_schema",
        {
            "schema_name_shape": (
                "simple_id",
                "nonexistent_schema",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T5/T4 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("privilege_level", "non_owner"),
        ("new_name_shape", "duplicate_name"),
        ("schema_name_shape", "nonexistent_schema"),
    }
)


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return sum(
        1
        for factor, value in _CROSSED_NEGATIVES
        if assignment.get(factor) == value
    )


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    os_ = assignment.get("object_state", "exists")
    dns = assignment.get("dict_name_shape", "simple_id")
    if os_ == "not_exists" and dns != "nonexistent_name":
        return False
    if os_ != "not_exists" and dns == "nonexistent_name":
        return False

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "exists")
    dns = a.get("dict_name_shape", "simple_id")
    pl = a.get("privilege_level", "owner")
    nns = a.get("new_name_shape", "simple_id")
    ons = a.get("owner_name_shape", "simple_id")
    sns = a.get("schema_name_shape", "simple_id")
    src = a.get("set_role_capability", "can_set_role")

    if os_ == "not_exists" or dns == "nonexistent_name":
        a["nonexistent_dict"] = "dict_missing"
    else:
        a["nonexistent_dict"] = "dict_exists"

    if pl == "non_owner":
        a["non_owner_attempt"] = "non_owner_execution"
    else:
        a["non_owner_attempt"] = "owner_execution"

    if nns == "duplicate_name":
        a["duplicate_new_name"] = "same_name_conflict"
    else:
        a["duplicate_new_name"] = "no_conflict"

    if ons == "nonexistent_role":
        a["nonexistent_owner_role"] = "role_missing"
        a["role_existence"] = "role_not_exists"
    else:
        a["nonexistent_owner_role"] = "role_exists"
        a["role_existence"] = "role_exists"

    if sns == "nonexistent_schema":
        a["nonexistent_target_schema"] = "schema_missing"
        a["schema_existence"] = "schema_not_exists"
    else:
        a["nonexistent_target_schema"] = "schema_exists"
        a["schema_existence"] = "schema_exists"

    if src == "cannot_set_role":
        a["cannot_set_role"] = "cannot_set_role_to_target"
    else:
        a["cannot_set_role"] = "can_set_role"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, action, axes in _BRANCH_CONFIG:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(
            *[all_axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = branch
            assignment["target_action"] = action
            assignment["alter_action"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise AlterTextSearchDictionaryFactorExtensionError(
                    "duplicate factor key in extension assignment"
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
    cases: tuple[AlterTextSearchDictionaryFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-text-search-dictionary-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(
                        case.factor_assignment
                    ),
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": (
                        case.expected_failure_reason
                    ),
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
    cases: tuple[AlterTextSearchDictionaryFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER TEXT SEARCH DICTIONARY extension "
                    f"{case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": (
                        "alter_text_search_dictionary_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER TEXT SEARCH DICTIONARY",
                    "primary_fence": (
                        "primary-target-begin/end"
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment[
                        "verification_mode"
                    ],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment["cleanup_mode"],
                },
            }
        )
    return yaml.safe_dump(
        entries, sort_keys=False, allow_unicode=True
    )


def build_alter_text_search_dictionary_factor_extension_plan(
    repository_root: Path,
) -> AlterTextSearchDictionaryFactorExtensionPlan:
    """Build the bounded ALTER TEXT SEARCH DICTIONARY post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_text_search_dictionary_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterTextSearchDictionaryFactorExtensionCase] = []
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
                outcome, sqlstate, reason = _outcome_for(
                    assignment
                )
                ordinal += 1
                cases.append(
                    AlterTextSearchDictionaryFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"ALTERTEXTSEARCHDICTIONARY{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"ALTERTEXTSEARCHDICTIONARY{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"alter_text_search_dictionary_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"ATSD-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_text_search_dictionary_required_"
                            "factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x verification_mode="
                            f"{verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "target_action"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return AlterTextSearchDictionaryFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(
            cases_tuple
        ),
        derived_combinations_yaml=_derived_combinations_yaml(
            cases_tuple
        ),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterTextSearchDictionaryFactorExtensionError",
    "AlterTextSearchDictionaryFactorExtensionCase",
    "AlterTextSearchDictionaryFactorExtensionPlan",
    "build_alter_text_search_dictionary_factor_extension_plan",
]
