# PG16 Factor Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first implementation slice for integrating the department PG16 factor list into the existing statement-reference factor system.

**Architecture:** Add a global factor catalog and statement-level mapping layer while keeping the existing SQL generator path unchanged. A small static audit script validates that mapped catalog factors exist, local factors exist, tiers match `factor_layers`, and coverage roles match `coverage_policy`.

**Tech Stack:** Python 3.9, PyYAML, `unittest`, Markdown reference files with fenced YAML `structured_config` blocks.

---

## Scope

This plan implements the foundation plus one end-to-end object-domain example: `database`. It also seeds the first-batch catalog domains so the structure is ready for later mapping work.

This plan does not rewrite all 183 statement references. It modifies only the database statement references as a proof of the migration model.

## Files

- Create: `pg_case_factory/tools/audit_factor_catalog_mapping.py`
  Static validator for factor catalog and statement mapping consistency.
- Create: `pg_case_factory/tests/test_factor_catalog_mapping_audit.py`
  Unit tests for the audit script.
- Create: `pg_case_factory/skills/pg-sql-generation/references/common/pg16_factor_catalog.md`
  Global PG16 factor catalog, with `database` detailed and first-batch domains seeded.
- Create: `pg_case_factory/skills/pg-sql-generation/references/templates/factor_catalog_mapping_template.md`
  Copyable mapping template for statement references.
- Modify: `pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/create_database.md`
  Add `factor_catalog_mapping`.
- Modify: `pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/alter_database.md`
  Add `factor_catalog_mapping`.
- Modify: `pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/drop_database.md`
  Add `factor_catalog_mapping`.
- Create: `pg_case_factory/docs/pg16_factor_catalog_mapping_status.md`
  First migration status report.
- Modify: `pg_case_factory/PROJECT_STRUCTURE.md`
  Mention the new catalog, mapping template, and audit script.

## Task 1: Add Audit Tests

**Files:**
- Create: `pg_case_factory/tests/test_factor_catalog_mapping_audit.py`
- Test command: `python3 -m unittest tests/test_factor_catalog_mapping_audit.py -v`

- [ ] **Step 1: Create the test directory**

Run:

```bash
mkdir -p tests
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_factor_catalog_mapping_audit.py` with this content:

```python
import importlib.util
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "audit_factor_catalog_mapping.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_factor_catalog_mapping", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
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
              {mapping_block}
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests and verify they fail because the script is missing**

Run:

```bash
python3 -m unittest tests/test_factor_catalog_mapping_audit.py -v
```

Expected: fail with a file-loading error mentioning `tools/audit_factor_catalog_mapping.py`.

- [ ] **Step 4: Commit the failing tests**

Run:

```bash
git add pg_case_factory/tests/test_factor_catalog_mapping_audit.py
git commit -m "test: add factor catalog mapping audit tests"
```

## Task 2: Implement Factor Catalog Mapping Audit Script

**Files:**
- Create: `pg_case_factory/tools/audit_factor_catalog_mapping.py`
- Test: `pg_case_factory/tests/test_factor_catalog_mapping_audit.py`

- [ ] **Step 1: Create the tools directory**

Run:

```bash
mkdir -p tools
```

- [ ] **Step 2: Write the audit script**

Create `tools/audit_factor_catalog_mapping.py` with this content:

```python
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml


YAML_BLOCK_PATTERN = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)
ALLOWED_COVERAGE_ROLES = {
    "main_axis",
    "representative_or_main",
    "representative",
    "rotate_attach",
    "audit_only",
}
ALLOWED_VALUE_POLICIES = {
    "reuse_catalog_values",
    "statement_specific_subset",
    "statement_specific_override",
}


@dataclass
class AuditResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    mapped_count: int = 0
    excluded_count: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors


def _load_structured_config(path: Path) -> dict:
    raw_text = path.read_text(encoding="utf-8")
    match = YAML_BLOCK_PATTERN.search(raw_text)
    if not match:
        raise ValueError(f"{path}: no fenced yaml block found")

    parsed = yaml.safe_load(match.group(1)) or {}
    config = dict(parsed.get("structured_config") or parsed)
    if not config:
        raise ValueError(f"{path}: empty structured config")
    return config


def _catalog_factor_paths(catalog_config: dict) -> set[str]:
    paths: set[str] = set()
    object_domains = dict(catalog_config.get("object_domains") or {})
    for domain_key, domain_doc in object_domains.items():
        domain_doc = dict(domain_doc or {})
        normalized_domain_key = str(domain_doc.get("key") or domain_key)
        factor_groups = dict(domain_doc.get("factor_groups") or {})
        for group_key, group_doc in factor_groups.items():
            group_doc = dict(group_doc or {})
            normalized_group_key = str(group_doc.get("key") or group_key)
            factors = dict(group_doc.get("factors") or {})
            for factor_key, factor_doc in factors.items():
                factor_doc = dict(factor_doc or {})
                normalized_factor_key = str(factor_doc.get("key") or factor_key)
                paths.add(f"{normalized_domain_key}.{normalized_group_key}.{normalized_factor_key}")
    return paths


def _catalog_domains(catalog_config: dict) -> set[str]:
    domains: set[str] = set()
    for domain_key, domain_doc in dict(catalog_config.get("object_domains") or {}).items():
        domain_doc = dict(domain_doc or {})
        domains.add(str(domain_doc.get("key") or domain_key))
    return domains


def _catalog_values(catalog_config: dict) -> dict[str, set[str]]:
    values_by_factor: dict[str, set[str]] = {}
    object_domains = dict(catalog_config.get("object_domains") or {})
    for domain_key, domain_doc in object_domains.items():
        domain_doc = dict(domain_doc or {})
        normalized_domain_key = str(domain_doc.get("key") or domain_key)
        factor_groups = dict(domain_doc.get("factor_groups") or {})
        for group_key, group_doc in factor_groups.items():
            group_doc = dict(group_doc or {})
            normalized_group_key = str(group_doc.get("key") or group_key)
            factors = dict(group_doc.get("factors") or {})
            for factor_key, factor_doc in factors.items():
                factor_doc = dict(factor_doc or {})
                normalized_factor_key = str(factor_doc.get("key") or factor_key)
                factor_path = f"{normalized_domain_key}.{normalized_group_key}.{normalized_factor_key}"
                values_by_factor[factor_path] = {
                    str(dict(item).get("key"))
                    for item in list(factor_doc.get("values") or [])
                    if isinstance(item, dict) and dict(item).get("key")
                }
    return values_by_factor


