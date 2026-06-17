# 技能：ALTER OPERATOR

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alteroperator.html

```sql
ALTER OPERATOR name ( { left_type | NONE } , right_type )
    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }

ALTER OPERATOR name ( { left_type | NONE } , right_type )
    SET SCHEMA new_schema

ALTER OPERATOR name ( { left_type | NONE } , right_type )
    SET ( {  RESTRICT = { res_proc | NONE }
           | JOIN = { join_proc | NONE }
         } [, ... ] )
```

## 语句作用

官方说明：ALTER OPERATOR — change the definition of an operator

该 reference 关注 operator 的属主变更、schema 迁移和选择性估算器设置，不负责定义 operator 创建逻辑本身。ALTER OPERATOR 需要指定操作数数据类型（left_type / right_type）来唯一标识目标 operator，这是该语句的关键特征。ALTER OPERATOR 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型，但操作数数据类型是关键覆盖维度。注意：SET 分支中的 RESTRICT 和 JOIN 是选择性估算器函数名，与 DROP 的 CASCADE/RESTRICT 无关。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 operator 对象状态
- operand_type_shape：操作数数据类型形态
- expected_status：预期结果

### T2：重要行为因子
- alter_action_type：ALTER 动作类型
- new_owner_shape：新 owner 形态（仅适用于 OWNER TO）
- restrict_estimator：RESTRICT 估算器设置（仅适用于 SET）
- join_estimator：JOIN 估算器设置（仅适用于 SET）
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：operator 名形态
- operand_data_type：操作数数据类型

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- schema_migration_state：schema 迁移状态

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 ALTER OPERATOR 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- ALTER OPERATOR 需要指定操作数数据类型来唯一标识目标 operator，操作数数据类型是关键覆盖维度。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 operator，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标对象存在时的成功修改路径、目标对象不存在时的失败路径。
- OWNER TO / SET SCHEMA / SET(RESTRICT/JOIN) 分支需要保持独立归因。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER OPERATOR 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 操作数数据类型必须覆盖二元（left_type, right_type）和前缀（NONE, right_type）两种形态。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。
- 操作数数据类型因子在二元和前缀 operator 分支上轮转挂靠，覆盖代表性类型。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、操作数类型形态和成功/失败路径。
- 次优先保证关键可选子句（OWNER TO、SET SCHEMA、SET RESTRICT/JOIN）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: operator
  skill_name: alter_operator
  official_source: https://www.postgresql.org/docs/16/sql-alteroperator.html
  statement:
    key: alter_operator
    name: ALTER OPERATOR
    aliases:
    - alter operator
    - ALTER OPERATOR
    purpose: change the definition of an operator
  syntax_templates:
  - "ALTER OPERATOR name ( { left_type | NONE } , right_type )\n    OWNER TO {\
    \ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }\n\nALTER OPERATOR\
    \ name ( { left_type | NONE } , right_type )\n    SET SCHEMA new_schema\n\n\
    ALTER OPERATOR name ( { left_type | NONE } , right_type )\n    SET ( {  RESTRICT\
    \ = { res_proc | NONE }\n           | JOIN = { join_proc | NONE }\n         }\
    \ [, ... ] )"
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
    - alter_action_type
    - new_owner_shape
    - restrict_estimator
    - join_estimator
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
    - schema_migration_state
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
      - key: branch_owner
        label: OWNER TO 分支
      - key: branch_set_schema
        label: SET SCHEMA 分支
      - key: branch_set_estimator
        label: SET(RESTRICT/JOIN) 分支
    target_object_state:
      label: 目标 operator 对象状态
      importance: important
      values:
      - exists
      - missing
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
    alter_action_type:
      label: ALTER 动作类型
      importance: important
      values:
      - owner_change
      - set_schema
      - set_estimator
    new_owner_shape:
      label: 新 owner 形态
      importance: non_important
      values:
      - plain_role
      - current_role
      - current_user
      - session_user
      - missing_role
    restrict_estimator:
      label: RESTRICT 估算器设置
      importance: non_important
      values:
      - none_value
      - res_proc_name
      - missing_proc
    join_estimator:
      label: JOIN 估算器设置
      importance: non_important
      values:
      - none_value
      - join_proc_name
      - missing_proc
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
      - ready
      - missing_dependency
    schema_migration_state:
      label: schema 迁移状态
      importance: non_important
      values:
      - target_schema_exists
      - target_schema_missing
      - target_schema_conflict
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
      - object_type_mismatch
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
    - alter_action_type
    - new_owner_shape
    - restrict_estimator
    - join_estimator
    - privilege_context
    - name_shape
    - operand_data_type
    - dependency_state
    - schema_migration_state
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
    statement_template: ALTER OPERATOR {name} ({left_type}, {right_type})
    verification_query_template: ''
    factor_value_bindings: {}
```
