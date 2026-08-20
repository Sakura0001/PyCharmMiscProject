"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER SUBSCRIPTION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER SUBSCRIPTION``.  ALTER SUBSCRIPTION is a PostgreSQL logical-
replication DDL statement with 11 official synopsis branches: CONNECTION,
SET/ADD/DROP PUBLICATION, REFRESH PUBLICATION, ENABLE, DISABLE, SET
(parameters), SKIP, OWNER TO, and RENAME TO.  The statement requires
superuser privilege and touches the ``pg_catalog.pg_subscription`` catalog
row (not a ``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  Because
ALTER SUBSCRIPTION is largely non-transactional (REFRESH/ENABLE/DISABLE
cannot run inside a transaction block) and the inventory declares no
``transaction_outcome`` factor, there are no ``RISK`` obligations.

The grammar ledger is self-contained (there is no separate
``alter_subscription_regress`` module): the 11 synopsis actions are frozen
inline.  The 70 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterSubscriptionFactorLoopError(ValueError):
    """Raised when a frozen ALTER SUBSCRIPTION obligation input drifts."""


@dataclass(frozen=True)
class AlterSubscriptionGrammarAction:
    """One official target action form of the ALTER SUBSCRIPTION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterSubscriptionFactorObligation:
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
class AlterSubscriptionFactorCase:
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
class AlterSubscriptionFactorLoopPlan:
    obligations: tuple[AlterSubscriptionFactorObligation, ...]
    cases: tuple[AlterSubscriptionFactorCase, ...]
    delegated: tuple[AlterSubscriptionFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altersubscription.html).
_BRANCH_CONNECTION = "branch_connection"
_BRANCH_SET_PUBLICATION = "branch_set_publication"
_BRANCH_ADD_PUBLICATION = "branch_add_publication"
_BRANCH_DROP_PUBLICATION = "branch_drop_publication"
_BRANCH_REFRESH = "branch_refresh_publication"
_BRANCH_ENABLE = "branch_enable"
_BRANCH_DISABLE = "branch_disable"
_BRANCH_SET_PARAMETERS = "branch_set_parameters"
_BRANCH_SKIP = "branch_skip"
_BRANCH_OWNER = "branch_owner_to"
_BRANCH_RENAME = "branch_rename"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altersubscription"

# A representative branch_rename action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.  RENAME TO
# is simple, superuser-only, and needs no replication connection.
_REPRESENTATIVE_ACTION = "rename"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_CONNECTION: "connection",
    _BRANCH_SET_PUBLICATION: "set_publication",
    _BRANCH_ADD_PUBLICATION: "add_publication",
    _BRANCH_DROP_PUBLICATION: "drop_publication",
    _BRANCH_REFRESH: "refresh_publication",
    _BRANCH_ENABLE: "enable",
    _BRANCH_DISABLE: "disable",
    _BRANCH_SET_PARAMETERS: "set_parameters",
    _BRANCH_SKIP: "skip",
    _BRANCH_OWNER: "owner_to",
    _BRANCH_RENAME: "rename",
}

# publication_operation value -> target action (value-dependent consumer).
_PUBLICATION_OPERATION_CONSUMER = {
    "set_publication_single": "set_publication",
    "set_publication_multiple": "set_publication",
    "add_publication_single": "add_publication",
    "add_publication_multiple": "add_publication",
    "drop_publication_single": "drop_publication",
    "drop_publication_multiple": "drop_publication",
}

# enable_disable_behavior value -> target action (value-dependent consumer).
_ENABLE_DISABLE_CONSUMER = {
    "enable_from_disabled": "enable",
    "disable_from_enabled": "disable",
    "enable_already_enabled_no_effect": "enable",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch,
# publication_operation, enable_disable_behavior) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "subscription_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "publication_operation": _REPRESENTATIVE_ACTION,
    "refresh_publication_option": "refresh_publication",
    "enable_disable_behavior": _REPRESENTATIVE_ACTION,
    "subscription_parameter": "set_parameters",
    "skip_option": "skip",
    "owner_to_shape": "owner_to",
    "rename_behavior": "rename",
    "connection_change": "connection",
    "subscription_name_shape": _REPRESENTATIVE_ACTION,
    "publication_name_shape": "set_publication",
    "new_name_shape": "rename",
    "conninfo_string_shape": "connection",
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "replication_connection": "refresh_publication",
    "publication_dependency": "refresh_publication",
    "nonexistent_subscription": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "replication_connection_failure": "refresh_publication",
    "publication_not_exists_on_remote": "refresh_publication",
    "disable_while_enabled": "disable",
    "drop_all_publications": "drop_publication",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("subscription_state", "non_existent"),
        ("subscription_name_shape", "non_existent_name"),
        ("nonexistent_subscription", "subscription_does_not_exist"),
        ("executor_privilege", "non_superuser"),
        ("privilege_insufficient", "non_superuser_altering_subscription"),
        ("replication_connection", "connection_unavailable"),
        ("replication_connection_failure", "connection_refused_on_refresh"),
        ("publication_dependency", "publication_not_exists_on_remote"),
        ("publication_not_exists_on_remote", "remote_publication_not_exists"),
        ("conninfo_string_shape", "invalid_conninfo"),
        ("connection_change", "invalid_new_conninfo"),
        ("new_name_shape", "existing_name_conflict"),
        ("rename_behavior", "rename_to_existing_name_conflict"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "subscription_does_not_exist_provisional",
    ),
    ("subscription_state", "non_existent"): (
        "42704",
        "subscription_does_not_exist_provisional",
    ),
    ("subscription_name_shape", "non_existent_name"): (
        "42704",
        "subscription_does_not_exist_provisional",
    ),
    ("nonexistent_subscription", "subscription_does_not_exist"): (
        "42704",
        "subscription_does_not_exist_provisional",
    ),
    ("executor_privilege", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_superuser_altering_subscription"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("replication_connection", "connection_unavailable"): (
        "08006",
        "connection_failure_provisional",
    ),
    ("replication_connection_failure", "connection_refused_on_refresh"): (
        "08006",
        "connection_failure_provisional",
    ),
    ("publication_dependency", "publication_not_exists_on_remote"): (
        "42704",
        "publication_does_not_exist_provisional",
    ),
    ("publication_not_exists_on_remote", "remote_publication_not_exists"): (
        "42704",
        "publication_does_not_exist_provisional",
    ),
    ("conninfo_string_shape", "invalid_conninfo"): (
        "08001",
        "invalid_connection_string_provisional",
    ),
    ("connection_change", "invalid_new_conninfo"): (
        "08001",
        "invalid_connection_string_provisional",
    ),
    ("new_name_shape", "existing_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("rename_behavior", "rename_to_existing_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[AlterSubscriptionGrammarAction, ...]
):
    """Freeze every ALTER SUBSCRIPTION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "connection",
            _BRANCH_CONNECTION,
            "ALTER SUBSCRIPTION name CONNECTION 'conninfo'",
            "synopsis-connection",
        ),
        (
            "set_publication",
            _BRANCH_SET_PUBLICATION,
            (
                "ALTER SUBSCRIPTION name SET PUBLICATION "
                "publication_name [, ...] [ WITH ( option [= value] ) ]"
            ),
            "synopsis-set-publication",
        ),
        (
            "add_publication",
            _BRANCH_ADD_PUBLICATION,
            (
                "ALTER SUBSCRIPTION name ADD PUBLICATION "
                "publication_name [, ...] [ WITH ( option [= value] ) ]"
            ),
            "synopsis-add-publication",
        ),
        (
            "drop_publication",
            _BRANCH_DROP_PUBLICATION,
            (
                "ALTER SUBSCRIPTION name DROP PUBLICATION "
                "publication_name [, ...] [ WITH ( option [= value] ) ]"
            ),
            "synopsis-drop-publication",
        ),
        (
            "refresh_publication",
            _BRANCH_REFRESH,
            (
                "ALTER SUBSCRIPTION name REFRESH PUBLICATION "
                "[ WITH ( option [= value] ) ]"
            ),
            "synopsis-refresh-publication",
        ),
        (
            "enable",
            _BRANCH_ENABLE,
            "ALTER SUBSCRIPTION name ENABLE",
            "synopsis-enable",
        ),
        (
            "disable",
            _BRANCH_DISABLE,
            "ALTER SUBSCRIPTION name DISABLE",
            "synopsis-disable",
        ),
        (
            "set_parameters",
            _BRANCH_SET_PARAMETERS,
            (
                "ALTER SUBSCRIPTION name SET "
                "( subscription_parameter [= value] [, ...] )"
            ),
            "synopsis-set-parameters",
        ),
        (
            "skip",
            _BRANCH_SKIP,
            "ALTER SUBSCRIPTION name SKIP ( skip_option = value )",
            "synopsis-skip",
        ),
        (
            "owner_to",
            _BRANCH_OWNER,
            (
                "ALTER SUBSCRIPTION name OWNER TO "
                "{ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
            ),
            "synopsis-owner-to",
        ),
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER SUBSCRIPTION name RENAME TO new_name",
            "synopsis-rename",
        ),
    )
    actions = [
        AlterSubscriptionGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 11:
        raise AlterSubscriptionFactorLoopError(
            "alter subscription action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterSubscriptionFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "publication_operation":
        try:
            return _PUBLICATION_OPERATION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterSubscriptionFactorLoopError(
                f"unknown publication_operation value: {row.value}"
            ) from exc
    if row.factor == "enable_disable_behavior":
        try:
            return _ENABLE_DISABLE_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterSubscriptionFactorLoopError(
                f"unknown enable_disable_behavior value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterSubscriptionFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[AlterSubscriptionFactorObligation]
):
    rows: list[AlterSubscriptionFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterSubscriptionFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ASUB-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 11:
        raise AlterSubscriptionFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterSubscriptionFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_subscription")
    if len(catalog_rows) != 70:
        raise AlterSubscriptionFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[AlterSubscriptionFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterSubscriptionFactorObligation(
                ordinal=0,
                obligation_id=f"ASUB-SFV|{row.row_id}|{consumer}",
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


def _obligation_multiset_sha256(
    rows: tuple[AlterSubscriptionFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-subscription-factor-obligations-v1\n"
    )
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
                    "delegated_statement_key": (
                        row.delegated_statement_key
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "connection": _BRANCH_CONNECTION,
    "set_publication": _BRANCH_SET_PUBLICATION,
    "add_publication": _BRANCH_ADD_PUBLICATION,
    "drop_publication": _BRANCH_DROP_PUBLICATION,
    "refresh_publication": _BRANCH_REFRESH,
    "enable": _BRANCH_ENABLE,
    "disable": _BRANCH_DISABLE,
    "set_parameters": _BRANCH_SET_PARAMETERS,
    "skip": _BRANCH_SKIP,
    "owner_to": _BRANCH_OWNER,
    "rename": _BRANCH_RENAME,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors (nonexistent_subscription, privilege_insufficient,
# replication_connection_failure, publication_not_exists_on_remote,
# disable_while_enabled, drop_all_publications) are NOT baselined here:
# every declared value is either a failure mode (the first four) or a
# branch-specific boundary (the last two), so they are set only when they
# are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_SET_PARAMETERS,
    "grammar_branch": _BRANCH_SET_PARAMETERS,
    "target_action": "set_parameters",
    "subscription_state": "exists_enabled",
    "expected_status": "success",
    "publication_operation": "set_publication_single",
    "refresh_publication_option": "without_with_clause",
    "enable_disable_behavior": "enable_from_disabled",
    "subscription_parameter": "single_parameter",
    "skip_option": "skip_lsn",
    "owner_to_shape": "explicit_role_name",
    "rename_behavior": "rename_to_new_name",
    "connection_change": "valid_new_conninfo",
    "subscription_name_shape": "simple_name",
    "publication_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "conninfo_string_shape": "valid_conninfo",
    "executor_privilege": "superuser",
    "replication_connection": "connection_available",
    "publication_dependency": "publication_exists_on_remote",
    "verification_mode": "pg_subscription_catalog",
    "cleanup_mode": "drop_subscription",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    ss = a.get("subscription_state", "exists_enabled")
    sns = a.get("subscription_name_shape", "simple_name")
    ns = a.get("nonexistent_subscription", "")
    ep = a.get("executor_privilege", "superuser")
    pi = a.get("privilege_insufficient", "")
    rc = a.get("replication_connection", "connection_available")
    rcf = a.get("replication_connection_failure", "")
    pd = a.get("publication_dependency", "publication_exists_on_remote")
    pner = a.get("publication_not_exists_on_remote", "")
    cs = a.get("conninfo_string_shape", "valid_conninfo")
    cc = a.get("connection_change", "valid_new_conninfo")
    nns = a.get("new_name_shape", "simple_name")
    rb = a.get("rename_behavior", "rename_to_new_name")
    edb = a.get("enable_disable_behavior", "enable_from_disabled")
    dwe = a.get("disable_while_enabled", "")
    dap = a.get("drop_all_publications", "")

    # nonexistent subscription cluster: subscription_state /
    # subscription_name_shape / nonexistent_subscription
    if (
        ss == "non_existent"
        or sns == "non_existent_name"
        or ns == "subscription_does_not_exist"
    ):
        a["subscription_state"] = "non_existent"
        a["subscription_name_shape"] = "non_existent_name"
        a["nonexistent_subscription"] = "subscription_does_not_exist"

    # non-superuser cluster: executor_privilege / privilege_insufficient
    if ep == "non_superuser" or pi == "non_superuser_altering_subscription":
        a["executor_privilege"] = "non_superuser"
        a["privilege_insufficient"] = "non_superuser_altering_subscription"

    # connection-unavailable cluster: replication_connection /
    # replication_connection_failure
    if (
        rc == "connection_unavailable"
        or rcf == "connection_refused_on_refresh"
    ):
        a["replication_connection"] = "connection_unavailable"
        a["replication_connection_failure"] = "connection_refused_on_refresh"

    # publication-not-on-remote cluster: publication_dependency /
    # publication_not_exists_on_remote
    if (
        pd == "publication_not_exists_on_remote"
        or pner == "remote_publication_not_exists"
    ):
        a["publication_dependency"] = "publication_not_exists_on_remote"
        a["publication_not_exists_on_remote"] = "remote_publication_not_exists"

    # invalid-conninfo cluster: conninfo_string_shape / connection_change
    if cs == "invalid_conninfo" or cc == "invalid_new_conninfo":
        a["conninfo_string_shape"] = "invalid_conninfo"
        a["connection_change"] = "invalid_new_conninfo"

    # rename-conflict cluster: new_name_shape / rename_behavior
    if (
        nns == "existing_name_conflict"
        or rb == "rename_to_existing_name_conflict"
    ):
        a["new_name_shape"] = "existing_name_conflict"
        a["rename_behavior"] = "rename_to_existing_name_conflict"

    # disable_while_enabled <-> enable_disable_behavior=disable_from_enabled
    if (
        edb == "disable_from_enabled"
        or dwe == "disable_active_subscription"
    ):
        a["enable_disable_behavior"] = "disable_from_enabled"
        a["disable_while_enabled"] = "disable_active_subscription"

    # drop_all_publications <-> publication_operation=drop_publication_single
    if (
        a.get("publication_operation") == "drop_publication_single"
        or dap == "dropping_last_publication"
    ):
        a["publication_operation"] = "drop_publication_single"
        a["drop_all_publications"] = "dropping_last_publication"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterSubscriptionFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments["target_action"] = obligation.consumer_action_id
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise AlterSubscriptionFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterSubscriptionFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterSubscriptionFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_subscription_factor_loop_plan(
    repository_root: Path,
) -> AlterSubscriptionFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_subscription_factor_loop_obligations(root)
    cases: list[AlterSubscriptionFactorCase] = []
    delegated: list[AlterSubscriptionFactorObligation] = []
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
            AlterSubscriptionFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERSUBSCRIPTION{ordinal:05d}",
                sql_filename=f"ALTERSUBSCRIPTION{ordinal:05d}.sql",
                object_prefix=(
                    f"alter_subscription_{ordinal:05d}_"
                ),
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
    plan = AlterSubscriptionFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 81 or len(plan.delegated) != 0:
        raise AlterSubscriptionFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 81:
        raise AlterSubscriptionFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 81:
        raise AlterSubscriptionFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_subscription_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterSubscriptionFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterSubscriptionFactorObligation(
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
    if len(rows) != 81:
        raise AlterSubscriptionFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterSubscriptionFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 11, "SFV": 70}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterSubscriptionFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterSubscriptionFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 81:
        raise AlterSubscriptionFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterSubscriptionFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "AlterSubscriptionFactorLoopError",
    "AlterSubscriptionGrammarAction",
    "AlterSubscriptionFactorObligation",
    "AlterSubscriptionFactorCase",
    "AlterSubscriptionFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_subscription_factor_loop_obligations",
    "build_alter_subscription_factor_loop_plan",
    "_obligation_multiset_sha256",
]
