from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.create_server_factor_extension import (
    CreateServerFactorExtensionCase,
    CreateServerFactorExtensionPlan,
    _BASELINE_COUNT,
    _CAP,
    _CLEANUP_MODES,
    _GENERAL_AXES,
    _VERIFICATION_MODES,
    build_create_server_factor_extension_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateServerFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_server_factor_extension_plan(ROOT)

    def test_plan_type_and_count(self) -> None:
        self.assertIsInstance(
            self.plan,
            CreateServerFactorExtensionPlan,
        )
        self.assertEqual(4800, len(self.plan.cases))

    def test_extension_starts_after_baseline(self) -> None:
        self.assertEqual(
            _BASELINE_COUNT + 1, self.plan.cases[0].ordinal
        )
        self.assertEqual(
            _BASELINE_COUNT + len(self.plan.cases),
            self.plan.cases[-1].ordinal,
        )

    def test_raw_equals_actual_no_over_pruning(self) -> None:
        self.assertEqual(
            self.plan.raw_combination_count, len(self.plan.cases)
        )
        self.assertEqual(0, self.plan.dropped_count)

    def test_case_id_and_filename_convention(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.case_id.startswith("CREATESERVER")
            )
            self.assertTrue(
                case.sql_filename.startswith("CREATESERVER")
            )
            self.assertTrue(case.sql_filename.endswith(".sql"))
            self.assertTrue(
                case.object_prefix.startswith("createserver_")
            )

    def test_all_cases_are_marked_extension(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.is_extension)

    def test_all_cases_have_derivation_record(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_outcome_counts_are_frozen(self) -> None:
        outcomes = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(1440, outcomes["success"])
        self.assertEqual(3360, outcomes["expected_failure"])

    def test_frozen_extension_multiset_sha256(self) -> None:
        self.assertEqual(
            "afa46da5c0dc4be717f5af887a680cb3a9b897d234c81b362364f4774a437522",
            self.plan.extension_multiset_sha256,
        )

    def test_plan_is_deterministic(self) -> None:
        again = build_create_server_factor_extension_plan(ROOT)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            again.extension_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in self.plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_all_verification_modes_present(self) -> None:
        for mode in _VERIFICATION_MODES:
            count = sum(
                1
                for c in self.plan.cases
                if dict(c.factor_assignment).get("verification_mode")
                == mode
            )
            self.assertGreater(
                count, 0, f"missing verification_mode={mode}"
            )

    def test_all_cleanup_modes_present(self) -> None:
        for mode in _CLEANUP_MODES:
            count = sum(
                1
                for c in self.plan.cases
                if dict(c.factor_assignment).get("cleanup_mode") == mode
            )
            self.assertGreater(count, 0, f"missing cleanup_mode={mode}")

    def test_cap_not_exceeded(self) -> None:
        self.assertLessEqual(len(self.plan.cases), _CAP)


if __name__ == "__main__":
    unittest.main()
