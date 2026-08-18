from __future__ import annotations

import json
from pathlib import Path
import re
import tempfile
import unittest

from pg_case_factory.regression_style import audit_complete_table_script
from pg_case_factory.remaining_statement_regress import (
    RemainingStatementRegressError,
    build_statement_regress_plan,
    generate_statement_regress_package,
    render_statement_regress_case,
    validate_statement_regress_package,
)
from pg_case_factory.statement_factor_cycle import discover_statement_factor_cycle


ROOT = Path(__file__).resolve().parents[1]


class AbortRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = discover_statement_factor_cycle(ROOT)
        cls.plan = build_statement_regress_plan(cls.snapshot, "abort")

    def test_abort_plan_uses_the_exact_official_products(self) -> None:
        self.assertEqual("abort", self.plan.statement_key)
        self.assertEqual("ABORT", self.plan.file_prefix)
        self.assertEqual(61, len(self.plan.cases))
        self.assertEqual(
            {
                "legal_syntax_state_product": 36,
                "chain_characteristics_product": 16,
                "transactional_ddl": 1,
                "syntax_boundary": 5,
                "prepared_transaction_noninterference": 3,
            },
            self.plan.case_group_counts,
        )

        core = [
            case
            for case in self.plan.cases
            if case.case_group == "legal_syntax_state_product"
        ]
        self.assertEqual(
            36,
            len(
                {
                    (
                        case.derived_axes["optional_keyword"],
                        case.derived_axes["chain_clause"],
                        case.derived_axes["transaction_state"],
                    )
                    for case in core
                }
            ),
        )
        characteristics = [
            case
            for case in self.plan.cases
            if case.case_group == "chain_characteristics_product"
        ]
        self.assertEqual(
            16,
            len(
                {
                    (
                        case.derived_axes["isolation"],
                        case.derived_axes["access_mode"],
                        case.derived_axes["deferrability"],
                    )
                    for case in characteristics
                }
            ),
        )

    def test_abort_plan_accounts_for_every_canonical_factor_value_once(self) -> None:
        abort_entry = next(
            entry for entry in self.snapshot.entries if entry.statement_key == "abort"
        )
        expected_rows = {
            row_id
            for factor in abort_entry.factors
            for row_id in factor.row_ids
        }
        decisions = {decision.row_id: decision for decision in self.plan.factor_decisions}

        self.assertEqual(43, len(decisions))
        self.assertEqual(expected_rows, set(decisions))
        self.assertEqual(
            {"covered": 31, "expected_failure": 3, "justified_na": 9},
            self.plan.factor_disposition_counts,
        )
        for decision in decisions.values():
            if decision.disposition == "justified_na":
                self.assertTrue(decision.reason)
                self.assertEqual((), decision.case_ids)
            else:
                self.assertTrue(decision.case_ids)


class AbortRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        snapshot = discover_statement_factor_cycle(ROOT)
        cls.plan = build_statement_regress_plan(snapshot, "abort")

    def case(self, group: str, **axes: str):
        matches = [
            case
            for case in self.plan.cases
            if case.case_group == group
            and all(case.derived_axes.get(key) == value for key, value in axes.items())
        ]
        self.assertEqual(1, len(matches), (group, axes))
        return matches[0]

    def test_active_failed_nested_idle_and_chain_programs_are_real(self) -> None:
        active = self.case(
            "legal_syntax_state_product",
            optional_keyword="omitted",
            chain_clause="omitted",
            transaction_state="active_clean",
        )
        failed = self.case(
            "legal_syntax_state_product",
            optional_keyword="WORK",
            chain_clause="AND NO CHAIN",
            transaction_state="active_failed",
        )
        nested = self.case(
            "legal_syntax_state_product",
            optional_keyword="TRANSACTION",
            chain_clause="AND CHAIN",
            transaction_state="active_with_nested_savepoints",
        )
        idle_error = self.case(
            "legal_syntax_state_product",
            optional_keyword="omitted",
            chain_clause="AND CHAIN",
            transaction_state="idle",
        )

        active_sql = render_statement_regress_case(self.plan, active)
        failed_sql = render_statement_regress_case(self.plan, failed)
        nested_sql = render_statement_regress_case(self.plan, nested)
        idle_sql = render_statement_regress_case(self.plan, idle_error)

        self.assertIn("\nABORT;\n", active_sql)
        self.assertIn("SELECT 1 / 0;", failed_sql)
        self.assertIn("setup_sqlstate :SQLSTATE", failed_sql)
        self.assertIn('SAVEPOINT "', nested_sql)
        self.assertIn("ABORT TRANSACTION AND CHAIN;", nested_sql)
        self.assertIn("chained_transaction_active", nested_sql)
        self.assertIn("ABORT AND CHAIN;", idle_sql)
        self.assertIn("'25P01'", idle_sql)
        self.assertNotIn("pg_sleep", active_sql + failed_sql + nested_sql + idle_sql)
        self.assertNotIn("\\!", active_sql + failed_sql + nested_sql + idle_sql)

    def test_characteristics_catalog_and_syntax_boundaries_have_unique_oracles(self) -> None:
        characteristic = self.case(
            "chain_characteristics_product",
            isolation="SERIALIZABLE",
            access_mode="READ ONLY",
            deferrability="DEFERRABLE",
        )
        catalog = self.case("transactional_ddl")
        syntax = self.case("syntax_boundary", syntax_error="target_operand")

        characteristic_sql = render_statement_regress_case(self.plan, characteristic)
        catalog_sql = render_statement_regress_case(self.plan, catalog)
        syntax_sql = render_statement_regress_case(self.plan, syntax)

        self.assertIn(
            "BEGIN ISOLATION LEVEL SERIALIZABLE, READ ONLY, DEFERRABLE;",
            characteristic_sql,
        )
        self.assertIn("characteristics_preserved", characteristic_sql)
        self.assertIn("transactional_ddl_was_discarded", catalog_sql)
        self.assertIn("ABORT abort_00058_target;", syntax_sql)
        self.assertIn("'42601'", syntax_sql)

    def test_prepared_transaction_factor_has_a_complete_external_fixture(self) -> None:
        prepared = self.case(
            "prepared_transaction_noninterference",
            chain_clause="AND CHAIN",
        )
        sql = render_statement_regress_case(self.plan, prepared)

        self.assertEqual("external_isolated", prepared.execution_profile)
        self.assertIn("PREPARE TRANSACTION", sql)
        self.assertIn("ABORT AND CHAIN;", sql)
        self.assertIn("prepared_transaction_preserved", sql)
        self.assertIn("ROLLBACK PREPARED", sql)
        self.assertIn("'25P01'", sql)

    def test_every_rendered_case_has_trace_stages_and_complete_table_cleanup(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            self.assertTrue(sql.startswith("-- --------------------------------------------------------\n"))
            self.assertTrue(sql.endswith("\n"))
            self.assertFalse(sql.endswith("\n\n"))
            self.assertIn(f"-- case_id: {case.case_id}", sql)
            self.assertIn("-- source_md:", sql)
            self.assertIn("-- factor_md:", sql)
            self.assertGreaterEqual(
                len(re.findall(r"^-- \d+\. ", sql, flags=re.MULTILINE)),
                3,
                case.case_id,
            )
            if "CREATE TABLE" in sql or "CREATE TEMP TABLE" in sql:
                audit = audit_complete_table_script(
                    sql,
                    expected_object_prefix=case.object_prefix,
                )
                self.assertTrue(audit.passed, (case.case_id, audit.to_dict()))


class AbortRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_output = root / "first" / "abort"
            first_evidence = root / "first-evidence"
            second_output = root / "second" / "abort"
            second_evidence = root / "second-evidence"

            first = generate_statement_regress_package(
                ROOT,
                "abort",
                output_dir=first_output,
                evidence_dir=first_evidence,
            )
            second = generate_statement_regress_package(
                ROOT,
                "abort",
                output_dir=second_output,
                evidence_dir=second_evidence,
            )

            self.assertTrue(first.passed, first.issues)
            self.assertTrue(second.passed, second.issues)
            self.assertEqual(61, len(list(first_output.glob("ABORT*.sql"))))
            self.assertTrue((first_output / "serial_schedule").is_file())
            self.assertTrue((first_output / "external_schedule").is_file())
            self.assertTrue((first_evidence / "validation.json").is_file())
            evidence = json.loads(
                (first_evidence / "validation.json").read_text(encoding="utf-8")
            )
            self.assertIs(True, evidence["passed"])
            self.assertEqual(61, evidence["sql_file_count"])
            self.assertEqual(43, evidence["factor_value_count"])

            validation = validate_statement_regress_package(
                ROOT,
                "abort",
                output_dir=first_output,
                evidence_dir=first_evidence,
            )
            self.assertTrue(validation.passed, validation.issues)

            first_files = {
                path.relative_to(first_output): path.read_bytes()
                for path in first_output.rglob("*")
                if path.is_file()
            }
            second_files = {
                path.relative_to(second_output): path.read_bytes()
                for path in second_output.rglob("*")
                if path.is_file()
            }
            self.assertEqual(first_files, second_files)

            for name in ("plan.json", "coverage.json", "package.json"):
                self.assertEqual(
                    (first_evidence / name).read_bytes(),
                    (second_evidence / name).read_bytes(),
                )

    def test_generation_refuses_to_overwrite_an_existing_statement_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "abort"
            evidence = root / "evidence"
            output.mkdir()
            with self.assertRaisesRegex(
                RemainingStatementRegressError,
                "output directory already exists",
            ):
                generate_statement_regress_package(
                    ROOT,
                    "abort",
                    output_dir=output,
                    evidence_dir=evidence,
                )


class AlterAggregateRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = discover_statement_factor_cycle(ROOT)
        cls.plan = build_statement_regress_plan(cls.snapshot, "alter_aggregate")

    def test_compatibility_filtered_products_and_official_signature_spellings_are_exact(self) -> None:
        self.assertEqual("ALTERAGGREGATE", self.plan.file_prefix)
        self.assertEqual(783, len(self.plan.cases))
        self.assertEqual(
            {
                "failure_owner_unavailable_product": 126,
                "failure_rename_conflict_product": 126,
                "failure_set_schema_state_product": 84,
                "function_conflict_product": 28,
                "lookup_failure_product": 12,
                "order_boundary_compatibility_product": 6,
                "owner_privilege_truth_product": 12,
                "rename_schema_privilege_product": 6,
                "same_owner_noop_product": 3,
                "same_schema_noop_product": 6,
                "set_schema_privilege_product": 6,
                "success_owner_product": 168,
                "success_rename_product": 126,
                "success_set_schema_product": 42,
                "syntax_type_object_boundary_product": 28,
                "system_schema_boundary_product": 4,
            },
            self.plan.case_group_counts,
        )

        branch_signature_status = {
            (
                next(value.split("=", 1)[1] for value in case.factor_values if value.startswith("statement_branch=")),
                next(value.split("=", 1)[1] for value in case.factor_values if value.startswith("aggregate_signature=")),
                next(value.split("=", 1)[1] for value in case.factor_values if value.startswith("expected_status=")),
            )
            for case in self.plan.cases
            if any(value.startswith("statement_branch=") for value in case.factor_values)
            and any(value.startswith("aggregate_signature=") for value in case.factor_values)
            and any(value.startswith("expected_status=") for value in case.factor_values)
        }
        self.assertEqual(
            {
                (branch, signature, status)
                for branch in ("branch_rename", "branch_owner", "branch_set_schema")
                for signature in (
                    "star_zero_arg",
                    "single_argtype",
                    "multi_argtype",
                    "ordered_set_signature",
                    "abbreviated_ordered_set",
                )
                for status in ("success", "failure")
            },
            branch_signature_status,
        )

    def test_all_52_canonical_values_have_real_witnesses(self) -> None:
        entry = next(
            item for item in self.snapshot.entries if item.statement_key == "alter_aggregate"
        )
        expected_rows = {
            row_id for factor in entry.factors for row_id in factor.row_ids
        }
        decisions = {decision.row_id: decision for decision in self.plan.factor_decisions}
        self.assertEqual(52, len(decisions))
        self.assertEqual(expected_rows, set(decisions))
        self.assertEqual(
            {"covered": 36, "expected_failure": 16, "justified_na": 0},
            self.plan.factor_disposition_counts,
        )
        self.assertTrue(all(decision.case_ids for decision in decisions.values()))


class AlterAggregateRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        snapshot = discover_statement_factor_cycle(ROOT)
        cls.plan = build_statement_regress_plan(snapshot, "alter_aggregate")

    def case(self, group: str, **axes: str):
        matches = [
            case
            for case in self.plan.cases
            if case.case_group == group
            and all(case.derived_axes.get(key) == value for key, value in axes.items())
        ]
        self.assertEqual(1, len(matches), (group, axes))
        return matches[0]

    def test_representative_success_failure_and_variadic_cases_are_executable_programs(self) -> None:
        rename = self.case(
            "success_rename_product",
            signature_id="s04_ordered_set",
            aggregate_name_shape="schema_qualified",
            new_name_shape="reserved_word",
        )
        owner = self.case(
            "success_owner_product",
            signature_id="s03_multi_arg",
            aggregate_name_shape="plain_identifier",
            owner_shape="plain_role",
        )
        conflict = self.case(
            "failure_set_schema_state_product",
            signature_id="s05_abbreviated_ordered_set",
            aggregate_name_shape="quoted_identifier",
            target_state="conflict",
        )
        variadic = self.case(
            "success_rename_product",
            signature_id="s12_ordered_variadic",
            aggregate_name_shape="plain_identifier",
            new_name_shape="plain_identifier",
        )
        ordinary_variadic = self.case(
            "success_rename_product",
            signature_id="s10_variadic",
            aggregate_name_shape="plain_identifier",
            new_name_shape="plain_identifier",
        )
        variadic_function_conflict = self.case(
            "function_conflict_product",
            branch="rename",
            signature_id="s12_ordered_variadic",
        )
        pg_temp_move_out = self.case(
            "system_schema_boundary_product",
            system_schema="pg_temp",
            direction="move_out",
        )
        ordinary_function_target = self.case(
            "syntax_type_object_boundary_product",
            branch="rename",
            boundary="ordinary_function_target",
        )
        order_boundary_owner = self.case(
            "order_boundary_compatibility_product",
            branch="owner",
            order_boundary="all_arguments_after_order_by",
        )

        rename_sql = render_statement_regress_case(self.plan, rename)
        owner_sql = render_statement_regress_case(self.plan, owner)
        conflict_sql = render_statement_regress_case(self.plan, conflict)
        variadic_sql = render_statement_regress_case(self.plan, variadic)
        ordinary_variadic_sql = render_statement_regress_case(
            self.plan, ordinary_variadic
        )
        variadic_function_conflict_sql = render_statement_regress_case(
            self.plan, variadic_function_conflict
        )
        pg_temp_move_out_sql = render_statement_regress_case(
            self.plan, pg_temp_move_out
        )
        ordinary_function_target_sql = render_statement_regress_case(
            self.plan, ordinary_function_target
        )
        order_boundary_owner_sql = render_statement_regress_case(
            self.plan, order_boundary_owner
        )

        self.assertIn("CREATE AGGREGATE", rename_sql)
        self.assertIn("ORDER BY", rename_sql)
        self.assertIn('RENAME TO "select";', rename_sql)
        self.assertIn("OWNER TO alteraggregate_", owner_sql)
        self.assertIn("GRANT", owner_sql)
        self.assertIn("'42723'", conflict_sql)
        self.assertIn('VARIADIC "any" ORDER BY VARIADIC "any"', variadic_sql)
        self.assertIn("rank_final", variadic_sql)
        self.assertIn("VARIADIC items integer[]", ordinary_variadic_sql)
        self.assertNotIn("VARIADIC values integer[]", ordinary_variadic_sql)
        self.assertIn(
            "AS 'hypothetical_rank_final';", variadic_function_conflict_sql
        )
        self.assertEqual(
            1,
            variadic_function_conflict_sql.count("DROP AGGREGATE IF EXISTS"),
        )
        self.assertIn(
            "n.oid = pg_catalog.pg_my_temp_schema()", pg_temp_move_out_sql
        )
        self.assertEqual(
            0, ordinary_function_target_sql.count("DROP AGGREGATE IF EXISTS")
        )
        self.assertIn(
            "pg_get_userbyid(p.proowner) = 'alteraggregate_00780_new_owner'",
            order_boundary_owner_sql,
        )
        self.assertNotIn("pg_sleep", rename_sql + owner_sql + conflict_sql + variadic_sql)
        self.assertNotRegex(rename_sql + owner_sql + conflict_sql + variadic_sql, r"\{[A-Za-z_][A-Za-z0-9_]*\}")

    def test_every_case_has_a_real_target_stages_oracle_and_reverse_cleanup(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            self.assertTrue(sql.startswith("-- --------------------------------------------------------\n"))
            self.assertTrue(sql.endswith("\n"))
            self.assertFalse(sql.endswith("\n\n"))
            self.assertIn(f"-- case_id: {case.case_id}", sql)
            self.assertGreaterEqual(
                len(re.findall(r"^-- \d+\. ", sql, flags=re.MULTILINE)),
                5,
                case.case_id,
            )
            self.assertRegex(sql, r"(?m)^ALTER\s+AGGREGATE\b")
            self.assertIn("cleanup_complete", sql)
            if case.outcome == "expected_failure":
                self.assertIn("SQLSTATE", sql)


class AlterAggregateRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_output = root / "first" / "alter_aggregate"
            first_evidence = root / "first-evidence"
            second_output = root / "second" / "alter_aggregate"
            second_evidence = root / "second-evidence"

            first = generate_statement_regress_package(
                ROOT,
                "alter_aggregate",
                output_dir=first_output,
                evidence_dir=first_evidence,
            )
            second = generate_statement_regress_package(
                ROOT,
                "alter_aggregate",
                output_dir=second_output,
                evidence_dir=second_evidence,
            )
            self.assertTrue(first.passed, first.issues)
            self.assertTrue(second.passed, second.issues)
            self.assertEqual(783, len(list(first_output.glob("ALTERAGGREGATE*.sql"))))
            self.assertEqual(52, first.factor_value_count)
            self.assertEqual(
                {
                    path.relative_to(first_output): path.read_bytes()
                    for path in first_output.rglob("*")
                    if path.is_file()
                },
                {
                    path.relative_to(second_output): path.read_bytes()
                    for path in second_output.rglob("*")
                    if path.is_file()
                },
            )
            validation = validate_statement_regress_package(
                ROOT,
                "alter_aggregate",
                output_dir=first_output,
                evidence_dir=first_evidence,
            )
            self.assertTrue(validation.passed, validation.issues)


class AlterCollationRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = discover_statement_factor_cycle(ROOT)
        cls.plan = build_statement_regress_plan(cls.snapshot, "alter_collation")

    def test_conditional_cartesian_products_are_exact(self) -> None:
        self.assertEqual("ALTERCOLLATION", self.plan.file_prefix)
        self.assertEqual(174, len(self.plan.cases))
        self.assertEqual(
            {
                "missing_object_product": 12,
                "owner_missing_role_product": 3,
                "owner_privilege_truth_product": 12,
                "owner_same_owner_noop_product": 3,
                "parser_namespace_boundary_product": 12,
                "refresh_privilege_truth_product": 3,
                "refresh_provider_boundary_product": 5,
                "rename_duplicate_product": 6,
                "rename_privilege_truth_product": 6,
                "rename_same_name_product": 3,
                "set_schema_conflict_product": 6,
                "set_schema_missing_product": 6,
                "set_schema_privilege_truth_product": 6,
                "set_schema_same_schema_product": 6,
                "success_owner_product": 36,
                "success_refresh_product": 9,
                "success_rename_product": 18,
                "success_set_schema_product": 18,
                "transactional_rollback_product": 4,
            },
            self.plan.case_group_counts,
        )

        rename = {
            (
                case.derived_axes["source_name_shape"],
                case.derived_axes["new_name_shape"],
                case.derived_axes["dependency_state"],
            )
            for case in self.plan.cases
            if case.case_group == "success_rename_product"
        }
        self.assertEqual(3 * 2 * 3, len(rename))
        owner = {
            (
                case.derived_axes["source_name_shape"],
                case.derived_axes["owner_shape"],
                case.derived_axes["dependency_state"],
            )
            for case in self.plan.cases
            if case.case_group == "success_owner_product"
        }
        self.assertEqual(3 * 4 * 3, len(owner))
        set_schema = {
            (
                case.derived_axes["source_name_shape"],
                case.derived_axes["target_schema_shape"],
                case.derived_axes["dependency_state"],
            )
            for case in self.plan.cases
            if case.case_group == "success_set_schema_product"
        }
        self.assertEqual(3 * 2 * 3, len(set_schema))
        refresh = {
            (
                case.derived_axes["source_name_shape"],
                case.derived_axes["dependency_state"],
            )
            for case in self.plan.cases
            if case.case_group == "success_refresh_product"
        }
        self.assertEqual(3 * 3, len(refresh))

        rename_same = [
            case
            for case in self.plan.cases
            if case.case_group == "rename_same_name_product"
        ]
        self.assertEqual({"plain_identifier", "quoted_identifier", "schema_qualified"}, {
            case.derived_axes["source_name_shape"] for case in rename_same
        })
        self.assertTrue(
            all(
                case.outcome == "expected_failure"
                and case.derived_axes["expected_sqlstate"] == "42710"
                for case in rename_same
            )
        )

        owner_same = [
            case
            for case in self.plan.cases
            if case.case_group == "owner_same_owner_noop_product"
        ]
        self.assertEqual(set(("superuser", "collation_owner", "non_owner")), {
            case.derived_axes["actor"] for case in owner_same
        })
        self.assertTrue(all(case.outcome == "success" for case in owner_same))

        same_schema = {
            (case.derived_axes["actor"], case.derived_axes["schema_create"]): case
            for case in self.plan.cases
            if case.case_group == "set_schema_same_schema_product"
        }
        self.assertEqual(
            {
                (actor, schema_create)
                for actor in ("superuser", "collation_owner", "non_owner")
                for schema_create in ("yes", "no")
            },
            set(same_schema),
        )
        for (actor, schema_create), case in same_schema.items():
            expected_success = actor == "superuser" or schema_create == "yes"
            self.assertEqual(
                "success" if expected_success else "expected_failure",
                case.outcome,
            )

        self.assertEqual(
            {
                "builtin_current_version",
                "default_collation",
                "system_c_collation",
                "libc_capability",
                "icu_stale_version",
            },
            {
                case.derived_axes["provider_boundary"]
                for case in self.plan.cases
                if case.case_group == "refresh_provider_boundary_product"
            },
        )
        provider_cases = {
            case.derived_axes["provider_boundary"]: case
            for case in self.plan.cases
            if case.case_group == "refresh_provider_boundary_product"
        }
        self.assertEqual("expected_failure", provider_cases["default_collation"].outcome)
        self.assertEqual("XX000", provider_cases["default_collation"].derived_axes["expected_sqlstate"])
        self.assertTrue(
            all(
                case.outcome == "success"
                and case.derived_axes["expected_sqlstate"] == "00000"
                for name, case in provider_cases.items()
                if name != "default_collation"
            )
        )
        three_part = [
            case
            for case in self.plan.cases
            if case.case_group == "parser_namespace_boundary_product"
            and case.derived_axes["boundary"].startswith("three_part_")
        ]
        self.assertEqual(4, len(three_part))
        self.assertTrue(
            all(case.derived_axes["expected_sqlstate"] == "0A000" for case in three_part)
        )
        self.assertEqual(
            {
                "three_part_refresh_version",
                "three_part_rename",
                "three_part_owner",
                "three_part_set_schema",
                "qualified_rename_target",
                "unquoted_reserved_rename_target",
                "qualified_owner_target",
                "qualified_set_schema_target",
                "pg_temp_move_into",
                "pg_temp_move_out",
                "pg_toast_move_into",
                "pg_toast_move_out",
            },
            {
                case.derived_axes["boundary"]
                for case in self.plan.cases
                if case.case_group == "parser_namespace_boundary_product"
            },
        )

    def test_all_47_canonical_values_have_real_witnesses(self) -> None:
        entry = next(
            item for item in self.snapshot.entries if item.statement_key == "alter_collation"
        )
        expected_rows = {
            row_id for factor in entry.factors for row_id in factor.row_ids
        }
        decisions = {decision.row_id: decision for decision in self.plan.factor_decisions}
        self.assertEqual(47, len(decisions))
        self.assertEqual(expected_rows, set(decisions))
        self.assertEqual(
            {"covered": 32, "expected_failure": 15, "justified_na": 0},
            self.plan.factor_disposition_counts,
        )
        self.assertTrue(all(decision.case_ids for decision in decisions.values()))
        actual_version_cases = [
            case
            for case in self.plan.cases
            if "verification_mode=pg_collation_actual_version_query"
            in case.factor_values
        ]
        self.assertTrue(actual_version_cases)
        self.assertTrue(
            all(
                case.derived_axes["branch"] == "refresh_version"
                for case in actual_version_cases
            )
        )
        for case in self.plan.cases:
            factor_names = [value.split("=", 1)[0] for value in case.factor_values]
            self.assertEqual(len(factor_names), len(set(factor_names)), case.case_id)


class AlterCollationRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        snapshot = discover_statement_factor_cycle(ROOT)
        cls.plan = build_statement_regress_plan(snapshot, "alter_collation")

    def case(self, group: str, **axes: str):
        matches = [
            case
            for case in self.plan.cases
            if case.case_group == group
            and all(case.derived_axes.get(key) == value for key, value in axes.items())
        ]
        self.assertEqual(1, len(matches), (group, axes))
        return matches[0]

    def test_version_dependency_privilege_noop_and_parser_cases_are_concrete(self) -> None:
        plain_rename = self.case(
            "success_rename_product",
            source_name_shape="plain_identifier",
            new_name_shape="plain_identifier",
            dependency_state="no_dependencies",
        )
        quoted_rename = self.case(
            "success_rename_product",
            source_name_shape="quoted_identifier",
            new_name_shape="quoted_identifier",
            dependency_state="no_dependencies",
        )
        refresh_index = self.case(
            "success_refresh_product",
            source_name_shape="schema_qualified",
            dependency_state="expression_index",
        )
        owner = self.case(
            "success_owner_product",
            source_name_shape="quoted_identifier",
            owner_shape="SESSION_USER",
            dependency_state="table_column",
        )
        owner_failure = self.case(
            "owner_privilege_truth_product",
            actor="collation_owner",
            can_set_role="yes",
            new_owner_create="no",
        )
        same_schema = self.case(
            "set_schema_same_schema_product",
            actor="non_owner",
            schema_create="yes",
        )
        default_refresh = self.case(
            "refresh_provider_boundary_product",
            provider_boundary="default_collation",
        )
        rollback_owner = self.case(
            "transactional_rollback_product",
            branch="owner",
        )
        qualified_target = self.case(
            "parser_namespace_boundary_product",
            boundary="qualified_rename_target",
        )

        plain_rename_sql = render_statement_regress_case(self.plan, plain_rename)
        quoted_rename_sql = render_statement_regress_case(self.plan, quoted_rename)
        refresh_sql = render_statement_regress_case(self.plan, refresh_index)
        owner_sql = render_statement_regress_case(self.plan, owner)
        owner_failure_sql = render_statement_regress_case(self.plan, owner_failure)
        same_schema_sql = render_statement_regress_case(self.plan, same_schema)
        default_sql = render_statement_regress_case(self.plan, default_refresh)
        rollback_owner_sql = render_statement_regress_case(self.plan, rollback_owner)
        parser_sql = render_statement_regress_case(self.plan, qualified_target)

        self.assertRegex(
            plain_rename_sql,
            r"(?m)^ALTER COLLATION altercollation_\d+_coll "
            r"RENAME TO altercollation_\d+_renamed;$",
        )
        self.assertRegex(
            quoted_rename_sql,
            r'(?m)^ALTER COLLATION "altercollation_\d+_Collation Name" '
            r'RENAME TO "altercollation_\d+_Renamed Collation";$',
        )
        self.assertIn("PROVIDER = builtin", refresh_sql)
        self.assertIn("VERSION = '0'", refresh_sql)
        self.assertIn("CREATE TABLE", refresh_sql)
        self.assertIn("CREATE INDEX", refresh_sql)
        self.assertIn("index_relfilenode_unchanged", refresh_sql)
        self.assertIn("collversion_matches_actual", refresh_sql)
        self.assertNotIn("UNIQUE (sort_key, id)", refresh_sql)
        self.assertIn("UNIQUE (rank_no, id)", refresh_sql)
        self.assertIn("OWNER TO SESSION_USER;", owner_sql)
        self.assertIn("table_column_dependency_preserved", owner_sql)
        self.assertNotIn("UNIQUE (sort_key, id)", owner_sql)
        self.assertIn("UNIQUE (rank_no, id)", owner_sql)
        self.assertIn("WITH SET TRUE", owner_failure_sql)
        self.assertIn("'42501'", owner_failure_sql)
        self.assertIn("same_schema_noop_preserved", same_schema_sql)
        self.assertIn('pg_catalog."default" REFRESH VERSION;', default_sql)
        self.assertIn("'XX000'", default_sql)
        self.assertIn("before_collation_version", default_sql)
        self.assertIn("protected_system_collation_preserved", default_sql)
        self.assertNotIn(
            "SELECT true AS protected_system_collation_preserved;", default_sql
        )
        self.assertIn(
            "pg_catalog.pg_get_userbyid(c.collowner) = session_user",
            rollback_owner_sql,
        )
        self.assertNotIn(
            "pg_catalog.pg_get_userbyid(c.collowner) = "
            "'altercollation_00173_new_owner'",
            rollback_owner_sql,
        )
        self.assertRegex(parser_sql, r"RENAME TO\s+[^;]+\.[^;]+;")
        self.assertIn("'42601'", parser_sql)

        pg_temp_out = render_statement_regress_case(
            self.plan,
            self.case(
                "parser_namespace_boundary_product",
                boundary="pg_temp_move_out",
            ),
        )
        pg_toast_out = render_statement_regress_case(
            self.plan,
            self.case(
                "parser_namespace_boundary_product",
                boundary="pg_toast_move_out",
            ),
        )
        self.assertIn("CREATE COLLATION pg_temp.", pg_temp_out)
        self.assertIn("n.oid = pg_catalog.pg_my_temp_schema()", pg_temp_out)
        self.assertIn("CREATE COLLATION pg_toast.", pg_toast_out)
        self.assertIn("n.nspname = 'pg_toast'", pg_toast_out)

    def test_every_case_has_real_target_stages_oracle_and_cleanup(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            self.assertTrue(sql.startswith("-- --------------------------------------------------------\n"))
            self.assertTrue(sql.endswith("\n"))
            self.assertFalse(sql.endswith("\n\n"))
            self.assertIn(f"-- case_id: {case.case_id}", sql)
            self.assertGreaterEqual(
                len(re.findall(r"^-- \d+\. ", sql, flags=re.MULTILINE)),
                5,
                case.case_id,
            )
            self.assertRegex(sql, r"(?m)^ALTER\s+COLLATION\b")
            self.assertEqual(
                1,
                len(re.findall(r"(?m)^ALTER\s+COLLATION\b", sql)),
                case.case_id,
            )
            self.assertIn("cleanup_complete", sql)
            self.assertNotIn("pg_sleep", sql)
            if case.outcome == "expected_failure":
                self.assertIn("SQLSTATE", sql)
            if "CREATE TABLE" in sql or "CREATE TEMP TABLE" in sql:
                audit = audit_complete_table_script(
                    sql,
                    expected_object_prefix=case.object_prefix,
                )
                self.assertTrue(audit.passed, (case.case_id, audit.to_dict()))

    def test_factor_labels_match_executed_oracles_and_membership_state(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            verification = case.derived_axes["verification_mode"]
            if verification == "pg_collation_actual_version_query":
                self.assertIn(
                    "pg_catalog.pg_collation_actual_version(", sql, case.case_id
                )
            elif verification == "collation_sort_verification":
                self.assertIn(" AS collation_sort_verification", sql, case.case_id)

            member = "owner_membership=member_of_new_owner" in case.factor_values
            not_member = (
                "owner_membership=not_member_of_new_owner" in case.factor_values
            )
            if member:
                self.assertRegex(
                    sql,
                    r"(?m)^GRANT altercollation_\d+_new_owner TO "
                    r"(?:SESSION_USER|altercollation_\d+_(?:old_owner|intruder)) "
                    r"WITH SET TRUE;$",
                    case.case_id,
                )
            if not_member:
                self.assertNotRegex(
                    sql,
                    r"(?m)^GRANT altercollation_\d+_new_owner TO ",
                    case.case_id,
                )
                self.assertNotIn("WITH SET FALSE", sql, case.case_id)

            must_preserve_snapshot = (
                case.outcome == "expected_failure"
                or case.case_group == "transactional_rollback_product"
            ) and "before_collation_oid" in sql
            if must_preserve_snapshot:
                self.assertIn("before_collation_owner", sql, case.case_id)
                self.assertIn("before_collation_version", sql, case.case_id)
                self.assertRegex(
                    sql,
                    r"(?:protected_)?collation_owner_stable",
                    case.case_id,
                )
                self.assertRegex(
                    sql,
                    r"(?:protected_)?collation_version_stable",
                    case.case_id,
                )

            if case.case_group in {
                "rename_privilege_truth_product",
                "set_schema_privilege_truth_product",
                "set_schema_same_schema_product",
            }:
                actor = case.derived_axes["actor"]
                grantee = (
                    "SESSION_USER"
                    if actor == "superuser"
                    else f"{case.object_prefix}old_owner"
                    if actor == "collation_owner"
                    else f"{case.object_prefix}intruder"
                )
                schema_suffix = (
                    "dst"
                    if case.case_group == "set_schema_privilege_truth_product"
                    else "src"
                )
                acl_line = (
                    f"GRANT CREATE ON SCHEMA {case.object_prefix}{schema_suffix} "
                    f"TO {grantee};"
                )
                setup_revoke = (
                    f"REVOKE CREATE ON SCHEMA {case.object_prefix}src "
                    f"FROM {case.object_prefix}old_owner;"
                )
                privilege_fixture_sql = (
                    sql.split(setup_revoke, 1)[1]
                    if setup_revoke in sql
                    else sql
                )
                if case.derived_axes["schema_create"] == "yes":
                    self.assertIn(acl_line, privilege_fixture_sql, case.case_id)
                else:
                    self.assertNotIn(acl_line, privilege_fixture_sql, case.case_id)


class AlterCollationRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_output = root / "first" / "alter_collation"
            first_evidence = root / "first-evidence"
            second_output = root / "second" / "alter_collation"
            second_evidence = root / "second-evidence"

            first = generate_statement_regress_package(
                ROOT,
                "alter_collation",
                output_dir=first_output,
                evidence_dir=first_evidence,
            )
            second = generate_statement_regress_package(
                ROOT,
                "alter_collation",
                output_dir=second_output,
                evidence_dir=second_evidence,
            )
            self.assertTrue(first.passed, first.issues)
            self.assertTrue(second.passed, second.issues)
            self.assertEqual(
                174, len(list(first_output.glob("ALTERCOLLATION*.sql")))
            )
            self.assertEqual(47, first.factor_value_count)
            self.assertEqual(
                {
                    path.relative_to(first_output): path.read_bytes()
                    for path in first_output.rglob("*")
                    if path.is_file()
                },
                {
                    path.relative_to(second_output): path.read_bytes()
                    for path in second_output.rglob("*")
                    if path.is_file()
                },
            )
            validation = validate_statement_regress_package(
                ROOT,
                "alter_collation",
                output_dir=first_output,
                evidence_dir=first_evidence,
            )
            self.assertTrue(validation.passed, validation.issues)


class AlterConversionRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = discover_statement_factor_cycle(ROOT)
        cls.plan = build_statement_regress_plan(cls.snapshot, "alter_conversion")

    def test_all_conditional_products_are_exact(self) -> None:
        self.assertEqual("ALTERCONVERSION", self.plan.file_prefix)
        self.assertEqual(216, len(self.plan.cases))
        self.assertEqual(
            {
                "default_pair_move_product": 1,
                "lookup_parser_boundary_product": 25,
                "missing_conversion_product": 3,
                "owner_missing_role_product": 6,
                "owner_privilege_truth_product": 12,
                "owner_same_owner_noop_product": 3,
                "protected_namespace_product": 10,
                "rename_conflict_product": 9,
                "rename_privilege_truth_product": 6,
                "rename_same_name_product": 6,
                "set_schema_conflict_product": 6,
                "set_schema_missing_product": 6,
                "set_schema_privilege_truth_product": 12,
                "set_schema_same_schema_product": 6,
                "success_owner_product": 42,
                "success_rename_product": 36,
                "success_set_schema_product": 24,
                "transactional_rollback_product": 3,
            },
            self.plan.case_group_counts,
        )

        rename = {
            (
                case.derived_axes["source_name_shape"],
                case.derived_axes["new_name_shape"],
                case.derived_axes["default_status"],
                case.derived_axes["actor"],
            )
            for case in self.plan.cases
            if case.case_group == "success_rename_product"
        }
        self.assertEqual(3 * 3 * 2 * 2, len(rename))
        owner = {
            (
                case.derived_axes["source_name_shape"],
                case.derived_axes["owner_shape"],
                case.derived_axes["default_status"],
                case.derived_axes["actor"],
            )
            for case in self.plan.cases
            if case.case_group == "success_owner_product"
        }
        self.assertEqual(3 * 2 * 2 * 2 + 3 * 3 * 2, len(owner))
        set_schema = {
            (
                case.derived_axes["source_name_shape"],
                case.derived_axes["target_schema_shape"],
                case.derived_axes["default_status"],
                case.derived_axes["actor"],
            )
            for case in self.plan.cases
            if case.case_group == "success_set_schema_product"
        }
        self.assertEqual(3 * 2 * 2 * 2, len(set_schema))

        owner_truth = {
            (
                case.derived_axes["actor"],
                case.derived_axes["can_set_role"],
                case.derived_axes["new_owner_create"],
            )
            for case in self.plan.cases
            if case.case_group == "owner_privilege_truth_product"
        }
        self.assertEqual(3 * 2 * 2, len(owner_truth))
        same_schema = {
            (case.derived_axes["actor"], case.derived_axes["schema_create"]): case
            for case in self.plan.cases
            if case.case_group == "set_schema_same_schema_product"
        }
        self.assertEqual(3 * 2, len(same_schema))
        for (actor, schema_create), case in same_schema.items():
            expected_success = actor == "superuser" or schema_create == "yes"
            self.assertEqual(
                "success" if expected_success else "expected_failure",
                case.outcome,
            )

    def test_lookup_parser_and_namespace_boundaries_are_complete(self) -> None:
        lookup = {
            case.derived_axes["boundary"]: case
            for case in self.plan.cases
            if case.case_group == "lookup_parser_boundary_product"
        }
        expected_lookup = {
            *(f"same_database_three_part_{branch}" for branch in ("rename", "owner", "set_schema")),
            *(f"cross_database_three_part_{branch}" for branch in ("rename", "owner", "set_schema")),
            *(f"four_part_source_{branch}" for branch in ("rename", "owner", "set_schema")),
            *(f"missing_source_schema_{branch}" for branch in ("rename", "owner", "set_schema")),
            *(f"source_schema_no_usage_{branch}" for branch in ("rename", "owner", "set_schema")),
            "qualified_rename_target",
            "unquoted_reserved_rename_target",
            "qualified_owner_target",
            "owner_public_target",
            "owner_none_target",
            "qualified_set_schema_target",
            "unquoted_reserved_set_schema_target",
            "search_path_first_match",
            "search_path_later_match",
            "temp_unqualified_lookup",
        }
        self.assertEqual(expected_lookup, set(lookup))
        self.assertEqual("42704", lookup["owner_public_target"].derived_axes["expected_sqlstate"])
        self.assertEqual("42939", lookup["owner_none_target"].derived_axes["expected_sqlstate"])
        self.assertTrue(
            all(
                lookup[f"same_database_three_part_{branch}"].outcome == "success"
                for branch in ("rename", "owner", "set_schema")
            )
        )

        namespace = {
            case.derived_axes["boundary"]: case
            for case in self.plan.cases
            if case.case_group == "protected_namespace_product"
        }
        self.assertEqual(
            {
                "pg_temp_move_into",
                "pg_temp_move_out",
                "pg_toast_move_into",
                "pg_toast_move_out",
                "pg_temp_same_schema_noop",
                "pg_toast_same_schema_noop",
                "pg_catalog_move_into_success",
                "pg_catalog_move_out_success",
                "pg_catalog_rename_success",
                "pg_catalog_owner_create_denied",
            },
            set(namespace),
        )
        self.assertEqual(
            "expected_failure",
            namespace["pg_catalog_owner_create_denied"].outcome,
        )

    def test_all_62_canonical_values_have_real_witnesses(self) -> None:
        entry = next(
            item for item in self.snapshot.entries if item.statement_key == "alter_conversion"
        )
        expected_rows = {
            row_id for factor in entry.factors for row_id in factor.row_ids
        }
        decisions = {decision.row_id: decision for decision in self.plan.factor_decisions}
        self.assertEqual(62, len(decisions))
        self.assertEqual(expected_rows, set(decisions))
        self.assertEqual(
            {"covered": 43, "expected_failure": 19, "justified_na": 0},
            self.plan.factor_disposition_counts,
        )
        self.assertTrue(all(decision.case_ids for decision in decisions.values()))
        for case in self.plan.cases:
            factor_names = [value.split("=", 1)[0] for value in case.factor_values]
            self.assertEqual(len(factor_names), len(set(factor_names)), case.case_id)


class AlterConversionRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        snapshot = discover_statement_factor_cycle(ROOT)
        cls.plan = build_statement_regress_plan(snapshot, "alter_conversion")

    def case(self, group: str, **axes: str):
        matches = [
            case
            for case in self.plan.cases
            if case.case_group == group
            and all(case.derived_axes.get(key) == value for key, value in axes.items())
        ]
        self.assertEqual(1, len(matches), (group, axes))
        return matches[0]

    def test_representative_syntax_default_permissions_lookup_and_rollback_are_real(self) -> None:
        reserved_rename = self.case(
            "success_rename_product",
            source_name_shape="quoted_id",
            new_name_shape="reserved_word_as_name",
            default_status="is_default_conversion",
            actor="superuser",
        )
        quoted_owner = self.case(
            "success_owner_product",
            source_name_shape="schema_qualified",
            owner_shape="quoted_id",
            default_status="is_not_default_conversion",
            actor="superuser",
        )
        default_pair = self.case("default_pair_move_product")
        owner_denied = self.case(
            "owner_privilege_truth_product",
            actor="conversion_owner",
            can_set_role="yes",
            new_owner_create="no",
        )
        owner_same = self.case(
            "owner_same_owner_noop_product",
            actor="non_owner",
        )
        current_db = self.case(
            "lookup_parser_boundary_product",
            boundary="same_database_three_part_rename",
        )
        temp_lookup = self.case(
            "lookup_parser_boundary_product",
            boundary="temp_unqualified_lookup",
        )
        rollback = self.case("transactional_rollback_product", branch="set_schema")

        reserved_sql = render_statement_regress_case(self.plan, reserved_rename)
        quoted_owner_sql = render_statement_regress_case(self.plan, quoted_owner)
        default_pair_sql = render_statement_regress_case(self.plan, default_pair)
        owner_denied_sql = render_statement_regress_case(self.plan, owner_denied)
        owner_same_sql = render_statement_regress_case(self.plan, owner_same)
        current_db_sql = render_statement_regress_case(self.plan, current_db)
        temp_lookup_sql = render_statement_regress_case(self.plan, temp_lookup)
        rollback_sql = render_statement_regress_case(self.plan, rollback)

        self.assertRegex(reserved_sql, r'(?m)^ALTER CONVERSION .* RENAME TO "select";$')
        self.assertIn("CREATE DEFAULT CONVERSION", reserved_sql)
        self.assertRegex(quoted_owner_sql, r'(?m)^ALTER CONVERSION .* OWNER TO ".+";$')
        self.assertIn("condefault_preserved", reserved_sql)
        self.assertIn("conversion_proc_preserved", reserved_sql)
        self.assertIn("default_pair_count_is_two", default_pair_sql)
        self.assertIn("WITH SET TRUE", owner_denied_sql)
        self.assertIn("'42501'", owner_denied_sql)
        self.assertIn("same_owner_noop_preserved", owner_same_sql)
        self.assertIn("current_database()", current_db_sql)
        self.assertIn("CREATE CONVERSION pg_temp.", temp_lookup_sql)
        self.assertIn("'42704'", temp_lookup_sql)
        self.assertIn("BEGIN;", rollback_sql)
        self.assertIn("ROLLBACK;", rollback_sql)
        self.assertIn("conversion_snapshot_preserved", rollback_sql)

    def test_every_case_has_one_target_complete_catalog_oracle_and_cleanup(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            self.assertTrue(sql.startswith("-- --------------------------------------------------------\n"))
            self.assertTrue(sql.endswith("\n"))
            self.assertFalse(sql.endswith("\n\n"))
            self.assertIn(f"-- case_id: {case.case_id}", sql)
            self.assertGreaterEqual(
                len(re.findall(r"^-- \d+\. ", sql, flags=re.MULTILINE)),
                5,
                case.case_id,
            )
            self.assertEqual(
                1,
                len(re.findall(r"(?m)^ALTER\s+CONVERSION\b", sql)),
                case.case_id,
            )
            self.assertIn("cleanup_complete", sql)
            self.assertNotIn("pg_sleep", sql)
            self.assertNotIn("CREATE TABLE", sql)
            self.assertNotIn("CREATE TEMP TABLE", sql)
            if case.outcome == "expected_failure":
                self.assertIn("SQLSTATE", sql)
            if "before_conversion_oid" in sql:
                self.assertIn("before_conversion_owner", sql, case.case_id)
                self.assertIn("before_conversion_proc", sql, case.case_id)
                self.assertIn("before_conversion_default", sql, case.case_id)

    def test_factor_labels_match_real_membership_acl_verification_and_cleanup(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            verification = case.derived_axes["verification_mode"]
            if verification == "catalog_query_pg_conversion":
                self.assertIn("pg_catalog.pg_conversion", sql, case.case_id)
            elif verification == "catalog_query_pg_namespace":
                self.assertIn("pg_catalog.pg_namespace", sql, case.case_id)
            elif verification == "error_assertion":
                self.assertEqual("expected_failure", case.outcome, case.case_id)
                self.assertIn("SQLSTATE", sql, case.case_id)

            if "owner_membership=can_set_role" in case.factor_values:
                self.assertRegex(
                    sql,
                    r'(?m)^GRANT (?:alterconversion_\d+_new_owner|"alterconversion_\d+_New Owner") TO .* WITH SET TRUE;$',
                    case.case_id,
                )
            if "owner_membership=cannot_set_role" in case.factor_values:
                self.assertRegex(
                    sql,
                    r'(?m)^GRANT (?:alterconversion_\d+_new_owner|"alterconversion_\d+_New Owner") TO .* WITH SET FALSE;$',
                    case.case_id,
                )

            cleanup = case.derived_axes["cleanup_mode"]
            if cleanup == "cascade_cleanup":
                self.assertRegex(sql, r"(?m)^DROP SCHEMA IF EXISTS .* CASCADE;$")
            elif cleanup == "drop_conversion":
                self.assertRegex(sql, r"(?m)^DROP CONVERSION IF EXISTS ")
            elif cleanup == "drop_role":
                self.assertRegex(sql, r"(?m)^DROP ROLE IF EXISTS ")
            elif cleanup == "drop_schema":
                self.assertRegex(sql, r"(?m)^DROP SCHEMA IF EXISTS ")


class AlterConversionRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_output = root / "first" / "alter_conversion"
            first_evidence = root / "first-evidence"
            second_output = root / "second" / "alter_conversion"
            second_evidence = root / "second-evidence"

            first = generate_statement_regress_package(
                ROOT,
                "alter_conversion",
                output_dir=first_output,
                evidence_dir=first_evidence,
            )
            second = generate_statement_regress_package(
                ROOT,
                "alter_conversion",
                output_dir=second_output,
                evidence_dir=second_evidence,
            )
            self.assertTrue(first.passed, first.issues)
            self.assertTrue(second.passed, second.issues)
            self.assertEqual(
                216, len(list(first_output.glob("ALTERCONVERSION*.sql")))
            )
            self.assertEqual(62, first.factor_value_count)
            self.assertEqual(
                {
                    path.relative_to(first_output): path.read_bytes()
                    for path in first_output.rglob("*")
                    if path.is_file()
                },
                {
                    path.relative_to(second_output): path.read_bytes()
                    for path in second_output.rglob("*")
                    if path.is_file()
                },
            )
            validation = validate_statement_regress_package(
                ROOT,
                "alter_conversion",
                output_dir=first_output,
                evidence_dir=first_evidence,
            )
            self.assertTrue(validation.passed, validation.issues)


if __name__ == "__main__":
    unittest.main()
