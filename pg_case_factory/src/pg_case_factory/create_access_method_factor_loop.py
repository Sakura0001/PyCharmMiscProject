"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE ACCESS METHOD.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE ACCESS METHOD``.  CREATE ACCESS METHOD is a PostgreSQL DDL
statement with a single official synopsis branch (``branch_1``):
``CREATE ACCESS METHOD name TYPE access_method_type HANDLER
handler_function``.  The statement registers an access method in
``pg_catalog.pg_am`` (not a ``pg_class`` relation), so
column/table/relation coverage is ``not_applicable`` and there is no
``INV`` block.

Each local obligation becomes exactly one regress program.  CREATE
ACCESS METHOD requires superuser privilege, so
``privilege_level=non_superuser`` is an expected failure (SQLSTATE
42501).  The inventory declares 15 factors / 30 factor values; together
with the single GRM synopsis obligation the ledger has 31 local cases.

The grammar ledger is self-contained (there is no separate
``create_access_method_regress`` module): the 1 synopsis action is
frozen inline.  The 30 canonical ``SFV`` rows are loaded from the
shipped applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateAccessMethodFactorLoopError(ValueError):
    """Raised when a frozen CREATE ACCESS METHOD obligation input drifts."""


@dataclass(frozen=True)
class CreateAccessMethodGrammarAction:
    """One official target action form of the CREATE ACCESS METHOD synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateAccessMethodFactorObligation:
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
class CreateAccessMethodFactorCase:
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
class CreateAccessMethodFactorLoopPlan:
    obligations: tuple[CreateAccessMethodFactorObligation, ...]
    cases: tuple[CreateAccessMethodFactorCase, ...]
    delegated: tuple[CreateAccessMethodFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createaccessmethod.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-create-access-method"

# CREATE ACCESS METHOD has a single synopsis action; every factor value
# is observable through it.
_REPRESENTATIVE_ACTION = "create_access_method"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1: "create_access_method",
}

# Canonical factor -> the action where the value is observable.
# CREATE ACCESS METHOD has one branch, so every factor is observable
# through ``create_access_method``.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "access_method_type": _REPRESENTATIVE_ACTION,
    "handler_function_state": _REPRESENTATIVE_ACTION,
    "am_name_shape": _REPRESENTATIVE_ACTION,
    "handler_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "handler_dependency": _REPRESENTATIVE_ACTION,
    "duplicate_am_name": _REPRESENTATIVE_ACTION,
    "invalid_access_method_type": _REPRESENTATIVE_ACTION,
    "handler_wrong_return_type": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target
# check and are rejected (provisional sqlstates - DB phase verifies
# on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("handler_function_state", "not_exists"),
        ("handler_function_state", "wrong_return_type"),
        ("privilege_level", "non_superuser"),
        ("handler_dependency", "handler_exists_wrong_return_type"),
        ("handler_dependency", "handler_not_exists"),
        ("duplicate_am_name", "with_existing_am"),
        ("duplicate_am_name", "with_builtin_am"),
        ("invalid_access_method_type", "unknown_type_value"),
        ("handler_wrong_return_type", "returns_non_internal"),
        ("insufficient_privilege", "non_superuser_create"),
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
    ("handler_function_state", "not_exists"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("handler_function_state", "wrong_return_type"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("privilege_level", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("handler_dependency", "handler_exists_wrong_return_type"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("handler_dependency", "handler_not_exists"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("duplicate_am_name", "with_existing_am"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("duplicate_am_name", "with_builtin_am"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("invalid_access_method_type", "unknown_type_value"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("handler_wrong_return_type", "returns_non_internal"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("insufficient_privilege", "non_superuser_create"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateAccessMethodGrammarAction, ...]
):
    """Freeze every CREATE ACCESS METHOD synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_access_method",
            _BRANCH_1,
            (
                "CREATE ACCESS METHOD name TYPE access_method_type "
                "HANDLER handler_function"
            ),
            "synopsis-branch-1",
        ),
    )
    actions = [
        CreateAccessMethodGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateAccessMethodFactorLoopError(
            "create access method action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateAccessMethodFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateAccessMethodFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[CreateAccessMethodFactorObligation]
):
    rows: list[CreateAccessMethodFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateAccessMethodFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CAM-GRM|{action.grammar_branch_id}|"
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
        raise CreateAccessMethodFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateAccessMethodFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_access_method")
    if len(catalog_rows) != 30:
        raise CreateAccessMethodFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateAccessMethodFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateAccessMethodFactorObligation(
                ordinal=0,
                obligation_id=f"CAM-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateAccessMethodFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-access-method-factor-obligations-v1\n"
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
    "create_access_method": _BRANCH_1,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The
# T5 single-value factors (duplicate_am_name, invalid_access_method_type,
# handler_wrong_return_type, insufficient_privilege) are NOT baselined
# here: every declared value is a failure mode, so they are set only
# when they are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "grammar_branch": _BRANCH_1,
    "target_action": "create_access_method",
    "object_state": "not_exists",
    "expected_status": "success",
    "access_method_type": "INDEX",
    "handler_function_state": "exists",
    "am_name_shape": "plain_identifier",
    "handler_name_shape": "plain_identifier",
    "privilege_level": "superuser",
    "handler_dependency": "handler_exists_returns_internal",
    "verification_mode": "pg_am_catalog_query",
    "cleanup_mode": "DROP_ACCESS_METHOD",
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
    hfs = a.get("handler_function_state", "exists")
    pl = a.get("privilege_level", "superuser")
    hd = a.get("handler_dependency", "")
    dan = a.get("duplicate_am_name", "")
    iamt = a.get("invalid_access_method_type", "")
    hwrt = a.get("handler_wrong_return_type", "")
    ip = a.get("insufficient_privilege", "")

    # object_state / duplicate_am_name cluster
    if (
        os_ == "already_exists"
        or dan in ("with_existing_am", "with_builtin_am")
    ):
        a["object_state"] = "already_exists"
        if dan == "with_builtin_am":
            a["duplicate_am_name"] = "with_builtin_am"
        elif dan == "with_existing_am":
            a["duplicate_am_name"] = "with_existing_am"
        else:
            a["duplicate_am_name"] = "with_existing_am"
    else:
        a["object_state"] = "not_exists"
        a["duplicate_am_name"] = "none"

    # handler_function_state / handler_dependency /
    # handler_wrong_return_type cluster
    if hfs == "not_exists" or hd == "handler_not_exists":
        a["handler_function_state"] = "not_exists"
        a["handler_dependency"] = "handler_not_exists"
        a["handler_wrong_return_type"] = "correct"
    elif (
        hfs == "wrong_return_type"
        or hd == "handler_exists_wrong_return_type"
        or hwrt == "returns_non_internal"
    ):
        a["handler_function_state"] = "wrong_return_type"
        a["handler_dependency"] = "handler_exists_wrong_return_type"
        a["handler_wrong_return_type"] = "returns_non_internal"
    else:
        a["handler_function_state"] = "exists"
        a["handler_dependency"] = "handler_exists_returns_internal"
        a["handler_wrong_return_type"] = "correct"

    # privilege_level / insufficient_privilege cluster
    if pl == "non_superuser" or ip == "non_superuser_create":
        a["privilege_level"] = "non_superuser"
        a["insufficient_privilege"] = "non_superuser_create"
    else:
        a["privilege_level"] = "superuser"
        a["insufficient_privilege"] = "sufficient"

    # invalid_access_method_type: standalone T5 boundary
    if iamt == "unknown_type_value":
        a["invalid_access_method_type"] = "unknown_type_value"
    else:
        a["invalid_access_method_type"] = "none"

    # expected_status: needs a real failure trigger.
    if a.get("expected_status") == "failure":
        if a.get("object_state") != "already_exists":
            a["object_state"] = "already_exists"
            a["duplicate_am_name"] = "with_existing_am"
        _derive_overlapping_factors_inner(a)
    else:
        _derive_overlapping_factors_inner(a)


def _derive_overlapping_factors_inner(a: dict[str, str]) -> None:
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
    obligation: CreateAccessMethodFactorObligation,
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
        raise CreateAccessMethodFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateAccessMethodFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateAccessMethodFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_access_method_factor_loop_plan(
    repository_root: Path,
) -> CreateAccessMethodFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_access_method_factor_loop_obligations(
        root
    )
    cases: list[CreateAccessMethodFactorCase] = []
    delegated: list[CreateAccessMethodFactorObligation] = []
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
            CreateAccessMethodFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEACCESSMETHOD{ordinal:05d}",
                sql_filename=(
                    f"CREATEACCESSMETHOD{ordinal:05d}.sql"
                ),
                object_prefix=(
                    f"createaccessmethod_{ordinal:05d}_"
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
    plan = CreateAccessMethodFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 31 or len(plan.delegated) != 0:
        raise CreateAccessMethodFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 31:
        raise CreateAccessMethodFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 31:
        raise CreateAccessMethodFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_access_method_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateAccessMethodFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateAccessMethodFactorObligation(
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
    if len(rows) != 31:
        raise CreateAccessMethodFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateAccessMethodFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 30}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateAccessMethodFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateAccessMethodFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 31:
        raise CreateAccessMethodFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateAccessMethodFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateAccessMethodFactorLoopError",
    "CreateAccessMethodGrammarAction",
    "CreateAccessMethodFactorObligation",
    "CreateAccessMethodFactorCase",
    "CreateAccessMethodFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_access_method_factor_loop_obligations",
    "build_create_access_method_factor_loop_plan",
    "_obligation_multiset_sha256",
]
