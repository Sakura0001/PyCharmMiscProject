from __future__ import annotations

import copy
import unittest

from pg_case_factory.regression_style import (
    ExecutionTranscript,
    HuaweiSqlHeader,
    RegressionBatchMapping,
    RegressionStyleError,
    audit_catalog_observability,
    audit_complete_table_script,
    build_regression_batch_mapping,
    compare_two_run_transcripts,
    render_huawei_sql_header,
    validate_huawei_sql_header,
    validate_two_run_determinism,
)


def _header(*, fe: str = "FE-PG-184") -> HuaweiSqlHeader:
    return HuaweiSqlHeader(
        author="00123456 Zhang San",
        create_at="2026-07-13",
        version="1.0",
        description="Verify deterministic relation metadata after CREATE TABLE",
        fe=fe,
    )


class RegressionBatchMappingTest(unittest.TestCase):
    def test_plan_order_maps_to_contiguous_stable_names(self) -> None:
        obligations = ["obl-zeta", "obl-alpha", "obl-middle"]

        mapping = build_regression_batch_mapping("IDX", obligations)

        self.assertEqual(3, mapping.number_width)
        self.assertEqual(
            ["IDX001.sql", "IDX002.sql", "IDX003.sql"],
            [case.sql_filename for case in mapping.cases],
        )
        self.assertEqual(
            ["idx_001_", "idx_002_", "idx_003_"],
            [case.object_prefix for case in mapping.cases],
        )
        self.assertEqual(obligations, [case.obligation_id for case in mapping.cases])
        self.assertEqual([1, 2, 3], [case.case_ordinal for case in mapping.cases])
        round_trip = RegressionBatchMapping.from_dict(mapping.to_dict())
        self.assertEqual(mapping, round_trip)
        self.assertEqual(mapping.sha256, round_trip.sha256)

    def test_large_batch_automatically_uses_enough_digits(self) -> None:
        obligations = [f"obl-{index:05d}" for index in range(1, 13154)]

        mapping = build_regression_batch_mapping("PG", obligations)

        self.assertEqual(5, mapping.number_width)
        self.assertEqual("PG00001.sql", mapping.cases[0].sql_filename)
        self.assertEqual("PG13153.sql", mapping.cases[-1].sql_filename)
        self.assertEqual("pg_13153_", mapping.cases[-1].object_prefix)

    def test_initial_mapping_can_reserve_a_wider_append_only_namespace(self) -> None:
        mapping = build_regression_batch_mapping(
            "A", ["obl-one", "obl-two"], minimum_width=5
        )

        self.assertEqual("A00001.sql", mapping.cases[0].sql_filename)
        self.assertEqual("a_00002_", mapping.cases[1].object_prefix)

    def test_explicit_prior_mapping_only_appends_and_preserves_old_assignments(self) -> None:
        prior = build_regression_batch_mapping(
            "A", ["obl-one", "obl-two"], minimum_width=5
        )

        extended = build_regression_batch_mapping(
            "A", ["obl-one", "obl-two", "obl-three"], prior_mapping=prior
        )

        self.assertEqual(prior.cases, extended.cases[:2])
        self.assertEqual("A00003.sql", extended.cases[-1].sql_filename)
        repeated = build_regression_batch_mapping(
            "A", ["obl-one", "obl-two", "obl-three"], prior_mapping=extended
        )
        self.assertEqual(extended, repeated)
        self.assertEqual(extended.sha256, repeated.sha256)

    def test_prior_mapping_rejects_removal_reorder_replacement_and_prefix_conflict(self) -> None:
        prior = build_regression_batch_mapping("A", ["obl-one", "obl-two"])
        invalid_inputs = (
            ("A", ["obl-one"]),
            ("A", ["obl-two", "obl-one", "obl-three"]),
            ("A", ["obl-one", "obl-other", "obl-three"]),
            ("B", ["obl-one", "obl-two", "obl-three"]),
        )
        for prefix, obligations in invalid_inputs:
            with self.subTest(prefix=prefix, obligations=obligations), self.assertRaises(
                RegressionStyleError
            ):
                build_regression_batch_mapping(
                    prefix, obligations, prior_mapping=prior
                )

    def test_append_refuses_width_change_that_would_rename_prior_files(self) -> None:
        prior = build_regression_batch_mapping(
            "A", [f"obl-{index:03d}" for index in range(1, 1000)]
        )
        obligations = [case.obligation_id for case in prior.cases] + ["obl-1000"]

        with self.assertRaisesRegex(RegressionStyleError, "number_width"):
            build_regression_batch_mapping("A", obligations, prior_mapping=prior)
        with self.assertRaisesRegex(RegressionStyleError, "cannot widen"):
            build_regression_batch_mapping(
                "A", [case.obligation_id for case in prior.cases],
                prior_mapping=prior, minimum_width=4
            )

    def test_invalid_prefix_obligations_and_sequences_fail_closed(self) -> None:
        invalid_prefixes = ("", "1A", "A-B", "A_", " A", "\u8868")
        for prefix in invalid_prefixes:
            with self.subTest(prefix=prefix), self.assertRaises(RegressionStyleError):
                build_regression_batch_mapping(prefix, ["obl-one"])
        for obligations in (
            [],
            ["obl-one", "obl-one"],
            ["bad/id"],
            [" line"],
        ):
            with self.subTest(obligations=obligations), self.assertRaises(
                RegressionStyleError
            ):
                build_regression_batch_mapping("A", obligations)
        with self.assertRaisesRegex(RegressionStyleError, "ordered sequence"):
            build_regression_batch_mapping("A", "obl-one")  # type: ignore[arg-type]
        with self.assertRaisesRegex(RegressionStyleError, "minimum_width"):
            build_regression_batch_mapping("A", ["obl-one"], minimum_width=True)
        with self.assertRaisesRegex(RegressionStyleError, "63-byte"):
            build_regression_batch_mapping("A" * 60, ["obl-one"])

    def test_mapping_schema_rejects_unknown_fields_and_tampered_names(self) -> None:
        document = build_regression_batch_mapping("A", ["obl-one"]).to_dict()
        unknown = copy.deepcopy(document)
        unknown["extra"] = True
        with self.assertRaisesRegex(RegressionStyleError, "unexpected extra"):
            RegressionBatchMapping.from_dict(unknown)

        tampered = copy.deepcopy(document)
        tampered["cases"][0]["sql_filename"] = "A002.sql"
        with self.assertRaisesRegex(RegressionStyleError, "must be A001.sql"):
            RegressionBatchMapping.from_dict(tampered)

        non_contiguous = copy.deepcopy(document)
        non_contiguous["cases"][0]["case_ordinal"] = 2
        with self.assertRaisesRegex(RegressionStyleError, "contiguous"):
            RegressionBatchMapping.from_dict(non_contiguous)

        no_cases = copy.deepcopy(document)
        no_cases["cases"] = []
        with self.assertRaisesRegex(RegressionStyleError, "non-empty"):
            RegressionBatchMapping.from_dict(no_cases)


