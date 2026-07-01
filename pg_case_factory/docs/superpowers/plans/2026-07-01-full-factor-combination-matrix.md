# Full Factor Combination Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 183 个 PostgreSQL statement reference 的因子体系升级为“常规覆盖矩阵优先、审计通过后允许扩展推导”的组合矩阵体系。

**Architecture:** 保留现有 `references/statements/**/*.md` 作为因子定义源，新增 `references/combinations/**/*.yaml` 作为 statement 级组合矩阵源。新增公共 schema、类型/对象目录、矩阵审计工具和迁移状态文件，先让工具强制覆盖契约，再按 domain 分批补齐正式矩阵。

**Tech Stack:** Python 3.9+、PyYAML、现有 `pg_case_factory.skill_loader`、Markdown/YAML reference 文件、Git main branch。

---

## Scope Check

当前仓库有 183 个 statement reference：

```text
cursor 4
dcl 2
ddl 136
dml 7
prepared 3
session 10
tcl 13
utility 8
```

这是跨 183 个 statement 的长期迁移，不应一次性由一个 agent 批量修改所有文件。执行时必须分阶段：

1. 先建立通用组合矩阵 schema、审计工具和上下文保全机制。
2. 再把 `CREATE INDEX` 从模板提升为正式矩阵，作为可审计样板。
3. 再按 domain 分批迁移，每批只改一个小范围，提交一次。
4. 每批迁移都必须通过矩阵审计，不允许只靠人工阅读。

## Non-Negotiable Context Rules

- 只在 `main` 分支开发；用户已明确要求“只在主分支下开发”。
- 每次改动前运行 `git status --short --branch`。
- 不提交用户已有未提交改动；当前已知 `1.txt` 可能保持未提交状态。
- 子 agent 不能依赖当前会话历史。每个子 agent 只接收：
  - 本计划的任务全文。
  - 相关 statement reference 路径。
  - 相关组合矩阵 schema 或模板路径。
  - 当前迁移状态文件路径。
  - 明确的验收命令。
- 每个任务完成后必须提交并 push，除非只是在本轮规划阶段。
- 常规覆盖矩阵审计通过前禁止矩阵外推导。
- 常规覆盖矩阵审计通过后允许扩展推导，但扩展组合必须写入 `derived_extension_combinations.yaml`，并且不能计入 required coverage。

## File Structure

### New Files

- `skills/pg-sql-generation/references/combinations/README.md`
  说明组合矩阵目录职责、文件命名和 AI/runner 的使用边界。

- `skills/pg-sql-generation/references/combinations/_shared/statement_combination_matrix_schema.yaml`
  通用组合矩阵 schema。所有 statement 的正式矩阵必须符合该 schema。

- `skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml`
  公共对象覆盖 inventory，包含 relation kind、table kind、column type set、object kind 分组。statement 矩阵引用它，但必须在自身文件中显式声明适用范围。

- `skills/pg-sql-generation/references/common/pg16_type_catalog.md`
  PG16 可作为表列声明的数据类型目录。包含类型 key、类别、声明 SQL、样例值、边界值、依赖准备、索引能力和不适用说明。

- `skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml`
  `CREATE INDEX` 正式组合矩阵，来源于现有模板，但作为真实可审计矩阵使用。

- `tools/audit_combination_matrix.py`
  审计所有组合矩阵和 statement reference 的一致性。

- `tests/test_combination_matrix_audit.py`
  审计工具单元测试。

- `docs/pg16_combination_matrix_migration_status.md`
  全量迁移状态文件，记录 183 个 statement 的矩阵状态、覆盖策略和审计结果。

- `docs/superpowers/context/2026-07-01-combination-matrix-context.md`
  子 agent 上下文包。每次批量任务前更新，确保上下文不依赖聊天历史。

### Modified Files

- `skills/pg-sql-generation/SKILL.md`
  增加组合矩阵导航。

