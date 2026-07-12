from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from pg_case_factory.contracts import (
    ContractValidationError,
    REQUIRED_RISK_DECISIONS,
    inventory_values_sha256,
    load_coverage_plan,
)
from pg_case_factory.inventory import resolve_inventory_values, verify_inventory_sources


ROOT = Path(__file__).resolve().parents[1]
SHIPPED_PLAN_TEMPLATE = (
    ROOT / "skills" / "pg-sql-generation" / "assets" / "templates" / "coverage_plan_template.yaml"
)


class InventoryVerificationTest(unittest.TestCase):
    def axis(self, values, source):
        document = {
            "values": list(values),
            "inventory_source": source,
            "coverage_mode": "complete",
            "inventory_count": len(values),
            "inventory_sha256": inventory_values_sha256(values),
        }
        if source.startswith("inline:"):
            document.update(
                {
                    "description": "Complete feature-local inventory fixture.",
                    "derivation": "Use every value supplied by this unit test.",
                    "source_locators": ["feature:REQ-001", "pg18:fixture"],
                    "exclusion_policy": "No supplied fixture value is excluded.",
                    "review_status": "semantic_reviewed",
                }
            )
        return document

    def plan(self, axis_id, values, source, scope, other_scopes=None):
        decisions = {
            name: {
                "status": "not_applicable",
                "reason": f"The fixture does not exercise canonical {name} scope.",
            }
            for name in ("object", "relation", "table", "column_type")
        }
        if other_scopes:
            decisions.update(other_scopes)
        return {
            "schema_version": 1,
            "kind": "coverage_plan",
            "plan_id": "PLAN-INVENTORY",
            "feature_id": "inventory-verification",
            "axes": {axis_id: self.axis(values, source)},
            "scope_decisions": decisions,
            "risk_decisions": {
                risk: {
                    "status": "not_applicable",
                    "reason": f"The inventory fixture does not exercise {risk} semantics.",
                }
                for risk in REQUIRED_RISK_DECISIONS
            },
            "test_points": [
                {
                    "id": "TP-001",
                    "title": "Exercise the resolved inventory",
                    "requirement_ids": ["REQ-001"],
                    "core_axes": [axis_id],
                    "dependencies": [],
                    "default_outcome": "success",
                }
            ],
        }

    def write_plan(self, root, document, name="plan.yaml"):
        path = root / name
        path.write_text(
            yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def test_resolves_yaml_sequence_and_markdown_mapping_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inventory.yaml").write_text(
                textwrap.dedent(
                    """
                    table_kinds:
                      all_table_kinds:
                        - heap
                        - partitioned
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            yaml_plan = self.plan(
                "table_kind",
                ["heap", "partitioned"],
                "inventory.yaml#table_kinds.all_table_kinds",
                "table",
            )
            loaded_yaml = load_coverage_plan(
                self.write_plan(root, yaml_plan, "yaml-plan.yaml"),
                inventory_root=root,
            )
            self.assertIsNone(verify_inventory_sources(loaded_yaml, root))

            (root / "types.md").write_text(
                textwrap.dedent(
                    """
                    # PostgreSQL 18.4 types

                    ```yaml
                    structured_config:
                      types:
                        integer: {category: numeric}
                        text: {category: string}
                    ```
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            markdown_plan = self.plan(
                "column_type",
                ["integer", "text"],
                "types.md#structured_config.types",
                "column_type",
            )
            loaded_markdown = load_coverage_plan(
                self.write_plan(root, markdown_plan, "markdown-plan.yaml"),
                inventory_root=root,
            )
            self.assertEqual(loaded_markdown.axes["column_type"].values, ("integer", "text"))

    def test_nonexistent_source_is_rejected_when_inventory_root_is_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            document = self.plan(
                "table_kind",
                ["heap"],
                "missing.yaml#table_kinds.all_table_kinds",
                "table",
            )
            with self.assertRaisesRegex(ContractValidationError, "inventory source does not exist"):
                load_coverage_plan(self.write_plan(root, document), inventory_root=root)

    def test_declared_subset_cannot_masquerade_as_complete_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inventory.yaml").write_text(
                "table_kinds:\n  all_table_kinds: [heap, partitioned]\n",
                encoding="utf-8",
            )
            document = self.plan(
                "table_kind",
                ["heap"],
                "inventory.yaml#table_kinds.all_table_kinds",
                "table",
            )
            with self.assertRaisesRegex(ContractValidationError, "does not exactly match resolved inventory"):
                load_coverage_plan(self.write_plan(root, document), inventory_root=root)

    def test_resolver_rejects_traversal_duplicate_keys_and_non_scalar_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            traversal = self.plan(
                "table_kind",
                ["heap"],
                "../outside.yaml#table_kinds.all_table_kinds",
                "table",
            )
            with self.assertRaisesRegex(ContractValidationError, "outside inventory_root"):
                load_coverage_plan(self.write_plan(root, traversal, "traversal.yaml"), inventory_root=root)

            (root / "duplicate.yaml").write_text(
                "table_kinds:\n  all_table_kinds: [heap]\n  all_table_kinds: [partitioned]\n",
                encoding="utf-8",
            )
            duplicate = self.plan(
                "table_kind",
                ["heap"],
                "duplicate.yaml#table_kinds.all_table_kinds",
                "table",
            )
            with self.assertRaisesRegex(ContractValidationError, "duplicate YAML key all_table_kinds"):
                load_coverage_plan(self.write_plan(root, duplicate, "duplicate-plan.yaml"), inventory_root=root)

            (root / "nested.yaml").write_text(
                "table_kinds:\n  all_table_kinds:\n    - {name: heap}\n",
                encoding="utf-8",
            )
            nested = self.plan(
                "table_kind",
                ["heap"],
                "nested.yaml#table_kinds.all_table_kinds",
                "table",
            )
            with self.assertRaisesRegex(ContractValidationError, "must contain only YAML scalars"):
                load_coverage_plan(self.write_plan(root, nested, "nested-plan.yaml"), inventory_root=root)

    def test_resolver_rejects_symlink_escape_and_missing_or_ambiguous_selector(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            outside = Path(outside_tmp) / "inventory.yaml"
            outside.write_text(
                "table_kinds:\n  all_table_kinds: [heap]\n",
                encoding="utf-8",
            )
            (root / "escaped.yaml").symlink_to(outside)
            escaped = self.plan(
                "table_kind",
                ["heap"],
                "escaped.yaml#table_kinds.all_table_kinds",
                "table",
            )
            with self.assertRaisesRegex(ContractValidationError, "outside inventory_root"):
                load_coverage_plan(self.write_plan(root, escaped, "escaped-plan.yaml"), inventory_root=root)

            (root / "missing.yaml").write_text(
                "table_kinds:\n  some_table_kinds: [heap]\n",
                encoding="utf-8",
            )
            missing = self.plan(
                "table_kind",
                ["heap"],
                "missing.yaml#table_kinds.all_table_kinds",
                "table",
            )
            with self.assertRaisesRegex(ContractValidationError, "selector.*was not found"):
                load_coverage_plan(self.write_plan(root, missing, "missing-selector-plan.yaml"), inventory_root=root)

            (root / "ambiguous.md").write_text(
                textwrap.dedent(
                    """
                    ```yaml
                    structured_config:
                      types: {integer: {}}
                    ```

                    ```yaml
                    structured_config:
                      types: {text: {}}
                    ```
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractValidationError, "selector.*is ambiguous"):
                resolve_inventory_values(
                    "ambiguous.md#structured_config.types",
                    root,
                )

    def test_markdown_duplicate_keys_and_scalar_type_substitution_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "duplicate.md").write_text(
                textwrap.dedent(
                    """
                    ```yaml
                    structured_config:
                      types: {integer: {}}
                      types: {text: {}}
                    ```
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractValidationError, "duplicate YAML key types"):
                resolve_inventory_values(
                    "duplicate.md#structured_config.types",
                    root,
                )

            # Python considers True == 1, but inventory equality is deliberately
            # YAML-type-aware so a boolean cannot replace an integer silently.
            (root / "inventory.yaml").write_text(
                "table_kinds:\n  all_table_kinds: [true]\n",
                encoding="utf-8",
            )
            substituted = self.plan(
                "table_kind",
                [1],
                "inventory.yaml#table_kinds.all_table_kinds",
                "table",
            )
            with self.assertRaisesRegex(ContractValidationError, "does not exactly match resolved inventory"):
                load_coverage_plan(
                    self.write_plan(root, substituted, "type-substitution-plan.yaml"),
                    inventory_root=root,
                )

    def test_inline_inventory_is_allowed_only_for_noncanonical_axes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            document = self.plan(
                "operation",
                ["read"],
                "inline:feature-local-operation",
                "table",
            )
            document["scope_decisions"]["table"] = {
                "status": "not_applicable",
                "reason": "This unit fixture has no table semantics.",
            }
            loaded = load_coverage_plan(
                self.write_plan(root, document, "inline-plan.yaml"),
                inventory_root=root,
            )
            self.assertIsNone(verify_inventory_sources(loaded, root))

            document["scope_decisions"]["table"] = {
                "status": "complete",
                "axis": "operation",
            }
            with self.assertRaisesRegex(ContractValidationError, "canonical inventory source"):
                load_coverage_plan(
                    self.write_plan(root, document, "inline-canonical-plan.yaml"),
                    inventory_root=root,
                )

    def test_canonical_scope_rejects_a_spoof_file_with_the_right_selector(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "spoof.yaml").write_text(
                "table_kinds:\n  all_table_kinds: [heap]\n",
                encoding="utf-8",
            )
            document = self.plan(
                "table_kind",
                ["heap"],
                "spoof.yaml#table_kinds.all_table_kinds",
                "table",
            )
            document["scope_decisions"]["table"] = {
                "status": "complete",
                "axis": "table_kind",
            }
            with self.assertRaisesRegex(ContractValidationError, "canonical inventory source"):
                load_coverage_plan(
                    self.write_plan(root, document, "spoof-plan.yaml"),
                    inventory_root=root,
                )

    def test_canonical_relative_path_cannot_redefine_the_pinned_pg18_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = (
                root
                / "skills"
                / "pg-sql-generation"
                / "references"
                / "combinations"
                / "_shared"
                / "coverage_inventory.yaml"
            )
            source.parent.mkdir(parents=True)
            source.write_text(
                "sql_object_types:\n  all_sql_object_types: [counterfeit_only]\n",
                encoding="utf-8",
            )
            document = self.plan(
                "object_type",
                ["counterfeit_only"],
                "skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml#sql_object_types.all_sql_object_types",
                "object",
            )
            document["scope_decisions"]["object"] = {
                "status": "complete",
                "axis": "object_type",
            }
            with self.assertRaisesRegex(ContractValidationError, "pinned PostgreSQL 18.4 provenance"):
                load_coverage_plan(
                    self.write_plan(root, document, "counterfeit-canonical.yaml"),
                    inventory_root=root,
                )

    def test_shipped_column_scope_requires_the_complete_pg18_type_universe(self):
        plan = load_coverage_plan(SHIPPED_PLAN_TEMPLATE, inventory_root=ROOT)
        self.assertEqual(
            plan.scope_decisions["column_type"].axes,
            (
                "column_type",
                "concrete_builtin_type",
                "auto_array_element_type",
                "pseudo_type",
                "declaration_alias",
                "typmod_declaration",
                "user_defined_archetype",
            ),
        )

        document = yaml.safe_load(SHIPPED_PLAN_TEMPLATE.read_text(encoding="utf-8"))
        document["scope_decisions"]["column_type"]["axes"].pop()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ContractValidationError, "canonical inventory source group"):
                load_coverage_plan(
                    self.write_plan(Path(tmp), document, "incomplete-type-universe.yaml"),
                    inventory_root=ROOT,
                )


if __name__ == "__main__":
    unittest.main()
