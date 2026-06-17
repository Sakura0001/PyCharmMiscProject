# 技能：DROP CAST

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropcast.html

```sql
DROP CAST [ IF EXISTS ] (source_type AS target_type) [ CASCADE | RESTRICT ]
```

**重要行为说明**：
- DROP CAST 通过 source_type → target_type 方向标识目标 cast 对象。
- CASCADE 和 RESTRICT **实际上没有任何效果**，因为 cast 没有依赖对象。
- 要删除 cast，必须拥有源类型或目标类型（与创建 cast 相同的权限要求）。
- 不需要超级用户权限（除非需要删除 binary-coercible cast 时需要对应类型的所有权）。
- source_type 和 target_type 是 cast 对象的身份关键组成部分。

## 语句作用

官方说明：DROP CAST — remove a cast

该 reference 关注类型转换删除语句的语法分支、source_type/target_type 标识、IF EXISTS 行为与权限边界，不负责覆盖表/列/索引类型组合。

DROP CAST **不涉及列类型组合**，具体表现为：
- source_type 和 target_type 是 cast 对象身份标识，不需要按列类型展开
- CASCADE/RESTRICT 对 cast 无实际效果

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支
- object_state：目标 Cast 对象存在性（不存在、已存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句（absent、present）
- cascade_restrict：CASCADE/RESTRICT 选择（RESTRICT_default、CASCADE、RESTRICT_explicit）— 对 cast 无实际效果
- source_type：源类型数据类型（cast 身份标识）
- target_type：目标类型数据类型（cast 身份标识）

### T3：对象名与输入形态因子
- source_type_shape：源类型名形态（plain_type、schema_qualified_type）
- target_type_shape：目标类型名形态（plain_type、schema_qualified_type）

### T4：依赖对象与环境因子
- privilege_level：权限级别（type_owner_source、type_owner_target、non_owner）
- type_ownership：类型所有权（owns_source、owns_target、owns_neither）

### T5：异常与边界因子
- nonexistent_cast：Cast 不存在（无 IF EXISTS → error）
- insufficient_privilege：不拥有源类型或目标类型 → error
- reverse_direction_cast：仅删除指定方向 cast（反方向不受影响）

### T6：验证与清理因子
- verification_mode：验证方式（pg_cast_catalog_query、pg_cast_removed_assertion）
- cleanup_mode：清理方式（DROP_CAST_IF_EXISTS)

## 覆盖策略

