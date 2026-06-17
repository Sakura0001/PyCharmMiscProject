# 技能：DROP STATISTICS

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropstatistics.html

```sql
DROP STATISTICS [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

**重要约束：**
- DROP STATISTICS 不涉及表/列/索引组合的直接选择。
- CASCADE / RESTRICT 对 statistics 对象本身通常无实际影响（statistics 通常不被其他对象依赖），但 RESTRICT 是默认行为。
- 需要 table owner 权限或 superuser 权限。

## 语句作用

官方说明：DROP STATISTICS — remove extended statistics

该 reference 关注扩展统计删除语句的 IF EXISTS 行为、CASCADE/RESTRICT 行为、权限边界和成功/失败路径。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP STATISTICS / DROP STATISTICS IF EXISTS / CASCADE / RESTRICT）
- statistics_existence：目标 statistics 存在状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句行为
- cascade_restrict_clause：CASCADE / RESTRICT 子句行为
- privilege_context：权限上下文
- multi_target：多目标删除行为

### T3：对象名与输入形态因子
- statistics_name_shape：statistics 名标识符形态

### T4：依赖对象与环境因子
- **DROP STATISTICS 不涉及表/列/索引组合。**
- executor_privilege：执行者权限上下文

### T5：异常与边界因子
- nonexistent_statistics：statistics 不存在
- privilege_insufficient：权限不足

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 statistics 存在/不存在、IF EXISTS、CASCADE/RESTRICT 等核心状态。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 statistics 存在时的成功删除路径、statistics 不存在时的失败路径。
- IF EXISTS 时，必须覆盖不存在 statistics 的代表性 no-op 路径。
- 每个样本必须包含明确的前置表准备、目标 DROP STATISTICS 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - statistics 存在/不存在全覆盖
  - IF EXISTS no-op 覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - CASCADE / RESTRICT 代表性覆盖
  - 多目标删除代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: statistics
  skill_name: drop_statistics
  official_source: https://www.postgresql.org/docs/16/sql-dropstatistics.html
  statement:
    key: drop_statistics
    name: DROP STATISTICS
    aliases:
    - drop_statistics
    - DROP STATISTICS
    purpose: DROP STATISTICS — remove extended statistics
  syntax_templates:
  - "DROP STATISTICS [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - statistics_existence
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_exists_clause
    - cascade_restrict_clause
    - privilege_context
    - multi_target
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - statistics_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_statistics
    - privilege_insufficient
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
      - key: branch_drop_statistics
        label: DROP STATISTICS name
      - key: branch_drop_statistics_if_exists
        label: DROP STATISTICS IF EXISTS name
      - key: branch_drop_statistics_cascade
        label: DROP STATISTICS name CASCADE
      - key: branch_drop_statistics_restrict
        label: DROP STATISTICS name RESTRICT
    statistics_existence:
      label: 目标 statistics 存在状态
      importance: important
      values:
      - statistics_exists
      - statistics_not_exists
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句
      importance: important
      values:
      - without_if_exists
      - with_if_exists
    cascade_restrict_clause:
      label: CASCADE / RESTRICT 子句
      importance: important
      values:
      - no_clause_default_restrict
      - cascade
      - restrict
    privilege_context:
      label: 权限上下文
      importance: important
      values:
      - superuser
      - table_owner
      - non_owner_no_privilege
    multi_target:
      label: 多目标删除行为
      importance: non_important
      values:
      - single_target
      - multi_target_all_exist
      - multi_target_some_not_exist
    statistics_name_shape:
      label: statistics 名标识符形态
      importance: non_important
      values:
      - simple_name
      - schema_qualified_name
      - quoted_name
      - reserved_word_name
      - non_existing_name
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - table_owner
      - non_owner_no_privilege
    nonexistent_statistics:
      label: statistics 不存在
      importance: non_important
      values:
      - statistics_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_table_owner_dropping_statistics
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_statistic_ext_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_statistics
  defaults:
    expected_status: success
    cascade_restrict_clause: no_clause_default_restrict
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - statistics_existence
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict_clause
    - privilege_context
    - multi_target
    - statistics_name_shape
    - executor_privilege
    - nonexistent_statistics
    - privilege_insufficient
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - statistics_existence
  rendering:
    statement_template: "DROP STATISTICS [ IF EXISTS ] {name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT stxname FROM pg_statistic_ext WHERE stxname = '{name}'"
    factor_value_bindings:
      if_exists_clause:
        without_if_exists: ""
        with_if_exists: "IF EXISTS"
      cascade_restrict_clause:
        no_clause_default_restrict: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
