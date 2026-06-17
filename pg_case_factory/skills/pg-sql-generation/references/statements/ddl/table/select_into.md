# 技能：SELECT INTO

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-selectinto.html

```sql
[ WITH [ RECURSIVE ] with_query [, ...] ]
SELECT [ ALL | DISTINCT [ ON ( expression [, ...] ) ] ]
    [ { * | expression [ [ AS ] output_name ] } [, ...] ]
    INTO [ TEMPORARY | TEMP | UNLOGGED ] [ TABLE ] new_table
    [ FROM from_item [, ...] ]
    [ WHERE condition ]
    [ GROUP BY expression [, ...] ]
    [ HAVING condition ]
    [ WINDOW window_name AS ( window_definition ) [, ...] ]
    [ { UNION | INTERSECT | EXCEPT } [ ALL | DISTINCT ] select ]
    [ ORDER BY expression [ ASC | DESC | USING operator ] [ NULLS { FIRST | LAST } ] [, ...] ]
    [ LIMIT { count | ALL } ]
    [ OFFSET start [ ROW | ROWS ] ]
    [ FETCH { FIRST | NEXT } [ count ] { ROW | ROWS } ONLY ]
    [ FOR { UPDATE | SHARE } [ OF table_name [, ...] ] [ NOWAIT ] [...] ]
```

**重要行为说明**：
- SELECT INTO 创建一张新表并将查询结果填入该表。列名与列数据类型均由查询结果派生，无法显式指定。
- SELECT INTO **不支持 IF NOT EXISTS**：目标表已存在时必定报错，不像 CREATE TABLE AS 有 IF NOT EXISTS 保护。
- SELECT INTO **不支持 USING method**、**不支持 TABLESPACE**、**不支持 ON COMMIT**、**不支持 WITH (storage_parameter)**——这些子句仅在 CREATE TABLE AS 中可用。
- TEMPORARY 与 TEMP 是同义词，均创建临时表。
- TABLE 关键字在 INTO 之后是可选的，对语义无影响。
- SELECT INTO 已被官方标记为**废弃（deprecated）**，推荐使用 CREATE TABLE AS 替代（功能更完整）。SELECT INTO 在 ECPG 和 PL/pgSQL 中有不同语义（表示将值选入宿主变量），不可用于表创建。
- SQL 标准中 SELECT INTO 表示将值选入宿主程序的标量变量，PostgreSQL 用于创建表是历史用法。

## 语句作用

官方说明：SELECT INTO — define a new table from the results of a query

该 reference 关注 SELECT INTO 的语法分支、目标表对象状态、查询形态与权限边界，不负责包装所有样本到统一外层事务。

**特别声明**：
- SELECT INTO 不涉及显式列定义与列类型指定——列名与类型均从查询结果自动派生，与 CREATE TABLE AS 相似。
- SELECT INTO 已废弃，CREATE TABLE AS 是推荐替代语句；本 skill 仍需完整覆盖 SELECT INTO 的所有合法语法分支与失败路径。
- SELECT INTO 不支持 IF NOT EXISTS，因此重名冲突路径只有纯失败路径，无 no-op 降级语义。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（永久表、临时表、无日志表）
- object_state：目标表对象存在性（不存在、已存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- table_type：表类型（permanent、temporary、unlogged）
- keyword_table：INTO 后 TABLE 关键字（present、absent）
- temp_modifier：TEMPORARY 与 TEMP 互为别名（TEMPORARY、TEMP）
- query_shape：查询形态（simple_select、select_with_from_where、select_with_join、select_with_subquery、select_with_aggregate）
- with_clause：WITH 子句（with_recursive、with_simple、without_with）
- select_modifier：ALL / DISTINCT 选择修饰符（ALL、DISTINCT、default）

### T3：对象名与输入形态因子
- table_name_shape：目标表名形态（simple、quoted、schema_qualified、reserved_word、non_existent_schema）
- column_name_shape：结果列名形态（inherited_from_query、aliased_with_AS、expression_derived）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、schema_owner、non_owner_with_create、non_owner_no_privilege）
- source_table_dependency：源表依赖（source_table_exists、source_table_not_exists）
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists、pg_catalog_reserved）
- column_type_derivation：列类型派生（从查询结果自动推断，涉及基表的列类型组合）

### T5：异常与边界因子
- duplicate_table_name：重名冲突（无 IF NOT EXISTS 支持，只有失败路径）
- privilege_insufficient：权限不足（无 CREATE 权限）
- query_error：查询错误（源表不存在、表达式无效、类型不匹配）
- schema_not_exists：目标 Schema 不存在
- reserved_schema_name：保留 Schema 名（pg_catalog、information_schema）
- identifier_length_exceeded：标识符长度超限（超过 63 字符）

### T6：验证与清理因子
- verification_mode：验证方式（pg_class_catalog_query、SELECT_count、information_schema_tables）
- cleanup_mode：清理方式（DROP_TABLE_IF_EXISTS）

## 覆盖策略

