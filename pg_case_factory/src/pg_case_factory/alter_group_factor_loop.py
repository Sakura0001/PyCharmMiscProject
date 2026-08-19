"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER GROUP.

This module compiles the marginal ``SFV``/``RISK`` obligation ledger for
``ALTER GROUP``.  ``ALTER GROUP`` has no grammar axis beyond the
canonical factors (every syntactic alternative is already an ``SFV``
row), so ``GRM`` compiles to ``0``; ``alter_group.yaml`` marks
column/table/relation coverage ``not_applicable``, so there is no
``INV`` block.  Each local obligation becomes exactly one regress
program; there are no delegated handoffs because every reachable
negative boundary is a real ``ALTER GROUP`` error that belongs to this
statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_group_regress import AlterGroupRegressError
from .applicability import load_shipped_applicability_universe


class AlterGroupFactorLoopError(ValueError):
    """Raised when a frozen ALTER GROUP obligation input drifts."""


@dataclass(frozen=True)
class AlterGroupFactorObligation:
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
class AlterGroupFactorCase:
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
class AlterGroupFactorLoopPlan:
    obligations: tuple[AlterGroupFactorObligation, ...]
    cases: tuple[AlterGroupFactorCase, ...]
    delegated: tuple[AlterGroupFactorObligation, ...]
    obligation_multiset_sha256: str


# A representative branch_1 action used as the baseline consumer for
# factors whose consumer does not depend on the value.
_REPRESENTATIVE_ACTION = "add_user"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    "branch_add_user": "add_user",
    "branch_drop_user": "drop_user",
    "branch_rename": "rename",
}

