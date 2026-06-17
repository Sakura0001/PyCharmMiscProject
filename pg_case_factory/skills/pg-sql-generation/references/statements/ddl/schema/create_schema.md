# 技能：CREATE SCHEMA

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createschema.html

### Synopsis 形式 1：命名 Schema +可选 Owner +可选内容

```sql
CREATE SCHEMA schema_name [ AUTHORIZATION role_specification ] [ schema_element [ ... ] ]
```

### Synopsis 形式 2：以 Owner 名命名的 Schema +可选内容

```sql
CREATE SCHEMA AUTHORIZATION role_specification [ schema_element [ ... ] ]
```

### Synopsis 形式 3：幂等命名 Schema

```sql
CREATE SCHEMA IF NOT EXISTS schema_name [ AUTHORIZATION role_specification ]
```

### Synopsis 形式 4：幂等以 Owner 名命名的 Schema

```sql
CREATE SCHEMA IF NOT EXISTS AUTHORIZATION role_specification
```

### role_specification

```sql
    user_name
  | CURRENT_ROLE
  | CURRENT_USER
  | SESSION_USER
```

**重要行为说明**：
- Schema 名称不能以 `pg_` 开头（系统保留）。
- IF NOT EXISTS 形式不允许包含 schema_element 子命令。
- schema_element 仅接受 CREATE TABLE、CREATE VIEW、CREATE INDEX、CREATE SEQUENCE、CREATE TRIGGER、GRANT 六种子命令，其余对象类型须在 Schema 创建后单独执行。
- 子命令不以分号结尾；PostgreSQL 不保证处理所有前向引用，可能需要手动重排序。
- 调用者必须拥有当前数据库的 CREATE 权限；超级用户自动绕过。
- AUTHORIZATION 指定 Owner 时，调用者必须能 SET ROLE 到该角色。
- PostgreSQL 偏离 SQL 标准：Schema 内对象可由非 Owner 用户拥有（若 Owner 授予 CREATE 权限或超级用户操作）。
- IF NOT EXISTS 是 PostgreSQL 扩展，不属于 SQL 标准。

## 语句作用

官方说明：CREATE SCHEMA — define a new schema

该 reference 关注 Schema 定义语句的语法分支、命名空间管理、Owner 语义与权限边界，不负责包装所有样本到统一外层事务。

CREATE SCHEMA 是命名空间管理语句，**不涉及列类型组合**。Schema 作为纯粹的命名空间容器，其创建行为仅受名称冲突、权限与 Owner 语义影响。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（命名 Schema、以 Owner 命名 Schema、幂等命名 Schema、幂等以 Owner 命名 Schema）
- object_state：目标 Schema 对象存在性（不存在、已存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_not_exists_clause：IF NOT EXISTS 子句（present、absent）
- authorization_clause：AUTHORIZATION 子句（explicit_user、CURRENT_ROLE、CURRENT_USER、SESSION_USER、absent）
- schema_element_inclusion：Schema 内容子命令（with_elements、without_elements）
- role_specification_form：角色指定形式（user_name、CURRENT_ROLE、CURRENT_USER、SESSION_USER）

### T3：对象名与输入形态因子
- schema_name_shape：Schema 名形态（simple、quoted、reserved_word、pg_prefix_reserved、non_existent）
- owner_name_shape：Owner 名形态（existing_role、non_existing_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、schema_creator、non_creator_no_privilege）
- database_privilege：数据库权限（has_CREATE_privilege、no_CREATE_privilege）
- role_dependency：角色依赖（role_exists、role_not_exists、can_SET_ROLE、cannot_SET_ROLE）
- schema_element_dependency：子命令依赖（element_table_exists、element_table_not_exists、element_view_dependency）

### T5：异常与边界因子
- duplicate_schema_name：重名冲突（with_IF_NOT_EXISTS_noop、without_IF_NOT_EXISTS_error）
- pg_prefix_name：pg_ 前缀名称冲突
- insufficient_privilege：权限不足（no_CREATE_on_database、cannot_SET_ROLE_to_owner）
- if_not_exists_with_elements：IF NOT EXISTS 与子命令组合（非法）
- forward_reference_in_elements：子命令前向引用失败

### T6：验证与清理因子
- verification_mode：验证方式（pg_namespace_catalog_query、information_schema_schemata、current_schema_query）
- cleanup_mode：清理方式（DROP_SCHEMA、DROP_SCHEMA_IF_EXISTS、DROP_SCHEMA_CASCADE）

## 覆盖策略

