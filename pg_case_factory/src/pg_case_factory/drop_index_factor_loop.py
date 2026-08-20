"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP INDEX.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP INDEX``.  A ``DROP INDEX`` DDL has no ``INV`` block, so the canonical
SFV obligations are derived one-to-one from the shipped applicability matrix:
exactly 53 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP INDEX [ CONCURRENTLY ] [ IF EXISTS ] name [, ...] [ CASCADE|RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.  A
RISK pair (commit/rollback) exercises the transactional DDL boundary,
mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP INDEX`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropIndexFactorLoopError(ValueError):
    """Raised when a frozen DROP INDEX obligation input drifts."""


@dataclass(frozen=True)
class DropIndexFactorObligation:
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
class DropIndexFactorCase:
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
class DropIndexFactorLoopPlan:
    obligations: tuple[DropIndexFactorObligation, ...]
    cases: tuple[DropIndexFactorCase, ...]
    delegated: tuple[DropIndexFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropindex.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropindex"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_index",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_index"

_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
    "concurrently": _REPRESENTATIVE_ACTION,
    "dependency_type": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists": _REPRESENTATIVE_ACTION,
    "index_method": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "multi_index": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "permission": _REPRESENTATIVE_ACTION,
    "permission_insufficient": _REPRESENTATIVE_ACTION,
    "syntax_error": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "drop_single": "drop_index",
    "drop_multiple": "drop_index",
    "drop_concurrently": "drop_index",
    "drop_cascade": "drop_index",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  The index is
# intentionally absent for expected_status=failure, object_state=not_exists
# and name_shape=missing_object (42704).  object_state=depended_by_constraint
# under the RESTRICT default surfaces 2BP01.  permission=non_owner and the
# permission_insufficient failure paths surface 42501.  syntax_error surfaces
# 42601.  The invalid_combination values surface their specific SQLSTATEs.
# Kept minimal (Option-A marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("object_state", "depended_by_constraint"),
        ("name_shape", "missing_object"),
        ("permission", "non_owner"),
        ("permission_insufficient", "non_owner_drop"),
        ("permission_insufficient", "no_schema_privilege"),
        ("syntax_error", "invalid_syntax"),
        ("invalid_combination", "concurrently_in_transaction"),
        ("invalid_combination", "concurrently_on_partitioned"),
        ("invalid_combination", "concurrently_with_cascade"),
        ("invalid_combination", "concurrently_with_multiple_indexes"),
        ("invalid_combination", "restrict_with_dependency"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropIndexFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropIndexFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropIndexFactorObligation]:
    rows: list[DropIndexFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropIndexFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPINDEX-GRM|{action.grammar_branch_id}|"
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
        raise DropIndexFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropIndexFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_index")
    if len(catalog_rows) != 53:
        raise DropIndexFactorLoopError("canonical obligation count drift")
    rows: list[DropIndexFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropIndexFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPINDEX-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropIndexFactorObligation]:
    return [
        DropIndexFactorObligation(
            ordinal=0,
            obligation_id=f"DROPINDEX-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropindex:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropIndexFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-index-factor-obligations-v1\n")
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
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks only the
# marginal pairs as expected_failure, but the bounded extension crosses
# permission, object_state and dependency_type negatives whose SQLSTATEs are
# resolved here too.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_index_declared_failure",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "undefined_index_absent",
    ),
    ("object_state", "depended_by_constraint"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("name_shape", "missing_object"): (
        "42704",
        "undefined_index_name",
    ),
    ("permission", "non_owner"): (
        "42501",
        "insufficient_index_privilege",
    ),
    ("permission_insufficient", "non_owner_drop"): (
        "42501",
        "insufficient_index_privilege",
    ),
    ("permission_insufficient", "no_schema_privilege"): (
        "42501",
        "insufficient_schema_privilege",
    ),
    ("syntax_error", "invalid_syntax"): (
        "42601",
        "invalid_drop_index_syntax",
    ),
    ("invalid_combination", "concurrently_in_transaction"): (
        "55006",
        "concurrently_in_transaction_block",
    ),
    ("invalid_combination", "concurrently_on_partitioned"): (
        "0A000",
        "concurrently_on_partitioned_index",
    ),
    ("invalid_combination", "concurrently_with_cascade"): (
        "42601",
        "concurrently_with_cascade_invalid",
    ),
    ("invalid_combination", "concurrently_with_multiple_indexes"): (
        "42601",
        "concurrently_with_multiple_indexes_invalid",
    ),
    ("invalid_combination", "restrict_with_dependency"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_type", "unique_pk_constraint"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
}


def _expected_failure_details(
    obligation: DropIndexFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropIndexFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "drop_single",
    "grammar_branch": "branch_1",
    "target_action": "drop_index",
    "object_state": "exists",
    "expected_status": "success",
    "concurrently": "false",
    "if_exists": "false",
    "cascade_restrict": "restrict",
    "multi_index": "single",
    "permission": "owner",
    "name_shape": "plain_identifier",
    "dependency_type": "no_dependency",
    "index_method": "btree",
    "invalid_combination": "none",
    "syntax_error": "none",
    "permission_insufficient": "none",
    "verification_mode": "catalog_absence_check",
    "cleanup_mode": "explicit_drop",
}


def _baseline_assignments(
    obligation: DropIndexFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropIndexFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_index_factor_loop_plan(
    repository_root: Path,
) -> DropIndexFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_index_factor_loop_obligations(root)
    cases: list[DropIndexFactorCase] = []
    delegated: list[DropIndexFactorObligation] = []
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
            DropIndexFactorCase(
                ordinal=ordinal,
                case_id=f"DROPINDEX{ordinal:05d}",
                sql_filename=f"DROPINDEX{ordinal:05d}.sql",
                object_prefix=f"dropindex_{ordinal:05d}_",
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
    plan = DropIndexFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 56 or len(plan.delegated) != 0:
        raise DropIndexFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 56
    ):
        raise DropIndexFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 56:
        raise DropIndexFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropIndexFactorLoopPlan] = {}


def _build_drop_index_factor_plan_lazily(
    repository_root: Path,
) -> DropIndexFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_index_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_index_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropIndexFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropIndexFactorObligation(
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
    if len(rows) != 56:
        raise DropIndexFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropIndexFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 53, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropIndexFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropIndexFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 56:
        raise DropIndexFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropIndexFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropIndexFactorLoopError",
    "DropIndexFactorObligation",
    "DropIndexFactorCase",
    "DropIndexFactorLoopPlan",
    "compile_drop_index_factor_loop_obligations",
    "build_drop_index_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_index_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