- `skills/pg-sql-generation/references/mainflow/write_sql_program.md`
  从“让 AI 写生成程序”调整为“优先读取组合矩阵和固定 runner 契约”。

- `skills/pg-sql-generation/references/mainflow/generate_sql_from_request.md`
  增加 `combination_matrix_path` 与 `execution_spec` 生成要求。

- `skills/pg-sql-generation/references/templates/create_index_combination_matrix_template.yaml`
  保留为模板，不作为正式矩阵。

- `PROJECT_STRUCTURE.md`
  增加 `references/combinations/`、`pg16_type_catalog.md` 和矩阵审计工具说明。

- `README.md`
  更新架构描述，说明组合矩阵层的职责。

---

## Task 1: Add Shared Combination Matrix Schema

**Files:**
- Create: `skills/pg-sql-generation/references/combinations/README.md`
- Create: `skills/pg-sql-generation/references/combinations/_shared/statement_combination_matrix_schema.yaml`
- Create: `skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml`

- [ ] **Step 1: Check repository state**

Run:

```bash
git status --short --branch
```

Expected: branch is `main`; unrelated `1.txt` may be modified and must remain unstaged.

- [ ] **Step 2: Create combinations README**

Create `skills/pg-sql-generation/references/combinations/README.md` with this content:

```markdown
# Statement Combination Matrices

This directory contains machine-readable statement combination matrices.

Statement references under `references/statements/**/*.md` define factors,
factor values, tiers, rendering hints, and coverage policy. Combination
matrices under this directory define which factor bindings are required
baseline SQL combinations.

Rules:

- Required baseline coverage must pass before AI or runner derived extensions
  are generated.
- Derived extensions are allowed after baseline audit passes, but must be
  written to `artifacts/intermediates/<task_slug>/derived_extension_combinations.yaml`.
- Derived extensions must not satisfy required factor, relation, table, or
  column-type coverage.
- Every expected failure must have a stable reason.
- Every matrix must explicitly declare whether relation, table, and column
  type coverage are required.
```

- [ ] **Step 3: Create shared schema**

Create `skills/pg-sql-generation/references/combinations/_shared/statement_combination_matrix_schema.yaml` with top-level required keys:

```yaml
schema_version: 1
kind: statement_combination_matrix_schema
required_top_level_keys:
  - schema_version
  - kind
  - statement
  - execution_contract
  - coverage_scope
  - factor_contract
  - dynamic_inputs
  - combination_groups
  - audit_rules
execution_contract_required_keys:
  - required_matrix_is_baseline
  - no_inference_before_required_coverage_passes
  - runner_must_complete_required_matrix_first
  - allow_post_coverage_extension_inference
  - extension_combinations_must_be_marked
  - extension_combinations_must_record_derivation
  - extension_combinations_must_not_replace_required_coverage
  - success_and_failure_both_allowed
  - all_success_and_failure_reasons_must_be_declared
coverage_scope_required_keys:
  - target_object_coverage
  - target_relation_coverage
  - table_coverage
  - column_type_coverage
combination_group_required_keys:
  - id
  - title
  - lifecycle_role
  - expected_status_policy
  - factors
  - expansion
  - compatibility
  - sql_shape
  - verification
  - cleanup
allowed_expected_status_policies:
  - fixed
  - per_object_kind
  - per_relation_kind
  - per_table_kind
  - per_column_type
  - per_method
  - per_method_and_column_type
  - per_factor_binding
  - per_lifecycle_context
allowed_coverage_modes:
  - not_applicable
  - explicit
  - exhaustive
  - representative
  - conditional
```

- [ ] **Step 4: Create coverage inventory**

Create `skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml` with this minimum content:

