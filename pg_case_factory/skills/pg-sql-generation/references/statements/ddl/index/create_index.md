# 技能：CREATE INDEX

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createindex.html

```sql
CREATE [ UNIQUE ] INDEX [ CONCURRENTLY ] [ [ IF NOT EXISTS ] name ] ON [ ONLY ] table_name [ USING method ]
    ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass [ ( opclass_parameter = value [, ... ] ) ] ] [ ASC | DESC ] [ NULLS { FIRST | LAST } ] [, ...] )
    [ INCLUDE ( column_name [, ...] ) ]
    [ NULLS [ NOT ] DISTINCT ]
    [ WITH ( storage_parameter [= value] [, ... ] ) ]
    [ TABLESPACE tablespace_name ]
    [ WHERE predicate ]
```

## 语句作用

用于描述普通表上的 PostgreSQL CREATE INDEX 生成规则。该语句用于在指定表上创建索引，以提升查询访问效率；可生成普通索引、唯一索引、部分索引、覆盖索引，并支持不同索引方法与并发构建模式。

这个 skill 承担如下职责：

- 定义测试因子与覆盖策略
- 定义 CREATE INDEX 的 SQL 生成范围
- 标识各语法分支的前置依赖与失败路径边界

## 语法范围

CREATE [ UNIQUE ] INDEX [ CONCURRENTLY ] [ [ IF NOT EXISTS ] name ] ON [ ONLY ] table_name [ USING method ]
(
  { column_name | ( expression ) } [ COLLATE collation ] [ opclass [ ( opclass_parameter = value [, ... ] ) ] ] [ ASC | DESC ] [ NULLS { FIRST | LAST } ] [, ...]
)
[ INCLUDE ( column_name [, ...] ) ]
[ NULLS [ NOT ] DISTINCT ]
[ WITH ( storage_parameter [= value] [, ... ] ) ]
[ TABLESPACE tablespace_name ]
[ WHERE predicate ]

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 中的顶层语法形式
- method：索引方法
- column_source：列名对应的列类型（不同 method 支持的列类型不同）
- unique：UNIQUE 约束
- predicate：WHERE predicate（部分索引）
- include：INCLUDE（覆盖索引）
- concurrently：CONCURRENTLY（并发构建）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- order：ASC | DESC 排序方向
- nulls：NULLS FIRST | LAST 空值排序
- if_not_exists：IF NOT EXISTS
- nulls_distinct：NULLS [ NOT ] DISTINCT（唯一索引空值处理）
- only：ONLY（分区表不递归）

### T3：对象名与输入形态因子
- name_style：索引名是否显式指定
- collation：COLLATE 子句
- opclass：operator class 指定

### T4：依赖对象与环境因子
- column_type_compatibility：不同索引方法与 PG 数据类型的兼容性矩阵
  - btree：支持几乎所有 PG 标准数据类型（int, float, numeric, text, varchar, date, timestamp, boolean, uuid, bytea, jsonb 等）
  - hash：支持有 hash operator class 的类型（int, text, varchar, date, timestamp 等）
  - gist：支持几何类型（point, box, polygon）、range 类型、tsvector、自定义类型
  - spgist：支持 text 前缀、几何 kd-tree、phone number radix tree 等非平衡结构类型
  - gin：支持 array 类型、tsvector、jsonb、复合类型
  - brin：支持 int, numeric, date, timestamp, geometric types 等可做 min/max 摘要的类型
- with_storage：WITH storage_parameter（各 method 的参数见下文）
- tablespace：TABLESPACE 指定
- expression_index：表达式索引

### T5：异常与边界因子
- invalid_combination：语法合法但语义非法的组合（如 UNIQUE + hash、多列 + hash/spgist、INCLUDE + hash/gin/brin、CONCURRENTLY + 事务块内）
- syntax_error：语法非法的组合
- concurrent_failure：并发构建失败（留下 INVALID 索引）
- partition_constraint：分区表上的限制

### T6：验证与清理因子
- verification_mode：验证方式（pg_catalog 查询、\d 元命令、索引可用性查询）
- cleanup_mode：清理方式（DROP INDEX、ROLLBACK）

## 覆盖策略
- 需要覆盖所有基表。
- 需要覆盖每张基表中所有的列类型。
- T1 和 T2 作为主覆盖因子。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖所有基表列类型。
- 必须覆盖不同 method 下的合法与非法列类型组合。
- 必须同时覆盖成功路径与失败路径。
- UNIQUE 仅在 btree method 下生成成功路径；在其他 method 下作为失败路径覆盖。
- INCLUDE 仅在 btree、gist、spgist method 下生成成功路径；在 hash、gin、brin 下作为失败路径覆盖。
- 多列索引仅在 btree、gist、gin、brin method 下生成成功路径；在 hash、spgist 下作为失败路径覆盖。
- CONCURRENTLY 不能在事务块内执行，必须标注环境依赖。
- T1 因子不得因规模问题被整体省略。
- T2 因子允许降级为代表性覆盖。
- T3-T6 因子仅允许挂靠，不单独扩展为主维度。

