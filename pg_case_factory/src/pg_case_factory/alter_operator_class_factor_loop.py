"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER OPERATOR CLASS.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER OPERATOR CLASS``.  ``alter_operator_class.yaml`` marks
relation/table/column-type coverage ``not_applicable`` (an operator-class DDL
names an operator class identified by ``(name, index_method)``, not a
relation), so the canonical SFV obligations are derived one-to-one from the
shipped applicability matrix: exactly 46 rows, one local obligation per row.

The official synopsis has three branches (``RENAME TO``, ``OWNER TO``, and
``SET SCHEMA``).  The grammar ledger freezes one action skeleton per declared
``alter_action_type`` (3 actions) as GRM obligations; there are no optional
keyword / alternative axes beyond the three action forms (operator classes have
no estimator/optimizer sub-clauses, unlike ``ALTER OPERATOR``).  A RISK pair
(commit/rollback) exercises the transactional DDL boundary, mirroring the
sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``ALTER OPERATOR CLASS`` error that belongs to this statement.  The
``dependency_state = missing_dependency`` value is intentionally a covered
(inert) baseline: ``ALTER OPERATOR CLASS`` performs no dependency check (there
is no bound estimator procedure whose absence would surface as a failure), so
the missing-dependency axis is witnessed as a labelled success.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterOperatorClassFactorLoopError(ValueError):
    """Raised when a frozen ALTER OPERATOR CLASS obligation input drifts."""


@dataclass(frozen=True)
class AlterOperatorClassFactorObligation:
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
class AlterOperatorClassFactorCase:
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
class AlterOperatorClassFactorLoopPlan:
    obligations: tuple[AlterOperatorClassFactorObligation, ...]
    cases: tuple[AlterOperatorClassFactorCase, ...]
    delegated: tuple[AlterOperatorClassFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-alteropclass.html).
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET_SCHEMA = "branch_set_schema"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alteropclass"

# One grammar action skeleton per declared alter_action_type.  ALTER OPERATOR
# CLASS has three synopsis branches and three action forms (RENAME TO, OWNER TO,
# SET SCHEMA); the GRM ledger freezes one skeleton per action form.
@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="rename",
        grammar_branch_id=_BRANCH_RENAME,
        source_locator=f"{_DOC_SOURCE}:synopsis-rename",
    ),
    _GrammarAction(
        action_id="owner_change",
        grammar_branch_id=_BRANCH_OWNER,
        source_locator=f"{_DOC_SOURCE}:synopsis-owner",
    ),
    _GrammarAction(
        action_id="set_schema",
        grammar_branch_id=_BRANCH_SET_SCHEMA,
        source_locator=f"{_DOC_SOURCE}:synopsis-set-schema",
    ),
)

# A representative branch_rename action used as the baseline consumer for
# statement-wide modifiers that are not bound to one sub-clause.
_REPRESENTATIVE_ACTION = "rename"

# Canonical factor -> the action where the value is observable.  Factors whose
# consumer depends on the value (statement_branch, alter_action_type) are
# resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "target_object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "new_owner_shape": "owner_change",
    "privilege_context": _REPRESENTATIVE_ACTION,
    "ownership_boundary": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "index_method_shape": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
    "rename_conflict": "rename",
    "schema_migration_state": "set_schema",
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_rename": "rename",
    "branch_owner": "owner_change",
    "branch_set_schema": "set_schema",
}

