# 技能：SECURITY LABEL

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-security-label.html

```sql
SECURITY LABEL [ FOR provider ] ON
{
  TABLE object_name |
  COLUMN table_name.column_name |
  AGGREGATE aggregate_name ( aggregate_signature ) |
  DATABASE object_name |
  DOMAIN object_name |
  EVENT TRIGGER object_name |
  FOREIGN TABLE object_name |
  FUNCTION function_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  LARGE OBJECT large_object_oid |
  MATERIALIZED VIEW object_name |
  [ PROCEDURAL ] LANGUAGE object_name |
  PROCEDURE procedure_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  PUBLICATION object_name |
  ROLE object_name |
  ROUTINE routine_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  SCHEMA object_name |
  SEQUENCE object_name |
  SUBSCRIPTION object_name |
  TABLESPACE object_name |
  TYPE object_name |
  VIEW object_name
} IS { string_literal | NULL }

where aggregate_signature is:

* |
[ argmode ] [ argname ] argtype [ , ... ] |
[[ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]
```

**重要约束：**
- SECURITY LABEL 需要 superuser 权限或由注册的 provider 扩展授予的 SECURITY LABEL 权限。
- 每个对象每个 provider 只能有一个安全标签；重复设置会替换旧标签。
- IS NULL 会移除对象上的安全标签。
- FOR provider 必须指定已注册的标签 provider（如 sepgsql）；否则使用默认 provider（seclabel_provider 配置参数）。
- 支持的对象类型共 19 种：TABLE、COLUMN、AGGREGATE、DATABASE、DOMAIN、EVENT TRIGGER、FOREIGN TABLE、FUNCTION、LARGE OBJECT、MATERIALIZED VIEW、LANGUAGE、PROCEDURE、PUBLICATION、ROLE、ROUTINE、SCHEMA、SEQUENCE、SUBSCRIPTION、TABLESPACE、TYPE、VIEW。

## 语句作用

官方说明：SECURITY LABEL — define or change a security label applied to an object

该 reference 关注安全标签语句的 19 种对象类型、FOR provider 子句、标签值形态（string_literal / NULL）、权限边界和成功/失败路径。SECURITY LABEL 需要 superuser 或已注册 provider 的授权。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（19 种 ON 对象类型分支）
- object_existence：目标对象存在状态
- expected_status：预期结果

### T2：重要行为因子
- object_type：ON 对象类型
- for_provider_clause：FOR provider 子句形态
- label_value：标签值形态（string_literal / NULL）
- aggregate_signature：聚合签名形态（AGGREGATE 分支）
- routine_signature：函数/过程/routine 签名形态

### T3：对象名与输入形态因子
- object_name_shape：对象名标识符形态
- provider_name_shape：provider 名形态
- column_name_shape：列名形态（COLUMN 分支）
- label_string_shape：标签字符串形态

### T4：依赖对象与环境因子
- **SECURITY LABEL 涉及多种对象类型（表、列、函数等），需要覆盖这些对象的代表性存在状态。**
- executor_privilege：执行者权限上下文
- provider_registration：provider 注册状态
- prerequisite_object：前置依赖对象存在状态

### T5：异常与边界因子
- nonexistent_object：目标对象不存在
- privilege_insufficient：权限不足
- unregistered_provider：provider 未注册
- invalid_label_for_provider：标签值不被 provider 接受
- duplicate_label_same_provider：重复设置同一 provider 的标签

### T6：验证与清理因子
- verification_mode：验证方式（pg_seclabel 目录查询）
- cleanup_mode：清理方式（SECURITY LABEL ... IS NULL / DROP 对象）

## 覆盖策略

