from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.alter_type_factor_extension import (
    build_alter_type_factor_extension_plan,
)
from pg_case_factory.alter_type_factor_loop import (
    build_alter_type_factor_loop_plan,
)
from pg_case_factory.alter_type_factor_render import (
    AlterTypeFactorWitness,
    count_primary_alter_type,
    generate_alter_type_factor_programs,
    render_alter_type_factor_case,
    resolve_alter_type_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


def _sql_statements(sql: str) -> list[str]:
    """Return executable ``;``-statements with comments/meta stripped."""

    stmts: list[str] = []
    for chunk in sql.split(";"):
        lines = [
            ln
            for ln in chunk.split("\n")
            if ln.strip()
            and not ln.strip().startswith("--")
            and not ln.strip().startswith("\\")
        ]
        body = "\n".join(lines).strip()
        if body:
            stmts.append(body)
    return stmts


class AlterTypeFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_alter_type_factor_loop_plan(ROOT)
        cls.extension = build_alter_type_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="atype_render_"))
        cls.count = generate_alter_type_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_10522_files(self) -> None:
        self.assertEqual(10522, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(10522, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(
                f"ALTERTYPE{i:05d}.sql", f.name
            )

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_alter_type(text)
            self.assertEqual(1, n, f.name)

    def test_bookend_for_table_creating_cases(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        table_files = 0
        for f in files:
            text = f.read_text()
            if not re.search(
                r"(?im)^\s*CREATE\s+TABLE\b", text
            ):
                continue
            table_files += 1
            stmts = _sql_statements(text)
            self.assertGreaterEqual(
                len(stmts), 2, f"too few statements in {f.name}"
            )
            self.assertRegex(
                stmts[0],
                r"(?im)^DROP\s+TABLE\s+IF\s+EXISTS\b",
                f"first stmt not DROP TABLE in {f.name}",
            )
            self.assertRegex(
                stmts[-1],
                r"(?im)^DROP\s+TABLE\s+IF\s+EXISTS\b",
                f"last stmt not DROP TABLE in {f.name}",
            )
        self.assertGreater(table_files, 0, "no typed-table cases")

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

    def test_no_non_pg_quoted_or_dotted_from_targets(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            for m in re.finditer(
                r"(?im)\bFROM\s+(\S+)", text
            ):
                target = m.group(1).rstrip(",")
                if target.lower().startswith(
                    ("pg_catalog.", "pg_catalog", "information_schema.")
                ) or target.startswith("("):
                    continue
                self.assertFalse(
                    '"' in target or "." in target,
                    f"quoted/dotted FROM target {target} in {f.name}",
                )

    def test_primary_target_is_alter_type(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(r"(?im)^\s*ALTER\s+TYPE\b", region),
                f"no ALTER TYPE in {f.name}",
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
            w = resolve_alter_type_factor_witness(case, root)
            self.assertIsInstance(w, AlterTypeFactorWitness)
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_alter_type_factor_case(case, root)
        b = render_alter_type_factor_case(case, root)
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
