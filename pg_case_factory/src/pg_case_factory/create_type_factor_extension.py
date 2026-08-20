"""Bounded post-coverage extension plan for CREATE TYPE factor regress.

The baseline :mod:`create_type_factor_loop` assigns one local SQL program
to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module crosses
the branch-specific factor values (composite attributes, enum labels,
range subtypes/options, base-type options) with the naming, privilege and
verification/cleanup axes under an at-most-one-failure attribution
policy, producing a bounded set of additional regress programs that
exercise pairwise factor interactions.

CREATE TYPE is a catalog-row DDL statement — it does not create tables,
so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_type`` catalog row is the semantic witness target.

The extension is deterministic: given the same repository root, it
always produces the same frozen multiset SHA-256 and the same contiguous
case ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_type_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateTypeFactorExtensionError(ValueError):
    """Raised when CREATE TYPE extension input drifts."""


@dataclass(frozen=True)
class CreateTypeFactorExtensionCase:
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
class CreateTypeFactorExtensionPlan:
    cases: tuple[CreateTypeFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 96
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_type_catalog_query",
    "information_schema_user_defined_types",
    "SELECT_type_query",
)
_CLEANUP_MODES = (
    "DROP_TYPE",
    "DROP_TYPE_IF_EXISTS",
    "DROP_TYPE_CASCADE",
)

_BRANCH_COMPOSITE = "branch_composite"
_BRANCH_ENUM = "branch_enum"
_BRANCH_RANGE = "branch_range"
_BRANCH_BASE = "branch_base"

_BRANCH_FORM: dict[str, str] = {
    _BRANCH_COMPOSITE: "composite",
    _BRANCH_ENUM: "enum",
    _BRANCH_RANGE: "range",
    _BRANCH_BASE: "base",
    "branch_shell": "shell",
}

# Independent (non-overlapping) failure values safe to cross.  Overlapping
# cluster members (insufficient_privilege, duplicate_type_name) are derived,
# not crossed, so they are NOT listed here (would double-count a single
# failure and break attribution).
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("schema_dependency", "schema_not_exists"),
        ("invalid_data_type_in_attribute", "unknown_type"),
        ("function_dependency", "input_output_functions_not_exist"),
        ("missing_required_functions", "no_input_function"),
        ("missing_required_functions", "no_output_function"),
        ("subtype_opclass_dependency", "opclass_not_exists"),
        ("canonical_function_dependency", "function_not_exists"),
        ("subtype_diff_dependency", "function_not_exists"),
        ("subtype_no_btree_opclass", "no_opclass"),
        ("privilege_level", "non_owner"),
    }
)

_COMBINATION_GROUP = "create_type_required_factor_value_matrix"
_CONSUMER_ACTION = "define_composite"

# Branch-pinned cross groups.  Each group pins its statement_branch (and
# type_form) so branch-specific factors never appear under a foreign form.
_BRANCH_GROUPS: list[tuple[str, str, dict[str, tuple[str, ...]]]] = [
    (
        "composite_attributes",
        _BRANCH_COMPOSITE,
        {
            "attribute_count": (
                "zero_attributes",
                "single_attribute",
                "multiple_attributes",
            ),
            "attribute_data_type": (
                "integer", "bigint", "text", "varchar", "numeric",
                "boolean", "date", "timestamp", "jsonb", "uuid",
            ),
            "attribute_name_shape": ("simple", "quoted", "reserved_word"),
        },
    ),
    (
        "enum_labels",
        _BRANCH_ENUM,
        {
            "enum_label_count": (
                "zero_labels", "single_label", "multiple_labels",
            ),
            "enum_label_shape": (
                "simple_label", "quoted_label", "long_label",
            ),
        },
    ),
    (
        "range_suboptions",
        _BRANCH_RANGE,
        {
            "range_subtype": (
                "integer", "bigint", "numeric", "float8",
                "timestamp", "timestamptz", "date",
            ),
            "range_option_completeness": (
                "minimal", "with_opclass", "with_canonical",
                "with_subtype_diff", "with_multirange_name",
            ),
        },
    ),
    (
        "base_options",
        _BRANCH_BASE,
        {
            "base_type_option_completeness": (
                "required_only", "with_optional_functions", "with_all_options",
            ),
            "base_type_io_functions": (
                "with_shell_type_first", "without_shell_type",
            ),
        },
    ),
    (
        "composite_attr_name",
        _BRANCH_COMPOSITE,
        {
            "attribute_data_type": (
                "integer", "bigint", "text", "varchar", "numeric",
                "boolean", "date", "timestamp", "jsonb", "uuid",
            ),
            "type_name_shape": (
                "simple", "quoted", "reserved_word",
                "underscore_prefix", "schema_qualified",
            ),
        },
    ),
    (
        "enum_label_name",
        _BRANCH_ENUM,
        {
            "enum_label_count": (
                "zero_labels", "single_label", "multiple_labels",
            ),
            "enum_label_shape": (
                "simple_label", "quoted_label", "long_label",
            ),
            "type_name_shape": (
                "simple", "quoted", "reserved_word",
                "underscore_prefix", "schema_qualified",
            ),
        },
    ),
    (
        "range_subopc",
        _BRANCH_RANGE,
        {
            "range_subtype": (
                "integer", "bigint", "numeric", "float8",
                "timestamp", "timestamptz", "date",
            ),
            "range_option_completeness": (
                "minimal", "with_opclass", "with_canonical",
                "with_subtype_diff", "with_multirange_name",
            ),
            "subtype_opclass_dependency": (
                "opclass_exists", "opclass_not_exists",
            ),
        },
    ),
    (
        "composite_boundary",
        _BRANCH_COMPOSITE,
        {
            "attribute_count": (
                "zero_attributes", "single_attribute", "multiple_attributes",
            ),
            "invalid_data_type_in_attribute": ("unknown_type",),
        },
    ),
    (
        "range_boundary_deps",
        _BRANCH_RANGE,
        {
            "range_subtype": (
                "integer", "bigint", "numeric", "float8",
                "timestamp", "timestamptz", "date",
            ),
            "subtype_opclass_dependency": (
                "opclass_exists", "opclass_not_exists",
            ),
            "canonical_function_dependency": (
                "function_exists", "function_not_exists",
            ),
        },
    ),
    (
        "base_boundary",
        _BRANCH_BASE,
        {
            "base_type_option_completeness": (
                "required_only", "with_optional_functions", "with_all_options",
            ),
            "function_dependency": (
                "input_output_functions_exist",
                "input_output_functions_not_exist",
            ),
            "missing_required_functions": (
                "no_input_function", "no_output_function",
            ),
        },
    ),
]

# Branch-agnostic cross groups (use the default composite form).
_GENERAL_AXES: list[tuple[str, dict[str, tuple[str, ...]]]] = [
    (
        "naming_state",
        {
            "type_name_shape": (
                "simple", "quoted", "reserved_word",
                "underscore_prefix", "schema_qualified",
            ),
            "object_state": ("not_exists", "already_exists"),
            "schema_dependency": ("schema_exists", "schema_not_exists"),
        },
    ),
    (
        "privilege_naming",
        {
            "type_name_shape": (
                "simple", "quoted", "reserved_word",
                "underscore_prefix", "schema_qualified",
            ),
            "privilege_level": ("superuser", "type_owner", "non_owner"),
            "object_state": ("not_exists", "already_exists"),
        },
    ),
]


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

    return _failure_unit_count(assignment) <= 1


def _sync_branch_form(a: dict[str, str]) -> None:
    branch = a.get("statement_branch", _BRANCH_COMPOSITE)
    a["statement_branch"] = branch
    a["type_form"] = _BRANCH_FORM.get(branch, "composite")


def _derive_privilege_cluster(a: dict[str, str]) -> None:
    ip = a.get("insufficient_privilege")
    if ip == "non_superuser_base_type":
        a["privilege_level"] = "non_owner"
        a["statement_branch"] = _BRANCH_BASE
        a["type_form"] = "base"
        return
    if ip == "non_owner_create":
        a["privilege_level"] = "non_owner"
        return
    pl = a.get("privilege_level", "type_owner")
    if pl == "non_owner":
        a["insufficient_privilege"] = "non_owner_create"


def _derive_duplicate_cluster(a: dict[str, str]) -> None:
    os_state = a.get("object_state", "not_exists")
    dtn = a.get("duplicate_type_name")
    if dtn in {"with_existing_type", "with_existing_table"}:
        a["object_state"] = "already_exists"
        return
    if os_state == "already_exists" and "duplicate_type_name" not in a:
        a["duplicate_type_name"] = "with_existing_type"


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    _sync_branch_form(a)
    _derive_privilege_cluster(a)
    _sync_branch_form(a)
    _derive_duplicate_cluster(a)
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
    cases: tuple[CreateTypeFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"create-type-factor-extension-v1\n")
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
                    "expected_failure_reason": case.expected_failure_reason,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _build_branch_group_cases(
    group_name: str,
    branch: str,
    behavior_axes: dict[str, tuple[str, ...]],
    ordinal_ref: list[int],
    cases: list[CreateTypeFactorExtensionCase],
) -> int:
    axes = dict(behavior_axes)
    axes["statement_branch"] = (branch,)
    axes["type_form"] = (_BRANCH_FORM[branch],)
    raw = 0
    for behavior in _behavior_combinations(axes):
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                full = _full_assignment(behavior, verification, cleanup)
                if not _is_valid_combination(full):
                    continue
                if len(full) != len(set(full)):
                    raise CreateTypeFactorExtensionError(
                        "duplicate factor key in assignment"
                    )
                ordinal_ref[0] += 1
                ordinal = ordinal_ref[0]
                outcome, sqlstate, reason = _outcome_for(full)
                derivation_id = (
                    f"CT-EXT|{ordinal:05d}|"
                    f"{verification}|{cleanup}|{group_name}"
                )
                cases.append(
                    CreateTypeFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATETYPE{ordinal:05d}",
                        sql_filename=f"CREATETYPE{ordinal:05d}.sql",
                        object_prefix=f"createtype_{ordinal:05d}_",
                        derivation_id=derivation_id,
                        derived_from_combination_group=_COMBINATION_GROUP,
                        derivation_reason=(
                            f"CREATE TYPE extension: group={group_name}, "
                            f"verification={verification}, cleanup={cleanup}"
                        ),
                        factor_assignment=tuple(sorted(full.items())),
                        consumer_action_id=_CONSUMER_ACTION,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                    )
                )
    return raw


def _build_general_group_cases(
    group_name: str,
    behavior_axes: dict[str, tuple[str, ...]],
    ordinal_ref: list[int],
    cases: list[CreateTypeFactorExtensionCase],
) -> int:
    raw = 0
    for behavior in _behavior_combinations(behavior_axes):
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                full = _full_assignment(behavior, verification, cleanup)
                if not _is_valid_combination(full):
                    continue
                if len(full) != len(set(full)):
                    raise CreateTypeFactorExtensionError(
                        "duplicate factor key in assignment"
                    )
                ordinal_ref[0] += 1
                ordinal = ordinal_ref[0]
                outcome, sqlstate, reason = _outcome_for(full)
                derivation_id = (
                    f"CT-EXT|{ordinal:05d}|"
                    f"{verification}|{cleanup}|{group_name}"
                )
                cases.append(
                    CreateTypeFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATETYPE{ordinal:05d}",
                        sql_filename=f"CREATETYPE{ordinal:05d}.sql",
                        object_prefix=f"createtype_{ordinal:05d}_",
                        derivation_id=derivation_id,
                        derived_from_combination_group=_COMBINATION_GROUP,
                        derivation_reason=(
                            f"CREATE TYPE extension: group={group_name}, "
                            f"verification={verification}, cleanup={cleanup}"
                        ),
                        factor_assignment=tuple(sorted(full.items())),
                        consumer_action_id=_CONSUMER_ACTION,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                    )
                )
    return raw


def build_create_type_factor_extension_plan(
    repository_root: Path,
) -> CreateTypeFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_type")
    if len(catalog_rows) != 91:
        raise CreateTypeFactorExtensionError("catalog row count drift")

    cases: list[CreateTypeFactorExtensionCase] = []
    raw_count = 0
    ordinal_ref = [_BASELINE_COUNT]

    for group_name, branch, axes in _BRANCH_GROUPS:
        raw_count += _build_branch_group_cases(
            group_name, branch, axes, ordinal_ref, cases
        )
    for group_name, axes in _GENERAL_AXES:
        raw_count += _build_general_group_cases(
            group_name, axes, ordinal_ref, cases
        )

    dropped = max(0, raw_count - len(cases))
    if len(cases) > _CAP:
        cases = cases[: _CAP]

    plan = CreateTypeFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateTypeFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateTypeFactorExtensionError("extension case count exceeds cap")
    ordinals = [case.ordinal for case in plan.cases]
    expected_ordinals = list(
        range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))
    )
    if ordinals != expected_ordinals:
        raise CreateTypeFactorExtensionError("extension ordinal gap")
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateTypeFactorExtensionError("duplicate extension case_id")
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateTypeFactorExtensionError("duplicate extension sql_filename")
    if not all(
        case.outcome in ("success", "expected_failure") for case in plan.cases
    ):
        raise CreateTypeFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("CT-EXT|") for case in plan.cases
    ):
        raise CreateTypeFactorExtensionError("extension derivation_id prefix drift")
    return plan


__all__ = [
    "CreateTypeFactorExtensionError",
    "CreateTypeFactorExtensionCase",
    "CreateTypeFactorExtensionPlan",
    "build_create_type_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
