"""Factor-value-loop obligation ledger for PostgreSQL 18.4 SELECT INTO.

SELECT INTO is a PostgreSQL DDL statement that creates a new table from a
query result (official synopsis: ``sql-selectinto.html``).  It has a single
official synopsis form; the three table-type modifiers (permanent, temporary,
unlogged) are factor *values* of the ``statement_branch``/``table_type``
axes, not separate GRM branches.

SELECT INTO does **not** support ``IF NOT EXISTS``: a re-creation always
errors (``42P07``).  It also does not support ``USING method``,
``TABLESPACE``, ``ON COMMIT``, or ``WITH (storage_parameter)`` -- those are
``CREATE TABLE AS`` only.  SELECT INTO is deprecated in favour of
``CREATE TABLE AS``.

The 56 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).  The single ``GRM``
target action is synthesised from the official synopsis and is NOT counted
in ``factor_value_count``.  Hence ``GRM`` 1 + ``SFV`` 56 = 57 local
obligations, each materialised as exactly one regress program.  There are
no ``RISK`` obligations (the catalog rows carry no RISK disposition).

SELECT INTO creates a ``pg_class`` relation of kind ``r`` (a base table),
so the catalog-audit probe checks ``pg_catalog.pg_class`` (``relname``,
``relkind = 'r'``).  The bookend gate (``audit_complete_table_script``)
triggers on raw ``CREATE TABLE``; ``SELECT INTO`` does not contain the
``CREATE`` keyword, so the bookend gate does **not** fire.  The source
fixture tables (created via ``CREATE TABLE`` unquoted) still need cleanup
``DROP TABLE IF EXISTS`` in the render's fixture management.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class SelectIntoFactorLoopError(ValueError):
    """Raised when a frozen SELECT INTO obligation input drifts."""


@dataclass(frozen=True)
class SelectIntoGrammarAction:
    """One official target action form of the SELECT INTO synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class SelectIntoFactorObligation:
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
class SelectIntoFactorCase:
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
class SelectIntoFactorLoopPlan:
    obligations: tuple[SelectIntoFactorObligation, ...]
    cases: tuple[SelectIntoFactorCase, ...]
    delegated: tuple[SelectIntoFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-selectinto.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-selectinto"

# The single consumer action for all SELECT INTO factors.  SELECT INTO has
# one synopsis, so every factor's consumer is "select_into".
_REPRESENTATIVE_ACTION = "select_into"

# statement_branch canonical value -> consumer action.
_STATEMENT_BRANCH_CONSUMER = {
    "branch_permanent": _REPRESENTATIVE_ACTION,
    "branch_temporary": _REPRESENTATIVE_ACTION,
    "branch_unlogged": _REPRESENTATIVE_ACTION,
}

# Canonical factor -> the action where the value is observable.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "table_type": _REPRESENTATIVE_ACTION,
    "keyword_table": _REPRESENTATIVE_ACTION,
    "temp_modifier": _REPRESENTATIVE_ACTION,
    "query_shape": _REPRESENTATIVE_ACTION,
    "with_clause": _REPRESENTATIVE_ACTION,
    "select_modifier": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "column_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "source_table_dependency": _REPRESENTATIVE_ACTION,
    "schema_dependency": _REPRESENTATIVE_ACTION,
    "column_type_derivation": _REPRESENTATIVE_ACTION,
    "duplicate_table_name": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "query_error": _REPRESENTATIVE_ACTION,
    "schema_not_exists": _REPRESENTATIVE_ACTION,
    "reserved_schema_name": _REPRESENTATIVE_ACTION,
    "identifier_length_exceeded": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# table_type -> statement_branch derivation.
_TABLE_TYPE_TO_BRANCH = {
    "permanent": "branch_permanent",
    "temporary": "branch_temporary",
    "unlogged": "branch_unlogged",
}

# statement_branch -> table_type derivation.
_BRANCH_TO_TABLE_TYPE = {
    "branch_permanent": "permanent",
    "branch_temporary": "temporary",
    "branch_unlogged": "unlogged",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
#
# SELECT INTO has no IF NOT EXISTS, so object_state=already_exists and
# duplicate_table_name are both 42P07 failures.  The privilege, query-error,
# schema, and reserved-schema-name failure paths mirror CREATE TABLE AS.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("duplicate_table_name", "without_if_not_exists_error"),
        ("privilege_insufficient", "no_create_privilege_in_schema"),
        ("query_error", "source_table_not_exists"),
        ("query_error", "expression_invalid"),
        ("query_error", "type_mismatch"),
        ("schema_not_exists", "target_schema_absent"),
        ("reserved_schema_name", "pg_catalog"),
        ("reserved_schema_name", "information_schema"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P07",
        "duplicate_table_provisional",
    ),
    ("object_state", "already_exists"): (
        "42P07",
        "duplicate_table_provisional",
    ),
    ("duplicate_table_name", "without_if_not_exists_error"): (
        "42P07",
        "duplicate_table_without_if_not_exists_provisional",
    ),
    ("privilege_insufficient", "no_create_privilege_in_schema"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("query_error", "source_table_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("query_error", "expression_invalid"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("query_error", "type_mismatch"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("schema_not_exists", "target_schema_absent"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("reserved_schema_name", "pg_catalog"): (
        "42501",
        "pg_catalog_reserved_provisional",
    ),
    ("reserved_schema_name", "information_schema"): (
        "42501",
        "information_schema_reserved_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[SelectIntoGrammarAction, ...]
):
    """Freeze the single SELECT INTO synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            _REPRESENTATIVE_ACTION,
            _BRANCH_1,
            (
                "SELECT [ALL|DISTINCT] [select_list] "
                "INTO [TEMPORARY|TEMP|UNLOGGED] [TABLE] new_table "
                "[FROM from_item] [WHERE condition] ..."
            ),
            "synopsis-select-into",
        ),
    )
    actions = [
        SelectIntoGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise SelectIntoFactorLoopError(
            "select_into action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise SelectIntoFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise SelectIntoFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[SelectIntoFactorObligation]
):
    rows: list[SelectIntoFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            SelectIntoFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"SELECTINTO-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|synopsis|"
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
        raise SelectIntoFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[SelectIntoFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("select_into")
    if len(catalog_rows) != 56:
        raise SelectIntoFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[SelectIntoFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            SelectIntoFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"SELECTINTO-SFV|{row.row_id}|{consumer}"
                ),
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
    rows: tuple[SelectIntoFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"select-into-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive factor values).
#
# temp_modifier uses "none" as an inactive sentinel (not an SFV value): it
# is only set to TEMPORARY/TEMP when temp_modifier is the primary factor or
# when table_type=temporary is derived.  The T5 exception factors use "none"
# to mean "no failure active".
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_permanent",
    "object_state": "not_exists",
    "expected_status": "success",
    "table_type": "permanent",
    "keyword_table": "absent",
    "temp_modifier": "none",
    "query_shape": "simple_select",
    "with_clause": "without_with",
    "select_modifier": "default",
    "table_name_shape": "simple",
    "column_name_shape": "inherited_from_query",
    "privilege_level": "superuser",
    "source_table_dependency": "source_table_exists",
    "schema_dependency": "schema_exists",
    "column_type_derivation": "from_query_result",
    "duplicate_table_name": "none",
    "privilege_insufficient": "none",
    "query_error": "none",
    "schema_not_exists": "none",
    "reserved_schema_name": "none",
    "identifier_length_exceeded": "none",
    "verification_mode": "pg_class_catalog_query",
    "cleanup_mode": "DROP_TABLE_IF_EXISTS",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping T1/T2 factors and expected_status."""

    # table_type <-> statement_branch
    table_type = a.get("table_type", "permanent")
    branch = a.get("statement_branch", "branch_permanent")
    if table_type in _TABLE_TYPE_TO_BRANCH:
        if a.get("statement_branch") == _BASELINE_DEFAULTS[
            "statement_branch"
        ]:
            a["statement_branch"] = _TABLE_TYPE_TO_BRANCH[table_type]
            branch = a["statement_branch"]
    if branch in _BRANCH_TO_TABLE_TYPE:
        derived_tt = _BRANCH_TO_TABLE_TYPE[branch]
        if a.get("table_type") == _BASELINE_DEFAULTS["table_type"]:
            a["table_type"] = derived_tt
            table_type = derived_tt

    # temp_modifier (TEMP/TEMPORARY) implies table_type=temporary.
    tm = a.get("temp_modifier", "none")
    if tm in ("TEMP", "TEMPORARY"):
        if a.get("table_type") == _BASELINE_DEFAULTS["table_type"]:
            a["table_type"] = "temporary"
            table_type = "temporary"
            a["statement_branch"] = "branch_temporary"
            branch = "branch_temporary"

    # When table_type=temporary and temp_modifier is still the "none"
    # sentinel, default it to TEMPORARY so the render emits the keyword.
    if table_type == "temporary" and a.get("temp_modifier") == "none":
        a["temp_modifier"] = "TEMPORARY"

    # T5 failure derivations -> T1/T4 counterparts
    # expected_status=failure (meta) -> duplicate-table scenario
    if a.get("expected_status") == "failure":
        if _count_baseline_failures(a) == 0:
            a["object_state"] = "already_exists"

    # duplicate_table_name -> already_exists
    if a.get("duplicate_table_name") == "without_if_not_exists_error":
        a["object_state"] = "already_exists"

    # query_error=source_table_not_exists -> source not exists
    if a.get("query_error") == "source_table_not_exists":
        a["source_table_dependency"] = "source_table_not_exists"

    # privilege_insufficient -> non_owner_no_privilege
    if a.get("privilege_insufficient") == "no_create_privilege_in_schema":
        a["privilege_level"] = "non_owner_no_privilege"

    # schema_not_exists=target_schema_absent -> schema_not_exists
    if a.get("schema_not_exists") == "target_schema_absent":
        a["schema_dependency"] = "schema_not_exists"
        a["table_name_shape"] = "schema_qualified"

    # reserved_schema_name -> schema_qualified
    if a.get("reserved_schema_name") in (
        "pg_catalog", "information_schema",
    ):
        if a.get("reserved_schema_name") == "pg_catalog":
            a["schema_dependency"] = "pg_catalog_reserved"
        a["table_name_shape"] = "schema_qualified"

    # schema_dependency -> table_name_shape=schema_qualified
    if a.get("schema_dependency") in (
        "schema_not_exists", "pg_catalog_reserved",
    ):
        a["table_name_shape"] = "schema_qualified"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: SelectIntoFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    if obligation.kind == "GRM":
        assignments["statement_branch"] = _BRANCH_1
    else:
        assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    # Re-assert the primary factor so a derived overlapping factor never
    # clobbers the obligation's own value.
    if obligation.kind != "GRM":
        assignments[obligation.factor_key] = obligation.value
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise SelectIntoFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: SelectIntoFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise SelectIntoFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_select_into_factor_loop_plan(
    repository_root: Path,
) -> SelectIntoFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_select_into_factor_loop_obligations(root)
    cases: list[SelectIntoFactorCase] = []
    delegated: list[SelectIntoFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(
                obligation
            )
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            SelectIntoFactorCase(
                ordinal=ordinal,
                case_id=f"SELECTINTO{ordinal:05d}",
                sql_filename=f"SELECTINTO{ordinal:05d}.sql",
                object_prefix=f"selectinto_{ordinal:05d}_",
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
    plan = SelectIntoFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 57 or len(plan.delegated) != 0:
        raise SelectIntoFactorLoopError(
            "factor loop plan count drift"
        )
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 57
    ):
        raise SelectIntoFactorLoopError(
            "local obligation mapping drift"
        )
    if (
        len({row.sql_filename for row in plan.cases}) != 57
    ):
        raise SelectIntoFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_select_into_factor_loop_obligations(
    repository_root: Path,
) -> tuple[SelectIntoFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        SelectIntoFactorObligation(
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
    if len(rows) != 57:
        raise SelectIntoFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise SelectIntoFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 56}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise SelectIntoFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise SelectIntoFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 57:
        raise SelectIntoFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {
        "covered",
        "expected_failure",
        "delegated",
    }
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise SelectIntoFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "SelectIntoFactorLoopError",
    "SelectIntoGrammarAction",
    "SelectIntoFactorObligation",
    "SelectIntoFactorCase",
    "SelectIntoFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "_BRANCH_TO_TABLE_TYPE",
    "_TABLE_TYPE_TO_BRANCH",
    "compile_select_into_factor_loop_obligations",
    "build_select_into_factor_loop_plan",
    "_obligation_multiset_sha256",
]
