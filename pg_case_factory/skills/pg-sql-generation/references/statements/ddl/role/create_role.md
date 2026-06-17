# 技能：CREATE ROLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createrole.html

```sql
CREATE ROLE name [ [ WITH ] option [ ... ] ]

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

## 语句作用

官方说明：CREATE ROLE — define a new database role

该 reference 关注角色定义语句的属性组合、密码策略、成员关系与权限边界，不负责覆盖所有基表列类型或表级依赖对象。

CREATE ROLE 与 CREATE USER 等价，唯一差异是 CREATE USER 默认含 LOGIN 属性而 CREATE ROLE 默认含 NOLOGIN。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE ROLE 仅有一条 synopsis 形式）
- role_identity：目标角色名的存在状态
- expected_status：预期结果（成功/失败）

### T2：重要行为因子
- role_attribute：角色属性开关（SUPERUSER/NOSUPERUSER 等 7 对互斥属性）
- password_clause：密码子句形态
- connection_limit_clause：连接限制子句形态
- valid_until_clause：密码有效期子句形态
- membership_clause：成员关系子句形态（IN ROLE / IN GROUP / ROLE / ADMIN / USER）
- with_keyword：WITH 关键字是否出现

### T3：对象名与输入形态因子
- role_name_shape：角色名标识符形态
- password_value_shape：密码值形态
- connlimit_value_shape：连接限制数值形态
- timestamp_value_shape：VALID UNTIL 时间戳形态

### T4：依赖对象与环境因子
- **本语句不涉及表（table）、列（column）或索引（index）对象。CREATE ROLE 是角色级语句，无表类型或列类型依赖。**
- executor_privilege：执行者权限上下文
- referenced_role_dependency：成员关系子句中引用角色的存在性

### T5：异常与边界因子
- duplicate_role_name：角色名已存在冲突
- privilege_insufficient：权限不足以创建特定属性角色
- nonexistent_referenced_role：成员关系子句引用不存在的角色
- invalid_parameter_value：非法参数值（连接限制、时间戳、密码）
- conflicting_attribute_pair：互斥属性同时指定

### T6：验证与清理因子
- verification_mode：验证方式（pg_roles 目录查询、属性验证、成员关系验证）
- cleanup_mode：清理方式（DROP ROLE、REVOKE 成员关系）

## 覆盖策略

- 覆盖角色不存在（成功创建）与角色已存在（失败冲突）两种核心状态。
- 覆盖所有 7 对互斥属性开关（SUPERUSER/NOSUPERUSER、CREATEDB/NOCREATEDB、CREATEROLE/NOCREATEROLE、INHERIT/NOINHERIT、LOGIN/NOLOGIN、REPLICATION/NOREPLICATION、BYPASSRLS/NOBYPASSRLS）的代表性取值。
- 覆盖密码子句（ENCRYPTED PASSWORD / PASSWORD NULL / 略省）与 CONNECTION LIMIT、VALID UNTIL 的代表性取值。
- 覆盖成员关系子句（IN ROLE / ROLE / ADMIN）的代表性取值；IN GROUP 与 USER 为废弃写法，仅冒烟覆盖。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。
- 需要 superuser 权限的属性（SUPERUSER、REPLICATION、BYPASSRLS）必须单独标注环境依赖。

## 生成约束

- 必须覆盖角色成功创建、重名冲突、权限不足与依赖角色缺失路径。
- CREATE ROLE 不支持 IF NOT EXISTS 或 OR REPLACE，因此重名路径必定失败。
- 成功路径必须包含可通过 pg_roles 目录验证的角色存在性与属性检查，并在生命周期末尾通过 DROP ROLE 清理。
- 对官方语法中出现的每一种选项，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置角色准备（如成员关系中的引用角色）、目标 CREATE ROLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 需要 superuser 权限才能创建 SUPERUSER/REPLICATION/BYPASSRLS 角色的分支，必须在生命周期计划中显式标注环境依赖。
- SYSID 子句已被废弃（仅接受但不生效），仅需冒烟覆盖。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- T3 因子挂靠到各语法分支的代表性样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或成员关系依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - 目标角色不存在（成功）/ 已存在（失败）全覆盖
  - 成功/失败路径全覆盖
  - 权限核心路径全覆盖（superuser 创建 SUPERUSER、普通用户创建普通角色、权限不足失败）
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - 密码子句、连接限制、有效期、成员关系代表性覆盖
  - 废弃子句（IN GROUP、USER、SYSID）冒烟覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: role
  skill_name: create_role
  official_source: https://www.postgresql.org/docs/16/sql-createrole.html
  statement:
    key: create_role
    name: CREATE ROLE
    aliases:
    - create_role
    - CREATE ROLE
    - create_user
    - CREATE USER
    purpose: CREATE ROLE — define a new database role
  syntax_templates:
  - "CREATE ROLE name [ [ WITH ] option [ ... ] ]\n\nwhere option can be:\n\n      SUPERUSER | NOSUPERUSER\n    | CREATEDB | NOCREATEDB\n    | CREATEROLE | NOCREATEROLE\n    | INHERIT | NOINHERIT\n    | LOGIN | NOLOGIN\n    | REPLICATION | NOREPLICATION\n    | BYPASSRLS | NOBYPASSRLS\n    | CONNECTION LIMIT connlimit\n    | [ ENCRYPTED ] PASSWORD 'password' | PASSWORD NULL\n    | VALID UNTIL 'timestamp'\n    | IN ROLE role_name [, ...]\n    | IN GROUP role_name [, ...]\n    | ROLE role_name [, ...]\n    | ADMIN role_name [, ...]\n    | USER role_name [, ...]\n    | SYSID uid"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - role_identity
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - role_attribute
    - password_clause
    - connection_limit_clause
    - valid_until_clause
    - membership_clause
    - with_keyword
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - role_name_shape
    - password_value_shape
    - connlimit_value_shape
    - timestamp_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - referenced_role_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_role_name
    - privilege_insufficient
    - nonexistent_referenced_role
    - invalid_parameter_value
    - conflicting_attribute_pair
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
      - key: branch_1
        label: CREATE ROLE name [ [ WITH ] option [ ... ] ]
    role_identity:
      label: 目标角色存在状态
      importance: important
      values:
      - not_exists
      - exists
      - reserved_word_name
      - quoted_duplicate
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    role_attribute:
      label: 角色属性开关
      importance: important
      values:
      - default_all_nosuperuser_nocreatedb_nocreaterole_inherit_nologin_noreplication_nobypassrls
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
    password_clause:
      label: 密码子句形态
      importance: important
      values:
      - omitted
      - encrypted_password
      - unencrypted_password
      - password_null
    connection_limit_clause:
      label: 连接限制子句形态
      importance: non_important
      values:
      - omitted
      - positive_limit
      - zero_limit
      - negative_one_unlimited
    valid_until_clause:
      label: 密码有效期子句形态
      importance: non_important
      values:
      - omitted
      - future_timestamp
      - past_timestamp
      - current_timestamp
      - infinity
    membership_clause:
      label: 成员关系子句形态
      importance: non_important
      values:
      - omitted
      - in_role
      - in_group
      - role_clause
      - admin_clause
      - user_clause
    with_keyword:
      label: WITH 关键字
      importance: non_important
      values:
      - present
      - absent
    role_name_shape:
      label: 角色名标识符形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_id
      - unicode_id
      - mixed_case_id
      - missing_name
    password_value_shape:
      label: 密码值形态
      importance: non_important
      values:
      - valid_string
      - null_value
      - empty_string
      - encrypted_md5_format
      - encrypted_scram_format
      - special_characters
    connlimit_value_shape:
      label: 连接限制数值形态
      importance: non_important
      values:
      - positive_integer
      - zero
      - negative_one
      - large_number
      - invalid_type
    timestamp_value_shape:
      label: VALID UNTIL 时间戳形态
      importance: non_important
      values:
      - valid_iso_timestamp
      - valid_date_only
      - far_future
      - past_date
      - infinity_literal
      - invalid_format
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - createrole_privilege
      - normal_user_no_createrole
      - role_member_with_set_role
    referenced_role_dependency:
      label: 成员关系引用角色存在性
      importance: non_important
      values:
      - existing_role
      - nonexistent_role
      - self_reference
      - multiple_roles
    duplicate_role_name:
      label: 角色名冲突
      importance: non_important
      values:
      - none
      - same_name_exists
      - case_insensitive_duplicate
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - none
      - non_superuser_creating_superuser
      - non_superuser_creating_replication
      - non_superuser_creating_bypassrls
      - no_createrole_privilege
    nonexistent_referenced_role:
      label: 引用角色不存在
      importance: non_important
      values:
      - none
      - in_role_references_nonexistent
      - role_clause_references_nonexistent
      - admin_clause_references_nonexistent
    invalid_parameter_value:
      label: 非法参数值
      importance: non_important
      values:
      - none
      - invalid_connlimit_type
      - invalid_timestamp_format
      - empty_password_string
    conflicting_attribute_pair:
      label: 互斥属性冲突
      importance: non_important
      values:
      - none
      - superuser_and_nosuperuser
      - login_and_nologin
      - multiple_conflicting_pairs
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_roles_catalog_query
      - attribute_check_query
      - membership_check_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_role
      - revoke_membership_then_drop
      - cascade_drop
  defaults:
    expected_status: success
    role_attribute: default_all_nosuperuser_nocreatedb_nocreaterole_inherit_nologin_noreplication_nobypassrls
    password_clause: omitted
    connection_limit_clause: omitted
    valid_until_clause: omitted
    membership_clause: omitted
    with_keyword: present
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - role_identity
    - expected_status
    non_main_factors:
    - role_attribute
    - password_clause
    - connection_limit_clause
    - valid_until_clause
    - membership_clause
    - with_keyword
    - role_name_shape
    - password_value_shape
    - connlimit_value_shape
    - timestamp_value_shape
    - executor_privilege
    - referenced_role_dependency
    - duplicate_role_name
    - privilege_insufficient
    - nonexistent_referenced_role
    - invalid_parameter_value
    - conflicting_attribute_pair
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - role_identity
  rendering:
    statement_template: "CREATE ROLE {role_name} [ [ WITH ] {options} ]"
    verification_query_template: "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolinherit, rolcanlogin, rolreplication, rolbypassrls, rolconnlimit, rolvaliduntil FROM pg_roles WHERE rolname = '{role_name}'"
    factor_value_bindings:
      role_attribute:
        superuser: "SUPERUSER"
        nosuperuser: "NOSUPERUSER"
        createdb: "CREATEDB"
        nocreatedb: "NOCREATEDB"
        createrole: "CREATEROLE"
        nocreaterole: "NOCREATEROLE"
        inherit: "INHERIT"
        noinherit: "NOINHERIT"
        login: "LOGIN"
        nologin: "NOLOGIN"
        replication: "REPLICATION"
        noreplication: "NOREPLICATION"
        bypassrls: "BYPASSRLS"
        nobypassrls: "NOBYPASSRLS"
      password_clause:
        encrypted_password: "ENCRYPTED PASSWORD '{password_value}'"
        unencrypted_password: "PASSWORD '{password_value}'"
        password_null: "PASSWORD NULL"
        omitted: ""
      connection_limit_clause:
        positive_limit: "CONNECTION LIMIT {connlimit_value}"
        zero_limit: "CONNECTION LIMIT 0"
        negative_one_unlimited: "CONNECTION LIMIT -1"
        omitted: ""
      valid_until_clause:
        future_timestamp: "VALID UNTIL '{timestamp_value}'"
        past_timestamp: "VALID UNTIL '{timestamp_value}'"
        current_timestamp: "VALID UNTIL current_timestamp"
        infinity: "VALID UNTIL 'infinity'"
        omitted: ""
      membership_clause:
        in_role: "IN ROLE {referenced_role_name}"
        in_group: "IN GROUP {referenced_role_name}"
        role_clause: "ROLE {referenced_role_name}"
        admin_clause: "ADMIN {referenced_role_name}"
        user_clause: "USER {referenced_role_name}"
        omitted: ""
      with_keyword:
        present: "WITH"
        absent: ""
```