```yaml
schema_version: 1
kind: coverage_inventory
relation_kinds:
  indexable_relation_kinds:
    - regular_table
    - unlogged_table
    - temporary_table
    - partitioned_table_parent
    - partitioned_table_leaf
    - inherited_parent_table
    - inherited_child_table
    - materialized_view
  non_indexable_relation_kinds:
    - plain_view
    - foreign_table
    - sequence
table_kinds:
  table_backed_statement_table_kinds:
    - regular_table
    - unlogged_table
    - temporary_table
    - partitioned_table_parent
    - partitioned_table_leaf
    - inherited_parent_table
    - inherited_child_table
column_type_sets:
  all_pg16_column_types:
    source: references/common/pg16_type_catalog.md
object_coverage_modes:
  not_applicable:
    description: Statement does not operate on this object class.
  explicit:
    description: Statement must list exact object kinds.
  exhaustive:
    description: Statement must cover every object kind in the referenced inventory set.
  representative:
    description: Statement covers representative objects and records why exhaustive coverage is not required.
```

- [ ] **Step 5: Commit**

Run:

```bash
git add \
  skills/pg-sql-generation/references/combinations/README.md \
  skills/pg-sql-generation/references/combinations/_shared/statement_combination_matrix_schema.yaml \
  skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml
git diff --cached --check
git commit -m "docs: add shared combination matrix schema"
git push origin main
```

Expected: commit only these three new files.

---

## Task 2: Add PG16 Type Catalog

**Files:**
- Create: `skills/pg-sql-generation/references/common/pg16_type_catalog.md`
- Modify: `PROJECT_STRUCTURE.md`
- Test later through `tools/audit_combination_matrix.py`

- [ ] **Step 1: Create type catalog skeleton**

Create `skills/pg-sql-generation/references/common/pg16_type_catalog.md` with a fenced YAML block:

```yaml
structured_config:
  kind: type_catalog
  skill_name: pg16_type_catalog
  version: pg16
  type_sets:
    all_pg16_column_types:
      description: Every PostgreSQL 16 type that can be declared as a table column.
      include_pseudo_types: false
  type_categories:
    numeric: {}
    monetary: {}
    character: {}
    binary: {}
    datetime: {}
    boolean: {}
    enum: {}
    geometric: {}
    network: {}
    bit_string: {}
    text_search: {}
    uuid: {}
    xml: {}
    json: {}
    array: {}
    range: {}
    domain: {}
    composite: {}
    object_identifier: {}
    pg_lsn: {}
    name: {}
  types: {}
```

- [ ] **Step 2: Fill required type entries**

Populate `structured_config.types` with at least these keys, preserving stable snake_case names:

```text
smallint, integer, bigint, smallserial, serial, bigserial,
numeric, decimal, real, double_precision, money,
character_varying, character, bpchar, text,
bytea,
timestamp, timestamp_with_time_zone, date, time, time_with_time_zone, interval,
boolean,
enum_type,
point, line, lseg, box, path, polygon, circle,
cidr, inet, macaddr, macaddr8,
bit, bit_varying,
tsvector, tsquery,
uuid,
xml,
json, jsonb,
integer_array, text_array, varchar_array, numeric_array, timestamp_array, jsonb_array,
int4range, int8range, numrange, tsrange, tstzrange, daterange,
domain_type,
composite_type,
oid, regclass, regtype, xid, xid8, cid, tid,
pg_lsn,
name
```

Each entry must contain:

```yaml
type_key: integer
type_category: numeric
declaration_sql: INTEGER
sample_values:
  success:
    - "1"
  boundary: []
  failure: []
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
```

- [ ] **Step 3: Record unsupported pseudo-types**

Add a `pseudo_types` section:

```yaml
pseudo_types:
  allowed_as_table_columns: false
  values:
    - any
    - anyelement
    - anyarray
    - anynonarray
    - anyenum
    - anyrange
    - anymultirange
    - cstring
    - internal
    - language_handler
    - fdw_handler
    - table_am_handler
    - index_am_handler
    - tsm_handler
    - record
    - trigger
    - event_trigger
    - pg_ddl_command
    - void
    - unknown
```

- [ ] **Step 4: Update project structure**

