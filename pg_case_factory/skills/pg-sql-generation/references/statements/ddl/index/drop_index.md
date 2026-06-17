# 技能：DROP INDEX

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropindex.html

```sql
DROP INDEX [ CONCURRENTLY ] [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

## 语句作用

用于描述 PostgreSQL DROP INDEX 生成规则。官方说明：remove an index。

这个 skill 承担如下职责：

- 定义测试因子与覆盖策略
- 定义 DROP INDEX 的 SQL 生成范围
- 标识语法分支、前置依赖、权限边界、成功路径与失败路径

## 语法范围

```sql
DROP INDEX [ CONCURRENTLY ] [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 中的顶层语法形式
- object_state：目标索引对象状态（已存在、不存在、被依赖）
- expected_status：预期结果（success / failure / no_op）

### T2：重要行为因子
- concurrently：CONCURRENTLY 是否指定
  - 注意：CONCURRENTLY 不能指定多个索引名
  - 注意：CONCURRENTLY 不能与 CASCADE 组合
  - 注意：CONCURRENTLY 不能在事务块内使用
  - 注意：CONCURRENTLY 不能用于分区表
- if_exists：IF EXISTS 是否指定
- cascade_restrict：CASCADE | RESTRICT 选择
  - RESTRICT 为默认行为
  - CASCADE 自动删除依赖对象
- multi_index：是否同时删除多个索引（逗号分隔列表）
- permission：权限与 owner 差异

### T3：对象名与输入形态因子
- name_shape：索引名的标识符形态
  - 合法普通标识符
  - schema 限定标识符
  - 双引号标识符
  - 保留字标识符
  - 已存在对象名
  - 不存在对象名

### T4：依赖对象与环境因子
- dependency_type：依赖对象类型
  - 索引被 UNIQUE/PRIMARY KEY 约束依赖
  - 索引被 FK 约束间接依赖
  - 索引无依赖对象
- index_method：目标索引所属的索引方法（btree/hash/gist/spgist/gin/brin），影响 CASCADE 传播范围和 CONCURRENTLY 限制

### T5：异常与边界因子
- invalid_combination：语义非法的组合
  - CONCURRENTLY + CASCADE（不允许）
  - CONCURRENTLY + 多索引名（不允许）
  - CONCURRENTLY + 分区表索引（不允许）
  - CONCURRENTLY + 事务块内（不允许）
  - 被约束依赖 + RESTRICT（失败）
- syntax_error：语法非法的组合
- permission_insufficient：权限不足失败路径

### T6：验证与清理因子
- verification_mode：验证方式（pg_catalog 查询确认索引已删除）
- cleanup_mode：清理方式（CASCADE 自动清理、显式清理依赖对象）

## 覆盖策略
- 需要覆盖所有 DROP INDEX 语法分支。
- 需要覆盖所有基表。
- 需要覆盖每张基表中所有的列类型。
- T1 和 T2 作为主覆盖因子。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- CONCURRENTLY 必须覆盖成功路径和各限制条件下的失败路径（事务块内、分区表、与 CASCADE 组合）。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP INDEX 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限和索引方法的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 被依赖全覆盖
  - 成功 / 失败 / no-op 路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - CONCURRENTLY 各限制条件代表性覆盖
  - CASCADE / RESTRICT 依赖场景代表性覆盖
  - schema 限定名、owner、角色等依赖对象代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 输出要求

- 生成结果应为可执行的 PostgreSQL DROP INDEX 测试样本集合。
- 输出样本应具备明确因子归因能力。
- 每个样本应标注所属语法分支、预期成功/失败、前置依赖和清理策略。
- 当采用裁剪策略时，应优先保留语句分支、成功/失败路径和对象状态覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: index
  skill_name: drop_index
  official_source: https://www.postgresql.org/docs/16/sql-dropindex.html
  statement:
    key: drop_index
    name: DROP INDEX
    aliases:
    - drop index
    - 删除索引
    - 索引删除
    purpose: 删除已有索引，覆盖 CONCURRENTLY、IF EXISTS、CASCADE/RESTRICT 和多索引删除等因子。
  syntax_templates:
  - "DROP INDEX [ CONCURRENTLY ] [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - concurrently
    - if_exists
    - cascade_restrict
    - multi_index
    - permission
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_type
    - index_method
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - syntax_error
    - permission_insufficient
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification_mode
    - cleanup_mode
  factors:
    statement_branch:
      label: 语句分支
      importance: important
      values:
      - key: drop_single
        label: 删除单个索引
      - key: drop_multiple
        label: 删除多个索引
      - key: drop_concurrently
        label: CONCURRENTLY 删除
      - key: drop_cascade
        label: CASCADE 删除
    object_state:
      label: 目标索引对象状态
      importance: important
      values:
      - exists
      - not_exists
      - depended_by_constraint
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
      - no_op
    concurrently:
      label: CONCURRENTLY
      importance: non_important
      values:
      - "false"
      - "true"
    if_exists:
      label: IF EXISTS
      importance: non_important
      values:
      - "false"
      - "true"
    cascade_restrict:
      label: CASCADE | RESTRICT
      importance: non_important
      values:
      - restrict
      - cascade
    multi_index:
      label: 多索引删除
      importance: non_important
      values:
      - single
      - multiple
    permission:
      label: 权限与 owner
      importance: non_important
      values:
      - owner
      - non_owner
      - superuser
    name_shape:
      label: 索引名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
      - reserved_word
      - existing_object
      - missing_object
    dependency_type:
      label: 依赖对象类型
      importance: non_important
      values:
      - no_dependency
      - unique_pk_constraint
      - fk_indirect_dependency
    index_method:
      label: 目标索引方法
      importance: non_important
      values:
      - btree
      - hash
      - gist
      - spgist
      - gin
      - brin
    invalid_combination:
      label: 语义非法组合
      importance: non_important
      values:
      - concurrently_with_cascade
      - concurrently_with_multiple_indexes
      - concurrently_on_partitioned
      - concurrently_in_transaction
      - restrict_with_dependency
      - none
    syntax_error:
      label: 语法非法组合
      importance: non_important
      values:
      - none
      - invalid_syntax
    permission_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - none
      - non_owner_drop
      - no_schema_privilege
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_absence_check
      - constraint_integrity_check
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - explicit_drop
      - cascade_auto_cleanup
      - rollback
  defaults:
    object_state: exists
    expected_status: success
    concurrently: "false"
    if_exists: "false"
    cascade_restrict: restrict
    multi_index: single
    permission: owner
    name_shape: plain_identifier
    dependency_type: no_dependency
    index_method: btree
    invalid_combination: none
    syntax_error: none
    permission_insufficient: none
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - concurrently
    - if_exists
    - cascade_restrict
    - multi_index
    - permission
    - name_shape
    - dependency_type
    - index_method
    - invalid_combination
    - syntax_error
    - permission_insufficient
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP INDEX {concurrently_clause}{if_exists_clause}{index_names} {cascade_restrict_clause};"
    verification_query_template: "SELECT COUNT(*) AS remaining FROM pg_class WHERE relname = '{index_name}' AND relkind = 'i';"
    factor_value_bindings:
      concurrently_clause:
        factor: concurrently
        values:
          "false": ""
          "true": "CONCURRENTLY "
      if_exists_clause:
        factor: if_exists
        values:
          "false": ""
          "true": "IF EXISTS "
      cascade_restrict_clause:
        factor: cascade_restrict
        values:
          restrict: "RESTRICT"
          cascade: "CASCADE"
```
