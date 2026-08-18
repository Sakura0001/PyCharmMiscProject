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
    def test_create_conversion_support_function_is_not_a_file_scoped_object(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "ALTERCONVERSION00001.sql").write_text(
                textwrap.dedent(
                    """
                    CREATE DEFAULT CONVERSION alterconversion_00001_conv
                    FOR 'UTF8' TO 'LATIN1'
                    FROM pg_catalog.utf8_to_iso8859_1;
                    ALTER CONVERSION alterconversion_00001_conv
                    RENAME TO alterconversion_00001_renamed;
                    DROP CONVERSION alterconversion_00001_renamed;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "ALTERCONVERSION")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_postgresql_table_functions_and_row_lock_keywords_are_not_objects(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "PCF00001.sql").write_text(
                textwrap.dedent(
                    """
                    DROP TABLE IF EXISTS pcf_00001_base_table;
                    CREATE TABLE pcf_00001_base_table (id int PRIMARY KEY);
                    SELECT value FROM generate_series(1, 2) AS generated(value);
                    SELECT value FROM unnest(ARRAY[1, 2]) AS generated(value);
                    SELECT id FROM json_to_record('{"id":1}'::json) AS record_row(id integer);
                    SELECT current_schema FROM current_schema() AS schema_name(current_schema);
                    SELECT * FROM ROWS FROM (
                        generate_series(1, 2),
                        unnest(ARRAY['alpha', 'beta'])
                    ) AS rows_out(id, payload);
                    SELECT id FROM pcf_00001_base_table FOR UPDATE NOWAIT;
                    SELECT id FROM pcf_00001_base_table FOR UPDATE SKIP LOCKED;
                    SELECT id FROM pcf_00001_base_table FOR NO KEY UPDATE;
                    DROP TABLE IF EXISTS pcf_00001_base_table;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "PCF")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_update_target_after_row_lock_examples_is_still_checked(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "PCF00001.sql").write_text(
                textwrap.dedent(
                    """
                    DROP TABLE IF EXISTS pcf_00001_base_table;
                    CREATE TABLE pcf_00001_base_table (id int PRIMARY KEY);
                    SELECT id FROM pcf_00001_base_table FOR UPDATE SKIP LOCKED;
                    UPDATE wrong_table SET id = 2;
                    DROP TABLE IF EXISTS pcf_00001_base_table;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "PCF")

            self.assertEqual(result.returncode, 1)
            self.assertIn("object 'wrong_table'", result.stdout)

    def test_cte_names_are_not_treated_as_file_scoped_database_objects(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "PCF00001.sql").write_text(
                textwrap.dedent(
                    """
                    DROP TABLE IF EXISTS pcf_00001_base_table;
                    CREATE TABLE pcf_00001_base_table (id int);
                    WITH RECURSIVE input_row(id) AS (
                        VALUES (1)
                        UNION ALL
                        SELECT id + 1 FROM input_row WHERE id < 2
                    ), selected_rows AS (
                        SELECT id FROM pcf_00001_base_table
                    )
                    SELECT input_row.id
                    FROM input_row
                    JOIN selected_rows ON selected_rows.id = input_row.id;
                    DROP TABLE IF EXISTS pcf_00001_base_table;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "PCF")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_statement_keywords_and_public_role_are_not_object_references(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "PCF00001.sql").write_text(
                textwrap.dedent(
                    """
                    DROP TABLE IF EXISTS pcf_00001_target, pcf_00001_source;
                    CREATE TABLE pcf_00001_target (id int PRIMARY KEY, payload text);
                    CREATE TABLE pcf_00001_source (id int PRIMARY KEY, payload text);
                    CREATE PROCEDURE pcf_00001_procedure(text) LANGUAGE SQL AS $$ SELECT 1 $$;
                    REVOKE EXECUTE ON PROCEDURE pcf_00001_procedure(text) FROM PUBLIC;
                    GRANT UPDATE ON pcf_00001_target TO pcf_00001_role;
                    CREATE TRIGGER pcf_00001_trigger BEFORE UPDATE OF payload
                    ON pcf_00001_target FOR EACH ROW EXECUTE FUNCTION pcf_00001_trigger_fn();
                    MERGE INTO pcf_00001_target AS target_rows
                    USING pcf_00001_source AS source_rows
                    ON target_rows.id = source_rows.id
                    WHEN MATCHED THEN UPDATE SET payload = source_rows.payload;
                    SELECT id FROM pcf_00001_target AS target_rows
                    FOR UPDATE OF target_rows;
                    DROP TABLE IF EXISTS pcf_00001_target, pcf_00001_source;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "PCF")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_alter_database_from_current_and_dblink_function_are_not_objects(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "ALTERDATABASE00001.sql").write_text(
                textwrap.dedent(
                    r"""
                    DROP DATABASE IF EXISTS alterdatabase_00001_db;
                    CREATE DATABASE alterdatabase_00001_db;
                    \set ON_ERROR_STOP off
                    ALTER DATABASE alterdatabase_00001_db SET work_mem FROM CURRENT;
                    SELECT observed.database_name
                    FROM public.dblink(
                        'alterdatabase_00001_link',
                        'SELECT current_database()'
                    ) AS observed(database_name name);
                    DROP DATABASE IF EXISTS alterdatabase_00001_db;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "ALTERDATABASE")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cte_name_cannot_hide_a_persistent_object_with_the_same_name(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "PCF00001.sql").write_text(
                textwrap.dedent(
                    """
                    CREATE TABLE input_row (id int);
                    WITH input_row(id) AS (VALUES (1))
                    SELECT id FROM input_row;
                    DROP TABLE input_row;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "PCF")

            self.assertEqual(result.returncode, 1)
            self.assertIn("object 'input_row'", result.stdout)

    def test_cte_name_does_not_hide_a_later_statement_relation_reference(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "PCF00001.sql").write_text(
                textwrap.dedent(
                    """
                    DROP TABLE IF EXISTS pcf_00001_base_table;
                    CREATE TABLE pcf_00001_base_table (id int);
                    WITH wrong_shared(id) AS (VALUES (1))
                    SELECT id FROM wrong_shared;
                    SELECT id FROM wrong_shared;
                    DROP TABLE IF EXISTS pcf_00001_base_table;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "PCF")

            self.assertEqual(result.returncode, 1)
            self.assertIn("object 'wrong_shared'", result.stdout)

    def test_accepts_fixed_five_digit_numbering_for_a_small_batch(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            for number in ("00001", "00002"):
                object_name = f"pcf_{number}_base_table"
                (sql_dir / f"PCF{number}.sql").write_text(
                    textwrap.dedent(
                        f"""
                        -- --------------------------------------------------------
                        -- author       : codex
                        -- create at    : 2026-08-05
                        -- description  : validates fixed-width numbering
                        -- FE           :
                        -- --------------------------------------------------------

                        DROP TABLE IF EXISTS {object_name};
                        CREATE TABLE {object_name} (id int);
                        SELECT id FROM {object_name} ORDER BY id;
                        DROP TABLE IF EXISTS {object_name};
                        """
                    ).strip()
                )

            result = run_validator(sql_dir, "--prefix", "PCF")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_information_schema_catalog_views_are_not_file_scoped_objects(self) -> None:
        with TemporaryDirectory() as raw_dir:
            sql_dir = Path(raw_dir)
            (sql_dir / "PCF00001.sql").write_text(
                textwrap.dedent(
                    """
                    DROP FUNCTION IF EXISTS pcf_00001_fn;
                    CREATE FUNCTION pcf_00001_fn() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;
                    SELECT routine_schema, routine_name
                    FROM information_schema.routines AS r
                    WHERE r.routine_name = 'pcf_00001_fn'
                    ORDER BY r.routine_schema, r.routine_name;
                    DROP FUNCTION IF EXISTS pcf_00001_fn;
                    """
                ).strip()
            )

            result = run_validator(sql_dir, "--prefix", "PCF")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

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
