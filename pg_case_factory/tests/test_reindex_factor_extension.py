from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.reindex_factor_extension import (
    ReindexFactorExtensionCase,
    ReindexFactorExtensionError,
    ReindexFactorExtensionPlan,
    _BASELINE_COUNT,
    _CAP,
    _CLEANUP_MODES,
    _VERIFICATION_MODES,
    build_reindex_factor_extension_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class ReindexFactorExtensionPlanTest(unittest.TestCase):
    def test_extension_case_count_is_frozen(self) -> None:
        plan = build_reindex_factor_extension_plan(ROOT)
        self.assertIsInstance(plan, ReindexFactorExtensionPlan)
        self.assertEqual(3492, len(plan.cases))
        self.assertEqual(3492, plan.raw_combination_count)
        self.assertEqual(0, plan.dropped_count)

    def test_case_numbering_is_contiguous_after_baseline(self) -> None:
        plan = build_reindex_factor_extension_plan(ROOT)
        ordinals = [c.ordinal for c in plan.cases]
        self.assertEqual(list(range(84, 3576)), ordinals)
        self.assertEqual("REINDEX00084", plan.cases[0].case_id)
        self.assertEqual("REINDEX03575", plan.cases[-1].case_id)
        self.assertEqual(
            "REINDEX00084.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            "REINDEX03575.sql", plan.cases[-1].sql_filename
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_reindex_factor_extension_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(1656, outcomes["success"])
        self.assertEqual(1836, outcomes["expected_failure"])

    def test_all_cases_are_marked_extension(self) -> None:
        plan = build_reindex_factor_extension_plan(ROOT)
        self.assertTrue(all(c.is_extension for c in plan.cases))

    def test_every_case_has_derivation_record(self) -> None:
        plan = build_reindex_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_every_case_has_factor_assignment(self) -> None:
        plan = build_reindex_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertGreater(len(case.factor_assignment), 0)

    def test_extension_sha256_is_frozen(self) -> None:
        plan = build_reindex_factor_extension_plan(ROOT)
        self.assertEqual(
            "b449c9129c5eecc88a14948a6b7bf3c0a3fefefa893822783a0567f61160b020",
            plan.extension_multiset_sha256,
        )

    def test_constants_are_frozen(self) -> None:
        self.assertEqual(83, _BASELINE_COUNT)
        self.assertEqual(20000, _CAP)
        self.assertEqual(4, len(_VERIFICATION_MODES))
        self.assertEqual(3, len(_CLEANUP_MODES))


if __name__ == "__main__":
    unittest.main()
