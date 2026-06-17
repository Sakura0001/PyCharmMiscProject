# 技能：PREPARE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-prepare.html

```sql
PREPARE name [ ( data_type [, ...] ) ] AS statement
```

## 语句作用

官方说明：PREPARE — prepare a statement for execution

该 reference 关注 prepared statement 生命周期、参数绑定和释放行为，不负责长期缓存执行计划。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- prepared_state：预备语句状态
- expected_status：预期结果

### T2：重要行为因子
- parameter_shape：参数定义形态
- prepared_statement_body：预备语句体

### T3：对象名与输入形态因子
- prepared_name_shape：预备语句名称形态
- argument_shape：执行参数形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- transaction_context：事务上下文

### T5：异常与边界因子
- invalid_combination：非法组合
- lifecycle_boundary：生命周期边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 PREPARE、EXECUTE、DEALLOCATE 的名称状态、参数类型、参数数量和 ALL 分支。
- 可执行 statement 类型按代表性覆盖，数据变更语句需要可复跑对象和清理。
- 重复名称、缺失名称、参数类型不匹配和释放后执行作为失败路径。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- EXECUTE 样本必须先 PREPARE；DEALLOCATE 后不得遗留同名 prepared statement。
- 失败样本只能聚焦一个生命周期或参数错误。
- 验证可通过 pg_prepared_statements 和语句执行结果完成。
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
  category: prepared
  domain: prepared_statement
  skill_name: prepare
  official_source: https://www.postgresql.org/docs/16/sql-prepare.html
  statement:
    key: prepare
    name: PREPARE
    aliases:
    - prepare
    - prepare
    - prepare
    - PREPARE
    purpose: PREPARE — prepare a statement for execution
  syntax_templates:
  - PREPARE name [ ( data_type [, ...] ) ] AS statement
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - prepared_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - parameter_shape
    - prepared_statement_body
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - prepared_name_shape
    - argument_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - transaction_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - lifecycle_boundary
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
    prepared_state:
      label: 预备语句状态
      importance: important
      values:
      - exists
      - missing
      - duplicate_name
      - deallocated
    parameter_shape:
      label: 参数定义形态
      importance: non_important
      values:
      - none
      - single_typed_parameter
      - multiple_typed_parameters
      - type_mismatch
    prepared_statement_body:
      label: 预备语句体
      importance: non_important
      values:
      - select_statement
      - insert_or_update_statement
      - utility_allowed_statement
    prepared_name_shape:
      label: 预备语句名称形态
      importance: non_important
      values:
      - plain_identifier
      - quoted_identifier
      - all_prepared_statements
      - missing_name
    argument_shape:
      label: 执行参数形态
      importance: non_important
      values:
      - none
      - matching_arguments
      - too_few_arguments
      - too_many_arguments
      - wrong_type_arguments
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    transaction_context:
      label: 事务上下文
      importance: non_important
      values:
      - outside_transaction
      - inside_transaction
      - after_rollback
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
      - object_type_mismatch
    lifecycle_boundary:
      label: 生命周期边界
      importance: non_important
      values:
      - prepare_execute_deallocate
      - execute_after_deallocate
      - deallocate_all
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
    - prepared_state
    - expected_status
    non_main_factors:
    - parameter_shape
    - prepared_statement_body
    - prepared_name_shape
    - argument_shape
    - dependency_state
    - transaction_context
    - invalid_combination
    - lifecycle_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - prepared_state
  rendering:
    statement_template: PREPARE name [ ( data_type [, ...] ) ] AS statement
    verification_query_template: ''
    factor_value_bindings: {}
```
