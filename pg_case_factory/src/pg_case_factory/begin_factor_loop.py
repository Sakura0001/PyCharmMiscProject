"""Factor-value-loop obligation ledger for PostgreSQL 18.4 BEGIN.

BEGIN is a PostgreSQL TCL transaction-control statement with a single
official synopsis branch: ``BEGIN [WORK | TRANSACTION]
[transaction_mode [, ...]]``.  The statement starts a transaction block.
No TABLE is created, so the bookend (DROP TABLE IF EXISTS) is never
emitted.  The obligation ledger has 1 GRM obligation (the single synopsis)
plus 43 SFV obligations (every canonical factor value from the shipped
applicability universe ``postgresql_18_4_factor_audit.tsv``).  Total:
44 obligations, 44 cases, 0 delegated.

BEGIN is a no-DB tickoff statement: validation is via a static
``validation.json`` (byte-level re-render + compare against the generated
leaf SQL).  SQLSTATE expectations are provisional — a later DB phase
verifies them on PG 18.4.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class BeginFactorLoopError(ValueError):
    """Raised when a frozen BEGIN obligation input drifts."""


@dataclass(frozen=True)
class BeginGrammarAction:
    """One official target action form of the BEGIN synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class BeginFactorObligation:
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
class BeginFactorCase:
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
class BeginFactorLoopPlan:
    obligations: tuple[BeginFactorObligation, ...]
    cases: tuple[BeginFactorCase, ...]
    delegated: tuple[BeginFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-begin.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-begin"

# The single BEGIN synopsis action.
_REPRESENTATIVE_ACTION = "begin_transaction"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1: _REPRESENTATIVE_ACTION,
}

# Canonical factor -> the action where the value is observable.  BEGIN has
# only one synopsis, so every factor is observed through ``begin_transaction``.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "transaction_state": _REPRESENTATIVE_ACTION,
    "transaction_mode": _REPRESENTATIVE_ACTION,
    "chain_behavior": _REPRESENTATIVE_ACTION,
    "transaction_id_shape": _REPRESENTATIVE_ACTION,
    "savepoint_name_shape": _REPRESENTATIVE_ACTION,
    "environment_context": _REPRESENTATIVE_ACTION,
    "framework_context": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "state_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that are rejected by PostgreSQL
# (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("transaction_state", "missing_required_state"),
        ("state_boundary", "prepared_transaction_leftover"),
        ("chain_behavior", "and_chain"),
        ("chain_behavior", "and_no_chain"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "25001",
        "active_sql_transaction_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("transaction_state", "missing_required_state"): (
        "25001",
        "active_sql_transaction_provisional",
    ),
    ("state_boundary", "prepared_transaction_leftover"): (
        "55000",
        "object_not_in_prerequisite_state_provisional",
    ),
    ("chain_behavior", "and_chain"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("chain_behavior", "and_no_chain"): (
        "42601",
        "syntax_error_provisional",
    ),
}


def _load_grammar_actions() -> tuple[BeginGrammarAction, ...]:
    """Freeze the single BEGIN synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            _REPRESENTATIVE_ACTION,
            _BRANCH_1,
            "BEGIN [ WORK | TRANSACTION ] [ transaction_mode [, ...] ]",
            "synopsis-branch-1",
        ),
    )
    actions = [
        BeginGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise BeginFactorLoopError("begin action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise BeginFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise BeginFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[BeginFactorObligation]:
    rows: list[BeginFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            BeginFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"BEGIN-GRM|{action.grammar_branch_id}|"
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
        raise BeginFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[BeginFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("begin")
    if len(catalog_rows) != 43:
        raise BeginFactorLoopError("canonical obligation count drift")
    rows: list[BeginFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            BeginFactorObligation(
                ordinal=0,
                obligation_id=f"BEGIN-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[BeginFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"begin-factor-obligations-v1\n")
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
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "target_action": _REPRESENTATIVE_ACTION,
    "expected_status": "success",
    "transaction_state": "outside_transaction",
    "transaction_mode": "default",
    "chain_behavior": "none",
    "transaction_id_shape": "simple_id",
    "savepoint_name_shape": "simple_name",
    "environment_context": "normal_session",
    "framework_context": "no_outer_transaction",
    "invalid_combination": "none",
    "state_boundary": "no_open_transaction",
    "verification_mode": "catalog_query",
    "cleanup_mode": "rollback",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    chain_behavior=and_chain/and_no_chain are syntax errors for BEGIN, so
    they imply invalid_combination=syntax_valid_semantic_error.
    transaction_state values imply their state_boundary counterparts.
    expected_status is derived from the failure count.
    """

    cb = a.get("chain_behavior", "none")
    ts = a.get("transaction_state", "outside_transaction")

    if cb in ("and_chain", "and_no_chain"):
        a["invalid_combination"] = "syntax_valid_semantic_error"

    if ts == "prepared_transaction_exists":
        a["state_boundary"] = "prepared_transaction_leftover"
    elif ts in ("inside_transaction", "savepoint_exists"):
        a["state_boundary"] = "nested_savepoint"
    elif ts == "missing_required_state":
        a["state_boundary"] = "no_open_transaction"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: BeginFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["target_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise BeginFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: BeginFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise BeginFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_begin_factor_loop_plan(
    repository_root: Path,
) -> BeginFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_begin_factor_loop_obligations(root)
    cases: list[BeginFactorCase] = []
    delegated: list[BeginFactorObligation] = []
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
            BeginFactorCase(
                ordinal=ordinal,
                case_id=f"BEGIN{ordinal:05d}",
                sql_filename=f"BEGIN{ordinal:05d}.sql",
                object_prefix=f"begin_{ordinal:05d}_",
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
    plan = BeginFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 44 or len(plan.delegated) != 0:
        raise BeginFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 44:
        raise BeginFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 44:
        raise BeginFactorLoopError("duplicate SQL filename")
    return plan


def compile_begin_factor_loop_obligations(
    repository_root: Path,
) -> tuple[BeginFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        BeginFactorObligation(
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
    if len(rows) != 44:
        raise BeginFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise BeginFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 43}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise BeginFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise BeginFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 44:
        raise BeginFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise BeginFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "BeginFactorLoopError",
    "BeginGrammarAction",
    "BeginFactorObligation",
    "BeginFactorCase",
    "BeginFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_begin_factor_loop_obligations",
    "build_begin_factor_loop_plan",
    "_obligation_multiset_sha256",
]
