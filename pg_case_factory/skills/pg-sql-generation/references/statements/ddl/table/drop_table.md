# 技能：DROP TABLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droptable.html

```sql
DROP TABLE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

**重要行为说明**：
- DROP TABLE 会自动移除目标表上的索引、规则、触发器和约束，无需 CASCADE。
- 若其他对象依赖该表（如视图引用、外键约束引用），则必须指定 CASCADE；否则 RESTRICT（默认）将拒绝删除。
- CASCADE 删除视图时会连同视图一并删除；CASCADE 删除外键约束时仅移除约束本身，不会删除引用表。
- 只有表拥有者、schema 拥有者和超级用户可以删除表。
- SQL 标准仅允许每条命令删除一个表；PostgreSQL 允许逗号分隔的多个表。
- IF EXISTS 是 PostgreSQL 扩展，不属于 SQL 标准。

## 语句作用

官方说明：DROP TABLE — remove a table

该 reference 关注表删除语句的对象状态、依赖链、权限边界和成功/失败路径。

**特别声明**：DROP TABLE 不涉及列类型组合（它删除整张表而非操作列），但涉及依赖链（视图、外键约束、触发器、策略、规则等依赖对象）。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- object_state：目标表对象状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句
- cascade_restrict：CASCADE / RESTRICT 行为
- table_type_permanence：表类型持久性

### T3：对象名与输入形态因子
- table_name_shape：表名形态
- multi_table_drop：单表/多表删除

### T4：依赖对象与环境因子
- privilege_level：权限级别
- dependency_state：依赖对象状态

### T5：异常与边界因子
- error_boundary：错误边界类型

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖表存在/不存在/临时表/无日志表的删除路径。
- IF EXISTS、CASCADE、RESTRICT 按语句支持情况覆盖。
- 依赖对象（视图、外键、触发器等）必须覆盖 RESTRICT 失败与 CASCADE 成功路径。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP TABLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP TABLE 不涉及列类型组合，无需覆盖不同列类型的交叉组合。
- 依赖链（视图、外键、触发器、策略、规则）必须作为独立成功/失败边界覆盖。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限或 schema 限定的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 临时 / 无日志全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - IF EXISTS、CASCADE、RESTRICT 代表性覆盖
  - schema 限定、owner、依赖对象代表性覆盖
  - 依赖链（视图、外键、触发器）代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: drop_table
  official_source: https://www.postgresql.org/docs/16/sql-droptable.html
  statement:
    key: drop_table
    name: DROP TABLE
    aliases:
    - drop_table
    - DROP TABLE
    - droptable
    - drop table
    purpose: DROP TABLE — remove a table
  syntax_templates:
  - "DROP TABLE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - if_exists_clause
    - cascade_restrict
    - table_type_permanence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - multi_table_drop
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - dependency_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - error_boundary
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
      - key: branch_drop_table
        label: DROP TABLE name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_table_if_exists
        label: DROP TABLE IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标表对象状态
      importance: important
      values:
      - key: exists_permanent
        label: 永久表已存在
      - key: not_exists
        label: 表不存在
      - key: exists_temporary
        label: 临时表已存在
      - key: exists_unlogged
        label: 无日志表已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句
      importance: important
      values:
      - absent
      - present
    cascade_restrict:
      label: CASCADE / RESTRICT 行为
      importance: important
      values:
      - none
      - cascade
      - restrict
    table_type_permanence:
      label: 表类型持久性
      importance: non_important
      values:
      - permanent
      - temporary
      - unlogged
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - simple
      - quoted
      - schema_qualified
      - non_existent
      - reserved_word
    multi_table_drop:
      label: 单表/多表删除
      importance: non_important
      values:
      - single_table
      - multi_table
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - owner
      - superuser
      - schema_owner
      - non_owner
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - no_dependents
      - has_views
      - has_fk_references
      - has_triggers
      - has_indexes
      - has_policies
      - has_rules
    error_boundary:
      label: 错误边界类型
      importance: non_important
      values:
      - none
      - non_existent_without_if_exists
      - dependent_objects_without_cascade
      - insufficient_privilege
      - drop_table_in_use
      - self_referential_fk
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_class_query
      - error_assertion
      - notice_assertion
      - effect_query
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - cascade_cleanup
      - manual_cleanup
      - rollback
  notes:
    column_type_combination: DROP TABLE 不涉及列类型组合，它删除整张表而非操作列。
    dependency_chain: DROP TABLE 涉及依赖链（视图、外键约束、触发器、策略、规则），这些依赖对象决定 CASCADE/RESTRICT 行为。
    auto_dropped: 目标表上的索引、规则、触发器和约束会被自动删除，无需 CASCADE。
    fk_cascade_behavior: CASCADE 删除外键约束时仅移除约束本身，不会删除引用表。
    view_cascade_behavior: CASCADE 删除视图时会连同视图一并删除。
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - table_type_permanence
    - table_name_shape
    - multi_table_drop
    - privilege_level
    - dependency_state
    - error_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP TABLE [ IF EXISTS ] {table_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT 1 FROM pg_class WHERE relname = '{table_name}' AND relkind = 'r'"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      cascade_restrict:
        none: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
