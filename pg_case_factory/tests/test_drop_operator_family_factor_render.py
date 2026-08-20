from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.drop_operator_family_factor_extension import (
    build_drop_operator_family_factor_extension_plan,
)
from pg_case_factory.drop_operator_family_factor_loop import (
    build_drop_operator_family_factor_loop_plan,
)
from pg_case_factory.drop_operator_family_factor_render import (
    DropOperatorFamilyFactorWitness,
    count_primary_drop_operator_family,
    generate_drop_operator_family_factor_programs,
    render_drop_operator_family_factor_case,
    resolve_drop_operator_family_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_TOTAL = 2229


class DropOperatorFamilyFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_drop_operator_family_factor_loop_plan(ROOT)
        cls.extension = build_drop_operator_family_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="drop_operator_family_render_"))
        cls.count = generate_drop_operator_family_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_2229_files(self) -> None:
        self.assertEqual(_TOTAL, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(_TOTAL, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(f"DROPOPERATORFAMILY{i:05d}.sql", f.name)

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_drop_operator_family(text)
            self.assertEqual(1, n, f.name)

    def test_bookend_gate_table_creating_cases(self) -> None:
        """First + last stmt are DROP TABLE IF EXISTS when CREATE TABLE present."""
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            has_create = bool(
                re.search(r"(?im)^\s*CREATE\s+TABLE\b", text)
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

    def test_primary_target_is_drop_operator_family(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?m)^DROP\s+OPERATOR\s+FAMILY\b", region),
                f"no col-0 DROP OPERATOR FAMILY in {f.name}",
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
            w = resolve_drop_operator_family_factor_witness(case, root)
            self.assertIsInstance(w, DropOperatorFamilyFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_drop_operator_family_factor_case(case, root)
        b = render_drop_operator_family_factor_case(case, root)
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

    def test_probe_uses_real_pg_opfamily_columns(self) -> None:
        """The catalog probe must reference the real opfname column."""
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            if "pg_catalog.pg_opfamily" not in text:
                continue
            self.assertIn("opfname", text, f"no opfname in {f.name}")
            for bad in ("opname", "oprfamily", "opftype"):
                self.assertNotIn(
                    bad, text, f"bad column {bad} in {f.name}"
                )


if __name__ == "__main__":
    unittest.main()
