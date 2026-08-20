"""Tests for create_function factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_function_factor_loop import (
    build_create_function_factor_loop_plan,
    compile_create_function_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateFunctionFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_function_factor_loop_plan(_REPO)

    def test_obligation_count(self) -> None:
        self.assertEqual(121, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(121, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"SFV": 121}, dict(counts))

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "04bd2be0fe47b5d5d708ed131d7ccc7fbf34973ebc95fae5d65b5fa2ab2c4163",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_create_function_factor_loop_plan(_REPO)
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 109, "expected_failure": 12}, dict(counts)
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
            list(range(1, 122)), ordinals
        )

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("createfunction_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("CREATEFUNCTION"))

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = compile_create_function_factor_loop_obligations(_REPO)
        self.assertEqual(len(obligations), len(self.plan.obligations))

    def test_parallel_clause_coverage(self) -> None:
        parallel_values = set()
        for case in self.plan.cases:
            for k, v in case.baseline_assignments:
                if k == "parallel_clause":
                    parallel_values.add(v)
        self.assertEqual(
            {"UNSAFE", "RESTRICTED", "SAFE", "absent"},
            parallel_values,
        )


if __name__ == "__main__":
    unittest.main()
