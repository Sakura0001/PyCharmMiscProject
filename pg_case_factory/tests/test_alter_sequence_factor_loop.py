from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_sequence_factor_loop import (
    AlterSequenceFactorLoopError,
    AlterSequenceFactorCase,
    AlterSequenceFactorLoopPlan,
    build_alter_sequence_factor_loop_plan,
    compile_alter_sequence_factor_loop_obligations,
)
from pg_case_factory.alter_sequence_regress import (
    load_alter_sequence_grammar_axes,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterSequenceRegressGrammarTest(unittest.TestCase):
    def test_grammar_axis_ledger_is_frozen(self) -> None:
        axes = load_alter_sequence_grammar_axes()
        self.assertEqual(4, len(axes))
        self.assertEqual(8, sum(len(axis.values) for axis in axes))


class AlterSequenceFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_sequence_factor_loop_obligations(ROOT)
        # GRM(8) + SFV(69) + RISK(2) = 79 ; INV is not applicable.
        self.assertEqual(79, len(rows))
        self.assertEqual(
            {"GRM": 8, "SFV": 69, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(79, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(0, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            79,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_alter_sequence_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(69, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(69, sum(seen.values()))
        self.assertEqual(69, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_alter_sequence_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 14 canonical values reach the PG target check and are rejected;
        # the remaining 55 SFV + 8 GRM + 2 RISK = 65 are covered.
        self.assertEqual(14, len(failures))
        self.assertEqual(65, covered)
        self.assertEqual(len(failures), len(set(failures)))


class AlterSequenceFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(self) -> None:
        plan = build_alter_sequence_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, AlterSequenceFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(79, len(plan.cases))
        self.assertEqual(
            list(range(1, 80)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual("ALTERSEQUENCE00001", plan.cases[0].case_id)
        self.assertEqual("ALTERSEQUENCE00079", plan.cases[-1].case_id)
        self.assertEqual("ALTERSEQUENCE00001.sql", plan.cases[0].sql_filename)
        self.assertEqual("ALTERSEQUENCE00079.sql", plan.cases[-1].sql_filename)
        self.assertEqual(
            "altersequence_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            "altersequence_00079_", plan.cases[-1].object_prefix
        )
        self.assertEqual(
            79, len({row.primary_obligation_id for row in plan.cases})
        )
        self.assertEqual(
            79, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(row.execution_profile == "serial_sql" for row in plan.cases)
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_alter_sequence_factor_loop_plan(ROOT)
        obligations = compile_alter_sequence_factor_loop_obligations(ROOT)
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
        plan = build_alter_sequence_factor_loop_plan(ROOT)
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
