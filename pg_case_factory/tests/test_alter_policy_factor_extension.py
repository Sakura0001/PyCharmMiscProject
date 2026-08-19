"""Tests for the bounded ALTER POLICY post-coverage extension expander.

The marginal factor-value-loop (``alter_policy_factor_loop.py``) is the
frozen 72-case baseline (GRM 2 + SFV 68 + RISK 2).  This module's expander
adds the bounded post-coverage extension phase: cross-factor combinations of
the positive behaviour axes (``policy_name_shape``, ``table_name_shape``,
``privilege_level``, ``rls_enabled``) across all five ``alter_action`` forms,
with each action's signature sub-axis crossed where it is observable
(``new_name_shape`` for ``rename``, ``using_expression`` for
``modify_using``, ``with_check_expression`` for ``modify_with_check``,
``role_target`` for ``modify_roles``), at most one failure-causing value per
case so attribution stays clean, with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.  Each
extension case carries a derivation record and is marked ``is_extension =
True``; it never replaces a required-baseline obligation.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_policy_factor_extension import (
    AlterPolicyFactorExtensionCase,
    AlterPolicyFactorExtensionError,
    AlterPolicyFactorExtensionPlan,
    build_alter_policy_factor_extension_plan,
)
from pg_case_factory.alter_policy_factor_loop import (
    _ACTION_TO_BRANCH,
    _SFV_FAILURE_SQLSTATE,
    build_alter_policy_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 72
_EXTENSION_COUNT = 13032
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 13104
_SUCCESS_EXTENSIONS = 5616
_FAILURE_EXTENSIONS = 7416
_EXTENSION_MULTISET_SHA256 = (
    "df574f2b0bccf0f8bca402ee4d5581fab75bfc6dbf3b15f401e778bdb465c6d4"
)

# Behaviour-negative (factor, value) pairs that are CROSSED in extensions.
# The privilege cluster (non_owner) is counted as a single unit via
# _PRIVILEGE_CLUSTER_VALUES and is therefore not duplicated here.  The
# new_name_shape = duplicate_name / invalid_name negatives are only ever
# attributable where RENAME TO is actually rendered (the rename action), so
# they are conditional on the action.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("table_name_shape", "nonexistent_table"),
        ("policy_name_shape", "nonexistent_name"),
        ("new_name_shape", "duplicate_name"),
        ("new_name_shape", "invalid_name"),
    }
)
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner"})

# Crossed axes.  Every value here must be witnessed somewhere in the
# extension plan.  alter_action and target_action are tied 1:1
# (target_action := alter_action), so both carry the same five values.
_CROSSED_AXES = {
    "alter_action": (
        "rename",
        "modify_combined",
        "modify_roles",
        "modify_using",
        "modify_with_check",
    ),
    "target_action": (
        "rename",
        "modify_combined",
        "modify_roles",
        "modify_using",
        "modify_with_check",
    ),
    "new_name_shape": ("simple_id", "quoted_id", "duplicate_name", "invalid_name"),
    "using_expression": ("omitted_keep_original", "new_expression"),
    "with_check_expression": ("omitted_keep_original", "new_expression"),
    "role_target": (
        "CURRENT_ROLE",
        "CURRENT_USER",
        "PUBLIC",
        "SESSION_USER",
        "multiple_roles",
        "single_role",
    ),
    "policy_name_shape": ("simple_id", "quoted_id", "nonexistent_name", "existing_name"),
    "table_name_shape": (
        "simple_id",
        "quoted_id",
        "schema_qualified",
        "nonexistent_table",
    ),
    "privilege_level": ("superuser", "table_owner", "non_owner"),
    "rls_enabled": ("rls_enabled", "rls_not_enabled"),
    "verification_mode": (
        "catalog_query_pg_policy",
        "rls_behavior_test",
        "error_assertion",
    ),
    "cleanup_mode": (
        "drop_policy",
        "revert_rename",
        "disable_rls_and_drop_policy",
        "drop_table",
    ),
}

# Factors held at a single baseline value across all extensions (the baseline
# owns their negative counterparts one-per-value; they are never crossed
# here).  statement_branch / grammar_branch are NOT held constant: they vary
# with the action (branch_rename for rename, branch_modify for the rest) and
# are asserted separately in test_branch_grammar_and_consumer_action.
_HELD_CONSTANT = {
    "object_state": "exists",
    "role_name_shape": "simple_id",
    "privilege_denied": "owner_execution",
    "rls_not_enabled": "rls_enabled",
    "table_existence": "table_exists",
    "policy_existence": "policy_exists",
    "role_existence": "role_exists",
    "nonexistent_policy": "policy_exists",
    "nonexistent_table": "table_exists",
    "cannot_alter_command_type": "only_rename_and_modify_allowed",
    "cannot_alter_policy_type": "only_rename_and_modify_allowed",
}


def _privilege_boundary_fires(assignment: dict[str, str]) -> bool:
    """Whether the must_be_owner check actually fires.

    ALTER POLICY has no ``OWNER TO`` clause, so there is no SESSION_USER
    no-op-transfer carve-out (unlike ALTER MATERIALIZED VIEW).  The privilege
    boundary fires simply when ``privilege_level = non_owner``: a non-owner
    attempting to alter a policy on a table they do not own is rejected with
    42501 (must_be_owner).
    """

    return assignment.get("privilege_level") == "non_owner"


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + behaviour negatives; must stay at most one."""

    cluster = (
        1
        if assignment.get("privilege_level") in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
        else 0
    )
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    return cluster + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    Mirrors the module's attribution order: privilege cluster (when the
    boundary fires), then nonexistent_table, then nonexistent_name, then
    duplicate_name, then invalid_name.  The at-most-one rule has already
    excluded double-failure cases from the kept set, so only one can match.
    """

    level = assignment.get("privilege_level")
    if (
        level in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
    ):
        return ("privilege_level", level)
    if assignment.get("table_name_shape") == "nonexistent_table":
        return ("table_name_shape", "nonexistent_table")
    if assignment.get("policy_name_shape") == "nonexistent_name":
        return ("policy_name_shape", "nonexistent_name")
    if assignment.get("new_name_shape") == "duplicate_name":
        return ("new_name_shape", "duplicate_name")
    if assignment.get("new_name_shape") == "invalid_name":
        return ("new_name_shape", "invalid_name")
    return None


class AlterPolicyFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_policy_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterPolicyFactorExtensionPlan)
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
        self.assertEqual("ALTERPOLICY00073", first.case_id)
        self.assertEqual(
            f"ALTERPOLICY{_TOTAL_COUNT:05d}", last.case_id
        )
        self.assertEqual("ALTERPOLICY00073.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERPOLICY{_TOTAL_COUNT:05d}.sql",
            last.sql_filename,
        )
        self.assertEqual("alterpolicy_00073_", first.object_prefix)
        self.assertEqual(
            f"alterpolicy_{_TOTAL_COUNT:05d}_",
            last.object_prefix,
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(
                case, AlterPolicyFactorExtensionCase
            )
            self.assertTrue(case.is_extension, case.case_id)
            # 26 keys: 24 _BASELINE_DEFAULTS + verification_mode (crossed) +
            # cleanup_mode (crossed).  The T5 negatives are absent because
            # they are owned one-per-value by the marginal baseline.
            self.assertEqual(26, len(case.factor_assignment), case.case_id)
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
        # ALTER POLICY has no IF EXISTS clause, so there is no no-op-success
        # carve-out: every success case has exactly zero failure units and
        # every expected_failure case has exactly one.
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            count = _failure_unit_count(assignment)
            self.assertLessEqual(count, 1, case.case_id)
            if case.outcome == "expected_failure":
                self.assertEqual(1, count, case.case_id)
            else:
                self.assertEqual(0, count, case.case_id)

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

    def test_privilege_cluster_fires_only_for_non_owner(self) -> None:
        # The single non_owner value models the must_be_owner (42501)
        # boundary.  superuser and table_owner are both success privilege
        # levels.  ALTER POLICY has no OWNER TO clause, so there is no
        # SESSION_USER no-op-transfer carve-out: non_owner always fires.
        witnessed_levels = {
            dict(c.factor_assignment)["privilege_level"]
            for c in self.plan.cases
        }
        self.assertTrue(
            _PRIVILEGE_CLUSTER_VALUES.issubset(witnessed_levels)
        )
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_level"] in _PRIVILEGE_CLUSTER_VALUES:
                self.assertTrue(_privilege_boundary_fires(a), case.case_id)
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                self.assertEqual(
                    "42501", case.expected_sqlstate, case.case_id
                )
            else:
                # superuser / table_owner: a 42501 failure is impossible.
                self.assertNotEqual(
                    "42501", case.expected_sqlstate, case.case_id
                )

    def test_new_name_shape_only_crossed_for_rename(self) -> None:
        # new_name_shape is only relevant for the rename action; for the
        # other four alter_action values it stays at simple_id, so
        # duplicate_name / invalid_name are never attributable where RENAME
        # TO is not rendered.
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["alter_action"] != "rename":
                self.assertEqual(
                    "simple_id", a["new_name_shape"], case.case_id
                )

    def test_branch_grammar_and_consumer_action_are_consistent(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            action = a["alter_action"]
            self.assertEqual(
                _ACTION_TO_BRANCH[action], a["statement_branch"], case.case_id
            )
            self.assertEqual(
                _ACTION_TO_BRANCH[action], a["grammar_branch"], case.case_id
            )
            self.assertEqual(action, a["target_action"], case.case_id)
            self.assertEqual(
                action, case.consumer_action_id, case.case_id
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
        # full T6 cross with no truncation => each value appears evenly.
        # The at-most-one filter is on behaviours, not on T6 values, so each
        # kept behaviour is crossed with all 12 (verification x cleanup)
        # pairs and the T6 distributions stay even.
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["verification_mode"]),
            vm_counts["catalog_query_pg_policy"],
        )
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["cleanup_mode"]),
            cm_counts["drop_policy"],
        )

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)
            self.assertTrue(case.derivation_id.startswith("AP-EXT|"))

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_policy_factor_extension_plan(ROOT)
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
        baseline = build_alter_policy_factor_loop_plan(ROOT)
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
