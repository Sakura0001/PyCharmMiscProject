# 技能：DROP ROUTINE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droproutine.html

```sql
DROP ROUTINE [ IF EXISTS ] name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] [, ...]
    [ CASCADE | RESTRICT ]
```

**重要约束：**
- DROP ROUTINE 是函数、过程和聚合的通用删除语句。DROP FUNCTION、DROP PROCEDURE、DROP AGGREGATE 是等效的别名。
- DROP ROUTINE 不涉及表/列/索引组合。
- CASCADE 会自动删除依赖此 routine 的所有对象（如触发器、视图、其他 routine）；RESTRICT（默认）在有依赖对象时失败。
- 参数签名用于区分同名但参数不同的 routine 重载。

## 语句作用

官方说明：DROP ROUTINE — remove a routine

该 reference 关注 routine 删除语句的 IF EXISTS 行为、CASCADE/RESTRICT 行为、参数签名识别、权限边界和成功/失败路径。DROP ROUTINE 是函数/过程/聚合的通用包装器。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP ROUTINE / DROP ROUTINE IF EXISTS / CASCADE / RESTRICT）
- routine_existence：目标 routine 存在状态
- expected_status：预期结果

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句行为
- cascade_restrict_clause：CASCADE / RESTRICT 子句行为
- routine_type：routine 对象类型（function / procedure / aggregate）
- arg_signature_disambiguation：参数签名消除重载歧义
- privilege_context：权限上下文
- multi_target：多目标删除行为

### T3：对象名与输入形态因子
- routine_name_shape：routine 名标识符形态
- arg_signature_shape：参数签名形态

### T4：依赖对象与环境因子
- **DROP ROUTINE 不涉及表/列/索引组合。**
- executor_privilege：执行者权限上下文
- dependent_objects：依赖对象状态（触发器、视图等）

### T5：异常与边界因子
- nonexistent_routine：routine 不存在
- privilege_insufficient：权限不足
- dependent_object_conflict：依赖对象冲突（RESTRICT 失败）
- overloaded_routine_ambiguity：重载 routine 参数签名歧义
- wrong_argument_types：参数签名不匹配

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 routine 存在/不存在、IF EXISTS、CASCADE/RESTRICT、参数签名识别等核心状态。
- 覆盖 function / procedure / aggregate 三种 routine 对象类型。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 routine 存在时的成功删除路径、routine 不存在时的失败路径。
- IF EXISTS 时，必须覆盖不存在 routine 的代表性 no-op 路径。
- CASCADE / RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- 必须覆盖重载 routine 的参数签名消除歧义行为。
- 每个样本必须包含明确的前置对象准备、目标 DROP ROUTINE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或依赖对象的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - routine 存在/不存在全覆盖
  - CASCADE / RESTRICT 全覆盖
  - 成功/失败路径全覆盖
  - function / procedure / aggregate 类型全覆盖
- 次优先保证：
  - IF EXISTS 行为代表性覆盖
  - 参数签名消除重载歧义代表性覆盖
  - 依赖对象冲突代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: routine
  skill_name: drop_routine
  official_source: https://www.postgresql.org/docs/16/sql-droproutine.html
  statement:
    key: drop_routine
    name: DROP ROUTINE
    aliases:
    - drop_routine
    - DROP ROUTINE
    - drop_function
    - DROP FUNCTION
    - drop_procedure
    - DROP PROCEDURE
    - drop_aggregate
    - DROP AGGREGATE
    purpose: DROP ROUTINE — remove a routine
  syntax_templates:
  - "DROP ROUTINE [ IF EXISTS ] name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] [, ...]\n    [ CASCADE | RESTRICT ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - routine_existence
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_exists_clause
    - cascade_restrict_clause
    - routine_type
    - arg_signature_disambiguation
    - privilege_context
    - multi_target
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - routine_name_shape
    - arg_signature_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - dependent_objects
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_routine
    - privilege_insufficient
    - dependent_object_conflict
    - overloaded_routine_ambiguity
    - wrong_argument_types
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
      - key: branch_drop_routine
        label: DROP ROUTINE name
      - key: branch_drop_routine_if_exists
        label: DROP ROUTINE IF EXISTS name
      - key: branch_drop_routine_cascade
        label: DROP ROUTINE name CASCADE
      - key: branch_drop_routine_restrict
        label: DROP ROUTINE name RESTRICT
    routine_existence:
      label: 目标 routine 存在状态
      importance: important
      values:
      - routine_exists
      - routine_not_exists
      - routine_exists_as_function
      - routine_exists_as_procedure
      - routine_exists_as_aggregate
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句
      importance: important
      values:
      - without_if_exists
      - with_if_exists
    cascade_restrict_clause:
      label: CASCADE / RESTRICT 子句
      importance: important
      values:
      - no_clause_default_restrict
      - cascade
      - restrict
    routine_type:
      label: routine 对象类型
      importance: important
      values:
      - function
      - procedure
      - aggregate
    arg_signature_disambiguation:
      label: 参数签名消除重载歧义
      importance: non_important
      values:
      - no_args_no_ambiguity
      - single_arg_with_signature
      - overloaded_requires_signature
      - signature_mismatch
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser
      - owner_of_routine
      - non_owner_no_privilege
    multi_target:
      label: 多目标删除行为
      importance: non_important
      values:
      - single_target
      - multi_target_all_exist
      - multi_target_some_not_exist
    routine_name_shape:
      label: routine 名标识符形态
      importance: non_important
      values:
      - simple_name
      - schema_qualified_name
      - quoted_name
      - non_existing_name
    arg_signature_shape:
      label: 参数签名形态
      importance: non_important
      values:
      - no_args
      - single_arg
      - multiple_args
      - with_argmode
      - with_argname
      - empty_arg_list
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - owner
      - non_owner_no_privilege
    dependent_objects:
      label: 依赖对象状态
      importance: non_important
      values:
      - no_dependent_objects
      - has_dependent_trigger
      - has_dependent_view
      - has_dependent_routine
    nonexistent_routine:
      label: routine 不存在
      importance: non_important
      values:
      - routine_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_owner_dropping_routine
    dependent_object_conflict:
      label: 依赖对象冲突
      importance: non_important
      values:
      - restrict_with_dependent_fails
      - cascade_with_dependent_succeeds
    overloaded_routine_ambiguity:
      label: 重载 routine 参数签名歧义
      importance: non_important
      values:
      - ambiguous_without_signature
      - resolved_with_signature
    wrong_argument_types:
      label: 参数签名不匹配
      importance: non_important
      values:
      - signature_does_not_match_any_routine
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_proc_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_routine
      - drop_function
      - drop_procedure
      - drop_aggregate
      - cascade_drop_with_dependents
  defaults:
    expected_status: success
    cascade_restrict_clause: no_clause_default_restrict
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - routine_existence
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict_clause
    - routine_type
    - arg_signature_disambiguation
    - privilege_context
    - multi_target
    - routine_name_shape
    - arg_signature_shape
    - executor_privilege
    - dependent_objects
    - nonexistent_routine
    - privilege_insufficient
    - dependent_object_conflict
    - overloaded_routine_ambiguity
    - wrong_argument_types
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - routine_existence
  rendering:
    statement_template: "DROP ROUTINE [ IF EXISTS ] {name} [ ( {arg_signature} ) ] [, ...] [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT proname FROM pg_proc WHERE proname = '{name}'"
    factor_value_bindings:
      if_exists_clause:
        without_if_exists: ""
        with_if_exists: "IF EXISTS"
      cascade_restrict_clause:
        no_clause_default_restrict: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
```
