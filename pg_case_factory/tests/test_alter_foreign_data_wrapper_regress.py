from __future__ import annotations

import itertools
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


class AlterForeignDataWrapperRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_statement_regress_plan(
            discover_statement_factor_cycle(REPOSITORY_ROOT),
            "alter_foreign_data_wrapper",
        )

    def test_exact_conditional_products(self) -> None:
        self.assertEqual(155, len(self.plan.cases))
        self.assertEqual(
            {
                "change_clause_product": 72,
                "owner_target_product": 10,
                "rename_target_product": 4,
                "missing_fdw_product": 3,
                "privilege_truth_product": 6,
                "function_existence_product": 4,
                "validator_compatibility_product": 9,
                "option_shape_operation_product": 8,
                "option_state_boundary_product": 6,
                "owner_boundary_product": 4,
                "rename_conflict_product": 4,
                "handler_access_product": 2,
                "support_signature_product": 4,
                "parser_boundary_product": 12,
                "transactional_rollback_product": 3,
                "single_clause_product": 4,
            },
            Counter(case.case_group for case in self.plan.cases),
        )
        self.assertEqual(tuple(range(1, 156)), tuple(c.ordinal for c in self.plan.cases))
        self.assertEqual(155, len({c.case_id for c in self.plan.cases}))
        self.assertEqual(0, len(self.plan.external_cases))

    def test_change_branch_is_the_exact_applicable_cartesian_product(self) -> None:
        rows = [c for c in self.plan.cases if c.case_group == "change_clause_product"]
        actual = {
            (
                c.derived_axes["fdw_name_shape"],
                c.derived_axes["handler_change"],
                c.derived_axes["validator_change"],
                c.derived_axes["options_operation"],
            )
            for c in rows
        }
        expected = set(
            itertools.product(
                ("simple_id", "quoted_id"),
                ("omitted", "specified_new_handler", "no_handler"),
                ("omitted", "specified_new_validator", "no_validator"),
                ("add_option", "set_option", "drop_option", "combined_operations"),
            )
        )
        self.assertEqual(expected, actual)

    def test_all_67_canonical_values_have_real_unique_witnesses(self) -> None:
        self.assertEqual(67, len(self.plan.factor_decisions))
        cases = {case.case_id: case for case in self.plan.cases}
        for row in self.plan.factor_decisions:
            self.assertNotEqual("justified_na", row.disposition)
            self.assertTrue(row.case_ids, row.row_id)
            for case_id in row.case_ids:
                self.assertIn(f"{row.factor}={row.value}", cases[case_id].factor_values)
        for case in self.plan.cases:
            keys = [token.split("=", 1)[0] for token in case.factor_values]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)


class AlterForeignDataWrapperRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_statement_regress_plan(
            discover_statement_factor_cycle(REPOSITORY_ROOT),
            "alter_foreign_data_wrapper",
        )

    def test_every_case_has_one_phase_8_target_and_real_oracles(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            primary = sql.split("-- 8. Primary target statement", 1)[1].split(
                "-- 9. SQLSTATE and primary-result oracle", 1
            )[0]
            self.assertEqual(
                1,
                len(re.findall(r"(?m)^ALTER\s+FOREIGN\s+DATA\s+WRAPPER\b", primary)),
            )
            self.assertIn("expected_SQLSTATE", sql)
            self.assertIn("pg_catalog.pg_foreign_data_wrapper", sql)
            self.assertIn("cleanup_complete", sql)
            self.assertNotRegex(sql, r"\{[A-Za-z_][A-Za-z0-9_]*\}")
            self.assertTrue(sql.endswith("\n"))
            self.assertFalse(sql.endswith("\n\n"))

    def test_server_proven_option_and_handler_boundaries_are_exact(self) -> None:
        by_boundary = {
            case.derived_axes.get("option_boundary"): case
            for case in self.plan.cases
            if case.case_group == "option_state_boundary_product"
        }
        duplicate = by_boundary["duplicate_names"]
        self.assertEqual("42710", duplicate.derived_axes["expected_sqlstate"])
        self.assertIn(
            "ADD duplicate_option 'one', ADD duplicate_option 'two'",
            render_statement_regress_case(self.plan, duplicate),
        )
        wrong_handler = next(
            case
            for case in self.plan.cases
            if case.derived_axes.get("support_signature") == "handler_wrong_return"
        )
        self.assertEqual("42809", wrong_handler.derived_axes["expected_sqlstate"])

    def test_foreign_table_boundaries_have_complete_column_structures(self) -> None:
        rows = [
            case
            for case in self.plan.cases
            if case.case_group in {"handler_access_product", "validator_compatibility_product"}
            and case.derived_axes.get("dependency_scope") == "foreign_table"
            or case.case_group == "handler_access_product"
        ]
        self.assertTrue(rows)
        for case in rows:
            sql = render_statement_regress_case(self.plan, case)
            self.assertIn("id bigint NOT NULL", sql)
            self.assertIn("code text NOT NULL", sql)
            self.assertIn("payload jsonb NOT NULL", sql)
            self.assertIn("created_at timestamp with time zone NOT NULL", sql)
            self.assertIn("status smallint NOT NULL", sql)


class AlterForeignDataWrapperRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = generate_statement_regress_package(
                REPOSITORY_ROOT,
                "alter_foreign_data_wrapper",
                output_dir=root / "first",
                evidence_dir=root / "first-evidence",
            )
            second = generate_statement_regress_package(
                REPOSITORY_ROOT,
                "alter_foreign_data_wrapper",
                output_dir=root / "second",
                evidence_dir=root / "second-evidence",
            )
            self.assertEqual(155, first.sql_file_count)
            self.assertEqual(first.sql_sha256, second.sql_sha256)
            for relative in first.sql_sha256:
                self.assertEqual(
                    (root / "first" / relative).read_bytes(),
                    (root / "second" / relative).read_bytes(),
                )
            for relative in ("plan.json", "coverage.json", "package.json", "validation.json"):
                self.assertEqual(
                    (root / "first-evidence" / relative).read_bytes(),
                    (root / "second-evidence" / relative).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
