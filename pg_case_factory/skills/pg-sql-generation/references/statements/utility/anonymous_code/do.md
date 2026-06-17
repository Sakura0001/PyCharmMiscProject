# 技能：DO

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-do.html

```sql
DO [ LANGUAGE lang_name ] code
```

## 语句作用

官方说明：DO — execute an anonymous code block

该 reference 关注维护、诊断、复制、锁、匿名代码和系统级工具命令的语法与环境边界，不负责伪造外部文件或超级用户能力。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_state：目标状态
- expected_status：预期结果

### T2：重要行为因子
- option_shape：选项形态
- execution_mode：执行模式

### T3：对象名与输入形态因子
- target_name_shape：目标名称形态
- input_output_shape：输入输出形态

### T4：依赖对象与环境因子
- environment_context：环境上下文
- privilege_context：权限上下文

### T5：异常与边界因子
- invalid_combination：非法组合
- resource_boundary：资源边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖官方选项分支、目标对象形态、执行上下文、权限和环境依赖。
- 涉及表、列或查询的工具语句应结合基础对象模板做代表性覆盖。
- 会产生锁、统计信息、文件访问或运行时副作用的分支必须显式标注。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 需要文件系统、PROGRAM、共享库、CHECKPOINT、VACUUM FULL 或服务端文件权限的分支不得默认视为普通用户成功路径。
- LOCK 必须在事务块中验证，VACUUM 部分分支不能放在事务块中运行。
- EXPLAIN ANALYZE 会执行目标语句，必须使用可控数据和清理策略。
- 需要特殊权限、外部服务、文件系统、两阶段事务、第二连接或非事务环境的分支必须显式标注，不得伪造为普通成功路径。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标/依赖状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: utility
  domain: anonymous_code
  skill_name: do
  official_source: https://www.postgresql.org/docs/16/sql-do.html
  statement:
    key: do
    name: DO
    aliases:
    - do
    - do
    - do
    - DO
    purpose: DO — execute an anonymous code block
  syntax_templates:
  - DO [ LANGUAGE lang_name ] code
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - target_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - option_shape
    - execution_mode
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - target_name_shape
    - input_output_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - environment_context
    - privilege_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - resource_boundary
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
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    target_state:
      label: 目标状态
      importance: important
      values:
      - target_exists
      - target_missing
      - database_wide
      - wrong_object_type
    option_shape:
      label: 选项形态
      importance: non_important
      values:
      - minimal
      - verbose_or_format
      - boolean_options
      - resource_options
    execution_mode:
      label: 执行模式
      importance: non_important
      values:
      - metadata_only
      - executes_statement
      - locks_or_rewrites
      - server_side_io
    target_name_shape:
      label: 目标名称形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
      - all_or_database_wide
    input_output_shape:
      label: 输入输出形态
      importance: non_important
      values:
      - none
      - table_columns
      - query_source
      - stdin_stdout
      - server_file_or_program
    environment_context:
      label: 环境上下文
      importance: non_important
      values:
      - normal_session
      - transaction_block
      - outside_transaction_required
      - external_resource_required
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - owner
      - granted_role
      - insufficient_privilege
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
      - object_type_mismatch
    resource_boundary:
      label: 资源边界
      importance: non_important
      values:
      - small_relation
      - empty_relation
      - locked_relation
      - missing_file_or_library
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - effect_query
      - returned_rows
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - rollback
      - drop_objects
      - reset_state
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - target_state
    - expected_status
    non_main_factors:
    - option_shape
    - execution_mode
    - target_name_shape
    - input_output_shape
    - environment_context
    - privilege_context
    - invalid_combination
    - resource_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_state
  rendering:
    statement_template: DO [ LANGUAGE lang_name ] code
    verification_query_template: ''
    factor_value_bindings: {}
```
