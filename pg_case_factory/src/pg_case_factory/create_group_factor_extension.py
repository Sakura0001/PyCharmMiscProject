"""Bounded post-coverage extension plan for CREATE GROUP factor regress.

The baseline :mod:`create_group_factor_loop` assigns one local SQL program
to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module crosses the
main-axis factor values with verification/cleanup axes under an
at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE GROUP is a deprecated alias for CREATE ROLE -- it targets a
``pg_catalog.pg_authid`` catalog row, not a ``pg_class`` relation, so it
does not create tables and the bookend (DROP TABLE IF EXISTS) is never
emitted.

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
from .create_group_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateGroupFactorExtensionError(ValueError):
    """Raised when CREATE GROUP extension input drifts."""


@dataclass(frozen=True)
class CreateGroupFactorExtensionCase:
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
class CreateGroupFactorExtensionPlan:
    cases: tuple[CreateGroupFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 66
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_authid_catalog_query",
    "pg_roles_view_query",
    "error_assertion",
)
_CLEANUP_MODES = ("drop_group", "drop_role", "referenced_role_cleanup")

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "already_exists"),
    "privilege_level": (
        "createrole_privilege",
        "non_createrole",
        "superuser",
    ),
}

_BEHAVIOR_AXES: dict[str, tuple[str, ...]] = {
    "login_option": ("nologin_default", "login"),
    "password_option": (
        "omitted",
        "password_value",
        "password_null",
        "encrypted_password",
    ),
}

# (factor, value) pairs that represent an active failure in a combination.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("privilege_level", "non_createrole"),
    }
)

_COMBINATION_GROUP = "create_group_required_factor_value_matrix"

_CONSUMER_ACTION = "create_group_with_options"


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    failures = [
        pair
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    ]
    return len(failures) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors from T1-T4 values in extension."""

    if a.get("object_state") == "already_exists":
        a["duplicate_group_name"] = "same_name_conflict"
        a["group_name_shape"] = "duplicate_name"
    else:
        a["duplicate_group_name"] = "no_conflict"
        a["group_name_shape"] = "simple_id"

    if a.get("privilege_level") == "non_createrole":
        a["insufficient_privilege"] = "lacks_createrole"
    else:
        a["insufficient_privilege"] = "has_createrole"

    if a.get("superuser_option") == "superuser":
        a["privilege_level"] = "superuser"
        a["insufficient_privilege"] = "has_createrole"

    po = a.get("password_option", "omitted")
    if po == "password_null":
        a["password_shape"] = "null_password"
    elif po == "encrypted_password":
        a["encrypted_keyword_ignored"] = "encrypted_ignored"
        a["deprecated_aliases"] = "encrypted_ignored"
        a["password_shape"] = "valid_password"
    else:
        a["password_shape"] = "valid_password"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    if a.get("object_state") == "already_exists":
        conditions.append("duplicate")
    if a.get("privilege_level") == "non_createrole":
        conditions.append("insufficient_privilege")
    return conditions


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_role_provisional"),
    "insufficient_privilege": (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _behavior_combinations() -> list[dict[str, str]]:
    """Cartesian product of general + behavior axes, filtered."""

    general_items = list(_GENERAL_AXES.items())
    behavior_items = list(_BEHAVIOR_AXES.items())

    all_keys = [k for k, _ in general_items] + [
        k for k, _ in behavior_items
    ]
    all_value_lists = [v for _, v in general_items] + [
        v for _, v in behavior_items
    ]

    combos: list[dict[str, str]] = []
    for values in itertools.product(*all_value_lists):
        assignment = dict(zip(all_keys, values))
        if _is_valid_combination(assignment):
            combos.append(assignment)
    return combos


def _full_assignment(
    behavior: dict[str, str],
    verification: str,
    cleanup: str,
) -> dict[str, str]:
    a: dict[str, str] = dict(_BASELINE_DEFAULTS)
    a["statement_branch"] = "branch_create_group_with_options"
    a["with_clause"] = "specified"
    for key, value in behavior.items():
        a[key] = value
    a["verification_mode"] = verification
    a["cleanup_mode"] = cleanup
    _derive_t5_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _extension_multiset_sha256(
    cases: tuple[CreateGroupFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-group-factor-extension-v1\n"
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


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    if a.get("object_state") == "already_exists":
        return ("object_state", "already_exists")
    if a.get("privilege_level") == "non_createrole":
        return ("privilege_level", "non_createrole")
    return None


def build_create_group_factor_extension_plan(
    repository_root: Path,
) -> CreateGroupFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_group")
    if len(catalog_rows) != 64:
        raise CreateGroupFactorExtensionError("catalog row count drift")

    cases: list[CreateGroupFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    behavior_combos = _behavior_combinations()
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
                    f"CGP-EXT|{ordinal:05d}|"
                    f"{verification}|{cleanup}"
                )
                cases.append(
                    CreateGroupFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATEGROUP{ordinal:05d}",
                        sql_filename=f"CREATEGROUP{ordinal:05d}.sql",
                        object_prefix=f"creategroup_{ordinal:05d}_",
                        derivation_id=derivation_id,
                        derived_from_combination_group=_COMBINATION_GROUP,
                        derivation_reason=(
                            f"CREATE GROUP extension: "
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

    plan = CreateGroupFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    if len(plan.cases) < 1:
        raise CreateGroupFactorExtensionError(
            "extension case count below minimum"
        )
    if len(plan.cases) > _CAP:
        raise CreateGroupFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(
        range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))
    ):
        raise CreateGroupFactorExtensionError("extension ordinal gap")
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateGroupFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateGroupFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome == "success" or case.outcome == "expected_failure"
        for case in plan.cases
    ):
        raise CreateGroupFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("CGP-EXT|") for case in plan.cases
    ):
        raise CreateGroupFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateGroupFactorExtensionError",
    "CreateGroupFactorExtensionCase",
    "CreateGroupFactorExtensionPlan",
    "build_create_group_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
