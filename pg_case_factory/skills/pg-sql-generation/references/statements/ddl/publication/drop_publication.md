# 技能：DROP PUBLICATION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droppublication.html

```sql
DROP PUBLICATION [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

**重要约束：**
- DROP PUBLICATION 需要 superuser 权限或 publication 的 owner 角色。
- CASCADE 会自动删除依赖此 publication 的 subscription；RESTRICT（默认）在有 subscription 依赖时失败。
- DROP PUBLICATION 不涉及表/列/索引组合。

## 语句作用

官方说明：DROP PUBLICATION — remove a publication

该 reference 关注发布删除语句的 IF EXISTS 行为、CASCADE/RESTRICT 行为、权限边界和成功/失败路径。DROP PUBLICATION 需要 superuser 权限。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP PUBLICATION / DROP PUBLICATION IF EXISTS / CASCADE / RESTRICT）
- publication_existence：目标 publication 存在状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句行为
- cascade_restrict_clause：CASCADE / RESTRICT 子句行为
- privilege_context：权限上下文
- multi_target：多目标删除行为

### T3：对象名与输入形态因子
- publication_name_shape：publication 名标识符形态

### T4：依赖对象与环境因子
- **DROP PUBLICATION 不涉及表/列/索引组合。**
- executor_privilege：执行者权限上下文
- subscription_dependency：subscription 依赖状态

### T5：异常与边界因子
- nonexistent_publication：publication 不存在
- privilege_insufficient：权限不足
- dependent_subscription：依赖 subscription 冲突

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 publication 存在/不存在、IF EXISTS、CASCADE/RESTRICT 等核心状态。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 publication 存在时的成功删除路径、publication 不存在时的失败路径。
- IF EXISTS 时，必须覆盖不存在 publication 的代表性 no-op 路径。
- CASCADE / RESTRICT 时，必须覆盖存在 subscription 依赖下的 RESTRICT 失败与 CASCADE 成功路径。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 每个样本必须包含明确的前置对象准备、目标 DROP PUBLICATION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或 subscription 依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - publication 存在/不存在全覆盖
  - CASCADE / RESTRICT 全覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - IF EXISTS 行为代表性覆盖
  - subscription 依赖代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: publication
  skill_name: drop_publication
  official_source: https://www.postgresql.org/docs/16/sql-droppublication.html
  statement:
    key: drop_publication
    name: DROP PUBLICATION
    aliases:
    - drop_publication
    - DROP PUBLICATION
    purpose: DROP PUBLICATION — remove a publication
  syntax_templates:
  - "DROP PUBLICATION [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - publication_existence
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
    - publication_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - subscription_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_publication
    - privilege_insufficient
    - dependent_subscription
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
      - key: branch_drop_publication
        label: DROP PUBLICATION name
      - key: branch_drop_publication_if_exists
        label: DROP PUBLICATION IF EXISTS name
      - key: branch_drop_publication_cascade
        label: DROP PUBLICATION name CASCADE
      - key: branch_drop_publication_restrict
        label: DROP PUBLICATION name RESTRICT
    publication_existence:
      label: 目标 publication 存在状态
      importance: important
      values:
      - publication_exists
      - publication_not_exists
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
      - owner_of_publication
      - non_owner_no_privilege
    multi_target:
      label: 多目标删除行为
      importance: non_important
      values:
      - single_target
      - multi_target_all_exist
      - multi_target_some_not_exist
    publication_name_shape:
      label: publication 名标识符形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - reserved_word_name
      - non_existing_name
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - owner
      - non_owner_no_privilege
    subscription_dependency:
      label: subscription 依赖状态
      importance: non_important
      values:
      - no_subscription_dependency
      - has_subscription_dependency
    nonexistent_publication:
      label: publication 不存在
      importance: non_important
      values:
      - publication_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_owner_dropping_publication
      - non_superuser_dropping_other_publication
    dependent_subscription:
      label: 依赖 subscription 冲突
      importance: non_important
      values:
      - restrict_with_subscription_fails
      - cascade_with_subscription_succeeds
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_publication_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_publication_cascade
      - drop_subscription_then_drop_publication
  defaults:
    expected_status: success
    cascade_restrict_clause: no_clause_default_restrict
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - publication_existence
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict_clause
    - privilege_context
    - multi_target
    - publication_name_shape
    - executor_privilege
    - subscription_dependency
    - nonexistent_publication
    - privilege_insufficient
    - dependent_subscription
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - publication_existence
  rendering:
    statement_template: "DROP PUBLICATION [ IF EXISTS ] {name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT pubname FROM pg_publication WHERE pubname = '{name}'"
    factor_value_bindings:
      if_exists_clause:
        without_if_exists: ""
        with_if_exists: "IF EXISTS"
      cascade_restrict_clause:
        no_clause_default_restrict: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
