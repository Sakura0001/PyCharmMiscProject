"""Tests for create_statistics factor_extension plan."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_statistics_factor_extension import (
    build_create_statistics_factor_extension_plan,
)
from src.pg_case_factory.create_statistics_factor_loop import (
    build_create_statistics_factor_loop_plan,
)

_REPO = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 56
_TOTAL = 2640
_EXTENSION_COUNT = _TOTAL - _BASELINE_COUNT


class TestCreateStatisticsFactorExtension(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_statistics_factor_extension_plan(_REPO)

    def test_case_count(self) -> None:
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))

    def test_deterministic(self) -> None:
        other = build_create_statistics_factor_extension_plan(_REPO)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            other.extension_multiset_sha256,
        )

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "1a40ec466edb7f8a796e0c3854dd81d2f13c629110705acd0bc90824f8f9e22c",
            self.plan.extension_multiset_sha256,
        )

    def test_contiguous_ordinals(self) -> None:
        ordinals = [c.ordinal for c in self.plan.cases]
        self.assertEqual(
            list(
                range(
                    _BASELINE_COUNT + 1,
                    _BASELINE_COUNT + 1 + len(self.plan.cases),
                )
            ),
            ordinals,
        )

    def test_unique_case_ids(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_filenames(self) -> None:
        names = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(names), len(set(names)))

    def test_outcomes_valid(self) -> None:
        for case in self.plan.cases:
            self.assertIn(case.outcome, ("success", "expected_failure"))

    def test_derivation_id_prefix(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id.startswith("CSTAT-EXT|"))

    def test_is_extension_flag(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.is_extension)

    def test_baseline_count_constant(self) -> None:
        baseline = build_create_statistics_factor_loop_plan(_REPO)
        self.assertEqual(_BASELINE_COUNT, len(baseline.cases))


if __name__ == "__main__":
    unittest.main()
