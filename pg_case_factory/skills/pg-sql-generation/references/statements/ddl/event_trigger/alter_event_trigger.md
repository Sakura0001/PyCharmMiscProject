# 技能：ALTER EVENT TRIGGER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altereventtrigger.html

```sql
ALTER EVENT TRIGGER name DISABLE
ALTER EVENT TRIGGER name ENABLE [ REPLICA | ALWAYS ]
ALTER EVENT TRIGGER name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER EVENT TRIGGER name RENAME TO new_name
```

PG16 关键约束：
- 必须 superuser 才能执行 ALTER EVENT TRIGGER（所有分支均需 superuser）
- DISABLE：禁用触发器，仍注册在系统目录中但不执行
- ENABLE：正常启用（仅在 session_replication_role 为 origin 时触发）
- ENABLE REPLICA：仅在 session_replication_role 为 replica 时触发
- ENABLE ALWAYS：无论 session_replication_role 设置如何都触发
- OWNER TO：更改 event trigger 的 owner；必须 superuser
- RENAME TO：更改 event trigger 名称；必须 superuser
- 不在 SQL 标准中（PostgreSQL 扩展）

## 语句作用

官方说明：ALTER EVENT TRIGGER — change the definition of an event trigger

该 reference 关注事件触发器的元数据变更。ALTER EVENT TRIGGER 有 4 种独立语法分支（DISABLE / ENABLE[REPLICA|ALWAYS] / OWNER TO / RENAME TO），所有分支均需 superuser 权限。该语句不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DISABLE / ENABLE / ENABLE REPLICA / ENABLE ALWAYS / OWNER TO / RENAME TO）
- object_state：目标 event trigger 对象状态（exists / not_exists）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- enable_mode：启用模式（ENABLE / ENABLE REPLICA / ENABLE ALWAYS）
- new_owner_target：OWNER TO 的目标形式（existing_role / nonexistent_role / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- rename_conflict：RENAME TO 目标名称状态（new_name_unique / new_name_exists）
- privilege_level：执行权限（superuser / non_superuser）
- trigger_current_state：触发器当前状态（enabled / disabled / enabled_replica / enabled_always）

### T3：对象名与输入形态因子
- trigger_name_shape：event trigger 名称形态
- new_name_shape：新名称形态（仅 RENAME TO）
- new_owner_shape：目标 owner 名称形态（仅 OWNER TO）

### T4：依赖对象与环境因子
- session_replication_role：session_replication_role 设置（origin / replica / local）
- trigger_function_state：触发函数依赖状态

### T5：异常与边界因子
- trigger_not_exist：目标 event trigger 不存在
- privilege_denied_non_superuser：非 superuser 执行 ALTER EVENT TRIGGER
- rename_target_conflict：RENAME TO 新名称已存在
- owner_not_exist：OWNER TO 目标角色不存在
- alter_nonexistent_trigger：修改不存在的 event trigger

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖 ALTER EVENT TRIGGER 的所有 4 种语法分支（DISABLE、ENABLE[REPLICA|ALWAYS]、OWNER TO、RENAME TO）。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖；statement_branch 跨 4 个主分支（含 ENABLE 的 3 个子变体）。
- T2 因子按分支适用性参与组合：
  - enable_mode 仅挂靠到 ENABLE 分支。
  - new_owner_target 仅挂靠到 OWNER TO 分支。
  - rename_conflict 仅挂靠到 RENAME TO 分支。
  - privilege_level 覆盖所有分支。
  - trigger_current_state 在不同分支上轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 所有分支均需 superuser 权限，非 superuser 属于失败路径。
- 必须预创建目标 event trigger 及其触发函数。
- DISABLE/ENABLE/ENABLE REPLICA/ENABLE ALWAYS 必须覆盖触发器状态变更的完整路径。
- OWNER TO 必须覆盖 existing_role 成功、CURRENT_ROLE/CURRENT_USER/SESSION_USER 目标形式、nonexistent_role 失败路径。
- RENAME TO 必须覆盖新名称成功、新名称已存在失败、trigger 不存在失败路径。
- 每个样本必须包含明确的前置函数和 trigger 准备、目标 ALTER EVENT TRIGGER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- session_replication_role 设置仅影响 ENABLE REPLICA 和 ENABLE ALWAYS 的触发行为，验证时应检查 pg_event_trigger.evtenabled 字段。

## 挂靠规则

- enable_mode 仅挂靠到 ENABLE 分支的样本上。
- new_owner_target 仅挂靠到 OWNER TO 分支。
- rename_conflict 仅挂靠到 RENAME TO 分支。
- privilege_denied_non_superuser 覆盖所有分支各至少一个失败样本。
- trigger_current_state 在不同分支上轮转挂靠（从 disabled 改为 enabled、从 enabled 改为 disabled 等代表性路径）。
- session_replication_role 仅挂靠到 ENABLE REPLICA/ENABLE ALWAYS 的验证样本上。

## 规模控制规则

