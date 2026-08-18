from __future__ import annotations

import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from pg_case_factory.remaining_statement_regress import (
    build_statement_regress_plan,
    generate_statement_regress_package,
    render_statement_regress_case,
)
from pg_case_factory.statement_factor_cycle import discover_statement_factor_cycle


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class AlterDatabaseRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = discover_statement_factor_cycle(REPOSITORY_ROOT)
        cls.plan = build_statement_regress_plan(cls.snapshot, "alter_database")

    def test_conditional_products_are_exact_and_not_sampled(self) -> None:
        self.assertEqual(1420, len(self.plan.cases))
        self.assertEqual(
            {
                "with_options_product": 456,
                "rename_product": 183,
                "owner_named_product": 120,
                "owner_rolespec_product": 93,
                "set_tablespace_product": 148,
                "refresh_collation_product": 19,
                "set_parameter_product": 228,
                "set_from_current_product": 76,
                "reset_parameter_product": 76,
                "reset_all_product": 19,
                "file_copy_method_product": 2,
            },
            Counter(case.case_group for case in self.plan.cases),
        )
        self.assertEqual(
            tuple(range(1, 1421)),
            tuple(case.ordinal for case in self.plan.cases),
        )
        self.assertEqual(1420, len({case.case_id for case in self.plan.cases}))
        self.assertEqual(1420, len({case.sql_filename for case in self.plan.cases}))

    def test_all_90_canonical_factor_values_have_real_unique_witnesses(self) -> None:
        self.assertEqual(90, len(self.plan.factor_decisions))
        self.assertEqual(90, len({row.row_id for row in self.plan.factor_decisions}))
        cases = {case.case_id: case for case in self.plan.cases}
        for row in self.plan.factor_decisions:
            self.assertNotEqual("justified_na", row.disposition, row.row_id)
            self.assertTrue(row.case_ids, row.row_id)
            for case_id in row.case_ids:
                case = cases[case_id]
                self.assertIn(f"{row.factor}={row.value}", case.factor_values, row.row_id)
        for case in self.plan.cases:
            assignments = [token.split("=", 1)[0] for token in case.factor_values]
            self.assertEqual(len(assignments), len(set(assignments)), case.case_id)

    def test_all_official_branch_and_state_projections_are_present(self) -> None:
        branches = {
            token.split("=", 1)[1]
            for case in self.plan.cases
            for token in case.factor_values
            if token.startswith("statement_branch=")
        }
        self.assertEqual(
            {
                "branch_with_options",
                "branch_rename",
                "branch_owner",
                "branch_set_tablespace",
                "branch_refresh_collation_version",
                "branch_set_parameter",
                "branch_set_from_current",
                "branch_reset_parameter",
                "branch_reset_all",
            },
            branches,
        )
        for branch in branches:
            cases = [
                case
                for case in self.plan.cases
                if f"statement_branch={branch}" in case.factor_values
            ]
            self.assertEqual(
                {"exists", "is_current_database", "not_exists"},
                {
                    token.split("=", 1)[1]
                    for case in cases
                    for token in case.factor_values
                    if token.startswith("object_state=")
                },
                branch,
            )
            self.assertEqual(
                {"success", "failure"},
                {
                    token.split("=", 1)[1]
                    for case in cases
                    for token in case.factor_values
                    if token.startswith("expected_status=")
                },
                branch,
            )

    def test_rename_connection_failure_follows_pg18_check_order(self) -> None:
        case = next(
            case
            for case in self.plan.cases
            if case.case_group == "rename_product"
            and case.derived_axes.get("source") == "different_simple"
            and case.derived_axes.get("actor") == "superuser"
            and case.derived_axes.get("createdb") == "has_createdb"
            and case.derived_axes.get("new_name_shape") == "simple_id"
            and case.derived_axes.get("rename_conflict") == "new_name_unique"
            and case.derived_axes.get("connection_state") == "has_connections"
        )
        self.assertEqual("expected_failure", case.outcome)
        self.assertEqual("55006", case.derived_axes["expected_sqlstate"])

    def test_session_user_rolespec_does_not_take_same_owner_early_return(self) -> None:
        same_owner = next(
            case
            for case in self.plan.cases
            if case.case_group == "owner_rolespec_product"
            and case.derived_axes.get("source") == "different_simple"
            and case.derived_axes.get("actor") == "database_owner"
            and case.derived_axes.get("new_owner_target") == "CURRENT_USER"
            and case.derived_axes.get("createdb") == "lacks_createdb"
            and case.derived_axes.get("connection_state") == "no_connections"
        )
        session_user = next(
            case
            for case in self.plan.cases
            if case.case_group == "owner_rolespec_product"
            and case.derived_axes.get("source") == "different_simple"
            and case.derived_axes.get("actor") == "database_owner"
            and case.derived_axes.get("new_owner_target") == "SESSION_USER"
            and case.derived_axes.get("createdb") == "lacks_createdb"
            and case.derived_axes.get("connection_state") == "no_connections"
        )
        self.assertEqual("success", same_owner.outcome)
        self.assertEqual("expected_failure", session_user.outcome)
        self.assertEqual("42501", session_user.derived_axes["expected_sqlstate"])


class AlterDatabaseRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        snapshot = discover_statement_factor_cycle(REPOSITORY_ROOT)
        cls.plan = build_statement_regress_plan(snapshot, "alter_database")

    def test_every_case_is_complete_and_has_one_primary_target(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            self.assertEqual(
                1,
                len(re.findall(r"(?m)^ALTER\s+DATABASE\b", sql)),
                case.case_id,
            )
            self.assertGreaterEqual(len(re.findall(r"(?m)^-- \d+\. ", sql)), 7)
            self.assertIn("expected_SQLSTATE", sql, case.case_id)
            self.assertIn("cleanup_complete", sql, case.case_id)
            self.assertIn("pg_catalog.pg_database", sql, case.case_id)
            self.assertNotRegex(sql, r"(?im)^CREATE\s+(?:TEMP\s+)?TABLE\s", case.case_id)
            self.assertNotRegex(sql, r"\{[A-Za-z_][A-Za-z0-9_]*\}")
            self.assertTrue(sql.endswith("\n"), case.case_id)
            self.assertFalse(sql.endswith("\n\n"), case.case_id)

    def test_representative_official_forms_and_harnesses_are_real(self) -> None:
        rendered = {
            case.case_id: render_statement_regress_case(self.plan, case)
            for case in self.plan.cases
        }
        all_sql = "\n".join(rendered.values())
        self.assertRegex(all_sql, r"ALTER DATABASE .* WITH ALLOW_CONNECTIONS true")
        self.assertRegex(all_sql, r"ALTER DATABASE .* ALLOW_CONNECTIONS false")
        self.assertIn("CONNECTION LIMIT -1", all_sql)
        self.assertIn("IS_TEMPLATE true", all_sql)
        self.assertIn("RENAME TO \"select\"", all_sql)
        self.assertIn("OWNER TO CURRENT_ROLE", all_sql)
        self.assertIn("OWNER TO CURRENT_USER", all_sql)
        self.assertIn("OWNER TO SESSION_USER", all_sql)
        self.assertIn("SET TABLESPACE", all_sql)
        self.assertIn("REFRESH COLLATION VERSION", all_sql)
        self.assertRegex(all_sql, r" SET [a-z_]+ TO ")
        self.assertRegex(all_sql, r" SET [a-z_]+ = ")
        self.assertRegex(all_sql, r" SET [a-z_]+ TO DEFAULT")
        self.assertIn("FROM CURRENT", all_sql)
        self.assertRegex(all_sql, r"RESET [a-z_]+;")
        self.assertIn("RESET ALL", all_sql)
        self.assertIn("file_copy_method = 'copy'", all_sql)
        self.assertIn("file_copy_method = 'clone'", all_sql)
        self.assertIn("public.dblink_connect", all_sql)
        self.assertIn("alterdatabase_tablespace_location", all_sql)


class AlterDatabaseRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = root / "first"
            second = root / "second"
            first_evidence = root / "first-evidence"
            second_evidence = root / "second-evidence"
            first_result = generate_statement_regress_package(
                REPOSITORY_ROOT,
                "alter_database",
                output_dir=first,
                evidence_dir=first_evidence,
            )
            second_result = generate_statement_regress_package(
                REPOSITORY_ROOT,
                "alter_database",
                output_dir=second,
                evidence_dir=second_evidence,
            )
            self.assertEqual(1420, first_result.sql_file_count)
            self.assertEqual(1420, second_result.sql_file_count)
            self.assertEqual(first_result.sql_sha256, second_result.sql_sha256)
            for relative in sorted(first_result.sql_sha256):
                self.assertEqual(
                    (first / relative).read_bytes(),
                    (second / relative).read_bytes(),
                    relative,
                )
            for relative in ("plan.json", "coverage.json", "package.json", "validation.json"):
                self.assertEqual(
                    (first_evidence / relative).read_bytes(),
                    (second_evidence / relative).read_bytes(),
                    relative,
                )


if __name__ == "__main__":
    unittest.main()
