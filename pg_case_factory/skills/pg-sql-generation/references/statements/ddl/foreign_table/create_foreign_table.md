# 技能：CREATE FOREIGN TABLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createforeigntable.html

### 形式 1：常规外部表

```sql
CREATE FOREIGN TABLE [ IF NOT EXISTS ] table_name ( [
  { column_name data_type [ OPTIONS ( option 'value' [, ...] ) ] [ COLLATE collation ] [ column_constraint [ ... ] ]
    | table_constraint }
    [, ... ]
] )
[ INHERITS ( parent_table [, ...] ) ]
  SERVER server_name
[ OPTIONS ( option 'value' [, ...] ) ]
```

### 形式 2：分区外部表

```sql
CREATE FOREIGN TABLE [ IF NOT EXISTS ] table_name
  PARTITION OF parent_table [ (
  { column_name [ WITH OPTIONS ] [ column_constraint [ ... ] ]
    | table_constraint }
    [, ... ]
) ]
{ FOR VALUES partition_bound_spec | DEFAULT }
  SERVER server_name
[ OPTIONS ( option 'value' [, ...] ) ]
```

### 列约束

```sql
[ CONSTRAINT constraint_name ]
{ NOT NULL |
  NULL |
  CHECK ( expression ) [ NO INHERIT ] |
  DEFAULT default_expr |
  GENERATED ALWAYS AS ( generation_expr ) STORED }
```

### 表约束

```sql
[ CONSTRAINT constraint_name ]
CHECK ( expression ) [ NO INHERIT ]
```

### 分区边界规格

```sql
IN ( partition_bound_expr [, …] ) |
FROM ( { partition_bound_expr | MINVALUE | MAXVALUE } [, …] )
  TO ( { partition_bound_expr | MINVALUE | MAXVALUE } [, …] ) |
WITH ( MODULUS numeric_literal, REMAINDER numeric_literal )
```

PG16 关键约束：
- 创建外部表需要 **USAGE** 权限于外部服务器和 **USAGE** 权限于所有列数据类型。
- 约束（NOT NULL、CHECK）**不被 PostgreSQL 核心强制执行**——仅被假设为真。应代表远程服务器实际强制的约束。
- 如果声明约束与实际不符，查询可能产生错误或不正确的结果。
- CREATE FOREIGN TABLE 自动创建复合类型（行类型），因此表名不能与同 schema 中已有数据类型重名。
- 表名在同 schema 内必须与所有其他关系（表、序列、索引、视图、物化视图、外部表）不同。
- 分区外部表的父表不能有 UNIQUE 索引。
- GENERATED 列：STORED 生成列在本地计算后传递给 FDW，但查询返回值不一定与生成表达式一致。
- UPDATE 分区路由：可以从本地分区移到外部表分区（如果 FDW 支持），但不能从外部表分区移到其他分区。

## 语句作用

官方说明：CREATE FOREIGN TABLE — define a new foreign table

该 reference 关注外部表创建语句的两种语法形式（常规外部表 / 分区外部表）、列定义与数据类型选择、约束声明（仅声明不强制）、SERVER 依赖、IF NOT EXISTS 行为和权限边界（USAGE 权限）。

CREATE FOREIGN TABLE **涉及列类型定义**——与 CREATE TABLE 类似，每列需要指定 data_type，这是类型覆盖的核心维度。列数据类型需要 USAGE 权限，这是权限边界的关键点。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（常规外部表 / 分区外部表）
- object_state：目标 foreign table 对象状态（不存在 / 已存在 / 同名冲突）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- table_form：表形式（regular / partition_of）
- if_not_exists_clause：IF NOT EXISTS 子句开关（省略 / 指定）
- column_count：列数量（zero_columns / single_column / multiple_columns）
- column_data_type：列数据类型（integer / text / varchar / numeric / boolean / date / timestamp / jsonb / uuid / bigint / float8）
- inherits_clause：INHERITS 子句形态（省略 / 指定单个 / 指定多个）— 仅常规形式
- partition_bound_spec：分区边界规格（FOR VALUES IN / FOR VALUES FROM...TO / FOR VALUES WITH / DEFAULT）— 仅分区形式
- server_clause：SERVER 子句（指定有效服务器 / 指定不存在服务器）

