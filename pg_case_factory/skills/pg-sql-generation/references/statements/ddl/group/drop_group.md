# 技能：DROP GROUP

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropgroup.html

```sql
DROP GROUP [ IF EXISTS ] name [, ...]
```

**重要废弃说明**：
- DROP GROUP 是 **DROP ROLE 的废弃别名**。它不是独立的命令——行为与 DROP ROLE 完全相同。
- 推荐使用 **DROP ROLE** 替代 DROP GROUP。
- 权限要求与 DROP ROLE 相同：必须是 superuser 或拥有 CREATEROLE 权限才能删除角色。
- 可以在一次命令中指定多个角色名（逗号分隔）。
- DROP GROUP 不属于 SQL 标准（SQL 标准中没有 DROP GROUP 语句）。

## 语句作用

官方说明：DROP GROUP — remove a database role

**该语句是 DROP ROLE 的废弃别名**。该 reference 关注 DROP GROUP 的语法形式（完全等同于 DROP ROLE）、IF EXISTS 行为、权限边界（CREATEROLE / superuser）和废弃别名映射行为。

DROP GROUP **不涉及列类型定义**——它删除数据库角色，不直接操作表/列结构。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP GROUP / DROP GROUP IF EXISTS）
- object_state：目标 group(role) 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- multi_group：是否同时删除多个 group(role)（单个 / 多个）
- role_session_state：角色是否被活跃 session 使用（无活跃 session / 有活跃 session）
- role_dependency：角色是否仍被依赖（无依赖 / 有对象依赖）

### T3：对象名与输入形态因子
- group_name_shape：GROUP(role) 名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / createrole_privilege / non_privilege）
- role_dependency_state：角色是否仍被数据库对象引用（无引用 / 有引用）
- session_dependency_state：角色是否被活跃 session 使用（无 / 有）

### T5：异常与边界因子
- nonexistent_group：目标 group(role) 不存在且无 IF EXISTS
- insufficient_privilege：无 CREATEROLE 权限或非 superuser
- role_still_referenced：角色仍被数据库对象引用
- session_role_in_use：角色被活跃 session 使用（行为边界）
- if_exists_notice：IF EXISTS 遇不存在对象的 notice 路径
- deprecated_alias_behavior：DROP GROUP 是 DROP ROLE 的废弃别名（行为边界标注）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP GROUP 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表和所有列类型，因为 DROP GROUP 不涉及表/列/索引组合。
- 需要覆盖废弃别名等价行为（DROP GROUP ≡ DROP ROLE）。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- DROP GROUP 是 DROP ROLE 的废弃别名，必须在每个样本中显式标注此废弃状态。
- 必须覆盖目标角色存在时的成功删除路径，以及目标角色不存在时的失败路径。
- 支持 `IF EXISTS` 时，必须覆盖不存在对象的代表性 no-op 路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP GROUP 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP GROUP 需要 CREATEROLE 权限或 superuser 权限，必须在生成样本中显式标注。
- DROP GROUP 不支持 CASCADE/RESTRICT 子句（与 DROP ROLE 相同），不得伪造这些子句的分支。
- 角色仍被数据库对象引用或被活跃 session 使用时，DROP 可能受限制，需要代表性覆盖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、角色依赖或 session 依赖的分支。
- T5 因子中废弃别名行为边界因子挂靠到所有使用 DROP GROUP 的样本上。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（DROP GROUP / DROP GROUP IF EXISTS）
  - 目标角色存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 废弃别名等价行为全覆盖
  - 权限核心路径全覆盖（CREATEROLE / superuser / 非 CREATEROLE）
