# 技能：ALTER SCHEMA

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterschema.html

### Synopsis 形式 1：重命名 Schema

```sql
ALTER SCHEMA name RENAME TO new_name
```

### Synopsis 形式 2：更改 Schema Owner

```sql
ALTER SCHEMA name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
```

**重要行为说明**：
- ALTER SCHEMA 只有两种形式：RENAME 和 OWNER TO。
- 重命名 Schema 时，新名称不能以 `pg_` 开头（系统保留）。
- 重命名 Schema 需要拥有该 Schema 且拥有当前数据库的 CREATE 权限。
- 更改 Owner 需要拥有该 Schema 且能 SET ROLE 到新 Owner 角色，新 Owner 必须拥有当前数据库的 CREATE 权限。
- 超级用户自动拥有所有权限。
- ALTER SCHEMA 不属于 SQL 标准（PostgreSQL 扩展）。

## 语句作用

官方说明：ALTER SCHEMA — change the definition of a schema

该 reference 关注 Schema 修改语句的语法分支、重命名语义、Owner 变更与权限边界，不负责包装所有样本到统一外层事务。

ALTER SCHEMA 是命名空间管理语句，**不涉及列类型组合**。Schema 作为纯粹的命名空间容器，其修改行为仅受名称冲突、权限与 Owner 语义影响。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（RENAME TO、OWNER TO）
- object_state：目标 Schema 对象存在性（已存在、不存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- rename_clause：RENAME TO 子句（new_simple_name、new_pg_prefix_name、new_existing_name）
- owner_clause：OWNER TO 子句（new_owner_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER）
- new_name_constraint：新名称约束（not_pg_prefix、pg_prefix_illegal）

### T3：对象名与输入形态因子
- schema_name_shape：Schema 名形态（simple、quoted、reserved_word、schema_qualified）
- new_name_shape：新名形态（simple、quoted、reserved_word、pg_prefix_reserved）
- new_owner_shape：新 Owner 名形态（existing_role、non_existing_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、schema_owner、non_owner）
- rename_privilege：重命名权限（owner_with_CREATE_on_db、owner_no_CREATE_on_db）
- owner_change_privilege：Owner 变更权限（can_SET_ROLE_to_new_owner、cannot_SET_ROLE_to_new_owner）
- new_owner_db_privilege：新 Owner 数据库权限（has_CREATE_privilege、no_CREATE_privilege）
- contained_objects_state：包含对象状态（empty_schema、schema_with_tables、schema_with_views）

### T5：异常与边界因子
- non_existent_schema：目标 Schema 不存在
- pg_prefix_new_name：新名称以 pg_ 开头（非法）
- insufficient_privilege：权限不足（非 Owner 尝试修改、Owner 无数据库 CREATE 权限、不能 SET ROLE）
- new_name_conflict：新名称与现有 Schema 冲突（RENAME 场景）
- new_owner_not_exists：新 Owner 角色不存在

### T6：验证与清理因子
- verification_mode：验证方式（pg_namespace_catalog_query、information_schema_schemata、current_schema_query）
- cleanup_mode：清理方式（DROP_SCHEMA、DROP_SCHEMA_IF_EXISTS、DROP_SCHEMA_CASCADE）

## 覆盖策略

