"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TEXT SEARCH TEMPLATE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TEXT SEARCH TEMPLATE``.  The statement has a single official
synopsis branch: ``CREATE TEXT SEARCH TEMPLATE name ( [ INIT =
init_function , ] LEXIZE = lexize_function )`` with two function slots
(one required ``LEXIZE``, one optional ``INIT``).  The statement requires
superuser privilege and touches the ``pg_catalog.pg_ts_template`` catalog
row (not a ``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.

CREATE TEXT SEARCH TEMPLATE does not create tables, so the bookend (DROP
TABLE IF EXISTS) is never emitted.  Cleanup uses ``DROP TEXT SEARCH
TEMPLATE IF EXISTS`` plus ``DROP FUNCTION IF EXISTS``.

Each local obligation becomes exactly one regress program.  The 37
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


class CreateTextSearchTemplateFactorLoopError(ValueError):
    """Raised when a frozen CREATE TEXT SEARCH TEMPLATE obligation input drifts."""


@dataclass(frozen=True)
class CreateTextSearchTemplateGrammarAction:
    """One official target action form of the CREATE TEXT SEARCH TEMPLATE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTextSearchTemplateFactorObligation:
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
class CreateTextSearchTemplateFactorCase:
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
class CreateTextSearchTemplateFactorLoopPlan:
    obligations: tuple[CreateTextSearchTemplateFactorObligation, ...]
    cases: tuple[CreateTextSearchTemplateFactorCase, ...]
    delegated: tuple[CreateTextSearchTemplateFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createtstemplate.html).
_BRANCH_DEFINE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtstemplate"

_REPRESENTATIVE_ACTION = "define_template"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    if row.factor == "statement_branch":
        return "define_template"
    if row.factor == "object_state":
        if row.value == "exists":
            return "define_duplicate"
        return "define_template"
    if row.factor == "expected_status":
        if row.value == "failure":
            return "define_duplicate"
        return "define_template"
    if row.factor == "init_clause":
        if row.value == "specified":
            return "define_with_init"
        return "define_template"
    if row.factor == "function_existence":
        if row.value == "some_functions_missing":
            return "define_missing_function"
        return "define_template"
    if row.factor == "privilege_requirement":
        if row.value == "non_superuser":
            return "define_insufficient_priv"
        return "define_template"
    if row.factor == "template_name_shape":
        if row.value == "duplicate_name":
            return "define_duplicate"
        if row.value == "invalid_name":
            return "define_invalid_name"
        if row.value == "reserved_word_as_name":
            return "define_reserved_name"
        if row.value == "quoted_id":
            return "define_quoted_name"
        if row.value == "schema_qualified_id":
            return "define_schema_qualified"
        return "define_template"
    if row.factor == "function_name_shape":
        if row.value == "nonexistent_name":
            return "define_nonexistent_fn"
        return "define_template"
    if row.factor == "privilege_level":
        if row.value == "non_superuser":
            return "define_insufficient_priv"
        return "define_template"
    if row.factor == "function_dependency":
        if row.value == "function_missing":
            return "define_missing_function"
        return "define_template"
    if row.factor == "duplicate_template_name":
        if row.value == "same_name_conflict":
            return "define_duplicate"
        return "define_template"
    if row.factor == "nonexistent_function":
        if row.value == "function_missing":
            return "define_missing_function"
        return "define_template"
    if row.factor == "non_superuser_attempt":
        if row.value == "non_superuser_execution":
            return "define_insufficient_priv"
        return "define_template"
    if row.factor == "missing_lexize_function":
        if row.value == "lexize_missing":
            return "define_missing_function"
        return "define_template"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("duplicate_template_name", "same_name_conflict"),
        ("template_name_shape", "duplicate_name"),
        ("template_name_shape", "invalid_name"),
        ("template_name_shape", "reserved_word_as_name"),
        ("function_name_shape", "nonexistent_name"),
        ("function_dependency", "function_missing"),
        ("function_existence", "some_functions_missing"),
        ("nonexistent_function", "function_missing"),
        ("missing_lexize_function", "lexize_missing"),
        ("privilege_level", "non_superuser"),
        ("privilege_requirement", "non_superuser"),
        ("non_superuser_attempt", "non_superuser_execution"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("duplicate_template_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("template_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("template_name_shape", "invalid_name"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("template_name_shape", "reserved_word_as_name"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("function_name_shape", "nonexistent_name"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("function_dependency", "function_missing"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("function_existence", "some_functions_missing"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("nonexistent_function", "function_missing"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("missing_lexize_function", "lexize_missing"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("privilege_level", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_requirement", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("non_superuser_attempt", "non_superuser_execution"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateTextSearchTemplateGrammarAction, ...]
):
    """Freeze every CREATE TEXT SEARCH TEMPLATE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "define_template",
            _BRANCH_DEFINE,
            "CREATE TEXT SEARCH TEMPLATE name "
            "( [ INIT = init_function , ] LEXIZE = lexize_function )",
            "synopsis-define-template",
        ),
    )
    actions = [
        CreateTextSearchTemplateGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateTextSearchTemplateFactorLoopError(
            "create text search template action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateTextSearchTemplateFactorObligation]
):
    rows: list[CreateTextSearchTemplateFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTextSearchTemplateFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CTST-GRM|{action.grammar_branch_id}|"
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
        raise CreateTextSearchTemplateFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTextSearchTemplateFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_text_search_template")
    if len(catalog_rows) != 37:
        raise CreateTextSearchTemplateFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateTextSearchTemplateFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTextSearchTemplateFactorObligation(
                ordinal=0,
                obligation_id=f"CTST-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateTextSearchTemplateFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-text-search-template-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_without_init",
    "object_state": "not_exists",
    "expected_status": "success",
    "init_clause": "omitted",
    "function_existence": "all_functions_exist",
    "privilege_requirement": "superuser",
    "template_name_shape": "simple_id",
    "function_name_shape": "simple_id",
    "privilege_level": "superuser",
    "function_dependency": "all_functions_valid",
    "duplicate_template_name": "no_conflict",
    "nonexistent_function": "function_exists",
    "non_superuser_attempt": "superuser_execution",
    "missing_lexize_function": "lexize_present",
    "verification_mode": "catalog_query_pg_ts_template",
    "cleanup_mode": "drop_text_search_template",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors from the primary value.

    init cluster: statement_branch <-> init_clause
    privilege cluster: privilege_level <-> privilege_requirement <-> non_superuser_attempt
    function cluster: function_dependency <-> function_existence <-> nonexistent_function <-> missing_lexize_function
    duplicate cluster: object_state <-> duplicate_template_name <-> template_name_shape=duplicate_name
    """

    # --- init cluster (bidirectional, read-then-write) ---
    sb_orig = a.get("statement_branch", "branch_without_init")
    ic_orig = a.get("init_clause", "omitted")
    if sb_orig == "branch_with_init" or ic_orig == "specified":
        a["statement_branch"] = "branch_with_init"
        a["init_clause"] = "specified"
    else:
        a["statement_branch"] = "branch_without_init"
        a["init_clause"] = "omitted"

    # --- privilege cluster ---
    pl = a.get("privilege_level", "superuser")
    if pl == "non_superuser":
        a["privilege_requirement"] = "non_superuser"
        a["non_superuser_attempt"] = "non_superuser_execution"
    else:
        a["privilege_requirement"] = "superuser"
        a["non_superuser_attempt"] = "superuser_execution"

    # --- function dependency cluster ---
    fd = a.get("function_dependency", "all_functions_valid")
    if fd == "function_missing":
        a["function_existence"] = "some_functions_missing"
        a["nonexistent_function"] = "function_missing"
        a["missing_lexize_function"] = "lexize_missing"
    else:
        a["function_existence"] = "all_functions_exist"
        a["nonexistent_function"] = "function_exists"
        a["missing_lexize_function"] = "lexize_present"

    # --- duplicate cluster ---
    os_state = a.get("object_state", "not_exists")
    dtn = a.get("duplicate_template_name", "no_conflict")
    tns = a.get("template_name_shape", "simple_id")
    if tns == "duplicate_name":
        a["object_state"] = "exists"
        a["duplicate_template_name"] = "same_name_conflict"
    if os_state == "exists":
        a["duplicate_template_name"] = "same_name_conflict"
    if dtn == "same_name_conflict":
        a["object_state"] = "exists"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateTextSearchTemplateFactorObligation,
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
        raise CreateTextSearchTemplateFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTextSearchTemplateFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateTextSearchTemplateFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_text_search_template_factor_loop_plan(
    repository_root: Path,
) -> CreateTextSearchTemplateFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = (
        compile_create_text_search_template_factor_loop_obligations(root)
    )
    cases: list[CreateTextSearchTemplateFactorCase] = []
    delegated: list[CreateTextSearchTemplateFactorObligation] = []
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
            CreateTextSearchTemplateFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETEXTSEARCHTEMPLATE{ordinal:05d}",
                sql_filename=(
                    f"CREATETEXTSEARCHTEMPLATE{ordinal:05d}.sql"
                ),
                object_prefix=(
                    f"createtextsearchtemplate_{ordinal:05d}_"
                ),
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
    plan = CreateTextSearchTemplateFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 38 or len(plan.delegated) != 0:
        raise CreateTextSearchTemplateFactorLoopError(
            "factor loop plan count drift"
        )
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 38
    ):
        raise CreateTextSearchTemplateFactorLoopError(
            "local obligation mapping drift"
        )
    if (
        len({row.sql_filename for row in plan.cases}) != 38
    ):
        raise CreateTextSearchTemplateFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_create_text_search_template_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTextSearchTemplateFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTextSearchTemplateFactorObligation(
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
    if len(rows) != 38:
        raise CreateTextSearchTemplateFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTextSearchTemplateFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 37}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTextSearchTemplateFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTextSearchTemplateFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 38:
        raise CreateTextSearchTemplateFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateTextSearchTemplateFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateTextSearchTemplateFactorLoopError",
    "CreateTextSearchTemplateGrammarAction",
    "CreateTextSearchTemplateFactorObligation",
    "CreateTextSearchTemplateFactorCase",
    "CreateTextSearchTemplateFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_text_search_template_factor_loop_obligations",
    "build_create_text_search_template_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
