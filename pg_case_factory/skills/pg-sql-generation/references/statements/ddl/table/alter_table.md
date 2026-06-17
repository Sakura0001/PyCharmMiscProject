# 技能：ALTER TABLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altertable.html

### Synopsis 形式 1：action 形式（最常用）

```sql
ALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]
    action [, ... ]
```

### Synopsis 形式 2：RENAME COLUMN

```sql
ALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]
    RENAME [ COLUMN ] column_name TO new_column_name
```

### Synopsis 形式 3：RENAME CONSTRAINT

```sql
ALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]
    RENAME CONSTRAINT constraint_name TO new_constraint_name
```

### Synopsis 形式 4：RENAME TABLE

```sql
ALTER TABLE [ IF EXISTS ] name
    RENAME TO new_name
```

### Synopsis 形式 5：SET SCHEMA

```sql
ALTER TABLE [ IF EXISTS ] name
    SET SCHEMA new_schema
```

### Synopsis 形式 6：SET TABLESPACE (批量)

```sql
ALTER TABLE ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]
    SET TABLESPACE new_tablespace [ NOWAIT ]
```

### Synopsis 形式 7：ATTACH PARTITION

```sql
ALTER TABLE [ IF EXISTS ] name
    ATTACH PARTITION partition_name { FOR VALUES partition_bound_spec | DEFAULT }
```

### Synopsis 形式 8：DETACH PARTITION

```sql
ALTER TABLE [ IF EXISTS ] name
    DETACH PARTITION partition_name [ CONCURRENTLY | FINALIZE ]
```

### action 子命令完整列表

```sql
ADD [ COLUMN ] [ IF NOT EXISTS ] column_name data_type
    [ COLLATE collation ] [ column_constraint [ ... ] ]

DROP [ COLUMN ] [ IF EXISTS ] column_name [ RESTRICT | CASCADE ]

ALTER [ COLUMN ] column_name [ SET DATA ] TYPE data_type
    [ COLLATE collation ] [ USING expression ]

ALTER [ COLUMN ] column_name SET DEFAULT expression
ALTER [ COLUMN ] column_name DROP DEFAULT

ALTER [ COLUMN ] column_name { SET | DROP } NOT NULL

ALTER [ COLUMN ] column_name DROP EXPRESSION [ IF EXISTS ]

ALTER [ COLUMN ] column_name ADD GENERATED { ALWAYS | BY DEFAULT } AS IDENTITY
    [ ( sequence_options ) ]

ALTER [ COLUMN ] column_name { SET GENERATED { ALWAYS | BY DEFAULT }
    | SET sequence_option | RESTART [ [ WITH ] restart ] } [...]

ALTER [ COLUMN ] column_name DROP IDENTITY [ IF EXISTS ]

ALTER [ COLUMN ] column_name SET STATISTICS integer

ALTER [ COLUMN ] column_name SET ( attribute_option = value [, ... ] )
ALTER [ COLUMN ] column_name RESET ( attribute_option [, ... ] )

ALTER [ COLUMN ] column_name SET STORAGE
    { PLAIN | EXTERNAL | EXTENDED | MAIN | DEFAULT }

ALTER [ COLUMN ] column_name SET COMPRESSION compression_method

ADD table_constraint [ NOT VALID ]
ADD table_constraint_using_index

ALTER CONSTRAINT constraint_name
    [ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]

VALIDATE CONSTRAINT constraint_name

DROP CONSTRAINT [ IF EXISTS ] constraint_name [ RESTRICT | CASCADE ]

DISABLE TRIGGER [ trigger_name | ALL | USER ]
ENABLE TRIGGER [ trigger_name | ALL | USER ]
ENABLE REPLICA TRIGGER trigger_name
ENABLE ALWAYS TRIGGER trigger_name

DISABLE RULE rewrite_rule_name
ENABLE RULE rewrite_rule_name
ENABLE REPLICA RULE rewrite_rule_name
ENABLE ALWAYS RULE rewrite_rule_name

DISABLE ROW LEVEL SECURITY
ENABLE ROW LEVEL SECURITY
FORCE ROW LEVEL SECURITY
NO FORCE ROW LEVEL SECURITY

CLUSTER ON index_name
SET WITHOUT CLUSTER
SET WITHOUT OIDS

SET ACCESS METHOD new_access_method
SET TABLESPACE new_tablespace
SET { LOGGED | UNLOGGED }

SET ( storage_parameter [= value] [, ... ] )
RESET ( storage_parameter [, ... ] )

INHERIT parent_table
NO INHERIT parent_table
OF type_name
NOT OF

OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }

REPLICA IDENTITY { DEFAULT | USING INDEX index_name | FULL | NOTHING }
```

### partition_bound_spec

