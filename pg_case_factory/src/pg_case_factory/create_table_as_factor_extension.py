"""Bounded post-coverage extension plan for CREATE TABLE AS factor regress.

The baseline :mod:`create_table_as_factor_loop` assigns one local SQL program
to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module crosses
the main-axis factor values with verification/cleanup axes under an
at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE TABLE AS creates a table from a query.  The no-DB ledger prefers
a fixture source table for fuller coverage and bookend gate compliance.

The extension is deterministic: given the same repository root, it always
produces the same frozen multiset SHA-256 and the same contiguous case
ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_table_as_factor_loop import (
    _BASELINE_DEFAULTS,
    _BRANCH_TO_TABLE_TYPE,
    _QUERY_TO_DERIVATION,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    _TABLE_TYPE_TO_BRANCH,
)


class CreateTableAsFactorExtensionError(ValueError):
    """Raised when CREATE TABLE AS extension input drifts."""


@dataclass(frozen=True)
class CreateTableAsFactorExtensionCase:
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
class CreateTableAsFactorExtensionPlan:
    cases: tuple[CreateTableAsFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 86
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "information_schema_tables",
    "information_schema_columns",
    "SELECT_count",
    "SELECT_star_structure",
)
_CLEANUP_MODES = ("DROP_TABLE", "DROP_TABLE_IF_EXISTS", "DROP_TABLE_CASCADE")

_TABLE_TYPES = (
    "permanent",
    "temporary_global",
    "temporary_local",
    "temp_short",
    "unlogged",
)

_MAIN_AXES: dict[str, tuple[str, ...]] = {
    "with_data": ("WITH_DATA", "WITH_NO_DATA", "absent_default"),
    "on_commit_clause": (
        "PRESERVE_ROWS", "DELETE_ROWS", "DROP", "absent",
    ),
}

_SECONDARY_AXES: list[tuple[str, tuple[str, ...]]] = [
    ("query_shape", (
        "simple_select", "table_command", "values_command",
        "execute_prepared", "aggregate_query", "join_query",
        "union_query", "subquery",
    )),
    ("column_names", ("explicit_list", "inherit_from_query")),
    ("column_name_list_shape", (
        "matching_query_columns", "fewer_than_query_columns",
        "more_than_query_columns", "absent",
    )),
    ("with_storage_clause", (
        "with_storage", "without_storage", "without_oids",
    )),
    ("tablespace_clause", ("specified", "default")),
    ("table_name_shape", (
        "simple", "quoted", "reserved_word",
        "schema_qualified", "duplicate",
    )),
    ("column_type_derivation", (
        "derived_from_select_expr", "derived_from_table_command",
        "derived_from_values", "derived_from_execute",
    )),
    ("privilege_level", (
        "superuser", "schema_owner_with_create",
        "non_owner_no_privilege",
    )),
    ("source_table_dependency", (
        "source_table_exists", "source_table_not_exists",
    )),
    ("schema_dependency", (
        "schema_exists", "schema_not_exists", "pg_catalog_reserved",
    )),
    ("tablespace_dependency", (
        "default_tablespace", "specified_tablespace_exists",
        "specified_tablespace_not_exists",
    )),
    ("if_not_exists_clause", ("present", "absent")),
]

_COMBINATION_GROUP = "create_table_as_required_factor_value_matrix"


def _is_temporary(table_type: str) -> bool:
    return table_type in (
        "temporary_global", "temporary_local", "temp_short",
    )


def _is_on_commit_permanent(a: dict[str, str]) -> bool:
    return (
        a.get("on_commit_clause", "absent") != "absent"
        and not _is_temporary(a.get("table_type", "permanent"))
    )


def _is_privilege_denied(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_owner_no_privilege"


def _is_source_not_exists(a: dict[str, str]) -> bool:
    return a.get("source_table_dependency") == "source_table_not_exists"


def _is_column_more_names(a: dict[str, str]) -> bool:
    return a.get("column_name_list_shape") == "more_than_query_columns"


def _is_schema_not_exists(a: dict[str, str]) -> bool:
    return a.get("schema_dependency") == "schema_not_exists"


def _is_tablespace_not_exists(a: dict[str, str]) -> bool:
    return (
        a.get("tablespace_dependency")
        == "specified_tablespace_not_exists"
    )


def _is_pg_catalog_reserved(a: dict[str, str]) -> bool:
    return a.get("schema_dependency") == "pg_catalog_reserved"


def _is_duplicate_no_ifne(a: dict[str, str]) -> bool:
    return (
        a.get("table_name_shape") == "duplicate"
        and a.get("if_not_exists_clause") == "absent"
    )


def _is_execute_prepared(a: dict[str, str]) -> bool:
    return a.get("query_shape") == "execute_prepared"


_FAILURE_SQLSTATE: dict[str, tuple[str, str]] = {
    "on_commit_permanent": (
        "42601",
        "on_commit_on_permanent_table_provisional",
    ),
    "privilege_denied": (
        "42501",
        "insufficient_privilege_provisional",
    ),
    "source_not_exists": (
        "42P01",
        "undefined_table_provisional",
    ),
    "column_more_names": (
        "42601",
        "too_many_column_names_provisional",
    ),
    "schema_not_exists": (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    "tablespace_not_exists": (
        "42704",
        "undefined_object_provisional",
    ),
    "pg_catalog_reserved": (
        "42501",
        "pg_catalog_reserved_provisional",
    ),
    "duplicate_no_ifne": (
        "42P07",
        "duplicate_table_without_if_not_exists_provisional",
    ),
    "execute_prepared_invalid": (
        "42601",
        "syntax_error_provisional",
    ),
}


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    if _is_on_commit_permanent(a):
        conditions.append("on_commit_permanent")
    if _is_privilege_denied(a):
        conditions.append("privilege_denied")
    if _is_source_not_exists(a):
        conditions.append("source_not_exists")
    if _is_column_more_names(a):
        conditions.append("column_more_names")
    if _is_schema_not_exists(a):
        conditions.append("schema_not_exists")
    if _is_tablespace_not_exists(a):
        conditions.append("tablespace_not_exists")
    if _is_pg_catalog_reserved(a):
        conditions.append("pg_catalog_reserved")
    if _is_duplicate_no_ifne(a):
        conditions.append("duplicate_no_ifne")
    if _is_execute_prepared(a):
        conditions.append("execute_prepared_invalid")
    return conditions


def _is_valid_combination(a: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""
    return len(_failure_conditions(a)) <= 1


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    if _is_on_commit_permanent(a):
        return ("on_commit_with_non_temporary", "on_commit_on_permanent_table")
    if _is_privilege_denied(a):
        return ("privilege_insufficient", "no_create_in_schema")
    if _is_source_not_exists(a):
        return ("query_error", "references_nonexistent_table")
    if _is_column_more_names(a):
        return ("column_name_mismatch", "more_names_error")
    if _is_schema_not_exists(a):
        return ("schema_dependency", "schema_not_exists")
    if _is_tablespace_not_exists(a):
        return ("tablespace_dependency", "specified_tablespace_not_exists")
    if _is_pg_catalog_reserved(a):
        return ("schema_dependency", "pg_catalog_reserved")
    if _is_duplicate_no_ifne(a):
        return ("duplicate_table_name", "without_IF_NOT_EXISTS_error")
    if _is_execute_prepared(a):
        return ("query_error", "invalid_sql_syntax")
    return None


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive overlapping T1/T2 factors from positive axis values."""

    table_type = a.get("table_type", "permanent")
    if table_type in _TABLE_TYPE_TO_BRANCH:
        a["statement_branch"] = _TABLE_TYPE_TO_BRANCH[table_type]

    branch = a.get("statement_branch", "branch_regular")
    if branch in _BRANCH_TO_TABLE_TYPE:
        derived_tt = _BRANCH_TO_TABLE_TYPE[branch]
        if a.get("table_type") == _BASELINE_DEFAULTS["table_type"]:
            a["table_type"] = derived_tt
            table_type = derived_tt

    if "_if_not_exists" in branch:
        if a.get("if_not_exists_clause") == _BASELINE_DEFAULTS["if_not_exists_clause"]:
            a["if_not_exists_clause"] = "present"

    if a.get("if_not_exists_clause") == "present" and "_if_not_exists" not in branch:
        if table_type == "unlogged":
            a["statement_branch"] = "branch_unlogged_if_not_exists"
        elif _is_temporary(table_type):
            a["statement_branch"] = "branch_temporary_if_not_exists"
        else:
            a["statement_branch"] = "branch_regular_if_not_exists"

    qs = a.get("query_shape", "simple_select")
    if qs in _QUERY_TO_DERIVATION:
        if a.get("column_type_derivation") == _BASELINE_DEFAULTS["column_type_derivation"]:
            a["column_type_derivation"] = _QUERY_TO_DERIVATION[qs]

    if a.get("column_names") == "explicit_list":
        if a.get("column_name_list_shape") == _BASELINE_DEFAULTS["column_name_list_shape"]:
            a["column_name_list_shape"] = "matching_query_columns"
    elif a.get("column_names") == "inherit_from_query":
        if a.get("column_name_list_shape") not in ("absent",):
            a["column_name_list_shape"] = "absent"

    if a.get("tablespace_dependency") == "specified_tablespace_exists":
        a["tablespace_clause"] = "specified"
    elif a.get("tablespace_dependency") == "specified_tablespace_not_exists":
        a["tablespace_clause"] = "specified"

    if a.get("schema_dependency") in ("schema_not_exists", "pg_catalog_reserved"):
        a["table_name_shape"] = "schema_qualified"

    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"


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
    _derive_t5_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _consumer_for(a: dict[str, str]) -> str:
    """Resolve the consumer action from the derived statement_branch."""
    branch = a.get("statement_branch", "branch_regular")
    mapping = {
        "branch_regular": "regular",
        "branch_regular_if_not_exists": "regular",
        "branch_temporary": "temporary",
        "branch_temp": "temporary",
        "branch_temporary_if_not_exists": "temporary",
        "branch_unlogged": "unlogged",
        "branch_unlogged_if_not_exists": "unlogged",
    }
    return mapping.get(branch, "regular")


