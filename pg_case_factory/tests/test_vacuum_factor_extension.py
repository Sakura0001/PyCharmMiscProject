from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.vacuum_factor_extension import (
    VacuumFactorExtensionCase,
    VacuumFactorExtensionError,
    VacuumFactorExtensionPlan,
    build_vacuum_factor_extension_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class VacuumFactorExtensionPlanTest(unittest.TestCase):
    def test_extension_case_count_is_frozen(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        self.assertIsInstance(plan, VacuumFactorExtensionPlan)
        self.assertEqual(1368, len(plan.cases))
        self.assertEqual(1368, plan.raw_combination_count)
        self.assertEqual(0, plan.dropped_count)

    def test_case_numbering_is_contiguous_after_baseline(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        ordinals = [c.ordinal for c in plan.cases]
        self.assertEqual(list(range(48, 1416)), ordinals)
        self.assertEqual("VACUUM00048", plan.cases[0].case_id)
        self.assertEqual("VACUUM01415", plan.cases[-1].case_id)
        self.assertEqual(
            "VACUUM00048.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            "VACUUM01415.sql", plan.cases[-1].sql_filename
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(432, outcomes["success"])
        self.assertEqual(936, outcomes["expected_failure"])

    def test_all_cases_are_marked_extension(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        self.assertTrue(all(c.is_extension for c in plan.cases))

    def test_every_case_has_derivation_record(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_every_case_has_factor_assignment(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertGreater(len(case.factor_assignment), 0)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(
                len(keys), len(set(keys)), case.case_id
            )

    def test_failure_cases_have_sqlstate_and_reason(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        for case in plan.cases:
            if case.outcome == "expected_failure":
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(case.expected_failure_reason)
            else:
                self.assertEqual("00000", case.expected_sqlstate)

    def test_plan_is_deterministic(self) -> None:
        plan_a = build_vacuum_factor_extension_plan(ROOT)
        plan_b = build_vacuum_factor_extension_plan(ROOT)
        self.assertEqual(
            plan_a.extension_multiset_sha256,
            plan_b.extension_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan_a.cases),
            tuple(c.case_id for c in plan_b.cases),
        )

    def test_frozen_extension_multiset_sha256(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        self.assertEqual(
            "3d861c691349d6a91bb97567605f8345e0f083f256fd45b1b91986aa63545695",
            plan.extension_multiset_sha256,
        )

    def test_total_case_count_is_within_cap(self) -> None:
        plan = build_vacuum_factor_extension_plan(ROOT)
        total = 47 + len(plan.cases)
        self.assertLessEqual(total, 20000)
        self.assertEqual(1415, total)


if __name__ == "__main__":
    unittest.main()
