"""Tests for create_group factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_group_factor_loop import (
    build_create_group_factor_loop_plan,
    compile_create_group_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateGroupFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_group_factor_loop_plan(_REPO)

    def test_obligation_count(self) -> None:
        self.assertEqual(66, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(66, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"GRM": 2, "SFV": 64}, dict(counts))

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "68b1eaac1835ba27ab5e0efa7929dbcbeb7f00838a62fe13b43213eea7f2e189",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_create_group_factor_loop_plan(_REPO)
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 57, "expected_failure": 9}, dict(counts)
        )

    def test_unique_case_ids(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_filenames(self) -> None:
        names = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(names), len(set(names)))

    def test_contiguous_ordinals(self) -> None:
        ordinals = [c.ordinal for c in self.plan.cases]
        self.assertEqual(
            list(range(1, 67)), ordinals
        )

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("creategroup_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("CREATEGROUP"))

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = compile_create_group_factor_loop_obligations(_REPO)
        self.assertEqual(len(obligations), len(self.plan.obligations))


if __name__ == "__main__":
    unittest.main()
