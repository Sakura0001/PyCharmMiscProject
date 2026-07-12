# 模板：PG18.4 Factor Catalog Mapping

## 使用方式

把 `factor_catalog_mapping` 复制到 statement reference 的 `structured_config`。用它记录 PG18.4 全局因子与 statement 局部因子的关系；SQL 渲染和 test-point 拆分仍由 coverage plan 决定。

## 映射片段

```yaml
factor_catalog_mapping:
  source_catalog: references/common/pg18_factor_catalog.md
  compatibility_target: postgresql-18.4
  object_domain: example_domain
  imported_factors:
    - catalog_factor: example_domain.naming.name_shape
      local_factor: example_name_shape
      target_tier: T3
      coverage_role: separate_complete_point
      value_policy: reuse_all_catalog_values
      reason: 当前 statement 需要完整覆盖对象名称输入形态。
  promoted_factors:
    - catalog_factor: example_domain.options.primary_option
      local_factor: primary_option_clause
      from_default_tier: T4
      target_tier: T2
      coverage_role: main_axis
      value_policy: reuse_all_catalog_values
      reason: 该选项属于 PostgreSQL 18.4 官方关键语义分支。
  excluded_factors:
    - catalog_factor: example_domain.options.unused_option
      disposition: justified_na
      reason: 当前 statement 的 PostgreSQL 18.4 官方语法不包含该选项。
  coverage_notes:
    - 每个适用 catalog value 都进入 complete axis；不使用代表值或抽样。
```

## 字段约束

- `catalog_factor` 必须存在于 PG18.4 factor inventory，且 compatibility audit 状态可用。
- `local_factor` 必须存在于当前 statement 的 `factors`。
- `target_tier` 必须与 `factor_layers` 一致。
- `coverage_role` 使用 `main_axis` 或 `separate_complete_point`；两者都要求完整 inventory。
- `value_policy` 默认 `reuse_all_catalog_values`。确实不适用的值不得静默裁剪，应保留在 axis 中并归为 `justified_na + reason`。
- `excluded_factors` 必须说明整个 factor 为何不适用；不要用 excluded 规避某些取值的测试。
- 每个 axis 声明 `coverage_mode: complete` 和非空 `inventory_source`。

## 审计清单

```text
1. 所有映射均以 PostgreSQL 18.4 compatibility profile 为目标。
2. catalog_factor、local_factor 和 tier 引用均有效。
3. 所有适用 catalog values 都能在 coverage obligations 中找到。
4. justified_na 与 expected_failure 均有具体 reason。
5. required = success + expected_failure + justified_na，且 missing = 0。
6. 不存在 representative、sampling、pairwise 或 rotate-attach 捷径。
```
