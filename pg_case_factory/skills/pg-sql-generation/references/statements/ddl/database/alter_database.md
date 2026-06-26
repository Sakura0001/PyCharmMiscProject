# 技能：ALTER DATABASE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterdatabase.html

```sql
ALTER DATABASE name [ [ WITH ] option [ ... ] ]

where option can be:
    ALLOW_CONNECTIONS allowconn
    CONNECTION LIMIT connlimit
    IS_TEMPLATE istemplate

ALTER DATABASE name RENAME TO new_name

ALTER DATABASE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }

ALTER DATABASE name SET TABLESPACE new_tablespace

ALTER DATABASE name REFRESH COLLATION VERSION

ALTER DATABASE name SET configuration_parameter { TO | = } { value | DEFAULT }
ALTER DATABASE name SET configuration_parameter FROM CURRENT
ALTER DATABASE name RESET configuration_parameter
ALTER DATABASE name RESET ALL
```

PG16 关键约束：
- WITH 选项（ALLOW_CONNECTIONS/CONNECTION LIMIT/IS_TEMPLATE）：需要 database owner 或 superuser
- RENAME TO：需要 database owner 或 superuser；非 superuser owner 还必须有 CREATEDB 权限；不能重命名当前连接的数据库
- OWNER TO：必须能 SET ROLE 到新拥有角色且必须有 CREATEDB 权限（superuser 自动满足）
- SET TABLESPACE：需要 database owner 或 superuser 且必须对新 tablespace 有 create 权限；新默认 tablespace 必须对该数据库为空；期间不能有任何人连接到该数据库；不能在事务块内执行；物理移动表/索引从旧默认 tablespace 到新 tablespace
- REFRESH COLLATION VERSION：需要 database owner 或 superuser
- SET/RESET configuration_parameter：需要 database owner 或 superuser；部分变量仅 superuser 可设置
- ALLOW_CONNECTIONS false 禁止任何连接
- CONNECTION LIMIT -1 表示无限制
- IS_TEMPLATE true 时任何 CREATEDB 用户可克隆；false 时仅 superuser/owner 可克隆
- 数据库级配置参数覆盖 postgresql.conf 和命令行设置
- SET FROM CURRENT 保存当前会话参数值作为数据库级默认值
- RESET（或 SET ... TO DEFAULT）移除数据库级设置，恢复系统默认值
- 角色级设置覆盖数据库级设置（如有冲突）

## 语句作用

官方说明：ALTER DATABASE — change a database

该 reference 关注数据库对象的元数据变更。ALTER DATABASE 有 9 种独立语法分支，涉及连接属性、重命名、owner 变更、tablespace 移动、collation 版本刷新和配置参数设置/重置。该语句不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（WITH 选项 / RENAME TO / OWNER TO / SET TABLESPACE / REFRESH COLLATION VERSION / SET parameter / SET FROM CURRENT / RESET parameter / RESET ALL）
- object_state：目标 database 对象状态（exists / not_exists / is_current_database）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- privilege_level：执行权限（superuser / database_owner / non_owner）
- with_option_type：WITH 选项类型（ALLOW_CONNECTIONS / CONNECTION LIMIT / IS_TEMPLATE / 组合）
- new_owner_target：OWNER TO 的目标形式（existing_role / nonexistent_role / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- rename_conflict：RENAME TO 目标名称状态（new_name_unique / new_name_exists）
- config_parameter_type：配置参数类型（superuser_only / owner_settable / common_parameter）

### T3：对象名与输入形态因子
- database_name_shape：database 名称形态
- new_name_shape：新名称形态（仅 RENAME TO）
- new_owner_shape：目标 owner 名称形态（仅 OWNER TO）
- new_tablespace_shape：新 tablespace 名称形态（仅 SET TABLESPACE）
- config_parameter_name_shape：配置参数名称形态（仅 SET/RESET）

### T4：依赖对象与环境因子
- tablespace_existence：tablespace 存在性（仅 SET TABLESPACE）
- tablespace_privilege：tablespace create 权限（仅 SET TABLESPACE）
- target_database_connection_state：目标数据库连接状态（无连接 / 有连接 / 当前连接）
- role_set_role_ability：SET ROLE 能力（仅 OWNER TO）
- role_createdb_privilege：CREATEDB 权限（仅 OWNER TO / RENAME TO）

