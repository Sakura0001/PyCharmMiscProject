"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE CONVERSION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE CONVERSION``.  CREATE CONVERSION is a PostgreSQL DDL statement
with 2 official synopsis branches: ``CREATE CONVERSION`` and ``CREATE
DEFAULT CONVERSION``.  The statement defines an encoding conversion
object (catalog metadata in ``pg_catalog.pg_conversion`` plus a function
binding), so column/table/relation coverage is ``not_applicable`` and
there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  The grammar
ledger is self-contained: the 2 synopsis actions are frozen inline.  The
64 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateConversionFactorLoopError(ValueError):
    """Raised when a frozen CREATE CONVERSION obligation input drifts."""


@dataclass(frozen=True)
class CreateConversionGrammarAction:
    """One official target action form of the CREATE CONVERSION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateConversionFactorObligation:
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
class CreateConversionFactorCase:
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
class CreateConversionFactorLoopPlan:
    obligations: tuple[CreateConversionFactorObligation, ...]
    cases: tuple[CreateConversionFactorCase, ...]
    delegated: tuple[CreateConversionFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createconversion.html).
_BRANCH_CREATE = "branch_create_conversion"
_BRANCH_CREATE_DEFAULT = "branch_create_default_conversion"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createconversion"

_REPRESENTATIVE_ACTION = "create_conversion"

_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_CREATE: "create_conversion",
    _BRANCH_CREATE_DEFAULT: "create_default_conversion",
}

_DEFAULT_FLAG_CONSUMER = {
    "omitted": "create_conversion",
    "specified_default": "create_default_conversion",
}

_OBJECT_STATE_CONSUMER = {
    "not_exists": "create_conversion",
    "exists": "create_conversion",
    "same_encoding_pair_default_exists": "create_default_conversion",
}

_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "source_encoding": _REPRESENTATIVE_ACTION,
    "dest_encoding": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "default_flag": _REPRESENTATIVE_ACTION,
    "conversion_function_state": _REPRESENTATIVE_ACTION,
    "encoding_pair_direction": "create_default_conversion",
    "conversion_name_shape": _REPRESENTATIVE_ACTION,
    "function_name_shape": _REPRESENTATIVE_ACTION,
    "encoding_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "schema_existence": _REPRESENTATIVE_ACTION,
    "function_privilege": _REPRESENTATIVE_ACTION,
    "duplicate_conversion_name": _REPRESENTATIVE_ACTION,
    "duplicate_default_for_encoding_pair": "create_default_conversion",
    "nonexistent_function": _REPRESENTATIVE_ACTION,
    "function_signature_mismatch": _REPRESENTATIVE_ACTION,
    "sql_ascii_encoding": _REPRESENTATIVE_ACTION,
    "nonexistent_encoding": _REPRESENTATIVE_ACTION,
    "nonexistent_schema": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "create_conversion_expected_failure_provisional",
    ),
    ("object_state", "exists"): (
        "42710",
        "duplicate_conversion_name_provisional",
    ),
    ("object_state", "same_encoding_pair_default_exists"): (
        "42710",
        "duplicate_default_conversion_provisional",
    ),
    ("duplicate_conversion_name", "same_schema_conflict"): (
        "42710",
        "duplicate_conversion_name_provisional",
    ),
    (
        "duplicate_default_for_encoding_pair",
        "default_already_exists",
    ): ("42710", "duplicate_default_conversion_provisional"),
    ("conversion_function_state", "function_not_exists"): (
        "42704",
        "undefined_function_provisional",
    ),
    (
        "conversion_function_state",
        "function_exists_invalid_signature",
    ): ("42P13", "invalid_function_definition_provisional"),
    ("nonexistent_function", "function_not_exists"): (
        "42704",
        "undefined_function_provisional",
    ),
    ("function_signature_mismatch", "invalid_signature"): (
        "42P13",
        "invalid_function_definition_provisional",
    ),
    ("source_encoding", "SQL_ASCII"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("dest_encoding", "SQL_ASCII"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("sql_ascii_encoding", "source_is_sql_ascii"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("sql_ascii_encoding", "dest_is_sql_ascii"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("nonexistent_encoding", "encoding_not_exists"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F000",
        "invalid_schema_provisional",
    ),
    ("nonexistent_schema", "schema_not_exists"): (
        "3F000",
        "invalid_schema_provisional",
    ),
    ("privilege_level", "non_owner_no_create"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("function_privilege", "no_execute"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("conversion_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_conversion_name_provisional",
    ),
    ("function_name_shape", "nonexistent_name"): (
        "42704",
        "undefined_function_provisional",
    ),
    ("encoding_name_shape", "nonexistent_encoding_name"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("encoding_name_shape", "sql_ascii_encoding_name"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
}

_SFV_FAILURE_VALUES = frozenset(_SFV_FAILURE_SQLSTATE.keys())

_ACTION_BRANCH = {
    "create_conversion": _BRANCH_CREATE,
    "create_default_conversion": _BRANCH_CREATE_DEFAULT,
}

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE,
    "grammar_branch": _BRANCH_CREATE,
    "target_action": "create_conversion",
    "source_encoding": "UTF8",
    "dest_encoding": "LATIN1",
    "object_state": "not_exists",
    "expected_status": "success",
    "default_flag": "omitted",
    "conversion_function_state": "function_exists_valid_signature",
    "encoding_pair_direction": "single_direction",
    "conversion_name_shape": "simple_id",
    "function_name_shape": "simple_id",
    "encoding_name_shape": "valid_encoding_name",
    "privilege_level": "superuser",
    "schema_existence": "schema_exists",
    "function_privilege": "has_execute",
    "duplicate_conversion_name": "no_conflict",
    "duplicate_default_for_encoding_pair": "no_existing_default",
    "nonexistent_function": "function_exists",
    "function_signature_mismatch": "valid_conv_proc_signature",
    "sql_ascii_encoding": "neither_is_sql_ascii",
    "nonexistent_encoding": "encoding_exists",
    "nonexistent_schema": "schema_exists",
    "verification_mode": "catalog_query_pg_conversion",
    "cleanup_mode": "drop_conversion",
}


def _load_grammar_actions() -> (
    tuple[CreateConversionGrammarAction, ...]
):
    """Freeze every CREATE CONVERSION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_conversion",
            _BRANCH_CREATE,
            "CREATE CONVERSION name FOR "
            "source_encoding TO dest_encoding FROM function_name",
            "synopsis-create-conversion",
        ),
        (
            "create_default_conversion",
            _BRANCH_CREATE_DEFAULT,
            "CREATE DEFAULT CONVERSION name FOR "
            "source_encoding TO dest_encoding FROM function_name",
            "synopsis-create-default-conversion",
        ),
    )
    actions = [
        CreateConversionGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise CreateConversionFactorLoopError(
            "create conversion action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateConversionFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "default_flag":
        try:
            return _DEFAULT_FLAG_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateConversionFactorLoopError(
                f"unknown default_flag value: {row.value}"
            ) from exc
    if row.factor == "object_state":
        try:
            return _OBJECT_STATE_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateConversionFactorLoopError(
                f"unknown object_state value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateConversionFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[CreateConversionFactorObligation]
):
    rows: list[CreateConversionFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateConversionFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CCONV-GRM|{action.grammar_branch_id}|"
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
        raise CreateConversionFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateConversionFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_conversion")
    if len(catalog_rows) != 64:
        raise CreateConversionFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateConversionFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateConversionFactorObligation(
                ordinal=0,
                obligation_id=f"CCONV-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateConversionFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-conversion-factor-obligations-v1\n"
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


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "not_exists")
    dcn = a.get("duplicate_conversion_name", "no_conflict")
    cns = a.get("conversion_name_shape", "simple_id")

    if os_ == "exists" or dcn == "same_schema_conflict" or cns == "duplicate_name":
        a["object_state"] = "exists"
        a["duplicate_conversion_name"] = "same_schema_conflict"
        a["conversion_name_shape"] = "duplicate_name"

    dd = a.get("duplicate_default_for_encoding_pair", "no_existing_default")
    if os_ == "same_encoding_pair_default_exists" or dd == "default_already_exists":
        a["object_state"] = "same_encoding_pair_default_exists"
        a["duplicate_default_for_encoding_pair"] = "default_already_exists"

    cfs = a.get(
        "conversion_function_state", "function_exists_valid_signature"
    )
    fns = a.get("function_name_shape", "simple_id")
    nf = a.get("nonexistent_function", "function_exists")
    if (
        cfs == "function_not_exists"
        or fns == "nonexistent_name"
        or nf == "function_not_exists"
    ):
        a["conversion_function_state"] = "function_not_exists"
        a["function_name_shape"] = "nonexistent_name"
        a["nonexistent_function"] = "function_not_exists"

    fsm = a.get(
        "function_signature_mismatch", "valid_conv_proc_signature"
    )
    if (
        cfs == "function_exists_invalid_signature"
        or fsm == "invalid_signature"
    ):
        a["conversion_function_state"] = (
            "function_exists_invalid_signature"
        )
        a["function_signature_mismatch"] = "invalid_signature"

    se = a.get("source_encoding", "UTF8")
    de = a.get("dest_encoding", "LATIN1")
    sae = a.get("sql_ascii_encoding", "neither_is_sql_ascii")
    ens = a.get("encoding_name_shape", "valid_encoding_name")
    if (
        se == "SQL_ASCII"
        or sae == "source_is_sql_ascii"
        or ens == "sql_ascii_encoding_name"
    ):
        a["source_encoding"] = "SQL_ASCII"
        a["sql_ascii_encoding"] = "source_is_sql_ascii"
        a["encoding_name_shape"] = "sql_ascii_encoding_name"
    if de == "SQL_ASCII" or sae == "dest_is_sql_ascii":
        a["dest_encoding"] = "SQL_ASCII"
        a["sql_ascii_encoding"] = "dest_is_sql_ascii"
        a["encoding_name_shape"] = "sql_ascii_encoding_name"

    ne = a.get("nonexistent_encoding", "encoding_exists")
    if ens == "nonexistent_encoding_name" or ne == "encoding_not_exists":
        a["encoding_name_shape"] = "nonexistent_encoding_name"
        a["nonexistent_encoding"] = "encoding_not_exists"

    sx = a.get("schema_existence", "schema_exists")
    ns = a.get("nonexistent_schema", "schema_exists")
    if sx == "schema_not_exists" or ns == "schema_not_exists":
        a["schema_existence"] = "schema_not_exists"
        a["nonexistent_schema"] = "schema_not_exists"

    fp = a.get("function_privilege", "has_execute")
    if fp == "no_execute":
        if a.get("privilege_level", "superuser") == "superuser":
            a["privilege_level"] = "schema_owner_with_create"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateConversionFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    consumer = obligation.consumer_action_id
    branch = _ACTION_BRANCH[consumer]
    assignments["grammar_branch"] = branch
    assignments["target_action"] = consumer
    assignments["statement_branch"] = branch
    if consumer == "create_default_conversion":
        assignments["default_flag"] = "specified_default"
    else:
        assignments["default_flag"] = "omitted"
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateConversionFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateConversionFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateConversionFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_conversion_factor_loop_plan(
    repository_root: Path,
) -> CreateConversionFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_conversion_factor_loop_obligations(
        root
    )
    cases: list[CreateConversionFactorCase] = []
    delegated: list[CreateConversionFactorObligation] = []
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
            CreateConversionFactorCase(
                ordinal=ordinal,
                case_id=f"CREATECONVERSION{ordinal:05d}",
                sql_filename=f"CREATECONVERSION{ordinal:05d}.sql",
                object_prefix=f"createconversion_{ordinal:05d}_",
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
    plan = CreateConversionFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 66 or len(plan.delegated) != 0:
        raise CreateConversionFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 66:
        raise CreateConversionFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 66:
        raise CreateConversionFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_conversion_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateConversionFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateConversionFactorObligation(
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
    if len(rows) != 66:
        raise CreateConversionFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateConversionFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 2, "SFV": 64}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateConversionFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateConversionFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 66:
        raise CreateConversionFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateConversionFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateConversionFactorLoopError",
    "CreateConversionGrammarAction",
    "CreateConversionFactorObligation",
    "CreateConversionFactorCase",
    "CreateConversionFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_conversion_factor_loop_obligations",
    "build_create_conversion_factor_loop_plan",
    "_obligation_multiset_sha256",
]
