# 技能：lifecycle_policy

## 作用

定义 SQL 生命周期计划的公共口径。主流程写 `artifacts/test_plans/<task_slug>.tsv` 时必须使用本规则，statement reference 只补充分支特有的前置条件、验证方式和清理动作。

## 生命周期原则

- 每一行 TSV 只描述一个可归因的生命周期场景。
- 生命周期必须闭环：前置清理、对象准备、目标语句、验证、结束清理。
- 成功路径与失败路径必须拆开，不得把多个独立失败原因混在同一个场景中。
- 对 table-backed statement，如果目标语句涉及列、表达式、索引、约束或表数据，应显式说明基表类型、列类型覆盖方式和数据准备方式。
- 对 schema、role、tablespace、extension、server、publication、subscription 等环境依赖，必须在 `operation_chain` 或 `notes` 中明确准备与清理责任。
- 不允许把解析阶段、模块名、内部实现细节当作生命周期动作。

## 常见 operation_chain 口径

- create-like table-backed：`create_table>target_statement>verify_target>drop_table`
- create-like 且存在独立 drop statement：增加一条 `create_table>target_statement>verify_target>drop_target>drop_table`
- alter-like：`prepare_object>target_statement>verify_change>cleanup_object`
- drop-like：`prepare_object>target_statement>verify_absence>cleanup_residue`
- maintenance-like：`prepare_object>target_statement>verify_effect>cleanup_object`

```yaml
structured_config:
  skill_name: lifecycle_policy
  statement: common
  lifecycle:
    require_closed_loop: true
    one_row_one_scenario: true
    split_success_and_failure: true
    forbid_internal_pipeline_steps: true
```
