"""Tests for deallocate factor render module."""

import re
import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.deallocate_factor_extension import (
    build_deallocate_factor_extension_plan,
)
from src.pg_case_factory.deallocate_factor_loop import (
    build_deallocate_factor_loop_plan,
)
from src.pg_case_factory.deallocate_factor_render import (
    count_primary_deallocate,
    generate_deallocate_factor_programs,
    render_deallocate_factor_case,
)

_REPO = Path(__file__).resolve().parents[1]


class TestDeallocateFactorRender(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_deallocate_factor_loop_plan(_REPO)
        self.extension = (
            build_deallocate_factor_extension_plan(_REPO)
        )
        self.out = Path(tempfile.mkdtemp())
        self.count = generate_deallocate_factor_programs(
            self.baseline, self.extension, self.out
        )

    def test_file_count(self) -> None:
        self.assertEqual(7698, self.count)

    def test_filename_numbering(self) -> None:
        files = sorted(f.name for f in self.out.iterdir())
        self.assertEqual(
            [
                f"DEALLOCATE{i:05d}.sql"
                for i in range(1, 7699)
            ],
            files,
        )

    def test_one_primary_target_per_file(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertEqual(
                1, count_primary_deallocate(sql)
            )

    def test_bookend_first_and_last_drop_table(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            lines = sql.strip().split("\n")
            stmts = [
                l.strip()
                for l in lines
                if l.strip().endswith(";")
                and not l.strip().startswith("--")
                and not l.strip().startswith("\\")
            ]
            self.assertTrue(
                stmts[0].startswith("DROP TABLE IF EXISTS"),
                msg=f"{f.name}: first stmt not bookend: {stmts[0]}",
            )
            self.assertTrue(
                stmts[-1].startswith("DROP TABLE IF EXISTS"),
                msg=f"{f.name}: last stmt not bookend: {stmts[-1]}",
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

    def test_primary_target_is_deallocate(
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
                region, r"(?im)^DEALLOCATE(?:\s|;|$)"
            )

    def test_witness_resolves(self) -> None:
        from src.pg_case_factory.deallocate_factor_render import (
            resolve_deallocate_factor_witness,
        )
        for case in self.baseline.cases[:3]:
            w = resolve_deallocate_factor_witness(
                case, _REPO
            )
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_deterministic_render(self) -> None:
        for case in self.baseline.cases[:5]:
            a = render_deallocate_factor_case(case, _REPO)
            b = render_deallocate_factor_case(case, _REPO)
            self.assertEqual(a, b)

    def test_header_fields(self) -> None:
        sql = (
            self.out / "DEALLOCATE00001.sql"
        ).read_text()
        self.assertIn(
            "-- case_id: DEALLOCATE00001", sql
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
