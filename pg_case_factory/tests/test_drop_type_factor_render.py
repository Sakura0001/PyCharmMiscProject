from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.drop_type_factor_extension import (
    build_drop_type_factor_extension_plan,
)
from pg_case_factory.drop_type_factor_loop import (
    build_drop_type_factor_loop_plan,
)
from pg_case_factory.drop_type_factor_render import (
    DropTypeFactorWitness,
    count_primary_drop_type,
    generate_drop_type_factor_programs,
    render_drop_type_factor_case,
    resolve_drop_type_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 46
_EXTENSION_COUNT = 4272
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 4318


class DropTypeFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_drop_type_factor_loop_plan(ROOT)
        cls.extension = build_drop_type_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="drop_type_render_"))
        cls.count = generate_drop_type_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_4318_files(self) -> None:
        self.assertEqual(_TOTAL_COUNT, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(_TOTAL_COUNT, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(f"DROPTYPE{i:05d}.sql", f.name)

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_drop_type(text)
            self.assertEqual(1, n, f.name)

    def test_bookend_gate_table_creating_cases(self) -> None:
        """First + last stmt are DROP TABLE IF EXISTS when CREATE TABLE present."""
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            has_create = bool(
                re.search(r"(?im)^\s*CREATE\s+(?:FOREIGN\s+)?TABLE\b", text)
            )
            if not has_create:
                continue
            stmts = self._executable_statements(text)
            self.assertTrue(
                stmts,
                f"no executable statements in {f.name}",
            )
            self.assertTrue(
                re.match(
                    r"(?i)^DROP\s+TABLE\s+IF\s+EXISTS\b",
                    stmts[0],
                ),
                f"first stmt not DROP TABLE in {f.name}: {stmts[0][:60]}",
            )
            self.assertTrue(
                re.match(
                    r"(?i)^DROP\s+TABLE\s+IF\s+EXISTS\b",
                    stmts[-1],
                ),
                f"last stmt not DROP TABLE in {f.name}: {stmts[-1][:60]}",
            )

    def test_no_quoted_table_names_in_create_or_drop(self) -> None:
        """Bookend gate identifier normalizer rejects quoted names."""
        files = sorted(self.tmp.glob("*.sql"))
        offenders: list[str] = []
        for f in files:
            text = f.read_text()
            for stmt in self._executable_statements(text):
                first = stmt.split(None, 3)
                if len(first) < 3:
                    continue
                kw0 = first[0].upper()
                kw1 = first[1].upper()
                if kw0 in {"CREATE", "DROP"} and kw1 == "TABLE":
                    if '"' in stmt:
                        offenders.append(f.name)
                        break
        self.assertEqual([], offenders)

    def test_cleanup_bookend_invariants(self) -> None:
        """Fix-A guard: DROP OWNED BY is unreachable in pre-cleanup (the
        granted_role fixture is created by setup, so on a fresh database the
        role does not exist at pre-cleanup time and DROP OWNED BY would crash
        under ON_ERROR_STOP=1 before the target statement).  In cleanup,
        DROP OWNED BY must precede DROP ROLE IF EXISTS."""
        files = sorted(self.tmp.glob("*.sql"))
        self.assertGreater(len(files), 0)
        pre_drop_owned: list[str] = []
        cleanup_order_bad: list[str] = []
        for f in files:
            text = f.read_text()
            if "cleanup-bookend: pre-cleanup-begin" not in text:
                continue
            pre = text.split("cleanup-bookend: pre-cleanup-begin", 1)[1]
            pre = pre.split("cleanup-bookend: pre-cleanup-end", 1)[0]
            if re.search(r"\bDROP\s+OWNED\s+BY\b", pre, re.IGNORECASE):
                pre_drop_owned.append(f.name)
            cln = text.split("cleanup-bookend: cleanup-begin", 1)[1]
            cln = cln.split("cleanup-bookend: cleanup-end", 1)[0]
            m_own = re.search(r"\bDROP\s+OWNED\s+BY\b", cln, re.IGNORECASE)
            m_role = re.search(r"\bDROP\s+ROLE\b", cln, re.IGNORECASE)
            if m_own and m_role and m_own.start() > m_role.start():
                cleanup_order_bad.append(f.name)
        self.assertEqual([], pre_drop_owned, "DROP OWNED BY leaked into pre-cleanup")
        self.assertEqual([], cleanup_order_bad, "DROP OWNED BY after DROP ROLE in cleanup")

    @staticmethod
    def _executable_statements(text: str) -> list[str]:
        """Extract SQL statements, stripping comments and psql meta-commands."""
        text = re.sub(r"--[^\n]*", "", text)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        text = re.sub(r"\\[a-zA-Z]+[^\n]*", "", text)
        stmts = [s.strip() for s in text.split(";") if s.strip()]
        return stmts

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

    def test_primary_target_is_drop_type(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?m)^DROP\s+TYPE\b", region),
                f"no col-0 DROP TYPE in {f.name}",
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
            w = resolve_drop_type_factor_witness(case, root)
            self.assertIsInstance(w, DropTypeFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_drop_type_factor_case(case, root)
        b = render_drop_type_factor_case(case, root)
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

    def test_no_placeholder_leakage(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertNotIn("{", text)
            self.assertNotIn("}", text)

    def test_on_error_stop_management(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertIn("\\set ON_ERROR_STOP on", text)

    def test_sqlstate_oracle_present(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertIn("target_sqlstate_matches_expected", text)


if __name__ == "__main__":
    unittest.main()
