"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE CAST.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE CAST``.  CREATE CAST is a PostgreSQL DDL statement with three
official synopsis branches: ``WITH FUNCTION``, ``WITHOUT FUNCTION`` and
``WITH INOUT``.  The statement defines type-conversion metadata recorded
in ``pg_catalog.pg_cast`` (not a ``pg_class`` relation), so
column/table/relation coverage is ``not_applicable`` and there is no
``INV`` block.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no
``RISK`` obligations.

The grammar ledger is self-contained: the 3 synopsis actions are frozen
inline.  The 60 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateCastFactorLoopError(ValueError):
    """Raised when a frozen CREATE CAST obligation input drifts."""


@dataclass(frozen=True)
class CreateCastGrammarAction:
    """One official target action form of the CREATE CAST synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateCastFactorObligation:
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
class CreateCastFactorCase:
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
class CreateCastFactorLoopPlan:
    obligations: tuple[CreateCastFactorObligation, ...]
    cases: tuple[CreateCastFactorCase, ...]
    delegated: tuple[CreateCastFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createcast.html).
_BRANCH_WITH_FUNCTION = "branch_with_function"
_BRANCH_WITHOUT_FUNCTION = "branch_without_function"
_BRANCH_WITH_INOUT = "branch_with_inout"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createcast"

# A representative action used as the baseline consumer for canonical
# factors that are not bound to one specific branch.  WITH FUNCTION is
# the most common form and needs a function fixture.
_REPRESENTATIVE_ACTION = "with_function"

# statement_branch / cast_implementation canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_WITH_FUNCTION: "with_function",
    _BRANCH_WITHOUT_FUNCTION: "without_function",
    _BRANCH_WITH_INOUT: "with_inout",
}

_CAST_IMPLEMENTATION_CONSUMER = {
    "with_function": "with_function",
    "without_function": "without_function",
    "with_inout": "with_inout",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch,
# cast_implementation) are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "cast_implementation": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "implicit_context": _REPRESENTATIVE_ACTION,
    "source_type": _REPRESENTATIVE_ACTION,
    "target_type": _REPRESENTATIVE_ACTION,
    "source_type_shape": _REPRESENTATIVE_ACTION,
    "target_type_shape": _REPRESENTATIVE_ACTION,
    "function_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "function_dependency": _REPRESENTATIVE_ACTION,
    "type_ownership": _REPRESENTATIVE_ACTION,
    "duplicate_cast": _REPRESENTATIVE_ACTION,
    "same_source_and_target": _REPRESENTATIVE_ACTION,
    "binary_coercible_non_superuser": "without_function",
    "function_signature_mismatch": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("duplicate_cast", "same_source_target_direction"),
        ("function_dependency", "function_not_exists"),
        ("function_dependency", "function_exists_wrong_signature"),
        ("function_signature_mismatch", "wrong_first_arg_type"),
        ("function_signature_mismatch", "wrong_return_type"),
        ("binary_coercible_non_superuser", "non_superuser_without_function"),
        ("same_source_and_target", "same_type_no_function"),
        ("privilege_level", "non_owner"),
        ("type_ownership", "owns_neither"),
        ("insufficient_privilege", "owns_no_type"),
        ("insufficient_privilege", "no_usage_on_other_type"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42809",
        "create_cast_binding_invalid_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_cast_provisional",
    ),
    ("duplicate_cast", "same_source_target_direction"): (
        "42710",
        "duplicate_cast_provisional",
    ),
    ("function_dependency", "function_not_exists"): (
        "42704",
        "missing_cast_function_provisional",
    ),
    ("function_dependency", "function_exists_wrong_signature"): (
        "42804",
        "wrong_cast_function_signature_provisional",
    ),
    ("function_signature_mismatch", "wrong_first_arg_type"): (
        "42804",
        "wrong_cast_function_signature_provisional",
    ),
    ("function_signature_mismatch", "wrong_return_type"): (
        "42804",
        "wrong_cast_function_signature_provisional",
    ),
    ("binary_coercible_non_superuser", "non_superuser_without_function"): (
        "42501",
        "binary_cast_requires_superuser_provisional",
    ),
    ("same_source_and_target", "same_type_no_function"): (
        "42804",
        "same_type_cast_requires_multiarg_function_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_cast_privilege_provisional",
    ),
    ("type_ownership", "owns_neither"): (
        "42501",
        "insufficient_cast_privilege_provisional",
    ),
    ("insufficient_privilege", "owns_no_type"): (
        "42501",
        "insufficient_cast_privilege_provisional",
    ),
    ("insufficient_privilege", "no_usage_on_other_type"): (
        "42501",
        "insufficient_cast_privilege_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateCastGrammarAction, ...]:
    """Freeze every CREATE CAST synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "with_function",
            _BRANCH_WITH_FUNCTION,
            (
                "CREATE CAST (source_type AS target_type) "
                "WITH FUNCTION function_name "
                "[ (argument_type [, ...]) ] "
                "[ AS ASSIGNMENT | AS IMPLICIT ]"
            ),
            "synopsis-with-function",
        ),
        (
            "without_function",
            _BRANCH_WITHOUT_FUNCTION,
            (
                "CREATE CAST (source_type AS target_type) "
                "WITHOUT FUNCTION "
                "[ AS ASSIGNMENT | AS IMPLICIT ]"
            ),
            "synopsis-without-function",
        ),
        (
            "with_inout",
            _BRANCH_WITH_INOUT,
            (
                "CREATE CAST (source_type AS target_type) "
                "WITH INOUT "
                "[ AS ASSIGNMENT | AS IMPLICIT ]"
            ),
            "synopsis-with-inout",
        ),
    )
    actions = [
        CreateCastGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 3:
        raise CreateCastFactorLoopError("create cast action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateCastFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "cast_implementation":
        try:
            return _CAST_IMPLEMENTATION_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateCastFactorLoopError(
                f"unknown cast_implementation value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateCastFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CreateCastFactorObligation]:
    rows: list[CreateCastFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateCastFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CCAST-GRM|{action.grammar_branch_id}|"
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
        raise CreateCastFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateCastFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_cast")
    if len(catalog_rows) != 60:
        raise CreateCastFactorLoopError("canonical obligation count drift")
    rows: list[CreateCastFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateCastFactorObligation(
                ordinal=0,
                obligation_id=f"CCAST-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateCastFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-cast-factor-obligations-v1\n")
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


# Action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "with_function": _BRANCH_WITH_FUNCTION,
    "without_function": _BRANCH_WITHOUT_FUNCTION,
    "with_inout": _BRANCH_WITH_INOUT,
}

# Action -> cast_implementation value.
_ACTION_IMPLEMENTATION = {
    "with_function": "with_function",
    "without_function": "without_function",
    "with_inout": "with_inout",
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors (binary_coercible_non_superuser,
# function_signature_mismatch, insufficient_privilege) are NOT baselined
# here: every declared value is a failure mode, so they are set only when
# they are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_WITH_FUNCTION,
    "target_action": "with_function",
    "object_state": "not_exists",
    "expected_status": "success",
    "cast_implementation": "with_function",
    "implicit_context": "explicit_only_default",
    "source_type": "integer",
    "target_type": "bigint",
    "source_type_shape": "plain_type",
    "target_type_shape": "plain_type",
    "function_name_shape": "plain_identifier",
    "privilege_level": "superuser",
    "function_dependency": "function_exists_correct_signature",
    "type_ownership": "owns_both",
    "duplicate_cast": "reverse_direction_exists",
    "same_source_and_target": "same_type_multiarg_function",
    "verification_mode": "pg_cast_catalog_query",
    "cleanup_mode": "DROP_CAST",
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

    ci = a.get("cast_implementation", "with_function")
    pl = a.get("privilege_level", "superuser")
    to = a.get("type_ownership", "owns_both")
    fd = a.get("function_dependency", "function_exists_correct_signature")
    fsm = a.get("function_signature_mismatch", "")
    ip = a.get("insufficient_privilege", "")
    src = a.get("source_type", "integer")
    tgt = a.get("target_type", "bigint")
    os_ = a.get("object_state", "not_exists")
    dc = a.get("duplicate_cast", "reverse_direction_exists")
    bcn = a.get("binary_coercible_non_superuser", "")

    # privilege / ownership cluster: privilege_level / type_ownership /
    # insufficient_privilege
    if (
        pl == "non_owner"
        or to == "owns_neither"
        or ip in ("owns_no_type", "no_usage_on_other_type")
    ):
        a["privilege_level"] = "non_owner"
        a["type_ownership"] = "owns_neither"
        a["insufficient_privilege"] = "owns_no_type"
    elif pl == "type_owner_source" or to == "owns_source_type":
        a["privilege_level"] = "type_owner_source"
        a["type_ownership"] = "owns_source_type"
    elif pl == "type_owner_target" or to == "owns_target_type":
        a["privilege_level"] = "type_owner_target"
        a["type_ownership"] = "owns_target_type"

    # binary_coercible_non_superuser: WITHOUT FUNCTION + non-superuser
    if bcn == "non_superuser_without_function":
        a["cast_implementation"] = "without_function"
        a["privilege_level"] = "non_owner"
        a["type_ownership"] = "owns_neither"
        a["insufficient_privilege"] = "owns_no_type"
    elif ci == "without_function" and pl != "superuser":
        a["binary_coercible_non_superuser"] = (
            "non_superuser_without_function"
        )

    # function_signature_mismatch <-> function_dependency
    if (
        fd == "function_exists_wrong_signature"
        or fsm in ("wrong_first_arg_type", "wrong_return_type")
    ):
        a["function_dependency"] = "function_exists_wrong_signature"
        a["function_signature_mismatch"] = "wrong_first_arg_type"

    # object_state / duplicate_cast cluster
    if os_ == "already_exists" or dc == "same_source_target_direction":
        a["object_state"] = "already_exists"
        a["duplicate_cast"] = "same_source_target_direction"

    # same_source_and_target: source == target
    if src == tgt:
        if ci == "with_function":
            a["same_source_and_target"] = "same_type_multiarg_function"
        else:
            a["same_source_and_target"] = "same_type_no_function"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateCastFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["target_action"] = obligation.consumer_action_id
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments["cast_implementation"] = _ACTION_IMPLEMENTATION[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateCastFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateCastFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateCastFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_cast_factor_loop_plan(
    repository_root: Path,
) -> CreateCastFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_cast_factor_loop_obligations(root)
    cases: list[CreateCastFactorCase] = []
    delegated: list[CreateCastFactorObligation] = []
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
            CreateCastFactorCase(
                ordinal=ordinal,
                case_id=f"CREATECAST{ordinal:05d}",
                sql_filename=f"CREATECAST{ordinal:05d}.sql",
                object_prefix=f"createcast_{ordinal:05d}_",
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
    plan = CreateCastFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 63 or len(plan.delegated) != 0:
        raise CreateCastFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 63:
        raise CreateCastFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 63:
        raise CreateCastFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_cast_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateCastFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateCastFactorObligation(
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
    if len(rows) != 63:
        raise CreateCastFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateCastFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 3, "SFV": 60}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateCastFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateCastFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 63:
        raise CreateCastFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateCastFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateCastFactorLoopError",
    "CreateCastGrammarAction",
    "CreateCastFactorObligation",
    "CreateCastFactorCase",
    "CreateCastFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_cast_factor_loop_obligations",
    "build_create_cast_factor_loop_plan",
    "_obligation_multiset_sha256",
]