- 优先保证：
  - 4 个主语法分支全覆盖（含 ENABLE 的 3 个子变体）
  - superuser 成功 / non_superuser 失败权限路径全覆盖
  - trigger 存在/不存在状态全覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - CURRENT_ROLE/CURRENT_USER/SESSION_USER 目标 owner 形式覆盖
  - DISABLE→ENABLE→DISABLE 状态轮转覆盖
  - session_replication_role 与 ENABLE REPLICA/ALWAYS 关联覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: event_trigger
  skill_name: alter_event_trigger
  official_source: https://www.postgresql.org/docs/16/sql-altereventtrigger.html
  statement:
    key: alter_event_trigger
    name: ALTER EVENT TRIGGER
    aliases:
    - alter_event_trigger
    - ALTER EVENT TRIGGER
    purpose: ALTER EVENT TRIGGER — change the definition of an event trigger
  syntax_templates:
  - "ALTER EVENT TRIGGER name DISABLE"
  - "ALTER EVENT TRIGGER name ENABLE [ REPLICA | ALWAYS ]"
  - "ALTER EVENT TRIGGER name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER\
    \ | SESSION_USER }"
  - "ALTER EVENT TRIGGER name RENAME TO new_name"
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
    - enable_mode
    - new_owner_target
    - rename_conflict
    - privilege_level
    - trigger_current_state
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - trigger_name_shape
    - new_name_shape
    - new_owner_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - session_replication_role
    - trigger_function_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - trigger_not_exist
    - privilege_denied_non_superuser
    - rename_target_conflict
    - owner_not_exist
    - alter_nonexistent_trigger
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
      - key: branch_disable
        label: ALTER EVENT TRIGGER name DISABLE
      - key: branch_enable
        label: ALTER EVENT TRIGGER name ENABLE
      - key: branch_enable_replica
        label: ALTER EVENT TRIGGER name ENABLE REPLICA
      - key: branch_enable_always
        label: ALTER EVENT TRIGGER name ENABLE ALWAYS
      - key: branch_owner
        label: ALTER EVENT TRIGGER name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_rename
        label: ALTER EVENT TRIGGER name RENAME TO new_name
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
    enable_mode:
      label: 启用模式
      importance: non_important
      values:
      - ENABLE
      - ENABLE REPLICA
      - ENABLE ALWAYS
    new_owner_target:
      label: OWNER TO 目标形式
      importance: non_important
      values:
      - existing_role
      - nonexistent_role
      - CURRENT_ROLE
      - CURRENT_USER
      - SESSION_USER
    rename_conflict:
      label: RENAME TO 目标名称状态
      importance: non_important
      values:
      - new_name_unique
      - new_name_exists
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - non_superuser
    trigger_current_state:
      label: 触发器当前状态
      importance: non_important
      values:
      - enabled
      - disabled
      - enabled_replica
      - enabled_always
    trigger_name_shape:
      label: event trigger 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_name
    new_name_shape:
      label: 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_as_name
    new_owner_shape:
      label: 目标 owner 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - special_token
    session_replication_role:
      label: session_replication_role 设置
      importance: non_important
      values:
      - origin
      - replica
      - local
    trigger_function_state:
      label: 触发函数依赖状态
      importance: non_important
      values:
      - function_exists
      - function_not_exists
    trigger_not_exist:
      label: 目标 event trigger 不存在
      importance: non_important
      values:
      - trigger_exists
      - trigger_not_exists
    privilege_denied_non_superuser:
      label: 非 superuser 执行 ALTER EVENT TRIGGER
      importance: non_important
      values:
      - superuser_success
      - non_superuser_failure
    rename_target_conflict:
      label: RENAME 目标名称已存在
      importance: non_important
      values:
      - no_conflict
      - name_already_exists
    owner_not_exist:
      label: OWNER TO 目标角色不存在
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    alter_nonexistent_trigger:
      label: 修改不存在的 event trigger
      importance: non_important
      values:
      - trigger_exists
      - trigger_not_exists
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_event_trigger
      - catalog_query_evtenabled_field
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_event_trigger
      - drop_function
      - cascade_cleanup
  defaults:
    expected_status: success
    statement_branch: branch_disable
    object_state: exists
    privilege_level: superuser
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - enable_mode
    - new_owner_target
    - rename_conflict
    - privilege_level
    - trigger_current_state
    - trigger_name_shape
    - new_name_shape
    - new_owner_shape
    - session_replication_role
    - trigger_function_state
    - trigger_not_exist
    - privilege_denied_non_superuser
    - rename_target_conflict
    - owner_not_exist
    - alter_nonexistent_trigger
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
  rendering:
    statement_template: "ALTER EVENT TRIGGER {trigger_name} {alter_action} {alter_target}"
    verification_query_template: "SELECT evtname, evtenabled, evtevent FROM pg_event_trigger\
      \ WHERE evtname = '{trigger_name}'"
    factor_value_bindings: {}
```
