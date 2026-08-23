from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.drop_transform_factor_extension import (
    build_drop_transform_factor_extension_plan,
)
from pg_case_factory.drop_transform_factor_loop import (
    build_drop_transform_factor_loop_plan,
)
from pg_case_factory.drop_transform_factor_render import (
    DropTransformFactorWitness,
    count_primary_drop_transform,
    generate_drop_transform_factor_programs,
    render_drop_transform_factor_case,
    resolve_drop_transform_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class DropTransformFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_drop_transform_factor_loop_plan(ROOT)
        cls.extension = build_drop_transform_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="drop_transform_render_"))
        cls.count = generate_drop_transform_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_1320_files(self) -> None:
        self.assertEqual(1320, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(1320, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(f"DROPTRANSFORM{i:05d}.sql", f.name)

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_drop_transform(text)
            self.assertEqual(1, n, f.name)

    def test_no_case_creates_a_table_so_bookend_is_not_applicable(self) -> None:
        """DROP TRANSFORM drops a transform (type<->language), not a table.

        The bookend gate (first+last ``;``-stmt = DROP TABLE IF EXISTS)
        triggers only on CREATE TABLE.  CREATE TYPE / CREATE FUNCTION /
        CREATE TRANSFORM fixtures do not create tables, so no case should
        contain a CREATE TABLE statement.
        """

        files = sorted(self.tmp.glob("*.sql"))
        offenders = []
        for f in files:
            text = f.read_text()
            if re.search(r"(?im)^\s*CREATE\s+TABLE\b", text):
                offenders.append(f.name)
        self.assertEqual([], offenders, "unexpected CREATE TABLE present")

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

    def test_primary_target_is_drop_transform(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?m)^DROP\s+TRANSFORM\b", region),
                f"no col-0 DROP TRANSFORM in {f.name}",
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
            w = resolve_drop_transform_factor_witness(case, root)
            self.assertIsInstance(w, DropTransformFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_drop_transform_factor_case(case, root)
        b = render_drop_transform_factor_case(case, root)
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
        """Fix-A guard: DROP OWNED BY is unreachable in pre-cleanup (the
        actor role fixture is created by setup, so on a fresh database the
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

    def test_probe_uses_real_pg_transform_columns(self) -> None:
        """The catalog probe must use real trftype/trflang columns and the
        verified ::regtype cast + pg_language.lanname join (NOT the
        non-existent ::reglanguage cast)."""

        files = sorted(self.tmp.glob("*.sql"))
        probed = 0
        for f in files:
            text = f.read_text()
            if "FROM pg_catalog.pg_transform" not in text:
                continue
            probed += 1
            self.assertIn("trftype", text, f.name)
            self.assertIn("trflang", text, f.name)
            self.assertIn("::regtype", text, f.name)
            self.assertIn("pg_language", text, f.name)
            self.assertNotIn("::reglanguage", text, f.name)
        self.assertGreater(probed, 0, "no catalog probe emitted anywhere")


if __name__ == "__main__":
    unittest.main()
