"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE USER.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE USER``.  CREATE USER is a PostgreSQL alias for CREATE ROLE: it
defines a database role (a ``pg_catalog.pg_authid`` catalog row) with a
LOGIN-oriented default, not a ``pg_class`` relation.  The official synopsis
has a single branch:
``CREATE USER name [ [ WITH ] option [ ... ] ]``.

The statement touches the ``pg_catalog.pg_authid`` catalog row (not a
relation), so column/table/relation coverage is ``not_applicable`` and
there is no ``INV`` block.  CREATE USER does not create tables, so the
bookend (DROP TABLE IF EXISTS) is never emitted; a residual
``SELECT 1 AS residual_check_no_objects;`` placeholder witnesses the
table-less nature of every program.

Each local obligation becomes exactly one regress program.  The 53
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``); the 1 ``GRM`` target form is
frozen from the official synopsis branch.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateUserFactorLoopError(ValueError):
    """Raised when a frozen CREATE USER obligation input drifts."""


@dataclass(frozen=True)
class CreateUserGrammarAction:
    """One official target action form of the CREATE USER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateUserFactorObligation:
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
class CreateUserFactorCase:
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
class CreateUserFactorLoopPlan:
    obligations: tuple[CreateUserFactorObligation, ...]
    cases: tuple[CreateUserFactorCase, ...]
    delegated: tuple[CreateUserFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createuser.html).
_BRANCH = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createuser"

# A representative action used as the baseline consumer for canonical
# factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "create_user_branch_1"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH: "create_user_branch_1",
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateUserFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SSV_FAILURE_VALUES = frozenset(
    {
        # duplicate_object_name (42710)
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("duplicate_role_name", "same_name_conflict"),
        ("role_name_shape", "duplicate_name"),
        ("reserved_role_name", "reserved_name"),
        # insufficient_privilege (42501)
        ("privilege_level", "non_createrole"),
        ("insufficient_privilege", "lacks_createrole"),
        # missing_referenced_role (42704)
        ("referenced_role_name_shape", "nonexistent_role"),
        ("referenced_role_existence", "role_not_exists"),
        ("nonexistent_referenced_role", "role_missing"),
        # syntax_error (42601)
        ("role_name_shape", "invalid_name"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SSV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("object_state", "exists"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("duplicate_role_name", "same_name_conflict"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("role_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("reserved_role_name", "reserved_name"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("privilege_level", "non_createrole"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "lacks_createrole"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("referenced_role_name_shape", "nonexistent_role"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("referenced_role_existence", "role_not_exists"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("nonexistent_referenced_role", "role_missing"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("role_name_shape", "invalid_name"): (
        "42601",
        "syntax_error_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateUserGrammarAction, ...]:
    """Freeze every CREATE USER synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_user_branch_1",
            _BRANCH,
            "CREATE USER name [ [ WITH ] option [ ... ] ]",
            "synopsis-create-user-branch-1",
        ),
    )
    actions = [
        CreateUserGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateUserFactorLoopError("create user action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateUserFactorObligation]:
    rows: list[CreateUserFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateUserFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CU-GRM|{action.grammar_branch_id}|"
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
        raise CreateUserFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateUserFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_user")
    if len(catalog_rows) != 53:
        raise CreateUserFactorLoopError("canonical obligation count drift")
    rows: list[CreateUserFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SSV_FAILURE_VALUES
        rows.append(
            CreateUserFactorObligation(
                ordinal=0,
                obligation_id=f"CU-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateUserFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-user-factor-obligations-v1\n")
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
    "create_user_branch_1": _BRANCH,
}

# Dense baseline defaults (all positive factor values).  Boundary factors
# are derived in :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH,
    "object_state": "not_exists",
    "expected_status": "success",
    "login_default": "default_login",
    "role_options": "no_options",
    "password_clause": "omitted",
    "valid_until_clause": "omitted",
    "membership_clause": "omitted",
    "role_name_shape": "simple_id",
    "password_value_shape": "valid_password",
    "referenced_role_name_shape": "existing_role",
    "privilege_level": "superuser",
    "referenced_role_existence": "role_exists",
    "duplicate_role_name": "no_conflict",
    "insufficient_privilege": "has_createrole",
    "nonexistent_referenced_role": "role_exists",
    "reserved_role_name": "normal_name",
    "verification_mode": "catalog_query_pg_roles",
    "cleanup_mode": "drop_user",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SSV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive boundary factors and expected_status from primary values.

    Keeps the baseline assignment self-consistent so the render produces
    SQL that reaches the intended boundary.
    """

    # --- Group 1: duplicate scenario -------------------------------
    # expected_status / object_state / duplicate_role_name /
    # role_name_shape=duplicate_name / reserved_role_name=reserved_name
    if a.get("expected_status") == "failure":
        a["object_state"] = "exists"
        a["duplicate_role_name"] = "same_name_conflict"
    if a.get("object_state") == "exists":
        a["duplicate_role_name"] = "same_name_conflict"
    if a.get("duplicate_role_name") == "same_name_conflict":
        a["object_state"] = "exists"
    if a.get("role_name_shape") == "duplicate_name":
        a["object_state"] = "exists"
        a["duplicate_role_name"] = "same_name_conflict"
    if a.get("reserved_role_name") == "reserved_name":
        a["object_state"] = "exists"
        a["duplicate_role_name"] = "same_name_conflict"

    # --- Group 2: privilege ----------------------------------------
    if a.get("privilege_level") == "non_createrole":
        a["insufficient_privilege"] = "lacks_createrole"
    if a.get("insufficient_privilege") == "lacks_createrole":
        a["privilege_level"] = "non_createrole"
    # role_options requiring superuser executor (only when no
    # privilege failure is active)
    if a.get("insufficient_privilege") != "lacks_createrole":
        ro = a.get("role_options", "no_options")
        if ro == "single_option_superuser":
            a["privilege_level"] = "superuser"

    # --- Group 3: referenced-role failure --------------------------
    if a.get("referenced_role_name_shape") == "nonexistent_role":
        a["referenced_role_existence"] = "role_not_exists"
        a["nonexistent_referenced_role"] = "role_missing"
        a["membership_clause"] = "in_role"
    if a.get("referenced_role_existence") == "role_not_exists":
        a["referenced_role_name_shape"] = "nonexistent_role"
        a["nonexistent_referenced_role"] = "role_missing"
        a["membership_clause"] = "in_role"
    if a.get("nonexistent_referenced_role") == "role_missing":
        a["referenced_role_name_shape"] = "nonexistent_role"
        a["referenced_role_existence"] = "role_not_exists"
        a["membership_clause"] = "in_role"

    # --- Group 4: arm clauses for non-default T3 values -----------
    pvs = a.get("password_value_shape", "valid_password")
    if pvs == "null_password":
        a["password_clause"] = "password_null"
    elif pvs == "empty_password":
        a["password_clause"] = "password_value"

    # --- Derive expected_status from failure count -----------------
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateUserFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
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
        raise CreateUserFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateUserFactorObligation,
) -> tuple[str, str]:
    try:
        return _SSV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateUserFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_user_factor_loop_plan(
    repository_root: Path,
) -> CreateUserFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_user_factor_loop_obligations(root)
    cases: list[CreateUserFactorCase] = []
    delegated: list[CreateUserFactorObligation] = []
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
            CreateUserFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEUSER{ordinal:05d}",
                sql_filename=f"CREATEUSER{ordinal:05d}.sql",
                object_prefix=f"createuser_{ordinal:05d}_",
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
    plan = CreateUserFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 54 or len(plan.delegated) != 0:
        raise CreateUserFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 54:
        raise CreateUserFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 54:
        raise CreateUserFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_user_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateUserFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateUserFactorObligation(
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
    if len(rows) != 54:
        raise CreateUserFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateUserFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 53}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateUserFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateUserFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 54:
        raise CreateUserFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateUserFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateUserFactorLoopError",
    "CreateUserGrammarAction",
    "CreateUserFactorObligation",
    "CreateUserFactorCase",
    "CreateUserFactorLoopPlan",
    "_SSV_FAILURE_SQLSTATE",
    "_SSV_FAILURE_VALUES",
    "compile_create_user_factor_loop_obligations",
    "build_create_user_factor_loop_plan",
    "_obligation_multiset_sha256",
]