- 必须覆盖所有四种 CREATE SCHEMA 语法分支。
- CREATE SCHEMA 不涉及列类型组合，无需覆盖不同列类型的交叉组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。
- IF NOT EXISTS 分支不得包含 schema_element 子命令，这是一个非法组合边界。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 IF NOT EXISTS 时，需要分别覆盖正常创建、no-op 语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE SCHEMA 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- CREATE SCHEMA 不涉及列类型组合，无需覆盖不同列类型的交叉组合。
- IF NOT EXISTS 分支不得包含 schema_element，这是语义非法组合，必须作为失败边界覆盖。
- Schema 名称不能以 pg_ 开头，必须作为失败边界覆盖。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限或角色限定的分支。
- T4 因子中 privilege_level 和 database_privilege 挂靠到所有分支的失败路径。
- T4 因子中 role_dependency 挂靠到包含 AUTHORIZATION 子句的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - IF NOT EXISTS、AUTHORIZATION 代表性覆盖
  - schema_element 子命令代表性覆盖
  - pg_ 前缀名称、角色依赖代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: schema
  skill_name: create_schema
  official_source: https://www.postgresql.org/docs/16/sql-createschema.html
  statement:
    key: create_schema
    name: CREATE SCHEMA
    aliases:
    - CREATE SCHEMA
    - create schema
    - create_schema
    purpose: define a new schema
  syntax_templates:
  - "CREATE SCHEMA schema_name [ AUTHORIZATION role_specification ] [ schema_element [ ... ] ]"
  - "CREATE SCHEMA AUTHORIZATION role_specification [ schema_element [ ... ] ]"
  - "CREATE SCHEMA IF NOT EXISTS schema_name [ AUTHORIZATION role_specification ]"
  - "CREATE SCHEMA IF NOT EXISTS AUTHORIZATION role_specification"
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
    - if_not_exists_clause
    - authorization_clause
    - schema_element_inclusion
    - role_specification_form
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - schema_name_shape
    - owner_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - database_privilege
    - role_dependency
    - schema_element_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_schema_name
    - pg_prefix_name
    - insufficient_privilege
    - if_not_exists_with_elements
    - forward_reference_in_elements
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
      - key: branch_named_schema
        label: CREATE SCHEMA schema_name [ AUTHORIZATION ... ] [ schema_element ... ]
      - key: branch_auth_schema
        label: CREATE SCHEMA AUTHORIZATION role_specification [ schema_element ... ]
      - key: branch_if_not_exists_named
        label: CREATE SCHEMA IF NOT EXISTS schema_name [ AUTHORIZATION ... ]
      - key: branch_if_not_exists_auth
        label: CREATE SCHEMA IF NOT EXISTS AUTHORIZATION role_specification
    object_state:
      label: 目标Schema对象存在性
      importance: important
      values:
      - key: not_exists
        label: Schema不存在
      - key: already_exists
        label: Schema已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_not_exists_clause:
      label: IF NOT EXISTS 子句
      importance: important
      values:
      - key: present
        label: 包含 IF NOT EXISTS
      - key: absent
        label: 不包含 IF NOT EXISTS
    authorization_clause:
      label: AUTHORIZATION 子句
      importance: important
      values:
      - key: absent
        label: 无 AUTHORIZATION (Owner为当前用户)
      - key: explicit_user
        label: AUTHORIZATION user_name
      - key: CURRENT_ROLE
        label: AUTHORIZATION CURRENT_ROLE
      - key: CURRENT_USER
        label: AUTHORIZATION CURRENT_USER
      - key: SESSION_USER
        label: AUTHORIZATION SESSION_USER
    schema_element_inclusion:
      label: Schema内容子命令
      importance: important
      values:
      - key: without_elements
        label: 无子命令 (空Schema)
      - key: with_create_table
        label: 包含 CREATE TABLE 子命令
      - key: with_create_view
        label: 包含 CREATE VIEW 子命令
      - key: with_multiple_elements
        label: 包含多个子命令
    role_specification_form:
      label: 角色指定形式
      importance: important
      values:
      - key: user_name
        label: 显式用户名
      - key: CURRENT_ROLE
        label: CURRENT_ROLE
      - key: CURRENT_USER
        label: CURRENT_USER
      - key: SESSION_USER
        label: SESSION_USER
    schema_name_shape:
      label: Schema名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: pg_prefix_reserved
        label: pg_ 前缀 (系统保留，非法)
      - key: non_existent
        label: 不存在标识符
    owner_name_shape:
      label: Owner名形态
      importance: non_important
      values:
      - key: existing_role
        label: 已存在角色名
      - key: non_existing_role
        label: 不存在角色名
      - key: CURRENT_ROLE
        label: CURRENT_ROLE
      - key: CURRENT_USER
        label: CURRENT_USER
      - key: SESSION_USER
        label: SESSION_USER
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: schema_creator
        label: 拥有CREATE权限的用户
      - key: non_creator_no_privilege
        label: 无CREATE权限的用户
    database_privilege:
      label: 数据库权限
      importance: non_important
      values:
      - key: has_CREATE_privilege
        label: 拥有数据库CREATE权限
      - key: no_CREATE_privilege
        label: 无数据库CREATE权限
    role_dependency:
      label: 角色依赖
      importance: non_important
      values:
      - key: role_exists
        label: 指定角色存在
      - key: role_not_exists
        label: 指定角色不存在
      - key: can_SET_ROLE
        label: 可以SET ROLE到指定角色
      - key: cannot_SET_ROLE
        label: 不能SET ROLE到指定角色
    schema_element_dependency:
      label: 子命令依赖对象
      importance: non_important
      values:
      - key: element_table_exists
        label: 子命令引用的表已存在
      - key: element_table_not_exists
        label: 子命令引用的表不存在
      - key: element_view_dependency
        label: 子命令VIEW依赖引用表
    duplicate_schema_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: with_IF_NOT_EXISTS_noop
        label: 重名 + IF NOT EXISTS → no-op
      - key: without_IF_NOT_EXISTS_error
        label: 重名 + 无 IF NOT EXISTS → error
    pg_prefix_name:
      label: pg_前缀名称
      importance: non_important
      values:
      - key: pg_prefix_schema_name
        label: 以pg_开头的Schema名 (非法)
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: no_CREATE_on_database
        label: 无数据库CREATE权限
      - key: cannot_SET_ROLE_to_owner
        label: 不能SET ROLE到指定Owner
    if_not_exists_with_elements:
      label: IF NOT EXISTS与子命令组合
      importance: non_important
      values:
      - key: if_not_exists_with_schema_elements
        label: IF NOT EXISTS + schema_element (语义非法)
    forward_reference_in_elements:
      label: 子命令前向引用
      importance: non_important
      values:
      - key: forward_reference_failure
        label: 子命令前向引用失败
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_namespace_catalog_query
        label: pg_namespace 系统目录查询
      - key: information_schema_schemata
        label: information_schema.schemata 查询
      - key: current_schema_query
        label: current_schema() 查询
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_SCHEMA
        label: DROP SCHEMA schema_name
      - key: DROP_SCHEMA_IF_EXISTS
        label: DROP SCHEMA IF EXISTS schema_name
      - key: DROP_SCHEMA_CASCADE
        label: DROP SCHEMA schema_name CASCADE
  notes:
    column_type_combination: CREATE SCHEMA 不涉及列类型组合，它管理命名空间而非操作列。
    namespace_management: Schema 是纯粹的命名空间容器，创建行为仅受名称冲突、权限与 Owner 语义影响。
    pg_prefix_reserved: Schema 名称不能以 pg_ 开头，这是系统保留命名空间。
    if_not_exists_no_elements: IF NOT EXISTS 形式不允许包含 schema_element 子命令。
    subcommand_limitation: schema_element 仅接受 CREATE TABLE/VIEW/INDEX/SEQUENCE/TRIGGER/GRANT 六种子命令。
  defaults:
    expected_status: success
    if_not_exists_clause: absent
    authorization_clause: absent
    schema_element_inclusion: without_elements
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_not_exists_clause
    - authorization_clause
    - schema_element_inclusion
    - role_specification_form
    - schema_name_shape
    - owner_name_shape
    - privilege_level
    - database_privilege
    - role_dependency
    - schema_element_dependency
    - duplicate_schema_name
    - pg_prefix_name
    - insufficient_privilege
    - if_not_exists_with_elements
    - forward_reference_in_elements
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE SCHEMA [ IF NOT EXISTS ] {schema_name} [ AUTHORIZATION {role_specification} ] [ schema_element [ ... ] ]"
    verification_query_template: "SELECT count(*) FROM pg_namespace WHERE nspname = '{schema_name}'"
    factor_value_bindings:
      if_not_exists_clause:
        present: "IF NOT EXISTS"
        absent: ""
      authorization_clause:
        absent: ""
        explicit_user: "AUTHORIZATION {user_name}"
        CURRENT_ROLE: "AUTHORIZATION CURRENT_ROLE"
        CURRENT_USER: "AUTHORIZATION CURRENT_USER"
        SESSION_USER: "AUTHORIZATION SESSION_USER"
```
