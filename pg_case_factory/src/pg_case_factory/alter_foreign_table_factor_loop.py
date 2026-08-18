"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER FOREIGN TABLE.

This module deliberately compiles marginal factor-value obligations.  It must
not enumerate the historical grammar/table/column candidate cross product.
Each local obligation will become exactly one regress program; inventory rows
owned by another statement remain explicit delegated handoffs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path

from .alter_foreign_table_regress import (
    compile_alter_foreign_table_column_obligations,
    load_alter_foreign_table_grammar_actions,
    load_alter_foreign_table_grammar_axes,
    load_alter_foreign_table_topologies,
    load_alter_foreign_table_type_witnesses,
)
from .applicability import CatalogRow, load_shipped_applicability_universe


class AlterForeignTableFactorLoopError(ValueError):
    """Raised when a frozen ALTER FOREIGN TABLE obligation input drifts."""


@dataclass(frozen=True)
class AlterForeignTableFactorObligation:
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
class AlterForeignTableFactorCase:
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
class AlterForeignTableFactorLoopPlan:
    obligations: tuple[AlterForeignTableFactorObligation, ...]
    cases: tuple[AlterForeignTableFactorCase, ...]
    delegated: tuple[AlterForeignTableFactorObligation, ...]
    obligation_multiset_sha256: str


_OUTER_AXIS_CONSUMER = {
    "branch_action_list": "add_column",
    "branch_rename_column": "rename_column",
    "branch_rename_table": "rename_table",
    "branch_set_schema": "set_schema",
}

_STATEMENT_BRANCH_CONSUMER = {
    "branch_action_list": "add_column",
    "branch_rename_column": "rename_column",
    "branch_rename_table": "rename_table",
    "branch_set_schema": "set_schema",
}

# A canonical factor is routed to one official action where the value is
# observable.  Baseline selection for the remaining factors is a later witness
# compilation step; this mapping does not claim that unrelated axes interact.
_SFV_FACTOR_CONSUMER = {
    "cleanup_mode": "add_column",
    "column_data_type": "add_column",
    "column_name_shape": "alter_column_type",
    "consistency_not_checked": "set_not_null",
    "constraint_name_shape": "validate_constraint",
    "constraint_not_enforced": "add_constraint",
    "expected_status": "add_column",
    "if_exists_notice": "drop_column",
    "new_column_name_shape": "rename_column",
    "new_schema_name_shape": "set_schema",
    "new_table_name_shape": "rename_table",
    "no_type_usage_privilege": "add_column",
    "non_owner_attempt": "add_column",
    "nonexistent_column": "drop_column",
    "nonexistent_constraint": "validate_constraint",
    "nonexistent_parent_table": "inherit",
    "nonexistent_table": "add_column",
    "object_state": "add_column",
    "only_clause": "add_column",
    "owner_name_shape": "owner",
    "parent_table_existence": "inherit",
    "parent_table_name_shape": "inherit",
    "privilege_level": "add_column",
    "schema_existence": "set_schema",
    "set_role_capability": "owner",
    "table_name_shape": "add_column",
    "type_usage_privilege": "add_column",
    "validate_constraint_no_action": "validate_constraint",
    "verification_mode": "add_column",
}

_SFV_FAILURE_VALUES = frozenset(
    {
        ("column_name_shape", "nonexistent_column"),
        ("constraint_name_shape", "nonexistent_constraint"),
        ("expected_status", "failure"),
        ("new_schema_name_shape", "nonexistent_schema"),
        ("no_type_usage_privilege", "lacks_usage"),
        ("non_owner_attempt", "non_owner_execution"),
        ("nonexistent_column", "column_missing"),
        ("nonexistent_constraint", "constraint_missing"),
        ("nonexistent_parent_table", "parent_missing"),
        ("nonexistent_table", "table_missing_no_if_exists"),
        ("object_state", "not_exists"),
        ("owner_name_shape", "nonexistent_role"),
        ("parent_table_existence", "parent_not_exists"),
        ("parent_table_name_shape", "nonexistent_parent"),
        ("privilege_level", "non_owner"),
        ("schema_existence", "schema_not_exists"),
        ("set_role_capability", "cannot_set_role"),
        ("table_name_shape", "nonexistent_name"),
        ("type_usage_privilege", "lacks_usage"),
    }
)


