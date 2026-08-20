"""Bounded post-coverage cross-factor extension expander for CREATE DATABASE.

The marginal factor-value-loop (:mod:`create_database_factor_loop`) is the
required baseline: one program per factor value, 68 local cases
(GRM 1 + SFV 67).  This module adds the bounded post-coverage extension
phase allowed by ``create_database.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T2 behaviour axes across the single
grammar branch (``branch_create_database``), with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode`` / ``cleanup_mode`` crossed so every declared T6
value is exercised.

CREATE DATABASE requires superuser or ``CREATEDB`` privilege, so
``privilege_level=non_createdb_role`` is an unconditional failure
(SQLSTATE 42501).  ``object_state=exists`` triggers a duplicate-database
failure (SQLSTATE 42P04).  No other general-axis value causes a failure
in isolation.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``post_coverage_extension_policy.required_fields``) and is marked
``is_extension``.  Filtering happens BEFORE counting (``raw += 1``), so
``raw_combination_count == len(cases)`` and ``dropped_count == 0``
(no over-pruning).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .create_database_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_database_factor_loop_plan,
)


class CreateDatabaseFactorExtensionError(ValueError):
    """Raised when a frozen CREATE DATABASE extension input drifts."""


@dataclass(frozen=True)
class CreateDatabaseFactorExtensionCase:
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
    is_extension: bool


@dataclass(frozen=True)
class CreateDatabaseFactorExtensionPlan:
    cases: tuple[CreateDatabaseFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 68
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_database",
    "connect_to_new_database",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_database",
    "force_drop_database",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "exists",
    ),
    "owner_clause": (
        "omitted",
        "current_user",
        "specified_other_role",
    ),
    "template_clause": (
        "omitted_default_template1",
        "template0",
        "custom_template",
    ),
    "encoding_clause": (
        "omitted",
        "UTF8",
        "LATIN1",
        "SQL_ASCII",
    ),
    "locale_clause": (
        "omitted",
        "C_locale",
        "POSIX_locale",
        "specific_locale",
        "builtin_locale",
    ),
    "strategy_clause": (
        "omitted_default_wal_log",
        "WAL_LOG",
        "FILE_COPY",
    ),
    "privilege_level": (
        "superuser",
        "createdb_role",
        "non_createdb_role",
    ),
}

_BASELINE: dict[str, str] = {
    "statement_branch": "branch_create_database",
    "grammar_branch": "branch_create_database",
    "target_action": "create_database",
    "expected_status": "success",
    "database_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "tablespace_name_shape": "default_tablespace",
    "template_existence": "template_exists_no_connections",
    "encoding_locale_compatibility": "compatible",
    "role_set_role_ability": "can_set_role",
    "tablespace_existence": "tablespace_exists",
    "duplicate_database_name": "no_conflict",
    "privilege_denied": "has_createdb",
    "cannot_set_role_to_owner": "can_set_role",
    "template_has_connections": "no_other_connections",
    "encoding_locale_incompatible": "compatible",
    "encoding_template_mismatch": "matches_template",
    "nonexistent_template": "template_exists",
    "nonexistent_tablespace": "tablespace_exists",
    "inside_transaction_block": "outside_transaction",
    "verification_mode": "catalog_query_pg_database",
    "cleanup_mode": "drop_database",
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "exists"),
        ("privilege_level", "non_createdb_role"),
    }
)

_CROSSED_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("object_state", "exists"): (
        "42P04",
        "duplicate_database_provisional",
    ),
    ("privilege_level", "non_createdb_role"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


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


def _derive_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary + consistency factors."""

    if a.get("object_state") == "exists":
        a["duplicate_database_name"] = "same_name_conflict"
        a["expected_status"] = "failure"
    if a.get("privilege_level") == "non_createdb_role":
        a["privilege_denied"] = "lacks_createdb"
        a["expected_status"] = "failure"
    if a.get("owner_clause") == "specified_other_role":
        if a.get("role_set_role_ability") != "cannot_set_role":
            a["role_set_role_ability"] = "can_set_role"
    if (
        a.get("encoding_clause") != "omitted"
        or a.get("locale_clause") != "omitted"
    ):
        if a.get("template_clause") == "omitted_default_template1":
            a["template_clause"] = "template0"
    if a.get("locale_clause") == "builtin_locale":
        a["template_clause"] = "template0"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments passing the filter."""

    combos: list[dict[str, str]] = []
    names = list(_GENERAL_AXES)
    for values in itertools.product(
        *[list(_GENERAL_AXES[n]) for n in names]
    ):
        assignment: dict[str, str] = dict(_BASELINE)
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise CreateDatabaseFactorExtensionError(
                "duplicate factor key in extension assignment"
            )
        combos.append(assignment)
    return combos


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE.get(
        pair, _CROSSED_FAILURE_SQLSTATE[pair]
    )
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[CreateDatabaseFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-database-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(
                        case.factor_assignment
                    ),
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": (
                        case.expected_failure_reason
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _derived_combinations_yaml(
    cases: tuple[CreateDatabaseFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE DATABASE extension "
                    f"{case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "create_database_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE DATABASE",
                    "primary_fence": (
                        "primary-target-begin/end"
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment[
                        "verification_mode"
                    ],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment["cleanup_mode"],
                },
            }
        )
    return yaml.safe_dump(
        entries, sort_keys=False, allow_unicode=True
    )


def build_create_database_factor_extension_plan(
    repository_root: Path,
) -> CreateDatabaseFactorExtensionPlan:
    """Build the bounded CREATE DATABASE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_database_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateDatabaseFactorExtensionCase] = []
    ordinal = _BASELINE_COUNT
    raw = 0
    for behavior in behaviors:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                if len(cases) >= _CAP:
                    continue
                assignment: dict[str, str] = dict(behavior)
                assignment["verification_mode"] = verification
                assignment["cleanup_mode"] = cleanup
                outcome, sqlstate, reason = _outcome_for(
                    assignment
                )
                ordinal += 1
                cases.append(
                    CreateDatabaseFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATEDATABASE{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATEDATABASE{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createdatabase_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CD-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_database_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"object_state="
                            f"{assignment['object_state']} "
                            f"owner_clause="
                            f"{assignment['owner_clause']} "
                            f"template_clause="
                            f"{assignment['template_clause']} "
                            f"encoding_clause="
                            f"{assignment['encoding_clause']} "
                            f"locale_clause="
                            f"{assignment['locale_clause']} "
                            f"strategy_clause="
                            f"{assignment['strategy_clause']} "
                            f"privilege_level="
                            f"{assignment['privilege_level']} "
                            f"verification_mode="
                            f"{verification} "
                            f"cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "target_action"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return CreateDatabaseFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(
            cases_tuple
        ),
        derived_combinations_yaml=_derived_combinations_yaml(
            cases_tuple
        ),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "CreateDatabaseFactorExtensionError",
    "CreateDatabaseFactorExtensionCase",
    "CreateDatabaseFactorExtensionPlan",
    "build_create_database_factor_extension_plan",
]