class HuaweiHeaderTest(unittest.TestCase):
    def test_renderer_and_validator_preserve_all_explicit_values(self) -> None:
        header = _header()
        rendered = render_huawei_sql_header(header)
        sql = rendered + "SELECT 1;\n"

        self.assertTrue(
            rendered.startswith("-- --------------------------------------------------------\n")
        )
        self.assertIn("-- author       : 00123456 Zhang San\n", rendered)
        self.assertIn("-- create at    : 2026-07-13\n", rendered)
        self.assertIn("-- version      : 1.0\n", rendered)
        self.assertIn("-- FE           : FE-PG-184\n", rendered)
        self.assertEqual(header, validate_huawei_sql_header(sql, expected=header))
        self.assertTrue(sql.endswith(";\n"))
        self.assertFalse(sql.endswith("\n\n"))

    def test_empty_fe_is_still_an_explicit_header_line(self) -> None:
        header = _header(fe="")
        sql = render_huawei_sql_header(header) + "SELECT 1;\n"

        self.assertIn("-- FE           : \n", sql)
        self.assertEqual("", validate_huawei_sql_header(sql).fe)

    def test_header_contract_is_strict_and_date_is_real(self) -> None:
        valid = _header().to_dict()
        missing_fe = dict(valid)
        missing_fe.pop("fe")
        with self.assertRaisesRegex(RegressionStyleError, "missing fe"):
            HuaweiSqlHeader.from_dict(missing_fe)
        unknown = dict(valid, generated_at="today")
        with self.assertRaisesRegex(RegressionStyleError, "unexpected generated_at"):
            HuaweiSqlHeader.from_dict(unknown)

        for changes in (
            {"create_at": "2026-02-30"},
            {"create_at": "2026-7-13"},
            {"description": ""},
            {"author": "author\nother"},
            {"version": " 1.0"},
        ):
            document = dict(valid, **changes)
            with self.subTest(changes=changes), self.assertRaises(RegressionStyleError):
                HuaweiSqlHeader.from_dict(document)

    def test_validator_rejects_noncanonical_header_and_eof(self) -> None:
        canonical = render_huawei_sql_header(_header()) + "SELECT 1;\n"
        invalid_sql = (
            canonical.replace("-- author       :", "-- author:"),
            canonical.replace("\n", "\r\n"),
            canonical[:-1],
            canonical + "\n",
            canonical + "   \n",
        )
        for sql in invalid_sql:
            with self.subTest(sql=repr(sql[-40:])), self.assertRaises(
                RegressionStyleError
            ):
                validate_huawei_sql_header(sql)

        with self.assertRaisesRegex(RegressionStyleError, "expected values"):
            validate_huawei_sql_header(canonical, expected=_header(fe="OTHER"))


