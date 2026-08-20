"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP OPERATOR.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP OPERATOR``.  A ``DROP OPERATOR`` DDL has no ``INV`` block, so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 40 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP OPERATOR [IF EXISTS] name ( { left_type | NONE } , right_type )
[, ...] [CASCADE|RESTRICT]``); the grammar ledger freezes that one action
skeleton as a GRM obligation.  A RISK pair (commit/rollback) exercises
the transactional DDL boundary, mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP OPERATOR`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropOperatorFactorLoopError(ValueError):
    """Raised when a frozen DROP OPERATOR obligation input drifts."""


@dataclass(frozen=True)
class DropOperatorFactorObligation:
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
class DropOperatorFactorCase:
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
class DropOperatorFactorLoopPlan:
    obligations: tuple[DropOperatorFactorObligation, ...]
    cases: tuple[DropOperatorFactorCase, ...]
    delegated: tuple[DropOperatorFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropoperator.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropoperator"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_operator",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_operator"

_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "target_object_state": _REPRESENTATIVE_ACTION,
    "operand_type_shape": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_clause": _REPRESENTATIVE_ACTION,
    "multi_drop": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "operand_data_type": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "cascade_behavior": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "ownership_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_1": "drop_operator",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (best-effort attribution against PG 18.4).  Operators
# dropped by a non-owner/insufficient-privilege role fail (42501).  A
# missing target with IF EXISTS absent fails (42704).  An operator with
# dependents under RESTRICT fails (2BP01).  An invalid semantic
# combination fails (42809).  expected_status=failure is the declared
# failure marker.  Kept minimal (Option-A marginal); cross-product
# failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "missing"),
        ("target_object_state", "exists_with_dependents"),
        ("privilege_context", "non_owner"),
        ("privilege_context", "insufficient_privilege"),
        ("ownership_boundary", "non_owner"),
        ("invalid_combination", "syntax_valid_semantic_error"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropOperatorFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropOperatorFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropOperatorFactorObligation]:
    rows: list[DropOperatorFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropOperatorFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPOPERATOR-GRM|{action.grammar_branch_id}|"
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
        raise DropOperatorFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropOperatorFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_operator")
    if len(catalog_rows) != 40:
        raise DropOperatorFactorLoopError("canonical obligation count drift")
    rows: list[DropOperatorFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropOperatorFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPOPERATOR-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropOperatorFactorObligation]:
    return [
        DropOperatorFactorObligation(
            ordinal=0,
            obligation_id=f"DROPOPERATOR-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropoperator:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropOperatorFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-operator-factor-obligations-v1\n")
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


# Best-effort PG 18.4 SQLSTATE attribution for each reachable
# expected-failure value.  The frozen counts and sha256s in the
# companion tests are the spec.  This table is a superset of
# _SFV_FAILURE_VALUES: the baseline marks seven pairs as
# expected_failure, but the bounded extension crosses privilege,
# not-exist, and dependency negatives whose SQLSTATEs are resolved
# here too.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_operator_declared_failure",
    ),
    ("target_object_state", "missing"): (
        "42704",
        "undefined_operator_absent",
    ),
    ("target_object_state", "exists_with_dependents"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("privilege_context", "non_owner"): (
        "42501",
        "insufficient_operator_privilege",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_operator_privilege",
    ),
    ("ownership_boundary", "non_owner"): (
        "42501",
        "insufficient_operator_privilege",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42809",
        "invalid_drop_operator_combination",
    ),
}


def _expected_failure_details(
    obligation: DropOperatorFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropOperatorFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_operator",
    "target_object_state": "exists",
    "operand_type_shape": "binary_operator",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_clause": "restrict_default",
    "multi_drop": "single",
    "privilege_context": "owner",
    "name_shape": "plain_identifier",
    "operand_data_type": "integer",
    "dependency_state": "no_dependents",
    "cascade_behavior": "cascade_succeeds",
    "invalid_combination": "none",
    "ownership_boundary": "owner",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}


def _baseline_assignments(
    obligation: DropOperatorFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropOperatorFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_operator_factor_loop_plan(
    repository_root: Path,
) -> DropOperatorFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_operator_factor_loop_obligations(root)
    cases: list[DropOperatorFactorCase] = []
    delegated: list[DropOperatorFactorObligation] = []
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
            DropOperatorFactorCase(
                ordinal=ordinal,
                case_id=f"DROPOPERATOR{ordinal:05d}",
                sql_filename=f"DROPOPERATOR{ordinal:05d}.sql",
                object_prefix=f"dropoperator_{ordinal:05d}_",
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
    plan = DropOperatorFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 43 or len(plan.delegated) != 0:
        raise DropOperatorFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 43
    ):
        raise DropOperatorFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 43:
        raise DropOperatorFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropOperatorFactorLoopPlan] = {}


def _build_drop_operator_factor_plan_lazily(
    repository_root: Path,
) -> DropOperatorFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_operator_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_operator_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropOperatorFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropOperatorFactorObligation(
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
    if len(rows) != 43:
        raise DropOperatorFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropOperatorFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 40, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropOperatorFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropOperatorFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 43:
        raise DropOperatorFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropOperatorFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropOperatorFactorLoopError",
    "DropOperatorFactorObligation",
    "DropOperatorFactorCase",
    "DropOperatorFactorLoopPlan",
    "compile_drop_operator_factor_loop_obligations",
    "build_drop_operator_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_operator_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