```sql
IN ( partition_bound_expr [, ... ] ) |
FROM ( { partition_bound_expr | MINVALUE | MAXVALUE } [, ... ] )
  TO ( { partition_bound_expr | MINVALUE | MAXVALUE } [, ... ] ) |
WITH ( MODULUS numeric_literal, REMAINDER numeric_literal )
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
  REFERENCES reftable [ ( refcolumn ) ]
    [ MATCH FULL | MATCH PARTIAL | MATCH SIMPLE ]
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
    [ MATCH FULL | MATCH PARTIAL | MATCH SIMPLE ]
    [ ON DELETE referential_action ] [ ON UPDATE referential_action ] }
[ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]
```

### table_constraint_using_index

```sql
[ CONSTRAINT constraint_name ]
{ UNIQUE | PRIMARY KEY } USING INDEX index_name
[ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]
```

### IF EXISTS / IF NOT EXISTS 适用范围

| 子句 | 适用对象 | 行为 |
|------|---------|------|
| `IF EXISTS` (顶层) | 表名 | 表不存在时不报错，发出 notice |
| `IF NOT EXISTS` | `ADD COLUMN` | 列已存在时不报错 |
| `IF EXISTS` | `DROP COLUMN` | 列不存在时不报错，发出 notice |
| `IF EXISTS` | `DROP EXPRESSION` | 列非存储生成列时不报错 |
| `IF EXISTS` | `DROP IDENTITY` | 列非标识列时不报错 |
| `IF EXISTS` | `DROP CONSTRAINT` | 约束不存在时不报错，发出 notice |
| `IF EXISTS` | `ATTACH/DETACH PARTITION` | 表不存在时不报错 |

### 权限要求

| 操作 | 所需权限 |
|------|---------|------|
| 一般 ALTER TABLE | 必须 **OWN** 目标表 |
| `SET SCHEMA` | OWN 表 + 新 schema 的 CREATE |
| `SET TABLESPACE` | OWN 表 + 新 tablespace 的 CREATE |
| `INHERIT parent_table` | OWN 目标表和父表 |
| `ATTACH PARTITION` | OWN 待挂载表 |
| `OWNER TO` | 必须能 SET ROLE 到新 owner；新 owner 须有表 schema 的 CREATE；superuser 可改任意表 owner |
| `ADD COLUMN`, `ALTER COLUMN TYPE`, `OF type_name` | OWN 表 + 数据类型的 USAGE |
| `DISABLE/ENABLE ALL` (存在约束触发器时) | **Superuser** |
| 禁用/启用内部生成的约束触发器 | **Superuser** |

## 语句作用

官方说明：ALTER TABLE — change the definition of a table

该 reference 关注表定义修改语句的所有语法分支、子命令类别、列类型转换、约束操作、分区操作与依赖环境，不负责包装所有样本到统一外层事务。

ALTER TABLE 是 PostgreSQL 中最复杂的 DDL 语句，拥有 8 种顶层 synopsis 形式和 46 种 action 子命令。

**涉及列数据类型组合的子命令**（data_type 因子参与生成）：
- ADD COLUMN：新增列需选择 data_type，列类型覆盖在此子命令中参与生成
- ALTER COLUMN TYPE：列类型转换涉及 (source_type → target_type) 组合，兼容转换无需 USING、不兼容转换需要 USING、不兼容且无 USING 报错，列类型覆盖在此子命令中参与生成

**涉及列数据类型引用但不作为生成因子的子命令**（列类型影响行为但 data_type 因子不参与生成）：
- ADD table_constraint (CHECK)：CHECK 表达式引用列值，不同类型列的 CHECK 行为不同
- ADD table_constraint (UNIQUE)：UNIQUE 索引按列类型选择操作符类
- ADD table_constraint (EXCLUDE)：EXCLUDE 约束依赖列类型和操作符类
- ADD table_constraint (FK)：引用列类型必须与被引用列类型匹配
- ALTER COLUMN SET STORAGE：存储模式取决于列数据类型 (TOAST 行为)
- ALTER COLUMN SET COMPRESSION：压缩适用性取决于列数据类型
- ALTER COLUMN ADD GENERATED AS IDENTITY：仅适用于整数类型列
- OF type_name：引用复合类型定义
- ATTACH PARTITION：分区键列类型必须与父表匹配

