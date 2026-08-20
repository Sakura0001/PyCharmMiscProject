"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP PROCEDURE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP PROCEDURE``.  An ``DROP PROCEDURE`` DDL has no ``INV`` block, so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 40 rows, one local obligation per row
(including both ``statement_branch`` values; no skip).

The official synopsis is a single production
(``DROP PROCEDURE [ IF EXISTS ] name [ ( argtypes ) ] [, ...]
[ CASCADE | RESTRICT ]``); the grammar ledger freezes that one action
skeleton as a GRM obligation.  A RISK pair (commit/rollback) exercises the
transactional DDL boundary, mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP PROCEDURE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropProcedureFactorLoopError(ValueError):
    """Raised when a frozen DROP PROCEDURE obligation input drifts."""


@dataclass(frozen=True)
class DropProcedureFactorObligation:
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
class DropProcedureFactorCase:
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
class DropProcedureFactorLoopPlan:
    obligations: tuple[DropProcedureFactorObligation, ...]
    cases: tuple[DropProcedureFactorCase, ...]
    delegated: tuple[DropProcedureFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropprocedure.html).  The
# ``[, ...]`` multi-object form is part of the same production, so a single
# grammar action covers both statement_branch values.
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropprocedure"


@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_procedure",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_procedure"

# Every canonical factor reaches the same target action; both
# statement_branch values (single + multi-object form) consume the same
# grammar action because ``[, ...]`` is part of one production.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict_clause": _REPRESENTATIVE_ACTION,
    "argtype_specification": _REPRESENTATIVE_ACTION,
    "multiple_objects": _REPRESENTATIVE_ACTION,
    "procedure_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "dependent_objects": _REPRESENTATIVE_ACTION,
    "schema_dependency": _REPRESENTATIVE_ACTION,
    "target_procedure_not_exists": _REPRESENTATIVE_ACTION,
    "target_procedure_different_type": _REPRESENTATIVE_ACTION,
    "permission_insufficient": _REPRESENTATIVE_ACTION,
    "cascade_destroys_dependents": _REPRESENTATIVE_ACTION,
    "identifier_length_exceeded": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_1": "drop_procedure",
    "branch_2": "drop_procedure",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected under the success-path baseline defaults (best-effort
# attribution against PG 18.4).  The baseline default policy is
# cascade_restrict_clause=absent (RESTRICT), so both has_dependents values
# surface 2BP01 in the marginal baseline; the extension crosses them with
# CASCADE to exercise the success side.  Kept minimal (Option-A marginal);
# cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("object_state", "different_signature_exists"),
        ("privilege_level", "non_owner_no_privilege"),
        ("permission_insufficient", "not_owner"),
        ("target_procedure_not_exists", "without_IF_EXISTS_error"),
        ("target_procedure_different_type", "same_name_is_function"),
        ("schema_dependency", "schema_not_exists"),
        ("argtype_specification", "without_signature_multiple"),
        ("dependent_objects", "has_dependents_restrict_blocks"),
        ("dependent_objects", "has_dependents_cascade_removes"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropProcedureFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropProcedureFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropProcedureFactorObligation]:
    rows: list[DropProcedureFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropProcedureFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPPROCEDURE-GRM|{action.grammar_branch_id}|"
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
        raise DropProcedureFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropProcedureFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_procedure")
    if len(catalog_rows) != 40:
        raise DropProcedureFactorLoopError("canonical obligation count drift")
    rows: list[DropProcedureFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropProcedureFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPPROCEDURE-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropProcedureFactorObligation]:
    return [
        DropProcedureFactorObligation(
            ordinal=0,
            obligation_id=f"DROPPROCEDURE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropprocedure:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropProcedureFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-procedure-factor-obligations-v1\n")
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
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks eleven
# pairs as expected_failure, and the bounded extension crosses
# privilege_level, target_procedure_not_exists, and dependent_objects
# negatives whose SQLSTATEs are resolved here too.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_procedure_declared_failure",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "undefined_procedure_absent",
    ),
    ("object_state", "different_signature_exists"): (
        "42883",
        "undefined_procedure_signature_mismatch",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "insufficient_procedure_privilege",
    ),
    ("permission_insufficient", "not_owner"): (
        "42501",
        "insufficient_procedure_privilege_not_owner",
    ),
    ("target_procedure_not_exists", "without_IF_EXISTS_error"): (
        "42704",
        "undefined_procedure_no_if_exists",
    ),
    ("target_procedure_different_type", "same_name_is_function"): (
        "42809",
        "wrong_object_type_not_procedure",
    ),
    ("schema_dependency", "schema_not_exists"): (
        "3F000",
        "invalid_schema_name",
    ),
    ("argtype_specification", "without_signature_multiple"): (
        "42725",
        "procedure_not_unique",
    ),
    ("dependent_objects", "has_dependents_restrict_blocks"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependent_objects", "has_dependents_cascade_removes"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("restrict_with_dependencies", "restrict_failure_with_dependencies"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
}


def _expected_failure_details(
    obligation: DropProcedureFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropProcedureFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  The default policy
# is cascade_restrict_clause=absent (RESTRICT) and if_exists_clause=absent,
# matching the matrix defaults.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_procedure",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict_clause": "absent",
    "argtype_specification": "with_full_signature",
    "multiple_objects": "single_procedure",
    "procedure_name_shape": "simple",
    "privilege_level": "superuser",
    "dependent_objects": "no_dependencies",
    "schema_dependency": "schema_exists",
    "target_procedure_not_exists": "with_IF_EXISTS_noop",
    "target_procedure_different_type": "same_name_is_function",
    "permission_insufficient": "not_owner",
    "cascade_destroys_dependents": "cascade_removes_trigger",
    "identifier_length_exceeded": "over_63_chars",
    "verification_mode": "pg_proc_catalog_query",
    "cleanup_mode": "DROP_PROCEDURE_cascade",
}


def _baseline_assignments(
    obligation: DropProcedureFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise DropProcedureFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_procedure_factor_loop_plan(
    repository_root: Path,
) -> DropProcedureFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_procedure_factor_loop_obligations(root)
    cases: list[DropProcedureFactorCase] = []
    delegated: list[DropProcedureFactorObligation] = []
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
            DropProcedureFactorCase(
                ordinal=ordinal,
                case_id=f"DROPPROCEDURE{ordinal:05d}",
                sql_filename=f"DROPPROCEDURE{ordinal:05d}.sql",
                object_prefix=f"dropprocedure_{ordinal:05d}_",
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
    plan = DropProcedureFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 43 or len(plan.delegated) != 0:
        raise DropProcedureFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 43
    ):
        raise DropProcedureFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 43:
        raise DropProcedureFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropProcedureFactorLoopPlan] = {}


def _build_drop_procedure_factor_plan_lazily(
    repository_root: Path,
) -> DropProcedureFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_procedure_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_procedure_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropProcedureFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropProcedureFactorObligation(
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
        raise DropProcedureFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropProcedureFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 40, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropProcedureFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropProcedureFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 43:
        raise DropProcedureFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropProcedureFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropProcedureFactorLoopError",
    "DropProcedureFactorObligation",
    "DropProcedureFactorCase",
    "DropProcedureFactorLoopPlan",
    "compile_drop_procedure_factor_loop_obligations",
    "build_drop_procedure_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_procedure_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