### T5：异常与边界因子
- database_not_exist：目标 database 不存在
- rename_current_database：重命名当前连接的数据库
- rename_target_conflict：RENAME TO 新名称已存在
- owner_not_exist：OWNER TO 目标角色不存在
- tablespace_not_exist：SET TABLESPACE 新 tablespace 不存在
- tablespace_has_connections：SET TABLESPACE 时有连接到目标数据库
- privilege_denied：非 owner/superuser 尝试修改
- cannot_set_role：无法 SET ROLE 到新 owner
- lacks_createdb_privilege：缺少 CREATEDB 权限（RENAME TO / OWNER TO）
- set_tablespace_in_transaction：SET TABLESPACE 在事务块内执行
- config_parameter_superuser_only：非 superuser 设置 superuser-only 参数

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 ALTER DATABASE 9 种语法分支。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖；statement_branch 跨 9 个分支。
- T2 因子按分支适用性参与组合：
  - with_option_type 仅挂靠到 WITH 选项分支。
  - new_owner_target 仅挂靠到 OWNER TO 分支。
  - rename_conflict 仅挂靠到 RENAME TO 分支。
  - config_parameter_type 仅挂靠到 SET/RESET 分支。
  - privilege_level 覆盖所有分支。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标数据库。
- RENAME TO 不能重命名当前连接的数据库，样本必须连接到不同数据库后执行。
- SET TABLESPACE 期间不能有连接到目标数据库，不能在事务块内执行。
- OWNER TO 必须能 SET ROLE 到新 owner 且有 CREATEDB 权限。
- 每个分支至少生成一个成功路径和一个失败路径样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER DATABASE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 配置参数 SET/RESET 样本必须覆盖常见参数（如 search_path、enable_indexscan）和 superuser-only 参数（如 wal_level）。

## 挂靠规则

- with_option_type 挂靠到 WITH 选项分支的代表性样本。
- new_owner_target 仅挂到 OWNER TO 分支。
- rename_conflict 仅挂到 RENAME TO 分支。
- config_parameter_type 仅挂到 SET/RESET 分支。
- privilege_denied 覆盖所有分支各至少一个样本。
- SET TABLESPACE 的连接状态和事务限制仅挂到 SET TABLESPACE 分支。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏语句分支和成功/失败归因的可识别性。

## 规模控制规则

