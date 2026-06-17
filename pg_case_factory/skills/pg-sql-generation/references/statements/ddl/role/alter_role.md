# 技能：ALTER ROLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterrole.html

```sql
ALTER ROLE role_specification [ WITH ] option [ ... ]

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

ALTER ROLE name RENAME TO new_name

ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter { TO | = } { value | DEFAULT }
ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter FROM CURRENT
ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] RESET configuration_parameter
ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] RESET ALL

where role_specification can be:

    role_name
  | CURRENT_ROLE
  | CURRENT_USER
  | SESSION_USER
```

## 语句作用

官方说明：ALTER ROLE — change a database role

该 reference 关注角色属性修改、角色重命名、角色级别配置参数设定与重置的行为、权限边界和错误归因。ALTER ROLE 不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- role_state：目标角色对象存在状态
- expected_status：预期结果

### T2：重要行为因子
- attribute_option：角色属性选项
- rename_behavior：RENAME 行为
- config_parameter_behavior：配置参数设定行为
- privilege_level：执行用户权限级别

### T3：对象名与输入形态因子
- role_name_shape：角色标识符形态
- new_name_shape：新角色名形态（RENAME 分支）
- config_parameter_shape：配置参数名形态
- database_name_shape：数据库名形态（IN DATABASE 子句）

### T4：依赖对象与环境因子
- table_column_index_involvement：表/列/索引参与（ALTER ROLE 不涉及）
- privilege_requirement：权限需求
- config_parameter_dependency：配置参数依赖
- role_membership_dependency：角色成员关系依赖

