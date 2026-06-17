# 技能：ALTER FOREIGN TABLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterforeigntable.html

```sql
ALTER FOREIGN TABLE [ IF EXISTS ] [ ONLY ] name [ * ]
    action [, ... ]
ALTER FOREIGN TABLE [ IF EXISTS ] [ ONLY ] name [ * ]
    RENAME [ COLUMN ] column_name TO new_column_name
ALTER FOREIGN TABLE [ IF EXISTS ] name
    RENAME TO new_name
ALTER FOREIGN TABLE [ IF EXISTS ] name
    SET SCHEMA new_schema

where action is one of:

    ADD [ COLUMN ] [ IF NOT EXISTS ] column_name data_type [ COLLATE collation ] [ column_constraint [ ... ] ]
    DROP [ COLUMN ] [ IF EXISTS ] column_name [ RESTRICT | CASCADE ]
    ALTER [ COLUMN ] column_name [ SET DATA ] TYPE data_type [ COLLATE collation ]
    ALTER [ COLUMN ] column_name SET DEFAULT expression
    ALTER [ COLUMN ] column_name DROP DEFAULT
    ALTER [ COLUMN ] column_name { SET | DROP } NOT NULL
    ALTER [ COLUMN ] column_name SET STATISTICS integer
    ALTER [ COLUMN ] column_name SET ( attribute_option = value [, ... ] )
    ALTER [ COLUMN ] column_name RESET ( attribute_option [, ... ] )
    ALTER [ COLUMN ] column_name SET STORAGE { PLAIN | EXTERNAL | EXTENDED | MAIN | DEFAULT }
    ALTER [ COLUMN ] column_name OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ])
    ADD table_constraint [ NOT VALID ]
    VALIDATE CONSTRAINT constraint_name
    DROP CONSTRAINT [ IF EXISTS ]  constraint_name [ RESTRICT | CASCADE ]
    DISABLE TRIGGER [ trigger_name | ALL | USER ]
    ENABLE TRIGGER [ trigger_name | ALL | USER ]
    ENABLE REPLICA TRIGGER trigger_name
    ENABLE ALWAYS TRIGGER trigger_name
    SET WITHOUT OIDS
    INHERIT parent_table
    NO INHERIT parent_table
    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
    OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ])
```

PG16 关键约束：
- 使用 ALTER FOREIGN TABLE 必须拥有该外部表。
- SET SCHEMA 还需要 CREATE 权限于新 schema。
- OWNER TO 还需要能够 SET ROLE 到新 owner 角色，且新 owner 需要有 CREATE 权限于表所在 schema。superuser 可以变更任何表的 owner。
- ADD COLUMN / ALTER COLUMN TYPE 需要 USAGE 权限于数据类型。
- ENABLE TRIGGER ALL（含内部生成触发器）需要 superuser 权限。
- 与外部服务器的一致性不被检查——用户需自行确保表定义与远程端匹配。
- 只有 CHECK 约束支持（ADD table_constraint），不执行验证——仅声明条件假设为真。
- VALIDATE CONSTRAINT 不执行验证动作，仅标记约束为有效。
- 所有 action（除 RENAME 和 SET SCHEMA）可以在一条 ALTER FOREIGN TABLE 中组合执行。
- ADD/DROP COLUMN 不影响底层存储——仅声明列变更。
- SET DATA TYPE 不影响底层存储——仅变更 PostgreSQL 认为的列类型。
- IF EXISTS：对象不存在时不报错，仅发 notice。

## 语句作用

官方说明：ALTER FOREIGN TABLE — change the definition of a foreign table

该 reference 关注外部表定义变更语句的四种顶层语法分支（action 列表 / RENAME COLUMN / RENAME TO / SET SCHEMA）、列操作多样性（ADD/DROP/ALTER COLUMN）、约束操作（CHECK only）、OWNER/INHERIT/OPTIONS 变更、IF EXISTS 行为和权限边界。

