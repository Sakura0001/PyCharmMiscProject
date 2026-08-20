"""Bounded post-coverage extension plan for CREATE USER MAPPING factor regress.

The baseline :mod:`create_user_mapping_factor_loop` assigns one local
SQL program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This
module crosses the main-axis factor values with verification/cleanup
axes under an at-most-one-failure attribution policy, producing a
bounded set of additional regress programs that exercise pairwise factor
interactions.

CREATE USER MAPPING is a catalog-row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_user_mapping`` catalog row (not a ``pg_class`` relation)
is the semantic witness target.  The foreign server and foreign data
wrapper fixtures are always set up and torn down per case.

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
from .create_user_mapping_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateUserMappingFactorExtensionError(ValueError):
    """Raised when CREATE USER MAPPING extension input drifts."""


@dataclass(frozen=True)
class CreateUserMappingFactorExtensionCase:
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
class CreateUserMappingFactorExtensionPlan:
    cases: tuple[CreateUserMappingFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 46
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_user_mapping",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_user_mapping",
    "drop_server",
    "drop_fdw",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "exists"),
    "privilege_level": (
        "server_owner",
        "user_with_usage",
        "non_privileged",
    ),
}

_CORE_DEFINITION_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_user_mapping",
        "branch_create_user_mapping_if_not_exists",
    ),
    "if_not_exists_clause": ("omitted", "present"),
    "options_clause": ("omitted", "single_option", "multiple_options"),
}

_USER_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_user_mapping",
        "branch_create_user_mapping_if_not_exists",
    ),
    "if_not_exists_clause": ("omitted", "present"),
    "user_specification": (
        "named_user",
        "user_keyword",
        "current_role",
        "current_user",
        "public",
    ),
}

_SERVER_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_user_mapping",
        "branch_create_user_mapping_if_not_exists",
    ),
    "if_not_exists_clause": ("omitted", "present"),
    "server_name_shape": ("simple_id", "nonexistent_name"),
    "option_value_shape": (
        "valid_value",
        "quoted_value",
        "duplicate_option_name",
    ),
}

_FULL_CROSS_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_user_mapping",
        "branch_create_user_mapping_if_not_exists",
    ),
    "if_not_exists_clause": ("omitted", "present"),
    "options_clause": ("omitted", "single_option", "multiple_options"),
    "user_specification": (
        "named_user",
        "user_keyword",
        "current_role",
        "current_user",
        "public",
    ),
    "server_name_shape": ("simple_id", "nonexistent_name"),
    "option_value_shape": (
        "valid_value",
        "quoted_value",
        "duplicate_option_name",
    ),
}

_USER_SHAPE_AXES: dict[str, tuple[str, ...]] = {
    "user_specification": (
        "named_user",
        "user_keyword",
        "current_role",
        "current_user",
        "public",
    ),
    "user_name_shape": (
        "simple_id",
        "quoted_id",
        "nonexistent_name",
        "public_keyword",
    ),
}

_USER_SERVER_AXES: dict[str, tuple[str, ...]] = {
    "user_specification": (
        "named_user",
        "user_keyword",
        "current_role",
        "current_user",
        "public",
    ),
    "server_name_shape": ("simple_id", "nonexistent_name"),
    "option_value_shape": (
        "valid_value",
        "quoted_value",
        "duplicate_option_name",
    ),
}

_CORE_USER_SERVER_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_user_mapping",
        "branch_create_user_mapping_if_not_exists",
    ),
    "if_not_exists_clause": ("omitted", "present"),
    "user_specification": (
        "named_user",
        "user_keyword",
        "current_role",
        "current_user",
        "public",
    ),
    "server_name_shape": ("simple_id", "nonexistent_name"),
}

_OPTIONS_USER_AXES: dict[str, tuple[str, ...]] = {
    "options_clause": ("omitted", "single_option", "multiple_options"),
    "user_specification": (
        "named_user",
        "user_keyword",
        "current_role",
        "current_user",
        "public",
    ),
    "option_value_shape": (
        "valid_value",
        "quoted_value",
        "duplicate_option_name",
    ),
}

# Representative failure (factor, value) pairs — one per failure scenario.
# Overlapping T5 values are derived, not crossed, so they are NOT listed
# here (would double-count a single failure and break attribution).
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "exists"),
        ("privilege_level", "non_privileged"),
        ("server_name_shape", "nonexistent_name"),
        ("option_value_shape", "duplicate_option_name"),
        ("user_name_shape", "nonexistent_name"),
    }
)

_COMBINATION_GROUP = (
    "create_user_mapping_required_factor_value_matrix"
)

_CONSUMER_ACTION = "define_mapping"


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

    # branch consistency — only when both are explicitly present
    if "statement_branch" in assignment and "if_not_exists_clause" in assignment:
        sb = assignment["statement_branch"]
        ine = assignment["if_not_exists_clause"]
        if sb == "branch_create_user_mapping_if_not_exists" and ine != "present":
            return False
        if sb == "branch_create_user_mapping" and ine != "omitted":
            return False

    return _failure_unit_count(assignment) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    # --- branch cluster (bidirectional, read-then-write) ---
    sb = a.get("statement_branch", "branch_create_user_mapping")
    ine = a.get("if_not_exists_clause", "omitted")
    if sb == "branch_create_user_mapping_if_not_exists" or ine == "present":
        a["statement_branch"] = "branch_create_user_mapping_if_not_exists"
        a["if_not_exists_clause"] = "present"
    else:
        a["statement_branch"] = "branch_create_user_mapping"
        a["if_not_exists_clause"] = "omitted"

    # --- privilege cluster ---
    pl = a.get("privilege_level", "server_owner")
    if pl == "non_privileged":
        a["insufficient_privilege"] = "lacks_privilege"
    else:
        a["insufficient_privilege"] = "has_privilege"

    # --- server dependency cluster ---
    sns = a.get("server_name_shape", "simple_id")
    se = a.get("server_existence", "server_exists")
    ns = a.get("nonexistent_server", "server_exists")
    sd = a.get("server_dependency", "server_exists_and_valid")
    server_missing = (
        sns == "nonexistent_name"
        or se == "server_not_exists"
        or ns == "server_missing"
        or sd == "server_missing"
    )
    if server_missing:
        a["server_name_shape"] = "nonexistent_name"
        a["server_existence"] = "server_not_exists"
        a["nonexistent_server"] = "server_missing"
        a["server_dependency"] = "server_missing"
    else:
        a["server_name_shape"] = "simple_id"
        a["server_existence"] = "server_exists"
        a["nonexistent_server"] = "server_exists"
        a["server_dependency"] = "server_exists_and_valid"

    # --- duplicate cluster ---
    os_state = a.get("object_state", "not_exists")
    dm = a.get("duplicate_mapping", "no_conflict")
    if os_state == "exists" or dm == "existing_mapping_without_if_not_exists":
        a["object_state"] = "exists"
        a["duplicate_mapping"] = "existing_mapping_without_if_not_exists"
    else:
        a["object_state"] = "not_exists"
        a["duplicate_mapping"] = "no_conflict"

    # --- options cluster ---
    ovs = a.get("option_value_shape", "valid_value")
    don = a.get("duplicate_option_name", "unique_options")
    if ovs == "duplicate_option_name" or don == "duplicate_option":
        a["option_value_shape"] = "duplicate_option_name"
        a["duplicate_option_name"] = "duplicate_option"
    else:
        a["option_value_shape"] = "valid_value"
        a["duplicate_option_name"] = "unique_options"

    # --- user cluster (public consistency) ---
    us = a.get("user_specification", "named_user")
    uns = a.get("user_name_shape", "simple_id")
    if us == "public" and uns != "nonexistent_name":
        a["user_name_shape"] = "public_keyword"

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
    cases: tuple[CreateUserMappingFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-user-mapping-factor-extension-v1\n"
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


def build_create_user_mapping_factor_extension_plan(
    repository_root: Path,
) -> CreateUserMappingFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_user_mapping")
    if len(catalog_rows) != 45:
        raise CreateUserMappingFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateUserMappingFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("core_definition", _CORE_DEFINITION_AXES),
        ("user", _USER_AXES),
        ("server", _SERVER_AXES),
        ("full_cross", _FULL_CROSS_AXES),
        ("user_shape", _USER_SHAPE_AXES),
        ("user_server", _USER_SERVER_AXES),
        ("core_user_server", _CORE_USER_SERVER_AXES),
        ("options_user", _OPTIONS_USER_AXES),
        ("core_definition", _CORE_DEFINITION_AXES),
    ]

    seen_keys: set[tuple[tuple[str, str], ...]] = set()
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
                            CreateUserMappingFactorExtensionError(
                                "duplicate factor key in assignment"
                            )
                        )
                    sorted_assignment = tuple(sorted(full.items()))
                    if sorted_assignment in seen_keys:
                        continue
                    seen_keys.add(sorted_assignment)
                    outcome, sqlstate, reason = _outcome_for(full)
                    ordinal += 1
                    derivation_id = (
                        f"CUM-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        CreateUserMappingFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=(
                                f"CREATEUSERMAPPING{ordinal:05d}"
                            ),
                            sql_filename=(
                                f"CREATEUSERMAPPING{ordinal:05d}.sql"
                            ),
                            object_prefix=(
                                f"createusermapping_{ordinal:05d}_"
                            ),
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"CREATE USER MAPPING extension: "
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

    plan = CreateUserMappingFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateUserMappingFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateUserMappingFactorExtensionError(
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
        raise CreateUserMappingFactorExtensionError(
            "extension ordinal gap"
        )
    if (
        len({case.case_id for case in plan.cases})
        != len(plan.cases)
    ):
        raise CreateUserMappingFactorExtensionError(
            "duplicate extension case_id"
        )
    if (
        len({case.sql_filename for case in plan.cases})
        != len(plan.cases)
    ):
        raise CreateUserMappingFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateUserMappingFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("CUM-EXT|")
        for case in plan.cases
    ):
        raise CreateUserMappingFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateUserMappingFactorExtensionError",
    "CreateUserMappingFactorExtensionCase",
    "CreateUserMappingFactorExtensionPlan",
    "build_create_user_mapping_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
