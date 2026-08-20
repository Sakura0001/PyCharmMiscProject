"""Tests for import_foreign_schema factor render module."""

import re
import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.import_foreign_schema_factor_extension import (
    build_import_foreign_schema_factor_extension_plan,
)
from src.pg_case_factory.import_foreign_schema_factor_loop import (
    build_import_foreign_schema_factor_loop_plan,
)
from src.pg_case_factory.import_foreign_schema_factor_render import (
    count_primary_import_foreign_schema,
    generate_import_foreign_schema_factor_programs,
    render_import_foreign_schema_factor_case,
)

_REPO = Path(__file__).resolve().parents[1]
_STYLE_VALIDATOR = (
    _REPO
    / "skills/regress-output-script-style/scripts/validate_regress_sql_style.py"
)


class TestImportForeignSchemaFactorRender(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_import_foreign_schema_factor_loop_plan(
            _REPO
        )
        self.extension = (
            build_import_foreign_schema_factor_extension_plan(_REPO)
        )
        self.out = Path(tempfile.mkdtemp())
        self.count = generate_import_foreign_schema_factor_programs(
            self.baseline, self.extension, self.out
        )

    def test_file_count(self) -> None:
        self.assertEqual(633, self.count)

    def test_filename_numbering(self) -> None:
        files = sorted(f.name for f in self.out.iterdir())
        self.assertEqual(
            [
                f"IMPORTFOREIGNSCHEMA{i:05d}.sql"
                for i in range(1, 634)
            ],
            files,
        )

    def test_one_primary_target_per_file(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertEqual(
                1, count_primary_import_foreign_schema(sql)
            )

    def test_no_create_table_bookend_na(self) -> None:
        # IMPORT FOREIGN SCHEMA creates FOREIGN TABLES (relkind='f'),
        # not CREATE TABLE -> the bookend gate is class-2 N/A.
        from src.pg_case_factory.regression_style import (
            contains_create_table_statement,
        )

        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertFalse(
                contains_create_table_statement(sql),
                msg=f"{f.name}: unexpected CREATE TABLE statement",
            )
            # gate 5 self-verify: 0 quoted CREATE TABLE
            self.assertEqual(
                0,
                len(re.findall(r'CREATE TABLE "', sql)),
            )

    def test_every_catalog_query_has_order_by(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            for m in re.finditer(
                r"(?is)SELECT\s[^;]*?FROM\s+"
                r"(?:pg_catalog|information_schema)\.\S+[^;]*;",
                sql,
            ):
                self.assertIn("ORDER BY", m.group(0).upper())

    def test_every_catalog_select_ends_order_by_count_limit_1(
        self,
    ) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            for stmt in re.findall(
                r"(?is)SELECT\s[^;]*?FROM\s+pg_catalog[^;]*;",
                sql,
            ):
                self.assertTrue(
                    stmt.rstrip().endswith(
                        "ORDER BY count(*) LIMIT 1;"
                    ),
                    msg=f"{f.name}: catalog SELECT missing ORDER BY gate",
                )

    def test_primary_target_is_import_foreign_schema(
        self,
    ) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            region = sql.split(
                "-- primary-target-begin", 1
            )[1]
            region = region.split(
                "-- primary-target-end", 1
            )[0]
            self.assertRegex(
                region,
                r"(?im)^IMPORT\s+FOREIGN\s+SCHEMA\b",
            )

    def test_witness_resolves(self) -> None:
        from src.pg_case_factory.import_foreign_schema_factor_render import (
            resolve_import_foreign_schema_factor_witness,
        )
        for case in self.baseline.cases[:3]:
            w = resolve_import_foreign_schema_factor_witness(
                case, _REPO
            )
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_deterministic_render(self) -> None:
        for case in self.baseline.cases[:5]:
            a = render_import_foreign_schema_factor_case(case, _REPO)
            b = render_import_foreign_schema_factor_case(case, _REPO)
            self.assertEqual(a, b)

    def test_header_fields(self) -> None:
        sql = (
            self.out / "IMPORTFOREIGNSCHEMA00001.sql"
        ).read_text()
        self.assertIn(
            "-- case_id: IMPORTFOREIGNSCHEMA00001", sql
        )
        self.assertIn("-- source_md:", sql)
        self.assertIn("-- factor_md:", sql)
        self.assertIn("-- primary_obligation_id:", sql)
        self.assertIn("-- expected_outcome:", sql)
        self.assertIn("-- expected_sqlstate:", sql)

    def test_cleanup_section(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn("-- 5. 清理全部本编号对象。", sql)

    def test_no_placeholder_leakage(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertNotIn("{", sql)
            self.assertNotIn("}", sql)

    def test_on_error_stop_management(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn("\\set ON_ERROR_STOP on", sql)

    def test_boundary_select(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn("SELECT 1 AS setup_boundary;", sql)

    def test_style_validator_passes(self) -> None:
        # gate 3: regress output script style on the generated leaf.
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_pgcf_importfs_style_validator", _STYLE_VALIDATOR
        )
        module = importlib.util.module_from_spec(spec)
        import sys

        sys.modules["_pgcf_importfs_style_validator"] = module
        spec.loader.exec_module(module)
        _, issues = module.validate_directory(
            self.out, "IMPORTFOREIGNSCHEMA"
        )
        self.assertEqual(
            [],
            [i.message for i in issues],
            msg="; ".join(i.message for i in issues),
        )


if __name__ == "__main__":
    unittest.main()