Add `pg16_type_catalog.md` under the `references/common/` description in `PROJECT_STRUCTURE.md`.

- [ ] **Step 5: Commit**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import re, yaml
path = Path("skills/pg-sql-generation/references/common/pg16_type_catalog.md")
match = re.search(r"```yaml\s*(.*?)```", path.read_text(encoding="utf-8"), re.S)
assert match
data = yaml.safe_load(match.group(1))
cfg = data["structured_config"]
assert cfg["kind"] == "type_catalog"
assert "all_pg16_column_types" in cfg["type_sets"]
assert len(cfg["types"]) >= 55
assert cfg["pseudo_types"]["allowed_as_table_columns"] is False
print("PASS pg16 type catalog structure")
PY
git add skills/pg-sql-generation/references/common/pg16_type_catalog.md PROJECT_STRUCTURE.md
git diff --cached --check
git commit -m "docs: add PG16 type catalog"
git push origin main
```

---

## Task 3: Add Combination Matrix Audit Tool

**Files:**
- Create: `tools/audit_combination_matrix.py`
- Create: `tests/test_combination_matrix_audit.py`
- Modify: `PROJECT_STRUCTURE.md`

- [ ] **Step 1: Write failing tests**

Create `tests/test_combination_matrix_audit.py` with this shape. The first run must fail because the audit module does not exist yet:

```python
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
    spec.loader.exec_module(module)
    return module


class CombinationMatrixAuditTest(unittest.TestCase):
    def write_file(self, root: Path, relative_path: str, content: str) -> Path:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
        return path

    def test_valid_matrix_passes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_file(root, "skills/pg-sql-generation/references/statements/ddl/example/example_statement.md", """
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
            """)
            self.write_file(root, "skills/pg-sql-generation/references/combinations/ddl/example/example_statement.yaml", """
            schema_version: 1
            kind: statement_combination_matrix
            statement:
              key: example_statement
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
            coverage_scope:
              target_object_coverage: {required: false, coverage_mode: not_applicable, decision_reason: example}
              target_relation_coverage: {required: false, coverage_mode: not_applicable, decision_reason: example}
              table_coverage: {required: false, coverage_mode: not_applicable, decision_reason: example}
              column_type_coverage: {required: false, coverage_mode: not_applicable, decision_reason: example}
            factor_contract:
              factors:
                mode:
                  required_values: [basic]
                expected_status:
                  required_values: [success, failure]
            dynamic_inputs: {}
            combination_groups:
              - id: basic_success
                title: Basic success
                lifecycle_role: target_statement
                expected_status_policy: fixed
                factors: {mode: basic, expected_status: success}
                expansion: {}
                compatibility: {success_when: ["mode == basic"], failure_when: []}
                sql_shape: {template: EXAMPLE}
                verification: {required: false, mode: none, sql: null}
                cleanup: {required: true, steps: [{sql: "-- cleanup"}]}
            audit_rules: []
            """)
            result = module.audit_root(root)
            self.assertTrue(result.passed, result.errors)

    def test_unknown_factor_fails(self):
        module = load_module()
        result = module.AuditResult()
        result.errors.append("unknown factor: missing_factor")
        self.assertFalse(result.passed)

    def test_unknown_factor_value_fails(self):
        module = load_module()
        result = module.AuditResult()
        result.errors.append("unknown factor value: mode=missing")
        self.assertFalse(result.passed)

    def test_failure_without_reason_fails(self):
        module = load_module()
        result = module.AuditResult()
        result.errors.append("failure group must declare reason")
        self.assertFalse(result.passed)

    def test_required_column_coverage_requires_type_catalog(self):
        module = load_module()
        result = module.AuditResult()
        result.errors.append("column_type_coverage requires pg16_type_catalog")
        self.assertFalse(result.passed)

    def test_extension_policy_cannot_replace_required_coverage(self):
        module = load_module()
        result = module.AuditResult()
        result.errors.append("extension coverage cannot satisfy required coverage")
        self.assertFalse(result.passed)

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
```

Use temporary fixture files under `tempfile.TemporaryDirectory()` so tests do not modify real references.

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
python3 -m unittest tests/test_combination_matrix_audit.py -v
```

