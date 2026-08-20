from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_table_factor_loop import (
    AlterTableFactorCase,
    AlterTableFactorLoopError,
    AlterTableFactorLoopPlan,
    build_alter_table_factor_loop_plan,
    compile_alter_table_factor_loop_obligations,
)
from pg_case_factory.alter_table_regress import (
    load_alter_table_grammar_axes,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterTableRegressGrammarTest(unittest.TestCase):
    def test_grammar_axis_ledger_is_frozen(self) -> None:
        axes = load_alter_table_grammar_axes()
        self.assertEqual(4, len(axes))
        self.assertEqual(8, sum(len(axis.values) for axis in axes))


class AlterTableFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_table_factor_loop_obligations(ROOT)
        # GRM(8) + SFV(197) + RISK(2) = 207 ; INV is not applicable.
        self.assertEqual(207, len(rows))
        self.assertEqual(
            {"GRM": 8, "SFV": 197, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(207, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(0, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            207,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_alter_table_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(197, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(197, sum(seen.values()))
        self.assertEqual(197, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_alter_table_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 29 canonical values reach the PG target check and are rejected;
        # the remaining 168 SFV + 8 GRM + 2 RISK = 178 are covered.
        self.assertEqual(29, len(failures))
        self.assertEqual(178, covered)
        self.assertEqual(len(failures), len(set(failures)))


class AlterTableFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(self) -> None:
        plan = build_alter_table_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, AlterTableFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(207, len(plan.cases))
        self.assertEqual(
            list(range(1, 208)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual("ALTERTABLE00001", plan.cases[0].case_id)
        self.assertEqual("ALTERTABLE00207", plan.cases[-1].case_id)
        self.assertEqual("ALTERTABLE00001.sql", plan.cases[0].sql_filename)
        self.assertEqual("ALTERTABLE00207.sql", plan.cases[-1].sql_filename)
        self.assertEqual(
            "altertable_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            "altertable_00207_", plan.cases[-1].object_prefix
        )
        self.assertEqual(
            207, len({row.primary_obligation_id for row in plan.cases})
        )
        self.assertEqual(
            207, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(row.execution_profile == "serial_sql" for row in plan.cases)
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_alter_table_factor_loop_plan(ROOT)
        obligations = compile_alter_table_factor_loop_obligations(ROOT)
        by_id = {row.obligation_id: row for row in obligations}
        for case in plan.cases:
            obligation = by_id[case.primary_obligation_id]
            if obligation.disposition == "expected_failure":
                self.assertEqual("expected_failure", case.outcome)
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(case.expected_failure_reason)
            else:
                self.assertEqual("success", case.outcome)
                self.assertEqual("00000", case.expected_sqlstate)
                self.assertIsNone(case.expected_failure_reason)

    def test_baseline_has_one_primary_value_no_duplicates(self) -> None:
        plan = build_alter_table_factor_loop_plan(ROOT)
        for case in plan.cases:
            primary_seen = sum(
                1
                for key, _ in case.baseline_assignments
                if key == case.factor_key
            )
            self.assertEqual(1, primary_seen, case.sql_filename)
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )
            primary_value = next(
                value
                for key, value in case.baseline_assignments
                if key == case.factor_key
            )
            self.assertEqual(case.factor_value, primary_value)
            self.assertEqual(
                case.baseline_assignments,
                tuple(sorted(case.baseline_assignments)),
            )


if __name__ == "__main__":
    unittest.main()
