"""Tests for set_role factor render module."""

import re
import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.set_role_factor_extension import (
    build_set_role_factor_extension_plan,
)
from src.pg_case_factory.set_role_factor_loop import (
    build_set_role_factor_loop_plan,
)
from src.pg_case_factory.set_role_factor_render import (
    count_primary_set_role,
    generate_set_role_factor_programs,
    render_set_role_factor_case,
)

_REPO = Path(__file__).resolve().parents[1]


class TestSetRoleFactorRender(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_set_role_factor_loop_plan(_REPO)
        self.extension = build_set_role_factor_extension_plan(
            _REPO
        )
        self.out = Path(tempfile.mkdtemp())
        self.count = generate_set_role_factor_programs(
            self.baseline, self.extension, self.out
        )

    def test_file_count(self) -> None:
        self.assertEqual(5675, self.count)

    def test_filename_numbering(self) -> None:
        files = sorted(f.name for f in self.out.iterdir())
        self.assertEqual(
            [f"SETROLE{i:05d}.sql" for i in range(1, 5676)],
            files,
        )

    def test_one_primary_target_per_file(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertEqual(1, count_primary_set_role(sql))

    def test_no_create_drop_table(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertNotRegex(sql, r"(?im)CREATE\s+TABLE")
            self.assertNotRegex(sql, r"(?im)DROP\s+TABLE")

    def test_every_catalog_query_has_order_by(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            for m in re.finditer(
                r"(?is)SELECT\s[^;]*?FROM\s+"
                r"(?:pg_catalog|information_schema)\.\S+[^;]*;",
                sql,
            ):
                self.assertIn("ORDER BY", m.group(0).upper())

    def test_primary_target_is_set_role(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            region = sql.split(
                "-- primary-target-begin", 1
            )[1]
            region = region.split(
                "-- primary-target-end", 1
            )[0]
            self.assertRegex(region, r"(?im)^\s*SET\s+ROLE\b")

    def test_col0_keyword_regex(self) -> None:
        rx = re.compile(r"(?m)^SET\s+ROLE(?:\s|;|$)")
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            region = sql.split(
                "-- primary-target-begin", 1
            )[1]
            region = region.split(
                "-- primary-target-end", 1
            )[0]
            self.assertTrue(rx.search(region))

    def test_witness_resolves(self) -> None:
        from src.pg_case_factory.set_role_factor_render import (
            resolve_set_role_factor_witness,
        )
        for case in self.baseline.cases[:3]:
            w = resolve_set_role_factor_witness(case, _REPO)
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_deterministic_render(self) -> None:
        for case in self.baseline.cases[:5]:
            a = render_set_role_factor_case(case, _REPO)
            b = render_set_role_factor_case(case, _REPO)
            self.assertEqual(a, b)

    def test_header_fields(self) -> None:
        sql = (self.out / "SETROLE00001.sql").read_text()
        self.assertIn("-- case_id: SETROLE00001", sql)
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

    def test_sqlstate_echo(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn(
                "\\echo PGCF_TARGET_SQLSTATE=:target_sqlstate",
                sql,
            )


if __name__ == "__main__":
    unittest.main()
