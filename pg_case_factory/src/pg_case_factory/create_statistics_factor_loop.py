"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE STATISTICS.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE STATISTICS``.  CREATE STATISTICS is a PostgreSQL DDL statement
with one official synopsis (``sql-createstatistics.html``) whose two
canonical statement-branch forms (univariate expression statistics and
multivariate column/expression statistics) are frozen as ``GRM`` target
forms.

CREATE STATISTICS references a table via ``FROM table_reference``.  The
no-DB ledger prefers a fixture table for fuller coverage and bookend
gate compliance.  The 54 canonical ``SFV`` rows are loaded from the
shipped applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateStatisticsFactorLoopError(ValueError):
    """Raised when a frozen CREATE STATISTICS obligation input drifts."""


@dataclass(frozen=True)
class CreateStatisticsGrammarAction:
    """One official target action form of the CREATE STATISTICS synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateStatisticsFactorObligation:
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
class CreateStatisticsFactorCase:
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
class CreateStatisticsFactorLoopPlan:
    obligations: tuple[CreateStatisticsFactorObligation, ...]
    cases: tuple[CreateStatisticsFactorCase, ...]
    delegated: tuple[CreateStatisticsFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createstatistics.html).
_BRANCH_UNIVARIATE = "branch_univariate_expression"
_BRANCH_MULTIVARIATE = "branch_multivariate_columns"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createstatistics"

_REPRESENTATIVE_ACTION = "branch_multivariate_columns"

_GRM_ACTIONS: tuple[tuple[str, str, str, str], ...] = (
    (
        "branch_univariate_expression",
        _BRANCH_UNIVARIATE,
        "CREATE STATISTICS [ [ IF NOT EXISTS ] statistics_name ] "
        "ON ( expression ) FROM table_name",
        "synopsis-univariate-expression",
    ),
    (
        "branch_multivariate_columns",
        _BRANCH_MULTIVARIATE,
        "CREATE STATISTICS [ [ IF NOT EXISTS ] statistics_name ] "
        "[ ( statistics_kind [, ...] ) ] "
        "ON { column_name | ( expression ) }, ... FROM table_name",
        "synopsis-multivariate-columns",
    ),
)


def _load_grammar_actions() -> tuple[CreateStatisticsGrammarAction, ...]:
    """Freeze every CREATE STATISTICS synopsis target action."""

    actions = [
        CreateStatisticsGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in _GRM_ACTIONS
    ]
    if len(actions) != 2:
        raise CreateStatisticsFactorLoopError("action count drift")
    return tuple(actions)


# Canonical (factor, value) pairs that reach a PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("statistics_identity", "exists"),
        ("duplicate_statistics_name", "same_name_exists"),
        ("table_dependency", "table_not_exists"),
        ("table_name_shape", "nonexistent_table"),
        ("nonexistent_table", "table_not_exists_failure"),
        ("column_dependency", "column_not_exists"),
        ("column_name_shape", "nonexistent_column"),
        ("nonexistent_column", "column_not_exists_failure"),
        ("executor_privilege", "non_owner_no_privilege"),
        ("privilege_insufficient", "non_table_owner_creating_statistics"),
        (
            "single_column_for_multivariate",
            "single_column_multivariate_failure",
        ),
        ("expression_syntax_error", "invalid_expression_failure"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_statistics_provisional",
    ),
    ("statistics_identity", "exists"): (
        "42710",
        "duplicate_statistics_provisional",
    ),
    ("duplicate_statistics_name", "same_name_exists"): (
        "42710",
        "duplicate_statistics_provisional",
    ),
    ("table_dependency", "table_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("table_name_shape", "nonexistent_table"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("nonexistent_table", "table_not_exists_failure"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("column_dependency", "column_not_exists"): (
        "42703",
        "undefined_column_provisional",
    ),
    ("column_name_shape", "nonexistent_column"): (
        "42703",
        "undefined_column_provisional",
    ),
    ("nonexistent_column", "column_not_exists_failure"): (
        "42703",
        "undefined_column_provisional",
    ),
    ("executor_privilege", "non_owner_no_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_table_owner_creating_statistics"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    (
        "single_column_for_multivariate",
        "single_column_multivariate_failure",
    ): ("42P16", "single_column_multivariate_provisional"),
    ("expression_syntax_error", "invalid_expression_failure"): (
        "42601",
        "syntax_error_provisional",
    ),
}


def _compile_grammar_obligations() -> list[CreateStatisticsFactorObligation]:
    rows: list[CreateStatisticsFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateStatisticsFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CSTAT-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 2:
        raise CreateStatisticsFactorLoopError("grammar obligation count drift")
    return rows


# factor -> {value: consumer_action_id}
_CONSUMER_MAP: dict[str, dict[str, str]] = {
    "statement_branch": {
        "branch_multivariate_columns": "branch_multivariate_columns",
        "branch_univariate_expression": "branch_univariate_expression",
    },
    "statistics_identity": {
        "not_exists": "branch_multivariate_columns",
        "exists": "duplicate_statistics",
        "exists_with_if_not_exists": "branch_multivariate_columns",
        "reserved_word_name": "branch_multivariate_columns",
    },
    "expected_status": {
        "success": "branch_multivariate_columns",
        "failure": "duplicate_statistics",
    },
    "statistics_kind_clause": {
        "omitted_all_kinds": "branch_multivariate_columns",
        "ndistinct_only": "branch_multivariate_columns",
        "dependencies_only": "branch_multivariate_columns",
        "mcv_only": "branch_multivariate_columns",
        "ndistinct_and_dependencies": "branch_multivariate_columns",
        "all_three_kinds": "branch_multivariate_columns",
    },
    "column_combination": {
        "two_columns": "branch_multivariate_columns",
        "three_columns": "branch_multivariate_columns",
        "column_and_expression_mix": "branch_multivariate_columns",
        "single_expression_univariate": "branch_univariate_expression",
    },
    "if_not_exists_clause": {
        "without_if_not_exists": "branch_multivariate_columns",
        "with_if_not_exists": "branch_multivariate_columns",
    },
    "expression_shape": {
        "simple_column_reference": "branch_multivariate_columns",
        "arithmetic_expression": "branch_multivariate_columns",
        "function_call_expression": "branch_multivariate_columns",
    },
    "statistics_name_presence": {
        "explicit_name": "branch_multivariate_columns",
        "auto_generated_name_omitted": "branch_multivariate_columns",
    },
    "statistics_name_shape": {
        "simple_name": "branch_multivariate_columns",
        "schema_qualified_name": "branch_multivariate_columns",
        "quoted_name": "branch_multivariate_columns",
        "reserved_word_name": "branch_multivariate_columns",
        "non_existing_name": "branch_multivariate_columns",
    },
    "table_name_shape": {
        "simple_name": "branch_multivariate_columns",
        "schema_qualified_name": "branch_multivariate_columns",
        "quoted_name": "branch_multivariate_columns",
        "nonexistent_table": "nonexistent_table",
    },
    "column_name_shape": {
        "simple_name": "branch_multivariate_columns",
        "quoted_name": "branch_multivariate_columns",
        "nonexistent_column": "nonexistent_column",
    },
    "executor_privilege": {
        "superuser": "branch_multivariate_columns",
        "table_owner": "branch_multivariate_columns",
        "non_owner_no_privilege": "privilege_insufficient",
    },
    "table_dependency": {
        "table_exists": "branch_multivariate_columns",
        "table_not_exists": "nonexistent_table",
    },
    "column_dependency": {
        "column_exists": "branch_multivariate_columns",
        "column_not_exists": "nonexistent_column",
    },
    "duplicate_statistics_name": {
        "none": "branch_multivariate_columns",
        "same_name_exists": "duplicate_statistics",
    },
    "privilege_insufficient": {
        "non_table_owner_creating_statistics": "privilege_insufficient",
    },
    "nonexistent_table": {
        "table_not_exists_failure": "nonexistent_table",
    },
    "nonexistent_column": {
        "column_not_exists_failure": "nonexistent_column",
    },
    "single_column_for_multivariate": {
        "single_column_multivariate_failure": "single_column_multivariate",
    },
    "expression_syntax_error": {
        "invalid_expression_failure": "expression_syntax_error",
    },
    "verification_mode": {
        "pg_statistic_ext_catalog": "branch_multivariate_columns",
        "error_assertion": "branch_multivariate_columns",
    },
    "cleanup_mode": {
        "drop_statistics": "branch_multivariate_columns",
    },
}


def _canonical_consumer(row) -> str:
    mapping = _CONSUMER_MAP.get(row.factor)
    if mapping is None:
        raise CreateStatisticsFactorLoopError(
            f"unknown factor key: {row.factor}"
        )
    consumer = mapping.get(row.value)
    if consumer is None:
        raise CreateStatisticsFactorLoopError(
            f"unknown {row.factor} value: {row.value}"
        )
    return consumer


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateStatisticsFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_statistics")
    if len(catalog_rows) != 54:
        raise CreateStatisticsFactorLoopError("canonical obligation count drift")
    rows: list[CreateStatisticsFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateStatisticsFactorObligation(
                ordinal=0,
                obligation_id=f"CSTAT-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateStatisticsFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-statistics-factor-obligations-v1\n"
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


# Sentinel default for single-value failure factors (not in the TSV).
_NONE = "none"

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_multivariate_columns",
    "statistics_identity": "not_exists",
    "expected_status": "success",
    "statistics_kind_clause": "omitted_all_kinds",
    "column_combination": "two_columns",
    "if_not_exists_clause": "without_if_not_exists",
    "expression_shape": "simple_column_reference",
    "statistics_name_presence": "explicit_name",
    "statistics_name_shape": "simple_name",
    "table_name_shape": "simple_name",
    "column_name_shape": "simple_name",
    "executor_privilege": "table_owner",
    "table_dependency": "table_exists",
    "column_dependency": "column_exists",
    "duplicate_statistics_name": _NONE,
    "privilege_insufficient": _NONE,
    "nonexistent_table": _NONE,
    "nonexistent_column": _NONE,
    "single_column_for_multivariate": _NONE,
    "expression_syntax_error": _NONE,
    "verification_mode": "pg_statistic_ext_catalog",
    "cleanup_mode": "drop_statistics",
}


def _is_duplicate_failure(a: dict[str, str]) -> bool:
    if a.get("if_not_exists_clause") == "with_if_not_exists":
        return False
    if a.get("expected_status") == "failure":
        return True
    if a.get("statistics_identity") == "exists":
        return True
    if a.get("duplicate_statistics_name") == "same_name_exists":
        return True
    return False


def _is_nonexistent_table(a: dict[str, str]) -> bool:
    if a.get("table_dependency") == "table_not_exists":
        return True
    if a.get("table_name_shape") == "nonexistent_table":
        return True
    if a.get("nonexistent_table") == "table_not_exists_failure":
        return True
    return False


def _is_nonexistent_column(a: dict[str, str]) -> bool:
    if a.get("column_dependency") == "column_not_exists":
        return True
    if a.get("column_name_shape") == "nonexistent_column":
        return True
    if a.get("nonexistent_column") == "column_not_exists_failure":
        return True
    return False


def _is_privilege_insufficient(a: dict[str, str]) -> bool:
    if a.get("executor_privilege") == "non_owner_no_privilege":
        return True
    if a.get("privilege_insufficient") == "non_table_owner_creating_statistics":
        return True
    return False


def _is_single_column_multivariate(a: dict[str, str]) -> bool:
    return a.get("single_column_for_multivariate") == (
        "single_column_multivariate_failure"
    )


def _is_expression_syntax_error(a: dict[str, str]) -> bool:
    return a.get("expression_syntax_error") == "invalid_expression_failure"


_FAILURE_CONDITIONS = (
    _is_duplicate_failure,
    _is_nonexistent_table,
    _is_nonexistent_column,
    _is_privilege_insufficient,
    _is_single_column_multivariate,
    _is_expression_syntax_error,
)


def _count_failures(a: dict[str, str]) -> int:
    return sum(1 for cond in _FAILURE_CONDITIONS if cond(a))


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping factors so the baseline assignment is consistent."""

    # column_combination drives statement_branch (Form 1 vs Form 2).
    combo = a.get("column_combination", "two_columns")
    if combo == "single_expression_univariate":
        a["statement_branch"] = "branch_univariate_expression"
        a["statistics_kind_clause"] = "omitted_all_kinds"
    else:
        a["statement_branch"] = "branch_multivariate_columns"

    # Univariate Form 1 has no statistics_kind clause.
    if a.get("statement_branch") == "branch_univariate_expression":
        a["statistics_kind_clause"] = "omitted_all_kinds"

    # IF NOT EXISTS requires an explicit statistics name.
    if a.get("if_not_exists_clause") == "with_if_not_exists":
        a["statistics_name_presence"] = "explicit_name"

    # statistics_identity drives duplicate/name-shape overlaps.
    ident = a.get("statistics_identity", "not_exists")
    if ident == "exists":
        a["duplicate_statistics_name"] = "same_name_exists"
        a["if_not_exists_clause"] = "without_if_not_exists"
    elif ident == "exists_with_if_not_exists":
        a["duplicate_statistics_name"] = "same_name_exists"
        a["if_not_exists_clause"] = "with_if_not_exists"
        a["statistics_name_presence"] = "explicit_name"
    elif ident == "reserved_word_name":
        a["statistics_name_shape"] = "reserved_word_name"
        a["duplicate_statistics_name"] = _NONE
    else:
        a.setdefault("duplicate_statistics_name", _NONE)

    # duplicate_statistics_name=same_name_exists implies identity=exists.
    if a.get("duplicate_statistics_name") == "same_name_exists":
        if ident == "not_exists":
            a["statistics_identity"] = "exists"

    # expected_status=failure sets up a duplicate scenario.
    if a.get("expected_status") == "failure":
        a["statistics_identity"] = "exists"
        a["duplicate_statistics_name"] = "same_name_exists"
        a["if_not_exists_clause"] = "without_if_not_exists"

    # T5 dependency failures derive T4/T3 counterparts.
    if a.get("nonexistent_table") == "table_not_exists_failure":
        a["table_dependency"] = "table_not_exists"
        a["table_name_shape"] = "nonexistent_table"
    if a.get("nonexistent_column") == "column_not_exists_failure":
        a["column_dependency"] = "column_not_exists"
        a["column_name_shape"] = "nonexistent_column"
    if a.get("privilege_insufficient") == "non_table_owner_creating_statistics":
        a["executor_privilege"] = "non_owner_no_privilege"

    # T4 failures derive T3 counterparts.
    if a.get("table_dependency") == "table_not_exists":
        a["table_name_shape"] = "nonexistent_table"
    if a.get("column_dependency") == "column_not_exists":
        a["column_name_shape"] = "nonexistent_column"
    if a.get("executor_privilege") == "non_owner_no_privilege":
        a["privilege_insufficient"] = "non_table_owner_creating_statistics"

    failures = _count_failures(a)
    a["expected_status"] = "failure" if failures else "success"


