from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_foreign_table_factor_loop import (
    build_alter_foreign_table_factor_loop_plan,
)
from pg_case_factory.alter_foreign_table_regress import (
    load_alter_foreign_table_grammar_actions,
)
from pg_case_factory.alter_foreign_table_factor_render import (
    AlterForeignTableFactorRenderError,
    direct_member_renderer_registry,
    resolve_alter_foreign_table_factor_witness,
    validate_alter_foreign_table_constraint_member_renderers,
    validate_alter_foreign_table_direct_member_renderers,
    validate_alter_foreign_table_remaining_inventory_renderers,
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

    def test_constraint_members_have_isolated_action_witnesses(self) -> None:
        validate_alter_foreign_table_constraint_member_renderers(ROOT)
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        dimensions = {
            "primary_key_participation",
            "unique_constraint",
            "check_constraint",
            "foreign_key_role",
        }
        rows = [row for row in plan.cases if row.factor_key in dimensions]
        self.assertEqual(128, len(rows))
        for case in rows:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_foreign_table_factor_witness(case, ROOT)
                self.assertTrue(witness.target_sql_fragment)
                if case.factor_key in {
                    "primary_key_participation",
                    "unique_constraint",
                    "foreign_key_role",
                } and case.factor_value not in {
                    "not_primary_key_member",
                    "no_unique_constraint",
                    "no_foreign_key_role",
                }:
                    self.assertEqual(
                        ("expected_failure", "0A000"),
                        (witness.outcome, witness.expected_sqlstate),
                    )

    def test_all_dependency_member_action_rows_have_real_fixtures(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        rows = [row for row in plan.cases if row.factor_key == "dependency_state"]
        self.assertEqual(60, len(rows))
        for case in rows:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_foreign_table_factor_witness(case, ROOT)
                self.assertTrue(witness.target_sql_fragment.strip())
                self.assertTrue(witness.oracle_sql)
                self.assertNotIn("::oid", "\n".join(witness.oracle_sql).lower())
                if case.factor_value != "no_external_dependency":
                    self.assertTrue(witness.setup_sql)

    def test_every_local_inventory_obligation_has_one_renderer(self) -> None:
        validate_alter_foreign_table_remaining_inventory_renderers(ROOT)
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        inv_cases = [row for row in plan.cases if row.kind == "INV"]
        self.assertEqual(1_564, len(inv_cases))
        rendered = [
            resolve_alter_foreign_table_factor_witness(row, ROOT)
            for row in inv_cases
        ]
        self.assertEqual(1_564, len(rendered))
        self.assertTrue(all(row.primary_obligation_id for row in rendered))

    def test_all_seven_relation_topologies_have_explicit_witnesses(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        rows = [row for row in plan.cases if row.factor_key == "relation_topology"]
        self.assertEqual(
            (
                "standalone",
                "inheritance_parent",
                "inheritance_child",
                "inheritance_parent_and_child",
                "partition_leaf_range",
                "partition_leaf_list",
                "partition_leaf_hash",
            ),
            tuple(row.factor_value for row in rows),
        )
        for case in rows:
            witness = resolve_alter_foreign_table_factor_witness(case, ROOT)
            self.assertTrue(witness.target_sql_fragment)
            self.assertEqual("fixture.column_state", witness.semantic_locus)

    def test_all_27_official_actions_render_once_as_primary(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        action_cases = [
            row
            for row in plan.cases
            if row.kind == "GRM" and row.factor_key == "target_action"
        ]
        self.assertEqual(27, len(action_cases))
        self.assertEqual(
            {
                row.action_id
                for row in load_alter_foreign_table_grammar_actions()
            },
            {row.factor_value for row in action_cases},
        )
        for case in action_cases:
            witness = resolve_alter_foreign_table_factor_witness(case, ROOT)
            self.assertTrue(witness.target_sql_fragment.startswith("ALTER FOREIGN TABLE"))
            self.assertNotRegex(witness.target_sql_fragment, r"\{[A-Za-z_]\w*\}")

    def test_every_grammar_canonical_and_transaction_case_renders(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        rows = [row for row in plan.cases if row.kind in {"GRM", "SFV", "RISK"}]
        self.assertEqual(241, len(rows))
        for case in rows:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_foreign_table_factor_witness(case, ROOT)
                self.assertTrue(witness.target_sql_fragment.strip())
                self.assertEqual(case.outcome, witness.outcome)
                self.assertEqual(case.expected_sqlstate, witness.expected_sqlstate)

    def test_transaction_witnesses_have_distinct_commit_and_rollback_oracles(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        rows = {row.factor_value: row for row in plan.cases if row.kind == "RISK"}
        self.assertEqual({"commit", "rollback"}, set(rows))
        commit = resolve_alter_foreign_table_factor_witness(rows["commit"], ROOT)
        rollback = resolve_alter_foreign_table_factor_witness(rows["rollback"], ROOT)
        self.assertIn("COMMIT;", commit.oracle_sql)
        self.assertIn("ROLLBACK;", rollback.oracle_sql)


if __name__ == "__main__":
    unittest.main()
