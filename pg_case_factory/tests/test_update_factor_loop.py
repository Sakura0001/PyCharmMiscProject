from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.update_factor_loop import (
    UpdateFactorCase,
    UpdateFactorLoopError,
    UpdateFactorLoopPlan,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_update_factor_loop_plan,
    compile_update_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class UpdateFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_update_factor_loop_obligations(ROOT)
        # GRM(1) + SFV(49) = 50 ; RISK is not applicable.
        self.assertEqual(50, len(rows))
        self.assertEqual(
            {"GRM": 1, "SFV": 49},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(50, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(
            0, sum(row.disposition == "delegated" for row in rows)
        )
        self.assertEqual(
            50,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_matrix(self) -> None:
        rows = compile_update_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(49, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(49, sum(seen.values()))
        self.assertEqual(49, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_update_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 8 canonical values reach the PG target check and are rejected;
        # the remaining 41 SFV + 1 GRM = 42 are covered.
        self.assertEqual(8, len(failures))
        self.assertEqual(42, covered)
        self.assertEqual(len(failures), len(set(failures)))
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)


class UpdateFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_update_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, UpdateFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(50, len(plan.cases))
        self.assertEqual(
            list(range(1, 51)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual("UPDATE00001", plan.cases[0].case_id)
        self.assertEqual("UPDATE00050", plan.cases[-1].case_id)
        self.assertEqual(
            "UPDATE00001.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            "UPDATE00050.sql", plan.cases[-1].sql_filename
        )
        self.assertEqual(
            "update_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            "update_00050_", plan.cases[-1].object_prefix
        )
        self.assertEqual(
            50,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(
            50, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(
                row.execution_profile == "serial_sql"
                for row in plan.cases
            )
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_update_factor_loop_plan(ROOT)
        obligations = compile_update_factor_loop_obligations(ROOT)
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
        plan = build_update_factor_loop_plan(ROOT)
        for case in plan.cases:
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )

    def test_plan_is_deterministic(self) -> None:
        plan = build_update_factor_loop_plan(ROOT)
        again = build_update_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_update_factor_loop_plan(ROOT)
        self.assertEqual(
            "24ad36386d12bff8c5438458f4867c40816799db8db8774a08e170e3dbe390bf",
            plan.obligation_multiset_sha256,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_update_factor_loop_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(42, outcomes["success"])
        self.assertEqual(8, outcomes["expected_failure"])

    def test_factor_value_count_is_frozen(self) -> None:
        plan = build_update_factor_loop_plan(ROOT)
        pairs: set[tuple[str, str]] = set()
        for case in plan.cases:
            for factor, value in case.baseline_assignments:
                if factor == "target_action":
                    continue
                pairs.add((factor, value))
        # 49 canonical factor values across all 15 factors
        # (sum of len(values) per factor; target_action is synthetic).
        self.assertEqual(49, len(pairs))


if __name__ == "__main__":
    unittest.main()
