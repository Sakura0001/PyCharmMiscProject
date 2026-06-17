# 技能：DROP POLICY

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droppolicy.html

```sql
DROP POLICY [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- 必须拥有目标表才能 DROP POLICY
- CASCADE/RESTRICT 对 policy 无实质效果，因为 policy 没有依赖对象
- 如果删除的是表的最后一个 policy，且表仍启用 RLS，将应用默认 deny 规则
- 要完全禁用 RLS 需使用 ALTER TABLE ... DISABLE ROW LEVEL SECURITY
- DROP POLICY 是 PostgreSQL 扩展（不在 SQL 标准中）

## 语句作用

官方说明：DROP POLICY — remove a row-level security policy from a table

该 reference 关注行级安全策略的删除操作，涉及表依赖但不需要覆盖列类型组合。Policy 删除后表的 RLS 状态变化（默认 deny 规则）需要特别关注。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP POLICY / DROP POLICY IF EXISTS）
- object_state：目标 policy 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关
- cascade_restrict：CASCADE / RESTRICT 子句
- last_policy_effect：是否为表的最后一个 policy

### T3：对象名与输入形态因子
- policy_name_shape：policy 名称形态
- table_name_shape：目标表名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（table_owner / non_owner / superuser）
- rls_state：表当前 RLS 状态（enabled / disabled）
- table_existence：目标表存在性

### T5：异常与边界因子
- nonexistent_policy：policy 不存在且无 IF EXISTS
- nonexistent_table：目标表不存在
- privilege_denied：非 table owner 尝试 DROP
- last_policy_default_deny：删除最后一个 policy 后 RLS 默认 deny 效果

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP POLICY 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表和所有列类型组合，Policy 行为不随列类型变化。
- 覆盖目标 policy 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括权限边界和最后一个 policy 的默认 deny 边界。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 policy 存在时的成功删除路径，以及目标 policy 不存在时的失败路径。
- IF EXISTS 必须覆盖不存在 policy 的代表性 no-op 路径。
- CASCADE/RESTRICT 对 policy 无实质效果（policy 没有依赖对象），但语法上仍需覆盖。
- 必须覆盖删除最后一个 policy 后 RLS 默认 deny 规则生效的边界。
- 要完全禁用 RLS 需 ALTER TABLE ... DISABLE ROW LEVEL SECURITY，必须在样本中标注此区别。
- 非 table owner 执行 DROP POLICY 属于失败路径。
- 成功路径必须包含可验证的 policy 不存在性检查。
- 每个样本必须包含明确的前置对象准备、目标 DROP POLICY 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- 与最后一个 policy 默认 deny 效果相关的因子必须挂靠到只有单个 policy 的表的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 子句、CASCADE/RESTRICT 子句和最后一个 policy 边界代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: policy
  skill_name: drop_policy
  official_source: https://www.postgresql.org/docs/16/sql-droppolicy.html
  statement:
    key: drop_policy
    name: DROP POLICY
    aliases:
    - drop_policy
    - DROP POLICY
    purpose: DROP POLICY — remove a row-level security policy from a table
  syntax_templates:
  - "DROP POLICY [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]"
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
    - if_exists_clause
    - cascade_restrict
    - last_policy_effect
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - policy_name_shape
    - table_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - rls_state
    - table_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_policy
    - nonexistent_table
    - privilege_denied
    - last_policy_default_deny
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
      - key: branch_drop_policy
        label: DROP POLICY name ON table_name [ CASCADE | RESTRICT ]
      - key: branch_drop_policy_if_exists
        label: DROP POLICY IF EXISTS name ON table_name [ CASCADE | RESTRICT ]
    object_state:
      label: 目标 policy 对象状态
      importance: important
      values:
      - exists
      - absent
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: important
      values:
      - present
      - absent
    cascade_restrict:
      label: CASCADE / RESTRICT 子句
      importance: non_important
      values:
      - cascade
      - restrict
      - omitted
    last_policy_effect:
      label: 是否为表的最后一个 policy
      importance: important
      values:
      - not_last_policy
      - last_policy_remaining
      - table_has_multiple_policies
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
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - table_owner
      - non_owner
    rls_state:
      label: 表当前 RLS 状态
      importance: non_important
      values:
      - rls_enabled
      - rls_disabled
    table_existence:
      label: 目标表存在性
      importance: non_important
      values:
      - table_exists
      - table_not_exists
    nonexistent_policy:
      label: policy 不存在且无 IF EXISTS
      importance: non_important
      values:
      - policy_exists
      - policy_missing_without_if_exists
    nonexistent_table:
      label: 目标表不存在
      importance: non_important
      values:
      - table_exists
      - table_missing
    privilege_denied:
      label: 非 table owner 尝试 DROP
      importance: non_important
      values:
      - owner_execution
      - non_owner_denied
      - superuser_execution
    last_policy_default_deny:
      label: 删除最后一个 policy 后 RLS 默认 deny
      importance: non_important
      values:
      - other_policies_remain
      - default_deny_after_drop
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_policy
      - error_assertion
      - notice_assertion
      - rls_behavior_test
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - disable_rls_drop_policy
      - drop_table
      - role_cleanup
  defaults:
    expected_status: success
    object_state: exists
    cascade_restrict: restrict
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - last_policy_effect
    - policy_name_shape
    - table_name_shape
    - privilege_level
    - rls_state
    - table_existence
    - nonexistent_policy
    - nonexistent_table
    - privilege_denied
    - last_policy_default_deny
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP POLICY {if_exists_clause} {policy_name} ON {table_name}\
    \ {cascade_restrict_clause}"
    verification_query_template: "SELECT polname FROM pg_policy WHERE polname =\
    \ '{policy_name}' AND polrelid = (SELECT oid FROM pg_class WHERE relname = '{table_name}')"
    factor_value_bindings: {}
```
