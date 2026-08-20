"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE FOREIGN DATA WRAPPER.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE FOREIGN DATA WRAPPER``.  The statement has a single official
synopsis branch (``branch_create_fdw``):
``CREATE FOREIGN DATA WRAPPER name [ HANDLER handler_function | NO HANDLER ]
[ VALIDATOR validator_function | NO VALIDATOR ]
[ OPTIONS ( option 'value' [, ... ] ) ]``.  The statement registers a
row in ``pg_catalog.pg_foreign_data_wrapper`` (not a ``pg_class``
relation), so column/table/relation coverage is ``not_applicable`` and
there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  CREATE
FOREIGN DATA WRAPPER requires superuser privilege, so
``privilege_level=non_superuser`` is an expected failure (SQLSTATE
42501).  The inventory declares 24 factors / 57 factor values; together
with the single GRM synopsis obligation the ledger has 58 local cases.

The grammar ledger is self-contained (there is no separate
``create_foreign_data_wrapper_regress`` module): the 1 synopsis action
is frozen inline.  The 57 canonical ``SFV`` rows are loaded from the
shipped applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateForeignDataWrapperFactorLoopError(ValueError):
    """Raised when a frozen CREATE FOREIGN DATA WRAPPER obligation input drifts."""


@dataclass(frozen=True)
class CreateForeignDataWrapperGrammarAction:
    """One official target action form of the CREATE FOREIGN DATA WRAPPER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateForeignDataWrapperFactorObligation:
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
class CreateForeignDataWrapperFactorCase:
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
class CreateForeignDataWrapperFactorLoopPlan:
    obligations: tuple[CreateForeignDataWrapperFactorObligation, ...]
    cases: tuple[CreateForeignDataWrapperFactorCase, ...]
    delegated: tuple[CreateForeignDataWrapperFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createforeigndatawrapper.html).
_BRANCH_CREATE_FDW = "branch_create_fdw"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createforeigndatawrapper"

# CREATE FOREIGN DATA WRAPPER has a single synopsis action; every
# factor value is observable through it.
_REPRESENTATIVE_ACTION = "create_foreign_data_wrapper"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_CREATE_FDW: "create_foreign_data_wrapper",
}

# Canonical factor -> the action where the value is observable.
# CREATE FOREIGN DATA WRAPPER has one branch, so every factor is
# observable through ``create_foreign_data_wrapper``.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "handler_clause": _REPRESENTATIVE_ACTION,
    "validator_clause": _REPRESENTATIVE_ACTION,
    "options_clause": _REPRESENTATIVE_ACTION,
    "handler_function_type": _REPRESENTATIVE_ACTION,
    "fdw_name_shape": _REPRESENTATIVE_ACTION,
    "handler_name_shape": _REPRESENTATIVE_ACTION,
    "validator_name_shape": _REPRESENTATIVE_ACTION,
    "option_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "handler_function_existence": _REPRESENTATIVE_ACTION,
    "validator_function_existence": _REPRESENTATIVE_ACTION,
    "handler_function_return_type": _REPRESENTATIVE_ACTION,
    "duplicate_fdw_name": _REPRESENTATIVE_ACTION,
    "nonexistent_handler_function": _REPRESENTATIVE_ACTION,
    "nonexistent_validator_function": _REPRESENTATIVE_ACTION,
    "invalid_handler_return_type": _REPRESENTATIVE_ACTION,
    "non_superuser_attempt": _REPRESENTATIVE_ACTION,
    "duplicate_option_name": _REPRESENTATIVE_ACTION,
    "no_handler_access_limit": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target
# check and are rejected (provisional sqlstates -- DB phase verifies
# on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("handler_function_type", "wrong_return_type"),
        ("fdw_name_shape", "duplicate_name"),
        ("handler_name_shape", "nonexistent_function"),
        ("validator_name_shape", "nonexistent_function"),
        ("option_name_shape", "duplicate_option"),
        ("privilege_level", "non_superuser"),
        ("handler_function_existence", "function_not_exists"),
        ("validator_function_existence", "function_not_exists"),
        ("handler_function_return_type", "mismatches_fdw_handler"),
        ("duplicate_fdw_name", "same_name_conflict"),
        ("nonexistent_handler_function", "function_missing"),
        ("nonexistent_validator_function", "function_missing"),
        ("invalid_handler_return_type", "wrong_type"),
        ("non_superuser_attempt", "non_superuser_execution"),
        ("duplicate_option_name", "duplicate_options"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure
# value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("handler_function_type", "wrong_return_type"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("fdw_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("handler_name_shape", "nonexistent_function"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("validator_name_shape", "nonexistent_function"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("option_name_shape", "duplicate_option"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("privilege_level", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("handler_function_existence", "function_not_exists"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("validator_function_existence", "function_not_exists"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("handler_function_return_type", "mismatches_fdw_handler"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("duplicate_fdw_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("nonexistent_handler_function", "function_missing"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("nonexistent_validator_function", "function_missing"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("invalid_handler_return_type", "wrong_type"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("non_superuser_attempt", "non_superuser_execution"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("duplicate_option_name", "duplicate_options"): (
        "42710",
        "duplicate_object_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateForeignDataWrapperGrammarAction, ...]
):
    """Freeze every CREATE FOREIGN DATA WRAPPER synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_foreign_data_wrapper",
            _BRANCH_CREATE_FDW,
            (
                "CREATE FOREIGN DATA WRAPPER name "
                "[ HANDLER handler_function | NO HANDLER ] "
                "[ VALIDATOR validator_function | NO VALIDATOR ] "
                "[ OPTIONS ( option 'value' [, ... ] ) ]"
            ),
            "synopsis-branch-create-fdw",
        ),
    )
    actions = [
        CreateForeignDataWrapperGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateForeignDataWrapperFactorLoopError(
            "create foreign data wrapper action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateForeignDataWrapperFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateForeignDataWrapperFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[CreateForeignDataWrapperFactorObligation]
):
    rows: list[CreateForeignDataWrapperFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateForeignDataWrapperFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CFDW-GRM|{action.grammar_branch_id}|"
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
        raise CreateForeignDataWrapperFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateForeignDataWrapperFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_foreign_data_wrapper")
    if len(catalog_rows) != 57:
        raise CreateForeignDataWrapperFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateForeignDataWrapperFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateForeignDataWrapperFactorObligation(
                ordinal=0,
                obligation_id=f"CFDW-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateForeignDataWrapperFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-foreign-data-wrapper-factor-obligations-v1\n"
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
    "create_foreign_data_wrapper": _BRANCH_CREATE_FDW,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).
# The T5 single-value factors (duplicate_fdw_name,
# nonexistent_handler_function, nonexistent_validator_function,
# invalid_handler_return_type, non_superuser_attempt,
# duplicate_option_name, no_handler_access_limit) overlap with their
# T1-T4 counterparts and are derived in
# :func:`_derive_overlapping_factors`, not baselined here.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE_FDW,
    "grammar_branch": _BRANCH_CREATE_FDW,
    "target_action": "create_foreign_data_wrapper",
    "object_state": "not_exists",
    "expected_status": "success",
    "handler_clause": "omitted",
    "validator_clause": "omitted",
    "options_clause": "omitted",
    "handler_function_type": "correct_fdw_handler",
    "fdw_name_shape": "simple_id",
    "handler_name_shape": "simple_id",
    "validator_name_shape": "simple_id",
    "option_name_shape": "valid_option",
    "privilege_level": "superuser",
    "handler_function_existence": "function_exists",
    "validator_function_existence": "function_exists",
    "handler_function_return_type": "matches_fdw_handler",
    "duplicate_fdw_name": "no_conflict",
    "nonexistent_handler_function": "function_exists",
    "nonexistent_validator_function": "function_exists",
    "invalid_handler_return_type": "correct_type",
    "non_superuser_attempt": "superuser_execution",
    "duplicate_option_name": "unique_options",
    "no_handler_access_limit": "with_handler_accessible",
    "verification_mode": "pg_foreign_data_wrapper_catalog",
    "cleanup_mode": "drop_fdw",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their
    T1-T4 counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value,
    the T1-T4 counterpart is derived.  This keeps the baseline
    assignment self-consistent so the render produces SQL that reaches
    the intended boundary.
    """

    os_ = a.get("object_state", "not_exists")
    fns = a.get("fdw_name_shape", "simple_id")
    hfe = a.get("handler_function_existence", "function_exists")
    hns = a.get("handler_name_shape", "simple_id")
    vfe = a.get("validator_function_existence", "function_exists")
    vns = a.get("validator_name_shape", "simple_id")
    hrt = a.get("handler_function_return_type", "matches_fdw_handler")
    hft = a.get("handler_function_type", "correct_fdw_handler")
    ons = a.get("option_name_shape", "valid_option")
    pl = a.get("privilege_level", "superuser")
    hc = a.get("handler_clause", "omitted")
    nhf = a.get("nonexistent_handler_function", "")
    nvf = a.get("nonexistent_validator_function", "")
    ihrt = a.get("invalid_handler_return_type", "")
    nsa = a.get("non_superuser_attempt", "")
    don = a.get("duplicate_option_name", "")
    dfn = a.get("duplicate_fdw_name", "")
    nhal = a.get("no_handler_access_limit", "")

    # object_state / fdw_name_shape / duplicate_fdw_name cluster
    if (
        os_ == "already_exists"
        or fns == "duplicate_name"
        or dfn == "same_name_conflict"
    ):
        a["object_state"] = "already_exists"
        a["fdw_name_shape"] = "duplicate_name"
        a["duplicate_fdw_name"] = "same_name_conflict"
    else:
        if os_ != "already_exists":
            a["object_state"] = "not_exists"
        if dfn != "same_name_conflict":
            a["duplicate_fdw_name"] = "no_conflict"

    # handler function existence / handler_name_shape /
    # nonexistent_handler_function cluster
    if (
        hfe == "function_not_exists"
        or hns == "nonexistent_function"
        or nhf == "function_missing"
    ):
        a["handler_function_existence"] = "function_not_exists"
        a["handler_name_shape"] = "nonexistent_function"
        a["nonexistent_handler_function"] = "function_missing"
    else:
        if hfe != "function_not_exists":
            a["handler_function_existence"] = "function_exists"
        if hns != "nonexistent_function":
            a["handler_name_shape"] = "simple_id"
        a["nonexistent_handler_function"] = "function_exists"

    # validator function existence / validator_name_shape /
    # nonexistent_validator_function cluster
    if (
        vfe == "function_not_exists"
        or vns == "nonexistent_function"
        or nvf == "function_missing"
    ):
        a["validator_function_existence"] = "function_not_exists"
        a["validator_name_shape"] = "nonexistent_function"
        a["nonexistent_validator_function"] = "function_missing"
    else:
        if vfe != "function_not_exists":
            a["validator_function_existence"] = "function_exists"
        if vns != "nonexistent_function":
            a["validator_name_shape"] = "simple_id"
        a["nonexistent_validator_function"] = "function_exists"

    # handler_function_return_type / handler_function_type /
    # invalid_handler_return_type cluster
    if (
        hrt == "mismatches_fdw_handler"
        or hft == "wrong_return_type"
        or ihrt == "wrong_type"
    ):
        a["handler_function_return_type"] = "mismatches_fdw_handler"
        a["handler_function_type"] = "wrong_return_type"
        a["invalid_handler_return_type"] = "wrong_type"
    else:
        if hrt != "mismatches_fdw_handler":
            a["handler_function_return_type"] = "matches_fdw_handler"
        if hft != "wrong_return_type":
            a["handler_function_type"] = "correct_fdw_handler"
        a["invalid_handler_return_type"] = "correct_type"

    # option_name_shape / duplicate_option_name cluster
    if ons == "duplicate_option" or don == "duplicate_options":
        a["option_name_shape"] = "duplicate_option"
        a["duplicate_option_name"] = "duplicate_options"
    else:
        if ons != "duplicate_option":
            a["option_name_shape"] = "valid_option"
        a["duplicate_option_name"] = "unique_options"

    # privilege_level / non_superuser_attempt cluster
    if pl == "non_superuser" or nsa == "non_superuser_execution":
        a["privilege_level"] = "non_superuser"
        a["non_superuser_attempt"] = "non_superuser_execution"
    else:
        if pl != "non_superuser":
            a["privilege_level"] = "superuser"
        a["non_superuser_attempt"] = "superuser_execution"

    # handler_clause / no_handler_access_limit cluster
    if hc == "no_handler" or nhal == "no_handler_not_accessible":
        a["handler_clause"] = "no_handler"
        a["no_handler_access_limit"] = "no_handler_not_accessible"
    else:
        if hc != "no_handler":
            a["handler_clause"] = hc if hc != "no_handler" else "omitted"
        a["no_handler_access_limit"] = "with_handler_accessible"

    # expected_status: needs a real failure trigger.
    if a.get("expected_status") == "failure":
        if a.get("object_state") != "already_exists":
            a["object_state"] = "already_exists"
            a["fdw_name_shape"] = "duplicate_name"
            a["duplicate_fdw_name"] = "same_name_conflict"
        _derive_expected_status(a)
    else:
        _derive_expected_status(a)


def _derive_expected_status(a: dict[str, str]) -> None:
    """Set expected_status from the failure count."""

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateForeignDataWrapperFactorObligation,
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
    if len(assignments) != len(set(assignments)):
        raise CreateForeignDataWrapperFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateForeignDataWrapperFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateForeignDataWrapperFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_foreign_data_wrapper_factor_loop_plan(
    repository_root: Path,
) -> CreateForeignDataWrapperFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = (
        compile_create_foreign_data_wrapper_factor_loop_obligations(root)
    )
    cases: list[CreateForeignDataWrapperFactorCase] = []
    delegated: list[CreateForeignDataWrapperFactorObligation] = []
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
            CreateForeignDataWrapperFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEFOREIGNDATAWRAPPER{ordinal:05d}",
                sql_filename=(
                    f"CREATEFOREIGNDATAWRAPPER{ordinal:05d}.sql"
                ),
                object_prefix=(
                    f"createforeigndatawrapper_{ordinal:05d}_"
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
    plan = CreateForeignDataWrapperFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 58 or len(plan.delegated) != 0:
        raise CreateForeignDataWrapperFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 58:
        raise CreateForeignDataWrapperFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 58:
        raise CreateForeignDataWrapperFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_create_foreign_data_wrapper_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateForeignDataWrapperFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateForeignDataWrapperFactorObligation(
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
    if len(rows) != 58:
        raise CreateForeignDataWrapperFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateForeignDataWrapperFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 57}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateForeignDataWrapperFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateForeignDataWrapperFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 58:
        raise CreateForeignDataWrapperFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateForeignDataWrapperFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateForeignDataWrapperFactorLoopError",
    "CreateForeignDataWrapperGrammarAction",
    "CreateForeignDataWrapperFactorObligation",
    "CreateForeignDataWrapperFactorCase",
    "CreateForeignDataWrapperFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_foreign_data_wrapper_factor_loop_obligations",
    "build_create_foreign_data_wrapper_factor_loop_plan",
    "_obligation_multiset_sha256",
]
