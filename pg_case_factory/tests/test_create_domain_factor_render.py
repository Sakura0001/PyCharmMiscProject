from __future__ import annotations

from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.create_domain_factor_extension import (
    build_create_domain_factor_extension_plan,
)
from pg_case_factory.create_domain_factor_loop import (
    build_create_domain_factor_loop_plan,
)
from pg_case_factory.create_domain_factor_render import (
    CreateDomainFactorWitness,
    count_primary_create_domain,
    generate_create_domain_factor_programs,
    render_create_domain_factor_case,
    resolve_create_domain_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateDomainFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_create_domain_factor_loop_plan(ROOT)
        cls.extension = build_create_domain_factor_extension_plan(
            ROOT
        )
        cls.tmp = Path(tempfile.mkdtemp(prefix="cdom_render_"))
        cls.count = generate_create_domain_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_2977_files(self) -> None:
        self.assertEqual(2977, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(2977, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for i, f in enumerate(files, start=1):
            self.assertEqual(
                f"CREATEDOMAIN{i:05d}.sql", f.name
            )

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            n = count_primary_create_domain(text)
            self.assertEqual(1, n, f.name)

    def test_table_less_no_create_or_drop_table(self) -> None:
        """CREATE DOMAIN is type-defining DDL: never creates a TABLE."""

        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            self.assertFalse(
                re.search(r"(?im)^\s*CREATE\s+TABLE\b", text),
                f"unexpected CREATE TABLE in {f.name}",
            )
            self.assertFalse(
                re.search(r"(?im)^\s*DROP\s+TABLE\b", text),
                f"unexpected DROP TABLE in {f.name}",
            )

    def test_placeholder_present_when_no_cleanup_objects(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        found_placeholder = False
        for f in files:
            text = f.read_text()
            if "residual_check_no_objects" in text:
                found_placeholder = True
                break
        self.assertTrue(
            found_placeholder,
            "no file uses the table-less residual placeholder",
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

    def test_no_quoted_or_dotted_from_targets(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            for m in re.finditer(
                r"(?is)(?:FROM|JOIN)\s+([^\s;]+)", text
            ):
                target = m.group(1).strip().rstrip(";").rstrip(",")
                if target.startswith("pg_catalog."):
                    continue
                if target.startswith("information_schema."):
                    continue
                self.assertNotIn(
                    '"', target, f"quoted FROM in {f.name}: {target}"
                )
                self.assertNotIn(
                    ".", target, f"dotted FROM in {f.name}: {target}"
                )

    def test_primary_target_is_create_domain_at_col0(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        for f in files:
            text = f.read_text()
            region = self._extract_target_region(text)
            self.assertIsNotNone(region, f.name)
            self.assertTrue(
                re.search(
                    r"(?im)^CREATE\s+DOMAIN\b", region
                ),
                f"no CREATE DOMAIN at col 0 in {f.name}",
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
            w = resolve_create_domain_factor_witness(case, root)
            self.assertIsInstance(
                w, CreateDomainFactorWitness
            )
            self.assertTrue(w.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        root = ROOT
        case = self.baseline.cases[0]
        a = render_create_domain_factor_case(case, root)
        b = render_create_domain_factor_case(case, root)
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
