# 技能：CREATE GROUP

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-creategroup.html

```sql
CREATE GROUP name [ [ WITH ] option [ ... ] ]

where option can be:

      SUPERUSER | NOSUPERUSER
    | CREATEDB | NOCREATEDB
    | CREATEROLE | NOCREATEROLE
    | INHERIT | NOINHERIT
    | LOGIN | NOLOGIN
    | REPLICATION | NOREPLICATION
    | BYPASSRLS | NOBYPASSRLS
    | CONNECTION LIMIT connlimit
    | [ ENCRYPTED ] PASSWORD 'password' | PASSWORD NULL
    | VALID UNTIL 'timestamp'
    | IN ROLE role_name [, ...]
    | IN GROUP role_name [, ...]
    | ROLE role_name [, ...]
    | ADMIN role_name [, ...]
    | USER role_name [, ...]
    | SYSID uid
```

**重要废弃说明**：
- CREATE GROUP 是 **CREATE ROLE 的废弃别名**。GROUP 和 USER 已被更通用的 ROLE 概念取代。
- 推荐使用 **CREATE ROLE** 替代 CREATE GROUP。
- `IN GROUP`、`USER`、`SYSID` 选项是历史遗留术语，仅为向后兼容保留。
- `IN GROUP` 是 `IN ROLE` 的废弃别名。
- `USER` 是 `ROLE` 的废弃别名。
- `SYSID` 被忽略（历史遗留），角色 ID 自动分配。
- `ENCRYPTED` 关键字被忽略，密码始终加密存储。
- CREATE GROUP 不属于 SQL 标准。
- 权限要求与 CREATE ROLE 相同：通常需要 CREATEROLE 权限。

## 语句作用

官方说明：CREATE GROUP — define a new database role

**该语句是 CREATE ROLE 的废弃别名**。该 reference 关注 CREATE GROUP 的语法形式（完全等同于 CREATE ROLE）、所有角色选项组合、权限边界（CREATEROLE）和废弃别名映射行为。

CREATE GROUP **不涉及列类型定义**——它定义数据库角色，不直接创建表/列结构。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE GROUP name / CREATE GROUP name WITH options）
- object_state：目标 group(role) 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- with_clause：WITH 子句开关（省略 / 指定）
- superuser_option：SUPERUSER / NOSUPERUSER 选项（默认 NOSUPERUSER / 指定 SUPERUSER）
- login_option：LOGIN / NOLOGIN 选项（默认 NOLOGIN / 指定 LOGIN）
- createdb_option：CREATEDB / NOCREATEDB 选项
- createrole_option：CREATEROLE / NOCREATEROLE 选项
- password_option：PASSWORD 子句形态（省略 / PASSWORD 'password' / PASSWORD NULL / ENCRYPTED PASSWORD）
- membership_option：成员关系子句（IN ROLE / IN GROUP / ROLE / ADMIN / USER）
- deprecated_aliases：废弃别名行为（IN GROUP 代替 IN ROLE / USER 代替 ROLE / SYSID 被忽略）

### T3：对象名与输入形态因子
- group_name_shape：GROUP(role) 名称形态
- referenced_role_shape：IN ROLE/IN GROUP/ROLE/ADMIN/USER 引用的角色名形态
- password_shape：密码值形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（createrole_privilege / non_createrole / superuser）
- referenced_role_existence：IN ROLE/ROLE/ADMIN 引用的角色存在性（存在 / 不存在）

### T5：异常与边界因子
- duplicate_group_name：重名冲突（与已有角色同名）
- insufficient_privilege：无 CREATEROLE 权限
- nonexistent_referenced_role：IN ROLE/ROLE/ADMIN 引用的角色不存在
- sysid_ignored：SYSID 选项被忽略（行为边界）
- in_group_deprecated_alias：IN GROUP 是 IN ROLE 的废弃别名（行为边界）
- user_deprecated_alias：USER 是 ROLE 的废弃别名（行为边界）
- encrypted_keyword_ignored：ENCRYPTED 关键字被忽略（行为边界）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE GROUP 全部语法分支。
- 不需要覆盖所有基表和所有列类型，因为 CREATE GROUP 不涉及表/列/索引组合。
- 需要覆盖废弃别名行为（IN GROUP、USER、SYSID）。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE GROUP 是 CREATE ROLE 的废弃别名，必须在每个样本中显式标注此废弃状态。
- 必须覆盖对象成功创建、重名冲突与依赖角色缺失路径。
- 成功路径必须包含可验证的角色存在性检查，并在生命周期末尾清理角色。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE GROUP 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- CREATE GROUP 需要 CREATEROLE 权限或 superuser 权限，必须在生成样本中显式标注。
- 废弃别名行为（IN GROUP / USER / SYSID / ENCRYPTED）需要代表性覆盖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要 CREATEROLE 权限或引用角色存在性的分支。
- T5 因子中废弃别名行为边界因子挂靠到使用废弃语法的样本上。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖（CREATEROLE / 非 CREATEROLE / superuser）
  - 废弃别名行为全覆盖（IN GROUP / USER / SYSID / ENCRYPTED）
