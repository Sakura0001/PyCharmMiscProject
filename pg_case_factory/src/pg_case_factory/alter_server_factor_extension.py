"""Bounded post-coverage cross-factor extension expander for ALTER SERVER.

The marginal factor-value-loop (:mod:`alter_server_factor_loop`) is the
required baseline: one program per factor value, 53 local cases
(GRM 3 + SFV 48 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_server.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes for ALL THREE grammar
branches (rename, owner and version_options), with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode`` crossed with ``cleanup_mode`` crossed so every
declared T6 value is exercised.

ALTER SERVER's keyword owner-transfers (``CURRENT_ROLE`` /
``CURRENT_USER`` / ``SESSION_USER``) are normal permitted transfers to
the current session role; there is no membership-wall escape, so no
special consistency rule is needed beyond keyword agreement.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension``.
Filtering happens BEFORE counting (``raw += 1``), so
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

from .alter_server_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_server_factor_loop_plan,
)


class AlterServerFactorExtensionError(ValueError):
    """Raised when a frozen ALTER SERVER extension input drifts."""


@dataclass(frozen=True)
class AlterServerFactorExtensionCase:
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
class AlterServerFactorExtensionPlan:
    cases: tuple[AlterServerFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 53
_CAP = 20000

_VERIFICATION_MODES = (
    "error_assertion",
    "pg_foreign_server_catalog",
    "pg_foreign_server_options_query",
)
_CLEANUP_MODES = (
    "drop_fdw_then_drop_server",
    "drop_server",
    "drop_user_mapping_then_drop_server",
)

# Dense positive baselines per branch.  The T5 single-value-negative
# factors (nonexistent_server, nonexistent_new_name_conflict,
# nonexistent_owner, privilege_insufficient, fdw_validator_rejection) are
# NOT baselined here; :func:`_derive_t5_factors` adds them at their declared
# values.
_RENAME_BASELINE: dict[str, str] = {
    "statement_branch": "branch_rename",
    "grammar_branch": "branch_rename",
    "target_action": "rename",
    "server_state": "exists",
    "expected_status": "success",
    "rename_behavior": "rename_to_new_name",
    "owner_to_shape": "explicit_role_name",
    "new_owner_shape": "existing_role",
    "version_clause": "omitted",
    "options_operation": "omitted_no_options",
    "option_key_value_shape": "valid_option",
    "server_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "user_mapping_dependency": "no_user_mapping",
    "verification_mode": "pg_foreign_server_catalog",
    "cleanup_mode": "drop_server",
}

_OWNER_BASELINE: dict[str, str] = {
    "statement_branch": "branch_owner_to",
    "grammar_branch": "branch_owner_to",
    "target_action": "owner",
    "server_state": "exists",
    "expected_status": "success",
    "rename_behavior": "rename_to_new_name",
    "owner_to_shape": "explicit_role_name",
    "new_owner_shape": "existing_role",
    "version_clause": "omitted",
    "options_operation": "omitted_no_options",
    "option_key_value_shape": "valid_option",
    "server_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "user_mapping_dependency": "no_user_mapping",
    "verification_mode": "pg_foreign_server_catalog",
    "cleanup_mode": "drop_server",
}

_VERSION_OPTIONS_BASELINE: dict[str, str] = {
    "statement_branch": "branch_version_options",
    "grammar_branch": "branch_version_options",
    "target_action": "version_options",
    "server_state": "exists",
    "expected_status": "success",
    "rename_behavior": "rename_to_new_name",
    "owner_to_shape": "explicit_role_name",
    "new_owner_shape": "existing_role",
    "version_clause": "omitted",
    "options_operation": "omitted_no_options",
    "option_key_value_shape": "valid_option",
    "server_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "executor_privilege": "superuser",
    "user_mapping_dependency": "no_user_mapping",
    "verification_mode": "pg_foreign_server_catalog",
    "cleanup_mode": "drop_server",
}

# Crossed axes per branch (T1-T4).  Each axis includes both positive and
# negative (failure-causing) values; the at-most-one-failure rule ensures
# clean attribution.
_RENAME_AXES: dict[str, tuple[str, ...]] = {
    "server_state": ("exists", "non_existent"),
    "new_name_shape": (
        "simple_name",
        "quoted_name",
        "existing_name_conflict",
    ),
    "executor_privilege": (
        "superuser",
        "owner_with_usage_on_fdw",
        "non_owner_no_privilege",
    ),
    "user_mapping_dependency": ("has_user_mapping", "no_user_mapping"),
}

_OWNER_AXES: dict[str, tuple[str, ...]] = {
    "server_state": ("exists", "non_existent"),
    "owner_to_shape": (
        "explicit_role_name",
        "current_role_keyword",
        "current_user_keyword",
        "session_user_keyword",
    ),
    "new_owner_shape": ("existing_role", "nonexistent_role"),
    "executor_privilege": (
        "superuser",
        "owner_with_usage_on_fdw",
        "non_owner_no_privilege",
    ),
    "user_mapping_dependency": ("has_user_mapping", "no_user_mapping"),
}

_VERSION_OPTIONS_AXES: dict[str, tuple[str, ...]] = {
    "server_state": ("exists", "non_existent"),
    "version_clause": ("omitted", "set_new_version", "set_version_null"),
    "options_operation": (
        "omitted_no_options",
        "add_option",
        "set_option",
        "drop_option",
        "add_and_set_combined",
    ),
    "option_key_value_shape": (
        "valid_option",
        "invalid_option_rejected_by_validator",
    ),
    "executor_privilege": (
        "superuser",
        "owner_with_usage_on_fdw",
        "non_owner_no_privilege",
    ),
    "user_mapping_dependency": ("has_user_mapping", "no_user_mapping"),
}

# Crossed behaviour-negative (factor, value) pairs across all branches.
# Each cluster is represented by its T3/T4 factor only; the tied T5 factor
# is derived by :func:`_derive_t5_factors` and is not counted here, so a
# single failure is never double-counted.
_CROSSED_NEGATIVES = frozenset(
    {
        ("server_state", "non_existent"),
        ("new_name_shape", "existing_name_conflict"),
        ("new_owner_shape", "nonexistent_role"),
        ("executor_privilege", "non_owner_no_privilege"),
        ("option_key_value_shape", "invalid_option_rejected_by_validator"),
    }
)

# Valid (owner_to_shape, new_owner_shape) keyword-agreement pairs.  The
# keyword transfers always target an existing role (the current session
# user); only an explicit role name may name a non-existent role.
_OWNER_KEYWORD_PAIRS = frozenset(
    {
        ("explicit_role_name", "existing_role"),
        ("explicit_role_name", "nonexistent_role"),
        ("current_role_keyword", "existing_role"),
        ("current_user_keyword", "existing_role"),
        ("session_user_keyword", "existing_role"),
    }
)

# options_operation values that invoke the FDW validator on an option (so an
# invalid option actually reaches the validator and is rejected).
_VALIDATOR_INVOKING_OPS = frozenset(
    {"add_option", "set_option", "add_and_set_combined"}
)

_BRANCH_CONFIG = (
    ("rename", _RENAME_AXES, _RENAME_BASELINE),
    ("owner", _OWNER_AXES, _OWNER_BASELINE),
    ("version_options", _VERSION_OPTIONS_AXES, _VERSION_OPTIONS_BASELINE),
)


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

    branch = assignment.get("target_action")
    if branch == "version_options":
        oks = assignment.get("option_key_value_shape")
        op = assignment.get("options_operation")
        if (
            oks == "invalid_option_rejected_by_validator"
            and op not in _VALIDATOR_INVOKING_OPS
        ):
            return False
    elif branch == "owner":
        oc = assignment.get("owner_to_shape")
        now = assignment.get("new_owner_shape")
        if (oc, now) not in _OWNER_KEYWORD_PAIRS:
            return False
    elif branch != "rename":
        return False
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T3/T4 values.

    The T5 single-value-negative factors carry only their declared
    (negative) value, so they are set to that declared value and fire only
    when the corresponding T3/T4 is also negative.  The extension's failure
    count uses T3/T4 crossed negatives only (:func:`_failure_unit_count`),
    so the always-on T5 values do not inflate the count.
    """

    ss = a.get("server_state", "exists")
    nns = a.get("new_name_shape", "simple_name")
    ep = a.get("executor_privilege", "superuser")

    # Always-on declared negative values (do not inflate _CROSSED count).
    a["nonexistent_server"] = "server_does_not_exist"
    a["nonexistent_new_name_conflict"] = "new_name_already_exists"
    a["nonexistent_owner"] = "owner_role_does_not_exist"
    a["fdw_validator_rejection"] = "validator_rejects_invalid_option"
    a["privilege_insufficient"] = "non_owner_altering_server"

    if ss == "non_existent":
        a["server_name_shape"] = "non_existent_name"
    if nns == "existing_name_conflict":
        a["rename_behavior"] = "rename_to_existing_name_conflict"
    if ep == "non_owner_no_privilege":
        a["privilege_insufficient"] = "non_owner_altering_server"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for _branch, axes, baseline in _BRANCH_CONFIG:
        names = list(axes)
        for values in itertools.product(*[axes[n] for n in names]):
            assignment: dict[str, str] = dict(baseline)
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise AlterServerFactorExtensionError(
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
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[AlterServerFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-server-factor-extension-v1\n")
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(case.factor_assignment),
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": case.expected_failure_reason,
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
    cases: tuple[AlterServerFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER SERVER extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_server_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER SERVER",
                    "primary_fence": "primary-target-begin/end",
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment["verification_mode"],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment["cleanup_mode"],
                },
            }
        )
    return yaml.safe_dump(entries, sort_keys=False, allow_unicode=True)


def build_alter_server_factor_extension_plan(
    repository_root: Path,
) -> AlterServerFactorExtensionPlan:
    """Build the bounded ALTER SERVER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_server_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterServerFactorExtensionCase] = []
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
                outcome, sqlstate, reason = _outcome_for(assignment)
                ordinal += 1
                cases.append(
                    AlterServerFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERSERVER{ordinal:05d}",
                        sql_filename=f"ALTERSERVER{ordinal:05d}.sql",
                        object_prefix=f"alterserver_{ordinal:05d}_",
                        derivation_id=(
                            f"ASRV-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_server_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x server_state="
                            f"{assignment['server_state']} "
                            f"x executor_privilege="
                            f"{assignment['executor_privilege']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment["target_action"],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return AlterServerFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterServerFactorExtensionError",
    "AlterServerFactorExtensionCase",
    "AlterServerFactorExtensionPlan",
    "build_alter_server_factor_extension_plan",
]
