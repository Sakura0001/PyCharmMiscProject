"""Tests for create_procedure factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_procedure_factor_loop import (
    build_create_procedure_factor_loop_plan,
    compile_create_procedure_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateProcedureFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_procedure_factor_loop_plan(_REPO)

    def test_obligation_count(self) -> None:
        self.assertEqual(92, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(92, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"SFV": 92}, dict(counts))

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "fba21366861f95df22e797cde089011a62e9308dd8c99c77115d983096e029be",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_create_procedure_factor_loop_plan(_REPO)
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 83, "expected_failure": 9}, dict(counts)
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
            list(range(1, 93)), ordinals
        )

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("createprocedure_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("CREATEPROCEDURE"))

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = compile_create_procedure_factor_loop_obligations(_REPO)
        self.assertEqual(len(obligations), len(self.plan.obligations))

    def test_or_replace_coverage(self) -> None:
        or_replace_values = set()
        for case in self.plan.cases:
            for k, v in case.baseline_assignments:
                if k == "or_replace_clause":
                    or_replace_values.add(v)
        self.assertEqual(
            {"present", "absent"},
            or_replace_values,
        )


if __name__ == "__main__":
    unittest.main()
