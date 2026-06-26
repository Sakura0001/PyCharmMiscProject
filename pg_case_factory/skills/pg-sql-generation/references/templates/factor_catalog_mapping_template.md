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
