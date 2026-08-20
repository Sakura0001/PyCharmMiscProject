from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.explain_factor_extension import (
    build_explain_factor_extension_plan,
)
from pg_case_factory.explain_factor_loop import (
    build_explain_factor_loop_plan,
)
from pg_case_factory.explain_factor_render import (
    ExplainFactorWitness,
    count_primary_explain,
    generate_explain_factor_programs,
    render_explain_factor_case,
    resolve_explain_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class ExplainFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_explain_factor_loop_plan(ROOT)
        cls.extension = build_explain_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="explain_render_"))
        cls.count = generate_explain_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_6672_files(self) -> None:
        self.assertEqual(6672, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(6672, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(f"EXPLAIN{i:05d}.sql", f.name)

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_explain(text)
            self.assertEqual(1, n, f.name)

    def test_every_catalog_query_has_order_by_with_limit_1(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            for m in re.finditer(
                r"(?is)SELECT\s[^;]*?FROM\s+"
                r"(?:pg_catalog|information_schema)\.\S+[^;]*;",
                text,
            ):
                seg = m.group(0).upper()
                self.assertIn(
                    "ORDER BY",
                    seg,
                    f"missing ORDER BY in {f.name}",
                )
                self.assertIn(
                    "LIMIT 1",
                    seg,
                    f"missing LIMIT 1 in {f.name}",
                )

    def test_primary_target_is_explain(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?im)^\s*EXPLAIN\b", region),
                f"no EXPLAIN in {f.name}",
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
            w = resolve_explain_factor_witness(case, root)
            self.assertIsInstance(w, ExplainFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_explain_factor_case(case, root)
        b = render_explain_factor_case(case, root)
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

    def test_bookend_for_table_creating_cases(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            # Filter to executable statements only (no comments, no \meta)
            lines = [
                line for line in text.splitlines()
                if line.strip()
                and not line.strip().startswith("--")
                and not line.strip().startswith("\\")
            ]
            joined = "\n".join(lines)
            stmts = [s.strip() for s in joined.split(";") if s.strip()]
            has_create = bool(
                re.search(r"(?im)CREATE\s+TABLE\b", text)
            )
            if has_create:
                self.assertTrue(
                    stmts[0].startswith("DROP TABLE IF EXISTS"),
                    f"first stmt not DROP TABLE in {f.name}: {stmts[0][:60]}",
                )
                self.assertTrue(
                    stmts[-1].startswith("DROP TABLE IF EXISTS"),
                    f"last stmt not DROP TABLE in {f.name}: {stmts[-1][:60]}",
                )

    def test_no_quoted_create_table_in_rendered_sql(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertFalse(
                re.search(r'(?im)CREATE\s+TABLE\s+"', text),
                f"quoted CREATE TABLE in {f.name}",
            )


if __name__ == "__main__":
    unittest.main()
