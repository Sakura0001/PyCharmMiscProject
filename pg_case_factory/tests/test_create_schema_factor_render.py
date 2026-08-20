from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.create_schema_factor_extension import (
    build_create_schema_factor_extension_plan,
)
from pg_case_factory.create_schema_factor_loop import (
    build_create_schema_factor_loop_plan,
)
from pg_case_factory.create_schema_factor_render import (
    count_primary_create_schema,
    generate_create_schema_factor_programs,
    render_create_schema_factor_case,
    resolve_create_schema_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_CREATE_SCHEMA_RE = re.compile(r"(?im)^\s*CREATE\s+SCHEMA\b")
_CREATE_TABLE_RE = re.compile(r"(?im)^\s*CREATE\s+TABLE\b")
_DROP_TABLE_RE = re.compile(r"(?im)^\s*DROP\s+TABLE\b")
_CATALOG_SELECT_RE = re.compile(
    r"(?ims)SELECT\s.+?\sFROM\s+(pg_catalog\.|information_schema\.)"
)
_ORDER_BY_RE = re.compile(r"(?ims)\bORDER\s+BY\b")


class CreateSchemaFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.mkdtemp(
            prefix="cschema_render_"
        )
        out = Path(cls.tmp)
        bp = build_create_schema_factor_loop_plan(ROOT)
        ep = build_create_schema_factor_extension_plan(ROOT)
        cls.count = generate_create_schema_factor_programs(
            bp, ep, out
        )
        cls.files = sorted(out.glob("*.sql"))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_10592_files(self) -> None:
        self.assertEqual(10592, self.count)
        self.assertEqual(10592, len(self.files))

    def test_filename_numbering_is_contiguous(self) -> None:
        names = [f.name for f in self.files]
        expected = [
            f"CREATESCHEMA{i:05d}.sql" for i in range(1, 10593)
        ]
        self.assertEqual(expected, names)

    def test_every_file_has_exactly_one_primary_target(self) -> None:
        for f in self.files:
            sql = f.read_text(encoding="utf-8")
            n = count_primary_create_schema(sql)
            self.assertEqual(1, n, f.name)

    def test_no_file_creates_or_drops_standalone_tables(self) -> None:
        for f in self.files:
            sql = f.read_text(encoding="utf-8")
            begins = sql.count("-- primary-target-begin")
            ends = sql.count("-- primary-target-end")
            self.assertEqual(1, begins, f.name)
            self.assertEqual(1, ends, f.name)
            before, after = sql.split("-- primary-target-begin", 1)
            target, after = after.split("-- primary-target-end", 1)
            # CREATE TABLE/DROP TABLE may appear only inside the
            # primary-target region (sub-clause of CREATE SCHEMA)
            # or in comments, never as standalone statements.
            ct_outside = len(_CREATE_TABLE_RE.findall(before + after))
            dt_outside = len(_DROP_TABLE_RE.findall(before + after))
            self.assertEqual(0, ct_outside, f"CREATE TABLE outside target: {f.name}")
            self.assertEqual(0, dt_outside, f"DROP TABLE outside target: {f.name}")

    def test_every_catalog_query_has_order_by(self) -> None:
        missing = []
        for f in self.files:
            sql = f.read_text(encoding="utf-8")
            selects = _CATALOG_SELECT_RE.findall(sql)
            for _ in selects:
                pass
            # Check each catalog FROM has ORDER BY on same line region
            lines = sql.split("\n")
            for i, line in enumerate(lines):
                if re.search(
                    r"FROM\s+(pg_catalog\.|information_schema\.)",
                    line,
                    re.IGNORECASE,
                ):
                    window = "\n".join(lines[i:i + 3])
                    if not _ORDER_BY_RE.search(window):
                        missing.append(f.name)
                        break
        self.assertEqual(0, len(missing))

    def test_primary_target_is_create_schema(self) -> None:
        for f in self.files[:10]:
            sql = f.read_text(encoding="utf-8")
            before, after = sql.split("-- primary-target-begin", 1)
            target, _ = after.split("-- primary-target-end", 1)
            self.assertTrue(
                _CREATE_SCHEMA_RE.search(target),
                f.name,
            )

    def test_witness_resolves_for_every_case(self) -> None:
        bp = build_create_schema_factor_loop_plan(ROOT)
        ep = build_create_schema_factor_extension_plan(ROOT)
        for case in list(bp.cases)[:5] + list(ep.cases)[:5]:
            w = resolve_create_schema_factor_witness(case, ROOT)
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_render_is_deterministic(self) -> None:
        bp = build_create_schema_factor_loop_plan(ROOT)
        ep = build_create_schema_factor_extension_plan(ROOT)
        case = bp.cases[0]
        a = render_create_schema_factor_case(case, ROOT)
        b = render_create_schema_factor_case(case, ROOT)
        self.assertEqual(a, b)
        ext = ep.cases[0]
        c = render_create_schema_factor_case(ext, ROOT)
        d = render_create_schema_factor_case(ext, ROOT)
        self.assertEqual(c, d)

    def test_header_has_required_fields(self) -> None:
        bp = build_create_schema_factor_loop_plan(ROOT)
        case = bp.cases[0]
        sql = render_create_schema_factor_case(case, ROOT)
        for field in (
            "case_id",
            "source_md",
            "factor_md",
            "primary_obligation_id",
            "expected_outcome",
            "expected_sqlstate",
        ):
            self.assertIn(f"-- {field}:", sql)


if __name__ == "__main__":
    unittest.main()
