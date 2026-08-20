"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE VIEW.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE VIEW``.  The statement has a single official synopsis branch:
``CREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] [ RECURSIVE ] VIEW name
[ ( column_name [, ...] ) ] [ WITH ( view_option_name [= view_option_value]
[, ... ] ) ] AS query [ WITH [ CASCADED | LOCAL ] CHECK OPTION ]`` with
optional OR REPLACE, TEMP/TEMPORARY, RECURSIVE, column list, WITH options,
and CHECK OPTION clauses.  CREATE VIEW creates a ``pg_class`` relation of
kind ``v`` (not a base table), so the bookend DROP-TABLE gate (which matches
``CREATE TABLE`` only) never fires.  Cleanup uses ``DROP VIEW IF EXISTS``
plus ``DROP TABLE IF EXISTS`` for fixture base tables.

Each local obligation becomes exactly one regress program.  The 70 canonical
``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateViewFactorLoopError(ValueError):
    """Raised when a frozen CREATE VIEW obligation input drifts."""


@dataclass(frozen=True)
class CreateViewGrammarAction:
    """One official target action form of the CREATE VIEW synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateViewFactorObligation:
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
class CreateViewFactorCase:
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
class CreateViewFactorLoopPlan:
    obligations: tuple[CreateViewFactorObligation, ...]
    cases: tuple[CreateViewFactorCase, ...]
    delegated: tuple[CreateViewFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createview.html).
_BRANCH_DEFINE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createview"

_REPRESENTATIVE_ACTION = "define_view"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    if row.factor == "statement_branch":
        if row.value == "branch_create_or_replace_view":
            return "define_or_replace_view"
        if row.value == "branch_create_temp_view":
            return "define_temp_view"
        if row.value == "branch_create_recursive_view":
            return "define_recursive_view"
        return "define_view"
    if row.factor == "object_state":
        if row.value == "already_exists":
            return "define_duplicate"
        return "define_view"
    if row.factor == "expected_status":
        if row.value == "failure":
            return "define_duplicate"
        return "define_view"
    if row.factor == "or_replace_clause":
        if row.value == "present":
            return "define_or_replace_view"
        return "define_view"
    if row.factor == "temporary_clause":
        if row.value in ("temp", "temporary"):
            return "define_temp_view"
        return "define_view"
    if row.factor == "recursive_clause":
        if row.value == "present":
            return "define_recursive_view"
        return "define_view"
    if row.factor == "column_name_list":
        if row.value == "required_for_recursive":
            return "define_recursive_view"
        return "define_view"
    if row.factor == "view_name_shape":
        if row.value == "duplicate":
            return "define_duplicate"
        return "define_view"
    if row.factor == "query_shape":
        if row.value == "merge_updatable_view":
            return "define_merge_updatable_view"
        return "define_view"
    if row.factor == "privilege_level":
        if row.value == "non_owner_no_privilege":
            return "define_insufficient_priv"
        return "define_view"
    if row.factor == "dependency_state":
        if row.value in (
            "base_table_not_exists",
            "referenced_view_not_exists",
        ):
            return "define_dependency_missing"
        return "define_view"
    if row.factor == "error_boundary":
        if row.value == "duplicate_without_or_replace":
            return "define_duplicate"
        if row.value == "or_replace_column_mismatch":
            return "define_or_replace_mismatch"
        if row.value == "recursive_without_column_list":
            return "define_recursive_without_column_list"
        if row.value == "check_option_on_recursive":
            return "define_check_option_on_recursive"
        if row.value == "base_table_not_exists":
            return "define_dependency_missing"
        if row.value == "insufficient_privilege":
            return "define_insufficient_priv"
        if row.value == "merge_view_with_rules":
            return "define_merge_with_rules"
        return "define_view"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("view_name_shape", "duplicate"),
        ("error_boundary", "duplicate_without_or_replace"),
        ("error_boundary", "or_replace_column_mismatch"),
        ("error_boundary", "recursive_without_column_list"),
        ("error_boundary", "check_option_on_recursive"),
        ("error_boundary", "base_table_not_exists"),
        ("error_boundary", "insufficient_privilege"),
        ("error_boundary", "merge_view_with_rules"),
        ("dependency_state", "base_table_not_exists"),
        ("dependency_state", "referenced_view_not_exists"),
        ("privilege_level", "non_owner_no_privilege"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P04",
        "duplicate_table_provisional",
    ),
    ("object_state", "already_exists"): (
        "42P04",
        "duplicate_table_provisional",
    ),
    ("view_name_shape", "duplicate"): (
        "42P04",
        "duplicate_table_provisional",
    ),
    ("error_boundary", "duplicate_without_or_replace"): (
        "42P04",
        "duplicate_table_provisional",
    ),
    ("error_boundary", "or_replace_column_mismatch"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("error_boundary", "recursive_without_column_list"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("error_boundary", "check_option_on_recursive"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("error_boundary", "base_table_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("error_boundary", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("error_boundary", "merge_view_with_rules"): (
        "0A000",
        "feature_not_supported_provisional",
    ),
    ("dependency_state", "base_table_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("dependency_state", "referenced_view_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateViewGrammarAction, ...]:
    """Freeze every CREATE VIEW synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "define_view",
            _BRANCH_DEFINE,
            "CREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] "
            "[ RECURSIVE ] VIEW name [ ( column_name [, ...] ) ] "
            "[ WITH ( view_option_name [= view_option_value] "
            "[, ... ] ) ] AS query "
            "[ WITH [ CASCADED | LOCAL ] CHECK OPTION ]",
            "synopsis-define-view",
        ),
    )
    actions = [
        CreateViewGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateViewFactorLoopError("create view action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateViewFactorObligation]:
    rows: list[CreateViewFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateViewFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CV-GRM|{action.grammar_branch_id}|"
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
        raise CreateViewFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateViewFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_view")
    if len(catalog_rows) != 70:
        raise CreateViewFactorLoopError("canonical obligation count drift")
    rows: list[CreateViewFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateViewFactorObligation(
                ordinal=0,
                obligation_id=f"CV-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateViewFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-view-factor-obligations-v1\n")
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
    "statement_branch": "branch_create_view",
    "object_state": "not_exists",
    "expected_status": "success",
    "or_replace_clause": "absent",
    "temporary_clause": "permanent",
    "recursive_clause": "absent",
    "with_options_clause": "absent",
    "check_option_clause": "absent",
    "column_name_list": "absent",
    "view_name_shape": "simple",
    "column_name_shape": "simple",
    "query_shape": "select_simple",
    "privilege_level": "owner",
    "dependency_state": "base_table_exists",
    "base_table_coverage": "representative_int_types",
    "error_boundary": "none",
    "verification_mode": "pg_class_query",
    "cleanup_mode": "drop_view_if_exists",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors and expected_status from T1-T5 values.

    duplicate cluster: object_state <-> view_name_shape=duplicate <-> error_boundary=duplicate_without_or_replace
    recursive cluster: recursive_clause <-> column_name_list <-> check_option_clause <-> error_boundary
    dependency cluster: dependency_state <-> error_boundary=base_table_not_exists
    privilege cluster: privilege_level <-> error_boundary=insufficient_privilege
    or_replace mismatch cluster: error_boundary=or_replace_column_mismatch
    merge cluster: error_boundary=merge_view_with_rules
    """

    eb = a.get("error_boundary", "none")

    # --- error_boundary-driven scenarios (when error_boundary is primary) ---
    if eb == "duplicate_without_or_replace":
        a["object_state"] = "already_exists"
        a["view_name_shape"] = "duplicate"
        a["or_replace_clause"] = "absent"
        a["recursive_clause"] = "absent"
    elif eb == "or_replace_column_mismatch":
        a["object_state"] = "already_exists"
        a["view_name_shape"] = "duplicate"
        a["or_replace_clause"] = "present"
        a["recursive_clause"] = "absent"
    elif eb == "recursive_without_column_list":
        a["recursive_clause"] = "present"
        a["column_name_list"] = "absent"
        a["check_option_clause"] = "absent"
        a["statement_branch"] = "branch_create_recursive_view"
    elif eb == "check_option_on_recursive":
        a["recursive_clause"] = "present"
        a["column_name_list"] = "required_for_recursive"
        a["check_option_clause"] = "cascaded"
        a["statement_branch"] = "branch_create_recursive_view"
    elif eb == "base_table_not_exists":
        a["dependency_state"] = "base_table_not_exists"
        a["recursive_clause"] = "absent"
    elif eb == "insufficient_privilege":
        a["privilege_level"] = "non_owner_no_privilege"
        a["recursive_clause"] = "absent"
    elif eb == "merge_view_with_rules":
        a["recursive_clause"] = "absent"

    # --- duplicate cluster (from object_state/view_name_shape primaries) ---
    os_state = a.get("object_state", "not_exists")
    vns = a.get("view_name_shape", "simple")
    if os_state == "already_exists" or vns == "duplicate":
        a["object_state"] = "already_exists"
        a["view_name_shape"] = "duplicate"
        if a.get("error_boundary", "none") == "none":
            a["error_boundary"] = "duplicate_without_or_replace"
        if a.get("or_replace_clause", "absent") != "present":
            a["or_replace_clause"] = "absent"
        a["recursive_clause"] = "absent"

    # --- recursive success cluster ---
    rc = a.get("recursive_clause", "absent")
    if rc == "present":
        if a.get("error_boundary", "none") == "none":
            a["column_name_list"] = "required_for_recursive"
            a["check_option_clause"] = "absent"
            a["statement_branch"] = "branch_create_recursive_view"

    # --- dependency cluster (from dependency_state primaries) ---
    ds = a.get("dependency_state", "base_table_exists")
    if ds in ("base_table_not_exists", "referenced_view_not_exists"):
        if a.get("error_boundary", "none") == "none":
            a["error_boundary"] = "base_table_not_exists"
        a["recursive_clause"] = "absent"

    # --- privilege cluster (from privilege_level primaries) ---
    pl = a.get("privilege_level", "owner")
    if pl == "non_owner_no_privilege":
        if a.get("error_boundary", "none") == "none":
            a["error_boundary"] = "insufficient_privilege"
        a["recursive_clause"] = "absent"

    # --- expected_status fallback: synthesize a concrete failure scenario
    # when the primary is expected_status=failure but no other failure factor
    # was set ---
    if (
        a.get("expected_status") == "failure"
        and a.get("error_boundary", "none") == "none"
    ):
        a["object_state"] = "already_exists"
        a["view_name_shape"] = "duplicate"
        a["error_boundary"] = "duplicate_without_or_replace"
        a["or_replace_clause"] = "absent"
        a["recursive_clause"] = "absent"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateViewFactorObligation,
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
        raise CreateViewFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateViewFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateViewFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_view_factor_loop_plan(
    repository_root: Path,
) -> CreateViewFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_view_factor_loop_obligations(root)
    cases: list[CreateViewFactorCase] = []
    delegated: list[CreateViewFactorObligation] = []
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
            CreateViewFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEVIEW{ordinal:05d}",
                sql_filename=f"CREATEVIEW{ordinal:05d}.sql",
                object_prefix=f"createview_{ordinal:05d}_",
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
    plan = CreateViewFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 71 or len(plan.delegated) != 0:
        raise CreateViewFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 71
    ):
        raise CreateViewFactorLoopError("local obligation mapping drift")
    if (
        len({row.sql_filename for row in plan.cases}) != 71
    ):
        raise CreateViewFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_view_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateViewFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateViewFactorObligation(
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
    if len(rows) != 71:
        raise CreateViewFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateViewFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 70}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateViewFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateViewFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 71:
        raise CreateViewFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateViewFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateViewFactorLoopError",
    "CreateViewGrammarAction",
    "CreateViewFactorObligation",
    "CreateViewFactorCase",
    "CreateViewFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_view_factor_loop_obligations",
    "build_create_view_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
