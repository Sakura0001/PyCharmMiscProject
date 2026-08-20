"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP CAST.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP CAST``.  ``drop_cast.yaml`` marks relation/table/column-type
coverage ``not_applicable``/``representative`` (a cast DDL has no ``INV``
block), so the canonical SFV obligations are derived one-to-one from the
shipped applicability matrix: exactly 41 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP CAST [ IF EXISTS ] (source_type AS target_type)
[ CASCADE | RESTRICT ]``); the grammar ledger freezes that one action
skeleton as a GRM obligation.  A RISK pair (commit/rollback) exercises the
transactional DDL boundary, mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP CAST`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropCastFactorLoopError(ValueError):
    """Raised when a frozen DROP CAST obligation input drifts."""


@dataclass(frozen=True)
class DropCastFactorObligation:
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
class DropCastFactorCase:
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
class DropCastFactorLoopPlan:
    obligations: tuple[DropCastFactorObligation, ...]
    cases: tuple[DropCastFactorCase, ...]
    delegated: tuple[DropCastFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropcast.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropcast"

# The single official synopsis action form.  DROP CAST has no optional
# keyword / alternative axes beyond the synopsis, so the GRM ledger is
# exactly this one action skeleton.
@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_cast",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

# A representative branch (branch_1) used as the baseline consumer for
# statement-wide modifiers that are not bound to one sub-clause.
_REPRESENTATIVE_ACTION = "drop_cast"

# Canonical factor -> the action where the value is observable.  DROP CAST
# has a single synopsis branch, so every factor's consumer is the
# representative action.  statement_branch is resolved in
# :func:`_canonical_consumer` for symmetry with the sibling ledgers.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "source_type": _REPRESENTATIVE_ACTION,
    "target_type": _REPRESENTATIVE_ACTION,
    "source_type_shape": _REPRESENTATIVE_ACTION,
    "target_type_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "type_ownership": _REPRESENTATIVE_ACTION,
    "nonexistent_cast": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "reverse_direction_cast": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_1": "drop_cast",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  The DB doublerun
# fork calibrates the exact SQLSTATEs; the frozen counts and sha256s are the
# spec.  Derived from ``drop_cast.yaml`` ``failure_when``:
#   * object_state == not_exists and if_exists_clause == absent
#       -> cast_does_not_exist (42704)
#   * privilege_level == non_owner or type_ownership == owns_neither or
#     insufficient_privilege == owns_no_type -> insufficient_cast_privilege
#     (42501)
# ``expected_status == failure`` is the status-axis marker for the
# missing-cast boundary; ``nonexistent_cast == without_if_exists`` is the
# explicit negative-boundary marker for the same 42704 boundary.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        # missing cast without IF EXISTS -> 42704
        ("object_state", "not_exists"),
        ("nonexistent_cast", "without_if_exists"),
        ("expected_status", "failure"),
        # non-owner / owns-neither drop -> 42501
        ("privilege_level", "non_owner"),
        ("type_ownership", "owns_neither"),
        ("insufficient_privilege", "owns_no_type"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropCastFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropCastFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _consumer_branch_map() -> dict[str, str]:
    return {
        action.action_id: action.grammar_branch_id
        for action in _GRAMMAR_ACTIONS
    }


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


def _compile_grammar_obligations() -> list[DropCastFactorObligation]:
    rows: list[DropCastFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropCastFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DCAST-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|{action.action_id}"
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
        raise DropCastFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropCastFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_cast")
    if len(catalog_rows) != 41:
        raise DropCastFactorLoopError("canonical obligation count drift")
    rows: list[DropCastFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropCastFactorObligation(
                ordinal=0,
                obligation_id=f"DCAST-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure"
                    if (row.factor, row.value) in _SFV_FAILURE_VALUES
                    else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _compile_risk_obligations() -> list[DropCastFactorObligation]:
    return [
        DropCastFactorObligation(
            ordinal=0,
            obligation_id=f"DCAST-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropcast:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropCastFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-cast-factor-obligations-v1\n")
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
                    "delegated_statement_key": row.delegated_statement_key,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Best-effort PG 18.4 SQLSTATE attribution for each reachable expected-failure
# value.  The DB doublerun fork calibrates these via a two-run comparison; the
# frozen counts and sha256s in the companion tests are the spec.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("object_state", "not_exists"): (
        "42704",
        "cast_does_not_exist",
    ),
    ("nonexistent_cast", "without_if_exists"): (
        "42704",
        "cast_does_not_exist",
    ),
    ("expected_status", "failure"): (
        "42704",
        "cast_does_not_exist",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_cast_privilege",
    ),
    ("type_ownership", "owns_neither"): (
        "42501",
        "insufficient_cast_privilege",
    ),
    ("insufficient_privilege", "owns_no_type"): (
        "42501",
        "insufficient_cast_privilege",
    ),
}


def _expected_failure_details(
    obligation: DropCastFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropCastFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: DropCastFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides.

    ``source_type`` / ``target_type`` default to ``custom_type`` so the
    fixture cast is always a fresh, prefix-named cast (never a built-in
    catalog cast).  This keeps every DROP CAST non-destructive and the
    two-run comparison idempotent: the cast dropped is one the fixture
    created, never a shipped system cast.
    """

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "statement_branch": "branch_1",
        "object_state": "already_exists",
        "expected_status": "success",
        "if_exists_clause": "absent",
        "cascade_restrict": "RESTRICT_default",
        "source_type": "custom_type",
        "target_type": "custom_type",
        "source_type_shape": "plain_type",
        "target_type_shape": "plain_type",
        "privilege_level": "type_owner_source",
        "type_ownership": "owns_source",
        "nonexistent_cast": "without_if_exists",
        "insufficient_privilege": "owns_no_type",
        "reverse_direction_cast": "reverse_still_exists",
        "verification_mode": "pg_cast_catalog_query",
        "cleanup_mode": "DROP_CAST_IF_EXISTS",
    }
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropCastFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_cast_factor_loop_plan(
    repository_root: Path,
) -> DropCastFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_cast_factor_loop_obligations(root)
    cases: list[DropCastFactorCase] = []
    delegated: list[DropCastFactorObligation] = []
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
            DropCastFactorCase(
                ordinal=ordinal,
                case_id=f"DROPCAST{ordinal:05d}",
                sql_filename=f"DROPCAST{ordinal:05d}.sql",
                object_prefix=f"dropcast_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=_renderer_factor_key(obligation.factor_key),
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = DropCastFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 44 or len(plan.delegated) != 0:
        raise DropCastFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 44:
        raise DropCastFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 44:
        raise DropCastFactorLoopError("duplicate SQL filename")
    return plan


def compile_drop_cast_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropCastFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropCastFactorObligation(
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
        raise DropCastFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropCastFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 41, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropCastFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropCastFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 44:
        raise DropCastFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise DropCastFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropCastFactorLoopError",
    "DropCastFactorObligation",
    "DropCastFactorCase",
    "DropCastFactorLoopPlan",
    "compile_drop_cast_factor_loop_obligations",
    "build_drop_cast_factor_loop_plan",
    "_obligation_multiset_sha256",
]
