"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE AGGREGATE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE AGGREGATE``.  CREATE AGGREGATE is a PostgreSQL DDL statement
with 3 official synopsis branches: regular, ordered-set/hypothetical, and
old-syntax.  The statement creates a routine (``pg_proc``/``pg_aggregate``
catalog row, not a ``pg_class`` relation), so column/table/relation coverage
is ``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no ``RISK``
obligations.

The grammar ledger is self-contained (there is no separate
``create_aggregate_regress`` module): the 3 synopsis actions are frozen
inline.  The 66 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateAggregateFactorLoopError(ValueError):
    """Raised when a frozen CREATE AGGREGATE obligation input drifts."""


@dataclass(frozen=True)
class CreateAggregateGrammarAction:
    """One official target action form of the CREATE AGGREGATE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateAggregateFactorObligation:
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
class CreateAggregateFactorCase:
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
class CreateAggregateFactorLoopPlan:
    obligations: tuple[CreateAggregateFactorObligation, ...]
    cases: tuple[CreateAggregateFactorCase, ...]
    delegated: tuple[CreateAggregateFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createaggregate.html).
_BRANCH_REGULAR = "branch_regular"
_BRANCH_ORDERED_SET = "branch_ordered_set"
_BRANCH_OLD_SYNTAX = "branch_old_syntax"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createaggregate"

# A representative branch_regular action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "regular"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_REGULAR: "regular",
    _BRANCH_ORDERED_SET: "ordered_set",
    _BRANCH_OLD_SYNTAX: "old_syntax",
}

# aggregate_form canonical value -> target action.
_AGGREGATE_FORM_CONSUMER = {
    "single_arg": "regular",
    "multi_arg": "regular",
    "zero_arg": "regular",
    "ordered_set": "ordered_set",
    "old_syntax": "old_syntax",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, aggregate_form)
# are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "or_replace_clause": _REPRESENTATIVE_ACTION,
    "parallel_option": _REPRESENTATIVE_ACTION,
    "arg_data_type": _REPRESENTATIVE_ACTION,
    "aggregate_name_shape": _REPRESENTATIVE_ACTION,
    "argmode_shape": _REPRESENTATIVE_ACTION,
    "argname_shape": _REPRESENTATIVE_ACTION,
    "sfunc_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "support_function_dependency": _REPRESENTATIVE_ACTION,
    "combinefunc_dependency": _REPRESENTATIVE_ACTION,
    "finalfunc_dependency": _REPRESENTATIVE_ACTION,
    "duplicate_aggregate": _REPRESENTATIVE_ACTION,
    "sfunc_signature_mismatch": _REPRESENTATIVE_ACTION,
    "or_replace_constraint_violation": _REPRESENTATIVE_ACTION,
    "invalid_ordered_set_variadic": "ordered_set",
    "missing_required_sfunc": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
# Includes both the T5 boundary versions and their T1-T4 crossed-negative
# counterparts so the extension's _present_failure_pair can resolve a
# SQLSTATE for every crossed failure.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("privilege_level", "non_owner"),
        ("or_replace_clause", "present_replace_with_constraint_violation"),
        ("support_function_dependency", "sfunc_not_exists"),
        ("support_function_dependency", "sfunc_wrong_signature"),
        ("finalfunc_dependency", "wrong_return_type"),
        ("duplicate_aggregate", "same_name_same_signature"),
        ("sfunc_signature_mismatch", "wrong_input_types"),
        ("sfunc_signature_mismatch", "wrong_return_type"),
        ("or_replace_constraint_violation", "changed_arg_types"),
        ("or_replace_constraint_violation", "changed_return_type"),
        ("or_replace_constraint_violation", "changed_kind"),
        ("invalid_ordered_set_variadic", "non_variadic_any"),
        ("missing_required_sfunc", "sfunc_not_found"),
        ("insufficient_privilege", "non_owner_create"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42723",
        "duplicate_function_provisional",
    ),
    ("object_state", "already_exists"): (
        "42723",
        "duplicate_function_provisional",
    ),
    ("support_function_dependency", "sfunc_not_exists"): (
        "42704",
        "undefined_function_provisional",
    ),
    ("support_function_dependency", "sfunc_wrong_signature"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("finalfunc_dependency", "wrong_return_type"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("duplicate_aggregate", "same_name_same_signature"): (
        "42723",
        "duplicate_function_provisional",
    ),
    ("sfunc_signature_mismatch", "wrong_input_types"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("sfunc_signature_mismatch", "wrong_return_type"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("or_replace_constraint_violation", "changed_arg_types"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("or_replace_constraint_violation", "changed_return_type"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("or_replace_constraint_violation", "changed_kind"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("invalid_ordered_set_variadic", "non_variadic_any"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
    ("missing_required_sfunc", "sfunc_not_found"): (
        "42704",
        "undefined_function_provisional",
    ),
    ("insufficient_privilege", "non_owner_create"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("or_replace_clause", "present_replace_with_constraint_violation"): (
        "42P17",
        "invalid_function_definition_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateAggregateGrammarAction, ...]
):
    """Freeze every CREATE AGGREGATE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "regular",
            _BRANCH_REGULAR,
            (
                "CREATE [ OR REPLACE ] AGGREGATE name "
                "( [ argmode ] [ argname ] arg_data_type [, ...] ) "
                "( SFUNC = sfunc, STYPE = state_data_type [, ...] )"
            ),
            "synopsis-regular",
        ),
        (
            "ordered_set",
            _BRANCH_ORDERED_SET,
            (
                "CREATE [ OR REPLACE ] AGGREGATE name "
                "( [ [ argmode ] [ argname ] arg_data_type [, ...] ] "
                "ORDER BY [ argmode ] [ argname ] arg_data_type [, ...] ) "
                "( SFUNC = sfunc, STYPE = state_data_type [, ...] )"
            ),
            "synopsis-ordered-set",
        ),
        (
            "old_syntax",
            _BRANCH_OLD_SYNTAX,
            (
                "CREATE [ OR REPLACE ] AGGREGATE name "
                "( BASETYPE = base_type, SFUNC = sfunc, "
                "STYPE = state_data_type [, ...] )"
            ),
            "synopsis-old-syntax",
        ),
    )
    actions = [
        CreateAggregateGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 3:
        raise CreateAggregateFactorLoopError(
            "create aggregate action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateAggregateFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "aggregate_form":
        try:
            return _AGGREGATE_FORM_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateAggregateFactorLoopError(
                f"unknown aggregate_form value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateAggregateFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[CreateAggregateFactorObligation]
):
    rows: list[CreateAggregateFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateAggregateFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CAGG-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 3:
        raise CreateAggregateFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateAggregateFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_aggregate")
    if len(catalog_rows) != 66:
        raise CreateAggregateFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateAggregateFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateAggregateFactorObligation(
                ordinal=0,
                obligation_id=f"CAGG-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateAggregateFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-aggregate-factor-obligations-v1\n"
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
    "regular": _BRANCH_REGULAR,
    "ordered_set": _BRANCH_ORDERED_SET,
    "old_syntax": _BRANCH_OLD_SYNTAX,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value failure factors (sfunc_signature_mismatch,
# or_replace_constraint_violation, invalid_ordered_set_variadic,
# missing_required_sfunc, insufficient_privilege) are NOT baselined here:
# every declared value is a failure mode, so they are set only when they
# are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_REGULAR,
    "grammar_branch": _BRANCH_REGULAR,
    "target_action": "regular",
    "object_state": "not_exists",
    "expected_status": "success",
    "aggregate_form": "single_arg",
    "or_replace_clause": "absent",
    "parallel_option": "UNSAFE_default",
    "arg_data_type": "integer",
    "aggregate_name_shape": "plain_identifier",
    "argmode_shape": "IN_default",
    "argname_shape": "absent",
    "sfunc_name_shape": "plain",
    "privilege_level": "aggregate_owner",
    "support_function_dependency": "sfunc_exists",
    "combinefunc_dependency": "exists",
    "finalfunc_dependency": "exists",
    "duplicate_aggregate": "same_name_different_signature",
    "verification_mode": "pg_aggregate_catalog_query",
    "cleanup_mode": "DROP_AGGREGATE",
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

    os_ = a.get("object_state", "not_exists")
    da = a.get("duplicate_aggregate", "same_name_different_signature")
    orc = a.get("or_replace_clause", "absent")
    orcv = a.get("or_replace_constraint_violation", "")
    sfd = a.get("support_function_dependency", "sfunc_exists")
    ssm = a.get("sfunc_signature_mismatch", "")
    mrs = a.get("missing_required_sfunc", "")
    pl = a.get("privilege_level", "aggregate_owner")
    ip = a.get("insufficient_privilege", "")
    iosv = a.get("invalid_ordered_set_variadic", "")

    # object_state=already_exists <-> duplicate_aggregate=same_name_same_signature
    if os_ == "already_exists" or da == "same_name_same_signature":
        a["object_state"] = "already_exists"
        a["duplicate_aggregate"] = "same_name_same_signature"

    # support_function_dependency=sfunc_not_exists <-> missing_required_sfunc=sfunc_not_found
    if sfd == "sfunc_not_exists" or mrs == "sfunc_not_found":
        a["support_function_dependency"] = "sfunc_not_exists"
        a["missing_required_sfunc"] = "sfunc_not_found"

    # support_function_dependency=sfunc_wrong_signature <-> sfunc_signature_mismatch
    if sfd == "sfunc_wrong_signature" or ssm in (
        "wrong_input_types",
        "wrong_return_type",
    ):
        a["support_function_dependency"] = "sfunc_wrong_signature"
        if not ssm:
            a["sfunc_signature_mismatch"] = "wrong_input_types"

    # privilege_level=non_owner <-> insufficient_privilege=non_owner_create
    if pl == "non_owner" or ip == "non_owner_create":
        a["privilege_level"] = "non_owner"
        a["insufficient_privilege"] = "non_owner_create"

    # or_replace_clause=present_replace_with_constraint_violation
    # <-> or_replace_constraint_violation
    if (
        orc == "present_replace_with_constraint_violation"
        or orcv
    ):
        a["or_replace_clause"] = (
            "present_replace_with_constraint_violation"
        )
        if not orcv:
            a["or_replace_constraint_violation"] = "changed_arg_types"

    # invalid_ordered_set_variadic -> ordered_set branch
    if iosv == "non_variadic_any":
        a["statement_branch"] = _BRANCH_ORDERED_SET
        a["grammar_branch"] = _BRANCH_ORDERED_SET
        a["target_action"] = "ordered_set"
        a["aggregate_form"] = "ordered_set"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateAggregateFactorObligation,
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
        raise CreateAggregateFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateAggregateFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateAggregateFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_aggregate_factor_loop_plan(
    repository_root: Path,
) -> CreateAggregateFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_aggregate_factor_loop_obligations(root)
    cases: list[CreateAggregateFactorCase] = []
    delegated: list[CreateAggregateFactorObligation] = []
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
            CreateAggregateFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEAGGREGATE{ordinal:05d}",
                sql_filename=f"CREATEAGGREGATE{ordinal:05d}.sql",
                object_prefix=(
                    f"createaggregate_{ordinal:05d}_"
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
    plan = CreateAggregateFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 69 or len(plan.delegated) != 0:
        raise CreateAggregateFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 69:
        raise CreateAggregateFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 69:
        raise CreateAggregateFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_aggregate_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateAggregateFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateAggregateFactorObligation(
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
    if len(rows) != 69:
        raise CreateAggregateFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateAggregateFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 3, "SFV": 66}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateAggregateFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateAggregateFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 69:
        raise CreateAggregateFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateAggregateFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateAggregateFactorLoopError",
    "CreateAggregateGrammarAction",
    "CreateAggregateFactorObligation",
    "CreateAggregateFactorCase",
    "CreateAggregateFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_aggregate_factor_loop_obligations",
    "build_create_aggregate_factor_loop_plan",
    "_obligation_multiset_sha256",
]
