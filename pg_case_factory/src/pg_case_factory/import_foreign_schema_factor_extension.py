"""Bounded post-coverage extension plan for IMPORT FOREIGN SCHEMA factor regress.

The baseline :mod:`import_foreign_schema_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module crosses
the main-axis factor values with verification/cleanup axes under an
at-most-one-failure attribution policy, producing a bounded set of additional
regress programs that exercise pairwise factor interactions.

IMPORT FOREIGN SCHEMA creates FOREIGN TABLES (``pg_class.relkind='f'``), so
the bookend gate does NOT trigger (table-less w.r.t. bookend, like
``drop_user_mapping``).  ``pg_catalog.pg_class`` (joined to ``pg_namespace``)
is the semantic witness target.

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
from .import_foreign_schema_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class ImportForeignSchemaFactorExtensionError(ValueError):
    """Raised when IMPORT FOREIGN SCHEMA extension input drifts."""


@dataclass(frozen=True)
class ImportForeignSchemaFactorExtensionCase:
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
class ImportForeignSchemaFactorExtensionPlan:
    cases: tuple[ImportForeignSchemaFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 57
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_foreign_tables",
    "drop_server",
    "drop_schema",
    "drop_fdw",
)

# General axes crossed in every group (both positive, no negatives).
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_basic",
        "branch_limit_to",
        "branch_except",
    ),
    "options_clause": ("omitted", "specified"),
}

_SERVER_STATE_AXES: dict[str, tuple[str, ...]] = {
    "server_existence": ("server_exists", "server_not_exists"),
    "server_name_shape": ("simple_id", "nonexistent_server"),
}

_SCHEMA_STATE_AXES: dict[str, tuple[str, ...]] = {
    "schema_existence": ("schema_exists", "schema_not_exists"),
    "local_schema_name_shape": (
        "simple_id",
        "quoted_id",
        "nonexistent_schema",
    ),
}

_PRIVILEGE_STATE_AXES: dict[str, tuple[str, ...]] = {
    "privilege_level": ("superuser", "no_usage", "no_create"),
    "no_create_privilege": ("has_create", "lacks_create"),
}

# Representative failure (factor, value) pairs — one per failure scenario.
# expected_status is derived, not crossed, so it is NOT listed here.
_CROSSED_NEGATIVES = frozenset(
    {
        ("server_existence", "server_not_exists"),
        ("server_name_shape", "nonexistent_server"),
        ("schema_existence", "schema_not_exists"),
        ("local_schema_name_shape", "nonexistent_schema"),
        ("privilege_level", "no_usage"),
        ("privilege_level", "no_create"),
        ("no_create_privilege", "lacks_create"),
    }
)

_COMBINATION_GROUP = "import_foreign_schema_declared_factor_baseline"

_CONSUMER_ACTION = "import_foreign_schema_statement"


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


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive expected_status from the crossed-negative failure count."""

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
    cases: tuple[ImportForeignSchemaFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"import-foreign-schema-factor-extension-v1\n"
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


def build_import_foreign_schema_factor_extension_plan(
    repository_root: Path,
) -> ImportForeignSchemaFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("import_foreign_schema")
    if len(catalog_rows) != 56:
        raise ImportForeignSchemaFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[ImportForeignSchemaFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("server_state", _SERVER_STATE_AXES),
        ("schema_state", _SCHEMA_STATE_AXES),
        ("privilege_state", _PRIVILEGE_STATE_AXES),
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
                            ImportForeignSchemaFactorExtensionError(
                                "duplicate factor key in assignment"
                            )
                        )
                    outcome, sqlstate, reason = _outcome_for(full)
                    ordinal += 1
                    sorted_assignment = tuple(sorted(full.items()))
                    derivation_id = (
                        f"IMPORTFOREIGNSCHEMA-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        ImportForeignSchemaFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"IMPORTFOREIGNSCHEMA{ordinal:05d}",
                            sql_filename=(
                                f"IMPORTFOREIGNSCHEMA{ordinal:05d}.sql"
                            ),
                            object_prefix=(
                                f"importforeignschema_{ordinal:05d}_"
                            ),
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"IMPORT FOREIGN SCHEMA extension: "
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

    plan = ImportForeignSchemaFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 100 - _BASELINE_COUNT
    if len(plan.cases) < max(0, expected_min):
        raise ImportForeignSchemaFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise ImportForeignSchemaFactorExtensionError(
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
        raise ImportForeignSchemaFactorExtensionError(
            "extension ordinal gap"
        )
    if (
        len({case.case_id for case in plan.cases})
        != len(plan.cases)
    ):
        raise ImportForeignSchemaFactorExtensionError(
            "duplicate extension case_id"
        )
    if (
        len({case.sql_filename for case in plan.cases})
        != len(plan.cases)
    ):
        raise ImportForeignSchemaFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise ImportForeignSchemaFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("IMPORTFOREIGNSCHEMA-EXT|")
        for case in plan.cases
    ):
        raise ImportForeignSchemaFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "ImportForeignSchemaFactorExtensionError",
    "ImportForeignSchemaFactorExtensionCase",
    "ImportForeignSchemaFactorExtensionPlan",
    "build_import_foreign_schema_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
