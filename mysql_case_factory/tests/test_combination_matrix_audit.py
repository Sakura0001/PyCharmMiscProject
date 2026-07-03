from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


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
            "skills/mysql-sql-generation/references/common/mysql80_type_catalog.md",
            """
            # MySQL 8.0.22 Type Catalog

            ```yaml
            structured_config:
              kind: type_catalog
              skill_name: mysql80_type_catalog
              version: mysql80
              type_sets:
                all_mysql80_column_types:
                  description: Test fixture.
                  include_pseudo_types: false
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

    def write_statement(self, root: Path) -> None:
        self.write_file(
            root,
            "skills/mysql-sql-generation/references/statements/ddl/example/example_statement.md",
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
        column_source = overrides.get("column_source", "")
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
          target_relation_coverage: {{required: false, coverage_mode: not_applicable, decision_reason: example}}
          table_coverage: {{required: false, coverage_mode: not_applicable, decision_reason: example}}
          column_type_coverage: {{required: {column_required}, coverage_mode: not_applicable, decision_reason: example{column_source}}}
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
              required_values: [success]
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
            expansion: {{}}
            compatibility:
              resolver: declared_matrix
              success_when: ["mode == basic"]
              failure_when: []
              default_failure_reason: ""
            sql_shape: {{template: EXAMPLE}}
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
            "skills/mysql-sql-generation/references/combinations/ddl/example/example_statement.yaml",
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
            column_source=", inventory_source: references/common/mysql80_type_catalog.md, required_type_set: all_mysql80_column_types",
        )
        result = self.audit_fixture(matrix, include_type_catalog=False)
        self.assertFalse(result.passed)
        self.assertTrue(any("column_type_coverage requires mysql80_type_catalog" in error for error in result.errors))

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
