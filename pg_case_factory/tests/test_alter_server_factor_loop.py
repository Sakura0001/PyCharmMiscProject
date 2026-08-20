from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_server_factor_loop import (
    AlterServerFactorCase,
    AlterServerFactorLoopError,
    AlterServerFactorLoopPlan,
    _EXPECTED_BEHAVIOR_VALUES,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_alter_server_factor_loop_plan,
    compile_alter_server_factor_loop_obligations,
    load_alter_server_grammar_actions,
    load_alter_server_grammar_axes,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterServerRegressGrammarTest(unittest.TestCase):
    def test_grammar_action_and_axis_ledger_is_frozen(self) -> None:
        actions = load_alter_server_grammar_actions()
        axes = load_alter_server_grammar_axes()
        self.assertEqual(3, len(actions))
        self.assertEqual(0, len(axes))
        ids = {a.action_id for a in actions}
        self.assertEqual(
            {"rename", "owner", "version_options"}, ids
        )


class AlterServerFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_server_factor_loop_obligations(ROOT)
        # GRM(3) + SFV(48) + RISK(2) = 53 ; INV is not applicable.
        self.assertEqual(53, len(rows))
        self.assertEqual(
            {"GRM": 3, "SFV": 48, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(53, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(
            0, sum(row.disposition == "delegated" for row in rows)
        )
        self.assertEqual(
            53,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_alter_server_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(48, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(48, sum(seen.values()))
        self.assertEqual(48, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_alter_server_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 14 canonical values reach the PG target check and are rejected;
        # the remaining 34 SFV + 3 GRM + 2 RISK = 39 are covered.
        self.assertEqual(14, len(failures))
        self.assertEqual(39, covered)
        self.assertEqual(len(failures), len(set(failures)))
        # ALTER SERVER has no membership-wall escape: the keyword
        # owner-transfers are normal permitted transfers, never failures.
        self.assertNotIn(
            ("owner_to_shape", "session_user_keyword"), failures
        )
        self.assertNotIn(
            ("owner_to_shape", "current_role_keyword"), failures
        )
        # Every failure value has a provisional SQLSTATE.
        for pair in failures:
            self.assertIn(pair, _SFV_FAILURE_SQLSTATE)

    def test_expected_behavior_set_is_frozen_empty(self) -> None:
        # ALTER SERVER has no membership-wall escape special case.
        self.assertEqual(0, len(_EXPECTED_BEHAVIOR_VALUES))


class AlterServerFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(
        self,
    ) -> None:
        plan = build_alter_server_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, AlterServerFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(53, len(plan.cases))
        self.assertEqual(
            list(range(1, 54)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual("ALTERSERVER00001", plan.cases[0].case_id)
        self.assertEqual("ALTERSERVER00053", plan.cases[-1].case_id)
        self.assertEqual(
            "ALTERSERVER00001.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            "ALTERSERVER00053.sql", plan.cases[-1].sql_filename
        )
        self.assertEqual(
            "alterserver_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            "alterserver_00053_", plan.cases[-1].object_prefix
        )
        self.assertEqual(
            53, len({row.primary_obligation_id for row in plan.cases})
        )
        self.assertEqual(53, len({row.sql_filename for row in plan.cases}))
        self.assertTrue(
            all(row.execution_profile == "serial_sql" for row in plan.cases)
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_alter_server_factor_loop_plan(ROOT)
        obligations = compile_alter_server_factor_loop_obligations(ROOT)
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
        plan = build_alter_server_factor_loop_plan(ROOT)
        for case in plan.cases:
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(
                len(keys), len(set(keys)), case.sql_filename
            )
            self.assertEqual(
                case.baseline_assignments,
                tuple(sorted(case.baseline_assignments)),
            )

    def test_plan_is_deterministic(self) -> None:
        plan = build_alter_server_factor_loop_plan(ROOT)
        again = build_alter_server_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )


if __name__ == "__main__":
    unittest.main()
