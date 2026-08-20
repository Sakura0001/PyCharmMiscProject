"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP SEQUENCE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP SEQUENCE``.  The canonical SFV obligations are derived one-to-one
from the shipped applicability matrix: exactly 43 rows, one local
obligation per row.

The official synopsis has a single branch
(``DROP SEQUENCE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]``); the
grammar ledger freezes that one action skeleton as a GRM obligation.  A RISK
pair (commit/rollback) exercises the transactional DDL boundary.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP SEQUENCE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropSequenceFactorLoopError(ValueError):
    """Raised when a frozen DROP SEQUENCE obligation input drifts."""


@dataclass(frozen=True)
class DropSequenceFactorObligation:
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
class DropSequenceFactorCase:
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
class DropSequenceFactorLoopPlan:
    obligations: tuple[DropSequenceFactorObligation, ...]
    cases: tuple[DropSequenceFactorCase, ...]
    delegated: tuple[DropSequenceFactorObligation, ...]
    obligation_multiset_sha256: str


_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropsequence"

_REPRESENTATIVE_ACTION = "drop_sequence"


@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_sequence",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "multi_sequence_drop": _REPRESENTATIVE_ACTION,
    "sequence_type_permanence": _REPRESENTATIVE_ACTION,
    "sequence_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "error_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_sequence": "drop_sequence",
    "branch_drop_sequence_if_exists": "drop_sequence",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  privilege_level=
# non_owner inherently fails (42501).  object_state=not_exists with the
# baseline default if_exists_clause=absent inherently errors (42704).
# dependency_state values other than no_dependents under the default
# cascade_restrict=none (RESTRICT) inherently error (2BP01).  expected_status
# =failure is the declared failure marker.  Kept minimal (Option-A
# marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("privilege_level", "non_owner"),
        ("object_state", "not_exists"),
        ("dependency_state", "used_by_identity_column"),
        ("dependency_state", "used_by_serial_column"),
        ("dependency_state", "owned_by_table_column"),
        ("dependency_state", "used_by_default_expression"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropSequenceFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropSequenceFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropSequenceFactorObligation]:
    rows: list[DropSequenceFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropSequenceFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSEQUENCE-GRM|{action.grammar_branch_id}|"
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
        raise DropSequenceFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropSequenceFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_sequence")
    if len(catalog_rows) != 43:
        raise DropSequenceFactorLoopError("canonical obligation count drift")
    rows: list[DropSequenceFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropSequenceFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSEQUENCE-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropSequenceFactorObligation]:
    return [
        DropSequenceFactorObligation(
            ordinal=0,
            obligation_id=f"DROPSEQUENCE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropsequence:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropSequenceFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-sequence-factor-obligations-v1\n")
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
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_sequence_declared_failure",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_sequence_privilege",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "undefined_sequence_absent",
    ),
    ("dependency_state", "used_by_identity_column"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_state", "used_by_serial_column"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_state", "owned_by_table_column"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_state", "used_by_default_expression"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
}


def _expected_failure_details(
    obligation: DropSequenceFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropSequenceFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_sequence",
    "grammar_branch": "branch_1",
    "target_action": "drop_sequence",
    "object_state": "exists_permanent",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "multi_sequence_drop": "single_sequence",
    "sequence_type_permanence": "permanent",
    "sequence_name_shape": "simple",
    "privilege_level": "owner",
    "dependency_state": "no_dependents",
    "error_boundary": "none",
    "verification_mode": "pg_class_query",
    "cleanup_mode": "no_cleanup_needed",
}


def _baseline_assignments(
    obligation: DropSequenceFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropSequenceFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_sequence_factor_loop_plan(
    repository_root: Path,
) -> DropSequenceFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_sequence_factor_loop_obligations(root)
    cases: list[DropSequenceFactorCase] = []
    delegated: list[DropSequenceFactorObligation] = []
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
            DropSequenceFactorCase(
                ordinal=ordinal,
                case_id=f"DROPSEQUENCE{ordinal:05d}",
                sql_filename=f"DROPSEQUENCE{ordinal:05d}.sql",
                object_prefix=f"dropsequence_{ordinal:05d}_",
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
    plan = DropSequenceFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 46 or len(plan.delegated) != 0:
        raise DropSequenceFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 46
    ):
        raise DropSequenceFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 46:
        raise DropSequenceFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropSequenceFactorLoopPlan] = {}


def _build_drop_sequence_factor_plan_lazily(
    repository_root: Path,
) -> DropSequenceFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_sequence_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_sequence_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropSequenceFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropSequenceFactorObligation(
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
    if len(rows) != 46:
        raise DropSequenceFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropSequenceFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 43, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropSequenceFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropSequenceFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 46:
        raise DropSequenceFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropSequenceFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropSequenceFactorLoopError",
    "DropSequenceFactorObligation",
    "DropSequenceFactorCase",
    "DropSequenceFactorLoopPlan",
    "compile_drop_sequence_factor_loop_obligations",
    "build_drop_sequence_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_sequence_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
