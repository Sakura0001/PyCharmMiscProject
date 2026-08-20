"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE LANGUAGE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE LANGUAGE``.  CREATE LANGUAGE is a PostgreSQL catalog-level DDL
statement with 2 official synopsis branches: the full handler form
(``CREATE [OR REPLACE] [TRUSTED] [PROCEDURAL] LANGUAGE name HANDLER
call_handler [INLINE inline_handler] [VALIDATOR valfunction]``) and the
obsolete handlerless form (``CREATE [OR REPLACE] [TRUSTED] [PROCEDURAL]
LANGUAGE name``) which is interpreted as ``CREATE EXTENSION`` for backward
compatibility with old dump files.

The statement touches the ``pg_catalog.pg_language`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.  CREATE LANGUAGE does
not create tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.

Each local obligation becomes exactly one regress program.  The 42
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


class CreateLanguageFactorLoopError(ValueError):
    """Raised when a frozen CREATE LANGUAGE obligation input drifts."""


@dataclass(frozen=True)
class CreateLanguageGrammarAction:
    """One official target action form of the CREATE LANGUAGE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateLanguageFactorObligation:
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
class CreateLanguageFactorCase:
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
class CreateLanguageFactorLoopPlan:
    obligations: tuple[CreateLanguageFactorObligation, ...]
    cases: tuple[CreateLanguageFactorCase, ...]
    delegated: tuple[CreateLanguageFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createlanguage.html).
_BRANCH_WITH_HANDLER = "branch_1"
_BRANCH_HANDLERLESS = "branch_2"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createlanguage"

# A representative with_handler action used as the baseline consumer
# for canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "with_handler"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_WITH_HANDLER: "with_handler",
    _BRANCH_HANDLERLESS: "handlerless_legacy",
}

# Grammar actions that always fail (obsolete handlerless form cannot
# resolve a custom language name to an extension).
_GRM_FAILURE_ACTIONS = frozenset({"handlerless_legacy"})


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateLanguageFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "exists"),
        ("target_object_state", "exists_conflict"),
        ("handler_clause", "handler_missing"),
        ("handler_name_shape", "missing_function"),
        ("dependency_state", "missing_handler"),
        ("dependency_state", "missing_validator"),
        ("dependency_state", "wrong_signature"),
        ("privilege_context", "non_superuser"),
        ("ownership_boundary", "non_superuser"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("statement_branch", "branch_2"),
        ("name_shape", "schema_qualified"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_language_provisional",
    ),
    ("target_object_state", "exists"): (
        "42710",
        "duplicate_language_provisional",
    ),
    ("target_object_state", "exists_conflict"): (
        "42710",
        "duplicate_language_provisional",
    ),
    ("handler_clause", "handler_missing"): (
        "42804",
        "missing_handler_dependency_provisional",
    ),
    ("handler_name_shape", "missing_function"): (
        "42804",
        "missing_handler_dependency_provisional",
    ),
    ("dependency_state", "missing_handler"): (
        "42804",
        "missing_handler_dependency_provisional",
    ),
    ("dependency_state", "missing_validator"): (
        "42804",
        "missing_validator_dependency_provisional",
    ),
    ("dependency_state", "wrong_signature"): (
        "42804",
        "wrong_signature_dependency_provisional",
    ),
    ("privilege_context", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("ownership_boundary", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "invalid_language_definition_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42804",
        "invalid_language_definition_provisional",
    ),
    ("statement_branch", "branch_2"): (
        "42704",
        "handlerless_extension_resolution_failure_provisional",
    ),
    ("name_shape", "schema_qualified"): (
        "42601",
        "invalid_language_definition_provisional",
    ),
    ("target_form", "handlerless_legacy"): (
        "42704",
        "handlerless_extension_resolution_failure_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateLanguageGrammarAction, ...]
):
    """Freeze every CREATE LANGUAGE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "with_handler",
            _BRANCH_WITH_HANDLER,
            "CREATE [OR REPLACE] [TRUSTED] [PROCEDURAL] LANGUAGE name "
            "HANDLER call_handler [INLINE inline_handler] "
            "[VALIDATOR valfunction]",
            "synopsis-with-handler",
        ),
        (
            "handlerless_legacy",
            _BRANCH_HANDLERLESS,
            "CREATE [OR REPLACE] [TRUSTED] [PROCEDURAL] LANGUAGE name",
            "synopsis-handlerless-legacy",
        ),
    )
    actions = [
        CreateLanguageGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise CreateLanguageFactorLoopError(
            "create language action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateLanguageFactorObligation]
):
    rows: list[CreateLanguageFactorObligation] = []
    for action in _load_grammar_actions():
        is_failure = action.action_id in _GRM_FAILURE_ACTIONS
        rows.append(
            CreateLanguageFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CLANG-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_form|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_form",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 2:
        raise CreateLanguageFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateLanguageFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_language")
    if len(catalog_rows) != 42:
        raise CreateLanguageFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateLanguageFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateLanguageFactorObligation(
                ordinal=0,
                obligation_id=f"CLANG-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateLanguageFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-language-factor-obligations-v1\n"
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
    "with_handler": _BRANCH_WITH_HANDLER,
    "handlerless_legacy": _BRANCH_HANDLERLESS,
}

# Dense baseline defaults (all positive T1-T6 factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_WITH_HANDLER,
    "target_object_state": "absent",
    "expected_status": "success",
    "or_replace_clause": "absent",
    "trusted_clause": "absent",
    "handler_clause": "handler_exists",
    "inline_clause": "absent",
    "validator_clause": "absent",
    "privilege_context": "superuser",
    "name_shape": "plain_identifier",
    "handler_name_shape": "plain_function",
    "dependency_state": "ready",
    "superuser_requirement": "superuser_available",
    "invalid_combination": "none",
    "ownership_boundary": "superuser",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive related factors from T1-T5 values to keep baselines consistent.

    The T5 boundary factors (ownership_boundary, invalid_combination)
    describe the same scenario as their T1-T4 counterparts.  When the
    primary factor is a T1-T4 value, the corresponding T5 value is
    derived; when the primary is a T5 value, the T1-T4 counterpart is
    derived.  This keeps the baseline assignment self-consistent so the
    render produces SQL that reaches the intended boundary.
    """

    # --- or_replace_clause ↔ target_object_state ---
    or_replace = a.get("or_replace_clause", "absent")
    if or_replace == "present_replace_existing":
        a["target_object_state"] = "exists"
    elif or_replace == "present_replace_new":
        a["target_object_state"] = "absent"

    # --- handler_clause ↔ dependency_state ↔ handler_name_shape ---
    handler = a.get("handler_clause", "handler_exists")
    dep = a.get("dependency_state", "ready")
    hns = a.get("handler_name_shape", "plain_function")

    if handler == "handler_missing":
        a["dependency_state"] = "missing_handler"
    if dep == "missing_handler":
        a["handler_clause"] = "handler_missing"
    elif dep == "missing_validator":
        a["validator_clause"] = "present"
    elif dep == "wrong_signature":
        a["handler_clause"] = "handler_exists"

    if hns == "missing_function":
        a["handler_clause"] = "handler_missing"
        a["dependency_state"] = "missing_handler"

    # --- privilege_context ↔ ownership_boundary ↔ superuser_requirement ---
    priv = a.get("privilege_context", "superuser")
    owner = a.get("ownership_boundary", "superuser")
    if priv == "non_superuser":
        a["ownership_boundary"] = "non_superuser"
        a["superuser_requirement"] = "superuser_required_only"
    if owner == "non_superuser":
        a["privilege_context"] = "non_superuser"
        a["superuser_requirement"] = "superuser_required_only"

    # --- statement_branch=branch_2 → handlerless (no handler) ---
    sb = a.get("statement_branch", "branch_1")
    if sb == "branch_2":
        a["handler_clause"] = "handler_missing"

    # --- expected_status=failure → duplicate scenario ---
    es = a.get("expected_status", "success")
    if es == "failure":
        a["target_object_state"] = "exists"
        a["or_replace_clause"] = "absent"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateLanguageFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
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
        raise CreateLanguageFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateLanguageFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateLanguageFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_language_factor_loop_plan(
    repository_root: Path,
) -> CreateLanguageFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_language_factor_loop_obligations(root)
    cases: list[CreateLanguageFactorCase] = []
    delegated: list[CreateLanguageFactorObligation] = []
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
            CreateLanguageFactorCase(
                ordinal=ordinal,
                case_id=f"CREATELANGUAGE{ordinal:05d}",
                sql_filename=f"CREATELANGUAGE{ordinal:05d}.sql",
                object_prefix=f"createlanguage_{ordinal:05d}_",
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
    plan = CreateLanguageFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 44 or len(plan.delegated) != 0:
        raise CreateLanguageFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 44:
        raise CreateLanguageFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 44:
        raise CreateLanguageFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_language_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateLanguageFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateLanguageFactorObligation(
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
    if len(rows) != 44:
        raise CreateLanguageFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateLanguageFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 42}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateLanguageFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateLanguageFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 44:
        raise CreateLanguageFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateLanguageFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateLanguageFactorLoopError",
    "CreateLanguageGrammarAction",
    "CreateLanguageFactorObligation",
    "CreateLanguageFactorCase",
    "CreateLanguageFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_language_factor_loop_obligations",
    "build_create_language_factor_loop_plan",
    "_obligation_multiset_sha256",
]