def _factor_tiers(statement_config: dict) -> dict[str, str]:
    tiers: dict[str, str] = {}
    for layer in list(statement_config.get("factor_layers") or []):
        layer = dict(layer or {})
        tier = str(layer.get("tier") or "")
        for factor in list(layer.get("factors") or []):
            tiers[str(factor)] = tier
    return tiers


def _statement_factor_names(statement_config: dict) -> set[str]:
    return {str(name) for name in dict(statement_config.get("factors") or {}).keys()}


def _coverage_sets(statement_config: dict) -> tuple[set[str], set[str]]:
    coverage_policy = dict(statement_config.get("coverage_policy") or {})
    main_axes = {str(item) for item in list(coverage_policy.get("main_combination_axes") or [])}
    non_main = {str(item) for item in list(coverage_policy.get("non_main_factors") or [])}
    return main_axes, non_main


def _mapping_entries(mapping: dict) -> Iterable[tuple[str, dict]]:
    for item in list(mapping.get("imported_factors") or []):
        yield "imported_factors", dict(item or {})
    for item in list(mapping.get("promoted_factors") or []):
        yield "promoted_factors", dict(item or {})


def _validate_mapping_entry(
    result: AuditResult,
    statement_path: Path,
    section: str,
    entry: dict,
    catalog_paths: set[str],
    catalog_values: dict[str, set[str]],
    factor_names: set[str],
    factor_tiers: dict[str, str],
    main_axes: set[str],
    non_main: set[str],
) -> None:
    catalog_factor = str(entry.get("catalog_factor") or "")
    local_factor = str(entry.get("local_factor") or "")
    target_tier = str(entry.get("target_tier") or "")
    coverage_role = str(entry.get("coverage_role") or "representative")
    value_policy = str(entry.get("value_policy") or "reuse_catalog_values")
    prefix = f"{statement_path}: {section}: {catalog_factor or '<missing catalog_factor>'}"

    if catalog_factor not in catalog_paths:
        result.errors.append(f"{prefix}: catalog factor is not defined")
    if not local_factor:
        result.errors.append(f"{prefix}: local_factor is required")
        return
    if local_factor not in factor_names:
        result.errors.append(f"{prefix}: local factor is not defined: {local_factor}")

    actual_tier = factor_tiers.get(local_factor)
    if target_tier and actual_tier and target_tier != actual_tier:
        result.errors.append(f"{prefix}: target_tier {target_tier} does not match factor_layers tier {actual_tier} for {local_factor}")
    if target_tier and local_factor in factor_names and local_factor not in factor_tiers:
        result.errors.append(f"{prefix}: local factor {local_factor} is not listed in factor_layers")

    if coverage_role not in ALLOWED_COVERAGE_ROLES:
        result.errors.append(f"{prefix}: unsupported coverage_role {coverage_role}")
    if value_policy not in ALLOWED_VALUE_POLICIES:
        result.errors.append(f"{prefix}: unsupported value_policy {value_policy}")

    if coverage_role == "main_axis" and local_factor not in main_axes:
        result.errors.append(f"{prefix}: main_axis factor must be listed in main_combination_axes: {local_factor}")
    if coverage_role == "rotate_attach" and local_factor not in non_main:
        result.errors.append(f"{prefix}: rotate_attach factor must be listed in non_main_factors: {local_factor}")
    if coverage_role == "representative_or_main" and local_factor not in main_axes and local_factor not in non_main:
        result.errors.append(f"{prefix}: representative_or_main factor must be in main_combination_axes or non_main_factors: {local_factor}")
    if coverage_role == "representative" and local_factor not in main_axes and local_factor not in non_main:
        result.warnings.append(f"{prefix}: representative factor is not listed in coverage_policy: {local_factor}")

    selected_values = [str(item) for item in list(entry.get("selected_values") or [])]
    if value_policy == "statement_specific_subset" and not selected_values:
        result.errors.append(f"{prefix}: statement_specific_subset requires selected_values")
    if selected_values and catalog_factor in catalog_values:
        unknown_values = sorted(set(selected_values) - catalog_values[catalog_factor])
        if unknown_values:
            result.errors.append(f"{prefix}: selected_values not found in catalog: {', '.join(unknown_values)}")

    reason = str(entry.get("reason") or "").strip()
    if not reason:
        result.errors.append(f"{prefix}: reason is required")

    result.mapped_count += 1


def _validate_statement_mapping(
    result: AuditResult,
    statement_path: Path,
    statement_config: dict,
    catalog_domains: set[str],
    catalog_paths: set[str],
    catalog_values: dict[str, set[str]],
) -> None:
    mapping = dict(statement_config.get("factor_catalog_mapping") or {})
    if not mapping:
        return

    object_domain = str(mapping.get("object_domain") or "")
    if object_domain not in catalog_domains:
        result.errors.append(f"{statement_path}: factor_catalog_mapping.object_domain is not in catalog: {object_domain}")

    factor_names = _statement_factor_names(statement_config)
    factor_tiers = _factor_tiers(statement_config)
    main_axes, non_main = _coverage_sets(statement_config)

    for section, entry in _mapping_entries(mapping):
        _validate_mapping_entry(
            result,
            statement_path,
            section,
            entry,
            catalog_paths,
            catalog_values,
            factor_names,
            factor_tiers,
            main_axes,
            non_main,
        )

    for item in list(mapping.get("excluded_factors") or []):
        item = dict(item or {})
        catalog_factor = str(item.get("catalog_factor") or "")
        reason = str(item.get("reason") or "").strip()
        prefix = f"{statement_path}: excluded_factors: {catalog_factor or '<missing catalog_factor>'}"
        if catalog_factor not in catalog_paths:
            result.errors.append(f"{prefix}: catalog factor is not defined")
        if not reason:
            result.errors.append(f"{prefix}: reason is required")
        result.excluded_count += 1


def audit_paths(catalog_path: Path, statement_paths: list[Path]) -> AuditResult:
    result = AuditResult()
    catalog_config = _load_structured_config(catalog_path)
    catalog_paths = _catalog_factor_paths(catalog_config)
    catalog_domains = _catalog_domains(catalog_config)
    catalog_values = _catalog_values(catalog_config)

    if not catalog_paths:
        result.errors.append(f"{catalog_path}: catalog contains no factors")

    for statement_path in statement_paths:
        statement_config = _load_structured_config(statement_path)
        _validate_statement_mapping(
            result,
            statement_path,
            statement_config,
            catalog_domains,
            catalog_paths,
            catalog_values,
        )

    return result


