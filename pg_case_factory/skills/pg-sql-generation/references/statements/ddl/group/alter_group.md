# 技能：ALTER GROUP

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altergroup.html

```sql
ALTER GROUP role_specification ADD USER user_name [, ... ]
ALTER GROUP role_specification DROP USER user_name [, ... ]

where role_specification can be:

    role_name
  | CURRENT_ROLE
  | CURRENT_USER
  | SESSION_USER

ALTER GROUP group_name RENAME TO new_name
```

**重要废弃说明**：
- ALTER GROUP 是 **废弃命令**，仅为向后兼容保留。Groups (和 users) 已被更通用的 **roles** 概念取代。
- 推荐使用现代命令替代：
  - `ALTER GROUP ... ADD USER` → `GRANT group_name TO user_name`
  - `ALTER GROUP ... DROP USER` → `REVOKE group_name FROM user_name`
  - `ALTER GROUP ... RENAME TO` → `ALTER ROLE group_name RENAME TO new_name`
- ADD USER / DROP USER 实质上等同于授予/撤销角色成员关系。
- GRANT 和 REVOKE 提供了 ALTER GROUP 不具备的额外选项（如 ADMIN OPTION、指定 grantor）。
- RENAME TO 与 ALTER ROLE ... RENAME TO 完全等价。
- 任何角色都可以作为 "user" 或 "group" 使用。
- ALTER GROUP 不属于 SQL 标准。
- ADD/DROP USER 要求 user_name 已经存在（ALTER GROUP 不创建/删除用户）。

## 语句作用

官方说明：ALTER GROUP — change role name or membership

**该语句是废弃命令**。该 reference 关注 ALTER GROUP 的三个语法分支（ADD USER / DROP USER / RENAME TO）、废弃别名映射行为、角色成员关系操作和权限边界。

ALTER GROUP **不涉及列类型定义**——它操作角色成员关系和角色重命名，不直接创建或修改表/列结构。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（ADD USER / DROP USER / RENAME TO）
- object_state：目标 group(role) 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（add_user / drop_user / rename）
- role_specification：role_specification 形态（role_name / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- multi_user：ADD/DROP USER 是否指定多个用户（单个 / 多个）
- deprecated_equivalence：废弃别名等价行为（ADD USER ≡ GRANT / DROP USER ≡ REVOKE / RENAME TO ≡ ALTER ROLE RENAME）

### T3：对象名与输入形态因子
- group_name_shape：GROUP(role) 名称形态
- user_name_shape：ADD/DROP USER 中的用户名形态
- new_name_shape：RENAME TO 新名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（group_role_admin / non_admin / superuser）
- user_existence：ADD/DROP USER 的 user_name 存在性（存在 / 不存在）
- target_role_admin：对目标 group 是否有 ADMIN OPTION（有 / 无）

