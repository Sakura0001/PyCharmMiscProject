"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER POLICY.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER POLICY``.  ``alter_policy.yaml`` marks the canonical SFV
obligations as one-to-one from the shipped applicability matrix: exactly
68 rows, one local obligation per row (``AP-SFV|{row_id}|{consumer}``).

The official synopsis spans two branches (``branch_rename`` for
``RENAME TO``, ``branch_modify`` for the ``FOR``/``TO``/``USING``/
``WITH CHECK`` modify forms).  The five ``alter_action`` values
(``rename``, ``modify_using``, ``modify_with_check``, ``modify_roles``,
``modify_combined``) are sampled as SFV factor values (one per matrix
row), not as separate GRM action forms.  The GRM ledger freezes two
branch-representative action skeletons (``rename`` for ``branch_rename``,
``modify_combined`` for ``branch_modify``).  A RISK pair (commit/rollback)
exercises the transactional DDL boundary, mirroring sibling ledgers.

ALTER POLICY is a table-attached RLS DDL: it alters a policy ON a table
(it does not alter the table itself).  The role/privilege sub-axis
(``role_target`` / ``role_name_shape`` / ``privilege_denied`` /
``privilege_level``) reuses the SESSION_USER no-op-transfer +
``_privilege_boundary_fires`` salvage from alter_language/
alter_large_object.  ``rls_not_enabled`` is NOT a failure for ALTER
POLICY (the policy definition can be altered with RLS off), so it is
treated as a success-variant axis; the DB fork calibrates the exact
dispositions.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``ALTER POLICY`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterPolicyFactorLoopError(ValueError):
    """Raised when a frozen ALTER POLICY obligation input drifts."""


@dataclass(frozen=True)
class AlterPolicyFactorObligation:
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
class AlterPolicyFactorCase:
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
class AlterPolicyFactorLoopPlan:
    obligations: tuple[AlterPolicyFactorObligation, ...]
    cases: tuple[AlterPolicyFactorCase, ...]
    delegated: tuple[AlterPolicyFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-alterpolicy.html).
_BRANCH_RENAME = "branch_rename"
_BRANCH_MODIFY = "branch_modify"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterpolicy"

# The two official synopsis branches, each with its representative action
# form.  The GRM ledger freezes one action skeleton per branch; the five
# ``alter_action`` values are sampled separately as SFV factor values.
@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="rename",
        grammar_branch_id=_BRANCH_RENAME,
        source_locator=f"{_DOC_SOURCE}:synopsis-rename",
    ),
    _GrammarAction(
        action_id="modify_combined",
        grammar_branch_id=_BRANCH_MODIFY,
        source_locator=f"{_DOC_SOURCE}:synopsis-modify",
    ),
)

# The modify branch's representative consumer for statement-wide modifiers
# that are not bound to a sub-clause (e.g. expected_status, verification_mode).
_REPRESENTATIVE_ACTION = "modify_combined"

# Canonical factor -> the action where the value is observable.  The
# ``alter_action`` and ``statement_branch`` factors are resolved in
# :func:`_canonical_consumer` (their values ARE the consumer action).
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "using_expression": "modify_using",
    "with_check_expression": "modify_with_check",
    "policy_name_shape": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "role_name_shape": "modify_roles",
    "role_target": "modify_roles",
    "role_existence": "modify_roles",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "privilege_denied": _REPRESENTATIVE_ACTION,
    "rls_enabled": _REPRESENTATIVE_ACTION,
    "rls_not_enabled": _REPRESENTATIVE_ACTION,
    "table_existence": _REPRESENTATIVE_ACTION,
    "policy_existence": _REPRESENTATIVE_ACTION,
    "nonexistent_policy": _REPRESENTATIVE_ACTION,
    "nonexistent_table": _REPRESENTATIVE_ACTION,
    "cannot_alter_command_type": _REPRESENTATIVE_ACTION,
    "cannot_alter_policy_type": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# statement_branch value -> its representative consumer action.
_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    _BRANCH_RENAME: "rename",
    _BRANCH_MODIFY: "modify_combined",
}

# consumer action -> its grammar branch.
_ACTION_TO_BRANCH: dict[str, str] = {
    "rename": _BRANCH_RENAME,
    "modify_combined": _BRANCH_MODIFY,
    "modify_roles": _BRANCH_MODIFY,
    "modify_using": _BRANCH_MODIFY,
    "modify_with_check": _BRANCH_MODIFY,
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterPolicyFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action":
        # The value IS the action; the renderer dispatches on it directly.
        if row.value not in _ACTION_TO_BRANCH:
            raise AlterPolicyFactorLoopError(
                f"unknown alter action: {row.value}"
            )
        return row.value
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterPolicyFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _grammar_branch_for(obligation: AlterPolicyFactorObligation) -> str:
    """The grammar branch the obligation's action renders under."""

    if obligation.factor_key == "statement_branch":
        return obligation.value
    if obligation.factor_key == "target_action":
        # GRM obligation: the action's own branch.
        return _ACTION_TO_BRANCH[obligation.consumer_action_id]
    return _ACTION_TO_BRANCH.get(
        obligation.consumer_action_id, _BRANCH_MODIFY
    )


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


def _compile_grammar_obligations() -> list[AlterPolicyFactorObligation]:
    rows: list[AlterPolicyFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            AlterPolicyFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AP-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 2:
        raise AlterPolicyFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterPolicyFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_policy")
    if len(catalog_rows) != 68:
        raise AlterPolicyFactorLoopError("canonical obligation count drift")
    rows: list[AlterPolicyFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterPolicyFactorObligation(
                ordinal=0,
                obligation_id=f"AP-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterPolicyFactorObligation]:
    return [
        AlterPolicyFactorObligation(
            ordinal=0,
            obligation_id=f"AP-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterpolicy:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterPolicyFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-policy-factor-obligations-v1\n")
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


# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (verified against PG 18.4).  Best-effort attribution; the DB
# doublerun fork calibrates the exact SQLSTATEs.  ``rls_not_enabled`` is NOT
# here: ALTER POLICY alters the policy definition regardless of RLS
# enablement, so rls_not_enabled is a success-variant axis.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("table_existence", "table_not_exists"),
        ("policy_existence", "policy_not_exists"),
        ("role_existence", "role_not_exists"),
        ("nonexistent_policy", "policy_missing"),
        ("nonexistent_table", "table_missing"),
        ("privilege_denied", "non_owner_denied"),
        ("privilege_level", "non_owner"),
        ("cannot_alter_command_type", "cannot_change_for_clause"),
        ("cannot_alter_policy_type", "cannot_change_as_clause"),
        ("new_name_shape", "duplicate_name"),
        ("new_name_shape", "invalid_name"),
        ("policy_name_shape", "nonexistent_name"),
        ("table_name_shape", "nonexistent_table"),
        ("role_name_shape", "nonexistent_role"),
    }
)

# Best-effort PG 18.4 SQLSTATE attribution for each reachable
# expected-failure value.  The DB doublerun fork calibrates these via a
# two-run comparison; the frozen counts and sha256s in the companion tests
# are the spec.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "policy_does_not_exist",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "policy_does_not_exist",
    ),
    ("table_existence", "table_not_exists"): (
        "42P01",
        "undefined_table",
    ),
    ("policy_existence", "policy_not_exists"): (
        "42704",
        "policy_does_not_exist",
    ),
    ("role_existence", "role_not_exists"): (
        "42704",
        "role_does_not_exist",
    ),
    ("nonexistent_policy", "policy_missing"): (
        "42704",
        "policy_does_not_exist",
    ),
    ("nonexistent_table", "table_missing"): (
        "42P01",
        "undefined_table",
    ),
    ("privilege_denied", "non_owner_denied"): (
        "42501",
        "must_be_owner",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "must_be_owner",
    ),
    ("cannot_alter_command_type", "cannot_change_for_clause"): (
        "42601",
        "syntax_error",
    ),
    ("cannot_alter_policy_type", "cannot_change_as_clause"): (
        "42601",
        "syntax_error",
    ),
    ("new_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object",
    ),
    ("new_name_shape", "invalid_name"): (
        "42601",
        "syntax_error",
    ),
    ("policy_name_shape", "nonexistent_name"): (
        "42704",
        "policy_does_not_exist",
    ),
    ("table_name_shape", "nonexistent_table"): (
        "42P01",
        "undefined_table",
    ),
    ("role_name_shape", "nonexistent_role"): (
        "42704",
        "role_does_not_exist",
    ),
}


def _expected_failure_details(
    obligation: AlterPolicyFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterPolicyFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: AlterPolicyFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _grammar_branch_for(obligation)
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "statement_branch": branch,
        "alter_action": _REPRESENTATIVE_ACTION,
        "object_state": "exists",
        "expected_status": "success",
        "role_target": "single_role",
        "using_expression": "omitted_keep_original",
        "with_check_expression": "omitted_keep_original",
        "policy_name_shape": "simple_id",
        "table_name_shape": "simple_id",
        "new_name_shape": "simple_id",
        "role_name_shape": "simple_id",
        "privilege_level": "superuser",
        "privilege_denied": "owner_execution",
        "rls_enabled": "rls_enabled",
        "rls_not_enabled": "rls_enabled",
        "table_existence": "table_exists",
        "policy_existence": "policy_exists",
        "role_existence": "role_exists",
        "nonexistent_policy": "policy_exists",
        "nonexistent_table": "table_exists",
        "cannot_alter_command_type": "only_rename_and_modify_allowed",
        "cannot_alter_policy_type": "only_rename_and_modify_allowed",
        "verification_mode": "catalog_query_pg_policy",
        "cleanup_mode": "drop_policy",
    }
    # The primary value overrides exactly one key (the obligation's factor).
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    # For an alter_action primary, keep statement_branch consistent.
    if obligation.factor_key == "alter_action":
        assignments["statement_branch"] = _ACTION_TO_BRANCH[obligation.value]
        assignments["grammar_branch"] = _ACTION_TO_BRANCH[obligation.value]
    # expected_status=failure is the "policy does not exist" sentinel
    # (42704): the fixture intentionally creates no policy so the alter
    # surfaces the not-found error.  Model this as object_state=not_exists so
    # the renderer's fixture decision (which reads object_state, not the
    # derived expected_status) stays self-consistent for both baseline and
    # extension failure cases.
    if (
        obligation.factor_key == "expected_status"
        and obligation.value == "failure"
    ):
        assignments["object_state"] = "not_exists"
    if len(assignments) != len(set(assignments)):
        raise AlterPolicyFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_policy_factor_loop_plan(
    repository_root: Path,
) -> AlterPolicyFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_policy_factor_loop_obligations(root)
    cases: list[AlterPolicyFactorCase] = []
    delegated: list[AlterPolicyFactorObligation] = []
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
            AlterPolicyFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERPOLICY{ordinal:05d}",
                sql_filename=f"ALTERPOLICY{ordinal:05d}.sql",
                object_prefix=f"alterpolicy_{ordinal:05d}_",
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
    plan = AlterPolicyFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 72 or len(plan.delegated) != 0:
        raise AlterPolicyFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 72:
        raise AlterPolicyFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 72:
        raise AlterPolicyFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_policy_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterPolicyFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterPolicyFactorObligation(
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
    if len(rows) != 72:
        raise AlterPolicyFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterPolicyFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 68, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterPolicyFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterPolicyFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 72:
        raise AlterPolicyFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterPolicyFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterPolicyFactorLoopError",
    "AlterPolicyFactorObligation",
    "AlterPolicyFactorCase",
    "AlterPolicyFactorLoopPlan",
    "compile_alter_policy_factor_loop_obligations",
    "build_alter_policy_factor_loop_plan",
    "_obligation_multiset_sha256",
]
