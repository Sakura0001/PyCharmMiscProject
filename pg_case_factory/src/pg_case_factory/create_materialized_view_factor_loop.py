"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE MATERIALIZED VIEW.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE MATERIALIZED VIEW``.  CREATE MATERIALIZED VIEW is a PostgreSQL
DDL statement with a single official synopsis branch (``branch_1``).  The
statement defines a schema relation whose kind is ``materialized_view``
(recorded in ``pg_catalog.pg_matviews`` / ``pg_class`` with
``relkind='m'``), so column/table/relation coverage is driven by the
query result shape rather than every table storage form, and there is no
``INV`` block.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no
``RISK`` obligations.

The grammar ledger is self-contained: the single synopsis action is
frozen inline.  The 47 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateMaterializedViewFactorLoopError(ValueError):
    """Raised when a frozen CREATE MATERIALIZED VIEW obligation input drifts."""


@dataclass(frozen=True)
class CreateMaterializedViewGrammarAction:
    """One official target action form of the CREATE MATERIALIZED VIEW synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateMaterializedViewFactorObligation:
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
class CreateMaterializedViewFactorCase:
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
class CreateMaterializedViewFactorLoopPlan:
    obligations: tuple[CreateMaterializedViewFactorObligation, ...]
    cases: tuple[CreateMaterializedViewFactorCase, ...]
    delegated: tuple[CreateMaterializedViewFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-creatematerializedview.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-creatematerializedview"

# The single target action used as the baseline consumer for every
# canonical factor (CREATE MATERIALIZED VIEW has one synopsis branch).
_REPRESENTATIVE_ACTION = "create_matview"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1: "create_matview",
}

# Canonical factor -> the action where the value is observable.  Every
# factor is observable on the single create_matview action; the
# statement_branch value is resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "target_object_state": _REPRESENTATIVE_ACTION,
    "query_shape": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_not_exists_clause": _REPRESENTATIVE_ACTION,
    "column_list_clause": _REPRESENTATIVE_ACTION,
    "using_clause": _REPRESENTATIVE_ACTION,
    "storage_parameter_clause": _REPRESENTATIVE_ACTION,
    "tablespace_clause": _REPRESENTATIVE_ACTION,
    "data_clause": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "column_type_coverage": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "query_source_state": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "constraint_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "exists"),
        ("target_object_state", "exists_conflict"),
        ("dependency_state", "missing_dependency"),
        ("query_source_state", "source_table_missing"),
        ("privilege_context", "insufficient_privilege"),
        ("constraint_boundary", "security_restricted_operation"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42809",
        "create_materialized_view_meta_failure_provisional",
    ),
    ("target_object_state", "exists"): (
        "42710",
        "duplicate_relation_provisional",
    ),
    ("target_object_state", "exists_conflict"): (
        "42710",
        "conflicting_existing_relation_kind_provisional",
    ),
    ("dependency_state", "missing_dependency"): (
        "42P01",
        "missing_query_dependency_provisional",
    ),
    ("query_source_state", "source_table_missing"): (
        "42P01",
        "source_table_does_not_exist_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "permission_denied_for_schema_or_tablespace_provisional",
    ),
    ("constraint_boundary", "security_restricted_operation"): (
        "0A000",
        "security_restricted_operation_not_allowed_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateMaterializedViewGrammarAction, ...]:
    """Freeze every CREATE MATERIALIZED VIEW synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_matview",
            _BRANCH_1,
            (
                "CREATE MATERIALIZED VIEW [ IF NOT EXISTS ] table_name "
                "[ (column_name [, ...] ) ] [ USING method ] "
                "[ WITH ( storage_parameter [= value] [, ... ] ) ] "
                "[ TABLESPACE tablespace_name ] AS query "
                "[ WITH [ NO ] DATA ]"
            ),
            "synopsis-create-materialized-view",
        ),
    )
    actions = [
        CreateMaterializedViewGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateMaterializedViewFactorLoopError(
            "create materialized view action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateMaterializedViewFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateMaterializedViewFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CreateMaterializedViewFactorObligation]:
    rows: list[CreateMaterializedViewFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateMaterializedViewFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CMATVIEW-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise CreateMaterializedViewFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateMaterializedViewFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_materialized_view")
    if len(catalog_rows) != 47:
        raise CreateMaterializedViewFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateMaterializedViewFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateMaterializedViewFactorObligation(
                ordinal=0,
                obligation_id=f"CMATVIEW-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _obligation_multiset_sha256(
    rows: tuple[CreateMaterializedViewFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-materialized-view-factor-obligations-v1\n"
    )
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
                    "delegated_statement_key": (
                        row.delegated_statement_key
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "create_matview": _BRANCH_1,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# boundary failure values (security_restricted_operation) and the
# concrete failure values are set only when they are the primary (or
# derived in the extension).  unscannable_state is a covered value: WITH
# NO DATA creates the matview successfully (00000); only a later scan
# would surface the unscannable error, which the DB phase verifies.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "target_action": "create_matview",
    "target_object_state": "absent",
    "query_shape": "minimal_query",
    "expected_status": "success",
    "if_not_exists_clause": "absent",
    "column_list_clause": "absent",
    "using_clause": "absent",
    "storage_parameter_clause": "absent",
    "tablespace_clause": "absent",
    "data_clause": "with_data",
    "privilege_context": "owner",
    "name_shape": "plain_identifier",
    "column_type_coverage": "representative_types",
    "dependency_state": "ready",
    "query_source_state": "source_table_exists",
    "invalid_combination": "none",
    "constraint_boundary": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive expected_status and invalid_combination from concrete values.

    The T5 ``invalid_combination`` value overlaps with the concrete
    failure factors: when the primary is a concrete failure value, the
    matching ``invalid_combination`` counterpart is derived so the
    baseline assignment stays self-consistent.  ``expected_status`` is
    recomputed from the count of concrete failure values present.
    """

    tos = a.get("target_object_state", "absent")
    ic = a.get("invalid_combination", "none")
    ds = a.get("dependency_state", "ready")
    qss = a.get("query_source_state", "source_table_exists")
    pc = a.get("privilege_context", "owner")
    cb = a.get("constraint_boundary", "none")

    # invalid_combination <-> concrete failure counterparts.
    if tos in ("exists", "exists_conflict") or ic == "object_type_mismatch":
        a["target_object_state"] = tos if tos != "absent" else "exists"
        a["invalid_combination"] = "object_type_mismatch"
    elif ds == "missing_dependency" or qss == "source_table_missing" or cb == "security_restricted_operation":
        if ic == "none":
            a["invalid_combination"] = "syntax_valid_semantic_error"

    # privilege_context insufficient_privilege is its own concrete failure.
    if pc == "insufficient_privilege" and ic == "none":
        a["invalid_combination"] = "syntax_valid_semantic_error"

    # constraint_boundary=unscannable_state is created by WITH NO DATA:
    # the matview is built successfully but left unscannable until refreshed.
    if cb == "unscannable_state":
        a["data_clause"] = "with_no_data"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateMaterializedViewFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["target_action"] = obligation.consumer_action_id
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateMaterializedViewFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateMaterializedViewFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateMaterializedViewFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_materialized_view_factor_loop_plan(
    repository_root: Path,
) -> CreateMaterializedViewFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_materialized_view_factor_loop_obligations(
        root
    )
    cases: list[CreateMaterializedViewFactorCase] = []
    delegated: list[CreateMaterializedViewFactorObligation] = []
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
            CreateMaterializedViewFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEMATERIALIZEDVIEW{ordinal:05d}",
                sql_filename=f"CREATEMATERIALIZEDVIEW{ordinal:05d}.sql",
                object_prefix=f"creatematerializedview_{ordinal:05d}_",
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
    plan = CreateMaterializedViewFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 48 or len(plan.delegated) != 0:
        raise CreateMaterializedViewFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 48:
        raise CreateMaterializedViewFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 48:
        raise CreateMaterializedViewFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_create_materialized_view_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateMaterializedViewFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateMaterializedViewFactorObligation(
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
    if len(rows) != 48:
        raise CreateMaterializedViewFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateMaterializedViewFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 47}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateMaterializedViewFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateMaterializedViewFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 48:
        raise CreateMaterializedViewFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateMaterializedViewFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateMaterializedViewFactorLoopError",
    "CreateMaterializedViewGrammarAction",
    "CreateMaterializedViewFactorObligation",
    "CreateMaterializedViewFactorCase",
    "CreateMaterializedViewFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_materialized_view_factor_loop_obligations",
    "build_create_materialized_view_factor_loop_plan",
    "_obligation_multiset_sha256",
]
