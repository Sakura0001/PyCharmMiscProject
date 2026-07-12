# 因子覆盖策略

## 目标

定义 PostgreSQL 18.4 SQL 测试的公共因子展开规则。statement reference 声明因子及适用范围，coverage plan 声明完整 inventory 和 test points，本规则禁止静默抽样。

## 规则

- 为每个适用 axis 设置 `coverage_mode: complete`、非空 `inventory_source` 和完整 `values`。
- 对 test point 的全部 `core_axes` 做完整笛卡尔积。
- 不用 representative、sampling、pairwise 或轮转挂靠替代 relation/table/column type、语法分支或其他适用 inventory 值。
- 不支持或不适用的值仍保留在 axis 中，并分类为 `expected_failure` 或 `justified_na`；两者必须给出具体 reason。
- 只把与主语义独立的附属因子拆到单独 test point；拆分后仍要求其每个 inventory 值进入 obligation，不能只选一个样本。
- 每个组合只能有一个可归因 outcome；冲突 classification 视为计划错误。
- 规模过大时拆分 test points、降低并发并断点续跑，不裁剪 inventory。
- 最终证明 `required = success + expected_failure + justified_na` 且 `missing = 0`。

```yaml
structured_config:
  skill_name: factor_policy
  statement: common
  compatibility_target: postgresql-18.4
  factor_policy:
    axis_coverage_mode: complete
    core_factor_strategy: full_cross
    sampling_allowed: false
    retain_excluded_values: true
    require_reconciliation: true
```
