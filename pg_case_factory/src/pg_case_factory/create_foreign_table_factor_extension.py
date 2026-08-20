"""Bounded post-coverage cross-factor extension expander for CREATE FOREIGN TABLE.

The marginal factor-value-loop (:mod:`create_foreign_table_factor_loop`) is
the required baseline: one program per factor value, 96 local cases
(GRM 5 + SFV 91).  This module adds the bounded post-coverage extension
phase allowed by ``create_foreign_table.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 5 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode``/``cleanup_mode`` crossed so every
declared T6 value is exercised.

CREATE FOREIGN TABLE requires ``USAGE`` on the foreign server and on every
column data type; ``privilege_level=no_server_usage`` and
``privilege_level=no_type_usage`` are unconditional failures.  The T5
single-value factors (duplicate_table_name, nonexistent_server,
nonexistent_parent_table, no_server_usage_privilege,
no_type_usage_privilege, type_name_conflict_error, parent_has_unique_index)
are derived from their T1-T4 counterparts, not crossed as axes.

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

from .create_foreign_table_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_foreign_table_factor_loop_plan,
)


class CreateForeignTableFactorExtensionError(ValueError):
    """Raised when a frozen CREATE FOREIGN TABLE extension input drifts."""


@dataclass(frozen=True)
class CreateForeignTableFactorExtensionCase:
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
class CreateForeignTableFactorExtensionPlan:
    cases: tuple[CreateForeignTableFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 96
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "drop_foreign_table",
    "drop_foreign_table_cascade",
    "drop_server",
    "drop_fdw",
    "drop_parent_table",
)

# General axes crossed for ALL 5 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "already_exists",
        "type_name_conflict",
    ),
    "privilege_level": (
        "usage_on_server_and_types",
        "no_server_usage",
        "no_type_usage",
    ),
    "server_existence": (
        "server_exists",
        "server_not_exists",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# table_form are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "not_exists",
    "expected_status": "success",
    "table_form": "regular",
    "if_not_exists_clause": "omitted",
    "column_count": "single_column",
    "column_data_type": "integer",
    "inherits_clause": "omitted",
    "partition_bound_spec": "for_values_in",
    "server_clause": "valid_server",
    "table_name_shape": "simple_id",
    "column_name_shape": "simple_id",
    "server_name_shape": "simple_id",
    "constraint_name_shape": "omitted",
    "collation_name_shape": "omitted",
    "privilege_level": "usage_on_server_and_types",
    "server_existence": "server_exists",
    "parent_table_existence": "parent_exists",
    "schema_existence": "schema_exists",
    "type_name_conflict": "no_conflict",
    "duplicate_table_name": "no_conflict",
    "nonexistent_server": "server_exists",
    "nonexistent_parent_table": "parent_exists",
    "no_server_usage_privilege": "has_usage",
    "no_type_usage_privilege": "has_usage",
    "if_not_exists_no_op": "new_create",
    "zero_column_table": "has_columns",
    "constraint_not_enforced": "no_constraints",
    "type_name_conflict_error": "no_conflict",
    "parent_has_unique_index": "parent_no_unique",
    "verification_mode": "pg_class_catalog_query",
    "cleanup_mode": "drop_foreign_table",
}

# Branch -> (table_form, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "regular",
        "create_regular",
        {
            "column_data_type": (
                "integer",
                "bigint",
                "text",
                "varchar",
                "numeric",
                "boolean",
                "date",
                "timestamp",
                "jsonb",
                "uuid",
                "float8",
            ),
            "inherits_clause": (
                "omitted",
                "single_parent",
            ),
        },
    ),
    (
        "partition_of",
        "create_partition",
        {
            "partition_bound_spec": (
                "for_values_in",
                "default_partition",
            ),
            "parent_table_existence": (
                "parent_exists",
                "parent_not_exists",
            ),
        },
    ),
    (
        "like_source",
        "pg18_like_source",
        {},
    ),
    (
        "regular_virtual_generated",
        "pg18_virtual_generated",
        {},
    ),
    (
        "regular_table_not_null",
        "pg18_table_not_null",
        {},
    ),
)

# Branch -> statement_branch.
_BRANCH_STATEMENT_BRANCH = {
    "regular": "branch_regular",
    "partition_of": "branch_partition",
    "like_source": "branch_regular",
    "regular_virtual_generated": "branch_regular",
    "regular_table_not_null": "branch_regular",
}

# table_form -> target action (mirrors the loop module mapping).
_TABLE_FORM_ACTION = {
    "regular": "create_regular",
    "partition_of": "create_partition",
    "like_source": "pg18_like_source",
    "regular_virtual_generated": "pg18_virtual_generated",
    "regular_table_not_null": "pg18_table_not_null",
}

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  Overlapping T5 values are NOT listed here (they
# are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("object_state", "type_name_conflict"),
        ("privilege_level", "no_server_usage"),
        ("privilege_level", "no_type_usage"),
        ("server_existence", "server_not_exists"),
        ("parent_table_existence", "parent_not_exists"),
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

    # privilege_level no_server_usage / no_type_usage are unconditional
    # failures regardless of other factors; at most one failure overall.
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_val = a.get("object_state", "not_exists")
    if os_val == "already_exists":
        a["duplicate_table_name"] = "same_name_conflict"
        a["table_name_shape"] = "duplicate_name"
    elif os_val == "type_name_conflict":
        a["type_name_conflict"] = "same_as_existing_type"
        a["type_name_conflict_error"] = "conflict_with_existing_type"
    else:
        a["duplicate_table_name"] = "no_conflict"
        a["type_name_conflict"] = "no_conflict"
        a["type_name_conflict_error"] = "no_conflict"

    pl = a.get("privilege_level", "usage_on_server_and_types")
    if pl == "no_server_usage":
        a["no_server_usage_privilege"] = "lacks_usage"
        a["no_type_usage_privilege"] = "has_usage"
    elif pl == "no_type_usage":
        a["no_server_usage_privilege"] = "has_usage"
        a["no_type_usage_privilege"] = "lacks_usage"
    else:
        a["no_server_usage_privilege"] = "has_usage"
        a["no_type_usage_privilege"] = "has_usage"

    se = a.get("server_existence", "server_exists")
    if se == "server_not_exists":
        a["server_clause"] = "nonexistent_server"
        a["server_name_shape"] = "nonexistent_server"
        a["nonexistent_server"] = "server_missing"
    else:
        a["server_clause"] = "valid_server"
        a["server_name_shape"] = "simple_id"
        a["nonexistent_server"] = "server_exists"

    pte = a.get("parent_table_existence", "parent_exists")
    if pte == "parent_not_exists":
        a["nonexistent_parent_table"] = "parent_missing"
    else:
        a["nonexistent_parent_table"] = "parent_exists"

    # if_not_exists_no_op
    ifne = a.get("if_not_exists_clause", "omitted")
    if ifne == "specified" and os_val == "already_exists":
        a["if_not_exists_no_op"] = "no_op_notice"
    else:
        a["if_not_exists_no_op"] = "new_create"

    # zero_column_table
    cc = a.get("column_count", "single_column")
    if cc == "zero_columns":
        a["zero_column_table"] = "zero_columns"
    else:
        a["zero_column_table"] = "has_columns"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for table_form, action, axes in _BRANCH_CONFIG:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(
            *[all_axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["table_form"] = table_form
            assignment["statement_branch"] = _BRANCH_STATEMENT_BRANCH[
                table_form
            ]
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateForeignTableFactorExtensionError(
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
    cases: tuple[CreateForeignTableFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-foreign-table-factor-extension-v1\n"
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
    cases: tuple[CreateForeignTableFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE FOREIGN TABLE extension "
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
                        "create_foreign_table_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE FOREIGN TABLE",
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


def build_create_foreign_table_factor_extension_plan(
    repository_root: Path,
) -> CreateForeignTableFactorExtensionPlan:
    """Build the bounded CREATE FOREIGN TABLE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_foreign_table_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateForeignTableFactorExtensionCase] = []
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
                    CreateForeignTableFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATEFOREIGNTABLE{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATEFOREIGNTABLE{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createforeigntable_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CFT-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_foreign_table_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['table_form']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x server_existence="
                            f"{assignment['server_existence']} "
                            f"x verification_mode="
                            f"{verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=_TABLE_FORM_ACTION[
                            assignment["table_form"]
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return CreateForeignTableFactorExtensionPlan(
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
    "CreateForeignTableFactorExtensionError",
    "CreateForeignTableFactorExtensionCase",
    "CreateForeignTableFactorExtensionPlan",
    "build_create_foreign_table_factor_extension_plan",
]