**不涉及列数据类型的子命令**：DROP COLUMN、SET/DROP DEFAULT、SET/DROP NOT NULL、DROP EXPRESSION、SET GENERATED / SET sequence_option / RESTART、DROP IDENTITY、SET STATISTICS、SET/RESET attribute_option、ADD table_constraint_using_index、ALTER CONSTRAINT (deferrability)、VALIDATE CONSTRAINT、DROP CONSTRAINT、DISABLE/ENABLE TRIGGER、ENABLE REPLICA/ALWAYS TRIGGER、DISABLE/ENABLE RULE、ENABLE REPLICA/ALWAYS RULE、DISABLE/ENABLE/FORCE/NO FORCE ROW LEVEL SECURITY、CLUSTER ON、SET WITHOUT CLUSTER、SET WITHOUT OIDS、SET ACCESS METHOD、SET TABLESPACE、SET LOGGED/UNLOGGED、SET/RESET storage_parameter (表级)、INHERIT / NO INHERIT、NOT OF、OWNER TO、REPLICA IDENTITY、RENAME COLUMN、RENAME CONSTRAINT、RENAME TO、SET SCHEMA、SET TABLESPACE 批量、DETACH PARTITION

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 顶层形式（action 形式、RENAME COLUMN、RENAME CONSTRAINT、RENAME TO、SET SCHEMA、SET TABLESPACE 批量、ATTACH PARTITION、DETACH PARTITION）
- subcommand_category：action 形式下的子命令类别（ADD COLUMN、DROP COLUMN、ALTER COLUMN TYPE、ALTER COLUMN SET/DROP DEFAULT、ALTER COLUMN SET/DROP NOT NULL、ALTER COLUMN DROP EXPRESSION、ALTER COLUMN ADD GENERATED AS IDENTITY、ALTER COLUMN SET GENERATED/SET sequence_option/RESTART、ALTER COLUMN DROP IDENTITY、ALTER COLUMN SET STATISTICS、ALTER COLUMN SET/RESET attribute_option、ALTER COLUMN SET STORAGE、ALTER COLUMN SET COMPRESSION、ADD table_constraint、ADD table_constraint_using_index、ALTER CONSTRAINT、VALIDATE CONSTRAINT、DROP CONSTRAINT、DISABLE/ENABLE TRIGGER、ENABLE REPLICA/ALWAYS TRIGGER、DISABLE/ENABLE RULE、ENABLE REPLICA/ALWAYS RULE、DISABLE/ENABLE/FORCE/NO FORCE ROW LEVEL SECURITY、CLUSTER ON、SET WITHOUT CLUSTER、SET WITHOUT OIDS、SET ACCESS METHOD、SET TABLESPACE、SET LOGGED/UNLOGGED、SET/RESET storage_parameter、INHERIT/NO INHERIT、OF/NOT OF、OWNER TO、REPLICA IDENTITY）
- object_state：目标表对象存在性（已存在、不存在、分区表、临时表、无日志表）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_exists_clause：顶层 IF EXISTS 子句（present、absent）
- if_not_exists_clause：ADD COLUMN IF NOT EXISTS 子句（present、absent）
- cascade_restrict：CASCADE/RESTRICT 选择（CASCADE、RESTRICT、absent）
- only_clause：ONLY 子句（present、absent）
- privilege_level：权限级别（superuser、table_owner、non_owner_with_privilege、non_owner_no_privilege）
- column_type_conversion：列类型转换类别（compatible_no_using、compatible_with_collation、incompatible_with_using、incompatible_no_using_error）

### T3：对象名与输入形态因子
- table_name_shape：表名形态（simple、quoted、reserved_word、schema_qualified、nonexistent）
- column_name_shape：列名形态（simple、quoted、reserved_word、nonexistent）
- constraint_name_shape：约束名形态（simple、quoted、nonexistent）
- new_name_shape：新名称形态（simple、quoted、reserved_word、duplicate）
- data_type：列数据类型（仅用于 ADD COLUMN 和 ALTER COLUMN TYPE 子命令；完整枚举见 factors 定义）
- expression_shape：USING/DEFAULT 表达式形态（simple_cast、complex_expression、invalid_expression）

### T4：依赖对象与环境因子
- base_table_template_coverage：基表模板覆盖（table_01_comprehensive_types、table_02_simplified_types、table_03_partition_parent、table_04_unlogged）
- dependency_state：依赖对象状态（views_dependent、FK_dependent、indexes_dependent、triggers_dependent、policies_dependent、no_dependencies）
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists）
- tablespace_dependency：表空间依赖（default_tablespace、specified_tablespace_exists、specified_tablespace_not_exists）
- role_dependency：角色依赖（owner_role_exists、owner_role_not_exists、current_role_variants）
- parent_table_dependency：父表依赖（parent_partitioned_exists、parent_not_partitioned、parent_not_exists）
- referenced_table_dependency：外键引用表依赖（referenced_table_exists、referenced_table_not_exists）
- index_dependency：索引依赖（index_exists、index_not_exists、unique_index_for_constraint）

### T5：异常与边界因子
- nonexistent_table：操作不存在的表（with_IF_EXISTS_notice、without_IF_EXISTS_error）
- nonexistent_column：操作不存在的列
- nonexistent_constraint：操作不存在的约束
- type_conversion_impossible：类型转换不可行（无 USING 且不兼容）
- constraint_violation_existing_data：已有数据违反新约束（SET NOT NULL with nulls、ADD CHECK with violating rows）
- privilege_insufficient：权限不足
- partition_mismatch：分区边界不匹配
- dependent_objects_block：依赖对象阻止操作（CASCADE vs RESTRICT）
- identifier_length_exceeded：标识符长度超限

