# 技能：ALTER DOMAIN

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterdomain.html

```sql
ALTER DOMAIN name
    { SET DEFAULT expression | DROP DEFAULT }

ALTER DOMAIN name
    { SET | DROP } NOT NULL

ALTER DOMAIN name
    ADD domain_constraint [ NOT VALID ]

ALTER DOMAIN name
    DROP CONSTRAINT [ IF EXISTS ] constraint_name [ RESTRICT | CASCADE ]

ALTER DOMAIN name
    RENAME CONSTRAINT constraint_name TO new_constraint_name

ALTER DOMAIN name
    VALIDATE CONSTRAINT constraint_name

ALTER DOMAIN name
    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }

ALTER DOMAIN name
    RENAME TO new_name

ALTER DOMAIN name
    SET SCHEMA new_schema

where domain_constraint is:

[ CONSTRAINT constraint_name ]
{ NOT NULL | CHECK (expression) }
```

PG16 关键约束：
- 必须拥有 domain 才能使用 ALTER DOMAIN
- SET SCHEMA 还需要 CREATE 权限于新 schema
- OWNER TO 需要能够 SET ROLE 到新拥有角色，且该角色必须有 CREATE 权限于 domain 的 schema
- ADD CONSTRAINT / VALIDATE CONSTRAINT / SET NOT NULL 对容器类型列（composite, array, range 列）使用 domain 时会失败
- ADD CONSTRAINT NOT VALID 仅接受 CHECK 约束，不接受 NOT NULL
- 并发数据风险：ADD CONSTRAINT 无法看到未提交行，推荐先 NOT VALID 再 VALIDATE CONSTRAINT

## 语句作用

官方说明：ALTER DOMAIN — change the definition of a domain

该 reference 关注域（SQL DOMAIN）对象的定义变更，包括默认值修改、约束增删改、约束验证、命名变更、owner 变更和 schema 变更。域的 ALTER 操作不涉及基表列类型组合，但需要关注 domain 列上的容器类型限制。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（9 种顶层 ALTER 形式）
- object_state：目标 domain 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（set_default / drop_default / set_not_null / drop_not_null / add_constraint / drop_constraint / rename_constraint / validate_constraint / owner_to / rename_to / set_schema）
- constraint_type：ADD 约束类型（NOT NULL / CHECK）
- if_exists：DROP CONSTRAINT IF EXISTS 开关
- cascade_restrict：DROP CONSTRAINT CASCADE / RESTRICT 开关
- not_valid：ADD CONSTRAINT NOT VALID 开关
- owner_target：OWNER TO 目标形态（指定 new_owner / CURRENT_ROLE / CURRENT_USER / SESSION_USER）

### T3：对象名与输入形态因子
- domain_name_shape：domain 名称形态
- constraint_name_shape：约束名称形态
- new_name_shape：RENAME TO 新名称形态
- new_constraint_name_shape：RENAME CONSTRAINT 新约束名称形态
- schema_name_shape：SET SCHEMA 目标 schema 名称形态
- owner_name_shape：OWNER TO 目标角色名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（domain_owner / non_owner / superuser）
- constraint_existence：约束存在性（存在 / 不存在）
- schema_existence：SET SCHEMA 目标 schema 存在性
- role_existence：OWNER TO 角色存在性
- set_role_capability：当前用户能否 SET ROLE 到新 owner
- container_column_usage：domain 是否被容器类型列使用

