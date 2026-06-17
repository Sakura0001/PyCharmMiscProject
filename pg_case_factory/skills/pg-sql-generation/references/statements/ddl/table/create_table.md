# 技能：CREATE TABLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createtable.html

### Synopsis 形式 1：常规 / 临时 / 无日志表

```sql
CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name ( [
  { column_name data_type [ STORAGE { PLAIN | EXTERNAL | EXTENDED | MAIN | DEFAULT } ] [ COMPRESSION compression_method ] [ COLLATE collation ] [ column_constraint [ ... ] ]
    | table_constraint
    | LIKE source_table [ like_option ... ] }
    [, ... ]
] )
[ INHERITS ( parent_table [, ... ] ) ]
[ PARTITION BY { RANGE | LIST | HASH } ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass ] [, ... ] ) ]
[ USING method ]
[ WITH ( storage_parameter [= value ] [, ... ] ) | WITHOUT OIDS ]
[ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]
[ TABLESPACE tablespace_name ]
```

### Synopsis 形式 2：类型化表 (OF type_name)

```sql
CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name
    OF type_name [ (
  { column_name [ WITH OPTIONS ] [ column_constraint [ ... ] ]
    | table_constraint }
    [, ... ]
) ]
[ PARTITION BY { RANGE | LIST | HASH } ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass ] [, ... ] ) ]
[ USING method ]
[ WITH ( storage_parameter [= value ] [, ... ] ) | WITHOUT OIDS ]
[ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]
[ TABLESPACE tablespace_name ]
```

### Synopsis 形式 3：分区表 (PARTITION OF)

```sql
CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name
    PARTITION OF parent_table [ (
  { column_name [ WITH OPTIONS ] [ column_constraint [ ... ] ]
    | table_constraint }
    [, ... ]
) ] { FOR VALUES partition_bound_spec | DEFAULT }
[ PARTITION BY { RANGE | LIST | HASH } ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass ] [, ... ] ) ]
[ USING method ]
[ WITH ( storage_parameter [= value ] [, ... ] ) | WITHOUT OIDS ]
[ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]
[ TABLESPACE tablespace_name ]
```

### column_constraint

```sql
[ CONSTRAINT constraint_name ]
{ NOT NULL |
  NULL |
  CHECK ( expression ) [ NO INHERIT ] |
  DEFAULT default_expr |
  GENERATED ALWAYS AS ( generation_expr ) STORED |
  GENERATED { ALWAYS | BY DEFAULT } AS IDENTITY [ ( sequence_options ) ] |
  UNIQUE [ NULLS [ NOT ] DISTINCT ] index_parameters |
  PRIMARY KEY index_parameters |
  REFERENCES reftable [ ( refcolumn ) ] [ MATCH FULL | MATCH PARTIAL | MATCH SIMPLE ]
    [ ON DELETE referential_action ] [ ON UPDATE referential_action ] }
[ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]
```

### table_constraint

```sql
[ CONSTRAINT constraint_name ]
{ CHECK ( expression ) [ NO INHERIT ] |
  UNIQUE [ NULLS [ NOT ] DISTINCT ] ( column_name [, ... ] ) index_parameters |
  PRIMARY KEY ( column_name [, ... ] ) index_parameters |
  EXCLUDE [ USING index_method ] ( exclude_element WITH operator [, ... ] ) index_parameters [ WHERE ( predicate ) ] |
  FOREIGN KEY ( column_name [, ... ] ) REFERENCES reftable [ ( refcolumn [, ... ] ) ]
    [ MATCH FULL | MATCH PARTIAL | MATCH SIMPLE ] [ ON DELETE referential_action ] [ ON UPDATE referential_action ] }
[ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]
```

### like_option

```sql
{ INCLUDING | EXCLUDING } { COMMENTS | COMPRESSION | CONSTRAINTS | DEFAULTS | GENERATED | IDENTITY | INDEXES | STATISTICS | STORAGE | ALL }
```

### partition_bound_spec

