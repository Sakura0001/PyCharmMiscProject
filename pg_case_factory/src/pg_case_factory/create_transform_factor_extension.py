"""Bounded post-coverage extension plan for CREATE TRANSFORM factor regress.

The baseline :mod:`create_transform_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE TRANSFORM is a catalog-row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_transform`` catalog row (not a ``pg_class`` relation) is
the semantic witness target.

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
from .create_transform_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateTransformFactorExtensionError(ValueError):
    """Raised when CREATE TRANSFORM extension input drifts."""


@dataclass(frozen=True)
class CreateTransformFactorExtensionCase:
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
class CreateTransformFactorExtensionPlan:
    cases: tuple[CreateTransformFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 59
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_transform",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_transform",
    "drop_type",
    "drop_function",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "exists"),
    "or_replace_clause": ("omitted", "present"),
}

_STATEMENT_DIRECTION_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_transform",
        "branch_create_or_replace_transform",
    ),
    "transform_direction": (
        "both_from_and_to_sql",
        "only_from_sql",
        "only_to_sql",
    ),
}

_TYPE_NAME_AXES: dict[str, tuple[str, ...]] = {
    "type_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "nonexistent_name",
    ),
}

_LANGUAGE_NAME_AXES: dict[str, tuple[str, ...]] = {
    "language_name_shape": ("simple_id", "nonexistent_name"),
}

_FUNCTION_NAME_AXES: dict[str, tuple[str, ...]] = {
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
}

_TYPE_EXISTENCE_AXES: dict[str, tuple[str, ...]] = {
    "type_existence": ("type_exists", "type_not_exists"),
}

_LANGUAGE_EXISTENCE_AXES: dict[str, tuple[str, ...]] = {
    "language_existence": ("language_exists", "language_not_exists"),
}

_FUNCTION_EXISTENCE_AXES: dict[str, tuple[str, ...]] = {
    "function_existence": (
        "all_functions_exist",
        "some_functions_missing",
    ),
}

_PRIVILEGE_TYPE_AXES: dict[str, tuple[str, ...]] = {
    "privilege_on_type": (
        "owner_with_usage",
        "non_owner_with_usage",
        "no_usage_privilege",
    ),
}

_PRIVILEGE_LANGUAGE_AXES: dict[str, tuple[str, ...]] = {
    "privilege_on_language": ("has_usage", "no_usage"),
}

_PRIVILEGE_FUNCTION_AXES: dict[str, tuple[str, ...]] = {
    "privilege_on_function": (
        "owner_with_execute",
        "no_execute_privilege",
    ),
}

_SIGNATURE_AXES: dict[str, tuple[str, ...]] = {
    "function_signature_mismatch": (
        "signature_matches",
        "signature_mismatch",
    ),
}

_TYPE_FUNCTION_NAME_AXES: dict[str, tuple[str, ...]] = {
    "type_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "nonexistent_name",
    ),
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
}

_TYPE_LANGUAGE_EXISTENCE_AXES: dict[str, tuple[str, ...]] = {
    "type_existence": ("type_exists", "type_not_exists"),
    "language_existence": ("language_exists", "language_not_exists"),
}

_DIRECTION_FUNCTION_EXISTENCE_AXES: dict[str, tuple[str, ...]] = {
    "transform_direction": (
        "both_from_and_to_sql",
        "only_from_sql",
        "only_to_sql",
    ),
    "function_existence": (
        "all_functions_exist",
        "some_functions_missing",
    ),
}

_ALL_PRIVILEGE_AXES: dict[str, tuple[str, ...]] = {
    "privilege_on_type": (
        "owner_with_usage",
        "non_owner_with_usage",
        "no_usage_privilege",
    ),
    "privilege_on_language": ("has_usage", "no_usage"),
    "privilege_on_function": (
        "owner_with_execute",
        "no_execute_privilege",
    ),
}

_TYPE_SHAPE_EXISTENCE_AXES: dict[str, tuple[str, ...]] = {
    "type_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "nonexistent_name",
    ),
    "type_existence": ("type_exists", "type_not_exists"),
}

_LANGUAGE_SHAPE_EXISTENCE_AXES: dict[str, tuple[str, ...]] = {
    "language_name_shape": ("simple_id", "nonexistent_name"),
    "language_existence": ("language_exists", "language_not_exists"),
}

_FUNCTION_SHAPE_EXISTENCE_AXES: dict[str, tuple[str, ...]] = {
    "function_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "nonexistent_name",
    ),
    "function_existence": (
        "all_functions_exist",
        "some_functions_missing",
    ),
}

_DIRECTION_TYPE_SHAPE_AXES: dict[str, tuple[str, ...]] = {
    "transform_direction": (
        "both_from_and_to_sql",
        "only_from_sql",
        "only_to_sql",
    ),
    "type_name_shape": (
        "simple_id",
        "schema_qualified_id",
        "quoted_id",
        "nonexistent_name",
    ),
}

# Representative failure (factor, value) pairs — one per failure scenario.
# The duplicate failure is conditional (object_state=exists +
# or_replace_clause=omitted) and handled separately in
# _failure_unit_count / _present_failure_pair via the derived
# duplicate_transform factor.
_CROSSED_NEGATIVES = frozenset(
    {
        ("type_existence", "type_not_exists"),
        ("language_existence", "language_not_exists"),
        ("function_existence", "some_functions_missing"),
        ("type_name_shape", "nonexistent_name"),
        ("language_name_shape", "nonexistent_name"),
        ("function_name_shape", "nonexistent_name"),
        ("function_signature_mismatch", "signature_mismatch"),
        ("privilege_on_type", "no_usage_privilege"),
        ("privilege_on_language", "no_usage"),
        ("privilege_on_function", "no_execute_privilege"),
    }
)

_DUPLICATE_FAILURE: tuple[str, str] = (
    "duplicate_transform",
    "existing_transform_without_or_replace",
)

_COMBINATION_GROUP = (
    "create_transform_required_factor_value_matrix"
)

_CONSUMER_ACTION = "define_transform"


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = sum(
        1
        for factor, value in _CROSSED_NEGATIVES
        if assignment.get(factor) == value
    )
    if (
        assignment.get("duplicate_transform")
        == "existing_transform_without_or_replace"
    ):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    if (
        assignment.get("duplicate_transform")
        == "existing_transform_without_or_replace"
    ):
        return _DUPLICATE_FAILURE
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    if (
        "statement_branch" in assignment
        and "or_replace_clause" in assignment
    ):
        sb = assignment["statement_branch"]
        orc = assignment["or_replace_clause"]
        if (
            sb == "branch_create_or_replace_transform"
            and orc != "present"
        ):
            return False
        if (
            sb == "branch_create_transform"
            and orc != "omitted"
        ):
            return False

    return _failure_unit_count(assignment) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

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
    if (
        pof == "no_execute_privilege"
        or ifp == "lacks_privilege"
    ):
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
        a["duplicate_transform"] = (
            "existing_transform_without_or_replace"
        )
    else:
        a["duplicate_transform"] = "no_conflict"

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
    cases: tuple[CreateTransformFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-transform-factor-extension-v1\n"
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


def build_create_transform_factor_extension_plan(
    repository_root: Path,
) -> CreateTransformFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_transform")
    if len(catalog_rows) != 58:
        raise CreateTransformFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateTransformFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("statement_direction", _STATEMENT_DIRECTION_AXES),
        ("type_name", _TYPE_NAME_AXES),
        ("language_name", _LANGUAGE_NAME_AXES),
        ("function_name", _FUNCTION_NAME_AXES),
        ("type_existence", _TYPE_EXISTENCE_AXES),
        ("language_existence", _LANGUAGE_EXISTENCE_AXES),
        ("function_existence", _FUNCTION_EXISTENCE_AXES),
        ("privilege_type", _PRIVILEGE_TYPE_AXES),
        ("privilege_language", _PRIVILEGE_LANGUAGE_AXES),
        ("privilege_function", _PRIVILEGE_FUNCTION_AXES),
        ("signature", _SIGNATURE_AXES),
        ("type_function_name", _TYPE_FUNCTION_NAME_AXES),
        (
            "type_language_existence",
            _TYPE_LANGUAGE_EXISTENCE_AXES,
        ),
        (
            "direction_function_existence",
            _DIRECTION_FUNCTION_EXISTENCE_AXES,
        ),
        ("all_privilege", _ALL_PRIVILEGE_AXES),
        (
            "type_shape_existence",
            _TYPE_SHAPE_EXISTENCE_AXES,
        ),
        (
            "language_shape_existence",
            _LANGUAGE_SHAPE_EXISTENCE_AXES,
        ),
        (
            "function_shape_existence",
            _FUNCTION_SHAPE_EXISTENCE_AXES,
        ),
        (
            "direction_type_shape",
            _DIRECTION_TYPE_SHAPE_AXES,
        ),
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
                            CreateTransformFactorExtensionError(
                                "duplicate factor key in assignment"
                            )
                        )
                    outcome, sqlstate, reason = _outcome_for(full)
                    ordinal += 1
                    sorted_assignment = tuple(sorted(full.items()))
                    derivation_id = (
                        f"CTR-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        CreateTransformFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=(
                                f"CREATETRANSFORM{ordinal:05d}"
                            ),
                            sql_filename=(
                                f"CREATETRANSFORM{ordinal:05d}.sql"
                            ),
                            object_prefix=(
                                f"createtransform_{ordinal:05d}_"
                            ),
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"CREATE TRANSFORM extension: "
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

    plan = CreateTransformFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateTransformFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateTransformFactorExtensionError(
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
        raise CreateTransformFactorExtensionError(
            "extension ordinal gap"
        )
    if (
        len({case.case_id for case in plan.cases})
        != len(plan.cases)
    ):
        raise CreateTransformFactorExtensionError(
            "duplicate extension case_id"
        )
    if (
        len({case.sql_filename for case in plan.cases})
        != len(plan.cases)
    ):
        raise CreateTransformFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateTransformFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("CTR-EXT|")
        for case in plan.cases
    ):
        raise CreateTransformFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateTransformFactorExtensionError",
    "CreateTransformFactorExtensionCase",
    "CreateTransformFactorExtensionPlan",
    "build_create_transform_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_DUPLICATE_FAILURE",
    "_present_failure_pair",
    "_failure_unit_count",
    "_extension_multiset_sha256",
]
