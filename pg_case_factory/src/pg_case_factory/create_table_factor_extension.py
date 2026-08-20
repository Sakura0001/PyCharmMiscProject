"""Bounded post-coverage extension plan for CREATE TABLE factor regress.

The baseline :mod:`create_table_factor_loop` assigns one local SQL program
to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module crosses
the main-axis factor values with verification/cleanup axes under an
at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE TABLE creates a relation (``pg_class.relkind = 'r'``).  The
bookend gate applies: the FIRST and LAST executable ``;``-statements
are each ``DROP TABLE IF EXISTS <all created tables>``.

The extension is deterministic: given the same repository root, it
always produces the same frozen multiset SHA-256 and the same
contiguous case ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .create_table_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_create_table_factor_loop_plan,
)


class CreateTableFactorExtensionError(ValueError):
    """Raised when CREATE TABLE extension input drifts."""


@dataclass(frozen=True)
class CreateTableFactorExtensionCase:
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
class CreateTableFactorExtensionPlan:
    cases: tuple[CreateTableFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 188
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "information_schema_tables",
    "information_schema_columns",
    "SELECT_count",
    "pg_attribute_query",
)

_CLEANUP_MODES = (
    "DROP_TABLE",
    "DROP_TABLE_IF_EXISTS",
    "DROP_TABLE_CASCADE",
    "DROP_TABLE_CASCADE_RESTRICT",
)

_MAIN_AXES: dict[str, tuple[str, ...]] = {
    "table_type": (
        "permanent", "temp_short", "temporary_global",
        "temporary_local", "unlogged",
    ),
    "constraint_type": (
        "NOT_NULL", "PRIMARY_KEY", "UNIQUE", "CHECK", "DEFAULT",
        "FOREIGN_KEY", "EXCLUDE", "GENERATED_ALWAYS_STORED",
        "GENERATED_IDENTITY",
    ),
    "partition_clause": ("RANGE", "LIST", "HASH", "not_partitioned"),
}

_SECONDARY_AXES: list[tuple[str, tuple[str, ...]]] = [
    ("on_commit_clause", ("PRESERVE_ROWS", "DELETE_ROWS", "DROP", "absent")),
    ("column_definition_count", ("single_column", "multiple_columns")),
    ("if_not_exists_clause", ("absent", "present")),
    ("inheritance_clause", ("INHERITS", "no_inheritance")),
    ("like_clause", ("LIKE_no_options", "LIKE_with_options", "no_LIKE")),
    ("table_name_shape", ("simple", "quoted", "reserved_word",
                          "schema_qualified", "duplicate")),
    ("column_name_shape", ("simple", "quoted", "reserved_word",
                           "duplicate_in_table")),
    ("default_value_shape", ("without_DEFAULT", "with_DEFAULT_literal",
                             "with_DEFAULT_expression")),
    ("collation_clause", ("without_COLLATION", "with_COLLATION")),
    ("generated_clause", ("none", "GENERATED_ALWAYS_AS_STORED",
                          "GENERATED_ALWAYS_AS_IDENTITY",
                          "GENERATED_BY_DEFAULT_AS_IDENTITY")),
    ("base_table_template_coverage", ("table_01_comprehensive_types",
                                      "table_02_simplified_types",
                                      "table_03_partition_parent",
                                      "table_04_typed_table")),
    ("data_type", ("integer", "bigint", "text", "boolean", "numeric",
                   "date", "timestamp", "jsonb", "uuid", "serial",
                   "bytea", "interval")),
    ("object_state", ("not_exists", "already_exists")),
    ("duplicate_table_name", ("with_IF_NOT_EXISTS_noop",
                              "without_IF_NOT_EXISTS_error")),
    ("max_column_limit", ("approaching_1600", "at_1600", "over_1600")),
]

_SECONDARY_TABLE_TYPES = ("permanent", "unlogged")

_CROSSED_NEGATIVES = frozenset(_SFV_FAILURE_VALUES)

_COMBINATION_GROUP = "create_table_declared_factor_baseline"


def _is_duplicate_scenario(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "already_exists"
        or a.get("table_name_shape") == "duplicate"
        or a.get("duplicate_table_name") == "without_IF_NOT_EXISTS_error"
        or a.get("temporary_table_scope_conflict")
        == "temp_table_same_name_permanent"
    )


def _is_on_commit_permanent(a: dict[str, str]) -> bool:
    return (
        a.get("on_commit_clause") != "absent"
        and a.get("table_type") == "permanent"
    )


def _is_reserved_schema(a: dict[str, str]) -> bool:
    sd = a.get("schema_dependency", "schema_exists")
    rsn = a.get("reserved_schema_name", "none")
    return sd in ("information_schema_reserved", "pg_catalog_reserved") or (
        rsn in ("information_schema", "pg_catalog")
    )


def _is_schema_missing(a: dict[str, str]) -> bool:
    return a.get("schema_dependency") == "schema_not_exists"


def _is_no_privilege(a: dict[str, str]) -> bool:
    return (
        a.get("privilege_level") == "non_owner_no_privilege"
        or a.get("schema_permission_insufficient")
        == "no_create_privilege_in_schema"
    )


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    if _is_duplicate_scenario(a):
        conditions.append("duplicate_object")
    if a.get("column_name_shape") == "duplicate_in_table" or (
        a.get("duplicate_column_name") == "same_column_name_in_table"
    ):
        conditions.append("duplicate_column")
    cv = a.get("constraint_violation_in_definition", "none")
    if cv != "none":
        conditions.append(f"constraint_violation:{cv}")
    idt = a.get("invalid_data_type", "none")
    if idt != "none":
        conditions.append(f"invalid_data_type:{idt}")
    if a.get("identifier_length_exceeded") == "over_63_chars":
        conditions.append("name_too_long")
    if a.get("max_column_limit") == "over_1600":
        conditions.append("too_many_columns")
    if _is_on_commit_permanent(a):
        conditions.append("on_commit_on_permanent_table")
    ptd = a.get("parent_table_dependency", "parent_table_exists")
    if ptd != "parent_table_exists":
        conditions.append(f"parent_dependency:{ptd}")
    pbi = a.get("partition_bound_invalid", "none")
    if pbi != "none":
        conditions.append(f"partition_bound_invalid:{pbi}")
    if _is_no_privilege(a):
        conditions.append("insufficient_privilege")
    if a.get("referenced_table_dependency") == "referenced_table_not_exists":
        conditions.append("referenced_table_missing")
    if _is_reserved_schema(a):
        conditions.append("reserved_schema")
    if _is_schema_missing(a):
        conditions.append("schema_missing")
    if a.get("tablespace_dependency") == "specified_tablespace_not_exists":
        conditions.append("tablespace_missing")
    if a.get("role_dependency") == "owner_role_not_exists":
        conditions.append("role_missing")
    if a.get("type_dependency") == "composite_type_not_exists":
        conditions.append("type_missing")
    return conditions


def _is_valid_combination(a: dict[str, str]) -> bool:
    return len(_failure_conditions(a)) <= 1


_FAILURE_SQLSTATE = {
    "duplicate_object": ("42710", "duplicate_object_provisional"),
    "duplicate_column": ("42710", "duplicate_column_provisional"),
    "constraint_violation:CHECK_expression_invalid": (
        "42P17", "invalid_table_definition_provisional",
    ),
    "constraint_violation:FK_references_nonexistent_table": (
        "42P01", "undefined_table_provisional",
    ),
    "constraint_violation:PK_with_nullable_column": (
        "42P17", "invalid_table_definition_provisional",
    ),
    "invalid_data_type:unknown_type_name": (
        "42704", "undefined_object_provisional",
    ),
    "invalid_data_type:wrong_array_syntax": (
        "42601", "syntax_error_provisional",
    ),
    "name_too_long": ("42602", "invalid_name_provisional"),
    "too_many_columns": ("54011", "too_many_columns_provisional"),
    "on_commit_on_permanent_table": (
        "42809", "wrong_object_type_provisional",
    ),
    "parent_dependency:parent_table_not_exists": (
        "42P01", "undefined_table_provisional",
    ),
    "parent_dependency:parent_table_not_partitioned": (
        "42809", "wrong_object_type_provisional",
    ),
    "partition_bound_invalid:bound_out_of_range": (
        "42804", "datatype_mismatch_provisional",
    ),
    "partition_bound_invalid:bound_type_mismatch": (
        "42804", "datatype_mismatch_provisional",
    ),
    "insufficient_privilege": (
        "42501", "insufficient_privilege_provisional",
    ),
    "referenced_table_missing": (
        "42P01", "undefined_table_provisional",
    ),
    "reserved_schema": (
        "42501", "insufficient_privilege_provisional",
    ),
    "schema_missing": ("3F000", "invalid_schema_name_provisional"),
    "tablespace_missing": ("42704", "undefined_object_provisional"),
    "role_missing": ("42704", "undefined_object_provisional"),
    "type_missing": ("42704", "undefined_object_provisional"),
}


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    if _is_duplicate_scenario(a):
        return ("object_state", "already_exists")
    if a.get("column_name_shape") == "duplicate_in_table":
        return ("column_name_shape", "duplicate_in_table")
    if a.get("duplicate_column_name") == "same_column_name_in_table":
        return ("duplicate_column_name", "same_column_name_in_table")
    cv = a.get("constraint_violation_in_definition", "none")
    if cv != "none":
        return ("constraint_violation_in_definition", cv)
    idt = a.get("invalid_data_type", "none")
    if idt != "none":
        return ("invalid_data_type", idt)
    if a.get("identifier_length_exceeded") == "over_63_chars":
        return ("identifier_length_exceeded", "over_63_chars")
    if a.get("max_column_limit") == "over_1600":
        return ("max_column_limit", "over_1600")
    if _is_on_commit_permanent(a):
        return ("on_commit_with_non_temporary", "on_commit_on_permanent_table")
    ptd = a.get("parent_table_dependency", "parent_table_exists")
    if ptd != "parent_table_exists":
        return ("parent_table_dependency", ptd)
    pbi = a.get("partition_bound_invalid", "none")
    if pbi != "none":
        return ("partition_bound_invalid", pbi)
    if _is_no_privilege(a):
        return ("privilege_level", "non_owner_no_privilege")
    if a.get("referenced_table_dependency") == "referenced_table_not_exists":
        return ("referenced_table_dependency", "referenced_table_not_exists")
    if _is_reserved_schema(a):
        return ("schema_dependency", a.get("schema_dependency"))
    if _is_schema_missing(a):
        return ("schema_dependency", "schema_not_exists")
    if a.get("tablespace_dependency") == "specified_tablespace_not_exists":
        return ("tablespace_dependency", "specified_tablespace_not_exists")
    if a.get("role_dependency") == "owner_role_not_exists":
        return ("role_dependency", "owner_role_not_exists")
    if a.get("type_dependency") == "composite_type_not_exists":
        return ("type_dependency", "composite_type_not_exists")
    return None


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    if _is_duplicate_scenario(a):
        a["object_state"] = "already_exists"
        a["duplicate_table_name"] = "without_IF_NOT_EXISTS_error"
        a["table_name_shape"] = "duplicate"
    if _is_on_commit_permanent(a):
        a["on_commit_with_non_temporary"] = "on_commit_on_permanent_table"
    if _is_reserved_schema(a):
        if a.get("schema_dependency") == "information_schema_reserved":
            a["reserved_schema_name"] = "information_schema"
        elif a.get("schema_dependency") == "pg_catalog_reserved":
            a["reserved_schema_name"] = "pg_catalog"
    if _is_no_privilege(a):
        a["privilege_level"] = "non_owner_no_privilege"
        a["schema_permission_insufficient"] = (
            "no_create_privilege_in_schema"
        )
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


def _extension_multiset_sha256(
    cases: tuple[CreateTableFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"create-table-factor-extension-v1\n")
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
    """Resolve the consumer action from the derived statement_branch."""
    sb = a.get("statement_branch", "branch_1")
    return {
        "branch_1": "create_regular",
        "branch_2": "create_typed",
        "branch_3": "create_partition",
    }.get(sb, "create_regular")


def _emit_case(
    ordinal: int,
    full: dict[str, str],
    verification: str,
    cleanup: str,
    round_label: str,
) -> CreateTableFactorExtensionCase | None:
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
        f"CT-EXT|{ordinal:05d}|{verification}|{cleanup}|{round_label}"
    )
    consumer = _consumer_for(full)
    return CreateTableFactorExtensionCase(
        ordinal=ordinal,
        case_id=f"CREATETABLE{ordinal:05d}",
        sql_filename=f"CREATETABLE{ordinal:05d}.sql",
        object_prefix=f"createtable_{ordinal:05d}_",
        derivation_id=derivation_id,
        derived_from_combination_group=_COMBINATION_GROUP,
        derivation_reason=(
            f"CREATE TABLE extension ({round_label}): "
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


def build_create_table_factor_extension_plan(
    repository_root: Path,
) -> CreateTableFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    baseline = build_create_table_factor_loop_plan(root)
    if len(baseline.cases) != _BASELINE_COUNT:
        raise CreateTableFactorExtensionError("baseline count drift")

    cases: list[CreateTableFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    # Round 1: main axes cross (table_type x constraint_type
    # x partition_clause) x verification x cleanup
    main_keys = list(_MAIN_AXES.keys())
    main_value_lists = [v for v in _MAIN_AXES.values()]
    for main_values in itertools.product(*main_value_lists):
        behavior = dict(zip(main_keys, main_values))
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw_count += 1
                full = _full_assignment(behavior, verification, cleanup)
                case = _emit_case(
                    ordinal + 1, full, verification, cleanup, "main",
                )
                if case is not None:
                    ordinal += 1
                    cases.append(case)

    # Round 2: secondary axis rotations (each axis crossed with
    # table_type x verification x cleanup, main axes at defaults)
    for axis_name, axis_values in _SECONDARY_AXES:
        for table_type in _SECONDARY_TABLE_TYPES:
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

    plan = CreateTableFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateTableFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateTableFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(range(
        _BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases)
    )):
        raise CreateTableFactorExtensionError("extension ordinal gap")
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateTableFactorExtensionError("duplicate extension case_id")
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateTableFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateTableFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("CT-EXT|")
        for case in plan.cases
    ):
        raise CreateTableFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateTableFactorExtensionError",
    "CreateTableFactorExtensionCase",
    "CreateTableFactorExtensionPlan",
    "build_create_table_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
