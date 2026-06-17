# 技能：CREATE SEQUENCE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createsequence.html

```sql
CREATE [ { TEMPORARY | TEMP } | UNLOGGED ] SEQUENCE [ IF NOT EXISTS ] name
    [ AS data_type ]
    [ INCREMENT [ BY ] increment ]
    [ MINVALUE minvalue | NO MINVALUE ] [ MAXVALUE maxvalue | NO MAXVALUE ]
    [ START [ WITH ] start ] [ CACHE cache ] [ [ NO ] CYCLE ]
    [ OWNED BY { table_name.column_name | NONE } ]
```

**重要行为说明**：
- TEMPORARY / TEMP 创建会话级临时序列，会话结束时自动删除；同名的永久序列在临时序列存在期间不可见（除非 Schema 限定）。临时序列不允许指定 Schema 名。
- UNLOGGED 序列的变更不写入 WAL，崩溃/不干净关机后重置为初始状态，不复制到备用服务器。与 logged 序列无明显性能差异，主要用于与 UNLOGGED 表关联。
- IF NOT EXISTS 不保证已存在关系是序列类型，仅抑制错误并发出 NOTICE。
- AS data_type 仅支持 smallint、integer、bigint，默认 bigint。类型决定隐式 min/max 值。
- INCREMENT 正值 = 递增序列，负值 = 递减序列，默认 1。
- MINVALUE / MAXVALUE 默认：递增→min=1/max=类型上限；递减→min=类型下限/max=-1。
- START 默认：递增→minvalue，递减→maxvalue。
- CACHE >=1（默认1=无缓存）；多会话时保证值唯一但不保证连续。
- CYCLE 到极限后回绕；NO CYCLE（默认）到极限后 nextval 报错。
- OWNED BY 将序列关联到列，列/表删除时自动删除序列；表须与序列同 Owner 同 Schema。
- nextval/setval 不会被回滚，序列值不保证无间隙。
- 序列名必须与同 Schema 中任何其他关系（表、视图、索引等）不同。

## 语句作用

官方说明：CREATE SEQUENCE — define a new sequence generator

该 reference 关注序列定义语句的语法分支、数据类型选择、参数组合与依赖环境，不负责包装所有样本到统一外层事务。

CREATE SEQUENCE **不直接涉及列类型组合**，但序列被 serial/identity 列使用。序列的数据类型选择（AS smallint/integer/bigint）是本 skill 的核心职责之一。序列参数组合（INCREMENT、MINVALUE、MAXVALUE、START、CACHE、CYCLE、OWNED BY）也需覆盖。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（永久序列、临时序列、无日志序列）
- object_state：目标序列对象存在性（不存在、已存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- sequence_type：序列类型（permanent、temporary、temporary_short、unlogged）
- if_not_exists_clause：IF NOT EXISTS 子句（present、absent）
- as_data_type：AS 数据类型（smallint、integer、bigint、absent_default）
- increment_direction：递增方向（ascending、descending）
- cycle_clause：CYCLE 子句（CYCLE、NO CYCLE、absent_default）
- owned_by_clause：OWNED BY 子句（owned_by_column、owned_by_none、absent_default）

### T3：对象名与输入形态因子
- sequence_name_shape：序列名形态（simple、quoted、reserved_word、schema_qualified、non_existent）
- minvalue_maxvalue_setting：MINVALUE/MAXVALUE 设置（explicit_values、NO_MINVALUE_NO_MAXVALUE、absent_defaults）
- start_value_setting：START 值设置（explicit_start、absent_default）
- cache_value：CACHE 值（1、10、absent_default）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、sequence_creator、non_creator_no_privilege）
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists、pg_catalog_reserved）
- owned_by_table_dependency：OWNED BY 表列依赖（table_column_exists、table_column_not_exists、different_owner、different_schema）
- same_name_conflict：同名关系冲突（same_name_table、same_name_view、same_name_index）

### T5：异常与边界因子
- duplicate_sequence_name：重名冲突（with_IF_NOT_EXISTS_noop、without_IF_NOT_EXISTS_error）
- increment_zero：INCREMENT 为零（非法）
- minvalue_greater_than_maxvalue：MINVALUE > MAXVALUE（非法）
- start_out_of_range：START 值超出 MINVALUE/MAXVALUE 范围
- incompatible_data_type_values：数据类型与 MIN/MAX/START 值不兼容
- temporary_sequence_with_schema：临时序列指定 Schema 名（非法）
- owned_by_different_owner：OWNED BY 表与序列不同 Owner
- owned_by_different_schema：OWNED BY 表与序列不同 Schema
- insufficient_privilege：权限不足

