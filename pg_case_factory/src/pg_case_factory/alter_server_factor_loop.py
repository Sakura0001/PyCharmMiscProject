"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER SERVER.

This module compiles the marginal ``GRM``/``SFV``/``RISK`` obligation ledger
for ``ALTER SERVER``.  ALTER SERVER manages a foreign server (a
``pg_catalog.pg_foreign_server`` row backed by a foreign data wrapper): it
has exactly three grammar branches (``RENAME TO``, ``OWNER TO`` and the
``VERSION`` / ``OPTIONS`` change form).  ``alter_server.yaml`` marks
column/table/relation coverage ``not_applicable`` (the statement target is
a ``pg_foreign_server`` row, not a ``pg_class`` relation), so there is no
``INV`` block.  Each local obligation becomes exactly one regress program;
there are no delegated handoffs because every reachable negative boundary is
a real ``ALTER SERVER`` error that belongs to this statement.

Privilege is server-ownership-based: the foreign-server owner (or a
superuser) may rename it, change its version/options and transfer ownership.
A non-owner without privilege is rejected with ``42501``.  The keyword
owner-transfers (``CURRENT_ROLE`` / ``CURRENT_USER`` / ``SESSION_USER``)
are normal permitted transfers to the current session role (there is no
membership-wall escape special case for ``ALTER SERVER``, unlike
``ALTER SCHEMA``): they are modelled as SUCCESS behaviour with a
state-checking oracle.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterServerFactorLoopError(ValueError):
    """Raised when a frozen ALTER SERVER obligation input drifts."""


@dataclass(frozen=True)
class AlterServerGrammarAction:
    """One official target action form of the ALTER SERVER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterServerGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis."""

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


@dataclass(frozen=True)
class AlterServerFactorObligation:
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
class AlterServerFactorCase:
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
class AlterServerFactorLoopPlan:
    obligations: tuple[AlterServerFactorObligation, ...]
    cases: tuple[AlterServerFactorCase, ...]
    delegated: tuple[AlterServerFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-alterserver.html).
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner_to"
_BRANCH_VERSION_OPTIONS = "branch_version_options"

# A representative branch_version_options action used as the baseline consumer
# for canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "version_options"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_RENAME: "rename",
    _BRANCH_OWNER: "owner",
    _BRANCH_VERSION_OPTIONS: "version_options",
}

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterserver"

# Ordered (action_id, branch, syntax, locator) tuples mirroring the official
# synopsis.  ALTER SERVER has three fixed forms with no optional keywords,
# alternatives, or list-boundary modifiers outside these branches, so the
# axis ledger is empty.
_GRAMMAR_ACTION_ROWS: tuple[tuple[str, str, str, str], ...] = (
    (
        "rename",
        _BRANCH_RENAME,
        "ALTER SERVER name RENAME TO new_name",
        "synopsis-rename",
    ),
    (
        "owner",
        _BRANCH_OWNER,
        (
            "ALTER SERVER name OWNER TO "
            "{ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
        ),
        "synopsis-owner-to",
    ),
    (
        "version_options",
        _BRANCH_VERSION_OPTIONS,
        (
            "ALTER SERVER name [ VERSION 'new_version' ] "
            "[ OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] ) ]"
        ),
        "synopsis-version-options",
    ),
)


def load_alter_server_grammar_actions() -> (
    tuple[AlterServerGrammarAction, ...]
):
    """Freeze every ALTER SERVER synopsis target action."""

    actions = [
        AlterServerGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in _GRAMMAR_ACTION_ROWS
    ]
    if len(actions) != 3:
        raise AlterServerFactorLoopError("alter server action count drift")
    return tuple(actions)


def load_alter_server_grammar_axes() -> (
    tuple[AlterServerGrammarAxis, ...]
):
    """Freeze every optional / alternative / list-boundary modifier.

    ALTER SERVER has three fixed forms with no optional keywords,
    alternatives, or list-boundary modifiers outside the branches, so the
    axis ledger is empty.
    """

    return ()


# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "server_state": _REPRESENTATIVE_ACTION,
    "server_name_shape": _REPRESENTATIVE_ACTION,
    "nonexistent_server": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "rename_behavior": "rename",
    "new_name_shape": "rename",
    "nonexistent_new_name_conflict": "rename",
    "owner_to_shape": "owner",
    "new_owner_shape": "owner",
    "nonexistent_owner": "owner",
    "version_clause": "version_options",
    "options_operation": "version_options",
    "option_key_value_shape": "version_options",
    "fdw_validator_rejection": "version_options",
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "user_mapping_dependency": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
# The keyword owner-transfers are NOT here: they are SUCCESS behaviour.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("server_state", "non_existent"),
        ("server_name_shape", "non_existent_name"),
        ("nonexistent_server", "server_does_not_exist"),
        ("new_name_shape", "existing_name_conflict"),
        ("rename_behavior", "rename_to_existing_name_conflict"),
        ("nonexistent_new_name_conflict", "new_name_already_exists"),
        ("new_owner_shape", "nonexistent_role"),
        ("nonexistent_owner", "owner_role_does_not_exist"),
        ("executor_privilege", "non_owner_no_privilege"),
        ("privilege_insufficient", "non_owner_altering_server"),
        ("privilege_insufficient", "non_superuser_altering_server"),
        ("option_key_value_shape", "invalid_option_rejected_by_validator"),
        ("fdw_validator_rejection", "validator_rejects_invalid_option"),
    }
)

