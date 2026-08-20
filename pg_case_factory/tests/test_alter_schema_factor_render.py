from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_schema_factor_extension import (
    AlterSchemaFactorExtensionCase,
    build_alter_schema_factor_extension_plan,
)
from pg_case_factory.alter_schema_factor_loop import (
    build_alter_schema_factor_loop_plan,
)
from pg_case_factory.alter_schema_factor_render import (
    AlterSchemaFactorRenderError,
    count_primary_alter_schema,
    generate_alter_schema_factor_programs,
    render_alter_schema_factor_case,
    resolve_alter_schema_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 57
_EXTENSION_COUNT = 4212
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT  # 4269


class AlterSchemaFactorRenderTest(unittest.TestCase):
    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_alter_schema_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_schema_factor_witness(case, ROOT)
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
                    witness.target_sql_fragment.startswith("ALTER SCHEMA")
                )
                self.assertTrue(witness.setup_sql)
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.cleanup_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_alter_schema_factor_loop_plan(ROOT)
        ext = build_alter_schema_factor_extension_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_schema_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_schema(sql))
                self.assertIn("-- primary-target-begin", sql)
                self.assertIn("-- primary-target-end", sql)
                self.assertIn("ALTER SCHEMA", sql)
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)
                self.assertTrue(sql.endswith("\n"))
        for case in ext.cases[:50]:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_schema_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_schema(sql))
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)

    def test_schema_qualified_catalog_oracles(self) -> None:
        plan = build_alter_schema_factor_loop_plan(ROOT)
        ext = build_alter_schema_factor_extension_plan(ROOT)
        for case in list(plan.cases) + list(ext.cases[:200]):
            with self.subTest(case_id=case.case_id):
                sql = render_alter_schema_factor_case(case, ROOT)
                # Catalog oracles must schema-qualify pg_namespace or
                # information_schema.schemata (both exempt from prefix).
                self.assertTrue(
                    "pg_catalog.pg_namespace" in sql
                    or "information_schema.schemata" in sql
                    or "current_schema()" in sql,
                    f"no schema-qualified catalog oracle in {case.case_id}",
                )

    def test_session_user_escape_oracle_is_present(self) -> None:
        plan = build_alter_schema_factor_loop_plan(ROOT)
        ext = build_alter_schema_factor_extension_plan(ROOT)
        found = False
        for case in list(plan.cases) + list(ext.cases):
            a = (
                dict(case.factor_assignment)
                if hasattr(case, "factor_assignment")
                else dict(case.baseline_assignments)
            )
            if a.get("owner_clause") != "SESSION_USER":
                continue
            if case.outcome != "success":
                continue
            found = True
            with self.subTest(case_id=case.case_id):
                sql = render_alter_schema_factor_case(case, ROOT)
                self.assertIn("OWNER TO SESSION_USER", sql)
                self.assertIn("ALTER SCHEMA", sql)
        self.assertTrue(
            found, "no SESSION_USER escape success case found"
        )

    def test_contained_table_for_schema_with_tables(self) -> None:
        ext = build_alter_schema_factor_extension_plan(ROOT)
        found = False
        for case in ext.cases:
            a = dict(case.factor_assignment)
            if a.get("contained_objects_state") != "schema_with_tables":
                continue
            if a.get("object_state") == "not_exists":
                continue
            found = True
            with self.subTest(case_id=case.case_id):
                sql = render_alter_schema_factor_case(case, ROOT)
                self.assertIn("CREATE TABLE", sql)
            break
        self.assertTrue(found, "no schema_with_tables extension case")

    def test_generate_programs_writes_all_files(self) -> None:
        import tempfile

        plan = build_alter_schema_factor_loop_plan(ROOT)
        ext = build_alter_schema_factor_extension_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            count = generate_alter_schema_factor_programs(
                plan, ext, Path(tmp)
            )
            self.assertEqual(_TOTAL, count)


if __name__ == "__main__":
    unittest.main()
