# 技能：DROP SEQUENCE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropsequence.html

```sql
DROP SEQUENCE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

**重要行为说明**：
- 只有序列的 Owner 或超级用户可以删除序列。
- RESTRICT（默认）拒绝删除有任何对象依赖的序列（如 identity 列、serial 列、OWNED BY 关联列）。
- CASCADE 自动删除依赖该序列的对象，以及进一步依赖这些对象的对象。
- PostgreSQL 允许每条命令删除多个序列（逗号分隔）；SQL 标准仅允许一个。
- IF EXISTS 是 PostgreSQL 扩展，不属于 SQL 标准。
- DROP SEQUENCE 可能需要 CASCADE 删除 identity/serial 列关联的序列时连带删除表。

## 语句作用

官方说明：DROP SEQUENCE — remove a sequence

该 reference 关注序列删除语句的对象状态、依赖链、权限边界和成功/失败路径。

**特别声明**：DROP SEQUENCE 不直接涉及列类型组合（它删除整个序列而非操作列），但涉及依赖链（identity 列、serial 列、OWNED BY 关联等依赖对象）。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- object_state：目标序列对象状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句
- cascade_restrict：CASCADE / RESTRICT 行为
- multi_sequence_drop：单序列 / 多序列删除
- sequence_type_permanence：序列类型持久性（permanent、temporary、unlogged）

### T3：对象名与输入形态因子
- sequence_name_shape：序列名形态

### T4：依赖对象与环境因子
- privilege_level：权限级别
- dependency_state：依赖对象状态

### T5：异常与边界因子
- error_boundary：错误边界类型

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖序列存在/不存在/永久/临时/无日志的删除路径。
- IF EXISTS、CASCADE、RESTRICT 按语句支持情况覆盖。
- 依赖对象（identity 列、serial 列、OWNED BY 关联）必须覆盖 RESTRICT 失败与 CASCADE 成功路径。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP SEQUENCE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP SEQUENCE 不涉及列类型组合，无需覆盖不同列类型的交叉组合。
- 依赖链（identity 列、serial 列、OWNED BY 关联列）必须作为独立成功/失败边界覆盖。
- CASCADE 删除 identity/serial 列关联的序列时可能连带删除表，必须作为代表性边界覆盖。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限或 Schema 限定的分支。
- T4 因子中 dependency_state 挂靠到 CASCADE/RESTRICT 分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 永久 / 临时 / 无日志全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - IF EXISTS、CASCADE、RESTRICT 代表性覆盖
  - 依赖链（identity 列、serial 列、OWNED BY）代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: sequence
  skill_name: drop_sequence
  official_source: https://www.postgresql.org/docs/16/sql-dropsequence.html
  statement:
    key: drop_sequence
    name: DROP SEQUENCE
    aliases:
    - DROP SEQUENCE
    - drop sequence
    - drop_sequence
    - dropsequence
    purpose: remove a sequence
  syntax_templates:
  - "DROP SEQUENCE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - multi_sequence_drop
    - sequence_type_permanence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - sequence_name_shape
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
      - key: branch_drop_sequence
        label: DROP SEQUENCE name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_sequence_if_exists
        label: DROP SEQUENCE IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标序列对象状态
      importance: important
      values:
      - key: exists_permanent
        label: 永久序列已存在
      - key: not_exists
        label: 序列不存在
      - key: exists_temporary
        label: 临时序列已存在
      - key: exists_unlogged
        label: 无日志序列已存在
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
      - key: absent
        label: 无 IF EXISTS
      - key: present
        label: 包含 IF EXISTS
    cascade_restrict:
      label: CASCADE / RESTRICT 行为
      importance: important
      values:
      - key: none
        label: 无 CASCADE/RESTRICT (默认RESTRICT)
      - key: cascade
        label: CASCADE
      - key: restrict
        label: RESTRICT
    multi_sequence_drop:
      label: 单/多序列删除
      importance: non_important
      values:
      - key: single_sequence
        label: 单个序列
      - key: multi_sequence
        label: 多个序列 (逗号分隔)
    sequence_type_permanence:
      label: 序列类型持久性
      importance: non_important
      values:
      - key: permanent
        label: 永久序列
      - key: temporary
        label: 临时序列
      - key: unlogged
        label: 无日志序列
    sequence_name_shape:
      label: 序列名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: schema_qualified
        label: Schema限定标识符
      - key: reserved_word
        label: 保留字标识符
      - key: non_existent
        label: 不存在标识符
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: owner
        label: 序列 Owner
      - key: superuser
        label: 超级用户
      - key: non_owner
        label: 非 Owner
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - key: no_dependents
        label: 无依赖对象
      - key: used_by_identity_column
        label: identity 列使用该序列
      - key: used_by_serial_column
        label: serial 列使用该序列
      - key: owned_by_table_column
        label: OWNED BY 关联列使用该序列
      - key: used_by_default_expression
        label: DEFAULT nextval() 表达式引用该序列
    error_boundary:
      label: 错误边界类型
      importance: non_important
      values:
      - key: none
        label: 无错误
      - key: non_existent_without_if_exists
        label: 不存在且无 IF EXISTS → error
      - key: dependent_objects_without_cascade
        label: 依赖对象存在且无 CASCADE → error
      - key: insufficient_privilege
        label: 权限不足 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_query
        label: pg_class 系统目录查询
      - key: error_assertion
        label: 错误消息断言
      - key: notice_assertion
        label: NOTICE 消息断言
      - key: effect_query
        label: 效果验证查询
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: no_cleanup_needed
        label: 无需清理 (对象已删除)
      - key: cascade_cleanup
        label: CASCADE 清理残余依赖对象
      - key: manual_cleanup
        label: 手动清理残余对象
      - key: rollback
        label: 事务回滚
  notes:
    column_type_combination: DROP SEQUENCE 不涉及列类型组合，它删除整个序列而非操作列。
    dependency_chain: DROP SEQUENCE 涉及依赖链（identity列、serial列、OWNED BY关联列等），这些依赖对象决定 CASCADE/RESTRICT 行为。
    cascade_may_drop_tables: CASCADE 删除 identity/serial 列关联的序列时可能连带删除表。
    only_owner_can_drop: 只有序列 Owner 和超级用户可以删除序列。
    restrict_default: RESTRICT 是默认行为，拒绝删除有依赖对象的序列。
    serial_and_identity_dependency: serial 和 identity 列隐式创建序列，删除序列需要 CASCADE 或先删除列。
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
    - multi_sequence_drop
    - sequence_type_permanence
    - sequence_name_shape
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
    statement_template: "DROP SEQUENCE [ IF EXISTS ] {sequence_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT count(*) FROM pg_class WHERE relname = '{sequence_name}' AND relkind = 'S'"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      cascade_restrict:
        none: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
