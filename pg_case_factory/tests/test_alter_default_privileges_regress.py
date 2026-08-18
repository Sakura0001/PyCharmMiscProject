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


class AlterDefaultPrivilegesRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = discover_statement_factor_cycle(REPOSITORY_ROOT)
        cls.plan = build_statement_regress_plan(
            cls.snapshot, "alter_default_privileges"
        )

    def test_conditional_products_are_exact_and_not_sampled(self) -> None:
        self.assertEqual(4271, len(self.plan.cases))
        self.assertEqual(
            {
                "official_core_product": 3528,
                "authorization_truth_product": 168,
                "missing_target_role_product": 56,
                "missing_schema_product": 40,
                "schema_class_conflict_product": 32,
                "recipient_existence_product": 112,
                "invalid_privilege_product": 118,
                "column_privilege_product": 4,
                "additive_semantics_product": 15,
                "existing_object_unchanged_product": 14,
                "recipient_shape_product": 98,
                "quoted_schema_product": 20,
                "multiple_target_atomicity_product": 14,
                "multiple_schema_atomicity_product": 10,
                "multiple_recipient_atomicity_product": 14,
                "transactional_rollback_product": 14,
                "parser_boundary_product": 10,
                "pg18_reference_product": 4,
            },
            Counter(case.case_group for case in self.plan.cases),
        )
        self.assertEqual(
            tuple(range(1, 4272)), tuple(case.ordinal for case in self.plan.cases)
        )
        self.assertEqual(4271, len({case.case_id for case in self.plan.cases}))
        self.assertEqual(4271, len({case.sql_filename for case in self.plan.cases}))

    def test_all_77_canonical_factor_values_have_real_unique_witnesses(self) -> None:
        self.assertEqual(77, len(self.plan.factor_decisions))
        self.assertEqual(77, len({row.row_id for row in self.plan.factor_decisions}))
        cases = {case.case_id: case for case in self.plan.cases}
        for row in self.plan.factor_decisions:
            self.assertNotEqual("justified_na", row.disposition, row.row_id)
            self.assertTrue(row.case_ids, row.row_id)
            for case_id in row.case_ids:
                self.assertIn(
                    f"{row.factor}={row.value}",
                    cases[case_id].factor_values,
                    row.row_id,
                )
        for case in self.plan.cases:
            keys = [token.split("=", 1)[0] for token in case.factor_values]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)

    def test_official_core_is_the_full_applicable_conditional_product(self) -> None:
        core = [
            case for case in self.plan.cases
            if case.case_group == "official_core_product"
        ]
        self.assertEqual(3528, len(core))
        self.assertEqual(
            3528,
            len(
                {
                    (
                        case.derived_axes["operation"],
                        case.derived_axes["object_class"],
                        case.derived_axes["privilege_binding"],
                        case.derived_axes["action_mode"],
                        case.derived_axes["for_scope"],
                        case.derived_axes["target_shape"],
                        case.derived_axes["schema_scope"],
                    )
                    for case in core
                }
            ),
        )
        for case in core:
            if case.derived_axes["object_class"] in {"SCHEMAS", "LARGE_OBJECTS"}:
                self.assertEqual("omitted", case.derived_axes["schema_scope"])


class AlterDefaultPrivilegesRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        snapshot = discover_statement_factor_cycle(REPOSITORY_ROOT)
        cls.plan = build_statement_regress_plan(
            snapshot, "alter_default_privileges"
        )

    def test_every_case_has_one_phase_8_target_and_complete_oracles(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            primary = sql.split("-- 8. Primary target statement", 1)[1].split(
                "-- 9. SQLSTATE and primary-result oracle", 1
            )[0]
            self.assertEqual(
                1,
                len(re.findall(r"(?m)^ALTER\s+DEFAULT\s+PRIVILEGES\b", primary)),
                case.case_id,
            )
            self.assertGreaterEqual(len(re.findall(r"(?m)^-- \d+\. ", sql)), 12)
            self.assertIn("expected_SQLSTATE", sql, case.case_id)
            self.assertIn("pg_catalog.pg_default_acl", sql, case.case_id)
            self.assertIn("cleanup_complete", sql, case.case_id)
            self.assertNotRegex(sql, r"\{[A-Za-z_][A-Za-z0-9_]*\}")
            self.assertTrue(sql.endswith("\n"), case.case_id)
            self.assertFalse(sql.endswith("\n\n"), case.case_id)

    def test_representative_official_and_pg18_forms_are_real(self) -> None:
        all_sql = "\n".join(
            render_statement_regress_case(self.plan, case)
            for case in self.plan.cases
        )
        self.assertIn("FOR ROLE", all_sql)
        self.assertIn("FOR USER", all_sql)
        self.assertIn("IN SCHEMA", all_sql)
        self.assertIn("WITH GRANT OPTION", all_sql)
        self.assertIn("GRANT OPTION FOR", all_sql)
        self.assertIn(" CASCADE;", all_sql)
        self.assertIn(" RESTRICT;", all_sql)
        self.assertIn("MAINTAIN ON TABLES", all_sql)
        self.assertIn("ON LARGE OBJECTS", all_sql)
        self.assertIn("SELECT, UPDATE ON LARGE OBJECTS", all_sql)
        self.assertIn(r"\ddp", all_sql)
        self.assertIn("CREATE TABLE", all_sql)
        self.assertIn("payload text NOT NULL", all_sql)
        self.assertIn("CREATE SEQUENCE", all_sql)
        self.assertIn("CREATE FUNCTION", all_sql)
        self.assertIn("CREATE PROCEDURE", all_sql)
        self.assertIn("CREATE TYPE", all_sql)
        self.assertIn("lo_create", all_sql)

    def test_future_object_oracle_credits_direct_acl_not_inherited_public_acl(self) -> None:
        routine_revoke = next(
            case for case in self.plan.cases
            if case.case_group == "official_core_product"
            and case.derived_axes["object_class"] == "ROUTINES"
            and case.derived_axes["action_mode"] == "revoke_plain_default"
            and case.derived_axes["recipient"] == "simple"
            and case.outcome == "success"
        )
        sql = render_statement_regress_case(self.plan, routine_revoke)
        self.assertIn("pg_catalog.aclexplode", sql)
        self.assertIn("direct_acl_privilege_matches", sql)
        self.assertNotIn("has_function_privilege", sql)

        revoke_option = next(
            case for case in self.plan.cases
            if case.case_group == "official_core_product"
            and case.derived_axes["object_class"] == "FUNCTIONS"
            and case.derived_axes["action_mode"] == "revoke_option_default"
            and case.derived_axes["recipient"] == "simple"
            and case.outcome == "success"
        )
        option_sql = render_statement_regress_case(self.plan, revoke_option)
        self.assertIn("direct_acl_privilege_matches", option_sql)
        self.assertIn("direct_acl_grant_option_matches", option_sql)
        self.assertIn("= true AS direct_acl_privilege_matches", option_sql)
        self.assertIn("= false AS direct_acl_grant_option_matches", option_sql)


class AlterDefaultPrivilegesRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = root / "first"
            second = root / "second"
            first_evidence = root / "first-evidence"
            second_evidence = root / "second-evidence"
            first_result = generate_statement_regress_package(
                REPOSITORY_ROOT,
                "alter_default_privileges",
                output_dir=first,
                evidence_dir=first_evidence,
            )
            second_result = generate_statement_regress_package(
                REPOSITORY_ROOT,
                "alter_default_privileges",
                output_dir=second,
                evidence_dir=second_evidence,
            )
            self.assertEqual(4271, first_result.sql_file_count)
            self.assertEqual(first_result.sql_sha256, second_result.sql_sha256)
            for relative in sorted(first_result.sql_sha256):
                self.assertEqual(
                    (first / relative).read_bytes(),
                    (second / relative).read_bytes(),
                    relative,
                )
            for relative in (
                "plan.json", "coverage.json", "package.json", "validation.json"
            ):
                self.assertEqual(
                    (first_evidence / relative).read_bytes(),
                    (second_evidence / relative).read_bytes(),
                    relative,
                )


if __name__ == "__main__":
    unittest.main()
