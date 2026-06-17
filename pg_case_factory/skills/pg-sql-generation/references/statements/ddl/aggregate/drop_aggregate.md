# 技能：DROP AGGREGATE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropaggregate.html

```sql
DROP AGGREGATE [ IF EXISTS ] name ( aggregate_signature ) [, ...] [ CASCADE | RESTRICT ]

where aggregate_signature is:

* |
[ argmode ] [ argname ] argtype [ , ... ] |
[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]
```

**重要行为说明**：
- aggregate_signature 用于标识目标聚合函数：`*` 表示零参数聚合，ORDER BY 分隔 direct/aggregated 参数。
- argname 不参与 PostgreSQL 聚合函数身份判断（仅 argtype 决定身份）。
- 可以在一条语句中删除多个聚合函数（逗号分隔）。
- RESTRICT 是默认行为；有依赖对象（视图等使用该聚合）时拒绝删除。
- CASCADE 自动删除依赖对象。
- 执行用户必须是聚合函数的 Owner。
- DROP AGGREGATE 不涉及表/列/索引类型组合。

## 语句作用

官方说明：DROP AGGREGATE — remove an aggregate function

该 reference 关注聚合函数删除语句的语法分支、签名形态、IF EXISTS 行为、CASCADE/RESTRICT 依赖处理与权限边界，不负责覆盖表/列/索引类型组合。

DROP AGGREGATE **不涉及列类型组合**，具体表现为：
- aggregate_signature 中的 argtype 是聚合函数身份标识，不需要按列类型展开
- 签名匹配是核心关注点

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支
- object_state：目标 Aggregate 对象存在性（不存在、已存在、has_dependencies）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句（absent、present）
- cascade_restrict：CASCADE/RESTRICT 选择（RESTRICT_default、CASCADE、RESTRICT_explicit）
- aggregate_signature：聚合签名形态（star_zero_arg、single_argtype、multi_argtype、ordered_set_signature）
- multiple_aggregates：多聚合函数删除（single、multiple_comma_separated）

### T3：对象名与输入形态因子
- aggregate_name_shape：聚合函数名称形态（plain_identifier、quoted_identifier、schema_qualified）
- signature_argtype_shape：签名参数类型形态（plain_type、schema_qualified_type）

### T4：依赖对象与环境因子
- privilege_level：权限级别（aggregate_owner、non_owner）
- dependency_state：依赖对象状态（no_dependencies、has_dependent_view、has_dependent_function）

### T5：异常与边界因子
- nonexistent_aggregate：聚合函数不存在（无 IF EXISTS → error）
- signature_mismatch：签名参数类型不匹配 → error
- dependent_objects_exist：有依赖对象且 RESTRICT → error
- insufficient_privilege：非 Owner 删除聚合函数 → error

### T6：验证与清理因子
- verification_mode：验证方式（pg_aggregate_catalog_query、pg_aggregate_removed_assertion）
- cleanup_mode：清理方式（DROP_AGGREGATE_CASCADE、DROP_DEPENDENT_OBJECTS_FIRST）

## 覆盖策略

- 必须覆盖 DROP AGGREGATE 的唯一语法分支。
- 必须覆盖签名形态：`*`、单参数、多参数、有序集。
- 必须覆盖 IF EXISTS / CASCADE / RESTRICT 的组合行为。
- 不需要覆盖所有基表列类型；签名中的 argtype 是身份标识。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合：当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP AGGREGATE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 签名形态全覆盖（`*`、单参数、多参数、有序集）
  - 目标对象存在 / 不存在 / 有依赖全覆盖
  - IF EXISTS / CASCADE / RESTRICT 行为全覆盖
  - 成功 / 失败路径全覆盖
