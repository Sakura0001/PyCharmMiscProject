"""Factor-value-loop obligation ledger for PostgreSQL 18.4 SET TRANSACTION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``SET TRANSACTION`` — set the characteristics of the current transaction.
The official synopsis (``SET TRANSACTION transaction_mode [, ...]`` /
``SET TRANSACTION SNAPSHOT snapshot_id`` / ``SET SESSION CHARACTERISTICS
AS TRANSACTION transaction_mode [, ...]``) collapses to a single declared
grammar branch (``branch_1``), so there is a single ``GRM`` obligation.  The
43 canonical ``SFV`` factor-value pairs are hardcoded verbatim from the
canonical combination matrix ``set_transaction.yaml`` (the package binds
directly to the matrix, which is the source of truth); the universal
invariant is ``catalog_rows == factor_value_count == 43``.

SET TRANSACTION is a session/transaction-scoped TCL statement with no
privilege restriction: any role may execute any variant.  The only declared
failure surface is the meta-declared ``expected_status=failure`` (reason
``set_transaction_declared_failure``), provisionally mapped to SQLSTATE
``25001`` (``active_sql_transaction``) — SET TRANSACTION issued inside a
transaction block.  The remaining 42 ``SFV`` values plus the single ``GRM``
form are success-covered.

Each local obligation becomes exactly one regress program.  There are no
``INV`` (column/table) obligations and no ``RISK`` obligations.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import stable_catalog_row_id


class SetTransactionFactorLoopError(ValueError):
    """Raised when a frozen SET TRANSACTION obligation input drifts."""


@dataclass(frozen=True)
class SetTransactionGrammarAction:
    """One official target action form of the SET TRANSACTION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class SetTransactionFactorObligation:
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
class SetTransactionFactorCase:
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
class SetTransactionFactorLoopPlan:
    obligations: tuple[SetTransactionFactorObligation, ...]
    cases: tuple[SetTransactionFactorCase, ...]
    delegated: tuple[SetTransactionFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-set-transaction.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-set-transaction"

# The single representative action for all canonical factors.
_REPRESENTATIVE_ACTION = "set_transaction"

_STATEMENT_KEY = "set_transaction"

_MATRIX_PATH = (
    "skills/pg-sql-generation/references/combinations/tcl/transaction/"
    "set_transaction.yaml"
)
_REFERENCE_PATH = (
    "references/statements/tcl/transaction/set_transaction.md"
)

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1: _REPRESENTATIVE_ACTION,
}

# Canonical factor -> the action where the value is observable.  Since
# SET TRANSACTION has only one synopsis form, every factor observes on the
# single ``set_transaction`` action.
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

# Canonical (factor, value) pairs hardcoded verbatim from
# set_transaction.yaml.  factor_value_count == sum(len(values)) == 43
# across the 13 factors.
_CANONICAL_FACTOR_VALUES: tuple[tuple[str, str], ...] = (
    ("statement_branch", "branch_1"),
    ("expected_status", "success"),
    ("expected_status", "failure"),
    ("transaction_state", "outside_transaction"),
    ("transaction_state", "inside_transaction"),
    ("transaction_state", "savepoint_exists"),
    ("transaction_state", "prepared_transaction_exists"),
    ("transaction_state", "missing_required_state"),
    ("transaction_mode", "default"),
    ("transaction_mode", "isolation_level"),
    ("transaction_mode", "read_write"),
    ("transaction_mode", "read_only"),
    ("transaction_mode", "deferrable"),
    ("chain_behavior", "none"),
    ("chain_behavior", "and_chain"),
    ("chain_behavior", "and_no_chain"),
    ("transaction_id_shape", "simple_id"),
    ("transaction_id_shape", "quoted_id"),
    ("transaction_id_shape", "missing_id"),
    ("transaction_id_shape", "duplicate_id"),
    ("savepoint_name_shape", "simple_name"),
    ("savepoint_name_shape", "quoted_name"),
    ("savepoint_name_shape", "missing_name"),
    ("savepoint_name_shape", "released_name"),
    ("environment_context", "normal_session"),
    ("environment_context", "transaction_block"),
    ("environment_context", "outside_transaction_required"),
    ("environment_context", "external_resource_required"),
    ("framework_context", "no_outer_transaction"),
    ("framework_context", "outer_transaction_present"),
    ("invalid_combination", "none"),
    ("invalid_combination", "syntax_valid_semantic_error"),
    ("invalid_combination", "object_type_mismatch"),
    ("state_boundary", "no_open_transaction"),
    ("state_boundary", "nested_savepoint"),
    ("state_boundary", "prepared_transaction_leftover"),
    ("verification_mode", "catalog_query"),
    ("verification_mode", "effect_query"),
    ("verification_mode", "returned_rows"),
    ("verification_mode", "error_assertion"),
    ("cleanup_mode", "rollback"),
    ("cleanup_mode", "drop_objects"),
    ("cleanup_mode", "reset_state"),
)

_FACTOR_VALUE_COUNT = len(_CANONICAL_FACTOR_VALUES)

