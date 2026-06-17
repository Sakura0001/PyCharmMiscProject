# 技能：ALTER ROUTINE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterroutine.html

```sql
ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    action [ ... ] [ RESTRICT ]
ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    RENAME TO new_name
ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    SET SCHEMA new_schema
ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    [ NO ] DEPENDS ON EXTENSION extension_name

where action is one of:

    IMMUTABLE | STABLE | VOLATILE
    [ NOT ] LEAKPROOF
    [ EXTERNAL ] SECURITY INVOKER | [ EXTERNAL ] SECURITY DEFINER
    PARALLEL { UNSAFE | RESTRICTED | SAFE }
    COST execution_cost
    ROWS result_rows
    SET configuration_parameter { TO | = } { value | DEFAULT }
    SET configuration_parameter FROM CURRENT
    RESET configuration_parameter
    RESET ALL
```

**重要约束：**
- ALTER ROUTINE 是函数、过程和聚合的通用修改语句。ALTER FUNCTION、ALTER PROCEDURE、ALTER AGGREGATE 是等效的别名。
- ALTER ROUTINE 不涉及表/列/索引组合。
- LEAKPROOF 属性仅 superuser 可设置。
- SECURITY DEFINER 函数以定义者权限执行，需要特别注意安全边界。
- DEPENDS ON EXTENSION 标记 routine 与扩展的依赖关系。

## 语句作用

官方说明：ALTER ROUTINE — change the definition of a routine

该 reference 关注 routine 修改语句的 5 个语法分支（action 属性变更 / RENAME / OWNER TO / SET SCHEMA / DEPENDS ON EXTENSION）、属性选项组合、权限边界和成功/失败路径。ALTER ROUTINE 是函数/过程/聚合的通用包装器。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（5 个 synopsis 分支）
- routine_state：目标 routine 存在状态
- expected_status：预期结果

### T2：重要行为因子
- action_option：属性选项（IMMUTABLE / STABLE / VOLATILE / LEAKPROOF / SECURITY / PARALLEL / COST / ROWS / SET / RESET）
- routine_type：routine 对象类型（function / procedure / aggregate）
- restrict_clause：RESTRICT 子句
- owner_to_shape：OWNER TO 子句形态
- schema_change：SET SCHEMA 行为
- extension_dependency：DEPENDS ON EXTENSION 行为

### T3：对象名与输入形态因子
- routine_name_shape：routine 名标识符形态
- arg_signature：参数签名形态
- new_name_shape：新名形态（RENAME 分支）
- new_schema_shape：新 schema 形态（SET SCHEMA 分支）

### T4：依赖对象与环境因子
- **ALTER ROUTINE 不涉及表/列/索引组合。**
- executor_privilege：执行者权限上下文
- extension_dependency_state：扩展依赖状态

