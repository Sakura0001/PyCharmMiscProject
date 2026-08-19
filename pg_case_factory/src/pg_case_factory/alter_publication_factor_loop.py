"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER PUBLICATION.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER PUBLICATION``.  It must not enumerate a table/column cross product:
``alter_publication.yaml`` marks ``column_type_coverage`` ``conditional``
on the ADD/SET branches, so there is no ``INV`` block.  Each local
obligation will become exactly one regress program; there are no delegated
handoffs because every reachable negative boundary is a real
``ALTER PUBLICATION`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_publication_regress import (
    AlterPublicationRegressError,
    load_alter_publication_grammar_actions,
    load_alter_publication_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterPublicationFactorLoopError(ValueError):
    """Raised when a frozen ALTER PUBLICATION obligation input drifts."""


@dataclass(frozen=True)
class AlterPublicationFactorObligation:
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
class AlterPublicationFactorCase:
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
class AlterPublicationFactorLoopPlan:
    obligations: tuple[AlterPublicationFactorObligation, ...]
    cases: tuple[AlterPublicationFactorCase, ...]
    delegated: tuple[AlterPublicationFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches.
_BRANCH_ADD = "branch_add"
_BRANCH_SET_OBJECT = "branch_set_object"
_BRANCH_DROP = "branch_drop"
_BRANCH_SET_PARAMETER = "branch_set_parameter"
_BRANCH_OWNER_TO = "branch_owner_to"
_BRANCH_RENAME = "branch_rename"

# A representative branch_add action used as the baseline consumer for
# canonical factors that are not bound to one specific sub-clause.
_REPRESENTATIVE_ACTION = "add_object"

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, publication_state,
# add_set_drop_operation) are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "expected_status": _REPRESENTATIVE_ACTION,
    "publication_parameter": "set_parameter",
    "owner_to_clause": "owner",
    "column_filter": _REPRESENTATIVE_ACTION,
    "where_clause": _REPRESENTATIVE_ACTION,
    "publication_name_shape": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "schema_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "new_owner_shape": "owner",
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "table_dependency": _REPRESENTATIVE_ACTION,
    "schema_dependency": _REPRESENTATIVE_ACTION,
    "nonexistent_publication": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "nonexistent_table": _REPRESENTATIVE_ACTION,
    "nonexistent_schema": _REPRESENTATIVE_ACTION,
    "drop_from_for_all_tables": "drop_object",
    "conflicting_add_existing_table": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER = {
    "branch_add": "add_object",
    "branch_set_object": "set_object",
    "branch_drop": "drop_object",
    "branch_set_parameter": "set_parameter",
    "branch_owner_to": "owner",
    "branch_rename": "rename",
}

_PUBLICATION_STATE_CONSUMER = {
    "exists": "add_object",
    "exists_with_tables": "add_object",
    "non_existent": "add_object",
    "exists_as_for_all_tables": "drop_object",
}

_OPERATION_CONSUMER = {
    "add_table": "add_object",
    "add_tables_in_schema": "add_object",
    "set_table": "set_object",
    "set_tables_in_schema": "set_object",
    "drop_table": "drop_object",
    "drop_tables_in_schema": "drop_object",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (provisional sqlstates -- DB phase will verify on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("publication_state", "non_existent"),
        ("publication_state", "exists_as_for_all_tables"),
        ("executor_privilege", "non_owner_no_privilege"),
        ("table_dependency", "table_not_exists"),
        ("schema_dependency", "schema_not_exists"),
        ("table_name_shape", "nonexistent_table"),
        ("schema_name_shape", "nonexistent_schema"),
        ("new_owner_shape", "nonexistent_role"),
        ("new_name_shape", "existing_name_conflict"),
        ("publication_name_shape", "non_existent_name"),
        ("nonexistent_publication", "publication_does_not_exist"),
        ("privilege_insufficient", "non_owner_altering_publication"),
        ("privilege_insufficient", "non_superuser_altering_other_publication"),
        ("nonexistent_table", "add_nonexistent_table_failure"),
        ("nonexistent_schema", "add_nonexistent_schema_failure"),
        ("drop_from_for_all_tables", "cannot_drop_from_for_all_tables"),
        ("conflicting_add_existing_table", "table_already_in_publication"),
    }
)


def _axis_consumer(action_id: str) -> str:
    """Resolve the baseline action that witnesses an outer/axis modifier."""

    if action_id == "__outer_action__":
        return _REPRESENTATIVE_ACTION
    return action_id


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterPublicationFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "publication_state":
        try:
            return _PUBLICATION_STATE_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterPublicationFactorLoopError(
                f"unknown publication_state value: {row.value}"
            ) from exc
    if row.factor == "add_set_drop_operation":
        try:
            return _OPERATION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterPublicationFactorLoopError(
                f"unknown add_set_drop_operation value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterPublicationFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterPublicationFactorObligation]:
    rows: list[AlterPublicationFactorObligation] = []
    for action in load_alter_publication_grammar_actions():
        rows.append(
            AlterPublicationFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ALTPUB-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    for axis in load_alter_publication_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id == "__outer_action__"
            else f"local:{axis.axis_id}"
        )
        consumer = _axis_consumer(axis.action_id)
        for value in axis.values:
            rows.append(
                AlterPublicationFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"ALTPUB-GRM|{axis.grammar_branch_id}|"
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
    if len(rows) != 26:
        raise AlterPublicationFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterPublicationFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_publication")
    if len(catalog_rows) != 65:
        raise AlterPublicationFactorLoopError("canonical obligation count drift")
    rows: list[AlterPublicationFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterPublicationFactorObligation(
                ordinal=0,
                obligation_id=f"ALTPUB-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterPublicationFactorObligation]:
    return [
        AlterPublicationFactorObligation(
            ordinal=0,
            obligation_id=f"ALTPUB-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterpublication:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterPublicationFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-publication-factor-obligations-v1\n")
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
    return {
        action.action_id: action.grammar_branch_id
        for action in load_alter_publication_grammar_actions()
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
        "44000",
        "publication_does_not_exist",
    ),
    ("publication_state", "non_existent"): (
        "44000",
        "publication_does_not_exist",
    ),
    ("publication_state", "exists_as_for_all_tables"): (
        "42809",
        "cannot_drop_from_for_all_tables",
    ),
    ("executor_privilege", "non_owner_no_privilege"): (
        "42501",
        "privilege_denied_for_publication",
    ),
    ("table_dependency", "table_not_exists"): (
        "42P01",
        "table_does_not_exist",
    ),
    ("schema_dependency", "schema_not_exists"): (
        "3F000",
        "schema_does_not_exist",
    ),
    ("table_name_shape", "nonexistent_table"): (
        "42P01",
        "table_does_not_exist",
    ),
    ("schema_name_shape", "nonexistent_schema"): (
        "3F000",
        "schema_does_not_exist",
    ),
    ("new_owner_shape", "nonexistent_role"): (
        "42704",
        "role_does_not_exist",
    ),
    ("new_name_shape", "existing_name_conflict"): (
        "42710",
        "duplicate_object",
    ),
    ("publication_name_shape", "non_existent_name"): (
        "44000",
        "publication_does_not_exist",
    ),
    ("nonexistent_publication", "publication_does_not_exist"): (
        "44000",
        "publication_does_not_exist",
    ),
    ("privilege_insufficient", "non_owner_altering_publication"): (
        "42501",
        "privilege_denied_for_publication",
    ),
    ("privilege_insufficient", "non_superuser_altering_other_publication"): (
        "42501",
        "privilege_denied_for_publication",
    ),
    ("nonexistent_table", "add_nonexistent_table_failure"): (
        "42P01",
        "table_does_not_exist",
    ),
    ("nonexistent_schema", "add_nonexistent_schema_failure"): (
        "3F000",
        "schema_does_not_exist",
    ),
    ("drop_from_for_all_tables", "cannot_drop_from_for_all_tables"): (
        "42809",
        "cannot_drop_from_for_all_tables",
    ),
    ("conflicting_add_existing_table", "table_already_in_publication"): (
        "42710",
        "duplicate_object",
    ),
    # Sentinel attribution key for the superuser-only owner-transfer wall
    # that fires only under a non-superuser publication owner: OWNER TO
    # <role> requires superuser (CURRENT_ROLE / CURRENT_USER fail 42501).
    # SESSION_USER is a permitted no-op transfer (PG 18.4 allows even for
    # non-owners) and does NOT fire this wall.  Surfaced by
    # _present_failure_pair in the extension expander.
    ("owner_to_clause", "membership_required_under_owner"): (
        "42501",
        "owner_change_requires_superuser",
    ),
}


def _expected_failure_details(
    obligation: AlterPublicationFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterPublicationFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


_BRANCH_BASELINE_OPERATION = {
    _BRANCH_ADD: "add_table",
    _BRANCH_SET_OBJECT: "set_table",
    _BRANCH_DROP: "drop_table",
}


def _baseline_assignments(
    obligation: AlterPublicationFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "publication_state": "exists",
        "expected_status": "success",
        "add_set_drop_operation": _BRANCH_BASELINE_OPERATION.get(branch, "add_table"),
        "publication_parameter": "publish_insert_only",
        "owner_to_clause": "explicit_role_name",
        "column_filter": "no_column_filter",
        "where_clause": "no_where",
        "publication_name_shape": "simple_name",
        "table_name_shape": "simple_name",
        "schema_name_shape": "simple_name",
        "new_name_shape": "simple_name",
        "new_owner_shape": "existing_role",
        "executor_privilege": "superuser",
        "table_dependency": "table_exists",
        "schema_dependency": "schema_exists",
        "verification_mode": "pg_publication_catalog",
        "cleanup_mode": "drop_publication",
        # GRM axis baselines (minimal / absent form).
        "only_keyword": "absent",
        "star_marker": "absent",
        "object_list_cardinality": "one_object",
        "parameter_assignment_form": "equals_value",
    }
    if branch == _BRANCH_RENAME:
        assignments["new_name_shape"] = "simple_name"
    elif branch == _BRANCH_OWNER_TO:
        assignments["owner_to_clause"] = "explicit_role_name"
        assignments["new_owner_shape"] = "existing_role"
    elif branch == _BRANCH_SET_PARAMETER:
        assignments["publication_parameter"] = "publish_insert_only"
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterPublicationFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_publication_factor_loop_plan(
    repository_root: Path,
) -> AlterPublicationFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_publication_factor_loop_obligations(root)
    cases: list[AlterPublicationFactorCase] = []
    delegated: list[AlterPublicationFactorObligation] = []
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
            AlterPublicationFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERPUBLICATION{ordinal:05d}",
                sql_filename=f"ALTERPUBLICATION{ordinal:05d}.sql",
                object_prefix=f"alterpublication_{ordinal:05d}_",
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
    plan = AlterPublicationFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 93 or len(plan.delegated) != 0:
        raise AlterPublicationFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 93:
        raise AlterPublicationFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 93:
        raise AlterPublicationFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_publication_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterPublicationFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterPublicationFactorObligation(
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
    if len(rows) != 93:
        raise AlterPublicationFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterPublicationFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 26, "SFV": 65, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterPublicationFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterPublicationFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 93:
        raise AlterPublicationFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterPublicationFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterPublicationFactorLoopError",
    "AlterPublicationFactorObligation",
    "AlterPublicationFactorCase",
    "AlterPublicationFactorLoopPlan",
    "compile_alter_publication_factor_loop_obligations",
    "build_alter_publication_factor_loop_plan",
    "_obligation_multiset_sha256",
]
