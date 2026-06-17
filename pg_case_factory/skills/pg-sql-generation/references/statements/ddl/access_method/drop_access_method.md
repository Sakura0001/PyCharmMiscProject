# 技能：DROP ACCESS METHOD

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropaccessmethod.html

```sql
DROP ACCESS METHOD [ IF EXISTS ] name [ CASCADE | RESTRICT ]
```

**重要行为说明**：
- 只有超级用户才能删除访问方法。
- `CASCADE` 自动删除依赖对象（操作符类、操作符族、索引等）。
- `RESTRICT` 拒绝删除有依赖对象的访问方法，这是默认行为。
- `IF EXISTS` 在访问方法不存在时不抛出错误，仅发出通知。
- DROP ACCESS METHOD 不涉及表/列/索引类型组合，仅涉及访问方法名称与依赖对象状态。

## 语句作用

官方说明：DROP ACCESS METHOD — remove an access method

该 reference 关注访问方法删除语句的语法分支、IF EXISTS 行为、CASCADE/RESTRICT 依赖处理与超级用户权限边界，不负责覆盖表/列/索引类型组合。

DROP ACCESS METHOD **不涉及表/列/索引类型**，具体表现为：
- 语句仅删除访问方法注册记录及其依赖对象
- CASCADE/RESTRICT 行为与依赖对象类型（操作符类、操作符族、索引等）有关
- 不需要按列类型组合展开

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支
- object_state：目标 Access Method 对象存在性（不存在、已存在、has_dependencies）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句（absent、present）
- cascade_restrict：CASCADE/RESTRICT 选择（RESTRICT_default、CASCADE、RESTRICT_explicit）
- dependency_state：依赖对象状态（no_dependencies、has_dependent_opclass、has_dependent_index）

### T3：对象名与输入形态因子
- am_name_shape：访问方法名称形态（plain_identifier、quoted_identifier、schema_qualified、nonexistent_name）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、non_superuser）

### T5：异常与边界因子
- nonexistent_am：访问方法不存在（无 IF EXISTS → error）
- dependent_objects_exist：有依赖对象且 RESTRICT → error
- insufficient_privilege：非超级用户删除访问方法 → error

### T6：验证与清理因子
- verification_mode：验证方式（pg_am_catalog_query、pg_am_removed_assertion）
- cleanup_mode：清理方式（DROP_ACCESS_METHOD_CASCADE、DROP_DEPENDENT_OBJECTS_FIRST）

## 覆盖策略

- 必须覆盖 DROP ACCESS METHOD 的唯一语法分支。
- 必须覆盖 IF EXISTS / CASCADE / RESTRICT 的组合行为。
- DROP ACCESS METHOD 不涉及表/列/索引类型组合。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合：当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 `IF EXISTS` 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 `CASCADE | RESTRICT` 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP ACCESS METHOD 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要超级用户权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 有依赖全覆盖
  - IF EXISTS / CASCADE / RESTRICT 行为全覆盖
  - 成功 / 失败路径全覆盖
  - 超级用户权限路径全覆盖
- 次优先保证：
  - 依赖对象类型代表性覆盖（操作符类、索引）
  - 标识符形态代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: access_method
  skill_name: drop_access_method
  official_source: https://www.postgresql.org/docs/16/sql-dropaccessmethod.html
  statement:
    key: drop_access_method
    name: DROP ACCESS METHOD
    aliases:
    - DROP ACCESS METHOD
    - drop access method
    - drop_access_method
    purpose: remove an access method
  syntax_templates:
  - "DROP ACCESS METHOD [ IF EXISTS ] name [ CASCADE | RESTRICT ]"
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
    - dependency_state
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - am_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_am
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
      label: 目标Access Method对象存在性
      importance: important
      values:
      - key: not_exists
        label: 访问方法不存在
      - key: already_exists
        label: 访问方法已存在且无依赖
      - key: exists_with_dependencies
        label: 访问方法已存在且有依赖对象
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
    dependency_state:
      label: 依赖对象状态
      importance: important
      values:
      - key: no_dependencies
        label: 无依赖对象
      - key: has_dependent_opclass
        label: 有依赖操作符类
      - key: has_dependent_index
        label: 有依赖索引
    am_name_shape:
      label: 访问方法名称形态
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符
      - key: schema_qualified
        label: Schema限定标识符 (不支持，访问方法无schema)
      - key: nonexistent_name
        label: 不存在的访问方法名
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户 (删除访问方法必需)
      - key: non_superuser
        label: 非超级用户 → error
    nonexistent_am:
      label: 访问方法不存在
      importance: non_important
      values:
      - key: without_if_exists
        label: 不使用IF EXISTS且访问方法不存在 → error
      - key: with_if_exists
        label: 使用IF EXISTS且访问方法不存在 → notice (no-op)
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
      - key: non_superuser_drop
        label: 非超级用户删除访问方法 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_am_catalog_query
        label: pg_am 系统目录查询确认删除
      - key: pg_am_removed_assertion
        label: 确认访问方法不再存在于系统目录
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_ACCESS_METHOD_CASCADE
        label: DROP ACCESS METHOD name CASCADE
      - key: DROP_DEPENDENT_OBJECTS_FIRST
        label: 先删除依赖对象再删除访问方法
  notes:
    requires_superuser: DROP ACCESS METHOD 只有超级用户才能执行。
    no_table_column_index_types: DROP ACCESS METHOD 不涉及表/列/索引类型组合。
    cascade_drops_dependencies: CASCADE 自动删除操作符类、操作符族、索引等依赖对象。
    restrict_default: RESTRICT 是默认行为，有依赖对象时拒绝删除。
    if_exists_noop: IF EXISTS 在访问方法不存在时发出 notice 而非 error。
  defaults:
    expected_status: success
    object_state: already_exists
    cascade_restrict: RESTRICT_default
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - dependency_state
    - am_name_shape
    - privilege_level
    - nonexistent_am
    - dependent_objects_exist
    - insufficient_privilege
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP ACCESS METHOD {if_exists} {am_name} {cascade_restrict}"
    verification_query_template: "SELECT count(*) FROM pg_am WHERE amname = '{am_name}'"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      cascade_restrict:
        RESTRICT_default: ""
        RESTRICT_explicit: "RESTRICT"
        CASCADE: "CASCADE"
```