## 挂靠规则

- T3 因子挂靠到 T1/T2 已生成样本上轮转注入。
- T4 因子仅挂靠到涉及 storage_parameter、tablespace、表达式索引和列类型兼容性的代表性样本。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖因子的可识别性与可归因性。

## 规模控制规则

- 优先保证：
  - method 全覆盖
  - 列类型全覆盖
  - UNIQUE 全覆盖
  - WHERE predicate 全覆盖
  - INCLUDE 全覆盖
  - CONCURRENTLY 代表性覆盖
- 次优先保证：
  - ASC | DESC 全覆盖
  - NULLS FIRST | LAST 全覆盖
  - IF NOT EXISTS 全覆盖
  - NULLS NOT DISTINCT 全覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 输出要求

- 生成结果应为可执行的 PostgreSQL CREATE INDEX 测试样本集合。
- 输出样本应具备明确因子归因能力。
- 输出样本应避免无意义重复。
- 当采用裁剪策略时，应优先保留核心语义覆盖样本。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: index
  skill_name: create_index
  official_source: https://www.postgresql.org/docs/16/sql-createindex.html
  statement:
    key: create_index
    name: CREATE INDEX
    aliases:
    - create index
    - 创建索引
    - 索引创建
    purpose: 在指定表上创建 PostgreSQL 索引，覆盖 method、列类型、唯一性、部分索引、覆盖索引和并发构建等因子。
  syntax_templates:
  - "CREATE [ UNIQUE ] INDEX [ CONCURRENTLY ] [ [ IF NOT EXISTS ] name ] ON [ ONLY ] table_name [ USING method ] ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass [ ( opclass_parameter = value [, ... ] ) ] ] [ ASC | DESC ] [ NULLS { FIRST | LAST } ] [, ...] ) [ INCLUDE ( column_name [, ...] ) ] [ NULLS [ NOT ] DISTINCT ] [ WITH ( storage_parameter [= value] [, ... ] ) ] [ TABLESPACE tablespace_name ] [ WHERE predicate ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - method
    - column_source
    - unique
    - predicate
    - include
    - concurrently
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - order
    - nulls
    - if_not_exists
    - nulls_distinct
    - only
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_style
    - collation
    - opclass
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - column_type_compatibility
    - with_storage
    - tablespace
    - expression_index
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - syntax_error
    - concurrent_failure
    - partition_constraint
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification_mode
    - cleanup_mode
  factors:
    statement_branch:
      label: 语句分支
      importance: important
      values:
      - key: single_column_btree
        label: 单列 btree 索引
      - key: multi_column_btree
        label: 多列 btree 索引
      - key: unique_btree
        label: 唯一 btree 索引
      - key: partial_index
        label: 部分索引
      - key: covering_index
        label: 覆盖索引（INCLUDE）
      - key: expression_index
        label: 表达式索引
      - key: hash_index
        label: hash 索引
      - key: gist_index
        label: GiST 索引
      - key: spgist_index
        label: SP-GiST 索引
      - key: gin_index
        label: GIN 索引
      - key: brin_index
        label: BRIN 索引
      - key: concurrent_build
        label: 并发构建索引
    method:
      label: index method
      importance: important
      values:
      - btree
      - hash
      - gist
      - spgist
      - gin
      - brin
    column_source:
      label: 列名对应的列类型
      importance: important
      values:
      - all_template_columns
    unique:
      label: UNIQUE
      importance: important
      values:
      - "false"
      - "true"
    predicate:
      label: WHERE predicate
      importance: important
      values:
      - "false"
      - "true"
    include:
      label: INCLUDE
      importance: important
      values:
      - "false"
      - "true"
    concurrently:
      label: CONCURRENTLY
      importance: important
      values:
      - "false"
      - "true"
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    order:
      label: ASC | DESC
      importance: non_important
      values:
      - none
      - asc
      - desc
    nulls:
      label: NULLS FIRST | LAST
      importance: non_important
      values:
      - none
      - first
      - last
    if_not_exists:
      label: IF NOT EXISTS
      importance: non_important
      values:
      - "false"
      - "true"
    nulls_distinct:
      label: NULLS [ NOT ] DISTINCT
      importance: non_important
      values:
      - none
      - distinct
      - not_distinct
    only:
      label: ONLY
      importance: non_important
      values:
      - "false"
      - "true"
    name_style:
      label: 索引名是否显式指定
      importance: non_important
      values:
      - explicit_compact
      - explicit_semantic
      - implicit
    collation:
      label: COLLATE 子句
      importance: non_important
      values:
      - none
      - default_collation
      - non_default_collation
    opclass:
      label: operator class 指定
      importance: non_important
      values:
      - none
      - default_opclass
      - non_default_opclass
    column_type_compatibility:
      label: 列类型与索引方法兼容性
      importance: non_important
      values:
      - btree_compatible
      - hash_compatible
      - gist_compatible
      - spgist_compatible
      - gin_compatible
      - brin_compatible
      - method_type_incompatible
    with_storage:
      label: WITH storage_parameter
      importance: non_important
      values:
      - none
      - btree_fillfactor
      - btree_deduplicate_items
      - gist_buffering
      - gin_fastupdate
      - gin_pending_list_limit
      - brin_pages_per_range
      - brin_autosummarize
    tablespace:
      label: TABLESPACE
      importance: non_important
      values:
      - none
      - pg_default
      - custom_tablespace
    expression_index:
      label: 表达式索引
      importance: non_important
      values:
      - column_only
      - simple_expression
      - complex_expression
    invalid_combination:
      label: 语义非法组合
      importance: non_important
      values:
      - unique_with_non_btree
      - include_with_unsupported_method
      - multi_column_with_unsupported_method
      - none
    syntax_error:
      label: 语法非法组合
      importance: non_important
      values:
      - none
      - invalid_syntax
    concurrent_failure:
      label: 并发构建失败
      importance: non_important
      values:
      - none
      - in_transaction_block
      - invalid_index_leftover
    partition_constraint:
      label: 分区表限制
      importance: non_important
      values:
      - none
      - only_on_partitioned
      - concurrently_on_partitioned
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - index_validity_check
      - explain_index_scan
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_index
      - rollback
  defaults:
    order: none
    nulls: none
    if_not_exists: "false"
    nulls_distinct: none
    only: "false"
    name_style: explicit_compact
    collation: none
    opclass: none
    with_storage: none
    tablespace: none
    expression_index: column_only
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - method
    - column_source
    - unique
    - predicate
    - include
    - concurrently
    - expected_status
    non_main_factors:
    - order
    - nulls
    - if_not_exists
    - nulls_distinct
    - only
    - name_style
    - collation
    - opclass
    - column_type_compatibility
    - with_storage
    - tablespace
    - expression_index
    - invalid_combination
    - syntax_error
    - concurrent_failure
    - partition_constraint
    - verification_mode
    - cleanup_mode
    dynamic_factor_sources:
      column_source: base_object_columns
    python_expand_threshold: 200
    preserve_axes_first:
    - method
    - column_source
    - unique
    - predicate
    - include
  rendering:
    statement_template: "CREATE {unique_clause}INDEX {concurrently_clause}{if_not_exists_clause}{index_name_clause}ON {only_clause}{table_name} USING {method} ({column_source}{order_clause}{nulls_clause}){include_clause}{nulls_distinct_clause}{with_clause}{tablespace_clause}{predicate_clause};"
    verification_query_template: "SELECT c.relname AS index_name, i.indisvalid AS is_valid FROM pg_class c JOIN pg_index i ON i.indexrelid = c.oid WHERE c.relname = '{index_name}' ORDER BY c.relname;"
    factor_value_bindings:
      method:
        factor: method
        values:
          btree: btree
          hash: hash
          gist: gist
          spgist: spgist
          gin: gin
          brin: brin
      unique_clause:
        factor: unique
        values:
          "false": ""
          "true": "UNIQUE "
      concurrently_clause:
        factor: concurrently
        values:
          "false": ""
          "true": "CONCURRENTLY "
      if_not_exists_clause:
        factor: if_not_exists
        values:
          "false": ""
          "true": "IF NOT EXISTS "
      only_clause:
        factor: only
        values:
          "false": ""
          "true": "ONLY "
      order_clause:
        factor: order
        values:
          none: ""
          asc: " ASC"
          desc: " DESC"
      nulls_clause:
        factor: nulls
        values:
          none: ""
          first: " NULLS FIRST"
          last: " NULLS LAST"
      nulls_distinct_clause:
        factor: nulls_distinct
        values:
          none: ""
          distinct: " NULLS DISTINCT"
          not_distinct: " NULLS NOT DISTINCT"
      include_clause:
        factor: include
        values:
          "false": ""
          "true": " INCLUDE ({include_columns})"
      with_clause:
        factor: with_storage
        values:
          none: ""
          btree_fillfactor: " WITH (fillfactor = {fillfactor_value})"
          btree_deduplicate_items: " WITH (deduplicate_items = {dedup_value})"
          gist_buffering: " WITH (buffering = {buffering_value})"
          gin_fastupdate: " WITH (fastupdate = {fastupdate_value})"
          gin_pending_list_limit: " WITH (gin_pending_list_limit = {gin_pending_value})"
          brin_pages_per_range: " WITH (pages_per_range = {pages_per_range_value})"
          brin_autosummarize: " WITH (autosummarize = {autosummarize_value})"
      tablespace_clause:
        factor: tablespace
        values:
          none: ""
          pg_default: " TABLESPACE pg_default"
          custom_tablespace: " TABLESPACE {tablespace_name}"
      predicate_clause:
        factor: predicate
        values:
          "false": ""
          "true": " WHERE {predicate_expr}"
```