def _compile_grammar_obligations() -> list[AlterForeignTableFactorObligation]:
    rows: list[AlterForeignTableFactorObligation] = []
    for action in load_alter_foreign_table_grammar_actions():
        rows.append(
            AlterForeignTableFactorObligation(
                ordinal=0,
                obligation_id=(
                    "AFT-GRM|"
                    f"{action.grammar_branch_id}|{action.action_id}|"
                    f"target_action|{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    for axis in load_alter_foreign_table_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id.startswith("__outer_")
            else f"local:{axis.axis_id}"
        )
        consumer = (
            _OUTER_AXIS_CONSUMER[axis.grammar_branch_id]
            if axis.action_id.startswith("__outer_")
            else axis.action_id
        )
        for value in axis.values:
            rows.append(
                AlterForeignTableFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        "AFT-GRM|"
                        f"{axis.grammar_branch_id}|{axis.action_id}|"
                        f"{axis.axis_id}|{value}"
                    ),
                    kind="GRM",
                    factor_key=factor_key,
                    value=value,
                    consumer_action_id=consumer,
                    disposition="covered",
                    source_locator=axis.source_locator,
                )
            )
    if len(rows) != 136:
        raise AlterForeignTableFactorLoopError("grammar obligation count drift")
    return rows


def _baseline_assignments(
    obligation: AlterForeignTableFactorObligation,
) -> tuple[tuple[str, str], ...]:
    actions = {
        row.action_id: row for row in load_alter_foreign_table_grammar_actions()
    }
    try:
        action = actions[obligation.consumer_action_id]
    except KeyError as exc:
        raise AlterForeignTableFactorLoopError(
            f"unknown consumer action: {obligation.consumer_action_id}"
        ) from exc
    assignments: dict[str, str] = {
        "grammar_branch": action.grammar_branch_id,
        "target_action": action.action_id,
        "object_state": "exists",
        "privilege_level": "table_owner",
        "table_name_shape": "simple_id",
        "relation_topology": "standalone",
        "expected_status": "success",
        "verification_mode": "effect_query",
        "cleanup_mode": "drop_foreign_table",
    }
    outer_action = {
        "branch_action_list": "__outer_action_list__",
        "branch_rename_column": "__outer_rename_column__",
        "branch_rename_table": "__outer_rename_table__",
        "branch_set_schema": "__outer_set_schema__",
    }[action.grammar_branch_id]
    for axis in load_alter_foreign_table_grammar_axes():
        if axis.action_id == outer_action:
            assignments[f"outer:{axis.axis_id}"] = axis.values[0]
        elif axis.action_id == action.action_id:
            assignments[f"local:{axis.axis_id}"] = axis.values[0]
    assignments[obligation.factor_key] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterForeignTableFactorLoopError("duplicate baseline factor key")
    return tuple(assignments.items())


