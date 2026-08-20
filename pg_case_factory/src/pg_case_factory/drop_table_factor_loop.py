"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP TABLE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP TABLE``.  A ``DROP TABLE`` DDL has no ``INV`` block, so the canonical
SFV obligations are derived one-to-one from the shipped applicability
matrix: exactly 47 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP TABLE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.
A RISK pair (commit/rollback) exercises the transactional DDL boundary,
mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP TABLE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropTableFactorLoopError(ValueError):
    """Raised when a frozen DROP TABLE obligation input drifts."""


@dataclass(frozen=True)
class DropTableFactorObligation:
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
class DropTableFactorCase:
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
class DropTableFactorLoopPlan:
    obligations: tuple[DropTableFactorObligation, ...]
    cases: tuple[DropTableFactorCase, ...]
    delegated: tuple[DropTableFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-droptable.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-droptable"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_table",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_table"

# Every canonical factor maps to the single DROP TABLE consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "table_type_permanence": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "multi_table_drop": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "error_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_table": "drop_table",
    "branch_drop_table_if_exists": "drop_table",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  privilege_level=
# non_owner inherently fails (42501) because DROP TABLE requires ownership.
# object_state=not_exists inherently errors (42P01) when IF EXISTS is omitted.
# table_name_shape=non_existent surfaces a 42P01 because the target name is
# not found.  dependency_state=has_views / has_fk_references fire 2BP01 under
# RESTRICT (or default RESTRICT) because dependent objects block the drop.
# error_boundary values describe the same failure boundaries; the renderer
# co-derives the matching causative factor.  Kept minimal (Option-A
# marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("privilege_level", "non_owner"),
        ("object_state", "not_exists"),
        ("table_name_shape", "non_existent"),
        ("dependency_state", "has_views"),
        ("dependency_state", "has_fk_references"),
        ("error_boundary", "non_existent_without_if_exists"),
        ("error_boundary", "dependent_objects_without_cascade"),
        ("error_boundary", "insufficient_privilege"),
        ("error_boundary", "drop_table_in_use"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropTableFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropTableFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _consumer_branch_map() -> dict[str, str]:
    return {
        action.action_id: action.grammar_branch_id
        for action in _GRAMMAR_ACTIONS
    }


def _renderer_factor_key(factor_key: str) -> str:
    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


def _compile_grammar_obligations() -> list[DropTableFactorObligation]:
    rows: list[DropTableFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropTableFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTABLE-GRM|{action.grammar_branch_id}|"
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
        raise DropTableFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropTableFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_table")
    if len(catalog_rows) != 47:
        raise DropTableFactorLoopError("canonical obligation count drift")
    rows: list[DropTableFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropTableFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTABLE-SFV|{row.row_id}|{consumer}"
                ),
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


def _compile_risk_obligations() -> list[DropTableFactorObligation]:
    return [
        DropTableFactorObligation(
            ordinal=0,
            obligation_id=f"DROPTABLE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-droptable:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropTableFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-table-factor-obligations-v1\n")
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
# value.  The frozen counts and sha256s in the companion tests are the spec.
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks ten
# pairs as expected_failure, but the bounded extension crosses privilege,
# object-state (table-missing), and dependency negatives whose SQLSTATEs are
# resolved here too.  SQLSTATEs are provisional in the no-DB phase (a later
# DB phase verifies on PG18.4).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "table_missing_without_if_exists",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_drop_privilege",
    ),
    ("object_state", "not_exists"): (
        "42P01",
        "undefined_table_missing",
    ),
    ("table_name_shape", "non_existent"): (
        "42P01",
        "undefined_table_name",
    ),
    ("dependency_state", "has_views"): (
        "2BP01",
        "dependent_objects_block_restrict",
    ),
    ("dependency_state", "has_fk_references"): (
        "2BP01",
        "dependent_objects_block_restrict",
    ),
    ("error_boundary", "non_existent_without_if_exists"): (
        "42P01",
        "table_missing_without_if_exists",
    ),
    ("error_boundary", "dependent_objects_without_cascade"): (
        "2BP01",
        "dependent_objects_block_restrict",
    ),
    ("error_boundary", "insufficient_privilege"): (
        "42501",
        "insufficient_drop_privilege",
    ),
    ("error_boundary", "drop_table_in_use"): (
        "55006",
        "object_in_use",
    ),
}


def _expected_failure_details(
    obligation: DropTableFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropTableFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "absent" (the raw DROP TABLE form without IF EXISTS) and cascade_restrict is
# "none" (RESTRICT is the default behavior when omitted).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_table",
    "grammar_branch": "branch_1",
    "target_action": "drop_table",
    "object_state": "exists_permanent",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "table_type_permanence": "permanent",
    "table_name_shape": "simple",
    "multi_table_drop": "single_table",
    "privilege_level": "owner",
    "dependency_state": "no_dependents",
    "error_boundary": "none",
    "verification_mode": "pg_class_query",
    "cleanup_mode": "cascade_cleanup",
}

# Baseline primaries whose target table is intentionally absent, so the DROP
# surfaces a not-found error (42P01) and the oracle asserts absence.
_ABSENT_TABLE_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("error_boundary", "non_existent_without_if_exists"),
    }
)

