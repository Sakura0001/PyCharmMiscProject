# SQL 生命周期策略

## 目标

定义 PostgreSQL 18.4 test point 和 SQL case 的公共生命周期口径。计划写入 `artifacts/runs/<run-id>/plans/`，SQL 与 manifests 写入该 run 的 `cases/`。

## 规则

- 一个 test point 表达一个测试意图；一个 executable obligation 对应一个 case manifest。
- 每个 SQL case 闭环：前置清理、对象准备、目标操作、稳定验证、结束清理。
- 成功路径与 expected failure 拆开，不把多个独立失败原因混进同一 case。
- 对 table-backed statement，显式绑定完整适用的 relation/table、列类型、数据准备和事务状态。
- 对 schema、role、tablespace、extension、server、publication、subscription 等依赖，明确准备、权限、环境和清理责任。
- 只写 SQL/用户可观察行为；不要把 agent 名、模块名、解析阶段、存储日志或内部实现步骤当作生命周期动作。
- 清理必须幂等并按反向依赖顺序执行，失败路径也必须可复跑。

## 常见动作链

- create-like：`pre_cleanup>prepare_object>target_statement>verify_target>final_cleanup`
- alter-like：`pre_cleanup>prepare_object>target_statement>verify_change>final_cleanup`
- drop-like：`pre_cleanup>prepare_object>target_statement>verify_absence>final_cleanup`
- maintenance-like：`pre_cleanup>prepare_object>target_statement>verify_effect>final_cleanup`
- transaction-like：`pre_cleanup>prepare_object>begin>target_operations>commit_or_rollback>verify_visibility>final_cleanup`

```yaml
structured_config:
  skill_name: lifecycle_policy
  statement: common
  compatibility_target: postgresql-18.4
  lifecycle:
    require_closed_loop: true
    one_case_one_obligation: true
    split_success_and_failure: true
    require_idempotent_cleanup: true
```
