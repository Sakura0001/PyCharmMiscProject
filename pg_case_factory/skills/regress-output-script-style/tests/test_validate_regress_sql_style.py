import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_regress_sql_style.py"


def run_validator(sql_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(sql_dir), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class ValidateRegressSqlStyleTest(unittest.TestCase):
    def test_accepts_numbered_files_with_matching_table_and_view_prefix(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "A001.sql").write_text(
                textwrap.dedent(
                    """
                    -- --------------------------------------------------------
                    -- author       : codex
                    -- create at    : 2026-05-31
                    -- description  : validates matching object names
                    -- FE           :
                    -- --------------------------------------------------------

                    DROP VIEW IF EXISTS a_001_result_view;
                    DROP TABLE IF EXISTS a_001_base_table;
                    CREATE TABLE a_001_base_table (id int);
                    CREATE VIEW a_001_result_view AS SELECT id FROM a_001_base_table;
                    SELECT id FROM a_001_result_view ORDER BY id;
                    DROP VIEW IF EXISTS a_001_result_view;
                    DROP TABLE IF EXISTS a_001_base_table;
                    """
                ).strip()
            )
            (sql_dir / "A002.sql").write_text(
                textwrap.dedent(
                    """
                    -- --------------------------------------------------------
                    -- author       : codex
                    -- create at    : 2026-05-31
                    -- description  : validates second file
                    -- FE           :
                    -- --------------------------------------------------------

                    DROP TABLE IF EXISTS a_002_base_table;
                    CREATE TABLE a_002_base_table (id int);
                    INSERT INTO a_002_base_table VALUES (1);
                    SELECT id FROM a_002_base_table ORDER BY id;
                    DROP TABLE IF EXISTS a_002_base_table;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "A")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_rejects_bad_filename_sequence_and_detached_object_names(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "A001.sql").write_text(
                "CREATE TABLE wrong_table (id int);\nSELECT * FROM wrong_table;\n"
            )
            (sql_dir / "A003.sql").write_text(
                "CREATE VIEW a_003_view AS SELECT 1 AS id;\nSELECT * FROM a_003_view;\n"
            )

            result = run_validator(sql_dir, "--prefix", "A")

            self.assertEqual(result.returncode, 1)
            self.assertIn("MANUAL_CONFIRMATION_REQUIRED", result.stdout)
            self.assertIn("missing expected SQL file", result.stdout)
            self.assertIn("wrong_table", result.stdout)


if __name__ == "__main__":
    unittest.main()