- 次优先保证：
  - 依赖对象类型代表性覆盖
  - 多聚合函数删除代表性覆盖
  - 标识符形态代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: aggregate
  skill_name: drop_aggregate
  official_source: https://www.postgresql.org/docs/16/sql-dropaggregate.html
  statement:
    key: drop_aggregate
    name: DROP AGGREGATE
    aliases:
    - DROP AGGREGATE
    - drop aggregate
    - drop_aggregate
    purpose: remove an aggregate function
  syntax_templates:
  - "DROP AGGREGATE [ IF EXISTS ] name ( aggregate_signature ) [, ...] [ CASCADE | RESTRICT ]"
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
    - aggregate_signature
    - multiple_aggregates
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - aggregate_name_shape
    - signature_argtype_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - dependency_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_aggregate
    - signature_mismatch
    - dependent_objects_exist
    - insufficient_privilege
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
      label: 目标Aggregate对象存在性
      importance: important
      values:
      - key: not_exists
        label: 聚合函数不存在
      - key: already_exists
        label: 聚合函数已存在且无依赖
      - key: exists_with_dependencies
        label: 聚合函数已存在且有依赖对象
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
      label: CASCADE/RESTRICT选择
      importance: important
      values:
      - key: RESTRICT_default
        label: 默认RESTRICT (省略子句)
      - key: RESTRICT_explicit
        label: 显式RESTRICT
      - key: CASCADE
        label: CASCADE (自动删除依赖对象)
    aggregate_signature:
      label: 聚合签名形态
      importance: important
      values:
      - key: star_zero_arg
        label: "* (零参数聚合签名)"
      - key: single_argtype
        label: 单参数签名 (如 integer)
      - key: multi_argtype
        label: 多参数签名 (如 integer, text)
      - key: ordered_set_signature
        label: 有序集签名 (direct_args ORDER BY aggregated_args)
    multiple_aggregates:
      label: 多聚合函数删除
      importance: non_important
      values:
      - key: single
        label: 删除单个聚合函数
      - key: multiple_comma_separated
        label: 逗号分隔删除多个聚合函数
    aggregate_name_shape:
      label: 聚合函数名称形态
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符
      - key: schema_qualified
        label: Schema限定标识符
    signature_argtype_shape:
      label: 签名参数类型形态
      importance: non_important
      values:
      - key: plain_type
        label: 普通类型名 (如 integer)
      - key: schema_qualified_type
        label: Schema限定类型名 (如 myschema.mytype)
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: aggregate_owner
        label: 聚合函数Owner
      - key: non_owner
        label: 非 Owner → error
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - key: no_dependencies
        label: 无依赖对象
      - key: has_dependent_view
        label: 有依赖视图
      - key: has_dependent_function
        label: 有依赖函数调用该聚合
    nonexistent_aggregate:
      label: 聚合函数不存在
      importance: non_important
      values:
      - key: without_if_exists
        label: 不使用IF EXISTS且聚合不存在 → error
      - key: with_if_exists
        label: 使用IF EXISTS且聚合不存在 → notice (no-op)
    signature_mismatch:
      label: 签名不匹配
      importance: non_important
      values:
      - key: wrong_arg_count
        label: 签名参数个数错误 → error
      - key: wrong_arg_type
        label: 签名参数类型错误 → error
    dependent_objects_exist:
      label: 有依赖对象且RESTRICT
      importance: non_important
      values:
      - key: restrict_with_dependencies
        label: RESTRICT且有依赖对象 → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_owner_drop
        label: 非 Owner 删除聚合函数 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_aggregate_catalog_query
        label: pg_aggregate 系统目录查询确认删除
      - key: pg_aggregate_removed_assertion
        label: 确认聚合函数不再存在于系统目录
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_AGGREGATE_CASCADE
        label: DROP AGGREGATE name (signature) CASCADE
      - key: DROP_DEPENDENT_OBJECTS_FIRST
        label: 先删除依赖对象再删除聚合函数
  notes:
    signature_identity: aggregate_signature 中的 argtype 决定聚合函数身份，argname 不参与。
    multiple_in_one_statement: 可在一条语句中删除多个聚合函数（逗号分隔）。
    restrict_default: RESTRICT 是默认行为，有依赖对象时拒绝删除。
    cascade_drops_dependencies: CASCADE 自动删除依赖视图等对象。
    owner_required: 执行用户必须是聚合函数的 Owner。
    no_table_column_index_types: DROP AGGREGATE 不涉及表/列/索引类型组合。
  defaults:
    expected_status: success
    object_state: already_exists
    cascade_restrict: RESTRICT_default
    aggregate_signature: single_argtype
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - aggregate_signature
    - multiple_aggregates
    - aggregate_name_shape
    - signature_argtype_shape
    - privilege_level
    - dependency_state
    - nonexistent_aggregate
    - signature_mismatch
    - dependent_objects_exist
    - insufficient_privilege
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP AGGREGATE {if_exists} {aggregate_name} ( {signature} ) {cascade_restrict}"
    verification_query_template: "SELECT count(*) FROM pg_aggregate WHERE aggfnoid = '{aggregate_name}'::regproc"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      cascade_restrict:
        RESTRICT_default: ""
        RESTRICT_explicit: "RESTRICT"
        CASCADE: "CASCADE"
```
