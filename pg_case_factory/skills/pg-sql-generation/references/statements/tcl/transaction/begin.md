# 技能：BEGIN

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-begin.html

```sql
BEGIN [ WORK | TRANSACTION ] [ transaction_mode [, ...] ]

where transaction_mode is one of:

    ISOLATION LEVEL { SERIALIZABLE | REPEATABLE READ | READ COMMITTED | READ UNCOMMITTED }
    READ WRITE | READ ONLY
    [ NOT ] DEFERRABLE
```

## 语句作用

官方说明：BEGIN — start a transaction block

该 reference 关注事务控制语句的状态转换、事务模式和错误边界，不负责包装所有样本到统一外层事务。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- transaction_state：事务状态
- expected_status：预期结果

### T2：重要行为因子
- transaction_mode：事务模式
- chain_behavior：CHAIN 行为

### T3：对象名与输入形态因子
- transaction_id_shape：事务标识形态
- savepoint_name_shape：保存点名称形态

### T4：依赖对象与环境因子
- environment_context：环境上下文
- framework_context：测试框架事务包装

### T5：异常与边界因子
- invalid_combination：非法组合
- state_boundary：状态边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖事务外、事务内、保存点存在/不存在、两阶段事务开启/关闭等状态。
- CHAIN、WORK/TRANSACTION、隔离级别、READ ONLY/WRITE、DEFERRABLE 等选项按语句支持情况覆盖。
- 两阶段事务分支必须单独标注环境依赖。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 事务控制样本不得被测试框架强制包裹在不可见外层事务中。
- PREPARE TRANSACTION、COMMIT PREPARED、ROLLBACK PREPARED 需要 max_prepared_transactions 支持。
- 失败样本必须避免遗留打开事务、保存点或 prepared transaction。
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
  category: tcl
  domain: transaction
  skill_name: begin
  official_source: https://www.postgresql.org/docs/16/sql-begin.html
  statement:
    key: begin
    name: BEGIN
    aliases:
    - begin
    - begin
    - begin
    - BEGIN
    purpose: BEGIN — start a transaction block
  syntax_templates:
  - "BEGIN [ WORK | TRANSACTION ] [ transaction_mode [, ...] ]\n\nwhere transaction_mode is one of:\n\n    ISOLATION LEVEL\
    \ { SERIALIZABLE | REPEATABLE READ | READ COMMITTED | READ UNCOMMITTED }\n    READ WRITE | READ ONLY\n    [ NOT ] DEFERRABLE"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - transaction_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - transaction_mode
    - chain_behavior
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - transaction_id_shape
    - savepoint_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - environment_context
    - framework_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - state_boundary
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
    transaction_state:
      label: 事务状态
      importance: important
      values:
      - outside_transaction
      - inside_transaction
      - savepoint_exists
      - prepared_transaction_exists
      - missing_required_state
    transaction_mode:
      label: 事务模式
      importance: non_important
      values:
      - default
      - isolation_level
      - read_write
      - read_only
      - deferrable
    chain_behavior:
      label: CHAIN 行为
      importance: non_important
      values:
      - none
      - and_chain
      - and_no_chain
    transaction_id_shape:
      label: 事务标识形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - missing_id
      - duplicate_id
    savepoint_name_shape:
      label: 保存点名称形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - missing_name
      - released_name
    environment_context:
      label: 环境上下文
      importance: non_important
      values:
      - normal_session
      - transaction_block
      - outside_transaction_required
      - external_resource_required
    framework_context:
      label: 测试框架事务包装
      importance: non_important
      values:
      - no_outer_transaction
      - outer_transaction_present
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
      - object_type_mismatch
    state_boundary:
      label: 状态边界
      importance: non_important
      values:
      - no_open_transaction
      - nested_savepoint
      - prepared_transaction_leftover
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
    - transaction_state
    - expected_status
    non_main_factors:
    - transaction_mode
    - chain_behavior
    - transaction_id_shape
    - savepoint_name_shape
    - environment_context
    - framework_context
    - invalid_combination
    - state_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - transaction_state
  rendering:
    statement_template: BEGIN [ WORK | TRANSACTION ] [ transaction_mode [, ...] ]
    verification_query_template: ''
    factor_value_bindings: {}
```
