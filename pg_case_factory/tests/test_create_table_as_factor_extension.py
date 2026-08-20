"""Tests for create_table_as factor extension plan."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_table_as_factor_extension import (
    _BASELINE_COUNT,
    _CAP,
    build_create_table_as_factor_extension_plan,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateTableAsFactorExtension(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_table_as_factor_extension_plan(_REPO)

    def test_frozen_extension_count(self) -> None:
        self.assertEqual(3975, len(self.plan.cases))

    def test_contiguous_numbering(self) -> None:
        ordinals = [c.ordinal for c in self.plan.cases]
        expected = list(
            range(
                _BASELINE_COUNT + 1,
                _BASELINE_COUNT + 1 + len(self.plan.cases),
            )
        )
        self.assertEqual(expected, ordinals)

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 3180, "expected_failure": 795},
            dict(counts),
        )

    def test_all_is_extension(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.is_extension)

    def test_derivation_records(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_frozen_extension_multiset_sha256(self) -> None:
        self.assertEqual(
            "e8a55668cd32462eef7a71369c5949eaae453b8817b32c19c4de808360332dbb",
            self.plan.extension_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_create_table_as_factor_extension_plan(_REPO)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            other.extension_multiset_sha256,
        )

    def test_constants(self) -> None:
        self.assertEqual(86, _BASELINE_COUNT)
        self.assertEqual(20000, _CAP)

    def test_total_within_cap(self) -> None:
        total = _BASELINE_COUNT + len(self.plan.cases)
        self.assertLessEqual(total, _CAP)
        self.assertGreaterEqual(total, 1000)

    def test_dropped_combinations(self) -> None:
        self.assertEqual(0, self.plan.dropped_combination_count)

    def test_raw_combinations(self) -> None:
        self.assertEqual(3975, self.plan.raw_combination_count)

    def test_unique_case_ids(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_filenames(self) -> None:
        names = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(names), len(set(names)))

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("createtableas_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_derivation_id_prefix(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id.startswith("CTAS-EXT|"))


if __name__ == "__main__":
    unittest.main()