_ACTION_TYPE_CONSUMER: dict[str, str] = {
    "rename": "rename",
    "owner_change": "owner_change",
    "set_schema": "set_schema",
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterOperatorClassFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action_type":
        try:
            return _ACTION_TYPE_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterOperatorClassFactorLoopError(
                f"unknown alter_action_type value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterOperatorClassFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _consumer_branch_map() -> dict[str, str]:
    return {
        action.action_id: action.grammar_branch_id
        for action in _GRAMMAR_ACTIONS
    }


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


def _compile_grammar_obligations() -> list[AlterOperatorClassFactorObligation]:
    rows: list[AlterOperatorClassFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            AlterOperatorClassFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AOC-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 3:
        raise AlterOperatorClassFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterOperatorClassFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_operator_class")
    if len(catalog_rows) != 46:
        raise AlterOperatorClassFactorLoopError("canonical obligation count drift")
    rows: list[AlterOperatorClassFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterOperatorClassFactorObligation(
                ordinal=0,
                obligation_id=f"AOC-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterOperatorClassFactorObligation]:
    return [
        AlterOperatorClassFactorObligation(
            ordinal=0,
            obligation_id=f"AOC-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alteropclass:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterOperatorClassFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-operator-class-factor-obligations-v1\n")
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


# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (verified against PG 18.4 best-effort; the DB doublerun fork
# calibrates the exact SQLSTATEs).  ``dependency_state=missing_dependency`` is
# intentionally absent: operator classes have no bound estimator procedure, so
# the missing-dependency boundary never surfaces during an ALTER (it is a
# labelled inert success in the marginal baseline).
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "missing"),
        ("new_owner_shape", "missing_role"),
        ("rename_conflict", "new_name_conflict"),
        ("schema_migration_state", "target_schema_missing"),
        ("schema_migration_state", "target_schema_conflict"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("privilege_context", "non_owner"),
        ("privilege_context", "insufficient_privilege"),
        ("ownership_boundary", "non_owner"),
    }
)

# Best-effort PG 18.4 SQLSTATE attribution for each reachable expected-failure
# value.  The DB doublerun fork calibrates these via a two-run comparison; the
# frozen counts and sha256s in the companion tests are the spec.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "alter_operator_class_declared_failure",
    ),
    ("target_object_state", "missing"): (
        "42704",
        "operator_class_does_not_exist",
    ),
    ("new_owner_shape", "missing_role"): ("42704", "missing_owner_role"),
    ("rename_conflict", "new_name_conflict"): (
        "42710",
        "operator_class_name_conflict",
    ),
    ("schema_migration_state", "target_schema_missing"): (
        "3F000",
        "missing_target_schema",
    ),
    ("schema_migration_state", "target_schema_conflict"): (
        "42710",
        "operator_class_schema_conflict",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "invalid_operator_class_alter_combination",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "wrong_object_type",
    ),
    ("privilege_context", "non_owner"): (
        "42501",
        "insufficient_operator_class_privilege",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_operator_class_privilege",
    ),
    ("ownership_boundary", "non_owner"): (
        "42501",
        "insufficient_operator_class_privilege",
    ),
}


def _expected_failure_details(
    obligation: AlterOperatorClassFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterOperatorClassFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: AlterOperatorClassFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "statement_branch": branch,
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "target_object_state": "exists",
        "expected_status": "success",
        "name_shape": "plain_identifier",
        "index_method_shape": "btree",
        "new_owner_shape": "plain_role",
        "privilege_context": "superuser",
        "ownership_boundary": "superuser",
        "dependency_state": "ready",
        "rename_conflict": "new_name_available",
        "schema_migration_state": "target_schema_exists",
        "invalid_combination": "none",
        "verification_mode": "catalog_query",
        "cleanup_mode": "drop_objects",
    }
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterOperatorClassFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_operator_class_factor_loop_plan(
    repository_root: Path,
) -> AlterOperatorClassFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_operator_class_factor_loop_obligations(root)
    cases: list[AlterOperatorClassFactorCase] = []
    delegated: list[AlterOperatorClassFactorObligation] = []
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
            AlterOperatorClassFactorCase(
                ordinal=ordinal,
                case_id=f"ALTEROPERATORCLASS{ordinal:05d}",
                sql_filename=f"ALTEROPERATORCLASS{ordinal:05d}.sql",
                object_prefix=f"alteroperatorclass_{ordinal:05d}_",
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
    plan = AlterOperatorClassFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 51 or len(plan.delegated) != 0:
        raise AlterOperatorClassFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 51:
        raise AlterOperatorClassFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 51:
        raise AlterOperatorClassFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_operator_class_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterOperatorClassFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterOperatorClassFactorObligation(
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
    if len(rows) != 51:
        raise AlterOperatorClassFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterOperatorClassFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 3, "SFV": 46, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterOperatorClassFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterOperatorClassFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 51:
        raise AlterOperatorClassFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterOperatorClassFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterOperatorClassFactorLoopError",
    "AlterOperatorClassFactorObligation",
    "AlterOperatorClassFactorCase",
    "AlterOperatorClassFactorLoopPlan",
    "compile_alter_operator_class_factor_loop_obligations",
    "build_alter_operator_class_factor_loop_plan",
    "_obligation_multiset_sha256",
]
