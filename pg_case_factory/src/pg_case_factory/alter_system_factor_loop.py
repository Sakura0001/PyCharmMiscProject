"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER SYSTEM.

This module compiles the marginal ``GRM``/``SFV``/``RISK`` obligation ledger
for ``ALTER SYSTEM``.  ALTER SYSTEM is a superuser-only server-configuration
statement that writes to ``postgresql.auto.conf``; it has four synopsis
branches (``SET``, ``SET ... = DEFAULT``, ``RESET``, ``RESET ALL``).
``alter_system.yaml`` marks table/relation coverage ``not_applicable`` (the
statement target is a ``pg_settings`` / ``postgresql.auto.conf`` entry, not a
``pg_class`` relation), so there is no ``INV`` block.  Each local obligation
becomes exactly one regress program; there are no delegated handoffs.

ALTER SYSTEM cannot run inside a transaction block, so the RISK axis models
the transaction-boundary rejection (``inside_transaction_block`` → ``25001``)
and the standalone auto-commit path (``outside_transaction`` → success).

Privilege is superuser-only: a non-superuser executing any ``ALTER SYSTEM``
form is rejected with ``42501``.  ``allow_alter_system = off`` is a server
configuration gate (provisional ``42501``) that rejects every form regardless
of privilege.  All SQLSTATEs are provisional pending DB-phase calibration on
PG 18.4.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterSystemFactorLoopError(ValueError):
    """Raised when a frozen ALTER SYSTEM obligation input drifts."""


@dataclass(frozen=True)
class AlterSystemFactorObligation:
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
class AlterSystemFactorCase:
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
class AlterSystemFactorLoopPlan:
    obligations: tuple[AlterSystemFactorObligation, ...]
    cases: tuple[AlterSystemFactorCase, ...]
    delegated: tuple[AlterSystemFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altersystem.html).
_BRANCH_SET = "branch_set"
_BRANCH_SET_DEFAULT = "branch_set_default"
_BRANCH_RESET = "branch_reset"
_BRANCH_RESET_ALL = "branch_reset_all"

# A representative branch_set action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "set"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_SET: "set",
    _BRANCH_SET_DEFAULT: "set_default",
    _BRANCH_RESET: "reset",
    _BRANCH_RESET_ALL: "reset_all",
}

# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "set": _BRANCH_SET,
    "set_default": _BRANCH_SET_DEFAULT,
    "reset": _BRANCH_RESET,
    "reset_all": _BRANCH_RESET_ALL,
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "configuration_parameter_type": _REPRESENTATIVE_ACTION,
    "set_value_behavior": "set",
    "reset_behavior": "reset",
    "parameter_effect_scope": _REPRESENTATIVE_ACTION,
    "parameter_name_shape": _REPRESENTATIVE_ACTION,
    "value_shape": "set",
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "parameter_validity": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "nonexistent_parameter": _REPRESENTATIVE_ACTION,
    "invalid_parameter_value": "set",
    "superuser_only_parameter_by_non_superuser": _REPRESENTATIVE_ACTION,
    "restart_required_parameter": _REPRESENTATIVE_ACTION,
    "reset_nonexistent_parameter_entry": "reset",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("parameter_validity", "nonexistent_parameter"),
        ("parameter_validity", "valid_parameter_invalid_value"),
        ("parameter_validity", "allow_alter_system_off"),
        ("nonexistent_parameter", "parameter_does_not_exist"),
        ("invalid_parameter_value", "wrong_type_value"),
        ("invalid_parameter_value", "out_of_range_value"),
        ("executor_privilege", "non_superuser"),
        ("privilege_insufficient", "non_superuser_using_alter_system"),
        (
            "superuser_only_parameter_by_non_superuser",
            "cannot_set_superuser_only_parameter",
        ),
        ("parameter_name_shape", "nonexistent_parameter_name"),
        ("value_shape", "invalid_value_type"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# These are provisional pending DB-phase calibration on PG 18.4.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "nonexistent_parameter_provisional",
    ),
    ("parameter_validity", "nonexistent_parameter"): (
        "42704",
        "nonexistent_parameter_provisional",
    ),
    ("parameter_validity", "valid_parameter_invalid_value"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("parameter_validity", "allow_alter_system_off"): (
        "42501",
        "alter_system_disabled_provisional",
    ),
    ("nonexistent_parameter", "parameter_does_not_exist"): (
        "42704",
        "nonexistent_parameter_provisional",
    ),
    ("invalid_parameter_value", "wrong_type_value"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("invalid_parameter_value", "out_of_range_value"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("executor_privilege", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_superuser_using_alter_system"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    (
        "superuser_only_parameter_by_non_superuser",
        "cannot_set_superuser_only_parameter",
    ): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("parameter_name_shape", "nonexistent_parameter_name"): (
        "42704",
        "nonexistent_parameter_provisional",
    ),
    ("value_shape", "invalid_value_type"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    # RISK: ALTER SYSTEM cannot run inside a transaction block.
    ("transaction_outcome", "inside_transaction_block"): (
        "25001",
        "active_transaction_provisional",
    ),
}

_DOC_SOURCE = "postgresql-18.4-doc:sql-altersystem"


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterSystemFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterSystemFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterSystemFactorObligation]:
    """Freeze the four ALTER SYSTEM synopsis target actions."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "set",
            _BRANCH_SET,
            "ALTER SYSTEM SET configuration_parameter value",
            "synopsis-set",
        ),
        (
            "set_default",
            _BRANCH_SET_DEFAULT,
            "ALTER SYSTEM SET configuration_parameter DEFAULT",
            "synopsis-set-default",
        ),
        (
            "reset",
            _BRANCH_RESET,
            "ALTER SYSTEM RESET configuration_parameter",
            "synopsis-reset",
        ),
        (
            "reset_all",
            _BRANCH_RESET_ALL,
            "ALTER SYSTEM RESET ALL",
            "synopsis-reset-all",
        ),
    )
    obligations = [
        AlterSystemFactorObligation(
            ordinal=0,
            obligation_id=(
                f"ASYS-GRM|{branch}|{action_id}|target_action|{action_id}"
            ),
            kind="GRM",
            factor_key="target_action",
            value=action_id,
            consumer_action_id=action_id,
            disposition="covered",
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, _syntax, locator in rows
    ]
    if len(obligations) != 4:
        raise AlterSystemFactorLoopError("grammar obligation count drift")
    return obligations


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterSystemFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_system")
    if len(catalog_rows) != 49:
        raise AlterSystemFactorLoopError("canonical obligation count drift")
    rows: list[AlterSystemFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterSystemFactorObligation(
                ordinal=0,
                obligation_id=f"ASYS-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterSystemFactorObligation]:
    """ALTER SYSTEM cannot run inside a transaction block."""

    return [
        AlterSystemFactorObligation(
            ordinal=0,
            obligation_id=f"ASYS-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition=(
                "expected_failure"
                if value == "inside_transaction_block"
                else "covered"
            ),
            source_locator=(
                "postgresql-18.4-doc:sql-altersystem:"
                "cannot-run-in-transaction-block"
            ),
        )
        for value in ("outside_transaction", "inside_transaction_block")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterSystemFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-system-factor-obligations-v1\n")
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


# Dense baseline defaults (all positive T1-T6 factor values).  The T5
# single-value-negative factors (privilege_insufficient,
# nonexistent_parameter, invalid_parameter_value,
# superuser_only_parameter_by_non_superuser) are NOT baselined here: every
# declared value is a failure mode, so they are set only when they are the
# primary (or derived in the extension).  restart_required_parameter and
# reset_nonexistent_parameter_entry carry non-failure behaviour values and
# ARE baselined.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_SET,
    "grammar_branch": _BRANCH_SET,
    "target_action": "set",
    "expected_status": "success",
    "configuration_parameter_type": "user_settable_parameter",
    "set_value_behavior": "single_value",
    "reset_behavior": "reset_specific_parameter",
    "parameter_effect_scope": "immediate_effect",
    "parameter_name_shape": "valid_parameter_name",
    "value_shape": "valid_string_value",
    "executor_privilege": "superuser",
    "parameter_validity": "valid_parameter_and_value",
    "restart_required_parameter": "parameter_change_requires_restart",
    "reset_nonexistent_parameter_entry": (
        "reset_parameter_not_in_auto_conf_no_op"
    ),
    "verification_mode": "pg_settings_query",
    "cleanup_mode": "alter_system_reset_parameter",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T3<->T4<->T5 overlapping factor values in-place.

    The T5 boundary factors describe the same scenario as their T3/T4
    counterparts.  When the primary factor is a T3/T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T3/T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that actually reaches the
    intended boundary.
    """

    es = a.get("expected_status", "success")
    pns = a.get("parameter_name_shape", "valid_parameter_name")
    vs = a.get("value_shape", "valid_string_value")
    pv = a.get("parameter_validity", "valid_parameter_and_value")
    ep = a.get("executor_privilege", "superuser")
    pi = a.get("privilege_insufficient", "")
    np_ = a.get("nonexistent_parameter", "")
    ipv = a.get("invalid_parameter_value", "")
    sop = a.get("superuser_only_parameter_by_non_superuser", "")
    cpt = a.get("configuration_parameter_type", "user_settable_parameter")

    # expected_status=failure -> representative failure (nonexistent param)
    if es == "failure":
        a["parameter_validity"] = "nonexistent_parameter"
        a["parameter_name_shape"] = "nonexistent_parameter_name"

    # parameter_name_shape=nonexistent <-> nonexistent_parameter <->
    # parameter_validity=nonexistent
    if (
        pns == "nonexistent_parameter_name"
        or np_ == "parameter_does_not_exist"
        or pv == "nonexistent_parameter"
    ):
        a["parameter_name_shape"] = "nonexistent_parameter_name"
        a["nonexistent_parameter"] = "parameter_does_not_exist"
        a["parameter_validity"] = "nonexistent_parameter"

    # value_shape=invalid_value_type <-> invalid_parameter_value=wrong_type <->
    # parameter_validity=valid_parameter_invalid_value.  out_of_range_value is
    # a valid-type-but-out-of-range boundary: it does NOT flip value_shape.
    if vs == "invalid_value_type" or ipv == "wrong_type_value":
        a["value_shape"] = "invalid_value_type"
        a["invalid_parameter_value"] = "wrong_type_value"
        a["parameter_validity"] = "valid_parameter_invalid_value"
    if ipv == "out_of_range_value":
        a["parameter_validity"] = "valid_parameter_invalid_value"

    # value_shape <-> set_value_behavior (SET group consistency).
    svb = a.get("set_value_behavior", "single_value")
    if svb == "set_to_default" or vs == "default_keyword":
        a["set_value_behavior"] = "set_to_default"
        a["value_shape"] = "default_keyword"
    if svb == "multiple_values" or vs == "multiple_comma_separated_values":
        a["set_value_behavior"] = "multiple_values"
        a["value_shape"] = "multiple_comma_separated_values"

    # executor_privilege=non_superuser <-> privilege_insufficient <->
    # superuser_only_parameter_by_non_superuser (when param is superuser_only)
    if (
        ep == "non_superuser"
        or pi == "non_superuser_using_alter_system"
        or (
            sop == "cannot_set_superuser_only_parameter"
            and cpt == "superuser_only_parameter"
        )
    ):
        a["executor_privilege"] = "non_superuser"
        a["privilege_insufficient"] = "non_superuser_using_alter_system"
        if cpt == "superuser_only_parameter":
            a["superuser_only_parameter_by_non_superuser"] = (
                "cannot_set_superuser_only_parameter"
            )

    # parameter_validity=allow_alter_system_off is standalone (no T3/T4
    # counterpart); it is only set when it is the primary.
    if pv == "allow_alter_system_off":
        a["parameter_validity"] = "allow_alter_system_off"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterSystemFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments["target_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = "failure" if failures > 0 else "success"
    if len(assignments) != len(set(assignments)):
        raise AlterSystemFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterSystemFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterSystemFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_system_factor_loop_plan(
    repository_root: Path,
) -> AlterSystemFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_system_factor_loop_obligations(root)
    cases: list[AlterSystemFactorCase] = []
    delegated: list[AlterSystemFactorObligation] = []
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
            AlterSystemFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERSYSTEM{ordinal:05d}",
                sql_filename=f"ALTERSYSTEM{ordinal:05d}.sql",
                object_prefix=f"alter_system_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = AlterSystemFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 55 or len(plan.delegated) != 0:
        raise AlterSystemFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 55:
        raise AlterSystemFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 55:
        raise AlterSystemFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_system_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterSystemFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterSystemFactorObligation(
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
    if len(rows) != 55:
        raise AlterSystemFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterSystemFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 4, "SFV": 49, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterSystemFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterSystemFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 55:
        raise AlterSystemFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterSystemFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterSystemFactorLoopError",
    "AlterSystemFactorObligation",
    "AlterSystemFactorCase",
    "AlterSystemFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_system_factor_loop_obligations",
    "build_alter_system_factor_loop_plan",
    "_obligation_multiset_sha256",
]