class CatalogObservabilityAuditTest(unittest.TestCase):
    def test_explicit_ordered_pg_catalog_observation_is_allowed(self) -> None:
        report = audit_catalog_observability(
            "SELECT c.relname, c.relkind\n"
            "FROM pg_catalog.pg_class AS c\n"
            "WHERE c.relname LIKE 'a_001_%'\n"
            "ORDER BY c.relname, c.relkind;\n"
        )

        self.assertTrue(report.passed, report.to_dict())
        self.assertEqual(1, len(report.queries))
        self.assertEqual(("pg_catalog.pg_class",), report.queries[0].relations)
        self.assertEqual("c.relname, c.relkind", report.queries[0].projection)

    def test_information_schema_and_aggregate_projection_are_not_blanket_banned(self) -> None:
        report = audit_catalog_observability(
            "SELECT count(*) AS column_count\n"
            "FROM information_schema.columns\n"
            "WHERE table_name = 'a_001_base'\n"
            "ORDER BY column_count;\n"
        )

        self.assertTrue(report.passed, report.to_dict())

    def test_wildcard_missing_order_and_unqualified_catalog_are_reported(self) -> None:
        report = audit_catalog_observability("SELECT * FROM pg_class;\n")

        self.assertFalse(report.passed)
        issues = " | ".join(report.queries[0].issues)
        self.assertIn("wildcard", issues)
        self.assertIn("ORDER BY", issues)
        self.assertIn("schema-qualified", issues)

    def test_volatile_and_positional_ordering_are_reported(self) -> None:
        volatile = audit_catalog_observability(
            "SELECT c.relname, clock_timestamp() AS observed_at "
            "FROM pg_catalog.pg_class AS c ORDER BY random();\n"
        )
        self.assertFalse(volatile.passed)
        self.assertIn("volatile", " ".join(volatile.queries[0].issues))

        positional = audit_catalog_observability(
            "SELECT c.relname FROM pg_catalog.pg_class AS c ORDER BY 1;\n"
        )
        self.assertFalse(positional.passed)
        self.assertIn("ordinals", " ".join(positional.queries[0].issues))

    def test_comments_and_literals_do_not_create_catalog_findings(self) -> None:
        report = audit_catalog_observability(
            "-- SELECT * FROM pg_catalog.pg_class\n"
            "SELECT 'FROM pg_catalog.pg_class ORDER BY random()';\n"
        )

        self.assertTrue(report.passed, report.to_dict())
        self.assertEqual((), report.queries)

        quoted = audit_catalog_observability(
            'SELECT c."strange--;name" FROM pg_catalog.pg_class AS c '
            'ORDER BY c."strange--;name";\n'
        )
        self.assertTrue(quoted.passed, quoted.to_dict())

    def test_compound_and_unterminated_statements_fail_conservatively(self) -> None:
        compound = audit_catalog_observability(
            "WITH objects AS (SELECT relname FROM pg_catalog.pg_class) "
            "SELECT relname FROM objects ORDER BY relname;\n"
        )
        self.assertFalse(compound.passed)
        self.assertIn("manual", " ".join(compound.queries[0].issues))

        unterminated = audit_catalog_observability(
            "SELECT relname FROM pg_catalog.pg_class ORDER BY relname\n"
        )
        self.assertFalse(unterminated.passed)
        self.assertIn("semicolon", " ".join(unterminated.parser_issues))


