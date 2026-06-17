# 技能：ALTER VIEW

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterview.html

```sql
ALTER VIEW [ IF EXISTS ] name ALTER [ COLUMN ] column_name SET DEFAULT expression
ALTER VIEW [ IF EXISTS ] name ALTER [ COLUMN ] column_name DROP DEFAULT
ALTER VIEW [ IF EXISTS ] name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER VIEW [ IF EXISTS ] name RENAME [ COLUMN ] column_name TO new_column_name
ALTER VIEW [ IF EXISTS ] name RENAME TO new_name
ALTER VIEW [ IF EXISTS ] name SET SCHEMA new_schema
ALTER VIEW [ IF EXISTS ] name SET ( view_option_name [= view_option_value] [, ... ] )
ALTER VIEW [ IF EXISTS ] name RESET ( view_option_name [, ... ] )
```

**重要行为说明**：
- ALTER VIEW 不改变视图的定义查询（修改查询应使用 CREATE OR REPLACE VIEW）。
- SET/DROP DEFAULT 设置或移除视图列的默认值，仅在 INSERT/UPDATE 通过视图操作时生效，优先级高于底层关系默认值。
- OWNER TO 需要当前用户能够 SET ROLE 到新 owner，且新 owner 在视图 schema 上有 CREATE 权限；超级用户可变更任何视图的 owner。
- SET SCHEMA 需要当前用户在新 schema 上有 CREATE 权限。
- SET/RESET 支持三个选项：`check_option`（local/cascaded）、`security_barrier`（boolean）、`security_invoker`（boolean）。
- ALTER VIEW 是 PostgreSQL 扩展，不属于 SQL 标准。

## 语句作用

官方说明：ALTER VIEW — change the definition of a view

该 reference 关注视图修改语句的语法分支、选项操作、所有权变更与权限边界，不负责长期保留测试视图或权限状态。

**特别声明**：ALTER VIEW 不涉及列类型操作（SET/RESET 选项、RENAME、OWNER、SET SCHEMA 不改变视图列类型），不需要覆盖基表列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支
- object_state：目标视图对象状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句

### T3：对象名与输入形态因子
- view_name_shape：视图名形态
- column_name_shape：列名形态
- new_name_shape：新名称形态
- new_schema_shape：新 schema 名形态
- owner_target_shape：owner 目标形态
- view_option_shape：视图选项形态

### T4：依赖对象与环境因子
- privilege_level：权限级别
- dependency_state：依赖对象状态

