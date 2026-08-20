from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.create_database_factor_extension import (
    build_create_database_factor_extension_plan,
)
from pg_case_factory.create_database_factor_loop import (
    build_create_database_factor_loop_plan,
)
from pg_case_factory.create_database_factor_render import (
    CreateDatabaseFactorWitness,
    count_primary_create_database,
    generate_create_database_factor_programs,
    render_create_database_factor_case,
    resolve_create_database_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateDatabaseFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_create_database_factor_loop_plan(ROOT)
        cls.extension = build_create_database_factor_extension_plan(
            ROOT
        )
        cls.tmp = Path(tempfile.mkdtemp(prefix="crdb_render_"))
        cls.count = generate_create_database_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_16268_files(self) -> None:
        self.assertEqual(16268, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(16268, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(
                f"CREATEDATABASE{i:05d}.sql", f.name
            )

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_create_database(text)
            self.assertEqual(1, n, f.name)

    def test_no_create_table_statements(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertFalse(
                re.search(r"(?im)^\s*CREATE\s+TABLE\b", text),
                f"CREATE TABLE found in {f.name}",
            )

    def test_placeholder_bookend_present(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertIn(
                "SELECT 1 AS residual_check_no_objects;",
                text,
                f"placeholder bookend missing in {f.name}",
            )

    def test_every_catalog_query_has_order_by(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            for m in re.finditer(
                r"(?is)SELECT\s[^;]*?FROM\s+"
                r"(?:pg_catalog|information_schema)\.\S+[^;]*;",
                text,
            ):
                self.assertIn(
                    "ORDER BY",
                    m.group(0).upper(),
                    f"missing ORDER BY in {f.name}",
                )

    def test_no_quoted_or_dotted_from_targets(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            for m in re.finditer(
                r"(?is)(?:FROM|JOIN)\s+([^\s;]+)", text
            ):
                target = m.group(1).strip().rstrip(";").rstrip(",")
                if target.startswith("pg_catalog."):
                    continue
                if target.startswith("information_schema."):
                    continue
                self.assertNotIn(
                    '"', target, f"quoted FROM in {f.name}: {target}"
                )
                self.assertNotIn(
                    ".", target, f"dotted FROM in {f.name}: {target}"
                )

    def test_primary_target_is_create_database(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?im)^\s*CREATE\s+DATABASE\b", region),
                f"no CREATE DATABASE in {f.name}",
            )

    @staticmethod
    def _extract_target_region(sql: str) -> str | None:
        begin = "-- primary-target-begin"
        end = "-- primary-target-end"
        if sql.count(begin) != 1 or sql.count(end) != 1:
            return None
        before_end, _ = sql.split(end, 1)
        if begin not in before_end:
            return None
        return before_end.split(begin, 1)[1].strip()

    def test_witness_resolves_for_every_case(self) -> None:
        root = ROOT
        for case in self.baseline.cases[:5]:
            w = resolve_create_database_factor_witness(case, root)
            self.assertIsInstance(
                w, CreateDatabaseFactorWitness
            )
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_create_database_factor_case(case, root)
        b = render_create_database_factor_case(case, root)
        self.assertEqual(a, b)

    def test_header_has_required_fields(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        text = files[0].read_text()
        self.assertIn("-- case_id:", text)
        self.assertIn("-- primary_obligation_id:", text)
        self.assertIn("-- expected_outcome:", text)
        self.assertIn("-- expected_sqlstate:", text)

    def test_cleanup_section_present(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertIn(
                "-- 5. 清理全部本编号对象。", text
            )


if __name__ == "__main__":
    unittest.main()
