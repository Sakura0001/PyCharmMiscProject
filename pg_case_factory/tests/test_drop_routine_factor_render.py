from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.drop_routine_factor_extension import (
    build_drop_routine_factor_extension_plan,
)
from pg_case_factory.drop_routine_factor_loop import (
    build_drop_routine_factor_loop_plan,
)
from pg_case_factory.drop_routine_factor_render import (
    DropRoutineFactorWitness,
    count_primary_drop_routine,
    generate_drop_routine_factor_programs,
    render_drop_routine_factor_case,
    resolve_drop_routine_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_TOTAL = 4353


class DropRoutineFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_drop_routine_factor_loop_plan(ROOT)
        cls.extension = build_drop_routine_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="drop_routine_render_"))
        cls.count = generate_drop_routine_factor_programs(cls.baseline, cls.extension, cls.tmp)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_4353_files(self) -> None:
        self.assertEqual(_TOTAL, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(_TOTAL, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(f"DROPROUTINE{i:05d}.sql", f.name)

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            self.assertEqual(1, count_primary_drop_routine(f.read_text()), f.name)

    def test_bookend_gate_table_creating_cases(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            text = f.read_text()
            if not re.search(r"(?im)^\s*CREATE\s+TABLE\b", text):
                continue
            stmts = self._executable_statements(text)
            self.assertTrue(stmts, f.name)
            self.assertTrue(re.match(r"(?i)^DROP\s+TABLE\s+IF\s+EXISTS\b", stmts[0]), f.name)
            self.assertTrue(re.match(r"(?i)^DROP\s+TABLE\s+IF\s+EXISTS\b", stmts[-1]), f.name)

    @staticmethod
    def _executable_statements(text: str) -> list[str]:
        text = re.sub(r"--[^\n]*", "", text)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        text = re.sub(r"\\[a-zA-Z]+[^\n]*", "", text)
        return [s.strip() for s in text.split(";") if s.strip()]

    def test_every_catalog_query_has_order_by(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            text = f.read_text()
            for m in re.finditer(
                r"(?is)SELECT\s[^;]*?FROM\s+(?:pg_catalog|information_schema)\.\S+[^;]*;",
                text,
            ):
                self.assertIn("ORDER BY", m.group(0).upper(), f.name)

    def test_primary_target_is_drop_routine(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(re.search(r"(?m)^DROP\s+ROUTINE\b", region), f.name)

    @staticmethod
    def _extract_target_region(sql: str) -> str | None:
        begin, end = "-- primary-target-begin", "-- primary-target-end"
        if sql.count(begin) != 1 or sql.count(end) != 1:
            return None
        before_end, _ = sql.split(end, 1)
        if begin not in before_end:
            return None
        return before_end.split(begin, 1)[1].strip()

    def test_witness_resolves_for_every_case(self) -> None:
        for case in self.baseline.cases[:5]:
            w = resolve_drop_routine_factor_witness(case, ROOT)
            self.assertIsInstance(w, DropRoutineFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        case = self.baseline.cases[0]
        a = render_drop_routine_factor_case(case, ROOT)
        b = render_drop_routine_factor_case(case, ROOT)
        self.assertEqual(a, b)

    def test_header_has_required_fields(self) -> None:
        text = sorted(self.tmp.glob("*.sql"))[0].read_text()
        self.assertIn("-- case_id:", text)
        self.assertIn("-- primary_obligation_id:", text)
        self.assertIn("-- expected_outcome:", text)
        self.assertIn("-- expected_sqlstate:", text)

    def test_cleanup_section_present(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            self.assertIn("-- 5. 清理全部本编号对象。", f.read_text())

    def test_no_placeholder_leakage(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            text = f.read_text()
            self.assertNotIn("{", text)
            self.assertNotIn("}", text)

    def test_on_error_stop_management(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            self.assertIn("\\set ON_ERROR_STOP on", f.read_text())


if __name__ == "__main__":
    unittest.main()
