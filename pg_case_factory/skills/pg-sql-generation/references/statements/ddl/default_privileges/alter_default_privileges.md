# 技能：ALTER DEFAULT PRIVILEGES

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterdefaultprivileges.html

```sql
ALTER DEFAULT PRIVILEGES
    [ FOR { ROLE | USER } target_role [, ...] ]
    [ IN SCHEMA schema_name [, ...] ]
    abbreviated_grant_or_revoke

where abbreviated_grant_or_revoke is one of:

GRANT { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }
    [, ...] | ALL [ PRIVILEGES ] }
    ON TABLES
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]

GRANT { { USAGE | SELECT | UPDATE }
    [, ...] | ALL [ PRIVILEGES ] }
    ON SEQUENCES
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]

GRANT { EXECUTE | ALL [ PRIVILEGES ] }
    ON { FUNCTIONS | ROUTINES }
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]

GRANT { USAGE | ALL [ PRIVILEGES ] }
    ON TYPES
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]

GRANT { { USAGE | CREATE }
    [, ...] | ALL [ PRIVILEGES ] }
    ON SCHEMAS
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]

REVOKE [ GRANT OPTION FOR ]
    { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }
    [, ...] | ALL [ PRIVILEGES ] }
    ON TABLES
    FROM { [ GROUP ] role_name | PUBLIC } [, ...]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { { USAGE | SELECT | UPDATE }
    [, ...] | ALL [ PRIVILEGES ] }
    ON SEQUENCES
    FROM { [ GROUP ] role_name | PUBLIC } [, ...]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { EXECUTE | ALL [ PRIVILEGES ] }
    ON { FUNCTIONS | ROUTINES }
    FROM { [ GROUP ] role_name | PUBLIC } [, ...]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { USAGE | ALL [ PRIVILEGES ] }
    ON TYPES
    FROM { [ GROUP ] role_name | PUBLIC } [, ...]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { { USAGE | CREATE }
    [, ...] | ALL [ PRIVILEGES ] }
    ON SCHEMAS
    FROM { [ GROUP ] role_name | PUBLIC } [, ...]
    [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- ALTER DEFAULT PRIVILEGES 仅影响将来创建的对象权限，不影响已存在对象的权限
- 当前角色决定新对象的默认权限；新对象权限仅受当前角色的默认权限影响，不受角色成员关系继承
- per-schema 默认权限是加法性的（additive only），仅添加到全局默认之上
- 不能通过 per-schema REVOKE 撤销全局 GRANT 的默认权限；per-schema REVOKE 仅用于撤销之前的 per-schema GRANT
- IN SCHEMA 不能用于 SCHEMAS 对象类型（schema 不能嵌套）
- FOR ROLE / FOR USER 是等效的；如果省略，则修改当前角色的默认权限
- 删除角色前必须撤销其默认权限修改或使用 DROP OWNED BY
- 使用 \ddp 查看现有默认权限分配
- 不在 SQL 标准中

## 语句作用

官方说明：ALTER DEFAULT PRIVILEGES — define default access privileges

该 reference 关注默认权限的定义与修改。ALTER DEFAULT PRIVILEGES 语法复杂，涉及 10 种 GRANT/REVOKE 形式（5 种对象类型的 GRANT + 5 种对象类型的 REVOKE），以及 FOR ROLE 和 IN SCHEMA 前缀组合。该语句不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- operation_type：操作类型（GRANT / REVOKE）
- object_class：权限对象类别（TABLES / SEQUENCES / FUNCTIONS / ROUTINES / TYPES / SCHEMAS）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- for_role_clause：FOR ROLE/USER 子句形态（省略当前角色 / 指定单个 target_role / 指定多个 target_role / 指定不存在角色）
- in_schema_clause：IN SCHEMA 子句形态（省略全局 / 指定单个 schema / 指定多个 schema / 指定不存在 schema / 对 SCHEMAS 对象类型不允许）
- privilege_set：权限集合形态（单一权限 / 多个权限 / ALL PRIVILEGES / PUBLIC）
- grant_option：WITH GRANT OPTION（仅 GRANT：省略 / 指定）
- revoke_grant_option_for：GRANT OPTION FOR（仅 REVOKE：省略 / 指定）
- revoke_cascade_restrict：CASCADE / RESTRICT（仅 REVOKE：省略默认 RESTRICT / CASCADE / RESTRICT）

### T3：对象名与输入形态因子
- target_role_name_shape：target_role 名称形态
- schema_name_shape：schema 名称形态
- recipient_role_name_shape：接受权限的角色名称形态
- group_keyword：GROUP 关键字形态（省略 / 指定 GROUP）
- routines_vs_functions：ROUTINES vs FUNCTIONS 关键字选择

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / target_role_owner / non_owner）
- schema_existence：schema 存在性
- role_existence：角色存在性
- additive_vs_overriding：per-schema 加法语义与全局默认覆盖语义

### T5：异常与边界因子
- in_schema_on_schemas：IN SCHEMA 与 SCHEMAS 对象类型冲突
- nonexistent_target_role：FOR ROLE 指定不存在角色
- nonexistent_schema：IN SCHEMA 指定不存在 schema
- cannot_revoke_global_from_per_schema：per-schema REVOKE 无法撤销全局 GRANT
- privilege_denied：非授权角色修改默认权限
- role_not_member_of_target_role：当前角色不是 target_role 的成员

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖 ALTER DEFAULT PRIVILEGES 的 10 种 GRANT/REVOKE 形式。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖（operation_type x object_class x expected_status）。
- T2 因子按规模控制策略参与组合：
  - FOR ROLE / IN SCHEMA 在各 GRANT/REVOKE 形式上轮转覆盖。
  - privilege_set 在各对象类别上做代表性覆盖（每种对象类别至少一个 ALL PRIVILEGES 和一个具体权限组合）。
  - GRANT OPTION / REVOKE GRANT OPTION FOR / CASCADE RESTRICT 仅在 REVOKE 形式上覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 每种 GRANT 形式（TABLES/SEQUENCES/FUNCTIONS/ROUTINES/TYPES/SCHEMAS）至少一个成功路径样本。
- 每种 REVOKE 形式至少一个成功路径样本。
- IN SCHEMA 与 SCHEMAS 对象类型的冲突必须作为失败路径覆盖。
- per-schema 加法语义必须验证：per-schema GRANT 添加到全局默认之上，不能通过 per-schema REVOKE 撤销全局默认。
- FOR ROLE 等效于 FOR USER，两种关键字至少各出现一次。
- FUNCTIONS 和 ROUTINES 关键字等效，至少各出现一次。
- 成功路径必须包含可验证的默认权限检查（\ddp 或 pg_default_acl 查询），并在生命周期末尾清理。
- 每个样本必须包含明确的前置角色和 schema 准备、目标 ALTER DEFAULT PRIVILEGES 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- FOR ROLE / IN SCHEMA 子句在不同 GRANT/REVOKE 形式上轮转挂靠，确保每种组合至少出现一次。
- privilege_set 在各对象类别上做代表性覆盖挂靠。
- GRANT OPTION 仅挂靠到 GRANT 形式。
- REVOKE GRANT OPTION FOR 和 CASCADE/RESTRICT 仅挂靠到 REVOKE 形式。
- IN SCHEMA 与 SCHEMAS 冲突仅挂靠到 SCHEMAS 对象类型的失败样本。
- per-schema 加法语义挂靠到同时使用全局和 per-schema GRANT 的样本上验证。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏操作类型、对象类别和成功/失败归因的可识别性。

## 规模控制规则

- 优先保证：
  - 所有 10 种 GRANT/REVOKE 形式全覆盖
  - 6 种对象类别全覆盖
  - 成功/失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - FOR ROLE / IN SCHEMA 组合代表性覆盖
  - privilege_set 代表性覆盖（ALL / 具体权限组合）
  - GRANT OPTION / REVOKE GRANT OPTION FOR / CASCADE RESTRICT 覆盖
  - per-schema 加法语义覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: default_privileges
  skill_name: alter_default_privileges
  official_source: https://www.postgresql.org/docs/16/sql-alterdefaultprivileges.html
  statement:
    key: alter_default_privileges
    name: ALTER DEFAULT PRIVILEGES
    aliases:
    - alter_default_privileges
    - ALTER DEFAULT PRIVILEGES
    purpose: ALTER DEFAULT PRIVILEGES — define default access privileges
  syntax_templates:
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    [ IN SCHEMA schema_name [, ...] ]\n    GRANT { { SELECT | INSERT | UPDATE\
    \ | DELETE | TRUNCATE | REFERENCES | TRIGGER }\n    [, ...] | ALL [ PRIVILEGES\
    \ ] }\n    ON TABLES\n    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH\
    \ GRANT OPTION ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    [ IN SCHEMA schema_name [, ...] ]\n    GRANT { { USAGE | SELECT | UPDATE\
    \ }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON SEQUENCES\n    TO { [ GROUP\
    \ ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    [ IN SCHEMA schema_name [, ...] ]\n    GRANT { EXECUTE | ALL [ PRIVILEGES\
    \ ] }\n    ON { FUNCTIONS | ROUTINES }\n    TO { [ GROUP ] role_name | PUBLIC\
    \ } [, ...] [ WITH GRANT OPTION ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    [ IN SCHEMA schema_name [, ...] ]\n    GRANT { USAGE | ALL [ PRIVILEGES\
    \ ] }\n    ON TYPES\n    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH\
    \ GRANT OPTION ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    GRANT { { USAGE | CREATE }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON\
    \ SCHEMAS\n    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION\
    \ ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    [ IN SCHEMA schema_name [, ...] ]\n    REVOKE [ GRANT OPTION FOR ]\n    {\
    \ { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }\n\
    \    [, ...] | ALL [ PRIVILEGES ] }\n    ON TABLES\n    FROM { [ GROUP ] role_name\
    \ | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    [ IN SCHEMA schema_name [, ...] ]\n    REVOKE [ GRANT OPTION FOR ]\n    {\
    \ { USAGE | SELECT | UPDATE }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON SEQUENCES\n\
    \    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT\
    \ ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    [ IN SCHEMA schema_name [, ...] ]\n    REVOKE [ GRANT OPTION FOR ]\n    {\
    \ EXECUTE | ALL [ PRIVILEGES ] }\n    ON { FUNCTIONS | ROUTINES }\n    FROM\
    \ { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    [ IN SCHEMA schema_name [, ...] ]\n    REVOKE [ GRANT OPTION FOR ]\n    {\
    \ USAGE | ALL [ PRIVILEGES ] }\n    ON TYPES\n    FROM { [ GROUP ] role_name\
    \ | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]"
  - "ALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n\
    \    REVOKE [ GRANT OPTION FOR ]\n    { { USAGE | CREATE }\n    [, ...] | ALL\
    \ [ PRIVILEGES ] }\n    ON SCHEMAS\n    FROM { [ GROUP ] role_name | PUBLIC\
    \ } [, ...]\n    [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - operation_type
    - object_class
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - for_role_clause
    - in_schema_clause
    - privilege_set
    - grant_option
    - revoke_grant_option_for
    - revoke_cascade_restrict
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - target_role_name_shape
    - schema_name_shape
    - recipient_role_name_shape
    - group_keyword
    - routines_vs_functions
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_existence
    - role_existence
    - additive_vs_overriding
  - tier: T5
    name: 异常与边界因子
    factors:
    - in_schema_on_schemas
    - nonexistent_target_role
    - nonexistent_schema
    - cannot_revoke_global_from_per_schema
    - privilege_denied
    - role_not_member_of_target_role
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification_mode
    - cleanup_mode
  factors:
    operation_type:
      label: 操作类型
      importance: important
      values:
      - key: grant
        label: GRANT
      - key: revoke
        label: REVOKE
    object_class:
      label: 权限对象类别
      importance: important
      values:
      - TABLES
      - SEQUENCES
      - FUNCTIONS
      - ROUTINES
      - TYPES
      - SCHEMAS
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    for_role_clause:
      label: FOR ROLE/USER 子句形态
      importance: non_important
      values:
      - omitted_current_role
      - single_target_role
      - multiple_target_roles
      - nonexistent_target_role
      - for_user_keyword
    in_schema_clause:
      label: IN SCHEMA 子句形态
      importance: non_important
      values:
      - omitted_global
      - single_schema
      - multiple_schemas
      - nonexistent_schema
      - not_allowed_for_schemas_class
    privilege_set:
      label: 权限集合形态
      importance: non_important
      values:
      - single_privilege
      - multiple_privileges
      - all_privileges
      - public
    grant_option:
      label: WITH GRANT OPTION（仅 GRANT）
      importance: non_important
      values:
      - omitted
      - with_grant_option
    revoke_grant_option_for:
      label: GRANT OPTION FOR（仅 REVOKE）
      importance: non_important
      values:
      - omitted
      - grant_option_for
    revoke_cascade_restrict:
      label: CASCADE / RESTRICT（仅 REVOKE）
      importance: non_important
      values:
      - omitted_default_restrict
      - cascade
      - restrict
    target_role_name_shape:
      label: target_role 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_role_name
    schema_name_shape:
      label: schema 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_schema_name
    recipient_role_name_shape:
      label: 接受权限的角色名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - public
      - group_role_name
    group_keyword:
      label: GROUP 关键字形态
      importance: non_important
      values:
      - omitted
      - specified_group
    routines_vs_functions:
      label: ROUTINES vs FUNCTIONS 关键字选择
      importance: non_important
      values:
      - functions_keyword
      - routines_keyword
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - target_role_owner
      - role_member
      - non_member
    schema_existence:
      label: schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    role_existence:
      label: 角色存在性
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    additive_vs_overriding:
      label: per-schema 加法语义与全局默认覆盖语义
      importance: non_important
      values:
      - global_only
      - per_schema_additive
      - per_schema_cannot_revoke_global
    in_schema_on_schemas:
      label: IN SCHEMA 与 SCHEMAS 对象类型冲突
      importance: non_important
      values:
      - no_conflict
      - in_schema_with_schemas_class
    nonexistent_target_role:
      label: FOR ROLE 指定不存在角色
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    nonexistent_schema:
      label: IN SCHEMA 指定不存在 schema
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    cannot_revoke_global_from_per_schema:
      label: per-schema REVOKE 无法撤销全局 GRANT
      importance: non_important
      values:
      - valid_revoke
      - invalid_per_schema_revoke_of_global
    privilege_denied:
      label: 非授权角色修改默认权限
      importance: non_important
      values:
      - authorized_success
      - unauthorized_failure
    role_not_member_of_target_role:
      label: 当前角色不是 target_role 的成员
      importance: non_important
      values:
      - is_member
      - is_not_member
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_default_acl
      - psql_ddp_command
      - create_object_and_verify_privileges
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - revoke_default_privileges
      - drop_role_owned_by
      - drop_schema
  defaults:
    expected_status: success
    operation_type: grant
    object_class: TABLES
    for_role_clause: omitted_current_role
    in_schema_clause: omitted_global
    privilege_set: all_privileges
  coverage_policy:
    main_combination_axes:
    - operation_type
    - object_class
    - expected_status
    non_main_factors:
    - for_role_clause
    - in_schema_clause
    - privilege_set
    - grant_option
    - revoke_grant_option_for
    - revoke_cascade_restrict
    - target_role_name_shape
    - schema_name_shape
    - recipient_role_name_shape
    - group_keyword
    - routines_vs_functions
    - privilege_level
    - schema_existence
    - role_existence
    - additive_vs_overriding
    - in_schema_on_schemas
    - nonexistent_target_role
    - nonexistent_schema
    - cannot_revoke_global_from_per_schema
    - privilege_denied
    - role_not_member_of_target_role
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 300
    preserve_axes_first:
    - operation_type
    - object_class
  rendering:
    statement_template: "ALTER DEFAULT PRIVILEGES {for_role_clause} {in_schema_clause}\
      \ {grant_or_revoke_body}"
    verification_query_template: "SELECT defaclobjtype, defaclacl FROM pg_default_acl\
      \ WHERE defaclnamespace = {schema_oid} AND defaclrole = {role_oid}"
    factor_value_bindings: {}
```
