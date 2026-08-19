"""Bounded post-coverage cross-factor extension expander for ALTER INDEX.

The marginal factor-value-loop (:mod:`alter_index_factor_loop`) is the
required baseline: one program per factor value, 772 local cases
(GRM 21 + SFV 751, 485 success + 287 expected_failure).  This module adds the
bounded post-coverage extension phase allowed by ``alter_index.yaml``:
cross-factor combinations of the positive (success-path) T1-T4 behaviour axes
with ``verification_mode`` crossed and ``cleanup_mode`` crossed so every
declared T6 value is exercised against the positive cross.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension =
True``.  It does **not** emit the full cartesian interaction universe (that
stays a diagnostic-only resolver artifact); it emits only the positive-axis
cross, which is the bounded, attributed subset.

Outcome attribution reuses the ledger's compatibility logic
(:func:`._resolve_disposition` + :func:`evaluate_condition` +
``EXPECTED_SQLSTATE_BY_REASON``) rather than redesigning bespoke rules, so the
extension and the marginal baseline share one attribution contract.  The
downstream PG18.4 serial two-run calibration verifies and refines these
sqlstates against the live catalog.

Design note (coverage scope): the success-path cross is bounded to the
positive (success) values of each behaviour axis.  Failure and no-op values
are owned one-per-value by the marginal baseline (one axis varies at a time
there); cross-factor failure-interaction combinations are a sequenced
refinement that requires per-group attribution and is not emitted here, so
the at-most-one-failure attribution stays clean and no success-group case is
mis-attributed by a negative value whose failure contract lives in another
group.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path

from .alter_index_factor_loop import (
    _axes_by_action,
    _resolve_disposition,
    build_alter_index_factor_loop_plan,
)
from .alter_index_regress import load_alter_index_grammar_actions


class AlterIndexFactorExtensionError(ValueError):
    """Raised when a frozen ALTER INDEX extension input drifts."""


@dataclass(frozen=True)
class AlterIndexFactorExtensionCase:
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
class AlterIndexFactorExtensionPlan:
    cases: tuple[AlterIndexFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 772
# Safety backstop only; the natural positive-axis x T6 cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The exact
# frozen count is asserted in the companion test.
_CAP = 50000

# Success-path (positive) values per behaviour axis.  Failure and no-op
# markers are intentionally absent: they are owned one-per-value by the
# marginal baseline and never crossed here, so attribution stays clean.
_POSITIVE_AXIS_VALUES: dict[str, tuple[str, ...]] = {
    "object_state": ("exists",),
    "if_exists": ("false", "true"),
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
        "existing_object",
    ),
    "index_method": ("btree", "hash", "gist", "spgist", "gin", "brin"),
    "storage_parameter_set": (
        "single_param_with_value",
        "single_param_no_value",
        "multiple_params",
    ),
    "storage_parameter_reset": ("single_param", "multiple_params"),
    "statistics_value": ("positive_integer",),
    "column_number_value": ("valid_position",),
    "owned_by": ("absent", "single_role", "multiple_roles"),
    "nowait": ("false", "true"),
    "no_keyword": ("false", "true"),
    "column_keyword": ("false", "true"),
}

# Axes never crossed: expected_status is derived; the T5 negative axes
# (invalid_combination, syntax_error, permission_boundary) stay at the
# action's baseline; verification_mode + cleanup_mode are the T6 cross;
# statement_branch is the action id.
_EXCLUDED_AXES = frozenset(
    {
        "expected_status",
        "invalid_combination",
        "syntax_error",
        "permission_boundary",
        "verification_mode",
        "cleanup_mode",
        "statement_branch",
    }
)

_VERIFICATION_MODES = ("catalog_query", "meta_command", "parameter_check")
_CLEANUP_MODES = ("drop_index", "reset_parameter", "detach_partition")

# Concrete storage parameter per index method (mirrors the ledger's
# ``_METHOD_PARAMETER_VALID`` table).  The grammar's ``storage_parameter_set``
# / ``storage_parameter_reset`` axes carry *shape* values
# (``single_param_with_value`` …), not concrete parameter names, but the
# shared evaluator's ``storage_parameter is [not] valid for index_method``
# condition resolves against a concrete ``storage_parameter`` binding.  The
# extension therefore supplies the method-valid concrete parameter so the
# shared evaluator resolves the positive cross as success (a valid parameter
# on a compatible method).  The marginal ledger's set_storage/reset_storage
# expected_failure attribution (missing ``storage_parameter`` binding) is a
# separate Fork-C double-run calibration concern and is left untouched here.
_VALID_PARAMETER_BY_METHOD: dict[str, str] = {
    "btree": "fillfactor",
    "hash": "fillfactor",
    "gist": "fillfactor",
    "spgist": "fillfactor",
    "gin": "fastupdate",
    "brin": "pages_per_range",
}


def _positive_axes_for_action(
    action_id: str,
    axes_by_action: dict[str, dict[str, tuple[str, ...]]],
) -> dict[str, tuple[str, ...]]:
    """The success-path cross axes for one branch action.

    Intersect the branch's declared axes with the positive-value table.  An
    axis with no positive-value entry is dropped (it carries only failure/noop
    markers and is not crossed here).
    """
    declared = axes_by_action.get(action_id, {})
    positive: dict[str, tuple[str, ...]] = {}
    for axis_id, values in declared.items():
        if axis_id in _EXCLUDED_AXES:
            continue
        positive_values = _POSITIVE_AXIS_VALUES.get(axis_id)
        if not positive_values:
            continue
        # Keep only declared values that are success-path (defensive: the
        # positive table may list values the branch does not declare).
        kept = tuple(v for v in values if v in positive_values)
        if kept:
            positive[axis_id] = kept
    return positive


def _behavior_combinations(
    actions,
    axes_by_action: dict[str, dict[str, tuple[str, ...]]],
) -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) for success actions."""
    combos: list[dict[str, str]] = []
    for action in actions:
        if action.default_expected_status != "success":
            # Failure/no-op group contexts are owned one-per-value by the
            # marginal baseline; their cross-factor interactions are a
            # sequenced refinement, not emitted here.
            continue
        axes = _positive_axes_for_action(action.action_id, axes_by_action)
        names = list(axes)
        if not names:
            continue
        for values in itertools.product(*(axes[name] for name in names)):
            assignment: dict[str, str] = dict(action.baseline_factors)
            assignment.pop("expected_status", None)
            assignment["statement_branch"] = action.action_id
            for name, value in zip(names, values):
                assignment[name] = value
            combos.append(assignment)
    return combos