ALTER FOREIGN TABLE **涉及列类型变更**——ALTER COLUMN SET DATA TYPE 和 ADD COLUMN 都涉及数据类型选择，需要 USAGE 权限于数据类型。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（action_list / RENAME COLUMN / RENAME TO / SET SCHEMA）
- object_state：目标 foreign table 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（add_column / drop_column / alter_column_type / set_drop_not_null / set_drop_default / add_constraint / drop_constraint / validate_constraint / inherit / no_inherit / owner / options / rename_column / rename_table / set_schema / set_without_oids / enable_trigger / disable_trigger）
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- column_data_type：ADD COLUMN / ALTER COLUMN TYPE 的数据类型（integer / text / varchar / numeric / boolean / date / timestamp / jsonb / uuid / bigint）
- only_clause：ONLY 子句开关（省略 / 指定）

### T3：对象名与输入形态因子
- table_name_shape：表名形态
- column_name_shape：列名形态
- new_column_name_shape：RENAME COLUMN 新名称形态
- new_table_name_shape：RENAME TO 新名称形态
- new_schema_name_shape：SET SCHEMA 目标 schema 名称形态
- owner_name_shape：OWNER TO 目标角色名称形态
- constraint_name_shape：约束名称形态
- parent_table_name_shape：INHERIT/NO INHERIT 父表名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（table_owner / non_owner / superuser）
- schema_existence：SET SCHEMA 目标 schema 存在性（存在 / 不存在）
- type_usage_privilege：ADD COLUMN / ALTER COLUMN TYPE 的数据类型 USAGE 权限（有 / 无）
- parent_table_existence：INHERIT 父表存在性（存在 / 不存在）
- set_role_capability：OWNER TO 时能否 SET ROLE 到新 owner（可以 / 不可以）

### T5：异常与边界因子
- nonexistent_table：目标表不存在且无 IF EXISTS
- nonexistent_column：DROP/ALTER 引用的列不存在
- nonexistent_constraint：DROP/VALIDATE 引用的约束不存在
- non_owner_attempt：非 owner 尝试 ALTER FOREIGN TABLE
- no_type_usage_privilege：无数据类型 USAGE 权限
- nonexistent_parent_table：INHERIT 父表不存在
- constraint_not_enforced：ADD CONSTRAINT 仅声明不强制（行为边界）
- validate_constraint_no_action：VALIDATE CONSTRAINT 不执行验证（行为边界）
- consistency_not_checked：ADD/DROP/ALTER COLUMN 不检查与远程端一致性（行为边界）
- if_exists_notice：IF EXISTS 遇不存在对象的 notice 路径

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER FOREIGN TABLE 四个语法分支中的所有行为路径。
- 需要覆盖 ALTER 行为的代表性类型（至少 add_column / drop_column / alter_column_type / set_not_null / add_constraint / owner / options / rename_column / rename_table / set_schema）。
- **需要覆盖列数据类型**：ADD COLUMN 和 ALTER COLUMN SET DATA TYPE 涉及数据类型选择。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标外部表对象，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标表存在时的成功修改路径、目标表不存在时的失败路径，以及 IF EXISTS 的 no-op 路径。
- 各 action 类型需要保持独立归因。
- ADD COLUMN / ALTER COLUMN SET DATA TYPE 涉及数据类型选择，需要在至少一个样本中出现代表性数据类型。
- 成功路径必须包含可验证的对象变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER FOREIGN TABLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- ALTER FOREIGN TABLE 要求执行者是表的 owner，ADD COLUMN / ALTER COLUMN TYPE 需要 USAGE 权限于数据类型。
- 约束仅声明不强制，VALIDATE CONSTRAINT 不执行验证——这些行为边界需要代表性覆盖。

## 挂靠规则

