# 技能：ALTER POLICY

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterpolicy.html

```sql
ALTER POLICY name ON table_name RENAME TO new_name

ALTER POLICY name ON table_name
    [ TO { role_name | PUBLIC | CURRENT_ROLE | CURRENT_USER | SESSION_USER } [, ...] ]
    [ USING ( using_expression ) ]
    [ WITH CHECK ( check_expression ) ]
```

PG16 关键约束：
- ALTER POLICY 只有两种形式：RENAME 和修改角色/表达式
- 第二种形式中，TO / USING / WITH CHECK 是独立替换的：省略的子句保持原值不变
- ALTER POLICY 不能修改 policy 的命令类型（FOR）或策略类型（AS PERMISSIVE/RESTRICTIVE），要改变这些必须先 DROP 再 CREATE
- 必须拥有目标表才能 ALTER POLICY
- 表必须已启用 RLS 且 policy 必须已存在

## 语句作用

官方说明：ALTER POLICY — change the definition of a row-level security policy

该 reference 关注行级安全策略的定义变更，包括策略重命名和角色/表达式修改。Policy 的 ALTER 操作涉及表依赖但不需要覆盖列类型组合。ALTER POLICY 不能改变命令类型和策略类型，仅能修改名称、角色和表达式。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（RENAME / 修改角色表达式 两种形式）
- object_state：目标 policy 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（rename / modify_roles / modify_using / modify_with_check / modify_combined）
- role_target：TO 角色目标形态
- using_expression：USING expression 修改形态（省略保持 / 指定新表达式）
- with_check_expression：WITH CHECK expression 修改形态（省略保持 / 指定新表达式）

### T3：对象名与输入形态因子
- policy_name_shape：policy 名称形态
- table_name_shape：目标表名称形态
- new_name_shape：RENAME TO 新名称形态
- role_name_shape：角色名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（table_owner / non_owner / superuser）
- rls_enabled：目标表是否已启用 RLS
- table_existence：目标表存在性
- policy_existence：目标 policy 是否存在
- role_existence：TO 角色存在性

### T5：异常与边界因子
- nonexistent_policy：目标 policy 不存在
- nonexistent_table：目标表不存在
- privilege_denied：非 table owner 尝试 ALTER
- rls_not_enabled：目标表未启用 RLS
- cannot_alter_command_type：尝试改变命令类型（只能 DROP+CREATE）
- cannot_alter_policy_type：尝试改变 PERMISSIVE/RESTRICTIVE 类型

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER POLICY 两种语法分支（RENAME / 修改角色表达式）中的所有行为路径。
- 不需要覆盖所有基表和所有列类型组合，Policy 行为不随列类型变化。
- 覆盖目标 policy 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括权限边界和语义边界。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 policy 和表对象，并为每个 ALTER 分支准备最小合法前置状态（含 RLS 启用）。
- 必须覆盖目标 policy 存在时的成功修改路径和不存在时的失败路径。
- ALTER POLICY 不能修改命令类型（FOR 子句）或策略类型（AS 子句），必须标注此限制。
- 第二种形式中省略的子句保持原值不变，必须覆盖省略和指定两种路径。
- 必须拥有目标表才能 ALTER POLICY，非 owner 路径属于失败路径。
- 成功路径必须包含可验证的 policy 变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备（含表创建、RLS 启用和 policy 创建）、目标 ALTER POLICY 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- RENAME 分支和修改角色/表达式分支的因子必须分别挂靠到对应分支的样本上。

## 规模控制规则

- 优先保证官方语法分支（2 种 ALTER 形式）、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证角色目标形态、USING/WITH CHECK 表达式形态代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: policy
  skill_name: alter_policy
  official_source: https://www.postgresql.org/docs/16/sql-alterpolicy.html
  statement:
    key: alter_policy
    name: ALTER POLICY
    aliases:
    - alter_policy
    - ALTER POLICY
    purpose: ALTER POLICY — change the definition of a row-level security policy
  syntax_templates:
  - "ALTER POLICY name ON table_name RENAME TO new_name"
  - "ALTER POLICY name ON table_name\n    [ TO { role_name | PUBLIC | CURRENT_ROLE\
    \ | CURRENT_USER | SESSION_USER } [, ...] ]\n    [ USING ( using_expression\
    \ ) ]\n    [ WITH CHECK ( check_expression ) ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - alter_action
    - role_target
    - using_expression
    - with_check_expression
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - policy_name_shape
    - table_name_shape
    - new_name_shape
    - role_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - rls_enabled
    - table_existence
    - policy_existence
    - role_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_policy
    - nonexistent_table
    - privilege_denied
    - rls_not_enabled
    - cannot_alter_command_type
    - cannot_alter_policy_type
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
      - key: branch_rename
        label: ALTER POLICY name ON table_name RENAME TO new_name
      - key: branch_modify
        label: ALTER POLICY name ON table_name [ TO ] [ USING ] [ WITH CHECK ]
    object_state:
      label: 目标 policy 对象状态
      importance: important
      values:
      - exists
      - not_exists
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    alter_action:
      label: ALTER 行为类型
      importance: non_important
      values:
      - rename
      - modify_roles
      - modify_using
      - modify_with_check
      - modify_combined
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
      label: USING expression 修改形态
      importance: non_important
      values:
      - omitted_keep_original
      - new_expression
    with_check_expression:
      label: WITH CHECK expression 修改形态
      importance: non_important
      values:
      - omitted_keep_original
      - new_expression
    policy_name_shape:
      label: policy 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_name
      - existing_name
    table_name_shape:
      label: 目标表名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified
      - nonexistent_table
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - duplicate_name
      - invalid_name
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
    policy_existence:
      label: 目标 policy 是否存在
      importance: non_important
      values:
      - policy_exists
      - policy_not_exists
    role_existence:
      label: TO 角色存在性
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    nonexistent_policy:
      label: 目标 policy 不存在
      importance: non_important
      values:
      - policy_exists
      - policy_missing
    nonexistent_table:
      label: 目标表不存在
      importance: non_important
      values:
      - table_exists
      - table_missing
    privilege_denied:
      label: 非 table owner 尝试 ALTER
      importance: non_important
      values:
      - owner_execution
      - non_owner_denied
      - superuser_execution
    rls_not_enabled:
      label: 目标表未启用 RLS
      importance: non_important
      values:
      - rls_enabled
      - rls_not_enabled
    cannot_alter_command_type:
      label: 不能改变命令类型
      importance: non_important
      values:
      - only_rename_and_modify_allowed
      - cannot_change_for_clause
    cannot_alter_policy_type:
      label: 不能改变策略类型
      importance: non_important
      values:
      - only_rename_and_modify_allowed
      - cannot_change_as_clause
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
      - revert_rename
      - disable_rls_and_drop_policy
      - drop_table
  defaults:
    expected_status: success
    privilege_level: superuser
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - role_target
    - using_expression
    - with_check_expression
    - policy_name_shape
    - table_name_shape
    - new_name_shape
    - role_name_shape
    - privilege_level
    - rls_enabled
    - table_existence
    - policy_existence
    - role_existence
    - nonexistent_policy
    - nonexistent_table
    - privilege_denied
    - rls_not_enabled
    - cannot_alter_command_type
    - cannot_alter_policy_type
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER POLICY {policy_name} ON {table_name} {alter_clause}"
    verification_query_template: "SELECT polname, polcmd, polpermissive FROM pg_policy\
      \ WHERE polname = '{policy_name}' AND polrelid = (SELECT oid FROM pg_class\
      \ WHERE relname = '{table_name}')"
    factor_value_bindings: {}
```
