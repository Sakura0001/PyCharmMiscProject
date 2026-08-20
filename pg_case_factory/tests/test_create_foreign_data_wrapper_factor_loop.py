from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.create_foreign_data_wrapper_factor_loop import (
    CreateForeignDataWrapperFactorCase,
    CreateForeignDataWrapperFactorLoopError,
    CreateForeignDataWrapperFactorLoopPlan,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_create_foreign_data_wrapper_factor_loop_plan,
    compile_create_foreign_data_wrapper_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateForeignDataWrapperFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = (
            compile_create_foreign_data_wrapper_factor_loop_obligations(
                ROOT
            )
        )
        # GRM(1) + SFV(57) = 58 ; no INV (CREATE FOREIGN DATA
        # WRAPPER registers in pg_foreign_data_wrapper, not pg_class).
        self.assertEqual(58, len(rows))
        self.assertEqual(
            {"GRM": 1, "SFV": 57},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(58, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(
            0, sum(row.disposition == "delegated" for row in rows)
        )
        self.assertEqual(
            58,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(
            all(row.disposition in allowed for row in rows)
        )

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = (
            compile_create_foreign_data_wrapper_factor_loop_obligations(
                ROOT
            )
        )
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(57, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(57, sum(seen.values()))
        self.assertEqual(57, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = (
            compile_create_foreign_data_wrapper_factor_loop_obligations(
                ROOT
            )
        )
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 17 canonical values reach the PG target check and are
        # rejected; the remaining 40 SFV + 1 GRM = 41 are covered.
        self.assertEqual(17, len(failures))
        self.assertEqual(41, covered)
        self.assertEqual(len(failures), len(set(failures)))
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)


class CreateForeignDataWrapperFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_create_foreign_data_wrapper_factor_loop_plan(ROOT)
        self.assertIsInstance(
            plan, CreateForeignDataWrapperFactorLoopPlan
        )
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(58, len(plan.cases))
        self.assertEqual(
            list(range(1, 59)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual(
            "CREATEFOREIGNDATAWRAPPER00001", plan.cases[0].case_id
        )
        self.assertEqual(
            "CREATEFOREIGNDATAWRAPPER00058", plan.cases[-1].case_id
        )
        self.assertEqual(
            "CREATEFOREIGNDATAWRAPPER00001.sql",
            plan.cases[0].sql_filename,
        )
        self.assertEqual(
            "CREATEFOREIGNDATAWRAPPER00058.sql",
            plan.cases[-1].sql_filename,
        )
        self.assertEqual(
            "createforeigndatawrapper_00001_",
            plan.cases[0].object_prefix,
        )
        self.assertEqual(
            "createforeigndatawrapper_00058_",
            plan.cases[-1].object_prefix,
        )
        self.assertEqual(
            58,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(
            58, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(
                row.execution_profile == "serial_sql"
                for row in plan.cases
            )
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_create_foreign_data_wrapper_factor_loop_plan(ROOT)
        obligations = (
            compile_create_foreign_data_wrapper_factor_loop_obligations(
                ROOT
            )
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
        plan = build_create_foreign_data_wrapper_factor_loop_plan(ROOT)
        for case in plan.cases:
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )

    def test_plan_is_deterministic(self) -> None:
        plan = build_create_foreign_data_wrapper_factor_loop_plan(ROOT)
        again = build_create_foreign_data_wrapper_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_create_foreign_data_wrapper_factor_loop_plan(ROOT)
        self.assertEqual(
            "da8ad32f1136312b25b45a3e2ffa56aa6e81d3a7b70c801d11dc747aa555ae55",
            plan.obligation_multiset_sha256,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_create_foreign_data_wrapper_factor_loop_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(41, outcomes["success"])
        self.assertEqual(17, outcomes["expected_failure"])


if __name__ == "__main__":
    unittest.main()
