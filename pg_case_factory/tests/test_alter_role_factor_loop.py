from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_role_factor_loop import (
    AlterRoleFactorCase,
    AlterRoleFactorLoopError,
    AlterRoleFactorLoopPlan,
    build_alter_role_factor_loop_plan,
    compile_alter_role_factor_loop_obligations,
)
from pg_case_factory.alter_role_regress import (
    load_alter_role_grammar_axes,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterRoleRegressGrammarTest(unittest.TestCase):
    def test_grammar_axis_ledger_is_frozen(self) -> None:
        axes = load_alter_role_grammar_axes()
        # Four pure grammar modifier axes (WITH / ENCRYPTED / action-list
        # cardinality / set-assignment form); the six branches and 18
        # attribute options are SFV rows, not GRM axes.
        self.assertEqual(4, len(axes))
        self.assertEqual(8, sum(len(axis.values) for axis in axes))
        axis_ids = {axis.axis_id for axis in axes}
        self.assertEqual(
            {
                "with_keyword",
                "encrypted_keyword",
                "action_list_cardinality",
                "set_assignment_form",
            },
            axis_ids,
        )


class AlterRoleFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_role_factor_loop_obligations(ROOT)
        # GRM(8) + SFV(98) + RISK(2) = 108 ; INV is not applicable.
        self.assertEqual(108, len(rows))
        self.assertEqual(
            {"GRM": 8, "SFV": 98, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(108, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(0, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            108,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_alter_role_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(98, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(98, sum(seen.values()))
        self.assertEqual(98, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_alter_role_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 17 canonical values reach the PG target check and are rejected;
        # the remaining 81 SFV + 8 GRM + 2 RISK = 91 are covered.
        self.assertEqual(17, len(failures))
        self.assertEqual(91, covered)
        self.assertEqual(len(failures), len(set(failures)))
        # The four BEHAVIOR assertions are SUCCESS paths and must NOT be
        # failure values.
        self.assertNotIn(
            ("rename_clears_password", "md5_password_cleared_on_rename"),
            failures,
        )
        self.assertNotIn(
            ("rename_clears_password", "scram_password_preserved_on_rename"),
            failures,
        )
        self.assertNotIn(
            ("password_security", "password_null_removes_password"),
            failures,
        )
        self.assertNotIn(
            ("password_security", "plaintext_password_in_sql"),
            failures,
        )


class AlterRoleFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, AlterRoleFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(108, len(plan.cases))
        self.assertEqual(
            list(range(1, 109)), [row.ordinal for row in plan.cases]
        )
        self.assertEqual("ALTERROLE0001", plan.cases[0].case_id)
        self.assertEqual("ALTERROLE0108", plan.cases[-1].case_id)
        self.assertEqual("ALTERROLE0001.sql", plan.cases[0].sql_filename)
        self.assertEqual("ALTERROLE0108.sql", plan.cases[-1].sql_filename)
        self.assertEqual("alterrole_0001_", plan.cases[0].object_prefix)
        self.assertEqual("alterrole_0108_", plan.cases[-1].object_prefix)
        self.assertEqual(
            108, len({row.primary_obligation_id for row in plan.cases})
        )
        self.assertEqual(108, len({row.sql_filename for row in plan.cases}))
        self.assertTrue(
            all(row.execution_profile == "serial_sql" for row in plan.cases)
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        obligations = compile_alter_role_factor_loop_obligations(ROOT)
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
        plan = build_alter_role_factor_loop_plan(ROOT)
        for case in plan.cases:
            primary_seen = sum(
                1
                for key, _ in case.baseline_assignments
                if key == case.factor_key
            )
            self.assertEqual(1, primary_seen, case.sql_filename)
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(len(keys), len(set(keys)), case.sql_filename)
            primary_value = next(
                value
                for key, value in case.baseline_assignments
                if key == case.factor_key
            )
            self.assertEqual(case.factor_value, primary_value)
            self.assertEqual(
                case.baseline_assignments,
                tuple(sorted(case.baseline_assignments)),
            )

    def test_obligation_multiset_is_stable(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        again = build_alter_role_factor_loop_plan(ROOT)
        self.assertEqual(
            plan.obligation_multiset_sha256,
            again.obligation_multiset_sha256,
        )


if __name__ == "__main__":
    unittest.main()