# ALTER SERVER has no membership-wall escape special case: the keyword
# owner-transfers are normal permitted transfers, so this set is empty.
_EXPECTED_BEHAVIOR_VALUES = frozenset()

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "server_does_not_exist_provisional",
    ),
    ("server_state", "non_existent"): (
        "42704",
        "server_does_not_exist_provisional",
    ),
    ("server_name_shape", "non_existent_name"): (
        "42704",
        "server_does_not_exist_provisional",
    ),
    ("nonexistent_server", "server_does_not_exist"): (
        "42704",
        "server_does_not_exist_provisional",
    ),
    ("new_name_shape", "existing_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("rename_behavior", "rename_to_existing_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("nonexistent_new_name_conflict", "new_name_already_exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("new_owner_shape", "nonexistent_role"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("nonexistent_owner", "owner_role_does_not_exist"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("executor_privilege", "non_owner_no_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_owner_altering_server"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_superuser_altering_server"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("option_key_value_shape", "invalid_option_rejected_by_validator"): (
        "HV00D",
        "invalid_option_name_provisional",
    ),
    ("fdw_validator_rejection", "validator_rejects_invalid_option"): (
        "HV00D",
        "validator_rejects_option_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterServerFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterServerFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterServerFactorObligation]:
    rows: list[AlterServerFactorObligation] = []
    for action in load_alter_server_grammar_actions():
        rows.append(
            AlterServerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ASRV-GRM|{action.grammar_branch_id}|"
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
        raise AlterServerFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterServerFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_server")
    if len(catalog_rows) != 48:
        raise AlterServerFactorLoopError("canonical obligation count drift")
    rows: list[AlterServerFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterServerFactorObligation(
                ordinal=0,
                obligation_id=f"ASRV-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterServerFactorObligation]:
    return [
        AlterServerFactorObligation(
            ordinal=0,
            obligation_id=f"ASRV-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterserver:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterServerFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-server-factor-obligations-v1\n")
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
_ACTION_BRANCH = {
    "rename": _BRANCH_RENAME,
    "owner": _BRANCH_OWNER,
    "version_options": _BRANCH_VERSION_OPTIONS,
}

# Dense baseline defaults (all positive T1-T6 factor values).  The T5
# single-value-negative factors (nonexistent_server,
# nonexistent_new_name_conflict, nonexistent_owner, privilege_insufficient,
# fdw_validator_rejection) are NOT baselined here: every declared value is a
# failure mode, so they are set only when they are the primary (or derived in
# the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_VERSION_OPTIONS,
    "grammar_branch": _BRANCH_VERSION_OPTIONS,
    "target_action": "version_options",
    "server_state": "exists",
    "expected_status": "success",
    "rename_behavior": "rename_to_new_name",
    "owner_to_shape": "explicit_role_name",
    "new_owner_shape": "existing_role",
    "version_clause": "omitted",
    "options_operation": "omitted_no_options",
    "option_key_value_shape": "valid_option",
    "server_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "user_mapping_dependency": "no_user_mapping",
    "verification_mode": "pg_foreign_server_catalog",
    "cleanup_mode": "drop_server",
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

    ss = a.get("server_state", "exists")
    snm = a.get("server_name_shape", "simple_name")
    nes = a.get("nonexistent_server", "")
    es = a.get("expected_status", "success")
    nns = a.get("new_name_shape", "simple_name")
    rb = a.get("rename_behavior", "rename_to_new_name")
    nncf = a.get("nonexistent_new_name_conflict", "")
    now = a.get("new_owner_shape", "existing_role")
    noe = a.get("nonexistent_owner", "")
    ep = a.get("executor_privilege", "superuser")
    pi = a.get("privilege_insufficient", "")
    oks = a.get("option_key_value_shape", "valid_option")
    fvr = a.get("fdw_validator_rejection", "")

    # server absent cluster: server_state / server_name_shape /
    # nonexistent_server / expected_status
    if ss == "non_existent" or snm == "non_existent_name" or (
        nes == "server_does_not_exist"
    ) or es == "failure":
        a["server_state"] = "non_existent"
        a["server_name_shape"] = "non_existent_name"
        a["nonexistent_server"] = "server_does_not_exist"

    # rename conflict cluster: new_name_shape / rename_behavior /
    # nonexistent_new_name_conflict
    if nns == "existing_name_conflict" or (
        rb == "rename_to_existing_name_conflict"
    ) or nncf == "new_name_already_exists":
        a["new_name_shape"] = "existing_name_conflict"
        a["rename_behavior"] = "rename_to_existing_name_conflict"
        a["nonexistent_new_name_conflict"] = "new_name_already_exists"

    # owner absent cluster: new_owner_shape / nonexistent_owner
    if now == "nonexistent_role" or noe == "owner_role_does_not_exist":
        a["new_owner_shape"] = "nonexistent_role"
        a["nonexistent_owner"] = "owner_role_does_not_exist"

    # privilege insufficient cluster: executor_privilege /
    # privilege_insufficient.  Both privilege_insufficient values tie to
    # executor_privilege=non_owner_no_privilege; the primary's value is
    # preserved when it is the T5 side.
    if ep == "non_owner_no_privilege":
        if pi not in ("non_owner_altering_server",
                      "non_superuser_altering_server"):
            a["privilege_insufficient"] = "non_owner_altering_server"
    elif pi in ("non_owner_altering_server",
                "non_superuser_altering_server"):
        a["executor_privilege"] = "non_owner_no_privilege"

    # option invalid cluster: option_key_value_shape / fdw_validator_rejection
    if oks == "invalid_option_rejected_by_validator" or (
        fvr == "validator_rejects_invalid_option"
    ):
        a["option_key_value_shape"] = "invalid_option_rejected_by_validator"
        a["fdw_validator_rejection"] = "validator_rejects_invalid_option"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterServerFactorObligation,
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
        raise AlterServerFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterServerFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterServerFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_server_factor_loop_plan(
    repository_root: Path,
) -> AlterServerFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_server_factor_loop_obligations(root)
    cases: list[AlterServerFactorCase] = []
    delegated: list[AlterServerFactorObligation] = []
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
            AlterServerFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERSERVER{ordinal:05d}",
                sql_filename=f"ALTERSERVER{ordinal:05d}.sql",
                object_prefix=f"alterserver_{ordinal:05d}_",
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
    plan = AlterServerFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 53 or len(plan.delegated) != 0:
        raise AlterServerFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 53:
        raise AlterServerFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 53:
        raise AlterServerFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_server_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterServerFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterServerFactorObligation(
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
    if len(rows) != 53:
        raise AlterServerFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterServerFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 3, "SFV": 48, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterServerFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterServerFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 53:
        raise AlterServerFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterServerFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterServerFactorLoopError",
    "AlterServerFactorObligation",
    "AlterServerFactorCase",
    "AlterServerFactorLoopPlan",
    "AlterServerGrammarAction",
    "AlterServerGrammarAxis",
    "_EXPECTED_BEHAVIOR_VALUES",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_server_factor_loop_obligations",
    "build_alter_server_factor_loop_plan",
    "load_alter_server_grammar_actions",
    "load_alter_server_grammar_axes",
    "_obligation_multiset_sha256",
]
