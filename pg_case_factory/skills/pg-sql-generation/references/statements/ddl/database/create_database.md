# 技能：CREATE DATABASE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createdatabase.html

```sql
CREATE DATABASE name
    [ WITH ] [ OWNER [=] user_name ]
           [ TEMPLATE [=] template ]
           [ ENCODING [=] encoding ]
           [ STRATEGY [=] strategy ]
           [ LOCALE [=] locale ]
           [ LC_COLLATE [=] lc_collate ]
           [ LC_CTYPE [=] lc_ctype ]
           [ ICU_LOCALE [=] icu_locale ]
           [ ICU_RULES [=] icu_rules ]
           [ LOCALE_PROVIDER [=] locale_provider ]
           [ COLLATION_VERSION = collation_version ]
           [ TABLESPACE [=] tablespace_name ]
           [ ALLOW_CONNECTIONS [=] allowconn ]
           [ CONNECTION LIMIT [=] connlimit ]
           [ IS_TEMPLATE [=] istemplate ]
           [ OID [=] oid ]
```

PG16 关键约束：
- 需要 superuser 或 CREATEDB 权限
- 要创建由其他角色拥有的数据库，必须能够 SET ROLE 到该角色
- 不能在事务块内执行
- 模板数据库在复制期间不能有其他连接；CREATE DATABASE 失败如果有其他连接到模板数据库
- 编码必须与 LC_COLLATE/LC_CTYPE 兼容；locale C/POSIX 允许所有编码，其他 locale 仅允许一种编码（Windows 上 UTF8 除外）
- 编码和 locale 必须与模板数据库匹配，除非使用 template0
- STRATEGY 选项：WAL_LOG（默认，逐块复制）或 FILE_COPY（文件系统级复制，强制 checkpoint）
- CONNECTION LIMIT 仅约略执行，不对 superuser 或后台 worker 生效
- ALLOW_CONNECTIONS 为 false 时禁止任何连接
- IS_TEMPLATE 为 true 时任何 CREATEDB 用户可克隆；为 false 时仅 superuser/owner 可克隆
- OID 选项通常仅 pg_upgrade 使用；小于 16384 的值只允许 pg_upgrade
- 数据库级配置参数和权限不从模板复制

## 语句作用

官方说明：CREATE DATABASE — create a new database

该 reference 关注数据库对象的创建。CREATE DATABASE 涉及编码/locale/模板选择、WITH 选项组合、权限边界和命名约束。该语句不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE DATABASE name [ WITH ] ... 单一顶层形式）
- object_state：目标 database 对象状态（not_exists / exists）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- owner_clause：OWNER 子句形态（省略 / 指定 user_name / 指定 other_role）
- template_clause：TEMPLATE 子句形态（省略默认 template1 / 指定 template0 / 指定其他模板）
- encoding_clause：ENCODING 子句形态（省略 / 指定 UTF8 / 指定 LATIN1 / 指定 SQL_ASCII）
- locale_clause：LOCALE 子句形态（省略 / 指定 locale / 指定 C / 指定 POSIX）
- strategy_clause：STRATEGY 子句形态（省略默认 WAL_LOG / 指定 WAL_LOG / 指定 FILE_COPY）
- privilege_level：执行权限（superuser / createdb_role / non_createdb_role）

### T3：对象名与输入形态因子
- database_name_shape：database 名称形态
- owner_name_shape：owner 名称形态
- tablespace_name_shape：tablespace 名称形态

### T4：依赖对象与环境因子
- template_existence：模板数据库存在性及连接状态（template 存在无连接 / template 存在有连接 / template 不存在）
- encoding_locale_compatibility：编码与 locale 兼容性（兼容 / 不兼容）
- role_set_role_ability：SET ROLE 能力（能 SET ROLE / 不能 SET ROLE）
- tablespace_existence：tablespace 存在性（存在 / 不存在）

