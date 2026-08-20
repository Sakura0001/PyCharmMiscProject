"""Bounded post-coverage cross-factor extension expander for ALTER USER MAPPING.

The marginal factor-value-loop (:mod:`alter_user_mapping_factor_loop`) is
the required baseline: one program per factor value, 55 local cases
(GRM 1 + SFV 54).  This module adds the bounded post-coverage extension
phase allowed by ``alter_user_mapping.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the single
OPTIONS branch, with at most one failure-causing value per case so
attribution stays clean, and ``verification_mode`` / ``cleanup_mode``
crossed so every declared T6 value is exercised.

ALTER USER MAPPING has a single synopsis branch (OPTIONS modification),
so there is no multi-branch crossing.  The T5 boundary factors
(``nonexistent_mapping``, ``nonexistent_server``, ``insufficient_privilege``,
``invalid_option``, ``duplicate_option_name``) are derived from their
T1-T4 counterparts, not crossed as axes.

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

from .alter_user_mapping_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_user_mapping_factor_loop_plan,
)


class AlterUserMappingFactorExtensionError(ValueError):
    """Raised when a frozen ALTER USER MAPPING extension input drifts."""


@dataclass(frozen=True)
class AlterUserMappingFactorExtensionCase:
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
class AlterUserMappingFactorExtensionPlan:
    cases: tuple[AlterUserMappingFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 55
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_user_mapping",
    "option_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "revert_option",
    "drop_user_mapping",
    "drop_server",
)

# General axes crossed for the single branch.  These include the failure
# representatives of clusters A (object_state=not_exists), B
# (server_dependency=server_missing) and C (privilege_level=non_privileged).
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("exists", "not_exists"),
    "privilege_level": (
        "server_owner",
        "user_with_usage",
        "non_privileged",
    ),
    "server_dependency": (
        "server_exists_and_valid",
        "server_missing",
    ),
}

# Branch-specific axes for branch_1 (OPTIONS modification).
_BRANCH_AXES: dict[str, tuple[str, ...]] = {
    "user_specification": (
        "named_user",
        "user_keyword",
        "current_role",
        "current_user",
        "session_user",
        "public",
    ),
    "option_action": (
        "add",
        "set",
        "drop",
        "default_add",
    ),
    "option_clause": (
        "single_option_add",
        "single_option_set",
        "single_option_drop",
        "multiple_options_mixed",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch are overridden per branch.
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "expected_status": "success",
    "user_specification": "named_user",
    "option_action": "add",
    "option_clause": "single_option_add",
    "user_name_shape": "simple_id",
    "server_name_shape": "simple_id",
    "option_name_shape": "valid_option",
    "option_value_shape": "valid_value",
    "privilege_level": "server_owner",
    "server_dependency": "server_exists_and_valid",
    "nonexistent_mapping": "mapping_exists",
    "nonexistent_server": "server_exists",
    "insufficient_privilege": "has_privilege",
    "invalid_option": "valid_option_and_value",
    "duplicate_option_name": "unique_options",
    "verification_mode": "catalog_query_pg_user_mapping",
    "cleanup_mode": "revert_option",
}

# Crossed behaviour-negative (factor, value) pairs - one representative
# per failure scenario.  Overlapping T5 values are NOT listed here (they
# are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("server_dependency", "server_missing"),
        ("privilege_level", "non_privileged"),
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

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "exists")
    us = a.get("user_specification", "named_user")
    sd = a.get("server_dependency", "server_exists_and_valid")
    pl = a.get("privilege_level", "server_owner")
    oa = a.get("option_action", "add")

    # Cluster A: mapping existence.
    if os_ == "not_exists":
        a["mapping_existence"] = "mapping_not_exists"
        a["nonexistent_mapping"] = "mapping_missing"
        a["user_name_shape"] = "nonexistent_name"
    else:
        a["mapping_existence"] = "mapping_exists"
        a["nonexistent_mapping"] = "mapping_exists"
        if us == "public":
            a["user_name_shape"] = "public_keyword"
        else:
            a["user_name_shape"] = "simple_id"

    # Cluster B: foreign server existence.
    if sd == "server_missing":
        a["nonexistent_server"] = "server_missing"
        a["server_name_shape"] = "nonexistent_name"
    else:
        a["nonexistent_server"] = "server_exists"
        a["server_name_shape"] = "simple_id"

    # Cluster C: privilege.
    if pl == "non_privileged":
        a["insufficient_privilege"] = "lacks_privilege"
    else:
        a["insufficient_privilege"] = "has_privilege"

    # Cluster D: invalid option - not crossed; always success path.
    a["option_name_shape"] = "valid_option"
    a["invalid_option"] = "valid_option_and_value"

    # Cluster E: duplicate option - not crossed; always success path.
    a["duplicate_option_name"] = "unique_options"

    # option_value_shape derived from option_action.
    if oa == "drop":
        a["option_value_shape"] = "drop_no_value"
    else:
        a["option_value_shape"] = "valid_value"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    all_axes = dict(_GENERAL_AXES)
    all_axes.update(_BRANCH_AXES)
    names = list(all_axes)
    combos: list[dict[str, str]] = []
    for values in itertools.product(
        *[all_axes[n] for n in names]
    ):
        assignment: dict[str, str] = dict(_BASELINE)
        assignment["statement_branch"] = "branch_1"
        assignment["grammar_branch"] = "branch_1"
        assignment["target_action"] = "options"
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_t5_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise AlterUserMappingFactorExtensionError(
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
    cases: tuple[AlterUserMappingFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-user-mapping-factor-extension-v1\n"
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
    cases: tuple[AlterUserMappingFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER USER MAPPING extension "
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
                        "alter_user_mapping_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER USER MAPPING",
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


def build_alter_user_mapping_factor_extension_plan(
    repository_root: Path,
) -> AlterUserMappingFactorExtensionPlan:
    """Build the bounded ALTER USER MAPPING post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_user_mapping_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterUserMappingFactorExtensionCase] = []
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
                    AlterUserMappingFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"ALTERUSERMAPPING{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"ALTERUSERMAPPING{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"alterusermapping_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"AUM-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_user_mapping_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x server_dependency="
                            f"{assignment['server_dependency']} "
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
    return AlterUserMappingFactorExtensionPlan(
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
    "AlterUserMappingFactorExtensionError",
    "AlterUserMappingFactorExtensionCase",
    "AlterUserMappingFactorExtensionPlan",
    "build_alter_user_mapping_factor_extension_plan",
]
