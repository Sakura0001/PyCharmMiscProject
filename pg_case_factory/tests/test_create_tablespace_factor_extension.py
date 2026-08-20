from pathlib import Path
import unittest

from pg_case_factory.create_tablespace_factor_extension import (
    CreateTablespaceFactorExtensionCase,
    CreateTablespaceFactorExtensionPlan,
    build_create_tablespace_factor_extension_plan,
)
from pg_case_factory.create_tablespace_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateTablespaceFactorExtensionPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_create_tablespace_factor_extension_plan(ROOT)

    def test_builds_extension_plan(self) -> None:
        self.assertIsInstance(
            self.plan, CreateTablespaceFactorExtensionPlan
        )

    def test_extension_case_count_is_frozen(self) -> None:
        self.assertEqual(4500, len(self.plan.cases))
        self.assertEqual(4500, self.plan.raw_combination_count)
        self.assertEqual(0, self.plan.dropped_count)

    def test_ordinals_continue_after_baseline(self) -> None:
        for case in self.plan.cases:
            self.assertGreater(case.ordinal, 67)
        self.assertEqual(
            68, self.plan.cases[0].ordinal
        )
        self.assertEqual(
            4567, self.plan.cases[-1].ordinal
        )

    def test_case_ids_and_filenames_are_unique(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        files = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(files), len(set(files)))

    def test_every_case_is_marked_extension(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.is_extension)
            self.assertIsInstance(
                case, CreateTablespaceFactorExtensionCase
            )

    def test_every_case_has_derivation_record(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_outcome_attribution_is_at_most_one_failure(self) -> None:
        from pg_case_factory.create_tablespace_factor_extension import (
            _failure_unit_count,
        )
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            self.assertLessEqual(
                _failure_unit_count(assignment), 1
            )

    def test_failure_cases_have_valid_sqlstate(self) -> None:
        failures = [
            c for c in self.plan.cases
            if c.outcome == "expected_failure"
        ]
        self.assertGreater(len(failures), 0)
        for case in failures:
            self.assertEqual(5, len(case.expected_sqlstate))
            self.assertIsNotNone(case.expected_failure_reason)

    def test_success_cases_have_zero_sqlstate(self) -> None:
        successes = [
            c for c in self.plan.cases
            if c.outcome == "success"
        ]
        self.assertGreater(len(successes), 0)
        for case in successes:
            self.assertEqual("00000", case.expected_sqlstate)
            self.assertIsNone(case.expected_failure_reason)

    def test_factor_assignments_have_no_duplicate_keys(self) -> None:
        for case in self.plan.cases:
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(
                len(keys), len(set(keys)), case.case_id
            )

    def test_frozen_extension_multiset_sha256(self) -> None:
        self.assertEqual(
            "39335d1fb6654e931888b6935c7c5655e7656d9e6cab96870f9fc04870123a55",
            self.plan.extension_multiset_sha256,
        )

    def test_derived_combinations_yaml_is_nonempty(self) -> None:
        self.assertTrue(self.plan.derived_combinations_yaml.strip())

    def test_plan_is_deterministic(self) -> None:
        again = build_create_tablespace_factor_extension_plan(ROOT)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            again.extension_multiset_sha256,
        )
        self.assertEqual(
            len(self.plan.cases), len(again.cases)
        )


if __name__ == "__main__":
    unittest.main()
