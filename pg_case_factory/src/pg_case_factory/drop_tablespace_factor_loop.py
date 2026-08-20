"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP TABLESPACE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP TABLESPACE``.  A ``DROP TABLESPACE`` DDL has no ``INV`` block, so the
canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 42 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP TABLESPACE [ IF EXISTS ] name``); the grammar ledger freezes that
one action skeleton as a GRM obligation.  A RISK pair (commit/rollback)
exercises the transactional DDL boundary, mirroring the sibling DROP
statement ledgers.  PG18.4 ``DROP TABLESPACE`` cannot run inside a
transaction block and supports no CASCADE/RESTRICT clause.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP TABLESPACE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropTablespaceFactorLoopError(ValueError):
    """Raised when a frozen DROP TABLESPACE obligation input drifts."""


@dataclass(frozen=True)
class DropTablespaceFactorObligation:
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
class DropTablespaceFactorCase:
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
class DropTablespaceFactorLoopPlan:
    obligations: tuple[DropTablespaceFactorObligation, ...]
    cases: tuple[DropTablespaceFactorCase, ...]
    delegated: tuple[DropTablespaceFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-droptablespace.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-droptablespace"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_tablespace",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_tablespace"

# Every canonical factor maps to the single DROP TABLESPACE consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "authorization_path": _REPRESENTATIVE_ACTION,
    "object_occupancy": _REPRESENTATIVE_ACTION,
    "tablespace_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "dependency_context": _REPRESENTATIVE_ACTION,
    "environment_context": _REPRESENTATIVE_ACTION,
    "error_type": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_tablespace": "drop_tablespace",
    "branch_drop_tablespace_if_exists": "drop_tablespace",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  authorization_path=
# non_owner_non_superuser inherently fails (42501) because DROP TABLESPACE
# requires ownership.  object_state=absent / tablespace_name_shape=
# non_existent_name inherently error (42704) when IF EXISTS is omitted (the
# renderer forces if_exists_clause=absent for these primaries so the missing
# tablespace surfaces a hard 42704).  object_occupancy/dependency/temp values
# represent an occupied tablespace (55006 provisional).  environment_context=
# inside_transaction_block fails because DROP TABLESPACE cannot run in a txn
# (25001 provisional).  Kept minimal (Option-A marginal); cross-product
# failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("tablespace_name_shape", "non_existent_name"),
        ("authorization_path", "non_owner_non_superuser"),
        ("privilege_context", "non_owner_session"),
        ("object_occupancy", "has_objects_in_current_db"),
        ("object_occupancy", "has_objects_in_other_db"),
        ("object_occupancy", "has_temp_files"),
        ("dependency_context", "objects_in_current_db"),
        ("dependency_context", "objects_in_other_db"),
        ("dependency_context", "temp_tablespace_active"),
        ("environment_context", "inside_transaction_block"),
        ("environment_context", "active_temp_tablespaces"),
        ("error_type", "non_existent_without_if_exists"),
        ("error_type", "occupied_tablespace"),
        ("error_type", "insufficient_privilege"),
        ("error_type", "inside_transaction_block"),
        ("error_type", "temp_tablespace_in_use"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropTablespaceFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropTablespaceFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropTablespaceFactorObligation]:
    rows: list[DropTablespaceFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropTablespaceFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTABLESPACE-GRM|{action.grammar_branch_id}|"
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
        raise DropTablespaceFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropTablespaceFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_tablespace")
    if len(catalog_rows) != 42:
        raise DropTablespaceFactorLoopError("canonical obligation count drift")
    rows: list[DropTablespaceFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropTablespaceFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTABLESPACE-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropTablespaceFactorObligation]:
    return [
        DropTablespaceFactorObligation(
            ordinal=0,
            obligation_id=f"DROPTABLESPACE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-droptablespace:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropTablespaceFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-tablespace-factor-obligations-v1\n")
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
# PG18.4).  42704=undefined_object, 42501=insufficient_privilege,
# 55006=object_in_use (occupied/temp), 25001=active_sql_transaction
# (cannot run inside a transaction block).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_tablespace_declared_failure",
    ),
    ("object_state", "absent"): (
        "42704",
        "undefined_tablespace_absent",
    ),
    ("tablespace_name_shape", "non_existent_name"): (
        "42704",
        "undefined_tablespace_name",
    ),
    ("authorization_path", "non_owner_non_superuser"): (
        "42501",
        "insufficient_tablespace_privilege",
    ),
    ("privilege_context", "non_owner_session"): (
        "42501",
        "insufficient_tablespace_privilege",
    ),
    ("object_occupancy", "has_objects_in_current_db"): (
        "55006",
        "occupied_tablespace_not_empty",
    ),
    ("object_occupancy", "has_objects_in_other_db"): (
        "55006",
        "occupied_tablespace_not_empty",
    ),
    ("object_occupancy", "has_temp_files"): (
        "55006",
        "temp_tablespace_in_use",
    ),
    ("dependency_context", "objects_in_current_db"): (
        "55006",
        "occupied_tablespace_not_empty",
    ),
    ("dependency_context", "objects_in_other_db"): (
        "55006",
        "occupied_tablespace_not_empty",
    ),
    ("dependency_context", "temp_tablespace_active"): (
        "55006",
        "temp_tablespace_in_use",
    ),
    ("environment_context", "inside_transaction_block"): (
        "25001",
        "drop_tablespace_in_transaction_block",
    ),
    ("environment_context", "active_temp_tablespaces"): (
        "55006",
        "temp_tablespace_in_use",
    ),
    ("error_type", "non_existent_without_if_exists"): (
        "42704",
        "undefined_tablespace_no_if_exists",
    ),
    ("error_type", "occupied_tablespace"): (
        "55006",
        "occupied_tablespace_not_empty",
    ),
    ("error_type", "insufficient_privilege"): (
        "42501",
        "insufficient_tablespace_privilege",
    ),
    ("error_type", "inside_transaction_block"): (
        "25001",
        "drop_tablespace_in_transaction_block",
    ),
    ("error_type", "temp_tablespace_in_use"): (
        "55006",
        "temp_tablespace_in_use",
    ),
}


def _expected_failure_details(
    obligation: DropTablespaceFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropTablespaceFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "present" (the safe IF EXISTS form) and the tablespace is empty + exists.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_tablespace",
    "grammar_branch": "branch_1",
    "target_action": "drop_tablespace",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "authorization_path": "superuser",
    "object_occupancy": "empty",
    "tablespace_name_shape": "simple_id",
    "privilege_context": "superuser_session",
    "dependency_context": "no_dependencies",
    "environment_context": "outside_transaction_block",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "remove_objects_first",
}

# Baseline primaries whose target tablespace is intentionally absent, so the
# DROP surfaces a not-found error (42704) and the oracle asserts absence.
# For these the renderer forces if_exists_clause=absent so the missing
# tablespace surfaces a hard error rather than an IF EXISTS notice.
_ABSENT_TABLESPACE_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("tablespace_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
    }
)

