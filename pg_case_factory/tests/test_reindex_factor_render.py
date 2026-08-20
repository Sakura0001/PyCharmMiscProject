from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.reindex_factor_extension import (
    build_reindex_factor_extension_plan,
)
from pg_case_factory.reindex_factor_loop import (
    build_reindex_factor_loop_plan,
)
from pg_case_factory.reindex_factor_render import (
    ReindexFactorWitness,
    count_primary_reindex,
    generate_reindex_factor_programs,
    render_reindex_factor_case,
    resolve_reindex_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


def _executable_statements(text: str) -> list[str]:
    stmts: list[str] = []
    for stmt in text.split(";"):
        lines = [
            line.strip()
            for line in stmt.splitlines()
            if line.strip()
            and not line.strip().startswith("--")
            and not line.strip().startswith("\\")
        ]
        if lines:
            stmts.append(" ".join(lines))
    return stmts


class ReindexFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_reindex_factor_loop_plan(ROOT)
        cls.extension = build_reindex_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="reindex_render_"))
        cls.count = generate_reindex_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_renders_exactly_3575_files(self) -> None:
        self.assertEqual(3575, self.count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(3575, len(files))

    def test_filename_numbering_is_contiguous(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))
        names = [f.stem for f in files]
        self.assertEqual(
            [f"REINDEX{i:05d}" for i in range(1, 3576)],
            names,
        )

    def test_every_file_has_primary_target(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            sql = f.read_text()
            self.assertEqual(
                1, count_primary_reindex(sql), f.name
            )

    def test_no_quoted_create_table_in_render(self) -> None:
        for f in sorted(self.tmp.glob("*.sql")):
            sql = f.read_text()
            self.assertEqual(
                0,
                len(re.findall(r'CREATE TABLE "', sql)),
                f.name,
            )

    def test_bookend_first_statement_is_drop_for_table_cases(
        self,
    ) -> None:
        case = self.baseline.cases[0]
        sql = render_reindex_factor_case(case, ROOT)
        stmts = _executable_statements(sql)
        if "CREATE TABLE" in sql:
            self.assertTrue(
                stmts[0].startswith("DROP TABLE"),
                f"first stmt not DROP: {stmts[0]}",
            )

    def test_witness_resolves_for_baseline_case(self) -> None:
        case = self.baseline.cases[0]
        witness = resolve_reindex_factor_witness(case, ROOT)
        self.assertIsInstance(witness, ReindexFactorWitness)
        self.assertTrue(witness.target_sql_fragment)

    def test_witness_resolves_for_extension_case(self) -> None:
        case = self.extension.cases[0]
        witness = resolve_reindex_factor_witness(case, ROOT)
        self.assertIsInstance(witness, ReindexFactorWitness)
        self.assertTrue(witness.target_sql_fragment)

    def test_header_contains_required_fields(self) -> None:
        case = self.baseline.cases[0]
        sql = render_reindex_factor_case(case, ROOT)
        self.assertIn(f"-- case_id: {case.case_id}", sql)
        self.assertIn(
            f"-- expected_outcome: {case.outcome}", sql
        )
        self.assertIn(
            f"-- expected_sqlstate: {case.expected_sqlstate}",
            sql,
        )

    def test_on_error_stop_toggled_for_failures(self) -> None:
        for case in self.baseline.cases:
            if case.outcome != "expected_failure":
                continue
            sql = render_reindex_factor_case(case, ROOT)
            self.assertIn("\\set ON_ERROR_STOP off", sql)
            break

    def test_probe_uses_pg_class_relkind(self) -> None:
        case = self.baseline.cases[0]
        sql = render_reindex_factor_case(case, ROOT)
        self.assertIn("pg_catalog.pg_class", sql)
        self.assertIn("relkind", sql)


if __name__ == "__main__":
    unittest.main()