### T5：异常与边界因子
- nonexistent_domain：目标 domain 不存在
- nonexistent_constraint：DROP/RENAME/VALIDATE 的约束不存在
- duplicate_constraint：ADD 同名约束冲突
- container_column_block：domain 被容器类型列使用导致 ADD/VALIDATE/SET NOT NULL 失败
- non_owner_attempt：非 owner 尝试 ALTER
- cannot_set_role：无法 SET ROLE 到新 owner
- nonexistent_role：OWNER TO 角色不存在
- nonexistent_schema：SET SCHEMA 目标 schema 不存在
- null_value_block：SET NOT NULL 但列中存在 null 值
- concurrent_data_hazard：并发 INSERT 可能绕过新约束

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER DOMAIN 9 种语法分支中的所有行为路径。
- 不需要覆盖所有基表，不需要覆盖所有列类型组合。
- 覆盖目标 domain 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 owner 权限边界、约束语义边界和容器类型列限制。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 domain 对象，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 domain 存在时的成功修改路径和不存在时的失败路径。
- DROP CONSTRAINT IF EXISTS 必须覆盖约束不存在时的 no-op 路径。
- ADD CONSTRAINT NOT VALID 仅接受 CHECK 约束（不接受 NOT NULL），违反此限制的路径属于失败路径。
- VALIDATE CONSTRAINT / ADD CONSTRAINT / SET NOT NULL 对容器类型列（composite, array, range）使用 domain 时会失败，必须覆盖此边界。
- SET NOT NULL 要求列中无 null 值，列中存在 null 的路径属于失败路径。
- OWNER TO 还需要当前用户能够 SET ROLE 到新 owner 角色，无法 SET ROLE 的路径属于失败路径。
- SET SCHEMA 还需要 CREATE 权限于新 schema，缺少权限的路径属于失败路径。
- 成功路径必须包含可验证的对象变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER DOMAIN 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- 与容器类型列限制相关的因子必须挂靠到 ADD/VALIDATE/SET NOT NULL 分支的样本上。
- OWNER TO 分支的角色存在性和 SET ROLE 能力因子必须挂靠到对应分支的样本上。
- SET SCHEMA 分支的 schema 存在性和 CREATE 权限因子必须挂靠到对应分支的样本上。

## 规模控制规则

