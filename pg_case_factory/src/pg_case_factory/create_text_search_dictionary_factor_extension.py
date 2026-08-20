"""Bounded post-coverage cross-factor extension expander for CREATE TEXT SEARCH DICTIONARY.

The marginal factor-value-loop
(:mod:`create_text_search_dictionary_factor_loop`) is the required
baseline: one program per factor value, 45 local cases (GRM 1 + SFV 44).
This module adds the bounded post-coverage extension phase allowed by
``create_text_search_dictionary.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the single
grammar branch, with at most one failure-causing value per case so
attribution stays clean, and ``verification_mode``/``cleanup_mode``
crossed so every declared T6 value is exercised.

CREATE TEXT SEARCH DICTIONARY is a catalog-row DDL statement (no DROP
TABLE bookend).  The extension phase never replaces a required-baseline
obligation.  Each extension case carries a derivation record and is
marked ``is_extension``.  Filtering happens BEFORE counting, so
``raw_combination_count == len(cases)`` and ``dropped_count == 0``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .create_text_search_dictionary_factor_loop import (
    _ACTION_BRANCH,
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    build_create_text_search_dictionary_factor_loop_plan,
)


class CreateTextSearchDictionaryFactorExtensionError(ValueError):
    """Raised when a frozen CREATE TEXT SEARCH DICTIONARY extension input drifts."""


@dataclass(frozen=True)
class CreateTextSearchDictionaryFactorExtensionCase:
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
    is_extension: bool = True


@dataclass(frozen=True)
class CreateTextSearchDictionaryFactorExtensionPlan:
    cases: tuple[CreateTextSearchDictionaryFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 45
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_ts_dict",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_text_search_dictionary",
    "drop_template",
)

# General axes crossed for the single branch.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "exists"),
    "template_existence": ("template_exists", "template_not_exists"),
    "option_clause": (
        "only_template",
        "template_plus_single_option",
        "template_plus_multiple_options",
    ),
    "option_value_type": (
        "simple_identifier",
        "numeric_value",
        "quoted_string_value",
    ),
    "dict_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "reserved_word_as_name",
    ),
    "template_name_shape": ("simple_id", "schema_qualified_id"),
    "option_value_shape": ("valid_value", "quoted_value"),
    "privilege_level": ("schema_owner", "superuser"),
    "schema_existence": ("schema_exists", "schema_not_exists"),
}

# Crossed behaviour-negative (factor, value) pairs -- one representative
# per failure scenario.  Overlapping T5 values are derived in
# :func:`_derive_t5_factors` so counting both would double-count a
# single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "exists"),
        ("template_existence", "template_not_exists"),
        ("schema_existence", "schema_not_exists"),
    }
)

_COMBINATION_GROUP = "create_text_search_dictionary_required_factor_value_matrix"


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

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "not_exists")
    te = a.get("template_existence", "template_exists")

    # duplicate-dictionary cluster
    if os_ == "exists":
        a["duplicate_dict_name"] = "same_name_conflict"
        a["dict_name_shape"] = "duplicate_name"
    else:
        a["duplicate_dict_name"] = "no_conflict"

    # template-missing cluster
    if te == "template_not_exists":
        a["nonexistent_template"] = "template_missing"
        a["template_dependency"] = "template_missing"
        a["template_name_shape"] = "nonexistent_name"
    else:
        a["nonexistent_template"] = "template_exists"
        a["template_dependency"] = "template_exists_and_valid"

    # privilege cluster (non_owner not crossed in extension)
    if a.get("privilege_level") == "non_owner":
        a["schema_permission_denied"] = "lacks_create_privilege"
    else:
        a["schema_permission_denied"] = "has_create_privilege"

    # invalid-option cluster (invalid_value not crossed in extension)
    if a.get("option_value_shape") == "invalid_value":
        a["invalid_option_value"] = "invalid_value"
    else:
        a["invalid_option_value"] = "valid_value"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    names = list(_GENERAL_AXES)
    for values in itertools.product(
        *[_GENERAL_AXES[n] for n in names]
    ):
        assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
        assignment["statement_branch"] = "branch_1"
        assignment["grammar_branch"] = _ACTION_BRANCH["create_dictionary"]
        assignment["target_action"] = "create_dictionary"
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_t5_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise CreateTextSearchDictionaryFactorExtensionError(
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
    cases: tuple[CreateTextSearchDictionaryFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-text-search-dictionary-factor-extension-v1\n"
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


def build_create_text_search_dictionary_factor_extension_plan(
    repository_root: Path,
) -> CreateTextSearchDictionaryFactorExtensionPlan:
    """Build the bounded CREATE TEXT SEARCH DICTIONARY post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_text_search_dictionary_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateTextSearchDictionaryFactorExtensionCase] = []
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
                    CreateTextSearchDictionaryFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATETEXTSEARCHDICTIONARY{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATETEXTSEARCHDICTIONARY{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createtextsearchdictionary_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CTSD-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            _COMBINATION_GROUP
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x template_existence="
                            f"{assignment['template_existence']} "
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
    plan = CreateTextSearchDictionaryFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(
            cases_tuple
        ),
        raw_combination_count=raw,
        dropped_combination_count=dropped,
    )
    if len(plan.cases) < 1000 - _BASELINE_COUNT:
        raise CreateTextSearchDictionaryFactorExtensionError(
            "extension case count below minimum"
        )
    if len(plan.cases) > _CAP:
        raise CreateTextSearchDictionaryFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [c.ordinal for c in plan.cases]
    expected_ordinals = list(
        range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))
    )
    if ordinals != expected_ordinals:
        raise CreateTextSearchDictionaryFactorExtensionError(
            "extension ordinal gap"
        )
    if len({c.case_id for c in plan.cases}) != len(plan.cases):
        raise CreateTextSearchDictionaryFactorExtensionError(
            "duplicate extension case id"
        )
    if len({c.sql_filename for c in plan.cases}) != len(plan.cases):
        raise CreateTextSearchDictionaryFactorExtensionError(
            "duplicate extension sql filename"
        )
    allowed_outcomes = {"success", "expected_failure"}
    if any(c.outcome not in allowed_outcomes for c in plan.cases):
        raise CreateTextSearchDictionaryFactorExtensionError(
            "unknown extension outcome"
        )
    if any(not c.derivation_id.startswith("CTSD-EXT|") for c in plan.cases):
        raise CreateTextSearchDictionaryFactorExtensionError(
            "derivation id prefix drift"
        )
    return plan


__all__ = [
    "CreateTextSearchDictionaryFactorExtensionError",
    "CreateTextSearchDictionaryFactorExtensionCase",
    "CreateTextSearchDictionaryFactorExtensionPlan",
    "build_create_text_search_dictionary_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
