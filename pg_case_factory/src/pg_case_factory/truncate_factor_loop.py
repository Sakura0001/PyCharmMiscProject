"""Factor-value-loop obligation ledger for PostgreSQL 18.4 TRUNCATE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``TRUNCATE``.  TRUNCATE is a PostgreSQL DDL/DML table-truncation
statement with a single official synopsis branch::

    TRUNCATE [ TABLE ] [ ONLY ] name [, ...]
        [ RESTART IDENTITY | CONTINUE IDENTITY ]
        [ CASCADE | RESTRICT ]

It acts on a ``pg_class`` relation of kind ``r`` (a base table), so
``object_state`` / ``table_name_shape`` describe the target relation,
and the failure state (exists / missing) refers to the truncated table.

The 17 canonical factors and their values are frozen in the shipped
combination matrix ``truncate.yaml`` (the source of truth);
``factor_value_count`` (the sum of ``len(values)`` across all 17
factors) equals 52.  The ``GRM`` target action is synthesised from
the official synopsis branch and is NOT counted in
``factor_value_count``.  All 52 factor-value pairs are read from the
shipped applicability catalog and become ``SFV`` obligations.
Hence ``GRM`` 1 + ``SFV`` 52 = 53 local obligations, each
materialised as exactly one regress program.

Each local obligation becomes exactly one regress program.  Because
TRUNCATE is a transactional destructive statement and the inventory
declares no ``transaction_outcome`` factor, there are no ``RISK``
obligations.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json

from .applicability import load_shipped_applicability_universe


class TruncateFactorLoopError(ValueError):
    """Raised when a frozen TRUNCATE obligation input drifts."""


@dataclass(frozen=True)
class TruncateGrammarAction:
    """One official target action form of the TRUNCATE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class TruncateFactorObligation:
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
class TruncateFactorCase:
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
class TruncateFactorLoopPlan:
    obligations: tuple[TruncateFactorObligation, ...]
    cases: tuple[TruncateFactorCase, ...]
    delegated: tuple[TruncateFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-truncate.html).
_BRANCH_1 = "truncate_table"

_DOC_SOURCE = "postgresql-18.4-doc:sql-truncate"
_STATEMENT_REF = "references/statements/ddl/table/truncate.md"

# The single consumer action for all TRUNCATE factors.  Since TRUNCATE
# has only one synopsis, every factor's consumer is "truncate".
_REPRESENTATIVE_ACTION = "truncate"

_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "identity_option": _REPRESENTATIVE_ACTION,
    "only_clause": _REPRESENTATIVE_ACTION,
    "multi_table": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "fk_dependency": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "fk_references_without_cascade": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "non_existent_table": _REPRESENTATIVE_ACTION,
    "partitioned_table_behavior": _REPRESENTATIVE_ACTION,
    "temporary_table_truncation": _REPRESENTATIVE_ACTION,
    "cleanup": _REPRESENTATIVE_ACTION,
    "verification": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target
# check and are rejected (provisional sqlstates -- DB phase verifies on
# PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "table_does_not_exist"),
        ("table_name_shape", "non_existent"),
        ("non_existent_table", "truncate_non_existent_table"),
        ("privilege_level", "insufficient_privilege"),
        ("insufficient_privilege", "no_truncate_privilege"),
        ("insufficient_privilege", "non_owner_truncate"),
        ("fk_references_without_cascade", "has_fk_ref_no_cascade"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure
# value.  TRUNCATE targets a ``pg_class`` relation, so a missing target
# yields ``42P01`` (undefined_table) rather than a routine sqlstate.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "missing_target_relation_provisional",
    ),
    ("object_state", "table_does_not_exist"): (
        "42P01",
        "missing_target_relation_provisional",
    ),
    ("table_name_shape", "non_existent"): (
        "42P01",
        "missing_target_relation_provisional",
    ),
    ("non_existent_table", "truncate_non_existent_table"): (
        "42P01",
        "missing_target_relation_provisional",
    ),
    ("privilege_level", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "no_truncate_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "non_owner_truncate"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("fk_references_without_cascade", "has_fk_ref_no_cascade"): (
        "23503",
        "foreign_key_violation_provisional",
    ),
}

