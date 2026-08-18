from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_function_factor_loop import (
    build_alter_function_factor_loop_plan,
)
from pg_case_factory.alter_function_factor_render import (
    AlterFunctionFactorRenderError,
    count_primary_alter_function,
    render_alter_function_factor_case,
    resolve_alter_function_factor_witness,
)


ROOT = Path(__file__).resolve().parents[1]


class AlterFunctionFactorRenderTest(unittest.TestCase):
    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_alter_function_factor_loop_plan(ROOT)
        self.assertEqual(123, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_function_factor_witness(case, ROOT)
                self.assertEqual(
                    case.primary_obligation_id,
                    witness.primary_obligation_id,
                )
                self.assertEqual(case.outcome, witness.outcome)
                self.assertEqual(
                    case.expected_sqlstate, witness.expected_sqlstate
                )
                self.assertTrue(witness.target_sql_fragment.strip())
                # no unresolved template placeholders leak into the target
                self.assertNotRegex(
                    witness.target_sql_fragment, r"\{[A-Za-z_]\w*\}"
                )
                self.assertTrue(
                    witness.target_sql_fragment.startswith("ALTER FUNCTION")
                )
                self.assertTrue(witness.setup_sql)
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.cleanup_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_alter_function_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_function_factor_case(plan, case, ROOT)
                self.assertTrue(
                    sql.startswith("-- --------------------------------------------------------\n")
                )
                self.assertEqual(1, count_primary_alter_function(sql))
                self.assertIn(
                    f"-- primary_obligation_id: {case.primary_obligation_id}",
                    sql,
                )
                self.assertIn(f"-- case_id: {case.case_id}", sql)
                self.assertIn(
                    f"-- expected_outcome: {case.outcome}", sql
                )
                self.assertIn(
                    f"-- expected_sqlstate: {case.expected_sqlstate}", sql
                )
                self.assertNotRegex(sql, r"\{[A-Za-z_]\w*\}")
                self.assertTrue(sql.endswith(";\n"))
                self.assertFalse(sql.endswith("\n\n"))

    def test_all_programs_are_deterministic_in_memory(self) -> None:
        plan = build_alter_function_factor_loop_plan(ROOT)
        first = [
            render_alter_function_factor_case(plan, row, ROOT)
            for row in plan.cases
        ]
        second = [
            render_alter_function_factor_case(plan, row, ROOT)
            for row in plan.cases
        ]
        self.assertEqual(first, second)
        self.assertEqual(123, len(first))

    def test_expected_failure_programs_capture_and_restore_error_mode(self) -> None:
        plan = build_alter_function_factor_loop_plan(ROOT)
        failures = [row for row in plan.cases if row.outcome == "expected_failure"]
        self.assertEqual(24, len(failures))
        for case in failures:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_function_factor_case(plan, case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP off", sql)
                self.assertIn("\\set target_sqlstate :SQLSTATE", sql)
                self.assertIn(
                    f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}'",
                    sql,
                )
                self.assertIn("\\set ON_ERROR_STOP on", sql)

    def test_success_programs_keep_error_stop_armed(self) -> None:
        plan = build_alter_function_factor_loop_plan(ROOT)
        successes = [
            row for row in plan.cases if row.outcome == "success"
        ]
        self.assertEqual(99, len(successes))
        for case in successes:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_function_factor_case(plan, case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP on", sql)
                # success path never disarms error stop around the target
                self.assertNotIn("\\set ON_ERROR_STOP off", sql)

    def test_witness_fragments_are_present_in_rendered_bytes(self) -> None:
        plan = build_alter_function_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_function_factor_case(plan, case, ROOT)
                witness = resolve_alter_function_factor_witness(case, ROOT)
                for fragment in witness.setup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.oracle_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.cleanup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                self.assertIn(witness.target_sql_fragment.rstrip(), sql)

    def test_transaction_witnesses_have_distinct_commit_and_rollback(self) -> None:
        plan = build_alter_function_factor_loop_plan(ROOT)
        rows = {row.factor_value: row for row in plan.cases if row.kind == "RISK"}
        self.assertEqual({"commit", "rollback"}, set(rows))
        commit_sql = render_alter_function_factor_case(
            plan, rows["commit"], ROOT
        )
        rollback_sql = render_alter_function_factor_case(
            plan, rows["rollback"], ROOT
        )
        self.assertIn("COMMIT;", commit_sql)
        self.assertIn("ROLLBACK;", rollback_sql)
        self.assertNotIn("ROLLBACK;", commit_sql)
        self.assertNotIn("COMMIT;", rollback_sql)


if __name__ == "__main__":
    unittest.main()
