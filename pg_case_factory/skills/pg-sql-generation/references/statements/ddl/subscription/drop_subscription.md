# 技能：DROP SUBSCRIPTION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropsubscription.html

```sql
DROP SUBSCRIPTION [ IF EXISTS ] name [ CASCADE | RESTRICT ]
```

**重要约束：**
- DROP SUBSCRIPTION 需要 superuser 权限。
- DROP SUBSCRIPTION 不支持多目标删除（只删除单个 subscription）。
- CASCADE 会同时删除 replication slot；RESTRICT（默认）在 subscription 仍有 replication slot 时失败。
- 如果 subscription 没有 replication slot（如 create_slot = false），RESTRICT 不会失败。
- DROP SUBSCRIPTION 不涉及表/列/索引组合。

## 语句作用

官方说明：DROP SUBSCRIPTION — remove a subscription

该 reference 关注订阅删除语句的 IF EXISTS 行为、CASCADE/RESTRICT 行为、replication slot 依赖、权限边界和成功/失败路径。DROP SUBSCRIPTION 需要 superuser 权限。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP SUBSCRIPTION / DROP SUBSCRIPTION IF EXISTS / CASCADE / RESTRICT）
- subscription_existence：目标 subscription 存在状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句行为
- cascade_restrict_clause：CASCADE / RESTRICT 子句行为
- privilege_context：权限上下文
- replication_slot_state：replication slot 状态

### T3：对象名与输入形态因子
- subscription_name_shape：subscription 名标识符形态

### T4：依赖对象与环境因子
- **DROP SUBSCRIPTION 不涉及表/列/索引组合。它依赖 replication slot。**
- executor_privilege：执行者权限上下文（superuser 必须）
- replication_slot_dependency：replication slot 依赖状态

### T5：异常与边界因子
- nonexistent_subscription：subscription 不存在
- privilege_insufficient：权限不足（非 superuser）
- replication_slot_conflict：replication slot 冲突（RESTRICT 下失败）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 subscription 存在/不存在、IF EXISTS、CASCADE/RESTRICT 等核心状态。
- 覆盖 replication slot 有/无依赖状态。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 subscription 存在时的成功删除路径、subscription 不存在时的失败路径。
- IF EXISTS 时，必须覆盖不存在 subscription 的代表性 no-op 路径。
- CASCADE / RESTRICT 时，必须覆盖有 replication slot 依赖下的 RESTRICT 失败与 CASCADE 成功路径。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- DROP SUBSCRIPTION 只删除单个 subscription，不支持多目标删除语法。
- 每个样本必须包含明确的前置准备、目标 DROP SUBSCRIPTION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或 replication slot 依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - subscription 存在/不存在全覆盖
  - IF EXISTS no-op 覆盖
  - CASCADE / RESTRICT 全覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - replication slot 依赖代表性覆盖
  - 无 slot 的 subscription 删除代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: subscription
  skill_name: drop_subscription
  official_source: https://www.postgresql.org/docs/16/sql-dropsubscription.html
  statement:
    key: drop_subscription
    name: DROP SUBSCRIPTION
    aliases:
    - drop_subscription
    - DROP SUBSCRIPTION
    purpose: DROP SUBSCRIPTION — remove a subscription
  syntax_templates:
  - "DROP SUBSCRIPTION [ IF EXISTS ] name [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - subscription_existence
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_exists_clause
    - cascade_restrict_clause
    - privilege_context
    - replication_slot_state
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - subscription_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - replication_slot_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_subscription
    - privilege_insufficient
    - replication_slot_conflict
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
      - key: branch_drop_subscription
        label: DROP SUBSCRIPTION name
      - key: branch_drop_subscription_if_exists
        label: DROP SUBSCRIPTION IF EXISTS name
      - key: branch_drop_subscription_cascade
        label: DROP SUBSCRIPTION name CASCADE
      - key: branch_drop_subscription_restrict
        label: DROP SUBSCRIPTION name RESTRICT
    subscription_existence:
      label: 目标 subscription 存在状态
      importance: important
      values:
      - subscription_exists
      - subscription_not_exists
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
      - non_superuser_no_privilege
    replication_slot_state:
      label: replication slot 状态
      importance: non_important
      values:
      - has_replication_slot
      - no_replication_slot
    subscription_name_shape:
      label: subscription 名标识符形态
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
      - non_superuser
    replication_slot_dependency:
      label: replication slot 依赖状态
      importance: non_important
      values:
      - slot_exists
      - slot_not_exists
      - slot_on_remote_only
    nonexistent_subscription:
      label: subscription 不存在
      importance: non_important
      values:
      - subscription_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_dropping_subscription
    replication_slot_conflict:
      label: replication slot 冲突
      importance: non_important
      values:
      - restrict_with_slot_fails
      - cascade_with_slot_succeeds
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_subscription_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_subscription_cascade
  defaults:
    expected_status: success
    cascade_restrict_clause: no_clause_default_restrict
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - subscription_existence
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict_clause
    - privilege_context
    - replication_slot_state
    - subscription_name_shape
    - executor_privilege
    - replication_slot_dependency
    - nonexistent_subscription
    - privilege_insufficient
    - replication_slot_conflict
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - subscription_existence
  rendering:
    statement_template: "DROP SUBSCRIPTION [ IF EXISTS ] {name} [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT subname FROM pg_subscription WHERE subname = '{name}'"
    factor_value_bindings:
      if_exists_clause:
        without_if_exists: ""
        with_if_exists: "IF EXISTS"
      cascade_restrict_clause:
        no_clause_default_restrict: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
