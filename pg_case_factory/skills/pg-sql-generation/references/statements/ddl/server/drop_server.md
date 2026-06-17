# 技能：DROP SERVER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropserver.html

```sql
DROP SERVER [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

**重要约束：**
- DROP SERVER 需要 superuser 权限或 server 的 owner 角色。
- CASCADE 会自动删除依赖此 server 的 user mapping；RESTRICT（默认）在有 user mapping 依赖时失败。
- DROP SERVER 不涉及表/列/索引组合。

## 语句作用

官方说明：DROP SERVER — remove a foreign server descriptor

该 reference 关注外部服务器删除语句的 IF EXISTS 行为、CASCADE/RESTRICT 行为、权限边界和成功/失败路径。DROP SERVER 需要 superuser 权限，是 FDW 依赖对象。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP SERVER / DROP SERVER IF EXISTS / CASCADE / RESTRICT）
- server_existence：目标 server 存在状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句行为
- cascade_restrict_clause：CASCADE / RESTRICT 子句行为
- privilege_context：权限上下文
- multi_target：多目标删除行为

### T3：对象名与输入形态因子
- server_name_shape：server 名标识符形态

### T4：依赖对象与环境因子
- **DROP SERVER 不涉及表/列/索引组合。**
- executor_privilege：执行者权限上下文
- user_mapping_dependency：user mapping 依赖状态

### T5：异常与边界因子
- nonexistent_server：server 不存在
- privilege_insufficient：权限不足
- dependent_user_mapping：依赖 user mapping 冲突

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 server 存在/不存在、IF EXISTS、CASCADE/RESTRICT 等核心状态。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 server 存在时的成功删除路径、server 不存在时的失败路径。
- IF EXISTS 时，必须覆盖不存在 server 的代表性 no-op 路径。
- CASCADE / RESTRICT 时，必须覆盖存在 user mapping 依赖下的 RESTRICT 失败与 CASCADE 成功路径。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 每个样本必须包含明确的前置 FDW 准备、目标 DROP SERVER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或 user mapping 依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - server 存在/不存在全覆盖
  - CASCADE / RESTRICT 全覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - IF EXISTS 行为代表性覆盖
  - user mapping 依赖代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: server
  skill_name: drop_server
  official_source: https://www.postgresql.org/docs/16/sql-dropserver.html
  statement:
    key: drop_server
    name: DROP SERVER
    aliases:
    - drop_server
    - DROP SERVER
    purpose: DROP SERVER — remove a foreign server descriptor
  syntax_templates:
  - "DROP SERVER [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - server_existence
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
    - server_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - user_mapping_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_server
    - privilege_insufficient
    - dependent_user_mapping
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
      - key: branch_drop_server
        label: DROP SERVER name
      - key: branch_drop_server_if_exists
        label: DROP SERVER IF EXISTS name
      - key: branch_drop_server_cascade
        label: DROP SERVER name CASCADE
      - key: branch_drop_server_restrict
        label: DROP SERVER name RESTRICT
    server_existence:
      label: 目标 server 存在状态
      importance: important
      values:
      - server_exists
      - server_not_exists
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
      - owner_of_server
      - non_owner_no_privilege
    multi_target:
      label: 多目标删除行为
      importance: non_important
      values:
      - single_target
      - multi_target_all_exist
      - multi_target_some_not_exist
    server_name_shape:
      label: server 名标识符形态
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
    user_mapping_dependency:
      label: user mapping 依赖状态
      importance: non_important
      values:
      - no_user_mapping_dependency
      - has_user_mapping_dependency
    nonexistent_server:
      label: server 不存在
      importance: non_important
      values:
      - server_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_owner_dropping_server
    dependent_user_mapping:
      label: 依赖 user mapping 冲突
      importance: non_important
      values:
      - restrict_with_user_mapping_fails
      - cascade_with_user_mapping_succeeds
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_foreign_server_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_server_cascade
      - drop_user_mapping_then_drop_server
  defaults:
    expected_status: success
    cascade_restrict_clause: no_clause_default_restrict
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - server_existence
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict_clause
    - privilege_context
    - multi_target
    - server_name_shape
    - executor_privilege
    - user_mapping_dependency
    - nonexistent_server
    - privilege_insufficient
    - dependent_user_mapping
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - server_existence
  rendering:
    statement_template: "DROP SERVER [ IF EXISTS ] {name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT srvname FROM pg_foreign_server WHERE srvname = '{name}'"
    factor_value_bindings:
      if_exists_clause:
        without_if_exists: ""
        with_if_exists: "IF EXISTS"
      cascade_restrict_clause:
        no_clause_default_restrict: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
