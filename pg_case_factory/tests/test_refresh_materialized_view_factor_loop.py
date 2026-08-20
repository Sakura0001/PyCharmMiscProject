from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.refresh_materialized_view_factor_loop import (
    RefreshMaterializedViewFactorCase,
    RefreshMaterializedViewFactorLoopError,
    RefreshMaterializedViewFactorLoopPlan,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_refresh_materialized_view_factor_loop_plan,
    compile_refresh_materialized_view_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class RefreshMaterializedViewFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_refresh_materialized_view_factor_loop_obligations(
            ROOT
        )
        # REFRESH MATERIALIZED VIEW has a single syntax branch
        # (statement_branch=branch_1).  All 38 declared factor values are
        # SFV obligations (0 GRM, 0 INV, 0 RISK).
        self.assertEqual(38, len(rows))
        self.assertEqual(
            {"SFV": 38},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(
            38, len({row.obligation_id for row in rows})
        )
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(
            0, sum(row.disposition == "delegated" for row in rows)
        )
        self.assertEqual(
            38,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_refresh_materialized_view_factor_loop_obligations(
            ROOT
        )
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(38, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(38, sum(seen.values()))
        self.assertEqual(38, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_refresh_materialized_view_factor_loop_obligations(
            ROOT
        )
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 11 canonical values reach the PG target check and are rejected;
        # the remaining 27 SFV are covered.
        self.assertEqual(11, len(failures))
        self.assertEqual(27, covered)
        self.assertEqual(len(failures), len(set(failures)))
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)


class RefreshMaterializedViewFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_refresh_materialized_view_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, RefreshMaterializedViewFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(38, len(plan.cases))
        self.assertEqual(
            list(range(1, 39)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual(
            "REFRESHMATERIALIZEDVIEW000001", plan.cases[0].case_id
        )
        self.assertEqual(
            "REFRESHMATERIALIZEDVIEW000038", plan.cases[-1].case_id
        )
        self.assertEqual(
            "REFRESHMATERIALIZEDVIEW000001.sql",
            plan.cases[0].sql_filename,
        )
        self.assertEqual(
            "REFRESHMATERIALIZEDVIEW000038.sql",
            plan.cases[-1].sql_filename,
        )
        self.assertEqual(
            "refreshmaterializedview_000001_",
            plan.cases[0].object_prefix,
        )
        self.assertEqual(
            "refreshmaterializedview_000038_",
            plan.cases[-1].object_prefix,
        )
        self.assertEqual(
            38,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(
            38, len({row.sql_filename for row in plan.cases})
        )
        self.assertTrue(
            all(
                row.execution_profile == "serial_sql"
                for row in plan.cases
            )
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_refresh_materialized_view_factor_loop_plan(ROOT)
        obligations = (
            compile_refresh_materialized_view_factor_loop_obligations(ROOT)
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
        plan = build_refresh_materialized_view_factor_loop_plan(ROOT)
        for case in plan.cases:
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )

    def test_plan_is_deterministic(self) -> None:
        plan = build_refresh_materialized_view_factor_loop_plan(ROOT)
        again = build_refresh_materialized_view_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_refresh_materialized_view_factor_loop_plan(ROOT)
        self.assertEqual(
            "603a8c2f81f501f68078b27514e3e859ec4217ae0f9a81b01f11a9119beb8a3d",
            plan.obligation_multiset_sha256,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_refresh_materialized_view_factor_loop_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(27, outcomes["success"])
        self.assertEqual(11, outcomes["expected_failure"])


if __name__ == "__main__":
    unittest.main()
