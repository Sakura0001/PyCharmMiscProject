"""Tests for create_operator_class factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_operator_class_factor_loop import (
    build_create_operator_class_factor_loop_plan,
    compile_create_operator_class_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateOperatorClassFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_operator_class_factor_loop_plan(
            _REPO
        )

    def test_obligation_count(self) -> None:
        self.assertEqual(54, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(54, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual(
            {"GRM": 1, "SFV": 53}, dict(counts)
        )

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "2b30b54c801935b4599330aade48f408b698c8252fd0263fce73be8556628110",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_create_operator_class_factor_loop_plan(
            _REPO
        )
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 41, "expected_failure": 13},
            dict(counts),
        )

    def test_unique_case_ids(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_filenames(self) -> None:
        names = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(names), len(set(names)))

    def test_contiguous_ordinals(self) -> None:
        ordinals = [c.ordinal for c in self.plan.cases]
        self.assertEqual(list(range(1, 55)), ordinals)

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith(
                    "createoperatorclass_"
                )
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.case_id.startswith("CREATEOPERATORCLASS")
            )

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = (
            compile_create_operator_class_factor_loop_obligations(
                _REPO
            )
        )
        self.assertEqual(
            len(obligations), len(self.plan.obligations)
        )


if __name__ == "__main__":
    unittest.main()
