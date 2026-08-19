"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER LANGUAGE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER LANGUAGE``.  ``alter_language.yaml`` marks column/table/relation
coverage ``not_applicable`` (a procedural-language DDL has no ``INV`` block),
so the canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 38 rows, one local obligation per row.

The official synopsis has two branches (``RENAME TO`` and ``OWNER TO``); the
grammar ledger freezes those two action skeletons as GRM obligations.  There
are no optional-keyword / alternative axes (the synopsis is minimal), so the
GRM count is 2.  A RISK pair (commit/rollback) exercises the transactional
DDL boundary, mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``ALTER LANGUAGE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterLanguageFactorLoopError(ValueError):
    """Raised when a frozen ALTER LANGUAGE obligation input drifts."""


@dataclass(frozen=True)
class AlterLanguageFactorObligation:
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
class AlterLanguageFactorCase:
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
class AlterLanguageFactorLoopPlan:
    obligations: tuple[AlterLanguageFactorObligation, ...]
    cases: tuple[AlterLanguageFactorCase, ...]
    delegated: tuple[AlterLanguageFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-alterlanguage.html).
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterlanguage"

# The two official synopsis action forms.  ALTER LANGUAGE has no optional
# keyword / alternative axes, so the GRM ledger is exactly these two action
# skeletons (no grammar axes, unlike ALTER FUNCTION).
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
)

# A representative branch (rename) used as the baseline consumer for
# statement-wide modifiers that are not bound to one sub-clause.
_REPRESENTATIVE_ACTION = "rename"

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, alter_action) are
# resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "target_object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "rename_conflict": "rename",
    "new_owner_shape": "owner_change",
    "privilege_context": _REPRESENTATIVE_ACTION,
    "ownership_boundary": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_rename": "rename",
    "branch_owner": "owner_change",
}

_ALTER_ACTION_CONSUMER: dict[str, str] = {
    "rename": "rename",
    "owner_change": "owner_change",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (verified against PG 18.4).  Best-effort attribution; the DB
# doublerun fork calibrates the exact SQLSTATEs.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "missing"),
        ("name_shape", "missing_object"),
        ("new_name_shape", "existing_name_conflict"),
        ("rename_conflict", "new_name_conflict"),
        ("new_owner_shape", "missing_role"),
        ("privilege_context", "non_owner"),
        ("privilege_context", "insufficient_privilege"),
        ("ownership_boundary", "non_owner"),
        ("invalid_combination", "object_type_mismatch"),
        ("invalid_combination", "syntax_valid_semantic_error"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterLanguageFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action":
        try:
            return _ALTER_ACTION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterLanguageFactorLoopError(
                f"unknown alter_action value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterLanguageFactorLoopError(
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


def _compile_grammar_obligations() -> list[AlterLanguageFactorObligation]:
    rows: list[AlterLanguageFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            AlterLanguageFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AL-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 2:
        raise AlterLanguageFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterLanguageFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_language")
    if len(catalog_rows) != 38:
        raise AlterLanguageFactorLoopError("canonical obligation count drift")
    rows: list[AlterLanguageFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterLanguageFactorObligation(
                ordinal=0,
                obligation_id=f"AL-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterLanguageFactorObligation]:
    return [
        AlterLanguageFactorObligation(
            ordinal=0,
            obligation_id=f"AL-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterlanguage:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterLanguageFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-language-factor-obligations-v1\n")
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
# value.  The DB doublerun fork calibrates these via a two-run comparison; the
# frozen counts and sha256s in the companion tests are the spec.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "expected_status_failure_language_not_found",
    ),
    ("target_object_state", "missing"): ("42704", "language_does_not_exist"),
    ("name_shape", "missing_object"): ("42704", "language_does_not_exist"),
    ("new_name_shape", "existing_name_conflict"): (
        "42710",
        "language_already_exists",
    ),
    ("rename_conflict", "new_name_conflict"): (
        "42710",
        "language_already_exists",
    ),
    ("new_owner_shape", "missing_role"): ("42704", "role_does_not_exist"),
    ("privilege_context", "non_owner"): (
        "42501",
        "must_be_owner_of_language",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "must_be_owner_of_language",
    ),
    ("ownership_boundary", "non_owner"): (
        "42501",
        "must_be_owner_of_language",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42601",
        "invalid_language_alter_combination",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "invalid_language_alter_combination",
    ),
}


def _expected_failure_details(
    obligation: AlterLanguageFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterLanguageFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: AlterLanguageFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "target_object_state": "exists",
        "expected_status": "success",
        "name_shape": "plain_identifier",
        "verification_mode": "catalog_query",
        "cleanup_mode": "drop_objects",
        "privilege_context": "owner",
        "ownership_boundary": "owner",
        "dependency_state": "ready",
        "rename_conflict": "new_name_available",
        "invalid_combination": "none",
    }
    if branch == _BRANCH_RENAME:
        assignments["new_name_shape"] = "plain_identifier"
    elif branch == _BRANCH_OWNER:
        assignments["new_owner_shape"] = "plain_role"
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterLanguageFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_language_factor_loop_plan(
    repository_root: Path,
) -> AlterLanguageFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_language_factor_loop_obligations(root)
    cases: list[AlterLanguageFactorCase] = []
    delegated: list[AlterLanguageFactorObligation] = []
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
            AlterLanguageFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERLANGUAGE{ordinal:05d}",
                sql_filename=f"ALTERLANGUAGE{ordinal:05d}.sql",
                object_prefix=f"alterlanguage_{ordinal:05d}_",
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
    plan = AlterLanguageFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 42 or len(plan.delegated) != 0:
        raise AlterLanguageFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 42:
        raise AlterLanguageFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 42:
        raise AlterLanguageFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_language_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterLanguageFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterLanguageFactorObligation(
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
    if len(rows) != 42:
        raise AlterLanguageFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterLanguageFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 38, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterLanguageFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterLanguageFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 42:
        raise AlterLanguageFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterLanguageFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterLanguageFactorLoopError",
    "AlterLanguageFactorObligation",
    "AlterLanguageFactorCase",
    "AlterLanguageFactorLoopPlan",
    "compile_alter_language_factor_loop_obligations",
    "build_alter_language_factor_loop_plan",
    "_obligation_multiset_sha256",
]
