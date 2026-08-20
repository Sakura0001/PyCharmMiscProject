"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP SUBSCRIPTION.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
DROP SUBSCRIPTION.  A DROP SUBSCRIPTION DDL has no INV block, so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 33 rows, one local obligation per row.

The official synopsis has a single branch
(DROP SUBSCRIPTION [ IF EXISTS ] name [ CASCADE | RESTRICT ]);
the grammar ledger freezes that one action skeleton as a GRM obligation.
A RISK pair (commit/rollback) exercises the transactional DDL boundary,
mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
DROP SUBSCRIPTION error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropSubscriptionFactorLoopError(ValueError):
    """Raised when a frozen DROP SUBSCRIPTION obligation input drifts."""


@dataclass(frozen=True)
class DropSubscriptionFactorObligation:
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
class DropSubscriptionFactorCase:
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
class DropSubscriptionFactorLoopPlan:
    obligations: tuple[DropSubscriptionFactorObligation, ...]
    cases: tuple[DropSubscriptionFactorCase, ...]
    delegated: tuple[DropSubscriptionFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropsubscription.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropsubscription"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_subscription",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_subscription"

# Every canonical factor maps to the single DROP SUBSCRIPTION consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "subscription_existence": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict_clause": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "replication_slot_state": _REPRESENTATIVE_ACTION,
    "subscription_name_shape": _REPRESENTATIVE_ACTION,
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "replication_slot_dependency": _REPRESENTATIVE_ACTION,
    "nonexistent_subscription": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "replication_slot_conflict": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_subscription": "drop_subscription",
    "branch_drop_subscription_if_exists": "drop_subscription",
    "branch_drop_subscription_cascade": "drop_subscription",
    "branch_drop_subscription_restrict": "drop_subscription",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  DROP SUBSCRIPTION
# requires superuser privilege, so privilege_context=non_superuser_no_privilege
# inherently fails (42501).  executor_privilege=non_superuser also fails
# (42501).  When the subscription is absent and IF EXISTS is omitted, the
# lookup fails (42704).  RESTRICT with an active replication slot fails
# (2BP01).  Kept minimal (Option-A marginal); cross-product failures live
# in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("privilege_context", "non_superuser_no_privilege"),
        ("executor_privilege", "non_superuser"),
        ("privilege_insufficient", "non_superuser_dropping_subscription"),
        ("nonexistent_subscription", "subscription_does_not_exist"),
        ("subscription_existence", "subscription_not_exists"),
        ("subscription_name_shape", "non_existing_name"),
        ("replication_slot_conflict", "restrict_with_slot_fails"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropSubscriptionFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropSubscriptionFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropSubscriptionFactorObligation]:
    rows: list[DropSubscriptionFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropSubscriptionFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSUBSCRIPTION-GRM|{action.grammar_branch_id}|"
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
        raise DropSubscriptionFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropSubscriptionFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_subscription")
    if len(catalog_rows) != 33:
        raise DropSubscriptionFactorLoopError("canonical obligation count drift")
    rows: list[DropSubscriptionFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropSubscriptionFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSUBSCRIPTION-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropSubscriptionFactorObligation]:
    return [
        DropSubscriptionFactorObligation(
            ordinal=0,
            obligation_id=f"DROPSUBSCRIPTION-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropsubscription:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropSubscriptionFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-subscription-factor-obligations-v1\n")
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
        "drop_subscription_declared_failure",
    ),
    ("privilege_context", "non_superuser_no_privilege"): (
        "42501",
        "insufficient_subscription_privilege",
    ),
    ("executor_privilege", "non_superuser"): (
        "42501",
        "insufficient_subscription_privilege",
    ),
    ("privilege_insufficient", "non_superuser_dropping_subscription"): (
        "42501",
        "insufficient_subscription_privilege",
    ),
    ("nonexistent_subscription", "subscription_does_not_exist"): (
        "42704",
        "undefined_subscription_no_if_exists",
    ),
    ("subscription_existence", "subscription_not_exists"): (
        "42704",
        "undefined_subscription_absent",
    ),
    ("subscription_name_shape", "non_existing_name"): (
        "42704",
        "undefined_subscription_name",
    ),
    ("replication_slot_conflict", "restrict_with_slot_fails"): (
        "2BP01",
        "replication_slot_restricted",
    ),
    ("replication_slot_dependency", "slot_exists"): (
        "2BP01",
        "replication_slot_restricted",
    ),
}


def _expected_failure_details(
    obligation: DropSubscriptionFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropSubscriptionFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "without_if_exists" (the plain DROP SUBSCRIPTION form) and
# cascade_restrict_clause is "no_clause_default_restrict" (RESTRICT is the
# default behavior).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_subscription",
    "grammar_branch": "branch_1",
    "target_action": "drop_subscription",
    "subscription_existence": "subscription_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "privilege_context": "superuser",
    "replication_slot_state": "has_replication_slot",
    "subscription_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "replication_slot_dependency": "slot_exists",
    "nonexistent_subscription": "subscription_exists",
    "privilege_insufficient": "superuser_sufficient",
    "replication_slot_conflict": "cascade_with_slot_succeeds",
    "verification_mode": "pg_subscription_catalog",
    "cleanup_mode": "drop_subscription_cascade",
}

# Baseline primaries whose target subscription is intentionally absent, so
# the DROP surfaces a not-found error (42704) and the oracle asserts
# absence.  For these the renderer forces if_exists_clause=without_if_exists
# so the missing subscription surfaces a hard error rather than an IF EXISTS
# notice.
_ABSENT_SUBSCRIPTION_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("subscription_existence", "subscription_not_exists"),
        ("nonexistent_subscription", "subscription_does_not_exist"),
        ("subscription_name_shape", "non_existing_name"),
    }
)

