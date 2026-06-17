# 技能：ALTER USER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alteruser.html

```sql
ALTER USER role_specification [ WITH ] option [ ... ]

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

ALTER USER name RENAME TO new_name

ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter { TO | = } { value | DEFAULT }
ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter FROM CURRENT
ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] RESET configuration_parameter
ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] RESET ALL

where role_specification can be:

    role_name
  | CURRENT_ROLE
  | CURRENT_USER
  | SESSION_USER
```

PG16 关键约束：
- **ALTER USER 是 ALTER ROLE 的已弃用别名（deprecated alias）**，行为完全一致
- ALTER USER 选项形式要求执行者拥有 CREATEROLE 权限（修改自身密码除外）
- ALTER USER RENAME TO 要求执行者拥有 CREATEROLE 权限
- ALTER USER SET/RESET 配置参数要求执行者拥有指定角色的所有权（或 superuser）
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：ALTER USER — change a database role

**重要提示：ALTER USER 是 ALTER ROLE 的已弃用别名（deprecated alias）。所有行为与 ALTER ROLE 一致。**

该 reference 关注角色属性修改、重命名、配置参数设置和权限边界，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（option 形式 / RENAME TO / SET config / SET FROM CURRENT / RESET / RESET ALL）
- object_state：目标 role 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（option_modify / rename / set_config / set_from_current / reset_config / reset_all）
- role_specification：角色指定形态（role_name / CURRENT_ROLE / CURRENT_USER / SESSION_USER / ALL）
- in_database_clause：IN DATABASE 子句形态（省略 / 指定）
- option_type：选项类型（SUPERUSER / CREATEDB / CREATEROLE / INHERIT / LOGIN / REPLICATION / BYPASSRLS / CONNECTION LIMIT / PASSWORD / VALID UNTIL）

### T3：对象名与输入形态因子
- role_name_shape：角色名称形态
- new_name_shape：RENAME TO 新名称形态
- database_name_shape：IN DATABASE 名称形态
- config_param_shape：配置参数名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（CREATEROLE / superuser / role_owner / non_owner / non_createrole）
- database_existence：IN DATABASE 指定的数据库存在性（存在 / 不存在）

### T5：异常与边界因子
- nonexistent_role：目标角色不存在
- duplicate_new_name：RENAME TO 新名称与已有角色重名
- nonexistent_database：IN DATABASE 指定的数据库不存在
- insufficient_privilege：缺少 CREATEROLE 权限或角色所有权
- superuser_modification_by_non_superuser：非 superuser 尝试修改 SUPERUSER 属性

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER USER 六个语法分支中的所有行为路径。
- 覆盖目标角色存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 CREATEROLE 权限边界。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER USER 是 ALTER ROLE 的已弃用别名，必须在每个样本中显式标注此关系。
- ALTER USER 选项形式要求 CREATEROLE 权限；修改自身密码除外。
- ALTER USER RENAME TO 要求 CREATEROLE 权限。
- ALTER USER SET/RESET 配置参数要求角色所有权（或 superuser）。
- ALTER USER 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER USER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 CREATEROLE 权限相关的因子必须挂靠到具有明确权限上下文的样本上。
- SET/RESET 分支的 IN DATABASE 因子必须挂靠到对应分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 role_specification 形态、IN DATABASE 子句和配置参数代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: user
  skill_name: alter_user
  official_source: https://www.postgresql.org/docs/16/sql-alteruser.html
  statement:
    key: alter_user
    name: ALTER USER
    aliases:
    - alter_user
    - ALTER USER
    - alter_role
    - ALTER ROLE
    purpose: ALTER USER — change a database role (deprecated alias for ALTER ROLE)
  syntax_templates:
  - "ALTER USER role_specification [ WITH ] option [ ... ]"
  - "ALTER USER name RENAME TO new_name"
  - "ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter { TO | = } { value | DEFAULT }"
  - "ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter FROM CURRENT"
  - "ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] RESET configuration_parameter"
  - "ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] RESET ALL"
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
    - in_database_clause
    - option_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - role_name_shape
    - new_name_shape
    - database_name_shape
    - config_param_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - database_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_role
    - duplicate_new_name
    - nonexistent_database
    - insufficient_privilege
    - superuser_modification_by_non_superuser
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
      - key: branch_option
        label: ALTER USER role_specification [ WITH ] option [ ... ]
      - key: branch_rename
        label: ALTER USER name RENAME TO new_name
      - key: branch_set_config
        label: ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter { TO | = } { value | DEFAULT }
      - key: branch_set_from_current
        label: ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter FROM CURRENT
      - key: branch_reset_config
        label: ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] RESET configuration_parameter
      - key: branch_reset_all
        label: ALTER USER { role_specification | ALL } [ IN DATABASE database_name ] RESET ALL
    object_state:
      label: 目标 role 对象状态
      importance: important
      values:
      - exists
      - not_exists
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
      - option_modify
      - rename
      - set_config
      - set_from_current
      - reset_config
      - reset_all
    role_specification:
      label: 角色指定形态
      importance: non_important
      values:
      - named_role
      - current_role
      - current_user
      - session_user
      - all
    in_database_clause:
      label: IN DATABASE 子句形态
      importance: non_important
      values:
      - omitted
      - specified
    option_type:
      label: 选项类型
      importance: non_important
      values:
      - superuser_toggle
      - createdb_toggle
      - createrole_toggle
      - inherit_toggle
      - login_toggle
      - replication_toggle
      - bypassrls_toggle
      - connection_limit
      - password
      - password_null
      - valid_until
    role_name_shape:
      label: 角色名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_name
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - duplicate_name
    database_name_shape:
      label: IN DATABASE 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_name
    config_param_shape:
      label: 配置参数名称形态
      importance: non_important
      values:
      - valid_param
      - invalid_param
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - createrole
      - superuser
      - role_owner
      - non_owner
      - non_createrole
    database_existence:
      label: IN DATABASE 指定的数据库存在性
      importance: non_important
      values:
      - database_exists
      - database_not_exists
    nonexistent_role:
      label: 目标角色不存在
      importance: non_important
      values:
      - role_exists
      - role_missing
    duplicate_new_name:
      label: RENAME TO 新名称与已有角色重名
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    nonexistent_database:
      label: IN DATABASE 指定的数据库不存在
      importance: non_important
      values:
      - database_exists
      - database_missing
    insufficient_privilege:
      label: 缺少 CREATEROLE 权限或角色所有权
      importance: non_important
      values:
      - has_privilege
      - lacks_createrole
      - lacks_role_ownership
    superuser_modification_by_non_superuser:
      label: 非 superuser 尝试修改 SUPERUSER 属性
      importance: non_important
      values:
      - superuser_execution
      - non_superuser_attempting_superuser_toggle
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_roles
      - config_parameter_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - revert_option
      - revert_rename
      - reset_config
      - drop_role
  defaults:
    expected_status: success
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - role_specification
    - in_database_clause
    - option_type
    - role_name_shape
    - new_name_shape
    - database_name_shape
    - config_param_shape
    - privilege_level
    - database_existence
    - nonexistent_role
    - duplicate_new_name
    - nonexistent_database
    - insufficient_privilege
    - superuser_modification_by_non_superuser
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER USER {role_spec} {alter_clause}"
    verification_query_template: "SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = '{role_name}'"
    factor_value_bindings: {}
```
