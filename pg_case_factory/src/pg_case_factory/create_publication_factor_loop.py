"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE PUBLICATION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE PUBLICATION``.  CREATE PUBLICATION is a PostgreSQL logical-replication
DDL statement with 4 official synopsis branches: ``FOR ALL TABLES``,
``FOR TABLE``, ``FOR TABLES IN SCHEMA``, and the no-FOR form
(``CREATE PUBLICATION name``).  Each branch is tracked as a separate grammar
target form.

The statement touches the ``pg_catalog.pg_publication`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.  CREATE PUBLICATION does
not create tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.

Each local obligation becomes exactly one regress program.  The 68
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreatePublicationFactorLoopError(ValueError):
    """Raised when a frozen CREATE PUBLICATION obligation input drifts."""


@dataclass(frozen=True)
class CreatePublicationGrammarAction:
    """One official target action form of the CREATE PUBLICATION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreatePublicationFactorObligation:
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
class CreatePublicationFactorCase:
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
class CreatePublicationFactorLoopPlan:
    obligations: tuple[CreatePublicationFactorObligation, ...]
    cases: tuple[CreatePublicationFactorCase, ...]
    delegated: tuple[CreatePublicationFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createpublication.html).
_BRANCH_FOR_ALL_TABLES = "branch_for_all_tables"
_BRANCH_FOR_TABLE = "branch_for_table"
_BRANCH_FOR_TABLES_IN_SCHEMA = "branch_for_tables_in_schema"
_BRANCH_NO_FOR = "branch_no_for"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createpublication"

# A representative for_all_tables action used as the baseline consumer
# for canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "for_all_tables"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_FOR_ALL_TABLES: "for_all_tables",
    _BRANCH_FOR_TABLE: "for_table",
    _BRANCH_FOR_TABLES_IN_SCHEMA: "for_tables_in_schema",
    _BRANCH_NO_FOR: "no_for",
}

# for_clause_shape canonical value -> target action.
_FOR_CLAUSE_SHAPE_CONSUMER = {
    "for_all_tables": "for_all_tables",
    "for_table_single": "for_table",
    "for_table_multiple": "for_table",
    "for_tables_in_schema": "for_tables_in_schema",
    "for_tables_in_schema_current_schema": "for_tables_in_schema",
    "for_mixed_table_and_schema": "for_table",
    "no_for_clause": "no_for",
}

# Factors that are only meaningful in the FOR TABLE branch.
_FOR_TABLE_FACTORS = frozenset(
    {"column_filter", "where_clause", "only_keyword", "table_name_shape",
     "column_name_shape", "table_dependency"}
)

# Factors that are only meaningful in the FOR TABLES IN SCHEMA branch.
_FOR_SCHEMA_FACTORS = frozenset(
    {"schema_name_shape", "schema_dependency"}
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreatePublicationFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "for_clause_shape":
        try:
            return _FOR_CLAUSE_SHAPE_CONSUMER[row.value]
        except KeyError as exc:
            raise CreatePublicationFactorLoopError(
                f"unknown for_clause_shape value: {row.value}"
            ) from exc
    if row.factor in _FOR_TABLE_FACTORS:
        return "for_table"
    if row.factor in _FOR_SCHEMA_FACTORS:
        return "for_tables_in_schema"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("publication_identity", "exists"),
        ("publication_identity", "quoted_duplicate"),
        ("table_dependency", "table_not_exists"),
        ("schema_dependency", "schema_not_exists"),
        ("executor_privilege", "non_superuser"),
        ("table_name_shape", "nonexistent_table"),
        ("schema_name_shape", "nonexistent_schema"),
        ("column_name_shape", "nonexistent_column"),
        ("duplicate_publication_name", "same_name_exists"),
        ("privilege_insufficient", "non_superuser_creating_publication"),
        ("nonexistent_table", "table_not_exists_failure"),
        ("nonexistent_schema", "schema_not_exists_failure"),
        ("conflicting_for_clause", "for_all_tables_with_for_table_conflict"),
        ("invalid_where_expression", "non_boolean_expression"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_publication_provisional",
    ),
    ("publication_identity", "exists"): (
        "42710",
        "duplicate_publication_provisional",
    ),
    ("publication_identity", "quoted_duplicate"): (
        "42710",
        "duplicate_publication_provisional",
    ),
    ("duplicate_publication_name", "same_name_exists"): (
        "42710",
        "duplicate_publication_provisional",
    ),
    ("executor_privilege", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_superuser_creating_publication"): (
        "42501",
        "insufficient_privilege_provisional",
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
    ("schema_dependency", "schema_not_exists"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("schema_name_shape", "nonexistent_schema"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("nonexistent_schema", "schema_not_exists_failure"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("column_name_shape", "nonexistent_column"): (
        "42703",
        "undefined_column_provisional",
    ),
    ("conflicting_for_clause", "for_all_tables_with_for_table_conflict"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("invalid_where_expression", "non_boolean_expression"): (
        "42804",
        "non_boolean_where_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreatePublicationGrammarAction, ...]
):
    """Freeze every CREATE PUBLICATION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "for_all_tables",
            _BRANCH_FOR_ALL_TABLES,
            "CREATE PUBLICATION name FOR ALL TABLES",
            "synopsis-for-all-tables",
        ),
        (
            "for_table",
            _BRANCH_FOR_TABLE,
            "CREATE PUBLICATION name FOR TABLE table_and_columns [, ...]",
            "synopsis-for-table",
        ),
        (
            "for_tables_in_schema",
            _BRANCH_FOR_TABLES_IN_SCHEMA,
            "CREATE PUBLICATION name FOR TABLES IN SCHEMA schema_name [, ...]",
            "synopsis-for-tables-in-schema",
        ),
        (
            "no_for",
            _BRANCH_NO_FOR,
            "CREATE PUBLICATION name",
            "synopsis-no-for",
        ),
    )
    actions = [
        CreatePublicationGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 4:
        raise CreatePublicationFactorLoopError(
            "create publication action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreatePublicationFactorObligation]
):
    rows: list[CreatePublicationFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreatePublicationFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CPUB-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 4:
        raise CreatePublicationFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreatePublicationFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_publication")
    if len(catalog_rows) != 68:
        raise CreatePublicationFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreatePublicationFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreatePublicationFactorObligation(
                ordinal=0,
                obligation_id=f"CPUB-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreatePublicationFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-publication-factor-obligations-v1\n"
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


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "for_all_tables": _BRANCH_FOR_ALL_TABLES,
    "for_table": _BRANCH_FOR_TABLE,
    "for_tables_in_schema": _BRANCH_FOR_TABLES_IN_SCHEMA,
    "no_for": _BRANCH_NO_FOR,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors are derived in :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_FOR_ALL_TABLES,
    "publication_identity": "not_exists",
    "expected_status": "success",
    "for_clause_shape": "for_all_tables",
    "with_parameter_clause": "omitted",
    "column_filter": "no_column_filter",
    "where_clause": "no_where",
    "only_keyword": "without_only",
    "publication_name_shape": "simple_name",
    "table_name_shape": "simple_name",
    "schema_name_shape": "simple_name",
    "column_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "table_dependency": "table_exists",
    "schema_dependency": "schema_exists",
    "duplicate_publication_name": "none",
    "privilege_insufficient": "none",
    "nonexistent_table": "none",
    "nonexistent_schema": "none",
    "conflicting_for_clause": "none",
    "invalid_where_expression": "none",
    "verification_mode": "pg_publication_catalog",
    "cleanup_mode": "drop_publication",
}

_FOR_CLAUSE_TO_BRANCH = {
    "for_all_tables": _BRANCH_FOR_ALL_TABLES,
    "for_table_single": _BRANCH_FOR_TABLE,
    "for_table_multiple": _BRANCH_FOR_TABLE,
    "for_tables_in_schema": _BRANCH_FOR_TABLES_IN_SCHEMA,
    "for_tables_in_schema_current_schema": _BRANCH_FOR_TABLES_IN_SCHEMA,
    "for_mixed_table_and_schema": _BRANCH_FOR_TABLE,
    "no_for_clause": _BRANCH_NO_FOR,
}

_BRANCH_TO_FOR_CLAUSE = {
    _BRANCH_FOR_ALL_TABLES: "for_all_tables",
    _BRANCH_FOR_TABLE: "for_table_single",
    _BRANCH_FOR_TABLES_IN_SCHEMA: "for_tables_in_schema",
    _BRANCH_NO_FOR: "no_for_clause",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # --- statement_branch <-> for_clause_shape consistency -------------
    fcs = a.get("for_clause_shape", "for_all_tables")
    if fcs in _FOR_CLAUSE_TO_BRANCH:
        a["statement_branch"] = _FOR_CLAUSE_TO_BRANCH[fcs]
    else:
        sb = a.get("statement_branch", _BRANCH_FOR_ALL_TABLES)
        a["for_clause_shape"] = _BRANCH_TO_FOR_CLAUSE.get(
            sb, "for_all_tables"
        )

    # --- T5 -> T1-T4 derivation (when T5 is the primary, set T1-T4) -----
    dpn = a.get("duplicate_publication_name", "")
    if dpn == "same_name_exists":
        a["publication_identity"] = "exists"

    pi_val = a.get("privilege_insufficient", "")
    if pi_val == "non_superuser_creating_publication":
        a["executor_privilege"] = "non_superuser"

    nt = a.get("nonexistent_table", "")
    if nt == "table_not_exists_failure":
        a["table_dependency"] = "table_not_exists"
        a["table_name_shape"] = "nonexistent_table"

    ns = a.get("nonexistent_schema", "")
    if ns == "schema_not_exists_failure":
        a["schema_dependency"] = "schema_not_exists"
        a["schema_name_shape"] = "nonexistent_schema"

    # --- T1-T4 -> T5 derivation ----------------------------------------
    pi = a.get("publication_identity", "not_exists")
    if pi in ("exists", "quoted_duplicate"):
        a["duplicate_publication_name"] = "same_name_exists"

    ep = a.get("executor_privilege", "superuser")
    if ep == "non_superuser":
        a["privilege_insufficient"] = "non_superuser_creating_publication"

    td = a.get("table_dependency", "table_exists")
    if td == "table_not_exists":
        a["nonexistent_table"] = "table_not_exists_failure"
        a["table_name_shape"] = "nonexistent_table"

    sd = a.get("schema_dependency", "schema_exists")
    if sd == "schema_not_exists":
        a["nonexistent_schema"] = "schema_not_exists_failure"
        a["schema_name_shape"] = "nonexistent_schema"

    tns = a.get("table_name_shape", "simple_name")
    if tns == "nonexistent_table":
        a["table_dependency"] = "table_not_exists"
        a["nonexistent_table"] = "table_not_exists_failure"

    sns = a.get("schema_name_shape", "simple_name")
    if sns == "nonexistent_schema":
        a["schema_dependency"] = "schema_not_exists"
        a["nonexistent_schema"] = "schema_not_exists_failure"

    cns = a.get("column_name_shape", "simple_name")
    if cns == "nonexistent_column":
        a["column_filter"] = "single_column_filter"

    # --- publication_identity=quoted_duplicate -> name shape -----------
    pi = a.get("publication_identity", "not_exists")
    if pi == "quoted_duplicate":
        a["publication_name_shape"] = "quoted_name"
    elif pi == "reserved_word_name":
        a["publication_name_shape"] = "reserved_word_name"

    # --- expected_status=failure -> representative failure -------------
    es = a.get("expected_status", "success")
    if es == "failure":
        a["publication_identity"] = "exists"
        a["duplicate_publication_name"] = "same_name_exists"

    # --- Derive expected_status from failure count ---------------------
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreatePublicationFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
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
        raise CreatePublicationFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreatePublicationFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreatePublicationFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_publication_factor_loop_plan(
    repository_root: Path,
) -> CreatePublicationFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_publication_factor_loop_obligations(root)
    cases: list[CreatePublicationFactorCase] = []
    delegated: list[CreatePublicationFactorObligation] = []
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
            CreatePublicationFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEPUBLICATION{ordinal:05d}",
                sql_filename=f"CREATEPUBLICATION{ordinal:05d}.sql",
                object_prefix=f"createpublication_{ordinal:05d}_",
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
    plan = CreatePublicationFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 72 or len(plan.delegated) != 0:
        raise CreatePublicationFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 72:
        raise CreatePublicationFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 72:
        raise CreatePublicationFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_publication_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreatePublicationFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreatePublicationFactorObligation(
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
    if len(rows) != 72:
        raise CreatePublicationFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreatePublicationFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 4, "SFV": 68}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreatePublicationFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreatePublicationFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 72:
        raise CreatePublicationFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreatePublicationFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreatePublicationFactorLoopError",
    "CreatePublicationGrammarAction",
    "CreatePublicationFactorObligation",
    "CreatePublicationFactorCase",
    "CreatePublicationFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_publication_factor_loop_obligations",
    "build_create_publication_factor_loop_plan",
    "_obligation_multiset_sha256",
]
