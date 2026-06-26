import io
import importlib.util
import sys
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "audit_factor_catalog_mapping.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_factor_catalog_mapping", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_catalog(path: Path) -> None:
    path.write_text(
        textwrap.dedent(
            """
            # PG16 Factor Catalog

            ```yaml
            structured_config:
              kind: factor_catalog
              skill_name: pg16_factor_catalog
              object_domains:
                database:
                  key: database
                  label: 数据库
                  applies_to:
                    - create_database
                  factor_groups:
                    naming:
                      key: naming
                      label: 命名因子
                      default_tier: T3
                      default_coverage_role: rotate_attach
                      factors:
                        name_shape:
                          key: name_shape
                          label: 数据库名称形态
                          values:
                            - key: valid_unquoted_lower
                              label: 合法未加引号小写名称
                              expected_status: success
                    options:
                      key: options
                      label: 选项因子
                      default_tier: T2
                      default_coverage_role: representative_or_main
                      factors:
                        owner:
                          key: owner
                          label: OWNER 子句
                          values:
                            - key: omitted
                              label: 省略 OWNER
                              expected_status: success
                    boundary:
                      key: boundary
                      label: 异常与边界
                      default_tier: T5
                      default_coverage_role: rotate_attach
                      factors:
                        duplicate_name:
                          key: duplicate_name
                          label: 重名冲突
                          values:
                            - key: name_already_exists
                              label: 名称已存在
                              expected_status: failure
            ```
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_statement(path: Path, mapping_block: str) -> None:
    indented_mapping_block = textwrap.indent(mapping_block, "              ")
    path.write_text(
        textwrap.dedent(
            f"""
            # 技能：CREATE DATABASE

            ```yaml
            structured_config:
              kind: statement
              category: ddl
              domain: database
              skill_name: create_database
              statement:
                key: create_database
                name: CREATE DATABASE
                aliases:
                  - create_database
              factor_layers:
                - tier: T1
                  name: 核心语义因子
                  factors:
                    - statement_branch
                    - expected_status
                - tier: T2
                  name: 重要行为因子
                  factors:
                    - owner_clause
                - tier: T3
                  name: 对象名与输入形态因子
                  factors:
                    - database_name_shape
                - tier: T5
                  name: 异常与边界因子
                  factors:
                    - duplicate_database_name
              factors:
                statement_branch:
                  label: 官方语法分支
                  importance: important
                  values:
                    - default_branch
                expected_status:
                  label: 预期结果
                  importance: important
                  values:
                    - success
                    - failure
                owner_clause:
                  label: OWNER 子句
                  importance: non_important
                  values:
                    - omitted
                    - specified_user
                database_name_shape:
                  label: database 名称形态
                  importance: non_important
                  values:
                    - simple_id
                    - quoted_id
                duplicate_database_name:
                  label: 重名冲突
                  importance: non_important
                  values:
                    - no_conflict
                    - name_already_exists
              coverage_policy:
                main_combination_axes:
                  - statement_branch
                  - expected_status
                non_main_factors:
                  - owner_clause
                  - database_name_shape
                  - duplicate_database_name
{indented_mapping_block}
              rendering:
                statement_template: CREATE DATABASE {{database_name}}
                verification_query_template: ""
                factor_value_bindings: {{}}
            ```
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


class FactorCatalogMappingAuditTest(unittest.TestCase):
    def test_valid_mapping_passes(self) -> None:
        audit = load_audit_module()
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            catalog_path = root / "pg16_factor_catalog.md"
            statement_path = root / "create_database.md"
            write_catalog(catalog_path)
            write_statement(
                statement_path,
                textwrap.dedent(
                    """
                    factor_catalog_mapping:
                      source_catalog: references/common/pg16_factor_catalog.md
                      object_domain: database
                      imported_factors:
                        - catalog_factor: database.naming.name_shape
                          local_factor: database_name_shape
                          target_tier: T3
                          coverage_role: rotate_attach
                          value_policy: statement_specific_subset
                          selected_values:
                            - valid_unquoted_lower
                          reason: CREATE DATABASE needs database name coverage.
                        - catalog_factor: database.options.owner
                          local_factor: owner_clause
                          target_tier: T2
                          coverage_role: representative_or_main
                          value_policy: reuse_catalog_values
                          reason: OWNER changes role behavior.
                      excluded_factors:
                        - catalog_factor: database.boundary.duplicate_name
                          reason: Covered by duplicate_database_name in a later migration step.
                    """
                ).strip(),
            )

            result = audit.audit_paths(catalog_path, [statement_path])

            self.assertTrue(result.passed, result.errors)
            self.assertEqual(result.mapped_count, 2)
            self.assertEqual(result.excluded_count, 1)

    def test_missing_local_factor_fails(self) -> None:
        audit = load_audit_module()
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            catalog_path = root / "pg16_factor_catalog.md"
            statement_path = root / "create_database.md"
            write_catalog(catalog_path)
            write_statement(
                statement_path,
                textwrap.dedent(
                    """
                    factor_catalog_mapping:
                      source_catalog: references/common/pg16_factor_catalog.md
                      object_domain: database
                      imported_factors:
                        - catalog_factor: database.naming.name_shape
                          local_factor: missing_database_name_shape
                          target_tier: T3
                          coverage_role: rotate_attach
                          value_policy: reuse_catalog_values
                          reason: Invalid local factor should fail.
                    """
                ).strip(),
            )

            result = audit.audit_paths(catalog_path, [statement_path])

            self.assertFalse(result.passed)
            self.assertIn("local factor is not defined", "\n".join(result.errors))

    def test_rotate_attach_must_be_non_main_factor(self) -> None:
        audit = load_audit_module()
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            catalog_path = root / "pg16_factor_catalog.md"
            statement_path = root / "create_database.md"
            write_catalog(catalog_path)
            write_statement(
                statement_path,
                textwrap.dedent(
                    """
                    factor_catalog_mapping:
                      source_catalog: references/common/pg16_factor_catalog.md
                      object_domain: database
                      imported_factors:
                        - catalog_factor: database.options.owner
                          local_factor: statement_branch
                          target_tier: T1
                          coverage_role: rotate_attach
                          value_policy: reuse_catalog_values
                          reason: rotate_attach cannot point at a main axis.
                    """
                ).strip(),
            )

            result = audit.audit_paths(catalog_path, [statement_path])

            self.assertFalse(result.passed)
            self.assertIn("rotate_attach factor must be listed in non_main_factors", "\n".join(result.errors))

    def test_main_missing_catalog_prints_error_without_traceback(self) -> None:
        audit = load_audit_module()
        with TemporaryDirectory() as raw_dir:
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = audit.main(["--root", raw_dir])

        output = stdout.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR:", output)
        self.assertIn("FAIL factor catalog mapping audit", output)
        self.assertNotIn("Traceback", output)

    def test_main_non_mapping_catalog_yaml_prints_error_without_traceback(self) -> None:
        audit = load_audit_module()
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            catalog_path = root / "pg16_factor_catalog.md"
            catalog_path.write_text(
                textwrap.dedent(
                    """
                    # Invalid Catalog

                    ```yaml
                    - not_a_mapping
                    ```
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = audit.main(["--root", raw_dir, "--catalog", str(catalog_path)])

        output = stdout.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR:", output)
        self.assertIn("structured yaml must be a mapping", output)
        self.assertNotIn("Traceback", output)


if __name__ == "__main__":
    unittest.main()
