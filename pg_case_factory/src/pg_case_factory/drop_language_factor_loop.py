"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP LANGUAGE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP LANGUAGE``.  A ``DROP LANGUAGE`` DDL has no ``INV`` block, so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 32 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP [ PROCEDURAL ] LANGUAGE [ IF EXISTS ] name [ CASCADE|RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.
The optional ``PROCEDURAL`` noise word is semantically equivalent to the
modern ``DROP LANGUAGE`` form, so every emitted program uses the modern
form (no ``PROCEDURAL``) and the inserter's default col-0 regex
``(?m)^DROP\\s+LANGUAGE(?:\\s|;|$)`` matches unconditionally.  A RISK pair
(commit/rollback) exercises the transactional DDL boundary, mirroring the
sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP LANGUAGE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropLanguageFactorLoopError(ValueError):
    """Raised when a frozen DROP LANGUAGE obligation input drifts."""


@dataclass(frozen=True)
class DropLanguageFactorObligation:
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
class DropLanguageFactorCase:
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
class DropLanguageFactorLoopPlan:
    obligations: tuple[DropLanguageFactorObligation, ...]
    cases: tuple[DropLanguageFactorCase, ...]
    delegated: tuple[DropLanguageFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-droplanguage.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-droplanguage"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_language",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_language"

_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "target_object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_clause": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "cascade_behavior": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "ownership_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_1": "drop_language",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  Languages require
# superuser or owner privilege, so privilege_context=non_owner inherently
# fails (42501).  target_object_state=missing with the dense default
# if_exists_clause=absent inherently errors (42704).  expected_status=failure
# is the declared failure marker.  target_object_state=exists_with_dependents
# and dependency_state=has_dependents surface the RESTRICT dependency boundary
# (2BP01) because the dense default cascade_clause is restrict_default.
# Kept minimal (Option-A marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "missing"),
        ("privilege_context", "non_owner"),
        ("target_object_state", "exists_with_dependents"),
        ("dependency_state", "has_dependents"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropLanguageFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropLanguageFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropLanguageFactorObligation]:
    rows: list[DropLanguageFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropLanguageFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPLANGUAGE-GRM|{action.grammar_branch_id}|"
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
        raise DropLanguageFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropLanguageFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_language")
    if len(catalog_rows) != 32:
        raise DropLanguageFactorLoopError("canonical obligation count drift")
    rows: list[DropLanguageFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropLanguageFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPLANGUAGE-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropLanguageFactorObligation]:
    return [
        DropLanguageFactorObligation(
            ordinal=0,
            obligation_id=f"DROPLANGUAGE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-droplanguage:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropLanguageFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-language-factor-obligations-v1\n")
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
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks five
# pairs as expected_failure, but the bounded extension crosses privilege,
# not-exist, and dependency negatives whose SQLSTATEs are resolved here too.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_language_declared_failure",
    ),
    ("target_object_state", "missing"): (
        "42704",
        "missing_language_without_if_exists",
    ),
    ("name_shape", "missing_object"): (
        "42704",
        "missing_language_without_if_exists",
    ),
    ("privilege_context", "non_owner"): (
        "42501",
        "insufficient_language_privilege",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_language_privilege",
    ),
    ("ownership_boundary", "non_owner"): (
        "42501",
        "insufficient_language_privilege",
    ),
    ("dependency_state", "has_dependents"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("target_object_state", "exists_with_dependents"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("cascade_behavior", "restrict_blocks"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42709",
        "invalid_language_drop_combination",
    ),
}


def _expected_failure_details(
    obligation: DropLanguageFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropLanguageFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_language",
    "target_object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_clause": "restrict_default",
    "privilege_context": "owner",
    "name_shape": "plain_identifier",
    "dependency_state": "no_dependents",
    "cascade_behavior": "cascade_succeeds",
    "invalid_combination": "none",
    "ownership_boundary": "owner",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}


def _baseline_assignments(
    obligation: DropLanguageFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropLanguageFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_language_factor_loop_plan(
    repository_root: Path,
) -> DropLanguageFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_language_factor_loop_obligations(root)
    cases: list[DropLanguageFactorCase] = []
    delegated: list[DropLanguageFactorObligation] = []
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
            DropLanguageFactorCase(
                ordinal=ordinal,
                case_id=f"DROPLANGUAGE{ordinal:05d}",
                sql_filename=f"DROPLANGUAGE{ordinal:05d}.sql",
                object_prefix=f"droplanguage_{ordinal:05d}_",
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
    plan = DropLanguageFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 35 or len(plan.delegated) != 0:
        raise DropLanguageFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 35
    ):
        raise DropLanguageFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 35:
        raise DropLanguageFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropLanguageFactorLoopPlan] = {}


def _build_drop_language_factor_plan_lazily(
    repository_root: Path,
) -> DropLanguageFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_language_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_language_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropLanguageFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropLanguageFactorObligation(
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
    if len(rows) != 35:
        raise DropLanguageFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropLanguageFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 32, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropLanguageFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropLanguageFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 35:
        raise DropLanguageFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropLanguageFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropLanguageFactorLoopError",
    "DropLanguageFactorObligation",
    "DropLanguageFactorCase",
    "DropLanguageFactorLoopPlan",
    "compile_drop_language_factor_loop_obligations",
    "build_drop_language_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_language_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