def _extension_multiset_sha256(
    cases: tuple[CreateTableAsFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-table-as-factor-extension-v1\n"
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


def _emit_case(
    ordinal: int,
    full: dict[str, str],
    verification: str,
    cleanup: str,
    round_label: str,
) -> CreateTableAsFactorExtensionCase | None:
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
        f"CTAS-EXT|{ordinal:05d}|"
        f"{verification}|{cleanup}|{round_label}"
    )
    consumer = _consumer_for(full)
    return CreateTableAsFactorExtensionCase(
        ordinal=ordinal,
        case_id=f"CREATETABLEAS{ordinal:05d}",
        sql_filename=f"CREATETABLEAS{ordinal:05d}.sql",
        object_prefix=f"createtableas_{ordinal:05d}_",
        derivation_id=derivation_id,
        derived_from_combination_group=_COMBINATION_GROUP,
        derivation_reason=(
            f"CREATE TABLE AS extension ({round_label}): "
            f"table_type={full.get('table_type')}, "
            f"verification={verification}, "
            f"cleanup={cleanup}"
        ),
        factor_assignment=sorted_assignment,
        consumer_action_id=consumer,
        outcome=outcome,
        expected_sqlstate=sqlstate,
        expected_failure_reason=reason,
    )


def build_create_table_as_factor_extension_plan(
    repository_root: Path,
) -> CreateTableAsFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_table_as")
    if len(catalog_rows) != 83:
        raise CreateTableAsFactorExtensionError("catalog row count drift")

    cases: list[CreateTableAsFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    # Round 1: table_type × with_data × on_commit_clause × verif × cleanup
    main_keys = list(_MAIN_AXES.keys())
    main_value_lists = [v for v in _MAIN_AXES.values()]
    for table_type in _TABLE_TYPES:
        for main_values in itertools.product(*main_value_lists):
            behavior = dict(zip(main_keys, main_values))
            behavior["table_type"] = table_type
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

    # Round 2: secondary axis rotations
    for axis_name, axis_values in _SECONDARY_AXES:
        for table_type in _TABLE_TYPES:
            for axis_value in axis_values:
                for verification in _VERIFICATION_MODES:
                    for cleanup in _CLEANUP_MODES:
                        raw_count += 1
                        behavior = {
                            "table_type": table_type,
                            axis_name: axis_value,
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

    plan = CreateTableAsFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateTableAsFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateTableAsFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(range(
        _BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases)
    )):
        raise CreateTableAsFactorExtensionError("extension ordinal gap")
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateTableAsFactorExtensionError("duplicate extension case_id")
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateTableAsFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateTableAsFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("CTAS-EXT|")
        for case in plan.cases
    ):
        raise CreateTableAsFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateTableAsFactorExtensionError",
    "CreateTableAsFactorExtensionCase",
    "CreateTableAsFactorExtensionPlan",
    "build_create_table_as_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_FAILURE_SQLSTATE",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
