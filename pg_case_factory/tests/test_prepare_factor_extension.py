"""Tests for prepare factor extension plan."""

import unittest
from pathlib import Path

from src.pg_case_factory.prepare_factor_extension import (
    _BASELINE_COUNT,
    _CAP,
    _CROSSED_NEGATIVES,
    build_prepare_factor_extension_plan,
)

_REPO = Path(__file__).resolve().parents[1]


class TestPrepareFactorExtension(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_prepare_factor_extension_plan(_REPO)

    def test_frozen_extension_count(self) -> None:
        self.assertEqual(7656, len(self.plan.cases))

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
            {"success": 2256, "expected_failure": 5400},
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
            "8c29c8835c99e34e3d5d43c3b45c283d"
            "0a38dafc5b3582260c13e7794ce70438",
            self.plan.extension_multiset_sha256,
        )

    def test_constants(self) -> None:
        self.assertEqual(42, _BASELINE_COUNT)
        self.assertEqual(20000, _CAP)

    def test_total_within_cap(self) -> None:
        total = _BASELINE_COUNT + len(self.plan.cases)
        self.assertLessEqual(total, _CAP)
        self.assertGreaterEqual(total, 1000)

    def test_dropped_is_zero(self) -> None:
        self.assertEqual(0, self.plan.dropped_combination_count)

    def test_unique_case_ids(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_filenames(self) -> None:
        names = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(names), len(set(names)))

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("prepare_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_derivation_id_prefix(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.derivation_id.startswith("PREPARE-EXT|")
            )

    def test_crossed_negatives_not_empty(self) -> None:
        self.assertGreater(len(_CROSSED_NEGATIVES), 0)


if __name__ == "__main__":
    unittest.main()
