"""Factor-value-loop obligation ledger for PostgreSQL 18.4 LOAD.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``LOAD``.  LOAD is a PostgreSQL utility statement that loads a shared
library file into the session.  The official synopsis has exactly one
branch (``LOAD 'filename'``), so there is a single ``GRM`` obligation.
The 45 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).

LOAD requires superuser privilege: a non-superuser session receives
SQLSTATE ``42501`` (``must be superuser``).  Beyond privilege denial,
LOAD has additional failure surfaces derived from the matrix rows: a
nonexistent library file (``42883`` undefined_file), a wrong-format
file that is not a shared library (``55000``), and a syntactically-valid
but semantically-invalid filename (``42601``).  The declared meta-failure
``expected_status=failure`` aliases to the privilege failure, mirroring
the checkpoint skeleton.  Seven canonical factor values reach these
failure surfaces; the remaining 38 values are success-covered.

Each local obligation becomes exactly one regress program.  There are no
``RISK`` obligations (LOAD has no ``transaction_outcome`` factor).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class LoadFactorLoopError(ValueError):
    """Raised when a frozen LOAD obligation input drifts."""


@dataclass(frozen=True)
class LoadGrammarAction:
    """One official target action form of the LOAD synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class LoadFactorObligation:
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
class LoadFactorCase:
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
class LoadFactorLoopPlan:
    obligations: tuple[LoadFactorObligation, ...]
    cases: tuple[LoadFactorCase, ...]
    delegated: tuple[LoadFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-load.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-load"

# The single representative action for all canonical factors.
_REPRESENTATIVE_ACTION = "load"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1: "load",
}

# Canonical factor -> the action where the value is observable.  Since
# LOAD has only one synopsis form, every factor observes on the single
# ``load`` action.
_SFF_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "target_state": _REPRESENTATIVE_ACTION,
    "option_shape": _REPRESENTATIVE_ACTION,
    "execution_mode": _REPRESENTATIVE_ACTION,
    "target_name_shape": _REPRESENTATIVE_ACTION,
    "input_output_shape": _REPRESENTATIVE_ACTION,
    "environment_context": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "resource_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("privilege_context", "insufficient_privilege"),
        ("resource_boundary", "missing_file_or_library"),
        ("target_state", "target_missing"),
        ("target_state", "wrong_object_type"),
        ("invalid_combination", "object_type_mismatch"),
        ("invalid_combination", "syntax_valid_semantic_error"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42501",
        "load_declared_failure",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "must_be_superuser_provisional",
    ),
    ("resource_boundary", "missing_file_or_library"): (
        "42883",
        "undefined_file_provisional",
    ),
    ("target_state", "target_missing"): (
        "42883",
        "undefined_file_provisional",
    ),
    ("target_state", "wrong_object_type"): (
        "55000",
        "wrong_elf_format_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "55000",
        "wrong_object_type_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "syntax_error_provisional",
    ),
}


def _load_grammar_actions() -> tuple[LoadGrammarAction, ...]:
    """Freeze every LOAD synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "load",
            _BRANCH_1,
            "LOAD 'filename'",
            "synopsis-load",
        ),
    )
    actions = [
        LoadGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise LoadFactorLoopError("load action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise LoadFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFF_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise LoadFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[LoadFactorObligation]:
    rows: list[LoadFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            LoadFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"LOAD-GRM|{action.grammar_branch_id}|"
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
        raise LoadFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[LoadFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("load")
    if len(catalog_rows) != 45:
        raise LoadFactorLoopError("canonical obligation count drift")
    rows: list[LoadFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            LoadFactorObligation(
                ordinal=0,
                obligation_id=f"LOAD-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[LoadFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"load-factor-obligations-v1\n")
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
    "load": _BRANCH_1,
}

# Dense baseline defaults (all positive T1-T6 factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "grammar_branch": _BRANCH_1,
    "target_action": "load",
    "expected_status": "success",
    "target_state": "database_wide",
    "option_shape": "minimal",
    "execution_mode": "server_side_io",
    "target_name_shape": "all_or_database_wide",
    "input_output_shape": "none",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "resource_boundary": "small_relation",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive expected_status and privilege_context from each other.

    LOAD's declared meta-failure (``expected_status=failure``) aliases to
    the privilege failure surface (SQLSTATE 42501), mirroring the
    checkpoint skeleton.  When ``expected_status=failure`` or
    ``privilege_context=insufficient_privilege`` is the primary, the
    other is derived so the baseline assignment is self-consistent and
    the render produces SQL that reaches the intended failure.  Other
    failure surfaces (missing file, wrong type, syntax) do not touch
    privilege_context; ``expected_status`` is re-derived downstream from
    the full failure-value count.
    """

    es = a.get("expected_status", "success")
    pc = a.get("privilege_context", "owner")
    if es == "failure" or pc == "insufficient_privilege":
        a["expected_status"] = "failure"
        a["privilege_context"] = "insufficient_privilege"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: LoadFactorObligation,
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
        raise LoadFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: LoadFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise LoadFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_load_factor_loop_plan(
    repository_root: Path,
) -> LoadFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_load_factor_loop_obligations(root)
    cases: list[LoadFactorCase] = []
    delegated: list[LoadFactorObligation] = []
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
            LoadFactorCase(
                ordinal=ordinal,
                case_id=f"LOAD{ordinal:05d}",
                sql_filename=f"LOAD{ordinal:05d}.sql",
                object_prefix=f"load_{ordinal:05d}_",
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
    plan = LoadFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 46 or len(plan.delegated) != 0:
        raise LoadFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 46:
        raise LoadFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 46:
        raise LoadFactorLoopError("duplicate SQL filename")
    return plan


def compile_load_factor_loop_obligations(
    repository_root: Path,
) -> tuple[LoadFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        LoadFactorObligation(
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
    if len(rows) != 46:
        raise LoadFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise LoadFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 45}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise LoadFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise LoadFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 46:
        raise LoadFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise LoadFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "LoadFactorLoopError",
    "LoadGrammarAction",
    "LoadFactorObligation",
    "LoadFactorCase",
    "LoadFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_load_factor_loop_obligations",
    "build_load_factor_loop_plan",
    "_obligation_multiset_sha256",
]
