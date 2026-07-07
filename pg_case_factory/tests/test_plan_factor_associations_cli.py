from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "plan_factor_associations.py"


def write_file(root: Path, relative_path: str, content: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return path


def write_mini_repository(root: Path) -> Path:
    write_file(
        root,
        "skills/pg-sql-generation/references/statements/ddl/index/create_index.md",
        """
        # CREATE INDEX

        ```yaml
        structured_config:
          kind: statement
          statement:
            key: create_index
            name: CREATE INDEX
          factors:
            target_relation_kind:
              label: 目标关系类型
              values: [ordinary_table, partitioned_table]
            data_type:
              label: 列数据类型
              values: [integer, text]
            concurrently:
              label: CONCURRENTLY
              values: [false, true]
            data_profile:
              label: 数据分布
              values: [empty, duplicates]
            expected_status:
              label: 预期结果
              values: [success, failure]
        ```
        """,
    )
    matrix_path = write_file(
        root,
        "skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml",
        """
        kind: statement_combination_matrix
        statement:
          key: create_index
          name: CREATE INDEX
        coverage_scope:
          target_relation_coverage:
            required: true
            coverage_mode: representative
            required_relation_kinds: [ordinary_table, partitioned_table]
          column_type_coverage:
            required: true
            coverage_mode: representative
            required_type_set: fixture_index_types
        combination_groups:
          - id: reject_view
            default_expected_status: failure
            factors:
              expected_status: failure
        """,
    )
    write_file(
        root,
        "skills/pg-sql-generation/references/common/pg16_type_catalog.md",
        """
        # PG16 Type Catalog

        ```yaml
        structured_config:
          kind: type_catalog
          type_sets:
            fixture_index_types:
              types: [integer, text]
          types:
            integer:
              type_category: numeric
            text:
              type_category: string
        ```
        """,
    )
    write_file(
        root,
        "skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml",
        """
        kind: coverage_inventory
        negative_controls:
          - id: unsupported_relation
        """,
    )
    return matrix_path


def run_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def test_statement_resolution_writes_default_factor_association_plan(tmp_path):
    write_mini_repository(tmp_path)

    result = run_cli(tmp_path, "--statement", "create_index")

    output_path = tmp_path / "artifacts/intermediates/create_index_association_plan.yaml"
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith(
        "PASS factor association plan: statement=create_index families="
    )
    assert " obligations=" in result.stdout
    assert output_path.exists()
    plan = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert plan["kind"] == "factor_association_plan"
    assert plan["scenario_families"]


def test_matrix_resolution_finds_matching_statement_reference_and_output_path(tmp_path):
    matrix_path = write_mini_repository(tmp_path)
    output_path = tmp_path / "custom/plan.yaml"

    result = run_cli(tmp_path, "--matrix", str(matrix_path), "--output", str(output_path))

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith(
        "PASS factor association plan: statement=create_index families="
    )
    assert output_path.exists()
    plan = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert plan["kind"] == "factor_association_plan"
    assert plan["target_statement"]["key"] == "create_index"
    assert plan["scenario_families"]


def test_statement_resolution_allows_missing_matrix_for_new_statement(tmp_path):
    write_file(
        tmp_path,
        "skills/pg-sql-generation/references/statements/ddl/example/new_statement.md",
        """
        # NEW STATEMENT

        ```yaml
        structured_config:
          kind: statement
          statement:
            key: new_statement
            name: NEW STATEMENT
          factors:
            data_profile:
              label: 数据分布
              values: [empty, duplicate_rows]
            expected_status:
              label: 预期结果
              values: [success, failure]
        ```
        """,
    )

    result = run_cli(tmp_path, "--statement", "new_statement")

    output_path = tmp_path / "artifacts/intermediates/new_statement_association_plan.yaml"
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith(
        "PASS factor association plan: statement=new_statement families="
    )
    assert output_path.exists()
    plan = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    family_ids = {family["id"] for family in plan["scenario_families"]}
    assert "data_profile_matrix" in family_ids
    assert "negative_control_matrix" in family_ids
