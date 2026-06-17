# 技能：CREATE MATERIALIZED VIEW

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-creatematerializedview.html

```sql
CREATE MATERIALIZED VIEW [ IF NOT EXISTS ] table_name
    [ (column_name [, ...] ) ]
    [ USING method ]
    [ WITH ( storage_parameter [= value] [, ... ] ) ]
    [ TABLESPACE tablespace_name ]
    AS query
    [ WITH [ NO ] DATA ]
```

## 语句作用

官方说明：CREATE MATERIALIZED VIEW — define a new materialized view

该 reference 关注 materialized view 的创建、查询来源、存储参数和列类型覆盖，不负责定义基础表模板本身。CREATE MATERIALIZED VIEW 涉及列类型（列类型从 query 推导，类似于 CREATE TABLE AS），因此需要覆盖仓库基表的代表性表类型与核心列类型。注意：query 在安全受限操作中执行（例如创建临时表的函数调用会失败）；WITH NO DATA 创建的 materialized view 处于不可扫描状态，必须先 REFRESH 才能查询。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 materialized view 对象状态
- query_shape：查询输入形态
- expected_status：预期结果

### T2：重要行为因子
- if_not_exists_clause：IF NOT EXISTS 子句
- column_list_clause：列名列表子句
- using_clause：USING method 子句
- storage_parameter_clause：WITH storage_parameter 子句
- tablespace_clause：TABLESPACE 子句
- data_clause：WITH [ NO ] DATA 子句
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：materialized view 名形态
- column_type_coverage：列类型覆盖

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- query_source_state：查询源对象状态

### T5：异常与边界因子
- invalid_combination：非法组合
- constraint_boundary：约束与边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 CREATE MATERIALIZED VIEW 语法分支。
- 需要覆盖仓库基表的代表性表类型与核心列类型。
- 列类型从 query 推导，类似于 CREATE TABLE AS 的列类型覆盖逻辑。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- IF NOT EXISTS 需要分别覆盖正常创建、no-op 语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE MATERIALIZED VIEW 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- WITH NO DATA 创建的 materialized view 必须标注不可扫描状态；query 在安全受限操作中执行的限制必须显式标注。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。
- 列类型覆盖因子挂靠到包含代表性数据类型的 query 来源样本上轮转注入。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句（IF NOT EXISTS、WITH DATA/NO DATA、USING、storage_parameter、TABLESPACE）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: materialized_view
  skill_name: create_materialized_view
  official_source: https://www.postgresql.org/docs/16/sql-creatematerializedview.html
  statement:
    key: create_materialized_view
    name: CREATE MATERIALIZED VIEW
    aliases:
    - create materialized view
    - CREATE MATERIALIZED VIEW
    purpose: define a new materialized view
  syntax_templates:
  - "CREATE MATERIALIZED VIEW [ IF NOT EXISTS ] table_name\n    [ (column_name [,\
    \ ...] ) ]\n    [ USING method ]\n    [ WITH ( storage_parameter [= value] [,\
    \ ... ] ) ]\n    [ TABLESPACE tablespace_name ]\n    AS query\n    [ WITH [\
    \ NO ] DATA ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - target_object_state
    - query_shape
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_not_exists_clause
    - column_list_clause
    - using_clause
    - storage_parameter_clause
    - tablespace_clause
    - data_clause
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - column_type_coverage
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - query_source_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - constraint_boundary
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
        label: CREATE MATERIALIZED VIEW 唯一语法分支
    target_object_state:
      label: 目标 materialized view 对象状态
      importance: important
      values:
      - absent
      - exists
      - exists_conflict
    query_shape:
      label: 查询输入形态
      importance: important
      values:
      - minimal_query
      - explicit_values
      - select_from_table
      - cte_source
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_not_exists_clause:
      label: IF NOT EXISTS 子句
      importance: non_important
      values:
      - absent
      - present
    column_list_clause:
      label: 列名列表子句
      importance: non_important
      values:
      - absent
      - present
    using_clause:
      label: USING method 子句
      importance: non_important
      values:
      - absent
      - present
    storage_parameter_clause:
      label: WITH storage_parameter 子句
      importance: non_important
      values:
      - absent
      - present
    tablespace_clause:
      label: TABLESPACE 子句
      importance: non_important
      values:
      - absent
      - present
    data_clause:
      label: WITH [ NO ] DATA 子句
      importance: non_important
      values:
      - with_data
      - with_no_data
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - owner
      - granted_role
      - insufficient_privilege
    name_shape:
      label: materialized view 名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
    column_type_coverage:
      label: 列类型覆盖
      importance: non_important
      values:
      - representative_types
      - derived_from_query
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    query_source_state:
      label: 查询源对象状态
      importance: non_important
      values:
      - source_table_exists
      - source_table_missing
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
      - object_type_mismatch
    constraint_boundary:
      label: 约束与边界
      importance: non_important
      values:
      - none
      - security_restricted_operation
      - unscannable_state
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - effect_query
      - returned_rows
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_objects
      - reset_state
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - target_object_state
    - query_shape
    - expected_status
    non_main_factors:
    - if_not_exists_clause
    - column_list_clause
    - using_clause
    - storage_parameter_clause
    - tablespace_clause
    - data_clause
    - privilege_context
    - name_shape
    - column_type_coverage
    - dependency_state
    - query_source_state
    - invalid_combination
    - constraint_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
    - query_shape
  rendering:
    statement_template: CREATE MATERIALIZED VIEW {table_name} AS {query}
    verification_query_template: ''
    factor_value_bindings: {}
```
