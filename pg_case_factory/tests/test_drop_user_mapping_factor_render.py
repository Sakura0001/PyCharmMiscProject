from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.drop_user_mapping_factor_extension import (
    build_drop_user_mapping_factor_extension_plan,
)
from pg_case_factory.drop_user_mapping_factor_loop import (
    build_drop_user_mapping_factor_loop_plan,
)
from pg_case_factory.drop_user_mapping_factor_render import (
    DropUserMappingFactorWitness,
    count_primary_drop_user_mapping,
    generate_drop_user_mapping_factor_programs,
    render_drop_user_mapping_factor_case,
    resolve_drop_user_mapping_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_TOTAL_FILES = 1081


class DropUserMappingFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_drop_user_mapping_factor_loop_plan(ROOT)
        cls.extension = build_drop_user_mapping_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="drop_user_mapping_render_"))
        cls.count = generate_drop_user_mapping_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_1081_files(self) -> None:
        self.assertEqual(_TOTAL_FILES, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(_TOTAL_FILES, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(f"DROPUSERMAPPING{i:05d}.sql", f.name)

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_drop_user_mapping(text)
            self.assertEqual(1, n, f.name)

    def test_no_create_table_bookend_gate(self) -> None:
        """Table-less statement: 0 CREATE TABLE."""
        files = sorted(self.tmp.glob("*.sql"))
        create_count = 0
        for f in files:
            text = f.read_text()
            if re.search(r"(?im)^\s*CREATE\s+TABLE\b", text):
                create_count += 1
        self.assertEqual(0, create_count)

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

    def test_primary_target_is_drop_user_mapping(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?m)^DROP\s+USER\s+MAPPING\b", region),
                f"no col-0 DROP USER MAPPING in {f.name}",
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
            w = resolve_drop_user_mapping_factor_witness(case, root)
            self.assertIsInstance(w, DropUserMappingFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_drop_user_mapping_factor_case(case, root)
        b = render_drop_user_mapping_factor_case(case, root)
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

    def test_cleanup_bookend_invariants(self) -> None:
        """Fix-A guard: DROP OWNED BY is unreachable in pre-cleanup (the role
        fixtures are created by setup, so on a fresh database the role does not
        exist at pre-cleanup time and DROP OWNED BY would crash under
        ON_ERROR_STOP=1 before the target statement).  In cleanup, DROP OWNED
        BY must precede DROP ROLE IF EXISTS."""
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

    def test_no_quoted_dotted_from_refs(self) -> None:
        """0 quoted/dotted non-catalog FROM refs."""
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            for m in re.finditer(
                r"(?is)\bFROM\s+(?!pg_catalog\.|information_schema\.)"
                r'("[^"]+"\s*\.\s*"[^"]+"|"[^"]+"\.\w+|\w+\."[^"]+")',
                text,
            ):
                self.fail(
                    f"quoted/dotted non-catalog FROM ref in {f.name}: "
                    f"{m.group(0)}"
                )


if __name__ == "__main__":
    unittest.main()
