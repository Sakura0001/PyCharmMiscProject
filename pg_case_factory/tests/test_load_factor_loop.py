from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.load_factor_loop import (
    LoadFactorCase,
    LoadFactorLoopError,
    LoadFactorLoopPlan,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_load_factor_loop_plan,
    compile_load_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class LoadFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_load_factor_loop_obligations(ROOT)
        # GRM(1) + SFV(45) = 46 ; RISK is not applicable.
        self.assertEqual(46, len(rows))
        self.assertEqual(
            {"GRM": 1, "SFV": 45},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(46, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(
            0, sum(row.disposition == "delegated" for row in rows)
        )
        self.assertEqual(
            46,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_load_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(45, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(45, sum(seen.values()))
        self.assertEqual(45, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_load_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 7 canonical values reach the PG target check and are rejected;
        # the remaining 38 SFV + 1 GRM = 39 are covered.
        self.assertEqual(7, len(failures))
        self.assertEqual(39, covered)
        self.assertEqual(len(failures), len(set(failures)))
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)

    def test_failure_values_are_derived_from_matrix(self) -> None:
        self.assertEqual(
            7, len(_SFV_FAILURE_VALUES)
        )
        expected_pairs = {
            ("expected_status", "failure"),
            ("privilege_context", "insufficient_privilege"),
            ("resource_boundary", "missing_file_or_library"),
            ("target_state", "target_missing"),
            ("target_state", "wrong_object_type"),
            ("invalid_combination", "object_type_mismatch"),
            ("invalid_combination", "syntax_valid_semantic_error"),
        }
        self.assertEqual(expected_pairs, set(_SFV_FAILURE_VALUES))


class LoadFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_load_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, LoadFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(46, len(plan.cases))
        self.assertEqual(
            list(range(1, 47)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual(
            "LOAD00001", plan.cases[0].case_id
        )
        self.assertEqual(
            "LOAD00046", plan.cases[-1].case_id
        )
        self.assertEqual(
            "LOAD00001.sql",
            plan.cases[0].sql_filename,
        )
        self.assertEqual(
            "LOAD00046.sql",
            plan.cases[-1].sql_filename,
        )
        self.assertEqual(
            "load_00001_",
            plan.cases[0].object_prefix,
        )
        self.assertEqual(
            "load_00046_",
            plan.cases[-1].object_prefix,
        )
        self.assertEqual(
            46,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(
            46, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(
                row.execution_profile == "serial_sql"
                for row in plan.cases
            )
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_load_factor_loop_plan(ROOT)
        obligations = compile_load_factor_loop_obligations(
            ROOT
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
        plan = build_load_factor_loop_plan(ROOT)
        for case in plan.cases:
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )

    def test_plan_is_deterministic(self) -> None:
        plan = build_load_factor_loop_plan(ROOT)
        again = build_load_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_load_factor_loop_plan(ROOT)
        self.assertEqual(
            "8a61a43a1b49ac9d7b2c8ce61d40fa84e52819efae8aeecaf3d1049b482ae863",
            plan.obligation_multiset_sha256,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_load_factor_loop_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(39, outcomes["success"])
        self.assertEqual(7, outcomes["expected_failure"])


if __name__ == "__main__":
    unittest.main()
