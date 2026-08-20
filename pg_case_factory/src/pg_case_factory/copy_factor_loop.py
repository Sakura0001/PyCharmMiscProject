"""Factor-value-loop obligation ledger for PostgreSQL 18.4 COPY.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``COPY``.  COPY is a PostgreSQL data-transfer utility statement with two
official synopsis branches: ``COPY ... FROM`` (``branch_1``, data into a
table) and ``COPY ... TO`` (``branch_2``, data out of a table or query).
The statement reads or writes a table-backed relation, so a fixture table is
created for the success / ``database_wide`` paths and the bookend (DROP
TABLE IF EXISTS as first + last executable ``;``-statement) applies to
table-creating cases.

Each local obligation becomes exactly one regress program.  The inventory
declares 13 factors / 49 factor values; together with the two GRM synopsis
obligations the ledger has 51 local cases (42 success + 9 expected-failure
plus the two GRM success cases — 41 success SFV + 2 GRM = 43 success, and
8 SFV expected-failure pairs sharing two scenarios; see
``_SFV_FAILURE_VALUES``).

The grammar ledger is self-contained (there is no separate ``copy_regress``
module): the 2 synopsis actions are frozen inline.  The 49 canonical
``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).

No-DB rendering note: ``COPY ... FROM STDIN`` and ``FROM PROGRAM`` are
avoided because the shared style gate's ``FROM`` scanner captures the bare
keyword (``stdin`` / ``program``) as a relation name.  Branch 1 (COPY FROM)
is always rendered with ``FROM '<filename>'`` (a string literal the scanner
does not capture).  ``input_output_shape=stdin_stdout`` and
``input_output_shape=query_source`` are routed to branch 2 (COPY TO STDOUT
/ COPY (query) TO STDOUT), which has no ``FROM`` target at all.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CopyFactorLoopError(ValueError):
    """Raised when a frozen COPY obligation input drifts."""


@dataclass(frozen=True)
class CopyGrammarAction:
    """One official target action form of the COPY synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CopyFactorObligation:
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
class CopyFactorCase:
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
class CopyFactorLoopPlan:
    obligations: tuple[CopyFactorObligation, ...]
    cases: tuple[CopyFactorCase, ...]
    delegated: tuple[CopyFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-copy.html).
_BRANCH_FROM = "branch_1"
_BRANCH_TO = "branch_2"

_DOC_SOURCE = "postgresql-18.4-doc:sql-copy"

# COPY has two synopsis actions.
_REPRESENTATIVE_ACTION = "copy_from"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_FROM: "copy_from",
    _BRANCH_TO: "copy_to",
}

# input_output_shape values that require branch 2 (COPY TO), because the
# branch 1 forms (FROM STDIN / FROM <query>) are either unsafe for the
# style gate or not part of the COPY FROM grammar.
_BRANCH2_INPUT_SHAPES = frozenset({"stdin_stdout", "query_source"})

