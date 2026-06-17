# 技能：COMMENT

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-comment.html

```sql
COMMENT ON
{
  ACCESS METHOD object_name |
  AGGREGATE aggregate_name ( aggregate_signature ) |
  CAST (source_type AS target_type) |
  COLLATION object_name |
  COLUMN relation_name.column_name |
  CONSTRAINT constraint_name ON table_name |
  CONSTRAINT constraint_name ON DOMAIN domain_name |
  CONVERSION object_name |
  DATABASE object_name |
  DOMAIN object_name |
  EXTENSION object_name |
  EVENT TRIGGER object_name |
  FOREIGN DATA WRAPPER object_name |
  FOREIGN TABLE object_name |
  FUNCTION function_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  INDEX object_name |
  LARGE OBJECT large_object_oid |
  MATERIALIZED VIEW object_name |
  OPERATOR operator_name (left_type, right_type) |
  OPERATOR CLASS object_name USING index_method |
  OPERATOR FAMILY object_name USING index_method |
  POLICY policy_name ON table_name |
  [ PROCEDURAL ] LANGUAGE object_name |
  PROCEDURE procedure_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  PUBLICATION object_name |
  ROLE object_name |
  ROUTINE routine_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  RULE rule_name ON table_name |
  SCHEMA object_name |
  SEQUENCE object_name |
  SERVER object_name |
  STATISTICS object_name |
  SUBSCRIPTION object_name |
  TABLE object_name |
  TABLESPACE object_name |
  TEXT SEARCH CONFIGURATION object_name |
  TEXT SEARCH DICTIONARY object_name |
  TEXT SEARCH PARSER object_name |
  TEXT SEARCH TEMPLATE object_name |
  TRANSFORM FOR type_name LANGUAGE lang_name |
  TRIGGER trigger_name ON table_name |
  TYPE object_name |
  VIEW object_name
} IS { string_literal | NULL }

where aggregate_signature is:

* |
[ argmode ] [ argname ] argtype [ , ... ] |
[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]
```

PG16 关键约束：
- COMMENT ON 每个对象只有一个注释，新注释替换旧注释
- 使用 IS NULL 或 IS ''（空字符串）可移除注释，两者等效
- 注释随对象删除而自动清除
- 只有对象 owner 才能设置注释；superuser 可以注释任何对象
- COMMENT ON ROLE 需要 superuser（对 superuser 角色）或 CREATEROLE + ADMIN OPTION
- COMMENT ON ACCESS METHOD 需要 superuser（access method 无 owner）
- 对 FUNCTION/PROCEDURE/AGGREGATE/ROUTINE：OUT 参数和参数名被忽略，仅输入参数数据类型决定身份
- 对 OPERATOR：缺失参数使用 NONE（如 OPERATOR - (NONE, integer)）
- PROCEDURAL 为噪声词（可选）
- 对象被注释时获取 SHARE UPDATE EXCLUSIVE 锁
- 任何连接用户可以查看当前数据库中所有注释；共享对象（database/role/tablespace）的注释全局可见

## 语句作用

官方说明：COMMENT — define or change the comment of an object

该 reference 关注 COMMENT 语句的所有可注释对象类型分支。COMMENT 的核心语义维度是对象类型（object_type），不同对象类型有不同的标识格式、权限要求和前置依赖。该语句不涉及列类型组合，不需要覆盖基表或列类型。

## 测试因子分级

### T1：核心语义因子
- object_type：可注释对象类型（37 种顶层语法分支）
- comment_action：注释动作（设置 string_literal / 设置 NULL 移除注释）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- privilege_level：执行权限（object_owner / non_owner / superuser / createrole_with_admin）
- object_state：目标对象状态（已存在 / 不存在）
- identifier_format：标识符格式（simple_name / schema_qualified / composite_format）

### T3：对象名与输入形态因子
- object_name_shape：对象名称形态
- column_name_shape：列名称形态（仅 COLUMN 分支）
- constraint_name_shape：约束名称形态（仅 CONSTRAINT 分支）
- function_signature_shape：函数签名形态（仅 FUNCTION/PROCEDURE/AGGREGATE/ROUTINE 分支）
- operator_signature_shape：运算符签名形态（仅 OPERATOR 分支）
- comment_text_shape：注释文本形态

### T4：依赖对象与环境因子
- prerequisite_object：前置依赖对象存在性（依赖表/函数/类型等存在 / 不存在）
- schema_privilege：schema 权限（有权限 / 无权限）
- role_privilege：角色权限（owner / CREATEROLE / superuser）
- shared_object_scope：共享对象可见性（database/role/tablespace 全局可见 / 本地可见）

