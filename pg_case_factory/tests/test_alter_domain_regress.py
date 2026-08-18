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


class AlterDomainRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = discover_statement_factor_cycle(REPOSITORY_ROOT)
        cls.plan = build_statement_regress_plan(cls.snapshot, "alter_domain")

    def test_conditional_products_are_exact_and_not_sampled(self) -> None:
        self.assertEqual(908, len(self.plan.cases))
        self.assertEqual(
            {
                "official_success_product": 168,
                "type_inventory_product": 595,
                "missing_domain_product": 11,
                "privilege_truth_product": 33,
                "add_constraint_failure_product": 8,
                "constraint_lookup_product": 11,
                "container_block_product": 9,
                "null_value_block_product": 1,
                "owner_truth_product": 12,
                "owner_missing_role_product": 2,
                "set_schema_truth_product": 6,
                "schema_state_product": 4,
                "rename_state_product": 6,
                "same_target_product": 12,
                "default_existing_rows_product": 6,
                "transactional_rollback_product": 11,
                "parser_boundary_product": 12,
                "concurrent_hazard_product": 1,
            },
            Counter(case.case_group for case in self.plan.cases),
        )
        self.assertEqual(tuple(range(1, 909)), tuple(c.ordinal for c in self.plan.cases))
        self.assertEqual(908, len({c.case_id for c in self.plan.cases}))
        self.assertEqual(908, len({c.sql_filename for c in self.plan.cases}))

    def test_all_109_factor_values_have_real_unique_witnesses(self) -> None:
        self.assertEqual(109, len(self.plan.factor_decisions))
        cases = {case.case_id: case for case in self.plan.cases}
        for row in self.plan.factor_decisions:
            self.assertNotEqual("justified_na", row.disposition, row.row_id)
            self.assertTrue(row.case_ids, row.row_id)
            for case_id in row.case_ids:
                self.assertIn(f"{row.factor}={row.value}", cases[case_id].factor_values)
        for case in self.plan.cases:
            keys = [token.split("=", 1)[0] for token in case.factor_values]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)

    def test_every_executable_type_profile_is_bound_to_all_sensitive_forms(self) -> None:
        rows = [c for c in self.plan.cases if c.case_group == "type_inventory_product"]
        self.assertEqual(85, len({c.derived_axes["type_key"] for c in rows}))
        self.assertEqual(7, len({c.derived_axes["type_form"] for c in rows}))
        self.assertEqual(
            595,
            len({(c.derived_axes["type_key"], c.derived_axes["type_form"]) for c in rows}),
        )


class AlterDomainRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        snapshot = discover_statement_factor_cycle(REPOSITORY_ROOT)
        cls.plan = build_statement_regress_plan(snapshot, "alter_domain")

    def test_every_case_has_one_phase_8_target_and_complete_oracles(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            primary = sql.split("-- 8. Primary target statement", 1)[1].split(
                "-- 9. SQLSTATE and primary-result oracle", 1
            )[0]
            self.assertEqual(1, len(re.findall(r"(?m)^ALTER\s+DOMAIN\b", primary)))
            self.assertIn("expected_SQLSTATE", sql)
            self.assertIn("pg_catalog.pg_type", sql)
            self.assertIn("cleanup_complete", sql)
            self.assertIn("payload text NOT NULL", sql)
            self.assertIn("amount numeric(18,2)", sql)
            self.assertNotRegex(sql, r"\{[A-Za-z_][A-Za-z0-9_]*\}")
            self.assertTrue(sql.endswith("\n"))
            self.assertFalse(sql.endswith("\n\n"))

    def test_container_and_concurrency_cases_are_real(self) -> None:
        all_sql = "\n".join(render_statement_regress_case(self.plan, c) for c in self.plan.cases)
        self.assertIn("CREATE TYPE", all_sql)
        self.assertIn("CREATE TYPE", all_sql)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS dblink", all_sql)
        self.assertIn("public.dblink_exec('worker', 'BEGIN ISOLATION LEVEL REPEATABLE READ')", all_sql)
        self.assertIn("ADD CONSTRAINT", all_sql)
        self.assertIn("NOT VALID", all_sql)
        self.assertIn("VALIDATE CONSTRAINT", all_sql)


class AlterDomainRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = root / "first"
            second = root / "second"
            first_evidence = root / "first-evidence"
            second_evidence = root / "second-evidence"
            first_result = generate_statement_regress_package(
                REPOSITORY_ROOT,
                "alter_domain",
                output_dir=first,
                evidence_dir=first_evidence,
            )
            second_result = generate_statement_regress_package(
                REPOSITORY_ROOT,
                "alter_domain",
                output_dir=second,
                evidence_dir=second_evidence,
            )
            self.assertEqual(908, first_result.sql_file_count)
            self.assertEqual(first_result.sql_sha256, second_result.sql_sha256)
            for relative in sorted(first_result.sql_sha256):
                self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes())
            for relative in ("plan.json", "coverage.json", "package.json", "validation.json"):
                self.assertEqual(
                    (first_evidence / relative).read_bytes(),
                    (second_evidence / relative).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
