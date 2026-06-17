# 技能：CREATE TABLE AS

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createtableas.html

```sql
CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name
    [ ( column_name [, ...] ) ]
    [ USING method ]
    [ WITH ( storage_parameter [= value ] [, ... ] ) | WITHOUT OIDS ]
    [ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]
    [ TABLESPACE tablespace_name ]
    AS query
    [ WITH [ NO ] DATA ]
```

**重要行为说明**：
- CREATE TABLE AS 创建新表并**仅执行一次**查询填充数据。新表不会跟踪源表的后续变更（与视图不同）。
- 列名和数据类型从源查询的输出列**自动派生**，除非通过显式列名列表覆盖列名（列类型仍由查询决定）。
- query 可以是 SELECT、TABLE、VALUES 或 EXECUTE（执行预备语句）。
- WITH DATA 为默认行为；WITH NO DATA 仅复制表结构不复制数据。
- 需要 CREATE 权限在目标 schema 上。
- CREATE TABLE AS 是 SELECT INTO 的首选替代，提供更多功能。
- ON COMMIT 子句仅适用于临时表，对永久表无效。
- GLOBAL / LOCAL 关键字已被弃用，仅为兼容性保留，实际行为相同。

## 语句作用

官方说明：CREATE TABLE AS — define a new table from the results of a query

该 reference 关注从查询结果创建表的语法分支、查询形态、列类型派生行为、表类型选项与依赖环境。

**特别声明**：CREATE TABLE AS 不涉及显式列类型定义（列类型由源查询自动派生），但涉及查询形态覆盖——不同查询形态将产生不同列类型组合。查询形态覆盖是本 skill 的核心职责之一。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（常规表、临时表、无日志表，及 IF NOT EXISTS 变体）
- object_state：目标表对象存在性（已存在、不存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- table_type：表类型（permanent、temporary_global、temporary_local、temp_short、unlogged）
- if_not_exists_clause：IF NOT EXISTS 子句（present、absent）
- with_data：数据复制行为（WITH DATA、WITH NO DATA）
- column_names：列名来源（explicit_list、inherit_from_query）
- on_commit_clause：ON COMMIT 子句（PRESERVE_ROWS、DELETE_ROWS、DROP、absent）
- with_storage_clause：存储参数子句（with_storage、without_storage、without_oids）
- tablespace_clause：表空间指定（specified、default）

### T3：对象名与输入形态因子
- table_name_shape：表名形态（simple、quoted、reserved_word、schema_qualified、duplicate）
- query_shape：查询形态（simple_select、table_command、values_command、execute_prepared、aggregate_query、join_query、union_query、subquery）
- column_name_list_shape：列名列表形态（matching_query_columns、fewer_than_query_columns、more_than_query_columns、absent）

### T4：依赖对象与环境因子
- column_type_derivation：列类型派生（由源查询决定——见备注）
- privilege_level：权限级别（superuser、schema_owner_with_create、non_owner_no_privilege）
- source_table_dependency：源表依赖（source_table_exists、source_table_not_exists）
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists、pg_catalog_reserved）
- tablespace_dependency：表空间依赖（default_tablespace、specified_tablespace_exists、specified_tablespace_not_exists）

### T5：异常与边界因子
- duplicate_table_name：重名冲突（with_IF_NOT_EXISTS_noop、without_IF_NOT_EXISTS_error）
- query_error：查询错误（invalid_sql_syntax、references_nonexistent_table、aggregate_mismatch）
- privilege_insufficient：权限不足（no_create_in_schema）
- column_name_mismatch：列名数量不匹配（fewer_names_than_query_columns导致多余列丢弃、more_names_than_query_columns报错）
- on_commit_with_non_temporary：ON COMMIT 与非临时表组合
- empty_query_result：空查询结果集（WITH DATA产生空表、WITH NO DATA仅结构）

### T6：验证与清理因子
- verification_mode：验证方式（pg_class_catalog_query、information_schema_tables、information_schema_columns、SELECT_count、SELECT_star_structure）
- cleanup_mode：清理方式（DROP_TABLE、DROP_TABLE_IF_EXISTS、DROP_TABLE_CASCADE）

## 覆盖策略

