# 技能：CREATE PUBLICATION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createpublication.html

```sql
CREATE PUBLICATION name
    [ FOR ALL TABLES
      | FOR publication_object [, ... ] ]
    [ WITH ( publication_parameter [= value] [, ... ] ) ]

where publication_object is one of:

    TABLE table_and_columns [, ...]
    TABLES IN SCHEMA { schema_name | CURRENT_SCHEMA } [, ...]

and table_and_columns is:

    [ ONLY ] table_name [ * ] [ ( column_name [, ... ] ) ] [ WHERE ( expression ) ]
```

**重要约束：**
- CREATE PUBLICATION 需要 superuser 权限。
- FOR ALL TABLES 表示发布当前数据库中所有表（含未来创建的表），不可与 FOR TABLE 或 FOR TABLES IN SCHEMA 同时使用。
- FOR TABLES IN SCHEMA 表示发布 schema 中所有表（含未来创建的表），不可与 FOR ALL TABLES 同时使用。
- publication_parameter 包括 publish、publish_via_partition_root 等。
- 一个 publication 可同时包含 TABLE 和 TABLES IN SCHEMA 对象（但不可与 FOR ALL TABLES 同时使用）。

## 语句作用

官方说明：CREATE PUBLICATION — define a new publication

该 reference 关注发布定义语句的 FOR 子句形态（FOR ALL TABLES / FOR TABLE / FOR TABLES IN SCHEMA）、WITH 参数组合、列筛选与 WHERE 过滤、权限边界和成功/失败路径。CREATE PUBLICATION 需要 superuser 权限，不负责覆盖所有基表列类型。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（FOR ALL TABLES / FOR TABLE / FOR TABLES IN SCHEMA / 无 FOR 子句）
- publication_identity：目标 publication 存在状态
- expected_status：预期结果

### T2：重要行为因子
- for_clause_shape：FOR 子句形态
- with_parameter_clause：WITH ( publication_parameter ) 子句
- column_filter：列筛选子句形态
- where_clause：WHERE 过滤子句形态
- only_keyword：ONLY 关键字形态

### T3：对象名与输入形态因子
- publication_name_shape：publication 名标识符形态
- table_name_shape：表名形态
- schema_name_shape：schema 名形态
- column_name_shape：列名形态

### T4：依赖对象与环境因子
- **CREATE PUBLICATION 需要引用已有的表和 schema 对象。**
- executor_privilege：执行者权限上下文（superuser 必须）
- table_dependency：依赖表对象存在状态
- schema_dependency：依赖 schema 对象存在状态

### T5：异常与边界因子
- duplicate_publication_name：publication 名冲突
- privilege_insufficient：权限不足（非 superuser）
- nonexistent_table：依赖表不存在
- nonexistent_schema：依赖 schema 不存在
- conflicting_for_clause：FOR ALL TABLES 与 FOR TABLE / FOR TABLES IN SCHEMA 互斥
- invalid_where_expression：非法 WHERE 表达式

### T6：验证与清理因子
- verification_mode：验证方式（pg_publication 目录查询）
- cleanup_mode：清理方式（DROP PUBLICATION）

## 覆盖策略

- 覆盖所有 FOR 子句形态（FOR ALL TABLES / FOR TABLE / FOR TABLES IN SCHEMA / 无 FOR 子句）。
- 覆盖 WITH 参数代表性取值（publish / publish_via_partition_root）。
- 覆盖列筛选和 WHERE 过滤的代表性取值。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 publication 成功创建、重名冲突、权限不足与依赖对象缺失路径。
- CREATE PUBLICATION 不支持 IF NOT EXISTS（PG16），重名路径必定失败。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- FOR ALL TABLES 与 FOR TABLE / FOR TABLES IN SCHEMA 互斥冲突路径必须覆盖。
- 每个样本必须包含明确的前置对象准备、目标 CREATE PUBLICATION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或表/schema 依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖（FOR ALL TABLES / FOR TABLE / FOR TABLES IN SCHEMA / 无 FOR）
  - publication 存在/不存在全覆盖
  - 成功/失败路径全覆盖
  - superuser 权限路径全覆盖
