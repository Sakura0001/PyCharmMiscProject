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

    def test_runtime_calibrated_branch_expectations_are_fail_closed(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        storage_cases = [
            row
            for row in plan.cases
            if row.consumer_action_id == "set_storage"
            and (
                row.factor_key == "local:storage_mode"
                and row.factor_value in {"main", "extended", "external"}
                or row.factor_key == "storage_and_compression"
                and row.factor_value
                in {"storage_main", "storage_extended", "storage_external"}
            )
        ]
        self.assertEqual(6, len(storage_cases))
        self.assertTrue(
            all(
                (row.outcome, row.expected_sqlstate)
                == ("expected_failure", "0A000")
                for row in storage_cases
            )
        )

        missing_relation_values = {
            ("expected_status", "failure"),
            ("nonexistent_table", "table_missing_no_if_exists"),
            ("object_state", "not_exists"),
            ("table_name_shape", "nonexistent_name"),
            ("nonexistent_parent_table", "parent_missing"),
            ("parent_table_existence", "parent_not_exists"),
            ("parent_table_name_shape", "nonexistent_parent"),
        }
        missing_cases = [
            row
            for row in plan.cases
            if (row.factor_key, row.factor_value) in missing_relation_values
        ]
        self.assertEqual(len(missing_relation_values), len(missing_cases))
        self.assertTrue(
            all(row.expected_sqlstate == "42P01" for row in missing_cases)
        )

    def test_option_axes_use_a_legal_conditional_baseline(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        option_cases = [
            row
            for row in plan.cases
            if row.consumer_action_id in {"column_options", "options"}
        ]
        self.assertTrue(option_cases)
        for case in option_cases:
            with self.subTest(case_id=case.case_id):
                assignments = dict(case.baseline_assignments)
                action = assignments["local:option_action"]
                presence = assignments["local:option_value_presence"]
                if action == "drop":
                    self.assertEqual("omitted", presence)
                else:
                    self.assertEqual("present", presence)

    def test_case_plan_is_byte_stable_in_memory(self) -> None:
        first = build_alter_foreign_table_factor_loop_plan(ROOT)
        second = build_alter_foreign_table_factor_loop_plan(ROOT)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