Expected: FAIL because `tools/audit_combination_matrix.py` does not exist.

- [ ] **Step 3: Implement audit tool**

Create `tools/audit_combination_matrix.py` with these responsibilities:

```text
1. Load statement reference YAML from references/statements/**/*.md.
2. Load combination matrix YAML from references/combinations/**/*.yaml, excluding _shared.
3. Check every matrix factor exists in the statement reference.
4. Check every matrix factor value exists in the statement reference.
5. Check required factor values are covered by baseline combination_groups.
6. Check expected failure paths have a failure reason.
7. Check column_type_coverage.required=true references pg16_type_catalog.
8. Check extension policy exists when allow_post_coverage_extension_inference=true.
9. Ensure derived extension groups are not counted as required coverage.
10. Print PASS/FAIL summary and return nonzero on errors.
```

Expose a Python API:

```python
def audit_root(root: Path) -> AuditResult:
    return audit_matrices(root, matrix_paths=None)

def audit_matrix(root: Path, matrix_path: Path) -> AuditResult:
    return audit_matrices(root, matrix_paths=[matrix_path])
```

The CLI must support:

```bash
python3 tools/audit_combination_matrix.py --root .
python3 tools/audit_combination_matrix.py --root . skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml
```

- [ ] **Step 4: Verify tests pass**

Run:

```bash
python3 -m unittest tests/test_combination_matrix_audit.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add tools/audit_combination_matrix.py tests/test_combination_matrix_audit.py PROJECT_STRUCTURE.md
git diff --cached --check
git commit -m "feat: add combination matrix audit"
git push origin main
```

---

## Task 4: Promote CREATE INDEX Template to Formal Matrix

**Files:**
- Create: `skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml`
- Modify: `docs/pg16_combination_matrix_migration_status.md`
- Test: `tools/audit_combination_matrix.py`

- [ ] **Step 1: Create formal matrix from template**

Copy the current logic from:

```text
skills/pg-sql-generation/references/templates/create_index_combination_matrix_template.yaml
```

into:

```text
skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml
```

Change:

```yaml
kind: statement_combination_matrix_template
```

to:

```yaml
kind: statement_combination_matrix
```

- [ ] **Step 2: Adjust template-only wording**

Ensure the formal matrix does not claim to be a template. Keep all baseline groups and post-coverage extension policy.

- [ ] **Step 3: Run audit**

Run:

```bash
python3 tools/audit_combination_matrix.py --root . skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml
```

Expected: PASS, or explicit errors that must be fixed before commit.

- [ ] **Step 4: Commit**

Run:

```bash
git add skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml
git diff --cached --check
git commit -m "docs: add create index combination matrix"
git push origin main
```

---

## Task 5: Add Migration Status and Context Bundle

**Files:**
- Create: `docs/pg16_combination_matrix_migration_status.md`
- Create: `docs/superpowers/context/2026-07-01-combination-matrix-context.md`

- [ ] **Step 1: Create migration status**

Create `docs/pg16_combination_matrix_migration_status.md` with a table containing all 183 statement paths and these columns:

```text
statement_key
category
domain
statement_reference
matrix_path
status
coverage_scope
last_audit
notes
```

Initial statuses:

```text
create_index: formal_matrix_ready
all others: pending
```

- [ ] **Step 2: Create context bundle**

Create `docs/superpowers/context/2026-07-01-combination-matrix-context.md` with:

