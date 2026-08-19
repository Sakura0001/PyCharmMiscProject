"""Frozen-spec tests for the ALTER OPERATOR FAMILY bounded Option-A extension."""

from __future__ import annotations

from collections import Counter
import unittest
from pathlib import Path

from pg_case_factory.alter_operator_family_factor_extension import (
    build_alter_operator_family_factor_extension_plan,
)
from pg_case_factory.alter_operator_family_factor_loop import (
    build_alter_operator_family_factor_loop_plan,
)

ROOT = Path(__file__).resolve().parents[1]

_EXPECTED_EXTENSION_MULTISETS_SHA256 = (
    "1e0033cc5148ef2570ba9c5f6702595813576038c9aee85438314db6eaf4b6a6"
)
_EXPECTED_BASELINE_COUNT = 59
_EXPECTED_EXTENSION_COUNT = 4464
_EXPECTED_TOTAL_COUNT = _EXPECTED_BASELINE_COUNT + _EXPECTED_EXTENSION_COUNT


class AlterOperatorFamilyFactorExtensionPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_alter_operator_family_factor_loop_plan(ROOT)
        self.plan = build_alter_operator_family_factor_extension_plan(ROOT)

    def test_extension_count_is_frozen(self) -> None:
        self.assertEqual(len(self.plan.cases), _EXPECTED_EXTENSION_COUNT)

    def test_total_count_is_frozen(self) -> None:
        self.assertEqual(
            len(self.baseline.cases) + len(self.plan.cases),
            _EXPECTED_TOTAL_COUNT,
        )

    def test_extension_multiset_sha256_is_frozen(self) -> None:
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            _EXPECTED_EXTENSION_MULTISETS_SHA256,
        )

    def test_all_cases_are_extension(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.is_extension)

    def test_outcome_counts_are_frozen(self) -> None:
        outcomes = Counter(case.outcome for case in self.plan.cases)
        self.assertEqual(outcomes["expected_failure"], 3480)
        self.assertEqual(outcomes["success"], 984)

    def test_each_case_has_derivation_record(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)
            self.assertTrue(case.derivation_id.startswith("AOF-EXT|"))

    def test_case_ids_are_unique_and_contiguous(self) -> None:
        ids = [
            int(c.case_id.replace("ALTEROPERATORFAMILY", ""))
            for c in self.plan.cases
        ]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(min(ids), _EXPECTED_BASELINE_COUNT + 1)
        self.assertEqual(max(ids), _EXPECTED_TOTAL_COUNT)

    def test_branch_coverage(self) -> None:
        branches = Counter(
            case.derived_from_combination_group for case in self.plan.cases
        )
        self.assertEqual(branches["branch_add"], 1728)
        self.assertEqual(branches["branch_drop"], 1152)
        self.assertEqual(branches["branch_rename"], 144)
        self.assertEqual(branches["branch_owner"], 1260)
        self.assertEqual(branches["branch_set_schema"], 180)

    def test_plan_is_reproducible(self) -> None:
        other = build_alter_operator_family_factor_extension_plan(ROOT)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            other.extension_multiset_sha256,
        )


if __name__ == "__main__":
    unittest.main()
