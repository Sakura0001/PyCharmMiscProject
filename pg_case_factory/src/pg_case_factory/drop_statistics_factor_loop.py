"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP STATISTICS.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP STATISTICS``.  A ``DROP STATISTICS`` DDL has no ``INV`` block, so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 32 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP STATISTICS [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.
A RISK pair (commit/rollback) exercises the transactional DDL boundary,
mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP STATISTICS`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropStatisticsFactorLoopError(ValueError):
    """Raised when a frozen DROP STATISTICS obligation input drifts."""


@dataclass(frozen=True)
class DropStatisticsFactorObligation:
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
class DropStatisticsFactorCase:
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
class DropStatisticsFactorLoopPlan:
    obligations: tuple[DropStatisticsFactorObligation, ...]
    cases: tuple[DropStatisticsFactorCase, ...]
    delegated: tuple[DropStatisticsFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropstatistics.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropstatistics"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_statistics",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_statistics"

# Every canonical factor maps to the single DROP STATISTICS consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "statistics_existence": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict_clause": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "multi_target": _REPRESENTATIVE_ACTION,
    "statistics_name_shape": _REPRESENTATIVE_ACTION,
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "nonexistent_statistics": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_statistics": "drop_statistics",
    "branch_drop_statistics_if_exists": "drop_statistics",
    "branch_drop_statistics_cascade": "drop_statistics",
    "branch_drop_statistics_restrict": "drop_statistics",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  privilege_context=
# non_owner inherently fails (42501) because DROP STATISTICS requires
# ownership.  executor_privilege=non_owner inherently fails (42501) for the
# same reason.  privilege_insufficient=non_table_owner is the declared
# privilege failure marker.  statistics_existence=statistics_not_exists
# inherently errors (42704) because the baseline default for if_exists_clause
# is "without_if_exists" so the missing statistics surfaces a 42704 instead
# of a notice.  nonexistent_statistics=statistics_does_not_exist is the
# declared missing marker.  statistics_name_shape=non_existing_name and
# multi_target=multi_target_some_not_exist also surface 42704 when IF EXISTS
# is omitted.  expected_status=failure is the declared failure marker
# (statistics held absent, IF EXISTS omitted).  Kept minimal (Option-A
# marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("privilege_context", "non_owner_no_privilege"),
        ("privilege_insufficient", "non_table_owner_dropping_statistics"),
        ("executor_privilege", "non_owner_no_privilege"),
        ("statistics_existence", "statistics_not_exists"),
        ("nonexistent_statistics", "statistics_does_not_exist"),
        ("statistics_name_shape", "non_existing_name"),
        ("multi_target", "multi_target_some_not_exist"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropStatisticsFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropStatisticsFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropStatisticsFactorObligation]:
    rows: list[DropStatisticsFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropStatisticsFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSTATISTICS-GRM|{action.grammar_branch_id}|"
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
        raise DropStatisticsFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropStatisticsFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_statistics")
    if len(catalog_rows) != 32:
        raise DropStatisticsFactorLoopError("canonical obligation count drift")
    rows: list[DropStatisticsFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropStatisticsFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSTATISTICS-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropStatisticsFactorObligation]:
    return [
        DropStatisticsFactorObligation(
            ordinal=0,
            obligation_id=f"DROPSTATISTICS-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropstatistics:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropStatisticsFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-statistics-factor-obligations-v1\n")
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
        "drop_statistics_declared_failure",
    ),
    ("privilege_context", "non_owner_no_privilege"): (
        "42501",
        "insufficient_statistics_privilege",
    ),
    ("privilege_insufficient", "non_table_owner_dropping_statistics"): (
        "42501",
        "insufficient_statistics_privilege",
    ),
    ("executor_privilege", "non_owner_no_privilege"): (
        "42501",
        "insufficient_statistics_privilege",
    ),
    ("statistics_existence", "statistics_not_exists"): (
        "42704",
        "undefined_statistics",
    ),
    ("nonexistent_statistics", "statistics_does_not_exist"): (
        "42704",
        "undefined_statistics",
    ),
    ("statistics_name_shape", "non_existing_name"): (
        "42704",
        "undefined_statistics_name",
    ),
    ("multi_target", "multi_target_some_not_exist"): (
        "42704",
        "undefined_statistics_multi",
    ),
}


def _expected_failure_details(
    obligation: DropStatisticsFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropStatisticsFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "without_if_exists" (matching the matrix default) and
# cascade_restrict_clause is "no_clause_default_restrict" (RESTRICT default).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_statistics",
    "grammar_branch": "branch_1",
    "target_action": "drop_statistics",
    "statistics_existence": "statistics_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "privilege_context": "superuser",
    "multi_target": "single_target",
    "statistics_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "nonexistent_statistics": "statistics_does_not_exist",
    "privilege_insufficient": "non_table_owner_dropping_statistics",
    "verification_mode": "pg_statistic_ext_catalog",
    "cleanup_mode": "drop_statistics",
}

# Baseline primaries whose target statistics is intentionally absent, so the
# DROP surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_STATISTICS_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("statistics_existence", "statistics_not_exists"),
        ("nonexistent_statistics", "statistics_does_not_exist"),
        ("statistics_name_shape", "non_existing_name"),
    }
)


def _baseline_assignments(
    obligation: DropStatisticsFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_STATISTICS_PRIMARIES:
        pass  # statistics held absent; default if_exists=without surfaces 42704
    if obligation.factor_key == "statement_branch":
        if obligation.value == "branch_drop_statistics_if_exists":
            assignments["if_exists_clause"] = "with_if_exists"
        elif obligation.value == "branch_drop_statistics_cascade":
            assignments["cascade_restrict_clause"] = "cascade"
        elif obligation.value == "branch_drop_statistics_restrict":
            assignments["cascade_restrict_clause"] = "restrict"
    if obligation.factor_key == "multi_target":
        if obligation.value == "multi_target_some_not_exist":
            pass  # renderer creates one stat, omits the other
    if len(assignments) != len(set(assignments)):
        raise DropStatisticsFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_statistics_factor_loop_plan(
    repository_root: Path,
) -> DropStatisticsFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_statistics_factor_loop_obligations(root)
    cases: list[DropStatisticsFactorCase] = []
    delegated: list[DropStatisticsFactorObligation] = []
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
            DropStatisticsFactorCase(
                ordinal=ordinal,
                case_id=f"DROPSTATISTICS{ordinal:05d}",
                sql_filename=f"DROPSTATISTICS{ordinal:05d}.sql",
                object_prefix=f"dropstatistics_{ordinal:05d}_",
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
    plan = DropStatisticsFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 35 or len(plan.delegated) != 0:
        raise DropStatisticsFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 35
    ):
        raise DropStatisticsFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 35:
        raise DropStatisticsFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropStatisticsFactorLoopPlan] = {}


def _build_drop_statistics_factor_plan_lazily(
    repository_root: Path,
) -> DropStatisticsFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_statistics_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_statistics_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropStatisticsFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropStatisticsFactorObligation(
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
        raise DropStatisticsFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropStatisticsFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 32, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropStatisticsFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropStatisticsFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 35:
        raise DropStatisticsFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropStatisticsFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropStatisticsFactorLoopError",
    "DropStatisticsFactorObligation",
    "DropStatisticsFactorCase",
    "DropStatisticsFactorLoopPlan",
    "compile_drop_statistics_factor_loop_obligations",
    "build_drop_statistics_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_statistics_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
