from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_group_factor_loop import (
    AlterGroupFactorLoopError,
    AlterGroupFactorCase,
    AlterGroupFactorLoopPlan,
    build_alter_group_factor_loop_plan,
    compile_alter_group_factor_loop_obligations,
)


ROOT = Path(__file__).resolve().parents[1]


class AlterGroupFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_group_factor_loop_obligations(ROOT)
        # GRM(0) + SFV(57) + RISK(2) = 59 ; INV is not applicable.
        self.assertEqual(59, len(rows))
        self.assertEqual(
            {"SFV": 57, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(59, len({row.obligation_id for row in rows}))
        # ALTER GROUP has no grammar axis beyond the canonical factors.
        self.assertEqual(0, sum(row.kind == "GRM" for row in rows))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(0, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            59,
            sum(row.disposition in {"covered", "expected_failure"} for row in rows),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_alter_group_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(57, len(sfv))
        # every canonical factor value has exactly one SFV obligation
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(57, sum(seen.values()))
        self.assertEqual(57, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_alter_group_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 13 canonical values reach the PG target check and are rejected;
        # the remaining 44 SFV + 2 RISK = 46 are covered.
        self.assertEqual(13, len(failures))
        self.assertEqual(46, covered)
        # no duplicate failure obligation
        self.assertEqual(len(failures), len(set(failures)))
        # NOTICE-boundary values are NOT failures (they succeed with a
        # NOTICE, not an error).
        self.assertNotIn(("duplicate_add_user", "existing_member"), failures)
        self.assertNotIn(("drop_non_member_user", "non_member"), failures)
        # deprecated_command_note is an annotation, not a failure.
        self.assertNotIn(("deprecated_command_note", "deprecated_no_warning"), failures)
        # the frozen failure set is exactly the reachable negatives.
        self.assertEqual(
            frozenset(failures),
            frozenset(
                {
                    ("expected_status", "failure"),
                    ("object_state", "not_exists"),
                    ("group_name_shape", "nonexistent_name"),
                    ("user_name_shape", "nonexistent_user"),
                    ("user_existence", "user_not_exists"),
                    ("nonexistent_group", "group_missing"),
                    ("nonexistent_user", "user_missing"),
                    ("new_name_shape", "duplicate_name"),
                    ("rename_to_existing_name", "same_name_conflict"),
                    ("privilege_level", "non_admin"),
                    ("insufficient_privilege", "insufficient_privilege"),
                    ("non_admin_attempt", "non_admin_execution"),
                    ("target_role_admin", "lacks_admin"),
                }
            ),
        )

    def test_risk_obligations_carry_transaction_outcome(self) -> None:
        rows = compile_alter_group_factor_loop_obligations(ROOT)
        risk = [row for row in rows if row.kind == "RISK"]
        self.assertEqual(2, len(risk))
        self.assertEqual(
            {"commit", "rollback"}, {row.value for row in risk}
        )
        self.assertTrue(
            all(row.factor_key == "transaction_outcome" for row in risk)
        )
        self.assertTrue(all(row.disposition == "covered" for row in risk))


class AlterGroupFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(self) -> None:
        plan = build_alter_group_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, AlterGroupFactorLoopPlan)
        # delegated is empty for ALTER GROUP (boundaries are expected_failure)
        self.assertEqual(0, len(plan.delegated))
        # exactly one local case per non-delegated obligation
        self.assertEqual(59, len(plan.cases))
        # stable 1..N numbering
        self.assertEqual(
            list(range(1, 60)), [row.ordinal for row in plan.cases]
        )
        # case_id / sql_filename / object_prefix follow the 4-digit scheme
        self.assertEqual("ALTERGROUP0001", plan.cases[0].case_id)
        self.assertEqual("ALTERGROUP0059", plan.cases[-1].case_id)
        self.assertEqual("ALTERGROUP0001.sql", plan.cases[0].sql_filename)
        self.assertEqual("ALTERGROUP0059.sql", plan.cases[-1].sql_filename)
        self.assertEqual("altergroup_0001_", plan.cases[0].object_prefix)
        self.assertEqual("altergroup_0059_", plan.cases[-1].object_prefix)
        # every case maps to exactly one obligation
        self.assertEqual(
            59, len({row.primary_obligation_id for row in plan.cases})
        )
        self.assertEqual(59, len({row.sql_filename for row in plan.cases}))
        # execution profile is the serial contract
        self.assertTrue(
            all(row.execution_profile == "serial_sql" for row in plan.cases)
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_alter_group_factor_loop_plan(ROOT)
        obligations = compile_alter_group_factor_loop_obligations(ROOT)
        by_id = {row.obligation_id: row for row in obligations}
        for case in plan.cases:
            obligation = by_id[case.primary_obligation_id]
            if obligation.disposition == "expected_failure":
                self.assertEqual("expected_failure", case.outcome)
                # fixed 5-digit SQLSTATE
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(case.expected_failure_reason)
            else:
                self.assertEqual("success", case.outcome)
                self.assertEqual("00000", case.expected_sqlstate)
                self.assertIsNone(case.expected_failure_reason)

    def test_baseline_has_one_primary_value_no_duplicates(self) -> None:
        plan = build_alter_group_factor_loop_plan(ROOT)
        for case in plan.cases:
            # exactly one primary factor override per case
            primary_seen = sum(
                1
                for key, _ in case.baseline_assignments
                if key == case.factor_key
            )
            self.assertEqual(1, primary_seen, case.sql_filename)
            # no duplicate keys in the baseline
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(len(keys), len(set(keys)), case.sql_filename)
            # the primary value is the obligation's own value
            primary_value = next(
                value
                for key, value in case.baseline_assignments
                if key == case.factor_key
            )
            self.assertEqual(case.factor_value, primary_value)
            # every baseline is sorted for determinism
            self.assertEqual(
                case.baseline_assignments,
                tuple(sorted(case.baseline_assignments)),
            )

    def test_baseline_branch_and_action_are_consistent(self) -> None:
        plan = build_alter_group_factor_loop_plan(ROOT)
        branch_to_action = {
            "branch_add_user": "add_user",
            "branch_drop_user": "drop_user",
            "branch_rename": "rename",
        }
        equiv = {
            "branch_add_user": "add_user_equals_grant",
            "branch_drop_user": "drop_user_equals_revoke",
            "branch_rename": "rename_equals_alter_role",
        }
        for case in plan.cases:
            baseline = dict(case.baseline_assignments)
            self.assertEqual(
                baseline["alter_action"],
                case.consumer_action_id,
                case.sql_filename,
            )
            self.assertEqual(
                baseline["statement_branch"],
                next(
                    b
                    for b, a in branch_to_action.items()
                    if a == case.consumer_action_id
                ),
                case.sql_filename,
            )
            self.assertEqual(
                equiv[baseline["statement_branch"]],
                baseline["deprecated_equivalence"],
                case.sql_filename,
            )

    def test_privilege_cluster_is_consistent(self) -> None:
        plan = build_alter_group_factor_loop_plan(ROOT)
        for case in plan.cases:
            baseline = dict(case.baseline_assignments)
            level = baseline["privilege_level"]
            if level == "superuser":
                self.assertEqual("has_admin", baseline["target_role_admin"])
                self.assertEqual(
                    "sufficient_privilege", baseline["insufficient_privilege"]
                )
                self.assertEqual("admin_execution", baseline["non_admin_attempt"])
            elif level == "non_admin":
                self.assertEqual("lacks_admin", baseline["target_role_admin"])
                self.assertEqual(
                    "insufficient_privilege", baseline["insufficient_privilege"]
                )
                self.assertEqual(
                    "non_admin_execution", baseline["non_admin_attempt"]
                )


if __name__ == "__main__":
    unittest.main()