- 优先保证官方语法分支（9 种 ALTER 形式）、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证约束类型形态、IF EXISTS 开关、CASCADE/RESTRICT 开关、NOT VALID 开关和 OWNER TO 目标形态代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: domain
  skill_name: alter_domain
  official_source: https://www.postgresql.org/docs/16/sql-alterdomain.html
  statement:
    key: alter_domain
    name: ALTER DOMAIN
    aliases:
    - alter_domain
    - ALTER DOMAIN
    purpose: ALTER DOMAIN — change the definition of a domain
  syntax_templates:
  - "ALTER DOMAIN name\n    { SET DEFAULT expression | DROP DEFAULT }"
  - "ALTER DOMAIN name\n    { SET | DROP } NOT NULL"
  - "ALTER DOMAIN name\n    ADD domain_constraint [ NOT VALID ]"
  - "ALTER DOMAIN name\n    DROP CONSTRAINT [ IF EXISTS ] constraint_name [ RESTRICT\
    \ | CASCADE ]"
  - "ALTER DOMAIN name\n    RENAME CONSTRAINT constraint_name TO new_constraint_name"
  - "ALTER DOMAIN name\n    VALIDATE CONSTRAINT constraint_name"
  - "ALTER DOMAIN name\n    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER\
    \ | SESSION_USER }"
  - "ALTER DOMAIN name\n    RENAME TO new_name"
  - "ALTER DOMAIN name\n    SET SCHEMA new_schema"
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
    - constraint_type
    - if_exists
    - cascade_restrict
    - not_valid
    - owner_target
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - domain_name_shape
    - constraint_name_shape
    - new_name_shape
    - new_constraint_name_shape
    - schema_name_shape
    - owner_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - constraint_existence
    - schema_existence
    - role_existence
    - set_role_capability
    - container_column_usage
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_domain
    - nonexistent_constraint
    - duplicate_constraint
    - container_column_block
    - non_owner_attempt
    - cannot_set_role
    - nonexistent_role
    - nonexistent_schema
    - null_value_block
    - concurrent_data_hazard
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
      - key: branch_set_default
        label: ALTER DOMAIN name SET DEFAULT expression
      - key: branch_drop_default
        label: ALTER DOMAIN name DROP DEFAULT
      - key: branch_set_not_null
        label: ALTER DOMAIN name SET NOT NULL
      - key: branch_drop_not_null
        label: ALTER DOMAIN name DROP NOT NULL
      - key: branch_add_constraint
        label: ALTER DOMAIN name ADD domain_constraint [ NOT VALID ]
      - key: branch_drop_constraint
        label: ALTER DOMAIN name DROP CONSTRAINT [ IF EXISTS ] constraint_name [ RESTRICT | CASCADE ]
      - key: branch_rename_constraint
        label: ALTER DOMAIN name RENAME CONSTRAINT constraint_name TO new_constraint_name
      - key: branch_validate_constraint
        label: ALTER DOMAIN name VALIDATE CONSTRAINT constraint_name
      - key: branch_owner_to
        label: ALTER DOMAIN name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_rename_to
        label: ALTER DOMAIN name RENAME TO new_name
      - key: branch_set_schema
        label: ALTER DOMAIN name SET SCHEMA new_schema
    object_state:
      label: 目标 domain 对象状态
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
      - set_default
      - drop_default
      - set_not_null
      - drop_not_null
      - add_constraint
      - drop_constraint
      - rename_constraint
      - validate_constraint
      - owner_to
      - rename_to
      - set_schema
    constraint_type:
      label: ADD 约束类型
      importance: non_important
      values:
      - not_null
      - check
      - not_null_with_name
      - check_with_name
    if_exists:
      label: DROP CONSTRAINT IF EXISTS 开关
      importance: non_important
      values:
      - present
      - absent
    cascade_restrict:
      label: DROP CONSTRAINT CASCADE/RESTRICT
      importance: non_important
      values:
      - restrict
      - cascade
      - omitted_default_restrict
    not_valid:
      label: ADD CONSTRAINT NOT VALID 开关
      importance: non_important
      values:
      - not_valid
      - full_valid
    owner_target:
      label: OWNER TO 目标形态
      importance: non_important
      values:
      - specified_new_owner
      - specified_current_role
      - specified_current_user
      - specified_session_user
    domain_name_shape:
      label: domain 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified
      - reserved_word_as_name
      - nonexistent_name
    constraint_name_shape:
      label: 约束名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_constraint
      - existing_constraint
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - duplicate_name
      - invalid_name
    new_constraint_name_shape:
      label: RENAME CONSTRAINT 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - duplicate_constraint_name
    schema_name_shape:
      label: SET SCHEMA 目标 schema 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_schema
      - existing_schema
    owner_name_shape:
      label: OWNER TO 目标角色名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_role
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - domain_owner
      - non_owner
    constraint_existence:
      label: 约束存在性
      importance: non_important
      values:
      - constraint_exists
      - constraint_not_exists
    schema_existence:
      label: SET SCHEMA 目标 schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    role_existence:
      label: OWNER TO 角色存在性
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    set_role_capability:
      label: SET ROLE 到新 owner 能力
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role
    container_column_usage:
      label: domain 被容器类型列使用
      importance: non_important
      values:
      - not_used_in_container
      - used_in_composite_column
      - used_in_array_column
      - used_in_range_column
    nonexistent_domain:
      label: 目标 domain 不存在
      importance: non_important
      values:
      - domain_exists
      - domain_missing
    nonexistent_constraint:
      label: 约束不存在
      importance: non_important
      values:
      - constraint_exists
      - constraint_missing
    duplicate_constraint:
      label: 同名约束冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_constraint
    container_column_block:
      label: 容器类型列阻止操作
      importance: non_important
      values:
      - no_container_block
      - composite_column_block
      - array_column_block
      - range_column_block
    non_owner_attempt:
      label: 非 owner 尝试 ALTER
      importance: non_important
      values:
      - owner_execution
      - non_owner_execution
      - superuser_execution
    cannot_set_role:
      label: 无法 SET ROLE 到新 owner
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role_to_target
    nonexistent_role:
      label: OWNER TO 角色不存在
      importance: non_important
      values:
      - role_exists
      - role_missing
    nonexistent_schema:
      label: SET SCHEMA 目标 schema 不存在
      importance: non_important
      values:
      - schema_exists
      - schema_missing
    null_value_block:
      label: SET NOT NULL 但列中存在 null
      importance: non_important
      values:
      - no_null_values
      - has_null_values_in_column
    concurrent_data_hazard:
      label: 并发数据风险
      importance: non_important
      values:
      - safe_serial_execution
      - concurrent_insert_possible
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_type
      - catalog_query_pg_constraint
      - effect_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - revert_alter
      - drop_domain
      - role_cleanup
      - schema_cleanup
  defaults:
    expected_status: success
    privilege_level: superuser
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - constraint_type
    - if_exists
    - cascade_restrict
    - not_valid
    - owner_target
    - domain_name_shape
    - constraint_name_shape
    - new_name_shape
    - new_constraint_name_shape
    - schema_name_shape
    - owner_name_shape
    - privilege_level
    - constraint_existence
    - schema_existence
    - role_existence
    - set_role_capability
    - container_column_usage
    - nonexistent_domain
    - nonexistent_constraint
    - duplicate_constraint
    - container_column_block
    - non_owner_attempt
    - cannot_set_role
    - nonexistent_role
    - nonexistent_schema
    - null_value_block
    - concurrent_data_hazard
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER DOMAIN {domain_name} {alter_clause}"
    verification_query_template: "SELECT typname, typtype FROM pg_type WHERE typname\
      \ = '{domain_name}' AND typtype = 'd'"
    factor_value_bindings: {}
```