# statement_branch values imply specific if_exists_clause and
# cascade_restrict_clause combinations.
_STATEMENT_BRANCH_IMPLICATIONS: dict[str, dict[str, str]] = {
    "branch_drop_subscription": {
        "if_exists_clause": "without_if_exists",
        "cascade_restrict_clause": "no_clause_default_restrict",
    },
    "branch_drop_subscription_if_exists": {
        "if_exists_clause": "with_if_exists",
        "cascade_restrict_clause": "no_clause_default_restrict",
    },
    "branch_drop_subscription_cascade": {
        "if_exists_clause": "without_if_exists",
        "cascade_restrict_clause": "cascade",
    },
    "branch_drop_subscription_restrict": {
        "if_exists_clause": "without_if_exists",
        "cascade_restrict_clause": "restrict",
    },
}


def _baseline_assignments(
    obligation: DropSubscriptionFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_SUBSCRIPTION_PRIMARIES:
        assignments["if_exists_clause"] = "without_if_exists"
    if obligation.factor_key == "statement_branch":
        impl = _STATEMENT_BRANCH_IMPLICATIONS.get(obligation.value, {})
        assignments.update(impl)
    if obligation.factor_key == "replication_slot_conflict":
        if obligation.value == "restrict_with_slot_fails":
            assignments["cascade_restrict_clause"] = "restrict"
            assignments["replication_slot_dependency"] = "slot_exists"
            assignments["replication_slot_state"] = "has_replication_slot"
    if obligation.factor_key == "cascade_restrict_clause":
        if obligation.value == "restrict":
            assignments["replication_slot_conflict"] = "restrict_with_slot_fails"
        elif obligation.value == "cascade":
            assignments["replication_slot_conflict"] = "cascade_with_slot_succeeds"
    if len(assignments) != len(set(assignments)):
        raise DropSubscriptionFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_subscription_factor_loop_plan(
    repository_root: Path,
) -> DropSubscriptionFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_subscription_factor_loop_obligations(root)
    cases: list[DropSubscriptionFactorCase] = []
    delegated: list[DropSubscriptionFactorObligation] = []
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
            DropSubscriptionFactorCase(
                ordinal=ordinal,
                case_id=f"DROPSUBSCRIPTION{ordinal:05d}",
                sql_filename=f"DROPSUBSCRIPTION{ordinal:05d}.sql",
                object_prefix=f"dropsubscription_{ordinal:05d}_",
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
    plan = DropSubscriptionFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 36 or len(plan.delegated) != 0:
        raise DropSubscriptionFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 36
    ):
        raise DropSubscriptionFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 36:
        raise DropSubscriptionFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropSubscriptionFactorLoopPlan] = {}


def _build_drop_subscription_factor_plan_lazily(
    repository_root: Path,
) -> DropSubscriptionFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_subscription_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_subscription_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropSubscriptionFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropSubscriptionFactorObligation(
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
    if len(rows) != 36:
        raise DropSubscriptionFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropSubscriptionFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 33, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropSubscriptionFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropSubscriptionFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 36:
        raise DropSubscriptionFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropSubscriptionFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropSubscriptionFactorLoopError",
    "DropSubscriptionFactorObligation",
    "DropSubscriptionFactorCase",
    "DropSubscriptionFactorLoopPlan",
    "compile_drop_subscription_factor_loop_obligations",
    "build_drop_subscription_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_subscription_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
