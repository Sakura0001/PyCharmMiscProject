# 技能：CREATE RULE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createrule.html

```sql
CREATE [ OR REPLACE ] RULE name AS ON event
    TO table_name [ WHERE condition ]
    DO [ ALSO | INSTEAD ] { NOTHING | command | ( command ; command ... ) }

where event can be one of:

    SELECT | INSERT | UPDATE | DELETE
```

PG16 关键约束：
- 必须拥有目标表才能创建规则
- ON SELECT 规则只能附加到视图上，必须命名为 "_RETURN"，必须是无条件 INSTEAD 规则，且动作必须是单个 SELECT 命令
- 多条规则在同一表同一事件上按名称字母顺序依次应用
- INSERT 包含 ON CONFLICT 子句时，不能用于有 INSERT 或 UPDATE 规则的表
- 条件规则中 NEW 仅在 ON INSERT / ON UPDATE 有效，OLD 仅在 ON UPDATE / ON DELETE 有效
- 视图上的条件规则需要无条件 INSTEAD 规则配合才能正常工作
- 规则动作中的 NOTIFY 命令无条件执行（即使无行匹配条件）
- CREATE RULE 是 PostgreSQL 语言扩展（不在 SQL 标准中）

## 语句作用

官方说明：CREATE RULE — define a new rewrite rule

该 reference 关注查询重写规则的定义，涉及表/视图依赖和事件类型但不需要覆盖列类型组合。Rule 的行为由事件类型（SELECT/INSERT/UPDATE/DELETE）、动作类型（ALSO/INSTEAD/NOTHING）和条件决定，不涉及列类型变化。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE RULE 单一顶层形式）
- event_type：事件类型（SELECT / INSERT / UPDATE / DELETE）
- rule_action：动作类型（ALSO / INSTEAD / NOTHING）
- object_state：目标 rule 对象状态（不存在 / 已存在同名同表）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- or_replace：OR REPLACE 开关
- where_condition：WHERE condition 形态（省略 / 指定）
- command_type：DO command 类型（单个命令 / 多个命令 / NOTHING）
- command_content：command 内容类型（SELECT / INSERT / UPDATE / DELETE / NOTIFY）

### T3：对象名与输入形态因子
- rule_name_shape：rule 名称形态
- table_name_shape：目标表/视图名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（table_owner / non_owner / superuser）
- table_type：目标对象类型（表 / 视图）
- table_existence：目标表/视图存在性

### T5：异常与边界因子
- duplicate_rule：同一表同一事件上重名冲突
- nonexistent_table：目标表/视图不存在
- privilege_denied：非 table owner 尝试创建
- on_select_rule_constraints：ON SELECT 规则违反视图约束（非 _RETURN 名称 / 有条件 / 非 INSTEAD / 非单个 SELECT）
- on_conflict_incompatibility：ON CONFLICT 与 INSERT/UPDATE 规则不兼容
- new_old_in_invalid_event：NEW/OLD 在无效事件上引用
- circular_rule：循环规则导致递归扩展错误
- conditional_rule_on_view：视图上仅有条件规则导致更新失败

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE RULE 单一语法分支中的所有可选子句组合（OR REPLACE / WHERE / ALSO / INSTEAD / NOTHING / 多命令）。
- 覆盖所有 4 种事件类型（SELECT / INSERT / UPDATE / DELETE）。
- 覆盖所有 3 种动作类型（ALSO / INSTEAD / NOTHING）。
- 不需要覆盖所有基表和所有列类型组合，Rule 行为不随列类型变化。
- 覆盖目标 rule 不存在/重名冲突路径。
- 覆盖成功路径与失败路径，包括权限边界、ON SELECT 约束和 ON CONFLICT 不兼容边界。
- T1 因子做笛卡尔积覆盖；event_type 和 rule_action 做全量覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE RULE 要求执行者是目标表/视图的 owner，非 owner 路径属于失败路径。
- ON SELECT 规则有严格约束：只能附加到视图、必须名为 "_RETURN"、无条件 INSTEAD、动作必须是单个 SELECT 命令。违反这些约束的路径属于失败路径。
- INSERT 包含 ON CONFLICT 子句时不能用于有 INSERT 或 UPDATE 规则的表，必须标注此不兼容性。
- 视图上的条件规则需要无条件 INSTEAD 规则配合才能正常工作，单独条件规则可能导致更新失败。
- 规则动作中的 NOTIFY 无条件执行，必须标注此语义边界。
- 成功路径必须包含可验证的 rule 存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备（含表/视图创建）、目标 CREATE RULE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- event_type 因子与 ON SELECT 约束因子必须联动挂靠，确保 ON SELECT 规则的严格约束边界被覆盖。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- 视图相关因子必须挂靠到目标对象为视图的样本上。
- ON CONFLICT 不兼容因子必须挂靠到 INSERT/UPDATE 事件类型的样本上。

## 规模控制规则

