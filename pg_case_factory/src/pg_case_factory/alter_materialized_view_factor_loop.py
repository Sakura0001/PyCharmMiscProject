"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER MATERIALIZED VIEW.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER MATERIALIZED VIEW``.  ``alter_materialized_view.yaml`` marks
relation/table/column-type coverage ``representative`` (the column-type
catalog is sampled, not an exhaustive ``INV`` block like
``ALTER FOREIGN TABLE``), so the canonical SFV obligations are derived
one-to-one from the shipped applicability matrix: exactly 53 rows, one
local obligation per row.

The official synopsis spans six branches (``branch_action``,
``branch_depends_extension``, ``branch_rename_column``, ``branch_rename``,
``branch_set_schema``, ``branch_set_tablespace_all``); the grammar ledger
freezes those six action skeletons as six GRM obligations.  The twelve
``alter_action_type`` values are sampled as SFV factor values (one per
matrix row), not as separate GRM action forms, because the matrix itself
models them as the ``alter_action_type`` factor.  A RISK pair
(commit/rollback) exercises the transactional DDL boundary, mirroring the
sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``ALTER MATERIALIZED VIEW`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterMaterializedViewFactorLoopError(ValueError):
    """Raised when a frozen ALTER MATERIALIZED VIEW obligation input drifts."""


@dataclass(frozen=True)
class AlterMaterializedViewFactorObligation:
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
class AlterMaterializedViewFactorCase:
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
class AlterMaterializedViewFactorLoopPlan:
    obligations: tuple[AlterMaterializedViewFactorObligation, ...]
    cases: tuple[AlterMaterializedViewFactorCase, ...]
    delegated: tuple[AlterMaterializedViewFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altermaterializedview.html).
_BRANCH_ACTION = "branch_action"
_BRANCH_DEPENDS_EXTENSION = "branch_depends_extension"
_BRANCH_RENAME_COLUMN = "branch_rename_column"
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_SET_TABLESPACE_ALL = "branch_set_tablespace_all"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altermaterializedview"

# The six official synopsis branches, each with its representative action
# form.  The GRM ledger freezes one action skeleton per branch; the twelve
# ``alter_action_type`` values are sampled separately as SFV factor values.
@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="set_statistics",
        grammar_branch_id=_BRANCH_ACTION,
        source_locator=f"{_DOC_SOURCE}:synopsis-action",
    ),
    _GrammarAction(
        action_id="depends_on_extension",
        grammar_branch_id=_BRANCH_DEPENDS_EXTENSION,
        source_locator=f"{_DOC_SOURCE}:synopsis-depends-extension",
    ),
    _GrammarAction(
        action_id="rename_column",
        grammar_branch_id=_BRANCH_RENAME_COLUMN,
        source_locator=f"{_DOC_SOURCE}:synopsis-rename-column",
    ),
    _GrammarAction(
        action_id="rename",
        grammar_branch_id=_BRANCH_RENAME,
        source_locator=f"{_DOC_SOURCE}:synopsis-rename",
    ),
    _GrammarAction(
        action_id="set_schema",
        grammar_branch_id=_BRANCH_SET_SCHEMA,
        source_locator=f"{_DOC_SOURCE}:synopsis-set-schema",
    ),
    _GrammarAction(
        action_id="set_tablespace",
        grammar_branch_id=_BRANCH_SET_TABLESPACE_ALL,
        source_locator=f"{_DOC_SOURCE}:synopsis-set-tablespace",
    ),
)

# The action branch's representative consumer for statement-wide modifiers
# that are not bound to a sub-clause (e.g. expected_status, verification_mode).
_REPRESENTATIVE_ACTION = "set_statistics"

# Canonical factor -> the action where the value is observable.  The
# ``alter_action_type`` and ``statement_branch`` factors are resolved in
# :func:`_canonical_consumer` (their values ARE the consumer action).
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "target_object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "new_owner_shape": "owner_to",
    "privilege_context": _REPRESENTATIVE_ACTION,
    "ownership_boundary": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "column_name_shape": _REPRESENTATIVE_ACTION,
    "dependency_state": "depends_on_extension",
    "extension_state": "depends_on_extension",
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# statement_branch value -> its representative consumer action.
_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    _BRANCH_ACTION: "set_statistics",
    _BRANCH_DEPENDS_EXTENSION: "depends_on_extension",
    _BRANCH_RENAME_COLUMN: "rename_column",
    _BRANCH_RENAME: "rename",
    _BRANCH_SET_SCHEMA: "set_schema",
    _BRANCH_SET_TABLESPACE_ALL: "set_tablespace",
}

# consumer action -> its grammar branch (for the action-branch actions and
# the four non-action branches).  ``set_tablespace`` lives under
# ``branch_action`` as an ``alter_action_type`` value (per the matrix), so
# its grammar branch is ``branch_action`` here; the
# ``branch_set_tablespace_all`` statement-branch SFV overrides this via the
# statement_branch primary path.
_ACTION_TO_BRANCH: dict[str, str] = {
    "set_statistics": _BRANCH_ACTION,
    "set_attribute_option": _BRANCH_ACTION,
    "reset_attribute_option": _BRANCH_ACTION,
    "set_storage": _BRANCH_ACTION,
    "set_compression": _BRANCH_ACTION,
    "cluster_on": _BRANCH_ACTION,
    "set_without_cluster": _BRANCH_ACTION,
    "set_access_method": _BRANCH_ACTION,
    "set_tablespace": _BRANCH_ACTION,
    "set_storage_parameter": _BRANCH_ACTION,
    "reset_storage_parameter": _BRANCH_ACTION,
    "owner_to": _BRANCH_ACTION,
    "depends_on_extension": _BRANCH_DEPENDS_EXTENSION,
    "rename_column": _BRANCH_RENAME_COLUMN,
    "rename": _BRANCH_RENAME,
    "set_schema": _BRANCH_SET_SCHEMA,
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterMaterializedViewFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action_type":
        # The value IS the action; the renderer dispatches on it directly.
        if row.value not in _ACTION_TO_BRANCH:
            raise AlterMaterializedViewFactorLoopError(
                f"unknown alter action type: {row.value}"
            )
        return row.value
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterMaterializedViewFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _grammar_branch_for(obligation: AlterMaterializedViewFactorObligation) -> str:
    """The grammar branch the obligation's action renders under.

    A ``statement_branch`` primary resolves to its own value; every other
    obligation resolves via the consumer action's branch map.
    """

    if obligation.factor_key == "statement_branch":
        return obligation.value
    if obligation.factor_key == "target_action":
        # GRM obligation: the action's own branch.
        return _ACTION_TO_BRANCH[obligation.consumer_action_id]
    return _ACTION_TO_BRANCH.get(
        obligation.consumer_action_id, _BRANCH_ACTION
    )


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


def _compile_grammar_obligations() -> list[AlterMaterializedViewFactorObligation]:
    rows: list[AlterMaterializedViewFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            AlterMaterializedViewFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AMV-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 6:
        raise AlterMaterializedViewFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterMaterializedViewFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_materialized_view")
    if len(catalog_rows) != 53:
        raise AlterMaterializedViewFactorLoopError("canonical obligation count drift")
    rows: list[AlterMaterializedViewFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterMaterializedViewFactorObligation(
                ordinal=0,
                obligation_id=f"AMV-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterMaterializedViewFactorObligation]:
    return [
        AlterMaterializedViewFactorObligation(
            ordinal=0,
            obligation_id=f"AMV-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-altermaterializedview:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterMaterializedViewFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-materialized-view-factor-obligations-v1\n"
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
# doublerun fork calibrates the exact SQLSTATEs.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "missing"),
        ("target_object_state", "wrong_object_type"),
        ("new_owner_shape", "missing_role"),
        ("privilege_context", "insufficient_privilege"),
        ("ownership_boundary", "non_owner"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("dependency_state", "missing_dependency"),
        ("extension_state", "extension_missing"),
    }
)

# Best-effort PG 18.4 SQLSTATE attribution for each reachable expected-failure
# value.  The DB doublerun fork calibrates these via a two-run comparison; the
# frozen counts and sha256s in the companion tests are the spec.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "materialized_view_does_not_exist",
    ),
    ("target_object_state", "missing"): (
        "42P01",
        "materialized_view_does_not_exist",
    ),
    ("target_object_state", "wrong_object_type"): (
        "42809",
        "wrong_object_type",
    ),
    ("new_owner_shape", "missing_role"): ("42704", "role_does_not_exist"),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "must_be_owner_of_materialized_view",
    ),
    ("ownership_boundary", "non_owner"): (
        "42501",
        "must_be_owner_of_materialized_view",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "invalid_materialized_view_alter_combination",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "wrong_object_type",
    ),
    ("dependency_state", "missing_dependency"): (
        "42704",
        "extension_does_not_exist",
    ),
    ("extension_state", "extension_missing"): (
        "42704",
        "extension_does_not_exist",
    ),
}


def _expected_failure_details(
    obligation: AlterMaterializedViewFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterMaterializedViewFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: AlterMaterializedViewFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _grammar_branch_for(obligation)
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "statement_branch": branch,
        "alter_action_type": _REPRESENTATIVE_ACTION,
        "target_object_state": "exists",
        "expected_status": "success",
        "if_exists_clause": "absent",
        "new_owner_shape": "plain_role",
        "privilege_context": "owner",
        "name_shape": "plain_identifier",
        "column_name_shape": "plain_identifier",
        "dependency_state": "ready",
        "extension_state": "extension_exists",
        "invalid_combination": "none",
        "ownership_boundary": "owner",
        "verification_mode": "catalog_query",
        "cleanup_mode": "drop_objects",
    }
    # The primary value overrides exactly one key (the obligation's factor).
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    # For an alter_action_type primary, keep statement_branch at branch_action
    # (all twelve action types live under branch_action per the matrix).
    if obligation.factor_key == "alter_action_type":
        assignments["statement_branch"] = _BRANCH_ACTION
        assignments["grammar_branch"] = _BRANCH_ACTION
    # expected_status=failure is the "materialized view does not exist"
    # sentinel (42P01): the fixture intentionally creates no mview so the
    # alter surfaces the not-found error.  Model this as
    # target_object_state=missing so the renderer's fixture decision (which
    # reads target_object_state, not the derived expected_status) stays
    # self-consistent for both baseline and extension failure cases.
    if (
        obligation.factor_key == "expected_status"
        and obligation.value == "failure"
    ):
        assignments["target_object_state"] = "missing"
    if len(assignments) != len(set(assignments)):
        raise AlterMaterializedViewFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_materialized_view_factor_loop_plan(
    repository_root: Path,
) -> AlterMaterializedViewFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_materialized_view_factor_loop_obligations(root)
    cases: list[AlterMaterializedViewFactorCase] = []
    delegated: list[AlterMaterializedViewFactorObligation] = []
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
            AlterMaterializedViewFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERMATERIALIZEDVIEW{ordinal:05d}",
                sql_filename=f"ALTERMATERIALIZEDVIEW{ordinal:05d}.sql",
                object_prefix=f"altermaterializedview_{ordinal:05d}_",
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
    plan = AlterMaterializedViewFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 61 or len(plan.delegated) != 0:
        raise AlterMaterializedViewFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 61:
        raise AlterMaterializedViewFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 61:
        raise AlterMaterializedViewFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_materialized_view_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterMaterializedViewFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterMaterializedViewFactorObligation(
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
    if len(rows) != 61:
        raise AlterMaterializedViewFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterMaterializedViewFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 6, "SFV": 53, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterMaterializedViewFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterMaterializedViewFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 61:
        raise AlterMaterializedViewFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterMaterializedViewFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterMaterializedViewFactorLoopError",
    "AlterMaterializedViewFactorObligation",
    "AlterMaterializedViewFactorCase",
    "AlterMaterializedViewFactorLoopPlan",
    "compile_alter_materialized_view_factor_loop_obligations",
    "build_alter_materialized_view_factor_loop_plan",
    "_obligation_multiset_sha256",
]
