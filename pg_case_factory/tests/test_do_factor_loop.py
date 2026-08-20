"""Tests for do factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.do_factor_loop import (
    build_do_factor_loop_plan,
    compile_do_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestDoFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_do_factor_loop_plan(_REPO)

    def test_obligation_count(self) -> None:
        self.assertEqual(46, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(46, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"GRM": 1, "SFV": 45}, dict(counts))

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "3090f4814061d16f8cb92547f8184630fc4ef269"
            "d04af383e1fd1edb8cdb0f7b",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_do_factor_loop_plan(_REPO)
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 45, "expected_failure": 1},
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
        self.assertEqual(list(range(1, 47)), ordinals)

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("do_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("DO"))

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = (
            compile_do_factor_loop_obligations(_REPO)
        )
        self.assertEqual(
            len(obligations), len(self.plan.obligations)
        )

    def test_baseline_assignments_cover_all_factors(self) -> None:
        required = {
            "statement_branch", "expected_status", "target_state",
            "option_shape", "execution_mode", "target_name_shape",
            "input_output_shape", "environment_context",
            "privilege_context", "invalid_combination",
            "resource_boundary", "verification_mode",
            "cleanup_mode",
        }
        for case in self.plan.cases:
            assign = dict(case.baseline_assignments)
            self.assertTrue(
                required.issubset(assign.keys())
            )


if __name__ == "__main__":
    unittest.main()
