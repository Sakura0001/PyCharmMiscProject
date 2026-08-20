from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.comment_factor_loop import (
    CommentFactorCase,
    CommentFactorLoopError,
    CommentFactorLoopPlan,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_comment_factor_loop_plan,
    compile_comment_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class CommentFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_comment_factor_loop_obligations(ROOT)
        # All 117 obligations are SFV (object_type is both the
        # grammar branch AND a T1 factor in the TSV, so no GRM).
        self.assertEqual(117, len(rows))
        self.assertEqual(
            {"SFV": 117},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(117, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(
            0, sum(row.disposition == "delegated" for row in rows)
        )
        self.assertEqual(
            117,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_comment_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(117, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            key = (row.factor_key, row.value)
            seen[key] = seen.get(key, 0) + 1
        self.assertEqual(117, sum(seen.values()))
        self.assertEqual(117, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_comment_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 17 canonical values reach the PG target check and are rejected;
        # the remaining 100 SFV are covered.
        self.assertEqual(17, len(failures))
        self.assertEqual(100, covered)
        self.assertEqual(len(failures), len(set(failures)))
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)


class CommentFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_comment_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, CommentFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(117, len(plan.cases))
        self.assertEqual(
            list(range(1, 118)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual("COMMENT00001", plan.cases[0].case_id)
        self.assertEqual("COMMENT00117", plan.cases[-1].case_id)
        self.assertEqual(
            "COMMENT00001.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            "COMMENT00117.sql", plan.cases[-1].sql_filename
        )
        self.assertEqual(
            "comment_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            "comment_00117_", plan.cases[-1].object_prefix
        )
        self.assertEqual(
            117,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(
            117, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(
                row.execution_profile == "serial_sql"
                for row in plan.cases
            )
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_comment_factor_loop_plan(ROOT)
        obligations = compile_comment_factor_loop_obligations(ROOT)
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
        plan = build_comment_factor_loop_plan(ROOT)
        for case in plan.cases:
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )

    def test_plan_is_deterministic(self) -> None:
        plan = build_comment_factor_loop_plan(ROOT)
        again = build_comment_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_comment_factor_loop_plan(ROOT)
        self.assertEqual(
            "429e2a9254f3d93129de50be91f61eee3963cf944ab4679f45f2e1eb4f936c67",
            plan.obligation_multiset_sha256,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_comment_factor_loop_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(100, outcomes["success"])
        self.assertEqual(17, outcomes["expected_failure"])


if __name__ == "__main__":
    unittest.main()