```sql
IN ( partition_bound_expr [, ... ] ) |
FROM ( { partition_bound_expr | MINVALUE | MAXVALUE } [, ... ] )
  TO ( { partition_bound_expr | MINVALUE | MAXVALUE } [, ... ] ) |
WITH ( MODULUS numeric_literal, REMAINDER numeric_literal )
```

### index_parameters

```sql
[ INCLUDE ( column_name [, ... ] ) ]
[ WITH ( storage_parameter [= value ] [, ... ] ) ]
[ USING INDEX TABLESPACE tablespace_name ]
```

### exclude_element

```sql
{ column_name | ( expression ) } [ COLLATE collation ] [ opclass [ ( opclass_parameter = value [, ... ] ) ] ] [ ASC | DESC ] [ NULLS { FIRST | LAST } ]
```

### referential_action

```sql
{ NO ACTION | RESTRICT | CASCADE | SET NULL [ ( column_name [, ... ] ) ] | SET DEFAULT [ ( column_name [, ... ] ) ] }
```

## 语句作用

官方说明：CREATE TABLE — define a new table

该 reference 关注表定义语句的语法分支、列类型选择、约束定义、分区策略与依赖环境，不负责包装所有样本到统一外层事务。

CREATE TABLE 是 PostgreSQL 中最复杂的 DDL 语句之一，涉及三种 synopsis 形式、多种表类型、六十余种列数据类型、多种约束类型与分区策略。列数据类型覆盖是本 skill 的核心职责。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（常规表、类型化表、分区表）
- object_state：目标表对象存在性（已存在、不存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- table_type：表类型（permanent、temporary、unlogged）
- if_not_exists_clause：IF NOT EXISTS 子句（present、absent）
- column_definition_count：列定义数量（single_column、multiple_columns）
- constraint_type：约束类型（PRIMARY_KEY、UNIQUE、CHECK、FOREIGN_KEY、EXCLUDE、NOT_NULL、NULL、DEFAULT、GENERATED_ALWAYS_STORED、GENERATED_IDENTITY）
- partition_clause：分区子句（RANGE、LIST、HASH、not_partitioned）
- inheritance_clause：继承子句（INHERITS、no_inheritance）
- like_clause：LIKE 子句（LIKE_with_options、LIKE_no_options、no_LIKE）
- on_commit_clause：ON COMMIT 子句（PRESERVE_ROWS、DELETE_ROWS、DROP、absent）

### T3：对象名与输入形态因子
- table_name_shape：表名形态（simple、quoted、reserved_word、schema_qualified、duplicate）
- column_name_shape：列名形态（simple、quoted、reserved_word、duplicate_in_table）
- data_type：列数据类型（完整枚举见下方 factors 定义）
- default_value_shape：默认值形态（with_DEFAULT、without_DEFAULT、expression_DEFAULT）
- collation_clause：排序规则子句（with_COLLATION、without_COLLATION）
- generated_clause：生成列子句（GENERATED_ALWAYS_AS_STORED、GENERATED_ALWAYS_AS_IDENTITY、GENERATED_BY_DEFAULT_AS_IDENTITY、none）

### T4：依赖对象与环境因子
- base_table_template_coverage：基表模板覆盖（table_01_comprehensive_types、table_02_simplified_types、table_03_partition_parent、table_04_typed_table）
- privilege_level：权限级别（superuser、table_owner、non_owner_with_create、non_owner_no_privilege）
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists、pg_catalog_reserved、information_schema_reserved）
- tablespace_dependency：表空间依赖（default_tablespace、specified_tablespace_exists、specified_tablespace_not_exists）
- role_dependency：角色依赖（owner_role_exists、owner_role_not_exists）
- type_dependency：类型依赖（composite_type_exists、composite_type_not_exists）
- parent_table_dependency：父表依赖（parent_table_exists、parent_table_not_exists、parent_table_not_partitioned）
- referenced_table_dependency：外键引用表依赖（referenced_table_exists、referenced_table_not_exists）

