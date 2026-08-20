"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ROLLBACK PREPARED.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ROLLBACK PREPARED``.  ROLLBACK PREPARED is a PostgreSQL two-phase
transaction control statement that rolls back a transaction earlier
prepared for two-phase commit.  The official synopsis has exactly one
branch (``ROLLBACK PREPARED transaction_id``), so there is a single
``GRM`` obligation.  The 43 canonical ``SFV`` rows are loaded from the
shipped applicability universe (``postgresql_18_4_factor_audit.tsv``).

ROLLBACK PREPARED reaches several PostgreSQL error surfaces.  Six
canonical factor values reach the target check and are rejected
(provisional sqlstates -- a later DB phase verifies on PG 18.4):

* ``expected_status=failure`` -- declared meta-failure mapped to the
  primary surface (prepared transaction does not exist, 42704).
* ``transaction_state=missing_required_state`` -- no prepared
  transaction exists for the supplied identifier (42704).
* ``transaction_state=inside_transaction`` -- ROLLBACK PREPARED cannot
  run inside a transaction block (25001).
* ``transaction_state=savepoint_exists`` -- a savepoint implies an open
  transaction block, which blocks ROLLBACK PREPARED (25001).
* ``transaction_id_shape=missing_id`` -- the transaction identifier is
  syntactically absent (42601).
* ``invalid_combination=syntax_valid_semantic_error`` -- a well-formed
  statement rejected for a semantic reason (the prepared transaction
  does not exist, 42704).

All other 37 ``SFV`` values plus the single ``GRM`` branch are
success-covered.  There are no ``RISK`` obligations (ROLLBACK PREPARED
has no ``transaction_outcome`` factor).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class RollbackPreparedFactorLoopError(ValueError):
    """Raised when a frozen ROLLBACK PREPARED obligation input drifts."""


