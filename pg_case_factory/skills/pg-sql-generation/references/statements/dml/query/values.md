# 技能：VALUES

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-values.html

```sql
VALUES ( expression [, ...] ) [, ...]
    [ ORDER BY sort_expression [ ASC | DESC | USING operator ] [, ...] ]
    [ LIMIT { count | ALL } ]
    [ OFFSET start [ ROW | ROWS ] ]
    [ FETCH { FIRST | NEXT } [ count ] { ROW | ROWS } ONLY ]
```

## 语句作用

官方说明：VALUES — compute a set of rows

该 reference 关注数据读取或数据变更语句的语法覆盖、目标对象状态、表达式/查询输入和结果验证，不负责定义基础表模板本身。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_relation_state：目标关系状态
- data_or_query_shape：数据或查询输入形态
- expected_status：预期结果

### T2：重要行为因子
- condition_shape：WHERE/匹配/过滤条件形态
- result_shape：结果输出形态
- with_clause：WITH 子句

### T3：对象名与输入形态因子
- name_shape：对象名与别名形态
- expression_shape：表达式形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- privilege_context：权限上下文

### T5：异常与边界因子
- invalid_combination：非法组合
- constraint_boundary：约束与边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 涉及表、列、表达式或查询结果的分支，需要结合基础对象模板分析是否覆盖所有基表和列类型。
- DML 主覆盖优先保留语句分支、目标对象状态、输入数据形态、条件/匹配形态和成功/失败路径。
- RETURNING、WITH、别名、锁定或冲突处理等子句按语义重要性进入 T2 或轮转挂靠。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 成功样本必须能通过行数、返回结果、系统目录或可重复查询验证效果。
- 失败样本只保留一个主要失败原因，例如权限不足、列不存在、约束冲突或对象类型不匹配。
- 涉及数据变更的样本必须准备可复跑数据，并在结束阶段清理或回滚到可预测状态。
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
  category: dml
  domain: query
  skill_name: values
  official_source: https://www.postgresql.org/docs/16/sql-values.html
  statement:
    key: values
    name: VALUES
    aliases:
    - values
    - values
    - values
    - VALUES
    purpose: VALUES — compute a set of rows
  syntax_templates:
  - "VALUES ( expression [, ...] ) [, ...]\n    [ ORDER BY sort_expression [ ASC | DESC | USING operator ] [, ...] ]\n   \
    \ [ LIMIT { count | ALL } ]\n    [ OFFSET start [ ROW | ROWS ] ]\n    [ FETCH { FIRST | NEXT } [ count ] { ROW | ROWS\
    \ } ONLY ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - target_relation_state
    - data_or_query_shape
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - condition_shape
    - result_shape
    - with_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - expression_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - privilege_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - constraint_boundary
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
    target_relation_state:
      label: 目标关系状态
      importance: important
      values:
      - exists
      - missing
      - wrong_object_type
    data_or_query_shape:
      label: 数据或查询输入形态
      importance: important
      values:
      - minimal
      - explicit_values
      - query_source
      - cte_source
    condition_shape:
      label: WHERE/匹配/过滤条件形态
      importance: non_important
      values:
      - none
      - simple_predicate
      - join_or_match_condition
      - cursor_or_conflict_target
    result_shape:
      label: 结果输出形态
      importance: non_important
      values:
      - none
      - returning_star
      - returning_expression
      - rowset_projection
    with_clause:
      label: WITH 子句
      importance: non_important
      values:
      - absent
      - non_recursive
      - recursive
    name_shape:
      label: 对象名与别名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
      - alias_used
    expression_shape:
      label: 表达式形态
      importance: non_important
      values:
      - literal
      - column_reference
      - function_call
      - subquery_expression
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
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
    constraint_boundary:
      label: 约束与边界
      importance: non_important
      values:
      - none
      - constraint_satisfied
      - constraint_violation
      - empty_input
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
    - target_relation_state
    - data_or_query_shape
    - expected_status
    non_main_factors:
    - condition_shape
    - result_shape
    - with_clause
    - name_shape
    - expression_shape
    - dependency_state
    - privilege_context
    - invalid_combination
    - constraint_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_relation_state
    - data_or_query_shape
  rendering:
    statement_template: VALUES ( expression [, ...] ) [, ...]
    verification_query_template: ''
    factor_value_bindings: {}
```
