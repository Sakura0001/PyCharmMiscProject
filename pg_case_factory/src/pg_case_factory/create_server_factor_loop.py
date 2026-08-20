"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE SERVER.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE SERVER``.  The statement has two official synopsis branches
(``branch_create_server`` and ``branch_create_server_if_not_exists``):
``CREATE SERVER [ IF NOT EXISTS ] server_name [ TYPE 'server_type' ]
[ VERSION 'server_version' ] FOREIGN DATA WRAPPER fdw_name
[ OPTIONS ( option 'value' [, ... ] ) ]``.  The statement registers a
row in ``pg_catalog.pg_foreign_server`` (not a ``pg_class`` relation),
so column/table/relation coverage is ``not_applicable`` and there is
no ``INV`` block.

Each local obligation becomes exactly one regress program.  CREATE
SERVER requires superuser privilege, so ``executor_privilege=non_superuser``
is an expected failure (SQLSTATE 42501).  The inventory declares 18
factors / 41 factor values; together with the two GRM synopsis
obligations the ledger has 43 local cases.

The grammar ledger is self-contained (there is no separate
``create_server_regress`` module): the 2 synopsis actions are frozen
inline.  The 41 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateServerFactorLoopError(ValueError):
    """Raised when a frozen CREATE SERVER obligation input drifts."""


