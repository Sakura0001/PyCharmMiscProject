from __future__ import annotations

from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.create_foreign_table_factor_extension import (
    build_create_foreign_table_factor_extension_plan,
)
from pg_case_factory.create_foreign_table_factor_loop import (
    build_create_foreign_table_factor_loop_plan,
)
from pg_case_factory.create_foreign_table_factor_render import (
    CreateForeignTableFactorWitness,
    count_primary_create_foreign_table,
    generate_create_foreign_table_factor_programs,
    render_create_foreign_table_factor_case,
    resolve_create_foreign_table_factor_witness,
)
from pg_case_factory.regression_style import (
    audit_complete_table_script,
    contains_create_table_statement,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateForeignTableFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_create_foreign_table_factor_loop_plan(ROOT)
        cls.extension = (
            build_create_foreign_table_factor_extension_plan(ROOT)
        )
        cls.tmp = Path(tempfile.mkdtemp(prefix="cft_render_"))
        cls.count = generate_create_foreign_table_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_2556_files(self) -> None:
        self.assertEqual(2556, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(2556, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(
                f"CREATEFOREIGNTABLE{i:05d}.sql", f.name
            )

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_create_foreign_table(text)
            self.assertEqual(1, n, f.name)

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

    def test_no_quoted_identifiers_in_from_or_join(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertFalse(
                re.search(
                    r"(?is)\bFROM\s+\"[^\"]+\"", text
                ),
                f"quoted FROM in {f.name}",
            )
            self.assertFalse(
                re.search(
                    r"(?is)\bJOIN\s+\"[^\"]+\"", text
                ),
                f"quoted JOIN in {f.name}",
            )

    def test_primary_target_is_create_foreign_table(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(
                    r"(?im)^CREATE\s+FOREIGN\s+TABLE(?:\s|;|$)",
                    region,
                ),
                f"no CREATE FOREIGN TABLE in {f.name}",
            )

    def test_table_creating_cases_have_bookend(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            if contains_create_table_statement(text):
                report = audit_complete_table_script(text)
                self.assertFalse(
                    report.issues,
                    f"bookend failure in {f.name}: "
                    f"{report.issues[:2]}",
                )

    def test_table_less_cases_have_no_create_table(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            if not contains_create_table_statement(text):
                self.assertFalse(
                    re.search(
                        r"(?im)^\s*CREATE\s+TABLE\b", text
                    ),
                    f"unexpected CREATE TABLE in {f.name}",
                )

    def test_witness_resolves_for_every_case(self) -> None:
        root = ROOT
        for case in self.baseline.cases[:5]:
            w = resolve_create_foreign_table_factor_witness(
                case, root
            )
            self.assertIsInstance(
                w, CreateForeignTableFactorWitness
            )
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_create_foreign_table_factor_case(case, root)
        b = render_create_foreign_table_factor_case(case, root)
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


if __name__ == "__main__":
    unittest.main()