- 优先保证：
  - 9 个语法分支全覆盖
  - superuser/owner/non_owner 权限路径全覆盖
  - database 存在/不存在/当前连接状态全覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - CURRENT_ROLE/CURRENT_USER/SESSION_USER 目标 owner 形式覆盖
  - 代表性配置参数覆盖（common/superuser-only）
  - WITH 选项组合覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: database
  skill_name: alter_database
  official_source: https://www.postgresql.org/docs/16/sql-alterdatabase.html
  statement:
    key: alter_database
    name: ALTER DATABASE
    aliases:
    - alter_database
    - ALTER DATABASE
    purpose: ALTER DATABASE — change a database
  syntax_templates:
  - "ALTER DATABASE name [ [ WITH ] option [ ... ] ]\nwhere option can be:\n    ALLOW_CONNECTIONS\
    \ allowconn\n    CONNECTION LIMIT connlimit\n    IS_TEMPLATE istemplate"
  - "ALTER DATABASE name RENAME TO new_name"
  - "ALTER DATABASE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER\
    \ }"
  - "ALTER DATABASE name SET TABLESPACE new_tablespace"
  - "ALTER DATABASE name REFRESH COLLATION VERSION"
  - "ALTER DATABASE name SET configuration_parameter { TO | = } { value | DEFAULT\
    \ }"
  - "ALTER DATABASE name SET configuration_parameter FROM CURRENT"
  - "ALTER DATABASE name RESET configuration_parameter"
  - "ALTER DATABASE name RESET ALL"
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
    - privilege_level
    - with_option_type
    - new_owner_target
    - rename_conflict
    - config_parameter_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - database_name_shape
    - new_name_shape
    - new_owner_shape
    - new_tablespace_shape
    - config_parameter_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - tablespace_existence
    - tablespace_privilege
    - target_database_connection_state
    - role_set_role_ability
    - role_createdb_privilege
  - tier: T5
    name: 异常与边界因子
    factors:
    - database_not_exist
    - rename_current_database
    - rename_target_conflict
    - owner_not_exist
    - tablespace_not_exist
    - tablespace_has_connections
    - privilege_denied
    - cannot_set_role
    - lacks_createdb_privilege
    - set_tablespace_in_transaction
    - config_parameter_superuser_only
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
      - key: branch_with_options
        label: ALTER DATABASE name [ [ WITH ] option [ ... ] ]
      - key: branch_rename
        label: ALTER DATABASE name RENAME TO new_name
      - key: branch_owner
        label: ALTER DATABASE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_set_tablespace
        label: ALTER DATABASE name SET TABLESPACE new_tablespace
      - key: branch_refresh_collation_version
        label: ALTER DATABASE name REFRESH COLLATION VERSION
      - key: branch_set_parameter
        label: ALTER DATABASE name SET configuration_parameter { TO | = } { value | DEFAULT }
      - key: branch_set_from_current
        label: ALTER DATABASE name SET configuration_parameter FROM CURRENT
      - key: branch_reset_parameter
        label: ALTER DATABASE name RESET configuration_parameter
      - key: branch_reset_all
        label: ALTER DATABASE name RESET ALL
    object_state:
      label: 目标 database 对象状态
      importance: important
      values:
      - exists
      - not_exists
      - is_current_database
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - database_owner
      - non_owner
    with_option_type:
      label: WITH 选项类型
      importance: non_important
      values:
      - allow_connections_true
      - allow_connections_false
      - connection_limit_positive
      - connection_limit_negative_one
      - is_template_true
      - is_template_false
      - multiple_options_combined
    new_owner_target:
      label: OWNER TO 目标形式
      importance: non_important
      values:
      - existing_role
      - nonexistent_role
      - CURRENT_ROLE
      - CURRENT_USER
      - SESSION_USER
    rename_conflict:
      label: RENAME TO 目标名称状态
      importance: non_important
      values:
      - new_name_unique
      - new_name_exists
    config_parameter_type:
      label: 配置参数类型
      importance: non_important
      values:
      - common_parameter
      - superuser_only_parameter
      - search_path
      - enable_indexscan
    database_name_shape:
      label: database 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_name
    new_name_shape:
      label: 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_as_name
    new_owner_shape:
      label: 目标 owner 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - special_token
    new_tablespace_shape:
      label: 新 tablespace 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_name
    config_parameter_name_shape:
      label: 配置参数名称形态
      importance: non_important
      values:
      - standard_parameter_name
      - superuser_only_name
    tablespace_existence:
      label: tablespace 存在性
      importance: non_important
      values:
      - tablespace_exists
      - tablespace_not_exists
    tablespace_privilege:
      label: tablespace create 权限
      importance: non_important
      values:
      - has_create_privilege
      - lacks_create_privilege
    target_database_connection_state:
      label: 目标数据库连接状态
      importance: non_important
      values:
      - no_connections
      - has_connections
      - is_current_database
    role_set_role_ability:
      label: SET ROLE 能力
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role
    role_createdb_privilege:
      label: CREATEDB 权限
      importance: non_important
      values:
      - has_createdb
      - lacks_createdb
    database_not_exist:
      label: 目标 database 不存在
      importance: non_important
      values:
      - database_exists
      - database_not_exists
    rename_current_database:
      label: 重命名当前连接的数据库
      importance: non_important
      values:
      - different_database
      - current_database
    rename_target_conflict:
      label: RENAME 目标名称已存在
      importance: non_important
      values:
      - no_conflict
      - name_already_exists
    owner_not_exist:
      label: OWNER TO 目标角色不存在
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    tablespace_not_exist:
      label: SET TABLESPACE 新 tablespace 不存在
      importance: non_important
      values:
      - tablespace_exists
      - tablespace_not_exists
    tablespace_has_connections:
      label: SET TABLESPACE 时有连接
      importance: non_important
      values:
      - no_connections
      - has_connections
    privilege_denied:
      label: 非 owner/superuser 尝试修改
      importance: non_important
      values:
      - owner_or_superuser_success
      - non_owner_failure
    cannot_set_role:
      label: 无法 SET ROLE 到新 owner
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role
    lacks_createdb_privilege:
      label: 缺少 CREATEDB 权限
      importance: non_important
      values:
      - has_createdb
      - lacks_createdb
    set_tablespace_in_transaction:
      label: SET TABLESPACE 在事务块内
      importance: non_important
      values:
      - outside_transaction
      - inside_transaction
    config_parameter_superuser_only:
      label: 非 superuser 设置 superuser-only 参数
      importance: non_important
      values:
      - superuser_setting_superuser_param
      - non_superuser_setting_superuser_param_failure
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_database
      - catalog_query_pg_db_role_setting
      - connect_verify
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_database
      - reset_config_parameter
      - force_drop_database
  defaults:
    expected_status: success
    statement_branch: branch_with_options
    object_state: exists
    privilege_level: superuser
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - privilege_level
    - with_option_type
    - new_owner_target
    - rename_conflict
    - config_parameter_type
    - database_name_shape
    - new_name_shape
    - new_owner_shape
    - new_tablespace_shape
    - config_parameter_name_shape
    - tablespace_existence
    - tablespace_privilege
    - target_database_connection_state
    - role_set_role_ability
    - role_createdb_privilege
    - database_not_exist
    - rename_current_database
    - rename_target_conflict
    - owner_not_exist
    - tablespace_not_exist
    - tablespace_has_connections
    - privilege_denied
    - cannot_set_role
    - lacks_createdb_privilege
    - set_tablespace_in_transaction
    - config_parameter_superuser_only
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
  factor_catalog_mapping:
    source_catalog: references/common/pg16_factor_catalog.md
    object_domain: database
    imported_factors:
    - catalog_factor: database.naming.name_shape
      local_factor: database_name_shape
      target_tier: T3
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - valid_unquoted_lower
      - valid_quoted_upper
      - quoted_reserved_keyword
      reason: ALTER DATABASE 需要覆盖目标 database 名称输入形态。
    - catalog_factor: database.naming.name_shape
      local_factor: new_name_shape
      target_tier: T3
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - valid_unquoted_lower
      - valid_quoted_upper
      - quoted_reserved_keyword
      reason: RENAME TO 分支需要覆盖新名称形态。
    - catalog_factor: database.options.allow_connections
      local_factor: with_option_type
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - "true"
      - "false"
      reason: ALTER DATABASE WITH 选项可修改 ALLOW_CONNECTIONS。
    - catalog_factor: database.options.connection_limit
      local_factor: with_option_type
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: ALTER DATABASE WITH 选项可修改 CONNECTION LIMIT。
    - catalog_factor: database.options.is_template
      local_factor: with_option_type
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: ALTER DATABASE WITH 选项可修改 IS_TEMPLATE。
    - catalog_factor: database.options.owner
      local_factor: new_owner_target
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - valid_other_role
      - nonexistent_user
      - no_set_role_privilege
      reason: OWNER TO 分支需要覆盖新 owner 和权限边界。
    - catalog_factor: database.options.tablespace
      local_factor: new_tablespace_shape
      target_tier: T3
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - valid_tablespace
      - nonexistent_tablespace
      reason: SET TABLESPACE 分支需要覆盖新表空间名称形态。
    - catalog_factor: database.options.config_parameter
      local_factor: config_parameter_type
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: ALTER DATABASE SET/RESET 分支需要覆盖普通参数和 superuser-only 参数。
    - catalog_factor: database.environment.tablespace_existence
      local_factor: tablespace_existence
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: SET TABLESPACE 需要验证表空间存在性。
    - catalog_factor: database.environment.connection_state
      local_factor: target_database_connection_state
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: RENAME 和 SET TABLESPACE 受目标数据库连接状态影响。
    - catalog_factor: database.environment.role_set_role_ability
      local_factor: role_set_role_ability
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: OWNER TO 需要验证 SET ROLE 能力。
    - catalog_factor: database.environment.privilege_level
      local_factor: role_createdb_privilege
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - createdb_role
      - non_owner
      reason: SET TABLESPACE 和部分 ALTER DATABASE 操作依赖 CREATEDB 或 owner 权限。
    - catalog_factor: database.boundary.duplicate_name
      local_factor: rename_target_conflict
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: RENAME TO 分支需要覆盖目标名称冲突。
    - catalog_factor: database.boundary.privilege_denied
      local_factor: privilege_denied
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 非 owner 或权限不足路径需要单独覆盖。
    - catalog_factor: database.boundary.inside_transaction
      local_factor: set_tablespace_in_transaction
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: SET TABLESPACE 不能在事务块内执行。
    - catalog_factor: database.validation.catalog_check
      local_factor: verification_mode
      target_tier: T6
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - pg_database_presence
      - error_assertion
      reason: ALTER DATABASE 需要通过 pg_database、pg_db_role_setting 或错误断言验证。
    excluded_factors:
    - catalog_factor: database.options.template
      reason: ALTER DATABASE 官方语法不修改 TEMPLATE。
    - catalog_factor: database.options.encoding
      reason: ALTER DATABASE 官方语法不修改 ENCODING。
    - catalog_factor: database.operation.if_exists
      reason: ALTER DATABASE 官方语法没有 IF EXISTS。
    - catalog_factor: database.operation.force
      reason: ALTER DATABASE 官方语法没有 WITH FORCE。
    coverage_notes:
    - 多个全局 database.options 因子映射到 with_option_type，因为现有 reference 已把 WITH 选项收敛为一个局部因子。
  rendering:
    statement_template: "ALTER DATABASE {database_name} {alter_action}"
    verification_query_template: "SELECT datname, datallowconn, datconnlimit, datistemplate\
      \ FROM pg_database WHERE datname = '{database_name}'"
    factor_value_bindings: {}
```
