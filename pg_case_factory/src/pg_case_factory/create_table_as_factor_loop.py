"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TABLE AS.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TABLE AS`` (CTAS).  CTAS is a PostgreSQL DDL statement with one
official synopsis (``sql-createtableas.html``) whose three structural
forms (regular permanent, temporary, unlogged) are frozen as ``GRM``
target forms.

CREATE TABLE AS creates a table from a query.  The no-DB ledger prefers
a fixture source table for fuller coverage and bookend gate compliance.
The 83 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateTableAsFactorLoopError(ValueError):
    """Raised when a frozen CREATE TABLE AS obligation input drifts."""


@dataclass(frozen=True)
class CreateTableAsGrammarAction:
    """One official target action form of the CREATE TABLE AS synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTableAsFactorObligation:
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
class CreateTableAsFactorCase:
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
class CreateTableAsFactorLoopPlan:
    obligations: tuple[CreateTableAsFactorObligation, ...]
    cases: tuple[CreateTableAsFactorCase, ...]
    delegated: tuple[CreateTableAsFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createtableas.html).
_BRANCH_REGULAR = "branch_regular"
_BRANCH_TEMPORARY = "branch_temporary"
_BRANCH_UNLOGGED = "branch_unlogged"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtableas"

_REPRESENTATIVE_ACTION = "regular"

_GRAMMAR_ACTIONS: tuple[tuple[str, str, str, str], ...] = (
    (
        "regular",
        _BRANCH_REGULAR,
        "CREATE TABLE [IF NOT EXISTS] table_name [(cols)] AS query "
        "[WITH [NO] DATA]",
        "synopsis-regular",
    ),
    (
        "temporary",
        _BRANCH_TEMPORARY,
        "CREATE [GLOBAL|LOCAL] {TEMP|TEMPORARY} TABLE [IF NOT EXISTS] "
        "table_name [(cols)] [ON COMMIT ...] AS query [WITH [NO] DATA]",
        "synopsis-temporary",
    ),
    (
        "unlogged",
        _BRANCH_UNLOGGED,
        "CREATE UNLOGGED TABLE [IF NOT EXISTS] table_name [(cols)] "
        "AS query [WITH [NO] DATA]",
        "synopsis-unlogged",
    ),
)

# table_type → statement_branch derivation.
_TABLE_TYPE_TO_BRANCH = {
    "permanent": _BRANCH_REGULAR,
    "temporary_global": _BRANCH_TEMPORARY,
    "temporary_local": _BRANCH_TEMPORARY,
    "temp_short": _BRANCH_TEMPORARY,
    "unlogged": _BRANCH_UNLOGGED,
}

# statement_branch → table_type derivation.
_BRANCH_TO_TABLE_TYPE = {
    _BRANCH_REGULAR: "permanent",
    _BRANCH_TEMPORARY: "temporary_global",
    _BRANCH_UNLOGGED: "unlogged",
    "branch_regular_if_not_exists": "permanent",
    "branch_temp": "temp_short",
    "branch_temporary_if_not_exists": "temporary_global",
    "branch_unlogged_if_not_exists": "unlogged",
}

# GRM action_id (target_form value) → grammar_branch_id (statement_branch).
_ACTION_TO_BRANCH: dict[str, str] = {
    action_id: branch
    for action_id, branch, _, _ in _GRAMMAR_ACTIONS
}

# statement_branch → consumer action.
_BRANCH_CONSUMER = {
    _BRANCH_REGULAR: "regular",
    "branch_regular_if_not_exists": "regular",
    _BRANCH_TEMPORARY: "temporary",
    "branch_temp": "temporary",
    "branch_temporary_if_not_exists": "temporary",
    _BRANCH_UNLOGGED: "unlogged",
    "branch_unlogged_if_not_exists": "unlogged",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("duplicate_table_name", "without_IF_NOT_EXISTS_error"),
        ("query_error", "invalid_sql_syntax"),
        ("query_error", "references_nonexistent_table"),
        ("query_error", "aggregate_mismatch"),
        ("privilege_insufficient", "no_create_in_schema"),
        ("column_name_mismatch", "more_names_error"),
        ("on_commit_with_non_temporary", "on_commit_on_permanent_table"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P07",
        "duplicate_table_provisional",
    ),
    ("duplicate_table_name", "without_IF_NOT_EXISTS_error"): (
        "42P07",
        "duplicate_table_without_if_not_exists_provisional",
    ),
    ("query_error", "invalid_sql_syntax"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("query_error", "references_nonexistent_table"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("query_error", "aggregate_mismatch"): (
        "42803",
        "grouping_error_provisional",
    ),
    ("privilege_insufficient", "no_create_in_schema"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("column_name_mismatch", "more_names_error"): (
        "42601",
        "too_many_column_names_provisional",
    ),
    ("on_commit_with_non_temporary", "on_commit_on_permanent_table"): (
        "42601",
        "on_commit_on_permanent_table_provisional",
    ),
}

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_REGULAR,
    "object_state": "not_exists",
    "expected_status": "success",
    "table_type": "permanent",
    "if_not_exists_clause": "absent",
    "with_data": "absent_default",
    "column_names": "inherit_from_query",
    "on_commit_clause": "absent",
    "with_storage_clause": "without_storage",
    "tablespace_clause": "default",
    "table_name_shape": "simple",
    "query_shape": "simple_select",
    "column_name_list_shape": "absent",
    "column_type_derivation": "derived_from_select_expr",
    "privilege_level": "superuser",
    "source_table_dependency": "source_table_exists",
    "schema_dependency": "schema_exists",
    "tablespace_dependency": "default_tablespace",
    "duplicate_table_name": "none",
    "query_error": "none",
    "privilege_insufficient": "none",
    "column_name_mismatch": "none",
    "on_commit_with_non_temporary": "none",
    "empty_query_result": "none",
    "verification_mode": "pg_class_catalog_query",
    "cleanup_mode": "DROP_TABLE",
}

# query_shape → column_type_derivation derivation.
_QUERY_TO_DERIVATION = {
    "simple_select": "derived_from_select_expr",
    "table_command": "derived_from_table_command",
    "values_command": "derived_from_values",
    "execute_prepared": "derived_from_execute",
    "aggregate_query": "derived_from_select_expr",
    "join_query": "derived_from_select_expr",
    "union_query": "derived_from_select_expr",
    "subquery": "derived_from_select_expr",
}


def _canonical_consumer(row) -> str:
    """Resolve the consumer action for an SFV catalog row."""

    if row.factor == "statement_branch":
        return _BRANCH_CONSUMER.get(row.value, _REPRESENTATIVE_ACTION)
    if row.factor == "table_type":
        branch = _TABLE_TYPE_TO_BRANCH.get(row.value, _BRANCH_REGULAR)
        return _BRANCH_CONSUMER.get(branch, _REPRESENTATIVE_ACTION)
    return _REPRESENTATIVE_ACTION


def _load_grammar_actions() -> tuple[CreateTableAsGrammarAction, ...]:
    """Freeze every CREATE TABLE AS synopsis target action."""

    actions = [
        CreateTableAsGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in _GRAMMAR_ACTIONS
    ]
    if len(actions) != 3:
        raise CreateTableAsFactorLoopError("action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateTableAsFactorObligation]:
    rows: list[CreateTableAsFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTableAsFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CTAS-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_form|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_form",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 3:
        raise CreateTableAsFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTableAsFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_table_as")
    if len(catalog_rows) != 83:
        raise CreateTableAsFactorLoopError("canonical obligation count drift")
    rows: list[CreateTableAsFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTableAsFactorObligation(
                ordinal=0,
                obligation_id=f"CTAS-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateTableAsFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-table-as-factor-obligations-v1\n")
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


def _is_temporary(table_type: str) -> bool:
    return table_type in (
        "temporary_global", "temporary_local", "temp_short",
    )


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping T1/T2 factors and expected_status."""

    # table_type ↔ statement_branch
    table_type = a.get("table_type", "permanent")
    branch = a.get("statement_branch", _BRANCH_REGULAR)
    if table_type in _TABLE_TYPE_TO_BRANCH:
        derived_branch = _TABLE_TYPE_TO_BRANCH[table_type]
        if a.get("statement_branch") == _BASELINE_DEFAULTS["statement_branch"]:
            a["statement_branch"] = derived_branch
            branch = derived_branch
    if branch in _BRANCH_TO_TABLE_TYPE:
        derived_tt = _BRANCH_TO_TABLE_TYPE[branch]
        if a.get("table_type") == _BASELINE_DEFAULTS["table_type"]:
            a["table_type"] = derived_tt
            table_type = derived_tt

    # statement_branch with _if_not_exists → if_not_exists_clause=present
    if "_if_not_exists" in branch:
        if a.get("if_not_exists_clause") == _BASELINE_DEFAULTS["if_not_exists_clause"]:
            a["if_not_exists_clause"] = "present"

    # if_not_exists_clause=present → statement_branch gets _if_not_exists
    if a.get("if_not_exists_clause") == "present" and "_if_not_exists" not in branch:
        if a.get("statement_branch") == _BASELINE_DEFAULTS["statement_branch"]:
            if table_type == "unlogged":
                a["statement_branch"] = "branch_unlogged_if_not_exists"
            elif _is_temporary(table_type):
                a["statement_branch"] = "branch_temporary_if_not_exists"
            else:
                a["statement_branch"] = "branch_regular_if_not_exists"
            branch = a["statement_branch"]

    # query_shape ↔ column_type_derivation
    qs = a.get("query_shape", "simple_select")
    if qs in _QUERY_TO_DERIVATION:
        if a.get("column_type_derivation") == _BASELINE_DEFAULTS["column_type_derivation"]:
            a["column_type_derivation"] = _QUERY_TO_DERIVATION[qs]

    # column_names=explicit_list → column_name_list_shape relevant
    if a.get("column_names") == "explicit_list":
        if a.get("column_name_list_shape") == _BASELINE_DEFAULTS["column_name_list_shape"]:
            a["column_name_list_shape"] = "matching_query_columns"

    # column_names=inherit_from_query → column_name_list_shape=absent
    if a.get("column_names") == "inherit_from_query":
        a["column_name_list_shape"] = "absent"

    # T5 failure derivations → T1 counterparts
    # expected_status=failure → duplicate table scenario
    if a.get("expected_status") == "failure":
        if _count_baseline_failures(a) == 0:
            a["object_state"] = "already_exists"
            a["if_not_exists_clause"] = "absent"

    # duplicate_table_name=without_IF_NOT_EXISTS_error → already_exists + absent
    if a.get("duplicate_table_name") == "without_IF_NOT_EXISTS_error":
        a["object_state"] = "already_exists"
        a["if_not_exists_clause"] = "absent"
        a["statement_branch"] = _BRANCH_REGULAR
        branch = _BRANCH_REGULAR

    # duplicate_table_name=with_IF_NOT_EXISTS_noop → already_exists + present
    if a.get("duplicate_table_name") == "with_IF_NOT_EXISTS_noop":
        a["object_state"] = "already_exists"
        a["if_not_exists_clause"] = "present"

    # query_error=references_nonexistent_table → source not exists
    if a.get("query_error") == "references_nonexistent_table":
        a["source_table_dependency"] = "source_table_not_exists"

    # query_error=invalid_sql_syntax → execute_prepared (invalid in CTAS)
    if a.get("query_error") == "invalid_sql_syntax":
        a["query_shape"] = "execute_prepared"
        a["column_type_derivation"] = "derived_from_execute"

    # query_error=aggregate_mismatch → aggregate_query with column mismatch
    if a.get("query_error") == "aggregate_mismatch":
        a["query_shape"] = "aggregate_query"
        a["column_names"] = "explicit_list"
        a["column_name_list_shape"] = "more_than_query_columns"

    # privilege_insufficient → non_owner_no_privilege
    if a.get("privilege_insufficient") == "no_create_in_schema":
        a["privilege_level"] = "non_owner_no_privilege"

    # column_name_mismatch=more_names_error → more_than_query_columns
    if a.get("column_name_mismatch") == "more_names_error":
        a["column_name_list_shape"] = "more_than_query_columns"
        a["column_names"] = "explicit_list"

    # column_name_mismatch=fewer_names_extra_columns_kept
    if a.get("column_name_mismatch") == "fewer_names_extra_columns_kept":
        a["column_name_list_shape"] = "fewer_than_query_columns"
        a["column_names"] = "explicit_list"

    # on_commit_with_non_temporary → on_commit on permanent table
    if a.get("on_commit_with_non_temporary") == "on_commit_on_permanent_table":
        if a.get("on_commit_clause") == _BASELINE_DEFAULTS["on_commit_clause"]:
            a["on_commit_clause"] = "DROP"
        a["table_type"] = "permanent"
        a["statement_branch"] = _BRANCH_REGULAR
        branch = _BRANCH_REGULAR

    # empty_query_result → with_data or no_data
    if a.get("empty_query_result") == "with_no_data_structure_only":
        a["with_data"] = "WITH_NO_DATA"
    elif a.get("empty_query_result") == "with_data_empty_table":
        a["with_data"] = "WITH_DATA"

    # schema_dependency=pg_catalog_reserved → reserved schema
    if a.get("schema_dependency") == "pg_catalog_reserved":
        a["table_name_shape"] = "schema_qualified"

    # schema_dependency=schema_not_exists → schema doesn't exist
    if a.get("schema_dependency") == "schema_not_exists":
        a["table_name_shape"] = "schema_qualified"

    # tablespace_dependency=specified_tablespace_not_exists → not exists
    if a.get("tablespace_dependency") == "specified_tablespace_not_exists":
        a["tablespace_clause"] = "specified"

    # tablespace_dependency=specified_tablespace_exists → specified
    if a.get("tablespace_dependency") == "specified_tablespace_exists":
        a["tablespace_clause"] = "specified"

    # source_table_dependency=source_table_not_exists → references_nonexistent
    if a.get("source_table_dependency") == "source_table_not_exists":
        if a.get("query_error") == _BASELINE_DEFAULTS["query_error"]:
            pass  # query_error stays at default; the failure is detected by render

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateTableAsFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    if obligation.kind == "GRM":
        branch = _ACTION_TO_BRANCH.get(
            obligation.value, obligation.value
        )
        assignments["statement_branch"] = branch
        if branch in _BRANCH_TO_TABLE_TYPE:
            assignments["table_type"] = _BRANCH_TO_TABLE_TYPE[branch]
    else:
        assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateTableAsFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTableAsFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateTableAsFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_table_as_factor_loop_plan(
    repository_root: Path,
) -> CreateTableAsFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_table_as_factor_loop_obligations(root)
    cases: list[CreateTableAsFactorCase] = []
    delegated: list[CreateTableAsFactorObligation] = []
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
            CreateTableAsFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETABLEAS{ordinal:05d}",
                sql_filename=f"CREATETABLEAS{ordinal:05d}.sql",
                object_prefix=f"createtableas_{ordinal:05d}_",
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
    plan = CreateTableAsFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 86 or len(plan.delegated) != 0:
        raise CreateTableAsFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 86:
        raise CreateTableAsFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 86:
        raise CreateTableAsFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_table_as_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTableAsFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTableAsFactorObligation(
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
    if len(rows) != 86:
        raise CreateTableAsFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTableAsFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 3, "SFV": 83}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTableAsFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTableAsFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 86:
        raise CreateTableAsFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateTableAsFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateTableAsFactorLoopError",
    "CreateTableAsGrammarAction",
    "CreateTableAsFactorObligation",
    "CreateTableAsFactorCase",
    "CreateTableAsFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "_BRANCH_TO_TABLE_TYPE",
    "_TABLE_TYPE_TO_BRANCH",
    "_ACTION_TO_BRANCH",
    "_QUERY_TO_DERIVATION",
    "compile_create_table_as_factor_loop_obligations",
    "build_create_table_as_factor_loop_plan",
    "_obligation_multiset_sha256",
]
