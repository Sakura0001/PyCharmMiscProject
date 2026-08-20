"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP USER MAPPING.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP USER MAPPING``.  A ``DROP USER MAPPING`` DDL has no ``INV`` block,
so the canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 43 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP USER MAPPING [ IF EXISTS ] FOR { role_name | USER | CURRENT_USER |
CURRENT_ROLE | PUBLIC } SERVER server_name``); the grammar ledger freezes
that one action skeleton as a GRM obligation.  A RISK pair (commit/rollback)
exercises the transactional DDL boundary, mirroring the sibling statement
ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP USER MAPPING`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropUserMappingFactorLoopError(ValueError):
    """Raised when a frozen DROP USER MAPPING obligation input drifts."""


@dataclass(frozen=True)
class DropUserMappingFactorObligation:
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
class DropUserMappingFactorCase:
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
class DropUserMappingFactorLoopPlan:
    obligations: tuple[DropUserMappingFactorObligation, ...]
    cases: tuple[DropUserMappingFactorCase, ...]
    delegated: tuple[DropUserMappingFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-dropusermapping.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-dropusermapping"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_user_mapping",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_user_mapping"

# Every canonical factor maps to the single DROP USER MAPPING consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "user_specification": _REPRESENTATIVE_ACTION,
    "user_name_shape": _REPRESENTATIVE_ACTION,
    "server_name_shape": _REPRESENTATIVE_ACTION,
    "server_existence": _REPRESENTATIVE_ACTION,
    "authorization_path": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "self_mapping_only": _REPRESENTATIVE_ACTION,
    "nonexistent_mapping": _REPRESENTATIVE_ACTION,
    "nonexistent_server": _REPRESENTATIVE_ACTION,
    "server_dependency": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_user_mapping": "drop_user_mapping",
    "branch_drop_user_mapping_if_exists": "drop_user_mapping",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  The privilege
# boundary (42501) fires for non-privileged users dropping another's or a
# PUBLIC mapping.  The server-lookup boundary (42704) fires when the
# foreign server is absent.  The mapping-lookup boundary (42704) fires when
# the mapping is absent and IF EXISTS is omitted.  The user-lookup boundary
# (42704) fires for a nonexistent role name.  Kept minimal (Option-A
# marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("authorization_path", "non_privileged"),
        ("privilege_context", "non_privileged_session"),
        ("insufficient_privilege", "lacks_privilege"),
        ("self_mapping_only", "attempting_other_user_mapping"),
        ("nonexistent_mapping", "mapping_missing_without_if_exists"),
        ("nonexistent_server", "server_missing"),
        ("server_existence", "server_not_exists"),
        ("server_name_shape", "nonexistent_name"),
        ("object_state", "absent"),
        ("user_name_shape", "nonexistent_name"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropUserMappingFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropUserMappingFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropUserMappingFactorObligation]:
    rows: list[DropUserMappingFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropUserMappingFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPUSERMAPPING-GRM|{action.grammar_branch_id}|"
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
        raise DropUserMappingFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropUserMappingFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_user_mapping")
    if len(catalog_rows) != 43:
        raise DropUserMappingFactorLoopError("canonical obligation count drift")
    rows: list[DropUserMappingFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropUserMappingFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPUSERMAPPING-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropUserMappingFactorObligation]:
    return [
        DropUserMappingFactorObligation(
            ordinal=0,
            obligation_id=f"DROPUSERMAPPING-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-dropusermapping:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropUserMappingFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-user-mapping-factor-obligations-v1\n")
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
# PG18.4).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_user_mapping_declared_failure",
    ),
    ("authorization_path", "non_privileged"): (
        "42501",
        "insufficient_user_mapping_privilege",
    ),
    ("privilege_context", "non_privileged_session"): (
        "42501",
        "insufficient_user_mapping_privilege",
    ),
    ("insufficient_privilege", "lacks_privilege"): (
        "42501",
        "insufficient_user_mapping_privilege",
    ),
    ("self_mapping_only", "attempting_other_user_mapping"): (
        "42501",
        "insufficient_user_mapping_privilege",
    ),
    ("nonexistent_mapping", "mapping_missing_without_if_exists"): (
        "42704",
        "undefined_user_mapping_no_if_exists",
    ),
    ("nonexistent_server", "server_missing"): (
        "42704",
        "undefined_foreign_server",
    ),
    ("server_existence", "server_not_exists"): (
        "42704",
        "undefined_foreign_server",
    ),
    ("server_name_shape", "nonexistent_name"): (
        "42704",
        "undefined_foreign_server_name",
    ),
    ("object_state", "absent"): (
        "42704",
        "undefined_user_mapping_absent",
    ),
    ("user_name_shape", "nonexistent_name"): (
        "42704",
        "undefined_role_name",
    ),
}


def _expected_failure_details(
    obligation: DropUserMappingFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropUserMappingFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "present" (the safe IF EXISTS form).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_user_mapping",
    "grammar_branch": "branch_1",
    "target_action": "drop_user_mapping",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "user_specification": "named_user",
    "user_name_shape": "simple_id",
    "server_name_shape": "simple_id",
    "server_existence": "server_exists",
    "authorization_path": "server_owner",
    "privilege_context": "server_owner_session",
    "insufficient_privilege": "has_privilege",
    "self_mapping_only": "deleting_own_mapping",
    "nonexistent_mapping": "mapping_exists",
    "nonexistent_server": "server_exists",
    "server_dependency": "server_exists_and_valid",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_user_mapping",
}

# Baseline primaries whose target mapping is intentionally absent, so the
# DROP surfaces a not-found error (42704) and the oracle asserts absence.
# For these the renderer forces if_exists_clause=absent so the missing
# mapping surfaces a hard error rather than an IF EXISTS notice.
_ABSENT_MAPPING_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("nonexistent_mapping", "mapping_missing_without_if_exists"),
        ("user_name_shape", "nonexistent_name"),
    }
)

# Baseline primaries whose target server is intentionally absent, so the
# DROP surfaces a server-missing error (42704).
_SERVER_MISSING_PRIMARIES = frozenset(
    {
        ("nonexistent_server", "server_missing"),
        ("server_existence", "server_not_exists"),
        ("server_name_shape", "nonexistent_name"),
    }
)

# Baseline primaries whose target role name is intentionally nonexistent.
_USER_MISSING_PRIMARIES = frozenset(
    {
        ("user_name_shape", "nonexistent_name"),
    }
)

# Baseline primaries that imply a non-privileged session role (privilege
# failure, 42501).
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("authorization_path", "non_privileged"),
        ("privilege_context", "non_privileged_session"),
        ("insufficient_privilege", "lacks_privilege"),
        ("self_mapping_only", "attempting_other_user_mapping"),
    }
)


def _baseline_assignments(
    obligation: DropUserMappingFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_MAPPING_PRIMARIES:
        assignments["if_exists_clause"] = "absent"
    if obligation.factor_key == "statement_branch":
        if obligation.value == "branch_drop_user_mapping_if_exists":
            assignments["if_exists_clause"] = "present"
    if (obligation.factor_key, obligation.value) in _PRIVILEGE_PRIMARIES:
        assignments["authorization_path"] = "non_privileged"
        assignments["privilege_context"] = "non_privileged_session"
        assignments["insufficient_privilege"] = "lacks_privilege"
        assignments["self_mapping_only"] = "attempting_other_user_mapping"
    if (obligation.factor_key, obligation.value) in _SERVER_MISSING_PRIMARIES:
        assignments["server_existence"] = "server_not_exists"
        assignments["nonexistent_server"] = "server_missing"
        assignments["server_dependency"] = "server_missing"
    if (obligation.factor_key, obligation.value) in _USER_MISSING_PRIMARIES:
        assignments["user_specification"] = "named_user"
    if len(assignments) != len(set(assignments)):
        raise DropUserMappingFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_user_mapping_factor_loop_plan(
    repository_root: Path,
) -> DropUserMappingFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_user_mapping_factor_loop_obligations(root)
    cases: list[DropUserMappingFactorCase] = []
    delegated: list[DropUserMappingFactorObligation] = []
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
            DropUserMappingFactorCase(
                ordinal=ordinal,
                case_id=f"DROPUSERMAPPING{ordinal:05d}",
                sql_filename=f"DROPUSERMAPPING{ordinal:05d}.sql",
                object_prefix=f"dropusermapping_{ordinal:05d}_",
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
    plan = DropUserMappingFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 46 or len(plan.delegated) != 0:
        raise DropUserMappingFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 46
    ):
        raise DropUserMappingFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 46:
        raise DropUserMappingFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropUserMappingFactorLoopPlan] = {}


def _build_drop_user_mapping_factor_plan_lazily(
    repository_root: Path,
) -> DropUserMappingFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_user_mapping_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_user_mapping_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropUserMappingFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropUserMappingFactorObligation(
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
        raise DropUserMappingFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropUserMappingFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 43, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropUserMappingFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropUserMappingFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 46:
        raise DropUserMappingFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropUserMappingFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropUserMappingFactorLoopError",
    "DropUserMappingFactorObligation",
    "DropUserMappingFactorCase",
    "DropUserMappingFactorLoopPlan",
    "compile_drop_user_mapping_factor_loop_obligations",
    "build_drop_user_mapping_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_user_mapping_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