class TranscriptDeterminismTest(unittest.TestCase):
    def test_success_transcripts_must_match_all_three_channels(self) -> None:
        first = ExecutionTranscript(0, b"row\n", b"")
        second = ExecutionTranscript(0, b"row\n", b"")

        report = validate_two_run_determinism(
            first, second, expected_failure=False
        )

        self.assertTrue(report.deterministic)
        self.assertFalse(report.both_failed)
        self.assertEqual(report.first_stdout_sha256, report.second_stdout_sha256)

    def test_expected_failure_is_compared_and_can_pass_deterministically(self) -> None:
        first = ExecutionTranscript(3, b"", b"ERROR:  duplicate key\n")
        second = ExecutionTranscript(3, b"", b"ERROR:  duplicate key\n")

        report = validate_two_run_determinism(first, second, expected_failure=True)

        self.assertTrue(report.deterministic)
        self.assertTrue(report.both_failed)

    def test_returncode_stdout_and_stderr_differences_are_all_reported(self) -> None:
        report = compare_two_run_transcripts(
            ExecutionTranscript(1, b"first\n", b"error one\n"),
            ExecutionTranscript(2, b"second\n", b"error two\n"),
        )

        self.assertFalse(report.deterministic)
        self.assertEqual(("returncode", "stdout", "stderr"), report.differences)
        with self.assertRaisesRegex(RegressionStyleError, "returncode, stdout, stderr"):
            validate_two_run_determinism(
                ExecutionTranscript(1, b"first\n", b"error one\n"),
                ExecutionTranscript(2, b"second\n", b"error two\n"),
            )

    def test_outcome_expectation_is_checked_after_byte_comparison(self) -> None:
        success = ExecutionTranscript(0, b"ok\n", b"")
        failure = ExecutionTranscript(1, b"", b"error\n")
        with self.assertRaisesRegex(RegressionStyleError, "unexpectedly succeeded"):
            validate_two_run_determinism(success, success, expected_failure=True)
        with self.assertRaisesRegex(RegressionStyleError, "unexpectedly failed"):
            validate_two_run_determinism(failure, failure, expected_failure=False)
        with self.assertRaisesRegex(RegressionStyleError, "boolean"):
            validate_two_run_determinism(
                success, success, expected_failure=1  # type: ignore[arg-type]
            )

    def test_transcript_requires_raw_bytes_and_real_integer_status(self) -> None:
        invalid_args = (
            (True, b"", b""),
            (0, "text", b""),
            (0, b"", bytearray()),
        )
        for args in invalid_args:
            with self.subTest(args=args), self.assertRaises(RegressionStyleError):
                ExecutionTranscript(*args)  # type: ignore[arg-type]


