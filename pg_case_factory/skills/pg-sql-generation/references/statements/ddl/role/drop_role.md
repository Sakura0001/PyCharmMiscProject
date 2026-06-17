# 技能：DROP ROLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droprole.html

```sql
DROP ROLE [ IF EXISTS ] name [, ...]
```

**重要约束：**
- DROP ROLE **不支持** CASCADE / RESTRICT 子句。
- DROP ROLE **不涉及** 表/列/索引组合。
- 删除角色前必须先处理该角色拥有的所有对象（使用 REASSIGN OWNED 或 DROP OWNED）。
- 删除角色前必须先撤销该角色被授予的其他对象权限。
- DROP ROLE 会自动撤销该角色在其他角色中的成员关系，以及其他角色在该角色中的成员关系。

## 语句作用

官方说明：DROP ROLE — remove a database role

该 reference 关注角色删除语句的语法分支、权限边界、依赖对象约束和成功/失败路径，不负责包装所有样本到统一外层事务。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP ROLE、DROP ROLE IF EXISTS）
- role_existence：目标角色对象存在状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句行为
- privilege_context：权限上下文（SUPERUSER / CREATEROLE+ADMIN / 无权限）
- multi_target：多目标删除行为

### T3：对象名与输入形态因子
- role_name_shape：角色名称形态

### T4：依赖对象与环境因子
- owned_objects：角色拥有的对象状态
- membership_state：角色成员关系状态
- active_session：角色活跃会话状态

### T5：异常与边界因子
- dependency_conflict：依赖冲突类型
- privilege_insufficient：权限不足场景
- boundary_case：边界情况

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖角色存在 / 不存在 / 拥有对象 / 有成员关系 / 有活跃会话等状态。
- IF EXISTS 子句按语句支持情况覆盖。
- DROP ROLE 不支持 CASCADE / RESTRICT，不覆盖该子句组合。
- DROP ROLE 不涉及表/列/索引组合，不覆盖基表列类型因子。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标角色存在时的成功删除路径，以及目标角色不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在角色的代表性 no-op 路径。
- DROP ROLE 不支持 CASCADE / RESTRICT，不得生成包含该子句的样本。
- DROP ROLE 不涉及表/列/索引组合，不得挂靠基表列类型因子。
- 必须覆盖角色仍拥有对象时的失败路径（需先使用 DROP OWNED / REASSIGN OWNED）。
- 必须覆盖权限不足时的失败路径（非 SUPERUSER 删除超级用户角色、无 CREATEROLE+ADMIN 删除普通角色）。
- 对需要 SUPERUSER 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 每个样本必须包含明确的前置对象准备、目标 DROP ROLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限、角色成员关系的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标角色存在 / 不存在 / 冲突 / 非法输入全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字代表性覆盖
  - 角色拥有对象、成员关系等依赖对象代表性覆盖
  - 引用、依赖、权限和环境限制代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 输出要求

- 生成结果应为可执行的 PostgreSQL DROP ROLE 测试样本集合。
- 输出样本应具备明确因子归因能力。
- 每个样本应标注所属语法分支、预期成功/失败、前置依赖和清理策略。
- 当采用裁剪策略时，应优先保留语句分支、成功/失败路径和对象状态覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: role
  skill_name: drop_role
  official_source: https://www.postgresql.org/docs/16/sql-droprole.html
  statement:
    key: drop_role
    name: DROP ROLE
    aliases:
    - drop_role
    - DROP ROLE
    - droprole
    purpose: DROP ROLE — remove a database role
  syntax_templates:
  - "DROP ROLE [ IF EXISTS ] name [, ...]"
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
    - if_exists_clause
    - privilege_context
    - multi_target
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - role_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - owned_objects
    - membership_state
    - active_session
  - tier: T5
    name: 异常与边界因子
    factors:
    - dependency_conflict
    - privilege_insufficient
    - boundary_case
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
      - key: branch_drop_role
        label: DROP ROLE name
      - key: branch_drop_role_if_exists
        label: DROP ROLE IF EXISTS name
    role_existence:
      label: 目标角色存在状态
      importance: important
      values:
      - role_exists
      - role_not_exists
      - role_exists_as_superuser
      - role_exists_as_nonsuperuser
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句行为
      importance: important
      values:
      - without_if_exists
      - with_if_exists
    privilege_context:
      label: 权限上下文
      importance: important
      values:
      - superuser
      - createrole_with_admin
      - createrole_without_admin
      - no_privilege
    multi_target:
      label: 多目标删除行为
      importance: non_important
      values:
      - single_target
      - multi_target_all_exist
      - multi_target_some_not_exist
    role_name_shape:
      label: 角色名称形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - reserved_word_name
      - case_sensitive_name
      - non_existing_name
      - invalid_name
    owned_objects:
      label: 角色拥有的对象状态
      importance: non_important
      values:
      - no_owned_objects
      - owns_tables
      - owns_sequences
      - owns_views
      - owns_functions
      - owns_multiple_objects
    membership_state:
      label: 角色成员关系状态
      importance: non_important
      values:
      - no_memberships
      - member_of_other_role
      - other_roles_member_of_this
      - both_directions
    active_session:
      label: 角色活跃会话状态
      importance: non_important
      values:
      - no_active_session
      - has_active_session
    dependency_conflict:
      label: 依赖冲突类型
      importance: non_important
      values:
      - no_conflict
      - owns_objects_conflict
      - referenced_in_database
      - privilege_grants_conflict
    privilege_insufficient:
      label: 权限不足场景
      importance: non_important
      values:
      - sufficient_privilege
      - nonsuperuser_dropping_superuser
      - no_createrole_dropping_role
      - createrole_without_admin
    boundary_case:
      label: 边界情况
      importance: non_important
      values:
      - none
      - drop_self
      - drop_current_session_role
      - drop_builtin_role
      - empty_name_list
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_roles
      - catalog_query_pg_authid
      - effect_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_owned_then_drop_role
      - reassign_owned_then_drop_role
      - revoke_privileges_then_drop_role
      - cascade_cleanup
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - role_existence
    - expected_status
    non_main_factors:
    - if_exists_clause
    - privilege_context
    - multi_target
    - role_name_shape
    - owned_objects
    - membership_state
    - active_session
    - dependency_conflict
    - privilege_insufficient
    - boundary_case
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - role_existence
  rendering:
    statement_template: "DROP ROLE [ IF EXISTS ] name [, ...]"
    verification_query_template: "SELECT rolname FROM pg_roles WHERE rolname = '{role_name}'"
    factor_value_bindings: {}
```