- 必须覆盖所有 SELECT INTO 语法分支（永久表、临时表、无日志表）。
- 必须覆盖源表查询中涉及的基表与列类型组合——列类型由查询结果派生，基表列类型需代表性覆盖。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 重名冲突路径必须覆盖——SELECT INTO 无 IF NOT EXISTS，重名必定失败。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖对象成功创建、重名冲突（无 IF NOT EXISTS 失败）、权限不足与依赖对象缺失路径。
- SELECT INTO 不支持 IF NOT EXISTS，重名冲突路径只有报错路径，无 no-op 降级语义。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（含源表）、目标 SELECT INTO 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 列类型由查询结果派生，源表列类型组合必须在至少一个 SELECT INTO 样本的查询中被引用。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 column_name_shape 挂靠到含表达式与别名输出的查询样本上。
- T4 因子仅挂靠到需要依赖对象、权限、schema 或源表对象的分支。
- T4 因子中 column_type_derivation 挂靠到代表性成功样本，确保基表列类型组合被覆盖。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T5 因子中 duplicate_table_name 必须覆盖——SELECT INTO 无 IF NOT EXISTS。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（永久表、临时表、无日志表）
  - 目标对象不存在 / 已存在全覆盖
  - 成功 / 失败路径全覆盖（重名冲突仅有失败路径）
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖（TABLE 关键字、TEMPORARY vs TEMP、WITH 子句、DISTINCT）
  - 源表列类型组合代表性覆盖
  - query_shape 代表性覆盖
  - schema、owner 等依赖对象代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: select_into
  official_source: https://www.postgresql.org/docs/16/sql-selectinto.html
  statement:
    key: select_into
    name: SELECT INTO
    aliases:
    - SELECT INTO
    - select into
    - select_into
    purpose: define a new table from the results of a query
  syntax_templates:
  - |
    [ WITH [ RECURSIVE ] with_query [, ...] ]
    SELECT [ ALL | DISTINCT [ ON ( expression [, ...] ) ] ]
        [ { * | expression [ [ AS ] output_name ] } [, ...] ]
        INTO [ TEMPORARY | TEMP | UNLOGGED ] [ TABLE ] new_table
        [ FROM from_item [, ...] ]
        [ WHERE condition ]
        [ GROUP BY expression [, ...] ]
        [ HAVING condition ]
        [ WINDOW window_name AS ( window_definition ) [, ...] ]
        [ { UNION | INTERSECT | EXCEPT } [ ALL | DISTINCT ] select ]
        [ ORDER BY expression [ ASC | DESC | USING operator ] [ NULLS { FIRST | LAST } ] [, ...] ]
        [ LIMIT { count | ALL } ]
        [ OFFSET start [ ROW | ROWS ] ]
        [ FETCH { FIRST | NEXT } [ count ] { ROW | ROWS } ONLY ]
        [ FOR { UPDATE | SHARE } [ OF table_name [, ...] ] [ NOWAIT ] [...] ]
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
    - keyword_table
    - temp_modifier
    - query_shape
    - with_clause
    - select_modifier
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - column_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - source_table_dependency
    - schema_dependency
    - column_type_derivation
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_table_name
    - privilege_insufficient
    - query_error
    - schema_not_exists
    - reserved_schema_name
    - identifier_length_exceeded
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
      - key: branch_permanent
        label: SELECT INTO new_table (永久表)
      - key: branch_temporary
        label: SELECT INTO TEMPORARY/TEMP [TABLE] new_table (临时表)
      - key: branch_unlogged
        label: SELECT INTO UNLOGGED [TABLE] new_table (无日志表)
    object_state:
      label: 目标表对象存在性
      importance: important
      values:
      - key: not_exists
        label: 表不存在
      - key: already_exists
        label: 表已存在
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
      - key: temporary
        label: 临时表 (TEMPORARY/TEMP)
      - key: unlogged
        label: 无日志表 (UNLOGGED)
    keyword_table:
      label: INTO 后 TABLE 关键字
      importance: important
      values:
      - key: present
        label: 包含 TABLE 关键字
      - key: absent
        label: 不包含 TABLE 关键字
    temp_modifier:
      label: 临时表修饰词
      importance: important
      values:
      - key: TEMPORARY
        label: TEMPORARY (全称)
      - key: TEMP
        label: TEMP (简称，与 TEMPORARY 同义)
    query_shape:
      label: 查询形态
      importance: important
      values:
      - key: simple_select
        label: SELECT * FROM source_table
      - key: select_with_from_where
        label: SELECT ... FROM ... WHERE ...
      - key: select_with_join
        label: SELECT ... FROM ... JOIN ...
      - key: select_with_subquery
        label: SELECT ... FROM (subquery)
      - key: select_with_aggregate
        label: SELECT aggregate_func(...) FROM ...
    with_clause:
      label: WITH 子句
      importance: important
      values:
      - key: without_with
        label: 无 WITH 子句
      - key: with_simple
        label: WITH CTE (非递归)
      - key: with_recursive
        label: WITH RECURSIVE CTE
    select_modifier:
      label: SELECT 修饰符
      importance: non_important
      values:
      - key: default
        label: 无修饰符 (隐式 ALL)
      - key: ALL
        label: SELECT ALL
      - key: DISTINCT
        label: SELECT DISTINCT
    table_name_shape:
      label: 目标表名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: schema_qualified
        label: Schema 限定标识符
      - key: reserved_word
        label: 保留字标识符
      - key: non_existent_schema
        label: 引用不存在的 Schema
    column_name_shape:
      label: 结果列名形态
      importance: non_important
      values:
      - key: inherited_from_query
        label: 列名从查询直接继承
      - key: aliased_with_AS
        label: 列名通过 AS output_name 指定
      - key: expression_derived
        label: 列名从表达式自动生成
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: schema_owner
        label: Schema Owner
      - key: non_owner_with_create
        label: 非 Owner 但有 CREATE 权限
      - key: non_owner_no_privilege
        label: 非 Owner 且无 CREATE 权限
    source_table_dependency:
      label: 源表依赖
      importance: non_important
      values:
      - key: source_table_exists
        label: 源表存在
      - key: source_table_not_exists
        label: 源表不存在
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
    column_type_derivation:
      label: 列类型派生
      importance: non_important
      values:
      - key: from_query_result
        label: 从查询结果自动推断 (列类型由源表列类型派生)
    duplicate_table_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: without_if_not_exists_error
        label: 重名 + 无 IF NOT EXISTS → 必定报错 (SELECT INTO 不支持 IF NOT EXISTS)
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: no_create_privilege_in_schema
        label: 在 Schema 中无 CREATE 权限
    query_error:
      label: 查询错误
      importance: non_important
      values:
      - key: source_table_not_exists
        label: 源表不存在
      - key: expression_invalid
        label: 查询表达式无效
      - key: type_mismatch
        label: 查询结果类型不匹配
    schema_not_exists:
      label: 目标 Schema 不存在
      importance: non_important
      values:
      - key: target_schema_absent
        label: 目标 Schema 不存在导致失败
    reserved_schema_name:
      label: 保留 Schema 名
      importance: non_important
      values:
      - key: pg_catalog
        label: pg_catalog
      - key: information_schema
        label: information_schema
    identifier_length_exceeded:
      label: 标识符长度超限
      importance: non_important
      values:
      - key: over_63_chars
        label: 目标表名超过 63 字符
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询
      - key: SELECT_count
        label: SELECT count(*) 验证
      - key: information_schema_tables
        label: information_schema.tables 查询
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_TABLE_IF_EXISTS
        label: DROP TABLE IF EXISTS table_name
  notes:
    deprecated: SELECT INTO 已废弃，官方推荐使用 CREATE TABLE AS 替代。SELECT INTO 在 ECPG 和 PL/pgSQL 中语义不同（选入变量），不可用于表创建。
    no_if_not_exists: SELECT INTO 不支持 IF NOT EXISTS 子句，目标表已存在时必定报错，不像 CREATE TABLE AS 有 no-op 降级语义。
    no_table_options: SELECT INTO 不支持 USING method、TABLESPACE、ON COMMIT、WITH (storage_parameter)，这些仅在 CREATE TABLE AS 中可用。
    column_type_derivation: 列名与列数据类型均由查询结果自动派生，无法显式指定列定义。
    temporary_alias: TEMPORARY 与 TEMP 是同义词，均创建临时表。
    keyword_table_optional: INTO 后的 TABLE 关键字是可选的，对语义无影响。
    sql_standard_note: SQL 标准中 SELECT INTO 表示将值选入宿主程序标量变量，PostgreSQL 用于创建表是历史用法。
  defaults:
    expected_status: success
    table_type: permanent
    keyword_table: absent
    temp_modifier: TEMPORARY
    query_shape: simple_select
    with_clause: without_with
    select_modifier: default
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - table_type
    - keyword_table
    - temp_modifier
    - query_shape
    - with_clause
    - select_modifier
    - table_name_shape
    - column_name_shape
    - privilege_level
    - source_table_dependency
    - schema_dependency
    - column_type_derivation
    - duplicate_table_name
    - privilege_insufficient
    - query_error
    - schema_not_exists
    - reserved_schema_name
    - identifier_length_exceeded
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "SELECT {select_list} INTO [ TEMPORARY | TEMP | UNLOGGED ] [ TABLE ] {new_table} [ FROM {from_item} ] [ WHERE {condition} ]"
    verification_query_template: "SELECT count(*) FROM pg_class WHERE relname = '{new_table}'"
    factor_value_bindings:
      table_type:
        permanent: ""
        temporary: "TEMPORARY"
        unlogged: "UNLOGGED"
      keyword_table:
        present: "TABLE"
        absent: ""
      temp_modifier:
        TEMPORARY: "TEMPORARY"
        TEMP: "TEMP"
```
