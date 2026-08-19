"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP COLLATION.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP COLLATION``.  ``drop_collation.yaml`` marks relation/table/column-type
coverage ``not_applicable``/``conditional`` (a collation DDL has no ``INV``
block), so the canonical SFV obligations are derived one-to-one from the
shipped applicability matrix: exactly 27 rows, one local obligation per row.

The official synopsis has a single branch (``DROP COLLATION [ IF EXISTS ]
name [ CASCADE | RESTRICT ]``); the grammar ledger freezes that one action
skeleton as a GRM obligation.  A RISK pair (commit/rollback) exercises the
transactional DDL boundary, mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP COLLATION`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropCollationFactorLoopError(ValueError):
    """Raised when a frozen DROP COLLATION obligation input drifts."""


@dataclass(frozen=True)
class DropCollationFactorObligation:
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
class DropCollationFactorCase:
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
class DropCollationFactorLoopPlan:
    obligations: tuple[DropCollationFactorObligation, ...]
    cases: tuple[DropCollationFactorCase, ...]
    delegated: tuple[DropCollationFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropcollation.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropcollation"

# The single official synopsis action form.  DROP COLLATION has no optional
# keyword / alternative axes beyond the synopsis, so the GRM ledger is exactly
# this one action skeleton.
@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_collation",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

# A representative branch (branch_1) used as the baseline consumer for
# statement-wide modifiers that are not bound to one sub-clause.
_REPRESENTATIVE_ACTION = "drop_collation"

# Canonical factor -> the action where the value is observable.  DROP
# COLLATION has a single synopsis branch, so every factor's consumer is the
# representative action.  statement_branch is resolved in
# :func:`_canonical_consumer` for symmetry with the sibling ledgers.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "collation_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "nonexistent_collation": _REPRESENTATIVE_ACTION,
    "dependent_objects_exist": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_1": "drop_collation",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  The DB doublerun fork
# calibrates the exact SQLSTATEs; the frozen counts and sha256s are the spec.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        # missing collation without IF EXISTS -> 42704
        ("object_state", "not_exists"),
        ("nonexistent_collation", "without_if_exists"),
        ("expected_status", "failure"),
        # dependent objects with RESTRICT -> 2BPQ1
        ("dependency_state", "referenced_by_table_column"),
        ("dependency_state", "referenced_by_index"),
        ("dependent_objects_exist", "restrict_with_dependencies"),
        # non-owner drop -> 42501
        ("privilege_level", "non_owner"),
        ("insufficient_privilege", "non_owner_drop"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropCollationFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropCollationFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropCollationFactorObligation]:
    rows: list[DropCollationFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropCollationFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DC-GRM|{action.grammar_branch_id}|"
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
        raise DropCollationFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropCollationFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_collation")
    if len(catalog_rows) != 27:
        raise DropCollationFactorLoopError("canonical obligation count drift")
    rows: list[DropCollationFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropCollationFactorObligation(
                ordinal=0,
                obligation_id=f"DC-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[DropCollationFactorObligation]:
    return [
        DropCollationFactorObligation(
            ordinal=0,
            obligation_id=f"DC-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropcollation:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropCollationFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-collation-factor-obligations-v1\n")
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
        "missing_collation_without_if_exists",
    ),
    ("nonexistent_collation", "without_if_exists"): (
        "42704",
        "missing_collation_without_if_exists",
    ),
    ("expected_status", "failure"): (
        "42704",
        "missing_collation_without_if_exists",
    ),
    ("dependency_state", "referenced_by_table_column"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_state", "referenced_by_index"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependent_objects_exist", "restrict_with_dependencies"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_collation_privilege",
    ),
    ("insufficient_privilege", "non_owner_drop"): (
        "42501",
        "insufficient_collation_privilege",
    ),
}


def _expected_failure_details(
    obligation: DropCollationFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropCollationFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: DropCollationFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "object_state": "already_exists_no_deps",
        "expected_status": "success",
        "if_exists_clause": "absent",
        "cascade_restrict": "RESTRICT_default",
        "dependency_state": "no_dependencies",
        "collation_name_shape": "plain_identifier",
        "privilege_level": "collation_owner",
        "nonexistent_collation": "without_if_exists",
        "dependent_objects_exist": "restrict_with_dependencies",
        "insufficient_privilege": "non_owner_drop",
        "verification_mode": "pg_collation_removed_assertion",
        "cleanup_mode": "DROP_COLLATION_CASCADE",
    }
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropCollationFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_collation_factor_loop_plan(
    repository_root: Path,
) -> DropCollationFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_collation_factor_loop_obligations(root)
    cases: list[DropCollationFactorCase] = []
    delegated: list[DropCollationFactorObligation] = []
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
            DropCollationFactorCase(
                ordinal=ordinal,
                case_id=f"DROPCOLLATION{ordinal:05d}",
                sql_filename=f"DROPCOLLATION{ordinal:05d}.sql",
                object_prefix=f"dropcollation_{ordinal:05d}_",
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
    plan = DropCollationFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 30 or len(plan.delegated) != 0:
        raise DropCollationFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 30:
        raise DropCollationFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 30:
        raise DropCollationFactorLoopError("duplicate SQL filename")
    return plan


def compile_drop_collation_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropCollationFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropCollationFactorObligation(
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
    if len(rows) != 30:
        raise DropCollationFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropCollationFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 27, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropCollationFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropCollationFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 30:
        raise DropCollationFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise DropCollationFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropCollationFactorLoopError",
    "DropCollationFactorObligation",
    "DropCollationFactorCase",
    "DropCollationFactorLoopPlan",
    "compile_drop_collation_factor_loop_obligations",
    "build_drop_collation_factor_loop_plan",
    "_obligation_multiset_sha256",
]
