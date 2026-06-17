# 技能：DROP RULE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droprule.html

```sql
DROP RULE [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- 必须指定规则所属的表/视图（ON table_name），规则名称仅在表范围内唯一
- RESTRICT 是默认行为（省略 CASCADE/RESTRICT 时等效于 RESTRICT）
- 必须拥有目标表/视图才能 DROP RULE
- CASCADE 会自动删除依赖该规则的对象
- DROP RULE 是 PostgreSQL 语言扩展（不在 SQL 标准中）
- 删除视图的 ON SELECT "_RETURN" 规则会导致视图失效

## 语句作用

官方说明：DROP RULE — remove a rewrite rule

该 reference 关注查询重写规则的删除操作，涉及表/视图依赖但不需要覆盖列类型组合。Rule 删除需要指定所属表名，删除视图的 "_RETURN" 规则会导致视图失效。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP RULE / DROP RULE IF EXISTS）
- object_state：目标 rule 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关
- cascade_restrict：CASCADE / RESTRICT 子句
- target_rule_type：规则类型（ON SELECT "_RETURN" / 其他规则）

### T3：对象名与输入形态因子
- rule_name_shape：rule 名称形态
- table_name_shape：目标表/视图名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（table_owner / non_owner / superuser）
- table_existence：目标表/视图存在性
- dependency_context：依赖对象驻留情况

### T5：异常与边界因子
- nonexistent_rule：rule 不存在且无 IF EXISTS
- nonexistent_table：目标表/视图不存在
- privilege_denied：非 table owner 尝试 DROP
- has_dependents_restrict：RESTRICT 模式下有依赖对象
- on_select_return_drop：删除 "_RETURN" 规则导致视图失效

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP RULE 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表和所有列类型组合，Rule 行为不随列类型变化。
- 覆盖目标 rule 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括权限边界和 "_RETURN" 规则删除导致视图失效的边界。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 rule 存在时的成功删除路径，以及目标 rule 不存在时的失败路径。
- IF EXISTS 必须覆盖不存在 rule 的代表性 no-op 路径。
- CASCADE/RESTRICT 必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- RESTRICT 是默认行为，省略 CASCADE/RESTRICT 的路径必须等效于 RESTRICT 路径。
- 删除视图的 ON SELECT "_RETURN" 规则会导致视图失效，必须覆盖此边界。
- DROP RULE 必须指定 ON table_name，不能仅凭规则名称删除。
- 非 table owner 执行 DROP RULE 属于失败路径。
- 成功路径必须包含可验证的 rule 不存在性检查。
- 每个样本必须包含明确的前置对象准备（含表/视图创建和 rule 创建）、目标 DROP RULE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- "_RETURN" 规则删除导致视图失效的因子必须挂靠到视图相关的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 子句、CASCADE/RESTRICT 子句和 "_RETURN" 规则边界代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: rule
  skill_name: drop_rule
  official_source: https://www.postgresql.org/docs/16/sql-droprule.html
  statement:
    key: drop_rule
    name: DROP RULE
    aliases:
    - drop_rule
    - DROP RULE
    purpose: DROP RULE — remove a rewrite rule
  syntax_templates:
  - "DROP RULE [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]"
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
    - target_rule_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - rule_name_shape
    - table_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - table_existence
    - dependency_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_rule
    - nonexistent_table
    - privilege_denied
    - has_dependents_restrict
    - on_select_return_drop
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
      - key: branch_drop_rule
        label: DROP RULE name ON table_name [ CASCADE | RESTRICT ]
      - key: branch_drop_rule_if_exists
        label: DROP RULE IF EXISTS name ON table_name [ CASCADE | RESTRICT ]
    object_state:
      label: 目标 rule 对象状态
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
      importance: important
      values:
      - cascade
      - restrict
      - omitted_default_restrict
    target_rule_type:
      label: 规则类型
      importance: non_important
      values:
      - normal_rule
      - on_select_return_rule
    rule_name_shape:
      label: rule 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - _RETURN_special
      - nonexistent_name
      - existing_name
    table_name_shape:
      label: 目标表/视图名称形态
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
    table_existence:
      label: 目标表/视图存在性
      importance: non_important
      values:
      - table_exists
      - table_not_exists
    dependency_context:
      label: 依赖对象驻留情况
      importance: non_important
      values:
      - no_dependencies
      - has_dependent_objects
    nonexistent_rule:
      label: rule 不存在且无 IF EXISTS
      importance: non_important
      values:
      - rule_exists
      - rule_missing_without_if_exists
    nonexistent_table:
      label: 目标表/视图不存在
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
    has_dependents_restrict:
      label: RESTRICT 模式下有依赖对象
      importance: non_important
      values:
      - no_dependents_safe
      - dependents_block_restrict
    on_select_return_drop:
      label: 删除 "_RETURN" 规则导致视图失效
      importance: non_important
      values:
      - normal_rule_drop
      - _RETURN_drop_breaks_view
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_rewrite
      - error_assertion
      - notice_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_rule
      - drop_view_after_return_drop
      - drop_table
      - cascade_cleanup
  defaults:
    expected_status: success
    cascade_restrict: restrict
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - target_rule_type
    - rule_name_shape
    - table_name_shape
    - privilege_level
    - table_existence
    - dependency_context
    - nonexistent_rule
    - nonexistent_table
    - privilege_denied
    - has_dependents_restrict
    - on_select_return_drop
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP RULE {if_exists_clause} {rule_name} ON {table_name}\
    \ {cascade_restrict_clause}"
    verification_query_template: "SELECT r.rulename FROM pg_rewrite r JOIN pg_class\
      \ c ON r.ev_class = c.oid WHERE r.rulename = '{rule_name}' AND c.relname =\
      \ '{table_name}'"
    factor_value_bindings: {}
```
