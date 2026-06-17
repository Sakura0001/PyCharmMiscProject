# 技能：CREATE VIEW

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createview.html

```sql
CREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] [ RECURSIVE ] VIEW name [ ( column_name [, ...] ) ]
    [ WITH ( view_option_name [= view_option_value] [, ... ] ) ]
    AS query
    [ WITH [ CASCADED | LOCAL ] CHECK OPTION ]
```

**重要行为说明**：
- `OR REPLACE` 替换现有视图的定义查询、WITH 参数和 CHECK OPTION，但不改变所有权和权限。新查询必须生成相同列（相同名称、顺序和类型），但允许在末尾追加新列。
- `TEMP / TEMPORARY` 创建临时视图，会话结束时自动删除；如果查询引用了临时表，视图自动成为临时视图。
- `RECURSIVE` 创建递归视图，必须指定列名列表。
- `WITH ( ... )` 支持三个选项：`check_option`（local/cascaded）、`security_barrier`（boolean）、`security_invoker`（boolean），均为 PostgreSQL 扩展。
- `CHECK OPTION` 仅适用于自动可更新视图，`CASCADED` 检查本视图及所有底层视图条件，`LOCAL` 仅检查本视图条件。RECURSIVE 视图不支持 CHECK OPTION。
- 视图列的数据类型由底层查询决定。

## 语句作用

官方说明：CREATE VIEW — define a new view

该 reference 关注视图定义语句的语法分支、查询形态、选项设置、安全属性与依赖环境，不负责包装所有样本到统一外层事务。

**特别声明**：CREATE VIEW 间接涉及列类型（列类型由查询推导），需要覆盖代表性基表和列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支
- object_state：目标视图对象状态
- expected_status：预期结果

### T2：重要行为因子
- or_replace_clause：OR REPLACE 子句
- temporary_clause：TEMP / TEMPORARY 子句
- recursive_clause：RECURSIVE 子句
- with_options_clause：WITH (view_option_name = value) 子句
- check_option_clause：CHECK OPTION 子句
- column_name_list：显式列名列表

### T3：对象名与输入形态因子
- view_name_shape：视图名形态
- column_name_shape：列名形态
- query_shape：查询形态

### T4：依赖对象与环境因子
- privilege_level：权限级别
- dependency_state：依赖对象状态
- base_table_coverage：基表列类型覆盖

### T5：异常与边界因子
- error_boundary：错误边界类型

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 必须覆盖所有 CREATE VIEW 语法分支（默认、OR REPLACE、TEMP/TEMPORARY、RECURSIVE）。
- 必须覆盖代表性基表和列类型组合（视图列类型由查询推导，需要覆盖不同基表列类型在视图中的呈现）。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖视图成功创建、重名冲突（不含/含 OR REPLACE）、非法定义与依赖对象缺失路径。
- OR REPLACE 必须覆盖正常创建、替换现有视图、列类型/列数不匹配的失败边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE VIEW 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- RECURSIVE 视图必须指定列名列表，不指定列名列表应作为失败路径覆盖。
- CHECK OPTION 与 RECURSIVE 视图组合为非法，应作为失败路径覆盖。
- 临时视图引用永久表、永久视图引用临时表的行为应作为代表性边界覆盖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子中 base_table_coverage 挂靠到默认分支的代表性成功样本，确保基表列类型组合被覆盖。
- T4 因子中 privilege_level 和 dependency_state 仅挂靠到需要权限、schema 或基表依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
  - 代表性基表和列类型间接覆盖
