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


class AlterExtensionRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_statement_regress_plan(
            discover_statement_factor_cycle(REPOSITORY_ROOT), "alter_extension"
        )

    def test_exact_conditional_products(self) -> None:
        self.assertEqual(416, len(self.plan.cases))
        self.assertEqual(
            {
                "update_version_product": 10,
                "set_schema_product": 12,
                "member_lexical_product": 146,
                "member_state_product": 112,
                "privilege_truth_product": 18,
                "missing_extension_product": 4,
                "member_signature_product": 64,
                "parser_boundary_product": 16,
                "transactional_rollback_product": 4,
                "cross_extension_membership_product": 28,
                "same_schema_noop_product": 2,
            },
            Counter(case.case_group for case in self.plan.cases),
        )
        self.assertEqual(tuple(range(1, 417)), tuple(c.ordinal for c in self.plan.cases))
        self.assertEqual(416, len({c.case_id for c in self.plan.cases}))

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

    def test_all_official_member_object_kinds_are_in_both_actions(self) -> None:
        official = {
            "access_method", "aggregate", "cast", "collation", "conversion",
            "domain", "event_trigger", "foreign_data_wrapper", "foreign_table",
            "function", "materialized_view", "operator", "operator_class",
            "operator_family", "language", "procedure", "routine", "schema",
            "sequence", "server", "table", "text_search_configuration",
            "text_search_dictionary", "text_search_parser",
            "text_search_template", "transform", "type", "view",
        }
        rows = [c for c in self.plan.cases if c.case_group == "member_lexical_product"]
        self.assertEqual(official, {c.derived_axes["member_kind"] for c in rows})
        for action in ("add", "drop"):
            self.assertEqual(
                official,
                {c.derived_axes["member_kind"] for c in rows if c.derived_axes["branch"] == action},
            )


class AlterExtensionRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_statement_regress_plan(
            discover_statement_factor_cycle(REPOSITORY_ROOT), "alter_extension"
        )

    def test_every_case_has_one_phase_8_target_and_real_oracles(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            primary = sql.split("-- 8. Primary target statement", 1)[1].split(
                "-- 9. SQLSTATE and primary-result oracle", 1
            )[0]
            self.assertEqual(1, len(re.findall(r"(?m)^ALTER\s+EXTENSION\b", primary)))
            self.assertIn("expected_SQLSTATE", sql)
            self.assertIn("pg_catalog.pg_extension", sql)
            self.assertIn("cleanup_complete", sql)
            self.assertNotRegex(sql, r"\{[A-Za-z_][A-Za-z0-9_]*\}")
            self.assertTrue(sql.endswith("\n"))
            self.assertFalse(sql.endswith("\n\n"))

    def test_relation_member_fixtures_have_complete_columns(self) -> None:
        relation_kinds = {"table", "foreign_table", "materialized_view", "view"}
        for case in self.plan.cases:
            if case.derived_axes.get("member_kind") not in relation_kinds:
                continue
            if case.derived_axes.get("branch") not in {"add", "drop"}:
                continue
            if case.case_group == "parser_boundary_product":
                continue
            if case.derived_axes.get("member_state") == "object_missing":
                continue
            sql = render_statement_regress_case(self.plan, case)
            self.assertIn("id bigint NOT NULL", sql)
            self.assertIn("code text NOT NULL", sql)
            self.assertIn("payload jsonb NOT NULL", sql)
            self.assertIn("created_at timestamp with time zone NOT NULL", sql)
            self.assertIn("status smallint NOT NULL", sql)

    def test_signature_boundaries_use_executable_fixtures_and_exact_sqlstate(self) -> None:
        out_cases = [
            case
            for case in self.plan.cases
            if case.derived_axes.get("signature_form") == "out_ignored"
            and case.derived_axes.get("member_kind") == "function"
        ]
        self.assertEqual(2, len(out_cases))
        for case in out_cases:
            sql = render_statement_regress_case(self.plan, case)
            self.assertIn(
                "OUT result text)  LANGUAGE sql AS $$ SELECT COALESCE($1, 0)::text $$;",
                sql,
            )

        postfix_cases = [
            case
            for case in self.plan.cases
            if case.derived_axes.get("signature_form") == "right_none"
        ]
        self.assertEqual(2, len(postfix_cases))
        for case in postfix_cases:
            self.assertEqual("expected_failure", case.outcome)
            self.assertEqual("42601", case.derived_axes["expected_sqlstate"])


class AlterExtensionRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = generate_statement_regress_package(
                REPOSITORY_ROOT, "alter_extension",
                output_dir=root / "first", evidence_dir=root / "first-evidence",
            )
            second = generate_statement_regress_package(
                REPOSITORY_ROOT, "alter_extension",
                output_dir=root / "second", evidence_dir=root / "second-evidence",
            )
            self.assertEqual(416, first.sql_file_count)
            self.assertEqual(first.sql_sha256, second.sql_sha256)
            for relative in first.sql_sha256:
                self.assertEqual((root / "first" / relative).read_bytes(), (root / "second" / relative).read_bytes())
            for relative in ("plan.json", "coverage.json", "package.json", "validation.json"):
                self.assertEqual((root / "first-evidence" / relative).read_bytes(), (root / "second-evidence" / relative).read_bytes())


if __name__ == "__main__":
    unittest.main()
