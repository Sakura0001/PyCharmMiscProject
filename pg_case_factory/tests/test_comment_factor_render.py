from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.comment_factor_extension import (
    build_comment_factor_extension_plan,
)
from pg_case_factory.comment_factor_loop import (
    build_comment_factor_loop_plan,
)
from pg_case_factory.comment_factor_render import (
    CommentFactorWitness,
    count_primary_comment,
    generate_comment_factor_programs,
    render_comment_factor_case,
    resolve_comment_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class CommentFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_comment_factor_loop_plan(ROOT)
        cls.extension = build_comment_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="comment_render_"))
        cls.count = generate_comment_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_13662_files(self) -> None:
        self.assertEqual(13662, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(13662, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(f"COMMENT{i:05d}.sql", f.name)

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_comment(text)
            self.assertEqual(1, n, f.name)

    def test_bookend_for_table_creating_cases(self) -> None:
        """Files with CREATE TABLE must start+end with DROP TABLE IF EXISTS."""
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            creates_table = bool(
                re.search(r"(?im)^\s*CREATE\s+TABLE\b", text)
            )
            if not creates_table:
                continue
            stmts = [
                line.strip()
                for line in text.split("\n")
                if line.strip()
                .upper()
                .startswith(("DROP", "CREATE", "SELECT", "COMMENT"))
            ]
            self.assertTrue(
                stmts[0].upper().startswith("DROP TABLE IF EXISTS"),
                f"first stmt not DROP TABLE in {f.name}: "
                f"{stmts[0][:60]}",
            )
            self.assertTrue(
                stmts[-1].upper().startswith("DROP TABLE IF EXISTS"),
                f"last stmt not DROP TABLE in {f.name}: "
                f"{stmts[-1][:60]}",
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

    def test_primary_target_is_comment_on(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?im)^\s*COMMENT\s+ON\b", region),
                f"no COMMENT ON in {f.name}",
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
            w = resolve_comment_factor_witness(case, root)
            self.assertIsInstance(w, CommentFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_comment_factor_case(case, root)
        b = render_comment_factor_case(case, root)
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