### T6：验证与清理因子
- verification_mode：验证方式（pg_class_catalog_query、pg_attribute_query、pg_constraint_query、information_schema_query、SELECT_inspection）
- cleanup_mode：清理方式（DROP_TABLE_IF_EXISTS、DROP_TABLE_CASCADE、ALTER_TABLE_REVERT、RESET_STATE）

## 覆盖策略

- 必须覆盖所有 8 种 ALTER TABLE 顶层 synopsis 形式。
- 必须覆盖所有 action 子命令类别（至少每个类别一个成功或失败可归因样本）。
- **列数据类型参与生成的子命令仅为 ADD COLUMN 和 ALTER COLUMN TYPE。ADD COLUMN 需要覆盖新增列的数据类型选择；ALTER COLUMN TYPE 需要覆盖列类型转换场景（兼容转换无需 USING、不兼容转换需要 USING、不兼容且无 USING 报错）。列类型覆盖仅在上述两个子命令中参与生成。**
- **列数据类型影响行为但不参与生成的子命令包括：ADD table_constraint (CHECK/UNIQUE/EXCLUDE/FK 引用列类型)、ALTER COLUMN SET STORAGE (存储模式取决于列类型)、ALTER COLUMN SET COMPRESSION (压缩适用性取决于列类型)、ADD GENERATED AS IDENTITY (仅适用于整数类型)、OF type_name (引用复合类型)、ATTACH PARTITION (分区键类型须匹配父表)。这些子命令中列类型通过 T4 依赖因子间接覆盖，不通过 T3 data_type 因子参与生成。**
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- data_type 因子（T3）仅在 ADD COLUMN 和 ALTER COLUMN TYPE 子命令中做代表性覆盖，每个数据类型类别至少一个代表，常用类型做完整覆盖。data_type 因子不参与其他子命令的生成。
- T3 其余因子、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩子命令类别数量。

## 生成约束

