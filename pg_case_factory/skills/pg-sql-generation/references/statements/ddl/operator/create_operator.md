# 技能：CREATE OPERATOR

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createoperator.html

```sql
CREATE OPERATOR name (
    {FUNCTION|PROCEDURE} = function_name
    [, LEFTARG = left_type ] [, RIGHTARG = right_type ]
    [, COMMUTATOR = com_op ] [, NEGATOR = neg_op ]
    [, RESTRICT = res_proc ] [, JOIN = join_proc ]
    [, HASHES ] [, MERGES ]
)
```

## 语句作用

官方说明：CREATE OPERATOR — define a new operator

该 reference 关注 operator 的创建、操作数数据类型（left_type / right_type）和依赖函数状态，不负责定义底层函数的实现逻辑本身。CREATE OPERATOR 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型，但操作数数据类型（LEFTARG / RIGHTARG）是关键覆盖维度。注意：operator 名长度不超过 NAMEDATALEN-1（63 字符）；允许的字符为 + - * / < > = ~ ! @ # % ^ & | ` ?；需要 superuser 或在目标 schema 有 CREATE 权限才能创建 operator；COMMUTATOR / NEGATOR 使用 OPERATOR() 语法做 schema 限定；FUNCTION 和 PROCEDURE 关键字等效，但 PROCEDURE 是历史用法。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 operator 对象状态
- operand_type_shape：操作数数据类型形态
- expected_status：预期结果

### T2：重要行为因子
- function_clause：FUNCTION/PROCEDURE 子句
- leftarg_clause：LEFTARG 子句
- rightarg_clause：RIGHTARG 子句
- commutator_clause：COMMUTATOR 子句
- negator_clause：NEGATOR 子句
- restrict_clause：RESTRICT 子句
- join_clause：JOIN 子句
- hashes_clause：HASHES 子句
- merges_clause：MERGES 子句
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：operator 名形态
- function_name_shape：函数名形态
- operand_data_type：操作数数据类型

### T4：依赖对象与环境因子
- dependency_state：依赖函数状态
- operator_type_compatibility：操作数类型兼容性

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 CREATE OPERATOR 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- CREATE OPERATOR 是对象级 DDL，但操作数数据类型（LEFTARG / RIGHTARG）是关键覆盖维度，需要覆盖代表性数据类型。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖函数缺失路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE OPERATOR 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 操作数数据类型必须覆盖二元（有 LEFTARG 和 RIGHTARG）和前缀（仅有 RIGHTARG，LEFTARG 为 NONE）两种形态。
- 需要 superuser 或 CREATE 权限的分支必须在生命周期计划中显式标注环境依赖。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。
- 操作数数据类型因子在二元和前缀 operator 分支上轮转挂靠，覆盖代表性类型。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、操作数类型形态和成功/失败路径。
- 次优先保证关键可选子句（COMMUTATOR、NEGATOR、RESTRICT、JOIN、HASHES、MERGES）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: operator
  skill_name: create_operator
  official_source: https://www.postgresql.org/docs/16/sql-createoperator.html
  statement:
    key: create_operator
    name: CREATE OPERATOR
    aliases:
    - create operator
    - CREATE OPERATOR
    purpose: define a new operator
  syntax_templates:
  - "CREATE OPERATOR name (\n    {FUNCTION|PROCEDURE} = function_name\n    [, LEFTARG\
    \ = left_type ] [, RIGHTARG = right_type ]\n    [, COMMUTATOR = com_op ] [,\
    \ NEGATOR = neg_op ]\n    [, RESTRICT = res_proc ] [, JOIN = join_proc ]\n  \
    \  [, HASHES ] [, MERGES ]\n)"
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
    - function_clause
    - leftarg_clause
    - rightarg_clause
    - commutator_clause
    - negator_clause
    - restrict_clause
    - join_clause
    - hashes_clause
    - merges_clause
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - function_name_shape
    - operand_data_type
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - operator_type_compatibility
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
        label: CREATE OPERATOR 唯一语法分支
    target_object_state:
      label: 目标 operator 对象状态
      importance: important
      values:
      - absent
      - exists
      - exists_conflict
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
    function_clause:
      label: FUNCTION/PROCEDURE 子句
      importance: non_important
      values:
      - function_keyword
      - procedure_keyword
    leftarg_clause:
      label: LEFTARG 子句
      importance: non_important
      values:
      - present
      - absent_prefix_operator
    rightarg_clause:
      label: RIGHTARG 子句
      importance: non_important
      values:
      - present
    commutator_clause:
      label: COMMUTATOR 子句
      importance: non_important
      values:
      - absent
      - present
    negator_clause:
      label: NEGATOR 子句
      importance: non_important
      values:
      - absent
      - present
    restrict_clause:
      label: RESTRICT 子句
      importance: non_important
      values:
      - absent
      - present
    join_clause:
      label: JOIN 子句
      importance: non_important
      values:
      - absent
      - present
    hashes_clause:
      label: HASHES 子句
      importance: non_important
      values:
      - absent
      - present
    merges_clause:
      label: MERGES 子句
      importance: non_important
      values:
      - absent
      - present
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser
      - schema_create_privilege
      - insufficient_privilege
    name_shape:
      label: operator 名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
    function_name_shape:
      label: 函数名形态
      importance: non_important
      values:
      - plain_function
      - schema_qualified_function
      - missing_function
    operand_data_type:
      label: 操作数数据类型
      importance: non_important
      values:
      - integer
      - text
      - boolean
      - numeric
      - custom_type
    dependency_state:
      label: 依赖函数状态
      importance: non_important
      values:
      - ready
      - missing_function
      - wrong_signature
    operator_type_compatibility:
      label: 操作数类型兼容性
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
      - schema_owner
      - non_privileged
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
    - function_clause
    - leftarg_clause
    - rightarg_clause
    - commutator_clause
    - negator_clause
    - restrict_clause
    - join_clause
    - hashes_clause
    - merges_clause
    - privilege_context
    - name_shape
    - function_name_shape
    - operand_data_type
    - dependency_state
    - operator_type_compatibility
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
    statement_template: CREATE OPERATOR {name}
    verification_query_template: ''
    factor_value_bindings: {}
```
