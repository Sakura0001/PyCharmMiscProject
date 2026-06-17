# 技能：DROP TRIGGER

## 官方语法范围

来源：https://www.postgresql.org/docs/16/sql-droptrigger.html

### Synopsis

```sql
DROP TRIGGER [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]
```

## 语句作用

官方说明：DROP TRIGGER — remove a trigger

该 reference 关注触发器删除语句的语法分支、IF EXISTS 子句、CASCADE/RESTRICT 行为与权限边界。

DROP TRIGGER 不直接涉及列数据类型选择。权限要求是必须拥有触发器所在表的所有权。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（单一语法形式）
- object_state：目标触发器对象存在性（exists、not_exists）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句（present、absent）
- cascade_restrict_clause：CASCADE | RESTRICT 子句（CASCADE、RESTRICT、absent）

### T3：对象名与输入形态因子
- trigger_name_shape：触发器名形态（simple、quoted、reserved_word）
- table_name_shape：表名形态（simple、quoted、schema_qualified）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、table_owner、non_owner_no_privilege）
- dependent_objects：依赖对象状态（no_dependencies、has_dependents_restrict_blocks）
- table_dependency：表依赖（table_exists、table_not_exists）

### T5：异常与边界因子
- target_trigger_not_exists：目标触发器不存在（without_IF_EXISTS_error、with_IF_EXISTS_noop）
- permission_insufficient：权限不足（非表Owner）
- cascade_destroys_dependents：CASCADE 级联删除依赖对象
- identifier_length_exceeded：标识符长度超限

### T6：验证与清理因子
- verification_mode：验证方式（pg_trigger_catalog_query、information_schema_triggers）
- cleanup_mode：清理方式（DROP_TRIGGER_cascade、DROP_TRIGGER_if_exists_cascade、no_cleanup_needed）

## 覆盖策略

- 必须覆盖所有 DROP TRIGGER 语法分支。
- 不需要覆盖所有基表列类型。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（创建表、创建触发器函数、创建触发器）、目标 DROP TRIGGER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 trigger_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 table_name_shape 挂靠到所有分支的样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限的分支。
- T4 因子中 privilege_level 挂靠到所有分支，确保权限路径被覆盖。
- T4 因子中 dependent_objects 挂靠到 CASCADE/RESTRICT 分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - IF EXISTS / CASCADE / RESTRICT 核心路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字代表性覆盖
  - schema、owner 等依赖对象代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - identifier 边界条件
  - 触发器名/表名形态变体

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: trigger
  skill_name: drop_trigger
  official_source: https://www.postgresql.org/docs/16/sql-droptrigger.html
  statement:
    key: drop_trigger
    name: DROP TRIGGER
    aliases:
    - DROP TRIGGER
    - drop trigger
    - drop_trigger
    purpose: remove a trigger
  syntax_templates:
  - |
    DROP TRIGGER [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]
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
    - cascade_restrict_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - trigger_name_shape
    - table_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - dependent_objects
    - table_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - target_trigger_not_exists
    - permission_insufficient
    - cascade_destroys_dependents
    - identifier_length_exceeded
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
        label: 单一触发器删除
    object_state:
      label: 目标触发器对象存在性
      importance: important
      values:
      - key: exists
        label: 触发器存在
      - key: not_exists
        label: 触发器不存在
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
      - key: present
        label: 包含 IF EXISTS
      - key: absent
        label: 不包含 IF EXISTS
    cascade_restrict_clause:
      label: CASCADE | RESTRICT 子句
      importance: important
      values:
      - key: CASCADE
        label: CASCADE (级联删除依赖对象)
      - key: RESTRICT
        label: RESTRICT (拒绝删除若有依赖)
      - key: absent
        label: 无 CASCADE/RESTRICT (默认 RESTRICT)
    trigger_name_shape:
      label: 触发器名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: schema_qualified
        label: Schema 限定标识符
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: table_owner
        label: 表 Owner
      - key: non_owner_no_privilege
        label: 非表Owner且无权限
    dependent_objects:
      label: 依赖对象状态
      importance: non_important
      values:
      - key: no_dependencies
        label: 无依赖对象
      - key: has_dependents_restrict_blocks
        label: 存在依赖对象且使用RESTRICT → 失败
    table_dependency:
      label: 表依赖
      importance: non_important
      values:
      - key: table_exists
        label: 目标表存在
      - key: table_not_exists
        label: 目标表不存在
    target_trigger_not_exists:
      label: 目标触发器不存在
      importance: non_important
      values:
      - key: without_IF_EXISTS_error
        label: 无IF EXISTS → 错误
      - key: with_IF_EXISTS_noop
        label: 有IF EXISTS → notice（no-op）
    permission_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: not_table_owner
        label: 非表Owner无法删除触发器
    cascade_destroys_dependents:
      label: CASCADE级联删除
      importance: non_important
      values:
      - key: cascade_removes_constraint
        label: CASCADE 删除依赖约束
    identifier_length_exceeded:
      label: 标识符长度超限
      importance: non_important
      values:
      - key: over_63_chars
        label: 标识符超过63字符
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_trigger_catalog_query
        label: pg_trigger 系统目录查询（确认不存在）
      - key: information_schema_triggers
        label: information_schema.triggers 查询
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_TRIGGER_cascade
        label: DROP TRIGGER ... ON table_name CASCADE
      - key: DROP_TRIGGER_if_exists_cascade
        label: DROP TRIGGER IF EXISTS ... ON table_name CASCADE
      - key: no_cleanup_needed
        label: 无需额外清理（DROP 已完成）
  defaults:
    expected_status: success
    object_state: exists
    if_exists_clause: absent
    cascade_restrict_clause: absent
  coverage_policy:
    main_combination_axes:
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict_clause
    - trigger_name_shape
    - table_name_shape
    - privilege_level
    - dependent_objects
    - table_dependency
    - target_trigger_not_exists
    - permission_insufficient
    - cascade_destroys_dependents
    - identifier_length_exceeded
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - object_state
    - if_exists_clause
    - cascade_restrict_clause
  rendering:
    statement_template: "DROP TRIGGER [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT count(*) FROM pg_trigger WHERE tgname = '{trigger_name}'"
    factor_value_bindings:
      if_exists_clause:
        present: "IF EXISTS"
        absent: ""
      cascade_restrict_clause:
        CASCADE: "CASCADE"
        RESTRICT: "RESTRICT"
        absent: ""
```
```