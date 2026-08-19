from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_procedure_factor_loop import (
    AlterProcedureFactorLoopError,
    AlterProcedureFactorCase,
    AlterProcedureFactorLoopPlan,
    build_alter_procedure_factor_loop_plan,
    compile_alter_procedure_factor_loop_obligations,
)
from pg_case_factory.alter_procedure_regress import (
    load_alter_procedure_grammar_actions,
    load_alter_procedure_grammar_axes,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterProcedureRegressGrammarTest(unittest.TestCase):
    def test_grammar_action_and_axis_ledger_is_frozen(self) -> None:
        actions = load_alter_procedure_grammar_actions()
        axes = load_alter_procedure_grammar_axes()
        self.assertEqual(9, len(actions))
        self.assertEqual(6, len(axes))
        self.assertEqual(13, sum(len(axis.values) for axis in axes))
        action_ids = {action.action_id for action in actions}
        for axis in axes:
            if not axis.action_id.startswith("__outer_"):
                self.assertIn(axis.action_id, action_ids)


class AlterProcedureFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_procedure_factor_loop_obligations(ROOT)
        # GRM(22) + SFV(70) + RISK(2) = 94 ; INV is not applicable.
        self.assertEqual(94, len(rows))
        self.assertEqual(
            {"GRM": 22, "SFV": 70, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(94, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(0, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            94,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_alter_procedure_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(70, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(70, sum(seen.values()))
        self.assertEqual(70, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_alter_procedure_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 24 canonical values reach the PG target check and are rejected;
        # the remaining 46 SFV + 22 GRM + 2 RISK = 70 are covered.
        self.assertEqual(24, len(failures))
        self.assertEqual(70, covered)
        self.assertEqual(len(failures), len(set(failures)))
        self.assertNotIn(("argtype_specification", "without_signature"), failures)
        self.assertNotIn(("identifier_length_exceeded", "over_63_chars"), failures)


class AlterProcedureFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(self) -> None:
        plan = build_alter_procedure_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, AlterProcedureFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(94, len(plan.cases))
        self.assertEqual(
            list(range(1, 95)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual("ALTERPROCEDURE00001", plan.cases[0].case_id)
        self.assertEqual("ALTERPROCEDURE00094", plan.cases[-1].case_id)
        self.assertEqual("ALTERPROCEDURE00001.sql", plan.cases[0].sql_filename)
        self.assertEqual("ALTERPROCEDURE00094.sql", plan.cases[-1].sql_filename)
        self.assertEqual(
            "alterprocedure_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            "alterprocedure_00094_", plan.cases[-1].object_prefix
        )
        self.assertEqual(
            94, len({row.primary_obligation_id for row in plan.cases})
        )
        self.assertEqual(
            94, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(row.execution_profile == "serial_sql" for row in plan.cases)
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_alter_procedure_factor_loop_plan(ROOT)
        obligations = compile_alter_procedure_factor_loop_obligations(ROOT)
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
        plan = build_alter_procedure_factor_loop_plan(ROOT)
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