### T5：异常与边界因子
- nonexistent_routine：routine 不存在
- privilege_insufficient：权限不足（非 owner / 非 superuser 设置 LEAKPROOF）
- nonexistent_schema：schema 不存在（SET SCHEMA）
- nonexistent_extension：扩展不存在（DEPENDS ON EXTENSION）
- nonexistent_owner：owner 不存在（OWNER TO）
- conflicting_routine_signature：参数签名冲突

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖所有 5 个 ALTER ROUTINE 语法分支。
- 覆盖 action 选项的代表性取值（每个 action 至少出现一次）。
- 覆盖 function / procedure / aggregate 三种 routine 对象类型。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 routine，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 routine 存在时的成功修改路径、routine 不存在时的失败路径。
- action / RENAME / OWNER TO / SET SCHEMA / DEPENDS ON EXTENSION 各分支需要保持独立归因。
- 需要 superuser 权限的分支（LEAKPROOF），必须在生命周期计划中显式标注环境依赖。
- 每个样本必须包含明确的前置对象准备、目标 ALTER ROUTINE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或扩展依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有 5 个语法分支全覆盖
  - routine 存在/不存在全覆盖
  - 成功/失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - action 选项代表性覆盖
  - function / procedure / aggregate 类型代表性覆盖
  - RESTRICT 子句代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: routine
  skill_name: alter_routine
  official_source: https://www.postgresql.org/docs/16/sql-alterroutine.html
  statement:
    key: alter_routine
    name: ALTER ROUTINE
    aliases:
    - alter_routine
    - ALTER ROUTINE
    - alter_function
    - ALTER FUNCTION
    - alter_procedure
    - ALTER PROCEDURE
    - alter_aggregate
    - ALTER AGGREGATE
    purpose: ALTER ROUTINE — change the definition of a routine
  syntax_templates:
  - "ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]\n    action [ ... ] [ RESTRICT ]"
  - "ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]\n    RENAME TO new_name"
  - "ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]\n    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]\n    SET SCHEMA new_schema"
  - "ALTER ROUTINE name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]\n    [ NO ] DEPENDS ON EXTENSION extension_name"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - routine_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - action_option
    - routine_type
    - restrict_clause
    - owner_to_shape
    - schema_change
    - extension_dependency
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - routine_name_shape
    - arg_signature
    - new_name_shape
    - new_schema_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - extension_dependency_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_routine
    - privilege_insufficient
    - nonexistent_schema
    - nonexistent_extension
    - nonexistent_owner
    - conflicting_routine_signature
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
      - key: branch_action
        label: ALTER ROUTINE name action [ ... ] [ RESTRICT ]
      - key: branch_rename
        label: ALTER ROUTINE name RENAME TO new_name
      - key: branch_owner_to
        label: ALTER ROUTINE name OWNER TO new_owner
      - key: branch_set_schema
        label: ALTER ROUTINE name SET SCHEMA new_schema
      - key: branch_depends_on_extension
        label: ALTER ROUTINE name [ NO ] DEPENDS ON EXTENSION extension_name
    routine_state:
      label: 目标 routine 存在状态
      importance: important
      values:
      - exists
      - non_existent
      - exists_as_function
      - exists_as_procedure
      - exists_as_aggregate
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    action_option:
      label: 属性选项
      importance: non_important
      values:
      - immutable
      - stable
      - volatile
      - leakproof
      - not_leakproof
      - security_invoker
      - security_definer
      - parallel_unsafe
      - parallel_restricted
      - parallel_safe
      - cost
      - rows
      - set_config_parameter
      - set_config_from_current
      - reset_config_parameter
      - reset_all
    routine_type:
      label: routine 对象类型
      importance: non_important
      values:
      - function
      - procedure
      - aggregate
    restrict_clause:
      label: RESTRICT 子句
      importance: non_important
      values:
      - omitted
      - restrict
    owner_to_shape:
      label: OWNER TO 子句形态
      importance: non_important
      values:
      - explicit_role_name
      - current_role_keyword
      - current_user_keyword
      - session_user_keyword
    schema_change:
      label: SET SCHEMA 行为
      importance: non_important
      values:
      - existing_schema
      - nonexistent_schema
    extension_dependency:
      label: DEPENDS ON EXTENSION 行为
      importance: non_important
      values:
      - depends_on_existing_extension
      - no_depends_removing_dependency
      - depends_on_nonexistent_extension
    routine_name_shape:
      label: routine 名标识符形态
      importance: non_important
      values:
      - simple_name
      - schema_qualified_name
      - quoted_name
      - non_existent_name
    arg_signature:
      label: 参数签名形态
      importance: non_important
      values:
      - no_args
      - single_arg
      - multiple_args
      - with_argmode
      - with_argname
      - mismatched_signature
    new_name_shape:
      label: 新名形态（RENAME 分支）
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - existing_name_conflict
    new_schema_shape:
      label: 新 schema 形态（SET SCHEMA 分支）
      importance: non_important
      values:
      - existing_schema
      - nonexistent_schema
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - owner_of_routine
      - non_owner_with_grant_option
      - non_owner_no_privilege
    extension_dependency_state:
      label: 扩展依赖状态
      importance: non_important
      values:
      - extension_exists
      - extension_not_exists
    nonexistent_routine:
      label: routine 不存在
      importance: non_important
      values:
      - routine_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_owner_altering_routine
      - non_superuser_setting_leakproof
      - non_superuser_setting_security_definer
    nonexistent_schema:
      label: schema 不存在
      importance: non_important
      values:
      - schema_does_not_exist
    nonexistent_extension:
      label: 扩展不存在
      importance: non_important
      values:
      - extension_does_not_exist
    nonexistent_owner:
      label: owner 不存在
      importance: non_important
      values:
      - owner_role_does_not_exist
    conflicting_routine_signature:
      label: 参数签名冲突
      importance: non_important
      values:
      - wrong_argument_types
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_proc_catalog
      - pg_aggregate_catalog
      - effect_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_routine
      - drop_function
      - drop_procedure
      - drop_aggregate
      - reset_config_parameter
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - routine_state
    - expected_status
    non_main_factors:
    - action_option
    - routine_type
    - restrict_clause
    - owner_to_shape
    - schema_change
    - extension_dependency
    - routine_name_shape
    - arg_signature
    - new_name_shape
    - new_schema_shape
    - executor_privilege
    - extension_dependency_state
    - nonexistent_routine
    - privilege_insufficient
    - nonexistent_schema
    - nonexistent_extension
    - nonexistent_owner
    - conflicting_routine_signature
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - routine_state
  rendering:
    statement_template: "ALTER ROUTINE {name} [ ( {arg_signature} ) ] {action_or_operation}"
    verification_query_template: "SELECT proname, prokind FROM pg_proc WHERE proname = '{name}'"
    factor_value_bindings: {}
```
