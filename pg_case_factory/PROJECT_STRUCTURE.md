# 项目结构说明

当前 `pg_case_factory` 已经收敛成“标准 Codex skill + statement reference + 最小通用引擎”。

## 1. 根目录结构

```text
pg_case_factory/
├─ README.md
├─ PROJECT_STRUCTURE.md
├─ pyproject.toml
├─ artifacts/
├─ skills/
└─ src/
```

## 2. 基础对象模板

```text
skills/pg-sql-generation/assets/objects/
└─ tables/
   └─ normal_table/
      ├─ table_01.sql
      └─ table_02.sql
```

对象模板属于 skill 的 bundled assets，只描述基础对象，不描述 statement 因子。这样独立发布 `pg-sql-generation` skill 时，agent 仍能直接读取基表模板并生成 SQL。

## 3. `skills/`

```text
skills/
└─ pg-sql-generation/
   ├─ SKILL.md
   ├─ agents/
   │  └─ openai.yaml
   ├─ references/
   │  ├─ mainflow/
   │  ├─ common/
   │  ├─ statements/
   │  └─ templates/
   └─ assets/
      ├─ templates/
      └─ objects/
         └─ tables/
            └─ normal_table/
```

### `skills/pg-sql-generation/SKILL.md`

标准 Codex skill 入口，包含 frontmatter 和轻量导航。具体细节按需读取 `references/`。

### `references/mainflow/`

主流程 reference。

职责：

- 指导 agent 从自然语言里识别对象和 statement
- 推导生命周期
- 先写计划 TSV
- 审计生命周期计划
- 再写动态 Python 批量脚本
- 再批量生成 SQL

当前主流程入口：

- `generate_sql_from_request.md`：总入口
- `audit_lifecycle_plan.md`：计划审计
- `write_sql_program.md`：生成批量 SQL 程序
- `create_statement_reference.md`：创建或补齐 statement reference

`references/mainflow/` 不放公共 SQL 输出风格，统一引用 `references/common/output_script_style.md`。

### `references/common/`

公共规则 reference。

职责：

- `output_script_style.md`：SQL 文件头、前置清理、对象准备、目标语句、验证、结束清理
- `factor_policy.md`：重要因子笛卡尔积，非重要因子轮转挂靠
- `pg16_factor_catalog.md`：PG16 全局对象域因子目录，供 statement reference 通过 `factor_catalog_mapping` 引用
- `pg16_type_catalog.md`：PG16 类型目录，供 statement reference 选择列类型、样例值、前置 setup 与索引能力
- `lifecycle_policy.md`：生命周期 TSV 的动作口径
- `validation_policy.md`：成功/失败验证与幂等清理
- `naming_rules.md`：对象命名规则

### `references/templates/` 和 `assets/templates/`

模板文件。

职责：

- `references/templates/statement_reference_template.md`：新增或补齐 statement reference 的标准骨架
- `references/templates/factor_catalog_mapping_template.md`：statement reference 引用全局因子目录的映射模板
- `assets/templates/lifecycle_plan_template.tsv`：生命周期计划 TSV 表头和示例行
- `assets/objects/tables/normal_table/*.sql`：随 skill 发布的基础对象 SQL 模板

### `references/statements/<category>/<domain>/`

statement reference。

职责：

- 定义 statement category，例如 `ddl`、`dml`、`dcl`、`tcl`、`session`、`cursor`、`prepared`、`utility`
- 定义 statement key/name/aliases
- 定义因子
- 定义默认值
- 定义覆盖策略
- 定义渲染模板

statement reference 不应写死完整生命周期。

## 4. `tools/`

因子目录映射审计脚本位于 `tools/audit_factor_catalog_mapping.py`。它只做静态一致性检查，不参与 SQL 渲染主路径。

## 5. `src/pg_case_factory/`

```text
src/pg_case_factory/
├─ __init__.py
├─ artifact_store.py
├─ discovery.py
├─ engine.py
├─ renderer.py
└─ skill_loader.py
```

这是当前项目的最小常驻引擎。

### [artifact_store.py](src/pg_case_factory/artifact_store.py)

负责清空并重建 `artifacts/`，以及统一写文本、JSON、YAML。

### [skill_loader.py](src/pg_case_factory/skill_loader.py)

读取 reference 文件中的结构化 YAML，并统一成通用字典结构。

### [discovery.py](src/pg_case_factory/discovery.py)

负责搜索：

- `skills/pg-sql-generation/assets/objects/**/*.sql`
- `skills/pg-sql-generation/references/statements/**/*.md`

并基于别名和名称给出候选匹配结果。

### [renderer.py](src/pg_case_factory/renderer.py)

负责：

- 按 statement reference 生成因子绑定
- 渲染对象模板
- 渲染 statement SQL
- 把多个 SQL 块组合成统一模板脚本

### [engine.py](src/pg_case_factory/engine.py)

对外暴露统一 API，供动态生成脚本复用。

## 6. 动态脚本位置

真正批量生成 SQL 的 Python 脚本不应常驻在 `src/`，而应动态写到：

- `artifacts/generated_programs/`

这些脚本再调用 `pg_case_factory` 引擎完成批量生成。

## 7. 已移除的常驻 Python

以下 demo 专用 Python 已经移除：

- `workflow.py`
- `request_parser.py`
- `task_normalizer.py`
- `abstract_case_generator.py`
- `evaluator.py`
- `runtime_defaults.py`
- `models.py`
- `cli.py`
- `__main__.py`
- `sql_renderer.py`

这样仓库里的常驻 Python 只保留通用能力，不保留语句专用流程。
