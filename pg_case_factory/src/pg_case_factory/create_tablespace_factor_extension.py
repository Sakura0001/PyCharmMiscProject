"""Bounded post-coverage cross-factor extension expander for CREATE TABLESPACE.

The marginal factor-value-loop (:mod:`create_tablespace_factor_loop`) is
the required baseline: one program per factor value, 67 local cases
(GRM 1 + SFV 66).  This module adds the bounded post-coverage extension
phase: cross-factor combinations of the positive T1-T4 behaviour axes
across the single grammar branch, with at most one failure-causing value
per case so attribution stays clean, and ``verification_mode`` crossed so
every declared T6 value is exercised, and ``cleanup_mode`` crossed so
every declared T6 cleanup value is exercised.

CREATE TABLESPACE requires superuser privilege, so
``privilege_level=non_superuser`` is an unconditional failure.  The T5
single-value factors (duplicate_tablespace_name, pg_reserved_name,
nonexistent_directory, non_absolute_path, non_superuser_attempt,
inside_transaction_block, nonexistent_owner_role,
directory_permission_denied) are derived from their T1-T4 counterparts,
not crossed as axes.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension``.
Filtering happens BEFORE counting (``raw += 1``), so
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

from .create_tablespace_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_tablespace_factor_loop_plan,
)


class CreateTablespaceFactorExtensionError(ValueError):
    """Raised when a frozen CREATE TABLESPACE extension input drifts."""


@dataclass(frozen=True)
class CreateTablespaceFactorExtensionCase:
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
class CreateTablespaceFactorExtensionPlan:
    cases: tuple[CreateTablespaceFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 67
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_tablespace",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_tablespace",
    "filesystem_cleanup",
    "role_cleanup",
)

# General axes crossed for the single branch.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "exists",
        "reserved_name_conflict",
    ),
    "privilege_level": ("superuser", "non_superuser"),
    "directory_condition": (
        "exists_valid",
        "not_exists",
        "permission_denied",
        "non_empty",
    ),
}

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "create",
    "object_state": "not_exists",
    "expected_status": "success",
    "owner_clause": "omitted",
    "with_clause": "omitted",
    "directory_condition": "exists_valid",
    "tablespace_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "directory_path_shape": "absolute_path",
    "privilege_level": "superuser",
    "filesystem_dependency": "directory_exists_owned_by_postgres",
    "transaction_context": "outside_transaction",
    "role_existence": "role_exists",
    "duplicate_tablespace_name": "no_conflict",
    "pg_reserved_name": "normal_name",
    "nonexistent_directory": "directory_exists",
    "non_absolute_path": "absolute_path",
    "invalid_option": "valid_option",
    "directory_permission_denied": "proper_permission",
    "non_superuser_attempt": "superuser_execution",
    "inside_transaction_block": "outside_transaction",
    "nonexistent_owner_role": "role_exists",
    "verification_mode": "catalog_query_pg_tablespace",
    "cleanup_mode": "drop_tablespace",
}

# Branch-specific axes (for branch_1).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_1",
        "create",
        {
            "owner_clause": (
                "omitted",
                "specified_new_owner",
                "specified_current_role",
                "specified_current_user",
                "specified_session_user",
            ),
            "with_clause": (
                "omitted",
                "single_option_seq_page_cost",
                "single_option_random_page_cost",
                "single_option_effective_io_concurrency",
                "single_option_maintenance_io_concurrency",
                "multiple_options",
            ),
            "tablespace_name_shape": (
                "simple_id",
                "quoted_id",
                "duplicate_name",
                "invalid_name",
                "pg_prefix_reserved",
            ),
            "transaction_context": (
                "outside_transaction",
                "inside_transaction_block",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T5/T3 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both
# would double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "exists"),
        ("object_state", "reserved_name_conflict"),
        ("privilege_level", "non_superuser"),
        ("directory_condition", "not_exists"),
        ("directory_condition", "permission_denied"),
        ("directory_condition", "non_empty"),
        ("tablespace_name_shape", "invalid_name"),
        ("transaction_context", "inside_transaction_block"),
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

    os_ = assignment.get("object_state", "not_exists")
    tns = assignment.get("tablespace_name_shape", "simple_id")

    # object_state=exists requires tablespace_name_shape=duplicate_name
    if os_ == "exists" and tns != "duplicate_name":
        return False
    if os_ != "exists" and tns == "duplicate_name":
        return False

    # object_state=reserved_name_conflict requires pg_prefix_reserved
    if os_ == "reserved_name_conflict" and tns != "pg_prefix_reserved":
        return False
    if os_ != "reserved_name_conflict" and tns == "pg_prefix_reserved":
        return False

    # object_state=not_exists excludes duplicate_name/pg_prefix_reserved
    if os_ == "not_exists" and tns in ("duplicate_name", "pg_prefix_reserved"):
        return False

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "not_exists")
    tns = a.get("tablespace_name_shape", "simple_id")
    dtn = a.get("duplicate_tablespace_name", "no_conflict")
    pgr = a.get("pg_reserved_name", "normal_name")

    if (
        os_ == "exists"
        or tns == "duplicate_name"
        or dtn == "same_name_conflict"
    ):
        a["object_state"] = "exists"
        a["tablespace_name_shape"] = "duplicate_name"
        a["duplicate_tablespace_name"] = "same_name_conflict"
    else:
        a["duplicate_tablespace_name"] = "no_conflict"

    if (
        os_ == "reserved_name_conflict"
        or tns == "pg_prefix_reserved"
        or pgr == "pg_prefix_name"
    ):
        a["object_state"] = "reserved_name_conflict"
        a["tablespace_name_shape"] = "pg_prefix_reserved"
        a["pg_reserved_name"] = "pg_prefix_name"
    else:
        a["pg_reserved_name"] = "normal_name"

    ep = a.get("privilege_level", "superuser")
    if ep == "non_superuser":
        a["non_superuser_attempt"] = "non_superuser_execution"
    else:
        a["non_superuser_attempt"] = "superuser_execution"

    dc = a.get("directory_condition", "exists_valid")
    if dc == "not_exists":
        a["filesystem_dependency"] = "directory_not_exists"
        a["nonexistent_directory"] = "directory_missing"
    elif dc == "permission_denied":
        a["filesystem_dependency"] = "directory_wrong_owner"
        a["directory_permission_denied"] = "wrong_owner"
        a["nonexistent_directory"] = "directory_exists"
    elif dc == "non_empty":
        a["filesystem_dependency"] = "directory_exists_owned_by_postgres"
        a["nonexistent_directory"] = "directory_exists"
        a["directory_permission_denied"] = "proper_permission"
    else:
        a["filesystem_dependency"] = "directory_exists_owned_by_postgres"
        a["nonexistent_directory"] = "directory_exists"
        a["directory_permission_denied"] = "proper_permission"

    dps = a.get("directory_path_shape", "absolute_path")
    if dps == "relative_path":
        a["non_absolute_path"] = "relative_path"
        a["filesystem_dependency"] = "path_not_absolute"
    else:
        a["non_absolute_path"] = "absolute_path"

    tc = a.get("transaction_context", "outside_transaction")
    if tc == "inside_transaction_block":
        a["inside_transaction_block"] = "inside_transaction"
    else:
        a["inside_transaction_block"] = "outside_transaction"

    # owner_name_shape / role_existence derivation from owner_clause
    oc = a.get("owner_clause", "omitted")
    if oc == "specified_new_owner":
        # role_existence stays as set; owner_name_shape derived
        re_ = a.get("role_existence", "role_exists")
        if re_ == "role_not_exists":
            a["owner_name_shape"] = "nonexistent_role"
            a["nonexistent_owner_role"] = "role_missing"
        else:
            a["owner_name_shape"] = "simple_id"
            a["nonexistent_owner_role"] = "role_exists"
    else:
        a["role_existence"] = "role_exists"
        a["nonexistent_owner_role"] = "role_exists"
        if oc in (
            "specified_current_role",
            "specified_current_user",
            "specified_session_user",
        ):
            a["owner_name_shape"] = "simple_id"
        else:
            a["owner_name_shape"] = "simple_id"

    # invalid_option defaults to valid
    a.setdefault("invalid_option", "valid_option")

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
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateTablespaceFactorExtensionError(
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
    cases: tuple[CreateTablespaceFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-tablespace-factor-extension-v1\n"
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
    cases: tuple[CreateTablespaceFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE TABLESPACE extension "
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
                        "create_tablespace_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE TABLESPACE",
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


def build_create_tablespace_factor_extension_plan(
    repository_root: Path,
) -> CreateTablespaceFactorExtensionPlan:
    """Build the bounded CREATE TABLESPACE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_tablespace_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateTablespaceFactorExtensionCase] = []
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
                    CreateTablespaceFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATETABLESPACE{ordinal:05d}",
                        sql_filename=(
                            f"CREATETABLESPACE{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createtablespace_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CTSP-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_tablespace_required_factor_"
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
                            f"x directory_condition="
                            f"{assignment['directory_condition']} "
                            f"x owner_clause="
                            f"{assignment['owner_clause']} "
                            f"x with_clause="
                            f"{assignment['with_clause']} "
                            f"x tablespace_name_shape="
                            f"{assignment['tablespace_name_shape']} "
                            f"x transaction_context="
                            f"{assignment['transaction_context']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment["target_action"],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return CreateTablespaceFactorExtensionPlan(
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
    "CreateTablespaceFactorExtensionError",
    "CreateTablespaceFactorExtensionCase",
    "CreateTablespaceFactorExtensionPlan",
    "build_create_tablespace_factor_extension_plan",
]
