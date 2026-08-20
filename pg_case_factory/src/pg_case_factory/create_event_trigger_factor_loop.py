"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE EVENT TRIGGER.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE EVENT TRIGGER``.  CREATE EVENT TRIGGER is a PostgreSQL DDL
statement with a single official synopsis branch:
``CREATE EVENT TRIGGER name ON event [ WHEN ... ] EXECUTE
{ FUNCTION | PROCEDURE } function_name()``.  The statement defines an
event trigger recorded in ``pg_catalog.pg_event_trigger`` (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.

CREATE EVENT TRIGGER requires superuser privilege: a non-superuser
session receives SQLSTATE ``42501``.  Other reachable failure surfaces
are: a duplicate trigger name (``42710``), a missing handler function
(``42883``), a wrong-return-type or wrong-arity handler function
(``42804``), an unsupported event type (``42601``) and an unsupported
filter variable (``42601``).  The declared meta-failure
``expected_status=failure`` is provisionally attributed ``42809``.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no
``RISK`` obligations.  CREATE EVENT TRIGGER does NOT support
``OR REPLACE`` (confirmed against the official PG18 synopsis).

The grammar ledger is self-contained: the single synopsis action is
frozen inline.  The 61 canonical ``SFV`` rows are loaded from the
shipped applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateEventTriggerFactorLoopError(ValueError):
    """Raised when a frozen CREATE EVENT TRIGGER obligation input drifts."""


@dataclass(frozen=True)
class CreateEventTriggerGrammarAction:
    """One official target action form of the CREATE EVENT TRIGGER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateEventTriggerFactorObligation:
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
class CreateEventTriggerFactorCase:
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
class CreateEventTriggerFactorLoopPlan:
    obligations: tuple[CreateEventTriggerFactorObligation, ...]
    cases: tuple[CreateEventTriggerFactorCase, ...]
    delegated: tuple[CreateEventTriggerFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createeventtrigger.html).
_BRANCH_CREATE_EVENT_TRIGGER = "branch_create_event_trigger"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createeventtrigger"

# The single representative action for all canonical factors.  CREATE
# EVENT TRIGGER has only one synopsis form.
_REPRESENTATIVE_ACTION = "create_event_trigger"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_CREATE_EVENT_TRIGGER: "create_event_trigger",
}

# Canonical factor -> the action where the value is observable.  Since
# CREATE EVENT TRIGGER has only one synopsis form, every factor observes
# on the single ``create_event_trigger`` action.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "event_type": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "when_filter_clause": _REPRESENTATIVE_ACTION,
    "execute_keyword": _REPRESENTATIVE_ACTION,
    "trigger_function_state": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "trigger_name_shape": _REPRESENTATIVE_ACTION,
    "function_name_shape": _REPRESENTATIVE_ACTION,
    "filter_value_shape": _REPRESENTATIVE_ACTION,
    "function_existence": _REPRESENTATIVE_ACTION,
    "function_return_type": _REPRESENTATIVE_ACTION,
    "function_parameter_count": _REPRESENTATIVE_ACTION,
    "single_user_mode": _REPRESENTATIVE_ACTION,
    "duplicate_trigger_name": _REPRESENTATIVE_ACTION,
    "privilege_denied_non_superuser": _REPRESENTATIVE_ACTION,
    "nonexistent_function": _REPRESENTATIVE_ACTION,
    "function_wrong_return_type": _REPRESENTATIVE_ACTION,
    "function_wrong_parameter_count": _REPRESENTATIVE_ACTION,
    "invalid_event_type": _REPRESENTATIVE_ACTION,
    "invalid_filter_variable": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target
# check and are rejected (provisional sqlstates — DB phase verifies on
# PG 18.4).  Overlapping T3-T5 values describe the same scenario as
# their T1-T2 counterparts; the renderer reaches the intended failure
# via the primary value's cluster.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("duplicate_trigger_name", "same_name_conflict"),
        ("trigger_function_state", "function_not_exists"),
        (
            "trigger_function_state",
            "function_exists_wrong_return_type",
        ),
        (
            "trigger_function_state",
            "function_exists_with_parameters",
        ),
        ("privilege_level", "non_superuser"),
        (
            "privilege_denied_non_superuser",
            "non_superuser_failure",
        ),
        ("function_name_shape", "nonexistent_name"),
        ("function_existence", "function_not_exists"),
        (
            "function_return_type",
            "non_event_trigger_return_type",
        ),
        ("function_parameter_count", "nonzero_parameters"),
        ("nonexistent_function", "function_not_exists"),
        ("function_wrong_return_type", "wrong_return_type"),
        (
            "function_wrong_parameter_count",
            "nonzero_parameters",
        ),
        ("invalid_event_type", "invalid_event_type"),
        ("invalid_filter_variable", "unsupported_variable"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42809",
        "create_event_trigger_declared_failure_provisional",
    ),
    ("object_state", "exists"): (
        "42710",
        "duplicate_event_trigger_provisional",
    ),
    ("duplicate_trigger_name", "same_name_conflict"): (
        "42710",
        "duplicate_event_trigger_provisional",
    ),
    ("trigger_function_state", "function_not_exists"): (
        "42883",
        "event_trigger_function_not_found_provisional",
    ),
    (
        "trigger_function_state",
        "function_exists_wrong_return_type",
    ): (
        "42804",
        "event_trigger_function_wrong_return_type_provisional",
    ),
    (
        "trigger_function_state",
        "function_exists_with_parameters",
    ): (
        "42804",
        "event_trigger_function_wrong_arity_provisional",
    ),
    ("privilege_level", "non_superuser"): (
        "42501",
        "must_be_superuser_provisional",
    ),
    (
        "privilege_denied_non_superuser",
        "non_superuser_failure",
    ): (
        "42501",
        "must_be_superuser_provisional",
    ),
    ("function_name_shape", "nonexistent_name"): (
        "42883",
        "event_trigger_function_not_found_provisional",
    ),
    ("function_existence", "function_not_exists"): (
        "42883",
        "event_trigger_function_not_found_provisional",
    ),
    ("function_return_type", "non_event_trigger_return_type"): (
        "42804",
        "event_trigger_function_wrong_return_type_provisional",
    ),
    ("function_parameter_count", "nonzero_parameters"): (
        "42804",
        "event_trigger_function_wrong_arity_provisional",
    ),
    ("nonexistent_function", "function_not_exists"): (
        "42883",
        "event_trigger_function_not_found_provisional",
    ),
    ("function_wrong_return_type", "wrong_return_type"): (
        "42804",
        "event_trigger_function_wrong_return_type_provisional",
    ),
    (
        "function_wrong_parameter_count",
        "nonzero_parameters",
    ): (
        "42804",
        "event_trigger_function_wrong_arity_provisional",
    ),
    ("invalid_event_type", "invalid_event_type"): (
        "42601",
        "invalid_event_type_provisional",
    ),
    ("invalid_filter_variable", "unsupported_variable"): (
        "42601",
        "invalid_filter_variable_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateEventTriggerGrammarAction, ...]
):
    """Freeze every CREATE EVENT TRIGGER synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_event_trigger",
            _BRANCH_CREATE_EVENT_TRIGGER,
            (
                "CREATE EVENT TRIGGER name ON event "
                "[ WHEN filter_variable IN "
                "(filter_value [, ...]) [ AND ...] ] "
                "EXECUTE { FUNCTION | PROCEDURE } function_name()"
            ),
            "synopsis-create-event-trigger",
        ),
    )
    actions = [
        CreateEventTriggerGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateEventTriggerFactorLoopError(
            "create event trigger action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateEventTriggerFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateEventTriggerFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[CreateEventTriggerFactorObligation]
):
    rows: list[CreateEventTriggerFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateEventTriggerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CET-GRM|{action.grammar_branch_id}|"
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
        raise CreateEventTriggerFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateEventTriggerFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_event_trigger")
    if len(catalog_rows) != 61:
        raise CreateEventTriggerFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateEventTriggerFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateEventTriggerFactorObligation(
                ordinal=0,
                obligation_id=f"CET-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateEventTriggerFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-event-trigger-factor-obligations-v1\n"
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
    "create_event_trigger": _BRANCH_CREATE_EVENT_TRIGGER,
}

# Dense baseline defaults (all positive T1-T6 factor values from the
# declared ``create_event_trigger_declared_factor_baseline`` group).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE_EVENT_TRIGGER,
    "target_action": "create_event_trigger",
    "event_type": "ddl_command_start",
    "object_state": "not_exists",
    "expected_status": "success",
    "when_filter_clause": "omitted",
    "execute_keyword": "FUNCTION",
    "trigger_function_state": "function_exists_valid_signature",
    "privilege_level": "superuser",
    "trigger_name_shape": "simple_id",
    "function_name_shape": "simple_id",
    "filter_value_shape": "single_command_tag",
    "function_existence": "function_exists",
    "function_return_type": "event_trigger_return_type",
    "function_parameter_count": "zero_parameters",
    "single_user_mode": "normal_mode",
    "duplicate_trigger_name": "no_conflict",
    "privilege_denied_non_superuser": "superuser_success",
    "nonexistent_function": "function_exists",
    "function_wrong_return_type": "correct_return_type",
    "function_wrong_parameter_count": "zero_parameters",
    "invalid_event_type": "valid_event_type",
    "invalid_filter_variable": "tag_variable",
    "verification_mode": "catalog_query_pg_event_trigger",
    "cleanup_mode": "drop_event_trigger",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping T3-T5 factors and expected_status from the primary.

    The T5 boundary factors describe the same scenario as their T1-T2
    counterparts.  When the primary is a T1-T2 value, the corresponding
    T3-T5 values are derived; when the primary is a T3-T5 value, the
    T1-T2 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # privilege cluster: privilege_level / privilege_denied_non_superuser
    pl = a.get("privilege_level", "superuser")
    pdn = a.get(
        "privilege_denied_non_superuser", "superuser_success"
    )
    if pl == "non_superuser" or pdn == "non_superuser_failure":
        a["privilege_level"] = "non_superuser"
        a["privilege_denied_non_superuser"] = "non_superuser_failure"

    # object existence cluster: object_state / duplicate_trigger_name
    os_ = a.get("object_state", "not_exists")
    dtn = a.get("duplicate_trigger_name", "no_conflict")
    if os_ == "exists" or dtn == "same_name_conflict":
        a["object_state"] = "exists"
        a["duplicate_trigger_name"] = "same_name_conflict"

    # function-not-exists cluster
    tfs = a.get(
        "trigger_function_state",
        "function_exists_valid_signature",
    )
    nf = a.get("nonexistent_function", "function_exists")
    fe = a.get("function_existence", "function_exists")
    fns = a.get("function_name_shape", "simple_id")
    if (
        tfs == "function_not_exists"
        or nf == "function_not_exists"
        or fe == "function_not_exists"
        or fns == "nonexistent_name"
    ):
        a["trigger_function_state"] = "function_not_exists"
        a["nonexistent_function"] = "function_not_exists"
        a["function_existence"] = "function_not_exists"
        a["function_name_shape"] = "nonexistent_name"

    # wrong-return-type cluster (only when the function exists)
    if a.get("trigger_function_state") != "function_not_exists":
        fwrt = a.get("function_wrong_return_type", "correct_return_type")
        frt = a.get(
            "function_return_type", "event_trigger_return_type"
        )
        if (
            tfs == "function_exists_wrong_return_type"
            or fwrt == "wrong_return_type"
            or frt == "non_event_trigger_return_type"
        ):
            a["trigger_function_state"] = (
                "function_exists_wrong_return_type"
            )
            a["function_wrong_return_type"] = "wrong_return_type"
            a["function_return_type"] = "non_event_trigger_return_type"

    # wrong-arity cluster (only when the function exists & return ok)
    if a.get("trigger_function_state") not in (
        "function_not_exists",
        "function_exists_wrong_return_type",
    ):
        fwpc = a.get(
            "function_wrong_parameter_count", "zero_parameters"
        )
        fpc = a.get("function_parameter_count", "zero_parameters")
        if (
            tfs == "function_exists_with_parameters"
            or fwpc == "nonzero_parameters"
            or fpc == "nonzero_parameters"
        ):
            a["trigger_function_state"] = (
                "function_exists_with_parameters"
            )
            a["function_wrong_parameter_count"] = "nonzero_parameters"
            a["function_parameter_count"] = "nonzero_parameters"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateEventTriggerFactorObligation,
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
        raise CreateEventTriggerFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateEventTriggerFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateEventTriggerFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_event_trigger_factor_loop_plan(
    repository_root: Path,
) -> CreateEventTriggerFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = (
        compile_create_event_trigger_factor_loop_obligations(root)
    )
    cases: list[CreateEventTriggerFactorCase] = []
    delegated: list[CreateEventTriggerFactorObligation] = []
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
            CreateEventTriggerFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEEVENTTRIGGER{ordinal:05d}",
                sql_filename=f"CREATEEVENTTRIGGER{ordinal:05d}.sql",
                object_prefix=f"createeventtrigger_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(
                    obligation
                ),
                execution_profile="serial_sql",
            )
        )
    plan = CreateEventTriggerFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 62 or len(plan.delegated) != 0:
        raise CreateEventTriggerFactorLoopError(
            "factor loop plan count drift"
        )
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 62
    ):
        raise CreateEventTriggerFactorLoopError(
            "local obligation mapping drift"
        )
    if (
        len({row.sql_filename for row in plan.cases}) != 62
    ):
        raise CreateEventTriggerFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_create_event_trigger_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateEventTriggerFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateEventTriggerFactorObligation(
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
    if len(rows) != 62:
        raise CreateEventTriggerFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateEventTriggerFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 61}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateEventTriggerFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateEventTriggerFactorLoopError(
            "delegated obligation count drift"
        )
    if (
        sum(
            row.disposition in {"covered", "expected_failure"}
            for row in rows
        )
        != 62
    ):
        raise CreateEventTriggerFactorLoopError(
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
        raise CreateEventTriggerFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateEventTriggerFactorLoopError",
    "CreateEventTriggerGrammarAction",
    "CreateEventTriggerFactorObligation",
    "CreateEventTriggerFactorCase",
    "CreateEventTriggerFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_event_trigger_factor_loop_obligations",
    "build_create_event_trigger_factor_loop_plan",
    "_obligation_multiset_sha256",
]
