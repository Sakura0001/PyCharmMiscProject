# 技能：DROP OWNED

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-drop-owned.html

```sql
DROP OWNED BY { name | CURRENT_ROLE | CURRENT_USER | SESSION_USER } [, ...] [ CASCADE | RESTRICT ]
```

**重要约束：**
- DROP OWNED 删除当前数据库中指定角色拥有的所有对象，以及该角色被授予的所有权限。
- DROP OWNED 只影响当前数据库中的对象，不影响其他数据库中的对象。
- DROP OWNED 需要 superuser 权限或 CREATEROLE 权限。
- CASCADE 会自动删除依赖这些对象的其他对象；RESTRICT（默认）在有依赖对象时失败。

## 语句作用

官方说明：DROP OWNED — remove database objects owned by a database role

该 reference 关注角色拥有对象删除语句的角色形态、CASCADE/RESTRICT 行为、权限边界和成功/失败路径，不负责覆盖所有基表列类型或表级依赖对象。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP OWNED、DROP OWNED CASCADE、DROP OWNED RESTRICT）
- role_existence：目标角色存在状态
- expected_status：预期结果

### T2：重要行为因子
- cascade_restrict_clause：CASCADE / RESTRICT 子句行为
- role_shape：角色形态（具体角色名 / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- multi_role：多角色列表行为

### T3：对象名与输入形态因子
- role_name_shape：角色名标识符形态

### T4：依赖对象与环境因子
- **本语句不涉及表/列/索引组合选择。DROP OWNED 自动删除源角色拥有的所有对象。**
- executor_privilege：执行者权限上下文
- owned_objects_state：角色拥有的对象状态

### T5：异常与边界因子
- nonexistent_role：角色不存在
- privilege_insufficient：权限不足
- dependent_objects：依赖对象冲突（RESTRICT 下的失败路径）
- cross_database_limitation：跨数据库限制

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖角色存在/不存在、CASCADE/RESTRICT、有/无依赖对象等核心状态。
- CURRENT_ROLE / CURRENT_USER / SESSION_USER 等特殊角色形态按代表性覆盖。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖角色存在时的成功删除路径、角色不存在时的失败路径。
- CASCADE 和 RESTRICT 必须分别覆盖：RESTRICT 下有依赖对象时失败、CASCADE 下自动删除依赖对象成功。
- DROP OWNED 只影响当前数据库中的对象，必须在样本中标注此限制。
- 每个样本必须包含明确的前置角色准备、目标 DROP OWNED 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 需要 superuser 或 CREATEROLE 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或角色拥有对象状态的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - 角色存在/不存在全覆盖
  - CASCADE / RESTRICT 全覆盖
  - 成功/失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - CURRENT_ROLE / CURRENT_USER / SESSION_USER 特殊形态代表性覆盖
  - 多角色列表代表性覆盖
  - 依赖对象冲突代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: ownership
  skill_name: drop_owned
  official_source: https://www.postgresql.org/docs/16/sql-drop-owned.html
  statement:
    key: drop_owned
    name: DROP OWNED
    aliases:
    - drop_owned
    - DROP OWNED
    purpose: DROP OWNED — remove database objects owned by a database role
  syntax_templates:
  - "DROP OWNED BY { name | CURRENT_ROLE | CURRENT_USER | SESSION_USER } [, ...] [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - role_existence
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - cascade_restrict_clause
    - role_shape
    - multi_role
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - role_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - owned_objects_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_role
    - privilege_insufficient
    - dependent_objects
    - cross_database_limitation
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
      - key: branch_drop_owned_by
        label: DROP OWNED BY name
      - key: branch_drop_owned_by_cascade
        label: DROP OWNED BY name CASCADE
      - key: branch_drop_owned_by_restrict
        label: DROP OWNED BY name RESTRICT
    role_existence:
      label: 目标角色存在状态
      importance: important
      values:
      - role_exists
      - role_not_exists
      - role_is_current_user
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    cascade_restrict_clause:
      label: CASCADE / RESTRICT 子句
      importance: important
      values:
      - no_clause_default_restrict
      - cascade
      - restrict
    role_shape:
      label: 角色形态
      importance: non_important
      values:
      - explicit_role_name
      - current_role_keyword
      - current_user_keyword
      - session_user_keyword
    multi_role:
      label: 多角色列表行为
      importance: non_important
      values:
      - single_role
      - multiple_roles
    role_name_shape:
      label: 角色名标识符形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - reserved_word_name
      - case_sensitive_name
      - non_existing_name
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - createrole_privilege
      - normal_user_no_privilege
    owned_objects_state:
      label: 角色拥有的对象状态
      importance: non_important
      values:
      - owns_no_objects
      - owns_tables
      - owns_multiple_objects
    nonexistent_role:
      label: 角色不存在
      importance: non_important
      values:
      - role_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_dropping_other_role_objects
      - no_createrole_privilege
    dependent_objects:
      label: 依赖对象冲突
      importance: non_important
      values:
      - no_dependent_objects
      - has_dependent_objects_restrict_fails
      - has_dependent_objects_cascade_succeeds
    cross_database_limitation:
      label: 跨数据库限制
      importance: non_important
      values:
      - only_current_database_objects
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_class_catalog_query
      - pg_roles_catalog_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_owned_cascade
      - drop_role_cascade
      - reassign_owned_then_drop_role
  defaults:
    expected_status: success
    cascade_restrict_clause: no_clause_default_restrict
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - role_existence
    - expected_status
    non_main_factors:
    - cascade_restrict_clause
    - role_shape
    - multi_role
    - role_name_shape
    - executor_privilege
    - owned_objects_state
    - nonexistent_role
    - privilege_insufficient
    - dependent_objects
    - cross_database_limitation
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - role_existence
  rendering:
    statement_template: "DROP OWNED BY {role_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT relowner FROM pg_class WHERE relowner = '{role_oid}'"
    factor_value_bindings:
      cascade_restrict_clause:
        no_clause_default_restrict: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