- 必须覆盖所有两种 ALTER SCHEMA 语法分支（RENAME TO、OWNER TO）。
- ALTER SCHEMA 不涉及列类型组合，无需覆盖不同列类型的交叉组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 Schema，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 Schema 存在时的成功修改路径、目标 Schema 不存在时的失败路径。
- RENAME / OWNER TO 分支需要保持独立归因。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER SCHEMA 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- ALTER SCHEMA 不涉及列类型组合，无需覆盖不同列类型的交叉组合。
- 新名称不能以 pg_ 开头，必须作为失败边界覆盖。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限或角色限定的分支。
- T4 因子中 privilege_level 挂靠到所有分支的失败路径。
- T4 因子中 rename_privilege 和 owner_change_privilege 挂靠到对应分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - RENAME TO 和 OWNER TO 各角色指定形式代表性覆盖
  - pg_ 前缀新名称、角色依赖代表性覆盖
  - 包含对象状态代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: schema
  skill_name: alter_schema
  official_source: https://www.postgresql.org/docs/16/sql-alterschema.html
  statement:
    key: alter_schema
    name: ALTER SCHEMA
    aliases:
    - ALTER SCHEMA
    - alter schema
    - alter_schema
    purpose: change the definition of a schema
  syntax_templates:
  - "ALTER SCHEMA name RENAME TO new_name"
  - "ALTER SCHEMA name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
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
    - rename_clause
    - owner_clause
    - new_name_constraint
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - schema_name_shape
    - new_name_shape
    - new_owner_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - rename_privilege
    - owner_change_privilege
    - new_owner_db_privilege
    - contained_objects_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - non_existent_schema
    - pg_prefix_new_name
    - insufficient_privilege
    - new_name_conflict
    - new_owner_not_exists
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
      - key: branch_rename
        label: ALTER SCHEMA name RENAME TO new_name
      - key: branch_owner
        label: ALTER SCHEMA name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
    object_state:
      label: 目标Schema对象存在性
      importance: important
      values:
      - key: exists
        label: Schema已存在
      - key: not_exists
        label: Schema不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    rename_clause:
      label: RENAME TO 子句
      importance: important
      values:
      - key: new_simple_name
        label: RENAME TO 合法新名称
      - key: new_pg_prefix_name
        label: RENAME TO pg_ 前缀名称 (非法)
      - key: new_existing_name
        label: RENAME TO 已存在Schema名
    owner_clause:
      label: OWNER TO 子句
      importance: important
      values:
      - key: new_owner_role
        label: OWNER TO user_name
      - key: CURRENT_ROLE
        label: OWNER TO CURRENT_ROLE
      - key: CURRENT_USER
        label: OWNER TO CURRENT_USER
      - key: SESSION_USER
        label: OWNER TO SESSION_USER
    new_name_constraint:
      label: 新名称约束
      importance: important
      values:
      - key: not_pg_prefix
        label: 新名称不以pg_开头 (合法)
      - key: pg_prefix_illegal
        label: 新名称以pg_开头 (非法)
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
      - key: schema_qualified
        label: Schema限定标识符
    new_name_shape:
      label: 新名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: pg_prefix_reserved
        label: pg_ 前缀标识符 (非法)
    new_owner_shape:
      label: 新Owner名形态
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
      - key: schema_owner
        label: Schema Owner
      - key: non_owner
        label: 非 Owner 用户
    rename_privilege:
      label: 重命名权限
      importance: non_important
      values:
      - key: owner_with_CREATE_on_db
        label: Owner且拥有数据库CREATE权限
      - key: owner_no_CREATE_on_db
        label: Owner但无数据库CREATE权限
    owner_change_privilege:
      label: Owner变更权限
      importance: non_important
      values:
      - key: can_SET_ROLE_to_new_owner
        label: 可以SET ROLE到新Owner
      - key: cannot_SET_ROLE_to_new_owner
        label: 不能SET ROLE到新Owner
    new_owner_db_privilege:
      label: 新Owner数据库权限
      importance: non_important
      values:
      - key: has_CREATE_privilege
        label: 新Owner拥有数据库CREATE权限
      - key: no_CREATE_privilege
        label: 新Owner无数据库CREATE权限
    contained_objects_state:
      label: 包含对象状态
      importance: non_important
      values:
      - key: empty_schema
        label: 空Schema
      - key: schema_with_tables
        label: Schema包含表
      - key: schema_with_views
        label: Schema包含视图
    non_existent_schema:
      label: 目标Schema不存在
      importance: non_important
      values:
      - key: target_not_exists
        label: 目标Schema不存在 → error
    pg_prefix_new_name:
      label: 新名称pg_前缀
      importance: non_important
      values:
      - key: pg_prefix_illegal
        label: 新名称以pg_开头 → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_owner_attempt
        label: 非Owner尝试修改
      - key: owner_no_CREATE_on_db
        label: Owner无数据库CREATE权限
      - key: cannot_SET_ROLE
        label: 不能SET ROLE到新Owner
    new_name_conflict:
      label: 新名称冲突
      importance: non_important
      values:
      - key: new_name_already_exists
        label: 新名称与现有Schema冲突
    new_owner_not_exists:
      label: 新Owner不存在
      importance: non_important
      values:
      - key: specified_role_not_exists
        label: 指定的Owner角色不存在
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
    column_type_combination: ALTER SCHEMA 不涉及列类型组合，它管理命名空间而非操作列。
    namespace_management: Schema 是纯粹的命名空间容器，修改行为仅受名称冲突、权限与 Owner 语义影响。
    pg_prefix_reserved: 新 Schema 名称不能以 pg_ 开头。
    sql_standard_extension: ALTER SCHEMA 不属于 SQL 标准，是 PostgreSQL 扩展。
    rename_requires_create_privilege: RENAME 需要额外拥有数据库 CREATE 权限。
    owner_change_requires_set_role: OWNER TO 需要能 SET ROLE 到新 Owner 角色。
  defaults:
    expected_status: success
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - rename_clause
    - owner_clause
    - new_name_constraint
    - schema_name_shape
    - new_name_shape
    - new_owner_shape
    - privilege_level
    - rename_privilege
    - owner_change_privilege
    - new_owner_db_privilege
    - contained_objects_state
    - non_existent_schema
    - pg_prefix_new_name
    - insufficient_privilege
    - new_name_conflict
    - new_owner_not_exists
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER SCHEMA {schema_name} RENAME TO {new_name} | OWNER TO {new_owner}"
    verification_query_template: "SELECT count(*) FROM pg_namespace WHERE nspname = '{schema_name}'"
    factor_value_bindings:
      owner_clause:
        new_owner_role: "OWNER TO {new_owner_name}"
        CURRENT_ROLE: "OWNER TO CURRENT_ROLE"
        CURRENT_USER: "OWNER TO CURRENT_USER"
        SESSION_USER: "OWNER TO SESSION_USER"
```
