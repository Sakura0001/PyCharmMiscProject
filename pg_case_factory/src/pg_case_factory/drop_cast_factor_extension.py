"""Bounded post-coverage cross-factor extension expander for DROP CAST.

The marginal factor-value-loop (:mod:`drop_cast_factor_loop`) is the
required baseline: one program per factor value, 44 local cases
(GRM 1 + SFV 41 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``drop_cast.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the single
official synopsis branch (at most one failure-causing value per case, so
attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The T5 negative factors (``nonexistent_cast``, ``insufficient_privilege``,
``expected_status``, ``object_state=not_exists``) are owned one-per-value by
the marginal baseline and are never crossed here, so the at-most-one-failure
attribution stays clean.

The single official synopsis branch is crossed:

* ``branch_1`` — ``source_type_shape`` x ``target_type_shape`` x
  ``if_exists_clause`` x ``cascade_restrict`` x ``privilege_level``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_cast_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_cast_factor_loop_plan,
)


class DropCastFactorExtensionError(ValueError):
    """Raised when a frozen DROP CAST extension input drifts."""


@dataclass(frozen=True)
class DropCastFactorExtensionCase:
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
class DropCastFactorExtensionPlan:
    cases: tuple[DropCastFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 44
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The exact
# frozen count is asserted in the companion test.
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_cast_catalog_query",
    "pg_cast_removed_assertion",
)
_CLEANUP_MODES = (
    "DROP_CAST_IF_EXISTS",
)

# Dense baseline assignment (all positive T1-T4 + T6 baselines).  The T5
# negative factors (nonexistent_cast, insufficient_privilege,
# expected_status, object_state=not_exists) are intentionally absent from
# the cross: they are owned one-per-value by the marginal baseline and are
# never crossed here, so the at-most-one-failure attribution stays clean.
# source_type / target_type are held at custom_type so the fixture cast is
# always a fresh prefix-named cast (never a shipped system cast).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_cast",
    "object_state": "already_exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "RESTRICT_default",
    "source_type": "custom_type",
    "target_type": "custom_type",
    "source_type_shape": "plain_type",
    "target_type_shape": "plain_type",
    "privilege_level": "type_owner_source",
    "type_ownership": "owns_source",
    "nonexistent_cast": "without_if_exists",
    "insufficient_privilege": "owns_no_type",
    "reverse_direction_cast": "reverse_still_exists",
    "verification_mode": "pg_cast_removed_assertion",
    "cleanup_mode": "DROP_CAST_IF_EXISTS",
}

# Official synopsis branch -> grammar_branch id used by the renderer.
_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_1": "branch_1",
}

# Fixed consumer action per branch (the synopsis action form).
_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_1": "drop_cast",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_1": {
        "source_type_shape": ("plain_type", "schema_qualified_type"),
        "target_type_shape": ("plain_type", "schema_qualified_type"),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict": ("RESTRICT_default", "RESTRICT_explicit", "CASCADE"),
        "privilege_level": ("type_owner_source", "non_owner"),
    },
}

# The privilege boundary (privilege_level=non_owner) is the only crossed
# behaviour negative; it is counted as a single unit.
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege boundary only; <= 1."""

    count = 0
    if assignment.get("privilege_level") == "non_owner":
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (must own a source or target type, 42501) is the
    only crossed behaviour negative, so attribution is trivially clean.
    """

    if assignment.get("privilege_level") == "non_owner":
        return _PRIVILEGE_NEGATIVE
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """At-most-one-failure attribution."""

    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, axes in _BRANCH_AXES.items():
        names = list(axes)
        for values in itertools.product(*(axes[name] for name in names)):
            assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = _BRANCH_GRAMMAR[branch]
            assignment["target_action"] = _BRANCH_FIXED_ACTION[branch]
            for name, value in zip(names, values):
                assignment[name] = value
            if not _is_valid_combination(assignment):
                continue
            # expected_status follows the ACTUAL outcome (from
            # _present_failure_pair), not the filter's failure-unit count.
            pair = _present_failure_pair(assignment)
            assignment["expected_status"] = (
                "failure" if pair is not None else "success"
            )
            combos.append(assignment)
    return combos


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    """Derive (outcome, expected_sqlstate, expected_failure_reason)."""

    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[DropCastFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-cast-factor-extension-v1\n")
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
    cases: tuple[DropCastFactorExtensionCase, ...],
) -> str:
    """Emit the derived-extension ledger with the yaml required fields."""

    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP CAST extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_cast_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP CAST",
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


def build_drop_cast_factor_extension_plan(
    repository_root: Path,
) -> DropCastFactorExtensionPlan:
    """Build the bounded DROP CAST post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_cast_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    # Stable sort so any cap truncation is deterministic and interleaves
    # branches rather than favouring the first branch.
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropCastFactorExtensionCase] = []
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
                action = assignment["target_action"]
                cases.append(
                    DropCastFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPCAST{ordinal:05d}",
                        sql_filename=f"DROPCAST{ordinal:05d}.sql",
                        object_prefix=f"dropcast_{ordinal:05d}_",
                        derivation_id=(
                            f"DCAST-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_cast_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(sorted(assignment.items())),
                        consumer_action_id=action,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return DropCastFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropCastFactorExtensionError",
    "DropCastFactorExtensionCase",
    "DropCastFactorExtensionPlan",
    "build_drop_cast_factor_extension_plan",
]
