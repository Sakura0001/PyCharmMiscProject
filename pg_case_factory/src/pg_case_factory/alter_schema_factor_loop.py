"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER SCHEMA.

This module compiles the marginal ``GRM``/``SFV``/``RISK`` obligation ledger
for ``ALTER SCHEMA``.  ALTER SCHEMA is a PostgreSQL extension (outside the
SQL standard) that manages the schema namespace: it has exactly two grammar
branches (``RENAME TO`` and ``OWNER TO``).  ``alter_schema.yaml`` marks
column/table/relation coverage ``not_applicable`` (the statement target is a
``pg_catalog.pg_namespace`` row, not a ``pg_class`` relation), so there is no
``INV`` block.  Each local obligation becomes exactly one regress program;
there are no delegated handoffs because every reachable negative boundary is
a real ``ALTER SCHEMA`` error that belongs to this statement.

Privilege is schema-ownership-based (not relation-ownership): ``OWNER TO``
requires owning the schema plus ``SET ROLE`` membership in the new owner,
and the new owner must hold ``CREATE`` on the database; superuser bypasses.
``OWNER TO SESSION_USER`` is a permitted no-op transfer that escapes the
membership wall (mirrors ``alter_publication``): it is modelled as a
SUCCESS behavior with a state-checking oracle, NOT as a failure.  The DB
phase must verify whether the escape truly holds for a NON-OWNER of the
schema (schema ownership semantics differ from publication ownership).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_schema_regress import (
    AlterSchemaRegressError,
    load_alter_schema_grammar_actions,
    load_alter_schema_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterSchemaFactorLoopError(ValueError):
    """Raised when a frozen ALTER SCHEMA obligation input drifts."""


@dataclass(frozen=True)
class AlterSchemaFactorObligation:
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
class AlterSchemaFactorCase:
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
class AlterSchemaFactorLoopPlan:
    obligations: tuple[AlterSchemaFactorObligation, ...]
    cases: tuple[AlterSchemaFactorCase, ...]
    delegated: tuple[AlterSchemaFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches.
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"

# A representative branch_rename action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "rename"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_RENAME: "rename",
    _BRANCH_OWNER: "owner",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "rename_clause": "rename",
    "owner_clause": "owner",
    "new_name_constraint": "rename",
    "schema_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "new_owner_shape": "owner",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "rename_privilege": "rename",
    "owner_change_privilege": "owner",
    "new_owner_db_privilege": "owner",
    "contained_objects_state": _REPRESENTATIVE_ACTION,
    "non_existent_schema": _REPRESENTATIVE_ACTION,
    "pg_prefix_new_name": "rename",
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "new_name_conflict": "rename",
    "new_owner_not_exists": "owner",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
# The SESSION_USER owner-transfer escape is deliberately NOT here: it is a
# SUCCESS behavior (see _EXPECTED_BEHAVIOR_VALUES).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("non_existent_schema", "target_not_exists"),
        ("new_name_conflict", "new_name_already_exists"),
        ("rename_clause", "new_existing_name"),
        ("new_name_shape", "pg_prefix_reserved"),
        ("pg_prefix_new_name", "pg_prefix_illegal"),
        ("rename_clause", "new_pg_prefix_name"),
        ("new_name_constraint", "pg_prefix_illegal"),
        ("new_owner_not_exists", "specified_role_not_exists"),
        ("new_owner_shape", "non_existing_role"),
        ("insufficient_privilege", "non_owner_attempt"),
        ("privilege_level", "non_owner"),
        ("insufficient_privilege", "owner_no_CREATE_on_db"),
        ("rename_privilege", "owner_no_CREATE_on_db"),
        ("insufficient_privilege", "cannot_SET_ROLE"),
        ("owner_change_privilege", "cannot_SET_ROLE_to_new_owner"),
        ("new_owner_db_privilege", "no_CREATE_privilege"),
    }
)

