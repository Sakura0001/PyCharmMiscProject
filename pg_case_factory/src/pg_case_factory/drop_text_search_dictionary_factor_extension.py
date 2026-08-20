"""Bounded post-coverage cross-factor extension expander for DROP TEXT SEARCH DICTIONARY.

The marginal factor-value-loop (:mod:`drop_text_search_dictionary_factor_loop`)
is the required baseline: one program per factor value, 38 local cases
(GRM 1 + SFV 35 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across the
single official synopsis branch (at most one failure-causing value per case,
so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The negative factors (``authorization_path=non_owner``,
``object_state=absent`` / ``dict_name_shape=non_existent_name`` when
``if_exists_clause=absent``, ``dependency_context=config_using_dict``
under RESTRICT) are crossed here with at-most-one-failure attribution; the
privilege boundary fires first (42501), then the object-lookup boundary
(42704), then the dependency boundary (2BP01).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_text_search_dictionary_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_text_search_dictionary_factor_loop_plan,
)


class DropTextSearchDictionaryFactorExtensionError(ValueError):
    """Raised when a frozen DROP TEXT SEARCH DICTIONARY extension input drifts."""


@dataclass(frozen=True)
class DropTextSearchDictionaryFactorExtensionCase:
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
class DropTextSearchDictionaryFactorExtensionPlan:
    cases: tuple[DropTextSearchDictionaryFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 38
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "cascade_cleanup",
    "manual_dependency_cleanup",
)

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_ts_dict",
    "grammar_branch": "branch_1",
    "target_action": "drop_text_search_dictionary",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict": "default_restrict",
    "authorization_path": "owner",
    "dependency_status": "no_dependencies",
    "dict_name_shape": "simple_id",
    "privilege_context": "owner_session",
    "dependency_context": "no_dependencies",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "cascade_cleanup",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_ts_dict": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_ts_dict": "drop_text_search_dictionary",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_ts_dict": {
        "authorization_path": (
            "non_owner",
            "owner",
            "superuser",
        ),
        "object_state": ("exists", "absent"),
        "if_exists_clause": ("present", "absent"),
        "cascade_restrict": (
            "default_restrict",
            "explicit_restrict",
            "explicit_cascade",
        ),
        "dependency_context": (
            "no_dependencies",
            "config_using_dict",
        ),
        "dict_name_shape": (
            "simple_id",
            "schema_qualified_id",
            "quoted_id",
            "reserved_word_id",
            "non_existent_name",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege ->
# object lookup -> dependency).  The privilege boundary (42501) fires first.
# The object-lookup boundary (42704) fires when the dictionary is absent
# (object_state=absent or dict_name_shape=non_existent_name) and IF EXISTS is
# omitted.  The dependency boundary (2BP01) fires when RESTRICT (or default
# RESTRICT) is used with a dependent text search configuration.  When the
# dictionary does not exist, the dependency boundary cannot fire.
_PRIVILEGE_NEGATIVE = ("authorization_path", "non_owner")
_OBJECT_MISSING_OBJECT = ("object_state", "absent")
_OBJECT_MISSING_NAME = ("dict_name_shape", "non_existent_name")
_DEPENDENCY_NEGATIVE = ("dependency_context", "config_using_dict")
_RESTRICT_VALUES = frozenset({"default_restrict", "explicit_restrict"})
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("authorization_path") == "non_owner"


def _object_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """object-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("object_state") == "absent"
        or assignment.get("dict_name_shape") == "non_existent_name"
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """config_using_dict fires only under a non-CASCADE drop policy.

    When the dictionary does not exist (object absent or non-existent name),
    there is no dictionary for a configuration to depend on, so the
    dependency boundary cannot fire.
    """

    if assignment.get("object_state") == "absent":
        return False
    if assignment.get("dict_name_shape") == "non_existent_name":
        return False
    return (
        assignment.get("dependency_context") == "config_using_dict"
        and assignment.get("cascade_restrict") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _object_missing_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _object_missing_failure_fires(assignment):
        if assignment.get("object_state") == "absent":
            return _OBJECT_MISSING_OBJECT
        return _OBJECT_MISSING_NAME
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
    cases: tuple[DropTextSearchDictionaryFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"drop-text-search-dictionary-factor-extension-v1\n"
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
    cases: tuple[DropTextSearchDictionaryFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP TEXT SEARCH DICTIONARY extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_text_search_dictionary_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP TEXT SEARCH DICTIONARY",
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


def build_drop_text_search_dictionary_factor_extension_plan(
    repository_root: Path,
) -> DropTextSearchDictionaryFactorExtensionPlan:
    """Build the bounded DROP TEXT SEARCH DICTIONARY post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_text_search_dictionary_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropTextSearchDictionaryFactorExtensionCase] = []
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
                    DropTextSearchDictionaryFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPTEXTSEARCHDICTIONARY{ordinal:05d}",
                        sql_filename=f"DROPTEXTSEARCHDICTIONARY{ordinal:05d}.sql",
                        object_prefix=f"droptextsearchdictionary_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPTEXTSEARCHDICTIONARY-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_text_search_dictionary_required_baseline_factor_space"
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
    return DropTextSearchDictionaryFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropTextSearchDictionaryFactorExtensionError",
    "DropTextSearchDictionaryFactorExtensionCase",
    "DropTextSearchDictionaryFactorExtensionPlan",
    "build_drop_text_search_dictionary_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