- 必须覆盖 CREATE TABLE AS 的所有主要语法变体（常规/临时/无日志 + IF NOT EXISTS）。
- 必须覆盖所有查询形态（SELECT、TABLE、VALUES、EXECUTE）。
- 必须覆盖 WITH DATA 与 WITH NO DATA 行为差异。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- query_shape 因子（T3）按查询形态类别做代表性覆盖，每种查询形态至少一个样本。
- T3 其余因子、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。查询形态覆盖不得被裁剪至零——每种形态至少保留一个代表。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、源表缺失与权限不足路径。
- 支持 IF NOT EXISTS 时，需要分别覆盖正常创建、no-op 语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE TABLE AS 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- **列类型由源查询派生：不同查询形态将产生不同列类型组合，必须确保每种查询形态在至少一个样本中出现。**
- 对需要 superuser、tablespace 目录或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 query_shape 挂靠到代表性成功样本，按查询形态类别轮转注入。
- T3 因子中 table_name_shape、column_name_list_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限、schema 或 tablespace 的分支。
- T4 因子中 source_table_dependency 挂靠到涉及源表查询的样本，确保源表存在/缺失路径被覆盖。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 所有表类型全覆盖（permanent、temporary、unlogged）
  - 所有查询形态代表性覆盖（SELECT、TABLE、VALUES、EXECUTE）
  - WITH DATA / WITH NO DATA 全覆盖
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - ON COMMIT 各选项代表性覆盖（仅临时表）
  - 列名列表与查询列数不匹配边界覆盖
  - schema、owner、tablespace 依赖对象代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - USING method 子句
  - WITH storage_parameter 子句各选项
  - identifier 边界条件

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: create_table_as
  official_source: https://www.postgresql.org/docs/16/sql-createtableas.html
  statement:
    key: create_table_as
    name: CREATE TABLE AS
    aliases:
    - CREATE TABLE AS
    - create table as
    - create_table_as
    - CTAS
    - ctas
    purpose: define a new table from the results of a query
  syntax_templates:
  - |
    CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name
        [ ( column_name [, ...] ) ]
        [ USING method ]
        [ WITH ( storage_parameter [= value ] [, ... ] ) | WITHOUT OIDS ]
        [ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]
        [ TABLESPACE tablespace_name ]
        AS query
        [ WITH [ NO ] DATA ]
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
    - table_type
    - if_not_exists_clause
    - with_data
    - column_names
    - on_commit_clause
    - with_storage_clause
    - tablespace_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - query_shape
    - column_name_list_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - column_type_derivation
    - privilege_level
    - source_table_dependency
    - schema_dependency
    - tablespace_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_table_name
    - query_error
    - privilege_insufficient
    - column_name_mismatch
    - on_commit_with_non_temporary
    - empty_query_result
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
      - key: branch_regular
        label: CREATE TABLE AS (常规永久表)
      - key: branch_regular_if_not_exists
        label: CREATE TABLE IF NOT EXISTS AS (常规永久表 + IF NOT EXISTS)
      - key: branch_temporary
        label: CREATE { GLOBAL | LOCAL } TEMPORARY TABLE AS (临时表)
      - key: branch_temp
        label: CREATE TEMP TABLE AS (临时表简写)
      - key: branch_temporary_if_not_exists
        label: CREATE { GLOBAL | LOCAL } TEMPORARY TABLE IF NOT EXISTS AS (临时表 + IF NOT EXISTS)
      - key: branch_unlogged
        label: CREATE UNLOGGED TABLE AS (无日志表)
      - key: branch_unlogged_if_not_exists
        label: CREATE UNLOGGED TABLE IF NOT EXISTS AS (无日志表 + IF NOT EXISTS)
    object_state:
      label: 目标表对象存在性
      importance: important
      values:
      - key: not_exists
        label: 表不存在
      - key: already_exists
        label: 同名表已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    table_type:
      label: 表类型
      importance: important
      values:
      - key: permanent
        label: 普通永久表 (无 TEMPORARY/UNLOGGED)
      - key: temporary_global
        label: 全局临时表 (GLOBAL TEMPORARY)
      - key: temporary_local
        label: 局部临时表 (LOCAL TEMPORARY)
      - key: temp_short
        label: 临时表简写 (TEMP)
      - key: unlogged
        label: 无日志表 (UNLOGGED)
    if_not_exists_clause:
      label: IF NOT EXISTS 子句
      importance: important
      values:
      - key: present
        label: 包含 IF NOT EXISTS
      - key: absent
        label: 不包含 IF NOT EXISTS
    with_data:
      label: 数据复制行为
      importance: important
      values:
      - key: WITH_DATA
        label: WITH DATA (复制查询结果数据，默认行为)
      - key: WITH_NO_DATA
        label: WITH NO DATA (仅复制表结构，不复制数据)
      - key: absent_default
        label: 无显式子句 (默认等同于 WITH DATA)
    column_names:
      label: 列名来源
      importance: important
      values:
      - key: explicit_list
        label: 显式列名列表 (column_name [, ...])
      - key: inherit_from_query
        label: 从查询结果继承列名 (无列名列表)
    on_commit_clause:
      label: ON COMMIT 子句
      importance: important
      values:
      - key: PRESERVE_ROWS
        label: ON COMMIT PRESERVE ROWS (默认行为)
      - key: DELETE_ROWS
        label: ON COMMIT DELETE ROWS (事务结束时清空行)
      - key: DROP
        label: ON COMMIT DROP (事务结束时删除临时表)
      - key: absent
        label: 无 ON COMMIT (默认 PRESERVE ROWS)
    with_storage_clause:
      label: 存储参数子句
      importance: important
      values:
      - key: with_storage
        label: WITH ( storage_parameter [= value] [, ...] )
      - key: without_storage
        label: 无存储参数子句
      - key: without_oids
        label: WITHOUT OIDS (向后兼容语法)
    tablespace_clause:
      label: 表空间指定
      importance: important
      values:
      - key: specified
        label: TABLESPACE tablespace_name (显式指定)
      - key: default
        label: 默认表空间 (无 TABLESPACE 子句)
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: schema_qualified
        label: Schema 限定标识符
      - key: duplicate
        label: 已存在表名
    query_shape:
      label: 查询形态
      importance: non_important
      values:
      - key: simple_select
        label: 简单 SELECT * FROM table
      - key: table_command
        label: TABLE table_name 命令
      - key: values_command
        label: VALUES (...) 常量值列表
      - key: execute_prepared
        label: EXECUTE prepared_statement_name [(params)]
      - key: aggregate_query
        label: 含聚合函数的 SELECT (count/sum/avg 等)
      - key: join_query
        label: 含 JOIN 的 SELECT
      - key: union_query
        label: 含 UNION / UNION ALL 的 SELECT
      - key: subquery
        label: 含子查询的 SELECT
    column_name_list_shape:
      label: 列名列表形态
      importance: non_important
      values:
      - key: matching_query_columns
        label: 列名数量与查询列数匹配
      - key: fewer_than_query_columns
        label: 列名数量少于查询列数 (多余列以原查询列名填充)
      - key: more_than_query_columns
        label: 列名数量多于查询列数 (报错)
      - key: absent
        label: 无列名列表 (全部从查询继承)
    column_type_derivation:
      label: 列类型派生
      importance: non_important
      values:
      - key: derived_from_select_expr
        label: 列类型由 SELECT 表达式结果类型决定
      - key: derived_from_table_command
        label: 列类型由源表列类型完整继承 (TABLE 命令)
      - key: derived_from_values
        label: 列类型由 VALUES 常量推断
      - key: derived_from_execute
        label: 列类型由预备语句查询结果决定
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: schema_owner_with_create
        label: Schema Owner / 有 CREATE 权限
      - key: non_owner_no_privilege
        label: 非 Owner 且无 CREATE 权限
    source_table_dependency:
      label: 源表依赖
      importance: non_important
      values:
      - key: source_table_exists
        label: 源表存在
      - key: source_table_not_exists
        label: 源表不存在 (查询报错)
    schema_dependency:
      label: Schema 依赖
      importance: non_important
      values:
      - key: schema_exists
        label: 目标 Schema 存在
      - key: schema_not_exists
        label: 目标 Schema 不存在
      - key: pg_catalog_reserved
        label: pg_catalog (系统保留 Schema)
    tablespace_dependency:
      label: 表空间依赖
      importance: non_important
      values:
      - key: default_tablespace
        label: 默认表空间
      - key: specified_tablespace_exists
        label: 指定表空间存在
      - key: specified_tablespace_not_exists
        label: 指定表空间不存在
    duplicate_table_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: with_IF_NOT_EXISTS_noop
        label: 重名 + IF NOT EXISTS → no-op (通知而非错误)
      - key: without_IF_NOT_EXISTS_error
        label: 重名 + 无 IF NOT EXISTS → error
    query_error:
      label: 查询错误
      importance: non_important
      values:
      - key: invalid_sql_syntax
        label: 源查询 SQL 语法无效
      - key: references_nonexistent_table
        label: 源查询引用不存在的表
      - key: aggregate_mismatch
        label: 聚合函数与列名列表不匹配
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: no_create_in_schema
        label: 在目标 Schema 中无 CREATE 权限
    column_name_mismatch:
      label: 列名数量不匹配
      importance: non_important
      values:
      - key: fewer_names_extra_columns_kept
        label: 列名少于查询列数 → 多余列保留原查询列名
      - key: more_names_error
        label: 列名多于查询列数 → 报错
    on_commit_with_non_temporary:
      label: ON COMMIT 与非临时表组合
      importance: non_important
      values:
      - key: on_commit_on_permanent_table
        label: ON COMMIT 用于永久表 (语义无效/报错)
    empty_query_result:
      label: 空查询结果集
      importance: non_important
      values:
      - key: with_data_empty_table
        label: WITH DATA + 空结果 → 创建空表
      - key: with_no_data_structure_only
        label: WITH NO DATA → 仅创建结构
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询
      - key: information_schema_tables
        label: information_schema.tables 查询
      - key: information_schema_columns
        label: information_schema.columns 查询 (验证列名/类型派生)
      - key: SELECT_count
        label: SELECT count(*) 验证数据行数
      - key: SELECT_star_structure
        label: SELECT * 验证表结构与数据
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_TABLE
        label: DROP TABLE table_name
      - key: DROP_TABLE_IF_EXISTS
        label: DROP TABLE IF EXISTS table_name
      - key: DROP_TABLE_CASCADE
        label: DROP TABLE table_name CASCADE
  notes:
    column_type_derivation: CREATE TABLE AS 不涉及显式列类型定义。列名和类型从源查询的输出列自动派生，除非通过显式列名列表覆盖列名（类型仍由查询决定）。
    query_forms: 源查询可以是 SELECT、TABLE、VALUES 或 EXECUTE (预备语句)，不同查询形态产生不同的列类型组合。
    vs_select_into: CREATE TABLE AS 是 SELECT INTO 的首选替代，提供更多功能（IF NOT EXISTS、WITH [NO] DATA 等）。
    vs_materialized_view: CREATE MATERIALIZED VIEW 与 CREATE TABLE AS 相似但创建物化视图而非普通表，属于独立语句不纳入本 skill。
    on_commit_scope: ON COMMIT 子句仅适用于临时表；对永久表指定 ON COMMIT 无效或报错。
    global_local_deprecated: GLOBAL / LOCAL 关键字仅为 SQL 标准兼容性保留，在 PostgreSQL 中行为相同，已被弃用。
    without_oids: WITHOUT OIDS 为向后兼容语法；PostgreSQL 16 不支持 WITH OIDS，所有表均不含 OID。
  defaults:
    expected_status: success
    table_type: permanent
    if_not_exists_clause: absent
    with_data: absent_default
    column_names: inherit_from_query
    on_commit_clause: absent
    with_storage_clause: without_storage
    tablespace_clause: default
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - table_type
    - expected_status
    non_main_factors:
    - if_not_exists_clause
    - with_data
    - column_names
    - on_commit_clause
    - with_storage_clause
    - tablespace_clause
    - table_name_shape
    - query_shape
    - column_name_list_shape
    - column_type_derivation
    - privilege_level
    - source_table_dependency
    - schema_dependency
    - tablespace_dependency
    - duplicate_table_name
    - query_error
    - privilege_insufficient
    - column_name_mismatch
    - on_commit_with_non_temporary
    - empty_query_result
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - table_type
  rendering:
    statement_template: "CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name [ ( column_name [, ...] ) ] AS query [ WITH [ NO ] DATA ]"
    verification_query_template: "SELECT count(*) FROM pg_class WHERE relname = '{table_name}'"
    factor_value_bindings:
      table_type:
        permanent: ""
        temporary_global: "GLOBAL TEMPORARY"
        temporary_local: "LOCAL TEMPORARY"
        temp_short: "TEMP"
        unlogged: "UNLOGGED"
      if_not_exists_clause:
        present: "IF NOT EXISTS"
        absent: ""
      with_data:
        WITH_DATA: "WITH DATA"
        WITH_NO_DATA: "WITH NO DATA"
        absent_default: ""
      column_names:
        explicit_list: "( col1, col2, ... )"
        inherit_from_query: ""
      on_commit_clause:
        PRESERVE_ROWS: "ON COMMIT PRESERVE ROWS"
        DELETE_ROWS: "ON COMMIT DELETE ROWS"
        DROP: "ON COMMIT DROP"
        absent: ""
```
