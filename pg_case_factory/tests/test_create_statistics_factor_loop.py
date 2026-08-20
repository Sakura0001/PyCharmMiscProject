"""Tests for create_statistics factor_loop obligation ledger."""

import unittest
from collections import Counter
from pathlib import Path

from src.pg_case_factory.create_statistics_factor_loop import (
    build_create_statistics_factor_loop_plan,
    compile_create_statistics_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateStatisticsFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_statistics_factor_loop_plan(_REPO)

    def test_obligation_count(self) -> None:
        self.assertEqual(56, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(56, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"GRM": 2, "SFV": 54}, dict(counts))

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "2c8d6490d6ae3c85645b1d4266b07f3340424db4e34e78433de6e5f86add4f82",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_create_statistics_factor_loop_plan(_REPO)
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 43, "expected_failure": 13}, dict(counts)
        )

    def test_unique_case_ids(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_filenames(self) -> None:
        names = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(names), len(set(names)))

    def test_contiguous_ordinals(self) -> None:
        ordinals = [c.ordinal for c in self.plan.cases]
        self.assertEqual(list(range(1, 57)), ordinals)

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("createstatistics_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("CREATESTATISTICS"))

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = compile_create_statistics_factor_loop_obligations(_REPO)
        self.assertEqual(len(obligations), len(self.plan.obligations))


if __name__ == "__main__":
    unittest.main()
