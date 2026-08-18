"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER FOREIGN TABLE.

This module deliberately compiles marginal factor-value obligations.  It must
not enumerate the historical grammar/table/column candidate cross product.
Each local obligation will become exactly one regress program; inventory rows
owned by another statement remain explicit delegated handoffs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

from .alter_foreign_table_regress import (
    compile_alter_foreign_table_column_obligations,
    load_alter_foreign_table_grammar_actions,
    load_alter_foreign_table_grammar_axes,
    load_alter_foreign_table_topologies,
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
                    factor_key=axis.axis_id,
                    value=value,
                    consumer_action_id=consumer,
                    disposition="covered",
                    source_locator=axis.source_locator,
                )
            )
    if len(rows) != 136:
        raise AlterForeignTableFactorLoopError("grammar obligation count drift")
    return rows


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
                disposition=("delegated" if delegated else column_row.disposition),
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
    "compile_alter_foreign_table_factor_loop_obligations",
]
