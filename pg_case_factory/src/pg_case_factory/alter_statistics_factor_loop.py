"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER STATISTICS.

This module compiles the marginal ``GRM``/``SFV``/``RISK`` obligation ledger
for ``ALTER STATISTICS`` (extended statistics objects).  ALTER STATISTICS has
exactly four grammar branches (``SET STATISTICS``, ``RENAME TO``,
``OWNER TO`` and ``SET SCHEMA``).  The statement target is a
``pg_catalog.pg_statistic_ext`` row (an extended statistics object), not a
``pg_class`` relation, so there is no ``INV`` block.  Each local obligation
becomes exactly one regress program; there are no delegated handoffs because
every reachable negative boundary is a real ``ALTER STATISTICS`` error that
belongs to this statement.

The grammar catalog (actions + axes) is inlined here because ALTER
STATISTICS, like ALTER SCHEMA, has fixed synopsis forms with no optional
keywords, alternatives, or list-boundary modifiers, so the axis ledger is
empty and the four target actions are the only GRM obligations.

Privilege is table-ownership-based: ``RENAME``/``SET SCHEMA``/``SET
STATISTICS`` require owning the underlying table (plus ``CREATE`` on the
target schema for ``SET SCHEMA``), while ``OWNER TO`` additionally requires
``CREATEROLE`` privilege (or superuser).  A non-table-owner that lacks the
required privilege is rejected with ``42501``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterStatisticsFactorLoopError(ValueError):
    """Raised when a frozen ALTER STATISTICS obligation input drifts."""


@dataclass(frozen=True)
class AlterStatisticsGrammarAction:
    """One official target action form of the ALTER STATISTICS synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-alterstatistics.html).
_BRANCH_SET_STATISTICS = "branch_set_statistics"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner_to"
_BRANCH_SET_SCHEMA = "branch_set_schema"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterstatistics"

# Ordered (branch, action) pairs so the factor-loop can resolve a canonical
# statement_branch value to its consumer action id.
STATEMENT_BRANCH_ACTIONS = (
    (_BRANCH_SET_STATISTICS, "set_statistics"),
    (_BRANCH_RENAME, "rename"),
    (_BRANCH_OWNER, "owner_to"),
    (_BRANCH_SET_SCHEMA, "set_schema"),
)


def load_alter_statistics_grammar_actions() -> (
    tuple[AlterStatisticsGrammarAction, ...]
):
    """Freeze every ALTER STATISTICS synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "set_statistics",
            _BRANCH_SET_STATISTICS,
            "ALTER STATISTICS name SET STATISTICS { integer | DEFAULT }",
            "synopsis-set-statistics",
        ),
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER STATISTICS name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "owner_to",
            _BRANCH_OWNER,
            (
                "ALTER STATISTICS name OWNER TO "
                "{ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
            ),
            "synopsis-owner-to",
        ),
        (
            "set_schema",
            _BRANCH_SET_SCHEMA,
            "ALTER STATISTICS name SET SCHEMA new_schema",
            "synopsis-set-schema",
        ),
    )
    actions = [
        AlterStatisticsGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 4:
        raise AlterStatisticsFactorLoopError(
            "alter statistics action count drift"
        )
    return tuple(actions)


@dataclass(frozen=True)
class AlterStatisticsFactorObligation:
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
class AlterStatisticsFactorCase:
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
class AlterStatisticsFactorLoopPlan:
    obligations: tuple[AlterStatisticsFactorObligation, ...]
    cases: tuple[AlterStatisticsFactorCase, ...]
    delegated: tuple[AlterStatisticsFactorObligation, ...]
    obligation_multiset_sha256: str


# A representative branch used as the baseline consumer for canonical
# factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "set_statistics"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_SET_STATISTICS: "set_statistics",
    _BRANCH_RENAME: "rename",
    _BRANCH_OWNER: "owner_to",
    _BRANCH_SET_SCHEMA: "set_schema",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "statistics_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "owner_to_shape": "owner_to",
    "rename_behavior": "rename",
    "set_schema_behavior": "set_schema",
    "statistics_target_value": "set_statistics",
    "statistics_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "new_schema_shape": "set_schema",
    "new_owner_shape": "owner_to",
    "target_value_shape": "set_statistics",
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "table_dependency": _REPRESENTATIVE_ACTION,
    "nonexistent_statistics": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "nonexistent_schema": "set_schema",
    "nonexistent_owner": "owner_to",
    "target_out_of_range": "set_statistics",
    "rename_conflict": "rename",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        # Cluster A: statistics object does not exist.
        ("expected_status", "failure"),
        ("statistics_state", "non_existent"),
        ("statistics_name_shape", "non_existent_name"),
        ("nonexistent_statistics", "statistics_does_not_exist"),
        # Cluster B: rename conflict (new name already exists).
        ("rename_behavior", "rename_to_existing_name_conflict"),
        ("new_name_shape", "existing_name_conflict"),
        ("rename_conflict", "new_name_already_exists"),
        # Cluster C: SET SCHEMA to a non-existent schema.
        ("set_schema_behavior", "nonexistent_schema"),
        ("new_schema_shape", "nonexistent_schema"),
        ("nonexistent_schema", "schema_does_not_exist"),
        # Cluster D: OWNER TO a non-existent role.
        ("new_owner_shape", "nonexistent_role"),
        ("nonexistent_owner", "owner_role_does_not_exist"),
        # Cluster E: insufficient privilege.
        ("executor_privilege", "non_owner_no_privilege"),
        ("privilege_insufficient", "non_table_owner_altering_statistics"),
        # Cluster F: statistics target out of range.
        ("statistics_target_value", "out_of_range"),
        ("target_value_shape", "very_large_value"),
        ("target_out_of_range", "negative_other_than_minus_one"),
    }
)

