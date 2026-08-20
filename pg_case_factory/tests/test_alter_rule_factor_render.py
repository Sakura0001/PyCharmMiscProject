from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_rule_factor_extension import (
    AlterRuleFactorExtensionCase,
    build_alter_rule_factor_extension_plan,
)
from pg_case_factory.alter_rule_factor_loop import (
    build_alter_rule_factor_loop_plan,
)
from pg_case_factory.alter_rule_factor_render import (
    AlterRuleFactorRenderError,
    count_primary_alter_rule,
    generate_alter_rule_factor_programs,
    render_alter_rule_factor_case,
    resolve_alter_rule_factor_witness,
)
ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 46
_EXTENSION_COUNT = 2096
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT  # 2142


class AlterRuleFactorRenderTest(unittest.TestCase):
    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_alter_rule_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_rule_factor_witness(case, ROOT)
                self.assertEqual(
                    case.primary_obligation_id,
                    witness.primary_obligation_id,
                )
                self.assertEqual(case.outcome, witness.outcome)
                self.assertEqual(
                    case.expected_sqlstate, witness.expected_sqlstate
                )
                self.assertTrue(witness.target_sql_fragment.strip())
                self.assertNotRegex(
                    witness.target_sql_fragment, r"\{[A-Za-z_]\w*\}"
                )
                self.assertTrue(
                    witness.target_sql_fragment.startswith("ALTER RULE")
                )
                self.assertTrue(witness.setup_sql)
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.cleanup_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_alter_rule_factor_loop_plan(ROOT)
        ext = build_alter_rule_factor_extension_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_rule_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_rule(sql))
                self.assertIn("-- primary-target-begin", sql)
                self.assertIn("-- primary-target-end", sql)
                self.assertIn("ALTER RULE", sql)
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)
                self.assertTrue(sql.endswith("\n"))
        for case in ext.cases[:50]:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_rule_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_rule(sql))
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)

    def test_bookend_for_table_type_table_cases(self) -> None:
        plan = build_alter_rule_factor_loop_plan(ROOT)
        for case in plan.cases:
            a = dict(case.baseline_assignments)
            if a.get("table_type") != "table":
                continue
            if a.get("table_name_shape") == "nonexistent_table":
                continue
            with self.subTest(case_id=case.case_id):
                sql = render_alter_rule_factor_case(case, ROOT)
                self.assertIn(
                    "CREATE TABLE",
                    sql,
                    f"expected CREATE TABLE in {case.case_id}",
                )
                self.assertIn(
                    "DROP TABLE IF EXISTS",
                    sql,
                    f"expected DROP TABLE bookend in {case.case_id}",
                )
                lines = [
                    ln.strip()
                    for ln in sql.splitlines()
                    if ln.strip() and not ln.strip().startswith("--")
                ]
                sql_only = [ln for ln in lines if not ln.startswith("\\")]
                self.assertTrue(
                    sql_only[0].startswith("DROP TABLE IF EXISTS"),
                    f"first executable statement must be DROP TABLE IF EXISTS in {case.case_id}: {sql_only[0]!r}",
                )
                self.assertTrue(
                    sql_only[-1].startswith("DROP TABLE IF EXISTS"),
                    f"last executable statement must be DROP TABLE IF EXISTS in {case.case_id}: {sql_only[-1]!r}",
                )

    def test_no_create_table_for_view_cases(self) -> None:
        plan = build_alter_rule_factor_loop_plan(ROOT)
        for case in plan.cases:
            a = dict(case.baseline_assignments)
            if a.get("table_type") != "view":
                continue
            with self.subTest(case_id=case.case_id):
                sql = render_alter_rule_factor_case(case, ROOT)
                self.assertNotIn(
                    "CREATE TABLE",
                    sql,
                    f"unexpected CREATE TABLE in view case {case.case_id}",
                )

    def test_return_behavior_oracle_is_present(self) -> None:
        plan = build_alter_rule_factor_loop_plan(ROOT)
        ext = build_alter_rule_factor_extension_plan(ROOT)
        found = False
        for case in plan.cases:
            a = dict(case.baseline_assignments)
            if a.get("on_select_return_rename") != "_RETURN_rename_breaks_view":
                continue
            if case.outcome != "success":
                continue
            found = True
            with self.subTest(case_id=case.case_id):
                sql = render_alter_rule_factor_case(case, ROOT)
                self.assertIn("return_rule_renamed", sql)
                self.assertIn("_RETURN", sql)
        self.assertTrue(found, "no _RETURN behavior success case found in baseline")
        ext_found = False
        for case in ext.cases:
            a = dict(case.factor_assignment)
            if a.get("on_select_return_rename") != "_RETURN_rename_breaks_view":
                continue
            if case.outcome != "success":
                continue
            ext_found = True
            with self.subTest(case_id=case.case_id):
                sql = render_alter_rule_factor_case(case, ROOT)
                self.assertIn("return_rule_renamed", sql)
        self.assertTrue(ext_found, "no _RETURN behavior success case found in extension")

    def test_generate_programs_writes_all_files(self) -> None:
        import tempfile
        plan = build_alter_rule_factor_loop_plan(ROOT)
        ext = build_alter_rule_factor_extension_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            count = generate_alter_rule_factor_programs(plan, ext, Path(tmp))
            self.assertEqual(_TOTAL, count)


if __name__ == "__main__":
    unittest.main()