# Canonical factor -> the action where the value is observable.  Most
# factors are observable through ``copy_from`` (branch 1, FROM '<file>').
_SFV_FACTOR_CONSUMER = {
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
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_state", "target_missing"),
        ("target_state", "wrong_object_type"),
        ("target_state", "database_wide"),
        ("target_name_shape", "all_or_database_wide"),
        ("privilege_context", "insufficient_privilege"),
        ("invalid_combination", "object_type_mismatch"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("resource_boundary", "locked_relation"),
        ("resource_boundary", "missing_file_or_library"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "target_missing_provisional",
    ),
    ("target_state", "target_missing"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("target_state", "wrong_object_type"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("target_state", "database_wide"): (
        "0A000",
        "unsupported_database_wide_target_provisional",
    ),
    ("target_name_shape", "all_or_database_wide"): (
        "0A000",
        "unsupported_database_wide_target_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "invalid_copy_option_provisional",
    ),
    ("resource_boundary", "locked_relation"): (
        "55P03",
        "lock_not_available_provisional",
    ),
    ("resource_boundary", "missing_file_or_library"): (
        "58P01",
        "resource_boundary_unavailable_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CopyGrammarAction, ...]:
    """Freeze every COPY synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "copy_from",
            _BRANCH_FROM,
            (
                "COPY table_name [ ( column_name [, ...] ) ] "
                "FROM { 'filename' | PROGRAM 'command' | STDIN } "
                "[ [ WITH ] ( option [, ...] ) ] [ WHERE condition ]"
            ),
            "synopsis-branch-1",
        ),
        (
            "copy_to",
            _BRANCH_TO,
            (
                "COPY { table_name [ ( column_name [, ...] ) ] | ( query ) } "
                "TO { 'filename' | PROGRAM 'command' | STDOUT } "
                "[ [ WITH ] ( option [, ...] ) ]"
            ),
            "synopsis-branch-2",
        ),
    )
    actions = [
        CopyGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise CopyFactorLoopError("copy action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CopyFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if (
        row.factor == "input_output_shape"
        and row.value in _BRANCH2_INPUT_SHAPES
    ):
        return "copy_to"
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CopyFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CopyFactorObligation]:
    rows: list[CopyFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CopyFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"COPY-GRM|{action.grammar_branch_id}|"
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
        raise CopyFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CopyFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("copy")
    if len(catalog_rows) != 49:
        raise CopyFactorLoopError("canonical obligation count drift")
    rows: list[CopyFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CopyFactorObligation(
                ordinal=0,
                obligation_id=f"COPY-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CopyFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"copy-factor-obligations-v1\n")
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
    "copy_from": _BRANCH_FROM,
    "copy_to": _BRANCH_TO,
}

# Dense baseline defaults (all positive factor values).  The default
# ``input_output_shape`` is ``server_file_or_program`` (COPY FROM '<file>')
# rather than the matrix group's ``stdin_stdout`` representative, because
# FROM STDIN is unsafe for the shared style gate (see module docstring).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_FROM,
    "grammar_branch": _BRANCH_FROM,
    "target_action": "copy_from",
    "expected_status": "success",
    "target_state": "target_exists",
    "option_shape": "minimal",
    "execution_mode": "executes_statement",
    "target_name_shape": "plain_identifier",
    "input_output_shape": "server_file_or_program",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "resource_boundary": "small_relation",
    "verification_mode": "effect_query",
    "cleanup_mode": "drop_objects",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping factors and expected_status from primary values.

    Several COPY factor values describe the same underlying scenario and
    must stay self-consistent so the rendered SQL reaches the intended
    boundary:

      * ``target_name_shape=all_or_database_wide``  <=> ``target_state=
        database_wide`` (database-wide COPY is unsupported -> 0A000).
      * ``invalid_combination=object_type_mismatch``  => ``target_state=
        wrong_object_type`` (a view, not a table -> 42809).
      * ``expected_status=failure`` needs a real failure trigger, so
        ``target_state=target_missing`` is attached.
      * ``input_output_shape`` in {stdin_stdout, query_source} forces
        ``statement_branch=branch_2`` (COPY TO), because the branch 1
        FROM-STDIN / FROM-query forms are unsafe / invalid.
    """

    ts = a.get("target_state", "target_exists")
    tns = a.get("target_name_shape", "plain_identifier")
    if ts == "database_wide" or tns == "all_or_database_wide":
        a["target_state"] = "database_wide"
        a["target_name_shape"] = "all_or_database_wide"

    if a.get("invalid_combination") == "object_type_mismatch":
        a["target_state"] = "wrong_object_type"
        a["target_name_shape"] = "plain_identifier"

    if a.get("expected_status") == "failure":
        a["target_state"] = "target_missing"
        a["target_name_shape"] = "plain_identifier"

    ios = a.get("input_output_shape", "server_file_or_program")
    if ios in _BRANCH2_INPUT_SHAPES:
        a["statement_branch"] = _BRANCH_TO
        a["grammar_branch"] = _BRANCH_TO
        a["target_action"] = "copy_to"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CopyFactorObligation,
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
        raise CopyFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CopyFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CopyFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_copy_factor_loop_plan(
    repository_root: Path,
) -> CopyFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_copy_factor_loop_obligations(root)
    cases: list[CopyFactorCase] = []
    delegated: list[CopyFactorObligation] = []
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
            CopyFactorCase(
                ordinal=ordinal,
                case_id=f"COPY{ordinal:05d}",
                sql_filename=f"COPY{ordinal:05d}.sql",
                object_prefix=f"copy_{ordinal:05d}_",
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
    plan = CopyFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 51 or len(plan.delegated) != 0:
        raise CopyFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 51:
        raise CopyFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 51:
        raise CopyFactorLoopError("duplicate SQL filename")
    return plan


def compile_copy_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CopyFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CopyFactorObligation(
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
    if len(rows) != 51:
        raise CopyFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CopyFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 49}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CopyFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CopyFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 51:
        raise CopyFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CopyFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CopyFactorLoopError",
    "CopyGrammarAction",
    "CopyFactorObligation",
    "CopyFactorCase",
    "CopyFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_copy_factor_loop_obligations",
    "build_copy_factor_loop_plan",
    "_obligation_multiset_sha256",
]
