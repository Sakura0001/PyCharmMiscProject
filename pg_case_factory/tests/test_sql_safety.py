from __future__ import annotations

import unittest

from pg_case_factory.sql_safety import (
    UnsafeSqlError,
    validate_sql_for_basic_runner,
    validate_sql_for_external_copy_ingest,
)


class SqlSafetyTest(unittest.TestCase):
    def test_rejects_psql_host_and_file_meta_commands(self) -> None:
        for sql in (
            "SELECT 1;\\! env\n",
            "SELECT 1 \\g |cat /etc/passwd\n",
            "\\copy data TO PROGRAM 'env'\n",
            "\\.\n",
            "\\i /tmp/secret.sql\n",
        ):
            with self.subTest(sql=sql), self.assertRaisesRegex(
                UnsafeSqlError,
                "psql meta commands",
            ):
                validate_sql_for_basic_runner(sql)

    def test_rejects_server_side_copy_program(self) -> None:
        with self.assertRaisesRegex(UnsafeSqlError, "COPY PROGRAM"):
            validate_sql_for_basic_runner("COPY data TO PROGRAM 'env';\n")

    def test_rejects_copy_stdin_data_mode_meta_command_bypass(self) -> None:
        payload = (
            "CREATE TEMP TABLE t(x text);\n"
            "COPY t FROM STDIN;\n"
            "'\n"
            "\\.\n"
            "\\! env\n"
        )
        with self.assertRaisesRegex(UnsafeSqlError, "COPY FROM STDIN"):
            validate_sql_for_basic_runner(payload)

    def test_quote_ambiguity_and_unicode_dollar_tags_cannot_hide_meta_commands(self) -> None:
        payloads = (
            "SELECT 'safe" + "\\" + "';\n\\! env\n",
            "SELECT $é$'$é$;\n\\! env\n",
        )
        for sql in payloads:
            with self.subTest(sql=sql), self.assertRaisesRegex(
                UnsafeSqlError,
                "psql meta commands",
            ):
                validate_sql_for_basic_runner(sql)

    def test_ignores_keywords_and_backslashes_inside_sql_literals_comments_and_bodies(self) -> None:
        validate_sql_for_basic_runner(
            "-- COPY data TO PROGRAM 'env'\n"
            "SELECT 'COPY x TO PROGRAM', E'\\\\not_meta';\n"
            "DO $$ BEGIN RAISE NOTICE '\\\\! text'; END $$;\n"
            "DO $é$ BEGIN RAISE NOTICE '\\! text'; END $é$;\n"
        )

    def test_external_copy_ingest_accepts_manifest_bound_inline_payloads(self) -> None:
        validate_sql_for_external_copy_ingest(
            "CREATE TEMP TABLE ingest_bound(id integer, note text);\n"
            "COPY ingest_bound (id, note) FROM STDIN WITH (FORMAT csv);\n"
            "1,first\n"
            "2,\\! is payload data, not a psql command\n"
            "\\.\n"
            "SELECT * FROM ingest_bound ORDER BY id;\n"
        )
        validate_sql_for_external_copy_ingest(
            "CREATE TEMP TABLE two_blocks(id integer);\r\n"
            "COPY two_blocks FROM STDIN;\r\n"
            "1\r\n"
            "\\.\r\n"
            "COPY two_blocks FROM STDIN;\r\n"
            "2\r\n"
            "\\."
        )

    def test_external_copy_ingest_rejects_missing_or_empty_inline_payload(self) -> None:
        invalid_programs = (
            "SELECT 'COPY t FROM STDIN;';\n",
            "COPY t FROM STDIN;\n\\.\n",
            "COPY t FROM STDIN;\n1\n",
            "COPY t FROM STDIN; 1\n\\.\n",
            "COPY t FROM STDIN\n1\n\\.\n",
            "COPY t FROM STDIN;\n1\n \\.\n",
        )
        for sql in invalid_programs:
            with self.subTest(sql=sql), self.assertRaises(UnsafeSqlError):
                validate_sql_for_external_copy_ingest(sql)

    def test_external_copy_ingest_rejects_external_or_out_of_band_sources(self) -> None:
        invalid_programs = (
            "COPY t FROM '/tmp/payload.csv';\n",
            "COPY t FROM PROGRAM 'payload-generator';\n",
            "COPY (SELECT * FROM t) TO STDOUT;\n",
            "\\copy t FROM '/tmp/payload.csv'\n",
            "COPY t FROM STDIN;\n1\n\\.\n\\i /tmp/more.sql\n",
        )
        for sql in invalid_programs:
            with self.subTest(sql=sql), self.assertRaises(UnsafeSqlError):
                validate_sql_for_external_copy_ingest(sql)


if __name__ == "__main__":
    unittest.main()
