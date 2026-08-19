"""Tests for the bounded ALTER GROUP post-coverage extension expander.

The marginal factor-value-loop (``alter_group_factor_loop.py``) is the
frozen 59-case baseline.  This module's expander adds the bounded
post-coverage extension phase: cross-factor combinations of the positive
T1-T4 behavior axes (at most one failure-causing value per case, so
attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` rotated so every declared T6 value is exercised.  Each
extension case carries a derivation record and is marked
``is_extension = True``; it never replaces a required-baseline obligation.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_group_factor_extension import (
    AlterGroupFactorExtensionCase,
    AlterGroupFactorExtensionPlan,
    AlterGroupFactorExtensionError,
    build_alter_group_factor_extension_plan,
)
from pg_case_factory.alter_group_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_group_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 59
_EXTENSION_COUNT = 3888
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 3947
_SUCCESS_EXTENSIONS = 864
_FAILURE_EXTENSIONS = 3024

# Behaviour-negative (factor, value) pairs that are CROSSED in extensions.
# The privilege cluster (privilege_level=non_admin + its three derived
# members) is counted as a single unit, so only the primary signal is here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("group_name_shape", "nonexistent_name"),
        ("user_name_shape", "nonexistent_user"),
        ("user_existence", "user_not_exists"),
        ("new_name_shape", "duplicate_name"),
        ("rename_to_existing_name", "same_name_conflict"),
    }
)
_PRIVILEGE_CLUSTER_KEY = ("privilege_level", "non_admin")

_CROSSED_AXES = {
    "statement_branch": ("branch_add_user", "branch_drop_user", "branch_rename"),
    "multi_user": ("single_user", "multiple_users"),
    "group_name_shape": ("simple_id", "quoted_id", "nonexistent_name"),
    "user_name_shape": ("simple_id", "quoted_id", "nonexistent_user"),
    "new_name_shape": ("simple_id", "quoted_id", "duplicate_name"),
    "privilege_level": ("group_role_admin", "non_admin", "superuser"),
    "user_existence": ("user_exists", "user_not_exists"),
    "object_state": ("exists", "not_exists"),
    "duplicate_add_user": ("new_member", "existing_member"),
    "drop_non_member_user": ("existing_member", "non_member"),
    "rename_to_existing_name": ("no_conflict", "same_name_conflict"),
    "verification_mode": (
        "pg_auth_members_catalog",
        "pg_authid_catalog",
        "error_assertion",
    ),
    "cleanup_mode": (
        "revoke_membership",
        "grant_membership",
        "revert_rename",
        "drop_role",
    ),
    "expected_status": ("success", "failure"),
    "alter_action": ("add_user", "drop_user", "rename"),
    "deprecated_equivalence": (
        "add_user_equals_grant",
        "drop_user_equals_revoke",
        "rename_equals_alter_role",
    ),
    "target_role_admin": ("has_admin", "lacks_admin"),
    "insufficient_privilege": (
        "sufficient_privilege",
        "insufficient_privilege",
    ),
    "non_admin_attempt": ("admin_execution", "non_admin_execution"),
}

# Factors held at baseline value across all extensions (the baseline owns
# their negative counterparts one-per-value).  role_specification is held at
# role_name: its keyword forms (CURRENT_ROLE/...) cannot produce the
# group-missing failure, so they are not crossed (baseline owns them).
_HELD_CONSTANT = {
    "nonexistent_group": "group_exists",
    "nonexistent_user": "user_exists",
    "deprecated_command_note": "deprecated_no_warning",
    "role_specification": "role_name",
}


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Count failure units: privilege cluster (1) + crossed behaviour negatives."""

    cluster = 1 if assignment.get("privilege_level") == "non_admin" else 0
    negatives = sum(
        1
        for pair in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    )
    return cluster + negatives


def _present_failure_pair(assignment: dict[str, str]) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    if assignment.get("privilege_level") == "non_admin":
        return _PRIVILEGE_CLUSTER_KEY
    for pair in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(pair[0]) == pair[1]:
            return pair
    return None


class AlterGroupFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_group_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterGroupFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        # raw product == kept count => no silent truncation
        self.assertEqual(_EXTENSION_COUNT, self.plan.raw_combination_count)
        self.assertEqual(0, self.plan.dropped_count)

    def test_ordinals_continue_after_baseline_with_four_digit_scheme(self) -> None:
        ordinals = [case.ordinal for case in self.plan.cases]
        self.assertEqual(
            list(range(_BASELINE_COUNT + 1, _TOTAL_COUNT + 1)), ordinals
        )
        first, last = self.plan.cases[0], self.plan.cases[-1]
        self.assertEqual(_BASELINE_COUNT + 1, first.ordinal)
        self.assertEqual(_TOTAL_COUNT, last.ordinal)
        self.assertEqual("ALTERGROUP0060", first.case_id)
        self.assertEqual(f"ALTERGROUP{_TOTAL_COUNT:04d}", last.case_id)
        self.assertEqual("ALTERGROUP0060.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERGROUP{_TOTAL_COUNT:04d}.sql", last.sql_filename
        )
        self.assertEqual("altergroup_0060_", first.object_prefix)
        self.assertEqual(
            f"altergroup_{_TOTAL_COUNT:04d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.is_extension, case.case_id)
            self.assertEqual(23, len(case.factor_assignment), case.case_id)
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
            else:
                self.assertEqual(0, count, case.case_id)

    def test_expected_status_is_derived_from_failure_unit(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            count = _failure_unit_count(assignment)
            self.assertEqual(
                "failure" if count == 1 else "success",
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
                self.assertIsNone(case.expected_failure_reason, case.case_id)
            else:
                self.assertEqual("expected_failure", case.outcome, case.case_id)
                sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
                self.assertEqual(sqlstate, case.expected_sqlstate, case.case_id)
                self.assertEqual(reason, case.expected_failure_reason, case.case_id)

    def test_privilege_cluster_is_consistent(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            level = a["privilege_level"]
            if level == "non_admin":
                self.assertEqual("lacks_admin", a["target_role_admin"])
                self.assertEqual("insufficient_privilege", a["insufficient_privilege"])
                self.assertEqual("non_admin_execution", a["non_admin_attempt"])
            elif level == "superuser":
                self.assertEqual("has_admin", a["target_role_admin"])
                self.assertEqual("sufficient_privilege", a["insufficient_privilege"])
                self.assertEqual("admin_execution", a["non_admin_attempt"])
            else:
                self.assertEqual("group_role_admin", level)
                self.assertEqual("has_admin", a["target_role_admin"])
                self.assertEqual("sufficient_privilege", a["insufficient_privilege"])
                self.assertEqual("admin_execution", a["non_admin_attempt"])

    def test_branch_action_deprecated_equivalence_are_consistent(self) -> None:
        branch_to_action = {
            "branch_add_user": "add_user",
            "branch_drop_user": "drop_user",
            "branch_rename": "rename",
        }
        branch_to_equiv = {
            "branch_add_user": "add_user_equals_grant",
            "branch_drop_user": "drop_user_equals_revoke",
            "branch_rename": "rename_equals_alter_role",
        }
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            branch = a["statement_branch"]
            self.assertEqual(branch_to_action[branch], a["alter_action"])
            self.assertEqual(branch_to_action[branch], case.consumer_action_id)
            self.assertEqual(branch_to_equiv[branch], a["deprecated_equivalence"])

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
        # full T6 cross: every verification x every cleanup value appears
        vm_counts = Counter()
        cm_counts = Counter()
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            vm_counts[a["verification_mode"]] += 1
            cm_counts[a["cleanup_mode"]] += 1
        self.assertEqual(set(_CROSSED_AXES["verification_mode"]), set(vm_counts))
        self.assertEqual(set(_CROSSED_AXES["cleanup_mode"]), set(cm_counts))
        # 3888 = 3 * 4 * 324 behaviour combos; each T6 value appears evenly
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["verification_mode"]),
            vm_counts["pg_auth_members_catalog"],
        )
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["cleanup_mode"]),
            cm_counts["revoke_membership"],
        )

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_group_factor_extension_plan(ROOT)
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
        baseline = build_alter_group_factor_loop_plan(ROOT)
        baseline_ids = {c.case_id for c in baseline.cases}
        extension_ids = {c.case_id for c in self.plan.cases}
        self.assertEqual(0, len(baseline_ids & extension_ids))
        self.assertEqual(_BASELINE_COUNT, len(baseline_ids))
        self.assertEqual(_EXTENSION_COUNT, len(extension_ids))

    def test_derived_combinations_yaml_parses_with_required_fields(self) -> None:
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
