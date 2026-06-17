# 技能：DROP SCHEMA

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropschema.html

```sql
DROP SCHEMA [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

**重要行为说明**：
- DROP SCHEMA 只能由 Schema Owner 或超级用户执行。
- Owner 可以删除 Schema（连同所有包含对象），即使不拥有 Schema 内的部分对象。
- RESTRICT（默认）拒绝删除包含任何对象的 Schema。
- CASCADE 自动删除 Schema 内的所有对象，以及依赖于这些对象的其他对象；CASCADE 可能跨越 Schema 边界删除其他 Schema 中的对象。
- SQL 标准仅允许每条命令删除一个 Schema；PostgreSQL 允许逗号分隔的多个 Schema。
- IF EXISTS 是 PostgreSQL 扩展，不属于 SQL 标准。

## 语句作用

官方说明：DROP SCHEMA — remove a schema

该 reference 关注 Schema 删除语句的对象状态、依赖链、权限边界和成功/失败路径。

**特别声明**：DROP SCHEMA 不涉及列类型组合（它删除整个 Schema 而非操作列），但涉及依赖链（Schema 内包含的表、视图、函数等依赖对象）。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- object_state：目标 Schema 对象状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句
- cascade_restrict：CASCADE / RESTRICT 行为
- multi_schema_drop：单 Schema / 多 Schema 删除

### T3：对象名与输入形态因子
- schema_name_shape：Schema 名形态

### T4：依赖对象与环境因子
- privilege_level：权限级别
- contained_objects_state：包含对象状态
- cross_schema_dependency：跨 Schema 依赖

### T5：异常与边界因子
- error_boundary：错误边界类型

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 Schema 存在/不存在/空/包含对象的删除路径。
- IF EXISTS、CASCADE、RESTRICT 按语句支持情况覆盖。
- 包含对象（表、视图、函数）必须覆盖 RESTRICT 失败与 CASCADE 成功路径。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖包含对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP SCHEMA 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP SCHEMA 不涉及列类型组合，无需覆盖不同列类型的交叉组合。
- 依赖链（表、视图、函数）必须作为独立成功/失败边界覆盖。
- CASCADE 可能跨越 Schema 边界，必须作为代表性边界覆盖。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限或 Schema 限定的分支。
- T4 因子中 contained_objects_state 挂靠到 CASCADE/RESTRICT 分支。
- T4 因子中 cross_schema_dependency 挂靠到 CASCADE 分支的代表性成功样本。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 空 / 包含对象全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - IF EXISTS、CASCADE、RESTRICT 代表性覆盖
  - Schema 限定、Owner、包含对象代表性覆盖
  - 依赖链（表、视图、函数）代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: schema
  skill_name: drop_schema
  official_source: https://www.postgresql.org/docs/16/sql-dropschema.html
  statement:
    key: drop_schema
    name: DROP SCHEMA
    aliases:
    - DROP SCHEMA
    - drop schema
    - drop_schema
    - dropschema
    purpose: remove a schema
  syntax_templates:
  - "DROP SCHEMA [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - multi_schema_drop
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - schema_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - contained_objects_state
    - cross_schema_dependency
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
      - key: branch_drop_schema
        label: DROP SCHEMA name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_schema_if_exists
        label: DROP SCHEMA IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标Schema对象状态
      importance: important
      values:
      - key: exists_empty
        label: 空Schema已存在
      - key: exists_with_objects
        label: 包含对象的Schema已存在
      - key: not_exists
        label: Schema不存在
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
    multi_schema_drop:
      label: 单/多Schema删除
      importance: non_important
      values:
      - key: single_schema
        label: 单个Schema
      - key: multi_schema
        label: 多个Schema (逗号分隔)
    schema_name_shape:
      label: Schema名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: schema_qualified
        label: 非Schema限定 (Schema本身不能被Schema限定)
      - key: reserved_word
        label: 保留字标识符
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: owner
        label: Schema Owner
      - key: superuser
        label: 超级用户
      - key: non_owner
        label: 非 Owner
    contained_objects_state:
      label: 包含对象状态
      importance: non_important
      values:
      - key: empty_schema
        label: 空 Schema (无包含对象)
      - key: has_tables
        label: 包含表
      - key: has_views
        label: 包含视图
      - key: has_functions
        label: 包含函数
      - key: has_multiple_object_types
        label: 包含多种对象类型
    cross_schema_dependency:
      label: 跨Schema依赖
      importance: non_important
      values:
      - key: no_cross_dependency
        label: 无跨Schema依赖
      - key: has_cross_schema_fk
        label: 其他Schema中有外键引用本Schema表
      - key: has_cross_schema_view
        label: 其他Schema中有视图依赖本Schema表
    error_boundary:
      label: 错误边界类型
      importance: non_important
      values:
      - key: none
        label: 无错误
      - key: non_existent_without_if_exists
        label: 不存在且无 IF EXISTS → error
      - key: contains_objects_without_cascade
        label: 包含对象且无 CASCADE → error
      - key: insufficient_privilege
        label: 权限不足 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_namespace_query
        label: pg_namespace 系统目录查询
      - key: information_schema_schemata
        label: information_schema.schemata 查询
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
    column_type_combination: DROP SCHEMA 不涉及列类型组合，它删除整个命名空间而非操作列。
    dependency_chain: DROP SCHEMA 涉及依赖链（包含的表、视图、函数等），这些依赖对象决定 CASCADE/RESTRICT 行为。
    cascade_cross_boundary: CASCADE 可能跨越 Schema 边界删除其他 Schema 中的依赖对象。
    owner_can_drop_all: Schema Owner 可以删除整个 Schema（连同不属于自己的包含对象）。
    restrict_default: RESTRICT 是默认行为，拒绝删除包含任何对象的 Schema。
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
    - multi_schema_drop
    - schema_name_shape
    - privilege_level
    - contained_objects_state
    - cross_schema_dependency
    - error_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP SCHEMA [ IF EXISTS ] {schema_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT count(*) FROM pg_namespace WHERE nspname = '{schema_name}'"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      cascade_restrict:
        none: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
