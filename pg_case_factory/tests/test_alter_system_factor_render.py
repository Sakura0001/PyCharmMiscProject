"""Tests for ALTER SYSTEM factor-loop SQL program rendering."""

from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_system_factor_extension import (
    AlterSystemFactorExtensionCase,
    build_alter_system_factor_extension_plan,
)
from pg_case_factory.alter_system_factor_loop import (
    build_alter_system_factor_loop_plan,
)
from pg_case_factory.alter_system_factor_render import (
    AlterSystemFactorRenderError,
    count_primary_alter_system,
    generate_alter_system_factor_programs,
    render_alter_system_factor_case,
    resolve_alter_system_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 55
_EXTENSION_COUNT = 6240
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT  # 6295


class AlterSystemFactorRenderTest(unittest.TestCase):
    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_alter_system_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_system_factor_witness(
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
                        "ALTER SYSTEM"
                    )
                )
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.cleanup_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_alter_system_factor_loop_plan(ROOT)
        ext = build_alter_system_factor_extension_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_system_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_system(sql))
                self.assertIn("-- primary-target-begin", sql)
                self.assertIn("-- primary-target-end", sql)
                self.assertIn("ALTER SYSTEM", sql)
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)
                self.assertTrue(sql.endswith("\n"))
        for case in ext.cases[:50]:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_system_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_system(sql))
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)

    def test_schema_qualified_catalog_oracles(self) -> None:
        plan = build_alter_system_factor_loop_plan(ROOT)
        ext = build_alter_system_factor_extension_plan(ROOT)
        for case in list(plan.cases) + list(ext.cases[:200]):
            with self.subTest(case_id=case.case_id):
                sql = render_alter_system_factor_case(case, ROOT)
                # Catalog oracles must schema-qualify pg_settings or
                # pg_file_settings (both exempt from prefix), or use
                # SHOW command, or be error_assertion (no catalog query).
                self.assertTrue(
                    "pg_catalog.pg_settings" in sql
                    or "pg_catalog.pg_file_settings" in sql
                    or "SHOW " in sql
                    or "error_assertion" in sql.lower()
                    or "SELECT true AS removed_primary" in sql,
                    f"no catalog oracle in {case.case_id}",
                )

    def test_generate_programs_writes_all_files(self) -> None:
        import tempfile

        plan = build_alter_system_factor_loop_plan(ROOT)
        ext = build_alter_system_factor_extension_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            count = generate_alter_system_factor_programs(
                plan, ext, Path(tmp)
            )
            self.assertEqual(_TOTAL, count)


if __name__ == "__main__":
    unittest.main()