class CompleteTableScriptAuditTest(unittest.TestCase):
    def _complete_sql(self) -> str:
        return (
            render_huawei_sql_header(_header())
            + "DROP TABLE IF EXISTS a_001_child, a_001_base;\n"
            + "CREATE TABLE a_001_base(id integer PRIMARY KEY, value text);\n"
            + "CREATE TABLE a_001_child(id integer REFERENCES a_001_base(id));\n"
            + "INSERT INTO a_001_base VALUES (1, 'one');\n"
            + "SELECT id, value FROM a_001_base ORDER BY id;\n"
            + "DROP TABLE IF EXISTS a_001_child, a_001_base;\n"
        )

    def test_complete_table_script_passes_conservative_structure_checks(self) -> None:
        sql = self._complete_sql()

        report = audit_complete_table_script(sql, expected_object_prefix="a_001_")

        self.assertTrue(report.passed, report.to_dict())
        self.assertEqual(("a_001_base", "a_001_child"), report.created_tables)
        self.assertEqual(
            ("a_001_child", "a_001_base"), report.final_cleanup_tables
        )
        self.assertIn("cannot prove", " ".join(report.warnings))

    def test_missing_boundary_cleanup_and_wrong_prefix_fail(self) -> None:
        missing = (
            "CREATE TABLE a_001_base(id integer);\n"
            "SELECT id FROM a_001_base ORDER BY id;\n"
        )
        report = audit_complete_table_script(
            missing, expected_object_prefix="a_001_"
        )
        self.assertFalse(report.passed)
        self.assertIn("first executable", " ".join(report.issues))
        self.assertIn("final executable", " ".join(report.issues))

        wrong_prefix = self._complete_sql().replace("a_001_", "other_")
        report = audit_complete_table_script(
            wrong_prefix, expected_object_prefix="a_001_"
        )
        self.assertFalse(report.passed)
        self.assertIn("does not use", " ".join(report.issues))

    def test_cleanup_must_cover_every_statically_created_table(self) -> None:
        sql = (
            "DROP TABLE IF EXISTS a_001_base;\n"
            "CREATE TABLE a_001_base(id integer);\n"
            "CREATE TABLE a_001_child(id integer);\n"
            "DROP TABLE IF EXISTS a_001_base;\n"
        )

        report = audit_complete_table_script(sql)

        self.assertFalse(report.passed)
        self.assertIn("a_001_child", " ".join(report.issues))

    def test_database_scope_and_dynamic_or_quoted_sql_are_conservative(self) -> None:
        database_sql = (
            "DROP TABLE IF EXISTS a_001_base;\n"
            "CREATE DATABASE forbidden;\n"
            "CREATE TABLE a_001_base(id integer);\n"
            "DROP TABLE IF EXISTS a_001_base;\n"
        )
        report = audit_complete_table_script(database_sql)
        self.assertFalse(report.passed)
        self.assertIn("database-level", " ".join(report.issues))

        dynamic_sql = (
            'DROP TABLE IF EXISTS "a_001_base";\n'
            'CREATE TABLE "a_001_base"(id integer);\n'
            "DO $$ BEGIN EXECUTE 'SELECT 1'; END $$;\n"
            'DROP TABLE IF EXISTS "a_001_base";\n'
        )
        report = audit_complete_table_script(dynamic_sql)
        self.assertFalse(report.passed)
        self.assertTrue(report.manual_review_reasons)

        unquoted_dynamic = (
            "DROP TABLE IF EXISTS a_001_base;\n"
            "CREATE TABLE a_001_base(id integer);\n"
            "DO $$ BEGIN EXECUTE 'SELECT 1'; END $$;\n"
            "DROP TABLE IF EXISTS a_001_base;\n"
        )
        report = audit_complete_table_script(unquoted_dynamic)
        self.assertFalse(report.passed)
        self.assertIn("dynamic SQL", " ".join(report.manual_review_reasons))

    def test_auditor_does_not_rewrite_input_and_reports_cleanup_order(self) -> None:
        sql = (
            "DROP TABLE IF EXISTS a_001_base, a_001_child;\n"
            "CREATE TABLE a_001_base(id integer);\n"
            "CREATE TABLE a_001_child(id integer);\n"
            "DROP TABLE IF EXISTS a_001_base, a_001_child;\n"
        )
        original = sql[:]

        report = audit_complete_table_script(sql)

        self.assertEqual(original, sql)
        self.assertTrue(report.passed)
        self.assertIn("reverse", " ".join(report.warnings))


if __name__ == "__main__":
    unittest.main()
