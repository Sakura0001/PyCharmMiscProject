"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP VIEW.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP VIEW``.  A ``DROP VIEW`` DDL has no ``INV`` block, so the canonical
SFV obligations are derived one-to-one from the shipped applicability
matrix: exactly 37 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP VIEW [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.
A RISK pair (commit/rollback) exercises the transactional DDL boundary,
mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP VIEW`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropViewFactorLoopError(ValueError):
    """Raised when a frozen DROP VIEW obligation input drifts."""


@dataclass(frozen=True)
class DropViewFactorObligation:
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
class DropViewFactorCase:
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
class DropViewFactorLoopPlan:
    obligations: tuple[DropViewFactorObligation, ...]
    cases: tuple[DropViewFactorCase, ...]
    delegated: tuple[DropViewFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropview.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropview"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_view",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_view"

# Every canonical factor maps to the single DROP VIEW consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "view_name_shape": _REPRESENTATIVE_ACTION,
    "multi_view_drop": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "error_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_view": "drop_view",
    "branch_drop_view_if_exists": "drop_view",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  privilege_level=
# non_owner inherently fails (42501) because DROP VIEW requires ownership.
# object_state=not_exists inherently errors (42704) when IF EXISTS is omitted.
# view_name_shape=non_existent surfaces a 42704 because the target name is
# not found.  dependency_state=has_dependent_views fires 2BP01 under RESTRICT
# (or default RESTRICT) because dependent objects block the drop.
# error_boundary=wrong_object_type fires 42809 when the target is a table.
# error_boundary values describe the same failure boundaries; the renderer
# co-derives the matching causative factor.  Kept minimal (Option-A
# marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("privilege_level", "non_owner"),
        ("object_state", "not_exists"),
        ("view_name_shape", "non_existent"),
        ("dependency_state", "has_dependent_views"),
        ("error_boundary", "non_existent_without_if_exists"),
        ("error_boundary", "dependent_objects_without_cascade"),
        ("error_boundary", "insufficient_privilege"),
        ("error_boundary", "wrong_object_type"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropViewFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropViewFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropViewFactorObligation]:
    rows: list[DropViewFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropViewFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPVIEW-GRM|{action.grammar_branch_id}|"
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
        raise DropViewFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropViewFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_view")
    if len(catalog_rows) != 37:
        raise DropViewFactorLoopError("canonical obligation count drift")
    rows: list[DropViewFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropViewFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPVIEW-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropViewFactorObligation]:
    return [
        DropViewFactorObligation(
            ordinal=0,
            obligation_id=f"DROPVIEW-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropview:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropViewFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-view-factor-obligations-v1\n")
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
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks nine
# pairs as expected_failure, but the bounded extension crosses privilege,
# view-missing, and dependency negatives whose SQLSTATEs are resolved here
# too.  SQLSTATEs are provisional in the no-DB phase (a later DB phase
# verifies on PG18.4).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_view_declared_failure",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_view_privilege",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "undefined_view_missing",
    ),
    ("view_name_shape", "non_existent"): (
        "42704",
        "undefined_view_name",
    ),
    ("dependency_state", "has_dependent_views"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("error_boundary", "non_existent_without_if_exists"): (
        "42704",
        "view_missing_without_if_exists",
    ),
    ("error_boundary", "dependent_objects_without_cascade"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("error_boundary", "insufficient_privilege"): (
        "42501",
        "insufficient_view_privilege",
    ),
    ("error_boundary", "wrong_object_type"): (
        "42809",
        "wrong_object_type",
    ),
}


def _expected_failure_details(
    obligation: DropViewFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropViewFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "absent" (the raw DROP VIEW form without IF EXISTS) and cascade_restrict is
# "none" (RESTRICT is the default behavior when omitted).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_view",
    "grammar_branch": "branch_1",
    "target_action": "drop_view",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "view_name_shape": "simple",
    "multi_view_drop": "single_view",
    "privilege_level": "owner",
    "dependency_state": "no_dependents",
    "error_boundary": "none",
    "verification_mode": "pg_class_query",
    "cleanup_mode": "cascade_cleanup",
}

# Baseline primaries whose target view is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.  For
# these the renderer forces object_state=not_exists and if_exists_clause=
# absent so the missing view surfaces a hard error rather than an IF EXISTS
# notice.
_ABSENT_VIEW_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("view_name_shape", "non_existent"),
        ("error_boundary", "non_existent_without_if_exists"),
    }
)

# Baseline primaries that imply a dependent-object fixture must be created.
_DEPENDENCY_FAILURE_PRIMARIES = frozenset(
    {
        ("dependency_state", "has_dependent_views"),
        ("dependency_state", "has_dependent_policies"),
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

# Baseline primaries that imply the target is a table, not a view.
_WRONG_OBJECT_TYPE_PRIMARIES = frozenset(
    {
        ("error_boundary", "wrong_object_type"),
    }
)


def _baseline_assignments(
    obligation: DropViewFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_VIEW_PRIMARIES:
        assignments["object_state"] = "not_exists"
        assignments["if_exists_clause"] = "absent"
    if (obligation.factor_key, obligation.value) in _DEPENDENCY_FAILURE_PRIMARIES:
        if obligation.factor_key == "error_boundary":
            assignments["dependency_state"] = "has_dependent_views"
    if (obligation.factor_key, obligation.value) in _PRIVILEGE_FAILURE_PRIMARIES:
        if obligation.factor_key == "error_boundary":
            assignments["privilege_level"] = "non_owner"
    if obligation.factor_key == "statement_branch":
        # statement_branch=branch_drop_view_if_exists implies IF EXISTS present.
        if obligation.value == "branch_drop_view_if_exists":
            assignments["if_exists_clause"] = "present"
    if len(assignments) != len(set(assignments)):
        raise DropViewFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_view_factor_loop_plan(
    repository_root: Path,
) -> DropViewFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_view_factor_loop_obligations(root)
    cases: list[DropViewFactorCase] = []
    delegated: list[DropViewFactorObligation] = []
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
            DropViewFactorCase(
                ordinal=ordinal,
                case_id=f"DROPVIEW{ordinal:05d}",
                sql_filename=f"DROPVIEW{ordinal:05d}.sql",
                object_prefix=f"dropview_{ordinal:05d}_",
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
    plan = DropViewFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 40 or len(plan.delegated) != 0:
        raise DropViewFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 40
    ):
        raise DropViewFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 40:
        raise DropViewFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropViewFactorLoopPlan] = {}


def _build_drop_view_factor_plan_lazily(
    repository_root: Path,
) -> DropViewFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_view_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_view_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropViewFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropViewFactorObligation(
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
    if len(rows) != 40:
        raise DropViewFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropViewFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 37, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropViewFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropViewFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 40:
        raise DropViewFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropViewFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropViewFactorLoopError",
    "DropViewFactorObligation",
    "DropViewFactorCase",
    "DropViewFactorLoopPlan",
    "compile_drop_view_factor_loop_obligations",
    "build_drop_view_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_view_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