# The SESSION_USER owner-transfer escape: ``OWNER TO SESSION_USER`` is a
# permitted no-op transfer that escapes the membership wall.  It is a
# SUCCESS path with a state-checking oracle (``pg_namespace.nspowner``
# resolves to the session user).  The DB phase must verify the escape
# actually holds for a NON-OWNER of the schema.
_EXPECTED_BEHAVIOR_VALUES = frozenset(
    {
        ("owner_clause", "SESSION_USER"),
        ("new_owner_shape", "SESSION_USER"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# These are provisional pending DB-phase calibration on PG 18.4.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("object_state", "not_exists"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("non_existent_schema", "target_not_exists"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("new_name_conflict", "new_name_already_exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("rename_clause", "new_existing_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("new_name_shape", "pg_prefix_reserved"): (
        "42939",
        "reserved_name_provisional",
    ),
    ("pg_prefix_new_name", "pg_prefix_illegal"): (
        "42939",
        "reserved_name_provisional",
    ),
    ("rename_clause", "new_pg_prefix_name"): (
        "42939",
        "reserved_name_provisional",
    ),
    ("new_name_constraint", "pg_prefix_illegal"): (
        "42939",
        "reserved_name_provisional",
    ),
    ("new_owner_not_exists", "specified_role_not_exists"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("new_owner_shape", "non_existing_role"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("insufficient_privilege", "non_owner_attempt"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "owner_no_CREATE_on_db"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("rename_privilege", "owner_no_CREATE_on_db"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "cannot_SET_ROLE"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("owner_change_privilege", "cannot_SET_ROLE_to_new_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("new_owner_db_privilege", "no_CREATE_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    # Sentinel attribution key for the membership wall that fires under a
    # non-superuser schema owner for OWNER TO with an explicit role or
    # CURRENT_ROLE / CURRENT_USER (SESSION_USER escapes).  Surfaced by
    # _present_failure_pair in the extension expander.
    ("owner_clause", "membership_required_under_owner"): (
        "42501",
        "owner_change_requires_membership_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterSchemaFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterSchemaFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterSchemaFactorObligation]:
    rows: list[AlterSchemaFactorObligation] = []
    for action in load_alter_schema_grammar_actions():
        rows.append(
            AlterSchemaFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AS-GRM|{action.grammar_branch_id}|"
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
    for axis in load_alter_schema_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id == "__outer_action__"
            else f"local:{axis.axis_id}"
        )
        consumer = (
            _REPRESENTATIVE_ACTION
            if axis.action_id == "__outer_action__"
            else axis.action_id
        )
        for value in axis.values:
            rows.append(
                AlterSchemaFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"AS-GRM|{axis.grammar_branch_id}|"
                        f"{axis.action_id}|{axis.axis_id}|{value}"
                    ),
                    kind="GRM",
                    factor_key=factor_key,
                    value=value,
                    consumer_action_id=consumer,
                    disposition="covered",
                    source_locator=axis.source_locator,
                )
            )
    if len(rows) != 2:
        raise AlterSchemaFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterSchemaFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_schema")
    if len(catalog_rows) != 53:
        raise AlterSchemaFactorLoopError("canonical obligation count drift")
    rows: list[AlterSchemaFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterSchemaFactorObligation(
                ordinal=0,
                obligation_id=f"AS-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _compile_risk_obligations() -> list[AlterSchemaFactorObligation]:
    return [
        AlterSchemaFactorObligation(
            ordinal=0,
            obligation_id=f"AS-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterschema:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterSchemaFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-schema-factor-obligations-v1\n")
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

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {"rename": _BRANCH_RENAME, "owner": _BRANCH_OWNER}

# Dense baseline defaults (all positive T1-T6 factor values).  The T5
# single-value-negative factors (non_existent_schema, pg_prefix_new_name,
# new_name_conflict, new_owner_not_exists, insufficient_privilege) are NOT
# baselined here: every declared value is a failure mode, so they are set
# only when they are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_RENAME,
    "grammar_branch": _BRANCH_RENAME,
    "target_action": "rename",
    "object_state": "exists",
    "expected_status": "success",
    "rename_clause": "new_simple_name",
    "owner_clause": "new_owner_role",
    "new_name_constraint": "not_pg_prefix",
    "schema_name_shape": "simple",
    "new_name_shape": "simple",
    "new_owner_shape": "existing_role",
    "privilege_level": "superuser",
    "rename_privilege": "owner_with_CREATE_on_db",
    "owner_change_privilege": "can_SET_ROLE_to_new_owner",
    "new_owner_db_privilege": "has_CREATE_privilege",
    "contained_objects_state": "empty_schema",
    "verification_mode": "pg_namespace_catalog_query",
    "cleanup_mode": "DROP_SCHEMA",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T3<->T4<->T5 overlapping factor values in-place.

    The T5 boundary factors describe the same scenario as their T3/T4
    counterparts.  When the primary factor is a T3/T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T3/T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that actually reaches the
    intended boundary.  The SESSION_USER escape is a SUCCESS behavior and
    keeps owner_clause / new_owner_shape consistent.
    """

    os_ = a.get("object_state", "exists")
    nes = a.get("non_existent_schema", "")
    es = a.get("expected_status", "success")
    rnc = a.get("rename_clause", "new_simple_name")
    nns = a.get("new_name_shape", "simple")
    nnc = a.get("new_name_constraint", "not_pg_prefix")
    ppn = a.get("pg_prefix_new_name", "")
    nncf = a.get("new_name_conflict", "")
    now = a.get("new_owner_shape", "existing_role")
    none_ = a.get("new_owner_not_exists", "")
    pl = a.get("privilege_level", "superuser")
    ip = a.get("insufficient_privilege", "")
    rp = a.get("rename_privilege", "owner_with_CREATE_on_db")
    ocp = a.get("owner_change_privilege", "can_SET_ROLE_to_new_owner")
    oc = a.get("owner_clause", "new_owner_role")

    # non_existent_schema <-> object_state / expected_status
    if os_ == "not_exists" or nes == "target_not_exists" or es == "failure":
        a["object_state"] = "not_exists"
        a["non_existent_schema"] = "target_not_exists"

    # pg_prefix cluster: rename_clause/new_name_shape/new_name_constraint/pg_prefix_new_name
    if (
        rnc == "new_pg_prefix_name"
        or nns == "pg_prefix_reserved"
        or nnc == "pg_prefix_illegal"
        or ppn == "pg_prefix_illegal"
    ):
        a["rename_clause"] = "new_pg_prefix_name"
        a["new_name_shape"] = "pg_prefix_reserved"
        a["new_name_constraint"] = "pg_prefix_illegal"
        a["pg_prefix_new_name"] = "pg_prefix_illegal"

    # new_name_conflict <-> rename_clause=new_existing_name
    if nncf == "new_name_already_exists" or rnc == "new_existing_name":
        a["rename_clause"] = "new_existing_name"
        a["new_name_conflict"] = "new_name_already_exists"

    # new_owner_not_exists <-> new_owner_shape=non_existing_role
    if none_ == "specified_role_not_exists" or now == "non_existing_role":
        a["new_owner_shape"] = "non_existing_role"
        a["new_owner_not_exists"] = "specified_role_not_exists"

    # insufficient_privilege=non_owner_attempt <-> privilege_level=non_owner
    if ip == "non_owner_attempt" or pl == "non_owner":
        a["privilege_level"] = "non_owner"
        a["insufficient_privilege"] = "non_owner_attempt"

    # insufficient_privilege=owner_no_CREATE_on_db <-> rename_privilege
    if ip == "owner_no_CREATE_on_db" or rp == "owner_no_CREATE_on_db":
        a["rename_privilege"] = "owner_no_CREATE_on_db"
        a["insufficient_privilege"] = "owner_no_CREATE_on_db"

    # insufficient_privilege=cannot_SET_ROLE <-> owner_change_privilege
    if (
        ip == "cannot_SET_ROLE"
        or ocp == "cannot_SET_ROLE_to_new_owner"
    ):
        a["owner_change_privilege"] = "cannot_SET_ROLE_to_new_owner"
        a["insufficient_privilege"] = "cannot_SET_ROLE"

    # SESSION_USER escape: owner_clause <-> new_owner_shape (SUCCESS behavior)
    if oc == "SESSION_USER" or now == "SESSION_USER":
        a["owner_clause"] = "SESSION_USER"
        a["new_owner_shape"] = "SESSION_USER"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterSchemaFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[obligation.consumer_action_id]
    assignments["target_action"] = obligation.consumer_action_id
    key = _renderer_factor_key(obligation.factor_key)
    assignments[key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = "failure" if failures > 0 else "success"
    if len(assignments) != len(set(assignments)):
        raise AlterSchemaFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterSchemaFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterSchemaFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_schema_factor_loop_plan(
    repository_root: Path,
) -> AlterSchemaFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_schema_factor_loop_obligations(root)
    cases: list[AlterSchemaFactorCase] = []
    delegated: list[AlterSchemaFactorObligation] = []
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
            AlterSchemaFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERSCHEMA{ordinal:05d}",
                sql_filename=f"ALTERSCHEMA{ordinal:05d}.sql",
                object_prefix=f"alterschema_{ordinal:05d}_",
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
    plan = AlterSchemaFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 57 or len(plan.delegated) != 0:
        raise AlterSchemaFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 57:
        raise AlterSchemaFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 57:
        raise AlterSchemaFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_schema_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterSchemaFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterSchemaFactorObligation(
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
    if len(rows) != 57:
        raise AlterSchemaFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterSchemaFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 53, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterSchemaFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterSchemaFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 57:
        raise AlterSchemaFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterSchemaFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterSchemaFactorLoopError",
    "AlterSchemaFactorObligation",
    "AlterSchemaFactorCase",
    "AlterSchemaFactorLoopPlan",
    "_EXPECTED_BEHAVIOR_VALUES",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_schema_factor_loop_obligations",
    "build_alter_schema_factor_loop_plan",
    "_obligation_multiset_sha256",
]
