"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE FUNCTION.

This module compiles the marginal ``SFV`` obligation ledger for
``CREATE [ OR REPLACE ] FUNCTION``.  CREATE FUNCTION is a PostgreSQL
routine DDL statement whose official synopsis is a single statement form
with many optional clauses (the two ``statement_branch`` values --
``branch_1`` (RETURNS rettype) and ``branch_2`` (RETURNS TABLE) -- are
themselves ``SFV`` rows in the shipped applicability universe, so there is
no separate ``GRM`` block).  The statement defines a ``pg_catalog.pg_proc``
catalog row (not a ``pg_class`` relation), so column/table/relation
coverage is ``not_applicable`` and there is no ``INV`` block.

CREATE FUNCTION is ``table-less``: it never creates a ``TABLE``, so the
bookend (DROP TABLE IF EXISTS) is never emitted.  The statement supports
``OR REPLACE``; the renderer emits both ``CREATE FUNCTION`` and ``CREATE
OR REPLACE FUNCTION`` variants.  PG18 changed the parallel-safety prose
(``document_change: changed``); the ``parallel_clause`` factor carries the
four required PG18 test points (SAFE, UNSAFE, RESTRICTED, ABSENT).

Each local obligation becomes exactly one regress program.  The 121
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


class CreateFunctionFactorLoopError(ValueError):
    """Raised when a frozen CREATE FUNCTION obligation input drifts."""


@dataclass(frozen=True)
class CreateFunctionFactorObligation:
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
class CreateFunctionFactorCase:
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
class CreateFunctionFactorLoopPlan:
    obligations: tuple[CreateFunctionFactorObligation, ...]
    cases: tuple[CreateFunctionFactorCase, ...]
    delegated: tuple[CreateFunctionFactorObligation, ...]
    obligation_multiset_sha256: str


_DOC_SOURCE = "postgresql-18.4-doc:sql-createfunction"

# CREATE FUNCTION has a single synopsis form (CREATE [OR REPLACE] FUNCTION
# name(...)...); the statement_branch values are SFV rows, not GRM actions.
# Every canonical factor is observable through the single create target.
_REPRESENTATIVE_ACTION = "create_function"


def _canonical_consumer(row) -> str:
    return _REPRESENTATIVE_ACTION