- 次优先保证：
  - 角色选项组合代表性覆盖
  - 成员关系子句代表性覆盖
  - PASSWORD 子句形态覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: group
  skill_name: create_group
  official_source: https://www.postgresql.org/docs/16/sql-creategroup.html
  statement:
    key: create_group
    name: CREATE GROUP
    aliases:
    - CREATE GROUP
    - create group
    - create_group
    - CREATE ROLE (canonical)
    - create_role (canonical)
    purpose: define a new database role (DEPRECATED alias for CREATE ROLE)
  syntax_templates:
  - "CREATE GROUP name [ [ WITH ] option [ ... ] ]"
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
    - with_clause
    - superuser_option
    - login_option
    - createdb_option
    - createrole_option
    - password_option
    - membership_option
    - deprecated_aliases
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - group_name_shape
    - referenced_role_shape
    - password_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - referenced_role_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_group_name
    - insufficient_privilege
    - nonexistent_referenced_role
    - sysid_ignored
    - in_group_deprecated_alias
    - user_deprecated_alias
    - encrypted_keyword_ignored
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
      - key: branch_create_group_simple
        label: CREATE GROUP name (无选项)
      - key: branch_create_group_with_options
        label: CREATE GROUP name [ WITH ] option [ ... ] (有选项)
    object_state:
      label: 目标 group(role) 对象状态
      importance: important
      values:
      - key: not_exists
        label: 角色/组不存在
      - key: already_exists
        label: 角色/组已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    with_clause:
      label: WITH 子句开关
      importance: non_important
      values:
      - key: omitted
        label: 省略 WITH
      - key: specified
        label: 指定 WITH
    superuser_option:
      label: SUPERUSER / NOSUPERUSER 选项
      importance: non_important
      values:
      - key: nosuperuser_default
        label: NOSUPERUSER (默认)
      - key: superuser
        label: SUPERUSER (需要 superuser 权限)
    login_option:
      label: LOGIN / NOLOGIN 选项
      importance: non_important
      values:
      - key: nologin_default
        label: NOLOGIN (默认，组角色)
      - key: login
        label: LOGIN (可登录角色)
    createdb_option:
      label: CREATEDB / NOCREATEDB 选项
      importance: non_important
      values:
      - key: nocreatedb_default
        label: NOCREATEDB (默认)
      - key: createdb
        label: CREATEDB
    createrole_option:
      label: CREATEROLE / NOCREATEROLE 选项
      importance: non_important
      values:
      - key: nocreaterole_default
        label: NOCREATEROLE (默认)
      - key: createrole
        label: CREATEROLE
    password_option:
      label: PASSWORD 子句形态
      importance: non_important
      values:
      - key: omitted
        label: 省略 PASSWORD
      - key: password_value
        label: PASSWORD 'password'
      - key: password_null
        label: PASSWORD NULL
      - key: encrypted_password
        label: "[ ENCRYPTED ] PASSWORD 'password' (ENCRYPTED 被忽略)"
    membership_option:
      label: 成员关系子句
      importance: non_important
      values:
      - key: omitted
        label: 省略成员关系
      - key: in_role
        label: IN ROLE role_name (标准)
      - key: in_group
        label: IN GROUP role_name (废弃别名)
      - key: role_clause
        label: ROLE role_name (标准)
      - key: user_clause
        label: USER role_name (废弃别名)
      - key: admin_clause
        label: ADMIN role_name
    deprecated_aliases:
      label: 废弃别名行为
      importance: non_important
      values:
      - key: no_deprecated_syntax
        label: 使用标准语法
      - key: in_group_alias
        label: 使用 IN GROUP (IN ROLE 的废弃别名)
      - key: user_alias
        label: 使用 USER (ROLE 的废弃别名)
      - key: sysid_ignored
        label: 使用 SYSID (被忽略)
      - key: encrypted_ignored
        label: 使用 ENCRYPTED (被忽略)
    group_name_shape:
      label: GROUP(role) 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: reserved_word_name
        label: 保留字作为名称
      - key: duplicate_name
        label: 已存在的角色名
    referenced_role_shape:
      label: IN ROLE/IN GROUP/ROLE/ADMIN/USER 引用的角色名形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: nonexistent_role
        label: 不存在的角色名
    password_shape:
      label: 密码值形态
      importance: non_important
      values:
      - key: valid_password
        label: 有效密码字符串
      - key: null_password
        label: NULL 密码
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: createrole_privilege
        label: CREATEROLE 权限 → success
      - key: non_createrole
        label: 无 CREATEROLE 权限 → error
      - key: superuser
        label: superuser → success
    referenced_role_existence:
      label: IN ROLE/ROLE/ADMIN 引用的角色存在性
      importance: non_important
      values:
      - key: role_exists
        label: 引用的角色存在 → success
      - key: role_not_exists
        label: 引用的角色不存在 → error
    duplicate_group_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: same_name_conflict
        label: 同名角色已存在 → error
    insufficient_privilege:
      label: 无 CREATEROLE 权限
      importance: non_important
      values:
      - key: has_createrole
        label: 有 CREATEROLE 权限 → success
      - key: lacks_createrole
        label: 无 CREATEROLE 权限 → error
    nonexistent_referenced_role:
      label: IN ROLE/ROLE/ADMIN 引用的角色不存在
      importance: non_important
      values:
      - key: role_exists
        label: 角色存在
      - key: role_missing
        label: 角色不存在 → error
    sysid_ignored:
      label: SYSID 选项被忽略
      importance: non_important
      values:
      - key: no_sysid
        label: 不使用 SYSID
      - key: sysid_ignored
        label: SYSID 被忽略 (行为边界)
    in_group_deprecated_alias:
      label: IN GROUP 是 IN ROLE 的废弃别名
      importance: non_important
      values:
      - key: use_in_role
        label: 使用 IN ROLE (标准)
      - key: use_in_group
        label: 使用 IN GROUP (废弃别名，行为等价)
    user_deprecated_alias:
      label: USER 是 ROLE 的废弃别名
      importance: non_important
      values:
      - key: use_role
        label: 使用 ROLE (标准)
      - key: use_user
        label: 使用 USER (废弃别名，行为等价)
    encrypted_keyword_ignored:
      label: ENCRYPTED 关键字被忽略
      importance: non_important
      values:
      - key: no_encrypted
        label: 不使用 ENCRYPTED
      - key: encrypted_ignored
        label: ENCRYPTED 被忽略 (行为边界)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_authid_catalog_query
        label: pg_authid 系统目录查询
      - key: pg_roles_view_query
        label: pg_roles 视图查询
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_group
        label: DROP GROUP
      - key: drop_role
        label: DROP ROLE (等价)
      - key: referenced_role_cleanup
        label: 清理引用的角色
  notes:
    deprecated_alias_for_create_role: CREATE GROUP 是 CREATE ROLE 的废弃别名，推荐使用 CREATE ROLE。
    in_group_deprecated: IN GROUP 是 IN ROLE 的废弃别名。
    user_deprecated: USER 是 ROLE 的废弃别名。
    sysid_ignored: SYSID 选项被忽略（历史遗留）。
    encrypted_ignored: ENCRYPTED 关键字被忽略（密码始终加密存储）。
    createrole_privilege: CREATE GROUP 需要 CREATEROLE 权限或 superuser 权限。
    group_no_column_types: CREATE GROUP 不涉及列类型定义，不需要挂靠基表列类型。
    nologin_default: 默认 NOLOGIN (组角色不可登录)。
  defaults:
    expected_status: success
    privilege_level: createrole_privilege
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - with_clause
    - superuser_option
    - login_option
    - createdb_option
    - createrole_option
    - password_option
    - membership_option
    - deprecated_aliases
    - group_name_shape
    - referenced_role_shape
    - password_shape
    - privilege_level
    - referenced_role_existence
    - duplicate_group_name
    - insufficient_privilege
    - nonexistent_referenced_role
    - sysid_ignored
    - in_group_deprecated_alias
    - user_deprecated_alias
    - encrypted_keyword_ignored
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE GROUP {group_name} [ [ WITH ] {options} ]"
    verification_query_template: "SELECT rolname FROM pg_authid WHERE rolname = '{group_name}'"
    factor_value_bindings: {}
```
