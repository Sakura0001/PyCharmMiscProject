"""Bounded post-coverage cross-factor extension expander for REINDEX."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .reindex_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_reindex_factor_loop_plan,
)


class ReindexFactorExtensionError(ValueError):
    """Raised when a frozen REINDEX extension input drifts."""


@dataclass(frozen=True)
class ReindexFactorExtensionCase:
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
class ReindexFactorExtensionPlan:
    cases: tuple[ReindexFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 83
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_validity_check",
    "invalid_index_detection",
    "search_path_sandbox",
    "verbose_output_check",
)

_CLEANUP_MODES = (
    "drop_invalid_index",
    "reindex_concurrently_fix",
    "rollback",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "name_shape": (
        "plain_identifier",
        "quoted_identifier",
        "schema_qualified",
    ),
    "permission": (
        "owner",
        "superuser",
        "insufficient_privilege",
    ),
}

_BASELINE: dict[str, str] = {
    "statement_branch": "reindex_index",
    "object_state": "exists",
    "expected_status": "success",
    "concurrently_keyword": "false",
    "option_concurrently": "absent",
    "option_tablespace": "absent",
    "option_verbose": "absent",
    "boolean_value": "omitted_default",
    "permission": "owner",
    "name_shape": "plain_identifier",
    "index_method": "btree",
    "tablespace_dependency": "no_tablespace_move",
    "toast_indexes": "not_applicable",
    "partition_behavior": "non_partitioned",
    "invalid_combination": "none",
    "concurrent_failure": "none",
    "syntax_error": "none",
    "permission_insufficient": "none",
    "verification_mode": "catalog_validity_check",
    "cleanup_mode": "drop_invalid_index",
}

_BRANCH_CONFIG: tuple[
    tuple[str, bool, dict[str, tuple[str, ...]]], ...
] = (
    (
        "reindex_index",
        True,
        {
            "object_state": (
                "exists",
                "not_exists",
                "corrupted_index",
            ),
            "index_method": (
                "btree",
                "brin",
                "gin",
                "gist",
            ),
            "concurrently_keyword": ("false", "true"),
        },
    ),
    (
        "reindex_table",
        True,
        {
            "object_state": ("exists", "not_exists"),
            "concurrently_keyword": ("false", "true"),
            "partition_behavior": (
                "non_partitioned",
                "partitioned_separate_transaction",
            ),
        },
    ),
    (
        "reindex_schema",
        True,
        {
            "object_state": ("exists", "not_exists"),
            "concurrently_keyword": ("false", "true"),
        },
    ),
    (
        "reindex_database",
        False,
        {
            "concurrently_keyword": ("false", "true"),
            "permission": (
                "owner",
                "superuser",
                "insufficient_privilege",
            ),
        },
    ),
    (
        "reindex_system",
        False,
        {
            "permission": (
                "owner",
                "superuser",
                "insufficient_privilege",
            ),
        },
    ),
)

_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("permission", "insufficient_privilege"),
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
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    os_ = a.get("object_state", "exists")
    ns = a.get("name_shape", "plain_identifier")
    pl = a.get("permission", "owner")
    pi = a.get("permission_insufficient", "none")

    if os_ == "not_exists":
        a["name_shape"] = "missing_object"
    else:
        if ns != "missing_object":
            a["name_shape"] = ns

    if pl == "insufficient_privilege":
        a["permission_insufficient"] = "non_owner_reindex"
    elif pl == "non_owner":
        a["permission_insufficient"] = "non_owner_reindex"
    else:
        if pi != "non_superuser_shared_catalog":
            a["permission_insufficient"] = "none"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    combos: list[dict[str, str]] = []
    for branch, use_general, axes in _BRANCH_CONFIG:
        all_axes: dict[str, tuple[str, ...]] = {}
        if use_general:
            all_axes.update(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(
            *[all_axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise ReindexFactorExtensionError(
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
    cases: tuple[ReindexFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"reindex-factor-extension-v1\n")
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(case.factor_assignment),
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
    cases: tuple[ReindexFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"REINDEX extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "reindex_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "REINDEX",
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


def build_reindex_factor_extension_plan(
    repository_root: Path,
) -> ReindexFactorExtensionPlan:
    root = Path(repository_root).resolve(strict=True)
    build_reindex_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[ReindexFactorExtensionCase] = []
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
                cases.append(
                    ReindexFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"REINDEX{ordinal:05d}",
                        sql_filename=f"REINDEX{ordinal:05d}.sql",
                        object_prefix=f"reindex_{ordinal:05d}_",
                        derivation_id=(
                            f"REINDEX-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "reindex_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x permission="
                            f"{assignment['permission']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "statement_branch"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return ReindexFactorExtensionPlan(
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
    "ReindexFactorExtensionError",
    "ReindexFactorExtensionCase",
    "ReindexFactorExtensionPlan",
    "build_reindex_factor_extension_plan",
]