- 必须预创建可被修改的目标表对象，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标表存在时的成功修改路径、目标表不存在时的失败路径，以及支持 IF EXISTS 分支的代表性 no-op 路径。
- 所有子命令分支需要保持独立归因——每个子命令类别至少一个成功或失败样本。
- ADD COLUMN 子命令必须覆盖新增列的数据类型代表性组合。
- ALTER COLUMN TYPE 子命令必须覆盖兼容类型转换（无 USING）和不兼容类型转换（有 USING）的代表性组合，以及不兼容且无 USING 的失败路径。
- DROP COLUMN、DROP CONSTRAINT 必须覆盖 CASCADE 和 RESTRICT 两种路径。
- 每个样本必须包含明确的前置对象准备、目标 ALTER TABLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 data_type 仅挂靠到 ADD COLUMN 和 ALTER COLUMN TYPE 子命令的代表性成功样本，按数据类型类别轮转注入。其他子命令不挂靠 data_type 因子。
- T3 因子中 table_name_shape、column_name_shape、constraint_name_shape、new_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 expression_shape 仅挂靠到 ALTER COLUMN TYPE (USING) 和 ALTER COLUMN SET DEFAULT 子命令的样本。
- T4 因子仅挂靠到需要依赖对象、权限、schema、tablespace、role 或表对象的分支。
- T4 因子中 base_table_template_coverage 挂靠到 ADD COLUMN 和 ALTER COLUMN TYPE 子命令，确保列类型组合被覆盖。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、子命令类别、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有顶层 synopsis 形式全覆盖
  - 所有子命令类别全覆盖
  - 目标对象存在 / 不存在 / 冲突 / 非法输入全覆盖
  - 成功 / 失败路径全覆盖
  - ADD COLUMN 和 ALTER COLUMN TYPE 的列数据类型各类别至少一个代表性类型全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - IF EXISTS / IF NOT EXISTS / CASCADE / RESTRICT 各选项代表性覆盖
  - ONLY 子句代表性覆盖
  - schema、owner、tablespace、role 等依赖对象代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - 属性选项 (SET/RESET attribute_option)
  - 存储参数 (SET/RESET storage_parameter)
  - COMPRESSION 方法
  - STORAGE 模式 (PLAIN/EXTERNAL/EXTENDED/MAIN/DEFAULT)
  - IDENTIFY 生成列选项
  - identifier 边界条件

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: alter_table
  official_source: https://www.postgresql.org/docs/16/sql-altertable.html
  statement:
    key: alter_table
    name: ALTER TABLE
    aliases:
    - ALTER TABLE
    - alter table
    - alter_table
    purpose: change the definition of a table
  syntax_templates:
  - |
    ALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]
        action [, ... ]
  - |
    ALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]
        RENAME [ COLUMN ] column_name TO new_column_name
  - |
    ALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]
        RENAME CONSTRAINT constraint_name TO new_constraint_name
  - |
    ALTER TABLE [ IF EXISTS ] name
        RENAME TO new_name
  - |
    ALTER TABLE [ IF EXISTS ] name
        SET SCHEMA new_schema
  - |
    ALTER TABLE ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]
        SET TABLESPACE new_tablespace [ NOWAIT ]
  - |
    ALTER TABLE [ IF EXISTS ] name
        ATTACH PARTITION partition_name { FOR VALUES partition_bound_spec | DEFAULT }
  - |
    ALTER TABLE [ IF EXISTS ] name
        DETACH PARTITION partition_name [ CONCURRENTLY | FINALIZE ]
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - subcommand_category
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_exists_clause
    - if_not_exists_clause
    - cascade_restrict
    - only_clause
    - privilege_level
    - column_type_conversion
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - column_name_shape
    - constraint_name_shape
    - new_name_shape
    - data_type
    - expression_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - base_table_template_coverage
    - dependency_state
    - schema_dependency
    - tablespace_dependency
    - role_dependency
    - parent_table_dependency
    - referenced_table_dependency
    - index_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_table
    - nonexistent_column
    - nonexistent_constraint
    - type_conversion_impossible
    - constraint_violation_existing_data
    - privilege_insufficient
    - partition_mismatch
    - dependent_objects_block
    - identifier_length_exceeded
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification_mode
    - cleanup_mode
  factors:
    statement_branch:
      label: 官方语法顶层形式
      importance: important
      values:
      - key: branch_1_action
        label: action 形式 (ALTER TABLE ... action [, ...])
      - key: branch_2_rename_column
        label: RENAME COLUMN 形式
      - key: branch_3_rename_constraint
        label: RENAME CONSTRAINT 形式
      - key: branch_4_rename_table
        label: RENAME TO 形式 (重命名表)
      - key: branch_5_set_schema
        label: SET SCHEMA 形式
      - key: branch_6_set_tablespace_batch
        label: SET TABLESPACE 批量形式 (ALL IN TABLESPACE)
      - key: branch_7_attach_partition
        label: ATTACH PARTITION 形式
      - key: branch_8_detach_partition
        label: DETACH PARTITION 形式
    subcommand_category:
      label: action 子命令类别 (仅用于 branch_1_action)
      importance: important
      values:
      - key: add_column
        label: ADD [ COLUMN ] [ IF NOT EXISTS ] column_name data_type
      - key: drop_column
        label: DROP [ COLUMN ] [ IF EXISTS ] column_name [ RESTRICT | CASCADE ]
      - key: alter_column_type
        label: ALTER [ COLUMN ] column_name [ SET DATA ] TYPE data_type [ USING expression ]
      - key: alter_column_set_default
        label: ALTER [ COLUMN ] column_name SET DEFAULT expression
      - key: alter_column_drop_default
        label: ALTER [ COLUMN ] column_name DROP DEFAULT
      - key: alter_column_set_drop_not_null
        label: ALTER [ COLUMN ] column_name { SET | DROP } NOT NULL
      - key: alter_column_drop_expression
        label: ALTER [ COLUMN ] column_name DROP EXPRESSION [ IF EXISTS ]
      - key: alter_column_add_generated_identity
        label: ALTER [ COLUMN ] column_name ADD GENERATED { ALWAYS | BY DEFAULT } AS IDENTITY
      - key: alter_column_set_generated_restart
        label: ALTER [ COLUMN ] column_name { SET GENERATED | SET sequence_option | RESTART }
      - key: alter_column_drop_identity
        label: ALTER [ COLUMN ] column_name DROP IDENTITY [ IF EXISTS ]
      - key: alter_column_set_statistics
        label: ALTER [ COLUMN ] column_name SET STATISTICS integer
      - key: alter_column_set_attribute_option
        label: ALTER [ COLUMN ] column_name SET ( attribute_option = value [, ... ] )
      - key: alter_column_reset_attribute_option
        label: ALTER [ COLUMN ] column_name RESET ( attribute_option [, ... ] )
      - key: alter_column_set_storage
        label: ALTER [ COLUMN ] column_name SET STORAGE { PLAIN | EXTERNAL | EXTENDED | MAIN | DEFAULT }
      - key: alter_column_set_compression
        label: ALTER [ COLUMN ] column_name SET COMPRESSION compression_method
      - key: add_table_constraint
        label: ADD table_constraint [ NOT VALID ]
      - key: add_table_constraint_using_index
        label: ADD table_constraint_using_index
      - key: alter_constraint
        label: ALTER CONSTRAINT constraint_name [ DEFERRABLE | NOT DEFERRABLE ]
      - key: validate_constraint
        label: VALIDATE CONSTRAINT constraint_name
      - key: drop_constraint
        label: DROP CONSTRAINT [ IF EXISTS ] constraint_name [ RESTRICT | CASCADE ]
      - key: disable_trigger
        label: DISABLE TRIGGER [ trigger_name | ALL | USER ]
      - key: enable_trigger
        label: ENABLE TRIGGER [ trigger_name | ALL | USER ]
      - key: enable_replica_trigger
        label: ENABLE REPLICA TRIGGER trigger_name
      - key: enable_always_trigger
        label: ENABLE ALWAYS TRIGGER trigger_name
      - key: disable_rule
        label: DISABLE RULE rewrite_rule_name
      - key: enable_rule
        label: ENABLE RULE rewrite_rule_name
      - key: enable_replica_rule
        label: ENABLE REPLICA RULE rewrite_rule_name
      - key: enable_always_rule
        label: ENABLE ALWAYS RULE rewrite_rule_name
      - key: disable_row_level_security
        label: DISABLE ROW LEVEL SECURITY
      - key: enable_row_level_security
        label: ENABLE ROW LEVEL SECURITY
      - key: force_row_level_security
        label: FORCE ROW LEVEL SECURITY
      - key: no_force_row_level_security
        label: NO FORCE ROW LEVEL SECURITY
      - key: cluster_on
        label: CLUSTER ON index_name
      - key: set_without_cluster
        label: SET WITHOUT CLUSTER
      - key: set_without_oids
        label: SET WITHOUT OIDS
      - key: set_access_method
        label: SET ACCESS METHOD new_access_method
      - key: set_tablespace
        label: SET TABLESPACE new_tablespace
      - key: set_logged_unlogged
        label: SET { LOGGED | UNLOGGED }
      - key: set_storage_parameter
        label: SET ( storage_parameter [= value] [, ... ] )
      - key: reset_storage_parameter
        label: RESET ( storage_parameter [, ... ] )
      - key: inherit
        label: INHERIT parent_table
      - key: no_inherit
        label: NO INHERIT parent_table
      - key: of_type
        label: OF type_name
      - key: not_of
        label: NOT OF
      - key: owner_to
        label: OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: replica_identity
        label: REPLICA IDENTITY { DEFAULT | USING INDEX index_name | FULL | NOTHING }
    object_state:
      label: 目标表对象状态
      importance: important
      values:
      - key: exists_normal
        label: 普通永久表已存在
      - key: exists_partitioned
        label: 分区表已存在
      - key: exists_temporary
        label: 临时表已存在
      - key: exists_unlogged
        label: 无日志表已存在
      - key: not_exists
        label: 表不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: 顶层 IF EXISTS 子句
      importance: important
      values:
      - key: present
        label: 包含 IF EXISTS
      - key: absent
        label: 不包含 IF EXISTS
    if_not_exists_clause:
      label: ADD COLUMN IF NOT EXISTS 子句
      importance: important
      values:
      - key: present
        label: 包含 IF NOT EXISTS
      - key: absent
        label: 不包含 IF NOT EXISTS
    cascade_restrict:
      label: CASCADE/RESTRICT 选择
      importance: important
      values:
      - key: CASCADE
        label: CASCADE (级联删除依赖对象)
      - key: RESTRICT
        label: RESTRICT (拒绝删除，有依赖时报错)
      - key: absent
        label: 不指定 (默认 RESTRICT)
    only_clause:
      label: ONLY 子句
      importance: important
      values:
      - key: present
        label: 包含 ONLY (不递归到子表)
      - key: absent
        label: 不包含 ONLY (递归到子表)
    privilege_level:
      label: 权限级别
      importance: important
      values:
      - key: superuser
        label: 超级用户
      - key: table_owner
        label: 表 Owner
      - key: non_owner_with_privilege
        label: 非Owner但有权限
      - key: non_owner_no_privilege
        label: 非Owner且无权限
    column_type_conversion:
      label: 列类型转换类别 (仅用于 ALTER COLUMN TYPE)
      importance: important
      values:
      - key: compatible_no_using
        label: 兼容转换无需 USING (如 int→bigint)
      - key: compatible_with_collation
        label: 兼容转换带 COLLATE (如 text→varchar COLLATE)
      - key: incompatible_with_using
        label: 不兼容转换需要 USING (如 text→integer USING expression)
      - key: incompatible_no_using_error
        label: 不兼容转换无 USING → 报错 (如 text→integer 无 USING)
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
      - key: nonexistent
        label: 不存在表名
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
      - key: nonexistent
        label: 不存在列名
    constraint_name_shape:
      label: 约束名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: nonexistent
        label: 不存在约束名
    new_name_shape:
      label: 新名称形态 (用于 RENAME)
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: duplicate
        label: 已存在名称冲突
    data_type:
      label: 列数据类型 (仅用于 ADD COLUMN 和 ALTER COLUMN TYPE)
      importance: important
      values:
      # --- 整数类型 ---
      - key: smallint
        label: smallint (2字节整数)
      - key: integer
        label: integer / int (4字节整数)
      - key: bigint
        label: bigint (8字节整数)
      # --- 浮点类型 ---
      - key: real
        label: real (4字节浮点)
      - key: double_precision
        label: double precision (8字节浮点)
      # --- 精确数值类型 ---
      - key: numeric
        label: numeric (可变精度)
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
      # --- 网络地址类型 ---
      - key: inet
        label: inet (IPv4/IPv6主机地址)
      - key: cidr
        label: cidr (IPv4/IPv6网络地址)
      # --- 位串类型 ---
      - key: bit
        label: bit (定长位串)
      - key: bit_varying
        label: bit varying / varbit (变长位串)
      # --- 全文搜索类型 ---
      - key: tsvector
        label: tsvector (全文搜索文档向量)
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
      # --- 范围类型 ---
      - key: int4range
        label: int4range (整数范围)
      - key: daterange
        label: daterange (日期范围)
      # --- 复合类型 ---
      - key: composite_type
        label: 用户定义复合类型
      # --- 枚举类型 ---
      - key: enum_type
        label: 用户定义枚举类型
      # --- 对象标识符类型 ---
      - key: oid
        label: oid (对象标识符)
      # --- LSN 类型 ---
      - key: pg_lsn
        label: pg_lsn (日志序列号)
    expression_shape:
      label: USING/DEFAULT 表达式形态
      importance: non_important
      values:
      - key: simple_cast
        label: 简单类型转换表达式 (如 column_name::integer)
      - key: complex_expression
        label: 复杂表达式 (如 length(column_name))
      - key: invalid_expression
        label: 无效表达式 (如引用不存在的函数)
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
      - key: table_04_unlogged
        label: 无日志表模板
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - key: views_dependent
        label: 有视图依赖目标表
      - key: FK_dependent
        label: 有外键依赖目标表
      - key: indexes_dependent
        label: 有索引依赖目标表列
      - key: triggers_dependent
        label: 有触发器依赖目标表
      - key: policies_dependent
        label: 有 RLS 策略依赖目标表
      - key: no_dependencies
        label: 无依赖对象
    schema_dependency:
      label: Schema 依赖
      importance: non_important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在
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
      - key: current_role_variants
        label: CURRENT_ROLE / CURRENT_USER / SESSION_USER
    parent_table_dependency:
      label: 父表依赖 (用于 ATTACH/DETACH PARTITION)
      importance: non_important
      values:
      - key: parent_partitioned_exists
        label: 父表已分区且存在
      - key: parent_not_partitioned
        label: 父表存在但未分区
      - key: parent_not_exists
        label: 父表不存在
    referenced_table_dependency:
      label: 外键引用表依赖
      importance: non_important
      values:
      - key: referenced_table_exists
        label: 引用表存在
      - key: referenced_table_not_exists
        label: 引用表不存在
    index_dependency:
      label: 索引依赖
      importance: non_important
      values:
      - key: index_exists
        label: 索引存在
      - key: index_not_exists
        label: 索引不存在
      - key: unique_index_for_constraint
        label: 唯一索引 (用于 ADD table_constraint_using_index)
    nonexistent_table:
      label: 操作不存在的表
      importance: non_important
      values:
      - key: with_IF_EXISTS_notice
        label: 表不存在 + IF EXISTS → notice no-op
      - key: without_IF_EXISTS_error
        label: 表不存在 + 无 IF EXISTS → error
    nonexistent_column:
      label: 操作不存在的列
      importance: non_important
      values:
      - key: with_IF_EXISTS_notice
        label: 列不存在 + IF EXISTS → notice no-op
      - key: without_IF_EXISTS_error
        label: 列不存在 + 无 IF EXISTS → error
    nonexistent_constraint:
      label: 操作不存在的约束
      importance: non_important
      values:
      - key: with_IF_EXISTS_notice
        label: 约束不存在 + IF EXISTS → notice no-op
      - key: without_IF_EXISTS_error
        label: 约束不存在 + 无 IF EXISTS → error
    type_conversion_impossible:
      label: 类型转换不可行
      importance: non_important
      values:
      - key: incompatible_no_using
        label: 类型不兼容且无 USING → 报错
      - key: incompatible_with_using_success
        label: 类型不兼容但有 USING → 成功
    constraint_violation_existing_data:
      label: 已有数据违反新约束
      importance: non_important
      values:
      - key: set_not_null_with_nulls
        label: SET NOT NULL 但列中存在 NULL 值
      - key: add_check_with_violating_rows
        label: ADD CHECK 但已有行违反条件
      - key: add_unique_with_duplicates
        label: ADD UNIQUE 但已有重复值
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: non_owner_attempt
        label: 非Owner尝试ALTER
      - key: non_superuser_constraint_trigger
        label: 非Superuser尝试禁用约束触发器
    partition_mismatch:
      label: 分区边界不匹配
      importance: non_important
      values:
      - key: bound_overlap
        label: 分区边界与已有分区重叠
      - key: bound_type_mismatch
        label: 分区边界类型与父表分区键不匹配
      - key: detach_concurrently_with_FK
        label: DETACH PARTITION CONCURRENTLY 但存在外键引用
    dependent_objects_block:
      label: 依赖对象阻止操作
      importance: non_important
      values:
      - key: drop_column_cascade
        label: DROP COLUMN CASCADE (级联删除依赖)
      - key: drop_column_restrict_blocked
        label: DROP COLUMN RESTRICT (依赖阻止删除)
      - key: drop_constraint_cascade
        label: DROP CONSTRAINT CASCADE
      - key: drop_constraint_restrict_blocked
        label: DROP CONSTRAINT RESTRICT (依赖阻止删除)
    identifier_length_exceeded:
      label: 标识符长度超限
      importance: non_important
      values:
      - key: over_63_chars
        label: 标识符超过63字符
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询
      - key: pg_attribute_query
        label: pg_attribute 列属性查询
      - key: pg_constraint_query
        label: pg_constraint 约束查询
      - key: information_schema_query
        label: information_schema 查询
      - key: SELECT_inspection
        label: SELECT 数据检查验证
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_TABLE_IF_EXISTS
        label: DROP TABLE IF EXISTS
      - key: DROP_TABLE_CASCADE
        label: DROP TABLE CASCADE
      - key: ALTER_TABLE_REVERT
        label: ALTER TABLE 恢复原状态
      - key: RESET_STATE
        label: 重置数据库状态
  defaults:
    expected_status: success
    object_state: exists_normal
    if_exists_clause: absent
    if_not_exists_clause: absent
    cascade_restrict: absent
    only_clause: absent
    privilege_level: table_owner
    column_type_conversion: compatible_no_using
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - subcommand_category
    - object_state
    - expected_status
    column_type_combination_analysis:
      involve_column_type_combinations:
        description: data_type 因子参与生成的子命令，需要覆盖列数据类型选择
        subcommands:
        - add_column
        - alter_column_type
      involve_column_type_references:
        description: 列数据类型影响行为但 data_type 因子不参与生成的子命令
        subcommands:
        - add_table_constraint
        - alter_column_set_storage
        - alter_column_set_compression
        - alter_column_add_generated_identity
        - of_type
        - attach_partition (branch_7)
      not_involve_column_types:
        description: 不涉及列数据类型的子命令
        subcommands:
        - drop_column
        - alter_column_set_default
        - alter_column_drop_default
        - alter_column_set_drop_not_null
        - alter_column_drop_expression
        - alter_column_set_generated_restart
        - alter_column_drop_identity
        - alter_column_set_statistics
        - alter_column_set_attribute_option
        - alter_column_reset_attribute_option
        - add_table_constraint_using_index
        - alter_constraint
        - validate_constraint
        - drop_constraint
        - disable_trigger
        - enable_trigger
        - enable_replica_trigger
        - enable_always_trigger
        - disable_rule
        - enable_rule
        - enable_replica_rule
        - enable_always_rule
        - disable_row_level_security
        - enable_row_level_security
        - force_row_level_security
        - no_force_row_level_security
        - cluster_on
        - set_without_cluster
        - set_without_oids
        - set_access_method
        - set_tablespace
        - set_logged_unlogged
        - set_storage_parameter
        - reset_storage_parameter
        - inherit
        - no_inherit
        - not_of
        - owner_to
        - replica_identity
        - rename_column (branch_2)
        - rename_constraint (branch_3)
        - rename_table (branch_4)
        - set_schema (branch_5)
        - set_tablespace_batch (branch_6)
        - detach_partition (branch_8)
    non_main_factors:
    - if_exists_clause
    - if_not_exists_clause
    - cascade_restrict
    - only_clause
    - privilege_level
    - column_type_conversion
    - table_name_shape
    - column_name_shape
    - constraint_name_shape
    - new_name_shape
    - data_type
    - expression_shape
    - base_table_template_coverage
    - dependency_state
    - schema_dependency
    - tablespace_dependency
    - role_dependency
    - parent_table_dependency
    - referenced_table_dependency
    - index_dependency
    - nonexistent_table
    - nonexistent_column
    - nonexistent_constraint
    - type_conversion_impossible
    - constraint_violation_existing_data
    - privilege_insufficient
    - partition_mismatch
    - dependent_objects_block
    - identifier_length_exceeded
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - subcommand_category
  rendering:
    statement_template: "ALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ] action"
    verification_query_template: "SELECT * FROM pg_class WHERE relname = '{table_name}'"
    factor_value_bindings:
      if_exists_clause:
        present: "IF EXISTS"
        absent: ""
      if_not_exists_clause:
        present: "IF NOT EXISTS"
        absent: ""
      cascade_restrict:
        CASCADE: "CASCADE"
        RESTRICT: "RESTRICT"
        absent: ""
      only_clause:
        present: "ONLY"
        absent: ""
      column_type_conversion:
        compatible_no_using: "TYPE data_type"
        compatible_with_collation: "TYPE data_type COLLATE collation"
        incompatible_with_using: "TYPE data_type USING expression"
        incompatible_no_using_error: "TYPE data_type"
```
