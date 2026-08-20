"""Bounded post-coverage extension plan for CREATE TEXT SEARCH PARSER factor regress.

The baseline :mod:`create_text_search_parser_factor_loop` assigns one local
SQL program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under an
at-most-one-failure attribution policy, producing a bounded set of additional
regress programs that exercise pairwise factor interactions.

CREATE TEXT SEARCH PARSER is a catalog-row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_ts_parser`` catalog row (not a ``pg_class`` relation) is the
semantic witness target.

The extension is deterministic: given the same repository root, it always
produces the same frozen multiset SHA-256 and the same contiguous case
ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_text_search_parser_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateTextSearchParserFactorExtensionError(ValueError):
    """Raised when CREATE TEXT SEARCH PARSER extension input drifts."""


@dataclass(frozen=True)
class CreateTextSearchParserFactorExtensionCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    derivation_id: str
    derived_from_combination_group: str
    derivation_reason: str
    factor_assignment: tuple[tuple[str, str], ...]
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    is_extension: bool = True


@dataclass(frozen=True)
class CreateTextSearchParserFactorExtensionPlan:
    cases: tuple[CreateTextSearchParserFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 38
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_ts_parser",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_text_search_parser",
    "drop_function",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "exists"),
    "privilege_level": ("superuser", "non_superuser"),
}

_CORE_DEFINITION_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_without_headline",
        "branch_with_headline",
    ),
    "headline_clause": ("omitted", "specified"),
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
}

_NAMING_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_without_headline",
        "branch_with_headline",
    ),
    "headline_clause": ("omitted", "specified"),
    "parser_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "reserved_word_as_name",
        "duplicate_name",
        "invalid_name",
    ),
}

_FULL_CROSS_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_without_headline",
        "branch_with_headline",
    ),
    "headline_clause": ("omitted", "specified"),
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
    "parser_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "reserved_word_as_name",
        "duplicate_name",
        "invalid_name",
    ),
    "function_dependency": (
        "all_functions_valid",
        "function_missing",
    ),
}

_NAMING_DEPENDENCY_AXES: dict[str, tuple[str, ...]] = {
    "parser_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "reserved_word_as_name",
        "duplicate_name",
        "invalid_name",
    ),
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
    "function_dependency": (
        "all_functions_valid",
        "function_missing",
    ),
}

_STATEMENT_FN_DEP_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_without_headline",
        "branch_with_headline",
    ),
    "headline_clause": ("omitted", "specified"),
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
    "function_dependency": (
        "all_functions_valid",
        "function_missing",
    ),
}

_PARSER_FN_NAME_AXES: dict[str, tuple[str, ...]] = {
    "parser_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "reserved_word_as_name",
        "duplicate_name",
        "invalid_name",
    ),
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
}

_STATEMENT_PARSER_FN_NAME_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_without_headline",
        "branch_with_headline",
    ),
    "headline_clause": ("omitted", "specified"),
    "parser_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "reserved_word_as_name",
        "duplicate_name",
        "invalid_name",
    ),
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
}

_PARSER_DEPENDENCY_AXES: dict[str, tuple[str, ...]] = {
    "parser_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "reserved_word_as_name",
        "duplicate_name",
        "invalid_name",
    ),
    "function_dependency": (
        "all_functions_valid",
        "function_missing",
    ),
}

_HEADLINE_FN_DEP_AXES: dict[str, tuple[str, ...]] = {
    "headline_clause": ("omitted", "specified"),
    "function_dependency": (
        "all_functions_valid",
        "function_missing",
    ),
}

# Representative failure (factor, value) pairs — one per failure scenario.
# Overlapping T5 values are derived, not crossed, so they are NOT listed
# here (would double-count a single failure and break attribution).
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "exists"),
        ("privilege_level", "non_superuser"),
        ("parser_name_shape", "duplicate_name"),
        ("parser_name_shape", "invalid_name"),
        ("parser_name_shape", "reserved_word_as_name"),
        ("function_name_shape", "nonexistent_name"),
        ("function_dependency", "function_missing"),
    }
)

_COMBINATION_GROUP = (
    "create_text_search_parser_required_factor_value_matrix"
)

_CONSUMER_ACTION = "define_parser"


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return sum(
        1
        for factor, value in _CROSSED_NEGATIVES
        if assignment.get(factor) == value
    )


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    # headline consistency — only when both are explicitly present
    if "statement_branch" in assignment and "headline_clause" in assignment:
        sb = assignment["statement_branch"]
        hc = assignment["headline_clause"]
        if sb == "branch_with_headline" and hc != "specified":
            return False
        if sb == "branch_without_headline" and hc != "omitted":
            return False

    return _failure_unit_count(assignment) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    # --- headline cluster (bidirectional, read-then-write) ---
    sb_orig = a.get("statement_branch", "branch_without_headline")
    hc_orig = a.get("headline_clause", "omitted")
    if sb_orig == "branch_with_headline" or hc_orig == "specified":
        a["statement_branch"] = "branch_with_headline"
        a["headline_clause"] = "specified"
    else:
        a["statement_branch"] = "branch_without_headline"
        a["headline_clause"] = "omitted"

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
        a["missing_required_function"] = "missing_required_function"
    else:
        a["function_existence"] = "all_functions_exist"
        a["nonexistent_function"] = "function_exists"
        a["missing_required_function"] = "all_required_present"

    # --- duplicate cluster ---
    pns = a.get("parser_name_shape", "simple_id")
    os_state = a.get("object_state", "not_exists")
    if pns == "duplicate_name":
        a["object_state"] = "exists"
        a["duplicate_parser_name"] = "same_name_conflict"
    elif os_state == "exists":
        a["duplicate_parser_name"] = "same_name_conflict"
    else:
        a["duplicate_parser_name"] = "no_conflict"

    # --- expected_status ---
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations(
    axes: dict[str, tuple[str, ...]],
) -> list[dict[str, str]]:
    """Cartesian product of given axes, filtered by consistency."""

    keys = list(axes.keys())
    value_lists = [axes[k] for k in keys]
    combos: list[dict[str, str]] = []
    for values in itertools.product(*value_lists):
        assignment = dict(zip(keys, values))
        if _is_valid_combination(assignment):
            combos.append(assignment)
    return combos


def _full_assignment(
    behavior: dict[str, str],
    verification: str,
    cleanup: str,
) -> dict[str, str]:
    a: dict[str, str] = dict(_BASELINE_DEFAULTS)
    for key, value in behavior.items():
        a[key] = value
    a["verification_mode"] = verification
    a["cleanup_mode"] = cleanup
    _derive_overlapping_factors(a)
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"
    return a


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[CreateTextSearchParserFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-text-search-parser-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "ordinal": case.ordinal,
                    "case_id": case.case_id,
                    "derivation_id": case.derivation_id,
                    "derived_from_combination_group": (
                        case.derived_from_combination_group
                    ),
                    "derivation_reason": case.derivation_reason,
                    "factor_assignment": [
                        list(item) for item in case.factor_assignment
                    ],
                    "consumer_action_id": case.consumer_action_id,
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": (
                        case.expected_failure_reason
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def build_create_text_search_parser_factor_extension_plan(
    repository_root: Path,
) -> CreateTextSearchParserFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_text_search_parser")
    if len(catalog_rows) != 37:
        raise CreateTextSearchParserFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateTextSearchParserFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("core_definition", _CORE_DEFINITION_AXES),
        ("naming_shape", _NAMING_AXES),
        ("full_cross", _FULL_CROSS_AXES),
        ("naming_dependency", _NAMING_DEPENDENCY_AXES),
        ("statement_fn_dep", _STATEMENT_FN_DEP_AXES),
        ("parser_fn_name", _PARSER_FN_NAME_AXES),
        (
            "statement_parser_fn_name",
            _STATEMENT_PARSER_FN_NAME_AXES,
        ),
        ("parser_dependency", _PARSER_DEPENDENCY_AXES),
        ("headline_fn_dep", _HEADLINE_FN_DEP_AXES),
    ]

    for group_name, behavior_axes in cross_groups:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(behavior_axes)
        behavior_combos = _behavior_combinations(all_axes)
        for behavior in behavior_combos:
            for verification in _VERIFICATION_MODES:
                for cleanup in _CLEANUP_MODES:
                    raw_count += 1
                    full = _full_assignment(
                        behavior, verification, cleanup
                    )
                    if not _is_valid_combination(full):
                        continue
                    if len(full) != len(set(full)):
                        raise (
                            CreateTextSearchParserFactorExtensionError(
                                "duplicate factor key in assignment"
                            )
                        )
                    outcome, sqlstate, reason = _outcome_for(full)
                    ordinal += 1
                    sorted_assignment = tuple(sorted(full.items()))
                    derivation_id = (
                        f"CTSP-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        CreateTextSearchParserFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=(
                                f"CREATETEXTSEARCHPARSER{ordinal:05d}"
                            ),
                            sql_filename=(
                                f"CREATETEXTSEARCHPARSER{ordinal:05d}.sql"
                            ),
                            object_prefix=(
                                f"createtextsearchparser_{ordinal:05d}_"
                            ),
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"CREATE TEXT SEARCH PARSER extension: "
                                f"group={group_name}, "
                                f"verification={verification}, "
                                f"cleanup={cleanup}"
                            ),
                            factor_assignment=sorted_assignment,
                            consumer_action_id=_CONSUMER_ACTION,
                            outcome=outcome,
                            expected_sqlstate=sqlstate,
                            expected_failure_reason=reason,
                        )
                    )

    dropped = max(0, raw_count - _CAP)
    if dropped > 0:
        cases = cases[: _CAP]

    plan = CreateTextSearchParserFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateTextSearchParserFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateTextSearchParserFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    expected_ordinals = list(
        range(
            _BASELINE_COUNT + 1,
            _BASELINE_COUNT + 1 + len(plan.cases),
        )
    )
    if ordinals != expected_ordinals:
        raise CreateTextSearchParserFactorExtensionError(
            "extension ordinal gap"
        )
    if (
        len({case.case_id for case in plan.cases})
        != len(plan.cases)
    ):
        raise CreateTextSearchParserFactorExtensionError(
            "duplicate extension case_id"
        )
    if (
        len({case.sql_filename for case in plan.cases})
        != len(plan.cases)
    ):
        raise CreateTextSearchParserFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateTextSearchParserFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("CTSP-EXT|")
        for case in plan.cases
    ):
        raise CreateTextSearchParserFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateTextSearchParserFactorExtensionError",
    "CreateTextSearchParserFactorExtensionCase",
    "CreateTextSearchParserFactorExtensionPlan",
    "build_create_text_search_parser_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
