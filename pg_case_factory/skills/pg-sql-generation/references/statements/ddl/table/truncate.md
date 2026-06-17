# 技能：TRUNCATE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-truncate.html

```sql
TRUNCATE [ TABLE ] [ ONLY ] name [ * ] [, ... ]
    [ RESTART IDENTITY | CONTINUE IDENTITY ] [ CASCADE | RESTRICT ]
```

## 语句作用

官方说明：TRUNCATE — empty a table or set of tables

该 reference 关注 TRUNCATE 语句的表级清空行为、外键依赖级联、序列重置与权限边界，不涉及列类型组合。

**重要声明**：TRUNCATE 操作在整表行级别执行，不涉及列类型组合。但 TRUNCATE 涉及外键依赖链——被其他表外键引用的表在清空时需要 CASCADE 或同时列出所有引用表。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- object_state：目标表对象状态
- expected_status：预期结果

### T2：重要行为因子
- only_clause：ONLY 子句开关
- identity_option：序列行为选项
- cascade_restrict：级联/限制选项

### T3：对象名与输入形态因子
- table_name_shape：表名形态
- multi_table：多表操作形态

### T4：依赖对象与环境因子
- privilege_level：权限级别
- fk_dependency：外键依赖关系

### T5：异常与边界因子
- non_existent_table：不存在的表
- fk_references_without_cascade：外键引用但未使用 CASCADE
- insufficient_privilege：权限不足
- temporary_table_truncation：临时表清空
- partitioned_table_behavior：分区表行为

### T6：验证与清理因子
- verification：验证方式
- cleanup：清理方式

## 覆盖策略

