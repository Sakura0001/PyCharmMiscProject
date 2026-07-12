from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

from pg_case_factory.audits._documents import UniqueKeySafeLoader


ROOT = Path(__file__).resolve().parents[1]
YAML_BLOCK = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)


def _load_catalog(name: str) -> dict:
    path = (
        ROOT
        / "skills"
        / "pg-sql-generation"
        / "references"
        / "common"
        / name
    )
    match = YAML_BLOCK.search(path.read_text(encoding="utf-8"))
    if not match:
        raise AssertionError(f"missing YAML catalog in {path}")
    parsed = yaml.load(match.group(1), Loader=UniqueKeySafeLoader)
    return parsed["structured_config"]


class Pg18TypeCatalogTest(unittest.TestCase):
    def test_catalog_is_a_ready_finite_profile_superset_of_the_pg16_baseline(self) -> None:
        baseline = _load_catalog("pg16_type_catalog.md")
        target = _load_catalog("pg18_type_catalog.md")

        self.assertEqual("pg18.4", target["version"])
        self.assertEqual("ready", target["source_audit"]["readiness"])
        canonical = target["type_sets"]["canonical_executable_column_profiles"]
        self.assertEqual("structured_config.types", canonical["selector"])
        self.assertEqual("core_executable_profiles", canonical["completeness_scope"])
        type_set = target["type_sets"]["all_pg18_column_types"]
        self.assertEqual("ready", type_set["readiness"])
        self.assertFalse(type_set["include_pseudo_types"])
        self.assertFalse(type_set["canonical"])
        self.assertLessEqual(set(baseline["types"]), set(target["types"]))
        self.assertIn("float", target["types"])

    def test_source_derived_type_sets_are_separate_and_exactly_sized(self) -> None:
        target = _load_catalog("pg18_type_catalog.md")

        concrete = target["concrete_builtin_types"]
        arrays = target["auto_array_types"]
        pseudo = target["pseudo_types"]
        self.assertEqual(85, concrete["count"])
        self.assertEqual(85, len(concrete["values"]))
        self.assertEqual(79, arrays["count"])
        self.assertEqual(79, len(arrays["element_types"]))
        self.assertEqual(26, pseudo["count"])
        self.assertEqual(26, len(pseudo["values"]))
        self.assertIn("pg_node_tree", concrete["values"])
        self.assertIn("refcursor", concrete["values"])
        self.assertIn("gtsvector", concrete["values"])
        self.assertIn("int4range", arrays["element_types"])
        self.assertIn("_record", pseudo["values"])

    def test_alias_typmod_and_user_defined_families_are_not_concrete_types(self) -> None:
        target = _load_catalog("pg18_type_catalog.md")

        aliases = target["declaration_aliases"]["mappings"]
        self.assertEqual("int4_with_sequence_default", aliases["serial"])
        self.assertEqual("numeric", aliases["decimal"])
        self.assertEqual("float4_or_float8_by_typmod", aliases["float"])
        typmods = target["typmod_profiles"]
        self.assertEqual(
            "semantic declaration classes and valid/invalid boundaries, not every integer typmod value",
            typmods["completeness_basis"],
        )
        self.assertIn("NUMERIC(10,-2)", typmods["numeric"]["success"])
        self.assertIn("TIMESTAMP(7)", typmods["datetime_precision"]["failure"])
        archetypes = target["user_defined_archetypes"]
        self.assertIn("range", archetypes["values"])
        self.assertIn("multirange", archetypes["values"])
        self.assertIn("base_type", archetypes["environment_required"])

    def test_every_type_has_executable_generation_metadata(self) -> None:
        target = _load_catalog("pg18_type_catalog.md")
        required = {
            "type_key",
            "type_category",
            "declaration_sql",
            "sample_values",
            "requires_setup",
            "index_capabilities",
            "notes",
        }
        for key, document in target["types"].items():
            with self.subTest(type_key=key):
                self.assertEqual(key, document["type_key"])
                self.assertEqual(set(), required - set(document))
                self.assertEqual(
                    {"success", "boundary", "failure"},
                    set(document["sample_values"]),
                )

    def test_pg18_semantic_type_deltas_are_explicit(self) -> None:
        target = _load_catalog("pg18_type_catalog.md")

        float_type = target["types"]["float"]
        self.assertEqual("FLOAT", float_type["declaration_sql"])
        self.assertIn("FLOAT(24)", float_type["declaration_variants"]["success"])
        self.assertIn("FLOAT(54)", float_type["declaration_variants"]["failure"])
        self.assertIn("'infinity'", target["types"]["interval"]["sample_values"]["boundary"])
        self.assertIn("uuidv7()", target["types"]["uuid"]["sample_values"]["success"])
        self.assertIn(
            "pg18_multidimensional_array_error_parity",
            target["source_audit"]["required_delta_tests"],
        )


if __name__ == "__main__":
    unittest.main()
