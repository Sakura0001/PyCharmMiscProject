# 技能：CREATE OPERATOR CLASS

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createopclass.html

```sql
CREATE OPERATOR CLASS name [ DEFAULT ] FOR TYPE data_type
  USING index_method [ FAMILY family_name ] AS
  {  OPERATOR strategy_number operator_name [ ( op_type , op_type ) ] [ FOR SEARCH | FOR ORDER BY sort_family_name ]
   | FUNCTION support_number [ ( op_type [ , op_type ] ) ] function_name ( argument_type [, ...] )
   | STORAGE storage_type
  } [, ... ]
```

## 语句作用

官方说明：CREATE OPERATOR CLASS — define a new operator class

该 reference 关注 operator class 的创建、DEFAULT 属性、索引方法与数据类型兼容性和内部元素（OPERATOR/FUNCTION/STORAGE）定义，不负责定义底层 operator 或 function 的实现逻辑本身。CREATE OPERATOR CLASS 是对象级 DDL，不要求覆盖普通表中的所有列类型或所有表类型，但 FOR TYPE data_type 与索引方法的兼容性是关键覆盖维度。STORAGE storage_type 仅允许用于 GiST、GIN、SP-GiST 和 BRIN 索引方法；如果 data_type 为 anyarray，则 storage_type 可为 anyelement。注意：需要 superuser 或在目标 schema 有 CREATE 权限才能创建 operator class。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 operator class 对象状态
- data_type_index_method：FOR TYPE data_type USING index_method 组合
- expected_status：预期结果

### T2：重要行为因子
- default_clause：DEFAULT 子句
- family_clause：FAMILY 子句
- operator_entry：OPERATOR 条目类型
- function_entry：FUNCTION 条目类型
- storage_entry：STORAGE 条目类型
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：operator class 名形态
- data_type_shape：FOR TYPE 数据类型形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- index_method_compatibility：索引方法与数据类型兼容性

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 CREATE OPERATOR CLASS 语法分支。
- 不需要覆盖所有基表。
- 不需要覆盖每张基表中所有的列类型。
- CREATE OPERATOR CLASS 是对象级 DDL，但 FOR TYPE data_type 与 USING index_method 的兼容性是关键覆盖维度，需要覆盖代表性索引方法和数据类型组合。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE OPERATOR CLASS 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- OPERATOR/FUNCTION/STORAGE 条目必须覆盖代表性策略号、支持号和存储类型。
- STORAGE storage_type 仅允许用于 GiST、GIN、SP-GiST 和 BRIN 索引方法的限制必须显式标注。
- 需要 superuser 或 CREATE 权限的分支必须在生命周期计划中显式标注环境依赖。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。
- 索引方法与数据类型兼容性因子挂靠到各代表性 index_method 分支上轮转注入。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、数据类型与索引方法组合和成功/失败路径。
- 次优先保证关键可选子句（DEFAULT、FAMILY、OPERATOR/FUNCTION/STORAGE 条目类型）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: operator_class
  skill_name: create_operator_class
  official_source: https://www.postgresql.org/docs/16/sql-createopclass.html
  statement:
    key: create_operator_class
    name: CREATE OPERATOR CLASS
    aliases:
    - create operator class
    - CREATE OPERATOR CLASS
    purpose: define a new operator class
  syntax_templates:
  - "CREATE OPERATOR CLASS name [ DEFAULT ] FOR TYPE data_type\n  USING index_method\
    \ [ FAMILY family_name ] AS\n  {  OPERATOR strategy_number operator_name [ (\
    \ op_type , op_type ) ] [ FOR SEARCH | FOR ORDER BY sort_family_name ]\n   |\
    \ FUNCTION support_number [ ( op_type [ , op_type ] ) ] function_name ( argument_type\
    \ [, ...] )\n   | STORAGE storage_type\n  } [, ... ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - target_object_state
    - data_type_index_method
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - default_clause
    - family_clause
    - operator_entry
    - function_entry
    - storage_entry
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - data_type_shape
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
      - key: branch_1
        label: CREATE OPERATOR CLASS 唯一语法分支
    target_object_state:
      label: 目标 operator class 对象状态
      importance: important
      values:
      - absent
      - exists
      - exists_conflict
    data_type_index_method:
      label: FOR TYPE data_type USING index_method 组合
      importance: important
      values:
      - key: btree_integer
        label: btree + integer
      - key: hash_text
        label: hash + text
      - key: gist_geometry
        label: gist + 自定义类型
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    default_clause:
      label: DEFAULT 子句
      importance: non_important
      values:
      - absent
      - present
    family_clause:
      label: FAMILY 子句
      importance: non_important
      values:
      - absent_auto_created
      - present_existing
      - present_missing
    operator_entry:
      label: OPERATOR 条目类型
      importance: non_important
      values:
      - for_search
      - for_order_by
      - with_op_type
      - without_op_type
    function_entry:
      label: FUNCTION 条目类型
      importance: non_important
      values:
      - with_op_type
      - without_op_type
    storage_entry:
      label: STORAGE 条目类型
      importance: non_important
      values:
      - absent
      - present_gist
      - present_gin
      - present_spgist
      - present_brin
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser
      - schema_create_privilege
      - insufficient_privilege
    name_shape:
      label: operator class 名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
    data_type_shape:
      label: FOR TYPE 数据类型形态
      importance: non_important
      values:
      - integer
      - text
      - anyarray
      - custom_type
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_operator
      - missing_function
      - missing_family
    index_method_compatibility:
      label: 索引方法与数据类型兼容性
      importance: non_important
      values:
      - compatible
      - storage_not_allowed_btree_hash
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
    - data_type_index_method
    - expected_status
    non_main_factors:
    - default_clause
    - family_clause
    - operator_entry
    - function_entry
    - storage_entry
    - privilege_context
    - name_shape
    - data_type_shape
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
    - data_type_index_method
  rendering:
    statement_template: CREATE OPERATOR CLASS {name} FOR TYPE {data_type} USING {index_method}
    verification_query_template: ''
    factor_value_bindings: {}
```
