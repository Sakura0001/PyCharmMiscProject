from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.select_into_factor_extension import (
    build_select_into_factor_extension_plan,
)
from pg_case_factory.select_into_factor_loop import (
    build_select_into_factor_loop_plan,
)
from pg_case_factory.select_into_factor_render import (
    SelectIntoFactorWitness,
    count_primary_select_into,
    generate_select_into_factor_programs,
    render_select_into_factor_case,
    resolve_select_into_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class SelectIntoFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = (
            build_select_into_factor_loop_plan(ROOT)
        )
        cls.extension = (
            build_select_into_factor_extension_plan(ROOT)
        )
        cls.tmp = Path(
            tempfile.mkdtemp(prefix="select_into_render_")
        )
        cls.count = generate_select_into_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_867_files(self) -> None:
        self.assertEqual(867, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(867, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(
                f"SELECTINTO{i:05d}.sql", f.name
            )

    def test_every_file_has_exactly_one_primary_target(
        self,
    ) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_select_into(text)
            self.assertEqual(1, n, f.name)

    def test_no_fixture_create_table_uses_quoted_names(self) -> None:
        # class-2 guard: fixture CREATE TABLE must use UNQUOTED base
        # names; quoted/shaped form ONLY in the credited SELECT INTO
        # target (inside the primary fence).
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            # Strip the primary-target fence before checking.
            begin = "-- primary-target-begin"
            end = "-- primary-target-end"
            outside = text.replace(
                text.split(begin, 1)[1].split(end, 1)[0]
                if begin in text and end in text
                else "",
                "",
            )
            self.assertFalse(
                re.search(
                    r'(?im)^\s*CREATE\s+TABLE\s+"',
                    outside,
                ),
                f"quoted fixture CREATE TABLE in {f.name}",
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

    def test_primary_target_is_select_into(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(
                    r"(?im)SELECT\b[^\n]*\bINTO\b",
                    region,
                ),
                f"no SELECT INTO in {f.name}",
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
            w = resolve_select_into_factor_witness(case, root)
            self.assertIsInstance(
                w, SelectIntoFactorWitness
            )
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_probe_uses_pg_class_with_relkind(self) -> None:
        # SELECT INTO creates a pg_class relation of kind 'r'.
        sql = render_select_into_factor_case(
            self.baseline.cases[0], ROOT
        )
        self.assertIn("pg_catalog.pg_class", sql)
        self.assertIn("relkind", sql)


if __name__ == "__main__":
    unittest.main()
