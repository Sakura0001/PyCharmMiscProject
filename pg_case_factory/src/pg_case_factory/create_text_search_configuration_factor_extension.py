"""Bounded post-coverage cross-factor extension expander for CREATE TEXT SEARCH CONFIGURATION.

The marginal factor-value-loop (:mod:`create_text_search_configuration_factor_loop`) is
the required baseline: one program per factor value, 54 local cases
(GRM 2 + SFV 52).  This module adds the bounded post-coverage extension
phase allowed by ``create_text_search_configuration.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the 2 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode``/``cleanup_mode`` crossed so every
declared T6 value is exercised.

CREATE TEXT SEARCH CONFIGURATION requires ``CREATE`` privilege on the
target schema, so ``privilege_level=non_owner`` is an unconditional
failure.  ``PARSER`` and ``COPY`` are mutually exclusive, so the
``both_specified`` and ``none_specified`` modes are unconditional
failures.  The T5 single-value factors
(duplicate_config_name, nonexistent_parser, nonexistent_copy_source,
parser_copy_both_specified, missing_parser_or_copy,
schema_permission_denied) are derived from their T1-T4 counterparts, not
crossed as axes.

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

from .create_text_search_configuration_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_text_search_configuration_factor_loop_plan,
)


class CreateTextSearchConfigurationFactorExtensionError(ValueError):
    """Raised when a frozen CREATE TEXT SEARCH CONFIGURATION extension input drifts."""


@dataclass(frozen=True)
class CreateTextSearchConfigurationFactorExtensionCase:
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
class CreateTextSearchConfigurationFactorExtensionPlan:
    cases: tuple[CreateTextSearchConfigurationFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 54
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_ts_config",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_text_search_configuration",
    "drop_parser",
)

# General axes crossed for ALL specified-modes.  Every declared value of
# each axis is crossed so the full shipped applicability universe is
# exercised (no silent under-coverage).
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "exists",
    ),
    "config_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "reserved_word_as_name",
        "duplicate_name",
        "invalid_name",
    ),
    "privilege_level": (
        "schema_owner",
        "superuser",
        "non_owner",
    ),
    "schema_existence": (
        "schema_exists",
        "schema_not_exists",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / config_source_type / parser_copy_conflict are
# overridden per specified-mode.
_BASELINE: dict[str, str] = {
    "object_state": "not_exists",
    "expected_status": "success",
    "config_source_type": "parser",
    "parser_existence": "parser_exists",
    "copy_source_existence": "source_exists",
    "parser_copy_conflict": "only_parser",
    "config_name_shape": "simple_id",
    "parser_name_shape": "simple_id",
    "copy_source_name_shape": "simple_id",
    "privilege_level": "schema_owner",
    "schema_existence": "schema_exists",
    "parser_dependency": "parser_exists_and_valid",
    "duplicate_config_name": "no_conflict",
    "nonexistent_parser": "parser_exists",
    "nonexistent_copy_source": "source_exists",
    "parser_copy_both_specified": "one_specified",
    "missing_parser_or_copy": "one_specified",
    "schema_permission_denied": "has_create_privilege",
    "verification_mode": "catalog_query_pg_ts_config",
    "cleanup_mode": "drop_text_search_configuration",
}

# Specified-mode -> (statement_branch, target_action, branch-specific axes).
# The 4 modes cover every parser_copy_conflict / missing_parser_or_copy
# combination.  both_specified and none_specified are single-failure
# modes (no additional parser/copy axes are crossed).
_MODE_CONFIG: tuple[
    tuple[str, str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "only_parser",
        "branch_parser",
        "parser",
        {
            "parser_existence": (
                "parser_exists",
                "parser_not_exists",
            ),
            "parser_name_shape": (
                "simple_id",
                "schema_qualified_id",
                "quoted_id",
                "nonexistent_name",
            ),
        },
    ),
    (
        "only_copy",
        "branch_copy",
        "copy",
        {
            "copy_source_existence": (
                "source_exists",
                "source_not_exists",
            ),
            "copy_source_name_shape": (
                "simple_id",
                "schema_qualified_id",
                "quoted_id",
                "nonexistent_name",
            ),
        },
    ),
    (
        "both_specified",
        "branch_parser",
        "parser",
        {},
    ),
    (
        "none_specified",
        "branch_parser",
        "parser",
        {},
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure cluster.  Synced T5/T3 values (e.g. config_name_shape=
# duplicate_name is always paired with object_state=exists) are NOT
# listed here so ``_failure_unit_count`` counts each failure scenario
# exactly once, keeping at-most-one attribution clean.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "exists"),
        ("config_name_shape", "invalid_name"),
        ("privilege_level", "non_owner"),
        ("schema_existence", "schema_not_exists"),
        ("parser_existence", "parser_not_exists"),
        ("copy_source_existence", "source_not_exists"),
        ("parser_copy_conflict", "both_specified"),
        ("missing_parser_or_copy", "none_specified"),
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


def _is_valid_combination(
    mode: str, assignment: dict[str, str]
) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    os_ = assignment.get("object_state", "not_exists")
    cns = assignment.get("config_name_shape", "simple_id")
    if os_ == "exists" and cns != "duplicate_name":
        return False
    if os_ != "exists" and cns == "duplicate_name":
        return False

    pe = assignment.get("parser_existence")
    pns = assignment.get("parser_name_shape")
    if pe is not None and pns is not None:
        if pe == "parser_not_exists" and pns != "nonexistent_name":
            return False
        if pe != "parser_not_exists" and pns == "nonexistent_name":
            return False

    cse = assignment.get("copy_source_existence")
    csns = assignment.get("copy_source_name_shape")
    if cse is not None and csns is not None:
        if cse == "source_not_exists" and csns != "nonexistent_name":
            return False
        if cse != "source_not_exists" and csns == "nonexistent_name":
            return False

    # both_specified and none_specified are themselves single failures;
    # they must not combine with any other failure value.
    if mode == "both_specified":
        other = _failure_unit_count(assignment) - 1
        return other <= 0
    if mode == "none_specified":
        other = _failure_unit_count(assignment) - 1
        return other <= 0

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(
    mode: str, a: dict[str, str]
) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "not_exists")
    cns = a.get("config_name_shape", "simple_id")
    pe = a.get("parser_existence", "parser_exists")
    pns = a.get("parser_name_shape", "simple_id")
    cse = a.get("copy_source_existence", "source_exists")
    csns = a.get("copy_source_name_shape", "simple_id")
    pl = a.get("privilege_level", "schema_owner")
    se = a.get("schema_existence", "schema_exists")

    if os_ == "exists" or cns == "duplicate_name":
        a["object_state"] = "exists"
        a["config_name_shape"] = "duplicate_name"
        a["duplicate_config_name"] = "same_name_conflict"
    else:
        a["duplicate_config_name"] = "no_conflict"

    if (
        pe == "parser_not_exists"
        or pns == "nonexistent_name"
    ):
        a["parser_existence"] = "parser_not_exists"
        a["parser_name_shape"] = "nonexistent_name"
        a["nonexistent_parser"] = "parser_missing"
        a["parser_dependency"] = "parser_missing"
    else:
        a["nonexistent_parser"] = "parser_exists"
        a["parser_dependency"] = "parser_exists_and_valid"

    if (
        cse == "source_not_exists"
        or csns == "nonexistent_name"
    ):
        a["copy_source_existence"] = "source_not_exists"
        a["copy_source_name_shape"] = "nonexistent_name"
        a["nonexistent_copy_source"] = "source_missing"
    else:
        a["nonexistent_copy_source"] = "source_exists"

    if pl == "non_owner":
        a["schema_permission_denied"] = "lacks_create_privilege"
    else:
        a["schema_permission_denied"] = "has_create_privilege"

    if se == "schema_not_exists":
        a["schema_existence"] = "schema_not_exists"

    if mode == "both_specified":
        a["parser_copy_conflict"] = "both_specified"
        a["parser_copy_both_specified"] = "both_specified"
        a["missing_parser_or_copy"] = "one_specified"
    elif mode == "none_specified":
        a["parser_copy_conflict"] = "only_parser"
        a["parser_copy_both_specified"] = "one_specified"
        a["missing_parser_or_copy"] = "none_specified"
    elif mode == "only_copy":
        a["config_source_type"] = "copy"
        a["parser_copy_conflict"] = "only_copy"
        a["parser_copy_both_specified"] = "one_specified"
        a["missing_parser_or_copy"] = "one_specified"
    else:
        a["config_source_type"] = "parser"
        a["parser_copy_conflict"] = "only_parser"
        a["parser_copy_both_specified"] = "one_specified"
        a["missing_parser_or_copy"] = "one_specified"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[tuple[str, dict[str, str]]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[tuple[str, dict[str, str]]] = []
    for mode, branch, action, axes in _MODE_CONFIG:
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
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(mode, assignment)
            if not _is_valid_combination(mode, assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateTextSearchConfigurationFactorExtensionError(
                    "duplicate factor key in extension assignment"
                )
            combos.append((mode, assignment))
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
    cases: tuple[CreateTextSearchConfigurationFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-text-search-configuration-factor-extension-v1\n"
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
    cases: tuple[CreateTextSearchConfigurationFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE TEXT SEARCH CONFIGURATION extension "
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
                        "create_text_search_configuration_"
                        "factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE TEXT SEARCH CONFIGURATION",
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


def build_create_text_search_configuration_factor_extension_plan(
    repository_root: Path,
) -> CreateTextSearchConfigurationFactorExtensionPlan:
    """Build the bounded CREATE TEXT SEARCH CONFIGURATION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_text_search_configuration_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda item: tuple(sorted(item[1].items())))
    cases: list[CreateTextSearchConfigurationFactorExtensionCase] = []
    ordinal = _BASELINE_COUNT
    raw = 0
    for mode, behavior in behaviors:
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
                    CreateTextSearchConfigurationFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATETEXTSEARCHCONFIGURATION{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATETEXTSEARCHCONFIGURATION{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createtextsearchconfiguration_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CTSC-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_text_search_configuration_"
                            "required_factor_value_matrix"
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
    return CreateTextSearchConfigurationFactorExtensionPlan(
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
    "CreateTextSearchConfigurationFactorExtensionError",
    "CreateTextSearchConfigurationFactorExtensionCase",
    "CreateTextSearchConfigurationFactorExtensionPlan",
    "build_create_text_search_configuration_factor_extension_plan",
]
