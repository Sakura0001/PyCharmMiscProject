"""Bounded post-coverage cross-factor extension expander for ALTER TEXT SEARCH CONFIGURATION.

The marginal factor-value-loop (:mod:`alter_text_search_configuration_factor_loop`) is
the required baseline: one program per factor value, 89 local cases
(GRM 8 + SFV 81).  This module adds the bounded post-coverage extension
phase allowed by ``alter_text_search_configuration.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 8 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode``/``cleanup_mode`` crossed so every
declared T6 value is exercised.

ALTER TEXT SEARCH CONFIGURATION requires the executor to be the
configuration's owner on every branch, so ``privilege_level=non_owner``
is an unconditional failure.  The T5 single-value factors
(nonexistent_config, nonexistent_dictionary,
nonexistent_token_type_mapping, duplicate_new_name,
nonexistent_owner_role, nonexistent_target_schema, non_owner_attempt,
drop_mapping_without_if_exists) are derived from their T1-T4
counterparts, not crossed as axes.

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

from .alter_text_search_configuration_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_text_search_configuration_factor_loop_plan,
)


class AlterTextSearchConfigurationFactorExtensionError(ValueError):
    """Raised when a frozen ALTER TEXT SEARCH CONFIGURATION extension input drifts."""


@dataclass(frozen=True)
class AlterTextSearchConfigurationFactorExtensionCase:
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
class AlterTextSearchConfigurationFactorExtensionPlan:
    cases: tuple[AlterTextSearchConfigurationFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 89
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_ts_config",
    "mapping_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_mapping_revert",
    "revert_rename",
    "revert_owner",
    "drop_text_search_configuration",
    "role_cleanup",
)

# General axes crossed for ALL 8 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "exists",
        "not_exists",
    ),
    "config_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "nonexistent_name",
    ),
    "privilege_level": (
        "owner",
        "superuser",
        "non_owner",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / alter_action / grammar_branch are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "omitted",
    "owner_target": "specified_new_owner",
    "dictionary_existence": "dictionary_exists",
    "token_type_existence": "token_type_mapped",
    "config_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "schema_name_shape": "simple_id",
    "dictionary_name_shape": "simple_id",
    "token_type_name_shape": "valid_token_type",
    "privilege_level": "owner",
    "role_existence": "role_exists",
    "schema_existence": "schema_exists",
    "dictionary_dependency": "dictionary_exists_and_valid",
    "verification_mode": "catalog_query_pg_ts_config",
    "cleanup_mode": "drop_mapping_revert",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_add_mapping",
        "add_mapping",
        {
            "dictionary_existence": (
                "dictionary_exists",
                "dictionary_not_exists",
            ),
            "dictionary_name_shape": (
                "simple_id",
                "schema_qualified_id",
                "nonexistent_name",
            ),
        },
    ),
    (
        "branch_alter_mapping",
        "alter_mapping",
        {
            "dictionary_existence": (
                "dictionary_exists",
                "dictionary_not_exists",
            ),
            "token_type_existence": (
                "token_type_mapped",
                "token_type_not_mapped",
            ),
        },
    ),
    (
        "branch_alter_mapping_replace",
        "alter_mapping_replace",
        {
            "dictionary_existence": (
                "dictionary_exists",
                "dictionary_not_exists",
            ),
            "token_type_existence": (
                "token_type_mapped",
                "token_type_not_mapped",
            ),
        },
    ),
    (
        "branch_alter_mapping_for_replace",
        "alter_mapping_for_replace",
        {
            "dictionary_existence": (
                "dictionary_exists",
                "dictionary_not_exists",
            ),
            "token_type_existence": (
                "token_type_mapped",
                "token_type_not_mapped",
            ),
        },
    ),
    (
        "branch_drop_mapping",
        "drop_mapping",
        {
            "if_exists_clause": (
                "omitted",
                "present",
            ),
            "token_type_existence": (
                "token_type_mapped",
                "token_type_not_mapped",
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
            "role_existence": (
                "role_exists",
                "role_not_exists",
            ),
        },
    ),
    (
        "branch_set_schema",
        "set_schema",
        {
            "schema_existence": (
                "schema_exists",
                "schema_not_exists",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T5/T3 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("privilege_level", "non_owner"),
        ("dictionary_existence", "dictionary_not_exists"),
        ("token_type_existence", "token_type_not_mapped"),
        ("token_type_name_shape", "invalid_token_type"),
        ("role_existence", "role_not_exists"),
        ("schema_existence", "schema_not_exists"),
        ("duplicate_new_name", "same_name_conflict"),
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
    cns = assignment.get("config_name_shape", "simple_id")
    if os_ == "not_exists" and cns != "nonexistent_name":
        return False
    if os_ != "not_exists" and cns == "nonexistent_name":
        return False

    de = assignment.get("dictionary_existence")
    dns = assignment.get("dictionary_name_shape")
    if de is not None and dns is not None:
        if de == "dictionary_not_exists" and dns != "nonexistent_name":
            return False
        if de != "dictionary_not_exists" and dns == "nonexistent_name":
            return False

    ot = assignment.get("owner_target")
    re_ = assignment.get("role_existence")
    if ot is not None and re_ is not None:
        keyword_target = ot in (
            "specified_current_role",
            "specified_current_user",
            "specified_session_user",
        )
        if re_ == "role_not_exists" and not keyword_target:
            # specified_new_owner with role_not_exists is the failure path
            pass
        if keyword_target and re_ == "role_not_exists":
            # CURRENT_ROLE/USER/SESSION_USER never "does not exist"
            return False

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "exists")
    cns = a.get("config_name_shape", "simple_id")
    de = a.get("dictionary_existence", "dictionary_exists")
    dns = a.get("dictionary_name_shape", "simple_id")
    pl = a.get("privilege_level", "owner")
    re_ = a.get("role_existence", "role_exists")
    ons = a.get("owner_name_shape", "simple_id")
    se = a.get("schema_existence", "schema_exists")
    sns = a.get("schema_name_shape", "simple_id")
    nns = a.get("new_name_shape", "simple_id")
    tte = a.get("token_type_existence", "token_type_mapped")
    ttns = a.get("token_type_name_shape", "valid_token_type")
    iec = a.get("if_exists_clause", "omitted")

    if os_ == "not_exists" or cns == "nonexistent_name":
        a["nonexistent_config"] = "config_missing"
        a["object_state"] = "not_exists"
        a["config_name_shape"] = "nonexistent_name"
    else:
        a["nonexistent_config"] = "config_exists"

    if (
        de == "dictionary_not_exists"
        or dns == "nonexistent_name"
    ):
        a["dictionary_existence"] = "dictionary_not_exists"
        a["dictionary_dependency"] = "dictionary_missing"
        a["nonexistent_dictionary"] = "dictionary_missing"
        a["dictionary_name_shape"] = "nonexistent_name"
    else:
        a["dictionary_dependency"] = "dictionary_exists_and_valid"
        a["nonexistent_dictionary"] = "dictionary_exists"

    if pl == "non_owner":
        a["non_owner_attempt"] = "non_owner_execution"
    else:
        a["non_owner_attempt"] = "owner_execution"

    if re_ == "role_not_exists" or ons == "nonexistent_role":
        a["role_existence"] = "role_not_exists"
        a["nonexistent_owner_role"] = "role_missing"
        a["owner_name_shape"] = "nonexistent_role"
    else:
        a["nonexistent_owner_role"] = "role_exists"

    if se == "schema_not_exists" or sns == "nonexistent_schema":
        a["schema_existence"] = "schema_not_exists"
        a["nonexistent_target_schema"] = "schema_missing"
        a["schema_name_shape"] = "nonexistent_schema"
    else:
        a["nonexistent_target_schema"] = "schema_exists"

    if nns == "duplicate_name":
        a["duplicate_new_name"] = "same_name_conflict"
    else:
        a["duplicate_new_name"] = "no_conflict"

    if (
        tte == "token_type_not_mapped"
        or ttns == "invalid_token_type"
    ):
        a["token_type_existence"] = "token_type_not_mapped"
        a["nonexistent_token_type_mapping"] = "mapping_missing"
        a["token_type_name_shape"] = "invalid_token_type"
    else:
        a["nonexistent_token_type_mapping"] = "mapping_exists"

    if iec == "omitted":
        a["drop_mapping_without_if_exists"] = "without_if_exists"
    else:
        a["drop_mapping_without_if_exists"] = "with_if_exists"

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
                raise AlterTextSearchConfigurationFactorExtensionError(
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
    cases: tuple[AlterTextSearchConfigurationFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-text-search-configuration-factor-extension-v1\n"
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
    cases: tuple[AlterTextSearchConfigurationFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER TEXT SEARCH CONFIGURATION extension "
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
                        "alter_text_search_configuration_"
                        "factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER TEXT SEARCH CONFIGURATION",
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


def build_alter_text_search_configuration_factor_extension_plan(
    repository_root: Path,
) -> AlterTextSearchConfigurationFactorExtensionPlan:
    """Build the bounded ALTER TEXT SEARCH CONFIGURATION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_text_search_configuration_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterTextSearchConfigurationFactorExtensionCase] = []
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
                    AlterTextSearchConfigurationFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"ALTERTEXTSEARCHCONFIGURATION{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"ALTERTEXTSEARCHCONFIGURATION{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"alter_text_search_configuration_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"ATSC-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_text_search_configuration_"
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
    return AlterTextSearchConfigurationFactorExtensionPlan(
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
    "AlterTextSearchConfigurationFactorExtensionError",
    "AlterTextSearchConfigurationFactorExtensionCase",
    "AlterTextSearchConfigurationFactorExtensionPlan",
    "build_alter_text_search_configuration_factor_extension_plan",
]
