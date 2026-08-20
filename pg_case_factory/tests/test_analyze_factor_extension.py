from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.analyze_factor_extension import (
    AnalyzeFactorExtensionCase,
    AnalyzeFactorExtensionError,
    AnalyzeFactorExtensionPlan,
    _BASELINE_COUNT,
    _CAP,
    _CLEANUP_MODES,
    _VERIFICATION_MODES,
    build_analyze_factor_extension_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class AnalyzeFactorExtensionPlanTest(unittest.TestCase):
    def test_extension_case_count_is_frozen(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        self.assertIsInstance(plan, AnalyzeFactorExtensionPlan)
        self.assertEqual(7104, len(plan.cases))
        self.assertEqual(7104, plan.raw_combination_count)
        self.assertEqual(0, plan.dropped_count)

    def test_case_numbering_is_contiguous_after_baseline(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        ordinals = [c.ordinal for c in plan.cases]
        self.assertEqual(list(range(49, 7153)), ordinals)
        self.assertEqual("ANALYZE00049", plan.cases[0].case_id)
        self.assertEqual("ANALYZE07152", plan.cases[-1].case_id)
        self.assertEqual(
            "ANALYZE00049.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            "ANALYZE07152.sql", plan.cases[-1].sql_filename
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(2304, outcomes["success"])
        self.assertEqual(4800, outcomes["expected_failure"])

    def test_all_cases_are_marked_extension(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        self.assertTrue(all(c.is_extension for c in plan.cases))

    def test_every_case_has_derivation_record(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_every_case_has_factor_assignment(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertGreater(len(case.factor_assignment), 0)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(
                len(keys), len(set(keys)), case.case_id
            )

    def test_failure_cases_have_sqlstate_and_reason(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        for case in plan.cases:
            if case.outcome == "expected_failure":
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(case.expected_failure_reason)
            else:
                self.assertEqual("00000", case.expected_sqlstate)

    def test_plan_is_deterministic(self) -> None:
        plan_a = build_analyze_factor_extension_plan(ROOT)
        plan_b = build_analyze_factor_extension_plan(ROOT)
        self.assertEqual(
            plan_a.extension_multiset_sha256,
            plan_b.extension_multiset_sha256,
        )

    def test_frozen_extension_multiset_sha256(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        self.assertEqual(
            "409396e2be84cc7bee9947145b0cc468a60f019eb491dae3f98fd49843c56a3e",
            plan.extension_multiset_sha256,
        )

    def test_constants_are_frozen(self) -> None:
        self.assertEqual(48, _BASELINE_COUNT)
        self.assertEqual(20000, _CAP)
        self.assertEqual(
            ("catalog_query", "effect_query", "returned_rows", "error_assertion"),
            _VERIFICATION_MODES,
        )
        self.assertEqual(
            ("rollback", "drop_objects", "reset_state"), _CLEANUP_MODES
        )

    def test_total_case_count_is_within_cap(self) -> None:
        plan = build_analyze_factor_extension_plan(ROOT)
        total = _BASELINE_COUNT + len(plan.cases)
        self.assertLessEqual(total, _CAP)
        self.assertEqual(7152, total)


if __name__ == "__main__":
    unittest.main()
