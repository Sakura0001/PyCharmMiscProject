from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.start_transaction_factor_loop import (
    StartTransactionFactorCase,
    StartTransactionFactorLoopError,
    StartTransactionFactorLoopPlan,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_start_transaction_factor_loop_plan,
    compile_start_transaction_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class StartTransactionFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_start_transaction_factor_loop_obligations(ROOT)
        # GRM(1) + SFV(43) = 44 ; START TRANSACTION has a single synopsis.
        self.assertEqual(44, len(rows))
        self.assertEqual(
            {"GRM": 1, "SFV": 43},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(44, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
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
        rows = compile_start_transaction_factor_loop_obligations(ROOT)
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
        rows = compile_start_transaction_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # START TRANSACTION: 7 canonical values reach the PG target check
        # and are rejected.  Unlike COMMIT, AND CHAIN is a SYNTAX ERROR
        # (42601) here (no AND CHAIN clause in the synopsis), and
        # inside_transaction / savepoint_exists warn 25001 ("there is
        # already a transaction in progress"); outside_transaction is the
        # success default (START begins a block).  The remaining 36 SFV
        # + 1 GRM = 37 are covered.
        self.assertEqual(7, len(failures))
        self.assertEqual(37, covered)
        self.assertEqual(len(failures), len(set(failures)))
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)

    def test_chain_behavior_values_are_failures_for_start_transaction(
        self,
    ) -> None:
        # START TRANSACTION has no AND [NO] CHAIN clause -> syntax error.
        self.assertIn(
            ("chain_behavior", "and_chain"), _SFV_FAILURE_VALUES
        )
        self.assertIn(
            ("chain_behavior", "and_no_chain"), _SFV_FAILURE_VALUES
        )
        sqlstate, _ = _SFV_FAILURE_SQLSTATE[
            ("chain_behavior", "and_chain")
        ]
        self.assertEqual("42601", sqlstate)

    def test_outside_transaction_is_success_for_start_transaction(
        self,
    ) -> None:
        # START TRANSACTION's normal success case is starting a block from
        # outside a transaction; inside_transaction warns 25001 instead.
        self.assertNotIn(
            ("transaction_state", "outside_transaction"),
            _SFV_FAILURE_VALUES,
        )
        self.assertIn(
            ("transaction_state", "inside_transaction"),
            _SFV_FAILURE_VALUES,
        )
        sqlstate, _ = _SFV_FAILURE_SQLSTATE[
            ("transaction_state", "inside_transaction")
        ]
        self.assertEqual("25001", sqlstate)


class StartTransactionFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_start_transaction_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, StartTransactionFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(44, len(plan.cases))
        self.assertEqual(
            list(range(1, 45)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual(
            "STARTTRANSACTION00001", plan.cases[0].case_id
        )
        self.assertEqual(
            "STARTTRANSACTION00044", plan.cases[-1].case_id
        )
        self.assertEqual(
            "STARTTRANSACTION00001.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            "STARTTRANSACTION00044.sql", plan.cases[-1].sql_filename
        )
        self.assertEqual(
            "starttransaction_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            "starttransaction_00044_", plan.cases[-1].object_prefix
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
        plan = build_start_transaction_factor_loop_plan(ROOT)
        obligations = (
            compile_start_transaction_factor_loop_obligations(ROOT)
        )
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
        plan = build_start_transaction_factor_loop_plan(ROOT)
        for case in plan.cases:
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )

    def test_plan_is_deterministic(self) -> None:
        plan = build_start_transaction_factor_loop_plan(ROOT)
        again = build_start_transaction_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_start_transaction_factor_loop_plan(ROOT)
        self.assertEqual(
            "6ef727241e2c92ae85dab69c1102901e907e0aa34c10f4788c28ebf96ea85e9a",
            plan.obligation_multiset_sha256,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_start_transaction_factor_loop_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(37, outcomes["success"])
        self.assertEqual(7, outcomes["expected_failure"])


if __name__ == "__main__":
    unittest.main()
