# 技能：CREATE POLICY

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createpolicy.html

```sql
CREATE POLICY name ON table_name
    [ AS { PERMISSIVE | RESTRICTIVE } ]
    [ FOR { ALL | SELECT | INSERT | UPDATE | DELETE } ]
    [ TO { role_name | PUBLIC | CURRENT_ROLE | CURRENT_USER | SESSION_USER } [, ...] ]
    [ USING ( using_expression ) ]
    [ WITH CHECK ( check_expression ) ]
```

PG16 关键约束：
- Policy 名称在同一个表内必须唯一，不同表可以使用相同的 policy 名称
- 默认 deny：如果 RLS 启用但没有适用的 policy，则所有行不可见也不可修改
- PERMISSIVE（默认）多个同类 policy 用 OR 组合；RESTRICTIVE 多个同类 policy 用 AND 组合
- 至少需要一个 PERMISSIVE policy 才能让行可见，仅 RESTRICTIVE policy 不够
- ALL policy 同时充当所有命令类型的 policy
- SELECT/DELETE 只能用 USING；INSERT 只能用 WITH CHECK；UPDATE 可以同时用 USING 和 WITH CHECK
- USING 返回 false/null 的行被静默过滤（不报错）；WITH CHECK 返回 false/null 导致命令中止报错
- 必须拥有目标表才能创建 policy
- 表必须先启用 RLS（ALTER TABLE ... ENABLE ROW LEVEL SECURITY）

## 语句作用

官方说明：CREATE POLICY — define a new row-level security policy for a table

该 reference 关注行级安全策略（RLS Policy）的定义，涉及表依赖但不需要覆盖列类型组合。Policy 的行为由策略类型（PERMISSIVE/RESTRICTIVE）、命令类型（ALL/SELECT/INSERT/UPDATE/DELETE）、角色目标（TO）和表达式（USING/WITH CHECK）决定，不涉及列类型变化。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE POLICY 单一顶层形式）
- policy_type：策略类型（PERMISSIVE / RESTRICTIVE）
- command_type：命令类型（ALL / SELECT / INSERT / UPDATE / DELETE）
- object_state：目标 policy 对象状态（不存在 / 已存在同名）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- role_target：TO 角色目标形态（PUBLIC / role_name / CURRENT_ROLE / CURRENT_USER / SESSION_USER / 多角色组合）
- using_expression：USING expression 形态（省略 / 指定）
- with_check_expression：WITH CHECK expression 形态（省略 / 指定）
- expression_compatibility：表达式与命令类型的兼容性（SELECT 无 WITH CHECK / INSERT 无 USING / UPDATE 两者 / DELETE 无 WITH CHECK）

### T3：对象名与输入形态因子
- policy_name_shape：policy 名称形态
- table_name_shape：目标表名称形态
- role_name_shape：角色名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（table_owner / non_owner / superuser）
- rls_enabled：目标表是否已启用 RLS
- table_existence：目标表存在性
- role_existence：TO 角色存在性

### T5：异常与边界因子
- duplicate_policy_name：同一表内重名冲突
- nonexistent_table：目标表不存在
- rls_not_enabled：目标表未启用 RLS
- privilege_denied：非 table owner 尝试创建
- select_with_check_conflict：SELECT policy 使用 WITH CHECK
- insert_with_using_conflict：INSERT policy 使用 USING
- only_restrictive_policy：仅有 RESTRICTIVE policy 导致默认 deny
- invalid_expression：USING/WITH CHECK 表达式非法（聚合函数、窗口函数）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE POLICY 单一语法分支中的所有可选子句组合（AS / FOR / TO / USING / WITH CHECK）。
- 覆盖所有 5 种命令类型（ALL / SELECT / INSERT / UPDATE / DELETE）。
- 覆盖 PERMISSIVE 和 RESTRICTIVE 两种策略类型。
- 不需要覆盖所有基表和所有列类型组合，Policy 行为不随列类型变化。
- 覆盖目标 policy 不存在/重名冲突路径。
- 覆盖成功路径与失败路径，包括权限边界和表达式兼容性边界。
- T1 因子做笛卡尔积覆盖；command_type 和 policy_type 做全量覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE POLICY 要求执行者是目标表的 owner，非 owner 路径属于失败路径。
- 目标表必须先启用 RLS（ALTER TABLE ... ENABLE ROW LEVEL SECURITY），未启用的路径需要显式标注前置条件。
- Policy 名称在同一个表内必须唯一，不同表可同名。
- SELECT policy 不能有 WITH CHECK 表达式，违反此限制的路径属于失败路径。
- INSERT policy 不能有 USING 表达式，违反此限制的路径属于失败路径。
- DELETE policy 不能有 WITH CHECK 表达式，违反此限制的路径属于失败路径。
- USING/WITH CHECK 表达式不能包含聚合函数或窗口函数，违反此限制的路径属于失败路径。
- 仅 RESTRICTIVE policy 不满足默认 deny 规则，需要至少一个 PERMISSIVE policy。
- 成功路径必须包含可验证的 policy 存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备（含表创建和 RLS 启用）、目标 CREATE POLICY 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- command_type 因子与 expression_compatibility 因子必须联动挂靠，确保 SELECT 无 WITH CHECK、INSERT 无 USING 等边界被覆盖。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- 与 RLS 启用前置条件相关的因子必须挂靠到满足前置条件的样本上。
- 仅 RESTRICTIVE policy 的默认 deny 边界必须独立挂靠到代表性样本上。

## 规模控制规则