# Canonical factor -> (tier, values) hardcoded verbatim from
# truncate.yaml ``factor_contract.factors``.  The sum of len(values)
# is exactly 52 (the frozen factor_value_count).
_CANONICAL_FACTORS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "statement_branch",
        "T1",
        (
            "truncate_table",
            "truncate_table_continue_identity",
            "truncate_table_only",
            "truncate_table_restart_identity",
        ),
    ),
    ("expected_status", "T1", ("failure", "success")),
    (
        "object_state",
        "T1",
        (
            "empty_table",
            "non_empty_table",
            "table_does_not_exist",
            "table_exists",
        ),
    ),
    ("cascade_restrict", "T2", ("cascade", "none", "restrict")),
    (
        "identity_option",
        "T2",
        ("continue_identity", "none", "restart_identity"),
    ),
    ("only_clause", "T2", ("only", "without_only")),
    ("multi_table", "T3", ("multiple", "single")),
    (
        "table_name_shape",
        "T3",
        ("non_existent", "quoted", "schema_qualified", "simple"),
    ),
    (
        "fk_dependency",
        "T4",
        ("no_fk_references", "referenced_by_other_tables"),
    ),
    (
        "privilege_level",
        "T4",
        (
            "insufficient_privilege",
            "owner",
            "superuser",
            "truncate_privilege",
        ),
    ),
    (
        "fk_references_without_cascade",
        "T5",
        ("has_fk_ref_no_cascade", "none"),
    ),
    (
        "insufficient_privilege",
        "T5",
        ("no_truncate_privilege", "non_owner_truncate", "none"),
    ),
    ("non_existent_table", "T5", ("none", "truncate_non_existent_table")),
    (
        "partitioned_table_behavior",
        "T5",
        (
            "none",
            "partitioned_table_only",
            "partitioned_table_with_descendants",
            "single_partition",
        ),
    ),
    (
        "temporary_table_truncation",
        "T5",
        ("none", "temp_table_with_sequences", "temporary_table"),
    ),
    (
        "cleanup",
        "T6",
        (
            "drop_objects",
            "reinsert_data",
            "restart_identity_resets_sequences",
            "rollback",
        ),
    ),
    (
        "verification",
        "T6",
        (
            "error_assertion",
            "pg_class_relpages",
            "select_count_zero",
            "sequence_reset_check",
        ),
    ),
)

# statement_branch -> (only_clause, identity_option) correlation.
# The four statement_branch values encode the combined ONLY/IDENTITY
# option state; only_clause and identity_option are derived from it.
_BRANCH_OPTIONS: dict[str, tuple[str, str]] = {
    "truncate_table": ("without_only", "none"),
    "truncate_table_continue_identity": (
        "without_only",
        "continue_identity",
    ),
    "truncate_table_only": ("only", "none"),
    "truncate_table_restart_identity": (
        "without_only",
        "restart_identity",
    ),
}
_OPTIONS_BRANCH: dict[tuple[str, str], str] = {
    v: k for k, v in _BRANCH_OPTIONS.items()
}


def _factor_value_count() -> int:
    return sum(len(values) for _, _, values in _CANONICAL_FACTORS)