# No SUCCESS-escape behavior values (unlike alter_schema's SESSION_USER).
# Every keyword owner target (CURRENT_ROLE / CURRENT_USER / SESSION_USER) is
# a valid SUCCESS path but needs no special escape modelling because the
# membership wall does not apply to statistics ownership transfer the way it
# does to schema ownership.
_EXPECTED_BEHAVIOR_VALUES: frozenset[tuple[str, str]] = frozenset()

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    # Cluster A: 42704 undefined_object.
    ("expected_status", "failure"): (
        "42704",
        "statistics_does_not_exist_provisional",
    ),
    ("statistics_state", "non_existent"): (
        "42704",
        "statistics_does_not_exist_provisional",
    ),
    ("statistics_name_shape", "non_existent_name"): (
        "42704",
        "statistics_does_not_exist_provisional",
    ),
    ("nonexistent_statistics", "statistics_does_not_exist"): (
        "42704",
        "statistics_does_not_exist_provisional",
    ),
    # Cluster B: 42710 duplicate_object.
    ("rename_behavior", "rename_to_existing_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("new_name_shape", "existing_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("rename_conflict", "new_name_already_exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    # Cluster C: 3F000 invalid_schema.
    ("set_schema_behavior", "nonexistent_schema"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("new_schema_shape", "nonexistent_schema"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("nonexistent_schema", "schema_does_not_exist"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    # Cluster D: 42704 undefined_object (role does not exist).
    ("new_owner_shape", "nonexistent_role"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("nonexistent_owner", "owner_role_does_not_exist"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    # Cluster E: 42501 insufficient_privilege.
    ("executor_privilege", "non_owner_no_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_table_owner_altering_statistics"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    # Cluster F: 22023 invalid_parameter_value.
    ("statistics_target_value", "out_of_range"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("target_value_shape", "very_large_value"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("target_out_of_range", "negative_other_than_minus_one"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterStatisticsFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterStatisticsFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterStatisticsFactorObligation]:
    rows: list[AlterStatisticsFactorObligation] = []
    for action in load_alter_statistics_grammar_actions():
        rows.append(
            AlterStatisticsFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ASTAT-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 4:
        raise AlterStatisticsFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterStatisticsFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_statistics")
    if len(catalog_rows) != 50:
        raise AlterStatisticsFactorLoopError("canonical obligation count drift")
    rows: list[AlterStatisticsFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterStatisticsFactorObligation(
                ordinal=0,
                obligation_id=f"ASTAT-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterStatisticsFactorObligation]:
    return [
        AlterStatisticsFactorObligation(
            ordinal=0,
            obligation_id=f"ASTAT-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterstatistics:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterStatisticsFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-statistics-factor-obligations-v1\n"
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


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "set_statistics": _BRANCH_SET_STATISTICS,
    "rename": _BRANCH_RENAME,
    "owner_to": _BRANCH_OWNER,
    "set_schema": _BRANCH_SET_SCHEMA,
}

# Dense baseline defaults (all positive T1-T6 factor values).  The T5
# single-value-negative factors are NOT baselined here: every declared value
# is a failure mode, so they are set only when they are the primary (or
# derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_SET_STATISTICS,
    "grammar_branch": _BRANCH_SET_STATISTICS,
    "target_action": "set_statistics",
    "statistics_state": "exists",
    "expected_status": "success",
    "owner_to_shape": "explicit_role_name",
    "rename_behavior": "rename_to_new_name",
    "set_schema_behavior": "existing_schema",
    "statistics_target_value": "zero",
    "statistics_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "new_schema_shape": "existing_schema",
    "new_owner_shape": "existing_role",
    "target_value_shape": "integer_value",
    "executor_privilege": "superuser",
    "table_dependency": "underlying_table_exists",
    "verification_mode": "pg_statistic_ext_catalog",
    "cleanup_mode": "drop_statistics",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T1<->T3<->T5 overlapping factor values in-place.

    The T5 boundary factors describe the same scenario as their T1/T3
    counterparts.  When the primary factor is a T1/T3 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1/T3 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that actually reaches the
    intended boundary.
    """

    ss = a.get("statistics_state", "exists")
    sns = a.get("statistics_name_shape", "simple_name")
    nes = a.get("nonexistent_statistics", "")
    es = a.get("expected_status", "success")
    rb = a.get("rename_behavior", "rename_to_new_name")
    nns = a.get("new_name_shape", "simple_name")
    rnc = a.get("rename_conflict", "")
    ssb = a.get("set_schema_behavior", "existing_schema")
    nss = a.get("new_schema_shape", "existing_schema")
    neschema = a.get("nonexistent_schema", "")
    now = a.get("new_owner_shape", "existing_role")
    neo = a.get("nonexistent_owner", "")
    ep = a.get("executor_privilege", "superuser")
    pi = a.get("privilege_insufficient", "")
    stv = a.get("statistics_target_value", "zero")
    tvs = a.get("target_value_shape", "integer_value")
    tor = a.get("target_out_of_range", "")

    # Cluster A: statistics does not exist.
    if (
        ss == "non_existent"
        or sns == "non_existent_name"
        or nes == "statistics_does_not_exist"
        or es == "failure"
    ):
        a["statistics_state"] = "non_existent"
        a["statistics_name_shape"] = "non_existent_name"
        a["nonexistent_statistics"] = "statistics_does_not_exist"

    # Cluster B: rename conflict.
    if (
        rb == "rename_to_existing_name_conflict"
        or nns == "existing_name_conflict"
        or rnc == "new_name_already_exists"
    ):
        a["rename_behavior"] = "rename_to_existing_name_conflict"
        a["new_name_shape"] = "existing_name_conflict"
        a["rename_conflict"] = "new_name_already_exists"

    # Cluster C: SET SCHEMA to non-existent schema.
    if (
        ssb == "nonexistent_schema"
        or nss == "nonexistent_schema"
        or neschema == "schema_does_not_exist"
    ):
        a["set_schema_behavior"] = "nonexistent_schema"
        a["new_schema_shape"] = "nonexistent_schema"
        a["nonexistent_schema"] = "schema_does_not_exist"

    # Cluster D: OWNER TO non-existent role.
    if (
        now == "nonexistent_role"
        or neo == "owner_role_does_not_exist"
    ):
        a["new_owner_shape"] = "nonexistent_role"
        a["nonexistent_owner"] = "owner_role_does_not_exist"

    # Cluster E: insufficient privilege.
    if (
        ep == "non_owner_no_privilege"
        or pi == "non_table_owner_altering_statistics"
    ):
        a["executor_privilege"] = "non_owner_no_privilege"
        a["privilege_insufficient"] = "non_table_owner_altering_statistics"

    # Cluster F: statistics target out of range.
    if (
        stv == "out_of_range"
        or tvs == "very_large_value"
        or tor == "negative_other_than_minus_one"
    ):
        a["statistics_target_value"] = "out_of_range"
        a["target_value_shape"] = "very_large_value"
        a["target_out_of_range"] = "negative_other_than_minus_one"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterStatisticsFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments["target_action"] = obligation.consumer_action_id
    key = _renderer_factor_key(obligation.factor_key)
    assignments[key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = "failure" if failures > 0 else "success"
    if len(assignments) != len(set(assignments)):
        raise AlterStatisticsFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterStatisticsFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterStatisticsFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_statistics_factor_loop_plan(
    repository_root: Path,
) -> AlterStatisticsFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_statistics_factor_loop_obligations(root)
    cases: list[AlterStatisticsFactorCase] = []
    delegated: list[AlterStatisticsFactorObligation] = []
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
            AlterStatisticsFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERSTATISTICS{ordinal:05d}",
                sql_filename=f"ALTERSTATISTICS{ordinal:05d}.sql",
                object_prefix=f"alterstatistics_{ordinal:05d}_",
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
    plan = AlterStatisticsFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 56 or len(plan.delegated) != 0:
        raise AlterStatisticsFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 56:
        raise AlterStatisticsFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 56:
        raise AlterStatisticsFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_statistics_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterStatisticsFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterStatisticsFactorObligation(
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
    if len(rows) != 56:
        raise AlterStatisticsFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterStatisticsFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 4, "SFV": 50, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterStatisticsFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterStatisticsFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 56:
        raise AlterStatisticsFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterStatisticsFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterStatisticsFactorLoopError",
    "AlterStatisticsGrammarAction",
    "AlterStatisticsFactorObligation",
    "AlterStatisticsFactorCase",
    "AlterStatisticsFactorLoopPlan",
    "STATEMENT_BRANCH_ACTIONS",
    "_EXPECTED_BEHAVIOR_VALUES",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "load_alter_statistics_grammar_actions",
    "compile_alter_statistics_factor_loop_obligations",
    "build_alter_statistics_factor_loop_plan",
    "_obligation_multiset_sha256",
]