```markdown
# Combination Matrix Migration Context

## Current Rules

- Statement reference defines factors.
- Combination matrix defines baseline SQL combinations.
- Baseline audit must pass before extension inference.
- Extensions are allowed after baseline audit and must be marked.
- Extensions never count as required coverage.

## Required Files For Subagents

- This context file.
- The implementation plan.
- The target statement reference file.
- The shared matrix schema.
- The audit tool.
- The migration status file.

## Known Local State

`1.txt` may be modified by the user. Do not stage, commit, or rewrite it unless explicitly requested.
```

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/pg16_combination_matrix_migration_status.md docs/superpowers/context/2026-07-01-combination-matrix-context.md
git diff --cached --check
git commit -m "docs: add combination matrix migration status"
git push origin main
```

---

## Task 6: Update Mainflow to Prefer Combination Matrices

**Files:**
- Modify: `skills/pg-sql-generation/SKILL.md`
- Modify: `skills/pg-sql-generation/references/mainflow/generate_sql_from_request.md`
- Modify: `skills/pg-sql-generation/references/mainflow/write_sql_program.md`
- Modify: `README.md`
- Modify: `PROJECT_STRUCTURE.md`

- [ ] **Step 1: Update skill navigation**

Add a navigation bullet to `SKILL.md`:

```markdown
- For statement factor combination matrices, read `references/combinations/README.md`
  and then the matching `references/combinations/<category>/<domain>/<statement_key>.yaml`.
```

- [ ] **Step 2: Update generate flow**

In `generate_sql_from_request.md`, add a step after statement reference discovery:

```text
If a matching combination matrix exists, include its path in the lifecycle plan notes and execution spec. The matrix is the baseline SQL-combination source. Do not ask AI to infer baseline combinations outside the matrix.
```

- [ ] **Step 3: Update write flow**

In `write_sql_program.md`, replace the current “create batch SQL program from TSV” wording with:

```text
When a combination matrix exists, the generator must consume the matrix before using free-form reasoning. Required baseline coverage comes from combination_groups. After the matrix audit reports required_coverage_passed, AI or runner may emit derived extension combinations into artifacts/intermediates/<task_slug>/derived_extension_combinations.yaml.
```

- [ ] **Step 4: Commit**

Run:

```bash
git add skills/pg-sql-generation/SKILL.md \
  skills/pg-sql-generation/references/mainflow/generate_sql_from_request.md \
  skills/pg-sql-generation/references/mainflow/write_sql_program.md \
  README.md PROJECT_STRUCTURE.md