def _load_grammar_actions() -> tuple[TruncateGrammarAction, ...]:
    """Freeze every TRUNCATE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "truncate",
            _BRANCH_1,
            (
                "TRUNCATE [ TABLE ] [ ONLY ] name [, ...] "
                "[ RESTART IDENTITY | CONTINUE IDENTITY ] "
                "[ CASCADE | RESTRICT ]"
            ),
            "synopsis-truncate",
        ),
    )
    actions = [
        TruncateGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise TruncateFactorLoopError("truncate action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise TruncateFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[TruncateFactorObligation]:
    rows: list[TruncateFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            TruncateFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"TRUNCATE-GRM|{action.grammar_branch_id}|"
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
        raise TruncateFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root,  # noqa: ANN001  (Path)
) -> list[TruncateFactorObligation]:
    """Compile the 52 SFV obligations from the shipped applicability catalog."""

    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("truncate")
    if len(catalog_rows) != 52:
        raise TruncateFactorLoopError("canonical obligation count drift")
    rows: list[TruncateFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            TruncateFactorObligation(
                ordinal=0,
                obligation_id=f"TRUNCATE-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[TruncateFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"truncate-factor-obligations-v1\n")
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


# Dense baseline defaults (all positive T1-T4 + T6 factor values).
# cascade_restrict defaults to "cascade" so that the
# fk_dependency=referenced_by_other_tables baseline case succeeds
# (TRUNCATE CASCADE handles FK references); cascade_restrict=none would
# behave like RESTRICT and cause an unattributed failure.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "expected_status": "success",
    "object_state": "table_exists",
    "cascade_restrict": "cascade",
    "identity_option": "none",
    "only_clause": "without_only",
    "multi_table": "single",
    "table_name_shape": "simple",
    "fk_dependency": "no_fk_references",
    "privilege_level": "owner",
    "fk_references_without_cascade": "none",
    "insufficient_privilege": "none",
    "non_existent_table": "none",
    "partitioned_table_behavior": "none",
    "temporary_table_truncation": "none",
    "verification": "select_count_zero",
    "cleanup": "rollback",
}


def _resolve_statement_branch_correlation(a: dict[str, str]) -> None:
    """Derive only_clause/identity_option from statement_branch or vice-versa."""

    sb = a.get("statement_branch", _BRANCH_1)
    oc = a.get("only_clause", "without_only")
    io = a.get("identity_option", "none")

    if sb != _BRANCH_1 or sb not in _BRANCH_OPTIONS:
        if sb in _BRANCH_OPTIONS:
            a["only_clause"], a["identity_option"] = _BRANCH_OPTIONS[sb]
    elif (oc, io) in _OPTIONS_BRANCH:
        a["statement_branch"] = _OPTIONS_BRANCH[(oc, io)]


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive related factors and ensure baseline self-consistency."""

    # statement_branch / only_clause / identity_option correlation.
    _resolve_statement_branch_correlation(a)

    # Group A: table doesn't exist (object_state / table_name_shape /
    # non_existent_table all describe the same scenario).
    os_state = a.get("object_state", "table_exists")
    tns = a.get("table_name_shape", "simple")
    net = a.get("non_existent_table", "none")

    if (
        os_state == "table_does_not_exist"
        or tns == "non_existent"
        or net == "truncate_non_existent_table"
    ):
        a["object_state"] = "table_does_not_exist"
        a["table_name_shape"] = "non_existent"
        a["non_existent_table"] = "truncate_non_existent_table"

    # Group B: insufficient privilege (privilege_level /
    # insufficient_privilege describe the same scenario).
    pl = a.get("privilege_level", "owner")
    ip = a.get("insufficient_privilege", "none")

    if pl == "insufficient_privilege" or ip in (
        "no_truncate_privilege",
        "non_owner_truncate",
    ):
        a["privilege_level"] = "insufficient_privilege"
        if ip == "none":
            a["insufficient_privilege"] = "no_truncate_privilege"

    # Group C: FK references without cascade.  When the primary is
    # fk_references_without_cascade=has_fk_ref_no_cascade, set the
    # concrete cause (fk_dependency + cascade_restrict).  When
    # fk_dependency=referenced_by_other_tables and cascade_restrict
    # is none/restrict, derive the failure marker.
    frwc = a.get("fk_references_without_cascade", "none")
    fk_dep = a.get("fk_dependency", "no_fk_references")
    cr = a.get("cascade_restrict", "cascade")

    if frwc == "has_fk_ref_no_cascade":
        a["fk_dependency"] = "referenced_by_other_tables"
        a["cascade_restrict"] = "restrict"
    elif (
        fk_dep == "referenced_by_other_tables"
        and cr in ("none", "restrict")
    ):
        a["fk_references_without_cascade"] = "has_fk_ref_no_cascade"
    else:
        a["fk_references_without_cascade"] = "none"

    # expected_status marker requires a concrete failure cause.
    es = a.get("expected_status", "success")
    if es == "failure":
        has_concrete = any(
            a.get(f) == v
            for f, v in _SFV_FAILURE_VALUES
            if f != "expected_status"
        )
        if not has_concrete:
            a["object_state"] = "table_does_not_exist"
            a["table_name_shape"] = "non_existent"
            a["non_existent_table"] = "truncate_non_existent_table"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: TruncateFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _BRANCH_1
    assignments["target_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise TruncateFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: TruncateFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise TruncateFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_truncate_factor_loop_plan(
    repository_root,  # noqa: ANN001  (Path; kept for API parity)
) -> TruncateFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    obligations = compile_truncate_factor_loop_obligations(
        repository_root
    )
    cases: list[TruncateFactorCase] = []
    delegated: list[TruncateFactorObligation] = []
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
            TruncateFactorCase(
                ordinal=ordinal,
                case_id=f"TRUNCATE{ordinal:05d}",
                sql_filename=f"TRUNCATE{ordinal:05d}.sql",
                object_prefix=f"truncate_{ordinal:05d}_",
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
    plan = TruncateFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 53 or len(plan.delegated) != 0:
        raise TruncateFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 53:
        raise TruncateFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 53:
        raise TruncateFactorLoopError("duplicate SQL filename")
    return plan


def compile_truncate_factor_loop_obligations(
    repository_root,  # noqa: ANN001  (Path; kept for API parity)
) -> tuple[TruncateFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    from pathlib import Path

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        TruncateFactorObligation(
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
        raise TruncateFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise TruncateFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 52}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise TruncateFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise TruncateFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 53:
        raise TruncateFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise TruncateFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "TruncateFactorLoopError",
    "TruncateGrammarAction",
    "TruncateFactorObligation",
    "TruncateFactorCase",
    "TruncateFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_truncate_factor_loop_obligations",
    "build_truncate_factor_loop_plan",
    "_obligation_multiset_sha256",
]
