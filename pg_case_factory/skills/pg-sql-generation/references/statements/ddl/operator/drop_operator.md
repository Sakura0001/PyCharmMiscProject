# 技能：DROP OPERATOR

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropoperator.html

```sql
DROP OPERATOR [ IF EXISTS ] name ( { left_type | NONE } , right_type ) [, ...] [ CASCADE | RESTRICT ]
```

## 语句作用

官方说明：DROP OPERATOR — remove an operator

该 reference 关注 operator 的删除、依赖级联和操作数数据类型标识，不负责定义 operator 创建逻辑本身。DROP OPERATOR 需要指定操作数数据类型（left_type / right_type）来唯一标识目标 operator，这是该语句的关键特征。DROP OPERATOR 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型，但操作数数据类型是关键覆盖维度。注意：可以在一条命令中同时删除多个 operator（逗号分隔列表）。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 operator 对象状态
- operand_type_shape：操作数数据类型形态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句
- cascade_clause：CASCADE/RESTRICT 子句
- multi_drop：多条 operator 删除
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：operator 名形态
- operand_data_type：操作数数据类型

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- cascade_behavior：级联行为

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 DROP OPERATOR 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- DROP OPERATOR 需要指定操作数数据类型来唯一标识目标 operator，操作数数据类型是关键覆盖维度。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标对象存在时的成功删除路径，以及目标对象不存在时的失败路径。
- IF EXISTS 必须覆盖不存在对象的代表性 no-op 路径。
- CASCADE/RESTRICT 必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP OPERATOR 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 操作数数据类型必须覆盖二元（left_type, right_type）和前缀（NONE, right_type）两种形态。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。
- 操作数数据类型因子在二元和前缀 operator 分支上轮转挂靠，覆盖代表性类型。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、操作数类型形态和成功/失败路径。
- 次优先保证关键可选子句（IF EXISTS、CASCADE/RESTRICT）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: operator
  skill_name: drop_operator
  official_source: https://www.postgresql.org/docs/16/sql-dropoperator.html
  statement:
    key: drop_operator
    name: DROP OPERATOR
    aliases:
    - drop operator
    - DROP OPERATOR
    purpose: remove an operator
  syntax_templates:
  - "DROP OPERATOR [ IF EXISTS ] name ( { left_type | NONE } , right_type ) [, ...]\
    \ [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - target_object_state
    - operand_type_shape
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_exists_clause
    - cascade_clause
    - multi_drop
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - operand_data_type
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - cascade_behavior
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - ownership_boundary
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
        label: DROP OPERATOR 唯一语法分支
    target_object_state:
      label: 目标 operator 对象状态
      importance: important
      values:
      - exists
      - missing
      - exists_with_dependents
    operand_type_shape:
      label: 操作数数据类型形态
      importance: important
      values:
      - binary_operator
      - prefix_operator
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句
      importance: non_important
      values:
      - absent
      - present
    cascade_clause:
      label: CASCADE/RESTRICT 子句
      importance: non_important
      values:
      - restrict_default
      - restrict_explicit
      - cascade
    multi_drop:
      label: 多条 operator 删除
      importance: non_important
      values:
      - single
      - multiple
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser
      - owner
      - non_owner
      - insufficient_privilege
    name_shape:
      label: operator 名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
    operand_data_type:
      label: 操作数数据类型
      importance: non_important
      values:
      - integer
      - text
      - boolean
      - custom_type
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - no_dependents
      - has_dependents
    cascade_behavior:
      label: 级联行为
      importance: non_important
      values:
      - restrict_blocks
      - cascade_succeeds
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
    ownership_boundary:
      label: 所有权边界
      importance: non_important
      values:
      - superuser
      - owner
      - non_owner
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - effect_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_objects
      - reset_state
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - target_object_state
    - operand_type_shape
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_clause
    - multi_drop
    - privilege_context
    - name_shape
    - operand_data_type
    - dependency_state
    - cascade_behavior
    - invalid_combination
    - ownership_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
    - operand_type_shape
  rendering:
    statement_template: DROP OPERATOR {name} ({left_type}, {right_type})
    verification_query_template: ''
    factor_value_bindings: {}
```