- 必须覆盖 DROP CAST 的唯一语法分支。
- 必须覆盖 source_type 和 target_type 的代表性类型组合标识。
- IF EXISTS / CASCADE / RESTRICT 行为必须覆盖（注意 CASCADE/RESTRICT 对 cast 无实际效果）。
- 不需要覆盖所有基表列类型；source_type/target_type 是 cast 身份标识而非列类型组合。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合：当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP CAST 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- CASCADE/RESTRICT 行为虽然对 cast 无实际效果，仍需在样本中覆盖以验证语法接受性。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在全覆盖
  - IF EXISTS 行为全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - source_type / target_type 代表性类型组合覆盖
  - CASCADE / RESTRICT 语法接受性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: cast
  skill_name: drop_cast
  official_source: https://www.postgresql.org/docs/16/sql-dropcast.html
  statement:
    key: drop_cast
    name: DROP CAST
    aliases:
    - DROP CAST
    - drop cast
    - drop_cast
    purpose: remove a cast
  syntax_templates:
  - "DROP CAST [ IF EXISTS ] (source_type AS target_type) [ CASCADE | RESTRICT ]"
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
    - source_type
    - target_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - source_type_shape
    - target_type_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - type_ownership
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_cast
    - insufficient_privilege
    - reverse_direction_cast
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
      - key: branch_1
        label: 官方 synopsis 分支 1
    object_state:
      label: 目标Cast对象存在性
      importance: important
      values:
      - key: not_exists
        label: Cast不存在
      - key: already_exists
        label: Cast已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS子句
      importance: important
      values:
      - key: absent
        label: 不使用IF EXISTS
      - key: present
        label: 使用IF EXISTS (不存在时发出notice而非error)
    cascade_restrict:
      label: CASCADE/RESTRICT选择 (对cast无实际效果)
      importance: non_important
      values:
      - key: RESTRICT_default
        label: 默认RESTRICT (省略子句)
      - key: RESTRICT_explicit
        label: 显式RESTRICT (语法接受但无实际效果)
      - key: CASCADE
        label: CASCADE (语法接受但无实际效果)
    source_type:
      label: 源类型 (Cast身份标识)
      importance: important
      values:
      - key: integer
        label: integer
      - key: bigint
        label: bigint
      - key: text
        label: text
      - key: numeric
        label: numeric
      - key: boolean
        label: boolean
      - key: date
        label: date
      - key: custom_type
        label: 自定义类型 (用户定义)
    target_type:
      label: 目标类型 (Cast身份标识)
      importance: important
      values:
      - key: integer
        label: integer
      - key: bigint
        label: bigint
      - key: text
        label: text
      - key: numeric
        label: numeric
      - key: float8
        label: float8 (double precision)
      - key: timestamp
        label: timestamp
      - key: custom_type
        label: 自定义类型 (用户定义)
    source_type_shape:
      label: 源类型名形态
      importance: non_important
      values:
      - key: plain_type
        label: 普通类型名 (如 integer)
      - key: schema_qualified_type
        label: Schema限定类型名
    target_type_shape:
      label: 目标类型名形态
      importance: non_important
      values:
      - key: plain_type
        label: 普通类型名 (如 bigint)
      - key: schema_qualified_type
        label: Schema限定类型名
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: type_owner_source
        label: 拥有源类型
      - key: type_owner_target
        label: 拥有目标类型
      - key: non_owner
        label: 不拥有源或目标类型 → error
    type_ownership:
      label: 类型所有权
      importance: non_important
      values:
      - key: owns_source
        label: 拥有源类型
      - key: owns_target
        label: 拥有目标类型
      - key: owns_neither
        label: 不拥有任何类型 → error
    nonexistent_cast:
      label: Cast不存在
      importance: non_important
      values:
      - key: without_if_exists
        label: 不使用IF EXISTS且Cast不存在 → error
      - key: with_if_exists
        label: 使用IF EXISTS且Cast不存在 → notice (no-op)
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: owns_no_type
        label: 不拥有源类型或目标类型 → error
    reverse_direction_cast:
      label: 反方向Cast不受影响
      importance: non_important
      values:
      - key: reverse_still_exists
        label: 删除source→target后，target→source仍存在 (如已创建)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_cast_catalog_query
        label: pg_cast 系统目录查询确认删除
      - key: pg_cast_removed_assertion
        label: 确认Cast不再存在于系统目录
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_CAST_IF_EXISTS
        label: DROP CAST IF EXISTS (source_type AS target_type)
  notes:
    cascade_restrict_no_effect: CASCADE/RESTRICT 对 cast 无实际效果，因为 cast 没有依赖对象。
    requires_type_ownership: 要删除 cast，必须拥有源类型或目标类型。
    no_superuser_required: 删除 cast 不需要超级用户权限（仅需类型所有权）。
    source_target_identity: source_type 和 target_type 是 cast 对象身份标识。
    reverse_direction_independent: 删除一个方向的 cast 不影响反方向的 cast。
  defaults:
    expected_status: success
    object_state: already_exists
    if_exists_clause: absent
    source_type: integer
    target_type: bigint
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - source_type
    - target_type
    - source_type_shape
    - target_type_shape
    - privilege_level
    - type_ownership
    - nonexistent_cast
    - insufficient_privilege
    - reverse_direction_cast
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP CAST {if_exists} ({source_type} AS {target_type}) {cascade_restrict}"
    verification_query_template: "SELECT count(*) FROM pg_cast WHERE castsource = '{source_type}'::regtype AND casttarget = '{target_type}'::regtype"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      cascade_restrict:
        RESTRICT_default: ""
        RESTRICT_explicit: "RESTRICT"
        CASCADE: "CASCADE"
```