- T3 因子中 column_data_type 挂靠到 ADD COLUMN 和 ALTER COLUMN TYPE 分支的代表性成功样本，按数据类型类别轮转注入。
- T3 因子中 table_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、schema 存在性、数据类型 USAGE 权限或父表存在性的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（action_list / RENAME COLUMN / RENAME TO / SET SCHEMA）
  - ALTER action 代表性类型全覆盖
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖（owner / non_owner / superuser）
- 次优先保证：
  - 列数据类型代表性覆盖
  - IF EXISTS 行为覆盖
  - ONLY 子句代表性覆盖
  - 约束声明不强制行为边界覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: foreign_table
  skill_name: alter_foreign_table
  official_source: https://www.postgresql.org/docs/16/sql-alterforeigntable.html
  statement:
    key: alter_foreign_table
    name: ALTER FOREIGN TABLE
    aliases:
    - ALTER FOREIGN TABLE
    - alter foreign table
    - alter_foreign_table
    purpose: change the definition of a foreign table
  syntax_templates:
  - "ALTER FOREIGN TABLE [ IF EXISTS ] [ ONLY ] name [ * ] action [, ... ]"
  - "ALTER FOREIGN TABLE [ IF EXISTS ] [ ONLY ] name [ * ] RENAME [ COLUMN ] column_name\
    \ TO new_column_name"
  - "ALTER FOREIGN TABLE [ IF EXISTS ] name RENAME TO new_name"
  - "ALTER FOREIGN TABLE [ IF EXISTS ] name SET SCHEMA new_schema"
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
    - if_exists_clause
    - column_data_type
    - only_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - column_name_shape
    - new_column_name_shape
    - new_table_name_shape
    - new_schema_name_shape
    - owner_name_shape
    - constraint_name_shape
    - parent_table_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_existence
    - type_usage_privilege
    - parent_table_existence
    - set_role_capability
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_table
    - nonexistent_column
    - nonexistent_constraint
    - non_owner_attempt
    - no_type_usage_privilege
    - nonexistent_parent_table
    - constraint_not_enforced
    - validate_constraint_no_action
    - consistency_not_checked
    - if_exists_notice
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
      - key: branch_action_list
        label: ALTER FOREIGN TABLE action [, ... ]
      - key: branch_rename_column
        label: ALTER FOREIGN TABLE RENAME COLUMN column_name TO new_column_name
      - key: branch_rename_table
        label: ALTER FOREIGN TABLE RENAME TO new_name
      - key: branch_set_schema
        label: ALTER FOREIGN TABLE SET SCHEMA new_schema
    object_state:
      label: 目标 foreign table 对象状态
      importance: important
      values:
      - key: exists
        label: 表已存在
      - key: not_exists
        label: 表不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    alter_action:
      label: ALTER 行为类型
      importance: important
      values:
      - key: add_column
        label: ADD COLUMN
      - key: drop_column
        label: DROP COLUMN
      - key: alter_column_type
        label: ALTER COLUMN SET DATA TYPE
      - key: set_not_null
        label: ALTER COLUMN SET NOT NULL
      - key: drop_not_null
        label: ALTER COLUMN DROP NOT NULL
      - key: set_default
        label: ALTER COLUMN SET DEFAULT
      - key: drop_default
        label: ALTER COLUMN DROP DEFAULT
      - key: add_constraint
        label: ADD table_constraint [ NOT VALID ]
      - key: drop_constraint
        label: DROP CONSTRAINT
      - key: validate_constraint
        label: VALIDATE CONSTRAINT
      - key: inherit
        label: INHERIT parent_table
      - key: no_inherit
        label: NO INHERIT parent_table
      - key: owner
        label: OWNER TO
      - key: options
        label: OPTIONS ( ADD / SET / DROP )
      - key: column_options
        label: ALTER COLUMN OPTIONS
      - key: set_without_oids
        label: SET WITHOUT OIDS
      - key: enable_trigger
        label: ENABLE TRIGGER
      - key: disable_trigger
        label: DISABLE TRIGGER
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: important
      values:
      - key: absent
        label: 省略 IF EXISTS
      - key: present
        label: 指定 IF EXISTS
    column_data_type:
      label: ADD COLUMN / ALTER COLUMN TYPE 的数据类型
      importance: non_important
      values:
      - key: integer
        label: integer
      - key: bigint
        label: bigint
      - key: text
        label: text
      - key: varchar
        label: character varying
      - key: numeric
        label: numeric
      - key: boolean
        label: boolean
      - key: date
        label: date
      - key: timestamp
        label: timestamp
      - key: jsonb
        label: jsonb
      - key: uuid
        label: uuid
    only_clause:
      label: ONLY 子句开关
      importance: non_important
      values:
      - key: omitted
        label: 省略 ONLY
      - key: specified
        label: 指定 ONLY
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: schema_qualified
        label: Schema 限定标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_name
        label: 不存在的表名
    column_name_shape:
      label: 列名形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_column
        label: 不存在的列名
    new_column_name_shape:
      label: RENAME COLUMN 新名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
    new_table_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
    new_schema_name_shape:
      label: SET SCHEMA 目标 schema 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: nonexistent_schema
        label: 不存在的 schema
    owner_name_shape:
      label: OWNER TO 目标角色名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: specified_current_role
        label: CURRENT_ROLE
      - key: specified_current_user
        label: CURRENT_USER
      - key: specified_session_user
        label: SESSION_USER
      - key: nonexistent_role
        label: 不存在的角色
    constraint_name_shape:
      label: 约束名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: nonexistent_constraint
        label: 不存在的约束名
    parent_table_name_shape:
      label: INHERIT/NO INHERIT 父表名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: nonexistent_parent
        label: 不存在的父表
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: table_owner
        label: 表 owner → success
      - key: non_owner
        label: 非 owner → error
      - key: superuser
        label: superuser → success
    schema_existence:
      label: SET SCHEMA 目标 schema 存在性
      importance: non_important
      values:
      - key: schema_exists
        label: 目标 schema 存在
      - key: schema_not_exists
        label: 目标 schema 不存在 → error
    type_usage_privilege:
      label: ADD COLUMN / ALTER COLUMN TYPE 的数据类型 USAGE 权限
      importance: non_important
      values:
      - key: has_usage
        label: 有 USAGE 权限 → success
      - key: lacks_usage
        label: 无 USAGE 权限 → error
    parent_table_existence:
      label: INHERIT 父表存在性
      importance: non_important
      values:
      - key: parent_exists
        label: 父表存在 → success
      - key: parent_not_exists
        label: 父表不存在 → error
    set_role_capability:
      label: OWNER TO 时能否 SET ROLE 到新 owner
      importance: non_important
      values:
      - key: can_set_role
        label: 可以 SET ROLE → success
      - key: cannot_set_role
        label: 不能 SET ROLE → error
    nonexistent_table:
      label: 目标表不存在且无 IF EXISTS
      importance: non_important
      values:
      - key: table_exists
        label: 表存在
      - key: table_missing_no_if_exists
        label: 表不存在且无 IF EXISTS → error
    nonexistent_column:
      label: DROP/ALTER 引用的列不存在
      importance: non_important
      values:
      - key: column_exists
        label: 列存在
      - key: column_missing
        label: 列不存在 → error (无 IF EXISTS)
      - key: column_missing_if_exists
        label: 列不存在 + IF EXISTS → notice
    nonexistent_constraint:
      label: DROP/VALIDATE 引用的约束不存在
      importance: non_important
      values:
      - key: constraint_exists
        label: 约束存在
      - key: constraint_missing
        label: 约束不存在 → error (无 IF EXISTS)
    non_owner_attempt:
      label: 非 owner 尝试 ALTER FOREIGN TABLE
      importance: non_important
      values:
      - key: owner_execution
        label: 表 owner 执行 → success
      - key: non_owner_execution
        label: 非 owner 执行 → error
      - key: superuser_execution
        label: superuser 执行 → success
    no_type_usage_privilege:
      label: 无数据类型 USAGE 权限
      importance: non_important
      values:
      - key: has_usage
        label: 有 USAGE 权限 → success
      - key: lacks_usage
        label: 无 USAGE 权限 → error
    nonexistent_parent_table:
      label: INHERIT 父表不存在
      importance: non_important
      values:
      - key: parent_exists
        label: 父表存在
      - key: parent_missing
        label: 父表不存在 → error
    constraint_not_enforced:
      label: ADD CONSTRAINT 仅声明不强制
      importance: non_important
      values:
      - key: with_check_constraint
        label: ADD CHECK constraint (仅声明)
      - key: with_not_valid
        label: ADD CHECK NOT VALID (仅声明且标记为未验证)
    validate_constraint_no_action:
      label: VALIDATE CONSTRAINT 不执行验证
      importance: non_important
      values:
      - key: validate_marks_valid
        label: VALIDATE CONSTRAINT 仅标记为有效 (不执行验证)
    consistency_not_checked:
      label: ADD/DROP/ALTER COLUMN 不检查与远程端一致性
      importance: non_important
      values:
      - key: no_consistency_check
        label: 列变更与远程端一致性不被检查 (行为边界)
    if_exists_notice:
      label: IF EXISTS 遇不存在对象的 notice 路径
      importance: non_important
      values:
      - key: no_notice
        label: 不使用 IF EXISTS 或对象存在
      - key: notice_no_op
        label: IF EXISTS 遇不存在 → notice (no-op)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询
      - key: pg_attribute_catalog_query
        label: pg_attribute 列信息查询
      - key: effect_query
        label: 效果查询
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: revert_alter
        label: 还原 ALTER 变更
      - key: drop_foreign_table
        label: DROP FOREIGN TABLE
      - key: role_cleanup
        label: 角色/权限清理
      - key: schema_cleanup
        label: Schema 清理
  notes:
    owner_privilege: ALTER FOREIGN TABLE 必须由表 owner 执行。
    type_usage_for_columns: ADD COLUMN / ALTER COLUMN TYPE 需要 USAGE 权限于数据类型。
    set_schema_requires_create: SET SCHEMA 还需要 CREATE 权限于新 schema。
    owner_requires_set_role: OWNER TO 需要能够 SET ROLE 到新 owner。
    constraint_not_enforced: CHECK 约束仅声明不强制，VALIDATE CONSTRAINT 不执行验证。
    consistency_not_checked: 列变更与远程端的一致性不被 PostgreSQL 自动检查。
    enable_trigger_superuser: ENABLE TRIGGER ALL (含内部触发器) 需要 superuser 权限。
    column_type_involvement: ALTER COLUMN SET DATA TYPE 和 ADD COLUMN 涉及数据类型选择。
  defaults:
    expected_status: success
    privilege_level: table_owner
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - if_exists_clause
    - column_data_type
    - only_clause
    - table_name_shape
    - column_name_shape
    - new_column_name_shape
    - new_table_name_shape
    - new_schema_name_shape
    - owner_name_shape
    - constraint_name_shape
    - parent_table_name_shape
    - privilege_level
    - schema_existence
    - type_usage_privilege
    - parent_table_existence
    - set_role_capability
    - nonexistent_table
    - nonexistent_column
    - nonexistent_constraint
    - non_owner_attempt
    - no_type_usage_privilege
    - nonexistent_parent_table
    - constraint_not_enforced
    - validate_constraint_no_action
    - consistency_not_checked
    - if_exists_notice
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER FOREIGN TABLE [ IF EXISTS ] {table_name} {alter_clause}"
    verification_query_template: "SELECT relname FROM pg_class WHERE relname = '{table_name}' AND relkind = 'f'"
    factor_value_bindings: {}
```