# Canonical (factor, value) pairs that reach the declared PostgreSQL
# failure surface (provisional sqlstates -- DB phase verifies on PG 18.4).
# SET TRANSACTION's only declared failure is the meta-declared
# expected_status=failure (reason set_transaction_declared_failure),
# provisionally mapped to SQLSTATE 25001 (active_sql_transaction).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "25001",
        "set_transaction_declared_failure",
    ),
}


def _load_grammar_actions() -> tuple[SetTransactionGrammarAction, ...]:
    """Freeze every SET TRANSACTION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "set_transaction",
            _BRANCH_1,
            "SET TRANSACTION transaction_mode [, ...]",
            "synopsis-set-transaction",
        ),
    )
    actions = [
        SetTransactionGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise SetTransactionFactorLoopError("set_transaction action count drift")
    return tuple(actions)


def _canonical_consumer(factor: str, value: str) -> str:
    """Map a canonical factor value to its target consumer action."""

    if factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[value]
        except KeyError as exc:
            raise SetTransactionFactorLoopError(
                f"unknown statement branch value: {value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[factor]
    except KeyError as exc:
        raise SetTransactionFactorLoopError(
            f"canonical factor has no consumer action: {factor}"
        ) from exc


def _compile_grammar_obligations() -> list[SetTransactionFactorObligation]:
    rows: list[SetTransactionFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            SetTransactionFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"SETTRANSACTION-GRM|{action.grammar_branch_id}|"
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
        raise SetTransactionFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations() -> list[SetTransactionFactorObligation]:
    """Hardcoded SFV obligations verbatim from set_transaction.yaml."""

    if _FACTOR_VALUE_COUNT != 43:
        raise SetTransactionFactorLoopError("canonical factor value count drift")
    rows: list[SetTransactionFactorObligation] = []
    for factor, value in _CANONICAL_FACTOR_VALUES:
        consumer = _canonical_consumer(factor, value)
        is_failure = (factor, value) in _SFV_FAILURE_VALUES
        row_id = stable_catalog_row_id(_STATEMENT_KEY, factor, value)
        rows.append(
            SetTransactionFactorObligation(
                ordinal=0,
                obligation_id=f"SETTRANSACTION-SFV|{row_id}|{consumer}",
                kind="SFV",
                factor_key=factor,
                value=value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=f"{_REFERENCE_PATH}#{row_id}",
            )
        )
    return rows


def _obligation_multiset_sha256(
    rows: tuple[SetTransactionFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"set-transaction-factor-obligations-v1\n")
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
    "set_transaction": _BRANCH_1,
}

# Dense baseline defaults (all positive T1-T6 factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "grammar_branch": _BRANCH_1,
    "target_action": "set_transaction",
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
    """Reconcile expected_status with the declared failure surface.

    SET TRANSACTION's only declared failure trigger is
    ``expected_status=failure`` (a meta-declared factor, not a physical
    axis that combines with others).  There is therefore no overlapping
    pair to cross-derive; the caller reconciles ``expected_status`` from
    the failure-unit count.  This hook is retained to mirror the reset
    ledger structure.
    """

    return None


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: SetTransactionFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
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
        raise SetTransactionFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: SetTransactionFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise SetTransactionFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_set_transaction_factor_loop_plan(
    repository_root: Path,
) -> SetTransactionFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_set_transaction_factor_loop_obligations(root)
    cases: list[SetTransactionFactorCase] = []
    delegated: list[SetTransactionFactorObligation] = []
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
            SetTransactionFactorCase(
                ordinal=ordinal,
                case_id=f"SETTRANSACTION{ordinal:05d}",
                sql_filename=f"SETTRANSACTION{ordinal:05d}.sql",
                object_prefix=f"settransaction_{ordinal:05d}_",
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
    plan = SetTransactionFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 44 or len(plan.delegated) != 0:
        raise SetTransactionFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 44
    ):
        raise SetTransactionFactorLoopError("local obligation mapping drift")
    if (
        len({row.sql_filename for row in plan.cases}) != 44
    ):
        raise SetTransactionFactorLoopError("duplicate SQL filename")
    return plan


def compile_set_transaction_factor_loop_obligations(
    repository_root: Path,
) -> tuple[SetTransactionFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    if not (root / _MATRIX_PATH).is_file():
        raise SetTransactionFactorLoopError(
            f"canonical matrix is missing for set_transaction: {_MATRIX_PATH}"
        )
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations()
    )
    rows = tuple(
        SetTransactionFactorObligation(
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
        raise SetTransactionFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise SetTransactionFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 43}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise SetTransactionFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise SetTransactionFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 44:
        raise SetTransactionFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise SetTransactionFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "SetTransactionFactorLoopError",
    "SetTransactionGrammarAction",
    "SetTransactionFactorObligation",
    "SetTransactionFactorCase",
    "SetTransactionFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_FACTOR_VALUE_COUNT",
    "_CANONICAL_FACTOR_VALUES",
    "compile_set_transaction_factor_loop_obligations",
    "build_set_transaction_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
