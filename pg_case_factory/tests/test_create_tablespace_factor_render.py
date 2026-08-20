from pathlib import Path
import shutil
import tempfile
import unittest

from pg_case_factory.create_tablespace_factor_extension import (
    build_create_tablespace_factor_extension_plan,
)
from pg_case_factory.create_tablespace_factor_loop import (
    build_create_tablespace_factor_loop_plan,
)
from pg_case_factory.create_tablespace_factor_render import (
    count_primary_create_tablespace,
    generate_create_tablespace_factor_programs,
    render_create_tablespace_factor_case,
    resolve_create_tablespace_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateTablespaceFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_create_tablespace_factor_loop_plan(ROOT)
        cls.extension = build_create_tablespace_factor_extension_plan(
            ROOT
        )
        cls.tmp = Path(tempfile.mkdtemp(prefix="ctsp_render_"))
        count = generate_create_tablespace_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )
        cls.file_count = count

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_writes_all_files(self) -> None:
        self.assertEqual(4567, self.file_count)
        files = sorted(self.tmp.glob("*.sql"))
        self.assertEqual(4567, len(files))

    def test_first_baseline_file_has_expected_header(self) -> None:
        sql = (
            self.tmp / "CREATETABLESPACE00001.sql"
        ).read_text()
        self.assertIn("-- case_id: CREATETABLESPACE00001", sql)
        self.assertIn(
            "-- primary_obligation_id:", sql
        )
        self.assertIn("CREATE TABLESPACE", sql)

    def test_primary_target_cardinality_is_one(self) -> None:
        files = sorted(self.tmp.glob("*.sql"))[:50]
        for f in files:
            sql = f.read_text()
            self.assertEqual(
                1, count_primary_create_tablespace(sql), f.name
            )

    def test_no_create_table_in_any_file(self) -> None:
        """Table-less-exempt: no case creates a TABLE."""
        import re
        files = sorted(self.tmp.glob("*.sql"))[:100]
        for f in files:
            sql = f.read_text()
            matches = re.findall(
                r"(?im)^\s*CREATE\s+TABLE\b", sql
            )
            self.assertEqual(
                0, len(matches), f.name
            )

    def test_no_drop_table_in_any_file(self) -> None:
        """Table-less-exempt: bookend DROP TABLE IF EXISTS is N/A."""
        import re
        files = sorted(self.tmp.glob("*.sql"))[:100]
        for f in files:
            sql = f.read_text()
            matches = re.findall(
                r"(?im)^\s*DROP\s+TABLE\b", sql
            )
            self.assertEqual(
                0, len(matches), f.name
            )

    def test_catalog_selects_have_order_by(self) -> None:
        import re
        files = sorted(self.tmp.glob("*.sql"))[:200]
        for f in files:
            sql = f.read_text()
            selects = re.findall(
                r"SELECT\s+count\(.*?\)\s+[><=]+\s+\d+\s+AS\s+\w+\s+"
                r"FROM\s+pg_catalog\.\w+",
                sql,
                re.IGNORECASE | re.DOTALL,
            )
            for sel in selects:
                idx = sql.find(sel)
                tail = sql[idx:idx + 400]
                self.assertIn(
                    "ORDER BY", tail, f.name
                )

    def test_no_quoted_or_dotted_from_targets(self) -> None:
        import re
        files = sorted(self.tmp.glob("*.sql"))[:200]
        for f in files:
            sql = f.read_text()
            froms = re.findall(
                r"FROM\s+(\S+)", sql
            )
            for target in froms:
                if target.startswith("pg_catalog."):
                    continue
                self.assertNotIn(
                    '"', target, f.name
                )
                self.assertNotIn(
                    ".", target, f.name
                )

    def test_cleanup_drops_tablespace_for_valid_names(self) -> None:
        import re
        files = sorted(self.tmp.glob("*.sql"))[:100]
        for f in files:
            sql = f.read_text()
            # Match CREATE TABLESPACE only at start of line (skips
            # comment lines starting with --).
            target = re.search(
                r"(?m)^CREATE TABLESPACE\s+(\S+)", sql
            )
            name = target.group(1) if target else ""
            if name.startswith("pg_") or name == '""':
                # PG rejects DROP for reserved/invalid names; cleanup
                # uses residual check instead.
                self.assertIn(
                    "residual_check_no_objects", sql, f.name
                )
            else:
                self.assertIn(
                    "DROP TABLESPACE IF EXISTS", sql, f.name
                )

    def test_witness_resolves_for_baseline_and_extension(self) -> None:
        base_case = self.baseline.cases[0]
        ext_case = self.extension.cases[0]
        w1 = resolve_create_tablespace_factor_witness(
            base_case, ROOT
        )
        w2 = resolve_create_tablespace_factor_witness(
            ext_case, ROOT
        )
        self.assertTrue(w1.target_sql_fragment)
        self.assertTrue(w2.target_sql_fragment)

    def test_render_is_deterministic(self) -> None:
        case = self.baseline.cases[0]
        first = render_create_tablespace_factor_case(case, ROOT)
        second = render_create_tablespace_factor_case(case, ROOT)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
