from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_foreign_table_factor_loop import (
    build_alter_foreign_table_factor_loop_plan,
)
from pg_case_factory.alter_foreign_table_factor_render import (
    AlterForeignTableFactorRenderError,
    direct_member_renderer_registry,
    resolve_alter_foreign_table_factor_witness,
    validate_alter_foreign_table_direct_member_renderers,
)


ROOT = Path(__file__).resolve().parents[1]


class AlterForeignTableColumnFactorRenderTest(unittest.TestCase):
    def test_every_column_definition_obligation_has_a_real_target_fragment(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        dimensions = {
            "data_type_and_typmod",
            "collation",
            "nullability",
            "default_state",
            "generation_mode",
            "identity_mode",
            "storage_and_compression",
        }
        cases = [row for row in plan.cases if row.factor_key in dimensions]
        self.assertEqual(853, len(cases))
        for case in cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_foreign_table_factor_witness(case, ROOT)
                self.assertEqual(
                    case.primary_obligation_id,
                    witness.primary_obligation_id,
                )
                self.assertTrue(witness.target_sql_fragment.strip())
                self.assertNotRegex(
                    witness.target_sql_fragment,
                    r"\{[A-Za-z_]\w*\}",
                )
                self.assertIn(
                    witness.semantic_locus,
                    {
                        "target.column_definition",
                        "target.type_name",
                        "fixture.column_state",
                    },
                )

    def test_direct_member_renderer_domains_are_exact(self) -> None:
        validate_alter_foreign_table_direct_member_renderers(ROOT)

    def test_deleting_one_member_renderer_fails_closed(self) -> None:
        registry = direct_member_renderer_registry()
        del registry["nullability"]["explicit_null"]
        with self.assertRaisesRegex(
            AlterForeignTableFactorRenderError,
            "missing member renderer",
        ):
            validate_alter_foreign_table_direct_member_renderers(
                ROOT,
                registry=registry,
            )

    def test_empty_type_declaration_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            AlterForeignTableFactorRenderError,
            "empty type declaration",
        ):
            validate_alter_foreign_table_direct_member_renderers(
                ROOT,
                type_declaration_overrides={
                    (
                        "structured_config.types",
                        "smallint",
                    ): "",
                },
            )


if __name__ == "__main__":
    unittest.main()
