"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DO.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``DO`` (execute an anonymous code block).  The statement has a single
official synopsis branch: ``DO [ LANGUAGE lang_name ] code`` where
``code`` is a string literal (typically ``$$ ... $$``) containing
PL/pgSQL.  ``DO`` is a session/utility statement that executes an
anonymous code block at runtime; it creates no persistent catalog row
and no table, so column/table/relation coverage is ``not_applicable``
and there is no ``INV`` block.  The bookend (DROP TABLE IF EXISTS) is
never emitted because no case creates a TABLE.

Each local obligation becomes exactly one regress program.  The 45
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


class DoFactorLoopError(ValueError):
    """Raised when a frozen DO obligation input drifts."""


@dataclass(frozen=True)
class DoGrammarAction:
    """One official target action form of the DO synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class DoFactorObligation:
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
class DoFactorCase:
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
class DoFactorLoopPlan:
    obligations: tuple[DoFactorObligation, ...]
    cases: tuple[DoFactorCase, ...]
    delegated: tuple[DoFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-do.html).
_BRANCH_DEFINE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-do"

_REPRESENTATIVE_ACTION = "do_statement"

_ABBREV = "DO"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    if row.factor == "expected_status":
        if row.value == "failure":
            return "do_failure"
        return "do_statement"
    if row.factor == "target_state":
        if row.value == "wrong_object_type":
            return "do_semantic_error"
        return "do_statement"
    if row.factor == "invalid_combination":
        if row.value == "syntax_valid_semantic_error":
            return "do_semantic_error"
        if row.value == "object_type_mismatch":
            return "do_semantic_error"
        return "do_statement"
    if row.factor == "privilege_context":
        if row.value == "insufficient_privilege":
            return "do_insufficient_priv"
        return "do_statement"
    if row.factor == "resource_boundary":
        if row.value == "missing_file_or_library":
            return "do_resource_error"
        return "do_statement"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
# The matrix ``failure_when`` clause is ``expected_status == failure``;
# the single pair below is the only canonical-loop failure trigger.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# Loop failures use the RAISE EXCEPTION default (P0001).  Extension
# crossed-negative pairs are also listed here so the extension module
# can resolve provisional sqlstates without a second lookup table.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "P0001",
        "raise_exception_provisional",
    ),
    ("target_state", "wrong_object_type"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "P0001",
        "raise_exception_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("resource_boundary", "missing_file_or_library"): (
        "58P01",
        "undefined_file_provisional",
    ),
}


def _load_grammar_actions() -> tuple[DoGrammarAction, ...]:
    """Freeze every DO synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "do_statement",
            _BRANCH_DEFINE,
            "DO [ LANGUAGE lang_name ] code",
            "synopsis-do",
        ),
    )
    actions = [
        DoGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise DoFactorLoopError("do action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[DoFactorObligation]:
    rows: list[DoFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            DoFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"{_ABBREV}-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_form|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_form",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise DoFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DoFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("do")
    if len(catalog_rows) != 45:
        raise DoFactorLoopError("canonical obligation count drift")
    rows: list[DoFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            DoFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"{_ABBREV}-SFV|{row.row_id}|{consumer}"
                ),
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
    rows: tuple[DoFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"do-factor-obligations-v1\n")
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


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "expected_status": "success",
    "target_state": "target_exists",
    "option_shape": "minimal",
    "execution_mode": "metadata_only",
    "target_name_shape": "plain_identifier",
    "input_output_shape": "none",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "resource_boundary": "small_relation",
    "verification_mode": "catalog_query",
    "cleanup_mode": "rollback",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive expected_status from the failure count.

    DO has no cross-factor overlap clusters (unlike CREATE TEXT SEARCH
    PARSER's headline/privilege/function/duplicate clusters).  The only
    derived factor is ``expected_status``, which mirrors whether any
    canonical failure pair is present.
    """

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: DoFactorObligation,
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
        raise DoFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: DoFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise DoFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_do_factor_loop_plan(
    repository_root: Path,
) -> DoFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_do_factor_loop_obligations(root)
    cases: list[DoFactorCase] = []
    delegated: list[DoFactorObligation] = []
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
            DoFactorCase(
                ordinal=ordinal,
                case_id=f"DO{ordinal:05d}",
                sql_filename=f"DO{ordinal:05d}.sql",
                object_prefix=f"do_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(
                    obligation
                ),
                execution_profile="serial_sql",
            )
        )
    plan = DoFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 46 or len(plan.delegated) != 0:
        raise DoFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 46
    ):
        raise DoFactorLoopError("local obligation mapping drift")
    if (
        len({row.sql_filename for row in plan.cases}) != 46
    ):
        raise DoFactorLoopError("duplicate SQL filename")
    return plan


def compile_do_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DoFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        DoFactorObligation(
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
        raise DoFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DoFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 45}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DoFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DoFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 46:
        raise DoFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DoFactorLoopError("unknown obligation disposition")
    return rows


_PLAN_CACHE: dict[Path, DoFactorLoopPlan] = {}


def _build_do_factor_plan_lazily(
    repository_root: Path,
) -> DoFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_do_factor_loop_plan(root)
    return _PLAN_CACHE[root]


__all__ = [
    "DoFactorLoopError",
    "DoGrammarAction",
    "DoFactorObligation",
    "DoFactorCase",
    "DoFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_do_factor_loop_obligations",
    "build_do_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
    "_build_do_factor_plan_lazily",
]