### T5：异常与边界因子
- duplicate_table_name：重名冲突（with_IF_NOT_EXISTS_noop、without_IF_NOT_EXISTS_error）
- duplicate_column_name：列名重复
- invalid_data_type：无效数据类型（unknown_type、wrong_array_syntax）
- constraint_violation_in_definition：定义时约束冲突（FK_references_nonexistent_table、CHECK_expression_invalid）
- schema_permission_insufficient：Schema 权限不足
- reserved_schema_name：保留 Schema 名（pg_catalog、information_schema）
- max_column_limit：列数上限（approaching_1600、at_1600、over_1600）
- identifier_length_exceeded：标识符长度超限（over_63_chars）
- temporary_table_scope_conflict：临时表作用域冲突
- partition_bound_invalid：分区边界无效
- on_commit_with_non_temporary：ON COMMIT 与非临时表组合

### T6：验证与清理因子
- verification_mode：验证方式（pg_class_catalog_query、information_schema_tables、information_schema_columns、SELECT_count、pg_attribute_query）
- cleanup_mode：清理方式（DROP_TABLE、DROP_TABLE_IF_EXISTS、DROP_TABLE_CASCADE、DROP_TABLE_CASCADE_RESTRICT）

## 覆盖策略

- 必须覆盖所有三种 CREATE TABLE 语法分支（常规表、类型化表、分区表）。
- 必须覆盖所有基表模板中的列数据类型组合。
- **必须覆盖列数据类型：CREATE TABLE 是列数据类型选择的核心语句，所有 PostgreSQL 16 支持的数据类型类别必须至少有一个代表性列定义。**
- 必须覆盖所有表类型（permanent、temporary、unlogged）。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- data_type 因子（T3）按数据类型类别做代表性覆盖，每个类别至少一个类型，常用类型（integer、varchar、timestamp、jsonb 等）做完整覆盖。
- T3 其余因子、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。列数据类型覆盖不得被裁剪至零——每个类别至少保留一个代表。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 IF NOT EXISTS 时，需要分别覆盖正常创建、no-op 语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE TABLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- **列数据类型与表类型必须参与生成：每个基表模板的列类型组合必须在至少一个 CREATE TABLE 样本中出现。**
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 data_type 挂靠到常规表分支（branch_1）的代表性成功样本，按数据类型类别轮转注入列定义。
- T3 因子中 table_name_shape、column_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 default_value_shape、collation_clause、generated_clause 挂靠到包含对应子句的样本上。
- T4 因子仅挂靠到需要依赖对象、权限、schema、tablespace、role 或表对象的分支。
- T4 因子中 base_table_template_coverage 挂靠到常规表分支，确保列类型组合被覆盖。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 所有表类型全覆盖（permanent、temporary、unlogged）
  - 目标对象存在 / 不存在 / 冲突 / 非法输入全覆盖
  - 成功 / 失败路径全覆盖
  - 列数据类型各类别至少一个代表性类型全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - 所有约束类型代表性覆盖
  - schema、owner、tablespace、role 等依赖对象代表性覆盖
  - 分区策略（RANGE、LIST、HASH）代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - ON COMMIT 各选项
  - LIKE 子句各 INCLUDING/EXCLUDING 选项
  - STORAGE 各选项
  - identifier 边界条件

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: create_table
  official_source: https://www.postgresql.org/docs/16/sql-createtable.html
  statement:
    key: create_table
    name: CREATE TABLE
    aliases:
    - CREATE TABLE
    - create table
    - create_table
    purpose: define a new table
  syntax_templates:
  - |
    CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name ( [
      { column_name data_type [ STORAGE { PLAIN | EXTERNAL | EXTENDED | MAIN | DEFAULT } ] [ COMPRESSION compression_method ] [ COLLATE collation ] [ column_constraint [ ... ] ]
        | table_constraint
        | LIKE source_table [ like_option ... ] }
        [, ... ]
    ] )
    [ INHERITS ( parent_table [, ... ] ) ]
    [ PARTITION BY { RANGE | LIST | HASH } ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass ] [, ... ] ) ]
    [ USING method ]
    [ WITH ( storage_parameter [= value ] [, ... ] ) | WITHOUT OIDS ]
    [ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]
    [ TABLESPACE tablespace_name ]
  - |
    CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name
        OF type_name [ (
      { column_name [ WITH OPTIONS ] [ column_constraint [ ... ] ]
        | table_constraint }
        [, ... ]
    ) ]
    [ PARTITION BY { RANGE | LIST | HASH } ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass ] [, ... ] ) ]
    [ USING method ]
    [ WITH ( storage_parameter [= value ] [, ... ] ) | WITHOUT OIDS ]
    [ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]
    [ TABLESPACE tablespace_name ]
  - |
    CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name
        PARTITION OF parent_table [ (
      { column_name [ WITH OPTIONS ] [ column_constraint [ ... ] ]
        | table_constraint }
        [, ... ]
    ) ] { FOR VALUES partition_bound_spec | DEFAULT }
    [ PARTITION BY { RANGE | LIST | HASH } ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass ] [, ... ] ) ]
    [ USING method ]
    [ WITH ( storage_parameter [= value ] [, ... ] ) | WITHOUT OIDS ]
    [ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]
    [ TABLESPACE tablespace_name ]
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
    - column_definition_count
    - constraint_type
    - partition_clause
    - inheritance_clause
    - like_clause
    - on_commit_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - column_name_shape
    - data_type
    - default_value_shape
    - collation_clause
    - generated_clause
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - base_table_template_coverage
    - privilege_level
    - schema_dependency
    - tablespace_dependency
    - role_dependency
    - type_dependency
    - parent_table_dependency
    - referenced_table_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_table_name
    - duplicate_column_name
    - invalid_data_type
    - constraint_violation_in_definition
    - schema_permission_insufficient
    - reserved_schema_name
    - max_column_limit
    - identifier_length_exceeded
    - temporary_table_scope_conflict
    - partition_bound_invalid
    - on_commit_with_non_temporary
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
        label: 常规表定义 (column definitions + constraints)
      - key: branch_2
        label: 类型化表 (OF type_name)
      - key: branch_3
        label: 分区表 (PARTITION OF parent_table)
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
    column_definition_count:
      label: 列定义数量
      importance: important
      values:
      - key: single_column
        label: 单列定义
      - key: multiple_columns
        label: 多列定义
    constraint_type:
      label: 约束类型
      importance: important
      values:
      - key: PRIMARY_KEY
        label: PRIMARY KEY 约束
      - key: UNIQUE
        label: UNIQUE 约束
      - key: CHECK
        label: CHECK 约束
      - key: FOREIGN_KEY
        label: FOREIGN KEY / REFERENCES 约束
      - key: EXCLUDE
        label: EXCLUDE 约束
      - key: NOT_NULL
        label: NOT NULL 约束
      - key: NULL
        label: NULL 约束
      - key: DEFAULT
        label: DEFAULT 约束
      - key: GENERATED_ALWAYS_STORED
        label: GENERATED ALWAYS AS (expr) STORED
      - key: GENERATED_IDENTITY
        label: GENERATED { ALWAYS | BY DEFAULT } AS IDENTITY
    partition_clause:
      label: 分区子句
      importance: important
      values:
      - key: RANGE
        label: PARTITION BY RANGE
      - key: LIST
        label: PARTITION BY LIST
      - key: HASH
        label: PARTITION BY HASH
      - key: not_partitioned
        label: 无分区
    inheritance_clause:
      label: 继承子句
      importance: important
      values:
      - key: INHERITS
        label: 包含 INHERITS 子句
      - key: no_inheritance
        label: 无继承
    like_clause:
      label: LIKE 子句
      importance: important
      values:
      - key: LIKE_with_options
        label: LIKE source_table WITH like_options
      - key: LIKE_no_options
        label: LIKE source_table (无 like_options)
      - key: no_LIKE
        label: 无 LIKE 子句
    on_commit_clause:
      label: ON COMMIT 子句
      importance: important
      values:
      - key: PRESERVE_ROWS
        label: ON COMMIT PRESERVE ROWS
      - key: DELETE_ROWS
        label: ON COMMIT DELETE ROWS
      - key: DROP
        label: ON COMMIT DROP
      - key: absent
        label: 无 ON COMMIT (默认 PRESERVE ROWS)
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
    column_name_shape:
      label: 列名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: duplicate_in_table
        label: 表内重复列名
    data_type:
      label: 列数据类型
      importance: important
      values:
      # --- 整数类型 ---
      - key: smallint
        label: smallint (2字节整数)
      - key: integer
        label: integer / int (4字节整数)
      - key: bigint
        label: bigint (8字节整数)
      # --- 序列整数类型 ---
      - key: smallserial
        label: smallserial (2字节自增整数)
      - key: serial
        label: serial (4字节自增整数)
      - key: bigserial
        label: bigserial (8字节自增整数)
      # --- 浮点类型 ---
      - key: real
        label: real (4字节浮点)
      - key: double_precision
        label: double precision (8字节浮点)
      # --- 精确数值类型 ---
      - key: numeric
        label: numeric (可变精度)
      - key: decimal
        label: decimal (numeric别名)
      # --- 货币类型 ---
      - key: money
        label: money (货币金额)
      # --- 字符类型 ---
      - key: character_varying
        label: character varying / varchar (可变长度字符串)
      - key: character
        label: character / char (定长字符串)
      - key: text
        label: text (可变长度无限制字符串)
      # --- 二进制类型 ---
      - key: bytea
        label: bytea (二进制数据)
      # --- 日期时间类型 ---
      - key: date
        label: date (日期)
      - key: time
        label: time (无时区时间)
      - key: time_with_time_zone
        label: time with time zone / timetz
      - key: timestamp
        label: timestamp (无时区时间戳)
      - key: timestamp_with_time_zone
        label: timestamp with time zone / timestamptz
      - key: interval
        label: interval (时间间隔)
      # --- 布尔类型 ---
      - key: boolean
        label: boolean / bool (布尔值)
      # --- 几何类型 ---
      - key: point
        label: point (平面点)
      - key: line
        label: line (无限直线)
      - key: lseg
        label: lseg (线段)
      - key: box
        label: box (矩形)
      - key: path
        label: path (几何路径)
      - key: polygon
        label: polygon (多边形)
      - key: circle
        label: circle (圆)
      # --- 网络地址类型 ---
      - key: cidr
        label: cidr (IPv4/IPv6网络地址)
      - key: inet
        label: inet (IPv4/IPv6主机地址)
      - key: macaddr
        label: macaddr (MAC地址6字节)
      - key: macaddr8
        label: macaddr8 (MAC地址8字节EUI-64)
      # --- 位串类型 ---
      - key: bit
        label: bit (定长位串)
      - key: bit_varying
        label: bit varying / varbit (变长位串)
      # --- 全文搜索类型 ---
      - key: tsvector
        label: tsvector (全文搜索文档向量)
      - key: tsquery
        label: tsquery (全文搜索查询)
      # --- UUID 类型 ---
      - key: uuid
        label: uuid (通用唯一标识符)
      # --- XML 类型 ---
      - key: xml
        label: xml (XML数据)
      # --- JSON 类型 ---
      - key: json
        label: json (JSON数据文本存储)
      - key: jsonb
        label: jsonb (JSON数据二进制存储)
      # --- 数组类型 ---
      - key: integer_array
        label: integer[] (整数数组)
      - key: text_array
        label: text[] (文本数组)
      - key: varchar_array
        label: varchar[] (变长字符数组)
      - key: numeric_array
        label: numeric[] (数值数组)
      - key: timestamp_array
        label: timestamp[] (时间戳数组)
      - key: jsonb_array
        label: jsonb[] (JSONB数组)
      # --- 范围类型 ---
      - key: int4range
        label: int4range (整数范围)
      - key: int8range
        label: int8range (大整数范围)
      - key: numrange
        label: numrange (数值范围)
      - key: tsrange
        label: tsrange (无时区时间戳范围)
      - key: tstzrange
        label: tstzrange (带时区时间戳范围)
      - key: daterange
        label: daterange (日期范围)
      # --- 复合类型 ---
      - key: composite_type
        label: 用户定义复合类型
      # --- 枚举类型 ---
      - key: enum_type
        label: 用户定义枚举类型 (CREATE TYPE ... AS ENUM)
      # --- 对象标识符类型 ---
      - key: oid
        label: oid (对象标识符)
      - key: regclass
        label: regclass (关系名OID别名)
      - key: regtype
        label: regtype (类型名OID别名)
      - key: regproc
        label: regproc (函数名OID别名)
      - key: regnamespace
        label: regnamespace (Schema名OID别名)
      - key: regrole
        label: regrole (角色名OID别名)
      # --- LSN 类型 ---
      - key: pg_lsn
        label: pg_lsn (日志序列号)
      # --- 名称与系统标识类型 ---
      - key: name
        label: name (63字符内部标识符)
      - key: tid
        label: tid (行标识符)
      - key: xid
        label: xid (事务标识符)
      - key: xid8
        label: xid8 (64位事务标识符)
      - key: cid
        label: cid (命令标识符)
      - key: aclitem
        label: aclitem (访问权限项)
      - key: pg_snapshot
        label: pg_snapshot (快照)
    default_value_shape:
      label: 默认值形态
      importance: non_important
      values:
      - key: with_DEFAULT_literal
        label: DEFAULT literal_value
      - key: with_DEFAULT_expression
        label: DEFAULT expression
      - key: without_DEFAULT
        label: 无 DEFAULT 子句
    collation_clause:
      label: 排序规则子句
      importance: non_important
      values:
      - key: with_COLLATION
        label: 指定 COLLATE collation_name
      - key: without_COLLATION
        label: 无 COLLATE (使用默认)
    generated_clause:
      label: 生成列子句
      importance: non_important
      values:
      - key: GENERATED_ALWAYS_AS_STORED
        label: GENERATED ALWAYS AS (expression) STORED
      - key: GENERATED_ALWAYS_AS_IDENTITY
        label: GENERATED ALWAYS AS IDENTITY
      - key: GENERATED_BY_DEFAULT_AS_IDENTITY
        label: GENERATED BY DEFAULT AS IDENTITY
      - key: none
        label: 无 GENERATED 子句
    base_table_template_coverage:
      label: 基表模板覆盖
      importance: non_important
      values:
      - key: table_01_comprehensive_types
        label: 综合列类型基表
      - key: table_02_simplified_types
        label: 简化列类型基表
      - key: table_03_partition_parent
        label: 分区父表模板
      - key: table_04_typed_table
        label: 类型化表模板
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: table_owner
        label: 表 Owner
      - key: non_owner_with_create
        label: 非Owner但有CREATE权限
      - key: non_owner_no_privilege
        label: 非Owner且无权限
    schema_dependency:
      label: Schema 依赖
      importance: non_important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在
      - key: pg_catalog_reserved
        label: pg_catalog (系统保留Schema)
      - key: information_schema_reserved
        label: information_schema (系统保留Schema)
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
    role_dependency:
      label: 角色依赖
      importance: non_important
      values:
      - key: owner_role_exists
        label: Owner角色存在
      - key: owner_role_not_exists
        label: Owner角色不存在
    type_dependency:
      label: 类型依赖 (用于 OF type_name)
      importance: non_important
      values:
      - key: composite_type_exists
        label: 复合类型已创建
      - key: composite_type_not_exists
        label: 复合类型不存在
    parent_table_dependency:
      label: 父表依赖 (用于 PARTITION OF)
      importance: non_important
      values:
      - key: parent_table_exists
        label: 父表已创建且已分区
      - key: parent_table_not_exists
        label: 父表不存在
      - key: parent_table_not_partitioned
        label: 父表存在但未分区
    referenced_table_dependency:
      label: 外键引用表依赖
      importance: non_important
      values:
      - key: referenced_table_exists
        label: 引用表存在
      - key: referenced_table_not_exists
        label: 引用表不存在
    duplicate_table_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: with_IF_NOT_EXISTS_noop
        label: 重名 + IF NOT EXISTS → no-op
      - key: without_IF_NOT_EXISTS_error
        label: 重名 + 无 IF NOT EXISTS → error
    duplicate_column_name:
      label: 列名重复
      importance: non_important
      values:
      - key: same_column_name_in_table
        label: 同一表中重复列名
    invalid_data_type:
      label: 无效数据类型
      importance: non_important
      values:
      - key: unknown_type_name
        label: 未知类型名
      - key: wrong_array_syntax
        label: 数组语法错误
    constraint_violation_in_definition:
      label: 定义时约束冲突
      importance: non_important
      values:
      - key: FK_references_nonexistent_table
        label: 外键引用不存在的表
      - key: CHECK_expression_invalid
        label: CHECK表达式无效
      - key: PK_with_nullable_column
        label: PRIMARY KEY列允许NULL
    schema_permission_insufficient:
      label: Schema权限不足
      importance: non_important
      values:
      - key: no_create_privilege_in_schema
        label: 在Schema中无CREATE权限
    reserved_schema_name:
      label: 保留Schema名
      importance: non_important
      values:
      - key: pg_catalog
        label: pg_catalog
      - key: information_schema
        label: information_schema
    max_column_limit:
      label: 列数上限
      importance: non_important
      values:
      - key: approaching_1600
        label: 接近1600列
      - key: at_1600
        label: 达到1600列
      - key: over_1600
        label: 超过1600列
    identifier_length_exceeded:
      label: 标识符长度超限
      importance: non_important
      values:
      - key: over_63_chars
        label: 标识符超过63字符
    temporary_table_scope_conflict:
      label: 临时表作用域冲突
      importance: non_important
      values:
      - key: temp_table_same_name_permanent
        label: 临时表与永久表同名冲突
    partition_bound_invalid:
      label: 分区边界无效
      importance: non_important
      values:
      - key: bound_out_of_range
        label: 分区边界超出父表范围
      - key: bound_type_mismatch
        label: 分区边界类型不匹配
    on_commit_with_non_temporary:
      label: ON COMMIT与非临时表组合
      importance: non_important
      values:
      - key: on_commit_on_permanent_table
        label: ON COMMIT用于永久表(非法)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询
      - key: information_schema_tables
        label: information_schema.tables 查询
      - key: information_schema_columns
        label: information_schema.columns 查询
      - key: SELECT_count
        label: SELECT count(*) 验证
      - key: pg_attribute_query
        label: pg_attribute 列属性查询
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
      - key: DROP_TABLE_CASCADE_RESTRICT
        label: DROP TABLE table_name CASCADE RESTRICT
  defaults:
    expected_status: success
    table_type: permanent
    if_not_exists_clause: absent
    column_definition_count: multiple_columns
    partition_clause: not_partitioned
    inheritance_clause: no_inheritance
    like_clause: no_LIKE
    on_commit_clause: absent
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - table_type
    - expected_status
    non_main_factors:
    - if_not_exists_clause
    - column_definition_count
    - constraint_type
    - partition_clause
    - inheritance_clause
    - like_clause
    - on_commit_clause
    - table_name_shape
    - column_name_shape
    - data_type
    - default_value_shape
    - collation_clause
    - generated_clause
    - base_table_template_coverage
    - privilege_level
    - schema_dependency
    - tablespace_dependency
    - role_dependency
    - type_dependency
    - parent_table_dependency
    - referenced_table_dependency
    - duplicate_table_name
    - duplicate_column_name
    - invalid_data_type
    - constraint_violation_in_definition
    - schema_permission_insufficient
    - reserved_schema_name
    - max_column_limit
    - identifier_length_exceeded
    - temporary_table_scope_conflict
    - partition_bound_invalid
    - on_commit_with_non_temporary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - table_type
  rendering:
    statement_template: "CREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name ( [ column_definitions ] )"
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
      partition_clause:
        RANGE: "PARTITION BY RANGE ( column_name )"
        LIST: "PARTITION BY LIST ( column_name )"
        HASH: "PARTITION BY HASH ( column_name )"
        not_partitioned: ""
      inheritance_clause:
        INHERITS: "INHERITS ( parent_table )"
        no_inheritance: ""
```
``