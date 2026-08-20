"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE SUBSCRIPTION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE SUBSCRIPTION``.  CREATE SUBSCRIPTION is a PostgreSQL logical-
replication DDL statement with a single official synopsis branch:
``CREATE SUBSCRIPTION name CONNECTION 'conninfo' PUBLICATION pub [, ...]
[ WITH ( parameter [= value] [, ...] ) ]``.

The statement touches the ``pg_catalog.pg_subscription`` catalog row (not
a ``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.  CREATE SUBSCRIPTION
does not create tables, so the bookend (DROP TABLE IF EXISTS) is never
emitted.  Cleanup uses ``DROP SUBSCRIPTION IF EXISTS`` plus ``DROP ROLE``.

Each local obligation becomes exactly one regress program.  The 54
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateSubscriptionFactorLoopError(ValueError):
    """Raised when a frozen CREATE SUBSCRIPTION obligation input drifts."""


@dataclass(frozen=True)
class CreateSubscriptionGrammarAction:
    """One official target action form of the CREATE SUBSCRIPTION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateSubscriptionFactorObligation:
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
class CreateSubscriptionFactorCase:
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
class CreateSubscriptionFactorLoopPlan:
    obligations: tuple[CreateSubscriptionFactorObligation, ...]
    cases: tuple[CreateSubscriptionFactorCase, ...]
    delegated: tuple[CreateSubscriptionFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createsubscription.html).
_BRANCH_CREATE = "branch_create_subscription"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createsubscription"

# The single define action used as the baseline consumer for all canonical
# factors.  CREATE SUBSCRIPTION has only one synopsis branch.
_REPRESENTATIVE_ACTION = "create_subscription"

_CONSUMER_ACTION = "create_subscription"


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("subscription_identity", "exists"),
        ("subscription_identity", "quoted_duplicate"),
        ("duplicate_subscription_name", "same_name_exists"),
        ("executor_privilege", "non_superuser"),
        ("privilege_insufficient", "non_superuser_creating_subscription"),
        ("replication_connection", "connection_unavailable"),
        ("replication_connection_failure", "authentication_failed"),
        ("replication_connection_failure", "connection_refused"),
        ("conninfo_string_shape", "invalid_conninfo_string"),
        ("invalid_conninfo", "malformed_conninfo"),
        ("publication_dependency", "publication_not_exists_on_remote"),
        ("publication_not_exists_on_remote", "remote_publication_not_exists"),
        ("expected_status", "failure"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("subscription_identity", "exists"): (
        "42710",
        "duplicate_subscription_provisional",
    ),
    ("subscription_identity", "quoted_duplicate"): (
        "42710",
        "duplicate_subscription_provisional",
    ),
    ("duplicate_subscription_name", "same_name_exists"): (
        "42710",
        "duplicate_subscription_provisional",
    ),
    ("executor_privilege", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_superuser_creating_subscription"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("replication_connection", "connection_unavailable"): (
        "08006",
        "connection_failure_provisional",
    ),
    ("replication_connection_failure", "authentication_failed"): (
        "08006",
        "connection_failure_provisional",
    ),
    ("replication_connection_failure", "connection_refused"): (
        "08006",
        "connection_failure_provisional",
    ),
    ("conninfo_string_shape", "invalid_conninfo_string"): (
        "08001",
        "invalid_connection_string_provisional",
    ),
    ("invalid_conninfo", "malformed_conninfo"): (
        "08001",
        "invalid_connection_string_provisional",
    ),
    ("publication_dependency", "publication_not_exists_on_remote"): (
        "42704",
        "publication_does_not_exist_provisional",
    ),
    ("publication_not_exists_on_remote", "remote_publication_not_exists"): (
        "42704",
        "publication_does_not_exist_provisional",
    ),
    ("expected_status", "failure"): (
        "42710",
        "duplicate_subscription_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateSubscriptionGrammarAction, ...]
):
    """Freeze every CREATE SUBSCRIPTION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_subscription",
            _BRANCH_CREATE,
            (
                "CREATE SUBSCRIPTION name CONNECTION 'conninfo' "
                "PUBLICATION publication_name [, ...] "
                "[ WITH ( subscription_parameter [= value] [, ...] ) ]"
            ),
            "synopsis-create-subscription",
        ),
    )
    actions = [
        CreateSubscriptionGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateSubscriptionFactorLoopError(
            "create subscription action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateSubscriptionFactorObligation]
):
    rows: list[CreateSubscriptionFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateSubscriptionFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CSUB-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_form|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_form",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise CreateSubscriptionFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateSubscriptionFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_subscription")
    if len(catalog_rows) != 54:
        raise CreateSubscriptionFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateSubscriptionFactorObligation] = []
    for row in catalog_rows:
        consumer = _CONSUMER_ACTION
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateSubscriptionFactorObligation(
                ordinal=0,
                obligation_id=f"CSUB-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateSubscriptionFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-subscription-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors (duplicate_subscription_name, invalid_conninfo,
# privilege_insufficient, publication_not_exists_on_remote,
# replication_connection_failure) are NOT baselined here: every declared
# value is a failure mode, so they are set only when they are the primary
# (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE,
    "grammar_branch": _BRANCH_CREATE,
    "target_form": _CONSUMER_ACTION,
    "subscription_identity": "not_exists",
    "expected_status": "success",
    "connection_info": "valid_conninfo",
    "conninfo_string_shape": "valid_conninfo_string",
    "copy_data_behavior": "copy_data_false",
    "executor_privilege": "superuser",
    "publication_dependency": "publication_exists_on_remote",
    "publication_list": "single_publication",
    "publication_name_shape": "simple_name",
    "replication_connection": "connection_available",
    "slot_name_behavior": "default_auto_slot",
    "subscription_name_shape": "simple_name",
    "with_parameter_clause": "omitted",
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

    si = a.get("subscription_identity", "not_exists")
    dsn = a.get("duplicate_subscription_name", "")
    ep = a.get("executor_privilege", "superuser")
    pi = a.get("privilege_insufficient", "")
    rc = a.get("replication_connection", "connection_available")
    rcf = a.get("replication_connection_failure", "")
    cs = a.get("conninfo_string_shape", "valid_conninfo_string")
    ic = a.get("invalid_conninfo", "")
    pd = a.get("publication_dependency", "publication_exists_on_remote")
    pner = a.get("publication_not_exists_on_remote", "")

    # duplicate cluster: subscription_identity /
    # duplicate_subscription_name
    if si in ("exists", "quoted_duplicate") or dsn == "same_name_exists":
        if si == "not_exists" and dsn == "same_name_exists":
            a["subscription_identity"] = "exists"
        a["duplicate_subscription_name"] = "same_name_exists"

    # non-superuser cluster: executor_privilege / privilege_insufficient
    if ep == "non_superuser" or pi == "non_superuser_creating_subscription":
        a["executor_privilege"] = "non_superuser"
        a["privilege_insufficient"] = "non_superuser_creating_subscription"

    # connection-unavailable cluster: replication_connection /
    # replication_connection_failure
    if (
        rc == "connection_unavailable"
        or rcf in ("authentication_failed", "connection_refused")
    ):
        a["replication_connection"] = "connection_unavailable"
        if not rcf:
            a["replication_connection_failure"] = "connection_refused"

    # invalid-conninfo cluster: conninfo_string_shape / invalid_conninfo
    if cs == "invalid_conninfo_string" or ic == "malformed_conninfo":
        a["conninfo_string_shape"] = "invalid_conninfo_string"
        a["invalid_conninfo"] = "malformed_conninfo"

    # publication-not-on-remote cluster: publication_dependency /
    # publication_not_exists_on_remote
    if (
        pd == "publication_not_exists_on_remote"
        or pner == "remote_publication_not_exists"
    ):
        a["publication_dependency"] = "publication_not_exists_on_remote"
        a["publication_not_exists_on_remote"] = (
            "remote_publication_not_exists"
        )


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateSubscriptionFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _BRANCH_CREATE
    assignments["grammar_branch"] = _BRANCH_CREATE
    assignments["target_form"] = _CONSUMER_ACTION
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateSubscriptionFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateSubscriptionFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateSubscriptionFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_subscription_factor_loop_plan(
    repository_root: Path,
) -> CreateSubscriptionFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_subscription_factor_loop_obligations(root)
    cases: list[CreateSubscriptionFactorCase] = []
    delegated: list[CreateSubscriptionFactorObligation] = []
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
            CreateSubscriptionFactorCase(
                ordinal=ordinal,
                case_id=f"CREATESUBSCRIPTION{ordinal:05d}",
                sql_filename=f"CREATESUBSCRIPTION{ordinal:05d}.sql",
                object_prefix=f"createsubscription_{ordinal:05d}_",
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
    plan = CreateSubscriptionFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 55 or len(plan.delegated) != 0:
        raise CreateSubscriptionFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 55:
        raise CreateSubscriptionFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 55:
        raise CreateSubscriptionFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_subscription_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateSubscriptionFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateSubscriptionFactorObligation(
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
        raise CreateSubscriptionFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateSubscriptionFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 54}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateSubscriptionFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateSubscriptionFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 55:
        raise CreateSubscriptionFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateSubscriptionFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateSubscriptionFactorLoopError",
    "CreateSubscriptionGrammarAction",
    "CreateSubscriptionFactorObligation",
    "CreateSubscriptionFactorCase",
    "CreateSubscriptionFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_subscription_factor_loop_obligations",
    "build_create_subscription_factor_loop_plan",
    "_obligation_multiset_sha256",
]