# deprecated_equivalence canonical value -> the branch whose modern
# equivalent it documents.
_DEPRECATED_EQUIVALENCE_CONSUMER = {
    "add_user_equals_grant": "add_user",
    "drop_user_equals_revoke": "drop_user",
    "rename_equals_alter_role": "rename",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, alter_action,
# deprecated_equivalence) are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "role_specification": _REPRESENTATIVE_ACTION,
    "multi_user": _REPRESENTATIVE_ACTION,
    "deprecated_command_note": _REPRESENTATIVE_ACTION,
    "group_name_shape": _REPRESENTATIVE_ACTION,
    "user_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "user_existence": _REPRESENTATIVE_ACTION,
    "target_role_admin": _REPRESENTATIVE_ACTION,
    "nonexistent_group": _REPRESENTATIVE_ACTION,
    "nonexistent_user": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "non_admin_attempt": _REPRESENTATIVE_ACTION,
    "duplicate_add_user": "add_user",
    "drop_non_member_user": "drop_user",
    "rename_to_existing_name": "rename",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterGroupFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action":
        # alter_action values are themselves the action identifiers.
        if row.value not in ("add_user", "drop_user", "rename"):
            raise AlterGroupFactorLoopError(
                f"unknown alter_action value: {row.value}"
            )
        return row.value
    if row.factor == "deprecated_equivalence":
        try:
            return _DEPRECATED_EQUIVALENCE_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterGroupFactorLoopError(
                f"unknown deprecated_equivalence value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterGroupFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (SQLSTATEs verified against PG 18.4 in Task 6).  The
# NOTICE-boundary values ``duplicate_add_user=existing_member`` and
# ``drop_non_member_user=non_member`` are NOT here: they succeed with a
# NOTICE rather than an error.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("group_name_shape", "nonexistent_name"),
        ("user_name_shape", "nonexistent_user"),
        ("user_existence", "user_not_exists"),
        ("nonexistent_group", "group_missing"),
        ("nonexistent_user", "user_missing"),
        ("new_name_shape", "duplicate_name"),
        ("rename_to_existing_name", "same_name_conflict"),
        ("privilege_level", "non_admin"),
        ("insufficient_privilege", "insufficient_privilege"),
        ("non_admin_attempt", "non_admin_execution"),
        ("target_role_admin", "lacks_admin"),
    }
)


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterGroupFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_group")
    if len(catalog_rows) != 57:
        raise AlterGroupFactorLoopError("canonical obligation count drift")
    rows: list[AlterGroupFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterGroupFactorObligation(
                ordinal=0,
                obligation_id=f"AG-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterGroupFactorObligation]:
    return [
        AlterGroupFactorObligation(
            ordinal=0,
            obligation_id=f"AG-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-altergroup:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterGroupFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-group-factor-obligations-v1\n")
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


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    return factor_key


# Verified PG 18.4 SQLSTATE for each reachable expected-failure value.
# These are probed against an isolated 18.4 instance under the
# group-role-admin baseline in Task 6; the table is corrected there if
# the deprecated RENAME path surfaces a different code.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): ("42704", "target_role_missing"),
    ("object_state", "not_exists"): ("42704", "role_does_not_exist"),
    ("group_name_shape", "nonexistent_name"): (
        "42704",
        "role_does_not_exist",
    ),
    ("user_name_shape", "nonexistent_user"): (
        "42704",
        "role_does_not_exist",
    ),
    ("user_existence", "user_not_exists"): ("42704", "role_does_not_exist"),
    ("nonexistent_group", "group_missing"): ("42704", "role_does_not_exist"),
    ("nonexistent_user", "user_missing"): ("42704", "role_does_not_exist"),
    ("new_name_shape", "duplicate_name"): ("42710", "role_already_exists"),
    ("rename_to_existing_name", "same_name_conflict"): (
        "42710",
        "role_already_exists",
    ),
    ("privilege_level", "non_admin"): ("42501", "permission_denied"),
    ("insufficient_privilege", "insufficient_privilege"): (
        "42501",
        "permission_denied",
    ),
    ("non_admin_attempt", "non_admin_execution"): (
        "42501",
        "permission_denied",
    ),
    ("target_role_admin", "lacks_admin"): ("42501", "permission_denied"),
}


def _expected_failure_details(
    obligation: AlterGroupFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterGroupFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Branch-derived canonical defaults.  The baseline sets statement_branch,
# alter_action and deprecated_equivalence consistently from the consumer
# branch so the renderer never sees a contradictory trio.
_ACTION_BRANCH = {
    "add_user": "branch_add_user",
    "drop_user": "branch_drop_user",
    "rename": "branch_rename",
}

_BRANCH_DEPRECATED_EQUIVALENCE = {
    "branch_add_user": "add_user_equals_grant",
    "branch_drop_user": "drop_user_equals_revoke",
    "branch_rename": "rename_equals_alter_role",
}

_BASELINE_DEFAULTS: dict[str, str] = {
    "object_state": "exists",
    "expected_status": "success",
    "role_specification": "role_name",
    "multi_user": "single_user",
    "deprecated_command_note": "deprecated_no_warning",
    "group_name_shape": "simple_id",
    "user_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "privilege_level": "group_role_admin",
    "user_existence": "user_exists",
    "target_role_admin": "has_admin",
    "nonexistent_group": "group_exists",
    "nonexistent_user": "user_exists",
    "insufficient_privilege": "sufficient_privilege",
    "non_admin_attempt": "admin_execution",
    "duplicate_add_user": "new_member",
    "drop_non_member_user": "existing_member",
    "rename_to_existing_name": "no_conflict",
    "verification_mode": "pg_auth_members_catalog",
    "cleanup_mode": "revoke_membership",
}

# The four privilege factors model the same admin-or-not dimension.  Keep
# them mutually consistent with the primary so a single non-admin
# executor is the attributable cause rather than four contradictory
# baseline values.
_PRIVILEGE_INSUFFICIENT_VALUES = frozenset(
    {
        ("privilege_level", "non_admin"),
        ("target_role_admin", "lacks_admin"),
        ("insufficient_privilege", "insufficient_privilege"),
        ("non_admin_attempt", "non_admin_execution"),
    }
)

_PRIVILEGE_INSUFFICIENT = {
    "privilege_level": "non_admin",
    "target_role_admin": "lacks_admin",
    "insufficient_privilege": "insufficient_privilege",
    "non_admin_attempt": "non_admin_execution",
}

_PRIVILEGE_SUFFICIENT = {
    "privilege_level": "group_role_admin",
    "target_role_admin": "has_admin",
    "insufficient_privilege": "sufficient_privilege",
    "non_admin_attempt": "admin_execution",
}


def _apply_privilege_cluster(
    assignments: dict[str, str],
    obligation: AlterGroupFactorObligation,
) -> None:
    """Keep the four privilege factors consistent with the primary value."""

    if (obligation.factor_key, obligation.value) in _PRIVILEGE_INSUFFICIENT_VALUES:
        assignments.update(_PRIVILEGE_INSUFFICIENT)
    elif (
        obligation.factor_key == "privilege_level"
        and obligation.value == "superuser"
    ):
        # A superuser is an admin path; privilege_level stays superuser.
        assignments["privilege_level"] = "superuser"
        assignments.update(
            {k: v for k, v in _PRIVILEGE_SUFFICIENT.items() if k != "privilege_level"}
        )
    # else: defaults already reflect the sufficient/admin path.


def _baseline_assignments(
    obligation: AlterGroupFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _ACTION_BRANCH[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = branch
    assignments["alter_action"] = obligation.consumer_action_id
    assignments["deprecated_equivalence"] = _BRANCH_DEPRECATED_EQUIVALENCE[branch]
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    # (expected_status, failure) is a meta failure flag with no concrete
    # cause of its own; give it the documented default failure cause
    # (target_role_missing) so the rendered target actually fails (42704).
    if (
        obligation.factor_key == "expected_status"
        and obligation.value == "failure"
    ):
        assignments["object_state"] = "not_exists"
    _apply_privilege_cluster(assignments, obligation)
    if len(assignments) != len(set(assignments)):
        raise AlterGroupFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_group_factor_loop_plan(
    repository_root: Path,
) -> AlterGroupFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_group_factor_loop_obligations(root)
    cases: list[AlterGroupFactorCase] = []
    delegated: list[AlterGroupFactorObligation] = []
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
            AlterGroupFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERGROUP{ordinal:04d}",
                sql_filename=f"ALTERGROUP{ordinal:04d}.sql",
                object_prefix=f"altergroup_{ordinal:04d}_",
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
    plan = AlterGroupFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 59 or len(plan.delegated) != 0:
        raise AlterGroupFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 59:
        raise AlterGroupFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 59:
        raise AlterGroupFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_group_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterGroupFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root) + _compile_risk_obligations()
    rows = tuple(
        AlterGroupFactorObligation(
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
    if len(rows) != 59:
        raise AlterGroupFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterGroupFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 57, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterGroupFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterGroupFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 59:
        raise AlterGroupFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterGroupFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterGroupFactorLoopError",
    "AlterGroupFactorObligation",
    "AlterGroupFactorCase",
    "AlterGroupFactorLoopPlan",
    "compile_alter_group_factor_loop_obligations",
    "build_alter_group_factor_loop_plan",
    "_obligation_multiset_sha256",
]
