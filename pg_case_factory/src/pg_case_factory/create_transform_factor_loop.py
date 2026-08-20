"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TRANSFORM.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TRANSFORM``.  The statement has one official synopsis branch:
``CREATE [ OR REPLACE ] TRANSFORM FOR type_name LANGUAGE lang_name
( FROM SQL WITH FUNCTION fn [ (argtype [, ...]) ],
  TO SQL WITH FUNCTION fn [ (argtype [, ...]) ] )`` with two optional
direction clauses (FROM SQL, TO SQL).  The statement requires USAGE on
the type, USAGE on the language, and EXECUTE on the functions, and
touches the ``pg_catalog.pg_transform`` catalog row (not a ``pg_class``
relation), so column/table/relation coverage is ``not_applicable`` and
there is no ``INV`` block.

CREATE TRANSFORM does not create tables, so the bookend (DROP TABLE IF
EXISTS) is never emitted.  Cleanup uses ``DROP TRANSFORM IF EXISTS``
plus ``DROP TYPE`` / ``DROP FUNCTION`` as needed.

Each local obligation becomes exactly one regress program.  The 58
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


class CreateTransformFactorLoopError(ValueError):
    """Raised when a frozen CREATE TRANSFORM obligation input drifts."""


@dataclass(frozen=True)
class CreateTransformGrammarAction:
    """One official target action form of the CREATE TRANSFORM synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTransformFactorObligation:
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
class CreateTransformFactorCase:
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
class CreateTransformFactorLoopPlan:
    obligations: tuple[CreateTransformFactorObligation, ...]
    cases: tuple[CreateTransformFactorCase, ...]
    delegated: tuple[CreateTransformFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createtransform.html).
_BRANCH_DEFINE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtransform"

_REPRESENTATIVE_ACTION = "define_transform"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    if row.factor == "statement_branch":
        if row.value == "branch_create_or_replace_transform":
            return "define_or_replace_transform"
        return "define_transform"
    if row.factor == "object_state":
        if row.value == "exists":
            return "define_duplicate"
        return "define_transform"
    if row.factor == "expected_status":
        if row.value == "failure":
            return "define_duplicate"
        return "define_transform"
    if row.factor == "or_replace_clause":
        if row.value == "present":
            return "define_or_replace_transform"
        return "define_transform"
    if row.factor == "transform_direction":
        if row.value == "only_from_sql":
            return "define_only_from_sql"
        if row.value == "only_to_sql":
            return "define_only_to_sql"
        return "define_transform"
    if row.factor == "function_existence":
        if row.value == "some_functions_missing":
            return "define_missing_function"
        return "define_transform"
    if row.factor == "type_existence":
        if row.value == "type_not_exists":
            return "define_missing_type"
        return "define_transform"
    if row.factor == "language_existence":
        if row.value == "language_not_exists":
            return "define_missing_language"
        return "define_transform"
    if row.factor == "type_name_shape":
        if row.value == "nonexistent_name":
            return "define_nonexistent_type_name"
        if row.value == "quoted_id":
            return "define_quoted_type_name"
        if row.value == "schema_qualified_id":
            return "define_schema_qualified_type"
        return "define_transform"
    if row.factor == "language_name_shape":
        if row.value == "nonexistent_name":
            return "define_nonexistent_language_name"
        return "define_transform"
    if row.factor == "function_name_shape":
        if row.value == "nonexistent_name":
            return "define_nonexistent_function_name"
        if row.value == "schema_qualified_id":
            return "define_schema_qualified_function"
        return "define_transform"
    if row.factor == "privilege_on_type":
        if row.value == "no_usage_privilege":
            return "define_insufficient_type_priv"
        return "define_transform"
    if row.factor == "privilege_on_language":
        if row.value == "no_usage":
            return "define_insufficient_language_priv"
        return "define_transform"
    if row.factor == "privilege_on_function":
        if row.value == "no_execute_privilege":
            return "define_insufficient_function_priv"
        return "define_transform"
    if row.factor == "type_dependency":
        if row.value == "type_missing":
            return "define_missing_type"
        return "define_transform"
    if row.factor == "language_dependency":
        if row.value == "language_missing":
            return "define_missing_language"
        return "define_transform"
    if row.factor == "duplicate_transform":
        if row.value == "existing_transform_without_or_replace":
            return "define_duplicate"
        return "define_transform"
    if row.factor == "nonexistent_type":
        if row.value == "type_missing":
            return "define_missing_type"
        return "define_transform"
    if row.factor == "nonexistent_language":
        if row.value == "language_missing":
            return "define_missing_language"
        return "define_transform"
    if row.factor == "nonexistent_function":
        if row.value == "function_missing":
            return "define_missing_function"
        return "define_transform"
    if row.factor == "insufficient_type_privilege":
        if row.value == "lacks_privilege":
            return "define_insufficient_type_priv"
        return "define_transform"
    if row.factor == "insufficient_language_privilege":
        if row.value == "lacks_privilege":
            return "define_insufficient_language_priv"
        return "define_transform"
    if row.factor == "insufficient_function_privilege":
        if row.value == "lacks_privilege":
            return "define_insufficient_function_priv"
        return "define_transform"
    if row.factor == "function_signature_mismatch":
        if row.value == "signature_mismatch":
            return "define_signature_mismatch"
        return "define_transform"
    if row.factor == "verification_mode":
        if row.value == "error_assertion":
            return "define_error_assertion"
        return "define_transform"
    if row.factor == "cleanup_mode":
        if row.value == "drop_type":
            return "define_drop_type_cleanup"
        if row.value == "drop_function":
            return "define_drop_function_cleanup"
        return "define_transform"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("duplicate_transform", "existing_transform_without_or_replace"),
        ("type_existence", "type_not_exists"),
        ("type_dependency", "type_missing"),
        ("nonexistent_type", "type_missing"),
        ("type_name_shape", "nonexistent_name"),
        ("language_existence", "language_not_exists"),
        ("language_dependency", "language_missing"),
        ("nonexistent_language", "language_missing"),
        ("language_name_shape", "nonexistent_name"),
        ("function_existence", "some_functions_missing"),
        ("nonexistent_function", "function_missing"),
        ("function_name_shape", "nonexistent_name"),
        ("function_signature_mismatch", "signature_mismatch"),
        ("privilege_on_type", "no_usage_privilege"),
        ("insufficient_type_privilege", "lacks_privilege"),
        ("privilege_on_language", "no_usage"),
        ("insufficient_language_privilege", "lacks_privilege"),
        ("privilege_on_function", "no_execute_privilege"),
        ("insufficient_function_privilege", "lacks_privilege"),
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
    ("duplicate_transform", "existing_transform_without_or_replace"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("type_existence", "type_not_exists"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("type_dependency", "type_missing"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("nonexistent_type", "type_missing"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("type_name_shape", "nonexistent_name"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("language_existence", "language_not_exists"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("language_dependency", "language_missing"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("nonexistent_language", "language_missing"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("language_name_shape", "nonexistent_name"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("function_existence", "some_functions_missing"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("nonexistent_function", "function_missing"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("function_name_shape", "nonexistent_name"): (
        "42883",
        "undefined_function_provisional",
    ),
    ("function_signature_mismatch", "signature_mismatch"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("privilege_on_type", "no_usage_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_type_privilege", "lacks_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_on_language", "no_usage"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_language_privilege", "lacks_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_on_function", "no_execute_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_function_privilege", "lacks_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateTransformGrammarAction, ...]:
    """Freeze every CREATE TRANSFORM synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "define_transform",
            _BRANCH_DEFINE,
            "CREATE [ OR REPLACE ] TRANSFORM FOR type_name "
            "LANGUAGE lang_name ( FROM SQL WITH FUNCTION fn, "
            "TO SQL WITH FUNCTION fn )",
            "synopsis-define-transform",
        ),
    )
    actions = [
        CreateTransformGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateTransformFactorLoopError("action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateTransformFactorObligation]
):
    rows: list[CreateTransformFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTransformFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CTR-GRM|{action.grammar_branch_id}|"
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
        raise CreateTransformFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTransformFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_transform")
    if len(catalog_rows) != 58:
        raise CreateTransformFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateTransformFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTransformFactorObligation(
                ordinal=0,
                obligation_id=f"CTR-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateTransformFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-transform-factor-obligations-v1\n"
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
    "statement_branch": "branch_create_transform",
    "object_state": "not_exists",
    "expected_status": "success",
    "or_replace_clause": "omitted",
    "transform_direction": "both_from_and_to_sql",
    "function_existence": "all_functions_exist",
    "type_existence": "type_exists",
    "language_existence": "language_exists",
    "type_name_shape": "simple_id",
    "language_name_shape": "simple_id",
    "function_name_shape": "simple_id",
    "privilege_on_type": "owner_with_usage",
    "privilege_on_language": "has_usage",
    "privilege_on_function": "owner_with_execute",
    "type_dependency": "type_exists_and_valid",
    "language_dependency": "language_exists_and_valid",
    "duplicate_transform": "no_conflict",
    "nonexistent_type": "type_exists",
    "nonexistent_language": "language_exists",
    "nonexistent_function": "function_exists",
    "insufficient_type_privilege": "has_privilege",
    "insufficient_language_privilege": "has_privilege",
    "insufficient_function_privilege": "has_privilege",
    "function_signature_mismatch": "signature_matches",
    "verification_mode": "catalog_query_pg_transform",
    "cleanup_mode": "drop_transform",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors from the primary value.

    statement_branch cluster: statement_branch <-> or_replace_clause
    type cluster: type_existence <-> type_dependency <-> nonexistent_type <-> type_name_shape=nonexistent_name
    language cluster: language_existence <-> language_dependency <-> nonexistent_language <-> language_name_shape=nonexistent_name
    function cluster: function_existence <-> nonexistent_function <-> function_name_shape=nonexistent_name
    type privilege cluster: privilege_on_type <-> insufficient_type_privilege
    language privilege cluster: privilege_on_language <-> insufficient_language_privilege
    function privilege cluster: privilege_on_function <-> insufficient_function_privilege
    duplicate cluster: object_state=exists + or_replace_clause=omitted <-> duplicate_transform
    """

    # --- statement_branch / or_replace_clause cluster ---
    sb_orig = a.get("statement_branch", "branch_create_transform")
    orc_orig = a.get("or_replace_clause", "omitted")
    if (
        sb_orig == "branch_create_or_replace_transform"
        or orc_orig == "present"
    ):
        a["statement_branch"] = "branch_create_or_replace_transform"
        a["or_replace_clause"] = "present"
    else:
        a["statement_branch"] = "branch_create_transform"
        a["or_replace_clause"] = "omitted"

    # --- type cluster ---
    te = a.get("type_existence", "type_exists")
    td = a.get("type_dependency", "type_exists_and_valid")
    nt = a.get("nonexistent_type", "type_exists")
    tns = a.get("type_name_shape", "simple_id")
    type_missing = (
        te == "type_not_exists"
        or td == "type_missing"
        or nt == "type_missing"
        or tns == "nonexistent_name"
    )
    if type_missing:
        a["type_existence"] = "type_not_exists"
        a["type_dependency"] = "type_missing"
        a["nonexistent_type"] = "type_missing"
        a["type_name_shape"] = "nonexistent_name"
    else:
        a["type_existence"] = "type_exists"
        a["type_dependency"] = "type_exists_and_valid"
        a["nonexistent_type"] = "type_exists"

    # --- language cluster ---
    le = a.get("language_existence", "language_exists")
    ld = a.get("language_dependency", "language_exists_and_valid")
    nl = a.get("nonexistent_language", "language_exists")
    lns = a.get("language_name_shape", "simple_id")
    lang_missing = (
        le == "language_not_exists"
        or ld == "language_missing"
        or nl == "language_missing"
        or lns == "nonexistent_name"
    )
    if lang_missing:
        a["language_existence"] = "language_not_exists"
        a["language_dependency"] = "language_missing"
        a["nonexistent_language"] = "language_missing"
        a["language_name_shape"] = "nonexistent_name"
    else:
        a["language_existence"] = "language_exists"
        a["language_dependency"] = "language_exists_and_valid"
        a["nonexistent_language"] = "language_exists"

    # --- function cluster ---
    fe = a.get("function_existence", "all_functions_exist")
    nf = a.get("nonexistent_function", "function_exists")
    fns = a.get("function_name_shape", "simple_id")
    func_missing = (
        fe == "some_functions_missing"
        or nf == "function_missing"
        or fns == "nonexistent_name"
    )
    if func_missing:
        a["function_existence"] = "some_functions_missing"
        a["nonexistent_function"] = "function_missing"
        a["function_name_shape"] = "nonexistent_name"
    else:
        a["function_existence"] = "all_functions_exist"
        a["nonexistent_function"] = "function_exists"

    # --- type privilege cluster ---
    pot = a.get("privilege_on_type", "owner_with_usage")
    itp = a.get("insufficient_type_privilege", "has_privilege")
    if pot == "no_usage_privilege" or itp == "lacks_privilege":
        a["privilege_on_type"] = "no_usage_privilege"
        a["insufficient_type_privilege"] = "lacks_privilege"
    else:
        a["insufficient_type_privilege"] = "has_privilege"

    # --- language privilege cluster ---
    pol = a.get("privilege_on_language", "has_usage")
    ilp = a.get("insufficient_language_privilege", "has_privilege")
    if pol == "no_usage" or ilp == "lacks_privilege":
        a["privilege_on_language"] = "no_usage"
        a["insufficient_language_privilege"] = "lacks_privilege"
    else:
        a["insufficient_language_privilege"] = "has_privilege"

    # --- function privilege cluster ---
    pof = a.get("privilege_on_function", "owner_with_execute")
    ifp = a.get("insufficient_function_privilege", "has_privilege")
    if pof == "no_execute_privilege" or ifp == "lacks_privilege":
        a["privilege_on_function"] = "no_execute_privilege"
        a["insufficient_function_privilege"] = "lacks_privilege"
    else:
        a["insufficient_function_privilege"] = "has_privilege"

    # --- duplicate cluster ---
    os_state = a.get("object_state", "not_exists")
    orc = a.get("or_replace_clause", "omitted")
    dt = a.get("duplicate_transform", "no_conflict")
    if dt == "existing_transform_without_or_replace":
        a["object_state"] = "exists"
        a["or_replace_clause"] = "omitted"
        a["statement_branch"] = "branch_create_transform"
    elif os_state == "exists" and orc == "omitted":
        a["duplicate_transform"] = "existing_transform_without_or_replace"
    else:
        a["duplicate_transform"] = "no_conflict"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateTransformFactorObligation,
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
        raise CreateTransformFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTransformFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateTransformFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_transform_factor_loop_plan(
    repository_root: Path,
) -> CreateTransformFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = (
        compile_create_transform_factor_loop_obligations(root)
    )
    cases: list[CreateTransformFactorCase] = []
    delegated: list[CreateTransformFactorObligation] = []
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
            CreateTransformFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETRANSFORM{ordinal:05d}",
                sql_filename=(
                    f"CREATETRANSFORM{ordinal:05d}.sql"
                ),
                object_prefix=(
                    f"createtransform_{ordinal:05d}_"
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
    plan = CreateTransformFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 59 or len(plan.delegated) != 0:
        raise CreateTransformFactorLoopError(
            "factor loop plan count drift"
        )
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 59
    ):
        raise CreateTransformFactorLoopError(
            "local obligation mapping drift"
        )
    if (
        len({row.sql_filename for row in plan.cases}) != 59
    ):
        raise CreateTransformFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_create_transform_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTransformFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTransformFactorObligation(
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
    if len(rows) != 59:
        raise CreateTransformFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTransformFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 58}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTransformFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTransformFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 59:
        raise CreateTransformFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateTransformFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateTransformFactorLoopError",
    "CreateTransformGrammarAction",
    "CreateTransformFactorObligation",
    "CreateTransformFactorCase",
    "CreateTransformFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_transform_factor_loop_obligations",
    "build_create_transform_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
