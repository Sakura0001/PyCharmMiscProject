from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_statistics_factor_extension import (
    build_alter_statistics_factor_extension_plan,
)
from pg_case_factory.alter_statistics_factor_loop import (
    build_alter_statistics_factor_loop_plan,
)
from pg_case_factory.alter_statistics_factor_render import (
    AlterStatisticsFactorRenderError,
    count_primary_alter_statistics,
    generate_alter_statistics_factor_programs,
    render_alter_statistics_factor_case,
    resolve_alter_statistics_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 56
_EXTENSION_COUNT = 1404
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT  # 1460


class AlterStatisticsFactorRenderTest(unittest.TestCase):
    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_alter_statistics_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_statistics_factor_witness(
                    case, ROOT
                )
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
                    witness.target_sql_fragment.startswith(
                        "ALTER STATISTICS"
                    )
                )
                self.assertTrue(witness.setup_sql)
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.cleanup_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_alter_statistics_factor_loop_plan(ROOT)
        ext = build_alter_statistics_factor_extension_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_statistics_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_statistics(sql))
                self.assertIn("-- primary-target-begin", sql)
                self.assertIn("-- primary-target-end", sql)
                self.assertIn("ALTER STATISTICS", sql)
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)
                self.assertTrue(sql.endswith("\n"))
        for case in ext.cases[:50]:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_statistics_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_statistics(sql))
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)

    def test_schema_qualified_catalog_oracles(self) -> None:
        plan = build_alter_statistics_factor_loop_plan(ROOT)
        ext = build_alter_statistics_factor_extension_plan(ROOT)
        for case in list(plan.cases) + list(ext.cases[:200]):
            with self.subTest(case_id=case.case_id):
                sql = render_alter_statistics_factor_case(case, ROOT)
                # Catalog oracles must schema-qualify pg_statistic_ext
                # or pg_class (both exempt from prefix rules), or use
                # information_schema for extended-statistics verification.
                self.assertTrue(
                    "pg_catalog.pg_statistic_ext" in sql
                    or "pg_catalog.pg_class" in sql
                    or "information_schema" in sql
                    or "pg_catalog.pg_roles" in sql
                    or "error_assertion" in sql,
                    f"no schema-qualified catalog oracle in {case.case_id}",
                )

    def test_underlying_table_is_created_for_statistics(self) -> None:
        plan = build_alter_statistics_factor_loop_plan(ROOT)
        ext = build_alter_statistics_factor_extension_plan(ROOT)
        for case in list(plan.cases) + list(ext.cases):
            with self.subTest(case_id=case.case_id):
                sql = render_alter_statistics_factor_case(case, ROOT)
                # Every ALTER STATISTICS case creates an underlying table
                # because extended statistics require a table to attach to.
                self.assertIn("CREATE TABLE", sql)

    def test_generate_programs_writes_all_files(self) -> None:
        import tempfile

        plan = build_alter_statistics_factor_loop_plan(ROOT)
        ext = build_alter_statistics_factor_extension_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            count = generate_alter_statistics_factor_programs(
                plan, ext, Path(tmp)
            )
            self.assertEqual(_TOTAL, count)


if __name__ == "__main__":
    unittest.main()