# Correlation between the two privilege axes.
_AUTH_PRIVILEGE_MAP: dict[str, str] = {
    "superuser": "superuser_session",
    "owner": "owner_session",
    "non_owner_non_superuser": "non_owner_session",
}
_PRIVILEGE_AUTH_MAP: dict[str, str] = {
    v: k for k, v in _AUTH_PRIVILEGE_MAP.items()
}

# Correlation between object_occupancy and dependency_context.
_OCCUPANCY_DEPENDENCY_MAP: dict[str, str] = {
    "empty": "no_dependencies",
    "has_objects_in_current_db": "objects_in_current_db",
    "has_objects_in_other_db": "objects_in_other_db",
    "has_temp_files": "temp_tablespace_active",
}
_DEPENDENCY_OCCUPANCY_MAP: dict[str, str] = {
    v: k for k, v in _OCCUPANCY_DEPENDENCY_MAP.items()
}

_TEMP_OCCUPANCY = "has_temp_files"
_TEMP_DEPENDENCY = "temp_tablespace_active"
_TEMP_ENVIRONMENT = "active_temp_tablespaces"


def _baseline_assignments(
    obligation: DropTablespaceFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value

    # Absent-tablespace primaries: force IF EXISTS omitted so 42704 surfaces.
    if (obligation.factor_key, obligation.value) in _ABSENT_TABLESPACE_PRIMARIES:
        assignments["if_exists_clause"] = "absent"

    # statement_branch=branch_drop_tablespace_if_exists implies IF EXISTS present.
    if obligation.factor_key == "statement_branch":
        if obligation.value == "branch_drop_tablespace_if_exists":
            assignments["if_exists_clause"] = "present"

    # Correlate the two privilege axes.
    if obligation.factor_key == "authorization_path":
        assignments["privilege_context"] = _AUTH_PRIVILEGE_MAP.get(
            obligation.value, assignments["privilege_context"]
        )
    if obligation.factor_key == "privilege_context":
        assignments["authorization_path"] = _PRIVILEGE_AUTH_MAP.get(
            obligation.value, assignments["authorization_path"]
        )

    # Correlate occupancy / dependency / temp environment.
    if obligation.factor_key == "object_occupancy":
        dep = _OCCUPANCY_DEPENDENCY_MAP.get(obligation.value)
        if dep is not None:
            assignments["dependency_context"] = dep
        if obligation.value == _TEMP_OCCUPANCY:
            assignments["environment_context"] = _TEMP_ENVIRONMENT
    if obligation.factor_key == "dependency_context":
        occ = _DEPENDENCY_OCCUPANCY_MAP.get(obligation.value)
        if occ is not None:
            assignments["object_occupancy"] = occ
        if obligation.value == _TEMP_DEPENDENCY:
            assignments["environment_context"] = _TEMP_ENVIRONMENT
    if obligation.factor_key == "environment_context":
        if obligation.value == _TEMP_ENVIRONMENT:
            assignments["object_occupancy"] = _TEMP_OCCUPANCY
            assignments["dependency_context"] = _TEMP_DEPENDENCY

    # error_type primaries imply their correlated behavior factors.
    if obligation.factor_key == "error_type":
        if obligation.value == "non_existent_without_if_exists":
            assignments["object_state"] = "absent"
            assignments["if_exists_clause"] = "absent"
        elif obligation.value == "occupied_tablespace":
            assignments["object_occupancy"] = "has_objects_in_current_db"
            assignments["dependency_context"] = "objects_in_current_db"
        elif obligation.value == "insufficient_privilege":
            assignments["authorization_path"] = "non_owner_non_superuser"
            assignments["privilege_context"] = "non_owner_session"
        elif obligation.value == "inside_transaction_block":
            assignments["environment_context"] = "inside_transaction_block"
        elif obligation.value == "temp_tablespace_in_use":
            assignments["object_occupancy"] = _TEMP_OCCUPANCY
            assignments["dependency_context"] = _TEMP_DEPENDENCY
            assignments["environment_context"] = _TEMP_ENVIRONMENT

    if len(assignments) != len(set(assignments)):
        raise DropTablespaceFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_tablespace_factor_loop_plan(
    repository_root: Path,
) -> DropTablespaceFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_tablespace_factor_loop_obligations(root)
    cases: list[DropTablespaceFactorCase] = []
    delegated: list[DropTablespaceFactorObligation] = []
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
            DropTablespaceFactorCase(
                ordinal=ordinal,
                case_id=f"DROPTABLESPACE{ordinal:05d}",
                sql_filename=f"DROPTABLESPACE{ordinal:05d}.sql",
                object_prefix=f"droptablespace_{ordinal:05d}_",
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
    plan = DropTablespaceFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 45 or len(plan.delegated) != 0:
        raise DropTablespaceFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 45
    ):
        raise DropTablespaceFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 45:
        raise DropTablespaceFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropTablespaceFactorLoopPlan] = {}


def _build_drop_tablespace_factor_plan_lazily(
    repository_root: Path,
) -> DropTablespaceFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_tablespace_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_tablespace_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropTablespaceFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropTablespaceFactorObligation(
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
    if len(rows) != 45:
        raise DropTablespaceFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropTablespaceFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 42, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropTablespaceFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropTablespaceFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 45:
        raise DropTablespaceFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropTablespaceFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropTablespaceFactorLoopError",
    "DropTablespaceFactorObligation",
    "DropTablespaceFactorCase",
    "DropTablespaceFactorLoopPlan",
    "compile_drop_tablespace_factor_loop_obligations",
    "build_drop_tablespace_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_tablespace_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
