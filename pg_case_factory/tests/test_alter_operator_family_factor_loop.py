"""Frozen-spec tests for the ALTER OPERATOR FAMILY factor-loop obligation ledger."""

from __future__ import annotations

from collections import Counter
import unittest
from pathlib import Path

from pg_case_factory.alter_operator_family_factor_loop import (
    AlterOperatorFamilyFactorLoopError,
    build_alter_operator_family_factor_loop_plan,
    compile_alter_operator_family_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]

_EXPECTED_OBLIGATION_MULTISETS_SHA256 = (
    "5c336c12ebc3c544db9ddbb7f3f085ed9c60528db3eba0478b1003d78d2074a6"
)


class AlterOperatorFamilyFactorLoopPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_operator_family_factor_loop_plan(ROOT)

    def test_obligation_count_is_frozen(self) -> None:
        self.assertEqual(len(self.plan.obligations), 59)

    def test_case_count_is_frozen(self) -> None:
        self.assertEqual(len(self.plan.cases), 59)

    def test_no_delegated_obligations(self) -> None:
        self.assertEqual(len(self.plan.delegated), 0)

    def test_kind_counts_are_frozen(self) -> None:
        self.assertEqual(
            Counter(obligation.kind for obligation in self.plan.obligations),
            {"GRM": 5, "SFV": 52, "RISK": 2},
        )

    def test_outcome_counts_are_frozen(self) -> None:
        self.assertEqual(
            Counter(case.outcome for case in self.plan.cases),
            {"success": 48, "expected_failure": 11},
        )

    def test_obligation_multiset_sha256_is_frozen(self) -> None:
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            _EXPECTED_OBLIGATION_MULTISETS_SHA256,
        )

    def test_each_case_has_unique_sql_filename(self) -> None:
        filenames = [case.sql_filename for case in self.plan.cases]
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_each_case_has_unique_primary_obligation(self) -> None:
        ids = [case.primary_obligation_id for case in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_sfv_obligation_ids_embed_matrix_row_id(self) -> None:
        sfv = [o for o in self.plan.obligations if o.kind == "SFV"]
        self.assertEqual(len(sfv), 52)
        for obligation in sfv:
            self.assertTrue(obligation.obligation_id.startswith("AOF-SFV|"))
            self.assertIn("|", obligation.obligation_id)

    def test_compiled_obligations_match_plan(self) -> None:
        obligations = compile_alter_operator_family_factor_loop_obligations(ROOT)
        self.assertEqual(
            tuple(o.obligation_id for o in obligations),
            tuple(o.obligation_id for o in self.plan.obligations),
        )

    def test_build_does_not_raise_on_frozen_matrix(self) -> None:
        plan = build_alter_operator_family_factor_loop_plan(ROOT)
        self.assertEqual(len(plan.cases), 59)


class AlterOperatorFamilyFactorLoopRebuildTests(unittest.TestCase):
    def test_plan_is_reproducible(self) -> None:
        plan_a = build_alter_operator_family_factor_loop_plan(ROOT)
        plan_b = build_alter_operator_family_factor_loop_plan(ROOT)
        self.assertEqual(
            plan_a.obligation_multiset_sha256,
            plan_b.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan_a.cases),
            tuple(c.case_id for c in plan_b.cases),
        )


if __name__ == "__main__":
    unittest.main()
