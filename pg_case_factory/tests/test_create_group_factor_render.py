"""Tests for create_group factor render module."""

import re
import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.create_group_factor_extension import (
    build_create_group_factor_extension_plan,
)
from src.pg_case_factory.create_group_factor_loop import (
    build_create_group_factor_loop_plan,
)
from src.pg_case_factory.create_group_factor_render import (
    count_primary_create_group,
    generate_create_group_factor_programs,
    render_create_group_factor_case,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateGroupFactorRender(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_create_group_factor_loop_plan(_REPO)
        self.extension = build_create_group_factor_extension_plan(_REPO)
        self.out = Path(tempfile.mkdtemp())
        self.count = generate_create_group_factor_programs(
            self.baseline, self.extension, self.out
        )

    def test_file_count(self) -> None:
        self.assertEqual(426, self.count)

    def test_filename_numbering(self) -> None:
        files = sorted(f.name for f in self.out.iterdir())
        self.assertEqual(
            [f"CREATEGROUP{i:05d}.sql" for i in range(1, 427)],
            files,
        )

    def test_one_primary_target_per_file(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertEqual(1, count_primary_create_group(sql))

    def test_no_create_drop_table(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertNotRegex(sql, r"(?im)CREATE\s+TABLE")
            self.assertNotRegex(sql, r"(?im)DROP\s+TABLE")

    def test_every_catalog_query_has_order_by(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            for m in re.finditer(
                r"(?is)SELECT\s[^;]*?FROM\s+(?:pg_catalog|information_schema)\.\S+[^;]*;",
                sql,
            ):
                self.assertIn("ORDER BY", m.group(0).upper())

    def test_primary_target_is_create_group(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            region = sql.split("-- primary-target-begin", 1)[1]
            region = region.split("-- primary-target-end", 1)[0]
            self.assertRegex(region, r"(?im)CREATE\s+GROUP\b")

    def test_witness_resolves(self) -> None:
        from src.pg_case_factory.create_group_factor_render import (
            resolve_create_group_factor_witness,
        )
        for case in self.baseline.cases[:3]:
            w = resolve_create_group_factor_witness(case, _REPO)
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_deterministic_render(self) -> None:
        for case in self.baseline.cases[:5]:
            a = render_create_group_factor_case(case, _REPO)
            b = render_create_group_factor_case(case, _REPO)
            self.assertEqual(a, b)

    def test_header_fields(self) -> None:
        sql = (self.out / "CREATEGROUP00001.sql").read_text()
        self.assertIn("-- case_id: CREATEGROUP00001", sql)
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

    def test_residual_placeholder(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn("SELECT 1 AS residual_check_no_objects;", sql)

    def test_setup_boundary(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn("SELECT 1 AS setup_boundary;", sql)


if __name__ == "__main__":
    unittest.main()
