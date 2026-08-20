"""Tests for create_view factor render module."""

import re
import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.create_view_factor_extension import (
    build_create_view_factor_extension_plan,
)
from src.pg_case_factory.create_view_factor_loop import (
    build_create_view_factor_loop_plan,
)
from src.pg_case_factory.create_view_factor_render import (
    count_primary_create_view,
    generate_create_view_factor_programs,
    render_create_view_factor_case,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateViewFactorRender(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = (
            build_create_view_factor_loop_plan(_REPO)
        )
        self.extension = (
            build_create_view_factor_extension_plan(_REPO)
        )
        self.out = Path(tempfile.mkdtemp())
        self.count = (
            generate_create_view_factor_programs(
                self.baseline, self.extension, self.out
            )
        )

    def test_file_count(self) -> None:
        self.assertEqual(5543, self.count)

    def test_filename_numbering(self) -> None:
        files = sorted(f.name for f in self.out.iterdir())
        self.assertEqual(
            [
                f"CREATEVIEW{i:05d}.sql"
                for i in range(1, 5544)
            ],
            files,
        )

    def test_one_primary_target_per_file(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertEqual(
                1, count_primary_create_view(sql)
            )

    def test_create_table_not_in_primary_target(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            before_end, _ = sql.split(
                "-- primary-target-end", 1
            )
            region = before_end.split(
                "-- primary-target-begin", 1
            )[1]
            self.assertNotRegex(
                region, r"(?im)CREATE\s+TABLE"
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

    def test_primary_target_is_create_view(self) -> None:
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
                r"(?im)^CREATE\s+(?:OR\s+REPLACE\s+)?"
                r"(?:TEMP(?:ORARY)?\s+)?"
                r"(?:RECURSIVE\s+)?VIEW\b",
            )

    def test_or_replace_appears(self) -> None:
        found = False
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            region = sql.split(
                "-- primary-target-begin", 1
            )[1]
            region = region.split(
                "-- primary-target-end", 1
            )[0]
            if re.search(
                r"(?m)^CREATE\s+OR\s+REPLACE\s+VIEW",
                region,
            ):
                found = True
                break
        self.assertTrue(found)

    def test_temp_temporary_appears(self) -> None:
        found_temp = False
        found_temporary = False
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            region = sql.split(
                "-- primary-target-begin", 1
            )[1]
            region = region.split(
                "-- primary-target-end", 1
            )[0]
            if re.search(
                r"(?m)^CREATE\s+TEMP\s+VIEW", region
            ):
                found_temp = True
            if re.search(
                r"(?m)^CREATE\s+TEMPORARY\s+VIEW",
                region,
            ):
                found_temporary = True
        self.assertTrue(found_temp)
        self.assertTrue(found_temporary)

    def test_witness_resolves(self) -> None:
        from src.pg_case_factory.create_view_factor_render import (
            resolve_create_view_factor_witness,
        )
        for case in self.baseline.cases[:3]:
            w = resolve_create_view_factor_witness(
                case, _REPO
            )
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_deterministic_render(self) -> None:
        for case in self.baseline.cases[:5]:
            a = render_create_view_factor_case(
                case, _REPO
            )
            b = render_create_view_factor_case(
                case, _REPO
            )
            self.assertEqual(a, b)

    def test_header_fields(self) -> None:
        sql = (
            self.out / "CREATEVIEW00001.sql"
        ).read_text()
        self.assertIn(
            "-- case_id: CREATEVIEW00001", sql
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


if __name__ == "__main__":
    unittest.main()