@dataclass(frozen=True)
class CreateServerGrammarAction:
    """One official target action form of the CREATE SERVER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateServerFactorObligation:
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
class CreateServerFactorCase:
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
class CreateServerFactorLoopPlan:
    obligations: tuple[CreateServerFactorObligation, ...]
    cases: tuple[CreateServerFactorCase, ...]
    delegated: tuple[CreateServerFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createserver.html).
_BRANCH_CREATE_SERVER = "branch_create_server"
_BRANCH_CREATE_SERVER_IF_NOT_EXISTS = "branch_create_server_if_not_exists"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createserver"

# CREATE SERVER has two synopsis branches (with / without IF NOT EXISTS).
# The without-IF-NOT-EXISTS form is the representative action for
# canonical factors that are not bound to a specific branch.
_REPRESENTATIVE_ACTION = "create_server"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_CREATE_SERVER: "create_server",
    _BRANCH_CREATE_SERVER_IF_NOT_EXISTS: "create_server_if_not_exists",
}

# if_not_exists_clause canonical value -> target action.
_IF_NOT_EXISTS_CONSUMER = {
    "without_if_not_exists": "create_server",
    "with_if_not_exists": "create_server_if_not_exists",
}

# Canonical factor -> the action where the value is observable.
# Factors whose consumer depends on the value (statement_branch,
# if_not_exists_clause) are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "server_identity": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "type_version_clause": _REPRESENTATIVE_ACTION,
    "options_clause": _REPRESENTATIVE_ACTION,
    "fdw_dependency": _REPRESENTATIVE_ACTION,
    "server_name_shape": _REPRESENTATIVE_ACTION,
    "fdw_name_shape": _REPRESENTATIVE_ACTION,
    "option_value_shape": _REPRESENTATIVE_ACTION,
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "fdw_existence": _REPRESENTATIVE_ACTION,
    "duplicate_server_name": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "nonexistent_fdw": _REPRESENTATIVE_ACTION,
    "fdw_validator_rejection": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target
# check and are rejected (provisional sqlstates -- DB phase verifies
# on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("server_identity", "exists"),
        ("server_identity", "quoted_duplicate"),
        ("fdw_dependency", "nonexistent_fdw"),
        ("fdw_existence", "fdw_not_exists"),
        ("fdw_name_shape", "nonexistent_fdw_name"),
        ("executor_privilege", "non_superuser"),
        ("duplicate_server_name", "same_name_exists"),
        ("privilege_insufficient", "non_superuser_creating_server"),
        ("nonexistent_fdw", "fdw_does_not_exist"),
        ("fdw_validator_rejection", "validator_rejects_invalid_option"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure
# value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("server_identity", "exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("server_identity", "quoted_duplicate"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("fdw_dependency", "nonexistent_fdw"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("fdw_existence", "fdw_not_exists"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("fdw_name_shape", "nonexistent_fdw_name"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("executor_privilege", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("duplicate_server_name", "same_name_exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("privilege_insufficient", "non_superuser_creating_server"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("nonexistent_fdw", "fdw_does_not_exist"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("fdw_validator_rejection", "validator_rejects_invalid_option"): (
        "HV000",
        "fdw_error_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateServerGrammarAction, ...]:
    """Freeze every CREATE SERVER synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_server",
            _BRANCH_CREATE_SERVER,
            (
                "CREATE SERVER server_name [ TYPE 'server_type' ] "
                "[ VERSION 'server_version' ] FOREIGN DATA WRAPPER "
                "fdw_name [ OPTIONS ( option 'value' [, ... ] ) ]"
            ),
            "synopsis-branch-create-server",
        ),
        (
            "create_server_if_not_exists",
            _BRANCH_CREATE_SERVER_IF_NOT_EXISTS,
            (
                "CREATE SERVER IF NOT EXISTS server_name "
                "[ TYPE 'server_type' ] [ VERSION 'server_version' ] "
                "FOREIGN DATA WRAPPER fdw_name "
                "[ OPTIONS ( option 'value' [, ... ] ) ]"
            ),
            "synopsis-branch-create-server-if-not-exists",
        ),
    )
    actions = [
        CreateServerGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise CreateServerFactorLoopError(
            "create server action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateServerFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "if_not_exists_clause":
        try:
            return _IF_NOT_EXISTS_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateServerFactorLoopError(
                f"unknown if_not_exists_clause value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateServerFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CreateServerFactorObligation]:
    rows: list[CreateServerFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateServerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CSRV-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 2:
        raise CreateServerFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateServerFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_server")
    if len(catalog_rows) != 41:
        raise CreateServerFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateServerFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateServerFactorObligation(
                ordinal=0,
                obligation_id=f"CSRV-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateServerFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-server-factor-obligations-v1\n"
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
    "create_server": _BRANCH_CREATE_SERVER,
    "create_server_if_not_exists": _BRANCH_CREATE_SERVER_IF_NOT_EXISTS,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).
# The T5 single-value factors (duplicate_server_name,
# privilege_insufficient, nonexistent_fdw, fdw_validator_rejection)
# overlap with their T1-T4 counterparts and are derived in
# :func:`_derive_overlapping_factors`, not baselined here as failure
# values.  Success counterparts for single-value T5 factors
# (superuser_creating_server, fdw_does_exist) are NOT in the TSV but
# are used as baseline defaults.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE_SERVER,
    "grammar_branch": _BRANCH_CREATE_SERVER,
    "target_action": "create_server",
    "server_identity": "not_exists",
    "expected_status": "success",
    "if_not_exists_clause": "without_if_not_exists",
    "type_version_clause": "omitted",
    "options_clause": "omitted",
    "fdw_dependency": "existing_fdw",
    "server_name_shape": "simple_name",
    "fdw_name_shape": "existing_fdw_name",
    "option_value_shape": "valid_option_value",
    "executor_privilege": "superuser",
    "fdw_existence": "fdw_exists",
    "duplicate_server_name": "none",
    "privilege_insufficient": "superuser_creating_server",
    "nonexistent_fdw": "fdw_does_exist",
    "fdw_validator_rejection": "none",
    "verification_mode": "pg_foreign_server_catalog",
    "cleanup_mode": "drop_server",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their
    T1-T4 counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value,
    the T1-T4 counterpart is derived.  This keeps the baseline
    assignment self-consistent so the render produces SQL that reaches
    the intended boundary.
    """

    # expected_status=failure needs a real failure trigger (duplicate).
    if a.get("expected_status") == "failure":
        if a.get("server_identity") not in (
            "exists",
            "quoted_duplicate",
        ):
            a["server_identity"] = "exists"

    si = a.get("server_identity", "not_exists")
    dsn = a.get("duplicate_server_name", "none")
    fd = a.get("fdw_dependency", "existing_fdw")
    fde = a.get("fdw_existence", "fdw_exists")
    fns = a.get("fdw_name_shape", "existing_fdw_name")
    nfdw = a.get("nonexistent_fdw", "fdw_does_exist")
    ep = a.get("executor_privilege", "superuser")
    pi = a.get("privilege_insufficient", "superuser_creating_server")
    ifne = a.get("if_not_exists_clause", "without_if_not_exists")
    sb = a.get("statement_branch", _BRANCH_CREATE_SERVER)

    # duplicate server name cluster: server_identity /
    # duplicate_server_name
    if si in ("exists", "quoted_duplicate") or dsn == "same_name_exists":
        if si not in ("exists", "quoted_duplicate"):
            a["server_identity"] = "exists"
            si = "exists"
        a["duplicate_server_name"] = "same_name_exists"
    else:
        a["duplicate_server_name"] = "none"
        if si not in ("reserved_word_name",):
            a["server_identity"] = "not_exists"

    # server_identity -> server_name_shape (reserved_word_name /
    # quoted_duplicate imply a specific name shape)
    if si == "reserved_word_name":
        a["server_name_shape"] = "reserved_word_name"
    elif si == "quoted_duplicate":
        a["server_name_shape"] = "quoted_name"

    # nonexistent FDW cluster: fdw_dependency / fdw_existence /
    # fdw_name_shape / nonexistent_fdw
    if (
        fd == "nonexistent_fdw"
        or fde == "fdw_not_exists"
        or fns == "nonexistent_fdw_name"
        or nfdw == "fdw_does_not_exist"
    ):
        a["fdw_dependency"] = "nonexistent_fdw"
        a["fdw_existence"] = "fdw_not_exists"
        a["fdw_name_shape"] = "nonexistent_fdw_name"
        a["nonexistent_fdw"] = "fdw_does_not_exist"
    else:
        a["fdw_dependency"] = "existing_fdw"
        a["fdw_existence"] = "fdw_exists"
        a["fdw_name_shape"] = "existing_fdw_name"
        a["nonexistent_fdw"] = "fdw_does_exist"

    # non-superuser cluster: executor_privilege / privilege_insufficient
    if ep == "non_superuser" or pi == "non_superuser_creating_server":
        a["executor_privilege"] = "non_superuser"
        a["privilege_insufficient"] = "non_superuser_creating_server"
    else:
        a["executor_privilege"] = "superuser"
        a["privilege_insufficient"] = "superuser_creating_server"

    # statement_branch / if_not_exists_clause cluster
    if (
        sb == _BRANCH_CREATE_SERVER_IF_NOT_EXISTS
        or ifne == "with_if_not_exists"
    ):
        a["statement_branch"] = _BRANCH_CREATE_SERVER_IF_NOT_EXISTS
        a["if_not_exists_clause"] = "with_if_not_exists"
        a["grammar_branch"] = _BRANCH_CREATE_SERVER_IF_NOT_EXISTS
        a["target_action"] = "create_server_if_not_exists"
    else:
        a["statement_branch"] = _BRANCH_CREATE_SERVER
        a["if_not_exists_clause"] = "without_if_not_exists"
        a["grammar_branch"] = _BRANCH_CREATE_SERVER
        a["target_action"] = "create_server"

    # expected_status: re-derive from the failure count
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateServerFactorObligation,
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
    if len(assignments) != len(set(assignments)):
        raise CreateServerFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateServerFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateServerFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_server_factor_loop_plan(
    repository_root: Path,
) -> CreateServerFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_server_factor_loop_obligations(root)
    cases: list[CreateServerFactorCase] = []
    delegated: list[CreateServerFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(
                obligation
            )
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            CreateServerFactorCase(
                ordinal=ordinal,
                case_id=f"CREATESERVER{ordinal:05d}",
                sql_filename=f"CREATESERVER{ordinal:05d}.sql",
                object_prefix=f"createserver_{ordinal:05d}_",
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
    plan = CreateServerFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 43 or len(plan.delegated) != 0:
        raise CreateServerFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 43:
        raise CreateServerFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 43:
        raise CreateServerFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_server_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateServerFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateServerFactorObligation(
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
    if len(rows) != 43:
        raise CreateServerFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateServerFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 41}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateServerFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateServerFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 43:
        raise CreateServerFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateServerFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateServerFactorLoopError",
    "CreateServerGrammarAction",
    "CreateServerFactorObligation",
    "CreateServerFactorCase",
    "CreateServerFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_server_factor_loop_obligations",
    "build_create_server_factor_loop_plan",
    "_obligation_multiset_sha256",
]
