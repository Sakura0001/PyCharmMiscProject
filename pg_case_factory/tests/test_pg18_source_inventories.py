from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "audit_pg18_source_inventories.py"
ARCHIVE = Path("/tmp/postgresql-18.4.tar.bz2")
SOURCE_ROOT = Path("/tmp/pg-factor-audit/18/postgresql-18.4")
REQUIRED_SOURCE_FILES = (
    "src/include/catalog/pg_class.h",
    "src/include/nodes/parsenodes.h",
    "src/include/catalog/pg_type.dat",
    "src/include/catalog/pg_am.dat",
)
HAS_SOURCE_ROOT = all((SOURCE_ROOT / path).is_file() for path in REQUIRED_SOURCE_FILES)
SPEC = importlib.util.spec_from_file_location("audit_pg18_source_inventories", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load {SCRIPT}")
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class CommittedSourceSnapshotTest(unittest.TestCase):
    def test_committed_snapshot_counts_hashes_and_legacy_boundaries_are_self_consistent(self) -> None:
        coverage = yaml.safe_load((ROOT / audit.COVERAGE_INVENTORY).read_text(encoding="utf-8"))
        markdown = (ROOT / audit.TYPE_CATALOG).read_text(encoding="utf-8")
        match = re.search(r"```yaml\s*(.*?)```", markdown, re.DOTALL)
        self.assertIsNotNone(match)
        types = yaml.safe_load(match.group(1))["structured_config"]

        for document, values in (
            (coverage["sql_object_types"], coverage["sql_object_types"]["all_sql_object_types"]),
            (coverage["relation_kinds"], coverage["relation_kinds"]["all_pg18_relkinds"]),
            (types["concrete_builtin_types"], types["concrete_builtin_types"]["values"]),
            (types["auto_array_types"], types["auto_array_types"]["element_types"]),
            (types["pseudo_types"], types["pseudo_types"]["values"]),
        ):
            self.assertEqual(document["count"], len(values))
            self.assertEqual(document["inventory_sha256"], audit.inventory_values_sha256(values))

        for dimension, expected_values in audit.EXPECTED_TABLE_DIMENSIONS.items():
            document = coverage["relation_dimensions"][dimension]
            self.assertEqual(tuple(document["values"]), expected_values)
            self.assertEqual(document["count"], len(expected_values))
            self.assertEqual(
                document["inventory_sha256"],
                audit.inventory_values_sha256(expected_values),
            )

        self.assertFalse(coverage["object_kinds"]["canonical"])
        self.assertFalse(coverage["table_kinds"]["canonical"])
        self.assertEqual(
            coverage["object_kinds"]["all_object_kinds"],
            coverage["test_target_contexts"]["all_legacy_test_target_contexts"],
        )
        self.assertEqual(
            "5f5887b75677cba2d4a1a0cfeb355df5ed91f85d385fac88bd8d7c605b3578f9",
            types["source_audit"]["catalog_sources"]["pg_type_dat"]["sha256"],
        )


@unittest.skipUnless(
    HAS_SOURCE_ROOT or ARCHIVE.exists(),
    "official PostgreSQL 18.4 source tree/archive is unavailable",
)
class Pg18SourceInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = (
            audit.SourceBundle(source_root=SOURCE_ROOT)
            if HAS_SOURCE_ROOT
            else audit.SourceBundle(archive=ARCHIVE)
        )

    def source_text(self, path: str) -> str:
        return self.sources.read(path).decode("utf-8")

    def test_committed_inventories_match_official_pg18_4_source(self) -> None:
        result = audit.audit_repository(ROOT, self.sources)
        self.assertTrue(result.passed, result.errors)

    def test_official_source_derivations_have_expected_cardinalities(self) -> None:
        pg_class = self.source_text("src/include/catalog/pg_class.h")
        parsenodes = self.source_text("src/include/nodes/parsenodes.h")
        pg_type = self.source_text("src/include/catalog/pg_type.dat")
        pg_am = self.source_text("src/include/catalog/pg_am.dat")

        self.assertEqual(10, len(audit.derive_relkind_records(pg_class)))
        self.assertEqual(52, len(audit.derive_object_types(parsenodes)))
        types = audit.derive_pg_type_inventory(pg_type)
        self.assertEqual(85, len(types.concrete))
        self.assertEqual(79, len(types.array_elements))
        self.assertEqual(26, len(types.pseudo))
        self.assertEqual(("heap",), audit.derive_builtin_table_access_methods(pg_am))

    def test_source_removal_or_duplicate_is_rejected(self) -> None:
        pg_class = self.source_text("src/include/catalog/pg_class.h")
        missing_relkind = pg_class.replace(
            "#define\t\t  RELKIND_VIEW\t\t\t  'v'\t/* view */\n",
            "",
            1,
        )
        with self.assertRaisesRegex(ValueError, "expected 10 unique RELKIND"):
            audit.derive_relkind_records(missing_relkind)

        parsenodes = self.source_text("src/include/nodes/parsenodes.h")
        duplicate_object = parsenodes.replace("OBJECT_VIEW,", "OBJECT_TABLE,", 1)
        with self.assertRaisesRegex(ValueError, "52 unique ObjectType"):
            audit.derive_object_types(duplicate_object)

        pg_type = self.source_text("src/include/catalog/pg_type.dat")
        missing_type = pg_type.replace("typname => 'bool'", "typname_missing => 'bool'", 1)
        with self.assertRaisesRegex(ValueError, "expected 85 explicit non-pseudo"):
            audit.derive_pg_type_inventory(missing_type)

    def test_archive_hash_drift_is_reported(self) -> None:
        class WrongArchiveHash(audit.SourceBundle):
            def archive_sha256(self):
                return "0" * 64

        wrong_sources = (
            WrongArchiveHash(source_root=SOURCE_ROOT)
            if HAS_SOURCE_ROOT
            else WrongArchiveHash(archive=ARCHIVE)
        )
        result = audit.audit_repository(ROOT, wrong_sources)
        self.assertFalse(result.passed)
        self.assertTrue(
            any("source_archive_sha256" in error for error in result.errors),
            result.errors,
        )


if __name__ == "__main__":
    unittest.main()
