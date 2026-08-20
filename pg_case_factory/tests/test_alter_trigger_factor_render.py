from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.alter_trigger_factor_extension import (
    build_alter_trigger_factor_extension_plan,
)
from pg_case_factory.alter_trigger_factor_loop import (
    build_alter_trigger_factor_loop_plan,
)
from pg_case_factory.alter_trigger_factor_render import (
    AlterTriggerFactorWitness,
    count_primary_alter_trigger,
    generate_alter_trigger_factor_programs,
    render_alter_trigger_factor_case,
    resolve_alter_trigger_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterTriggerFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_alter_trigger_factor_loop_plan(ROOT)
        cls.extension = build_alter_trigger_factor_extension_plan(
            ROOT
        )
        cls.tmp = Path(tempfile.mkdtemp(prefix="atrig_render_"))
        cls.count = generate_alter_trigger_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_3067_files(self) -> None:
        self.assertEqual(3067, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(3067, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(
                f"ALTERTRIGGER{i:05d}.sql", f.name
            )

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_alter_trigger(text)
            self.assertEqual(1, n, f.name)

    def test_every_file_has_bookend_drop_table(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            stmts = [
                s.strip()
                for s in re.split(
                    r";\s*(?:\n|$)", text
                )
                if s.strip()
            ]
            self.assertTrue(stmts, f"no stmts in {f.name}")

            def _first_executable(stmt: str) -> str:
                for line in stmt.splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith(
                        ("--", "\\")
                    ):
                        return stripped
                return stmt.strip()[:80]

            first = _first_executable(stmts[0])
            self.assertTrue(
                re.match(
                    r"(?i)^DROP\s+TABLE\s+IF\s+EXISTS\b",
                    first,
                ),
                f"first stmt not DROP TABLE in {f.name}: {first}",
            )
            last = _first_executable(stmts[-1])
            self.assertTrue(
                re.match(
                    r"(?i)^DROP\s+TABLE\s+IF\s+EXISTS\b",
                    last,
                ),
                f"last stmt not DROP TABLE in {f.name}: {last}",
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

    def test_primary_target_is_alter_trigger(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(
                    r"(?im)^\s*ALTER\s+TRIGGER\b", region
                ),
                f"no ALTER TRIGGER in {f.name}",
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
            w = resolve_alter_trigger_factor_witness(case, root)
            self.assertIsInstance(
                w, AlterTriggerFactorWitness
            )
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_alter_trigger_factor_case(case, root)
        b = render_alter_trigger_factor_case(case, root)
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
            self.assertIn(
                "-- 5. 清理全部本编号对象。", text
            )


if __name__ == "__main__":
    unittest.main()
