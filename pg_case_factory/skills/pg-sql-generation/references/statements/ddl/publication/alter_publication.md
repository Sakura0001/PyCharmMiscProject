# 技能：ALTER PUBLICATION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterpublication.html

```sql
ALTER PUBLICATION name ADD publication_object [, ...]
ALTER PUBLICATION name SET publication_object [, ...]
ALTER PUBLICATION name DROP publication_drop_object [, ...]
ALTER PUBLICATION name SET ( publication_parameter [= value] [, ... ] )
ALTER PUBLICATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER PUBLICATION name RENAME TO new_name

where publication_object is one of:

    TABLE table_and_columns [, ... ]
    TABLES IN SCHEMA { schema_name | CURRENT_SCHEMA } [, ... ]

and publication_drop_object is one of:

    TABLE [ ONLY ] table_name [ * ] [, ... ]
    TABLES IN SCHEMA { schema_name | CURRENT_SCHEMA } [, ... ]

and table_and_columns is:

    [ ONLY ] table_name [ * ] [ ( column_name [, ... ] ) ] [ WHERE ( expression ) ]
```

**重要约束：**
- ALTER PUBLICATION 需要 superuser 权限或 publication 的 owner 角色。
- ADD / SET / DROP 分支操作 publication 的成员对象（表或 schema）。
- SET ( publication_parameter ) 分支修改发布参数（publish / publish_via_partition_root）。
- OWNER TO 需要 superuser 或 CREATEROLE 权限。
- RENAME TO 需要 superuser 或 CREATEROLE 权限。
- ALTER PUBLICATION 不支持 IF EXISTS。

## 语句作用

官方说明：ALTER PUBLICATION — change the definition of a publication

该 reference 关注发布修改语句的 6 个语法分支、ADD/SET/DROP 对象操作、参数变更、所有权变更、重命名行为和权限边界。ALTER PUBLICATION 需要 superuser 权限。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（ADD / SET publication_object / DROP / SET parameter / OWNER TO / RENAME TO）
- publication_state：目标 publication 存在状态
- expected_status：预期结果

### T2：重要行为因子
- add_set_drop_operation：ADD / SET / DROP 操作类型
- publication_parameter：SET 参数子句形态
- owner_to_clause：OWNER TO 子句形态
- column_filter：列筛选子句（ADD/SET 分支）
- where_clause：WHERE 过滤子句（ADD/SET 分支）

### T3：对象名与输入形态因子
- publication_name_shape：publication 名形态
- table_name_shape：表名形态
- schema_name_shape：schema 名形态
- new_name_shape：新名形态（RENAME 分支）
- new_owner_shape：新 owner 形态（OWNER TO 分支）

### T4：依赖对象与环境因子
- **ALTER PUBLICATION 需要引用已有的表和 schema 对象。**
- executor_privilege：执行者权限上下文
- table_dependency：依赖表对象存在状态
- schema_dependency：依赖 schema 对象存在状态

### T5：异常与边界因子
- nonexistent_publication：publication 不存在
- privilege_insufficient：权限不足
- nonexistent_table：依赖表不存在
- nonexistent_schema：依赖 schema 不存在
- drop_from_for_all_tables：从 FOR ALL TABLES publication 中 DROP 的限制
- conflicting_add_existing_table：ADD 已存在的表到 publication

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖所有 6 个 ALTER PUBLICATION 语法分支。
- 覆盖 ADD / SET / DROP 操作的代表性对象类型（TABLE / TABLES IN SCHEMA）。
- 覆盖 SET ( publication_parameter ) 的代表性参数取值。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 publication，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 publication 存在时的成功修改路径、publication 不存在时的失败路径。
- ADD / SET / DROP / SET parameter / OWNER TO / RENAME TO 各分支需要保持独立归因。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 每个样本必须包含明确的前置对象准备、目标 ALTER PUBLICATION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或表/schema 依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有 6 个语法分支全覆盖
  - publication 存在/不存在全覆盖
  - 成功/失败路径全覆盖
  - superuser 权限路径全覆盖
