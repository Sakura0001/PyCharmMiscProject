"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TEXT SEARCH DICTIONARY.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TEXT SEARCH DICTIONARY``.  CREATE TEXT SEARCH DICTIONARY is a
PostgreSQL schema-level DDL statement with a single official synopsis
branch: ``CREATE TEXT SEARCH DICTIONARY name ( TEMPLATE = template
[, option = value [, ...] ] )``.

The statement touches the ``pg_catalog.pg_ts_dict`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.  CREATE TEXT SEARCH
DICTIONARY does not create tables, so the bookend (DROP TABLE IF EXISTS)
is never emitted (table-less-exempt).

Each local obligation becomes exactly one regress program.  The 44
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


class CreateTextSearchDictionaryFactorLoopError(ValueError):
    """Raised when a frozen CREATE TEXT SEARCH DICTIONARY obligation input drifts."""


@dataclass(frozen=True)
class CreateTextSearchDictionaryGrammarAction:
    """One official target action form of the CREATE TEXT SEARCH DICTIONARY synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTextSearchDictionaryFactorObligation:
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
class CreateTextSearchDictionaryFactorCase:
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
class CreateTextSearchDictionaryFactorLoopPlan:
    obligations: tuple[CreateTextSearchDictionaryFactorObligation, ...]
    cases: tuple[CreateTextSearchDictionaryFactorCase, ...]
    delegated: tuple[CreateTextSearchDictionaryFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createtsdictionary.html).
_BRANCH_CREATE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtsdictionary"

# The single CREATE TEXT SEARCH DICTIONARY action used as the baseline
# consumer for all canonical factors.
_ACTION = "create_dictionary"

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("template_existence", "template_not_exists"),
        ("dict_name_shape", "duplicate_name"),
        ("dict_name_shape", "invalid_name"),
        ("template_name_shape", "nonexistent_name"),
        ("option_value_shape", "invalid_value"),
        ("privilege_level", "non_owner"),
        ("schema_existence", "schema_not_exists"),
        ("template_dependency", "template_missing"),
        ("duplicate_dict_name", "same_name_conflict"),
        ("nonexistent_template", "template_missing"),
        ("invalid_option_value", "invalid_value"),
        ("schema_permission_denied", "lacks_create_privilege"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "text_search_dictionary_failure_provisional",
    ),
    ("object_state", "exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("template_existence", "template_not_exists"): (
        "42704",
        "text_search_template_does_not_exist_provisional",
    ),
    ("dict_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("dict_name_shape", "invalid_name"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("template_name_shape", "nonexistent_name"): (
        "42704",
        "text_search_template_does_not_exist_provisional",
    ),
    ("option_value_shape", "invalid_value"): (
        "42601",
        "invalid_option_value_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F001",
        "invalid_schema_name_provisional",
    ),
    ("template_dependency", "template_missing"): (
        "42704",
        "text_search_template_does_not_exist_provisional",
    ),
    ("duplicate_dict_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("nonexistent_template", "template_missing"): (
        "42704",
        "text_search_template_does_not_exist_provisional",
    ),
    ("invalid_option_value", "invalid_value"): (
        "42601",
        "invalid_option_value_provisional",
    ),
    ("schema_permission_denied", "lacks_create_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}

# All 18 canonical factor names known to this statement.
_KNOWN_FACTORS = frozenset(
    {
        "statement_branch",
        "object_state",
        "expected_status",
        "template_existence",
        "option_clause",
        "option_value_type",
        "dict_name_shape",
        "template_name_shape",
        "option_value_shape",
        "privilege_level",
        "schema_existence",
        "template_dependency",
        "duplicate_dict_name",
        "nonexistent_template",
        "invalid_option_value",
        "schema_permission_denied",
        "verification_mode",
        "cleanup_mode",
    }
)


def _load_grammar_actions() -> (
    tuple[CreateTextSearchDictionaryGrammarAction, ...]
):
    """Freeze every CREATE TEXT SEARCH DICTIONARY synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_dictionary",
            _BRANCH_CREATE,
            (
                "CREATE TEXT SEARCH DICTIONARY name "
                "( TEMPLATE = template [, option = value [, ...] ] )"
            ),
            "synopsis-create-dictionary",
        ),
    )
    actions = [
        CreateTextSearchDictionaryGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateTextSearchDictionaryFactorLoopError(
            "create text search dictionary action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor not in _KNOWN_FACTORS:
        raise CreateTextSearchDictionaryFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        )
    return _ACTION


def _compile_grammar_obligations() -> (
    list[CreateTextSearchDictionaryFactorObligation]
):
    rows: list[CreateTextSearchDictionaryFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTextSearchDictionaryFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CTSD-GRM|{action.grammar_branch_id}|"
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
        raise CreateTextSearchDictionaryFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTextSearchDictionaryFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_text_search_dictionary")
    if len(catalog_rows) != 44:
        raise CreateTextSearchDictionaryFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateTextSearchDictionaryFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTextSearchDictionaryFactorObligation(
                ordinal=0,
                obligation_id=f"CTSD-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateTextSearchDictionaryFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-text-search-dictionary-factor-obligations-v1\n"
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
    "create_dictionary": _BRANCH_CREATE,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The
# T5 single-value factors (duplicate_dict_name, nonexistent_template,
# invalid_option_value, schema_permission_denied) describe the same
# scenario as their T1-T4 counterparts; they are set only when they are
# the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE,
    "object_state": "not_exists",
    "expected_status": "success",
    "template_existence": "template_exists",
    "option_clause": "only_template",
    "option_value_type": "simple_identifier",
    "dict_name_shape": "simple_id",
    "template_name_shape": "simple_id",
    "option_value_shape": "valid_value",
    "privilege_level": "schema_owner",
    "schema_existence": "schema_exists",
    "template_dependency": "template_exists_and_valid",
    "duplicate_dict_name": "no_conflict",
    "nonexistent_template": "template_exists",
    "invalid_option_value": "valid_value",
    "schema_permission_denied": "has_create_privilege",
    "verification_mode": "catalog_query_pg_ts_dict",
    "cleanup_mode": "drop_text_search_dictionary",
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

    os_ = a.get("object_state", "not_exists")
    dns = a.get("dict_name_shape", "simple_id")
    ddn = a.get("duplicate_dict_name", "")
    te = a.get("template_existence", "template_exists")
    tns = a.get("template_name_shape", "simple_id")
    nt = a.get("nonexistent_template", "")
    td = a.get("template_dependency", "template_exists_and_valid")
    pl = a.get("privilege_level", "schema_owner")
    spd = a.get("schema_permission_denied", "")
    ovs = a.get("option_value_shape", "valid_value")
    iov = a.get("invalid_option_value", "")

    # duplicate-dictionary cluster: object_state / dict_name_shape /
    # duplicate_dict_name
    if (
        os_ == "exists"
        or dns == "duplicate_name"
        or ddn == "same_name_conflict"
    ):
        a["object_state"] = "exists"
        a["dict_name_shape"] = "duplicate_name"
        a["duplicate_dict_name"] = "same_name_conflict"

    # template-missing cluster: template_existence / template_name_shape /
    # nonexistent_template / template_dependency
    if (
        te == "template_not_exists"
        or tns == "nonexistent_name"
        or nt == "template_missing"
        or td == "template_missing"
    ):
        a["template_existence"] = "template_not_exists"
        a["template_name_shape"] = "nonexistent_name"
        a["nonexistent_template"] = "template_missing"
        a["template_dependency"] = "template_missing"

    # privilege cluster: privilege_level / schema_permission_denied
    if pl == "non_owner" or spd == "lacks_create_privilege":
        a["privilege_level"] = "non_owner"
        a["schema_permission_denied"] = "lacks_create_privilege"

    # invalid-option cluster: option_value_shape / invalid_option_value
    if ovs == "invalid_value" or iov == "invalid_value":
        a["option_value_shape"] = "invalid_value"
        a["invalid_option_value"] = "invalid_value"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateTextSearchDictionaryFactorObligation,
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
        raise CreateTextSearchDictionaryFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTextSearchDictionaryFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateTextSearchDictionaryFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_text_search_dictionary_factor_loop_plan(
    repository_root: Path,
) -> CreateTextSearchDictionaryFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_text_search_dictionary_factor_loop_obligations(root)
    cases: list[CreateTextSearchDictionaryFactorCase] = []
    delegated: list[CreateTextSearchDictionaryFactorObligation] = []
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
            CreateTextSearchDictionaryFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETEXTSEARCHDICTIONARY{ordinal:05d}",
                sql_filename=f"CREATETEXTSEARCHDICTIONARY{ordinal:05d}.sql",
                object_prefix=(
                    f"createtextsearchdictionary_{ordinal:05d}_"
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
    plan = CreateTextSearchDictionaryFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 45 or len(plan.delegated) != 0:
        raise CreateTextSearchDictionaryFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 45:
        raise CreateTextSearchDictionaryFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 45:
        raise CreateTextSearchDictionaryFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_text_search_dictionary_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTextSearchDictionaryFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTextSearchDictionaryFactorObligation(
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
    if len(rows) != 45:
        raise CreateTextSearchDictionaryFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTextSearchDictionaryFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 44}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTextSearchDictionaryFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTextSearchDictionaryFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 45:
        raise CreateTextSearchDictionaryFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateTextSearchDictionaryFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateTextSearchDictionaryFactorLoopError",
    "CreateTextSearchDictionaryGrammarAction",
    "CreateTextSearchDictionaryFactorObligation",
    "CreateTextSearchDictionaryFactorCase",
    "CreateTextSearchDictionaryFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "_ACTION_BRANCH",
    "_KNOWN_FACTORS",
    "compile_create_text_search_dictionary_factor_loop_obligations",
    "build_create_text_search_dictionary_factor_loop_plan",
    "_obligation_multiset_sha256",
]
