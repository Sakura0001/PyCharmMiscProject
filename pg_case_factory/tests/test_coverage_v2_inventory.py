from __future__ import annotations

import unittest
from pathlib import Path

from pg_case_factory.coverage_v2.input_lock import freeze_input_lock, verify_input_lock
from pg_case_factory.coverage_v2.inventory import (
    build_statement_order_artifact,
    compile_global_input_specs,
    discover_statement_inventory,
)
from pg_case_factory.coverage_v2.schema_registry import ArtifactSchemaRegistry


ROOT = Path(__file__).resolve().parents[1]
FIRST_TEN = (
    "abort",
    "alter_aggregate",
    "alter_collation",
    "alter_conversion",
    "alter_database",
    "alter_default_privileges",
    "alter_domain",
    "alter_event_trigger",
    "alter_extension",
    "alter_foreign_data_wrapper",
)


class StatementInventoryCompilerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = discover_statement_inventory(ROOT)

    def test_inventory_is_exactly_the_canonical_183_3357_9978_universe(self) -> None:
        self.assertEqual(183, len(self.inventory.entries))
        self.assertEqual(3357, self.inventory.factor_count)
        self.assertEqual(9978, self.inventory.factor_value_count)
        self.assertEqual(FIRST_TEN, self.inventory.statement_keys[:10])
        self.assertEqual(237, sum(row.factor_count for row in self.inventory.entries[:10]))
        self.assertEqual(
            670, sum(row.factor_value_count for row in self.inventory.entries[:10])
        )
        self.assertEqual(
            list(range(1, 184)), [row.ordinal for row in self.inventory.entries]
        )
        self.assertEqual(183, len(set(self.inventory.statement_keys)))
        for row in self.inventory.entries:
            with self.subTest(statement=row.statement_key):
                self.assertTrue(ROOT.joinpath(row.reference_path).is_file())
                self.assertTrue(ROOT.joinpath(row.matrix_path).is_file())
                self.assertGreater(row.factor_count, 0)
                self.assertGreater(row.factor_value_count, 0)

    def test_statement_order_artifact_is_strict_and_reproducible(self) -> None:
        registry = ArtifactSchemaRegistry.load_packaged()
        first = build_statement_order_artifact(self.inventory)
        second = build_statement_order_artifact(discover_statement_inventory(ROOT))
        registry.validate(first)
        self.assertEqual(first, second)
        payload = first["semantic_payload"]
        self.assertEqual(183, payload["statement_count"])
        self.assertEqual(3357, payload["factor_count"])
        self.assertEqual(9978, payload["factor_value_count"])
        self.assertEqual(
            list(FIRST_TEN),
            [row["statement_key"] for row in payload["statements"][:10]],
        )

    def test_global_input_specs_are_complete_unique_and_freezable(self) -> None:
        specs = compile_global_input_specs(ROOT, self.inventory)
        paths = [spec.relative_path for spec in specs]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(paths, sorted(paths, key=lambda value: value.encode("utf-8")))
        required = {
            "docs/superpowers/specs/2026-08-12-full-statement-regress-coverage-generation-design.md",
            "skills/pg-sql-generation/references/common/statement_support_inventory.yaml",
            "skills/pg-sql-generation/references/common/postgresql_18_4_factor_audit.tsv",
            "skills/pg-sql-generation/references/statements/tcl/transaction/abort.md",
            "skills/pg-sql-generation/references/combinations/tcl/transaction/abort.yaml",
            "src/pg_case_factory/coverage_v2/schema_registry.py",
            "src/pg_case_factory/coverage_v2/schemas/registry.json",
        }
        self.assertTrue(required <= set(paths))
        document = freeze_input_lock(ROOT, scope="global", input_specs=specs)
        bindings = verify_input_lock(ROOT, document)
        self.assertEqual(len(specs), len(bindings))


if __name__ == "__main__":
    unittest.main()
