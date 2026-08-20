"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP DATABASE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP DATABASE``.  ``drop_database.yaml`` marks relation/table/column-type
coverage ``not_applicable`` (a database DDL has no ``INV`` block), so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 47 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP DATABASE [ IF EXISTS ] name [ WITH ( FORCE ) ]``); the grammar ledger
freezes that one action skeleton as a GRM obligation.  A RISK pair
(commit/rollback) exercises the transactional DDL boundary, mirroring the
sibling DROP statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP DATABASE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropDatabaseFactorLoopError(ValueError):
    """Raised when a frozen DROP DATABASE obligation input drifts."""


@dataclass(frozen=True)
class DropDatabaseFactorObligation:
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
class DropDatabaseFactorCase:
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
class DropDatabaseFactorLoopPlan:
    obligations: tuple[DropDatabaseFactorObligation, ...]
    cases: tuple[DropDatabaseFactorCase, ...]
    delegated: tuple[DropDatabaseFactorObligation, ...]
    obligation_multiset_sha256: str


# The statement abbreviation used as the obligation-id and case-id prefix.
_ABBREV = "DROPDATABASE"

# Official synopsis branch (PostgreSQL 18 sql-dropdatabase.html).
_BRANCH_DROP_DATABASE = "branch_drop_database"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropdatabase"

# The single official synopsis action form.  DROP DATABASE has no optional
# keyword / alternative axes beyond the synopsis, so the GRM ledger is exactly
# this one action skeleton.
@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_database",
        grammar_branch_id=_BRANCH_DROP_DATABASE,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

# A representative branch used as the baseline consumer for statement-wide
# modifiers that are not bound to one sub-clause.
_REPRESENTATIVE_ACTION = "drop_database"

