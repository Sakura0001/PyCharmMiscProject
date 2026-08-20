"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP TRIGGER.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP TRIGGER``.  A ``DROP TRIGGER`` DDL has no ``INV`` block, so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 33 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP TRIGGER [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.
A RISK pair (commit/rollback) exercises the transactional DDL boundary,
mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP TRIGGER`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropTriggerFactorLoopError(ValueError):
    """Raised when a frozen DROP TRIGGER obligation input drifts."""


@dataclass(frozen=True)
class DropTriggerFactorObligation:
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
class DropTriggerFactorCase:
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
class DropTriggerFactorLoopPlan:
    obligations: tuple[DropTriggerFactorObligation, ...]
    cases: tuple[DropTriggerFactorCase, ...]
    delegated: tuple[DropTriggerFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-droptrigger.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-droptrigger"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_trigger",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_trigger"

# Every canonical factor maps to the single DROP TRIGGER consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict_clause": _REPRESENTATIVE_ACTION,
    "trigger_name_shape": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "dependent_objects": _REPRESENTATIVE_ACTION,
    "table_dependency": _REPRESENTATIVE_ACTION,
    "target_trigger_not_exists": _REPRESENTATIVE_ACTION,
    "permission_insufficient": _REPRESENTATIVE_ACTION,
    "cascade_destroys_dependents": _REPRESENTATIVE_ACTION,
    "identifier_length_exceeded": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_1": "drop_trigger",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  privilege_level=
# non_owner_no_privilege inherently fails (42501) because DROP TRIGGER
# requires ownership of the trigger's table.  object_state=not_exists
# inherently errors (42704) when IF EXISTS is omitted.  expected_status=
# failure is the declared failure marker (trigger held absent, IF EXISTS
# omitted).  dependent_objects=has_dependents_restrict_blocks is provisional
# (2BP01) — triggers have no real dependents in PG, so RESTRICT never
# actually fails; the SQLSTATE is provisional in the no-DB phase.
# identifier_length_exceeded=over_63_chars is provisional (42622) — PG
# silently truncates long identifiers rather than erroring; the SQLSTATE
# is provisional.  Kept minimal (Option-A marginal); cross-product failures
# live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("target_trigger_not_exists", "without_IF_EXISTS_error"),
        ("privilege_level", "non_owner_no_privilege"),
        ("permission_insufficient", "not_table_owner"),
        ("dependent_objects", "has_dependents_restrict_blocks"),
        ("table_dependency", "table_not_exists"),
        ("identifier_length_exceeded", "over_63_chars"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropTriggerFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropTriggerFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropTriggerFactorObligation]:
    rows: list[DropTriggerFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropTriggerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTRIGGER-GRM|{action.grammar_branch_id}|"
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
        raise DropTriggerFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropTriggerFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_trigger")
    if len(catalog_rows) != 33:
        raise DropTriggerFactorLoopError("canonical obligation count drift")
    rows: list[DropTriggerFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropTriggerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTRIGGER-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropTriggerFactorObligation]:
    return [
        DropTriggerFactorObligation(
            ordinal=0,
            obligation_id=f"DROPTRIGGER-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-droptrigger:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropTriggerFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-trigger-factor-obligations-v1\n")
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
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks eight
# pairs as expected_failure, but the bounded extension crosses privilege,
# table-existence, object-state (trigger-missing), and dependency negatives
# whose SQLSTATEs are resolved here too.  SQLSTATEs are provisional in the
# no-DB phase (a later DB phase verifies on PG18.4).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_trigger_declared_failure",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "undefined_trigger_absent",
    ),
    ("target_trigger_not_exists", "without_IF_EXISTS_error"): (
        "42704",
        "undefined_trigger_no_if_exists",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "insufficient_trigger_privilege",
    ),
    ("permission_insufficient", "not_table_owner"): (
        "42501",
        "insufficient_trigger_privilege",
    ),
    ("dependent_objects", "has_dependents_restrict_blocks"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("table_dependency", "table_not_exists"): (
        "42P01",
        "undefined_table_missing",
    ),
    ("identifier_length_exceeded", "over_63_chars"): (
        "42622",
        "identifier_too_long",
    ),
}


def _expected_failure_details(
    obligation: DropTriggerFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropTriggerFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "present" (the safe IF EXISTS form) and cascade_restrict_clause is
# "absent" (default RESTRICT is the default behavior).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_trigger",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict_clause": "absent",
    "trigger_name_shape": "simple",
    "table_name_shape": "simple",
    "privilege_level": "superuser",
    "dependent_objects": "no_dependencies",
    "table_dependency": "table_exists",
    "target_trigger_not_exists": "without_IF_EXISTS_error",
    "permission_insufficient": "not_table_owner",
    "cascade_destroys_dependents": "cascade_removes_constraint",
    "identifier_length_exceeded": "over_63_chars",
    "verification_mode": "pg_trigger_catalog_query",
    "cleanup_mode": "DROP_TRIGGER_cascade",
}

# Baseline primaries whose target trigger is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.  For
# these the renderer forces if_exists_clause=absent so the missing trigger
# surfaces a hard error rather than an IF EXISTS notice.
_ABSENT_TRIGGER_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("target_trigger_not_exists", "without_IF_EXISTS_error"),
        ("identifier_length_exceeded", "over_63_chars"),
    }
)

# Baseline primaries whose host relation is intentionally absent, so the DROP
# surfaces a relation-missing error (42P01) and no table is created.
_TABLE_MISSING_PRIMARIES = frozenset(
    {
        ("table_dependency", "table_not_exists"),
    }
)

# Baseline primaries that imply a dependent-object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependent_objects", "has_dependents_restrict_blocks"),
    }
)


def _baseline_assignments(
    obligation: DropTriggerFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_TRIGGER_PRIMARIES:
        assignments["if_exists_clause"] = "absent"
    if obligation.factor_key == "target_trigger_not_exists":
        # with_IF_EXISTS_noop: trigger absent + IF EXISTS = notice (success)
        if obligation.value == "with_IF_EXISTS_noop":
            assignments["if_exists_clause"] = "present"
    if obligation.factor_key == "dependent_objects":
        if obligation.value == "has_dependents_restrict_blocks":
            assignments["cascade_restrict_clause"] = "RESTRICT"
    if obligation.factor_key == "cascade_destroys_dependents":
        if obligation.value == "cascade_removes_constraint":
            assignments["cascade_restrict_clause"] = "CASCADE"
            assignments["dependent_objects"] = "has_dependents_restrict_blocks"
    if len(assignments) != len(set(assignments)):
        raise DropTriggerFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_trigger_factor_loop_plan(
    repository_root: Path,
) -> DropTriggerFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_trigger_factor_loop_obligations(root)
    cases: list[DropTriggerFactorCase] = []
    delegated: list[DropTriggerFactorObligation] = []
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
            DropTriggerFactorCase(
                ordinal=ordinal,
                case_id=f"DROPTRIGGER{ordinal:05d}",
                sql_filename=f"DROPTRIGGER{ordinal:05d}.sql",
                object_prefix=f"droptrigger_{ordinal:05d}_",
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
    plan = DropTriggerFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 36 or len(plan.delegated) != 0:
        raise DropTriggerFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 36
    ):
        raise DropTriggerFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 36:
        raise DropTriggerFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropTriggerFactorLoopPlan] = {}


def _build_drop_trigger_factor_plan_lazily(
    repository_root: Path,
) -> DropTriggerFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_trigger_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_trigger_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropTriggerFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropTriggerFactorObligation(
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
        raise DropTriggerFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropTriggerFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 33, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropTriggerFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropTriggerFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 36:
        raise DropTriggerFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropTriggerFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropTriggerFactorLoopError",
    "DropTriggerFactorObligation",
    "DropTriggerFactorCase",
    "DropTriggerFactorLoopPlan",
    "compile_drop_trigger_factor_loop_obligations",
    "build_drop_trigger_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_trigger_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
