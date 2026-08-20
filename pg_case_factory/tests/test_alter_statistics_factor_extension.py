"""Tests for the bounded ALTER STATISTICS post-coverage extension expander."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_statistics_factor_extension import (
    AlterStatisticsFactorExtensionCase,
    AlterStatisticsFactorExtensionPlan,
    build_alter_statistics_factor_extension_plan,
)
from pg_case_factory.alter_statistics_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_statistics_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 56
_EXTENSION_COUNT = 1404
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 1460
_SUCCESS_EXTENSIONS = 648
_FAILURE_EXTENSIONS = 756

_CROSSED_NEGATIVES = frozenset(
    {
        ("statistics_state", "non_existent"),
        ("executor_privilege", "non_owner_no_privilege"),
        ("statistics_target_value", "out_of_range"),
        ("rename_behavior", "rename_to_existing_name_conflict"),
        ("new_owner_shape", "nonexistent_role"),
        ("set_schema_behavior", "nonexistent_schema"),
    }
)


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return sum(
        1
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    )


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for pair in _CROSSED_NEGATIVES:
        if assignment.get(pair[0]) == pair[1]:
            return pair
    return None


class AlterStatisticsFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_statistics_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(
        self,
    ) -> None:
        self.assertIsInstance(
            self.plan, AlterStatisticsFactorExtensionPlan
        )
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        self.assertEqual(
            _EXTENSION_COUNT, self.plan.raw_combination_count
        )
        self.assertEqual(0, self.plan.dropped_count)

    def test_ordinals_continue_after_baseline_with_five_digit_scheme(
        self,
    ) -> None:
        ordinals = [case.ordinal for case in self.plan.cases]
        self.assertEqual(
            list(range(_BASELINE_COUNT + 1, _TOTAL_COUNT + 1)),
            ordinals,
        )
        first, last = self.plan.cases[0], self.plan.cases[-1]
        self.assertEqual(_BASELINE_COUNT + 1, first.ordinal)
        self.assertEqual(_TOTAL_COUNT, last.ordinal)
        self.assertEqual("ALTERSTATISTICS00057", first.case_id)
        self.assertEqual(
            f"ALTERSTATISTICS{_TOTAL_COUNT:05d}", last.case_id
        )

    def test_every_case_is_marked_extension_with_full_assignment(
        self,
    ) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(
                case, AlterStatisticsFactorExtensionCase
            )
            self.assertTrue(case.is_extension, case.case_id)
            self.assertEqual(
                24, len(case.factor_assignment), case.case_id
            )
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)
            self.assertEqual(
                tuple(sorted(case.factor_assignment)),
                case.factor_assignment,
            )

    def test_outcome_split_matches_frozen_arithmetic(self) -> None:
        outcomes = Counter(case.outcome for case in self.plan.cases)
        self.assertEqual(_SUCCESS_EXTENSIONS, outcomes["success"])
        self.assertEqual(
            _FAILURE_EXTENSIONS, outcomes["expected_failure"]
        )
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

    def test_expected_sqlstate_matches_present_failure_pair(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            pair = _present_failure_pair(assignment)
            if pair is None:
                self.assertEqual(
                    "success", case.outcome, case.case_id
                )
                self.assertEqual(
                    "00000", case.expected_sqlstate, case.case_id
                )
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

    def test_every_crossed_factor_value_is_witnessed(self) -> None:
        crossed = {
            "statistics_state": ("exists", "non_existent"),
            "executor_privilege": (
                "superuser",
                "table_owner",
                "non_owner_no_privilege",
            ),
            "statistics_target_value": (
                "default_keyword",
                "zero",
                "positive_integer",
                "negative_one_default",
                "maximum_value_10000",
                "out_of_range",
            ),
            "rename_behavior": (
                "rename_to_new_name",
                "rename_to_existing_name_conflict",
            ),
            "new_name_shape": (
                "simple_name",
                "quoted_name",
                "existing_name_conflict",
            ),
            "new_owner_shape": ("existing_role", "nonexistent_role"),
            "new_schema_shape": (
                "existing_schema",
                "nonexistent_schema",
            ),
            "owner_to_shape": (
                "explicit_role_name",
                "current_role_keyword",
                "current_user_keyword",
                "session_user_keyword",
            ),
            "statistics_name_shape": (
                "simple_name",
                "quoted_name",
                "schema_qualified_name",
                "non_existent_name",
            ),
            "target_value_shape": (
                "integer_value",
                "default_keyword",
                "negative_one",
                "very_large_value",
            ),
            "grammar_branch": (
                "branch_set_statistics",
                "branch_rename",
                "branch_owner_to",
                "branch_set_schema",
            ),
            "verification_mode": (
                "pg_statistic_ext_catalog",
                "stxstattarget_query",
                "error_assertion",
            ),
            "cleanup_mode": (
                "DROP_STATISTICS",
                "DROP_STATISTICS_IF_EXISTS",
                "DROP_STATISTICS_CASCADE",
            ),
            "table_dependency": ("underlying_table_exists",),
        }
        witnessed: dict[str, set[str]] = {
            factor: set() for factor in crossed
        }
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            for factor in crossed:
                if factor in a:
                    witnessed[factor].add(a[factor])
        for factor, values in crossed.items():
            self.assertEqual(
                set(values),
                witnessed[factor],
                f"factor {factor}: "
                f"missing {set(values) - witnessed[factor]}",
            )

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(
                case.derived_from_combination_group, case.case_id
            )
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_statistics_factor_extension_plan(ROOT)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            again.extension_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in self.plan.cases),
            tuple(c.case_id for c in again.cases),
        )
        for left, right in zip(self.plan.cases, again.cases):
            self.assertEqual(
                left.factor_assignment, right.factor_assignment
            )

    def test_extensions_do_not_collide_with_baseline_numbering(
        self,
    ) -> None:
        baseline = build_alter_statistics_factor_loop_plan(ROOT)
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
