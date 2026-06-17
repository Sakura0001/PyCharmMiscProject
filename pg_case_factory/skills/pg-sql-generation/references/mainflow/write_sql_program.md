# 技能：Write SQL Program

## 作用

根据生命周期计划 TSV、对象模板、statement reference 和公共规则，创建批量 SQL 生成程序，并由该程序输出完整 SQL 测试脚本集合。

本 skill 约束生成程序的职责和 SQL 输出质量；具体 statement 因子以对应 `references/statements/<category>/<domain>/<statement>.md` 为准。

## 输入

- `artifacts/test_plans/<task_slug>.tsv`
- TSV 中引用的 `base_object_path`
- TSV 中引用的 `statement_reference_path`
- TSV 中引用的 `common_rule_paths`
- 必要时读取 `references/common/output_script_style.md`
- 必要时读取 `references/common/factor_policy.md`
- 必要时读取 `references/common/validation_policy.md`
- 必要时读取 `references/common/naming_rules.md`

## 生成规则

- 对 TSV 中每一行生命周期场景，生成可以批量展开该场景的程序逻辑。
- 生成程序应放到 `artifacts/generated_programs/`。
- SQL 文件应放到 `artifacts/generated_sql/<task_slug>/`。
- 中间清单、manifest 或统计摘要应放到 `artifacts/intermediates/` 或 `artifacts/evaluations/`。
- 生成程序必须读取相关 statement reference，遵循其中的语法范围、因子分级、覆盖策略、生成约束、挂靠规则和规模控制规则。
- 若 statement 涉及列类型，应覆盖对象模板中的所有相关列类型；如果某些列类型对某 method 或语法分支不合法，应保留为可归因失败路径，而不是静默跳过。
- 每个 SQL 文件只判断一件事情；若需要在 40 个列上创建索引并验证，则生成 40 个独立 SQL 文件，而不是把所有判断塞进一个 SQL 文件。
- 重要因子采用完整笛卡尔积；非重要因子按 `factor_policy.md` 轮转挂靠。
- 如果生成数量超过 100 万，应重新审视重要因子和语句分支，优先保留 T1 覆盖，再裁剪附属因子。
- 生成的 SQL 必须符合 `output_script_style.md`、`validation_policy.md` 和 `naming_rules.md`。

## 输出要求

- SQL 必须是完整测试脚本，不是裸语句。
- 每个 SQL 文件必须包含文件头、前置清理、对象准备、目标语句、验证、结束清理。
- 成功路径与失败路径必须可归因。
- 生成摘要必须说明 SQL 数量、成功/失败数量、覆盖的对象模板、覆盖的关键因子和输出目录。

```yaml
structured_config:
  kind: mainflow
  skill_name: write_sql_program
  mainflow_role: generate_program
  inputs:
    - artifacts/test_plans/
    - assets/objects/**/*.sql
    - references/statements/**/*.md
  outputs:
    generated_programs: artifacts/generated_programs/
    generated_sql: artifacts/generated_sql/
    intermediates: artifacts/intermediates/
    evaluations: artifacts/evaluations/
  common_rules:
    - references/common/output_script_style.md
    - references/common/factor_policy.md
    - references/common/validation_policy.md
    - references/common/naming_rules.md
```