# Unconditional failure (factor, value) pairs: every T5 boundary value plus
# the expected_status=failure catch-all.  The conditional duplicate failure
# (object_state=already_exists_same_signature + or_replace_clause=absent) is
# NOT listed here -- it is resolved via duplicate_function_signature in
# :func:`_derive_overlapping_factors` so that the OR REPLACE replace variant
# (a success) is not falsely counted as a failure.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("duplicate_function_signature", "with_OR_REPLACE_noop_signature_change"),
        ("duplicate_function_signature", "without_OR_REPLACE_error"),
        ("invalid_argtype", "unknown_type_name"),
        ("invalid_rettype", "unknown_type_name"),
        ("conflicting_attributes", "WINDOW_with_RETURNS_TABLE"),
        ("conflicting_attributes", "IMMUTABLE_with_SIDE_EFFECT"),
        ("permission_insufficient", "no_create_privilege_in_schema"),
        ("permission_insufficient", "no_usage_privilege_on_language"),
        ("language_not_available", "untrusted_language_requires_superuser"),
        ("identifier_length_exceeded", "over_63_chars"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# These encode the expected outcome class only; the DB phase verifies on a
# live PG 18.4 server.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_function_provisional",
    ),
    ("object_state", "already_exists_same_signature"): (
        "42710",
        "duplicate_function_provisional",
    ),
    ("duplicate_function_signature", "with_OR_REPLACE_noop_signature_change"): (
        "42P13",
        "cannot_change_signature_provisional",
    ),
    ("duplicate_function_signature", "without_OR_REPLACE_error"): (
        "42710",
        "duplicate_function_provisional",
    ),
    ("invalid_argtype", "unknown_type_name"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("invalid_rettype", "unknown_type_name"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("conflicting_attributes", "WINDOW_with_RETURNS_TABLE"): (
        "0A000",
        "window_set_return_provisional",
    ),
    ("conflicting_attributes", "IMMUTABLE_with_SIDE_EFFECT"): (
        "42P13",
        "invalid_function_definition_provisional",
    ),
    ("permission_insufficient", "no_create_privilege_in_schema"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("permission_insufficient", "no_usage_privilege_on_language"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("language_not_available", "untrusted_language_requires_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("identifier_length_exceeded", "over_63_chars"): (
        "42622",
        "name_too_long_provisional",
    ),
}


def _obligation_is_failure(factor: str, value: str) -> bool:
    if (factor, value) in _SFV_FAILURE_VALUES:
        return True
    # Conditional duplicate: object_state=already_exists_same_signature with
    # the default or_replace_clause=absent is a duplicate-function failure.
    if factor == "object_state" and value == "already_exists_same_signature":
        return True
    return False


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateFunctionFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_function")
    if len(catalog_rows) != 121:
        raise CreateFunctionFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateFunctionFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = _obligation_is_failure(row.factor, row.value)
        rows.append(
            CreateFunctionFactorObligation(
                ordinal=0,
                obligation_id=f"CFUNC-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateFunctionFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-function-factor-obligations-v1\n"
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
# single-value boundary factors are derived in
# :func:`_derive_overlapping_factors` (set only when their T1-T4 trigger is
# active) so that the success path is never falsely attributed a failure.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "object_state": "not_exists",
    "expected_status": "success",
    "or_replace_clause": "absent",
    "returns_clause": "RETURNS_rettype",
    "language_clause": "sql",
    "volatility_clause": "absent",
    "null_handling_clause": "absent",
    "security_clause": "absent",
    "parallel_clause": "absent",
    "leakproof_clause": "absent",
    "window_clause": "absent",
    "transform_clause": "absent",
    "sql_body_form": "sql_body_inline",
    "function_name_shape": "simple",
    "argmode": "absent",
    "argname": "without_argname",
    "argtype": "integer",
    "rettype": "same_as_argtype",
    "default_expr_shape": "without_DEFAULT",
    "privilege_level": "superuser",
    "schema_dependency": "schema_exists",
    "role_dependency": "owner_role_exists",
    "language_dependency": "language_installed_sql",
    "extension_dependency": "extension_exists",
    "verification_mode": "pg_proc_catalog_query",
    "cleanup_mode": "DROP_FUNCTION_IF_EXISTS",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # --- duplicate_function_signature cluster -------------------------
    os_ = a.get("object_state", "not_exists")
    orr = a.get("or_replace_clause", "absent")
    dfs = a.get("duplicate_function_signature", "")
    if dfs == "with_OR_REPLACE_replace":
        a["or_replace_clause"] = "present"
        a["object_state"] = "already_exists_same_signature"
    elif dfs == "with_OR_REPLACE_noop_signature_change":
        a["or_replace_clause"] = "present"
        a["object_state"] = "already_exists_same_signature"
    elif dfs == "without_OR_REPLACE_error":
        a["or_replace_clause"] = "absent"
        a["object_state"] = "already_exists_same_signature"
    else:
        # Derive duplicate_function_signature from object_state + or_replace
        if os_ == "already_exists_same_signature":
            if orr == "present":
                a["duplicate_function_signature"] = (
                    "with_OR_REPLACE_replace"
                )
            else:
                a["duplicate_function_signature"] = (
                    "without_OR_REPLACE_error"
                )

    # --- invalid_argtype cluster --------------------------------------
    iat = a.get("invalid_argtype", "")
    if iat == "unknown_type_name":
        a["argtype"] = "nosuchtype"
    # --- invalid_rettype cluster --------------------------------------
    irt = a.get("invalid_rettype", "")
    if irt == "unknown_type_name":
        a["rettype"] = "nosuchtype"

    # --- conflicting_attributes cluster -------------------------------
    ca = a.get("conflicting_attributes", "")
    if ca == "WINDOW_with_RETURNS_TABLE":
        a["window_clause"] = "present"
        a["returns_clause"] = "RETURNS_TABLE"
    elif ca == "IMMUTABLE_with_SIDE_EFFECT":
        a["volatility_clause"] = "IMMUTABLE"

    # --- permission_insufficient cluster -------------------------------
    pi = a.get("permission_insufficient", "")
    pl = a.get("privilege_level", "superuser")
    if pi == "no_create_privilege_in_schema":
        a["privilege_level"] = "non_owner_no_privilege"
        a["schema_dependency"] = "schema_not_exists"
    elif pi == "no_usage_privilege_on_language":
        a["privilege_level"] = "non_owner_no_privilege"
    if pl == "non_owner_no_privilege":
        a["permission_insufficient"] = (
            a.get("permission_insufficient")
            or "no_create_privilege_in_schema"
        )

    # --- language_not_available cluster -------------------------------
    lna = a.get("language_not_available", "")
    if lna == "untrusted_language_requires_superuser":
        a["language_clause"] = "c"
        a["privilege_level"] = "non_owner_no_privilege"
    elif (
        a.get("language_clause") == "c"
        and a.get("privilege_level", "superuser") != "superuser"
    ):
        a["language_not_available"] = (
            "untrusted_language_requires_superuser"
        )

    # --- identifier_length_exceeded cluster ---------------------------
    ile = a.get("identifier_length_exceeded", "")
    if ile == "over_63_chars":
        a["function_name_shape"] = "simple"

    # --- expected_status=failure -> representative failure -------------
    es = a.get("expected_status", "success")
    if es == "failure":
        a["object_state"] = "already_exists_same_signature"
        a["or_replace_clause"] = "absent"
        a["duplicate_function_signature"] = "without_OR_REPLACE_error"

    # --- Derive expected_status from failure count -------------------
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateFunctionFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateFunctionFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateFunctionFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateFunctionFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_function_factor_loop_plan(
    repository_root: Path,
) -> CreateFunctionFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_function_factor_loop_obligations(root)
    cases: list[CreateFunctionFactorCase] = []
    delegated: list[CreateFunctionFactorObligation] = []
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
            CreateFunctionFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEFUNCTION{ordinal:05d}",
                sql_filename=f"CREATEFUNCTION{ordinal:05d}.sql",
                object_prefix=f"createfunction_{ordinal:05d}_",
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
    plan = CreateFunctionFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 121 or len(plan.delegated) != 0:
        raise CreateFunctionFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 121:
        raise CreateFunctionFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 121:
        raise CreateFunctionFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_function_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateFunctionFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        CreateFunctionFactorObligation(
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
    if len(rows) != 121:
        raise CreateFunctionFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateFunctionFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 121}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateFunctionFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateFunctionFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 121:
        raise CreateFunctionFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateFunctionFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateFunctionFactorLoopError",
    "CreateFunctionFactorObligation",
    "CreateFunctionFactorCase",
    "CreateFunctionFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "compile_create_function_factor_loop_obligations",
    "build_create_function_factor_loop_plan",
    "_obligation_multiset_sha256",
]
