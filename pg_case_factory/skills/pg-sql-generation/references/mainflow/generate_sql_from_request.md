# 技能：Generate SQL From Request

## 作用

将自然语言形式的 PostgreSQL SQL 测试请求，基于 PostgreSQL 16.4、本 skill 中的 statement reference 和基础对象模板，转换为生命周期计划 TSV；随后交给计划审计流程和 SQL 程序生成流程。

这个主流程 skill 只定义 agent 工作方式，不定义具体 statement 因子。

## 固定输入来源

- 基础对象模板：`assets/objects/**/*.sql`
- statement reference：`references/statements/**/*.md`
- 公共规则：
  - `references/common/output_script_style.md`
  - `references/common/factor_policy.md`
  - `references/common/lifecycle_policy.md`
  - `references/common/validation_policy.md`
  - `references/common/naming_rules.md`
- 计划审计：`references/mainflow/audit_lifecycle_plan.md`
- 生成程序：`references/mainflow/write_sql_program.md`

## 主流程规则

- 除必要路径和必要代码片段外，文字部分使用中文。
- 从用户输入中识别目标基础对象和目标 statement。
- 搜索 `assets/objects/**/*.sql` 发现基础对象；若基础对象不存在或候选不唯一，请用户二次确认。
- 搜索 `references/statements/**/*.md` 发现 statement reference。
- 优先匹配 statement 的别名、名称和 key；不得硬编码对象名或 statement 名。
- 严格按以下步骤执行，前一步未完成时不得进入后一步：
  1. 结合用户自然语言、对象模板和 statement reference 设计生命周期。
  2. 写计划 TSV 到 `artifacts/test_plans/`。
  3. 读取 `references/mainflow/audit_lifecycle_plan.md` 审计计划，并将审计结果写到 `artifacts/evaluations/`。
  4. 若审计发现缺失、冗余、歧义或错误映射，主 agent 必须先修订 TSV，再继续生成。
  5. 将 TSV、相关 statement reference、对象模板和公共规则交给 `references/mainflow/write_sql_program.md` 生成批量 SQL 程序。
  6. 运行生成程序，批量生成 SQL 到 `artifacts/generated_sql/`。

## 产物约束

- 每次运行前清空 `artifacts/`。
- 只允许保留五类目录：
  - `artifacts/generated_programs/`
  - `artifacts/generated_sql/`
  - `artifacts/test_plans/`
  - `artifacts/evaluations/`
  - `artifacts/intermediates/`

## TSV 文件约束

- 路径：`artifacts/test_plans/<task_slug>.tsv`
- `<task_slug>` = `<base_object_key>-<statement_key>`，全部小写。
- 表头必须精确为：

```text
case_id	dbms	base_object_key	base_object_path	statement_key	statement_reference_path	operation_chain	common_rule_paths	notes
```

- 每一个生命周期场景写一行。
- 每个生命周期应该是一类用例，而不是一个用例，例如create index的生命周期设计为 
- `common_rule_paths` 使用分号分隔，优先写入 `references/common/` 下的公共规则相对路径。
- `operation_chain` 只描述生命周期动作，不写解析阶段、agent 名、模块名或流水线内部概念。
- `notes` 必须细化到后续生成程序可以展开用例：使用哪个对象模板、覆盖哪些语句因子、是否覆盖所有列类型、预期成功或失败、验证方式、清理方式。

```yaml
structured_config:
  kind: mainflow
  skill_name: generate_sql_from_request
  mainflow:
    inputs:
      object_glob: assets/objects/**/*.sql
      reference_glob: references/statements/**/*.md
    exclude_reference_dirs: []
    outputs:
      test_plans: artifacts/test_plans/
      evaluations: artifacts/evaluations/
      generated_programs: artifacts/generated_programs/
      generated_sql: artifacts/generated_sql/
      intermediates: artifacts/intermediates/
    downstream_skills:
      audit_lifecycle_plan: references/mainflow/audit_lifecycle_plan.md
      write_sql_program: references/mainflow/write_sql_program.md
    common_rules:
      - references/common/output_script_style.md
      - references/common/factor_policy.md
      - references/common/lifecycle_policy.md
      - references/common/validation_policy.md
      - references/common/naming_rules.md
```
