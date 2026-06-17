# 技能：DROP FOREIGN TABLE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropforeigntable.html

```sql
DROP FOREIGN TABLE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- 只有外部表的 **owner** 才能删除该外部表。
- IF EXISTS：如果外部表不存在，不报错，仅发 notice。
- CASCADE：自动删除依赖该外部表的对象（如视图），以及依赖这些对象的所有对象。
- RESTRICT（默认）：如果有对象依赖该外部表，则拒绝删除。
- 可以在一次命令中指定多个外部表名称（逗号分隔）。
- DROP FOREIGN TABLE 符合 ISO/IEC 9075-9 (SQL/MED)，但标准仅允许一次命令删除一个外部表，IF EXISTS 是 PostgreSQL 扩展。

## 语句作用

官方说明：DROP FOREIGN TABLE — remove a foreign table

该 reference 关注外部表删除操作的权限边界（owner 权限）、IF EXISTS 行为、CASCADE/RESTRICT 依赖追踪路径和依赖对象（视图等）自动删除行为。

DROP FOREIGN TABLE **不涉及列类型定义**——它删除外部表及其依赖对象，不直接操作列结构。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP FOREIGN TABLE / DROP FOREIGN TABLE IF EXISTS）
- object_state：目标 foreign table 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- cascade_restrict：CASCADE / RESTRICT 选择（RESTRICT 默认 / CASCADE）
- multi_table：是否同时删除多个外部表（单个 / 多个）
- dependent_objects：是否存在依赖对象（无依赖 / 有视图依赖 / 有其他依赖）

### T3：对象名与输入形态因子
- table_name_shape：外部表名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（table_owner / non_owner / superuser）
- dependency_state：是否有对象依赖该外部表（无依赖 / 有视图依赖）

### T5：异常与边界因子
- nonexistent_table：目标外部表不存在且无 IF EXISTS
- dependent_with_restrict：有依赖对象且使用 RESTRICT
- insufficient_privilege：非 owner 尝试 DROP FOREIGN TABLE
- if_exists_notice：IF EXISTS 遇不存在对象的 notice 路径

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP FOREIGN TABLE 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表中所有的列类型，因为 DROP FOREIGN TABLE 不涉及列定义。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标外部表存在时的成功删除路径，以及目标外部表不存在时的失败路径。
- 支持 `IF EXISTS` 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 `CASCADE | RESTRICT` 时，必须覆盖存在依赖对象（视图等）下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（FDW + 服务器 + 外部表）、目标 DROP FOREIGN TABLE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP FOREIGN TABLE 要求执行者是外部表的 owner，必须在生成样本中显式标注。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限或依赖对象驻留的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - CASCADE / RESTRICT 依赖追踪全覆盖
  - 权限核心路径全覆盖（owner / non_owner / superuser）
- 次优先保证：
  - IF EXISTS 子句代表性覆盖
  - 多表删除代表性覆盖
  - 依赖对象自动删除覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: foreign_table
  skill_name: drop_foreign_table
  official_source: https://www.postgresql.org/docs/16/sql-dropforeigntable.html
  statement:
    key: drop_foreign_table
    name: DROP FOREIGN TABLE
    aliases:
    - DROP FOREIGN TABLE
    - drop foreign table
    - drop_foreign_table
    purpose: remove a foreign table
  syntax_templates:
  - "DROP FOREIGN TABLE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - multi_table
    - dependent_objects
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - dependency_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_table
    - dependent_with_restrict
    - insufficient_privilege
    - if_exists_notice
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
      - key: branch_drop_foreign_table
        label: DROP FOREIGN TABLE name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_foreign_table_if_exists
        label: DROP FOREIGN TABLE IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标 foreign table 对象状态
      importance: important
      values:
      - key: exists
        label: 外部表已存在
      - key: not_exists
        label: 外部表不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: important
      values:
      - key: absent
        label: 省略 IF EXISTS
      - key: present
        label: 指定 IF EXISTS
    cascade_restrict:
      label: CASCADE / RESTRICT 选择
      importance: important
      values:
      - key: restrict_default
        label: RESTRICT (默认行为)
      - key: cascade
        label: CASCADE (自动删除依赖对象)
    multi_table:
      label: 是否同时删除多个外部表
      importance: non_important
      values:
      - key: single_table
        label: 单个外部表
      - key: multiple_tables
        label: 多个外部表 (逗号分隔)
    dependent_objects:
      label: 是否存在依赖对象
      importance: non_important
      values:
      - key: no_dependencies
        label: 无依赖对象
      - key: view_dependencies
        label: 有视图依赖
      - key: other_dependencies
        label: 有其他对象依赖
    table_name_shape:
      label: 外部表名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: schema_qualified
        label: Schema 限定标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_name
        label: 不存在的表名
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: table_owner
        label: 表 owner → success
      - key: non_owner
        label: 非 owner → error
      - key: superuser
        label: 超级用户 → success
    dependency_state:
      label: 是否有对象依赖该外部表
      importance: non_important
      values:
      - key: no_dependencies
        label: 无依赖
      - key: has_view_dependency
        label: 有视图依赖
    nonexistent_table:
      label: 目标外部表不存在且无 IF EXISTS
      importance: non_important
      values:
      - key: table_exists
        label: 外部表存在
      - key: table_missing_no_if_exists
        label: 外部表不存在且无 IF EXISTS → error
    dependent_with_restrict:
      label: 有依赖对象且使用 RESTRICT
      importance: non_important
      values:
      - key: no_deps_restrict
        label: 无依赖 + RESTRICT → success
      - key: has_deps_restrict
        label: 有依赖 + RESTRICT → error
      - key: has_deps_cascade
        label: 有依赖 + CASCADE → success
    insufficient_privilege:
      label: 非 owner 尝试 DROP FOREIGN TABLE
      importance: non_important
      values:
      - key: owner_execution
        label: 表 owner 执行 → success
      - key: non_owner_execution
        label: 非 owner 执行 → error
      - key: superuser_execution
        label: superuser 执行 → success
    if_exists_notice:
      label: IF EXISTS 遇不存在对象的 notice 路径
      importance: non_important
      values:
      - key: no_notice
        label: 不使用 IF EXISTS 或表存在
      - key: notice_no_op
        label: IF EXISTS 遇不存在 → notice (no-op)
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
      - key: recreate_foreign_table
        label: 重新创建外部表
      - key: recreate_server
        label: 重新创建外部服务器
      - key: recreate_fdw
        label: 重新创建 FDW
      - key: drop_dependent_views
        label: 删除依赖视图 (CASCADE 路径还原)
  notes:
    owner_privilege: 只有外部表的 owner 才能删除该外部表。
    cascade_drops_views: CASCADE 自动删除依赖该外部表的对象（如视图）。
    restrict_default: RESTRICT 是默认行为；有依赖对象时拒绝删除。
    sql_med_conformance: DROP FOREIGN TABLE 符合 ISO/IEC 9075-9 (SQL/MED)，但 IF EXISTS 是 PostgreSQL 扩展，标准仅允许一次命令删除一个外部表。
    no_column_types: DROP FOREIGN TABLE 不涉及列类型定义，不需要挂靠基表列类型。
  defaults:
    expected_status: success
    privilege_level: table_owner
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - multi_table
    - dependent_objects
    - table_name_shape
    - privilege_level
    - dependency_state
    - nonexistent_table
    - dependent_with_restrict
    - insufficient_privilege
    - if_exists_notice
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP FOREIGN TABLE [ IF EXISTS ] {table_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT relname FROM pg_class WHERE relname = '{table_name}' AND relkind = 'f'"
    factor_value_bindings: {}
```
