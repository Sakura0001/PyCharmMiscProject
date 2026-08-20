"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP TRANSFORM.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP TRANSFORM``.  A ``DROP TRANSFORM`` DDL has no ``INV`` block, so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 45 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP TRANSFORM [ IF EXISTS ] FOR type_name LANGUAGE lang_name
[ CASCADE | RESTRICT ]``); the grammar ledger freezes that one action
skeleton as a GRM obligation.  A RISK pair (commit/rollback) exercises the
transactional DDL boundary, mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP TRANSFORM`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropTransformFactorLoopError(ValueError):
    """Raised when a frozen DROP TRANSFORM obligation input drifts."""


@dataclass(frozen=True)
class DropTransformFactorObligation:
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
class DropTransformFactorCase:
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
class DropTransformFactorLoopPlan:
    obligations: tuple[DropTransformFactorObligation, ...]
    cases: tuple[DropTransformFactorCase, ...]
    delegated: tuple[DropTransformFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-droptransform.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-droptransform"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_transform",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_transform"

# Every canonical factor maps to the single DROP TRANSFORM consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "privilege_requirement": _REPRESENTATIVE_ACTION,
    "type_existence": _REPRESENTATIVE_ACTION,
    "language_existence": _REPRESENTATIVE_ACTION,
    "type_name_shape": _REPRESENTATIVE_ACTION,
    "language_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_on_type": _REPRESENTATIVE_ACTION,
    "privilege_on_language": _REPRESENTATIVE_ACTION,
    "dependency_context": _REPRESENTATIVE_ACTION,
    "nonexistent_transform": _REPRESENTATIVE_ACTION,
    "nonexistent_type": _REPRESENTATIVE_ACTION,
    "nonexistent_language": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "dependent_object_exists": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_transform": "drop_transform",
    "branch_drop_transform_if_exists": "drop_transform",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  A transform is
# identified by the (trftype, trflang) pair; the target is absent (42704)
# when the transform is held missing without IF EXISTS, or when the bound
# type/language name does not exist.  privilege_requirement=missing_* and
# privilege_on_type=not_owns_type / privilege_on_language=not_owns_language
# inherently fail (42501) because DROP TRANSFORM requires ownership of both
# the type and the language.  dependent_object_exists=has_dependencies /
# dependency_context=has_dependent_objects under RESTRICT (default or
# explicit) inherently fail (2BP01).  Kept minimal (Option-A marginal);
# cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("nonexistent_transform", "transform_missing_without_if_exists"),
        ("type_existence", "type_not_exists"),
        ("nonexistent_type", "type_missing"),
        ("type_name_shape", "nonexistent_name"),
        ("language_existence", "language_not_exists"),
        ("nonexistent_language", "language_missing"),
        ("language_name_shape", "nonexistent_name"),
        ("privilege_requirement", "missing_type_ownership"),
        ("privilege_requirement", "missing_language_ownership"),
        ("privilege_on_type", "not_owns_type"),
        ("privilege_on_language", "not_owns_language"),
        ("insufficient_privilege", "missing_type_ownership"),
        ("insufficient_privilege", "missing_language_ownership"),
        ("dependent_object_exists", "has_dependencies"),
        ("dependency_context", "has_dependent_objects"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropTransformFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropTransformFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropTransformFactorObligation]:
    rows: list[DropTransformFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropTransformFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTRANSFORM-GRM|{action.grammar_branch_id}|"
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
        raise DropTransformFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropTransformFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_transform")
    if len(catalog_rows) != 45:
        raise DropTransformFactorLoopError("canonical obligation count drift")
    rows: list[DropTransformFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropTransformFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTRANSFORM-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropTransformFactorObligation]:
    return [
        DropTransformFactorObligation(
            ordinal=0,
            obligation_id=f"DROPTRANSFORM-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-droptransform:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropTransformFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-transform-factor-obligations-v1\n")
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
# expected-failure value.  The frozen counts and sha256s in the companion
# tests are the spec.  This table is a superset of _SFV_FAILURE_VALUES: the
# baseline marks seventeen pairs as expected_failure, but the bounded
# extension crosses privilege, type-existence, language-existence,
# object-state (transform-missing), and dependency negatives whose
# SQLSTATEs are resolved here too.  SQLSTATEs are provisional in the no-DB
# phase (a later DB phase verifies on PG18.4); the privilege (42501) and
# object-missing (42704) attributions are confirmed against a live PG18.4
# server, the dependency attribution (2BP01) is provisional.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_transform_declared_failure",
    ),
    ("object_state", "absent"): (
        "42704",
        "undefined_transform_absent",
    ),
    ("nonexistent_transform", "transform_missing_without_if_exists"): (
        "42704",
        "undefined_transform_no_if_exists",
    ),
    ("type_existence", "type_not_exists"): (
        "42704",
        "transform_type_missing",
    ),
    ("nonexistent_type", "type_missing"): (
        "42704",
        "transform_type_missing",
    ),
    ("type_name_shape", "nonexistent_name"): (
        "42704",
        "transform_type_name_missing",
    ),
    ("language_existence", "language_not_exists"): (
        "42704",
        "transform_language_missing",
    ),
    ("nonexistent_language", "language_missing"): (
        "42704",
        "transform_language_missing",
    ),
    ("language_name_shape", "nonexistent_name"): (
        "42704",
        "transform_language_name_missing",
    ),
    ("privilege_requirement", "missing_type_ownership"): (
        "42501",
        "insufficient_transform_privilege",
    ),
    ("privilege_requirement", "missing_language_ownership"): (
        "42501",
        "insufficient_transform_privilege",
    ),
    ("privilege_on_type", "not_owns_type"): (
        "42501",
        "insufficient_transform_privilege",
    ),
    ("privilege_on_language", "not_owns_language"): (
        "42501",
        "insufficient_transform_privilege",
    ),
    ("insufficient_privilege", "missing_type_ownership"): (
        "42501",
        "insufficient_transform_privilege",
    ),
    ("insufficient_privilege", "missing_language_ownership"): (
        "42501",
        "insufficient_transform_privilege",
    ),
    ("dependent_object_exists", "has_dependencies"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_context", "has_dependent_objects"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
}


def _expected_failure_details(
    obligation: DropTransformFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropTransformFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "present" (the safe IF EXISTS form) and cascade_restrict is
# "default_restrict" (RESTRICT is the default behavior).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_transform",
    "grammar_branch": "branch_1",
    "target_action": "drop_transform",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict": "default_restrict",
    "privilege_requirement": "own_type_and_language",
    "type_existence": "type_exists",
    "language_existence": "language_exists",
    "type_name_shape": "simple_id",
    "language_name_shape": "simple_id",
    "privilege_on_type": "owns_type",
    "privilege_on_language": "owns_language",
    "dependency_context": "no_dependencies",
    "nonexistent_transform": "transform_exists",
    "nonexistent_type": "type_exists",
    "nonexistent_language": "language_exists",
    "insufficient_privilege": "owns_both",
    "dependent_object_exists": "no_dependencies",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_transform",
}

# Baseline primaries whose target transform is intentionally absent, so the
# DROP surfaces a not-found error (42704) and the oracle asserts absence.
# For these the renderer forces if_exists_clause=absent so the missing
# transform surfaces a hard error rather than an IF EXISTS notice.
_ABSENT_TRANSFORM_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("nonexistent_transform", "transform_missing_without_if_exists"),
    }
)

# Baseline primaries that imply a privilege boundary fixture must be armed
# (non-owner actor) so the DROP surfaces an insufficient-privilege error
# (42501).
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("privilege_requirement", "missing_type_ownership"),
        ("privilege_requirement", "missing_language_ownership"),
        ("privilege_on_type", "not_owns_type"),
        ("privilege_on_language", "not_owns_language"),
        ("insufficient_privilege", "missing_type_ownership"),
        ("insufficient_privilege", "missing_language_ownership"),
    }
)

# Baseline primaries that imply a dependent-object fixture must be created
# so the DROP surfaces a dependent-objects-block error (2BP01, provisional)
# under RESTRICT.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_context", "has_dependent_objects"),
        ("dependent_object_exists", "has_dependencies"),
    }
)


def _baseline_assignments(
    obligation: DropTransformFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    primary = (obligation.factor_key, obligation.value)
    if primary in _ABSENT_TRANSFORM_PRIMARIES:
        assignments["if_exists_clause"] = "absent"
    if obligation.factor_key == "statement_branch":
        # branch_drop_transform_if_exists implies IF EXISTS present.
        if obligation.value == "branch_drop_transform_if_exists":
            assignments["if_exists_clause"] = "present"
    if obligation.factor_key == "cascade_restrict":
        if obligation.value == "explicit_cascade":
            assignments["dependency_context"] = "no_dependencies"
    if obligation.factor_key in {"dependency_context", "dependent_object_exists"}:
        if (obligation.factor_key, obligation.value) in _DEPENDENCY_PRIMARIES:
            assignments["dependent_object_exists"] = "has_dependencies"
            assignments["dependency_context"] = "has_dependent_objects"
            assignments["cascade_restrict"] = "explicit_restrict"
    if obligation.factor_key == "privilege_requirement":
        if obligation.value == "missing_type_ownership":
            assignments["privilege_on_type"] = "not_owns_type"
            assignments["insufficient_privilege"] = "missing_type_ownership"
        elif obligation.value == "missing_language_ownership":
            assignments["privilege_on_language"] = "not_owns_language"
            assignments["insufficient_privilege"] = "missing_language_ownership"
    if obligation.factor_key == "privilege_on_type":
        if obligation.value == "not_owns_type":
            assignments["privilege_requirement"] = "missing_type_ownership"
            assignments["insufficient_privilege"] = "missing_type_ownership"
    if obligation.factor_key == "privilege_on_language":
        if obligation.value == "not_owns_language":
            assignments["privilege_requirement"] = "missing_language_ownership"
            assignments["insufficient_privilege"] = "missing_language_ownership"
    if obligation.factor_key == "insufficient_privilege":
        if obligation.value == "missing_type_ownership":
            assignments["privilege_on_type"] = "not_owns_type"
            assignments["privilege_requirement"] = "missing_type_ownership"
        elif obligation.value == "missing_language_ownership":
            assignments["privilege_on_language"] = "not_owns_language"
            assignments["privilege_requirement"] = "missing_language_ownership"
    if len(assignments) != len(set(assignments)):
        raise DropTransformFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_transform_factor_loop_plan(
    repository_root: Path,
) -> DropTransformFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_transform_factor_loop_obligations(root)
    cases: list[DropTransformFactorCase] = []
    delegated: list[DropTransformFactorObligation] = []
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
            DropTransformFactorCase(
                ordinal=ordinal,
                case_id=f"DROPTRANSFORM{ordinal:05d}",
                sql_filename=f"DROPTRANSFORM{ordinal:05d}.sql",
                object_prefix=f"droptransform_{ordinal:05d}_",
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
    plan = DropTransformFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 48 or len(plan.delegated) != 0:
        raise DropTransformFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 48
    ):
        raise DropTransformFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 48:
        raise DropTransformFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropTransformFactorLoopPlan] = {}


def _build_drop_transform_factor_plan_lazily(
    repository_root: Path,
) -> DropTransformFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_transform_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_transform_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropTransformFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropTransformFactorObligation(
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
    if len(rows) != 48:
        raise DropTransformFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropTransformFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 45, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropTransformFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropTransformFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 48:
        raise DropTransformFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropTransformFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropTransformFactorLoopError",
    "DropTransformFactorObligation",
    "DropTransformFactorCase",
    "DropTransformFactorLoopPlan",
    "compile_drop_transform_factor_loop_obligations",
    "build_drop_transform_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_transform_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
