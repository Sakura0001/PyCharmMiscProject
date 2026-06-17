# 技能：DROP TYPE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droptype.html

```sql
DROP TYPE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

**重要行为说明**：
- 只有类型的 Owner 可以删除它。
- RESTRICT（默认）拒绝删除有任何对象依赖的类型（如表列、函数、操作符）。
- CASCADE 自动删除依赖该类型的对象（表列、函数、操作符），以及进一步依赖这些对象的对象。
- PostgreSQL 允许每条命令删除多个类型（逗号分隔）；SQL 标准仅允许一个。
- IF EXISTS 是 PostgreSQL 扩展，不属于 SQL 标准。
- DROP TYPE 可能需要 CASCADE 删除依赖表列的类型时连带删除整张表。

## 语句作用

官方说明：DROP TYPE — remove a data type

该 reference 关注类型删除语句的对象状态、依赖链、权限边界和成功/失败路径。

**特别声明**：DROP TYPE 不直接涉及类型定义操作（它删除整个类型而非修改类型），但涉及依赖链（使用该类型的表列、函数、操作符等依赖对象）。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- object_state：目标 Type 对象状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句
- cascade_restrict：CASCADE / RESTRICT 行为
- multi_type_drop：单类型 / 多类型删除
- type_category：目标类型类别（composite、enum、range、base）

### T3：对象名与输入形态因子
- type_name_shape：类型名形态

### T4：依赖对象与环境因子
- privilege_level：权限级别
- dependency_state：依赖对象状态

### T5：异常与边界因子
- error_boundary：错误边界类型

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖类型存在/不存在/各种类别类型的删除路径。
- IF EXISTS、CASCADE、RESTRICT 按语句支持情况覆盖。
- 依赖对象（表列、函数、操作符）必须覆盖 RESTRICT 失败与 CASCADE 成功路径。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP TYPE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP TYPE 不涉及类型定义操作，无需覆盖不同属性数据类型的交叉组合。
- 依赖链（表列使用该类型、函数参数/返回值为该类型、操作符使用该类型）必须作为独立成功/失败边界覆盖。
- CASCADE 删除依赖表列的类型时可能连带删除整张表，必须作为代表性边界覆盖。
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
  - 目标对象存在 / 不存在 / 各类型类别全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - IF EXISTS、CASCADE、RESTRICT 代表性覆盖
  - 各类型类别（composite、enum、range、base）代表性覆盖
  - 依赖链（表列、函数、操作符）代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: type
  skill_name: drop_type
  official_source: https://www.postgresql.org/docs/16/sql-droptype.html
  statement:
    key: drop_type
    name: DROP TYPE
    aliases:
    - DROP TYPE
    - drop type
    - drop_type
    - droptype
    purpose: remove a data type
  syntax_templates:
  - "DROP TYPE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - multi_type_drop
    - type_category
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - type_name_shape
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
      - key: branch_drop_type
        label: DROP TYPE name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_type_if_exists
        label: DROP TYPE IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标Type对象状态
      importance: important
      values:
      - key: exists_composite
        label: 复合类型已存在
      - key: exists_enum
        label: 枚举类型已存在
      - key: exists_range
        label: 范围类型已存在
      - key: exists_base
        label: 基础类型已存在
      - key: not_exists
        label: 类型不存在
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
    multi_type_drop:
      label: 单/多类型删除
      importance: non_important
      values:
      - key: single_type
        label: 单个类型
      - key: multi_type
        label: 多个类型 (逗号分隔)
    type_category:
      label: 目标类型类别
      importance: important
      values:
      - key: composite
        label: 复合类型
      - key: enum
        label: 枚举类型
      - key: range
        label: 范围类型
      - key: base
        label: 基础类型
    type_name_shape:
      label: 类型名形态
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
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: owner
        label: 类型 Owner
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
      - key: used_in_table_columns
        label: 表列使用该类型
      - key: used_in_function_params
        label: 函数参数/返回值使用该类型
      - key: used_in_operators
        label: 操作符使用该类型
      - key: used_in_typed_tables
        label: typed table 依赖该类型
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
      - key: pg_type_query
        label: pg_type 系统目录查询
      - key: information_schema_user_defined_types
        label: information_schema.user_defined_types 查询
      - key: error_assertion
        label: 错误消息断言
      - key: notice_assertion
        label: NOTICE 消息断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: no_cleanup_needed
        label: 无需清理 (对象已删除)
      - key: manual_cleanup
        label: 手动清理残余对象
      - key: rollback
        label: 事务回滚
  notes:
    type_deletion: DROP TYPE 删除整个类型而非修改类型定义，不涉及属性数据类型交叉组合。
    dependency_chain: DROP TYPE 涉及依赖链（表列、函数、操作符），这些依赖对象决定 CASCADE/RESTRICT 行为。
    cascade_may_drop_tables: CASCADE 删除表列依赖的类型时可能连带删除整张表。
    only_owner_can_drop: 只有类型的 Owner 可以删除它。
    restrict_default: RESTRICT 是默认行为，拒绝删除有任何依赖的类型。
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
    - multi_type_drop
    - type_category
    - type_name_shape
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
    statement_template: "DROP TYPE [ IF EXISTS ] {type_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT count(*) FROM pg_type WHERE typname = '{type_name}'"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      cascade_restrict:
        none: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
