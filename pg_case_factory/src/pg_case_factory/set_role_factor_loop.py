"""Factor-value-loop obligation ledger for PostgreSQL 18.4 SET ROLE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``SET ROLE`` — set the current user identifier of the current session.  The
official synopsis (``SET [ SESSION | LOCAL ] ROLE role_name`` /
``SET [ SESSION | LOCAL ] ROLE NONE`` / ``RESET ROLE``) has exactly one
branch, so there is a single ``GRM`` obligation.  The 42 canonical ``SFV``
factor-value pairs are hardcoded verbatim from the canonical combination
matrix ``set_role.yaml`` (the package binds directly to the matrix, which
is the source of truth); ``factor_value_count == 42``.

SET ROLE is a session-scoped statement with no privilege restriction in the
no-DB tickoff phase.  The only reachable failure surface is ``SET ROLE``
executed inside a transaction block, which PostgreSQL rejects with
SQLSTATE ``25001`` (``active_sql_transaction``).  Three canonical factor
values reach this surface: the declared meta-failure
``expected_status=failure`` and the two in-transaction
``transaction_visibility`` values.  The remaining 39 ``SFV`` values plus
the single ``GRM`` form are success-covered.

Each local obligation becomes exactly one regress program.  There are no
``INV`` (column/table) obligations and no ``RISK`` obligations.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import stable_catalog_row_id


class SetRoleFactorLoopError(ValueError):
    """Raised when a frozen SET ROLE obligation input drifts."""


@dataclass(frozen=True)
class SetRoleGrammarAction:
    """One official target action form of the SET ROLE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class SetRoleFactorObligation:
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
class SetRoleFactorCase:
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
class SetRoleFactorLoopPlan:
    obligations: tuple[SetRoleFactorObligation, ...]
    cases: tuple[SetRoleFactorCase, ...]
    delegated: tuple[SetRoleFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-set-role.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-set-role"

# The single representative action for all canonical factors.
_REPRESENTATIVE_ACTION = "set_role"

_STATEMENT_KEY = "set_role"

_MATRIX_PATH = (
    "skills/pg-sql-generation/references/combinations/session/"
    "authorization/set_role.yaml"
)
_REFERENCE_PATH = (
    "references/statements/session/authorization/set_role.md"
)

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1: _REPRESENTATIVE_ACTION,
}

# Canonical factor -> the action where the value is observable.  Since
# SET ROLE has only one synopsis form, every factor observes on the single
# ``set_role`` action.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "session_state": _REPRESENTATIVE_ACTION,
    "scope_shape": _REPRESENTATIVE_ACTION,
    "value_shape": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "payload_shape": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "transaction_visibility": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs hardcoded verbatim from set_role.yaml.
# factor_value_count == sum(len(values)) == 42 across the 13 factors.
_CANONICAL_FACTOR_VALUES: tuple[tuple[str, str], ...] = (
    ("statement_branch", "branch_1"),
    ("expected_status", "success"),
    ("expected_status", "failure"),
    ("session_state", "default_state"),
    ("session_state", "modified_state"),
    ("session_state", "missing_channel_or_role"),
    ("session_state", "restored_state"),
    ("scope_shape", "session"),
    ("scope_shape", "local"),
    ("scope_shape", "all"),
    ("scope_shape", "default_or_reset"),
    ("value_shape", "valid_value"),
    ("value_shape", "default_value"),
    ("value_shape", "invalid_value"),
    ("value_shape", "list_or_identifier_value"),
    ("name_shape", "plain_identifier"),
    ("name_shape", "schema_qualified"),
    ("name_shape", "quoted_identifier"),
    ("name_shape", "alias_used"),
    ("payload_shape", "absent"),
    ("payload_shape", "short_text"),
    ("payload_shape", "boundary_length"),
    ("payload_shape", "invalid_payload"),
    ("dependency_state", "ready"),
    ("dependency_state", "missing_dependency"),
    ("privilege_context", "owner"),
    ("privilege_context", "granted_role"),
    ("privilege_context", "insufficient_privilege"),
    ("privilege_context", "authenticated_user_permission_check"),
    ("invalid_combination", "none"),
    ("invalid_combination", "syntax_valid_semantic_error"),
    ("invalid_combination", "object_type_mismatch"),
    ("transaction_visibility", "outside_transaction"),
    ("transaction_visibility", "inside_committed_transaction"),
    ("transaction_visibility", "inside_rolled_back_transaction"),
    ("verification_mode", "catalog_query"),
    ("verification_mode", "effect_query"),
    ("verification_mode", "returned_rows"),
    ("verification_mode", "error_assertion"),
    ("cleanup_mode", "rollback"),
    ("cleanup_mode", "drop_objects"),
    ("cleanup_mode", "reset_state"),
)

_FACTOR_VALUE_COUNT = len(_CANONICAL_FACTOR_VALUES)

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
# SET ROLE's only reachable failure surface is SET ROLE inside a transaction
# block (SQLSTATE 25001, active_sql_transaction).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("transaction_visibility", "inside_committed_transaction"),
        ("transaction_visibility", "inside_rolled_back_transaction"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "25001",
        "set_role_declared_failure",
    ),
    ("transaction_visibility", "inside_committed_transaction"): (
        "25001",
        "set_role_declared_failure",
    ),
    ("transaction_visibility", "inside_rolled_back_transaction"): (
        "25001",
        "set_role_declared_failure",
    ),
}