def _default_statement_paths(root: Path) -> list[Path]:
    return sorted((root / "skills" / "pg-sql-generation" / "references" / "statements").glob("**/*.md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit PG16 factor catalog mappings in statement references.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="pg_case_factory project root",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="factor catalog path; defaults to skills/pg-sql-generation/references/common/pg16_factor_catalog.md",
    )
    parser.add_argument(
        "statements",
        nargs="*",
        type=Path,
        help="statement reference files to audit; defaults to all statement references",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    catalog_path = args.catalog or root / "skills" / "pg-sql-generation" / "references" / "common" / "pg16_factor_catalog.md"
    statement_paths = args.statements or _default_statement_paths(root)
    result = audit_paths(catalog_path, [path.resolve() for path in statement_paths])

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    if result.passed:
        print(f"PASS factor catalog mapping audit: mapped={result.mapped_count} excluded={result.excluded_count}")
        return 0

    print(f"FAIL factor catalog mapping audit: mapped={result.mapped_count} excluded={result.excluded_count} errors={len(result.errors)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 3: Run the unit tests**

Run:

```bash
python3 -m unittest tests/test_factor_catalog_mapping_audit.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 4: Commit the audit script**

Run:

```bash
git add pg_case_factory/tools/audit_factor_catalog_mapping.py pg_case_factory/tests/test_factor_catalog_mapping_audit.py
git commit -m "feat: add factor catalog mapping audit"
```

## Task 3: Add PG16 Factor Catalog

**Files:**
- Create: `pg_case_factory/skills/pg-sql-generation/references/common/pg16_factor_catalog.md`
- Test command: `python3 tools/audit_factor_catalog_mapping.py --root .`

- [ ] **Step 1: Write the catalog file**

Create `skills/pg-sql-generation/references/common/pg16_factor_catalog.md` with this content:

````markdown
# 技能：PG16 Factor Catalog

## 作用

本 reference 将部门梳理的 PostgreSQL 16 因子沉淀为全局对象域因子目录。它只说明“有哪些可测维度”，不直接决定 SQL 生成规模。具体 statement 是否使用某个因子、映射到 T1-T6 哪一层、是否进入主组合，由 statement reference 的 `factor_catalog_mapping` 和 `coverage_policy` 决定。

## 使用方式

- 新增或补齐 statement reference 时，先查找对应 `object_domain`。
- 将适用因子映射到本 statement 的局部因子。
- 不适用的全局因子必须在 statement 映射中说明排除原因。
- 全局目录中的 `default_tier` 和 `default_coverage_role` 是默认建议，不覆盖 statement 的局部判断。

## 结构化配置

```yaml
structured_config:
  kind: factor_catalog
  skill_name: pg16_factor_catalog
  version: pg16
  object_domains:
    database:
      key: database
      label: 数据库
      applies_to:
        - create_database
        - alter_database
        - drop_database
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
              description: 覆盖普通标识符、引号标识符、保留字、长度边界、特殊字符和 pg_ 前缀。
              values:
                - key: valid_unquoted_lower
                  label: 合法未加引号小写名称
                  expected_status: success
                - key: valid_unquoted_mixed_case
                  label: 未加引号混合大小写名称
                  expected_status: success
                - key: valid_quoted_upper
                  label: 加双引号全大写名称
                  expected_status: success
                - key: quoted_reserved_keyword
                  label: 加双引号保留字
                  expected_status: success
                - key: reserved_keyword_unquoted
                  label: 未加引号保留字
                  expected_status: failure
                - key: invalid_special_char_unquoted
                  label: 未加引号特殊字符
                  expected_status: failure
                - key: invalid_space_unquoted
                  label: 未加引号包含空格
                  expected_status: failure
                - key: max_length_63_bytes
                  label: 63 字节名称边界
                  expected_status: success
                - key: over_length_64_bytes
                  label: 64 字节名称边界
                  expected_status: boundary
                - key: pg_prefix_non_superuser
                  label: 普通用户使用 pg_ 前缀
                  expected_status: failure
              notes:
                - PostgreSQL 标识符限制按字节计算，边界用例必须按实际编码确认。
        options:
          key: options
          label: CREATE/ALTER DATABASE 选项因子
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
                - key: valid_current_user
                  label: 当前用户
                  expected_status: success
                - key: valid_other_role
                  label: 可 SET ROLE 的其他角色
                  expected_status: success
                - key: nonexistent_user
                  label: 不存在的用户
                  expected_status: failure
                - key: no_set_role_privilege
                  label: 无法 SET ROLE 到目标 owner
                  expected_status: failure
            template:
              key: template
              label: TEMPLATE 子句
              values:
                - key: omitted_default_template1
                  label: 省略，默认 template1
                  expected_status: success
                - key: template0
                  label: 指定 template0
                  expected_status: success
                - key: custom_template
                  label: 自定义模板
                  expected_status: success
                - key: nonexistent_template
                  label: 不存在模板
                  expected_status: failure
                - key: template_has_connections
                  label: 模板存在其他连接
                  expected_status: failure
            encoding:
              key: encoding
              label: ENCODING 子句
              values:
                - key: omitted_client_default
                  label: 省略，使用客户端默认编码
                  expected_status: success
                - key: utf8
                  label: UTF8
                  expected_status: success
                - key: latin1
                  label: LATIN1
                  expected_status: context_dependent
                - key: sql_ascii
                  label: SQL_ASCII
                  expected_status: context_dependent
                - key: invalid_encoding
                  label: 无效编码
                  expected_status: failure
            locale:
              key: locale
              label: LOCALE / LC_COLLATE / LC_CTYPE
              values:
                - key: omitted
                  label: 省略 locale
                  expected_status: success
                - key: c_locale
                  label: C locale
                  expected_status: success
                - key: posix_locale
                  label: POSIX locale
                  expected_status: success
                - key: valid_system_locale
                  label: 系统存在的 locale
                  expected_status: context_dependent
                - key: nonexistent_locale
                  label: 系统不存在的 locale
                  expected_status: failure
                - key: encoding_locale_mismatch
                  label: 编码与 locale 不兼容
                  expected_status: failure
            strategy:
              key: strategy
              label: STRATEGY 子句
              values:
                - key: omitted_default_wal_log
                  label: 省略，默认 WAL_LOG
                  expected_status: success
                - key: wal_log
                  label: STRATEGY WAL_LOG
                  expected_status: success
                - key: file_copy
                  label: STRATEGY FILE_COPY
                  expected_status: success
                - key: invalid_strategy
                  label: 无效 STRATEGY
                  expected_status: failure
            allow_connections:
              key: allow_connections
              label: ALLOW_CONNECTIONS 选项
              values:
                - key: true
                  label: 允许连接
                  expected_status: success
                - key: false
                  label: 禁止连接
                  expected_status: success
            connection_limit:
              key: connection_limit
              label: CONNECTION LIMIT 选项
              values:
                - key: positive
                  label: 正整数限制
                  expected_status: success
                - key: unlimited_negative_one
                  label: -1 不限制
                  expected_status: success
                - key: zero
                  label: 0 不允许普通连接
                  expected_status: success
            is_template:
              key: is_template
              label: IS_TEMPLATE 选项
              values:
                - key: true
                  label: 可作为模板
                  expected_status: success
                - key: false
                  label: 不作为模板
                  expected_status: success
            tablespace:
              key: tablespace
              label: TABLESPACE 子句
              values:
                - key: omitted_default
                  label: 省略，使用默认表空间
                  expected_status: success
                - key: pg_default
                  label: 显式指定 pg_default
                  expected_status: success
                - key: valid_tablespace
                  label: 有效表空间
                  expected_status: success
                - key: nonexistent_tablespace
                  label: 不存在表空间
                  expected_status: failure
                - key: no_create_privilege
                  label: 无 CREATE 权限
                  expected_status: failure
            config_parameter:
              key: config_parameter
              label: ALTER DATABASE 配置参数
              values:
                - key: common_parameter
                  label: 普通参数
                  expected_status: success
                - key: superuser_only_parameter
                  label: superuser-only 参数
                  expected_status: context_dependent
                - key: reset_all
                  label: RESET ALL
                  expected_status: success
        operation:
          key: operation
          label: DROP DATABASE 操作因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            if_exists:
              key: if_exists
              label: IF EXISTS 子句
              values:
                - key: omitted
                  label: 省略 IF EXISTS
                  expected_status: context_dependent
                - key: specified
                  label: 指定 IF EXISTS
                  expected_status: success
            force:
              key: force
              label: WITH (FORCE) 选项
              values:
                - key: omitted
                  label: 省略 FORCE
                  expected_status: context_dependent
                - key: specified
                  label: 指定 FORCE
                  expected_status: context_dependent
        environment:
          key: environment
          label: 依赖对象与环境因子
          default_tier: T4
          default_coverage_role: rotate_attach
          factors:
            privilege_level:
              key: privilege_level
              label: 执行权限
              values:
                - key: superuser
                  label: superuser
                  expected_status: success
                - key: createdb_role
                  label: 拥有 CREATEDB 的角色
                  expected_status: success
                - key: database_owner
                  label: database owner
                  expected_status: success
                - key: non_owner
                  label: 非 owner
                  expected_status: failure
            template_existence:
              key: template_existence
              label: 模板数据库存在性与连接状态
              values:
                - key: exists_no_connections
                  label: 存在且无其他连接
                  expected_status: success
                - key: exists_has_connections
                  label: 存在但有其他连接
                  expected_status: failure
                - key: not_exists
                  label: 不存在
                  expected_status: failure
            encoding_locale_compatibility:
              key: encoding_locale_compatibility
              label: 编码与 locale 兼容性
              values:
                - key: compatible
                  label: 兼容
                  expected_status: success
                - key: incompatible
                  label: 不兼容
                  expected_status: failure
                - key: template_mismatch
                  label: 与模板不匹配且未使用 template0
                  expected_status: failure
            role_set_role_ability:
              key: role_set_role_ability
              label: SET ROLE 能力
              values:
                - key: can_set_role
                  label: 能 SET ROLE
                  expected_status: success
                - key: cannot_set_role
                  label: 不能 SET ROLE
                  expected_status: failure
            tablespace_existence:
              key: tablespace_existence
              label: 表空间存在性
              values:
                - key: exists
                  label: 表空间存在
                  expected_status: success
                - key: not_exists
                  label: 表空间不存在
                  expected_status: failure
            connection_state:
              key: connection_state
              label: 目标数据库连接状态
              values:
                - key: no_other_connections
                  label: 无其他连接
                  expected_status: success
                - key: has_other_connections
                  label: 有其他连接
                  expected_status: context_dependent
                - key: connected_to_target_database
                  label: 当前连接到目标数据库
                  expected_status: failure
        boundary:
          key: boundary
          label: 异常与边界因子
          default_tier: T5
          default_coverage_role: rotate_attach
          factors:
            duplicate_name:
              key: duplicate_name
              label: 重名冲突
              values:
                - key: no_conflict
                  label: 无冲突
                  expected_status: success
                - key: name_already_exists
                  label: 名称已存在
                  expected_status: failure
            privilege_denied:
              key: privilege_denied
              label: 权限不足
              values:
                - key: has_privilege
                  label: 有权限
                  expected_status: success
                - key: missing_createdb
                  label: 缺少 CREATEDB
                  expected_status: failure
                - key: non_owner_operation
                  label: 非 owner 执行 owner-only 操作
                  expected_status: failure
            inside_transaction:
              key: inside_transaction
              label: 事务块内执行
              values:
                - key: outside_transaction
                  label: 事务块外
                  expected_status: success
                - key: inside_transaction
                  label: 事务块内
                  expected_status: failure
            active_connections:
              key: active_connections
              label: 活动连接边界
              values:
                - key: no_active_connections
                  label: 无活动连接
                  expected_status: success
                - key: has_terminable_connections
                  label: 有可终止连接
                  expected_status: context_dependent
                - key: has_unterminable_connections
                  label: 有不可终止连接
                  expected_status: failure
        validation:
          key: validation
          label: 验证与清理因子
          default_tier: T6
          default_coverage_role: rotate_attach
          factors:
            catalog_check:
              key: catalog_check
              label: 系统表验证
              values:
                - key: pg_database_presence
                  label: 查询 pg_database 验证存在
                  expected_status: success
                - key: pg_database_absence
                  label: 查询 pg_database 验证不存在
                  expected_status: success
                - key: error_assertion
                  label: 错误断言
                  expected_status: success
            cleanup:
              key: cleanup
              label: 清理策略
              values:
                - key: drop_database
                  label: DROP DATABASE 清理
                  expected_status: success
                - key: force_drop_database
                  label: FORCE 清理
                  expected_status: success
                - key: reset_config_parameter
                  label: RESET 配置参数
                  expected_status: success

    domain:
      key: domain
      label: 域
      applies_to:
        - create_domain
        - alter_domain
        - drop_domain
      factor_groups:
        naming:
          key: naming
          label: 域名因子
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: 域名形态
              values:
                - key: valid_identifier
                  label: 合法标识符
                  expected_status: success
                - key: quoted_reserved_keyword
                  label: 加双引号保留字
                  expected_status: success
                - key: invalid_unquoted_special_char
                  label: 未加引号特殊字符
                  expected_status: failure
        definition:
          key: definition
          label: 域定义因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            base_data_type:
              key: base_data_type
              label: 底层基类型
              values:
                - key: integer
                  label: integer
                  expected_status: success
                - key: text
                  label: text
                  expected_status: success
                - key: domain_based_on_domain
                  label: 域基于域
                  expected_status: success
                - key: nonexistent_type
                  label: 不存在类型
                  expected_status: failure
            constraint:
              key: constraint
              label: 域约束
              values:
                - key: not_null
                  label: NOT NULL
                  expected_status: success
                - key: null_constraint
                  label: NULL
                  expected_status: success
                - key: check_value
                  label: CHECK (VALUE ...)
                  expected_status: success
                - key: check_subquery
                  label: CHECK 中包含子查询
                  expected_status: failure

    schema:
      key: schema
      label: Schema
      applies_to:
        - create_schema
        - alter_schema
        - drop_schema
      factor_groups:
        naming:
          key: naming
          label: Schema 名称
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: Schema 名称形态
              values:
                - key: valid_identifier
                  label: 合法标识符
                  expected_status: success
                - key: existing_schema
                  label: 已存在 schema
                  expected_status: failure
        ownership:
          key: ownership
          label: 所有者与权限
          default_tier: T4
          default_coverage_role: rotate_attach
          factors:
            owner:
              key: owner
              label: Schema owner
              values:
                - key: current_user
                  label: 当前用户
                  expected_status: success
                - key: nonexistent_owner
                  label: 不存在 owner
                  expected_status: failure

    role_user_group:
      key: role_user_group
      label: Role/User/Group
      applies_to:
        - create_role
        - alter_role
        - drop_role
        - create_user
        - alter_user
        - drop_user
        - create_group
        - alter_group
        - drop_group
      factor_groups:
        identity:
          key: identity
          label: 身份因子
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: 角色名称形态
              values:
                - key: valid_role_name
                  label: 合法角色名
                  expected_status: success
                - key: duplicate_role_name
                  label: 重复角色名
                  expected_status: failure
        privileges:
          key: privileges
          label: 角色权限
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            role_attribute:
              key: role_attribute
              label: 角色属性
              values:
                - key: login
                  label: LOGIN
                  expected_status: success
                - key: createdb
                  label: CREATEDB
                  expected_status: success
                - key: createrole
                  label: CREATEROLE
                  expected_status: success

    tablespace:
      key: tablespace
      label: 表空间
      applies_to:
        - create_tablespace
        - alter_tablespace
        - drop_tablespace
      factor_groups:
        naming:
          key: naming
          label: 表空间名称
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: 表空间名称形态
              values:
                - key: valid_identifier
                  label: 合法表空间名
                  expected_status: success
                - key: pg_default
                  label: 内置表空间 pg_default
                  expected_status: context_dependent
        storage:
          key: storage
          label: 存储位置
          default_tier: T4
          default_coverage_role: rotate_attach
          factors:
            location:
              key: location
              label: LOCATION 路径
              values:
                - key: valid_empty_directory
                  label: 有效空目录
                  expected_status: success
                - key: nonexistent_directory
                  label: 不存在目录
                  expected_status: failure
                - key: permission_denied_directory
                  label: 无权限目录
                  expected_status: failure

    extension:
      key: extension
      label: 扩展
      applies_to:
        - create_extension
        - alter_extension
        - drop_extension
      factor_groups:
        installation:
          key: installation
          label: 安装因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            target_schema:
              key: target_schema
              label: 安装目标 schema
              values:
                - key: omitted
                  label: 省略 schema
                  expected_status: success
                - key: valid_schema
                  label: 有效 schema
                  expected_status: success
                - key: nonexistent_schema
                  label: 不存在 schema
                  expected_status: failure
            version:
              key: version
              label: 扩展版本
              values:
                - key: default_version
                  label: 默认版本
                  expected_status: success
                - key: explicit_valid_version
                  label: 指定有效版本
                  expected_status: success
                - key: nonexistent_version
                  label: 不存在版本
                  expected_status: failure

    sequence:
      key: sequence
      label: 序列
      applies_to:
        - create_sequence
        - alter_sequence
        - drop_sequence
      factor_groups:
        definition:
          key: definition
          label: 序列定义因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            data_type:
              key: data_type
              label: AS data_type
              values:
                - key: smallint
                  label: smallint
                  expected_status: success
                - key: integer
                  label: integer
                  expected_status: success
                - key: bigint
                  label: bigint
                  expected_status: success
            increment:
              key: increment
              label: INCREMENT
              values:
                - key: positive
                  label: 正增量
                  expected_status: success
                - key: negative
                  label: 负增量
                  expected_status: success
                - key: zero
                  label: 零增量
                  expected_status: failure
            bounds:
              key: bounds
              label: MINVALUE / MAXVALUE
              values:
                - key: default_bounds
                  label: 默认边界
                  expected_status: success
                - key: explicit_valid_bounds
                  label: 显式合法边界
                  expected_status: success
                - key: min_greater_than_max
                  label: 最小值大于最大值
                  expected_status: failure
```
````

- [ ] **Step 2: Run the audit script before statement mappings exist**

Run:

```bash
python3 tools/audit_factor_catalog_mapping.py --root .
```

Expected: pass with `mapped=0 excluded=0` because no statement reference has mapping yet.

- [ ] **Step 3: Commit the catalog**

Run:

```bash
git add pg_case_factory/skills/pg-sql-generation/references/common/pg16_factor_catalog.md
git commit -m "feat: add PG16 factor catalog"
```

## Task 4: Add Mapping Template

**Files:**
- Create: `pg_case_factory/skills/pg-sql-generation/references/templates/factor_catalog_mapping_template.md`

- [ ] **Step 1: Write the mapping template**

Create `skills/pg-sql-generation/references/templates/factor_catalog_mapping_template.md` with this content:

````markdown
# 模板：Factor Catalog Mapping

## 使用方式

将本模板中的 `factor_catalog_mapping` 片段复制到 statement reference 的 `structured_config` 中，放在 `coverage_policy` 之后、`rendering` 之前。

`factor_catalog_mapping` 只描述全局因子与当前 statement 局部因子的关系，不直接改变 SQL 渲染逻辑。生成规模仍由 `coverage_policy.main_combination_axes` 和 `coverage_policy.non_main_factors` 控制。

## 映射片段

```yaml
factor_catalog_mapping:
  source_catalog: references/common/pg16_factor_catalog.md
  object_domain: example_domain
  imported_factors:
    - catalog_factor: example_domain.naming.name_shape
      local_factor: example_name_shape
      target_tier: T3
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
        - valid_identifier
        - quoted_reserved_keyword
      reason: 当前 statement 需要覆盖对象名称输入形态。
  promoted_factors:
    - catalog_factor: example_domain.options.primary_option
      local_factor: primary_option_clause
      from_default_tier: T4
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: 该选项在当前 statement 中属于官方关键语义分支。
  excluded_factors:
    - catalog_factor: example_domain.options.unused_option
      reason: 当前 statement 的官方语法不包含该选项。
  coverage_notes:
    - 命名类因子只做轮转挂靠，不进入主笛卡尔积。
```

## 字段说明

```text
catalog_factor
全局因子路径，格式为 object_domain.factor_group.factor。

local_factor
当前 statement reference 中 `factors` 下的局部因子名。

target_tier
局部因子所在 T1-T6 分层，必须与 `factor_layers` 一致。

coverage_role
允许值：main_axis、representative_or_main、representative、rotate_attach、audit_only。

value_policy
允许值：reuse_catalog_values、statement_specific_subset、statement_specific_override。

selected_values
当 value_policy 为 statement_specific_subset 时，列出实际使用的 catalog value key。

reason
说明映射或排除原因，必须可被审计人员理解。
```

## 审计清单

```text
1. catalog_factor 必须存在于 pg16_factor_catalog.md。
2. local_factor 必须存在于当前 statement 的 factors。
3. target_tier 必须与 factor_layers 中 local_factor 的层级一致。
4. coverage_role 为 main_axis 时，local_factor 必须出现在 main_combination_axes。
5. coverage_role 为 rotate_attach 时，local_factor 必须出现在 non_main_factors。
6. excluded_factors 必须写明 reason。
7. 全局因子值被裁剪时，必须使用 selected_values 记录保留取值。
```
````

- [ ] **Step 2: Commit the template**

Run:

```bash
git add pg_case_factory/skills/pg-sql-generation/references/templates/factor_catalog_mapping_template.md
git commit -m "docs: add factor catalog mapping template"
```

## Task 5: Add DATABASE Mappings to Statement References

**Files:**
- Modify: `pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/create_database.md`
- Modify: `pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/alter_database.md`
- Modify: `pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/drop_database.md`
- Test command: `python3 tools/audit_factor_catalog_mapping.py --root . skills/pg-sql-generation/references/statements/ddl/database/create_database.md skills/pg-sql-generation/references/statements/ddl/database/alter_database.md skills/pg-sql-generation/references/statements/ddl/database/drop_database.md`

- [ ] **Step 1: Insert CREATE DATABASE mapping**

In `skills/pg-sql-generation/references/statements/ddl/database/create_database.md`, inside the fenced YAML `structured_config`, insert this block after `coverage_policy` and before `rendering`:

```yaml
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
      - valid_quoted_upper
      - quoted_reserved_keyword
      - invalid_special_char_unquoted
      - max_length_63_bytes
      - over_length_64_bytes
      reason: CREATE DATABASE 需要覆盖数据库名的合法形态、引号语义、特殊字符和长度边界。
    - catalog_factor: database.options.owner
      local_factor: owner_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - omitted
      - valid_current_user
      - valid_other_role
      - nonexistent_user
      - no_set_role_privilege
      reason: OWNER 子句影响目标 owner、角色存在性和 SET ROLE 权限边界。
    - catalog_factor: database.options.template
      local_factor: template_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - omitted_default_template1
      - template0
      - custom_template
      - nonexistent_template
      - template_has_connections
      reason: TEMPLATE 子句影响复制来源、连接状态和编码 locale 兼容性。
    - catalog_factor: database.options.encoding
      local_factor: encoding_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - omitted_client_default
      - utf8
      - latin1
      - sql_ascii
      - invalid_encoding
      reason: ENCODING 是 CREATE DATABASE 的关键选项，需要覆盖有效编码、无效编码和兼容性边界。
    - catalog_factor: database.options.locale
      local_factor: locale_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - omitted
      - c_locale
      - posix_locale
      - valid_system_locale
      - nonexistent_locale
      - encoding_locale_mismatch
      reason: LOCALE、LC_COLLATE 和 LC_CTYPE 影响数据库排序和编码兼容性。
    - catalog_factor: database.options.strategy
      local_factor: strategy_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: STRATEGY 决定数据库复制策略，覆盖 WAL_LOG、FILE_COPY 和非法策略。
    - catalog_factor: database.environment.privilege_level
      local_factor: privilege_level
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - superuser
      - createdb_role
      - non_owner
      reason: CREATE DATABASE 需要 superuser 或 CREATEDB 权限。
    - catalog_factor: database.environment.template_existence
      local_factor: template_existence
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 模板数据库存在性和连接状态影响 CREATE DATABASE 成功路径。
    - catalog_factor: database.environment.encoding_locale_compatibility
      local_factor: encoding_locale_compatibility
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 编码、locale 和模板兼容性属于环境约束。
    - catalog_factor: database.environment.role_set_role_ability
      local_factor: role_set_role_ability
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 指定其他 owner 时需要验证 SET ROLE 能力。
    - catalog_factor: database.environment.tablespace_existence
      local_factor: tablespace_existence
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: TABLESPACE 子句需要验证目标表空间存在性。
    - catalog_factor: database.boundary.duplicate_name
      local_factor: duplicate_database_name
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 数据库名在集群内必须唯一，重名是关键失败路径。
    - catalog_factor: database.boundary.privilege_denied
      local_factor: privilege_denied
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 权限不足路径需要与成功路径明确区分。
    - catalog_factor: database.boundary.inside_transaction
      local_factor: inside_transaction_block
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: CREATE DATABASE 不能在事务块内执行。
    - catalog_factor: database.validation.catalog_check
      local_factor: verification_mode
      target_tier: T6
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - pg_database_presence
      - error_assertion
      reason: CREATE DATABASE 的成功和失败路径需要通过 pg_database 查询或错误断言验证。
    excluded_factors:
    - catalog_factor: database.operation.if_exists
      reason: CREATE DATABASE 官方语法没有 IF EXISTS。
    - catalog_factor: database.operation.force
      reason: CREATE DATABASE 官方语法没有 WITH FORCE。
    coverage_notes:
    - database.naming.name_shape 只做轮转挂靠，不进入主笛卡尔积。
```

- [ ] **Step 2: Insert ALTER DATABASE mapping**

In `skills/pg-sql-generation/references/statements/ddl/database/alter_database.md`, inside the fenced YAML `structured_config`, insert this block after `coverage_policy` and before `rendering`:

```yaml
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
      - valid_quoted_upper
      - quoted_reserved_keyword
      reason: ALTER DATABASE 需要覆盖目标 database 名称输入形态。
    - catalog_factor: database.naming.name_shape
      local_factor: new_name_shape
      target_tier: T3
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - valid_unquoted_lower
      - valid_quoted_upper
      - quoted_reserved_keyword
      reason: RENAME TO 分支需要覆盖新名称形态。
    - catalog_factor: database.options.allow_connections
      local_factor: with_option_type
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - true
      - false
      reason: ALTER DATABASE WITH 选项可修改 ALLOW_CONNECTIONS。
    - catalog_factor: database.options.connection_limit
      local_factor: with_option_type
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: ALTER DATABASE WITH 选项可修改 CONNECTION LIMIT。
    - catalog_factor: database.options.is_template
      local_factor: with_option_type
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: ALTER DATABASE WITH 选项可修改 IS_TEMPLATE。
    - catalog_factor: database.options.owner
      local_factor: new_owner_target
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - valid_other_role
      - nonexistent_user
      - no_set_role_privilege
      reason: OWNER TO 分支需要覆盖新 owner 和权限边界。
    - catalog_factor: database.options.tablespace
      local_factor: new_tablespace_shape
      target_tier: T3
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - valid_tablespace
      - nonexistent_tablespace
      reason: SET TABLESPACE 分支需要覆盖新表空间名称形态。
    - catalog_factor: database.options.config_parameter
      local_factor: config_parameter_type
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: ALTER DATABASE SET/RESET 分支需要覆盖普通参数和 superuser-only 参数。
    - catalog_factor: database.environment.tablespace_existence
      local_factor: tablespace_existence
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: SET TABLESPACE 需要验证表空间存在性。
    - catalog_factor: database.environment.connection_state
      local_factor: target_database_connection_state
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: RENAME 和 SET TABLESPACE 受目标数据库连接状态影响。
    - catalog_factor: database.environment.role_set_role_ability
      local_factor: role_set_role_ability
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: OWNER TO 需要验证 SET ROLE 能力。
    - catalog_factor: database.environment.privilege_level
      local_factor: role_createdb_privilege
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - createdb_role
      - non_owner
      reason: SET TABLESPACE 和部分 ALTER DATABASE 操作依赖 CREATEDB 或 owner 权限。
    - catalog_factor: database.boundary.duplicate_name
      local_factor: rename_target_conflict
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: RENAME TO 分支需要覆盖目标名称冲突。
    - catalog_factor: database.boundary.privilege_denied
      local_factor: privilege_denied
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 非 owner 或权限不足路径需要单独覆盖。
    - catalog_factor: database.boundary.inside_transaction
      local_factor: set_tablespace_in_transaction
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: SET TABLESPACE 不能在事务块内执行。
    - catalog_factor: database.validation.catalog_check
      local_factor: verification_mode
      target_tier: T6
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - pg_database_presence
      - error_assertion
      reason: ALTER DATABASE 需要通过 pg_database、pg_db_role_setting 或错误断言验证。
    excluded_factors:
    - catalog_factor: database.options.template
      reason: ALTER DATABASE 官方语法不修改 TEMPLATE。
    - catalog_factor: database.options.encoding
      reason: ALTER DATABASE 官方语法不修改 ENCODING。
    - catalog_factor: database.operation.if_exists
      reason: ALTER DATABASE 官方语法没有 IF EXISTS。
    - catalog_factor: database.operation.force
      reason: ALTER DATABASE 官方语法没有 WITH FORCE。
    coverage_notes:
    - 多个全局 database.options 因子映射到 with_option_type，因为现有 reference 已把 WITH 选项收敛为一个局部因子。
```

- [ ] **Step 3: Insert DROP DATABASE mapping**

In `skills/pg-sql-generation/references/statements/ddl/database/drop_database.md`, inside the fenced YAML `structured_config`, insert this block after `coverage_policy` and before `rendering`:

```yaml
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
      - valid_quoted_upper
      - quoted_reserved_keyword
      reason: DROP DATABASE 需要覆盖目标 database 名称输入形态。
    - catalog_factor: database.operation.if_exists
      local_factor: if_exists_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: IF EXISTS 改变不存在对象时的行为。
    - catalog_factor: database.operation.force
      local_factor: force_option
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: WITH FORCE 改变有连接时的删除行为。
    - catalog_factor: database.environment.privilege_level
      local_factor: privilege_level
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - superuser
      - database_owner
      - non_owner
      reason: DROP DATABASE 需要 owner 或 superuser 权限。
    - catalog_factor: database.environment.connection_state
      local_factor: connection_state
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: DROP DATABASE 受目标数据库连接状态影响。
    - catalog_factor: database.boundary.active_connections
      local_factor: active_connections
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: WITH FORCE 和普通 DROP 的核心差异是活动连接处理。
    - catalog_factor: database.boundary.privilege_denied
      local_factor: privilege_denied
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 非 owner 删除数据库属于关键失败路径。
    - catalog_factor: database.boundary.inside_transaction
      local_factor: inside_transaction_block
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: DROP DATABASE 不能在事务块内执行。
    - catalog_factor: database.validation.catalog_check
      local_factor: verification_mode
      target_tier: T6
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - pg_database_absence
      - error_assertion
      reason: DROP DATABASE 需要验证 pg_database 中对象不存在或断言错误路径。
    excluded_factors:
    - catalog_factor: database.options.owner
      reason: DROP DATABASE 不设置 OWNER。
    - catalog_factor: database.options.template
      reason: DROP DATABASE 不使用 TEMPLATE。
    - catalog_factor: database.options.encoding
      reason: DROP DATABASE 不使用 ENCODING。
    - catalog_factor: database.options.locale
      reason: DROP DATABASE 不使用 LOCALE。
    - catalog_factor: database.options.strategy
      reason: DROP DATABASE 不使用 STRATEGY。
    - catalog_factor: database.options.allow_connections
      reason: DROP DATABASE 不修改 ALLOW_CONNECTIONS。
    - catalog_factor: database.options.connection_limit
      reason: DROP DATABASE 不修改 CONNECTION LIMIT。
    - catalog_factor: database.options.is_template
      reason: DROP DATABASE 不修改 IS_TEMPLATE。
    coverage_notes:
    - DROP DATABASE 的核心新增覆盖来自 operation.if_exists、operation.force 和 connection_state。
```

- [ ] **Step 4: Run the mapping audit on the three database references**

Run:

```bash
python3 tools/audit_factor_catalog_mapping.py --root . \
  skills/pg-sql-generation/references/statements/ddl/database/create_database.md \
  skills/pg-sql-generation/references/statements/ddl/database/alter_database.md \
  skills/pg-sql-generation/references/statements/ddl/database/drop_database.md
```

Expected: pass with nonzero `mapped` and `excluded` counts.

- [ ] **Step 5: Run the unit tests**

Run:

```bash
python3 -m unittest tests/test_factor_catalog_mapping_audit.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit the database mappings**

Run:

```bash
git add \
  pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/create_database.md \
  pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/alter_database.md \
  pg_case_factory/skills/pg-sql-generation/references/statements/ddl/database/drop_database.md
git commit -m "feat: map database statements to factor catalog"
```

## Task 6: Add Migration Status and Project Structure Notes

**Files:**
- Create: `pg_case_factory/docs/pg16_factor_catalog_mapping_status.md`
- Modify: `pg_case_factory/PROJECT_STRUCTURE.md`

- [ ] **Step 1: Create the status report**

Create `docs/pg16_factor_catalog_mapping_status.md` with this content:

````markdown
# PG16 Factor Catalog Mapping Status

Updated: 2026-06-26

## Summary

The factor integration model is in its first implementation slice. The global catalog exists, the mapping template exists, and the database object domain has end-to-end mappings for `CREATE DATABASE`, `ALTER DATABASE`, and `DROP DATABASE`.

## Object Domain Status

| Object domain | Catalog status | Statement mapping status | Notes |
| --- | --- | --- | --- |
| database | Detailed | CREATE / ALTER / DROP mapped | First end-to-end example |
| domain | Seeded | Not mapped | Next first-batch target |
| schema | Seeded | Not mapped | Next first-batch target |
| role_user_group | Seeded | Not mapped | Next first-batch target |
| tablespace | Seeded | Not mapped | Next first-batch target |
| extension | Seeded | Not mapped | Next first-batch target |
| sequence | Seeded | Not mapped | Next first-batch target |

## DATABASE Mapping Results

| Statement | Mapping result | Main policy |
| --- | --- | --- |
| `create_database` | Uses database naming, owner, template, encoding, locale, strategy, privilege, environment, boundary, and validation factors | Existing main axes stay `statement_branch`, `object_state`, `expected_status` |
| `alter_database` | Uses database naming, WITH options, owner target, tablespace, config parameter, environment, boundary, and validation factors | Existing main axes stay `statement_branch`, `object_state`, `expected_status` |
| `drop_database` | Uses database naming, IF EXISTS, FORCE, privilege, connection state, active connection, boundary, and validation factors | Existing main axes stay `statement_branch`, `object_state`, `expected_status` |

## Current Audit Command

```bash
python3 tools/audit_factor_catalog_mapping.py --root .
```

## Next Migration Targets

1. Expand `domain` catalog values from `1.txt`.
2. Map `create_domain`, `alter_domain`, and `drop_domain`.
3. Expand and map `schema`.
4. Expand and map `role_user_group`.
5. Expand and map `tablespace`, `extension`, and `sequence`.
````

- [ ] **Step 2: Update project structure**

In `PROJECT_STRUCTURE.md`, under `references/common/` responsibilities, add this bullet after `factor_policy.md`:

```markdown
- `pg16_factor_catalog.md`：PG16 全局对象域因子目录，供 statement reference 通过 `factor_catalog_mapping` 引用
```

In the `references/templates/` responsibilities, add this bullet:

```markdown
- `references/templates/factor_catalog_mapping_template.md`：statement reference 引用全局因子目录的映射模板
```

Under section `4. src/pg_case_factory/`, add a short note after the engine file list:

```markdown
因子目录映射审计脚本位于 `tools/audit_factor_catalog_mapping.py`。它只做静态一致性检查，不参与 SQL 渲染主路径。
```

- [ ] **Step 3: Run the audit and tests**

Run:

```bash
python3 tools/audit_factor_catalog_mapping.py --root .
python3 -m unittest tests/test_factor_catalog_mapping_audit.py -v
```

Expected: audit passes and unit tests pass.

- [ ] **Step 4: Commit docs**

Run:

```bash
git add \
  pg_case_factory/docs/pg16_factor_catalog_mapping_status.md \
  pg_case_factory/PROJECT_STRUCTURE.md
git commit -m "docs: record factor catalog mapping status"
```

## Task 7: Final Verification and Push

**Files:**
- Verify all files changed in Tasks 1-6.

- [ ] **Step 1: Check Git status**

Run:

```bash
git status --short --branch
```

Expected: either clean, or only pre-existing unrelated user changes remain. In this thread, `pg_case_factory/1.txt` may still appear as a pre-existing unstaged change and must not be committed unless the user asks.

- [ ] **Step 2: Run full verification commands**

Run from `pg_case_factory`:

```bash
python3 -m unittest tests/test_factor_catalog_mapping_audit.py -v
python3 tools/audit_factor_catalog_mapping.py --root .
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from pg_case_factory.skill_loader import load_skill

paths = [
    Path("skills/pg-sql-generation/references/statements/ddl/database/create_database.md"),
    Path("skills/pg-sql-generation/references/statements/ddl/database/alter_database.md"),
    Path("skills/pg-sql-generation/references/statements/ddl/database/drop_database.md"),
]
for path in paths:
    loaded = load_skill(path)
    assert loaded["statement"]["key"]
    assert "factor_catalog_mapping" in loaded["structured_config"]
print("PASS database statement references load with factor catalog mappings")
PY
```

Expected:

```text
OK
PASS factor catalog mapping audit: mapped=<nonzero> excluded=<nonzero>
PASS database statement references load with factor catalog mappings
```

- [ ] **Step 3: Review the final diff**

Run:

```bash
git diff --stat HEAD
git log --oneline --decorate -5
```

Expected: recent commits correspond to this plan's tasks.

- [ ] **Step 4: Push**

Run from repository root `/Users/yuyu/PyCharmMiscProject`:

```bash
git push origin main
```

Expected: push succeeds.

## Self-Review

Spec coverage:

- Global catalog: Task 3.
- Mapping template: Task 4.
- Database end-to-end example: Task 5.
- Audit status report: Task 6.
- Optional static audit tool: Tasks 1 and 2.
- Existing engine unchanged: all tasks avoid `src/pg_case_factory`.
- Verification that existing statement loader still works: Task 7.

Completeness scan:

- The plan contains no unresolved blanks.
- All code-producing steps include exact file content or exact YAML blocks.

Type and field consistency:

- Audit script API used by tests is `audit_paths(catalog_path, statement_paths)`.
- Mapping fields match the design: `source_catalog`, `object_domain`, `imported_factors`, `promoted_factors`, `excluded_factors`, `coverage_notes`.
- Coverage roles match the design: `main_axis`, `representative_or_main`, `representative`, `rotate_attach`, `audit_only`.
- Value policies match the design: `reuse_catalog_values`, `statement_specific_subset`, `statement_specific_override`.
