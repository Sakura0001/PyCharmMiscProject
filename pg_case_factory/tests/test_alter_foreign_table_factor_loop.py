from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_foreign_table_factor_loop import (
    build_alter_foreign_table_factor_loop_plan,
    compile_alter_foreign_table_factor_loop_obligations,
)


ROOT = Path(__file__).resolve().parents[1]


class AlterForeignTableFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_foreign_table_factor_loop_obligations(ROOT)
        self.assertEqual(1_817, len(rows))
        self.assertEqual(
            {"GRM": 136, "SFV": 103, "INV": 1_576, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(1_817, len({row.obligation_id for row in rows}))
        self.assertEqual(12, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            1_805,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )

    def test_builds_one_stable_program_per_local_obligation(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        self.assertEqual(1_805, len(plan.cases))
        self.assertEqual(12, len(plan.delegated))
        self.assertEqual(
            tuple(range(1, 1_806)),
            tuple(row.ordinal for row in plan.cases),
        )
        self.assertEqual(
            1_805,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(1_805, len({row.sql_filename for row in plan.cases}))
        self.assertEqual("ALTERFOREIGNTABLE0001.sql", plan.cases[0].sql_filename)
        self.assertEqual("alterforeigntable_0001_", plan.cases[0].object_prefix)
        self.assertEqual("ALTERFOREIGNTABLE1805.sql", plan.cases[-1].sql_filename)
        expected = {
            row.obligation_id
            for row in plan.obligations
            if row.disposition in {"covered", "expected_failure"}
        }
        self.assertEqual(
            expected,
            {row.primary_obligation_id for row in plan.cases},
        )

    def test_failure_disposition_drives_case_outcome(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        cases = {row.primary_obligation_id: row for row in plan.cases}
        for obligation in plan.obligations:
            with self.subTest(obligation_id=obligation.obligation_id):
                if obligation.disposition == "delegated":
                    self.assertNotIn(obligation.obligation_id, cases)
                    continue
                case = cases[obligation.obligation_id]
                if obligation.disposition == "expected_failure":
                    self.assertEqual("expected_failure", case.outcome)
                    self.assertRegex(case.expected_sqlstate, r"^[0-9A-Z]{5}$")
                    self.assertNotEqual("00000", case.expected_sqlstate)
                    self.assertTrue(case.expected_failure_reason)
                else:
                    self.assertEqual(
                        ("success", "00000", None),
                        (
                            case.outcome,
                            case.expected_sqlstate,
                            case.expected_failure_reason,
                        ),
                    )

    def test_each_case_has_one_primary_factor_value_and_unique_baselines(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                assignments = dict(case.baseline_assignments)
                self.assertEqual(len(assignments), len(case.baseline_assignments))
                self.assertIn(case.factor_key, assignments)
                self.assertEqual(case.factor_value, assignments[case.factor_key])

    def test_case_plan_is_byte_stable_in_memory(self) -> None:
        first = build_alter_foreign_table_factor_loop_plan(ROOT)
        second = build_alter_foreign_table_factor_loop_plan(ROOT)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
