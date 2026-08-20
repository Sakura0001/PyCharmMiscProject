"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP SERVER.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP SERVER``.  A ``DROP SERVER`` DDL has a single official synopsis
(``DROP SERVER [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]``) with no
``INV`` block, so the canonical SFV obligations are derived one-to-one from
the shipped applicability matrix: exactly 36 rows, one local obligation per
row.

The grammar ledger freezes that one action skeleton as a single GRM
obligation.  A RISK pair (commit/rollback) exercises the transactional DDL
boundary, mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP SERVER`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropServerFactorLoopError(ValueError):
    """Raised when a frozen DROP SERVER obligation input drifts."""


@dataclass(frozen=True)
class DropServerFactorObligation:
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
class DropServerFactorCase:
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
class DropServerFactorLoopPlan:
    obligations: tuple[DropServerFactorObligation, ...]
    cases: tuple[DropServerFactorCase, ...]
    delegated: tuple[DropServerFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropserver.html).  DROP SERVER
# has a single grammar branch; the four ``statement_branch`` factor values
# describe behavioural syntax variants, not separate grammar productions.
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropserver"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_server",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_server"

# Every canonical factor resolves to the single DROP SERVER grammar action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "server_existence": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict_clause": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "multi_target": _REPRESENTATIVE_ACTION,
    "server_name_shape": _REPRESENTATIVE_ACTION,
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "user_mapping_dependency": _REPRESENTATIVE_ACTION,
    "nonexistent_server": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "dependent_user_mapping": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_server": "drop_server",
    "branch_drop_server_if_exists": "drop_server",
    "branch_drop_server_cascade": "drop_server",
    "branch_drop_server_restrict": "drop_server",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  The dense baseline
# holds ``if_exists_clause`` at ``without_if_exists``, so a non-existent
# server (``server_existence=server_not_exists`` or a ``non_existing_name``)
# surfaces ``42704``.  ``privilege_context``/``executor_privilege`` at
# ``non_owner_no_privilege`` surface ``42501``.  ``expected_status=failure``
# is the declared failure marker.  Kept minimal (Option-A marginal);
# cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("server_existence", "server_not_exists"),
        ("server_name_shape", "non_existing_name"),
        ("privilege_context", "non_owner_no_privilege"),
        ("executor_privilege", "non_owner_no_privilege"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropServerFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropServerFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropServerFactorObligation]:
    rows: list[DropServerFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropServerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSERVER-GRM|{action.grammar_branch_id}|"
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
        raise DropServerFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropServerFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_server")
    if len(catalog_rows) != 36:
        raise DropServerFactorLoopError("canonical obligation count drift")
    rows: list[DropServerFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropServerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSERVER-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropServerFactorObligation]:
    return [
        DropServerFactorObligation(
            ordinal=0,
            obligation_id=f"DROPSERVER-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropserver:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropServerFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-server-factor-obligations-v1\n")
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
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks only
# five pairs as expected_failure, but the bounded extension crosses
# privilege_context, server_existence, server_name_shape, multi_target, and
# user_mapping_dependency negatives whose SQLSTATEs are resolved here too.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_server_declared_failure",
    ),
    ("server_existence", "server_not_exists"): (
        "42704",
        "undefined_server_absent",
    ),
    ("server_name_shape", "non_existing_name"): (
        "42704",
        "undefined_server_name",
    ),
    ("privilege_context", "non_owner_no_privilege"): (
        "42501",
        "insufficient_server_privilege",
    ),
    ("executor_privilege", "non_owner_no_privilege"): (
        "42501",
        "insufficient_server_privilege",
    ),
    ("user_mapping_dependency", "has_user_mapping_dependency"): (
        "2BP01",
        "dependent_user_mapping_restricted",
    ),
    ("dependent_user_mapping", "restrict_with_user_mapping_fails"): (
        "2BP01",
        "dependent_user_mapping_restricted",
    ),
    ("cascade_restrict_clause", "restrict"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("nonexistent_server", "server_does_not_exist"): (
        "42704",
        "undefined_server_marker",
    ),
    ("privilege_insufficient", "non_owner_dropping_server"): (
        "42501",
        "insufficient_server_privilege_marker",
    ),
    ("multi_target", "multi_target_some_not_exist"): (
        "42704",
        "undefined_server_in_multi_target",
    ),
}


def _expected_failure_details(
    obligation: DropServerFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropServerFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_server",
    "grammar_branch": "branch_1",
    "target_action": "drop_server",
    "server_existence": "server_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "privilege_context": "superuser",
    "multi_target": "single_target",
    "server_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "user_mapping_dependency": "no_user_mapping_dependency",
    "nonexistent_server": "server_does_not_exist",
    "privilege_insufficient": "non_owner_dropping_server",
    "dependent_user_mapping": "restrict_with_user_mapping_fails",
    "verification_mode": "pg_foreign_server_catalog",
    "cleanup_mode": "drop_server_cascade",
}


def _baseline_assignments(
    obligation: DropServerFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropServerFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_server_factor_loop_plan(
    repository_root: Path,
) -> DropServerFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_server_factor_loop_obligations(root)
    cases: list[DropServerFactorCase] = []
    delegated: list[DropServerFactorObligation] = []
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
            DropServerFactorCase(
                ordinal=ordinal,
                case_id=f"DROPSERVER{ordinal:05d}",
                sql_filename=f"DROPSERVER{ordinal:05d}.sql",
                object_prefix=f"dropserver_{ordinal:05d}_",
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
    plan = DropServerFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 39 or len(plan.delegated) != 0:
        raise DropServerFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 39
    ):
        raise DropServerFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 39:
        raise DropServerFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropServerFactorLoopPlan] = {}


def _build_drop_server_factor_plan_lazily(
    repository_root: Path,
) -> DropServerFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_server_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_server_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropServerFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropServerFactorObligation(
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
    if len(rows) != 39:
        raise DropServerFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropServerFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 36, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropServerFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropServerFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 39:
        raise DropServerFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropServerFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropServerFactorLoopError",
    "DropServerFactorObligation",
    "DropServerFactorCase",
    "DropServerFactorLoopPlan",
    "compile_drop_server_factor_loop_obligations",
    "build_drop_server_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_server_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
