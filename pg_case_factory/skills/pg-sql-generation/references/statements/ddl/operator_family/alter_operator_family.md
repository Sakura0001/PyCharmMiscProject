# 技能：ALTER OPERATOR FAMILY

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alteropfamily.html

```sql
ALTER OPERATOR FAMILY name USING index_method ADD
  {  OPERATOR strategy_number operator_name ( op_type , op_type )
              [ FOR SEARCH | FOR ORDER BY sort_family_name ]
   | FUNCTION support_number [ ( op_type [ , op_type ] ) ]
              function_name [ ( argument_type [, ...] ) ]
  } [, ... ]

ALTER OPERATOR FAMILY name USING index_method DROP
  {  OPERATOR strategy_number ( op_type [ , op_type ] )
   | FUNCTION support_number ( op_type [ , op_type ] )
  } [, ... ]

ALTER OPERATOR FAMILY name USING index_method
    RENAME TO new_name

ALTER OPERATOR FAMILY name USING index_method
    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }

ALTER OPERATOR FAMILY name USING index_method
    SET SCHEMA new_schema
```

## 语句作用

官方说明：ALTER OPERATOR FAMILY — change the definition of an operator family

该 reference 关注 operator family 的 ADD/DROP 元素管理、重命名、属主变更和 schema 迁移，不负责定义底层 operator 或 function 的实现逻辑本身。ALTER OPERATOR FAMILY 是 operator class 的更高层级管理对象，ADD/DROP 分支用于管理 operator family 中不属于任何 operator class 的"松散"operator 和 support function。ADD 分支的 OPERATOR 必须指定 op_type（与 CREATE OPERATOR CLASS 不同），DROP 分支仅指定"槽位"号和输入数据类型。ALTER OPERATOR FAMILY 需要同时指定 name 和 USING index_method 来唯一标识目标对象。注意：ADD/DROP 分支中的 op_type 与 CREATE OPERATOR CLASS 中的 op_type 语义不同；B-tree comparison/hash 函数的 op_type 在 ADD FUNCTION 中可选，但 GiST/SP-GiST/GIN 的所有函数必须指定。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 operator family 对象状态
- expected_status：预期结果

### T2：重要行为因子
- alter_action_type：ALTER 动作类型
- add_element_type：ADD 元素类型（仅适用于 ADD 分支）
- drop_element_type：DROP 元素类型（仅适用于 DROP 分支）
- new_owner_shape：新 owner 形态（仅适用于 OWNER TO）
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：operator family 名形态
- element_op_type：元素操作数数据类型

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- index_method_compatibility：索引方法兼容性

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 ALTER OPERATOR FAMILY 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- ALTER OPERATOR FAMILY 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型。
- ADD/DROP 分支的元素类型（OPERATOR/FUNCTION）和 op_type 是关键覆盖维度。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 operator family，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标对象存在时的成功修改路径、目标对象不存在时的失败路径。
- ADD/DROP/RENAME/OWNER/SET SCHEMA 各分支需要保持独立归因。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER OPERATOR FAMILY 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- ADD OPERATOR 必须指定 op_type（与 CREATE OPERATOR CLASS 不同），DROP 仅指定策略号/支持号和输入数据类型。
- 需要 superuser 或 CREATE 权限的分支必须在生命周期计划中显式标注环境依赖。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。
- ADD/DROP 元素类型因子仅挂靠到 ADD/DROP 分支。
- 元素操作数数据类型因子在 ADD/DROP 分支上轮转挂靠，覆盖代表性数据类型。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句（ADD/DROP 元素类型、RENAME、OWNER TO、SET SCHEMA）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: operator_family
  skill_name: alter_operator_family
  official_source: https://www.postgresql.org/docs/16/sql-alteropfamily.html
  statement:
    key: alter_operator_family
    name: ALTER OPERATOR FAMILY
    aliases:
    - alter operator family
    - ALTER OPERATOR FAMILY
    purpose: change the definition of an operator family
  syntax_templates:
  - "ALTER OPERATOR FAMILY name USING index_method ADD\n  {  OPERATOR strategy_number\
    \ operator_name ( op_type , op_type )\n              [ FOR SEARCH | FOR ORDER\
    \ BY sort_family_name ]\n   | FUNCTION support_number [ ( op_type [ , op_type\
    \ ] ) ]\n              function_name [ ( argument_type [, ...] ) ]\n  } [, ...\
    \ ]\n\nALTER OPERATOR FAMILY name USING index_method DROP\n  {  OPERATOR strategy_number\
    \ ( op_type [ , op_type ] )\n   | FUNCTION support_number ( op_type [ , op_type\
    \ ] )\n  } [, ... ]\n\nALTER OPERATOR FAMILY name USING index_method\n    RENAME\
    \ TO new_name\n\nALTER OPERATOR FAMILY name USING index_method\n    OWNER TO\
    \ { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }\n\nALTER OPERATOR\
    \ FAMILY name USING index_method\n    SET SCHEMA new_schema"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - target_object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - alter_action_type
    - add_element_type
    - drop_element_type
    - new_owner_shape
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - element_op_type
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - index_method_compatibility
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
      - key: branch_add
        label: ADD 分支
      - key: branch_drop
        label: DROP 分支
      - key: branch_rename
        label: RENAME TO 分支
      - key: branch_owner
        label: OWNER TO 分支
      - key: branch_set_schema
        label: SET SCHEMA 分支
    target_object_state:
      label: 目标 operator family 对象状态
      importance: important
      values:
      - exists
      - missing
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
      - add_elements
      - drop_elements
      - rename
      - owner_change
      - set_schema
    add_element_type:
      label: ADD 元素类型
      importance: non_important
      values:
      - add_operator_for_search
      - add_operator_for_order_by
      - add_function
    drop_element_type:
      label: DROP 元素类型
      importance: non_important
      values:
      - drop_operator
      - drop_function
    new_owner_shape:
      label: 新 owner 形态
      importance: non_important
      values:
      - plain_role
      - current_role
      - current_user
      - session_user
      - missing_role
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser
      - owner
      - non_owner
      - insufficient_privilege
    name_shape:
      label: operator family 名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
    element_op_type:
      label: 元素操作数数据类型
      importance: non_important
      values:
      - integer
      - text
      - custom_type
      - none_prefix_operator
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_operator
      - missing_function
      - missing_family
    index_method_compatibility:
      label: 索引方法兼容性
      importance: non_important
      values:
      - compatible
      - incompatible
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
    - expected_status
    non_main_factors:
    - alter_action_type
    - add_element_type
    - drop_element_type
    - new_owner_shape
    - privilege_context
    - name_shape
    - element_op_type
    - dependency_state
    - index_method_compatibility
    - invalid_combination
    - ownership_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
  rendering:
    statement_template: ALTER OPERATOR FAMILY {name} USING {index_method}
    verification_query_template: ''
    factor_value_bindings: {}
```