git diff --cached --check
git commit -m "docs: route SQL generation through combination matrices"
git push origin main
```

---

## Task 7: Batch A Matrices For Table, Type, Index, View, Materialized View

**Files:**
- Create matrices under:
  - `skills/pg-sql-generation/references/combinations/ddl/table/*.yaml`
  - `skills/pg-sql-generation/references/combinations/ddl/type/*.yaml`
  - `skills/pg-sql-generation/references/combinations/ddl/index/*.yaml`
  - `skills/pg-sql-generation/references/combinations/ddl/view/*.yaml`
  - `skills/pg-sql-generation/references/combinations/ddl/materialized_view/*.yaml`
- Modify: `docs/pg16_combination_matrix_migration_status.md`

Target statement count:

```text
ddl/table: 7
ddl/type: 3
ddl/index: 4
ddl/view: 3
ddl/materialized_view: 4
total: 21
```

- [ ] **Step 1: Dispatch one subagent per domain, not per statement**

Subagent instruction must include:

```text
Read the shared schema, context bundle, and all statement references in your assigned domain. Create baseline combination matrices for the assigned domain only. Do not edit other domains. Run combination matrix audit for your files. Update migration status rows for your files only. Do not touch 1.txt.
```

- [ ] **Step 2: Required coverage rule**

For table/type/index/view/materialized_view statements:

```text
If the statement creates, alters, reads, transforms, indexes, stores, or validates table columns, column_type_coverage must be explicit. If exhaustive coverage is not applicable, the matrix must say why and use representative or conditional coverage with concrete values.
```

- [ ] **Step 3: Audit**

Run:

```bash
python3 tools/audit_combination_matrix.py --root .
```

Expected: PASS for all matrices in this batch.

- [ ] **Step 4: Commit**

Run:

```bash
git add skills/pg-sql-generation/references/combinations/ddl/table \
  skills/pg-sql-generation/references/combinations/ddl/type \
  skills/pg-sql-generation/references/combinations/ddl/index \
  skills/pg-sql-generation/references/combinations/ddl/view \
  skills/pg-sql-generation/references/combinations/ddl/materialized_view \
  docs/pg16_combination_matrix_migration_status.md
git diff --cached --check
git commit -m "docs: add table-backed combination matrices"
git push origin main
```

---

## Task 8: Batch B Matrices For DML And Query Statements

**Files:**
- Create matrices under:
  - `skills/pg-sql-generation/references/combinations/dml/**/*.yaml`
  - `skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml`
- Modify: `docs/pg16_combination_matrix_migration_status.md`

Target statements:

```text
dml/query/select.md
dml/query/values.md
dml/routine/call.md
dml/table/delete.md
dml/table/insert.md
dml/table/merge.md
dml/table/update.md
utility/data_transfer/copy.md
```

- [ ] **Step 1: Use DML-specific coverage**

DML matrices must explicitly decide:

```text
table_coverage
column_type_coverage
index_interaction_coverage
constraint_interaction_coverage
trigger_interaction_coverage
transaction_interaction_coverage
```

- [ ] **Step 2: Audit and commit**

Run:

```bash
python3 tools/audit_combination_matrix.py --root .
git add skills/pg-sql-generation/references/combinations/dml \
  skills/pg-sql-generation/references/combinations/utility/data_transfer \
  docs/pg16_combination_matrix_migration_status.md
git diff --cached --check
git commit -m "docs: add dml combination matrices"
git push origin main
```

---

## Task 9: Batch C Matrices For Object-Level DDL

**Files:**
- Create matrices under `skills/pg-sql-generation/references/combinations/ddl/**/*.yaml`
- Exclude domains completed in Task 7.
- Modify: `docs/pg16_combination_matrix_migration_status.md`

Object-level DDL includes:

```text
database, schema, role, user, group, tablespace, extension, sequence,
domain, function, procedure, aggregate, operator, operator_class,
operator_family, cast, collation, conversion, language, server,
foreign_data_wrapper, foreign_server-related statements, publication,
subscription, policy, trigger, rule, text_search_*, transform,
event_trigger, access_method, statistics, security_label, system
```

- [ ] **Step 1: Subagent batching**

Split into batches of 8 to 12 statement files. Each subagent gets one batch and must update only those matrix files and status rows.

- [ ] **Step 2: Coverage decision**

For each matrix:

```text
table_coverage.required must be true only when the statement directly operates on tables, columns, predicates, policies, triggers, statistics, or dependencies that require table objects.
column_type_coverage.required must be true only when column types affect SQL validity, semantics, or verification.
When false, decision_reason must be concrete and statement-specific.
```

- [ ] **Step 3: Audit and commit per sub-batch**

Run:

```bash
python3 tools/audit_combination_matrix.py --root .
git diff --cached --check
git commit -m "docs: add <domain> combination matrices"
git push origin main
```

Use a domain-specific commit message, for example:

```bash
git commit -m "docs: add database and schema combination matrices"
```

---

## Task 10: Batch D Matrices For TCL, Session, Cursor, Prepared, DCL, Utility

**Files:**
- Create matrices under:
  - `skills/pg-sql-generation/references/combinations/tcl/**/*.yaml`
  - `skills/pg-sql-generation/references/combinations/session/**/*.yaml`
  - `skills/pg-sql-generation/references/combinations/cursor/**/*.yaml`
  - `skills/pg-sql-generation/references/combinations/prepared/**/*.yaml`
  - `skills/pg-sql-generation/references/combinations/dcl/**/*.yaml`
  - `skills/pg-sql-generation/references/combinations/utility/**/*.yaml`
- Modify: `docs/pg16_combination_matrix_migration_status.md`

- [ ] **Step 1: Treat non-DDL statements carefully**

These statements often do not need exhaustive table or column coverage. Matrices must still explicitly state:

```text
target_object_coverage.required
target_relation_coverage.required
table_coverage.required
column_type_coverage.required
decision_reason
```

- [ ] **Step 2: Required extension policy**

All matrices must carry the same extension policy:

```text
Baseline first.
Extensions after baseline audit only.
Extensions are marked and do not satisfy required coverage.
```

- [ ] **Step 3: Audit and commit**

Run:

```bash
python3 tools/audit_combination_matrix.py --root .
git add skills/pg-sql-generation/references/combinations/tcl \
  skills/pg-sql-generation/references/combinations/session \
  skills/pg-sql-generation/references/combinations/cursor \
  skills/pg-sql-generation/references/combinations/prepared \
  skills/pg-sql-generation/references/combinations/dcl \
  skills/pg-sql-generation/references/combinations/utility \
  docs/pg16_combination_matrix_migration_status.md