- 覆盖 19 种对象类型的代表性分支（不必对所有 19 种做笛卡尔积，但每种至少出现一次）。
- 覆盖 FOR provider 和默认 provider 的代表性取值。
- 覆盖 IS string_literal 和 IS NULL 的代表性取值。
- T1 因子做笛卡尔积覆盖（按对象类型分组做局部笛卡尔积）；T2 因子按规模控制策略参与组合。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖所有 19 种对象类型的代表性成功/失败路径。
- 成功路径必须包含可通过 pg_seclabel 目录验证的标签存在性检查。
- IS NULL 路径必须覆盖标签移除行为。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 每个样本必须包含明确的前置对象准备、目标 SECURITY LABEL 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- provider 未注册时的失败路径必须覆盖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或 provider 注册状态的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 19 种对象类型各至少一个成功/失败样本
  - FOR provider 和默认 provider 覆盖
  - IS string_literal / IS NULL 覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - 聚合签名代表性覆盖
  - 函数/过程/routine 签名代表性覆盖
  - provider 注册状态代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: security_label
  skill_name: security_label
  official_source: https://www.postgresql.org/docs/16/sql-security-label.html
  statement:
    key: security_label
    name: SECURITY LABEL
    aliases:
    - security_label
    - SECURITY LABEL
    purpose: SECURITY LABEL — define or change a security label applied to an object
  syntax_templates:
  - "SECURITY LABEL [ FOR provider ] ON\n{\n  TABLE object_name |\n  COLUMN table_name.column_name |\
    \n  AGGREGATE aggregate_name ( aggregate_signature ) |\n  DATABASE object_name |\n  DOMAIN\
    \ object_name |\n  EVENT TRIGGER object_name |\n  FOREIGN TABLE object_name |\n\
    \  FUNCTION function_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |\n\
    \  LARGE OBJECT large_object_oid |\n  MATERIALIZED VIEW object_name |\n  [ PROCEDURAL\
    \ ] LANGUAGE object_name |\n  PROCEDURE procedure_name [ ( [ [ argmode ] [ argname\
    \ ] argtype [, ...] ] ) ] |\n  PUBLICATION object_name |\n  ROLE object_name |\n\
    \  ROUTINE routine_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |\n\
    \  SCHEMA object_name |\n  SEQUENCE object_name |\n  SUBSCRIPTION object_name |\n\
    \  TABLESPACE object_name |\n  TYPE object_name |\n  VIEW object_name\n} IS {\
    \ string_literal | NULL }"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - object_existence
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - object_type
    - for_provider_clause
    - label_value
    - aggregate_signature
    - routine_signature
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - object_name_shape
    - provider_name_shape
    - column_name_shape
    - label_string_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - provider_registration
    - prerequisite_object
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_object
    - privilege_insufficient
    - unregistered_provider
    - invalid_label_for_provider
    - duplicate_label_same_provider
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
      - key: branch_on_table
        label: SECURITY LABEL ON TABLE
      - key: branch_on_column
        label: SECURITY LABEL ON COLUMN
      - key: branch_on_aggregate
        label: SECURITY LABEL ON AGGREGATE
      - key: branch_on_database
        label: SECURITY LABEL ON DATABASE
      - key: branch_on_domain
        label: SECURITY LABEL ON DOMAIN
      - key: branch_on_event_trigger
        label: SECURITY LABEL ON EVENT TRIGGER
      - key: branch_on_foreign_table
        label: SECURITY LABEL ON FOREIGN TABLE
      - key: branch_on_function
        label: SECURITY LABEL ON FUNCTION
      - key: branch_on_large_object
        label: SECURITY LABEL ON LARGE OBJECT
      - key: branch_on_materialized_view
        label: SECURITY LABEL ON MATERIALIZED VIEW
      - key: branch_on_language
        label: SECURITY LABEL ON LANGUAGE
      - key: branch_on_procedure
        label: SECURITY LABEL ON PROCEDURE
      - key: branch_on_publication
        label: SECURITY LABEL ON PUBLICATION
      - key: branch_on_role
        label: SECURITY LABEL ON ROLE
      - key: branch_on_routine
        label: SECURITY LABEL ON ROUTINE
      - key: branch_on_schema
        label: SECURITY LABEL ON SCHEMA
      - key: branch_on_sequence
        label: SECURITY LABEL ON SEQUENCE
      - key: branch_on_subscription
        label: SECURITY LABEL ON SUBSCRIPTION
      - key: branch_on_tablespace
        label: SECURITY LABEL ON TABLESPACE
      - key: branch_on_type
        label: SECURITY LABEL ON TYPE
      - key: branch_on_view
        label: SECURITY LABEL ON VIEW
    object_existence:
      label: 目标对象存在状态
      importance: important
      values:
      - object_exists
      - object_not_exists
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    object_type:
      label: ON 对象类型
      importance: important
      values:
      - table
      - column
      - aggregate
      - database
      - domain
      - event_trigger
      - foreign_table
      - function
      - large_object
      - materialized_view
      - language
      - procedure
      - publication
      - role
      - routine
      - schema
      - sequence
      - subscription
      - tablespace
      - type
      - view
    for_provider_clause:
      label: FOR provider 子句形态
      importance: non_important
      values:
      - omitted_default_provider
      - explicit_provider
    label_value:
      label: 标签值形态
      importance: non_important
      values:
      - string_literal
      - null_removes_label
    aggregate_signature:
      label: 聚合签名形态
      importance: non_important
      values:
      - star_wildcard
      - single_arg_type
      - multiple_arg_types
      - with_order_by
    routine_signature:
      label: 函数/过程/routine 签名形态
      importance: non_important
      values:
      - no_args
      - single_arg
      - multiple_args
    object_name_shape:
      label: 对象名标识符形态
      importance: non_important
      values:
      - simple_name
      - schema_qualified_name
      - quoted_name
      - non_existing_name
    provider_name_shape:
      label: provider 名形态
      importance: non_important
      values:
      - registered_provider
      - unregistered_provider
    column_name_shape:
      label: 列名形态（COLUMN 分支）
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - nonexistent_column
    label_string_shape:
      label: 标签字符串形态
      importance: non_important
      values:
      - valid_label
      - empty_string
      - special_characters_label
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - non_superuser_no_provider_privilege
    provider_registration:
      label: provider 注册状态
      importance: non_important
      values:
      - provider_registered
      - provider_not_registered
    prerequisite_object:
      label: 前置依赖对象存在状态
      importance: non_important
      values:
      - object_exists
      - object_not_exists
    nonexistent_object:
      label: 目标对象不存在
      importance: non_important
      values:
      - target_object_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_without_provider_privilege
    unregistered_provider:
      label: provider 未注册
      importance: non_important
      values:
      - provider_not_registered_failure
    invalid_label_for_provider:
      label: 标签值不被 provider 接受
      importance: non_important
      values:
      - provider_rejects_label
    duplicate_label_same_provider:
      label: 重复设置同一 provider 的标签
      importance: non_important
      values:
      - replaces_existing_label
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_seclabel_catalog_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - security_label_is_null
      - drop_object
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_existence
    - expected_status
    non_main_factors:
    - object_type
    - for_provider_clause
    - label_value
    - aggregate_signature
    - routine_signature
    - object_name_shape
    - provider_name_shape
    - column_name_shape
    - label_string_shape
    - executor_privilege
    - provider_registration
    - prerequisite_object
    - nonexistent_object
    - privilege_insufficient
    - unregistered_provider
    - invalid_label_for_provider
    - duplicate_label_same_provider
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_existence
  rendering:
    statement_template: "SECURITY LABEL [ FOR {provider} ] ON {object_type} {object_name} IS {label_value}"
    verification_query_template: "SELECT label FROM pg_seclabel WHERE objoid = '{object_oid}' AND provider = '{provider}'"
    factor_value_bindings:
      label_value:
        string_literal: "'{label_string}'"
        null_removes_label: "NULL"
```
