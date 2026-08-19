"""Tests for the bounded ALTER LARGE OBJECT post-coverage extension expander.

The marginal factor-value-loop (``alter_large_object_factor_loop.py``) is the
frozen 31-case baseline (GRM 1 + SFV 28 + RISK 2).  This module's expander
adds the bounded post-coverage extension phase: cross-factor combinations of
the positive T1-T4 behaviour axes across the single official synopsis branch
(at most one failure-causing value per case, so attribution stays clean),
with ``verification_mode`` crossed and ``cleanup_mode`` rotated so every
declared T6 value is exercised.  Each extension case carries a derivation
record and is marked ``is_extension = True``; it never replaces a
required-baseline obligation.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_large_object_factor_extension import (
    AlterLargeObjectFactorExtensionCase,
    AlterLargeObjectFactorExtensionError,
    AlterLargeObjectFactorExtensionPlan,
    build_alter_large_object_factor_extension_plan,
)
from pg_case_factory.alter_large_object_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_large_object_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 31
_EXTENSION_COUNT = 204
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 235
_SUCCESS_EXTENSIONS = 60
_FAILURE_EXTENSIONS = 144
_EXTENSION_MULTISET_SHA256 = (
    "26fd4214e64ec3e4e5584d8b62874241160e86f8be94c51b2a5c444fbf7eb2b3"
)

# Behaviour-negative (factor, value) pairs that are CROSSED in extensions.
# The privilege cluster (privilege_context=non_owner/insufficient_privilege)
# is counted as a single unit, so neither member is duplicated here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("target_object_state", "missing"),
        ("oid_shape", "nonexistent_oid"),
        ("new_owner_shape", "missing_role"),
    }
)
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner", "insufficient_privilege"})

# Crossed axes (the single branch's crossed axes + T6).  Every value here
# must be witnessed somewhere in the extension plan.
_CROSSED_AXES = {
    "statement_branch": ("branch_owner",),
    "target_action": ("owner_change",),
    "new_owner_shape": (
        "plain_role",
        "current_role",
        "current_user",
        "session_user",
        "missing_role",
    ),
    "target_object_state": ("exists", "missing"),
    "privilege_context": (
        "superuser",
        "owner",
        "non_owner",
        "insufficient_privilege",
    ),
    "oid_shape": ("valid_oid", "nonexistent_oid"),
    "verification_mode": ("catalog_query", "effect_query", "error_assertion"),
    "cleanup_mode": ("drop_objects", "reset_state"),
}

# Factors held at baseline value across all extensions (the baseline owns
# their negative counterparts one-per-value; they are never crossed here).
_HELD_CONSTANT = {
    "dependency_state": "ready",
    "invalid_combination": "none",
    "ownership_boundary": "owner",
}

_BRANCH_GRAMMAR = {
    "branch_owner": "branch_owner",
}
_BRANCH_FIXED_ACTION = {
    "branch_owner": "owner_change",
}


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + behaviour negatives; must stay at most one."""

    cluster = (
        1
        if assignment.get("privilege_context") in _PRIVILEGE_CLUSTER_VALUES
        else 0
    )
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    return cluster + negatives


