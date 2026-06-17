# 技能：DROP EVENT TRIGGER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropeventtrigger.html

```sql
DROP EVENT TRIGGER [ IF EXISTS ] name [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- 当前用户必须是 event trigger 的 owner 才能执行此命令
- IF EXISTS：不抛出错误而是发出通知
- CASCADE：自动删除依赖于该 trigger 的对象，以及依赖于那些对象的递归依赖
- RESTRICT：如果有任何对象依赖于该 trigger，则拒绝删除（默认行为）
- 不在 SQL 标准中（PostgreSQL 扩展）

## 语句作用

官方说明：DROP EVENT TRIGGER — remove an event trigger

该 reference 关注事件触发器的删除。DROP EVENT TRIGGER 语法简单（单一顶层形式），核心维度是对象存在性、IF EXISTS 容错行为、CASCADE/RESTRICT 依赖处理和权限要求。该语句需要 owner 权限，不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP EVENT TRIGGER 单一顶层形式）
- object_state：目标 event trigger 对象状态（exists / not_exists）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句形态（省略 / 指定 IF EXISTS）
- cascade_restrict：CASCADE / RESTRICT 选择（省略默认 RESTRICT / CASCADE / RESTRICT）
- privilege_level：执行权限（superuser / trigger_owner / non_owner）

### T3：对象名与输入形态因子
- trigger_name_shape：event trigger 名称形态

### T4：依赖对象与环境因子
- trigger_dependency：trigger 依赖对象状态（无依赖 / 有依赖对象）
- trigger_function_state：触发函数关联状态

### T5：异常与边界因子
- trigger_not_exist_no_if_exists：目标 trigger 不存在且无 IF EXISTS
- privilege_denied：非 owner 尝试删除
- cascade_with_dependencies：CASCADE 删除有依赖对象的 trigger
- restrict_with_dependencies：RESTRICT 删除有依赖对象的 trigger（失败路径）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP EVENT TRIGGER 单一语法分支的所有可选子句组合。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖（object_state x expected_status）。
- T2 因子按规模控制策略参与组合。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 trigger 存在时的成功删除路径，以及目标 trigger 不存在时的失败路径。
- IF EXISTS 必须覆盖不存在对象的代表性 no-op 路径。
- CASCADE 必须覆盖有依赖对象下的成功删除路径。
- RESTRICT 必须覆盖有依赖对象下的失败路径（拒绝删除）。
- 必须覆盖 owner 成功删除和 non_owner 失败删除的路径。
- 每个样本必须包含明确的前置函数和 trigger 准备、目标 DROP EVENT TRIGGER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- if_exists_clause 挂靠到对象不存在场景的样本上。
- cascade_restrict 在有依赖和无依赖场景的样本上轮转注入。
- privilege_level 挂靠到 owner 成功和 non_owner 失败的样本上。
- T3 因子挂靠到代表性成功样本和失败样本上轮转注入。
- T5 因子按失败原因单独挂靠。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 形态、CASCADE/RESTRICT 依赖语义覆盖。
- 低优先级命名形态和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: event_trigger
  skill_name: drop_event_trigger
  official_source: https://www.postgresql.org/docs/16/sql-dropeventtrigger.html
  statement:
    key: drop_event_trigger
    name: DROP EVENT TRIGGER
    aliases:
    - drop_event_trigger
    - DROP EVENT TRIGGER
    purpose: DROP EVENT TRIGGER — remove an event trigger
  syntax_templates:
  - "DROP EVENT TRIGGER [ IF EXISTS ] name [ CASCADE | RESTRICT ]"
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
    - privilege_level
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - trigger_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - trigger_dependency
    - trigger_function_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - trigger_not_exist_no_if_exists
    - privilege_denied
    - cascade_with_dependencies
    - restrict_with_dependencies
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
      - key: branch_drop_event_trigger
        label: DROP EVENT TRIGGER [ IF EXISTS ] name [ CASCADE | RESTRICT ]
    object_state:
      label: 目标 event trigger 对象状态
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
    if_exists_clause:
      label: IF EXISTS 子句形态
      importance: non_important
      values:
      - omitted
      - specified_if_exists
    cascade_restrict:
      label: CASCADE / RESTRICT 选择
      importance: non_important
      values:
      - omitted_default_restrict
      - cascade
      - restrict
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - trigger_owner
      - non_owner
    trigger_name_shape:
      label: event trigger 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_name
    trigger_dependency:
      label: trigger 依赖对象状态
      importance: non_important
      values:
      - no_dependencies
      - has_dependencies
    trigger_function_state:
      label: 触发函数关联状态
      importance: non_important
      values:
      - function_exists
      - function_dropped_after_trigger
    trigger_not_exist_no_if_exists:
      label: 目标 trigger 不存在且无 IF EXISTS
      importance: non_important
      values:
      - trigger_exists
      - trigger_not_exists_no_if_exists
    privilege_denied:
      label: 非 owner 尝试删除
      importance: non_important
      values:
      - owner_success
      - non_owner_failure
      - superuser_success
    cascade_with_dependencies:
      label: CASCADE 删除有依赖对象的 trigger
      importance: non_important
      values:
      - cascade_success_with_dependencies
      - no_dependencies_cascade
    restrict_with_dependencies:
      label: RESTRICT 删除有依赖对象的 trigger
      importance: non_important
      values:
      - restrict_failure_with_dependencies
      - no_dependencies_restrict_success
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_event_trigger_absence
      - error_assertion
      - notice_assertion_if_exists
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_event_trigger
      - drop_function
      - cascade_cleanup
  defaults:
    expected_status: success
    object_state: exists
    if_exists_clause: omitted
    cascade_restrict: omitted_default_restrict
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - privilege_level
    - trigger_name_shape
    - trigger_dependency
    - trigger_function_state
    - trigger_not_exist_no_if_exists
    - privilege_denied
    - cascade_with_dependencies
    - restrict_with_dependencies
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 100
    preserve_axes_first:
    - statement_branch
  rendering:
    statement_template: "DROP EVENT TRIGGER {if_exists} {trigger_name} {cascade_restrict}"
    verification_query_template: "SELECT count(*) FROM pg_event_trigger WHERE evtname\
      \ = '{trigger_name}'"
    factor_value_bindings: {}
```