### T3：对象名与输入形态因子
- table_name_shape：表名形态
- column_name_shape：列名形态
- server_name_shape：服务器名称形态
- constraint_name_shape：约束名称形态
- collation_name_shape：COLLATE 名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（usage_on_server + usage_on_types / no_server_usage / no_type_usage）
- server_existence：外部服务器存在性（存在 / 不存在）
- parent_table_existence：父表存在性（存在 / 不存在）— 仅分区形式
- schema_existence：目标 schema 存在性（存在 / 不存在）
- type_name_conflict：表名与同 schema 中已有数据类型重名

### T5：异常与边界因子
- duplicate_table_name：重名冲突（与已有外部表/普通表/视图等重名）
- nonexistent_server：外部服务器不存在
- nonexistent_parent_table：父表不存在 — 仅分区形式
- no_server_usage_privilege：无外部服务器 USAGE 权限
- no_type_usage_privilege：无列数据类型 USAGE 权限
- if_not_exists_no_op：IF NOT EXISTS 遇已存在对象
- zero_column_table：零列外部表（PostgreSQL 扩展，SQL 标准不允许）
- constraint_not_enforced：约束仅声明不强制（行为边界）
- type_name_conflict_error：表名与同 schema 已有数据类型重名 → error
- parent_has_unique_index：分区外部表的父表有 UNIQUE 索引 → error

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 必须覆盖两种 CREATE FOREIGN TABLE 语法分支（常规 / 分区）。
- **必须覆盖列数据类型**：CREATE FOREIGN TABLE 涉及列定义，需要覆盖代表性数据类型。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- column_data_type 因子按数据类型类别做代表性覆盖，每个类别至少一个类型。
- T3 其余因子、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 `IF NOT EXISTS` 时，需要分别覆盖正常创建、no-op 语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（FDW + 服务器）、目标 CREATE FOREIGN TABLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- **列数据类型必须参与生成**：外部表每列的 data_type 必须在至少一个样本中出现。
- CREATE FOREIGN TABLE 需要 USAGE 权限于外部服务器和所有列数据类型，必须在生成样本中显式标注权限依赖。
- 约束不被 PostgreSQL 强制执行，仅被声明——此行为边界需要代表性覆盖。
- 分区外部表需要前置准备父表和外部服务器，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 column_data_type 挂靠到常规外部表分支的代表性成功样本，按数据类型类别轮转注入列定义。
- T3 因子中 table_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、服务器依赖、父表依赖或 schema 存在性的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（常规 / 分区）
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 列数据类型代表性覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 列约束代表性覆盖（NOT NULL / CHECK / DEFAULT）
  - INHERITS 子句代表性覆盖
  - 分区边界规格代表性覆盖
  - OPTIONS 子句代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: foreign_table
  skill_name: create_foreign_table
  official_source: https://www.postgresql.org/docs/16/sql-createforeigntable.html
  statement:
    key: create_foreign_table
    name: CREATE FOREIGN TABLE
    aliases:
    - CREATE FOREIGN TABLE
    - create foreign table
    - create_foreign_table
    purpose: define a new foreign table
  syntax_templates:
  - "CREATE FOREIGN TABLE [ IF NOT EXISTS ] table_name ( [ { column_name data_type\
    \ [ OPTIONS ] [ COLLATE collation ] [ column_constraint ] | table_constraint\
    \ } [, ...] ] ) [ INHERITS ( parent_table [, ...] ) ] SERVER server_name [ OPTIONS\
    \ ]"
  - "CREATE FOREIGN TABLE [ IF NOT EXISTS ] table_name PARTITION OF parent_table\
    \ [ ( column_defs ) ] { FOR VALUES partition_bound_spec | DEFAULT } SERVER server_name\
    \ [ OPTIONS ]"
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
    - table_form
    - if_not_exists_clause
    - column_count
    - column_data_type
    - inherits_clause
    - partition_bound_spec
    - server_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - column_name_shape
    - server_name_shape
    - constraint_name_shape
    - collation_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - server_existence
    - parent_table_existence
    - schema_existence
    - type_name_conflict
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_table_name
    - nonexistent_server
    - nonexistent_parent_table
    - no_server_usage_privilege
    - no_type_usage_privilege
    - if_not_exists_no_op
    - zero_column_table
    - constraint_not_enforced
    - type_name_conflict_error
    - parent_has_unique_index
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
        label: CREATE FOREIGN TABLE 常规形式 (列定义 + SERVER)
      - key: branch_partition
        label: CREATE FOREIGN TABLE PARTITION OF 形式 (分区外部表)
    object_state:
      label: 目标 foreign table 对象状态
      importance: important
      values:
      - key: not_exists
        label: 表不存在
      - key: already_exists
        label: 表已存在
      - key: type_name_conflict
        label: 与已有数据类型同名冲突
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    table_form:
      label: 表形式
      importance: important
      values:
      - key: regular
        label: 常规外部表
      - key: partition_of
        label: 分区外部表 (PARTITION OF)
    if_not_exists_clause:
      label: IF NOT EXISTS 子句开关
      importance: important
      values:
      - key: omitted
        label: 省略 IF NOT EXISTS
      - key: specified
        label: 指定 IF NOT EXISTS
    column_count:
      label: 列数量
      importance: important
      values:
      - key: zero_columns
        label: 零列 (PostgreSQL 扩展)
      - key: single_column
        label: 单列
      - key: multiple_columns
        label: 多列
    column_data_type:
      label: 列数据类型
      importance: important
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
      - key: float8
        label: double precision
    inherits_clause:
      label: INHERITS 子句形态 (仅常规形式)
      importance: non_important
      values:
      - key: omitted
        label: 省略 INHERITS
      - key: single_parent
        label: 指定单个父表
      - key: multiple_parents
        label: 指定多个父表
    partition_bound_spec:
      label: 分区边界规格 (仅分区形式)
      importance: non_important
      values:
      - key: for_values_in
        label: FOR VALUES IN (列表分区)
      - key: for_values_from_to
        label: FOR VALUES FROM (...) TO (...) (范围分区)
      - key: for_values_with
        label: FOR VALUES WITH (哈希分区)
      - key: default_partition
        label: DEFAULT (默认分区)
    server_clause:
      label: SERVER 子句
      importance: non_important
      values:
      - key: valid_server
        label: 指定有效外部服务器
      - key: nonexistent_server
        label: 指定不存在的外部服务器
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
      - key: reserved_word_name
        label: 保留字作为名称
      - key: duplicate_name
        label: 已存在的表名
    column_name_shape:
      label: 列名形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: reserved_word_name
        label: 保留字作为列名
    server_name_shape:
      label: 服务器名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: nonexistent_server
        label: 不存在的服务器
    constraint_name_shape:
      label: 约束名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: omitted
        label: 省略约束名
    collation_name_shape:
      label: COLLATE 名称形态
      importance: non_important
      values:
      - key: omitted
        label: 省略 COLLATE
      - key: specified
        label: 指定 COLLATE
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: usage_on_server_and_types
        label: USAGE on server + USAGE on types → success
      - key: no_server_usage
        label: 无 USAGE on server → error
      - key: no_type_usage
        label: 无 USAGE on column type → error
    server_existence:
      label: 外部服务器存在性
      importance: non_important
      values:
      - key: server_exists
        label: 外部服务器存在
      - key: server_not_exists
        label: 外部服务器不存在 → error
    parent_table_existence:
      label: 父表存在性 (仅分区形式)
      importance: non_important
      values:
      - key: parent_exists
        label: 父表存在
      - key: parent_not_exists
        label: 父表不存在 → error
    schema_existence:
      label: 目标 schema 存在性
      importance: non_important
      values:
      - key: schema_exists
        label: 目标 schema 存在
      - key: schema_not_exists
        label: 目标 schema 不存在 → error
    type_name_conflict:
      label: 表名与同 schema 已有数据类型重名
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: same_as_existing_type
        label: 与已有数据类型同名 → error
    duplicate_table_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: same_name_conflict
        label: 与已有关系同名 → error
    nonexistent_server:
      label: 外部服务器不存在
      importance: non_important
      values:
      - key: server_exists
        label: 服务器存在
      - key: server_missing
        label: 服务器不存在 → error
    nonexistent_parent_table:
      label: 父表不存在 (仅分区形式)
      importance: non_important
      values:
      - key: parent_exists
        label: 父表存在
      - key: parent_missing
        label: 父表不存在 → error
    no_server_usage_privilege:
      label: 无外部服务器 USAGE 权限
      importance: non_important
      values:
      - key: has_usage
        label: 有 USAGE 权限 → success
      - key: lacks_usage
        label: 无 USAGE 权限 → error
    no_type_usage_privilege:
      label: 无列数据类型 USAGE 权限
      importance: non_important
      values:
      - key: has_usage
        label: 有 USAGE 权限 → success
      - key: lacks_usage
        label: 无 USAGE 权限 → error
    if_not_exists_no_op:
      label: IF NOT EXISTS 遇已存在对象
      importance: non_important
      values:
      - key: new_create
        label: 正常创建 (不存在)
      - key: no_op_notice
        label: IF NOT EXISTS 遇已存在 → notice (no-op)
    zero_column_table:
      label: 零列外部表
      importance: non_important
      values:
      - key: has_columns
        label: 有列定义
      - key: zero_columns
        label: 零列 (PostgreSQL 扩展，SQL 标准不允许)
    constraint_not_enforced:
      label: 约束仅声明不强制
      importance: non_important
      values:
      - key: with_not_null
        label: 有 NOT NULL 约束 (仅声明)
      - key: with_check
        label: 有 CHECK 约束 (仅声明)
      - key: no_constraints
        label: 无约束
    type_name_conflict_error:
      label: 表名与同 schema 已有数据类型重名 → error
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: conflict_with_existing_type
        label: 与已有数据类型同名 → error
    parent_has_unique_index:
      label: 分区外部表的父表有 UNIQUE 索引
      importance: non_important
      values:
      - key: parent_no_unique
        label: 父表无 UNIQUE 索引 → success
      - key: parent_has_unique
        label: 父表有 UNIQUE 索引 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询
      - key: error_assertion
        label: 错误断言
      - key: notice_assertion
        label: notice 断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_foreign_table
        label: DROP FOREIGN TABLE
      - key: drop_foreign_table_cascade
        label: DROP FOREIGN TABLE CASCADE
      - key: drop_server
        label: 删除外部服务器
      - key: drop_fdw
        label: 删除 FDW
      - key: drop_parent_table
        label: 删除父表 (分区形式)
  notes:
    column_type_involvement: CREATE FOREIGN TABLE 涉及列数据类型定义，需要覆盖代表性数据类型。
    constraint_not_enforced: 约束 (NOT NULL, CHECK) 不被 PostgreSQL 核心强制执行，仅被假设为真。
    usage_privilege_required: 需要 USAGE 权限于外部服务器和所有列数据类型，不需要 superuser。
    auto_composite_type: 自动创建复合类型，表名不能与同 schema 中已有数据类型重名。
    partition_foreign_table: PARTITION OF 形式需要前置父表，父表不能有 UNIQUE 索引。
    server_dependency: 外部服务器需要由 superuser 前置创建 (FDW + CREATE SERVER)。
  defaults:
    expected_status: success
    table_form: regular
    object_state: not_exists
    privilege_level: usage_on_server_and_types
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - table_form
    - if_not_exists_clause
    - column_count
    - column_data_type
    - inherits_clause
    - partition_bound_spec
    - server_clause
    - table_name_shape
    - column_name_shape
    - server_name_shape
    - constraint_name_shape
    - collation_name_shape
    - privilege_level
    - server_existence
    - parent_table_existence
    - schema_existence
    - type_name_conflict
    - duplicate_table_name
    - nonexistent_server
    - nonexistent_parent_table
    - no_server_usage_privilege
    - no_type_usage_privilege
    - if_not_exists_no_op
    - zero_column_table
    - constraint_not_enforced
    - type_name_conflict_error
    - parent_has_unique_index
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE FOREIGN TABLE [ IF NOT EXISTS ] {table_name} ( {column_defs} ) SERVER {server_name}"
    verification_query_template: "SELECT relname FROM pg_class WHERE relname = '{table_name}' AND relkind = 'f'"
    factor_value_bindings: {}
```
