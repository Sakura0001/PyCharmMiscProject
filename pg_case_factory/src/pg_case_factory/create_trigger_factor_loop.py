"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TRIGGER.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TRIGGER``.  CREATE TRIGGER is a PostgreSQL DDL statement with
3 official synopsis branches: BEFORE, AFTER, and INSTEAD OF.  The
statement targets a trigger ON a table (or view for INSTEAD OF) and
requires ownership of the table plus the ``CREATE TRIGGER`` privilege.

Each local obligation becomes exactly one regress program.  Because
CREATE TRIGGER is table-dependent (it creates a trigger ON a table that
the script itself CREATEs), the render creates tables, trigger
functions, and the trigger; the bookend gate (DROP TABLE IF EXISTS)
applies.

The grammar ledger is self-contained: the 3 synopsis actions are frozen
inline.  The 88 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateTriggerFactorLoopError(ValueError):
    """Raised when a frozen CREATE TRIGGER obligation input drifts."""


@dataclass(frozen=True)
class CreateTriggerGrammarAction:
    """One official target action form of the CREATE TRIGGER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTriggerFactorObligation:
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
class CreateTriggerFactorCase:
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
class CreateTriggerFactorLoopPlan:
    obligations: tuple[CreateTriggerFactorObligation, ...]
    cases: tuple[CreateTriggerFactorCase, ...]
    delegated: tuple[CreateTriggerFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createtrigger.html).
_BRANCH_BEFORE = "branch_1"
_BRANCH_AFTER = "branch_2"
_BRANCH_INSTEAD_OF = "branch_3"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtrigger"

# statement_branch / trigger_timing canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_BEFORE: "before_trigger",
    _BRANCH_AFTER: "after_trigger",
    _BRANCH_INSTEAD_OF: "instead_of_trigger",
}

_TRIGGER_TIMING_CONSUMER = {
    "BEFORE": "before_trigger",
    "AFTER": "after_trigger",
    "INSTEAD_OF": "instead_of_trigger",
}

_REPRESENTATIVE_ACTION = "before_trigger"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    f = row.factor
    v = row.value
    if f == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[v]
        except KeyError as exc:
            raise CreateTriggerFactorLoopError(
                f"unknown statement branch value: {v}"
            ) from exc
    if f == "trigger_timing":
        try:
            return _TRIGGER_TIMING_CONSUMER[v]
        except KeyError as exc:
            raise CreateTriggerFactorLoopError(
                f"unknown trigger timing value: {v}"
            ) from exc
    if f == "INSTEAD_OF_on_table":
        return "instead_of_trigger"
    if f == "BEFORE_INSTEAD_OF_on_view":
        if v == "BEFORE_INSERT_on_view":
            return "before_trigger"
        if v == "AFTER_INSERT_on_view":
            return "after_trigger"
        return _REPRESENTATIVE_ACTION
    if f == "constraint_trigger_on_non_constraint_event":
        if v == "CONSTRAINT_with_INSTEAD_OF":
            return "instead_of_trigger"
        return _REPRESENTATIVE_ACTION
    if f == "permission_insufficient":
        if v == "not_table_owner_for_CONSTRAINT":
            return "before_trigger"
        return _REPRESENTATIVE_ACTION
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("trigger_name_shape", "duplicate"),
        ("event_column_list", "nonexistent_column"),
        ("privilege_level", "non_owner_no_privilege"),
        ("table_dependency", "table_not_exists"),
        ("function_dependency", "trigger_function_not_exists"),
        ("function_dependency", "function_returns_wrong_type"),
        ("referenced_table_dependency", "referenced_table_not_exists"),
        ("schema_dependency", "schema_not_exists"),
        ("duplicate_trigger", "without_OR_REPLACE_error"),
        ("INSTEAD_OF_on_table", "INSTEAD_OF_INSERT_on_regular_table"),
        ("BEFORE_INSTEAD_OF_on_view", "BEFORE_INSERT_on_view"),
        ("BEFORE_INSTEAD_OF_on_view", "AFTER_INSERT_on_view"),
        ("TRUNCATE_with_FOR_EACH_ROW", "TRUNCATE_FOR_EACH_ROW"),
        ("UPDATE_OF_nonexistent_column", "UPDATE_OF_missing_column"),
        ("constraint_trigger_on_non_constraint_event", "CONSTRAINT_with_INSTEAD_OF"),
        ("permission_insufficient", "no_create_trigger_privilege"),
        ("permission_insufficient", "not_table_owner_for_CONSTRAINT"),
        ("referenced_table_not_exists", "FROM_table_not_found"),
        ("identifier_length_exceeded", "over_63_chars"),
        ("referencing_clause", "transition_table_on_foreign_table"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("trigger_name_shape", "duplicate"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("event_column_list", "nonexistent_column"): (
        "42703",
        "undefined_column_provisional",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("table_dependency", "table_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("function_dependency", "trigger_function_not_exists"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("function_dependency", "function_returns_wrong_type"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("referenced_table_dependency", "referenced_table_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("schema_dependency", "schema_not_exists"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("duplicate_trigger", "without_OR_REPLACE_error"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("INSTEAD_OF_on_table", "INSTEAD_OF_INSERT_on_regular_table"): (
        "42609",
        "instead_of_requires_view_provisional",
    ),
    ("BEFORE_INSTEAD_OF_on_view", "BEFORE_INSERT_on_view"): (
        "42609",
        "before_after_disallowed_on_view_provisional",
    ),
    ("BEFORE_INSTEAD_OF_on_view", "AFTER_INSERT_on_view"): (
        "42609",
        "before_after_disallowed_on_view_provisional",
    ),
    ("TRUNCATE_with_FOR_EACH_ROW", "TRUNCATE_FOR_EACH_ROW"): (
        "42609",
        "truncate_for_each_row_provisional",
    ),
    ("UPDATE_OF_nonexistent_column", "UPDATE_OF_missing_column"): (
        "42703",
        "undefined_column_provisional",
    ),
    ("constraint_trigger_on_non_constraint_event", "CONSTRAINT_with_INSTEAD_OF"): (
        "42609",
        "constraint_instead_of_provisional",
    ),
    ("permission_insufficient", "no_create_trigger_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("permission_insufficient", "not_table_owner_for_CONSTRAINT"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("referenced_table_not_exists", "FROM_table_not_found"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("identifier_length_exceeded", "over_63_chars"): (
        "42622",
        "name_too_long_provisional",
    ),
    ("referencing_clause", "transition_table_on_foreign_table"): (
        "42609",
        "transition_table_on_foreign_table_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateTriggerGrammarAction, ...]
):
    """Freeze every CREATE TRIGGER synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "before_trigger",
            _BRANCH_BEFORE,
            "CREATE [OR REPLACE] TRIGGER name BEFORE event "
            "ON table_name EXECUTE FUNCTION fn()",
            "synopsis-before",
        ),
        (
            "after_trigger",
            _BRANCH_AFTER,
            "CREATE [OR REPLACE] TRIGGER name AFTER event "
            "ON table_name EXECUTE FUNCTION fn()",
            "synopsis-after",
        ),
        (
            "instead_of_trigger",
            _BRANCH_INSTEAD_OF,
            "CREATE TRIGGER name INSTEAD OF event "
            "ON view_name EXECUTE FUNCTION fn()",
            "synopsis-instead-of",
        ),
    )
    actions = [
        CreateTriggerGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 3:
        raise CreateTriggerFactorLoopError(
            "create trigger action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateTriggerFactorObligation]
):
    rows: list[CreateTriggerFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTriggerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CTRG-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 3:
        raise CreateTriggerFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTriggerFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_trigger")
    if len(catalog_rows) != 88:
        raise CreateTriggerFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateTriggerFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTriggerFactorObligation(
                ordinal=0,
                obligation_id=f"CTRG-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateTriggerFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-trigger-factor-obligations-v1\n"
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
    "before_trigger": _BRANCH_BEFORE,
    "after_trigger": _BRANCH_AFTER,
    "instead_of_trigger": _BRANCH_INSTEAD_OF,
}

# Branch -> default trigger_timing and table_dependency.
_BRANCH_TIMING = {
    _BRANCH_BEFORE: "BEFORE",
    _BRANCH_AFTER: "AFTER",
    _BRANCH_INSTEAD_OF: "INSTEAD_OF",
}

_BRANCH_TABLE_DEP = {
    _BRANCH_BEFORE: "table_exists",
    _BRANCH_AFTER: "table_exists",
    _BRANCH_INSTEAD_OF: "view_exists_for_INSTEAD_OF",
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The
# T5 single-value factors are NOT baselined here; they are derived in
# :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_BEFORE,
    "trigger_timing": "BEFORE",
    "trigger_event": "INSERT",
    "object_state": "not_exists",
    "expected_status": "success",
    "or_replace_clause": "absent",
    "constraint_trigger": "absent",
    "for_each_clause": "ROW",
    "deferrable_clause": "absent",
    "when_clause": "without_WHEN",
    "referencing_clause": "absent",
    "from_clause": "absent",
    "update_of_columns": "without_column_list",
    "execute_clause": "FUNCTION",
    "trigger_name_shape": "simple",
    "table_name_shape": "simple",
    "function_name_shape": "simple",
    "event_column_list": "single_column",
    "privilege_level": "superuser",
    "table_dependency": "table_exists",
    "function_dependency": "trigger_function_exists",
    "referenced_table_dependency": "referenced_table_exists",
    "schema_dependency": "schema_exists",
    "verification_mode": "pg_trigger_catalog_query",
    "cleanup_mode": "DROP_TRIGGER",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    os = a.get("object_state", "not_exists")
    dt = a.get("duplicate_trigger", "")
    orc = a.get("or_replace_clause", "absent")
    tns = a.get("trigger_name_shape", "simple")

    # duplicate cluster: object_state / or_replace_clause / duplicate_trigger
    if os == "already_exists" or dt == "without_OR_REPLACE_error" or tns == "duplicate":
        a["object_state"] = "already_exists"
        a["duplicate_trigger"] = "without_OR_REPLACE_error"
        a["or_replace_clause"] = "absent"
        a["trigger_name_shape"] = "duplicate"
    elif dt == "with_OR_REPLACE_replace" or orc == "present":
        a["or_replace_clause"] = "present"
        a["duplicate_trigger"] = "with_OR_REPLACE_replace"
        if a.get("object_state") != "already_exists":
            a["object_state"] = "not_exists"
    else:
        a["duplicate_trigger"] = "with_OR_REPLACE_replace"

    # privilege cluster: privilege_level / permission_insufficient
    pl = a.get("privilege_level", "superuser")
    pi = a.get("permission_insufficient", "")
    if pl == "non_owner_no_privilege" or pi == "no_create_trigger_privilege":
        a["privilege_level"] = "non_owner_no_privilege"
        a["permission_insufficient"] = "no_create_trigger_privilege"
    elif pi == "not_table_owner_for_CONSTRAINT":
        a["constraint_trigger"] = "present"
        a["privilege_level"] = "non_owner_with_create_trigger"
    else:
        a["permission_insufficient"] = "no_create_trigger_privilege"

    # table-not-exists cluster
    td = a.get("table_dependency", "table_exists")
    if td == "table_not_exists":
        a["table_dependency"] = "table_not_exists"

    # function-not-exists cluster
    fd = a.get("function_dependency", "trigger_function_exists")
    if fd == "trigger_function_not_exists":
        a["function_dependency"] = "trigger_function_not_exists"
    elif fd == "function_returns_wrong_type":
        a["function_dependency"] = "function_returns_wrong_type"

    # referenced-table cluster
    rtd = a.get("referenced_table_dependency", "referenced_table_exists")
    rtn = a.get("referenced_table_not_exists", "")
    if rtd == "referenced_table_not_exists" or rtn == "FROM_table_not_found":
        a["referenced_table_dependency"] = "referenced_table_not_exists"
        a["referenced_table_not_exists"] = "FROM_table_not_found"
        a["from_clause"] = "present"
    else:
        a["referenced_table_not_exists"] = "FROM_table_not_found"

    # schema-not-exists cluster
    sd = a.get("schema_dependency", "schema_exists")
    if sd == "schema_not_exists":
        a["schema_dependency"] = "schema_not_exists"

    # INSTEAD OF on regular table cluster
    iot = a.get("INSTEAD_OF_on_table", "")
    if iot == "INSTEAD_OF_INSERT_on_regular_table":
        a["trigger_timing"] = "INSTEAD_OF"
        a["table_dependency"] = "table_exists"

    # BEFORE/AFTER on view cluster
    bio = a.get("BEFORE_INSTEAD_OF_on_view", "")
    if bio == "BEFORE_INSERT_on_view":
        a["trigger_timing"] = "BEFORE"
        a["table_dependency"] = "view_exists_for_INSTEAD_OF"
    elif bio == "AFTER_INSERT_on_view":
        a["trigger_timing"] = "AFTER"
        a["table_dependency"] = "view_exists_for_INSTEAD_OF"

    # TRUNCATE + FOR EACH ROW cluster
    tfr = a.get("TRUNCATE_with_FOR_EACH_ROW", "")
    if tfr == "TRUNCATE_FOR_EACH_ROW":
        a["trigger_event"] = "TRUNCATE"
        a["for_each_clause"] = "ROW"

    # UPDATE OF nonexistent column cluster
    uoc = a.get("UPDATE_OF_nonexistent_column", "")
    if uoc == "UPDATE_OF_missing_column":
        a["trigger_event"] = "UPDATE"
        a["update_of_columns"] = "with_column_list"
        a["event_column_list"] = "nonexistent_column"

    # CONSTRAINT + INSTEAD OF cluster
    ctn = a.get("constraint_trigger_on_non_constraint_event", "")
    if ctn == "CONSTRAINT_with_INSTEAD_OF":
        a["constraint_trigger"] = "present"
        a["trigger_timing"] = "INSTEAD_OF"
        a["table_dependency"] = "view_exists_for_INSTEAD_OF"

    # identifier-length-exceeded is standalone
    ile = a.get("identifier_length_exceeded", "")
    if ile == "over_63_chars":
        a["identifier_length_exceeded"] = "over_63_chars"

    # REFERENCING requires AFTER trigger (transition tables only work
    # with AFTER, not BEFORE).  Also handles the foreign-table PG18
    # test point which mandates AFTER INSERT.
    rc = a.get("referencing_clause", "absent")
    if rc in (
        "with_OLD_TABLE",
        "with_NEW_TABLE",
        "with_BOTH",
        "transition_table_on_foreign_table",
    ):
        a["trigger_timing"] = "AFTER"
        # Foreign-table case keeps table_exists for the base fixture.
        a["table_dependency"] = "table_exists"

    failures = _count_baseline_failures(a)
    a["expected_status"] = (
        "failure" if failures > 0 else "success"
    )


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateTriggerFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    branch = _ACTION_BRANCH[obligation.consumer_action_id]
    assignments["statement_branch"] = branch
    assignments["trigger_timing"] = _BRANCH_TIMING[branch]
    assignments["table_dependency"] = _BRANCH_TABLE_DEP[branch]
    assignments["target_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateTriggerFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTriggerFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateTriggerFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_trigger_factor_loop_plan(
    repository_root: Path,
) -> CreateTriggerFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_trigger_factor_loop_obligations(root)
    cases: list[CreateTriggerFactorCase] = []
    delegated: list[CreateTriggerFactorObligation] = []
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
            CreateTriggerFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETRIGGER{ordinal:05d}",
                sql_filename=f"CREATETRIGGER{ordinal:05d}.sql",
                object_prefix=f"createtrigger_{ordinal:05d}_",
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
    plan = CreateTriggerFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 91 or len(plan.delegated) != 0:
        raise CreateTriggerFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 91:
        raise CreateTriggerFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 91:
        raise CreateTriggerFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_trigger_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTriggerFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTriggerFactorObligation(
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
    if len(rows) != 91:
        raise CreateTriggerFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTriggerFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 3, "SFV": 88}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTriggerFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTriggerFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 91:
        raise CreateTriggerFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateTriggerFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateTriggerFactorLoopError",
    "CreateTriggerGrammarAction",
    "CreateTriggerFactorObligation",
    "CreateTriggerFactorCase",
    "CreateTriggerFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_trigger_factor_loop_obligations",
    "build_create_trigger_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
