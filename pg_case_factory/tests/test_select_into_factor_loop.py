from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.select_into_factor_loop import (
    SelectIntoFactorCase,
    SelectIntoFactorLoopError,
    SelectIntoFactorLoopPlan,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_select_into_factor_loop_plan,
    compile_select_into_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class SelectIntoFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_select_into_factor_loop_obligations(ROOT)
        # GRM(1) + SFV(56) = 57 ; SELECT INTO has a single synopsis.
        self.assertEqual(57, len(rows))
        self.assertEqual(
            {"GRM": 1, "SFV": 56},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(
            57, len({row.obligation_id for row in rows})
        )
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(
            0, sum(row.disposition == "delegated" for row in rows)
        )
        self.assertEqual(
            57,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(
            all(row.disposition in allowed for row in rows)
        )

    def test_canonical_obligation_count_matches_inventory(
        self,
    ) -> None:
        rows = compile_select_into_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(56, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(56, sum(seen.values()))
        self.assertEqual(56, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_select_into_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(
            row.disposition == "covered" for row in rows
        )
        # SELECT INTO: 10 canonical values reach the PG target check
        # and are rejected; the remaining 46 SFV + 1 GRM = 47 covered.
        self.assertEqual(10, len(failures))
        self.assertEqual(47, covered)
        self.assertEqual(len(failures), len(set(failures)))
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)

    def test_no_if_not_exists_failure_is_duplicate_table(self) -> None:
        # SELECT INTO has no IF NOT EXISTS, so duplicate_table_name is a
        # 42P07 failure.
        self.assertIn(
            ("duplicate_table_name", "without_if_not_exists_error"),
            _SFV_FAILURE_VALUES,
        )
        sqlstate, _ = _SFV_FAILURE_SQLSTATE[
            ("duplicate_table_name", "without_if_not_exists_error")
        ]
        self.assertEqual("42P07", sqlstate)

    def test_object_state_already_exists_is_failure(self) -> None:
        self.assertIn(
            ("object_state", "already_exists"), _SFV_FAILURE_VALUES
        )
        sqlstate, _ = _SFV_FAILURE_SQLSTATE[
            ("object_state", "already_exists")
        ]
        self.assertEqual("42P07", sqlstate)


class SelectIntoFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_select_into_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, SelectIntoFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(57, len(plan.cases))
        self.assertEqual(
            list(range(1, 58)),
            [row.ordinal for row in plan.cases],
        )
        self.assertEqual(
            "SELECTINTO00001", plan.cases[0].case_id
        )
        self.assertEqual(
            "SELECTINTO00057", plan.cases[-1].case_id
        )
        self.assertEqual(
            "SELECTINTO00001.sql",
            plan.cases[0].sql_filename,
        )
        self.assertEqual(
            "SELECTINTO00057.sql",
            plan.cases[-1].sql_filename,
        )
        self.assertEqual(
            "selectinto_00001_",
            plan.cases[0].object_prefix,
        )
        self.assertEqual(
            "selectinto_00057_",
            plan.cases[-1].object_prefix,
        )
        self.assertEqual(
            57,
            len(
                {
                    row.primary_obligation_id
                    for row in plan.cases
                }
            ),
        )
        self.assertEqual(
            57,
            len({row.sql_filename for row in plan.cases}),
        )
        self.assertTrue(
            all(
                row.execution_profile == "serial_sql"
                for row in plan.cases
            )
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_select_into_factor_loop_plan(ROOT)
        obligations = (
            compile_select_into_factor_loop_obligations(ROOT)
        )
        by_id = {row.obligation_id: row for row in obligations}
        for case in plan.cases:
            obligation = by_id[case.primary_obligation_id]
            if obligation.disposition == "expected_failure":
                self.assertEqual(
                    "expected_failure", case.outcome
                )
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(
                    case.expected_failure_reason
                )
            else:
                self.assertEqual("success", case.outcome)
                self.assertEqual("00000", case.expected_sqlstate)
                self.assertIsNone(case.expected_failure_reason)

    def test_baseline_has_one_primary_value_no_duplicates(
        self,
    ) -> None:
        plan = build_select_into_factor_loop_plan(ROOT)
        for case in plan.cases:
            assignment = dict(case.baseline_assignments)
            keys = list(assignment)
            self.assertEqual(
                len(keys), len(set(keys)), case.case_id
            )


if __name__ == "__main__":
    unittest.main()