### T5：异常与边界因子
- object_not_exist：目标对象不存在时的失败路径
- privilege_denied：非 owner 尝试注释的失败路径
- wrong_identifier_format：标识格式错误（如 COLUMN 缺少 relation_name）
- cast_type_not_exist：CAST 的 source/target 类型不存在
- aggregate_signature_invalid：AGGREGATE 签名不匹配
- operator_none_misuse：OPERATOR NONE 使用不当
- transform_type_or_lang_not_exist：TRANSFORM 的类型或语言不存在
- large_object_oid_invalid：LARGE OBJECT OID 无效

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖 COMMENT 的所有 37 种对象类型分支，每种分支至少一个成功路径样本。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- object_type 为主要覆盖轴，做全量枚举覆盖（37 种对象类型全覆盖）。
- comment_action（设置/移除）在每个主要对象类型分支上轮转覆盖。
- privilege_level 在代表性分支上做笛卡尔覆盖：owner 成功、non_owner 失败、superuser 成功、CREATEROLE 对 ROLE 成功/失败。
- object_state 仅覆盖"对象存在/不存在"路径：存在时设置注释成功、不存在时失败。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 每个对象类型分支至少生成一个设置注释的成功路径样本和一个移除注释（IS NULL）的成功路径样本。
- 对需要前置依赖对象（表、函数、类型等）的分支，必须先创建前置对象再执行 COMMENT。
- 对 COMMENT ON ROLE 分支：必须覆盖 superuser 对 superuser 角色、CREATEROLE + ADMIN OPTION、无权限失败的路径。
- 对 COMMENT ON ACCESS METHOD 分支：必须覆盖 superuser 成功、非 superuser 失败的路径。
- 对 COLUMN 分支：必须使用 relation_name.column_name 格式。
- 对 CONSTRAINT 分支：必须使用 constraint_name ON table_name 或 constraint_name ON DOMAIN domain_name 格式。
- 对 FUNCTION/PROCEDURE/AGGREGATE/ROUTINE 分支：签名中仅列出输入参数类型。
- 对 OPERATOR 分支：缺失参数使用 NONE。
- 失败路径必须使用预期失败包装，不得让单个失败样本中断整批 SQL 执行。
- 成功路径必须包含验证语句（obj_description / col_description / shobj_description），并在生命周期末尾清理对象和注释。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- object_type 是主覆盖轴，37 种分支全量覆盖。
- privilege_level 挂靠到代表性分支（TABLE、COLUMN、ROLE、ACCESS METHOD、FUNCTION）的样本上轮转注入。
- comment_action（设置/移除）在每个主要分支上轮转覆盖。
- identifier_format 挂靠到对应分支类型的代表性样本上。
- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限、schema 或 role 的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上。

## 规模控制规则

- 优先保证：
  - 所有 37 种对象类型分支全覆盖
  - 设置注释 / 移除注释路径全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖（owner/superuser/non_owner/CREATEROLE）