### T6：验证与清理因子
- verification_mode：验证方式（pg_class_catalog_query、sequence_inspection_query、nextval_call）
- cleanup_mode：清理方式（DROP_SEQUENCE、DROP_SEQUENCE_IF_EXISTS、DROP_SEQUENCE_CASCADE）

## 覆盖策略

- 必须覆盖所有三种序列类型（永久、临时、无日志）的创建路径。
- CREATE SEQUENCE 不涉及列类型组合，但 AS 数据类型（smallint/integer/bigint）必须覆盖。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。
- 递增序列与递减序列必须分别覆盖。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 IF NOT EXISTS 时，需要分别覆盖正常创建、no-op 语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE SEQUENCE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- **AS 数据类型必须参与生成**：smallint、integer、bigint 三种数据类型必须在至少一个 CREATE SEQUENCE 样本中出现。
- 递增/递减序列必须分别覆盖。
- CYCLE/NO CYCLE 必须分别覆盖。
- OWNED BY NONE / OWNED BY column 必须分别覆盖。
- 临时序列不允许 Schema 名，必须作为失败边界覆盖。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 sequence_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 minvalue_maxvalue_setting 挂靠到包含参数组合的代表性样本。
- T3 因子中 start_value_setting 和 cache_value 挂靠到包含对应子句的样本。
- T4 因子仅挂靠到需要依赖对象、权限或 Schema 限定的分支。
- T4 因子中 owned_by_table_dependency 挂靠到包含 OWNED BY 子句的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（永久、临时、无日志）
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - AS 数据类型全覆盖（smallint、integer、bigint）
  - 递增 / 递减路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - IF NOT EXISTS 代表性覆盖
  - CYCLE / NO CYCLE 代表性覆盖
  - OWNED BY NONE / OWNED BY column 代表性覆盖
  - 参数组合代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - CACHE 大值
  - START / INCREMENT 边界值
  - 标识符边界条件

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: sequence
  skill_name: create_sequence
  official_source: https://www.postgresql.org/docs/16/sql-createsequence.html
  statement:
    key: create_sequence
    name: CREATE SEQUENCE
    aliases:
    - CREATE SEQUENCE
    - create sequence
    - create_sequence
    purpose: define a new sequence generator
  syntax_templates:
  - "CREATE [ { TEMPORARY | TEMP } | UNLOGGED ] SEQUENCE [ IF NOT EXISTS ] name [ AS data_type ] [ INCREMENT [ BY ] increment ] [ MINVALUE minvalue | NO MINVALUE ] [ MAXVALUE maxvalue | NO MAXVALUE ] [ START [ WITH ] start ] [ CACHE cache ] [ [ NO ] CYCLE ] [ OWNED BY { table_name.column_name | NONE } ]"
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
    - sequence_type
    - if_not_exists_clause
    - as_data_type
    - increment_direction
    - cycle_clause
    - owned_by_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - sequence_name_shape
    - minvalue_maxvalue_setting
    - start_value_setting
    - cache_value
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_dependency
    - owned_by_table_dependency
    - same_name_conflict
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_sequence_name
    - increment_zero
    - minvalue_greater_than_maxvalue
    - start_out_of_range
    - incompatible_data_type_values
    - temporary_sequence_with_schema
    - owned_by_different_owner
    - owned_by_different_schema
    - insufficient_privilege
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
        label: CREATE SEQUENCE name [ ... ] (永久序列)
      - key: branch_temporary
        label: CREATE TEMPORARY SEQUENCE name [ ... ] (临时序列)
      - key: branch_temp
        label: CREATE TEMP SEQUENCE name [ ... ] (临时序列简写)
      - key: branch_unlogged
        label: CREATE UNLOGGED SEQUENCE name [ ... ] (无日志序列)
      - key: branch_if_not_exists_permanent
        label: CREATE SEQUENCE IF NOT EXISTS name [ ... ] (幂等永久序列)
      - key: branch_if_not_exists_temporary
        label: CREATE TEMPORARY SEQUENCE IF NOT EXISTS name [ ... ] (幂等临时序列)
    object_state:
      label: 目标序列对象存在性
      importance: important
      values:
      - key: not_exists
        label: 序列不存在
      - key: already_exists
        label: 序列已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    sequence_type:
      label: 序列类型
      importance: important
      values:
      - key: permanent
        label: 永久序列
      - key: temporary
        label: 临时序列 (TEMPORARY)
      - key: temporary_short
        label: 临时序列简写 (TEMP)
      - key: unlogged
        label: 无日志序列 (UNLOGGED)
    if_not_exists_clause:
      label: IF NOT EXISTS 子句
      importance: important
      values:
      - key: present
        label: 包含 IF NOT EXISTS
      - key: absent
        label: 不包含 IF NOT EXISTS
    as_data_type:
      label: AS 数据类型
      importance: important
      values:
      - key: smallint
        label: AS smallint
      - key: integer
        label: AS integer
      - key: bigint
        label: AS bigint
      - key: absent_default
        label: 无 AS 子句 (默认bigint)
    increment_direction:
      label: 递增方向
      importance: important
      values:
      - key: ascending
        label: 正增量 (递增序列)
      - key: descending
        label: 负增量 (递减序列)
    cycle_clause:
      label: CYCLE 子句
      importance: important
      values:
      - key: CYCLE
        label: CYCLE (到极限后回绕)
      - key: NO_CYCLE
        label: NO CYCLE (到极限后报错)
      - key: absent_default
        label: 无 CYCLE 子句 (默认NO CYCLE)
    owned_by_clause:
      label: OWNED BY 子句
      importance: important
      values:
      - key: owned_by_column
        label: OWNED BY table_name.column_name
      - key: owned_by_none
        label: OWNED BY NONE
      - key: absent_default
        label: 无 OWNED BY 子句 (默认NONE)
    sequence_name_shape:
      label: 序列名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: schema_qualified
        label: Schema限定标识符
      - key: non_existent
        label: 不存在标识符
    minvalue_maxvalue_setting:
      label: MINVALUE/MAXVALUE设置
      importance: non_important
      values:
      - key: explicit_values
        label: 显式指定MINVALUE和MAXVALUE
      - key: NO_MINVALUE_NO_MAXVALUE
        label: NO MINVALUE / NO MAXVALUE (使用类型隐式值)
      - key: absent_defaults
        label: 无子句 (使用默认值)
    start_value_setting:
      label: START值设置
      importance: non_important
      values:
      - key: explicit_start
        label: 显式START WITH值
      - key: absent_default
        label: 无START子句 (使用默认值)
    cache_value:
      label: CACHE值
      importance: non_important
      values:
      - key: cache_1
        label: CACHE 1 (无缓存)
      - key: cache_10
        label: CACHE 10
      - key: absent_default
        label: 无CACHE子句 (默认1)
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: sequence_creator
        label: 拥有CREATE权限的用户
      - key: non_creator_no_privilege
        label: 无CREATE权限的用户
    schema_dependency:
      label: Schema依赖
      importance: non_important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在
      - key: pg_catalog_reserved
        label: pg_catalog (系统保留)
    owned_by_table_dependency:
      label: OWNED BY表列依赖
      importance: non_important
      values:
      - key: table_column_exists
        label: 关联表列已存在
      - key: table_column_not_exists
        label: 关联表列不存在
      - key: different_owner
        label: 关联表与序列不同Owner
      - key: different_schema
        label: 关联表与序列不同Schema
    same_name_conflict:
      label: 同名关系冲突
      importance: non_important
      values:
      - key: same_name_table
        label: 同名表已存在
      - key: same_name_view
        label: 同名视图已存在
    duplicate_sequence_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: with_IF_NOT_EXISTS_noop
        label: 重名 + IF NOT EXISTS → no-op
      - key: without_IF_NOT_EXISTS_error
        label: 重名 + 无 IF NOT EXISTS → error
    increment_zero:
      label: INCREMENT为零
      importance: non_important
      values:
      - key: zero_increment
        label: INCREMENT 0 → error
    minvalue_greater_than_maxvalue:
      label: MINVALUE > MAXVALUE
      importance: non_important
      values:
      - key: min_greater_than_max
        label: MINVALUE > MAXVALUE → error
    start_out_of_range:
      label: START值超出范围
      importance: non_important
      values:
      - key: start_below_minvalue
        label: START < MINVALUE → error
      - key: start_above_maxvalue
        label: START > MAXVALUE → error
    incompatible_data_type_values:
      label: 数据类型与值不兼容
      importance: non_important
      values:
      - key: smallint_overflow
        label: smallint类型与超出范围的值 → error
    temporary_sequence_with_schema:
      label: 临时序列指定Schema名
      importance: non_important
      values:
      - key: temp_with_schema_illegal
        label: 临时序列指定Schema名 → error
    owned_by_different_owner:
      label: OWNED BY不同Owner
      importance: non_important
      values:
      - key: table_different_owner
        label: 关联表与序列不同Owner → error
    owned_by_different_schema:
      label: OWNED BY不同Schema
      importance: non_important
      values:
      - key: table_different_schema
        label: 关联表与序列不同Schema → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: no_CREATE_privilege
        label: 无Schema CREATE权限 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询
      - key: sequence_inspection_query
        label: SELECT * FROM sequence_name 查询
      - key: nextval_call
        label: nextval() 调用验证
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_SEQUENCE
        label: DROP SEQUENCE sequence_name
      - key: DROP_SEQUENCE_IF_EXISTS
        label: DROP SEQUENCE IF EXISTS sequence_name
      - key: DROP_SEQUENCE_CASCADE
        label: DROP SEQUENCE sequence_name CASCADE
  notes:
    no_column_type_combination: CREATE SEQUENCE 不直接涉及列类型组合，但序列被 serial/identity 列使用。
    as_data_type_coverage: AS 数据类型（smallint/integer/bigint）是序列定义的核心参数，必须覆盖。
    increment_direction: 递增/递减序列有不同的默认参数值和行为。
    owned_by_column: OWNED BY 关联序列到列时，表须与序列同 Owner 同 Schema。
    temporary_sequence_no_schema: 临时序列不允许指定 Schema 名。
    no_gapless_guarantee: nextval/setval 不回滚，序列值不保证无间隙。
    unlogged_sequence: UNLOGGED 序列不写入 WAL，崩溃后重置为初始状态。
  defaults:
    expected_status: success
    sequence_type: permanent
    if_not_exists_clause: absent
    as_data_type: absent_default
    increment_direction: ascending
    cycle_clause: absent_default
    owned_by_clause: absent_default
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - sequence_type
    - if_not_exists_clause
    - as_data_type
    - increment_direction
    - cycle_clause
    - owned_by_clause
    - sequence_name_shape
    - minvalue_maxvalue_setting
    - start_value_setting
    - cache_value
    - privilege_level
    - schema_dependency
    - owned_by_table_dependency
    - same_name_conflict
    - duplicate_sequence_name
    - increment_zero
    - minvalue_greater_than_maxvalue
    - start_out_of_range
    - incompatible_data_type_values
    - temporary_sequence_with_schema
    - owned_by_different_owner
    - owned_by_different_schema
    - insufficient_privilege
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE [ { TEMPORARY | TEMP } | UNLOGGED ] SEQUENCE [ IF NOT EXISTS ] {sequence_name} [ AS data_type ] [ INCREMENT [ BY ] increment ] [ MINVALUE minvalue | NO MINVALUE ] [ MAXVALUE maxvalue | NO MAXVALUE ] [ START [ WITH ] start ] [ CACHE cache ] [ [ NO ] CYCLE ] [ OWNED BY { table_name.column_name | NONE } ]"
    verification_query_template: "SELECT count(*) FROM pg_class WHERE relname = '{sequence_name}' AND relkind = 'S'"
    factor_value_bindings:
      sequence_type:
        permanent: ""
        temporary: "TEMPORARY"
        temporary_short: "TEMP"
        unlogged: "UNLOGGED"
      if_not_exists_clause:
        present: "IF NOT EXISTS"
        absent: ""
      as_data_type:
        smallint: "AS smallint"
        integer: "AS integer"
        bigint: "AS bigint"
        absent_default: ""
      increment_direction:
        ascending: "INCREMENT BY 1"
        descending: "INCREMENT BY -1"
      cycle_clause:
        CYCLE: "CYCLE"
        NO_CYCLE: "NO CYCLE"
        absent_default: ""
      owned_by_clause:
        owned_by_column: "OWNED BY {table_name}.{column_name}"
        owned_by_none: "OWNED BY NONE"
        absent_default: ""
```
