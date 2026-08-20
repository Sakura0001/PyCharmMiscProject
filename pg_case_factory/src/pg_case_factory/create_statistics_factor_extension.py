"""Bounded post-coverage extension plan for CREATE STATISTICS factor regress.

The baseline :mod:`create_statistics_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE STATISTICS references a table via ``FROM table_reference``.  The
no-DB ledger prefers a fixture table for fuller coverage and bookend
gate compliance.

The extension is deterministic: given the same repository root, it
always produces the same frozen multiset SHA-256 and the same contiguous
case ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_statistics_factor_loop import (
    _BASELINE_DEFAULTS,
    _FAILURE_CONDITIONS,
    _SFV_FAILURE_SQLSTATE,
)


class CreateStatisticsFactorExtensionError(ValueError):
    """Raised when CREATE STATISTICS extension input drifts."""


@dataclass(frozen=True)
class CreateStatisticsFactorExtensionCase:
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
class CreateStatisticsFactorExtensionPlan:
    cases: tuple[CreateStatisticsFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 56
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_statistic_ext_catalog",
    "error_assertion",
)
_CLEANUP_MODES = ("drop_statistics", "rollback")

_KINDS = (
    "omitted_all_kinds",
    "ndistinct_only",
    "dependencies_only",
    "mcv_only",
    "ndistinct_and_dependencies",
    "all_three_kinds",
)
_COLUMN_COMBINATIONS = (
    "two_columns",
    "three_columns",
    "column_and_expression_mix",
    "single_expression_univariate",
)
_IF_NOT_EXISTS = ("without_if_not_exists", "with_if_not_exists")
_EXPRESSION_SHAPES = (
    "simple_column_reference",
    "arithmetic_expression",
    "function_call_expression",
)
_NAME_PRESENCE = ("explicit_name", "auto_generated_name_omitted")

_MAIN_AXES: dict[str, tuple[str, ...]] = {
    "if_not_exists_clause": _IF_NOT_EXISTS,
    "expression_shape": _EXPRESSION_SHAPES,
    "statistics_name_presence": _NAME_PRESENCE,
}

_SECONDARY_AXES: list[tuple[str, tuple[str, ...]]] = [
    ("statistics_name_shape", (
        "simple_name", "schema_qualified_name", "quoted_name",
        "reserved_word_name", "non_existing_name",
    )),
    ("table_name_shape", (
        "simple_name", "schema_qualified_name",
        "quoted_name", "nonexistent_table",
    )),
    ("column_name_shape", (
        "simple_name", "quoted_name", "nonexistent_column",
    )),
    ("executor_privilege", ("superuser", "table_owner", "non_owner_no_privilege")),
    ("table_dependency", ("table_exists", "table_not_exists")),
    ("column_dependency", ("column_exists", "column_not_exists")),
    ("duplicate_statistics_name", ("none", "same_name_exists")),
    ("expected_status", ("success", "failure")),
    ("statistics_identity", (
        "not_exists", "exists", "exists_with_if_not_exists",
        "reserved_word_name",
    )),
    ("privilege_insufficient", ("non_table_owner_creating_statistics",)),
    ("nonexistent_table", ("table_not_exists_failure",)),
    ("nonexistent_column", ("column_not_exists_failure",)),
    ("single_column_for_multivariate", ("single_column_multivariate_failure",)),
    ("expression_syntax_error", ("invalid_expression_failure",)),
]

_COMBINATION_GROUP = "create_statistics_required_factor_value_matrix"

_NONE = "none"


def _is_duplicate_failure(a: dict[str, str]) -> bool:
    if a.get("if_not_exists_clause") == "with_if_not_exists":
        return False
    if a.get("expected_status") == "failure":
        return True
    if a.get("statistics_identity") == "exists":
        return True
    if a.get("duplicate_statistics_name") == "same_name_exists":
        return True
    return False


def _is_nonexistent_table(a: dict[str, str]) -> bool:
    return (
        a.get("table_dependency") == "table_not_exists"
        or a.get("table_name_shape") == "nonexistent_table"
        or a.get("nonexistent_table") == "table_not_exists_failure"
    )


def _is_nonexistent_column(a: dict[str, str]) -> bool:
    return (
        a.get("column_dependency") == "column_not_exists"
        or a.get("column_name_shape") == "nonexistent_column"
        or a.get("nonexistent_column") == "column_not_exists_failure"
    )


def _is_privilege_insufficient(a: dict[str, str]) -> bool:
    return (
        a.get("executor_privilege") == "non_owner_no_privilege"
        or a.get("privilege_insufficient")
        == "non_table_owner_creating_statistics"
    )


def _is_single_column_multivariate(a: dict[str, str]) -> bool:
    return a.get("single_column_for_multivariate") == (
        "single_column_multivariate_failure"
    )


def _is_expression_syntax_error(a: dict[str, str]) -> bool:
    return a.get("expression_syntax_error") == "invalid_expression_failure"


_EXT_FAILURE_CONDITIONS = (
    _is_duplicate_failure,
    _is_nonexistent_table,
    _is_nonexistent_column,
    _is_privilege_insufficient,
    _is_single_column_multivariate,
    _is_expression_syntax_error,
)


def _failure_conditions(a: dict[str, str]) -> list[str]:
    conditions: list[str] = []
    if _is_duplicate_failure(a):
        conditions.append("duplicate_statistics")
    if _is_nonexistent_table(a):
        conditions.append("nonexistent_table")
    if _is_nonexistent_column(a):
        conditions.append("nonexistent_column")
    if _is_privilege_insufficient(a):
        conditions.append("privilege_insufficient")
    if _is_single_column_multivariate(a):
        conditions.append("single_column_multivariate")
    if _is_expression_syntax_error(a):
        conditions.append("expression_syntax_error")
    return conditions


def _is_valid_combination(a: dict[str, str]) -> bool:
    return len(_failure_conditions(a)) <= 1


_FAILURE_SQLSTATE = {
    "duplicate_statistics": ("42710", "duplicate_statistics_provisional"),
    "nonexistent_table": ("42P01", "undefined_table_provisional"),
    "nonexistent_column": ("42703", "undefined_column_provisional"),
    "privilege_insufficient": ("42501", "insufficient_privilege_provisional"),
    "single_column_multivariate": (
        "42P16", "single_column_multivariate_provisional"
    ),
    "expression_syntax_error": ("42601", "syntax_error_provisional"),
}


def _derive_factors(a: dict[str, str]) -> None:
    """Derive overlapping factors from the behavior axis values."""

    combo = a.get("column_combination", "two_columns")
    if combo == "single_expression_univariate":
        a["statement_branch"] = "branch_univariate_expression"
        a["statistics_kind_clause"] = "omitted_all_kinds"
    else:
        a["statement_branch"] = "branch_multivariate_columns"

    if a.get("statement_branch") == "branch_univariate_expression":
        a["statistics_kind_clause"] = "omitted_all_kinds"

    if a.get("if_not_exists_clause") == "with_if_not_exists":
        a["statistics_name_presence"] = "explicit_name"

    ident = a.get("statistics_identity", "not_exists")
    if ident == "exists":
        a["duplicate_statistics_name"] = "same_name_exists"
        a["if_not_exists_clause"] = "without_if_not_exists"
    elif ident == "exists_with_if_not_exists":
        a["duplicate_statistics_name"] = "same_name_exists"
        a["if_not_exists_clause"] = "with_if_not_exists"
        a["statistics_name_presence"] = "explicit_name"
    elif ident == "reserved_word_name":
        a["statistics_name_shape"] = "reserved_word_name"
        a["duplicate_statistics_name"] = _NONE

    if a.get("duplicate_statistics_name") == "same_name_exists":
        if a.get("statistics_identity", "not_exists") == "not_exists":
            a["statistics_identity"] = "exists"

    if a.get("expected_status") == "failure":
        a["statistics_identity"] = "exists"
        a["duplicate_statistics_name"] = "same_name_exists"
        a["if_not_exists_clause"] = "without_if_not_exists"

    if a.get("nonexistent_table") == "table_not_exists_failure":
        a["table_dependency"] = "table_not_exists"
        a["table_name_shape"] = "nonexistent_table"
    if a.get("nonexistent_column") == "column_not_exists_failure":
        a["column_dependency"] = "column_not_exists"
        a["column_name_shape"] = "nonexistent_column"
    if a.get("privilege_insufficient") == "non_table_owner_creating_statistics":
        a["executor_privilege"] = "non_owner_no_privilege"
    if a.get("table_dependency") == "table_not_exists":
        a["table_name_shape"] = "nonexistent_table"
    if a.get("column_dependency") == "column_not_exists":
        a["column_name_shape"] = "nonexistent_column"
    if a.get("executor_privilege") == "non_owner_no_privilege":
        a["privilege_insufficient"] = "non_table_owner_creating_statistics"

    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    if _is_duplicate_failure(a):
        return ("duplicate_statistics_name", "same_name_exists")
    if _is_nonexistent_table(a):
        return ("nonexistent_table", "table_not_exists_failure")
    if _is_nonexistent_column(a):
        return ("nonexistent_column", "column_not_exists_failure")
    if _is_privilege_insufficient(a):
        return ("privilege_insufficient", "non_table_owner_creating_statistics")
    if _is_single_column_multivariate(a):
        return (
            "single_column_for_multivariate",
            "single_column_multivariate_failure",
        )
    if _is_expression_syntax_error(a):
        return ("expression_syntax_error", "invalid_expression_failure")
    return None


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
    _derive_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _extension_multiset_sha256(
    cases: tuple[CreateStatisticsFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-statistics-factor-extension-v1\n"
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


def _consumer_for(a: dict[str, str]) -> str:
    sbv = a.get("statement_branch", "branch_multivariate_columns")
    if sbv == "branch_univariate_expression":
        return "branch_univariate_expression"
    return "branch_multivariate_columns"


def _emit_case(
    ordinal: int,
    full: dict[str, str],
    verification: str,
    cleanup: str,
    round_label: str,
) -> CreateStatisticsFactorExtensionCase | None:
    failures = _failure_conditions(full)
    if len(failures) > 1:
        return None
    if failures:
        condition = failures[0]
        sqlstate, reason = _FAILURE_SQLSTATE[condition]
        outcome = "expected_failure"
    else:
        sqlstate = "00000"
        reason = None
        outcome = "success"
    sorted_assignment = tuple(sorted(full.items()))
    derivation_id = (
        f"CSTAT-EXT|{ordinal:05d}|"
        f"{verification}|{cleanup}|{round_label}"
    )
    consumer = _consumer_for(full)
    return CreateStatisticsFactorExtensionCase(
        ordinal=ordinal,
        case_id=f"CREATESTATISTICS{ordinal:05d}",
        sql_filename=f"CREATESTATISTICS{ordinal:05d}.sql",
        object_prefix=f"createstatistics_{ordinal:05d}_",
        derivation_id=derivation_id,
        derived_from_combination_group=_COMBINATION_GROUP,
        derivation_reason=(
            f"CREATE STATISTICS extension ({round_label}): "
            f"verification={verification}, cleanup={cleanup}"
        ),
        factor_assignment=sorted_assignment,
        consumer_action_id=consumer,
        outcome=outcome,
        expected_sqlstate=sqlstate,
        expected_failure_reason=reason,
    )


def build_create_statistics_factor_extension_plan(
    repository_root: Path,
) -> CreateStatisticsFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_statistics")
    if len(catalog_rows) != 54:
        raise CreateStatisticsFactorExtensionError("catalog row count drift")

    cases: list[CreateStatisticsFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    main_keys = list(_MAIN_AXES.keys())
    main_value_lists = [v for v in _MAIN_AXES.values()]

    # Round 1: kind × column_combination × main axes × verification × cleanup.
    for combo in _COLUMN_COMBINATIONS:
        is_univariate = combo == "single_expression_univariate"
        kinds = ("omitted_all_kinds",) if is_univariate else _KINDS
        for kind in kinds:
            for main_values in itertools.product(*main_value_lists):
                behavior: dict[str, str] = dict(zip(main_keys, main_values))
                behavior["statistics_kind_clause"] = kind
                behavior["column_combination"] = combo
                for verification in _VERIFICATION_MODES:
                    for cleanup in _CLEANUP_MODES:
                        raw_count += 1
                        full = _full_assignment(
                            behavior, verification, cleanup
                        )
                        case = _emit_case(
                            ordinal + 1, full, verification, cleanup,
                            "main",
                        )
                        if case is not None:
                            ordinal += 1
                            cases.append(case)

    # Round 2: secondary axis rotations × column_combination ×
    # verification × cleanup (exercises pairwise interactions).
    for axis_name, axis_values in _SECONDARY_AXES:
        for axis_value in axis_values:
            for combo in _COLUMN_COMBINATIONS:
                is_univariate = combo == "single_expression_univariate"
                kinds = ("omitted_all_kinds",) if is_univariate else _KINDS
                for kind in kinds:
                    for verification in _VERIFICATION_MODES:
                        for cleanup in _CLEANUP_MODES:
                            raw_count += 1
                            behavior = {
                                axis_name: axis_value,
                                "column_combination": combo,
                                "statistics_kind_clause": kind,
                            }
                            full = _full_assignment(
                                behavior, verification, cleanup
                            )
                            case = _emit_case(
                                ordinal + 1, full, verification, cleanup,
                                f"secondary_{axis_name}",
                            )
                            if case is not None:
                                ordinal += 1
                                cases.append(case)

    dropped = max(0, raw_count - len(cases))
    if len(cases) > _CAP:
        cases = cases[:_CAP]

    plan = CreateStatisticsFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateStatisticsFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateStatisticsFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(range(
        _BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases)
    )):
        raise CreateStatisticsFactorExtensionError("extension ordinal gap")
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateStatisticsFactorExtensionError("duplicate extension case_id")
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateStatisticsFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateStatisticsFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("CSTAT-EXT|")
        for case in plan.cases
    ):
        raise CreateStatisticsFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateStatisticsFactorExtensionError",
    "CreateStatisticsFactorExtensionCase",
    "CreateStatisticsFactorExtensionPlan",
    "build_create_statistics_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
