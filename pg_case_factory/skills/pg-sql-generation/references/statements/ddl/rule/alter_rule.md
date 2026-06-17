# 技能：ALTER RULE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterrule.html

```sql
ALTER RULE name ON table_name RENAME TO new_name
```

PG16 关键约束：
- ALTER RULE 当前仅支持 RENAME 操作，不支持修改规则体、条件或其他属性
- 必须拥有目标表/视图才能 ALTER RULE（不要求拥有规则本身）
- ENABLE/DISABLE RULE 不属于 ALTER RULE 命令，而是 ALTER TABLE 的子命令：
  - ALTER TABLE name ENABLE RULE rule_name
  - ALTER TABLE name DISABLE RULE rule_name
  - ALTER TABLE name ENABLE REPLICA RULE rule_name
  - ALTER TABLE name ENABLE ALWAYS RULE rule_name
- DISABLED 规则仍存在于系统但不在查询重写时应用
- ON SELECT 规则不受 enable/disable 配置影响，总是应用以保持视图工作

## 语句作用

官方说明：ALTER RULE — change the definition of a rule

该 reference 关注查询重写规则的定义变更（仅 RENAME）。ALTER RULE 功能极其有限，仅支持重命名操作。规则的启用/禁用属于 ALTER TABLE 子命令范畴，不在此 reference 中覆盖。Rule 的 ALTER 操作涉及表依赖但不需要覆盖列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（ALTER RULE name ON table_name RENAME TO new_name 单一形式）
- object_state：目标 rule 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（rename_only）
- table_type：目标对象类型（表 / 视图）

### T3：对象名与输入形态因子
- rule_name_shape：rule 名称形态
- table_name_shape：目标表/视图名称形态
- new_name_shape：RENAME TO 新名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（table_owner / non_owner / superuser）
- table_existence：目标表/视图存在性

### T5：异常与边界因子
- nonexistent_rule：目标 rule 不存在
- nonexistent_table：目标表/视图不存在
- privilege_denied：非 table owner 尝试 ALTER
- duplicate_new_name：新名称与同表已有规则重名
- on_select_return_rename：重命名 ON SELECT 的 _RETURN 规则导致视图失效

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER RULE 单一语法分支（仅 RENAME）中的所有行为路径。
- 不需要覆盖所有基表和所有列类型组合，Rule 行为不随列类型变化。
- 覆盖目标 rule 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括权限边界。
- ALTER TABLE 的 ENABLE/DISABLE RULE 子命令不在本 reference 中，但必须标注此功能边界。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER RULE 仅支持 RENAME 操作，不支持修改规则体或条件，必须在样本中标注此限制。
- ENABLE/DISABLE RULE 属于 ALTER TABLE 子命令，不在此 reference 中生成。但必须标注此功能边界和关联性。
- 必须拥有目标表/视图才能 ALTER RULE，非 owner 路径属于失败路径。
- 必须预创建可被重命名的目标 rule 对象。
- 必须覆盖目标 rule 存在时的成功重命名路径和不存在时的失败路径。
- ON SELECT 视图规则名为 "_RETURN"，重命名可能导致视图失效，必须覆盖此边界。
- 成功路径必须包含可验证的 rule 名称变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备（含表/视图创建和 rule 创建）、目标 ALTER RULE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- ON SELECT "_RETURN" 规则重命名边界必须挂靠到视图相关样本上。

## 规模控制规则

- 优先保证官方语法分支（单一 RENAME 形式）、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证目标对象类型（表/视图）、新名称形态和 ON SELECT 规则边界代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: rule
  skill_name: alter_rule
  official_source: https://www.postgresql.org/docs/16/sql-alterrule.html
  statement:
    key: alter_rule
    name: ALTER RULE
    aliases:
    - alter_rule
    - ALTER RULE
    purpose: ALTER RULE — change the definition of a rule (rename only; enable/disable via ALTER TABLE)
  syntax_templates:
  - "ALTER RULE name ON table_name RENAME TO new_name"
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
    - table_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - rule_name_shape
    - table_name_shape
    - new_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - table_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_rule
    - nonexistent_table
    - privilege_denied
    - duplicate_new_name
    - on_select_return_rename
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
        label: ALTER RULE name ON table_name RENAME TO new_name
    object_state:
      label: 目标 rule 对象状态
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
    table_type:
      label: 目标对象类型
      importance: non_important
      values:
      - table
      - view
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
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - duplicate_name_same_table
      - invalid_name
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
    nonexistent_rule:
      label: 目标 rule 不存在
      importance: non_important
      values:
      - rule_exists
      - rule_missing
    nonexistent_table:
      label: 目标表/视图不存在
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
    duplicate_new_name:
      label: 新名称与同表已有规则重名
      importance: non_important
      values:
      - no_conflict
      - same_table_same_event_conflict
    on_select_return_rename:
      label: 重命名 ON SELECT 的 _RETURN 规则
      importance: non_important
      values:
      - normal_rule_rename
      - _RETURN_rename_breaks_view
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_rewrite
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - revert_rename
      - drop_rule
      - drop_view
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
    - table_type
    - rule_name_shape
    - table_name_shape
    - new_name_shape
    - privilege_level
    - table_existence
    - nonexistent_rule
    - nonexistent_table
    - privilege_denied
    - duplicate_new_name
    - on_select_return_rename
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER RULE {rule_name} ON {table_name} RENAME TO {new_name}"
    verification_query_template: "SELECT r.rulename FROM pg_rewrite r JOIN pg_class\
      \ c ON r.ev_class = c.oid WHERE r.rulename = '{new_name}' AND c.relname =\
      \ '{table_name}'"
    factor_value_bindings: {}
```
