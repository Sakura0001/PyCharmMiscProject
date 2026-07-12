from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "audit_combination_matrix.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_combination_matrix", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CombinationMatrixAuditTest(unittest.TestCase):
    def write_file(self, root: Path, relative_path: str, content: str) -> Path:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
        return path

    def write_type_catalog(self, root: Path) -> None:
        self.write_file(
            root,
            "skills/pg-sql-generation/references/common/pg18_type_catalog.md",
            """
            # PG18.4 Type Catalog

            ```yaml
            structured_config:
              kind: type_catalog
              skill_name: pg18_type_catalog
              version: pg18.4
              type_sets:
                canonical_executable_column_profiles:
                  description: Canonical finite fixture profiles.
                  readiness: ready
                all_pg18_column_types:
                  description: Test fixture.
                  canonical: false
                  include_pseudo_types: false
                  readiness: ready
              types:
                integer:
                  type_key: integer
                  type_category: numeric
                  declaration_sql: INTEGER
                  sample_values: {success: ["1"], boundary: [], failure: []}
                  requires_setup: []
                  index_capabilities:
                    btree: true
                    btree_unique: true
                    hash: true
                    gist: false
                    spgist: false
                    gin: false
                    brin: true
                    collation: false
                    predicate_expression: true
                  notes: []
              pseudo_types:
                allowed_as_table_columns: false
                values: [any]
            ```
            """,
        )
        self.write_file(
            root,
            "skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml",
            """
            schema_version: 1
            kind: coverage_inventory
            object_kinds:
              canonical: false
              all_object_kinds: [example_object]
            sql_object_types:
              canonical: true
              all_sql_object_types: [example_object, second_object]
            relation_kinds:
              canonical: true
              all_relation_kinds: [regular_table, plain_view]
              all_pg18_relkinds: [relation, view]
            table_kinds:
              canonical: false
              all_table_kinds: [regular_table]
            """,
        )

    def write_statement(self, root: Path) -> None:
        self.write_file(
            root,
            "skills/pg-sql-generation/references/statements/ddl/example/example_statement.md",
            """
            ```yaml
            structured_config:
              kind: statement
              category: ddl
              domain: example
              statement:
                key: example_statement
                name: EXAMPLE STATEMENT
              factor_layers:
                - tier: T1
                  factors: [mode, expected_status]
              factors:
                mode:
                  values: [basic]
                expected_status:
                  values: [success, failure]
              coverage_policy:
                main_combination_axes: [mode, expected_status]
                non_main_factors: []
              rendering:
                statement_template: EXAMPLE
                factor_value_bindings: {}
            ```
            """,
        )

    def valid_matrix(self, **overrides: str) -> str:
        mode_value = overrides.get("mode_value", "basic")
        expected_status = overrides.get("expected_status", "success")
        extra_factor = overrides.get("extra_factor", "")
        failure_reason = overrides.get("failure_reason", "")
        column_required = overrides.get("column_required", "false")
        column_mode = overrides.get("column_mode", "not_applicable")
        column_source = overrides.get("column_source", "")
        type_expansion = overrides.get("type_expansion", "{}")
        relation_required = overrides.get("relation_required", "false")
        relation_mode = overrides.get("relation_mode", "not_applicable")
        relation_source = overrides.get("relation_source", "")
        table_required = overrides.get("table_required", "false")
        table_mode = overrides.get("table_mode", "not_applicable")
        table_source = overrides.get("table_source", "")
        derived_flag = overrides.get("derived_flag", "false")
        audit_extension_counts = overrides.get("audit_extension_counts", "false")
        return f"""
        schema_version: 1
        kind: statement_combination_matrix
        statement:
          key: example_statement
          name: EXAMPLE STATEMENT
          category: ddl
          domain: example
          source_reference: references/statements/ddl/example/example_statement.md
        execution_contract:
          required_matrix_is_baseline: true
          no_inference_before_required_coverage_passes: true
          runner_must_complete_required_matrix_first: true
          allow_post_coverage_extension_inference: true
          extension_combinations_must_be_marked: true
          extension_combinations_must_record_derivation: true
          extension_combinations_must_not_replace_required_coverage: true
          success_and_failure_both_allowed: true
          all_success_and_failure_reasons_must_be_declared: true
          required_coverage_sql_templates_must_come_from_combination_groups: true
          extension_sql_templates_must_be_recorded_in_artifacts: true
        post_coverage_extension_policy:
          enabled: true
          allowed_after_audit_verdict: required_coverage_passed
          output_location: artifacts/intermediates/<task_slug>/derived_extension_combinations.yaml
          required_fields: [id, title, derived_from_combination_group, derivation_reason, factors, expected_status_policy, compatibility, sql_shape, verification, cleanup]
          guardrails:
            - Required matrix coverage must pass before any derived extension is emitted.
        coverage_scope:
          target_object_coverage: {{required: false, coverage_mode: not_applicable, decision_reason: example}}
          target_relation_coverage: {{required: {relation_required}, coverage_mode: {relation_mode}, decision_reason: example{relation_source}}}
          table_coverage: {{required: {table_required}, coverage_mode: {table_mode}, decision_reason: example{table_source}}}
          column_type_coverage: {{required: {column_required}, coverage_mode: {column_mode}, decision_reason: example{column_source}}}
        factor_contract:
          source_reference_must_define_all_factors: true
          matrix_must_cover_required_factor_values: true
          factors:
            mode:
              tier: T1
              coverage_role: main_axis
              required_values: [basic]
              coverage_requirement: all_values
            expected_status:
              tier: T1
              coverage_role: main_axis
              required_values: [success, failure]
              coverage_requirement: all_values
        dynamic_inputs: {{}}
        combination_groups:
          - id: basic_case
            title: Basic case
            lifecycle_role: target_statement
            expected_status_policy: fixed
            default_expected_status: {expected_status}
            expected_failure_reasons: [{failure_reason}]
            derived_extension: {derived_flag}
            factors: {{mode: {mode_value}, expected_status: {expected_status}{extra_factor}}}
            expansion: {type_expansion}
            compatibility:
              resolver: declared_matrix
              success_when: ["mode == basic"]
              failure_when: []
              default_failure_reason: ""
            sql_shape: {{template: EXAMPLE}}
            verification: {{required: false, mode: none, sql: null}}
            cleanup: {{required: true, steps: [{{sql: "-- cleanup"}}]}}
          - id: expected_failure_case
            title: Expected failure case
            lifecycle_role: negative_control
            expected_status_policy: fixed
            default_expected_status: failure
            expected_failure_reasons: [fixture expected failure]
            factors: {{mode: basic, expected_status: failure}}
            expansion: {{}}
            compatibility:
              resolver: declared_matrix
              success_when: []
              failure_when:
                - condition: expected_status == failure
                  reason: fixture expected failure
              default_failure_reason: fixture expected failure
            sql_shape: {{template: EXAMPLE FAILURE}}
            verification: {{required: false, mode: none, sql: null}}
            cleanup: {{required: true, steps: [{{sql: "-- cleanup"}}]}}
        audit_rules:
          require_all_required_top_level_keys: true
          require_declared_coverage_scope: true
          require_declared_factor_values: true
          require_expected_failure_reasons: true
          require_post_coverage_extension_policy: true
          forbid_extension_before_required_coverage_passes: true
          forbid_extension_counting_toward_required_coverage: {audit_extension_counts}
        """

    def write_matrix(self, root: Path, content: str) -> Path:
        return self.write_file(
            root,
            "skills/pg-sql-generation/references/combinations/ddl/example/example_statement.yaml",
            content,
        )

    def audit_fixture(self, matrix: str, include_type_catalog: bool = True):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_statement(root)
            if include_type_catalog:
                self.write_type_catalog(root)
            self.write_matrix(root, matrix)
            return module.audit_root(root)

    def test_valid_matrix_passes(self):
        result = self.audit_fixture(self.valid_matrix())
        self.assertTrue(result.passed, result.errors)

    def test_empty_repository_fails_closed(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            result = module.audit_root(Path(tmp))

        self.assertFalse(result.passed)
        self.assertTrue(any("statement reference directory" in error for error in result.errors))
        self.assertTrue(any("combination matrix directory" in error for error in result.errors))

    def test_every_statement_requires_exactly_one_matrix(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_statement(root)
            self.write_type_catalog(root)

            missing = module.audit_root(root)
            self.assertFalse(missing.passed)
            self.assertTrue(
                any("statement reference has no combination matrix" in error for error in missing.errors)
            )

            matrix = self.write_matrix(root, self.valid_matrix())
            self.write_file(
                root,
                "skills/pg-sql-generation/references/combinations/ddl/example/duplicate.yaml",
                matrix.read_text(encoding="utf-8"),
            )
            duplicate = module.audit_root(root)

        self.assertFalse(duplicate.passed)
        self.assertTrue(
            any("duplicate combination matrix statement key" in error for error in duplicate.errors)
        )

    def test_matrix_key_must_match_source_reference_statement_key(self):
        document = yaml.safe_load(textwrap.dedent(self.valid_matrix()))
        document["statement"]["key"] = "wrong_statement"

        result = self.audit_fixture(yaml.safe_dump(document, sort_keys=False))

        self.assertFalse(result.passed)
        self.assertTrue(
            any("does not match source_reference statement.key" in error for error in result.errors)
        )

    def test_all_values_requirement_rejects_omitted_declared_value(self):
        for requirement in ("all_values", "all_declared_values"):
            with self.subTest(requirement=requirement):
                document = yaml.safe_load(textwrap.dedent(self.valid_matrix()))
                factor = document["factor_contract"]["factors"]["expected_status"]
                factor["coverage_requirement"] = requirement
                factor["required_values"] = ["success"]

                result = self.audit_fixture(yaml.safe_dump(document, sort_keys=False))

                self.assertFalse(result.passed)
                self.assertTrue(
                    any(
                        f"coverage_requirement={requirement} missing declared factor value: "
                        "expected_status=failure" in error
                        for error in result.errors
                    )
                )

    def test_factor_contract_cannot_omit_a_statement_factor(self):
        document = yaml.safe_load(textwrap.dedent(self.valid_matrix()))
        document["factor_contract"]["factors"].pop("mode")

        result = self.audit_fixture(yaml.safe_dump(document, sort_keys=False))

        self.assertFalse(result.passed)
        self.assertTrue(
            any("factor contract missing statement factor: mode" in error for error in result.errors)
        )

    def test_unknown_factor_fails(self):
        result = self.audit_fixture(self.valid_matrix(extra_factor=", missing_factor: x"))
        self.assertFalse(result.passed)
        self.assertTrue(any("unknown factor" in error for error in result.errors))

    def test_unknown_factor_value_fails(self):
        result = self.audit_fixture(self.valid_matrix(mode_value="missing"))
        self.assertFalse(result.passed)
        self.assertTrue(any("unknown factor value" in error for error in result.errors))

    def test_failure_without_reason_fails(self):
        result = self.audit_fixture(self.valid_matrix(expected_status="failure"))
        self.assertFalse(result.passed)
        self.assertTrue(any("failure group must declare reason" in error for error in result.errors))

    def test_required_column_coverage_requires_type_catalog(self):
        matrix = self.valid_matrix(
            column_required="true",
            column_source=", inventory_source: references/common/pg18_type_catalog.md, required_type_set: all_pg18_column_types",
        )
        result = self.audit_fixture(matrix, include_type_catalog=False)
        self.assertFalse(result.passed)
        self.assertTrue(any("column_type_coverage requires pg18_type_catalog" in error for error in result.errors))

    def test_required_column_coverage_rejects_pg16_inventory(self):
        matrix = self.valid_matrix(
            column_required="true",
            column_source=", inventory_source: references/common/pg16_type_catalog.md, required_type_set: all_pg16_column_types",
        )
        result = self.audit_fixture(matrix)
        self.assertFalse(result.passed)
        self.assertTrue(any("pg18_type_catalog" in error for error in result.errors))

    def test_exhaustive_column_scope_requires_group_expansion_evidence(self):
        matrix = self.valid_matrix(
            column_required="true",
            column_mode="exhaustive",
            column_source=", inventory_source: references/common/pg18_type_catalog.md, required_type_set: all_pg18_column_types, expansion_mode: expand_every_type, require_each_type_success_or_failure: true",
        )
        result = self.audit_fixture(matrix)

        self.assertFalse(result.passed)
        self.assertTrue(any("all seven canonical dimensions" in error for error in result.errors))

    def test_partial_column_scope_is_reported_without_being_relabelled_complete(self):
        matrix = self.valid_matrix(
            column_required="true",
            column_mode="representative",
            column_source=", inventory_source: references/common/pg18_type_catalog.md, required_type_set: all_pg18_column_types, expansion_mode: representative_by_type_category, require_each_type_success_or_failure: false",
        )
        result = self.audit_fixture(matrix)

        self.assertTrue(result.passed, result.errors)
        self.assertTrue(any("partial column-type coverage" in warning for warning in result.warnings))

    def test_deprecated_single_type_set_cannot_claim_exhaustive_coverage(self):
        matrix = self.valid_matrix(
            column_required="true",
            column_mode="exhaustive",
            column_source=", inventory_source: references/common/pg18_type_catalog.md, required_type_set: all_pg18_column_types, expansion_mode: expand_every_type, require_each_type_success_or_failure: true",
            type_expansion="{column_types: {mode: exhaustive, source: coverage_scope.column_type_coverage.required_type_set}}",
        )
        result = self.audit_fixture(matrix)

        self.assertFalse(result.passed)
        self.assertTrue(
            any("all seven canonical dimensions" in error for error in result.errors)
        )

    def test_exhaustive_table_scope_requires_matching_group_expansion(self):
        matrix = self.valid_matrix(
            table_required="true",
            table_mode="exhaustive",
            table_source=", inventory_source: references/combinations/_shared/coverage_inventory.yaml#table_kinds.all_table_kinds, required_table_kinds: [regular_table]",
        )
        result = self.audit_fixture(matrix)

        self.assertFalse(result.passed)
        self.assertTrue(any("table_coverage has no exhaustive group expansion" in error for error in result.errors))

    def test_exhaustive_relation_scope_requires_exact_canonical_inventory(self):
        matrix = self.valid_matrix(
            relation_required="true",
            relation_mode="exhaustive",
            relation_source=", inventory_source: references/combinations/_shared/coverage_inventory.yaml#relation_kinds.all_pg18_relkinds, required_relation_kinds: [relation]",
            type_expansion="{relation_kinds: {mode: exhaustive, source: coverage_scope.target_relation_coverage.required_relation_kinds}}",
        )
        result = self.audit_fixture(matrix)

        self.assertFalse(result.passed)
        self.assertTrue(
            any("omits canonical values: view" in error for error in result.errors)
        )

    def test_partial_relation_scope_is_visible_as_a_warning(self):
        matrix = self.valid_matrix(
            relation_required="true",
            relation_mode="representative",
            relation_source=", inventory_source: references/combinations/_shared/coverage_inventory.yaml#relation_kinds.all_relation_kinds, required_relation_kinds: [regular_table]",
        )
        result = self.audit_fixture(matrix)

        self.assertTrue(result.passed, result.errors)
        self.assertTrue(any("partial target_relation_coverage" in warning for warning in result.warnings))

    def test_required_scope_value_must_exist_in_canonical_inventory(self):
        matrix = self.valid_matrix(
            table_required="true",
            table_mode="explicit",
            table_source=", inventory_source: references/combinations/_shared/coverage_inventory.yaml#table_kinds.all_table_kinds, required_table_kinds: [invented_table_kind]",
        )
        result = self.audit_fixture(matrix)

        self.assertFalse(result.passed)
        self.assertTrue(any("invented_table_kind" in error for error in result.errors))

    def test_extension_policy_cannot_replace_required_coverage(self):
        result = self.audit_fixture(self.valid_matrix(derived_flag="true", audit_extension_counts="true"))
        self.assertFalse(result.passed)
        self.assertTrue(any("extension coverage cannot satisfy required coverage" in error for error in result.errors))

    def test_cli_reports_clean_error_without_traceback(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", "/path/that/does/not/exist"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ERROR:", completed.stdout)
        self.assertNotIn("Traceback", completed.stdout)


if __name__ == "__main__":
    unittest.main()