def _extension_multiset_sha256(
    cases: tuple[AlterIndexFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-index-factor-extension-v1\n")
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
    cases: tuple[AlterIndexFactorExtensionCase, ...],
) -> str:
    """Emit the derived-extension ledger with the yaml required fields."""
    import yaml

    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER INDEX extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_index_factor_extension",
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER INDEX",
                    "primary_fence": "primary-target-begin/end",
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment.get("verification_mode", ""),
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment.get("cleanup_mode", ""),
                },
            }
        )
    return yaml.safe_dump(entries, sort_keys=False, allow_unicode=True)


def build_alter_index_factor_extension_plan(
    repository_root: Path,
) -> AlterIndexFactorExtensionPlan:
    """Build the bounded ALTER INDEX post-coverage extension plan."""
    root = Path(repository_root).resolve(strict=True)
    # Touch the marginal plan so any ledger drift surfaces here too.
    build_alter_index_factor_loop_plan(root)
    actions = load_alter_index_grammar_actions(root)
    axes_by_action = _axes_by_action(root)
    behaviors = _behavior_combinations(actions, axes_by_action)
    # Stable sort so any cap truncation is deterministic and interleaves
    # actions rather than favouring the first.
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterIndexFactorExtensionCase] = []
    ordinal = _BASELINE_COUNT
    raw = 0
    for behavior in behaviors:
        action = _action_for(behavior["statement_branch"], actions)
        if action is None:
            raise AlterIndexFactorExtensionError(
                f"extension behavior has no action: {behavior['statement_branch']}"
            )
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                if len(cases) >= _CAP:
                    continue
                assignment: dict[str, str] = dict(behavior)
                assignment["verification_mode"] = verification
                assignment["cleanup_mode"] = cleanup
                # Supply the method-valid concrete storage parameter so the
                # shared evaluator's storage-validity condition resolves the
                # positive cross as success (see _VALID_PARAMETER_BY_METHOD).
                assignment["storage_parameter"] = (
                    _VALID_PARAMETER_BY_METHOD.get(
                        assignment.get("index_method", "btree"), "fillfactor"
                    )
                )
                disposition, sqlstate, reason = _resolve_disposition(
                    action, assignment
                )
                if disposition == "delegated":
                    continue
                if disposition == "expected_failure":
                    outcome = "expected_failure"
                elif disposition == "no_op":
                    outcome = "no_op"
                else:
                    outcome = "success"
                ordinal += 1
                cases.append(
                    AlterIndexFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERINDEX{ordinal:05d}",
                        sql_filename=f"ALTERINDEX{ordinal:05d}.sql",
                        object_prefix=f"alterindex_{ordinal:05d}_",
                        derivation_id=(
                            f"AI-EXT|{ordinal:05d}|{action.action_id}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_index_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(sorted(assignment.items())),
                        consumer_action_id=action.action_id,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return AlterIndexFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


def _action_for(action_id: str, actions):
    """First action matching ``action_id`` with a success default.

    The marginal ledger's ``_action_index`` keeps the first action per branch
    id; the extension mirrors that so the two share one action-resolution
    contract.  The first success-default action is the canonical success
    baseline for the branch.
    """
    for action in actions:
        if action.action_id == action_id:
            return action
    return None


__all__ = [
    "AlterIndexFactorExtensionError",
    "AlterIndexFactorExtensionCase",
    "AlterIndexFactorExtensionPlan",
    "build_alter_index_factor_extension_plan",
]
