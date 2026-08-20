"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP ACCESS METHOD.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP ACCESS METHOD``.  ``drop_access_method.yaml`` marks relation/table/
column-type coverage ``not_applicable`` (an access method DDL has no ``INV``
block), so the canonical SFV obligations are derived one-to-one from the
shipped applicability matrix: exactly 28 rows, one local obligation per row.

The official synopsis has a single branch (``DROP ACCESS METHOD [ IF EXISTS ]
name [ CASCADE | RESTRICT ]``); the grammar ledger freezes that one action
skeleton as a GRM obligation.  A RISK pair (commit/rollback) exercises the
transactional DDL boundary, mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP ACCESS METHOD`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropAccessMethodFactorLoopError(ValueError):
    """Raised when a frozen DROP ACCESS METHOD obligation input drifts."""


@dataclass(frozen=True)
class DropAccessMethodFactorObligation:
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
class DropAccessMethodFactorCase:
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
class DropAccessMethodFactorLoopPlan:
    obligations: tuple[DropAccessMethodFactorObligation, ...]
    cases: tuple[DropAccessMethodFactorCase, ...]
    delegated: tuple[DropAccessMethodFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropaccessmethod.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropaccessmethod"

# The single official synopsis action form.  DROP ACCESS METHOD has no
# optional keyword / alternative axes beyond the synopsis, so the GRM ledger
# is exactly this one action skeleton.
@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_access_method",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

# A representative branch (branch_1) used as the baseline consumer for
# statement-wide modifiers that are not bound to one sub-clause.
_REPRESENTATIVE_ACTION = "drop_access_method"

# Canonical factor -> the action where the value is observable.  DROP
# ACCESS METHOD has a single synopsis branch, so every factor's consumer is
# the representative action.  statement_branch is resolved in
# :func:`_canonical_consumer` for symmetry with the sibling ledgers.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "am_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "nonexistent_am": _REPRESENTATIVE_ACTION,
    "dependent_objects_exist": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_1": "drop_access_method",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  The drop_access_method
# yaml declares a single failure condition (``expected_status == failure``);
# the DB doublerun fork calibrates the exact SQLSTATEs; the frozen counts and
# sha256s are the spec.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropAccessMethodFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropAccessMethodFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropAccessMethodFactorObligation]:
    rows: list[DropAccessMethodFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropAccessMethodFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DAM-GRM|{action.grammar_branch_id}|"
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
        raise DropAccessMethodFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropAccessMethodFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_access_method")
    if len(catalog_rows) != 28:
        raise DropAccessMethodFactorLoopError("canonical obligation count drift")
    rows: list[DropAccessMethodFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropAccessMethodFactorObligation(
                ordinal=0,
                obligation_id=f"DAM-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[DropAccessMethodFactorObligation]:
    return [
        DropAccessMethodFactorObligation(
            ordinal=0,
            obligation_id=f"DAM-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropaccessmethod:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropAccessMethodFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-access-method-factor-obligations-v1\n")
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
# frozen counts and sha256s in the companion tests are the spec.  This table is
# a superset of _SFV_FAILURE_VALUES: the baseline only marks
# (expected_status, failure) as expected_failure, but the bounded extension
# crosses privilege_level and dependency_state negatives whose SQLSTATEs are
# resolved here too.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_access_method_declared_failure",
    ),
    ("privilege_level", "non_superuser"): (
        "42501",
        "insufficient_access_method_privilege",
    ),
    ("dependency_state", "has_dependent_opclass"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_state", "has_dependent_index"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
}


def _expected_failure_details(
    obligation: DropAccessMethodFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropAccessMethodFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: DropAccessMethodFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "object_state": "already_exists",
        "expected_status": "success",
        "if_exists_clause": "absent",
        "cascade_restrict": "RESTRICT_default",
        "dependency_state": "no_dependencies",
        "am_name_shape": "plain_identifier",
        "privilege_level": "superuser",
        "nonexistent_am": "without_if_exists",
        "dependent_objects_exist": "restrict_with_dependencies",
        "insufficient_privilege": "non_superuser_drop",
        "verification_mode": "pg_am_removed_assertion",
        "cleanup_mode": "DROP_ACCESS_METHOD_CASCADE",
    }
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropAccessMethodFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_access_method_factor_loop_plan(
    repository_root: Path,
) -> DropAccessMethodFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_access_method_factor_loop_obligations(root)
    cases: list[DropAccessMethodFactorCase] = []
    delegated: list[DropAccessMethodFactorObligation] = []
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
            DropAccessMethodFactorCase(
                ordinal=ordinal,
                case_id=f"DROPACCESSMETHOD{ordinal:05d}",
                sql_filename=f"DROPACCESSMETHOD{ordinal:05d}.sql",
                object_prefix=f"dropaccessmethod_{ordinal:05d}_",
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
    plan = DropAccessMethodFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 31 or len(plan.delegated) != 0:
        raise DropAccessMethodFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 31:
        raise DropAccessMethodFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 31:
        raise DropAccessMethodFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropAccessMethodFactorLoopPlan] = {}


def _build_drop_access_method_factor_plan_lazily(
    repository_root: Path,
) -> DropAccessMethodFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_access_method_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_access_method_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropAccessMethodFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropAccessMethodFactorObligation(
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
    if len(rows) != 31:
        raise DropAccessMethodFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropAccessMethodFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 28, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropAccessMethodFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropAccessMethodFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 31:
        raise DropAccessMethodFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise DropAccessMethodFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropAccessMethodFactorLoopError",
    "DropAccessMethodFactorObligation",
    "DropAccessMethodFactorCase",
    "DropAccessMethodFactorLoopPlan",
    "compile_drop_access_method_factor_loop_obligations",
    "build_drop_access_method_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_access_method_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
