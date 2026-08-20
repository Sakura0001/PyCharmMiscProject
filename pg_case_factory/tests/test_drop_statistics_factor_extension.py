"""Tests for the bounded DROP STATISTICS post-coverage extension expander.

The marginal factor-value-loop (``drop_statistics_factor_loop.py``) is the
frozen 35-case baseline (GRM 1 + SFV 32 + RISK 2).  This module's expander
adds the bounded post-coverage extension phase: cross-factor combinations
of the behaviour axes across the single official synopsis branch (at most one
failure-causing value per case, so attribution stays clean), with
``verification_mode`` crossed and ``cleanup_mode`` crossed so every declared
T6 value is exercised.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.drop_statistics_factor_extension import (
    DropStatisticsFactorExtensionCase,
    DropStatisticsFactorExtensionError,
    DropStatisticsFactorExtensionPlan,
    build_drop_statistics_factor_extension_plan,
)
from pg_case_factory.drop_statistics_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_statistics_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 35
_EXTENSION_COUNT = 2580
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 2615
_SUCCESS_EXTENSIONS = 912
_FAILURE_EXTENSIONS = 1668
_EXTENSION_MULTISET_SHA256 = (
    "bd5483d4d46dfab2c11acfd4ff3b62c955f2b8b3cb3a8ea62198d64d883fad7c"
)

_IF_EXISTS_OMITTED = "without_if_exists"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("privilege_context") == "non_owner_no_privilege"
        or assignment.get("executor_privilege") == "non_owner_no_privilege"
    )


def _stats_missing_failure_fires(assignment: dict[str, str]) -> bool:
    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("statistics_existence") == "statistics_not_exists"
        or assignment.get("statistics_name_shape") == "non_existing_name"
        or assignment.get("multi_target") == "multi_target_some_not_exist"
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _stats_missing_failure_fires(assignment):
        count += 1
    return count


_CROSSED_AXES = {
    "statement_branch": ("branch_drop_statistics",),
    "target_action": ("drop_statistics",),
    "privilege_context": (
        "non_owner_no_privilege",
        "superuser",
        "table_owner",
    ),
    "statistics_existence": ("statistics_exists", "statistics_not_exists"),
    "if_exists_clause": ("with_if_exists", "without_if_exists"),
    "cascade_restrict_clause": (
        "cascade",
        "no_clause_default_restrict",
        "restrict",
    ),
    "multi_target": (
        "multi_target_all_exist",
        "multi_target_some_not_exist",
        "single_target",
    ),
    "statistics_name_shape": (
        "non_existing_name",
        "quoted_name",
        "reserved_word_name",
        "schema_qualified_name",
        "simple_name",
    ),
    "executor_privilege": (
        "non_owner_no_privilege",
        "superuser",
        "table_owner",
    ),
    "verification_mode": (
        "error_assertion",
        "pg_statistic_ext_catalog",
    ),
    "cleanup_mode": ("drop_statistics",),
}

_HELD_CONSTANT = {
    "grammar_branch": "branch_1",
    "nonexistent_statistics": "statistics_does_not_exist",
    "privilege_insufficient": "non_table_owner_dropping_statistics",
}

_BRANCH_GRAMMAR = {"branch_drop_statistics": "branch_1"}
_BRANCH_FIXED_ACTION = {"branch_drop_statistics": "drop_statistics"}


class DropStatisticsFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_drop_statistics_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, DropStatisticsFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
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
        self.assertEqual("DROPSTATISTICS00036", first.case_id)
        self.assertEqual(
            f"DROPSTATISTICS{_TOTAL_COUNT:05d}", last.case_id
        )
        self.assertEqual("DROPSTATISTICS00036.sql", first.sql_filename)
        self.assertEqual(
            f"DROPSTATISTICS{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("dropstatistics_00036_", first.object_prefix)
        self.assertEqual(
            f"dropstatistics_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, DropStatisticsFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
            self.assertEqual(15, len(case.factor_assignment), case.case_id)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)
            self.assertEqual(
                tuple(sorted(case.factor_assignment)),
                case.factor_assignment,
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

    def test_expected_status_is_derived_from_failure(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            fires = _privilege_failure_fires(a) or _stats_missing_failure_fires(a)
            self.assertEqual(
                "failure" if fires else "success",
                a["expected_status"],
                case.case_id,
            )

    def test_expected_sqlstate_matches_failure_pair(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if case.outcome == "success":
                self.assertEqual("00000", case.expected_sqlstate)
                self.assertIsNone(case.expected_failure_reason)
            else:
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(case.expected_failure_reason)

    def test_privilege_negative_fires_for_non_owner(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_context"] == "non_owner_no_privilege":
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                self.assertEqual("42501", case.expected_sqlstate)

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

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_drop_statistics_factor_extension_plan(ROOT)
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
        baseline = build_drop_statistics_factor_loop_plan(ROOT)
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