### T5：异常与边界因子
- error_boundary：错误边界类型

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 必须覆盖所有 ALTER VIEW 语法分支（8 个 synopsis 形式）。
- ALTER VIEW 不涉及列类型，不需要覆盖所有基表和列类型组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标视图，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标对象存在时的成功修改路径、目标对象不存在时的失败路径，以及 IF EXISTS 分支的代表性 no-op 路径。
- SET DEFAULT / DROP DEFAULT / OWNER TO / RENAME COLUMN / RENAME TO / SET SCHEMA / SET / RESET 各分支需要保持独立归因。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER VIEW 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- ALTER VIEW 不涉及列类型组合，无需覆盖不同列类型的交叉组合。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限、schema 或角色依赖的分支。
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
  - IF EXISTS 代表性覆盖
  - COLUMN 关键字可选性覆盖
  - schema 限定、owner、依赖对象代表性覆盖
  - view_option 各选项值代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: view
  skill_name: alter_view
  official_source: https://www.postgresql.org/docs/16/sql-alterview.html
  statement:
    key: alter_view
    name: ALTER VIEW
    aliases:
    - alter_view
    - ALTER VIEW
    - alterview
    - alter view
    purpose: change the definition of a view
  syntax_templates:
  - "ALTER VIEW [ IF EXISTS ] name ALTER [ COLUMN ] column_name SET DEFAULT expression\n\nALTER VIEW [ IF EXISTS ] name ALTER [ COLUMN ] column_name DROP DEFAULT\n\nALTER VIEW [ IF EXISTS ] name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }\n\nALTER VIEW [ IF EXISTS ] name RENAME [ COLUMN ] column_name TO new_column_name\n\nALTER VIEW [ IF EXISTS ] name RENAME TO new_name\n\nALTER VIEW [ IF EXISTS ] name SET SCHEMA new_schema\n\nALTER VIEW [ IF EXISTS ] name SET ( view_option_name [= view_option_value] [, ... ] )\n\nALTER VIEW [ IF EXISTS ] name RESET ( view_option_name [, ... ] )"
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
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - view_name_shape
    - column_name_shape
    - new_name_shape
    - new_schema_shape
    - owner_target_shape
    - view_option_shape
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
      - key: branch_set_default
        label: ALTER VIEW name ALTER COLUMN column_name SET DEFAULT expression
      - key: branch_drop_default
        label: ALTER VIEW name ALTER COLUMN column_name DROP DEFAULT
      - key: branch_owner_to
        label: ALTER VIEW name OWNER TO new_owner
      - key: branch_rename_column
        label: ALTER VIEW name RENAME COLUMN column_name TO new_column_name
      - key: branch_rename_view
        label: ALTER VIEW name RENAME TO new_name
      - key: branch_set_schema
        label: ALTER VIEW name SET SCHEMA new_schema
      - key: branch_set_option
        label: ALTER VIEW name SET (view_option = value)
      - key: branch_reset_option
        label: ALTER VIEW name RESET (view_option)
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
    column_name_shape:
      label: 列名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通列名
      - key: quoted
        label: 双引号列名
      - key: with_column_keyword
        label: 包含 COLUMN 关键字
      - key: without_column_keyword
        label: 不包含 COLUMN 关键字
    new_name_shape:
      label: 新名称形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通新名称
      - key: quoted
        label: 双引号新名称
      - key: reserved_word
        label: 保留字新名称
      - key: same_as_existing
        label: 与现有对象同名
    new_schema_shape:
      label: 新 schema 名形态
      importance: non_important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在
      - key: pg_catalog_reserved
        label: pg_catalog（系统保留Schema）
    owner_target_shape:
      label: owner 目标形态
      importance: non_important
      values:
      - key: role_name
        label: 指定角色名
      - key: current_role
        label: CURRENT_ROLE
      - key: current_user
        label: CURRENT_USER
      - key: session_user
        label: SESSION_USER
      - key: non_existent_role
        label: 不存在的角色名
    view_option_shape:
      label: 视图选项形态
      importance: non_important
      values:
      - key: check_option_local
        label: check_option = local
      - key: check_option_cascaded
        label: check_option = cascaded
      - key: security_barrier_true
        label: security_barrier = true
      - key: security_barrier_false
        label: security_barrier = false
      - key: security_invoker_true
        label: security_invoker = true
      - key: security_invoker_false
        label: security_invoker = false
      - key: multiple_options
        label: 多个选项组合
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: owner
        label: 视图 Owner
      - key: superuser
        label: 超级用户
      - key: non_owner_with_privilege
        label: 非Owner但有权限
      - key: non_owner_no_privilege
        label: 非Owner且无权限
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - key: base_table_exists
        label: 基表存在
      - key: base_table_not_exists
        label: 基表不存在（视图仍可ALTER部分属性）
      - key: other_view_depends
        label: 其他视图依赖本视图
    error_boundary:
      label: 错误边界类型
      importance: non_important
      values:
      - key: none
        label: 无错误
      - key: view_not_exists_without_if_exists
        label: 视图不存在且无IF EXISTS
      - key: insufficient_privilege
        label: 权限不足
      - key: non_existent_role
        label: 指定不存在的角色
      - key: non_existent_schema
        label: 指定不存在的Schema
      - key: wrong_object_type
        label: 目标不是视图（对象类型不匹配）
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_query
        label: pg_class 系统目录查询
      - key: pg_views_query
        label: pg_views 系统视图查询
      - key: information_schema_views
        label: information_schema.views 查询
      - key: select_from_view
        label: 从视图SELECT验证
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_view_if_exists
        label: DROP VIEW IF EXISTS view_name
      - key: drop_view_cascade
        label: DROP VIEW view_name CASCADE
      - key: revert_alter
        label: 反向ALTER恢复
  notes:
    no_column_types: ALTER VIEW 不涉及列类型操作（SET/RESET 选项、RENAME、OWNER、SET SCHEMA 不改变视图列类型）。
    view_options: view_option_name 可选值包括 check_option、security_barrier、security_invoker。
    alter_table_compat: ALTER TABLE 可以用于视图（历史兼容），但仅允许等价于 ALTER VIEW 的操作。
  defaults:
    expected_status: success
    object_state: exists
    if_exists_clause: absent
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - view_name_shape
    - column_name_shape
    - new_name_shape
    - new_schema_shape
    - owner_target_shape
    - view_option_shape
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
    statement_template: "ALTER VIEW [ IF EXISTS ] {view_name} ..."
    verification_query_template: "SELECT 1 FROM pg_class WHERE relname = '{view_name}' AND relkind = 'v'"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
```
