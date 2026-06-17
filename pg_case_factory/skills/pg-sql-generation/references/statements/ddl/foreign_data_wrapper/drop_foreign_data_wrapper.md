# 技能：DROP FOREIGN DATA WRAPPER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropforeigndatawrapper.html

```sql
DROP FOREIGN DATA WRAPPER [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- 当前用户必须是 FDW 的 **owner** 才能执行 DROP FOREIGN DATA WRAPPER。
- CASCADE：自动删除依赖该 FDW 的对象（如外部表和外部服务器），以及依赖这些对象的所有对象。
- RESTRICT（默认）：如果任何对象依赖该 FDW，则拒绝删除。
- 可以在一次命令中指定多个 FDW 名称（逗号分隔）。
- DROP FOREIGN DATA WRAPPER 符合 ISO/IEC 9075-9 (SQL/MED)，但 IF EXISTS 子句是 PostgreSQL 扩展。

## 语句作用

官方说明：DROP FOREIGN DATA WRAPPER — remove a foreign-data wrapper

该 reference 关注 FDW 删除操作的权限边界（owner 权限）、IF EXISTS 行为、CASCADE/RESTRICT 依赖追踪路径（外部服务器和外部表依赖）和依赖对象自动删除行为。

DROP FOREIGN DATA WRAPPER **不涉及列类型定义**——它删除 FDW 及其依赖对象，不直接操作表/列结构。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP FOREIGN DATA WRAPPER / DROP FOREIGN DATA WRAPPER IF EXISTS）
- object_state：目标 FDW 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- cascade_restrict：CASCADE / RESTRICT 选择（RESTRICT 默认 / CASCADE）
- multi_fdw：是否同时删除多个 FDW（单个 / 多个）
- dependent_objects：是否存在依赖对象（无依赖 / 有外部服务器依赖 / 有外部表依赖）

### T3：对象名与输入形态因子
- fdw_name_shape：FDW 名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（fdw_owner / non_owner / superuser）
- server_dependency_state：外部服务器是否依赖该 FDW（无依赖 / 有依赖）
- foreign_table_dependency_state：外部表是否依赖该 FDW（无依赖 / 有依赖）

### T5：异常与边界因子
- nonexistent_fdw：目标 FDW 不存在且无 IF EXISTS
- dependent_with_restrict：有依赖对象且使用 RESTRICT
- insufficient_privilege：非 owner 尝试 DROP FDW
- if_exists_notice：IF EXISTS 遇不存在对象的 notice 路径

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP FOREIGN DATA WRAPPER 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表和所有列类型，因为 DROP FDW 不涉及表/列/索引组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 FDW 存在时的成功删除路径，以及目标 FDW 不存在时的失败路径。
- 支持 `IF EXISTS` 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 `CASCADE | RESTRICT` 时，必须覆盖存在依赖对象（外部服务器、外部表）下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP FOREIGN DATA WRAPPER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP FOREIGN DATA WRAPPER 要求执行者是 FDW 的 owner，必须在生成样本中显式标注。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、外部服务器依赖或外部表依赖的分支。
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
  - 多 FDW 删除代表性覆盖
  - 外部服务器/外部表依赖自动删除覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: foreign_data_wrapper
  skill_name: drop_foreign_data_wrapper
  official_source: https://www.postgresql.org/docs/16/sql-dropforeigndatawrapper.html
  statement:
    key: drop_foreign_data_wrapper
    name: DROP FOREIGN DATA WRAPPER
    aliases:
    - DROP FOREIGN DATA WRAPPER
    - drop foreign data wrapper
    - drop_foreign_data_wrapper
    purpose: remove a foreign-data wrapper
  syntax_templates:
  - "DROP FOREIGN DATA WRAPPER [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - multi_fdw
    - dependent_objects
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - fdw_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - server_dependency_state
    - foreign_table_dependency_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_fdw
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
      - key: branch_drop_fdw
        label: DROP FOREIGN DATA WRAPPER name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_fdw_if_exists
        label: DROP FOREIGN DATA WRAPPER IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标 FDW 对象状态
      importance: important
      values:
      - key: exists
        label: FDW 已存在
      - key: not_exists
        label: FDW 不存在
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
    multi_fdw:
      label: 是否同时删除多个 FDW
      importance: non_important
      values:
      - key: single_fdw
        label: 单个 FDW 名称
      - key: multiple_fdws
        label: 多个 FDW 名称 (逗号分隔)
    dependent_objects:
      label: 是否存在依赖对象
      importance: non_important
      values:
      - key: no_dependencies
        label: 无依赖对象
      - key: server_dependencies
        label: 有外部服务器依赖
      - key: foreign_table_dependencies
        label: 有外部表依赖
      - key: both_dependencies
        label: 同时有服务器和外部表依赖
    fdw_name_shape:
      label: FDW 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_name
        label: 不存在的 FDW 名称
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: fdw_owner
        label: FDW owner → success
      - key: non_owner
        label: 非 owner → error
      - key: superuser
        label: 超级用户 → success
    server_dependency_state:
      label: 外部服务器是否依赖该 FDW
      importance: non_important
      values:
      - key: no_server_deps
        label: 无外部服务器依赖
      - key: has_server_deps
        label: 有外部服务器依赖
    foreign_table_dependency_state:
      label: 外部表是否依赖该 FDW
      importance: non_important
      values:
      - key: no_table_deps
        label: 无外部表依赖
      - key: has_table_deps
        label: 有外部表依赖
    nonexistent_fdw:
      label: 目标 FDW 不存在且无 IF EXISTS
      importance: non_important
      values:
      - key: fdw_exists
        label: FDW 存在
      - key: fdw_missing_no_if_exists
        label: FDW 不存在且无 IF EXISTS → error
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
      label: 非 owner 尝试 DROP FDW
      importance: non_important
      values:
      - key: owner_execution
        label: FDW owner 执行 → success
      - key: non_owner_execution
        label: 非 owner 执行 → error
      - key: superuser_execution
        label: superuser 执行 → success
    if_exists_notice:
      label: IF EXISTS 遇不存在对象的 notice 路径
      importance: non_important
      values:
      - key: no_notice
        label: 不使用 IF EXISTS 或 FDW 存在
      - key: notice_no_op
        label: IF EXISTS 遇不存在 → notice (no-op)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_foreign_data_wrapper_catalog
        label: pg_foreign_data_wrapper 系统目录查询
      - key: error_assertion
        label: 错误断言
      - key: notice_assertion
        label: notice 断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: recreate_fdw
        label: 重新创建 FDW (用于 CASCADE 路径还原)
      - key: recreate_server
        label: 重新创建外部服务器
      - key: recreate_foreign_table
        label: 重新创建外部表
  notes:
    owner_privilege: 当前用户必须是 FDW 的 owner 才能执行 DROP FOREIGN DATA WRAPPER。
    cascade_drops_servers_tables: CASCADE 自动删除依赖该 FDW 的外部服务器和外部表。
    restrict_default: RESTRICT 是默认行为；有依赖对象时拒绝删除。
    sql_med_conformance: DROP FOREIGN DATA WRAPPER 符合 ISO/IEC 9075-9 (SQL/MED)，IF EXISTS 是 PostgreSQL 扩展。
    fdw_no_column_types: DROP FOREIGN DATA WRAPPER 不涉及列类型定义，不需要挂靠基表列类型。
  defaults:
    expected_status: success
    privilege_level: fdw_owner
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - multi_fdw
    - dependent_objects
    - fdw_name_shape
    - privilege_level
    - server_dependency_state
    - foreign_table_dependency_state
    - nonexistent_fdw
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
    statement_template: "DROP FOREIGN DATA WRAPPER [ IF EXISTS ] {fdw_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT fdwname FROM pg_foreign_data_wrapper WHERE fdwname = '{fdw_name}'"
    factor_value_bindings: {}
```