def _privilege_boundary_fires(assignment: dict[str, str]) -> bool:
    """Whether the must_be_owner_of_large_object check actually fires."""

    return assignment.get("new_owner_shape") != "session_user"


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    level = assignment.get("privilege_context")
    if (
        level in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
    ):
        return ("privilege_context", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


class AlterLargeObjectFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_large_object_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterLargeObjectFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        # raw product == kept count => no silent truncation
        self.assertEqual(_EXTENSION_COUNT, self.plan.raw_combination_count)
        self.assertEqual(0, self.plan.dropped_count)

    def test_extension_multiset_sha256_is_frozen(self) -> None:
        self.assertEqual(
            _EXTENSION_MULTISET_SHA256,
            self.plan.extension_multiset_sha256,
        )

    def test_ordinals_continue_after_baseline_with_five_digit_scheme(
        self,
    ) -> None:
        ordinals = [case.ordinal for case in self.plan.cases]
        self.assertEqual(
            list(range(_BASELINE_COUNT + 1, _TOTAL_COUNT + 1)), ordinals
        )
        first, last = self.plan.cases[0], self.plan.cases[-1]
        self.assertEqual(_BASELINE_COUNT + 1, first.ordinal)
        self.assertEqual(_TOTAL_COUNT, last.ordinal)
        self.assertEqual("ALTERLARGEOBJECT00032", first.case_id)
        self.assertEqual(f"ALTERLARGEOBJECT{_TOTAL_COUNT:05d}", last.case_id)
        self.assertEqual("ALTERLARGEOBJECT00032.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERLARGEOBJECT{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("alterlargeobject_00032_", first.object_prefix)
        self.assertEqual(
            f"alterlargeobject_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterLargeObjectFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
            # 13 keys: 11 _BASELINE_DEFAULTS (excl. verification/cleanup
            # crossed) + verification_mode + cleanup_mode + statement_branch.
            self.assertEqual(13, len(case.factor_assignment), case.case_id)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)
            self.assertEqual(
                tuple(sorted(case.factor_assignment)), case.factor_assignment
            )

    def test_outcome_split_matches_frozen_arithmetic(self) -> None:
        outcomes = Counter(case.outcome for case in self.plan.cases)
        self.assertEqual(_SUCCESS_EXTENSIONS, outcomes["success"])
        self.assertEqual(_FAILURE_EXTENSIONS, outcomes["expected_failure"])
        self.assertEqual(_EXTENSION_COUNT, sum(outcomes.values()))

    def test_at_most_one_failure_unit_per_case(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            count = _failure_unit_count(assignment)
            self.assertLessEqual(count, 1, case.case_id)
            if case.outcome == "expected_failure":
                self.assertEqual(1, count, case.case_id)
            # Success cases may have count=0 (no failure unit) or count=1
            # (privilege cluster that does not fire for SESSION_USER no-op).

    def test_expected_status_is_derived_from_present_failure_pair(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            pair = _present_failure_pair(assignment)
            self.assertEqual(
                "failure" if pair is not None else "success",
                assignment["expected_status"],
                case.case_id,
            )

    def test_expected_sqlstate_matches_present_failure_pair(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            pair = _present_failure_pair(assignment)
            if pair is None:
                self.assertEqual("success", case.outcome, case.case_id)
                self.assertEqual("00000", case.expected_sqlstate, case.case_id)
                self.assertIsNone(
                    case.expected_failure_reason, case.case_id
                )
            else:
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
                self.assertEqual(
                    sqlstate, case.expected_sqlstate, case.case_id
                )
                self.assertEqual(
                    reason, case.expected_failure_reason, case.case_id
                )

    def test_privilege_cluster_collapses_two_non_owner_levels(self) -> None:
        # Both non-owner privilege values model the same must_be_owner
        # (42501) boundary and must never co-occur with another failure.
        witnessed_levels = {
            dict(c.factor_assignment)["privilege_context"]
            for c in self.plan.cases
        }
        self.assertTrue(_PRIVILEGE_CLUSTER_VALUES.issubset(witnessed_levels))
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_context"] in _PRIVILEGE_CLUSTER_VALUES:
                if _privilege_boundary_fires(a):
                    self.assertEqual(
                        "expected_failure", case.outcome, case.case_id
                    )
                    self.assertEqual(
                        "42501", case.expected_sqlstate, case.case_id
                    )
                else:
                    # SESSION_USER resolves to the session user (the owner),
                    # making OWNER TO a no-op that PG allows even for
                    # non-owners, so the boundary does not fire.
                    self.assertEqual(
                        "success", case.outcome, case.case_id
                    )
                    self.assertEqual(
                        "00000", case.expected_sqlstate, case.case_id
                    )

    def test_branch_grammar_and_consumer_action_are_consistent(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            branch = a["statement_branch"]
            self.assertEqual(
                _BRANCH_GRAMMAR[branch], a["grammar_branch"], case.case_id
            )
            self.assertEqual(
                _BRANCH_FIXED_ACTION[branch],
                a["target_action"],
                case.case_id,
            )
            self.assertEqual(
                _BRANCH_FIXED_ACTION[branch],
                case.consumer_action_id,
                case.case_id,
            )

    def test_held_constant_factors_stay_at_baseline(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            for factor, value in _HELD_CONSTANT.items():
                self.assertEqual(value, a[factor], (case.case_id, factor))

    def test_every_crossed_factor_value_is_witnessed(self) -> None:
        witnessed: dict[str, set[str]] = {
            factor: set() for factor in _CROSSED_AXES
        }
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            for factor in _CROSSED_AXES:
                witnessed[factor].add(a[factor])
        for factor, values in _CROSSED_AXES.items():
            self.assertEqual(
                set(values),
                witnessed[factor],
                f"factor {factor}: missing {set(values) - witnessed[factor]}",
            )

    def test_verification_and_cleanup_modes_are_both_crossed(self) -> None:
        vm_counts: Counter[str] = Counter()
        cm_counts: Counter[str] = Counter()
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            vm_counts[a["verification_mode"]] += 1
            cm_counts[a["cleanup_mode"]] += 1
        self.assertEqual(
            set(_CROSSED_AXES["verification_mode"]), set(vm_counts)
        )
        self.assertEqual(
            set(_CROSSED_AXES["cleanup_mode"]), set(cm_counts)
        )
        # full T6 cross with no truncation => each value appears evenly
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["verification_mode"]),
            vm_counts["catalog_query"],
        )
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["cleanup_mode"]),
            cm_counts["drop_objects"],
        )

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_large_object_factor_extension_plan(ROOT)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            again.extension_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in self.plan.cases),
            tuple(c.case_id for c in again.cases),
        )
        for left, right in zip(self.plan.cases, again.cases):
            self.assertEqual(left.factor_assignment, right.factor_assignment)

    def test_extensions_do_not_collide_with_baseline_numbering(self) -> None:
        baseline = build_alter_large_object_factor_loop_plan(ROOT)
        baseline_ids = {c.case_id for c in baseline.cases}
        extension_ids = {c.case_id for c in self.plan.cases}
        self.assertEqual(0, len(baseline_ids & extension_ids))
        self.assertEqual(_BASELINE_COUNT, len(baseline_ids))
        self.assertEqual(_EXTENSION_COUNT, len(extension_ids))

    def test_derived_combinations_yaml_parses_with_required_fields(
        self,
    ) -> None:
        doc = yaml.safe_load(self.plan.derived_combinations_yaml)
        self.assertIsInstance(doc, list)
        self.assertEqual(_EXTENSION_COUNT, len(doc))
        required = {
            "id",
            "title",
            "derived_from_combination_group",
            "derivation_reason",
            "factors",
            "expected_status_policy",
            "compatibility",
            "sql_shape",
            "verification",
            "cleanup",
        }
        for entry in doc:
            self.assertTrue(required.issubset(entry.keys()), entry.keys())


if __name__ == "__main__":
    unittest.main()