### T5：异常与边界因子
- nonexistent_role：角色不存在
- privilege_insufficient：权限不足
- invalid_config_parameter：非法配置参数
- rename_current_session_user：重命名当前会话用户
- rename_clears_password：重命名清除 MD5 密码
- password_security：密码安全风险

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 ALTER ROLE 语法分支（6 个官方 synopsis 分支）。
- 不需要覆盖所有基表，ALTER ROLE 不涉及表/列/索引组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须预创建可被修改的目标角色对象，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标角色存在时的成功修改路径、目标角色不存在时的失败路径。
- RENAME、SET、RESET、FROM CURRENT、DEFAULT、ALL 各分支需要保持独立归因。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置角色准备、目标 ALTER ROLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser 或 CREATEROLE 权限的分支，必须在生命周期计划中显式标注环境依赖。
- ALTER ROLE 不能修改角色成员关系（成员关系由 GRANT/REVOKE 管理），不得将成员关系变更伪装为 ALTER ROLE 行为。
- 重命名角色会清除 MD5 加密密码，失败样本需覆盖此边界。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文、配置参数依赖或角色成员关系的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、角色状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（6 个官方 synopsis 分支）
  - 目标角色存在/不存在/冲突/非法输入全覆盖
  - 成功/失败路径全覆盖
  - 权限核心路径全覆盖（superuser、CREATEROLE、普通角色）
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖（WITH、ENCRYPTED、DEFAULT、NULL、FROM CURRENT、ALL、IN DATABASE）
  - 角色属性选项代表性覆盖（每个属性至少出现一次）
  - 配置参数依赖代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: role
  skill_name: alter_role
  official_source: https://www.postgresql.org/docs/16/sql-alterrole.html
  statement:
    key: alter_role
    name: ALTER ROLE
    aliases:
    - alter_role
    - ALTER ROLE
    purpose: ALTER ROLE — change a database role
  syntax_templates:
  - "ALTER ROLE role_specification [ WITH ] option [ ... ]\n\nwhere option can\
    \ be:\n\n      SUPERUSER | NOSUPERUSER\n    | CREATEDB | NOCREATEDB\n    | CREATEROLE\
    \ | NOCREATEROLE\n    | INHERIT | NOINHERIT\n    | LOGIN | NOLOGIN\n    | REPLICATION\
    \ | NOREPLICATION\n    | BYPASSRLS | NOBYPASSRLS\n    | CONNECTION LIMIT connlimit\n\
    \    | [ ENCRYPTED ] PASSWORD 'password' | PASSWORD NULL\n    | VALID UNTIL 'timestamp'"
  - "ALTER ROLE name RENAME TO new_name"
  - "ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter\
    \ { TO | = } { value | DEFAULT }"
  - "ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter\
    \ FROM CURRENT"
  - "ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] RESET\
    \ configuration_parameter"
  - "ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] RESET\
    \ ALL"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - role_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - attribute_option
    - rename_behavior
    - config_parameter_behavior
    - privilege_level
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - role_name_shape
    - new_name_shape
    - config_parameter_shape
    - database_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - table_column_index_involvement
    - privilege_requirement
    - config_parameter_dependency
    - role_membership_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_role
    - privilege_insufficient
    - invalid_config_parameter
    - rename_current_session_user
    - rename_clears_password
    - password_security
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
      - key: branch_1_with_option
        label: ALTER ROLE role_specification [ WITH ] option [ ... ] — 属性变更
      - key: branch_2_rename
        label: ALTER ROLE name RENAME TO new_name — 重命名
      - key: branch_3_set_value
        label: ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter { TO | = } { value | DEFAULT }
      - key: branch_4_set_from_current
        label: ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter FROM CURRENT
      - key: branch_5_reset_parameter
        label: ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] RESET configuration_parameter
      - key: branch_6_reset_all
        label: ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] RESET ALL
    role_state:
      label: 目标角色对象存在状态
      importance: important
      values:
      - exists
      - non_existent
      - reserved_word_name
      - quoted_name
      - current_session_user
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    attribute_option:
      label: 角色属性选项
      importance: non_important
      values:
      - superuser
      - nosuperuser
      - createdb
      - nocreatedb
      - createrole
      - nocreaterole
      - inherit
      - noinherit
      - login
      - nologin
      - replication
      - noreplication
      - bypassrls
      - nobypassrls
      - connection_limit
      - encrypted_password
      - password_null
      - valid_until
    rename_behavior:
      label: RENAME 行为
      importance: non_important
      values:
      - rename_to_new_name
      - rename_reserved_word
      - rename_current_user_blocked
    config_parameter_behavior:
      label: 配置参数设定行为
      importance: non_important
      values:
      - set_value
      - set_default
      - set_from_current
      - reset_parameter
      - reset_all
      - all_roles
      - in_database_specific
    privilege_level:
      label: 执行用户权限级别
      importance: non_important
      values:
      - superuser
      - createrole_with_admin_option
      - createrole_without_admin_option
      - ordinary_role_self
      - ordinary_role_other
    role_name_shape:
      label: 角色标识符形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - current_role_keyword
      - current_user_keyword
      - session_user_keyword
      - all_keyword
      - non_existent_name
      - reserved_word_name
    new_name_shape:
      label: 新角色名形态（RENAME 分支）
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - existing_name_conflict
      - reserved_word_name
      - non_existent_name
    config_parameter_shape:
      label: 配置参数名形态
      importance: non_important
      values:
      - valid_parameter
      - superuser_only_parameter
      - invalid_parameter
    database_name_shape:
      label: 数据库名形态（IN DATABASE 子句）
      importance: non_important
      values:
      - existing_database
      - non_existent_database
      - omitted_no_database_clause
    table_column_index_involvement:
      label: 表/列/索引参与
      importance: non_important
      values:
      - not_involved
    privilege_requirement:
      label: 权限需求
      importance: non_important
      values:
      - superuser_required
      - createrole_with_admin_option_required
      - self_password_only
      - all_roles_requires_superuser
    config_parameter_dependency:
      label: 配置参数依赖
      importance: non_important
      values:
      - settable_by_any_role
      - settable_only_by_superuser
      - cannot_be_set_at_role_level
    role_membership_dependency:
      label: 角色成员关系依赖
      importance: non_important
      values:
      - admin_option_granted
      - admin_option_not_granted
      - role_is_member_of_another
    nonexistent_role:
      label: 角色不存在
      importance: non_important
      values:
      - role_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - ordinary_role_altering_other_role_attributes
      - createrole_altering_superuser
      - createrole_without_admin_option
      - ordinary_role_altering_other_role_config
    invalid_config_parameter:
      label: 非法配置参数
      importance: non_important
      values:
      - superuser_only_parameter_by_non_superuser
      - parameter_cannot_be_set_at_role_level
      - invalid_parameter_name
    rename_current_session_user:
      label: 重命名当前会话用户
      importance: non_important
      values:
      - session_user_rename_blocked
    rename_clears_password:
      label: 重命名清除 MD5 密码
      importance: non_important
      values:
      - md5_password_cleared_on_rename
      - scram_password_preserved_on_rename
    password_security:
      label: 密码安全风险
      importance: non_important
      values:
      - plaintext_password_in_sql
      - password_null_removes_password
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_roles_catalog
      - pg_settings_catalog
      - pg_authid_catalog
      - effect_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - reset_config_parameter
      - drop_role
      - revert_attribute_change
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - role_state
    - expected_status
    non_main_factors:
    - attribute_option
    - rename_behavior
    - config_parameter_behavior
    - privilege_level
    - role_name_shape
    - new_name_shape
    - config_parameter_shape
    - database_name_shape
    - table_column_index_involvement
    - privilege_requirement
    - config_parameter_dependency
    - role_membership_dependency
    - nonexistent_role
    - privilege_insufficient
    - invalid_config_parameter
    - rename_current_session_user
    - rename_clears_password
    - password_security
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - role_state
  rendering:
    statement_template: ALTER ROLE role_specification [ WITH ] option [ ... ] | ALTER ROLE name RENAME TO new_name | ALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET/RESET configuration_parameter
    verification_query_template: SELECT * FROM pg_roles WHERE rolname = 'role_name'; SELECT * FROM pg_settings WHERE name = 'configuration_parameter';
    factor_value_bindings: {}
```