# Baseline primaries that imply a dependent-object fixture must be created.
_DEPENDENCY_FAILURE_PRIMARIES = frozenset(
    {
        ("dependency_state", "has_views"),
        ("dependency_state", "has_fk_references"),
        ("error_boundary", "dependent_objects_without_cascade"),
    }
)

# Baseline primaries that imply a non-owner role fixture.
_PRIVILEGE_FAILURE_PRIMARIES = frozenset(
    {
        ("privilege_level", "non_owner"),
        ("error_boundary", "insufficient_privilege"),
    }
)

# Baseline primaries that simulate a table-in-use boundary.
_IN_USE_PRIMARIES = frozenset(
    {
        ("error_boundary", "drop_table_in_use"),
    }
)


def _baseline_assignments(
    obligation: DropTableFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_TABLE_PRIMARIES:
        assignments["object_state"] = "not_exists"
        assignments["if_exists_clause"] = "absent"
    if (obligation.factor_key, obligation.value) in _DEPENDENCY_FAILURE_PRIMARIES:
        if obligation.factor_key == "error_boundary":
            assignments["dependency_state"] = "has_views"
    if (obligation.factor_key, obligation.value) in _PRIVILEGE_FAILURE_PRIMARIES:
        if obligation.factor_key == "error_boundary":
            assignments["privilege_level"] = "non_owner"
    if obligation.factor_key == "statement_branch":
        # statement_branch=branch_drop_table_if_exists implies IF EXISTS present.
        if obligation.value == "branch_drop_table_if_exists":
            assignments["if_exists_clause"] = "present"
    if len(assignments) != len(set(assignments)):
        raise DropTableFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_table_factor_loop_plan(
    repository_root: Path,
) -> DropTableFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_table_factor_loop_obligations(root)
    cases: list[DropTableFactorCase] = []
    delegated: list[DropTableFactorObligation] = []
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
            DropTableFactorCase(
                ordinal=ordinal,
                case_id=f"DROPTABLE{ordinal:05d}",
                sql_filename=f"DROPTABLE{ordinal:05d}.sql",
                object_prefix=f"droptable_{ordinal:05d}_",
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
    plan = DropTableFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 50 or len(plan.delegated) != 0:
        raise DropTableFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 50
    ):
        raise DropTableFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 50:
        raise DropTableFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropTableFactorLoopPlan] = {}


def _build_drop_table_factor_plan_lazily(
    repository_root: Path,
) -> DropTableFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_table_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_table_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropTableFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropTableFactorObligation(
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
        raise DropTableFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropTableFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 47, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropTableFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropTableFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 50:
        raise DropTableFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropTableFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropTableFactorLoopError",
    "DropTableFactorObligation",
    "DropTableFactorCase",
    "DropTableFactorLoopPlan",
    "compile_drop_table_factor_loop_obligations",
    "build_drop_table_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_table_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
