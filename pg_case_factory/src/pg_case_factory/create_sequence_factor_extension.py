"""Bounded post-coverage extension plan for CREATE SEQUENCE factor regress.

The baseline :mod:`create_sequence_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE SEQUENCE targets a ``pg_class`` relation row (relkind ``S``).
Most extension cases do not create tables; only ``owned_by_column``
combinations with ``owned_by_table_dependency=table_column_exists`` emit a
fixture ``CREATE TABLE`` (per-script ``DROP TABLE`` bookend).  The
extension is deterministic: same root → same frozen multiset SHA-256 and
contiguous ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_sequence_factor_loop import (
    _BASELINE_DEFAULTS,
    _FAILURE_SQLSTATE,
    _failure_conditions,
)


class CreateSequenceFactorExtensionError(ValueError):
    """Raised when CREATE SEQUENCE extension input drifts."""


@dataclass(frozen=True)
class CreateSequenceFactorExtensionCase:
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
class CreateSequenceFactorExtensionPlan:
    cases: tuple[CreateSequenceFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 71
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "nextval_call",
    "sequence_inspection_query",
)
_CLEANUP_MODES = (
    "DROP_SEQUENCE_IF_EXISTS",
    "DROP_SEQUENCE_CASCADE",
    "DROP_SEQUENCE",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "already_exists"),
    "privilege_level": (
        "sequence_creator",
        "non_creator_no_privilege",
    ),
    "sequence_type": (
        "permanent",
        "temporary",
        "temporary_short",
        "unlogged",
    ),
}

_CORE_OPTION_AXES: dict[str, tuple[str, ...]] = {
    "as_data_type": (
        "absent_default",
        "bigint",
        "integer",
        "smallint",
    ),
    "increment_direction": ("ascending", "descending"),
    "cycle_clause": ("CYCLE", "NO_CYCLE", "absent_default"),
}

_BOUND_OPTION_AXES: dict[str, tuple[str, ...]] = {
    "minvalue_maxvalue_setting": (
        "absent_defaults",
        "explicit_values",
        "NO_MINVALUE_NO_MAXVALUE",
    ),
    "start_value_setting": ("absent_default", "explicit_start"),
    "cache_value": ("absent_default", "cache_1", "cache_10"),
}

_NAMING_AXES: dict[str, tuple[str, ...]] = {
    "sequence_name_shape": (
        "simple",
        "schema_qualified",
        "quoted",
        "reserved_word",
    ),
    "if_not_exists_clause": ("absent", "present"),
    "owned_by_clause": (
        "absent_default",
        "owned_by_column",
        "owned_by_none",
    ),
}

_OWNERSHIP_AXES: dict[str, tuple[str, ...]] = {
    "owned_by_table_dependency": (
        "table_column_exists",
        "table_column_not_exists",
        "different_owner",
        "different_schema",
    ),
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("privilege_level", "non_creator_no_privilege"),
        ("schema_dependency", "pg_catalog_reserved"),
        ("schema_dependency", "schema_not_exists"),
        ("sequence_name_shape", "non_existent"),
        ("owned_by_table_dependency", "table_column_not_exists"),
        ("owned_by_table_dependency", "different_owner"),
        ("owned_by_table_dependency", "different_schema"),
        ("same_name_conflict", "same_name_table"),
        ("same_name_conflict", "same_name_view"),
        ("incompatible_data_type_values", "smallint_overflow"),
        ("increment_zero", "zero_increment"),
        ("minvalue_greater_than_maxvalue", "min_greater_than_max"),
        ("start_out_of_range", "start_above_maxvalue"),
        ("start_out_of_range", "start_below_minvalue"),
        ("temporary_sequence_with_schema", "temp_with_schema_illegal"),
    }
)

_COMBINATION_GROUP = "create_sequence_required_factor_value_matrix"
_CONSUMER_ACTION = "define_sequence"


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    st = assignment.get("sequence_type", "permanent")
    nsh = assignment.get("sequence_name_shape", "simple")
    # TEMP sequences cannot be schema-qualified.
    if st in ("temporary", "temporary_short") and nsh == "schema_qualified":
        return False
    # owned_by_column + schema_qualified → table/sequence must share a
    # custom schema, which complicates per-script bookend; exclude.
    obc = assignment.get("owned_by_clause", "absent_default")
    if obc == "owned_by_column" and nsh == "schema_qualified":
        return False
    otd = assignment.get("owned_by_table_dependency", "table_column_exists")
    if obc == "owned_by_column" and otd == "table_column_exists":
        # success path — table fixture needed
        pass
    failures = [
        pair
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    ]
    return len(failures) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors from primary values."""

    tos = a.get("object_state", "not_exists")
    ine = a.get("if_not_exists_clause", "absent")
    if tos == "already_exists":
        if ine == "present":
            a["duplicate_sequence_name"] = "with_IF_NOT_EXISTS_noop"
        else:
            a["duplicate_sequence_name"] = "without_IF_NOT_EXISTS_error"

    pl = a.get("privilege_level", "sequence_creator")
    if pl == "non_creator_no_privilege":
        a["insufficient_privilege"] = "no_CREATE_privilege"
    ip = a.get("insufficient_privilege", "has_create_privilege")
    if ip == "no_CREATE_privilege":
        a["privilege_level"] = "non_creator_no_privilege"

    otd = a.get("owned_by_table_dependency", "table_column_exists")
    if otd in ("table_column_not_exists", "different_owner",
               "different_schema"):
        a["owned_by_clause"] = "owned_by_column"

    sd = a.get("schema_dependency", "schema_exists")
    nsh = a.get("sequence_name_shape", "simple")
    if sd == "schema_not_exists":
        a["sequence_name_shape"] = "non_existent"
    if nsh == "non_existent":
        a["schema_dependency"] = "schema_not_exists"

    st = a.get("sequence_type", "permanent")
    ine = a.get("if_not_exists_clause", "absent")
    if st == "permanent":
        a["statement_branch"] = (
            "branch_if_not_exists_permanent"
            if ine == "present" else "branch_permanent"
        )
    elif st == "temporary":
        a["statement_branch"] = (
            "branch_if_not_exists_temporary"
            if ine == "present" else "branch_temporary"
        )
    elif st == "temporary_short":
        a["statement_branch"] = "branch_temp"
    elif st == "unlogged":
        a["statement_branch"] = "branch_unlogged"


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    conditions = _failure_conditions(a)
    if not conditions:
        return None
    condition = conditions[0]
    mapping = {
        "duplicate": ("object_state", "already_exists"),
        "insufficient_privilege": (
            "privilege_level",
            "non_creator_no_privilege",
        ),
        "missing_table": (
            "owned_by_table_dependency",
            "table_column_not_exists",
        ),
        "different_owner": (
            "owned_by_table_dependency",
            "different_owner",
        ),
        "different_schema": (
            "owned_by_table_dependency",
            "different_schema",
        ),
        "name_conflict_table": (
            "same_name_conflict",
            "same_name_table",
        ),
        "name_conflict_view": (
            "same_name_conflict",
            "same_name_view",
        ),
        "pg_catalog_reserved": (
            "schema_dependency",
            "pg_catalog_reserved",
        ),
        "missing_schema": ("schema_dependency", "schema_not_exists"),
        "smallint_overflow": (
            "incompatible_data_type_values",
            "smallint_overflow",
        ),
        "zero_increment": ("increment_zero", "zero_increment"),
        "min_gt_max": (
            "minvalue_greater_than_maxvalue",
            "min_greater_than_max",
        ),
        "start_above": ("start_out_of_range", "start_above_maxvalue"),
        "start_below": ("start_out_of_range", "start_below_minvalue"),
        "temp_schema_qualified": (
            "temporary_sequence_with_schema",
            "temp_with_schema_illegal",
        ),
    }
    return mapping.get(condition)


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
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _extension_multiset_sha256(
    cases: tuple[CreateSequenceFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-sequence-factor-extension-v1\n"
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


def build_create_sequence_factor_extension_plan(
    repository_root: Path,
) -> CreateSequenceFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_sequence")
    if len(catalog_rows) != 70:
        raise CreateSequenceFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateSequenceFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("core_options", _CORE_OPTION_AXES),
        ("bound_options", _BOUND_OPTION_AXES),
        ("naming_options", _NAMING_AXES),
        ("ownership", _OWNERSHIP_AXES),
    ]

    for group_name, behavior_axes in cross_groups:
        behavior_combos = _behavior_combinations(
            {**_GENERAL_AXES, **behavior_axes}
        )
        for behavior in behavior_combos:
            for verification in _VERIFICATION_MODES:
                for cleanup in _CLEANUP_MODES:
                    raw_count += 1
                    full = _full_assignment(
                        behavior, verification, cleanup
                    )
                    failures = _failure_conditions(full)
                    if len(failures) > 1:
                        continue
                    if failures:
                        condition = failures[0]
                        sqlstate, reason = _FAILURE_SQLSTATE[condition]
                        outcome = "expected_failure"
                    else:
                        sqlstate = "00000"
                        reason = None
                        outcome = "success"
                    ordinal += 1
                    sorted_assignment = tuple(sorted(full.items()))
                    derivation_id = (
                        f"CSQ-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        CreateSequenceFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"CREATESEQUENCE{ordinal:05d}",
                            sql_filename=f"CREATESEQUENCE{ordinal:05d}.sql",
                            object_prefix=f"createsequence_{ordinal:05d}_",
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"CREATE SEQUENCE extension: "
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

    plan = CreateSequenceFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateSequenceFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateSequenceFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    expected_ord = list(
        range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))
    )
    if ordinals != expected_ord:
        raise CreateSequenceFactorExtensionError("ordinal gap")
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateSequenceFactorExtensionError("duplicate case_id")
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateSequenceFactorExtensionError("duplicate sql_filename")
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateSequenceFactorExtensionError("unknown outcome")
    if not all(
        case.derivation_id.startswith("CSQ-EXT|")
        for case in plan.cases
    ):
        raise CreateSequenceFactorExtensionError("derivation_id drift")
    return plan


__all__ = [
    "CreateSequenceFactorExtensionError",
    "CreateSequenceFactorExtensionCase",
    "CreateSequenceFactorExtensionPlan",
    "build_create_sequence_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