- 次优先保证：
  - 有复合标识格式的分支（COLUMN、CONSTRAINT、OPERATOR、AGGREGATE 等）的标识形态代表性覆盖
  - 共享对象（DATABASE、ROLE、TABLESPACE）的注释可见性覆盖
  - TRANSFORM、CAST、LARGE OBJECT 等特殊分支的完整覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: comment
  skill_name: comment
  official_source: https://www.postgresql.org/docs/16/sql-comment.html
  statement:
    key: comment
    name: COMMENT ON
    aliases:
    - comment
    - COMMENT ON
    - COMMENT
    purpose: COMMENT — define or change the comment of an object
  syntax_templates:
  - "COMMENT ON\n{\n  ACCESS METHOD object_name |\n  AGGREGATE aggregate_name\
    \ ( aggregate_signature ) |\n  CAST (source_type AS target_type) |\n  COLLATION\
    \ object_name |\n  COLUMN relation_name.column_name |\n  CONSTRAINT constraint_name\
    \ ON table_name |\n  CONSTRAINT constraint_name ON DOMAIN domain_name |\n  CONVERSION\
    \ object_name |\n  DATABASE object_name |\n  DOMAIN object_name |\n  EXTENSION\
    \ object_name |\n  EVENT TRIGGER object_name |\n  FOREIGN DATA WRAPPER object_name\
    \ |\n  FOREIGN TABLE object_name |\n  FUNCTION function_name [ ( [ [ argmode\
    \ ] [ argname ] argtype [, ...] ] ) ] |\n  INDEX object_name |\n  LARGE OBJECT\
    \ large_object_oid |\n  MATERIALIZED VIEW object_name |\n  OPERATOR operator_name\
    \ (left_type, right_type) |\n  OPERATOR CLASS object_name USING index_method\
    \ |\n  OPERATOR FAMILY object_name USING index_method |\n  POLICY policy_name\
    \ ON table_name |\n  [ PROCEDURAL ] LANGUAGE object_name |\n  PROCEDURE procedure_name\
    \ [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |\n  PUBLICATION object_name\
    \ |\n  ROLE object_name |\n  ROUTINE routine_name [ ( [ [ argmode ] [ argname\
    \ ] argtype [, ...] ] ) ] |\n  RULE rule_name ON table_name |\n  SCHEMA object_name\
    \ |\n  SEQUENCE object_name |\n  SERVER object_name |\n  STATISTICS object_name\
    \ |\n  SUBSCRIPTION object_name |\n  TABLE object_name |\n  TABLESPACE object_name\
    \ |\n  TEXT SEARCH CONFIGURATION object_name |\n  TEXT SEARCH DICTIONARY object_name\
    \ |\n  TEXT SEARCH PARSER object_name |\n  TEXT SEARCH TEMPLATE object_name |\n\
    \  TRANSFORM FOR type_name LANGUAGE lang_name |\n  TRIGGER trigger_name ON table_name\
    \ |\n  TYPE object_name |\n  VIEW object_name\n} IS { string_literal | NULL }"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - object_type
    - comment_action
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - privilege_level
    - object_state
    - identifier_format
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - object_name_shape
    - column_name_shape
    - constraint_name_shape
    - function_signature_shape
    - operator_signature_shape
    - comment_text_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - prerequisite_object
    - schema_privilege
    - role_privilege
    - shared_object_scope
  - tier: T5
    name: 异常与边界因子
    factors:
    - object_not_exist
    - privilege_denied
    - wrong_identifier_format
    - cast_type_not_exist
    - aggregate_signature_invalid
    - operator_none_misuse
    - transform_type_or_lang_not_exist
    - large_object_oid_invalid
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification_mode
    - cleanup_mode
  factors:
    object_type:
      label: 可注释对象类型
      importance: important
      values:
      - key: access_method
        label: ACCESS METHOD object_name
      - key: aggregate
        label: AGGREGATE aggregate_name (aggregate_signature)
      - key: cast
        label: CAST (source_type AS target_type)
      - key: collation
        label: COLLATION object_name
      - key: column
        label: COLUMN relation_name.column_name
      - key: constraint_on_table
        label: CONSTRAINT constraint_name ON table_name
      - key: constraint_on_domain
        label: CONSTRAINT constraint_name ON DOMAIN domain_name
      - key: conversion
        label: CONVERSION object_name
      - key: database
        label: DATABASE object_name
      - key: domain
        label: DOMAIN object_name
      - key: extension
        label: EXTENSION object_name
      - key: event_trigger
        label: EVENT TRIGGER object_name
      - key: foreign_data_wrapper
        label: FOREIGN DATA WRAPPER object_name
      - key: foreign_table
        label: FOREIGN TABLE object_name
      - key: function
        label: FUNCTION function_name [(arg types)]
      - key: index
        label: INDEX object_name
      - key: large_object
        label: LARGE OBJECT large_object_oid
      - key: materialized_view
        label: MATERIALIZED VIEW object_name
      - key: operator
        label: OPERATOR operator_name (left_type, right_type)
      - key: operator_class
        label: OPERATOR CLASS object_name USING index_method
      - key: operator_family
        label: OPERATOR FAMILY object_name USING index_method
      - key: policy
        label: POLICY policy_name ON table_name
      - key: procedural_language
        label: "[ PROCEDURAL ] LANGUAGE object_name"
      - key: procedure
        label: PROCEDURE procedure_name [(arg types)]
      - key: publication
        label: PUBLICATION object_name
      - key: role
        label: ROLE object_name
      - key: routine
        label: ROUTINE routine_name [(arg types)]
      - key: rule
        label: RULE rule_name ON table_name
      - key: schema
        label: SCHEMA object_name
      - key: sequence
        label: SEQUENCE object_name
      - key: server
        label: SERVER object_name
      - key: statistics
        label: STATISTICS object_name
      - key: subscription
        label: SUBSCRIPTION object_name
      - key: table
        label: TABLE object_name
      - key: tablespace
        label: TABLESPACE object_name
      - key: text_search_configuration
        label: TEXT SEARCH CONFIGURATION object_name
      - key: text_search_dictionary
        label: TEXT SEARCH DICTIONARY object_name
      - key: text_search_parser
        label: TEXT SEARCH PARSER object_name
      - key: text_search_template
        label: TEXT SEARCH TEMPLATE object_name
      - key: transform
        label: TRANSFORM FOR type_name LANGUAGE lang_name
      - key: trigger
        label: TRIGGER trigger_name ON table_name
      - key: type
        label: TYPE object_name
      - key: view
        label: VIEW object_name
    comment_action:
      label: 注释动作
      importance: important
      values:
      - key: set_comment
        label: 设置 string_literal 注释
      - key: remove_comment_null
        label: 设置 IS NULL 移除注释
      - key: remove_comment_empty
        label: 设置 IS '' 移除注释
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - object_owner
      - non_owner
      - superuser
      - createrole_with_admin
    object_state:
      label: 目标对象状态
      importance: non_important
      values:
      - object_exists
      - object_not_exists
    identifier_format:
      label: 标识符格式
      importance: non_important
      values:
      - simple_name
      - schema_qualified
      - composite_format_column
      - composite_format_constraint
      - composite_format_operator
      - composite_format_aggregate
    object_name_shape:
      label: 对象名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified_id
      - reserved_word_as_name
    column_name_shape:
      label: 列名称形态
      importance: non_important
      values:
      - simple_column_name
      - quoted_column_name
    constraint_name_shape:
      label: 约束名称形态
      importance: non_important
      values:
      - simple_constraint_name
      - quoted_constraint_name
    function_signature_shape:
      label: 函数签名形态
      importance: non_important
      values:
      - no_args
      - single_arg_type
      - multiple_arg_types
      - wildcard_star
    operator_signature_shape:
      label: 运算符签名形态
      importance: non_important
      values:
      - both_types_specified
      - one_none_left
      - one_none_right
    comment_text_shape:
      label: 注释文本形态
      importance: non_important
      values:
      - short_literal
      - long_literal
      - empty_string_literal
      - null_literal
      - special_chars_literal
    prerequisite_object:
      label: 前置依赖对象存在性
      importance: non_important
      values:
      - prerequisite_exists
      - prerequisite_not_exists
    schema_privilege:
      label: schema 权限
      importance: non_important
      values:
      - has_schema_privilege
      - lacks_schema_privilege
    role_privilege:
      label: 角色权限
      importance: non_important
      values:
      - owner
      - createrole_with_admin_option
      - no_privilege
    shared_object_scope:
      label: 共享对象可见性
      importance: non_important
      values:
      - globally_visible
      - locally_visible
    object_not_exist:
      label: 目标对象不存在
      importance: non_important
      values:
      - object_exists
      - object_not_exists
    privilege_denied:
      label: 非 owner 尝试注释
      importance: non_important
      values:
      - owner_success
      - non_owner_failure
      - superuser_success
    wrong_identifier_format:
      label: 标识格式错误
      importance: non_important
      values:
      - correct_format
      - missing_relation_for_column
      - missing_on_for_constraint
    cast_type_not_exist:
      label: CAST 类型不存在
      importance: non_important
      values:
      - both_types_exist
      - source_type_not_exist
      - target_type_not_exist
    aggregate_signature_invalid:
      label: AGGREGATE 签名不匹配
      importance: non_important
      values:
      - signature_matches
      - signature_mismatch
    operator_none_misuse:
      label: OPERATOR NONE 使用不当
      importance: non_important
      values:
      - correct_none_usage
      - misplaced_none
    transform_type_or_lang_not_exist:
      label: TRANSFORM 类型或语言不存在
      importance: non_important
      values:
      - both_exist
      - type_not_exist
      - lang_not_exist
    large_object_oid_invalid:
      label: LARGE OBJECT OID 无效
      importance: non_important
      values:
      - valid_oid
      - nonexistent_oid
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - obj_description_query
      - col_description_query
      - shobj_description_query
      - psql_dd_command
      - catalog_query_pg_description
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_prerequisite_object
      - comment_is_null_cleanup
      - cascade_drop
  defaults:
    expected_status: success
    object_type: table
    comment_action: set_comment
    object_state: object_exists
    privilege_level: object_owner
  coverage_policy:
    main_combination_axes:
    - object_type
    - comment_action
    - expected_status
    non_main_factors:
    - privilege_level
    - object_state
    - identifier_format
    - object_name_shape
    - column_name_shape
    - constraint_name_shape
    - function_signature_shape
    - operator_signature_shape
    - comment_text_shape
    - prerequisite_object
    - schema_privilege
    - role_privilege
    - shared_object_scope
    - object_not_exist
    - privilege_denied
    - wrong_identifier_format
    - cast_type_not_exist
    - aggregate_signature_invalid
    - operator_none_misuse
    - transform_type_or_lang_not_exist
    - large_object_oid_invalid
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - object_type
  rendering:
    statement_template: "COMMENT ON {object_type} {object_identifier} IS {comment_text}"
    verification_query_template: "SELECT obj_description('{object_identifier_oid}')"
    factor_value_bindings: {}
```
