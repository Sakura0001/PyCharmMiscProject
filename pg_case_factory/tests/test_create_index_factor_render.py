"""Tests for create_index factor render module."""

import re
import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.create_index_factor_extension import (
    build_create_index_factor_extension_plan,
)
from src.pg_case_factory.create_index_factor_loop import (
    build_create_index_factor_loop_plan,
)
from src.pg_case_factory.create_index_factor_render import (
    count_primary_create_index,
    generate_create_index_factor_programs,
    render_create_index_factor_case,
)

_REPO = Path(__file__).resolve().parents[1]


def _statements(sql: str) -> list[str]:
    """Split into ;-terminated statements, skipping comments and \\commands."""
    cleaned = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if stripped.startswith("\\"):
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    stmts = []
    for stmt in text.split(";"):
        s = stmt.strip()
        if s:
            stmts.append(s)
    return stmts


class TestCreateIndexFactorRender(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_create_index_factor_loop_plan(_REPO)
        self.extension = build_create_index_factor_extension_plan(_REPO)
        self.out = Path(tempfile.mkdtemp())
        self.count = generate_create_index_factor_programs(
            self.baseline, self.extension, self.out
        )

    def test_file_count(self) -> None:
        self.assertEqual(2009, self.count)

    def test_filename_numbering(self) -> None:
        files = sorted(f.name for f in self.out.iterdir())
        self.assertEqual(
            [f"CREATEINDEX{i:05d}.sql" for i in range(1, 2010)],
            files,
        )

    def test_one_primary_target_per_file(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertEqual(1, count_primary_create_index(sql))

    def test_fixture_table_created(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertRegex(sql, r"(?im)CREATE\s+TABLE")

    def test_bookend_first_and_last_drop_table(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            stmts = _statements(sql)
            self.assertGreaterEqual(
                len(stmts), 2,
                f"{f.name}: too few statements for bookend",
            )
            first = stmts[0]
            last = stmts[-1]
            self.assertRegex(
                first,
                r"(?im)^DROP\s+TABLE\s+IF\s+EXISTS\b",
                f"{f.name}: first stmt is not DROP TABLE: {first}",
            )
            self.assertRegex(
                last,
                r"(?im)^DROP\s+TABLE\s+IF\s+EXISTS\b",
                f"{f.name}: last stmt is not DROP TABLE: {last}",
            )

    def test_every_catalog_query_has_order_by(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            for m in re.finditer(
                r"(?is)SELECT\s[^;]*?FROM\s+(?:pg_catalog|information_schema)\.\S+[^;]*;",
                sql,
            ):
                self.assertIn("ORDER BY", m.group(0).upper())

    def test_primary_target_is_create_index(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            region = sql.split("-- primary-target-begin", 1)[1]
            region = region.split("-- primary-target-end", 1)[0]
            self.assertRegex(region, r"(?im)CREATE\s+(?:UNIQUE\s+)?INDEX\b")

    def test_witness_resolves(self) -> None:
        from src.pg_case_factory.create_index_factor_render import (
            resolve_create_index_factor_witness,
        )
        for case in self.baseline.cases[:3]:
            w = resolve_create_index_factor_witness(case, _REPO)
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_deterministic_render(self) -> None:
        for case in self.baseline.cases[:5]:
            a = render_create_index_factor_case(case, _REPO)
            b = render_create_index_factor_case(case, _REPO)
            self.assertEqual(a, b)

    def test_header_fields(self) -> None:
        sql = (self.out / "CREATEINDEX00001.sql").read_text()
        self.assertIn("-- case_id: CREATEINDEX00001", sql)
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

    def test_setup_boundary_select(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn("SELECT 1 AS setup_boundary;", sql)

    def test_target_sqlstate_capture(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn("\\set target_sqlstate :SQLSTATE", sql)
            self.assertIn("PGCF_TARGET_SQLSTATE=", sql)


if __name__ == "__main__":
    unittest.main()
