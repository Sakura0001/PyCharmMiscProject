# 技能：DROP PROCEDURE

## 官方语法范围

来源：https://www.postgresql.org/docs/16/sql-dropprocedure.html

### Synopsis

```sql
DROP PROCEDURE [ IF EXISTS ] name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] [, ...]
    [ CASCADE | RESTRICT ]
```

## 语句作用

官方说明：DROP PROCEDURE — remove a procedure

该 reference 关注过程删除语句的语法分支、IF EXISTS 子句、CASCADE/RESTRICT 行为、参数类型签名标识与权限边界。

DROP PROCEDURE 不直接涉及列数据类型选择，但参数类型签名（argtype）用于唯一标识目标过程，必须与 CREATE PROCEDURE 的 argtype 覆盖协调。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（单一过程删除、多过程删除）
- object_state：目标过程对象存在性（exists、not_exists、different_signature_exists）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句（present、absent）
- cascade_restrict_clause：CASCADE | RESTRICT 子句（CASCADE、RESTRICT、absent）
- argtype_specification：参数类型签名指定（with_full_signature、without_signature_single、without_signature_multiple）
- multiple_objects：多对象删除（single_procedure、multiple_procedures）

### T3：对象名与输入形态因子
- procedure_name_shape：过程名形态（simple、quoted、reserved_word、schema_qualified）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、procedure_owner、non_owner_no_privilege）
- dependent_objects：依赖对象状态（no_dependencies、has_dependents_restrict_blocks、has_dependents_cascade_removes）
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists）

### T5：异常与边界因子
- target_procedure_not_exists：目标过程不存在（without_IF_EXISTS_error、with_IF_EXISTS_noop）
- target_procedure_different_type：对象类型不匹配（同名但非过程）
- permission_insufficient：权限不足
- cascade_destroys_dependents：CASCADE 级联删除依赖对象
- identifier_length_exceeded：标识符长度超限

### T6：验证与清理因子
- verification_mode：验证方式（pg_proc_catalog_query、information_schema_routines）
- cleanup_mode：清理方式（DROP_PROCEDURE_cascade、DROP_PROCEDURE_if_exists_cascade、no_cleanup_needed）

## 覆盖策略

- 必须覆盖所有 DROP PROCEDURE 语法分支。
- 不需要覆盖所有基表列类型；参数类型签名仅用于标识目标过程。
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
- 每个样本必须包含明确的前置对象准备、目标 DROP PROCEDURE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 procedure_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限、schema 的分支。
- T4 因子中 privilege_level 挂靠到所有分支，确保权限路径被覆盖。
- T4 因子中 dependent_objects 挂靠到 CASCADE/RESTRICT 分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - IF EXISTS / CASCADE / RESTRICT 核心路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字代表性覆盖
  - 多过程删除代表性覆盖
  - schema、owner 等依赖对象代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - identifier 边界条件
  - 参数类型签名变体

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: procedure
  skill_name: drop_procedure
  official_source: https://www.postgresql.org/docs/16/sql-dropprocedure.html
  statement:
    key: drop_procedure
    name: DROP PROCEDURE
    aliases:
    - DROP PROCEDURE
    - drop procedure
    - drop_procedure
    purpose: remove a procedure
  syntax_templates:
  - |
    DROP PROCEDURE [ IF EXISTS ] name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] [, ...]
        [ CASCADE | RESTRICT ]
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
    - argtype_specification
    - multiple_objects
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - procedure_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - dependent_objects
    - schema_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - target_procedure_not_exists
    - target_procedure_different_type
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
        label: 单一过程删除
      - key: branch_2
        label: 多过程删除 (name [, ...])
    object_state:
      label: 目标过程对象存在性
      importance: important
      values:
      - key: exists
        label: 过程存在
      - key: not_exists
        label: 过程不存在
      - key: different_signature_exists
        label: 同名不同签名过程存在
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
    argtype_specification:
      label: 参数类型签名指定
      importance: important
      values:
      - key: with_full_signature
        label: 包含完整参数类型签名
      - key: without_signature_single
        label: 无参数签名（仅适用于唯一过程名）
      - key: without_signature_multiple
        label: 无参数签名但存在多个同名过程（歧义/失败）
    multiple_objects:
      label: 多对象删除
      importance: important
      values:
      - key: single_procedure
        label: 删除单一过程
      - key: multiple_procedures
        label: 删除多个过程
    procedure_name_shape:
      label: 过程名形态
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
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: procedure_owner
        label: 过程 Owner
      - key: non_owner_no_privilege
        label: 非Owner且无权限
    dependent_objects:
      label: 依赖对象状态
      importance: non_important
      values:
      - key: no_dependencies
        label: 无依赖对象
      - key: has_dependents_restrict_blocks
        label: 存在依赖对象且使用RESTRICT → 失败
      - key: has_dependents_cascade_removes
        label: 存在依赖对象且使用CASCADE → 成功级联
    schema_dependency:
      label: Schema 依赖
      importance: non_important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在
    target_procedure_not_exists:
      label: 目标过程不存在
      importance: non_important
      values:
      - key: without_IF_EXISTS_error
        label: 无IF EXISTS → 错误
      - key: with_IF_EXISTS_noop
        label: 有IF EXISTS → notice（no-op）
    target_procedure_different_type:
      label: 对象类型不匹配
      importance: non_important
      values:
      - key: same_name_is_function
        label: 同名对象是函数而非过程
    permission_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: not_owner
        label: 非Owner无法删除
    cascade_destroys_dependents:
      label: CASCADE级联删除
      importance: non_important
      values:
      - key: cascade_removes_trigger
        label: CASCADE 删除依赖触发器
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
      - key: pg_proc_catalog_query
        label: pg_proc 系统目录查询（确认不存在）
      - key: information_schema_routines
        label: information_schema.routines 查询
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_PROCEDURE_cascade
        label: DROP PROCEDURE ... CASCADE
      - key: DROP_PROCEDURE_if_exists_cascade
        label: DROP PROCEDURE IF EXISTS ... CASCADE
      - key: no_cleanup_needed
        label: 无需额外清理（DROP 已完成）
  defaults:
    expected_status: success
    object_state: exists
    if_exists_clause: absent
    cascade_restrict_clause: absent
    multiple_objects: single_procedure
    argtype_specification: with_full_signature
  coverage_policy:
    main_combination_axes:
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict_clause
    - argtype_specification
    - multiple_objects
    - procedure_name_shape
    - privilege_level
    - dependent_objects
    - schema_dependency
    - target_procedure_not_exists
    - target_procedure_different_type
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
    statement_template: "DROP PROCEDURE [ IF EXISTS ] name ( argtypes ) [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT count(*) FROM pg_proc WHERE proname = '{procedure_name}' AND prokind = 'p'"
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