"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP TYPE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP TYPE``.  A ``DROP TYPE`` DDL has no ``INV`` block, so the canonical
SFV obligations are derived one-to-one from the shipped applicability
matrix: exactly 43 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP TYPE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.
A RISK pair (commit/rollback) exercises the transactional DDL boundary,
mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP TYPE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropTypeFactorLoopError(ValueError):
    """Raised when a frozen DROP TYPE obligation input drifts."""


@dataclass(frozen=True)
class DropTypeFactorObligation:
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
class DropTypeFactorCase:
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
class DropTypeFactorLoopPlan:
    obligations: tuple[DropTypeFactorObligation, ...]
    cases: tuple[DropTypeFactorCase, ...]
    delegated: tuple[DropTypeFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-droptype.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-droptype"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_type",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_type"

# Every canonical factor maps to the single DROP TYPE consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "multi_type_drop": _REPRESENTATIVE_ACTION,
    "type_category": _REPRESENTATIVE_ACTION,
    "type_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "error_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_type": "drop_type",
    "branch_drop_type_if_exists": "drop_type",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  privilege_level=
# non_owner inherently fails (42501) because DROP TYPE requires ownership.
# object_state=not_exists / expected_status=failure / error_boundary=
# non_existent_without_if_exists inherently error (42704) because the
# baseline default for if_exists_clause is "absent" so the missing type
# surfaces a 42704 instead of a notice.  dependency_state=used_in_* under
# RESTRICT inherently errors (2BP01).  error_boundary=insufficient_privilege
# and dependent_objects_without_cascade mirror the privilege/dependency
# boundaries.  Kept minimal (Option-A marginal); cross-product failures
# live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("privilege_level", "non_owner"),
        ("dependency_state", "used_in_table_columns"),
        ("dependency_state", "used_in_function_params"),
        ("dependency_state", "used_in_operators"),
        ("dependency_state", "used_in_typed_tables"),
        ("error_boundary", "non_existent_without_if_exists"),
        ("error_boundary", "dependent_objects_without_cascade"),
        ("error_boundary", "insufficient_privilege"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropTypeFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropTypeFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropTypeFactorObligation]:
    rows: list[DropTypeFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropTypeFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTYPE-GRM|{action.grammar_branch_id}|"
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
        raise DropTypeFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropTypeFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_type")
    if len(catalog_rows) != 43:
        raise DropTypeFactorLoopError("canonical obligation count drift")
    rows: list[DropTypeFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropTypeFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTYPE-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropTypeFactorObligation]:
    return [
        DropTypeFactorObligation(
            ordinal=0,
            obligation_id=f"DROPTYPE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-droptype:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropTypeFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-type-factor-obligations-v1\n")
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
# SQLSTATEs are provisional in the no-DB phase (a later DB phase verifies on
# PG18.4).  The privilege boundary (42501) fires when the caller is not the
# type owner.  The not-exist boundary (42704) fires when the type is absent
# and IF EXISTS is omitted.  The dependency boundary (2BP01) fires under
# RESTRICT (or default RESTRICT) with dependents.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_type_declared_failure",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "undefined_type_absent",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_type_privilege",
    ),
    ("dependency_state", "used_in_table_columns"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_state", "used_in_function_params"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_state", "used_in_operators"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_state", "used_in_typed_tables"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("error_boundary", "non_existent_without_if_exists"): (
        "42704",
        "undefined_type_no_if_exists",
    ),
    ("error_boundary", "dependent_objects_without_cascade"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("error_boundary", "insufficient_privilege"): (
        "42501",
        "insufficient_type_privilege",
    ),
}


def _expected_failure_details(
    obligation: DropTypeFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropTypeFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "absent" (the plain DROP TYPE form) and cascade_restrict is "none" (RESTRICT
# is the default behavior).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_type",
    "grammar_branch": "branch_1",
    "target_action": "drop_type",
    "object_state": "exists_composite",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "multi_type_drop": "single_type",
    "type_category": "composite",
    "type_name_shape": "simple",
    "privilege_level": "superuser",
    "dependency_state": "no_dependents",
    "error_boundary": "none",
    "verification_mode": "pg_type_query",
    "cleanup_mode": "no_cleanup_needed",
}

# Baseline primaries whose target type is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.  For
# these the renderer forces if_exists_clause=absent so the missing type
# surfaces a hard error rather than an IF EXISTS notice.
_ABSENT_TYPE_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("error_boundary", "non_existent_without_if_exists"),
    }
)

# object_state <-> type_category pairing (the exists_* value encodes the
# category, so the two must stay consistent in the baseline).
_OBJECT_STATE_CATEGORY: dict[str, str] = {
    "exists_composite": "composite",
    "exists_enum": "enum",
    "exists_range": "range",
    "exists_base": "base",
}


def _baseline_assignments(
    obligation: DropTypeFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_TYPE_PRIMARIES:
        assignments["if_exists_clause"] = "absent"
        assignments["object_state"] = "not_exists"
        assignments["expected_status"] = "failure"
        assignments["error_boundary"] = "non_existent_without_if_exists"
    if obligation.factor_key == "statement_branch":
        # statement_branch=branch_drop_type_if_exists implies IF EXISTS present.
        if obligation.value == "branch_drop_type_if_exists":
            assignments["if_exists_clause"] = "present"
    if obligation.factor_key == "if_exists_clause":
        if obligation.value == "present":
            assignments["statement_branch"] = "branch_drop_type_if_exists"
    if obligation.factor_key == "object_state":
        category = _OBJECT_STATE_CATEGORY.get(obligation.value)
        if category is not None:
            assignments["type_category"] = category
    if obligation.factor_key == "type_category":
        for state, cat in _OBJECT_STATE_CATEGORY.items():
            if cat == obligation.value:
                assignments["object_state"] = state
                break
    if obligation.factor_key == "privilege_level":
        if obligation.value == "non_owner":
            assignments["error_boundary"] = "insufficient_privilege"
    if obligation.factor_key == "dependency_state":
        if obligation.value != "no_dependents":
            assignments["cascade_restrict"] = "restrict"
            assignments["error_boundary"] = (
                "dependent_objects_without_cascade"
            )
    if obligation.factor_key == "error_boundary":
        if obligation.value == "dependent_objects_without_cascade":
            assignments["cascade_restrict"] = "restrict"
            assignments["dependency_state"] = "used_in_table_columns"
        elif obligation.value == "insufficient_privilege":
            assignments["privilege_level"] = "non_owner"
        elif obligation.value == "non_existent_without_if_exists":
            assignments["object_state"] = "not_exists"
            assignments["if_exists_clause"] = "absent"
            assignments["expected_status"] = "failure"
    if len(assignments) != len(set(assignments)):
        raise DropTypeFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_type_factor_loop_plan(
    repository_root: Path,
) -> DropTypeFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_type_factor_loop_obligations(root)
    cases: list[DropTypeFactorCase] = []
    delegated: list[DropTypeFactorObligation] = []
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
            DropTypeFactorCase(
                ordinal=ordinal,
                case_id=f"DROPTYPE{ordinal:05d}",
                sql_filename=f"DROPTYPE{ordinal:05d}.sql",
                object_prefix=f"droptype_{ordinal:05d}_",
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
    plan = DropTypeFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 46 or len(plan.delegated) != 0:
        raise DropTypeFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 46
    ):
        raise DropTypeFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 46:
        raise DropTypeFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropTypeFactorLoopPlan] = {}


def _build_drop_type_factor_plan_lazily(
    repository_root: Path,
) -> DropTypeFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_type_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_type_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropTypeFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropTypeFactorObligation(
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
    if len(rows) != 46:
        raise DropTypeFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropTypeFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 43, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropTypeFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropTypeFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 46:
        raise DropTypeFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropTypeFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropTypeFactorLoopError",
    "DropTypeFactorObligation",
    "DropTypeFactorCase",
    "DropTypeFactorLoopPlan",
    "compile_drop_type_factor_loop_obligations",
    "build_drop_type_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_type_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
