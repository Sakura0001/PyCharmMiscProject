"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER TABLE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER TABLE``.  It must not enumerate a table/column cross product:
``alter_table.yaml`` marks ``column_type_coverage`` ``conditional`` with
``expansion_mode: conditional``, so there is no ``INV`` block.  Each local
obligation will become exactly one regress program; there are no delegated
handoffs because every reachable negative boundary is a real
``ALTER TABLE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_table_regress import (
    AlterTableRegressError,
    load_alter_table_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterTableFactorLoopError(ValueError):
    """Raised when a frozen ALTER TABLE obligation input drifts."""


@dataclass(frozen=True)
class AlterTableFactorObligation:
    ordinal: int
    obligation_id: str
    kind: str
    factor_key: str
    value: str
    consumer_action_id: str
    disposition: str
    source_locator: str
    delegated_statement_key: str | None = None


@dataclass(frozen=True)
class AlterTableFactorCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    primary_obligation_id: str
    kind: str
    factor_key: str
    factor_value: str
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    baseline_assignments: tuple[tuple[str, str], ...]
    execution_profile: str


@dataclass(frozen=True)
class AlterTableFactorLoopPlan:
    obligations: tuple[AlterTableFactorObligation, ...]
    cases: tuple[AlterTableFactorCase, ...]
    delegated: tuple[AlterTableFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches.
_BRANCH_1_ACTION = "branch_1_action"
_BRANCH_2_RENAME_COLUMN = "branch_2_rename_column"
_BRANCH_3_RENAME_CONSTRAINT = "branch_3_rename_constraint"
_BRANCH_4_RENAME_TABLE = "branch_4_rename_table"
_BRANCH_5_SET_SCHEMA = "branch_5_set_schema"
_BRANCH_6_SET_TABLESPACE_BATCH = "branch_6_set_tablespace_batch"
_BRANCH_7_ATTACH_PARTITION = "branch_7_attach_partition"
_BRANCH_8_DETACH_PARTITION = "branch_8_detach_partition"

# A representative action used as the baseline consumer for canonical
# factors that are not bound to one specific sub-clause.
_REPRESENTATIVE_ACTION = "add_column"

# Canonical factor -> the action where the value is observable.
_SFV_FACTOR_CONSUMER = {
    "expected_status": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "if_not_exists_clause": _REPRESENTATIVE_ACTION,
    "only_clause": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "data_type": _REPRESENTATIVE_ACTION,
    "base_table_template_coverage": _REPRESENTATIVE_ACTION,
    "dependency_state": "drop_column",
    "cascade_restrict": "drop_column",
    "column_type_conversion": "alter_column_type",
    "column_name_shape": "alter_column_type",
    "constraint_name_shape": "drop_constraint",
    "new_name_shape": "rename_column",
    "expression_shape": "alter_column_type",
    "schema_dependency": "set_schema",
    "tablespace_dependency": "set_tablespace",
    "role_dependency": "owner_to",
    "parent_table_dependency": "inherit",
    "referenced_table_dependency": "add_table_constraint",
    "index_dependency": "add_table_constraint_using_index",
    "nonexistent_table": _REPRESENTATIVE_ACTION,
    "nonexistent_column": "alter_column_type",
    "nonexistent_constraint": "drop_constraint",
    "type_conversion_impossible": "alter_column_type",
    "constraint_violation_existing_data": "alter_column_set_drop_not_null",
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "partition_mismatch": "attach_partition",
    "dependent_objects_block": "drop_column",
    "identifier_length_exceeded": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1_ACTION: _REPRESENTATIVE_ACTION,
    _BRANCH_2_RENAME_COLUMN: "rename_column",
    _BRANCH_3_RENAME_CONSTRAINT: "rename_constraint",
    _BRANCH_4_RENAME_TABLE: "rename_table",
    _BRANCH_5_SET_SCHEMA: "set_schema",
    _BRANCH_6_SET_TABLESPACE_BATCH: "set_tablespace",
    _BRANCH_7_ATTACH_PARTITION: "attach_partition",
    _BRANCH_8_DETACH_PARTITION: "detach_partition",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (provisional sqlstates -- DB phase will verify on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("nonexistent_table", "without_IF_EXISTS_error"),
        ("nonexistent_column", "without_IF_EXISTS_error"),
        ("nonexistent_constraint", "without_IF_EXISTS_error"),
        ("type_conversion_impossible", "incompatible_no_using"),
        ("constraint_violation_existing_data", "set_not_null_with_nulls"),
        ("constraint_violation_existing_data", "add_check_with_violating_rows"),
        ("constraint_violation_existing_data", "add_unique_with_duplicates"),
        ("privilege_insufficient", "non_owner_attempt"),
        ("privilege_insufficient", "non_superuser_constraint_trigger"),
        ("partition_mismatch", "bound_overlap"),
        ("partition_mismatch", "bound_type_mismatch"),
        ("partition_mismatch", "detach_concurrently_with_FK"),
        ("dependent_objects_block", "drop_column_restrict_blocked"),
        ("dependent_objects_block", "drop_constraint_restrict_blocked"),
        ("identifier_length_exceeded", "over_63_chars"),
        ("privilege_level", "non_owner_no_privilege"),
        ("table_name_shape", "nonexistent"),
        ("column_name_shape", "nonexistent"),
        ("constraint_name_shape", "nonexistent"),
        ("new_name_shape", "duplicate"),
        ("schema_dependency", "schema_not_exists"),
        ("tablespace_dependency", "specified_tablespace_not_exists"),
        ("role_dependency", "owner_role_not_exists"),
        ("parent_table_dependency", "parent_not_exists"),
        ("parent_table_dependency", "parent_not_partitioned"),
        ("referenced_table_dependency", "referenced_table_not_exists"),
        ("index_dependency", "index_not_exists"),
    }
)


_GRM_SUB_ACTIONS = frozenset(
    {
        "add_column",
        "drop_column",
        "alter_column_type",
    }
)


def _axis_consumer(action_id: str) -> str:
    """Resolve the baseline action that witnesses a grammar modifier."""

    if action_id == "__outer_action__":
        return _REPRESENTATIVE_ACTION
    if action_id in _GRM_SUB_ACTIONS:
        return action_id
    return action_id


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTableFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "subcommand_category":
        return row.value
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterTableFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterTableFactorObligation]:
    rows: list[AlterTableFactorObligation] = []
    for axis in load_alter_table_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id == "__outer_action__"
            else f"local:{axis.axis_id}"
        )
        consumer = _axis_consumer(axis.action_id)
        for value in axis.values:
            rows.append(
                AlterTableFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"ALT-TBL-GRM|{axis.grammar_branch_id}|"
                        f"{axis.action_id}|{axis.axis_id}|{value}"
                    ),
                    kind="GRM",
                    factor_key=factor_key,
                    value=value,
                    consumer_action_id=consumer,
                    disposition="covered",
                    source_locator=axis.source_locator,
                )
            )
    if len(rows) != 8:
        raise AlterTableFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterTableFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_table")
    if len(catalog_rows) != 197:
        raise AlterTableFactorLoopError("canonical obligation count drift")
    rows: list[AlterTableFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterTableFactorObligation(
                ordinal=0,
                obligation_id=f"ALTERTABLE-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure"
                    if (row.factor, row.value) in _SFV_FAILURE_VALUES
                    else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _compile_risk_obligations() -> list[AlterTableFactorObligation]:
    return [
        AlterTableFactorObligation(
            ordinal=0,
            obligation_id=f"ALTERTABLE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-altertable:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterTableFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-table-factor-obligations-v1\n")
    for row in rows:
        digest.update(
            json.dumps(
                {
                    "obligation_id": row.obligation_id,
                    "kind": row.kind,
                    "factor_key": row.factor_key,
                    "value": row.value,
                    "consumer_action_id": row.consumer_action_id,
                    "disposition": row.disposition,
                    "delegated_statement_key": row.delegated_statement_key,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _consumer_branch_map() -> dict[str, str]:
    # Every consumer_action_id that appears in the obligation ledger must
    # resolve to exactly one statement_branch.  The 53 subcommand_category
    # values dominate the count; most are branch_1 (general ALTER TABLE
    # <action>), with the special syntactic forms routed to their branch.
    branch_1 = _BRANCH_1_ACTION
    return {
        # --- branch_1_action (general ALTER TABLE <action>) ---
        "add_column": branch_1,
        "add_virtual_generated_column": branch_1,
        "add_temporal_constraint": branch_1,
        "drop_column": branch_1,
        "alter_column_type": branch_1,
        "alter_column_set_default": branch_1,
        "alter_column_drop_default": branch_1,
        "alter_column_set_drop_not_null": branch_1,
        "alter_column_drop_expression": branch_1,
        "alter_column_set_expression": branch_1,
        "alter_column_add_generated_identity": branch_1,
        "alter_column_set_generated_restart": branch_1,
        "alter_column_drop_identity": branch_1,
        "alter_column_set_statistics": branch_1,
        "alter_column_set_statistics_default": branch_1,
        "alter_column_set_attribute_option": branch_1,
        "alter_column_reset_attribute_option": branch_1,
        "alter_column_set_storage": branch_1,
        "alter_column_set_compression": branch_1,
        "add_table_constraint": branch_1,
        "add_table_constraint_using_index": branch_1,
        "alter_constraint": branch_1,
        "alter_constraint_enforced": branch_1,
        "alter_constraint_inherit": branch_1,
        "validate_constraint": branch_1,
        "drop_constraint": branch_1,
        "disable_trigger": branch_1,
        "enable_trigger": branch_1,
        "enable_replica_trigger": branch_1,
        "enable_always_trigger": branch_1,
        "disable_rule": branch_1,
        "enable_rule": branch_1,
        "enable_replica_rule": branch_1,
        "enable_always_rule": branch_1,
        "disable_row_level_security": branch_1,
        "enable_row_level_security": branch_1,
        "force_row_level_security": branch_1,
        "no_force_row_level_security": branch_1,
        "cluster_on": branch_1,
        "set_without_cluster": branch_1,
        "set_without_oids": branch_1,
        "set_access_method": branch_1,
        "set_access_method_default": branch_1,
        "set_logged_unlogged": branch_1,
        "set_storage_parameter": branch_1,
        "reset_storage_parameter": branch_1,
        "inherit": branch_1,
        "no_inherit": branch_1,
        "of_type": branch_1,
        "not_of": branch_1,
        "owner_to": branch_1,
        "replica_identity": branch_1,
        # --- branch_2_rename_column ---
        "rename_column": _BRANCH_2_RENAME_COLUMN,
        # --- branch_3_rename_constraint ---
        "rename_constraint": _BRANCH_3_RENAME_CONSTRAINT,
        # --- branch_4_rename_table ---
        "rename_table": _BRANCH_4_RENAME_TABLE,
        # --- branch_5_set_schema ---
        "set_schema": _BRANCH_5_SET_SCHEMA,
        # --- branch_6_set_tablespace_batch ---
        "set_tablespace": _BRANCH_6_SET_TABLESPACE_BATCH,
        # --- branch_7_attach_partition ---
        "attach_partition": _BRANCH_7_ATTACH_PARTITION,
        # --- branch_8_detach_partition ---
        "detach_partition": _BRANCH_8_DETACH_PARTITION,
    }


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# These will be verified against an isolated 18.4 instance in the DB phase.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("object_state", "not_exists"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("nonexistent_table", "without_IF_EXISTS_error"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("nonexistent_column", "without_IF_EXISTS_error"): (
        "42703",
        "undefined_column",
    ),
    ("nonexistent_constraint", "without_IF_EXISTS_error"): (
        "42704",
        "undefined_object",
    ),
    ("type_conversion_impossible", "incompatible_no_using"): (
        "42804",
        "datatype_mismatch",
    ),
    ("constraint_violation_existing_data", "set_not_null_with_nulls"): (
        "23502",
        "not_null_violation",
    ),
    ("constraint_violation_existing_data", "add_check_with_violating_rows"): (
        "23514",
        "check_violation",
    ),
    ("constraint_violation_existing_data", "add_unique_with_duplicates"): (
        "23505",
        "unique_violation",
    ),
    ("privilege_insufficient", "non_owner_attempt"): (
        "42501",
        "insufficient_privilege",
    ),
    ("privilege_insufficient", "non_superuser_constraint_trigger"): (
        "42501",
        "insufficient_privilege",
    ),
    ("partition_mismatch", "bound_overlap"): (
        "42P17",
        "object_not_in_prerequisite_state",
    ),
    ("partition_mismatch", "bound_type_mismatch"): (
        "42P17",
        "object_not_in_prerequisite_state",
    ),
    ("partition_mismatch", "detach_concurrently_with_FK"): (
        "55006",
        "object_not_in_prerequisite_state",
    ),
    ("dependent_objects_block", "drop_column_restrict_blocked"): (
        "2BP01",
        "dependent_objects_still_exist",
    ),
    ("dependent_objects_block", "drop_constraint_restrict_blocked"): (
        "2BP01",
        "dependent_objects_still_exist",
    ),
    ("identifier_length_exceeded", "over_63_chars"): (
        "42622",
        "name_too_long",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "insufficient_privilege",
    ),
    ("table_name_shape", "nonexistent"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("column_name_shape", "nonexistent"): (
        "42703",
        "undefined_column",
    ),
    ("constraint_name_shape", "nonexistent"): (
        "42704",
        "undefined_object",
    ),
    ("new_name_shape", "duplicate"): (
        "42P07",
        "duplicate_table",
    ),
    ("schema_dependency", "schema_not_exists"): (
        "3F000",
        "schema_does_not_exist",
    ),
    ("tablespace_dependency", "specified_tablespace_not_exists"): (
        "42704",
        "undefined_object",
    ),
    ("role_dependency", "owner_role_not_exists"): (
        "42704",
        "undefined_object",
    ),
    ("parent_table_dependency", "parent_not_exists"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("parent_table_dependency", "parent_not_partitioned"): (
        "42809",
        "wrong_object_type",
    ),
    ("referenced_table_dependency", "referenced_table_not_exists"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("index_dependency", "index_not_exists"): (
        "42704",
        "undefined_object",
    ),
    # Sentinel attribution key for the SESSION_USER owner-transfer membership
    # wall.  Under a non-superuser table owner, OWNER TO <explicit role>
    # requires SET ROLE membership; SESSION_USER is a provisional no-op escape.
    ("role_specification", "membership_required_under_owner"): (
        "42501",
        "owner_change_requires_membership",
    ),
}


def _expected_failure_details(
    obligation: AlterTableFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterTableFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: AlterTableFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "statement_branch": branch,
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
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
        # GRM-axis baselines (minimal / absent form).
        "add_column_keyword": "absent",
        "drop_column_keyword": "absent",
        "alter_column_keyword": "absent",
        "set_data_keyword": "absent",
    }
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterTableFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_table_factor_loop_plan(
    repository_root: Path,
) -> AlterTableFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_table_factor_loop_obligations(root)
    cases: list[AlterTableFactorCase] = []
    delegated: list[AlterTableFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(obligation)
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            AlterTableFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERTABLE{ordinal:05d}",
                sql_filename=f"ALTERTABLE{ordinal:05d}.sql",
                object_prefix=f"altertable_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=_renderer_factor_key(obligation.factor_key),
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = AlterTableFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 207 or len(plan.delegated) != 0:
        raise AlterTableFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 207:
        raise AlterTableFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 207:
        raise AlterTableFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_table_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterTableFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterTableFactorObligation(
            ordinal=ordinal,
            obligation_id=row.obligation_id,
            kind=row.kind,
            factor_key=row.factor_key,
            value=row.value,
            consumer_action_id=row.consumer_action_id,
            disposition=row.disposition,
            source_locator=row.source_locator,
            delegated_statement_key=row.delegated_statement_key,
        )
        for ordinal, row in enumerate(unordered_rows, start=1)
    )
    if len(rows) != 207:
        raise AlterTableFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterTableFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 8, "SFV": 197, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterTableFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterTableFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 207:
        raise AlterTableFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterTableFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterTableFactorLoopError",
    "AlterTableFactorObligation",
    "AlterTableFactorCase",
    "AlterTableFactorLoopPlan",
    "compile_alter_table_factor_loop_obligations",
    "build_alter_table_factor_loop_plan",
    "_obligation_multiset_sha256",
]