- 覆盖所有 TRUNCATE 语法分支：基础形式、ONLY、RESTART IDENTITY、CONTINUE IDENTITY、CASCADE、RESTRICT 及其组合。
- 覆盖所有基表作为 TRUNCATE 目标对象，不覆盖每张基表的列类型。
- TRUNCATE 不涉及列类型组合，但必须覆盖外键依赖链的场景。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖该命令的所有顶层语法形式、成功路径、失败路径和对象状态验证。
- 需要为会修改对象元数据或物理状态的路径提供前置对象、执行语句、验证语句和清理语句。
- 对不可事务化、需要 superuser 或受环境约束的分支，必须单独标识生命周期边界。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 TRUNCATE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- TRUNCATE 不涉及列类型组合，此约束必须体现在因子定义与覆盖策略中。
- TRUNCATE 涉及外键依赖链时，必须覆盖 CASCADE 和 RESTRICT 的成功与失败路径。
- TRUNCATE 获取 ACCESS EXCLUSIVE 锁，阻塞所有并发操作，此行为边界必须在异常因子中体现。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象（外键引用）、权限的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 空 / 非空全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
  - 外键依赖链 CASCADE / RESTRICT 覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - schema、owner 等依赖对象代表性覆盖
  - 分区表、临时表行为覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: truncate
  official_source: https://www.postgresql.org/docs/16/sql-truncate.html
  statement:
    key: truncate
    name: TRUNCATE
    aliases:
    - TRUNCATE
    - TRUNCATE TABLE
    purpose: TRUNCATE — empty a table or set of tables
  syntax_templates:
  - "TRUNCATE [ TABLE ] [ ONLY ] name [ * ] [, ... ]\n    [ RESTART IDENTITY | CONTINUE\
      \ IDENTITY ] [ CASCADE | RESTRICT ]"
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
    - only_clause
    - identity_option
    - cascade_restrict
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - multi_table
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - fk_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - non_existent_table
    - fk_references_without_cascade
    - insufficient_privilege
    - temporary_table_truncation
    - partitioned_table_behavior
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification
    - cleanup
  factors:
    statement_branch:
      label: 官方语法分支
      importance: important
      values:
      - key: truncate_table
        label: TRUNCATE TABLE name
      - key: truncate_table_only
        label: TRUNCATE TABLE ONLY name
      - key: truncate_table_restart_identity
        label: TRUNCATE TABLE name RESTART IDENTITY
      - key: truncate_table_continue_identity
        label: TRUNCATE TABLE name CONTINUE IDENTITY
    object_state:
      label: 目标表对象状态
      importance: important
      values:
      - table_exists
      - table_does_not_exist
      - empty_table
      - non_empty_table
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    only_clause:
      label: ONLY 子句开关
      importance: non_important
      values:
      - key: only
        label: ONLY — 仅清空指定表，不包含分区后代
      - key: without_only
        label: 无 ONLY — 清空指定表及其分区后代
    identity_option:
      label: 序列行为选项
      importance: non_important
      values:
      - key: restart_identity
        label: RESTART IDENTITY — 重置序列
      - key: continue_identity
        label: CONTINUE IDENTITY — 保持序列值（默认）
      - key: none
        label: 无序列选项
    cascade_restrict:
      label: 级联/限制选项
      importance: non_important
      values:
      - key: cascade
        label: CASCADE — 级联清空外键引用表
      - key: restrict
        label: RESTRICT — 有外键引用时拒绝清空（默认）
      - key: none
        label: 无级联/限制选项
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - simple
      - quoted
      - schema_qualified
      - non_existent
    multi_table:
      label: 多表操作形态
      importance: non_important
      values:
      - single
      - multiple
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - owner
      - superuser
      - truncate_privilege
      - insufficient_privilege
    fk_dependency:
      label: 外键依赖关系
      importance: non_important
      values:
      - key: no_fk_references
        label: 无外键引用 — 表不被其他表外键引用
      - key: referenced_by_other_tables
        label: 被其他表外键引用 — 需要 CASCADE 或同时清空引用表
    non_existent_table:
      label: 不存在的表
      importance: non_important
      values:
      - none
      - truncate_non_existent_table
    fk_references_without_cascade:
      label: 外键引用但未使用 CASCADE
      importance: non_important
      values:
      - none
      - has_fk_ref_no_cascade
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - none
      - non_owner_truncate
      - no_truncate_privilege
    temporary_table_truncation:
      label: 临时表清空
      importance: non_important
      values:
      - none
      - temporary_table
      - temp_table_with_sequences
    partitioned_table_behavior:
      label: 分区表行为
      importance: non_important
      values:
      - none
      - partitioned_table_only
      - partitioned_table_with_descendants
      - single_partition
    verification:
      label: 验证方式
      importance: non_important
      values:
      - key: select_count_zero
        label: SELECT count(*) = 0 — 验证表被清空
      - key: pg_class_relpages
        label: pg_class relpages — 验证物理页面已释放
      - key: sequence_reset_check
        label: 序列重置验证 — 检查序列值是否回到起始
      - key: error_assertion
        label: 错误断言 — 验证预期失败确实发生
    cleanup:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_objects
        label: DROP 已创建的测试对象
      - key: restart_identity_resets_sequences
        label: RESTART IDENTITY 重置序列 — TRUNCATE 自带清理能力
      - key: rollback
        label: ROLLBACK 事务回滚
      - key: reinsert_data
        label: 重新插入测试数据以恢复状态
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - only_clause
    - identity_option
    - cascade_restrict
    - table_name_shape
    - multi_table
    - privilege_level
    - fk_dependency
    - non_existent_table
    - fk_references_without_cascade
    - insufficient_privilege
    - temporary_table_truncation
    - partitioned_table_behavior
    - verification
    - cleanup
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "TRUNCATE [ TABLE ] [ ONLY ] {table_name} [ * ] [, ... ]\
      \ [ RESTART IDENTITY | CONTINUE IDENTITY ] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT count(*) FROM {table_name}"
    factor_value_bindings:
      only_clause:
        only: "ONLY"
        without_only: ""
      identity_option:
        restart_identity: "RESTART IDENTITY"
        continue_identity: "CONTINUE IDENTITY"
        none: ""
      cascade_restrict:
        cascade: "CASCADE"
        restrict: "RESTRICT"
        none: ""
```
