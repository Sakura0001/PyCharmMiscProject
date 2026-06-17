# 技能：DROP VIEW

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropview.html

```sql
DROP VIEW [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

**重要行为说明**：
- DROP VIEW 删除视图定义，不删除底层基表。
- 若其他对象依赖该视图（如其他视图引用），RESTRICT（默认）将拒绝删除；CASCADE 会连同依赖视图一并删除。
- CASCADE 删除依赖对象时会递归追踪整个依赖链。
- 只有视图拥有者、schema 拥有者和超级用户可以删除视图。
- SQL 标准仅允许每条命令删除一个视图；PostgreSQL 允许逗号分隔的多个视图。
- IF EXISTS 是 PostgreSQL 扩展，不属于 SQL 标准。

## 语句作用

官方说明：DROP VIEW — remove a view

该 reference 关注视图删除语句的对象状态、依赖链、权限边界和成功/失败路径。

**特别声明**：DROP VIEW 不涉及列类型操作（它删除视图定义而非操作列），但涉及依赖链（其他视图引用目标视图时，CASCADE/RESTRICT 决定行为）。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- object_state：目标视图对象状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句
- cascade_restrict：CASCADE / RESTRICT 行为

### T3：对象名与输入形态因子
- view_name_shape：视图名形态
- multi_view_drop：单视图/多视图删除

### T4：依赖对象与环境因子
- privilege_level：权限级别
- dependency_state：依赖对象状态

### T5：异常与边界因子
- error_boundary：错误边界类型

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖视图存在/不存在的删除路径。
- IF EXISTS、CASCADE、RESTRICT 按语句支持情况覆盖。
- 依赖对象（其他视图引用）必须覆盖 RESTRICT 失败与 CASCADE 成功路径。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP VIEW 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP VIEW 不涉及列类型组合，无需覆盖不同列类型的交叉组合。
- 依赖链（其他视图引用目标视图）必须作为独立成功/失败边界覆盖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限或 schema 限定的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - IF EXISTS、CASCADE、RESTRICT 代表性覆盖
  - schema 限定、owner、依赖对象代表性覆盖
  - 依赖链（其他视图引用）代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: view
  skill_name: drop_view
  official_source: https://www.postgresql.org/docs/16/sql-dropview.html
  statement:
    key: drop_view
    name: DROP VIEW
    aliases:
    - drop_view
    - DROP VIEW
    - dropview
    - drop view
    purpose: remove a view
  syntax_templates:
  - "DROP VIEW [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - view_name_shape
    - multi_view_drop
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
      - key: branch_drop_view
        label: DROP VIEW name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_view_if_exists
        label: DROP VIEW IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标视图对象状态
      importance: important
      values:
      - key: exists
        label: 视图已存在
      - key: not_exists
        label: 视图不存在
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
        label: 不包含 IF EXISTS
      - key: present
        label: 包含 IF EXISTS
    cascade_restrict:
      label: CASCADE / RESTRICT 行为
      importance: important
      values:
      - key: none
        label: 默认（隐式 RESTRICT）
      - key: cascade
        label: CASCADE
      - key: restrict
        label: RESTRICT
    view_name_shape:
      label: 视图名形态
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
      - key: non_existent
        label: 不存在的视图名
    multi_view_drop:
      label: 单视图/多视图删除
      importance: non_important
      values:
      - key: single_view
        label: 单个视图
      - key: multi_view
        label: 多个视图（逗号分隔）
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: owner
        label: 视图 Owner
      - key: superuser
        label: 超级用户
      - key: schema_owner
        label: Schema Owner
      - key: non_owner
        label: 非Owner且无权限
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - key: no_dependents
        label: 无依赖对象
      - key: has_dependent_views
        label: 其他视图引用目标视图
      - key: has_dependent_policies
        label: 策略引用目标视图
    error_boundary:
      label: 错误边界类型
      importance: non_important
      values:
      - key: none
        label: 无错误
      - key: non_existent_without_if_exists
        label: 视图不存在且无IF EXISTS
      - key: dependent_objects_without_cascade
        label: 有依赖对象且未指定CASCADE
      - key: insufficient_privilege
        label: 权限不足
      - key: wrong_object_type
        label: 目标不是视图（对象类型不匹配）
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_query
        label: pg_class 系统目录查询
      - key: error_assertion
        label: 错误断言
      - key: notice_assertion
        label: 通知断言（IF EXISTS场景）
      - key: effect_query
        label: 依赖对象验证
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: cascade_cleanup
        label: 级联清理
      - key: manual_cleanup
        label: 手动清理
      - key: rollback
        label: 回滚清理
  notes:
    column_type_combination: DROP VIEW 不涉及列类型操作，它删除视图定义而非操作列。
    dependency_chain: DROP VIEW 涉及依赖链（其他视图引用目标视图），CASCADE 递归删除所有依赖视图。
    base_table_preserved: DROP VIEW 不删除底层基表。
  defaults:
    expected_status: success
    object_state: exists
    if_exists_clause: absent
    cascade_restrict: none
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - view_name_shape
    - multi_view_drop
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
    statement_template: "DROP VIEW [ IF EXISTS ] {view_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT 1 FROM pg_class WHERE relname = '{view_name}' AND relkind = 'v'"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      cascade_restrict:
        none: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
