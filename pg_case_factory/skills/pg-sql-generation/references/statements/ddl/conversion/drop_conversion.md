# 技能：DROP CONVERSION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropconversion.html

```sql
DROP CONVERSION [ IF EXISTS ] name [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- 必须拥有该 conversion 才能删除它
- CASCADE 和 RESTRICT 关键字实际上没有效果，因为不存在依赖于 conversion 的对象
- 不在 SQL 标准中（SQL 标准使用 DROP TRANSLATION）
- IF EXISTS：不抛出错误而是发出通知

## 语句作用

官方说明：DROP CONVERSION — remove a conversion

该 reference 关注字符集编码转换对象的删除。DROP CONVERSION 语法简单（单一顶层形式），核心维度是对象存在性、IF EXISTS 容错行为和权限要求。CASCADE/RESTRICT 对该对象类型无实际语义效果但仍需覆盖语法层面。该语句不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP CONVERSION 单一顶层形式）
- object_state：目标 conversion 对象状态（exists / not_exists）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句形态（省略 / 指定 IF EXISTS）
- cascade_restrict：CASCADE / RESTRICT 选择（省略 / CASCADE / RESTRICT）
- privilege_level：执行权限（superuser / conversion_owner / non_owner）

### T3：对象名与输入形态因子
- conversion_name_shape：conversion 名称形态

### T4：依赖对象与环境因子
- schema_existence：schema 存在性（schema 存在 / schema 不存在）
- conversion_ownership：ownership 状态（owner 删除 / 非 owner 删除）

### T5：异常与边界因子
- conversion_not_exist：目标 conversion 不存在且无 IF EXISTS
- privilege_denied：非 owner 尝试删除
- nonexistent_name：指定不存在的 conversion 名称
- cascade_semantics_null：CASCADE/RESTRICT 对 conversion 无实际依赖效果

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP CONVERSION 单一语法分支的所有可选子句组合。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖（object_state x expected_status）。
- T2 因子按规模控制策略参与组合。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 conversion 存在时的成功删除路径，以及目标 conversion 不存在时的失败路径。
- IF EXISTS 必须覆盖不存在对象的代表性 no-op 路径。
- CASCADE 和 RESTRICT 虽对 conversion 无实际依赖效果，仍需在语法层面覆盖。
- 必须覆盖 owner 成功删除和 non_owner 失败删除的路径。
- 每个样本必须包含明确的前置对象准备、目标 DROP CONVERSION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- if_exists_clause 挂靠到对象不存在场景的样本上。
- cascade_restrict 在代表性样本上轮转注入（虽然无实际语义效果）。
- privilege_level 挂靠到 owner 成功和 non_owner 失败的样本上。
- T3 因子挂靠到代表性成功样本和失败样本上轮转注入。
- T5 因子按失败原因单独挂靠。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 形态、CASCADE/RESTRICT 语法覆盖。
- 低优先级命名形态和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: conversion
  skill_name: drop_conversion
  official_source: https://www.postgresql.org/docs/16/sql-dropconversion.html
  statement:
    key: drop_conversion
    name: DROP CONVERSION
    aliases:
    - drop_conversion
    - DROP CONVERSION
    purpose: DROP CONVERSION — remove a conversion
  syntax_templates:
  - "DROP CONVERSION [ IF EXISTS ] name [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_exists_clause
    - cascade_restrict
    - privilege_level
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - conversion_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - schema_existence
    - conversion_ownership
  - tier: T5
    name: 异常与边界因子
    factors:
    - conversion_not_exist
    - privilege_denied
    - nonexistent_name
    - cascade_semantics_null
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification_mode
    - cleanup_mode
  factors:
    statement_branch:
      label: 官方语法分支
      importance: important
      values:
      - key: branch_drop_conversion
        label: DROP CONVERSION [ IF EXISTS ] name [ CASCADE | RESTRICT ]
    object_state:
      label: 目标 conversion 对象状态
      importance: important
      values:
      - exists
      - not_exists
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句形态
      importance: non_important
      values:
      - omitted
      - specified_if_exists
    cascade_restrict:
      label: CASCADE / RESTRICT 选择
      importance: non_important
      values:
      - omitted
      - cascade
      - restrict
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - conversion_owner
      - non_owner
    conversion_name_shape:
      label: conversion 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified
      - nonexistent_name
    schema_existence:
      label: schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    conversion_ownership:
      label: ownership 状态
      importance: non_important
      values:
      - is_owner
      - is_not_owner
    conversion_not_exist:
      label: 目标 conversion 不存在
      importance: non_important
      values:
      - conversion_exists
      - conversion_not_exists
    privilege_denied:
      label: 非 owner 尝试删除
      importance: non_important
      values:
      - owner_success
      - non_owner_failure
      - superuser_success
    nonexistent_name:
      label: 指定不存在的名称
      importance: non_important
      values:
      - valid_name
      - nonexistent_conversion_name
    cascade_semantics_null:
      label: CASCADE/RESTRICT 对 conversion 无实际依赖效果
      importance: non_important
      values:
      - cascade_no_effect
      - restrict_no_effect
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_conversion
      - error_assertion
      - notice_assertion_if_exists
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_conversion
      - drop_schema_cascade
  defaults:
    expected_status: success
    object_state: exists
    if_exists_clause: omitted
    cascade_restrict: omitted
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - privilege_level
    - conversion_name_shape
    - schema_existence
    - conversion_ownership
    - conversion_not_exist
    - privilege_denied
    - nonexistent_name
    - cascade_semantics_null
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 100
    preserve_axes_first:
    - statement_branch
  rendering:
    statement_template: "DROP CONVERSION {if_exists} {conversion_name} {cascade_restrict}"
    verification_query_template: "SELECT count(*) FROM pg_conversion WHERE conname\
      \ = '{conversion_name}'"
    factor_value_bindings: {}
```