- 优先保证官方语法分支、命令类型全覆盖（ALL/SELECT/INSERT/UPDATE/DELETE）、策略类型全覆盖（PERMISSIVE/RESTRICTIVE）、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 TO 角色目标形态、USING/WITH CHECK 表达式形态和表达式兼容性代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: policy
  skill_name: create_policy
  official_source: https://www.postgresql.org/docs/16/sql-createpolicy.html
  statement:
    key: create_policy
    name: CREATE POLICY
    aliases:
    - create_policy
    - CREATE POLICY
    purpose: CREATE POLICY — define a new row-level security policy for a table
  syntax_templates:
  - "CREATE POLICY name ON table_name\n    [ AS { PERMISSIVE | RESTRICTIVE } ]\n\
    \    [ FOR { ALL | SELECT | INSERT | UPDATE | DELETE } ]\n    [ TO { role_name\
    \ | PUBLIC | CURRENT_ROLE | CURRENT_USER | SESSION_USER } [, ...] ]\n    [ USING\
    \ ( using_expression ) ]\n    [ WITH CHECK ( check_expression ) ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - policy_type
    - command_type
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - role_target
    - using_expression
    - with_check_expression
    - expression_compatibility
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - policy_name_shape
    - table_name_shape
    - role_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - rls_enabled
    - table_existence
    - role_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_policy_name
    - nonexistent_table
    - rls_not_enabled
    - privilege_denied
    - select_with_check_conflict
    - insert_with_using_conflict
    - only_restrictive_policy
    - invalid_expression
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
      - key: branch_create_policy
        label: CREATE POLICY name ON table_name [ AS ] [ FOR ] [ TO ] [ USING ] [ WITH CHECK ]
    policy_type:
      label: 策略类型
      importance: important
      values:
      - permissive
      - restrictive
    command_type:
      label: 命令类型
      importance: important
      values:
      - ALL
      - SELECT
      - INSERT
      - UPDATE
      - DELETE
    object_state:
      label: 目标 policy 对象状态
      importance: important
      values:
      - not_exists
      - exists_same_table
      - exists_different_table
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    role_target:
      label: TO 角色目标形态
      importance: non_important
      values:
      - PUBLIC
      - single_role
      - multiple_roles
      - CURRENT_ROLE
      - CURRENT_USER
      - SESSION_USER
    using_expression:
      label: USING expression 形态
      importance: non_important
      values:
      - omitted
      - simple_boolean_expr
      - column_reference_expr
      - complex_expr
    with_check_expression:
      label: WITH CHECK expression 形态
      importance: non_important
      values:
      - omitted
      - simple_boolean_expr
      - column_reference_expr
      - complex_expr
    expression_compatibility:
      label: 表达式与命令类型兼容性
      importance: non_important
      values:
      - compatible_pairing
      - select_with_check_incompatible
      - insert_with_using_incompatible
      - delete_with_check_incompatible
    policy_name_shape:
      label: policy 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_as_name
      - duplicate_name_same_table
      - duplicate_name_different_table
    table_name_shape:
      label: 目标表名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified
      - nonexistent_table
    role_name_shape:
      label: 角色名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - PUBLIC_keyword
      - nonexistent_role
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - table_owner
      - non_owner
    rls_enabled:
      label: 目标表是否已启用 RLS
      importance: non_important
      values:
      - rls_enabled
      - rls_not_enabled
    table_existence:
      label: 目标表存在性
      importance: non_important
      values:
      - table_exists
      - table_not_exists
    role_existence:
      label: TO 角色存在性
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    duplicate_policy_name:
      label: 同一表内重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_table_same_name
    nonexistent_table:
      label: 目标表不存在
      importance: non_important
      values:
      - table_exists
      - table_missing
    rls_not_enabled:
      label: 目标表未启用 RLS
      importance: non_important
      values:
      - rls_enabled
      - rls_not_enabled
    privilege_denied:
      label: 非 table owner 尝试创建
      importance: non_important
      values:
      - owner_execution
      - non_owner_denied
      - superuser_execution
    select_with_check_conflict:
      label: SELECT policy 使用 WITH CHECK
      importance: non_important
      values:
      - compatible_no_with_check
      - incompatible_with_check
    insert_with_using_conflict:
      label: INSERT policy 使用 USING
      importance: non_important
      values:
      - compatible_no_using
      - incompatible_using
    only_restrictive_policy:
      label: 仅 RESTRICTIVE policy 导致默认 deny
      importance: non_important
      values:
      - has_permissive_policy
      - only_restrictive_no_permissive
    invalid_expression:
      label: USING/WITH CHECK 表达式非法
      importance: non_important
      values:
      - valid_expression
      - aggregate_in_expression
      - window_function_in_expression
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_policy
      - rls_behavior_test
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_policy
      - disable_rls_and_drop_policy
      - drop_table
  defaults:
    expected_status: success
    policy_type: permissive
    command_type: ALL
    object_state: not_exists
    role_target: PUBLIC
    using_expression: omitted
    with_check_expression: omitted
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - policy_type
    - command_type
    - object_state
    - expected_status
    non_main_factors:
    - role_target
    - using_expression
    - with_check_expression
    - expression_compatibility
    - policy_name_shape
    - table_name_shape
    - role_name_shape
    - privilege_level
    - rls_enabled
    - table_existence
    - role_existence
    - duplicate_policy_name
    - nonexistent_table
    - rls_not_enabled
    - privilege_denied
    - select_with_check_conflict
    - insert_with_using_conflict
    - only_restrictive_policy
    - invalid_expression
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - policy_type
    - command_type
  rendering:
    statement_template: "CREATE POLICY {policy_name} ON {table_name} {as_clause}\
    \ {for_clause} {to_clause} {using_clause} {with_check_clause}"
    verification_query_template: "SELECT polname, polcmd, polpermissive FROM pg_policy\
      \ WHERE polname = '{policy_name}' AND polrelid = (SELECT oid FROM pg_class\
      \ WHERE relname = '{table_name}')"
    factor_value_bindings: {}
```