# Canonical failure (factor, value) -> the consumer action where the value is
# observable.  These are the minimal baseline expected-failure triggers
# (Option-A marginal): the declared ``expected_status == failure`` meta-factor
# plus the three canonical values that inherently error on PG 18.4 — dropping
# the currently-open database, running inside a transaction block, and a
# non-owner drop.  All remaining cross-product failures are exercised by the
# bounded post-coverage extension module.
_FAILURE_CONSUMERS: dict[tuple[str, str], str] = {
    ("expected_status", "failure"): "drop_database_declared_failure",
    ("drop_current_database", "current_database"): (
        "drop_database_current_db_error"
    ),
    ("inside_transaction_block", "inside_transaction"): (
        "drop_database_txn_error"
    ),
    ("privilege_level", "non_owner"): "drop_database_insufficient_priv",
}


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action.

    Uses ``row.factor`` / ``row.value`` directly (no hardcoded factor list,
    no stable-id derivation).  ``statement_branch`` is validated; every
    other factor falls through to the representative action unless it is a
    baseline expected-failure value, in which case it receives a specific
    failure consumer.
    """

    if row.factor == "statement_branch":
        if row.value == _BRANCH_DROP_DATABASE:
            return _REPRESENTATIVE_ACTION
        raise DropDatabaseFactorLoopError(
            f"unknown statement branch value: {row.value}"
        )
    return _FAILURE_CONSUMERS.get(
        (row.factor, row.value), _REPRESENTATIVE_ACTION
    )


# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  The yaml declares a
# single failure condition (``expected_status == failure``); the minimal
# baseline additionally marks three inherently-erroring canonical values.  The
# DB doublerun fork calibrates the exact SQLSTATEs; the frozen counts and
# sha256s are the spec.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("drop_current_database", "current_database"),
        ("inside_transaction_block", "inside_transaction"),
        ("privilege_level", "non_owner"),
    }
)


# Best-effort PG 18.4 SQLSTATE attribution for each reachable expected-failure
# value.  This table is a superset of ``_SFV_FAILURE_VALUES``: the baseline
# only marks four pairs as expected_failure, but the bounded extension crosses
# additional failure axes (object-in-use, undefined-database) whose SQLSTATEs
# are resolved here too so the extension module can attribute without a second
# lookup table.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_database_declared_failure",
    ),
    ("drop_current_database", "current_database"): (
        "0A000",
        "cannot_drop_current_database_provisional",
    ),
    ("inside_transaction_block", "inside_transaction"): (
        "25001",
        "active_sql_transaction",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege",
    ),
    ("database_not_exist_no_if_exists", "database_not_exists_no_if_exists"): (
        "42704",
        "undefined_database",
    ),
    ("connection_state", "has_other_connections"): (
        "55006",
        "object_in_use",
    ),
    ("prepared_transactions", "has_prepared_transactions"): (
        "55006",
        "object_in_use_prepared_transactions",
    ),
    ("replication_slots", "has_active_slots"): (
        "55006",
        "object_in_use_replication_slot",
    ),
    ("subscriptions", "has_subscriptions"): (
        "55006",
        "object_in_use_subscription",
    ),
}


def _load_grammar_actions() -> tuple[_GrammarAction, ...]:
    if len(_GRAMMAR_ACTIONS) != 1:
        raise DropDatabaseFactorLoopError("grammar action count drift")
    return _GRAMMAR_ACTIONS


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


def _compile_grammar_obligations() -> list[DropDatabaseFactorObligation]:
    rows: list[DropDatabaseFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            DropDatabaseFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"{_ABBREV}-GRM|{action.grammar_branch_id}|"
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
        raise DropDatabaseFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropDatabaseFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_database")
    if len(catalog_rows) != 47:
        raise DropDatabaseFactorLoopError("canonical obligation count drift")
    rows: list[DropDatabaseFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropDatabaseFactorObligation(
                ordinal=0,
                obligation_id=f"{_ABBREV}-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[DropDatabaseFactorObligation]:
    return [
        DropDatabaseFactorObligation(
            ordinal=0,
            obligation_id=f"{_ABBREV}-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropdatabase:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropDatabaseFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-database-factor-obligations-v1\n")
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


# Dense baseline defaults (all positive factor values) for the 21 catalog
# factors of ``drop_database``.  Each baseline assignment overrides exactly one
# key with the obligation's primary value, then derives ``expected_status``.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_database",
    "object_state": "exists",
    "expected_status": "success",
    "connection_state": "no_other_connections",
    "force_option": "omitted",
    "if_exists_clause": "omitted",
    "database_name_shape": "simple_id",
    "database_not_exist_no_if_exists": "database_exists",
    "drop_current_database": "different_database",
    "inside_transaction_block": "outside_transaction",
    "prepared_transactions": "no_prepared_transactions",
    "privilege_level": "superuser",
    "privilege_denied": "superuser_success",
    "replication_slots": "no_active_slots",
    "subscriptions": "no_subscriptions",
    "active_connections": "no_active_connections",
    "active_connections_without_force": "no_connections_or_force_used",
    "connected_to_target_database": "connected_to_different_database",
    "force_with_unterminable_connections": "all_connections_terminable",
    "cleanup_mode": "drop_database_simple",
    "verification_mode": "catalog_query_pg_database_absence",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive ``expected_status`` from the baseline failure count.

    DROP DATABASE has no multi-factor overlap clusters that require derivation
    beyond ``expected_status``.  ``privilege_denied`` is held at its baseline
    default and only overridden when it is the primary; the renderer reads
    ``privilege_level`` (not ``privilege_denied``) for the role fixture, so no
    cross-derivation is needed for byte-deterministic rendering.
    """

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: DropDatabaseFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides.

    DROP DATABASE has a single official synopsis branch, so every consumer
    (including the failure consumers) maps to the same grammar branch and the
    same synopsis target action.  ``target_action`` is held at the
    representative action (not the failure consumer) so the baseline and the
    bounded extension share the same ``target_action`` value and the coverage
    witness stays gap-free.
    """

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _BRANCH_DROP_DATABASE
    assignments["target_action"] = _REPRESENTATIVE_ACTION
    assignments[_renderer_factor_key(obligation.factor_key)] = (
        obligation.value
    )
    _derive_overlapping_factors(assignments)
    # Re-assert the primary after derivation so the primary value survives any
    # overlap derivation (``expected_status`` derivation never touches the
    # primary key, but this guards against future overlap clusters).
    assignments[_renderer_factor_key(obligation.factor_key)] = (
        obligation.value
    )
    if len(assignments) != len(set(assignments)):
        raise DropDatabaseFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: DropDatabaseFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise DropDatabaseFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_drop_database_factor_loop_plan(
    repository_root: Path,
) -> DropDatabaseFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_database_factor_loop_obligations(root)
    cases: list[DropDatabaseFactorCase] = []
    delegated: list[DropDatabaseFactorObligation] = []
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
            DropDatabaseFactorCase(
                ordinal=ordinal,
                case_id=f"{_ABBREV}{ordinal:05d}",
                sql_filename=f"{_ABBREV}{ordinal:05d}.sql",
                object_prefix=f"dropdatabase_{ordinal:05d}_",
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
    plan = DropDatabaseFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 50 or len(plan.delegated) != 0:
        raise DropDatabaseFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 50:
        raise DropDatabaseFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 50:
        raise DropDatabaseFactorLoopError("duplicate SQL filename")
    return plan


def compile_drop_database_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropDatabaseFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropDatabaseFactorObligation(
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
    if len(rows) != 50:
        raise DropDatabaseFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropDatabaseFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 47, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropDatabaseFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropDatabaseFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 50:
        raise DropDatabaseFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise DropDatabaseFactorLoopError("unknown obligation disposition")
    return rows


_PLAN_CACHE: dict[Path, DropDatabaseFactorLoopPlan] = {}


def _build_drop_database_factor_plan_lazily(
    repository_root: Path,
) -> DropDatabaseFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_database_factor_loop_plan(root)
    return _PLAN_CACHE[root]


__all__ = [
    "DropDatabaseFactorLoopError",
    "DropDatabaseFactorObligation",
    "DropDatabaseFactorCase",
    "DropDatabaseFactorLoopPlan",
    "compile_drop_database_factor_loop_obligations",
    "build_drop_database_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_database_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
