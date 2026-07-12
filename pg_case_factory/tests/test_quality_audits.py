from __future__ import annotations

import json
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pg_case_factory.audits import (
    audit_assets,
    audit_capabilities,
    audit_dialect,
    audit_placeholders,
    audit_repository,
    audit_statement_references,
)
from pg_case_factory.discovery import discover_request_candidates, list_statement_skills
from pg_case_factory.renderer import build_bindings, build_name_context, render_statement
from pg_case_factory.skill_loader import load_skill


def _write_statement(
    root: Path,
    key: str,
    *,
    template: str = "CREATE TABLE {table_name} (id integer)",
    verification_template: str = "",
    bindings: str = "{}",
    defaults: str = "expected_status: success",
) -> Path:
    path = (
        root
        / "skills"
        / "pg-sql-generation"
        / "references"
        / "statements"
        / "ddl"
        / "table"
        / f"{key}.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    indented_bindings = textwrap.indent(bindings, " " * 18)
    path.write_text(
        textwrap.dedent(
            f"""
            # {key}

            ```yaml
            structured_config:
              kind: statement
              category: ddl
              domain: table
              skill_name: {key}
              statement:
                key: {key}
                name: {key.upper()}
                aliases: [{key}]
              factor_layers:
                - tier: T1
                  name: core
                  factors: [expected_status]
              factors:
                expected_status:
                  label: expected status
                  importance: important
                  values: [success, failure]
              defaults:
                {defaults}
              coverage_policy:
                main_combination_axes: [expected_status]
                non_main_factors: []
              rendering:
                statement_template: {json.dumps(template)}
                verification_query_template: {json.dumps(verification_template)}
                factor_value_bindings:
{indented_bindings}
            ```
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_asset(root: Path, text: str, name: str = "table_01.sql") -> Path:
    path = (
        root
        / "skills"
        / "pg-sql-generation"
        / "assets"
        / "objects"
        / "tables"
        / "normal_table"
        / name
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    return path


class StatementAuditTest(unittest.TestCase):
    def test_valid_statement_passes_and_duplicate_key_fails(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            _write_statement(root, "create_table")

            result = audit_statement_references(root)

            self.assertTrue(result.ok, result.to_dict())
            duplicate = _write_statement(root, "duplicate")
            duplicate.write_text(
                duplicate.read_text(encoding="utf-8").replace(
                    "key: duplicate", "key: create_table", 1
                ),
                encoding="utf-8",
            )
            result = audit_statement_references(root)
            self.assertFalse(result.ok)
            self.assertIn("statement.duplicate_key", {item.code for item in result.errors})

    def test_unknown_default_and_coverage_factor_fail(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            path = _write_statement(
                root,
                "create_table",
                defaults="missing_factor: value",
            )
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "main_combination_axes: [expected_status]",
                    "main_combination_axes: [missing_factor]",
                ),
                encoding="utf-8",
            )

            result = audit_statement_references(root)

            codes = {item.code for item in result.errors}
            self.assertIn("statement.unknown_default_factor", codes)
            self.assertIn("statement.unknown_coverage_factor", codes)

    def test_duplicate_yaml_key_and_path_key_mismatch_fail(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            path = _write_statement(root, "create_table")
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    "name: CREATE_TABLE",
                    "name: CREATE_TABLE\n                name: DUPLICATE",
                ),
                encoding="utf-8",
            )

            result = audit_statement_references(root)

            self.assertIn("statement.invalid_yaml", {item.code for item in result.errors})

            path = _write_statement(root, "create_table")
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "key: create_table", "key: wrong_key", 1
                ),
                encoding="utf-8",
            )
            result = audit_statement_references(root)
            self.assertIn("statement.path_key_mismatch", {item.code for item in result.errors})


class PlaceholderAndCapabilityAuditTest(unittest.TestCase):
    def test_complete_canonical_binding_is_renderable(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            _write_statement(
                root,
                "create_table",
                template="SELECT {expected_status}",
                bindings=textwrap.dedent(
                    """
                    expected_status:
                      factor: expected_status
                      values:
                        success: ok
                        failure: error
                    """
                ).strip(),
            )

            placeholder_result = audit_placeholders(root)
            capability_result = audit_capabilities(root)

            self.assertTrue(placeholder_result.ok, placeholder_result.to_dict())
            self.assertEqual([], placeholder_result.warnings)
            self.assertEqual("renderable", capability_result.capabilities[0].level)

    def test_builtin_name_context_is_a_declared_placeholder_resolver(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            _write_statement(root, "create_table", template="SELECT '{table_name}'")

            placeholder_result = audit_placeholders(root)
            capability_result = audit_capabilities(root)

            self.assertEqual([], placeholder_result.warnings)
            self.assertEqual("renderable", capability_result.capabilities[0].level)

    def test_malformed_template_and_legacy_binding_are_reported(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            _write_statement(
                root,
                "broken",
                template="GRANT { { SELECT | INSERT }",
                bindings="{expected_status: {success: ok, failure: error}}",
            )

            result = audit_placeholders(root)
            capabilities = audit_capabilities(root)

            self.assertIn("placeholder.invalid_template", {item.code for item in result.errors})
            self.assertIn("placeholder.legacy_binding", {item.code for item in result.warnings})
            self.assertEqual("reference_only", capabilities.capabilities[0].level)

    def test_capability_checks_verification_and_nested_binding_placeholders(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            _write_statement(
                root,
                "create_table",
                template="SELECT {status_clause}",
                verification_template="SELECT {runtime_only_name}",
                bindings=textwrap.dedent(
                    """
                    status_clause:
                      factor: expected_status
                      values:
                        success: "{nested_runtime_name}"
                        failure: error
                    unused_legacy_clause:
                      success: ok
                      failure: error
                    """
                ).strip(),
            )

            capability = audit_capabilities(root).capabilities[0]

            self.assertEqual("reference_only", capability.level)
            joined_reasons = "\n".join(capability.reasons)
            self.assertIn("legacy or invalid bindings: unused_legacy_clause", joined_reasons)
            self.assertIn("unresolved binding placeholders: nested_runtime_name", joined_reasons)
            self.assertIn("unresolved placeholders: runtime_only_name", joined_reasons)


class RepositoryRenderingRegressionTest(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_explicit_statement_spellings_have_unambiguous_discovery_aliases(self) -> None:
        report = audit_statement_references(self.ROOT)
        self.assertNotIn("statement.ambiguous_alias", {item.code for item in report.warnings})

        for request_text, expected_key, formerly_ambiguous_key in (
            ("ALTER FUNCTION", "alter_function", "alter_routine"),
            ("CREATE USER", "create_user", "create_role"),
            ("DROP ROLE", "drop_role", "drop_user"),
        ):
            candidates = discover_request_candidates(request_text, self.ROOT)["statement_skills"]
            scores = {item["statement"]["key"]: item["score"] for item in candidates}
            self.assertGreater(scores[expected_key], scores[formerly_ambiguous_key])

    def test_reindex_boolean_keyword_binding_is_complete_and_renderable(self) -> None:
        path = (
            self.ROOT
            / "skills"
            / "pg-sql-generation"
            / "references"
            / "statements"
            / "ddl"
            / "index"
            / "reindex.md"
        )
        skill = load_skill(path)
        binding = dict(skill["defaults"])
        binding.update(
            {
                "statement_branch": "reindex_index",
                "option_concurrently": "present_boolean_keyword",
            }
        )
        context = {**build_name_context("reindex", 1), "target_name": "idx_reindex_case"}

        rendered = render_statement(skill, binding, context)

        self.assertIn("REINDEX (CONCURRENTLY) INDEX idx_reindex_case;", rendered["statement_sql"])
        warnings = [
            item
            for item in audit_placeholders(self.ROOT).warnings
            if item.path == path.relative_to(self.ROOT).as_posix()
        ]
        self.assertNotIn("placeholder.incomplete_binding", {item.code for item in warnings})

    def test_every_advertised_renderable_statement_renders_all_generated_bindings(self) -> None:
        levels = {
            item.statement_key: item.level
            for item in audit_capabilities(self.ROOT).capabilities
        }
        for skill in list_statement_skills(self.ROOT):
            statement_key = skill["statement"]["key"]
            if levels[statement_key] != "renderable":
                continue
            context = build_name_context(statement_key, 1)
            for binding in build_bindings(skill):
                with self.subTest(statement=statement_key, binding=binding):
                    render_statement(skill, binding, context)


class DialectAndAssetAuditTest(unittest.TestCase):
    def test_mysql_and_host_shell_constructs_fail(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            common = (
                root
                / "skills"
                / "pg-sql-generation"
                / "references"
                / "common"
                / "output_script_style.md"
            )
            common.parent.mkdir(parents=True, exist_ok=True)
            common.write_text(
                "```sql\nCREATE TABLE t (id int AUTO_INCREMENT);\n"
                "SET optimizer_switch='x';\n\\! bash dangerous.sh\n```\n",
                encoding="utf-8",
            )

            result = audit_dialect(root)

            codes = {item.code for item in result.errors}
            self.assertIn("dialect.mysql.auto_increment", codes)
            self.assertIn("dialect.mysql.optimizer_switch", codes)
            self.assertIn("dialect.host_command", codes)

    def test_asset_requires_metadata_and_base_object_only(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            _write_asset(
                root,
                """
                CREATE TABLE tab_base (id integer);
                CREATE INDEX idx_base ON tab_base (id);
                """,
            )

            result = audit_assets(root)

            codes = {item.code for item in result.errors}
            self.assertIn("asset.missing_metadata", codes)
            self.assertIn("asset.non_base_statement", codes)

    def test_valid_base_asset_passes(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            _write_asset(
                root,
                """
                -- object_key: table_01_comprehensive_types
                -- aliases: normal table, comprehensive table
                -- object_kind: table
                -- compatibility_target: postgresql-18.4
                -- purpose: reusable base relation
                -- primary_object: tab_base

                DROP TABLE IF EXISTS tab_base;
                CREATE TABLE tab_base (id integer, payload text);
                """,
            )

            result = audit_assets(root)

            self.assertTrue(result.ok, result.to_dict())


class AggregateAuditTest(unittest.TestCase):
    def test_empty_directory_fails_closed(self) -> None:
        with TemporaryDirectory() as raw_dir:
            report = audit_repository(Path(raw_dir))

        self.assertFalse(report.ok)
        codes = {finding.code for finding in report.errors}
        self.assertIn("repository.statement_corpus_empty", codes)
        self.assertIn("repository.matrix_corpus_empty", codes)

    def test_repository_report_is_json_serializable(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            _write_statement(root, "create_table")
            _write_asset(
                root,
                """
                -- object_key: table_01_comprehensive_types
                -- aliases: normal table
                -- object_kind: table
                -- compatibility_target: postgresql-18.4
                -- purpose: reusable base relation
                -- primary_object: tab_base
                DROP TABLE IF EXISTS tab_base;
                CREATE TABLE tab_base (id integer);
                """,
            )

            report = audit_repository(root)
            payload = report.to_dict()

            json.dumps(payload)
            self.assertEqual(
                {"errors", "warnings", "capabilities", "summary", "ok"},
                set(payload),
            )
            self.assertIn("statement_count", payload["summary"])


if __name__ == "__main__":
    unittest.main()