def _baseline_assignments(
    obligation: CreateStatisticsFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    if obligation.kind == "GRM":
        assignments["statement_branch"] = obligation.value
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise CreateStatisticsFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateStatisticsFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateStatisticsFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_statistics_factor_loop_plan(
    repository_root: Path,
) -> CreateStatisticsFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_statistics_factor_loop_obligations(root)
    cases: list[CreateStatisticsFactorCase] = []
    delegated: list[CreateStatisticsFactorObligation] = []
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
            CreateStatisticsFactorCase(
                ordinal=ordinal,
                case_id=f"CREATESTATISTICS{ordinal:05d}",
                sql_filename=f"CREATESTATISTICS{ordinal:05d}.sql",
                object_prefix=f"createstatistics_{ordinal:05d}_",
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
    plan = CreateStatisticsFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 56 or len(plan.delegated) != 0:
        raise CreateStatisticsFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 56:
        raise CreateStatisticsFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 56:
        raise CreateStatisticsFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_statistics_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateStatisticsFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateStatisticsFactorObligation(
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
    if len(rows) != 56:
        raise CreateStatisticsFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateStatisticsFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 54}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateStatisticsFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateStatisticsFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 56:
        raise CreateStatisticsFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateStatisticsFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateStatisticsFactorLoopError",
    "CreateStatisticsGrammarAction",
    "CreateStatisticsFactorObligation",
    "CreateStatisticsFactorCase",
    "CreateStatisticsFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "_FAILURE_CONDITIONS",
    "compile_create_statistics_factor_loop_obligations",
    "build_create_statistics_factor_loop_plan",
    "_obligation_multiset_sha256",
]