- 次优先保证：
  - IF EXISTS 子句代表性覆盖
  - 多角色删除代表性覆盖
  - 角色依赖边界覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: group
  skill_name: drop_group
  official_source: https://www.postgresql.org/docs/16/sql-dropgroup.html
  statement:
    key: drop_group
    name: DROP GROUP
    aliases:
    - DROP GROUP
    - drop group
    - drop_group
    - DROP ROLE (canonical)
    - drop_role (canonical)
    purpose: remove a database role (DEPRECATED alias for DROP ROLE)
  syntax_templates:
  - "DROP GROUP [ IF EXISTS ] name [, ...]"
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
    - multi_group
    - role_session_state
    - role_dependency
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - group_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - role_dependency_state
    - session_dependency_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_group
    - insufficient_privilege
    - role_still_referenced
    - session_role_in_use
    - if_exists_notice
    - deprecated_alias_behavior
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
      - key: branch_drop_group
        label: DROP GROUP name [, ...]
      - key: branch_drop_group_if_exists
        label: DROP GROUP IF EXISTS name [, ...]
    object_state:
      label: 目标 group(role) 对象状态
      importance: important
      values:
      - key: exists
        label: 角色/组已存在
      - key: not_exists
        label: 角色/组不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: important
      values:
      - key: absent
        label: 省略 IF EXISTS
      - key: present
        label: 指定 IF EXISTS
    multi_group:
      label: 是否同时删除多个 group(role)
      importance: non_important
      values:
      - key: single_group
        label: 单个角色名
      - key: multiple_groups
        label: 多个角色名 (逗号分隔)
    role_session_state:
      label: 角色是否被活跃 session 使用
      importance: non_important
      values:
      - key: no_active_session
        label: 无活跃 session 使用该角色
      - key: active_session
        label: 有活跃 session 使用该角色 (行为边界)
    role_dependency:
      label: 角色是否仍被依赖
      importance: non_important
      values:
      - key: no_dependencies
        label: 角色无依赖对象
      - key: has_dependencies
        label: 角色仍被数据库对象引用
    group_name_shape:
      label: GROUP(role) 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_name
        label: 不存在的角色名
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: superuser
        label: 超级用户 → success
      - key: createrole_privilege
        label: CREATEROLE 权限 → success
      - key: non_privilege
        label: 无 CREATEROLE 且非 superuser → error
    role_dependency_state:
      label: 角色是否仍被数据库对象引用
      importance: non_important
      values:
      - key: no_references
        label: 角色无对象引用
      - key: has_references
        label: 角色被对象引用 (DROP 可能受限)
    session_dependency_state:
      label: 角色是否被活跃 session 使用
      importance: non_important
      values:
      - key: no_active_session
        label: 无活跃 session
      - key: has_active_session
        label: 有活跃 session (行为边界)
    nonexistent_group:
      label: 目标 group(role) 不存在且无 IF EXISTS
      importance: non_important
      values:
      - key: group_exists
        label: 角色/组存在
      - key: group_missing_no_if_exists
        label: 角色/组不存在且无 IF EXISTS → error
    insufficient_privilege:
      label: 无 CREATEROLE 权限或非 superuser
      importance: non_important
      values:
      - key: sufficient_privilege
        label: CREATEROLE 或 superuser → success
      - key: lacks_privilege
        label: 无 CREATEROLE 且非 superuser → error
    role_still_referenced:
      label: 角色仍被数据库对象引用
      importance: non_important
      values:
      - key: no_references
        label: 角色无引用 → success
      - key: has_references
        label: 角色仍被引用 (行为边界)
    session_role_in_use:
      label: 角色被活跃 session 使用
      importance: non_important
      values:
      - key: no_active_session
        label: 无活跃 session
      - key: active_session
        label: 有活跃 session (行为边界)
    if_exists_notice:
      label: IF EXISTS 遇不存在对象的 notice 路径
      importance: non_important
      values:
      - key: no_notice
        label: 不使用 IF EXISTS 或角色存在
      - key: notice_no_op
        label: IF EXISTS 遇不存在 → notice (no-op)
    deprecated_alias_behavior:
      label: DROP GROUP 是 DROP ROLE 的废弃别名
      importance: non_important
      values:
      - key: deprecated_alias
        label: DROP GROUP ≡ DROP ROLE (行为完全等价)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_authid_catalog_query
        label: pg_authid 系统目录查询
      - key: error_assertion
        label: 错误断言
      - key: notice_assertion
        label: notice 断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: recreate_role
        label: 重新创建角色
      - key: cleanup_referenced_objects
        label: 清理引用对象
      - key: terminate_session
        label: 终止活跃 session
  notes:
    deprecated_alias_for_drop_role: DROP GROUP 是 DROP ROLE 的废弃别名，行为完全等价。
    no_cascade_restrict: DROP GROUP (和 DROP ROLE) 不支持 CASCADE/RESTRICT 子句。
    createrole_or_superuser: 需要 CREATEROLE 权限或 superuser 权限才能删除角色。
    role_may_be_referenced: 角色仍被数据库对象引用时 DROP 可能受限。
    session_dependency: 角色被活跃 session 使用时是行为边界。
    group_no_column_types: DROP GROUP 不涉及列类型定义，不需要挂靠基表列类型。
    sql_standard: SQL 标准中没有 DROP GROUP 语句。
  defaults:
    expected_status: success
    privilege_level: superuser
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - multi_group
    - role_session_state
    - role_dependency
    - group_name_shape
    - privilege_level
    - role_dependency_state
    - session_dependency_state
    - nonexistent_group
    - insufficient_privilege
    - role_still_referenced
    - session_role_in_use
    - if_exists_notice
    - deprecated_alias_behavior
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP GROUP [ IF EXISTS ] {group_name} [, ...]"
    verification_query_template: "SELECT rolname FROM pg_authid WHERE rolname = '{group_name}'"
    factor_value_bindings: {}
```