### T5：异常与边界因子
- duplicate_database_name：重名冲突
- privilege_denied：缺少 CREATEDB 权限
- cannot_set_role_to_owner：无法 SET ROLE 到指定 owner
- template_has_connections：模板数据库有其他连接
- encoding_locale_incompatible：编码与 locale 不兼容
- encoding_template_mismatch：编码与模板不匹配且未使用 template0
- nonexistent_template：模板不存在
- nonexistent_tablespace：tablespace 不存在
- inside_transaction_block：在事务块内执行

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE DATABASE 单一语法分支中的所有关键 WITH 选项组合。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖（object_state x expected_status）。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
  - WITH 选项组合规模大，优先覆盖 OWNER、TEMPLATE、ENCODING、LOCALE 核心选项。
  - STRATEGY、ALLOW_CONNECTIONS、CONNECTION LIMIT、IS_TEMPLATE 等选项做代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE DATABASE 不能在事务块内执行，成功样本必须脱离事务上下文。
- 编码和 locale 必须与模板兼容（除非使用 template0），违反此限制的路径属于失败路径。
- 模板数据库在复制期间不能有其他连接，违反此限制的路径属于失败路径。
- database 名称在 PostgreSQL 集群中必须唯一，重名属于失败路径。
- 需要 CREATEDB 权限或 superuser，缺少权限属于失败路径。
- 成功路径必须包含可验证的对象存在性检查（连接到新数据库或查询 pg_database），并在生命周期末尾清理数据库。
- 每个样本必须包含明确的前置对象准备、目标 CREATE DATABASE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP DATABASE 同样不能在事务块内执行，清理阶段需注意。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- WITH 选项组合挂靠到不同核心场景的代表性样本上轮转注入。
- 与编码/locale 兼容性相关的因子必须挂靠到使用不同模板的样本上。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- 与模板连接状态相关的因子必须挂靠到使用模板复制策略的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 OWNER、TEMPLATE、ENCODING、LOCALE 核心选项代表性覆盖。
- 低优先级 WITH 选项（STRATEGY、ICU_LOCALE、ICU_RULES、LOCALE_PROVIDER、COLLATION_VERSION、OID）仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: database
  skill_name: create_database
  official_source: https://www.postgresql.org/docs/16/sql-createdatabase.html
  statement:
    key: create_database
    name: CREATE DATABASE
    aliases:
    - create_database
    - CREATE DATABASE
    purpose: CREATE DATABASE — create a new database
  syntax_templates:
  - "CREATE DATABASE name\n    [ WITH ] [ OWNER [=] user_name ]\n           [ TEMPLATE\
    \ [=] template ]\n           [ ENCODING [=] encoding ]\n           [ STRATEGY\
    \ [=] strategy ]\n           [ LOCALE [=] locale ]\n           [ LC_COLLATE\
    \ [=] lc_collate ]\n           [ LC_CTYPE [=] lc_ctype ]\n           [ ICU_LOCALE\
    \ [=] icu_locale ]\n           [ ICU_RULES [=] icu_rules ]\n           [ LOCALE_PROVIDER\
    \ [=] locale_provider ]\n           [ COLLATION_VERSION = collation_version ]\n\
    \           [ TABLESPACE [=] tablespace_name ]\n           [ ALLOW_CONNECTIONS\
    \ [=] allowconn ]\n           [ CONNECTION LIMIT [=] connlimit ]\n           [\
    \ IS_TEMPLATE [=] istemplate ]\n           [ OID [=] oid ]"
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
    - owner_clause
    - template_clause
    - encoding_clause
    - locale_clause
    - strategy_clause
    - privilege_level
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - database_name_shape
    - owner_name_shape
    - tablespace_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - template_existence
    - encoding_locale_compatibility
    - role_set_role_ability
    - tablespace_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_database_name
    - privilege_denied
    - cannot_set_role_to_owner
    - template_has_connections
    - encoding_locale_incompatible
    - encoding_template_mismatch
    - nonexistent_template
    - nonexistent_tablespace
    - inside_transaction_block
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
      - key: branch_create_database
        label: CREATE DATABASE name [ WITH ] [ OWNER ] [ TEMPLATE ] [ ENCODING ] ... [ OID ]
    object_state:
      label: 目标 database 对象状态
      importance: important
      values:
      - not_exists
      - exists
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    owner_clause:
      label: OWNER 子句形态
      importance: non_important
      values:
      - omitted
      - current_user
      - specified_other_role
    template_clause:
      label: TEMPLATE 子句形态
      importance: non_important
      values:
      - omitted_default_template1
      - template0
      - custom_template
    encoding_clause:
      label: ENCODING 子句形态
      importance: non_important
      values:
      - omitted
      - UTF8
      - LATIN1
      - SQL_ASCII
    locale_clause:
      label: LOCALE 子句形态
      importance: non_important
      values:
      - omitted
      - C_locale
      - POSIX_locale
      - specific_locale
    strategy_clause:
      label: STRATEGY 子句形态
      importance: non_important
      values:
      - omitted_default_wal_log
      - WAL_LOG
      - FILE_COPY
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - createdb_role
      - non_createdb_role
    database_name_shape:
      label: database 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_as_name
      - duplicate_name
    owner_name_shape:
      label: owner 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_role
    tablespace_name_shape:
      label: tablespace 名称形态
      importance: non_important
      values:
      - default_tablespace
      - existing_tablespace
      - nonexistent_tablespace
    template_existence:
      label: 模板数据库存在性及连接状态
      importance: non_important
      values:
      - template_exists_no_connections
      - template_exists_with_connections
      - template_not_exists
    encoding_locale_compatibility:
      label: 编码与 locale 兼容性
      importance: non_important
      values:
      - compatible
      - incompatible
    role_set_role_ability:
      label: SET ROLE 能力
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role
    tablespace_existence:
      label: tablespace 存在性
      importance: non_important
      values:
      - tablespace_exists
      - tablespace_not_exists
    duplicate_database_name:
      label: 重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    privilege_denied:
      label: 缺少 CREATEDB 权限
      importance: non_important
      values:
      - has_createdb
      - lacks_createdb
    cannot_set_role_to_owner:
      label: 无法 SET ROLE 到指定 owner
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role
    template_has_connections:
      label: 模板数据库有其他连接
      importance: non_important
      values:
      - no_other_connections
      - has_other_connections
    encoding_locale_incompatible:
      label: 编码与 locale 不兼容
      importance: non_important
      values:
      - compatible
      - incompatible
    encoding_template_mismatch:
      label: 编码与模板不匹配且未使用 template0
      importance: non_important
      values:
      - matches_template
      - mismatches_template_not_template0
    nonexistent_template:
      label: 模板不存在
      importance: non_important
      values:
      - template_exists
      - template_not_exists
    nonexistent_tablespace:
      label: tablespace 不存在
      importance: non_important
      values:
      - tablespace_exists
      - tablespace_not_exists
    inside_transaction_block:
      label: 在事务块内执行
      importance: non_important
      values:
      - outside_transaction
      - inside_transaction
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_database
      - connect_to_new_database
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_database
      - force_drop_database
  defaults:
    expected_status: success
    object_state: not_exists
    owner_clause: omitted
    template_clause: omitted_default_template1
    encoding_clause: omitted
    locale_clause: omitted
    privilege_level: superuser
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - owner_clause
    - template_clause
    - encoding_clause
    - locale_clause
    - strategy_clause
    - privilege_level
    - database_name_shape
    - owner_name_shape
    - tablespace_name_shape
    - template_existence
    - encoding_locale_compatibility
    - role_set_role_ability
    - tablespace_existence
    - duplicate_database_name
    - privilege_denied
    - cannot_set_role_to_owner
    - template_has_connections
    - encoding_locale_incompatible
    - encoding_template_mismatch
    - nonexistent_template
    - nonexistent_tablespace
    - inside_transaction_block
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
      - invalid_special_char_unquoted
      - max_length_63_bytes
      - over_length_64_bytes
      reason: CREATE DATABASE 需要覆盖数据库名的合法形态、引号语义、特殊字符和长度边界。
    - catalog_factor: database.options.owner
      local_factor: owner_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - omitted
      - valid_current_user
      - valid_other_role
      - nonexistent_user
      - no_set_role_privilege
      reason: OWNER 子句影响目标 owner、角色存在性和 SET ROLE 权限边界。
    - catalog_factor: database.options.template
      local_factor: template_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - omitted_default_template1
      - template0
      - custom_template
      - nonexistent_template
      - template_has_connections
      reason: TEMPLATE 子句影响复制来源、连接状态和编码 locale 兼容性。
    - catalog_factor: database.options.encoding
      local_factor: encoding_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - omitted_client_default
      - utf8
      - latin1
      - sql_ascii
      - invalid_encoding
      reason: ENCODING 是 CREATE DATABASE 的关键选项，需要覆盖有效编码、无效编码和兼容性边界。
    - catalog_factor: database.options.locale
      local_factor: locale_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - omitted
      - c_locale
      - posix_locale
      - valid_system_locale
      - nonexistent_locale
      - encoding_locale_mismatch
      reason: LOCALE、LC_COLLATE 和 LC_CTYPE 影响数据库排序和编码兼容性。
    - catalog_factor: database.options.strategy
      local_factor: strategy_clause
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: reuse_catalog_values
      reason: STRATEGY 决定数据库复制策略，覆盖 WAL_LOG、FILE_COPY 和非法策略。
    - catalog_factor: database.environment.privilege_level
      local_factor: privilege_level
      target_tier: T2
      coverage_role: representative_or_main
      value_policy: statement_specific_subset
      selected_values:
      - superuser
      - createdb_role
      - non_owner
      reason: CREATE DATABASE 需要 superuser 或 CREATEDB 权限。
    - catalog_factor: database.environment.template_existence
      local_factor: template_existence
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 模板数据库存在性和连接状态影响 CREATE DATABASE 成功路径。
    - catalog_factor: database.environment.encoding_locale_compatibility
      local_factor: encoding_locale_compatibility
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 编码、locale 和模板兼容性属于环境约束。
    - catalog_factor: database.environment.role_set_role_ability
      local_factor: role_set_role_ability
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 指定其他 owner 时需要验证 SET ROLE 能力。
    - catalog_factor: database.environment.tablespace_existence
      local_factor: tablespace_existence
      target_tier: T4
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: TABLESPACE 子句需要验证目标表空间存在性。
    - catalog_factor: database.boundary.duplicate_name
      local_factor: duplicate_database_name
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 数据库名在集群内必须唯一，重名是关键失败路径。
    - catalog_factor: database.boundary.privilege_denied
      local_factor: privilege_denied
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: 权限不足路径需要与成功路径明确区分。
    - catalog_factor: database.boundary.inside_transaction
      local_factor: inside_transaction_block
      target_tier: T5
      coverage_role: rotate_attach
      value_policy: reuse_catalog_values
      reason: CREATE DATABASE 不能在事务块内执行。
    - catalog_factor: database.validation.catalog_check
      local_factor: verification_mode
      target_tier: T6
      coverage_role: rotate_attach
      value_policy: statement_specific_subset
      selected_values:
      - pg_database_presence
      - error_assertion
      reason: CREATE DATABASE 的成功和失败路径需要通过 pg_database 查询或错误断言验证。
    excluded_factors:
    - catalog_factor: database.operation.if_exists
      reason: CREATE DATABASE 官方语法没有 IF EXISTS。
    - catalog_factor: database.operation.force
      reason: CREATE DATABASE 官方语法没有 WITH FORCE。
    coverage_notes:
    - database.naming.name_shape 只做轮转挂靠，不进入主笛卡尔积。
  rendering:
    statement_template: "CREATE DATABASE {database_name} {with_clause_options}"
    verification_query_template: "SELECT datname FROM pg_database WHERE datname =\
      \ '{database_name}'"
    factor_value_bindings: {}
```