- 次优先保证：
  - OR REPLACE、TEMP/TEMPORARY、RECURSIVE、WITH 选项、CHECK OPTION 代表性覆盖
  - schema、owner、基表依赖代表性覆盖
  - security_barrier、security_invoker 代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: view
  skill_name: create_view
  official_source: https://www.postgresql.org/docs/16/sql-createview.html
  statement:
    key: create_view
    name: CREATE VIEW
    aliases:
    - create_view
    - CREATE VIEW
    - createview
    - create view
    purpose: define a new view
  syntax_templates:
  - "CREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] [ RECURSIVE ] VIEW name [ ( column_name [, ...] ) ]\n    [ WITH ( view_option_name [= view_option_value] [, ... ] ) ]\n    AS query\n    [ WITH [ CASCADED | LOCAL ] CHECK OPTION ]"
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
    - or_replace_clause
    - temporary_clause
    - recursive_clause
    - with_options_clause
    - check_option_clause
    - column_name_list
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - view_name_shape
    - column_name_shape
    - query_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - dependency_state
    - base_table_coverage
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
      - key: branch_create_view
        label: CREATE VIEW name AS query
      - key: branch_create_or_replace_view
        label: CREATE OR REPLACE VIEW name AS query
      - key: branch_create_temp_view
        label: CREATE TEMP/TEMPORARY VIEW name AS query
      - key: branch_create_recursive_view
        label: CREATE RECURSIVE VIEW name (columns) AS query
    object_state:
      label: 目标视图对象状态
      importance: important
      values:
      - key: not_exists
        label: 视图不存在
      - key: already_exists
        label: 视图已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    or_replace_clause:
      label: OR REPLACE 子句
      importance: important
      values:
      - key: absent
        label: 不包含 OR REPLACE
      - key: present
        label: 包含 OR REPLACE
    temporary_clause:
      label: TEMP/TEMPORARY 子句
      importance: important
      values:
      - key: permanent
        label: 永久视图（无 TEMP/TEMPORARY）
      - key: temp
        label: TEMP 视图
      - key: temporary
        label: TEMPORARY 视图
    recursive_clause:
      label: RECURSIVE 子句
      importance: important
      values:
      - key: absent
        label: 不包含 RECURSIVE
      - key: present
        label: 包含 RECURSIVE
    with_options_clause:
      label: WITH (view_options) 子句
      importance: important
      values:
      - key: absent
        label: 不包含 WITH 选项
      - key: security_barrier
        label: WITH (security_barrier = true/false)
      - key: security_invoker
        label: WITH (security_invoker = true/false)
      - key: check_option
        label: WITH (check_option = local/cascaded)
      - key: multiple_options
        label: WITH 多个选项组合
    check_option_clause:
      label: CHECK OPTION 子句
      importance: important
      values:
      - key: absent
        label: 不包含 CHECK OPTION
      - key: cascaded
        label: WITH CASCADED CHECK OPTION
      - key: local
        label: WITH LOCAL CHECK OPTION
    column_name_list:
      label: 显式列名列表
      importance: non_important
      values:
      - key: absent
        label: 不指定列名（由查询推导）
      - key: present
        label: 显式指定列名列表
      - key: required_for_recursive
        label: RECURSIVE 视图必须指定列名
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
      - key: duplicate
        label: 已存在视图名
    column_name_shape:
      label: 列名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通列名
      - key: quoted
        label: 双引号列名
      - key: reserved_word
        label: 保留字列名
    query_shape:
      label: 查询形态
      importance: non_important
      values:
      - key: select_simple
        label: 简单 SELECT FROM table
      - key: select_with_where
        label: SELECT FROM table WHERE condition
      - key: select_with_join
        label: SELECT ... JOIN ...
      - key: select_with_aggregate
        label: SELECT with aggregate/window function
      - key: values_clause
        label: VALUES (...) 形式
      - key: select_with_expression
        label: SELECT with computed expressions
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: owner
        label: 视图 Owner
      - key: superuser
        label: 超级用户
      - key: non_owner_with_create
        label: 非Owner但有CREATE权限
      - key: non_owner_no_privilege
        label: 非Owner且无权限
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - key: base_table_exists
        label: 基表存在
      - key: base_table_not_exists
        label: 基表不存在
      - key: referenced_view_exists
        label: 被引用视图存在
      - key: referenced_view_not_exists
        label: 被引用视图不存在
    base_table_coverage:
      label: 基表列类型覆盖
      importance: non_important
      values:
      - key: representative_int_types
        label: 整数类型基表（smallint, integer, bigint）
      - key: representative_string_types
        label: 字符类型基表（varchar, text, char）
      - key: representative_datetime_types
        label: 日期时间类型基表（timestamp, date, interval）
      - key: representative_numeric_types
        label: 数值类型基表（numeric, real, double precision）
      - key: representative_json_types
        label: JSON类型基表（json, jsonb）
      - key: representative_boolean_types
        label: 布尔类型基表（boolean）
    error_boundary:
      label: 错误边界类型
      importance: non_important
      values:
      - key: none
        label: 无错误
      - key: duplicate_without_or_replace
        label: 视图已存在且无OR REPLACE
      - key: or_replace_column_mismatch
        label: OR REPLACE列类型/列数不匹配
      - key: recursive_without_column_list
        label: RECURSIVE未指定列名列表
      - key: check_option_on_recursive
        label: CHECK OPTION与RECURSIVE组合
      - key: base_table_not_exists
        label: 查询引用不存在的表
      - key: insufficient_privilege
        label: 权限不足
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_query
        label: pg_class 系统目录查询
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
      - key: drop_base_table_cascade
        label: DROP TABLE base_table CASCADE
  notes:
    column_type_combination: CREATE VIEW 的列类型由底层查询决定，列类型覆盖通过基表和查询表达式间接实现。
    check_option_behavior: CHECK OPTION 仅适用于自动可更新视图，RECURSIVE 视图不支持 CHECK OPTION。
    security_barrier_invoker: security_barrier 和 security_invoker 是 PostgreSQL 扩展选项。
    temporary_view_auto: 临时视图在会话结束时自动删除；若查询引用了临时表，视图自动成为临时视图。
    or_replace_preserves_ownership: OR REPLACE 不改变视图所有权和权限，仅替换定义查询、WITH 参数和 CHECK OPTION。
  defaults:
    expected_status: success
    object_state: not_exists
    or_replace_clause: absent
    temporary_clause: permanent
    recursive_clause: absent
    with_options_clause: absent
    check_option_clause: absent
    column_name_list: absent
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - or_replace_clause
    - temporary_clause
    - recursive_clause
    - with_options_clause
    - check_option_clause
    - column_name_list
    - view_name_shape
    - column_name_shape
    - query_shape
    - privilege_level
    - dependency_state
    - base_table_coverage
    - error_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] [ RECURSIVE ] VIEW {view_name} [ ( {column_names} ) ] [ WITH ( {view_options} ) ] AS {query} [ WITH [ CASCADED | LOCAL ] CHECK OPTION ]"
    verification_query_template: "SELECT 1 FROM pg_class WHERE relname = '{view_name}' AND relkind = 'v'"
    factor_value_bindings:
      or_replace_clause:
        absent: ""
        present: "OR REPLACE"
      temporary_clause:
        permanent: ""
        temp: "TEMP"
        temporary: "TEMPORARY"
      recursive_clause:
        absent: ""
        present: "RECURSIVE"
      check_option_clause:
        absent: ""
        cascaded: "WITH CASCADED CHECK OPTION"
        local: "WITH LOCAL CHECK OPTION"
```
