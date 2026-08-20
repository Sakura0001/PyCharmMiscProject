"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP SCHEMA.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP SCHEMA``.  ``DROP SCHEMA`` DDL has no ``INV`` block, so the canonical
SFV obligations are derived one-to-one from the shipped applicability matrix:
exactly 40 rows, one local obligation per row (including every
``statement_branch`` row -- no skip).

The official synopsis has a single grammar action
(``DROP SCHEMA [IF EXISTS] name [, ...] [CASCADE|RESTRICT]``); the grammar
ledger freezes that one action skeleton as a GRM obligation.  A RISK pair
(commit/rollback) exercises the transactional DDL boundary, mirroring the
sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP SCHEMA`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropSchemaFactorLoopError(ValueError):
    """Raised when a frozen DROP SCHEMA obligation input drifts."""


@dataclass(frozen=True)
class DropSchemaFactorObligation:
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
class DropSchemaFactorCase:
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
class DropSchemaFactorLoopPlan:
    obligations: tuple[DropSchemaFactorObligation, ...]
    cases: tuple[DropSchemaFactorCase, ...]
    delegated: tuple[DropSchemaFactorObligation, ...]
    obligation_multiset_sha256: str


_BRANCH_1 = "branch_1"
_DOC_SOURCE = "postgresql-18.4-doc:sql-dropschema"


@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_schema",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_schema"

_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "multi_schema_drop": _REPRESENTATIVE_ACTION,
    "schema_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "contained_objects_state": _REPRESENTATIVE_ACTION,
    "cross_schema_dependency": _REPRESENTATIVE_ACTION,
    "error_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_schema": "drop_schema",
    "branch_drop_schema_if_exists": "drop_schema",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  insufficient_privilege
# (42501) fires for non_owner.  non_existent_without_if_exists (42704) fires
# when the schema is absent and IF EXISTS is omitted.  contains_objects_without_
# cascade (2BP01) fires when a non-empty schema is dropped under RESTRICT.
# expected_status=failure is the declared failure marker.  Kept minimal (Option-A
# marginal); cross-product failures live in EXTENSION.  The remaining
# behaviour-axis negatives (object_state=exists_with_objects, contained_objects_
# state=has_*, cross_schema_dependency=has_cross_*) are exercised accurately in
# the bounded extension; their baseline cases stay provisionally covered.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("error_boundary", "non_existent_without_if_exists"),
        ("error_boundary", "insufficient_privilege"),
        ("error_boundary", "contains_objects_without_cascade"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropSchemaFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropSchemaFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropSchemaFactorObligation]:
    rows: list[DropSchemaFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropSchemaFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSCHEMA-GRM|{action.grammar_branch_id}|"
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
        raise DropSchemaFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropSchemaFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_schema")
    if len(catalog_rows) != 40:
        raise DropSchemaFactorLoopError("canonical obligation count drift")
    rows: list[DropSchemaFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropSchemaFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPSCHEMA-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropSchemaFactorObligation]:
    return [
        DropSchemaFactorObligation(
            ordinal=0,
            obligation_id=f"DROPSCHEMA-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropschema:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropSchemaFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-schema-factor-obligations-v1\n")
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
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks only four
# pairs as expected_failure, but the bounded extension crosses privilege_level,
# object_state (not_exists / exists_with_objects) negatives whose SQLSTATEs are
# resolved here too.  SQLSTATEs are provisional (a later DB phase verifies on
# PG18.4); the not-exist boundary uses 42704 for consistency with the cascaded
# drop_* siblings (drop_role/drop_publication).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_schema_declared_failure",
    ),
    ("error_boundary", "non_existent_without_if_exists"): (
        "42704",
        "undefined_schema_no_if_exists",
    ),
    ("error_boundary", "insufficient_privilege"): (
        "42501",
        "insufficient_schema_privilege",
    ),
    ("error_boundary", "contains_objects_without_cascade"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_schema_privilege",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "undefined_schema_no_if_exists",
    ),
    ("object_state", "exists_with_objects"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
}


def _expected_failure_details(
    obligation: DropSchemaFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropSchemaFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  privilege_level
# defaults to superuser so the common case needs no role fixture; the marginal
# privilege_level=owner / non_owner baseline cases install a role fixture.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_schema",
    "grammar_branch": "branch_1",
    "target_action": "drop_schema",
    "object_state": "exists_empty",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "multi_schema_drop": "single_schema",
    "schema_name_shape": "simple",
    "privilege_level": "superuser",
    "contained_objects_state": "empty_schema",
    "cross_schema_dependency": "no_cross_dependency",
    "error_boundary": "none",
    "verification_mode": "pg_namespace_query",
    "cleanup_mode": "no_cleanup_needed",
}


def _baseline_assignments(
    obligation: DropSchemaFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropSchemaFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_schema_factor_loop_plan(
    repository_root: Path,
) -> DropSchemaFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_schema_factor_loop_obligations(root)
    cases: list[DropSchemaFactorCase] = []
    delegated: list[DropSchemaFactorObligation] = []
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
            DropSchemaFactorCase(
                ordinal=ordinal,
                case_id=f"DROPSCHEMA{ordinal:05d}",
                sql_filename=f"DROPSCHEMA{ordinal:05d}.sql",
                object_prefix=f"dropschema_{ordinal:05d}_",
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
    plan = DropSchemaFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 43 or len(plan.delegated) != 0:
        raise DropSchemaFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 43
    ):
        raise DropSchemaFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 43:
        raise DropSchemaFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropSchemaFactorLoopPlan] = {}


def _build_drop_schema_factor_plan_lazily(
    repository_root: Path,
) -> DropSchemaFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_schema_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_schema_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropSchemaFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropSchemaFactorObligation(
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
        raise DropSchemaFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropSchemaFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 40, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropSchemaFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropSchemaFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 43:
        raise DropSchemaFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropSchemaFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropSchemaFactorLoopError",
    "DropSchemaFactorObligation",
    "DropSchemaFactorCase",
    "DropSchemaFactorLoopPlan",
    "compile_drop_schema_factor_loop_obligations",
    "build_drop_schema_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_schema_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
