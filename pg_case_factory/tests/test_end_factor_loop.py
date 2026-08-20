from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.end_factor_loop import (
    EndFactorCase,
    EndFactorLoopError,
    EndFactorLoopPlan,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_end_factor_loop_plan,
    compile_end_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class EndFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_end_factor_loop_obligations(ROOT)
        # GRM(1) + SFV(43) = 44 ; END has a single synopsis branch.
        self.assertEqual(44, len(rows))
        self.assertEqual(
            {"GRM": 1, "SFV": 43},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(44, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(0, sum(row.kind == "RISK" for row in rows))
        self.assertEqual(
            0, sum(row.disposition == "delegated" for row in rows)
        )
        self.assertEqual(
            44,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_end_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(43, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(43, sum(seen.values()))
        self.assertEqual(43, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_end_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # END (COMMIT synonym): 6 canonical values reach the PG target check
        # and are rejected (and_chain / and_no_chain are VALID for END, so
        # they are NOT failures here; outside_transaction IS a failure
        # 25P01); the remaining 37 SFV + 1 GRM = 38 are covered.
        self.assertEqual(6, len(failures))
        self.assertEqual(38, covered)
        self.assertEqual(len(failures), len(set(failures)))
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)

    def test_chain_behavior_values_are_success_for_end(self) -> None:
        # END supports AND [NO] CHAIN -- these are success, not failure.
        self.assertNotIn(
            ("chain_behavior", "and_chain"), _SFV_FAILURE_VALUES
        )
        self.assertNotIn(
            ("chain_behavior", "and_no_chain"), _SFV_FAILURE_VALUES
        )

    def test_outside_transaction_is_failure_for_end(self) -> None:
        # END outside an active transaction warns 25P01.
        self.assertIn(
            ("transaction_state", "outside_transaction"),
            _SFV_FAILURE_VALUES,
        )
        sqlstate, _ = _SFV_FAILURE_SQLSTATE[
            ("transaction_state", "outside_transaction")
        ]
        self.assertEqual("25P01", sqlstate)


class EndFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_end_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, EndFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(44, len(plan.cases))
        self.assertEqual(
            list(range(1, 45)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual("END00001", plan.cases[0].case_id)
        self.assertEqual("END00044", plan.cases[-1].case_id)
        self.assertEqual(
            "END00001.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            "END00044.sql", plan.cases[-1].sql_filename
        )
        self.assertEqual(
            "end_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            "end_00044_", plan.cases[-1].object_prefix
        )
        self.assertEqual(
            44,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(
            44, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(
                row.execution_profile == "serial_sql"
                for row in plan.cases
            )
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_end_factor_loop_plan(ROOT)
        obligations = compile_end_factor_loop_obligations(ROOT)
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
        plan = build_end_factor_loop_plan(ROOT)
        for case in plan.cases:
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )

    def test_plan_is_deterministic(self) -> None:
        plan = build_end_factor_loop_plan(ROOT)
        again = build_end_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_end_factor_loop_plan(ROOT)
        self.assertEqual(
            "9d5c9d17662dc5166ad2d081293bed22f638d1f386755c762b9d1a7f47488ac8",
            plan.obligation_multiset_sha256,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_end_factor_loop_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(38, outcomes["success"])
        self.assertEqual(6, outcomes["expected_failure"])


if __name__ == "__main__":
    unittest.main()