git diff --cached --check
git commit -m "docs: add non-ddl combination matrices"
git push origin main
```

---

## Task 11: Final Whole-Repo Audit

**Files:**
- Modify: `docs/pg16_combination_matrix_migration_status.md`

- [ ] **Step 1: Run complete audits**

Run:

```bash
python3 tools/audit_factor_catalog_mapping.py --root .
python3 tools/audit_combination_matrix.py --root .
python3 -m unittest tests/test_factor_catalog_mapping_audit.py -v
python3 -m unittest tests/test_combination_matrix_audit.py -v
```

Expected:

```text
PASS factor catalog mapping audit: mapped=<nonzero> excluded=<nonzero>
PASS combination matrix audit: matrices=<expected> baseline_groups=<nonzero>
OK
OK
```

- [ ] **Step 2: Update migration status**

Mark every row in `docs/pg16_combination_matrix_migration_status.md` as one of:

```text
formal_matrix_ready
not_applicable_with_reason
blocked_with_reason
```

No row may remain `pending`.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/pg16_combination_matrix_migration_status.md
git diff --cached --check
git commit -m "docs: finalize combination matrix migration status"
git push origin main
```

---

## Subagent Execution Protocol

Use subagents only after Tasks 1 to 6 establish the schema, audit tool, type catalog, formal `CREATE INDEX` matrix, and context bundle.

For each subagent task, provide this exact context:

```text
You are working in /Users/yuyu/PyCharmMiscProject/pg_case_factory on main.
Do not create a feature branch.
Do not edit or stage 1.txt.
Read:
- docs/superpowers/plans/2026-07-01-full-factor-combination-matrix.md
- docs/superpowers/context/2026-07-01-combination-matrix-context.md
- skills/pg-sql-generation/references/combinations/_shared/statement_combination_matrix_schema.yaml
- skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml
- tools/audit_combination_matrix.py
Only edit the files assigned in your task.
Run the audit command listed in the task.
Commit and push only assigned files.
```

Review every subagent result in two passes:

1. Spec compliance: Does it satisfy this plan and assigned paths only?
2. Code/content quality: Is the YAML stable, concrete, auditable, and free of vague AI inference?

## Self-Review

- Spec coverage: The plan covers shared schema, type catalog, audit tooling, formal `CREATE INDEX` matrix, status tracking, mainflow integration, and all 183 statement references by category/domain batches.
- Placeholder scan: No task relies on unresolved placeholder wording or “do appropriate work.” Batch tasks define exact path groups, audit commands, and commit rules.
- Context preservation: The plan creates a dedicated context bundle and migration status file, and every subagent prompt must include them.
- Scope control: Full migration is split into foundation tasks and four content batches. Subagents start only after audit infrastructure exists.
- User local changes: The plan explicitly preserves `1.txt` and requires targeted `git add`.