- 次优先保证：
  - ADD/SET/DROP 对象操作类型代表性覆盖
  - SET 参数代表性覆盖
  - CURRENT_SCHEMA 关键字代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: publication
  skill_name: alter_publication
  official_source: https://www.postgresql.org/docs/16/sql-alterpublication.html
  statement:
    key: alter_publication
    name: ALTER PUBLICATION
    aliases:
    - alter_publication
    - ALTER PUBLICATION
    purpose: ALTER PUBLICATION — change the definition of a publication
  syntax_templates:
  - "ALTER PUBLICATION name ADD publication_object [, ...]"
  - "ALTER PUBLICATION name SET publication_object [, ...]"
  - "ALTER PUBLICATION name DROP publication_drop_object [, ...]"
  - "ALTER PUBLICATION name SET ( publication_parameter [= value] [, ... ] )"
  - "ALTER PUBLICATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER PUBLICATION name RENAME TO new_name"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - publication_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - add_set_drop_operation
    - publication_parameter
    - owner_to_clause
    - column_filter
    - where_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - publication_name_shape
    - table_name_shape
    - schema_name_shape
    - new_name_shape
    - new_owner_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - table_dependency
    - schema_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_publication
    - privilege_insufficient
    - nonexistent_table
    - nonexistent_schema
    - drop_from_for_all_tables
    - conflicting_add_existing_table
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
      - key: branch_add
        label: ALTER PUBLICATION name ADD publication_object
      - key: branch_set_object
        label: ALTER PUBLICATION name SET publication_object
      - key: branch_drop
        label: ALTER PUBLICATION name DROP publication_drop_object
      - key: branch_set_parameter
        label: ALTER PUBLICATION name SET ( publication_parameter )
      - key: branch_owner_to
        label: ALTER PUBLICATION name OWNER TO new_owner
      - key: branch_rename
        label: ALTER PUBLICATION name RENAME TO new_name
    publication_state:
      label: 目标 publication 存在状态
      importance: important
      values:
      - exists
      - non_existent
      - exists_as_for_all_tables
      - exists_with_tables
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    add_set_drop_operation:
      label: ADD / SET / DROP 操作类型
      importance: important
      values:
      - add_table
      - add_tables_in_schema
      - set_table
      - set_tables_in_schema
      - drop_table
      - drop_tables_in_schema
    publication_parameter:
      label: SET 参数子句形态
      importance: non_important
      values:
      - publish_insert_only
      - publish_all_operations
      - publish_via_partition_root
      - multiple_parameters
    owner_to_clause:
      label: OWNER TO 子句形态
      importance: non_important
      values:
      - explicit_role_name
      - current_role_keyword
      - current_user_keyword
      - session_user_keyword
    column_filter:
      label: 列筛选子句（ADD/SET 分支）
      importance: non_important
      values:
      - no_column_filter
      - single_column_filter
      - multiple_column_filter
    where_clause:
      label: WHERE 过滤子句（ADD/SET 分支）
      importance: non_important
      values:
      - no_where
      - simple_where_condition
    publication_name_shape:
      label: publication 名形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - non_existent_name
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - simple_name
      - schema_qualified_name
      - quoted_name
      - nonexistent_table
    schema_name_shape:
      label: schema 名形态
      importance: non_important
      values:
      - simple_name
      - current_schema_keyword
      - quoted_name
      - nonexistent_schema
    new_name_shape:
      label: 新名形态（RENAME 分支）
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - existing_name_conflict
    new_owner_shape:
      label: 新 owner 形态（OWNER TO 分支）
      importance: non_important
      values:
      - existing_role
      - nonexistent_role
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - owner_of_publication
      - non_owner_no_privilege
    table_dependency:
      label: 依赖表对象存在状态
      importance: non_important
      values:
      - table_exists
      - table_not_exists
    schema_dependency:
      label: 依赖 schema 对象存在状态
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    nonexistent_publication:
      label: publication 不存在
      importance: non_important
      values:
      - publication_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_owner_altering_publication
      - non_superuser_altering_other_publication
    nonexistent_table:
      label: 依赖表不存在
      importance: non_important
      values:
      - add_nonexistent_table_failure
    nonexistent_schema:
      label: 依赖 schema 不存在
      importance: non_important
      values:
      - add_nonexistent_schema_failure
    drop_from_for_all_tables:
      label: FOR ALL TABLES 限制
      importance: non_important
      values:
      - cannot_drop_from_for_all_tables
    conflicting_add_existing_table:
      label: ADD 已存在表冲突
      importance: non_important
      values:
      - table_already_in_publication
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_publication_catalog
      - pg_publication_tables_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_publication
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - publication_state
    - expected_status
    non_main_factors:
    - add_set_drop_operation
    - publication_parameter
    - owner_to_clause
    - column_filter
    - where_clause
    - publication_name_shape
    - table_name_shape
    - schema_name_shape
    - new_name_shape
    - new_owner_shape
    - executor_privilege
    - table_dependency
    - schema_dependency
    - nonexistent_publication
    - privilege_insufficient
    - nonexistent_table
    - nonexistent_schema
    - drop_from_for_all_tables
    - conflicting_add_existing_table
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - publication_state
  rendering:
    statement_template: "ALTER PUBLICATION {name} {operation}"
    verification_query_template: "SELECT pubname FROM pg_publication WHERE pubname = '{name}'"
    factor_value_bindings: {}
```
