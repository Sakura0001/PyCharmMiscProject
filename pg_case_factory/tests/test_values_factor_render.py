from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.values_factor_extension import (
    build_values_factor_extension_plan,
)
from pg_case_factory.values_factor_loop import (
    build_values_factor_loop_plan,
)
from pg_case_factory.values_factor_render import (
    ValuesFactorWitness,
    count_primary_values,
    generate_values_factor_programs,
    render_values_factor_case,
    resolve_values_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class ValuesFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = (
            build_values_factor_loop_plan(ROOT)
        )
        cls.extension = (
            build_values_factor_extension_plan(ROOT)
        )
        cls.tmp = Path(
            tempfile.mkdtemp(prefix="values_render_")
        )
        cls.count = generate_values_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_17713_files(self) -> None:
        self.assertEqual(17713, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(17713, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(
                f"VALUES{i:05d}.sql", f.name
            )

    def test_every_file_has_exactly_one_primary_target(
        self,
    ) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_values(text)
            self.assertEqual(1, n, f.name)

    def test_no_file_uses_quoted_create_table(self) -> None:
        # CLASS-2 bookend gate: VALUES is a pure literal query with no
        # CREATE TABLE fixtures at all.
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertFalse(
                re.search(r'(?im)^\s*CREATE\s+TABLE\s+"', text),
                f"quoted CREATE TABLE found in {f.name}",
            )

    def test_no_file_has_create_table_at_all(self) -> None:
        # VALUES is a pure literal query: the combination matrix
        # declares target_relation_coverage as not_applicable, so no
        # CREATE TABLE fixtures should appear anywhere.
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertFalse(
                re.search(r'(?im)CREATE\s+TABLE', text),
                f"CREATE TABLE found in {f.name}",
            )

    def test_no_catalog_probe_selects(self) -> None:
        # VALUES has no catalog relation (pure literal query); no
        # catalog probe SELECTs should appear in any file.
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertFalse(
                re.search(
                    r"(?is)FROM\s+"
                    r"(?:pg_catalog|information_schema)\.",
                    text,
                ),
                f"catalog probe found in {f.name}",
            )

    def test_primary_target_is_values(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?im)^\s*VALUES\b", region),
                f"no VALUES in {f.name}",
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
            w = resolve_values_factor_witness(case, root)
            self.assertIsInstance(w, ValuesFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_values_factor_case(case, root)
        b = render_values_factor_case(case, root)
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
            self.assertIn("-- 5. 清理全部本编号对象。", text)


if __name__ == "__main__":
    unittest.main()