- 优先保证官方语法分支、事件类型全覆盖（SELECT/INSERT/UPDATE/DELETE）、动作类型全覆盖（ALSO/INSTEAD/NOTHING）、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 OR REPLACE 开关、WHERE condition 形态、command 内容类型和 ON SELECT 约束边界代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: rule
  skill_name: create_rule
  official_source: https://www.postgresql.org/docs/16/sql-createrule.html
  statement:
    key: create_rule
    name: CREATE RULE
    aliases:
    - create_rule
    - CREATE RULE
    purpose: CREATE RULE — define a new rewrite rule
  syntax_templates:
  - "CREATE [ OR REPLACE ] RULE name AS ON event\n    TO table_name [ WHERE condition\
    \ ]\n    DO [ ALSO | INSTEAD ] { NOTHING | command | ( command ; command ...\
    \ ) }\n\nwhere event can be one of:\n\n    SELECT | INSERT | UPDATE | DELETE"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - event_type
    - rule_action
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - or_replace
    - where_condition
    - command_type
    - command_content
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - rule_name_shape
    - table_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - table_type
    - table_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_rule
    - nonexistent_table
    - privilege_denied
    - on_select_rule_constraints
    - on_conflict_incompatibility
    - new_old_in_invalid_event
    - circular_rule
    - conditional_rule_on_view
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
      - key: branch_create_rule
        label: CREATE [ OR REPLACE ] RULE name AS ON event TO table_name [ WHERE ] DO [ ALSO | INSTEAD ] { NOTHING | command | ( command ; ... ) }
    event_type:
      label: 事件类型
      importance: important
      values:
      - SELECT
      - INSERT
      - UPDATE
      - DELETE
    rule_action:
      label: 动作类型
      importance: important
      values:
      - ALSO
      - INSTEAD
      - NOTHING
      - implicit_also
    object_state:
      label: 目标 rule 对象状态
      importance: important
      values:
      - not_exists
      - exists_same_table_same_event
      - exists_different_table
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    or_replace:
      label: OR REPLACE 开关
      importance: non_important
      values:
      - present
      - absent
    where_condition:
      label: WHERE condition 形态
      importance: non_important
      values:
      - omitted
      - simple_boolean_condition
      - new_old_reference_condition
      - complex_condition
    command_type:
      label: DO command 类型
      importance: non_important
      values:
      - NOTHING
      - single_command
      - multiple_commands
    command_content:
      label: command 内容类型
      importance: non_important
      values:
      - SELECT_command
      - INSERT_command
      - UPDATE_command
      - DELETE_command
      - NOTIFY_command
    rule_name_shape:
      label: rule 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - _RETURN_special_name
      - reserved_word_as_name
      - duplicate_name
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
    table_type:
      label: 目标对象类型
      importance: non_important
      values:
      - table
      - view
    table_existence:
      label: 目标表/视图存在性
      importance: non_important
      values:
      - table_exists
      - table_not_exists
    duplicate_rule:
      label: 同一表同一事件上重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_table_same_event_same_name
    nonexistent_table:
      label: 目标表/视图不存在
      importance: non_important
      values:
      - table_exists
      - table_missing
    privilege_denied:
      label: 非 table owner 尝试创建
      importance: non_important
      values:
      - owner_execution
      - non_owner_denied
      - superuser_execution
    on_select_rule_constraints:
      label: ON SELECT 规则约束违反
      importance: non_important
      values:
      - valid_on_select_on_view
      - on_select_on_table_invalid
      - on_select_not_RETURN_name
      - on_select_conditional_invalid
      - on_select_not_INSTEAD_invalid
      - on_select_multi_command_invalid
    on_conflict_incompatibility:
      label: ON CONFLICT 与 INSERT/UPDATE 规则不兼容
      importance: non_important
      values:
      - no_on_conflict_issue
      - on_conflict_insert_rule_conflict
    new_old_in_invalid_event:
      label: NEW/OLD 在无效事件上引用
      importance: non_important
      values:
      - valid_new_old_reference
      - new_in_delete_invalid
      - old_in_insert_invalid
    circular_rule:
      label: 循环规则导致递归扩展错误
      importance: non_important
      values:
      - no_circular_dependency
      - circular_select_rule_error
    conditional_rule_on_view:
      label: 视图上仅有条件规则导致更新失败
      importance: non_important
      values:
      - unconditional_instead_present
      - only_conditional_rules_on_view
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_rewrite
      - rule_behavior_test
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_rule
      - drop_view
      - drop_table
  defaults:
    expected_status: success
    event_type: INSERT
    rule_action: ALSO
    object_state: not_exists
    or_replace: absent
    where_condition: omitted
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - event_type
    - rule_action
    - object_state
    - expected_status
    non_main_factors:
    - or_replace
    - where_condition
    - command_type
    - command_content
    - rule_name_shape
    - table_name_shape
    - privilege_level
    - table_type
    - table_existence
    - duplicate_rule
    - nonexistent_table
    - privilege_denied
    - on_select_rule_constraints
    - on_conflict_incompatibility
    - new_old_in_invalid_event
    - circular_rule
    - conditional_rule_on_view
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - event_type
    - rule_action
  rendering:
    statement_template: "CREATE {or_replace_clause} RULE {rule_name} AS ON {event_type}\n\
    \    TO {table_name} {where_clause}\n    DO {rule_action} {command_clause}"
    verification_query_template: "SELECT r.rulename, r.ev_type, r.is_instead FROM\
    \ pg_rewrite r JOIN pg_class c ON r.ev_class = c.oid WHERE r.rulename = '{rule_name}'\
    \ AND c.relname = '{table_name}'"
    factor_value_bindings: {}
```