### T5：异常与边界因子
- nonexistent_group：目标 group(role) 不存在
- nonexistent_user：ADD/DROP USER 的 user_name 不存在
- insufficient_privilege：无足够权限操作成员关系
- non_admin_attempt：非 ADMIN 角色尝试 ADD/DROP USER
- duplicate_add_user：ADD USER 添加已是成员的用户（行为边界）
- drop_non_member_user：DROP USER 移除不是成员的用户（行为边界）
- rename_to_existing_name：RENAME TO 与已有角色重名
- deprecated_command_note：ALTER GROUP 是废弃命令（行为边界标注）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER GROUP 三个语法分支中的所有行为路径（ADD USER / DROP USER / RENAME TO）。
- 不需要覆盖所有基表和所有列类型，因为 ALTER GROUP 不涉及表/列/索引组合。
- 需要覆盖废弃别名等价行为（ADD USER ≡ GRANT、DROP USER ≡ REVOKE、RENAME TO ≡ ALTER ROLE）。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER GROUP 是废弃命令，必须在每个样本中显式标注此废弃状态和现代替代命令。
- 必须预创建可被修改的目标 group(role) 对象和 user(role) 对象。
- 必须覆盖目标 group 存在时的成功修改路径、目标 group 不存在时的失败路径。
- ADD USER / DROP USER / RENAME TO 三个分支需要保持独立归因。
- ADD USER 要求 user_name 已经存在（ALTER GROUP 不创建用户），不存在的 user 属于失败路径。
- 成功路径必须包含可验证的角色成员关系变更检查，并在生命周期末尾清理角色。
- 每个样本必须包含明确的前置对象准备、目标 ALTER GROUP 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- ALTER GROUP 的权限要求与对应的现代命令（GRANT/REVOKE/ALTER ROLE）相同。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、user 存在性或 ADMIN OPTION 的分支。
- T5 因子中废弃命令行为边界因子挂靠到所有使用 ALTER GROUP 的样本上。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（ADD USER / DROP USER / RENAME TO）
  - 目标 group 存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 废弃别名等价行为全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - role_specification 形态覆盖（role_name / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
  - 多用户 ADD/DROP 覆盖
  - 成员关系边界覆盖（重复添加 / 移除非成员）
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: group
  skill_name: alter_group
  official_source: https://www.postgresql.org/docs/16/sql-altergroup.html
  statement:
    key: alter_group
    name: ALTER GROUP
    aliases:
    - ALTER GROUP
    - alter group
    - alter_group
    - GRANT (modern equivalent for ADD USER)
    - REVOKE (modern equivalent for DROP USER)
    - ALTER ROLE RENAME (modern equivalent for RENAME TO)
    purpose: change role name or membership (DEPRECATED)
  syntax_templates:
  - "ALTER GROUP role_specification ADD USER user_name [, ... ]"
  - "ALTER GROUP role_specification DROP USER user_name [, ... ]"
  - "ALTER GROUP group_name RENAME TO new_name"
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
    - alter_action
    - role_specification
    - multi_user
    - deprecated_equivalence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - group_name_shape
    - user_name_shape
    - new_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - user_existence
    - target_role_admin
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_group
    - nonexistent_user
    - insufficient_privilege
    - non_admin_attempt
    - duplicate_add_user
    - drop_non_member_user
    - rename_to_existing_name
    - deprecated_command_note
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
      - key: branch_add_user
        label: ALTER GROUP role_specification ADD USER user_name [, ... ]
      - key: branch_drop_user
        label: ALTER GROUP role_specification DROP USER user_name [, ... ]
      - key: branch_rename
        label: ALTER GROUP group_name RENAME TO new_name
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
    alter_action:
      label: ALTER 行为类型
      importance: non_important
      values:
      - key: add_user
        label: ADD USER (≡ GRANT group TO user)
      - key: drop_user
        label: DROP USER (≡ REVOKE group FROM user)
      - key: rename
        label: RENAME TO (≡ ALTER ROLE RENAME TO)
    role_specification:
      label: role_specification 形态
      importance: non_important
      values:
      - key: role_name
        label: 指定 role_name
      - key: current_role
        label: CURRENT_ROLE
      - key: current_user
        label: CURRENT_USER
      - key: session_user
        label: SESSION_USER
    multi_user:
      label: ADD/DROP USER 是否指定多个用户
      importance: non_important
      values:
      - key: single_user
        label: 单个用户名
      - key: multiple_users
        label: 多个用户名 (逗号分隔)
    deprecated_equivalence:
      label: 废弃别名等价行为
      importance: non_important
      values:
      - key: add_user_equals_grant
        label: ADD USER ≡ GRANT group_name TO user_name
      - key: drop_user_equals_revoke
        label: DROP USER ≡ REVOKE group_name FROM user_name
      - key: rename_equals_alter_role
        label: RENAME TO ≡ ALTER ROLE group_name RENAME TO new_name
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
    user_name_shape:
      label: ADD/DROP USER 中的用户名形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_user
        label: 不存在的用户名
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: duplicate_name
        label: 与已有角色重名
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: group_role_admin
        label: 拥有 ADMIN OPTION 的角色成员 → success
      - key: non_admin
        label: 非 ADMIN 角色 → error
      - key: superuser
        label: superuser → success
    user_existence:
      label: ADD/DROP USER 的 user_name 存在性
      importance: non_important
      values:
      - key: user_exists
        label: 用户存在 → success
      - key: user_not_exists
        label: 用户不存在 → error
    target_role_admin:
      label: 对目标 group 是否有 ADMIN OPTION
      importance: non_important
      values:
      - key: has_admin
        label: 有 ADMIN OPTION → success
      - key: lacks_admin
        label: 无 ADMIN OPTION → error
    nonexistent_group:
      label: 目标 group(role) 不存在
      importance: non_important
      values:
      - key: group_exists
        label: 角色/组存在
      - key: group_missing
        label: 角色/组不存在 → error
    nonexistent_user:
      label: ADD/DROP USER 的 user_name 不存在
      importance: non_important
      values:
      - key: user_exists
        label: 用户存在
      - key: user_missing
        label: 用户不存在 → error
    insufficient_privilege:
      label: 无足够权限操作成员关系
      importance: non_important
      values:
      - key: sufficient_privilege
        label: 权限充足 (ADMIN 或 superuser) → success
      - key: insufficient_privilege
        label: 权限不足 (非 ADMIN) → error
    non_admin_attempt:
      label: 非 ADMIN 角色尝试 ADD/DROP USER
      importance: non_important
      values:
      - key: admin_execution
        label: ADMIN 角色执行 → success
      - key: non_admin_execution
        label: 非 ADMIN 角色执行 → error
    duplicate_add_user:
      label: ADD USER 添加已是成员的用户
      importance: non_important
      values:
      - key: new_member
        label: 添加新成员 → success
      - key: existing_member
        label: 添加已是成员的用户 (行为边界，通常 notice)
    drop_non_member_user:
      label: DROP USER 移除不是成员的用户
      importance: non_important
      values:
      - key: existing_member
        label: 移除已是成员的用户 → success
      - key: non_member
        label: 移除不是成员的用户 (行为边界，通常 notice 或 error)
    rename_to_existing_name:
      label: RENAME TO 与已有角色重名
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: same_name_conflict
        label: 与已有角色重名 → error
    deprecated_command_note:
      label: ALTER GROUP 是废弃命令
      importance: non_important
      values:
      - key: deprecated_no_warning
        label: ALTER GROUP 为废弃命令 (PG 不发警告，但文档标注)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_auth_members_catalog
        label: pg_auth_members 系统目录查询 (成员关系)
      - key: pg_authid_catalog
        label: pg_authid 系统目录查询 (角色名)
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: revoke_membership
        label: REVOKE 撤销成员关系 (还原 ADD USER)
      - key: grant_membership
        label: GRANT 重新授予成员关系 (还原 DROP USER)
      - key: revert_rename
        label: 还原角色重命名
      - key: drop_role
        label: DROP ROLE/DROP GROUP
  notes:
    deprecated_command: ALTER GROUP 是废弃命令，推荐使用 GRANT/REVOKE/ALTER ROLE 替代。
    add_user_equals_grant: ALTER GROUP ... ADD USER 等同于 GRANT group_name TO user_name。
    drop_user_equals_revoke: ALTER GROUP ... DROP USER 等同于 REVOKE group_name FROM user_name。
    rename_equals_alter_role: ALTER GROUP ... RENAME TO 等同于 ALTER ROLE ... RENAME TO。
    user_must_exist: ADD/DROP USER 要求 user_name 已经存在，ALTER GROUP 不创建/删除用户。
    any_role_as_user_or_group: 任何角色都可以作为 "user" 或 "group" 使用。
    group_no_column_types: ALTER GROUP 不涉及列类型定义，不需要挂靠基表列类型。
  defaults:
    expected_status: success
    privilege_level: group_role_admin
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - role_specification
    - multi_user
    - deprecated_equivalence
    - group_name_shape
    - user_name_shape
    - new_name_shape
    - privilege_level
    - user_existence
    - target_role_admin
    - nonexistent_group
    - nonexistent_user
    - insufficient_privilege
    - non_admin_attempt
    - duplicate_add_user
    - drop_non_member_user
    - rename_to_existing_name
    - deprecated_command_note
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER GROUP {group_name} {alter_clause}"
    verification_query_template: "SELECT rolname FROM pg_authid WHERE rolname = '{group_name}'"
    factor_value_bindings:
      alter_action:
        add_user: "ADD USER {user_names}"
        drop_user: "DROP USER {user_names}"
        rename: "RENAME TO {new_name}"
```