- 次优先保证：
  - WITH 参数代表性覆盖
  - 列筛选和 WHERE 过滤代表性覆盖
  - CURRENT_SCHEMA 关键字代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: publication
  skill_name: create_publication
  official_source: https://www.postgresql.org/docs/16/sql-createpublication.html
  statement:
    key: create_publication
    name: CREATE PUBLICATION
    aliases:
    - create_publication
    - CREATE PUBLICATION
    purpose: CREATE PUBLICATION — define a new publication
  syntax_templates:
  - "CREATE PUBLICATION name\n    [ FOR ALL TABLES\n      | FOR publication_object [, ... ] ]\n    [ WITH ( publication_parameter [= value] [, ... ] ) ]\n\nwhere publication_object is one of:\n\n    TABLE table_and_columns [, ...]\n    TABLES IN SCHEMA { schema_name | CURRENT_SCHEMA } [, ...]\n\nand table_and_columns is:\n\n    [ ONLY ] table_name [ * ] [ ( column_name [, ... ] ) ] [ WHERE ( expression ) ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - publication_identity
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - for_clause_shape
    - with_parameter_clause
    - column_filter
    - where_clause
    - only_keyword
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - publication_name_shape
    - table_name_shape
    - schema_name_shape
    - column_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - table_dependency
    - schema_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_publication_name
    - privilege_insufficient
    - nonexistent_table
    - nonexistent_schema
    - conflicting_for_clause
    - invalid_where_expression
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
      - key: branch_for_all_tables
        label: CREATE PUBLICATION name FOR ALL TABLES
      - key: branch_for_table
        label: CREATE PUBLICATION name FOR TABLE table_and_columns
      - key: branch_for_tables_in_schema
        label: CREATE PUBLICATION name FOR TABLES IN SCHEMA schema_name
      - key: branch_no_for
        label: CREATE PUBLICATION name (无 FOR 子句)
    publication_identity:
      label: publication 存在状态
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
    for_clause_shape:
      label: FOR 子句形态
      importance: important
      values:
      - for_all_tables
      - for_table_single
      - for_table_multiple
      - for_tables_in_schema
      - for_tables_in_schema_current_schema
      - for_mixed_table_and_schema
      - no_for_clause
    with_parameter_clause:
      label: WITH 参数子句
      importance: non_important
      values:
      - omitted
      - publish_insert_only
      - publish_all_operations
      - publish_via_partition_root
      - multiple_parameters
    column_filter:
      label: 列筛选子句
      importance: non_important
      values:
      - no_column_filter
      - single_column_filter
      - multiple_column_filter
    where_clause:
      label: WHERE 过滤子句
      importance: non_important
      values:
      - no_where
      - simple_where_condition
      - complex_where_expression
    only_keyword:
      label: ONLY 关键字
      importance: non_important
      values:
      - without_only
      - with_only
    publication_name_shape:
      label: publication 名标识符形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - schema_qualified_name
      - reserved_word_name
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
      - quoted_name
      - current_schema_keyword
      - nonexistent_schema
    column_name_shape:
      label: 列名形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - nonexistent_column
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - non_superuser
    table_dependency:
      label: 依赖表对象存在状态
      importance: non_important
      values:
      - table_exists
      - table_not_exists
      - partition_table
    schema_dependency:
      label: 依赖 schema 对象存在状态
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    duplicate_publication_name:
      label: publication 名冲突
      importance: non_important
      values:
      - none
      - same_name_exists
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - none
      - non_superuser_creating_publication
    nonexistent_table:
      label: 依赖表不存在
      importance: non_important
      values:
      - none
      - table_not_exists_failure
    nonexistent_schema:
      label: 依赖 schema 不存在
      importance: non_important
      values:
      - none
      - schema_not_exists_failure
    conflicting_for_clause:
      label: FOR 子句互斥
      importance: non_important
      values:
      - none
      - for_all_tables_with_for_table_conflict
    invalid_where_expression:
      label: 非法 WHERE 表达式
      importance: non_important
      values:
      - none
      - non_boolean_expression
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
    - publication_identity
    - expected_status
    non_main_factors:
    - for_clause_shape
    - with_parameter_clause
    - column_filter
    - where_clause
    - only_keyword
    - publication_name_shape
    - table_name_shape
    - schema_name_shape
    - column_name_shape
    - executor_privilege
    - table_dependency
    - schema_dependency
    - duplicate_publication_name
    - privilege_insufficient
    - nonexistent_table
    - nonexistent_schema
    - conflicting_for_clause
    - invalid_where_expression
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - publication_identity
  rendering:
    statement_template: "CREATE PUBLICATION {publication_name} [ FOR {for_clause} ] [ WITH ( {parameters} ) ]"
    verification_query_template: "SELECT pubname FROM pg_publication WHERE pubname = '{publication_name}'"
    factor_value_bindings: {}
```
