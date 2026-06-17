# 技能：DROP EXTENSION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropextension.html

```sql
DROP EXTENSION [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- 必须拥有扩展才能使用 DROP EXTENSION。
- 删除扩展时，其**成员对象**和**显式依赖的 routine**（通过 ALTER ROUTINE ... DEPENDS ON EXTENSION 注册）也会被删除。
- RESTRICT（默认）：如果除扩展自身、其成员对象和显式依赖 routine 外还有其他对象依赖该扩展，则拒绝删除。
- CASCADE：自动删除依赖该扩展的所有对象。
- 可以在一次命令中指定多个扩展名（逗号分隔）。
- DROP EXTENSION 是 PostgreSQL 扩展，不属于 SQL 标准。

## 语句作用

官方说明：DROP EXTENSION — remove an extension

该 reference 关注扩展删除操作的权限边界（owner 权限）、IF EXISTS 行为、CASCADE/RESTRICT 依赖追踪路径和成员对象自动删除行为。

DROP EXTENSION **不涉及列类型定义**——它删除扩展及其成员对象，不直接操作表/列结构。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP EXTENSION / DROP EXTENSION IF EXISTS）
- object_state：目标 extension 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- cascade_restrict：CASCADE / RESTRICT 选择（RESTRICT 默认 / CASCADE）
- multi_extension：是否同时删除多个扩展（单个 / 多个）
- dependent_objects：是否存在依赖对象（无依赖 / 有成员对象依赖 / 有外部对象依赖）

### T3：对象名与输入形态因子
- extension_name_shape：extension 名称形态
- multi_name_separator：多扩展名分隔形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（extension_owner / non_owner / superuser）
- member_object_state：成员对象存在性（扩展有成员对象 / 扩展无成员对象）
- external_dependency_state：外部对象是否依赖该扩展（无依赖 / 有依赖）

### T5：异常与边界因子
- nonexistent_extension：目标 extension 不存在且无 IF EXISTS
- dependent_with_restrict：有外部依赖对象且使用 RESTRICT
- insufficient_privilege：非 owner 尝试 DROP EXTENSION
- if_exists_notice：IF EXISTS 遇不存在对象的 notice 路径

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP EXTENSION 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表和所有列类型，因为 DROP EXTENSION 不涉及表/列/索引组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 extension 存在时的成功删除路径，以及目标 extension 不存在时的失败路径。
- 支持 `IF EXISTS` 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 `CASCADE | RESTRICT` 时，必须覆盖存在外部依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP EXTENSION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- DROP EXTENSION 要求执行者是 extension 的 owner，必须在生成样本中显式标注。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、成员对象存在性或外部依赖对象的分支。
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
  - 多扩展名删除代表性覆盖
  - 成员对象自动删除行为覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: extension
  skill_name: drop_extension
  official_source: https://www.postgresql.org/docs/16/sql-dropextension.html
  statement:
    key: drop_extension
    name: DROP EXTENSION
    aliases:
    - DROP EXTENSION
    - drop extension
    - drop_extension
    purpose: remove an extension
  syntax_templates:
  - "DROP EXTENSION [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - multi_extension
    - dependent_objects
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - extension_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - member_object_state
    - external_dependency_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_extension
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
      - key: branch_drop_extension
        label: DROP EXTENSION name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_extension_if_exists
        label: DROP EXTENSION IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标 extension 对象状态
      importance: important
      values:
      - key: exists
        label: 扩展已存在
      - key: not_exists
        label: 扩展不存在
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
    multi_extension:
      label: 是否同时删除多个扩展
      importance: non_important
      values:
      - key: single_extension
        label: 单个扩展名
      - key: multiple_extensions
        label: 多个扩展名 (逗号分隔)
    dependent_objects:
      label: 是否存在依赖对象
      importance: non_important
      values:
      - key: no_dependencies
        label: 无依赖对象
      - key: member_objects_only
        label: 仅成员对象依赖
      - key: external_dependencies
        label: 有外部对象依赖
    extension_name_shape:
      label: extension 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_name
        label: 不存在的扩展名
      - key: duplicate_name
        label: 已存在的扩展名
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: extension_owner
        label: 扩展 owner
      - key: non_owner
        label: 非 owner 用户 → error
      - key: superuser
        label: 超级用户
    member_object_state:
      label: 成员对象存在性
      importance: non_important
      values:
      - key: has_members
        label: 扩展包含成员对象
      - key: no_members
        label: 扩展无成员对象
    external_dependency_state:
      label: 外部对象是否依赖该扩展
      importance: non_important
      values:
      - key: no_external_deps
        label: 无外部对象依赖
      - key: has_external_deps
        label: 有外部对象依赖
    nonexistent_extension:
      label: 目标 extension 不存在且无 IF EXISTS
      importance: non_important
      values:
      - key: extension_exists
        label: 扩展存在
      - key: extension_missing_no_if_exists
        label: 扩展不存在且无 IF EXISTS → error
    dependent_with_restrict:
      label: 有外部依赖对象且使用 RESTRICT
      importance: non_important
      values:
      - key: no_deps_restrict
        label: 无依赖 + RESTRICT → success
      - key: has_deps_restrict
        label: 有依赖 + RESTRICT → error
      - key: has_deps_cascade
        label: 有依赖 + CASCADE → success
    insufficient_privilege:
      label: 非 owner 尝试 DROP EXTENSION
      importance: non_important
      values:
      - key: owner_execution
        label: extension owner 执行 → success
      - key: non_owner_execution
        label: 非 owner 执行 → error
      - key: superuser_execution
        label: superuser 执行 → success
    if_exists_notice:
      label: IF EXISTS 遇不存在对象的 notice 路径
      importance: non_important
      values:
      - key: no_notice
        label: 不使用 IF EXISTS 或扩展存在
      - key: notice_no_op
        label: IF EXISTS 遇不存在 → notice (no-op)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_extension_catalog_query
        label: pg_extension 系统目录查询
      - key: error_assertion
        label: 错误断言
      - key: notice_assertion
        label: notice 断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_dependent_objects
        label: 删除依赖对象
      - key: recreate_extension
        label: 重新创建扩展 (用于 RESTRICT 失败路径还原)
      - key: role_cleanup
        label: 角色/权限清理
  notes:
    owner_privilege: 必须拥有扩展才能使用 DROP EXTENSION。
    member_objects_auto_drop: 删除扩展时，成员对象和显式依赖的 routine 也会被自动删除。
    restrict_default: RESTRICT 是默认行为；存在外部依赖对象时 RESTRICT 拒绝删除。
    cascade_deps: CASCADE 自动删除依赖该扩展的所有对象。
    multi_name_support: 可以在一次命令中指定多个扩展名（逗号分隔）。
    extension_no_column_types: DROP EXTENSION 不涉及列类型定义，不需要挂靠基表列类型。
  defaults:
    expected_status: success
    privilege_level: extension_owner
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - multi_extension
    - dependent_objects
    - extension_name_shape
    - privilege_level
    - member_object_state
    - external_dependency_state
    - nonexistent_extension
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
    statement_template: "DROP EXTENSION [ IF EXISTS ] {extension_name} [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT extname FROM pg_extension WHERE extname = '{extension_name}'"
    factor_value_bindings: {}
```
