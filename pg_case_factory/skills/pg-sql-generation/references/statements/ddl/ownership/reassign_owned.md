# 技能：REASSIGN OWNED

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-reassign-owned.html

```sql
REASSIGN OWNED BY { old_role | CURRENT_ROLE | CURRENT_USER | SESSION_USER } [, ...]
               TO { new_role | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
```

**重要约束：**
- REASSIGN OWNED **不支持** IF EXISTS、CASCADE 或 RESTRICT 子句。
- REASSIGN OWNED **不涉及** 表/列/索引组合；它操作的是角色拥有的所有数据库对象。
- REASSIGN OWNED 只影响当前数据库中的对象，不影响其他数据库中的对象。
- REASSIGN OWNED 需要 superuser 权限或源角色与目标角色的 CREATEROLE 权限。

## 语句作用

官方说明：REASSIGN OWNED — change the ownership of database objects owned by a database role

该 reference 关注角色所有权转移语句的源角色形态、目标角色形态、权限边界和成功/失败路径，不负责覆盖所有基表列类型或表级依赖对象。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（REASSIGN OWNED 仅有一条 synopsis 形式）
- old_role_identity：源角色存在状态
- new_role_identity：目标角色存在状态
- expected_status：预期结果（成功/失败）

### T2：重要行为因子
- old_role_shape：源角色形态（具体角色名 / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- new_role_shape：目标角色形态（具体角色名 / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- multi_old_role：多源角色行为

### T3：对象名与输入形态因子
- role_name_shape：角色名标识符形态
- quoted_identifier：双引号标识符形态

### T4：依赖对象与环境因子
- **本语句不涉及表（table）、列（column）或索引（index）对象。REASSIGN OWNED 是角色级语句，自动操作当前数据库中源角色拥有的所有对象，无表类型或列类型依赖。**
- executor_privilege：执行者权限上下文（superuser / CREATEROLE / 普通角色）
- owned_objects_state：源角色拥有的对象状态（有/无拥有对象）

### T5：异常与边界因子
- nonexistent_old_role：源角色不存在
- nonexistent_new_role：目标角色不存在
- privilege_insufficient：权限不足（非 superuser 且非 CREATEROLE）
- self_reassign：源角色与目标角色相同
- cross_database_limitation：跨数据库限制

### T6：验证与清理因子
- verification_mode：验证方式（pg_class / pg_roles 目录查询）
- cleanup_mode：清理方式（DROP OWNED / REASSIGN OWNED / DROP ROLE）

## 覆盖策略

- 覆盖源角色不存在（失败）、目标角色不存在（失败）、源角色与目标角色均存在（成功）的核心状态。
- 覆盖 CURRENT_ROLE、CURRENT_USER、SESSION_USER 等特殊角色形态的代表性取值。
- 覆盖多源角色列表的代表性取值。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。
- 需要 superuser 权限的分支必须单独标注环境依赖。

## 生成约束

- 必须覆盖源角色存在且拥有对象时的成功转移路径，以及源角色或目标角色不存在时的失败路径。
- REASSIGN OWNED 不支持 IF EXISTS、CASCADE 或 RESTRICT，不得生成包含该子句的样本。
- 成功路径必须包含可通过 pg_class 目录验证的对象所有权变更检查，并在生命周期末尾清理角色和对象。
- REASSIGN OWNED 只影响当前数据库中的对象，必须在样本中标注此限制。
- 每个样本必须包含明确的前置角色准备、目标 REASSIGN OWNED 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或角色拥有对象状态的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - 源角色存在/不存在、目标角色存在/不存在全覆盖
  - 成功/失败路径全覆盖
  - 权限核心路径全覆盖（superuser 成功、普通角色失败）
- 次优先保证：
  - CURRENT_ROLE / CURRENT_USER / SESSION_USER 特殊形态代表性覆盖
  - 多源角色列表代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: ownership
  skill_name: reassign_owned
  official_source: https://www.postgresql.org/docs/16/sql-reassign-owned.html
  statement:
    key: reassign_owned
    name: REASSIGN OWNED
    aliases:
    - reassign_owned
    - REASSIGN OWNED
    purpose: REASSIGN OWNED — change the ownership of database objects owned by a database role
  syntax_templates:
  - "REASSIGN OWNED BY { old_role | CURRENT_ROLE | CURRENT_USER | SESSION_USER } [, ...]\n               TO { new_role | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - old_role_identity
    - new_role_identity
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - old_role_shape
    - new_role_shape
    - multi_old_role
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - role_name_shape
    - quoted_identifier
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - owned_objects_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_old_role
    - nonexistent_new_role
    - privilege_insufficient
    - self_reassign
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
      - key: branch_reassign_owned
        label: REASSIGN OWNED BY old_role [, ...] TO new_role
    old_role_identity:
      label: 源角色存在状态
      importance: important
      values:
      - role_exists
      - role_not_exists
      - role_is_current_user
      - role_is_superuser
    new_role_identity:
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
    old_role_shape:
      label: 源角色形态
      importance: non_important
      values:
      - explicit_role_name
      - current_role_keyword
      - current_user_keyword
      - session_user_keyword
    new_role_shape:
      label: 目标角色形态
      importance: non_important
      values:
      - explicit_role_name
      - current_role_keyword
      - current_user_keyword
      - session_user_keyword
    multi_old_role:
      label: 多源角色行为
      importance: non_important
      values:
      - single_old_role
      - multiple_old_roles
    role_name_shape:
      label: 角色名标识符形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - reserved_word_name
      - case_sensitive_name
      - non_existing_name
    quoted_identifier:
      label: 双引号标识符形态
      importance: non_important
      values:
      - unquoted
      - double_quoted
      - mixed_case_quoted
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - createrole_privilege
      - normal_user_no_privilege
    owned_objects_state:
      label: 源角色拥有对象状态
      importance: non_important
      values:
      - owns_no_objects
      - owns_tables
      - owns_multiple_objects
    nonexistent_old_role:
      label: 源角色不存在
      importance: non_important
      values:
      - old_role_does_not_exist
    nonexistent_new_role:
      label: 目标角色不存在
      importance: non_important
      values:
      - new_role_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_reassigning_other_role
      - no_createrole_privilege
    self_reassign:
      label: 源角色与目标角色相同
      importance: non_important
      values:
      - same_role_no_effect
    cross_database_limitation:
      label: 跨数据库限制
      importance: non_important
      values:
      - only_current_database_objects
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_class_owner_query
      - pg_roles_catalog_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_owned_then_drop_role
      - reassign_owned_then_drop_role
      - drop_role_cascade
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - old_role_identity
    - new_role_identity
    - expected_status
    non_main_factors:
    - old_role_shape
    - new_role_shape
    - multi_old_role
    - role_name_shape
    - quoted_identifier
    - executor_privilege
    - owned_objects_state
    - nonexistent_old_role
    - nonexistent_new_role
    - privilege_insufficient
    - self_reassign
    - cross_database_limitation
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - old_role_identity
  rendering:
    statement_template: "REASSIGN OWNED BY {old_role} [, ...] TO {new_role}"
    verification_query_template: "SELECT relowner FROM pg_class WHERE relowner = '{new_role_oid}'"
    factor_value_bindings: {}
```