@dataclass(frozen=True)
class RollbackPreparedGrammarAction:
    """One official target action form of the ROLLBACK PREPARED synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class RollbackPreparedFactorObligation:
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
class RollbackPreparedFactorCase:
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
class RollbackPreparedFactorLoopPlan:
    obligations: tuple[RollbackPreparedFactorObligation, ...]
    cases: tuple[RollbackPreparedFactorCase, ...]
    delegated: tuple[RollbackPreparedFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-rollback-prepared.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-rollback-prepared"

# The single representative action for all canonical factors.  ROLLBACK
# PREPARED has only one synopsis form, so every factor observes on the
# single ``rollback_prepared`` action.
_REPRESENTATIVE_ACTION = "rollback_prepared"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1: "rollback_prepared",
}

# Canonical factor -> the action where the value is observable.  Since
# ROLLBACK PREPARED has only one synopsis form, every factor observes
# on the single ``rollback_prepared`` action.
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

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("transaction_state", "missing_required_state"),
        ("transaction_state", "inside_transaction"),
        ("transaction_state", "savepoint_exists"),
        ("transaction_id_shape", "missing_id"),
        ("invalid_combination", "syntax_valid_semantic_error"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "prepared_transaction_does_not_exist_provisional",
    ),
    ("transaction_state", "missing_required_state"): (
        "42704",
        "prepared_transaction_does_not_exist_provisional",
    ),
    ("transaction_state", "inside_transaction"): (
        "25001",
        "active_sql_transaction_provisional",
    ),
    ("transaction_state", "savepoint_exists"): (
        "25001",
        "active_sql_transaction_provisional",
    ),
    ("transaction_id_shape", "missing_id"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42704",
        "prepared_transaction_does_not_exist_provisional",
    ),
}


def _load_grammar_actions() -> tuple[RollbackPreparedGrammarAction, ...]:
    """Freeze every ROLLBACK PREPARED synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "rollback_prepared",
            _BRANCH_1,
            "ROLLBACK PREPARED transaction_id",
            "synopsis-rollback-prepared",
        ),
    )
    actions = [
        RollbackPreparedGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise RollbackPreparedFactorLoopError(
            "rollback prepared action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise RollbackPreparedFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise RollbackPreparedFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[RollbackPreparedFactorObligation]:
    rows: list[RollbackPreparedFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            RollbackPreparedFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ROLLBACKPREPARED-GRM|{action.grammar_branch_id}|"
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
        raise RollbackPreparedFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[RollbackPreparedFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("rollback_prepared")
    if len(catalog_rows) != 43:
        raise RollbackPreparedFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[RollbackPreparedFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            RollbackPreparedFactorObligation(
                ordinal=0,
                obligation_id=f"ROLLBACKPREPARED-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[RollbackPreparedFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"rollback-prepared-factor-obligations-v1\n"
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
    "rollback_prepared": _BRANCH_1,
}

# Dense baseline defaults (all positive T1-T6 factor values).  The single
# synopsis branch means statement_branch / grammar_branch / target_action
# are always branch_1 / rollback_prepared.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "grammar_branch": _BRANCH_1,
    "target_action": "rollback_prepared",
    "expected_status": "success",
    "transaction_state": "prepared_transaction_exists",
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
    """Derive the no-prepared-transaction failure cluster and expected_status.

    ROLLBACK PREPARED's reachable failure surfaces cluster around three
    overlapping notions of the same "no rollback-able prepared transaction"
    boundary: ``expected_status=failure`` (declared meta-failure),
    ``invalid_combination=syntax_valid_semantic_error`` (semantic error),
    and ``transaction_state=missing_required_state`` (no prepared
    transaction exists).  When the primary is one of these, the others are
    derived so the baseline assignment is self-consistent and the render
    produces SQL that reaches the 42704 surface.  The distinct
    ``inside_transaction`` / ``savepoint_exists`` (25001) and
    ``transaction_id_shape=missing_id`` (42601) surfaces are left untouched
    so their distinct semantics survive.
    """

    ts = a.get("transaction_state", "prepared_transaction_exists")
    ic = a.get("invalid_combination", "none")
    es = a.get("expected_status", "success")
    tid = a.get("transaction_id_shape", "simple_id")

    explicit_ts_failure = ts in (
        "inside_transaction",
        "savepoint_exists",
        "missing_required_state",
    )
    has_missing_id = tid == "missing_id"

    # Cluster: no-prepared-transaction semantic failure.  Fires only when
    # the primary is expected_status=failure or invalid_combination (and no
    # other explicit failure is already set), so it never clobbers the
    # distinct inside_transaction / savepoint_exists / missing_id surfaces.
    if not explicit_ts_failure and not has_missing_id:
        if es == "failure" or ic == "syntax_valid_semantic_error":
            a["transaction_state"] = "missing_required_state"
            if ic != "syntax_valid_semantic_error":
                a["invalid_combination"] = "syntax_valid_semantic_error"
    # When transaction_state is explicitly missing_required_state, mark the
    # semantic-error side so the assignment stays self-consistent.
    if a.get("transaction_state") == "missing_required_state":
        a["invalid_combination"] = "syntax_valid_semantic_error"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: RollbackPreparedFactorObligation,
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
        raise RollbackPreparedFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: RollbackPreparedFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise RollbackPreparedFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_rollback_prepared_factor_loop_plan(
    repository_root: Path,
) -> RollbackPreparedFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_rollback_prepared_factor_loop_obligations(root)
    cases: list[RollbackPreparedFactorCase] = []
    delegated: list[RollbackPreparedFactorObligation] = []
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
            RollbackPreparedFactorCase(
                ordinal=ordinal,
                case_id=f"ROLLBACKPREPARED{ordinal:05d}",
                sql_filename=f"ROLLBACKPREPARED{ordinal:05d}.sql",
                object_prefix=(
                    f"rollbackprepared_{ordinal:05d}_"
                ),
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
    plan = RollbackPreparedFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 44 or len(plan.delegated) != 0:
        raise RollbackPreparedFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 44:
        raise RollbackPreparedFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 44:
        raise RollbackPreparedFactorLoopError("duplicate SQL filename")
    return plan


def compile_rollback_prepared_factor_loop_obligations(
    repository_root: Path,
) -> tuple[RollbackPreparedFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        RollbackPreparedFactorObligation(
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
        raise RollbackPreparedFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise RollbackPreparedFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 43}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise RollbackPreparedFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise RollbackPreparedFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 44:
        raise RollbackPreparedFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise RollbackPreparedFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "RollbackPreparedFactorLoopError",
    "RollbackPreparedGrammarAction",
    "RollbackPreparedFactorObligation",
    "RollbackPreparedFactorCase",
    "RollbackPreparedFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_rollback_prepared_factor_loop_obligations",
    "build_rollback_prepared_factor_loop_plan",
    "_obligation_multiset_sha256",
]