def _expected_failure_details(
    repository_root: Path,
    obligation: AlterForeignTableFactorObligation,
    type_expectations: dict[tuple[str, str, str], tuple[str, str]],
) -> tuple[str, str]:
    if obligation.kind == "INV" and obligation.factor_key == "data_type_and_typmod":
        selector, member = obligation.value.split("::", 1)
        try:
            return type_expectations[
                (selector, member, obligation.consumer_action_id)
            ]
        except KeyError as exc:
            raise AlterForeignTableFactorLoopError(
                "missing type failure expectation for "
                f"{selector}::{member}/{obligation.consumer_action_id}"
            ) from exc

    sfv_sqlstate = {
        ("new_schema_name_shape", "nonexistent_schema"): "3F000",
        ("schema_existence", "schema_not_exists"): "3F000",
        ("no_type_usage_privilege", "lacks_usage"): "42501",
        ("non_owner_attempt", "non_owner_execution"): "42501",
        ("privilege_level", "non_owner"): "42501",
        ("set_role_capability", "cannot_set_role"): "42501",
        ("type_usage_privilege", "lacks_usage"): "42501",
    }
    if obligation.kind == "SFV":
        sqlstate = sfv_sqlstate.get(
            (obligation.factor_key, obligation.value), "42704"
        )
        return (
            sqlstate,
            f"canonical_factor_rejected:{obligation.factor_key}={obligation.value}",
        )

    inventory_sqlstate = {
        "column_name_shape": "42703",
        "collation": "42704",
        "nullability": "0A000",
        "default_state": "0A000",
        "generation_mode": "42P17",
        "identity_mode": "22023",
        "primary_key_participation": "0A000",
        "unique_constraint": "0A000",
        "check_constraint": "0A000",
        "foreign_key_role": "0A000",
        "storage_and_compression": "0A000",
        "statistics_target": "22023",
        "dropped_or_existing_column_state": "42703",
    }
    direct_failure = {
        ("collation", "nonexistent_collation"): (
            "42704",
            "collation_not_found",
        ),
        ("collation", "collation_on_noncollatable_type"): (
            "42804",
            "collation_not_supported_by_type",
        ),
        ("collation", "encoding_incompatible_collation"): (
            "42704",
            "collation_not_available_for_database_encoding",
        ),
        ("nullability", "not_null_enforced"): (
            "42601",
            "invalid_nullability_constraint_combination",
        ),
        ("nullability", "not_null_not_enforced"): (
            "42601",
            "invalid_nullability_constraint_combination",
        ),
        ("nullability", "explicit_null_with_not_null"): (
            "42601",
            "invalid_nullability_constraint_combination",
        ),
        ("default_state", "incompatible_type_default"): (
            "42804",
            "default_expression_type_mismatch",
        ),
        ("default_state", "self_column_reference_default"): (
            "0A000",
            "column_reference_not_allowed_in_default",
        ),
        ("default_state", "other_column_reference_default"): (
            "0A000",
            "column_reference_not_allowed_in_default",
        ),
        ("default_state", "subquery_default"): (
            "0A000",
            "subquery_not_allowed_in_default",
        ),
        ("generation_mode", "volatile_generation_expression"): (
            "42P17",
            "generation_expression_not_immutable",
        ),
        ("generation_mode", "stable_generation_expression"): (
            "42P17",
            "generation_expression_not_immutable",
        ),
        ("generation_mode", "self_reference_generation_expression"): (
            "42P17",
            "generation_expression_self_reference",
        ),
        ("generation_mode", "generated_column_reference"): (
            "42P17",
            "generation_expression_references_generated_column",
        ),
        ("generation_mode", "subquery_generation_expression"): (
            "0A000",
            "subquery_not_allowed_in_generation_expression",
        ),
        ("generation_mode", "incompatible_generation_result_type"): (
            "42804",
            "generation_expression_type_mismatch",
        ),
        ("identity_mode", "identity_on_non_integer_type"): (
            "22023",
            "identity_column_type_not_integer",
        ),
        ("storage_and_compression", "compression_lz4"): (
            "0A000",
            "compression_method_not_supported_by_current_build",
        ),
        ("storage_and_compression", "unknown_compression_method"): (
            "22023",
            "unknown_compression_method",
        ),
        (
            "storage_and_compression",
            "incompatible_fixed_length_storage_mode",
        ): (
            "0A000",
            "storage_mode_not_supported_by_fixed_length_type",
        ),
    }
    if (obligation.factor_key, obligation.value) in direct_failure:
        return direct_failure[(obligation.factor_key, obligation.value)]
    sqlstate = inventory_sqlstate.get(obligation.factor_key, "0A000")
    return (
        sqlstate,
        f"inventory_member_rejected:{obligation.factor_key}={obligation.value}",
    )


