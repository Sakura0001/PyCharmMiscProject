"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER TEXT SEARCH PARSER.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER TEXT SEARCH PARSER``.  ALTER TEXT SEARCH PARSER is a PostgreSQL
text-search DDL statement with 2 official synopsis branches: RENAME TO and
SET SCHEMA.  The statement requires superuser privilege and touches the
``pg_catalog.pg_ts_parser`` catalog row (not a ``pg_class`` relation), so
column/table/relation coverage is ``not_applicable`` and there is no
``INV`` block.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no
``RISK`` obligations.

The grammar ledger is self-contained (there is no separate
``alter_text_search_parser_regress`` module): the 2 synopsis actions are
frozen inline.  The 33 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterTextSearchParserFactorLoopError(ValueError):
    """Raised when a frozen ALTER TEXT SEARCH PARSER obligation input drifts."""


@dataclass(frozen=True)
class AlterTextSearchParserGrammarAction:
    """One official target action form of the ALTER TEXT SEARCH PARSER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterTextSearchParserFactorObligation:
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
class AlterTextSearchParserFactorCase:
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
class AlterTextSearchParserFactorLoopPlan:
    obligations: tuple[AlterTextSearchParserFactorObligation, ...]
    cases: tuple[AlterTextSearchParserFactorCase, ...]
    delegated: tuple[AlterTextSearchParserFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altertsparser.html).
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_SCHEMA = "branch_set_schema"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altertsparser"

# A representative branch_rename action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.  RENAME TO
# is simple, superuser-only, and needs no schema dependency.
_REPRESENTATIVE_ACTION = "rename"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_RENAME: "rename",
    _BRANCH_SET_SCHEMA: "set_schema",
}

# alter_action value -> target action (value-dependent consumer).
_ALTER_ACTION_CONSUMER = {
    "rename": "rename",
    "set_schema": "set_schema",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, alter_action)
# are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "duplicate_new_name": "rename",
    "nonexistent_target_schema": "set_schema",
    "parser_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "schema_name_shape": "set_schema",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "schema_existence": "set_schema",
    "nonexistent_parser": _REPRESENTATIVE_ACTION,
    "non_superuser_attempt": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("nonexistent_parser", "parser_missing"),
        ("parser_name_shape", "nonexistent_name"),
        ("privilege_level", "non_superuser"),
        ("non_superuser_attempt", "non_superuser_execution"),
        ("duplicate_new_name", "same_name_conflict"),
        ("new_name_shape", "duplicate_name"),
        ("nonexistent_target_schema", "schema_not_exists"),
        ("schema_existence", "schema_not_exists"),
        ("schema_name_shape", "nonexistent_schema"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "text_search_parser_failure_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "text_search_parser_does_not_exist_provisional",
    ),
    ("nonexistent_parser", "parser_missing"): (
        "42704",
        "text_search_parser_does_not_exist_provisional",
    ),
    ("parser_name_shape", "nonexistent_name"): (
        "42704",
        "text_search_parser_does_not_exist_provisional",
    ),
    ("privilege_level", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("non_superuser_attempt", "non_superuser_execution"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("duplicate_new_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("new_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("nonexistent_target_schema", "schema_not_exists"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("schema_name_shape", "nonexistent_schema"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[AlterTextSearchParserGrammarAction, ...]
):
    """Freeze every ALTER TEXT SEARCH PARSER synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER TEXT SEARCH PARSER name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "set_schema",
            _BRANCH_SET_SCHEMA,
            "ALTER TEXT SEARCH PARSER name SET SCHEMA new_schema",
            "synopsis-set-schema",
        ),
    )
    actions = [
        AlterTextSearchParserGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise AlterTextSearchParserFactorLoopError(
            "alter text search parser action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTextSearchParserFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action":
        try:
            return _ALTER_ACTION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTextSearchParserFactorLoopError(
                f"unknown alter_action value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterTextSearchParserFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[AlterTextSearchParserFactorObligation]
):
    rows: list[AlterTextSearchParserFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterTextSearchParserFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ATSP-GRM|{action.grammar_branch_id}|"
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
        raise AlterTextSearchParserFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterTextSearchParserFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_text_search_parser")
    if len(catalog_rows) != 33:
        raise AlterTextSearchParserFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[AlterTextSearchParserFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterTextSearchParserFactorObligation(
                ordinal=0,
                obligation_id=f"ATSP-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterTextSearchParserFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-text-search-parser-factor-obligations-v1\n"
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
    "rename": _BRANCH_RENAME,
    "set_schema": _BRANCH_SET_SCHEMA,
}

# Dense baseline defaults (all positive T1-T6 factor values).  The T5
# single-value factors (nonexistent_parser, non_superuser_attempt,
# duplicate_new_name, nonexistent_target_schema) are derived from their
# T1-T4 counterparts, not crossed as axes.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_RENAME,
    "grammar_branch": _BRANCH_RENAME,
    "target_action": "rename",
    "alter_action": "rename",
    "object_state": "exists",
    "expected_status": "success",
    "duplicate_new_name": "no_conflict",
    "nonexistent_target_schema": "schema_exists",
    "parser_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "schema_name_shape": "simple_id",
    "privilege_level": "superuser",
    "schema_existence": "schema_exists",
    "nonexistent_parser": "parser_exists",
    "non_superuser_attempt": "superuser_execution",
    "verification_mode": "catalog_query_pg_ts_parser",
    "cleanup_mode": "revert_rename",
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

    os_ = a.get("object_state", "exists")
    pns = a.get("parser_name_shape", "simple_id")
    np_ = a.get("nonexistent_parser", "parser_exists")

    # nonexistent-parser cluster: object_state /
    # nonexistent_parser / parser_name_shape
    if (
        os_ == "not_exists"
        or np_ == "parser_missing"
        or pns == "nonexistent_name"
    ):
        a["object_state"] = "not_exists"
        a["nonexistent_parser"] = "parser_missing"
        a["parser_name_shape"] = "nonexistent_name"

    # non-superuser cluster: privilege_level / non_superuser_attempt
    pl = a.get("privilege_level", "superuser")
    nsa = a.get("non_superuser_attempt", "superuser_execution")
    if pl == "non_superuser" or nsa == "non_superuser_execution":
        a["privilege_level"] = "non_superuser"
        a["non_superuser_attempt"] = "non_superuser_execution"

    # rename-conflict cluster: duplicate_new_name / new_name_shape
    dnn = a.get("duplicate_new_name", "no_conflict")
    nns = a.get("new_name_shape", "simple_id")
    if dnn == "same_name_conflict" or nns == "duplicate_name":
        a["duplicate_new_name"] = "same_name_conflict"
        a["new_name_shape"] = "duplicate_name"

    # schema-not-exists cluster: nonexistent_target_schema /
    # schema_existence / schema_name_shape
    nts = a.get("nonexistent_target_schema", "schema_exists")
    se = a.get("schema_existence", "schema_exists")
    sns = a.get("schema_name_shape", "simple_id")
    if (
        nts == "schema_not_exists"
        or se == "schema_not_exists"
        or sns == "nonexistent_schema"
    ):
        a["nonexistent_target_schema"] = "schema_not_exists"
        a["schema_existence"] = "schema_not_exists"
        a["schema_name_shape"] = "nonexistent_schema"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterTextSearchParserFactorObligation,
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
    assignments["alter_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise AlterTextSearchParserFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterTextSearchParserFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterTextSearchParserFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_text_search_parser_factor_loop_plan(
    repository_root: Path,
) -> AlterTextSearchParserFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_text_search_parser_factor_loop_obligations(root)
    cases: list[AlterTextSearchParserFactorCase] = []
    delegated: list[AlterTextSearchParserFactorObligation] = []
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
            AlterTextSearchParserFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERTEXTSEARCHPARSER{ordinal:05d}",
                sql_filename=f"ALTERTEXTSEARCHPARSER{ordinal:05d}.sql",
                object_prefix=(
                    f"alter_text_search_parser_{ordinal:05d}_"
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
    plan = AlterTextSearchParserFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 35 or len(plan.delegated) != 0:
        raise AlterTextSearchParserFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 35:
        raise AlterTextSearchParserFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 35:
        raise AlterTextSearchParserFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_text_search_parser_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterTextSearchParserFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterTextSearchParserFactorObligation(
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
    if len(rows) != 35:
        raise AlterTextSearchParserFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterTextSearchParserFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 33}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterTextSearchParserFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterTextSearchParserFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 35:
        raise AlterTextSearchParserFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterTextSearchParserFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "AlterTextSearchParserFactorLoopError",
    "AlterTextSearchParserGrammarAction",
    "AlterTextSearchParserFactorObligation",
    "AlterTextSearchParserFactorCase",
    "AlterTextSearchParserFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_text_search_parser_factor_loop_obligations",
    "build_alter_text_search_parser_factor_loop_plan",
    "_obligation_multiset_sha256",
]