def _load_grammar_actions() -> tuple[SetRoleGrammarAction, ...]:
    """Freeze every SET ROLE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "set_role",
            _BRANCH_1,
            "SET [ SESSION | LOCAL ] ROLE { role_name | NONE }",
            "synopsis-set-role",
        ),
    )
    actions = [
        SetRoleGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise SetRoleFactorLoopError("set_role action count drift")
    return tuple(actions)


def _canonical_consumer(factor: str, value: str) -> str:
    """Map a canonical factor value to its target consumer action."""

    if factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[value]
        except KeyError as exc:
            raise SetRoleFactorLoopError(
                f"unknown statement branch value: {value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[factor]
    except KeyError as exc:
        raise SetRoleFactorLoopError(
            f"canonical factor has no consumer action: {factor}"
        ) from exc


def _compile_grammar_obligations() -> list[SetRoleFactorObligation]:
    rows: list[SetRoleFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            SetRoleFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"SETROLE-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 1:
        raise SetRoleFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations() -> list[SetRoleFactorObligation]:
    """Hardcoded SFV obligations verbatim from set_role.yaml."""

    if _FACTOR_VALUE_COUNT != 42:
        raise SetRoleFactorLoopError("canonical factor value count drift")
    rows: list[SetRoleFactorObligation] = []
    for factor, value in _CANONICAL_FACTOR_VALUES:
        consumer = _canonical_consumer(factor, value)
        is_failure = (factor, value) in _SFV_FAILURE_VALUES
        row_id = stable_catalog_row_id(_STATEMENT_KEY, factor, value)
        rows.append(
            SetRoleFactorObligation(
                ordinal=0,
                obligation_id=f"SETROLE-SFV|{row_id}|{consumer}",
                kind="SFV",
                factor_key=factor,
                value=value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=f"{_REFERENCE_PATH}#{row_id}",
            )
        )
    return rows


def _obligation_multiset_sha256(
    rows: tuple[SetRoleFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"set-role-factor-obligations-v1\n")
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
    "set_role": _BRANCH_1,
}

# Dense baseline defaults (all positive T1-T6 factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "grammar_branch": _BRANCH_1,
    "target_action": "set_role",
    "expected_status": "success",
    "session_state": "default_state",
    "scope_shape": "session",
    "value_shape": "valid_value",
    "name_shape": "plain_identifier",
    "payload_shape": "absent",
    "dependency_state": "ready",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "transaction_visibility": "outside_transaction",
    "verification_mode": "catalog_query",
    "cleanup_mode": "rollback",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive expected_status and transaction_visibility from each other.

    SET ROLE's only reachable failure surface is SET ROLE inside a
    transaction block (SQLSTATE 25001).  When ``expected_status=failure``
    or a ``transaction_visibility`` in-transaction value is the primary,
    the other is derived so the baseline assignment is self-consistent and
    the render produces SQL that reaches the intended failure.
    """

    tv = a.get("transaction_visibility", "outside_transaction")
    es = a.get("expected_status", "success")
    if tv in ("inside_committed_transaction", "inside_rolled_back_transaction"):
        a["expected_status"] = "failure"
    elif es == "failure":
        a["transaction_visibility"] = "inside_committed_transaction"
    else:
        a["expected_status"] = "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: SetRoleFactorObligation,
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
        raise SetRoleFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: SetRoleFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise SetRoleFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_set_role_factor_loop_plan(
    repository_root: Path,
) -> SetRoleFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_set_role_factor_loop_obligations(root)
    cases: list[SetRoleFactorCase] = []
    delegated: list[SetRoleFactorObligation] = []
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
            SetRoleFactorCase(
                ordinal=ordinal,
                case_id=f"SETROLE{ordinal:05d}",
                sql_filename=f"SETROLE{ordinal:05d}.sql",
                object_prefix=f"setrole_{ordinal:05d}_",
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
    plan = SetRoleFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 43 or len(plan.delegated) != 0:
        raise SetRoleFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 43
    ):
        raise SetRoleFactorLoopError("local obligation mapping drift")
    if (
        len({row.sql_filename for row in plan.cases}) != 43
    ):
        raise SetRoleFactorLoopError("duplicate SQL filename")
    return plan


def compile_set_role_factor_loop_obligations(
    repository_root: Path,
) -> tuple[SetRoleFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    if not (root / _MATRIX_PATH).is_file():
        raise SetRoleFactorLoopError(
            f"canonical matrix is missing for set_role: {_MATRIX_PATH}"
        )
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations()
    )
    rows = tuple(
        SetRoleFactorObligation(
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
        raise SetRoleFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise SetRoleFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 42}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise SetRoleFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise SetRoleFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 43:
        raise SetRoleFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise SetRoleFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "SetRoleFactorLoopError",
    "SetRoleGrammarAction",
    "SetRoleFactorObligation",
    "SetRoleFactorCase",
    "SetRoleFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_FACTOR_VALUE_COUNT",
    "_CANONICAL_FACTOR_VALUES",
    "compile_set_role_factor_loop_obligations",
    "build_set_role_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