def _obligation_multiset_sha256(
    rows: tuple[AlterForeignTableFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-foreign-table-factor-obligations-v1\n")
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


def build_alter_foreign_table_factor_loop_plan(
    repository_root: Path,
) -> AlterForeignTableFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_foreign_table_factor_loop_obligations(root)
    type_expectations: dict[tuple[str, str, str], tuple[str, str]] = {}
    for witness in load_alter_foreign_table_type_witnesses(root):
        for action_id in ("add_column", "alter_column_type"):
            expectation = witness.expectation_for(action_id)
            if expectation.outcome == "expected_failure":
                type_expectations[(witness.selector_id, witness.member, action_id)] = (
                    expectation.expected_sqlstate,
                    expectation.failure_reason or "type_member_rejected",
                )

    cases: list[AlterForeignTableFactorCase] = []
    delegated: list[AlterForeignTableFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(
                root, obligation, type_expectations
            )
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            AlterForeignTableFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERFOREIGNTABLE{ordinal:04d}",
                sql_filename=f"ALTERFOREIGNTABLE{ordinal:04d}.sql",
                object_prefix=f"alterforeigntable_{ordinal:04d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = AlterForeignTableFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 1_805 or len(plan.delegated) != 12:
        raise AlterForeignTableFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 1_805:
        raise AlterForeignTableFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 1_805:
        raise AlterForeignTableFactorLoopError("duplicate SQL filename")
    return plan


def _canonical_consumer(row: CatalogRow) -> str:
    if row.factor == "alter_action":
        return row.value
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterForeignTableFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "if_exists_clause":
        return (
            "add_column"
            if row.value.startswith("add_column_")
            else "drop_column"
        )
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterForeignTableFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterForeignTableFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_foreign_table")
    if len(catalog_rows) != 103:
        raise AlterForeignTableFactorLoopError("canonical obligation count drift")
    return [
        AlterForeignTableFactorObligation(
            ordinal=0,
            obligation_id=f"AFT-SFV|{row.row_id}|{_canonical_consumer(row)}",
            kind="SFV",
            factor_key=row.factor,
            value=row.value,
            consumer_action_id=_canonical_consumer(row),
            disposition=(
                "expected_failure"
                if (row.factor, row.value) in _SFV_FAILURE_VALUES
                else "covered"
            ),
            source_locator=f"{row.source_reference}#{row.row_id}",
        )
        for row in catalog_rows
    ]


def _compile_column_obligations(
    repository_root: Path,
) -> list[AlterForeignTableFactorObligation]:
    source = (
        "skills/pg-sql-generation/references/common/"
        "pg18_column_structure_catalog.yaml"
    )
    rows: list[AlterForeignTableFactorObligation] = []
    for column_row in compile_alter_foreign_table_column_obligations(
        repository_root
    ):
        delegated = column_row.consumer_action_id.startswith("handoff:")
        consumer = column_row.consumer_action_id
        disposition = "delegated" if delegated else column_row.disposition
        if (
            column_row.dimension_id == "storage_and_compression"
            and column_row.member_qualified_id == "compression_lz4"
        ):
            disposition = "expected_failure"
        rows.append(
            AlterForeignTableFactorObligation(
                ordinal=0,
                obligation_id=(
                    "AFT-INV|"
                    f"{consumer}|{column_row.dimension_id}|"
                    f"{column_row.member_qualified_id}"
                ),
                kind="INV",
                factor_key=column_row.dimension_id,
                value=column_row.member_qualified_id,
                consumer_action_id=consumer,
                disposition=disposition,
                source_locator=(
                    f"{source}#dimension={column_row.dimension_id};"
                    f"member={column_row.member_qualified_id}"
                ),
                delegated_statement_key=("create_index" if delegated else None),
            )
        )
    if len(rows) != 1_569:
        raise AlterForeignTableFactorLoopError("column obligation count drift")
    return rows


def _compile_topology_obligations() -> list[AlterForeignTableFactorObligation]:
    return [
        AlterForeignTableFactorObligation(
            ordinal=0,
            obligation_id=f"AFT-INV|add_column|relation_topology|{row.topology_id}",
            kind="INV",
            factor_key="relation_topology",
            value=row.topology_id,
            consumer_action_id="add_column",
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterforeigntable:relation-topology"
            ),
        )
        for row in load_alter_foreign_table_topologies()
    ]


def _compile_transaction_obligations() -> list[AlterForeignTableFactorObligation]:
    return [
        AlterForeignTableFactorObligation(
            ordinal=0,
            obligation_id=f"AFT-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id="add_column",
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterforeigntable:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def compile_alter_foreign_table_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterForeignTableFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_column_obligations(root)
        + _compile_topology_obligations()
        + _compile_transaction_obligations()
    )
    rows = tuple(
        replace(row, ordinal=ordinal)
        for ordinal, row in enumerate(unordered_rows, start=1)
    )
    if len(rows) != 1_817:
        raise AlterForeignTableFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterForeignTableFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 136, "SFV": 103, "INV": 1_576, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterForeignTableFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 12:
        raise AlterForeignTableFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 1_805:
        raise AlterForeignTableFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterForeignTableFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterForeignTableFactorLoopError",
    "AlterForeignTableFactorObligation",
    "AlterForeignTableFactorCase",
    "AlterForeignTableFactorLoopPlan",
    "build_alter_foreign_table_factor_loop_plan",
    "compile_alter_foreign_table_factor_loop_obligations",
]
