"""Bounded post-coverage cross-factor extension expander for ALTER TABLE.

The marginal factor-value-loop (:mod:`alter_table_factor_loop`) is the
required baseline: one program per factor value, 207 local cases
(GRM 8 + SFV 197 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_table.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive T1-T4 behaviour axes (at most one failure-causing value per
case, so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

SESSION_USER owner-transfer escape: ``OWNER TO SESSION_USER`` is a
provisional permitted no-op transfer that escapes both the privilege cluster
(non_owner_no_privilege) and the SET-ROLE membership wall.  Under a
non-superuser table owner, OWNER TO with an explicit role fails 42501
(requires SET ROLE membership); only ``SESSION_USER`` escapes.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_table_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_table_factor_loop_plan,
)


class AlterTableFactorExtensionError(ValueError):
    """Raised when a frozen ALTER TABLE extension input drifts."""


@dataclass(frozen=True)
class AlterTableFactorExtensionCase:
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
class AlterTableFactorExtensionPlan:
    cases: tuple[AlterTableFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 207
_CAP = 50000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "pg_attribute_query",
    "pg_constraint_query",
    "information_schema_query",
    "SELECT_inspection",
)
_CLEANUP_MODES = (
    "DROP_TABLE_IF_EXISTS",
    "DROP_TABLE_CASCADE",
    "ALTER_TABLE_REVERT",
    "RESET_STATE",
)

_BRANCH_1_ACTION = "branch_1_action"
_BRANCH_2_RENAME_COLUMN = "branch_2_rename_column"
_BRANCH_4_RENAME_TABLE = "branch_4_rename_table"
_BRANCH_5_SET_SCHEMA = "branch_5_set_schema"

# Privilege cluster: non_owner_no_privilege models must_be_owner (42501).
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner_no_privilege"})
_SESSION_USER_ESCAPE = "current_role_variants"
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset({"owner_role_exists"})

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1_ACTION,
    "grammar_branch": _BRANCH_1_ACTION,
    "target_action": "add_column",
    "object_state": "exists_normal",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "if_not_exists_clause": "absent",
    "only_clause": "absent",
    "privilege_level": "superuser",
    "table_name_shape": "simple",
    "column_name_shape": "simple",
    "constraint_name_shape": "simple",
    "new_name_shape": "simple",
    "data_type": "integer",
    "expression_shape": "simple_cast",
    "column_type_conversion": "compatible_no_using",
    "base_table_template_coverage": "table_01_comprehensive_types",
    "dependency_state": "no_dependencies",
    "schema_dependency": "schema_exists",
    "tablespace_dependency": "default_tablespace",
    "role_dependency": "owner_role_exists",
    "parent_table_dependency": "parent_partitioned_exists",
    "referenced_table_dependency": "referenced_table_exists",
    "index_dependency": "index_exists",
    "nonexistent_table": "with_IF_EXISTS_notice",
    "nonexistent_column": "with_IF_EXISTS_notice",
    "nonexistent_constraint": "with_IF_EXISTS_notice",
    "type_conversion_impossible": "incompatible_no_using",
    "constraint_violation_existing_data": "set_not_null_with_nulls",
    "privilege_insufficient": "non_owner_attempt",
    "partition_mismatch": "bound_overlap",
    "dependent_objects_block": "drop_column_cascade",
    "identifier_length_exceeded": "over_63_chars",
    "verification_mode": "pg_class_catalog_query",
    "cleanup_mode": "DROP_TABLE_IF_EXISTS",
    "cascade_restrict": "absent",
    "add_column_keyword": "absent",
    "drop_column_keyword": "absent",
    "alter_column_keyword": "absent",
    "set_data_keyword": "absent",
}

_CONSUMER_BRANCH: dict[str, str] = {
    "add_column": _BRANCH_1_ACTION,
    "drop_column": _BRANCH_1_ACTION,
    "alter_column_type": _BRANCH_1_ACTION,
    "owner_to": _BRANCH_1_ACTION,
    "rename_column": _BRANCH_2_RENAME_COLUMN,
    "rename_table": _BRANCH_4_RENAME_TABLE,
    "set_schema": _BRANCH_5_SET_SCHEMA,
}

_CONSUMER_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "add_column": {
        "if_exists_clause": ("absent", "present"),
        "if_not_exists_clause": ("absent", "present"),
        "table_name_shape": ("simple", "quoted", "schema_qualified"),
        "privilege_level": ("superuser", "table_owner", "non_owner_no_privilege"),
    },
    "drop_column": {
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict": ("CASCADE", "RESTRICT", "absent"),
        "table_name_shape": ("simple", "quoted", "schema_qualified"),
        "privilege_level": ("superuser", "table_owner", "non_owner_no_privilege"),
    },
    "alter_column_type": {
        "table_name_shape": ("simple", "quoted", "schema_qualified"),
        "privilege_level": ("superuser", "table_owner", "non_owner_no_privilege"),
        "column_type_conversion": (
            "compatible_no_using",
            "compatible_with_collation",
            "incompatible_with_using",
        ),
    },
    "owner_to": {
        "role_dependency": (
            "current_role_variants",
            "owner_role_exists",
            "owner_role_not_exists",
        ),
        "table_name_shape": ("simple", "schema_qualified"),
        "privilege_level": ("superuser", "table_owner", "non_owner_no_privilege"),
    },
    "rename_column": {
        "if_exists_clause": ("absent", "present"),
        "table_name_shape": ("simple", "quoted", "schema_qualified"),
        "new_name_shape": ("simple", "quoted", "duplicate"),
        "privilege_level": ("superuser", "table_owner", "non_owner_no_privilege"),
    },
    "rename_table": {
        "if_exists_clause": ("absent", "present"),
        "table_name_shape": ("simple", "quoted", "schema_qualified"),
        "new_name_shape": ("simple", "quoted", "duplicate"),
        "privilege_level": ("superuser", "table_owner", "non_owner_no_privilege"),
    },
    "set_schema": {
        "if_exists_clause": ("absent", "present"),
        "table_name_shape": ("simple", "schema_qualified"),
        "schema_dependency": ("schema_exists", "schema_not_exists"),
        "privilege_level": ("superuser", "table_owner", "non_owner_no_privilege"),
    },
}

_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("new_name_shape", "duplicate"),
        ("schema_dependency", "schema_not_exists"),
        ("role_dependency", "owner_role_not_exists"),
    }
)


def _owner_privilege_failure(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """The role-membership wall (factor, value) pair, else None."""

    if assignment.get("privilege_level") != "table_owner":
        return None
    target_action = assignment.get("target_action")
    if (
        target_action == "owner_to"
        and assignment.get("role_dependency") in _OWNER_TARGET_REQUIRES_MEMBERSHIP
    ):
        return ("role_specification", "membership_required_under_owner")
    return None


def _privilege_cluster_fires(assignment: dict[str, str]) -> bool:
    """The privilege wall firing for non-owners, EXCEPT SESSION_USER."""

    level = assignment.get("privilege_level")
    if level not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    if assignment.get("role_dependency") == _SESSION_USER_ESCAPE:
        return False
    return True


def _applicable_negative(
    factor: str, value: str, assignment: dict[str, str]
) -> bool:
    action = assignment.get("target_action", "")
    if factor == "new_name_shape":
        return action in ("rename_column", "rename_table")
    if factor == "schema_dependency":
        return action == "set_schema"
    if factor == "role_dependency":
        return action == "owner_to"
    return False


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    pair = _owner_privilege_failure(assignment)
    if pair is not None:
        return pair
    if _privilege_cluster_fires(assignment):
        level = assignment.get("privilege_level")
        return ("privilege_level", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if _applicable_negative(neg_factor, neg_value, assignment):
            return (neg_factor, neg_value)
    return None


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _owner_privilege_failure(assignment) is not None:
        count += 1
    if _privilege_cluster_fires(assignment):
        count += 1
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if _applicable_negative(neg_factor, neg_value, assignment):
            count += 1
    return count


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    return _failure_unit_count(assignment) <= 1


def _outcome_for(assignment: dict[str, str]) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is not None:
        sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
        return "expected_failure", sqlstate, reason
    return "success", "00000", None


def _behavior_combinations() -> list[dict[str, str]]:
    behaviors: list[dict[str, str]] = []
    for consumer, axes in _CONSUMER_AXES.items():
        branch = _CONSUMER_BRANCH[consumer]
        keys = list(axes.keys())
        value_lists = [axes[k] for k in keys]
        for combo in itertools.product(*value_lists):
            assignment = dict(_BASELINE_DEFAULTS)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = branch
            assignment["target_action"] = consumer
            for key, value in zip(keys, combo):
                assignment[key] = value
            if _is_valid_combination(assignment):
                assignment["expected_status"] = (
                    "failure" if _present_failure_pair(assignment) else "success"
                )
                behaviors.append(assignment)
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    return behaviors


def _extension_multiset_sha256(
    cases: tuple[AlterTableFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-table-factor-extension-v1\n")
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
    cases: tuple[AlterTableFactorExtensionCase, ...],
) -> str:
    entries = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": f"cross-factor extension for {case.consumer_action_id}",
                "derived_from_combination_group": case.derived_from_combination_group,
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": "per_factor_binding",
                "compatibility": {
                    "resolver": "declared_matrix",
                    "attribution_pair": (
                        list(_present_failure_pair(assignment))
                        if _present_failure_pair(assignment)
                        else None
                    ),
                },
                "sql_shape": {
                    "target": "ALTER TABLE ...",
                    "primary_fence": "-- primary-target-begin / -- primary-target-end",
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment.get("verification_mode"),
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment.get("cleanup_mode"),
                },
            }
        )
    return yaml.safe_dump(entries, sort_keys=False, allow_unicode=True)


def build_alter_table_factor_extension_plan(
    repository_root: Path,
) -> AlterTableFactorExtensionPlan:
    """Build the bounded ALTER TABLE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    # Enforce the baseline invariant before building extensions.
    build_alter_table_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    ordinal = _BASELINE_COUNT
    cases: list[AlterTableFactorExtensionCase] = []
    raw = 0
    for behavior in behaviors:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                if len(cases) >= _CAP:
                    continue
                assignment = dict(behavior)
                assignment["verification_mode"] = verification
                assignment["cleanup_mode"] = cleanup
                consumer = assignment.get("target_action", "add_column")
                outcome, sqlstate, reason = _outcome_for(assignment)
                ordinal += 1
                case_id = f"ALTERTABLE{ordinal:05d}"
                derivation_id = (
                    f"ALT-TBL-EXT|{ordinal:05d}|{consumer}|"
                    f"{verification}|{cleanup}"
                )
                cases.append(
                    AlterTableFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=case_id,
                        sql_filename=f"{case_id}.sql",
                        object_prefix=f"altertable_{ordinal:05d}_",
                        derivation_id=derivation_id,
                        derived_from_combination_group=(
                            "alter_table_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: target_action={consumer}"
                            f" x verification_mode={verification}"
                            f" x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(sorted(assignment.items())),
                        consumer_action_id=consumer,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    plan = AlterTableFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(tuple(cases)),
        derived_combinations_yaml=_derived_combinations_yaml(tuple(cases)),
        dropped_count=dropped,
        raw_combination_count=raw,
    )
    if plan.dropped_count != 0:
        raise AlterTableFactorExtensionError("extension dropped_count drift")
    return plan


__all__ = [
    "AlterTableFactorExtensionError",
    "AlterTableFactorExtensionCase",
    "AlterTableFactorExtensionPlan",
    "build_alter_table_factor_extension_plan",
    "_present_failure_pair",
]
