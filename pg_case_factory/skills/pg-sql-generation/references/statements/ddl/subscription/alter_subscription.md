# 技能：ALTER SUBSCRIPTION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altersubscription.html

```sql
ALTER SUBSCRIPTION name CONNECTION 'conninfo'
ALTER SUBSCRIPTION name SET PUBLICATION publication_name [, ...] [ WITH ( publication_option [= value] [, ... ] ) ]
ALTER SUBSCRIPTION name ADD PUBLICATION publication_name [, ...] [ WITH ( publication_option [= value] [, ... ] ) ]
ALTER SUBSCRIPTION name DROP PUBLICATION publication_name [, ...] [ WITH ( publication_option [= value] [, ... ] ) ]
ALTER SUBSCRIPTION name REFRESH PUBLICATION [ WITH ( refresh_option [= value] [, ... ] ) ]
ALTER SUBSCRIPTION name ENABLE
ALTER SUBSCRIPTION name DISABLE
ALTER SUBSCRIPTION name SET ( subscription_parameter [= value] [, ... ] )
ALTER SUBSCRIPTION name SKIP ( skip_option = value )
ALTER SUBSCRIPTION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER SUBSCRIPTION name RENAME TO new_name
```

**重要约束：**
- ALTER SUBSCRIPTION 需要 superuser 权限。
- 共 11 个语法分支，涵盖连接变更、publication 管理（SET/ADD/DROP）、刷新、启用/禁用、参数设置、跳过、所有权变更和重命名。
- REFRESH PUBLICATION 需要复制连接，属于非事务环境依赖。
- ENABLE / DISABLE 切换订阅的启用状态。
- SET ( subscription_parameter ) 修改订阅参数。
- SKIP ( skip_option = value ) 设置跳过选项（PG16 新增）。
- OWNER TO 需要超级用户权限。
- RENAME TO 需要超级用户权限。

## 语句作用

官方说明：ALTER SUBSCRIPTION — change the definition of a subscription

该 reference 关注订阅修改语句的 11 个语法分支、publication 操作（SET/ADD/DROP）、REFRESH PUBLICATION 复制依赖、ENABLE/DISABLE 状态切换、参数设置、SKIP 选项、权限边界和成功/失败路径。ALTER SUBSCRIPTION 需要 superuser 权限且涉及复制连接依赖。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（11 个 synopsis 分支）
- subscription_state：目标 subscription 存在状态
- expected_status：预期结果

### T2：重要行为因子
- publication_operation：publication 操作类型（SET / ADD / DROP）
- refresh_publication_option：REFRESH PUBLICATION WITH 选项
- enable_disable_behavior：ENABLE / DISABLE 状态切换
- subscription_parameter：SET ( subscription_parameter ) 参数形态
- skip_option：SKIP ( skip_option ) 选项形态
- owner_to_shape：OWNER TO 子句形态
- rename_behavior：RENAME 行为
- connection_change：CONNECTION 变更行为

### T3：对象名与输入形态因子
- subscription_name_shape：subscription 名形态
- publication_name_shape：publication 名形态
- new_name_shape：新名形态（RENAME 分支）
- conninfo_string_shape：连接信息字符串形态（CONNECTION 分支）

### T4：依赖对象与环境因子
- **ALTER SUBSCRIPTION 涉及复制连接依赖。REFRESH PUBLICATION 分支需要复制连接可用。**
- executor_privilege：执行者权限上下文（superuser 必须）
- replication_connection：复制连接可用性
- publication_dependency：远程 publication 存在状态

### T5：异常与边界因子
- nonexistent_subscription：subscription 不存在
- privilege_insufficient：权限不足（非 superuser）
- replication_connection_failure：复制连接失败
- publication_not_exists_on_remote：远程 publication 不存在
- disable_while_enabled：状态切换边界
- drop_all_publications：DROP PUBLICATION 删除所有 publication 时的限制

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖所有 11 个 ALTER SUBSCRIPTION 语法分支。
- 覆盖 publication 操作类型（SET / ADD / DROP）的代表性取值。
- 覆盖 REFRESH PUBLICATION 的复制连接依赖。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 subscription（需要先创建 publication 和复制连接），并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 subscription 存在时的成功修改路径、subscription 不存在时的失败路径。
- 各分支需要保持独立归因。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 复制连接依赖必须在生命周期计划中显式标注，不得伪造为普通成功路径。
- 每个样本必须包含明确的前置准备、目标 ALTER SUBSCRIPTION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或复制连接依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有 11 个语法分支全覆盖
  - subscription 存在/不存在全覆盖
  - 成功/失败路径全覆盖
  - superuser 权限路径全覆盖
- 次优先保证：
  - publication SET / ADD / DROP 操作类型代表性覆盖
  - REFRESH PUBLICATION 复制连接依赖代表性覆盖
  - ENABLE / DISABLE 状态切换代表性覆盖
  - SKIP 选项代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: subscription
  skill_name: alter_subscription
  official_source: https://www.postgresql.org/docs/16/sql-altersubscription.html
  statement:
    key: alter_subscription
    name: ALTER SUBSCRIPTION
    aliases:
    - alter_subscription
    - ALTER SUBSCRIPTION
    purpose: ALTER SUBSCRIPTION — change the definition of a subscription
  syntax_templates:
  - "ALTER SUBSCRIPTION name CONNECTION 'conninfo'"
  - "ALTER SUBSCRIPTION name SET PUBLICATION publication_name [, ...] [ WITH ( publication_option [= value] [, ... ] ) ]"
  - "ALTER SUBSCRIPTION name ADD PUBLICATION publication_name [, ...] [ WITH ( publication_option [= value] [, ... ] ) ]"
  - "ALTER SUBSCRIPTION name DROP PUBLICATION publication_name [, ...] [ WITH ( publication_option [= value] [, ... ] ) ]"
  - "ALTER SUBSCRIPTION name REFRESH PUBLICATION [ WITH ( refresh_option [= value] [, ... ] ) ]"
  - "ALTER SUBSCRIPTION name ENABLE"
  - "ALTER SUBSCRIPTION name DISABLE"
  - "ALTER SUBSCRIPTION name SET ( subscription_parameter [= value] [, ... ] )"
  - "ALTER SUBSCRIPTION name SKIP ( skip_option = value )"
  - "ALTER SUBSCRIPTION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER SUBSCRIPTION name RENAME TO new_name"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - subscription_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - publication_operation
    - refresh_publication_option
    - enable_disable_behavior
    - subscription_parameter
    - skip_option
    - owner_to_shape
    - rename_behavior
    - connection_change
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - subscription_name_shape
    - publication_name_shape
    - new_name_shape
    - conninfo_string_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - replication_connection
    - publication_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_subscription
    - privilege_insufficient
    - replication_connection_failure
    - publication_not_exists_on_remote
    - disable_while_enabled
    - drop_all_publications
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
      - key: branch_connection
        label: ALTER SUBSCRIPTION name CONNECTION 'conninfo'
      - key: branch_set_publication
        label: ALTER SUBSCRIPTION name SET PUBLICATION
      - key: branch_add_publication
        label: ALTER SUBSCRIPTION name ADD PUBLICATION
      - key: branch_drop_publication
        label: ALTER SUBSCRIPTION name DROP PUBLICATION
      - key: branch_refresh_publication
        label: ALTER SUBSCRIPTION name REFRESH PUBLICATION
      - key: branch_enable
        label: ALTER SUBSCRIPTION name ENABLE
      - key: branch_disable
        label: ALTER SUBSCRIPTION name DISABLE
      - key: branch_set_parameters
        label: ALTER SUBSCRIPTION name SET ( subscription_parameter )
      - key: branch_skip
        label: ALTER SUBSCRIPTION name SKIP ( skip_option )
      - key: branch_owner_to
        label: ALTER SUBSCRIPTION name OWNER TO new_owner
      - key: branch_rename
        label: ALTER SUBSCRIPTION name RENAME TO new_name
    subscription_state:
      label: 目标 subscription 存在状态
      importance: important
      values:
      - exists
      - non_existent
      - exists_enabled
      - exists_disabled
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    publication_operation:
      label: publication 操作类型
      importance: non_important
      values:
      - set_publication_single
      - set_publication_multiple
      - add_publication_single
      - add_publication_multiple
      - drop_publication_single
      - drop_publication_multiple
    refresh_publication_option:
      label: REFRESH PUBLICATION WITH 选项
      importance: non_important
      values:
      - without_with_clause
      - with_copy_data_true
      - with_copy_data_false
    enable_disable_behavior:
      label: ENABLE / DISABLE 状态切换
      importance: non_important
      values:
      - enable_from_disabled
      - disable_from_enabled
      - enable_already_enabled_no_effect
    subscription_parameter:
      label: SET ( subscription_parameter ) 参数形态
      importance: non_important
      values:
      - single_parameter
      - multiple_parameters
      - synchronous_commit
      - binary
      - stream
    skip_option:
      label: SKIP ( skip_option ) 选项形态
      importance: non_important
      values:
      - skip_lsn
    owner_to_shape:
      label: OWNER TO 子句形态
      importance: non_important
      values:
      - explicit_role_name
      - current_role_keyword
      - current_user_keyword
      - session_user_keyword
    rename_behavior:
      label: RENAME 行为
      importance: non_important
      values:
      - rename_to_new_name
      - rename_to_existing_name_conflict
    connection_change:
      label: CONNECTION 变更行为
      importance: non_important
      values:
      - valid_new_conninfo
      - invalid_new_conninfo
    subscription_name_shape:
      label: subscription 名形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - non_existent_name
    publication_name_shape:
      label: publication 名形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
    new_name_shape:
      label: 新名形态（RENAME 分支）
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - existing_name_conflict
    conninfo_string_shape:
      label: 连接信息字符串形态（CONNECTION 分支）
      importance: non_important
      values:
      - valid_conninfo
      - invalid_conninfo
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - non_superuser
    replication_connection:
      label: 复制连接可用性
      importance: non_important
      values:
      - connection_available
      - connection_unavailable
    publication_dependency:
      label: 远程 publication 存在状态
      importance: non_important
      values:
      - publication_exists_on_remote
      - publication_not_exists_on_remote
    nonexistent_subscription:
      label: subscription 不存在
      importance: non_important
      values:
      - subscription_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_altering_subscription
    replication_connection_failure:
      label: 复制连接失败
      importance: non_important
      values:
      - connection_refused_on_refresh
    publication_not_exists_on_remote:
      label: 远程 publication 不存在
      importance: non_important
      values:
      - remote_publication_not_exists
    disable_while_enabled:
      label: 状态切换边界
      importance: non_important
      values:
      - disable_active_subscription
    drop_all_publications:
      label: DROP 所有 publication
      importance: non_important
      values:
      - dropping_last_publication
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_subscription_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_subscription
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - subscription_state
    - expected_status
    non_main_factors:
    - publication_operation
    - refresh_publication_option
    - enable_disable_behavior
    - subscription_parameter
    - skip_option
    - owner_to_shape
    - rename_behavior
    - connection_change
    - subscription_name_shape
    - publication_name_shape
    - new_name_shape
    - conninfo_string_shape
    - executor_privilege
    - replication_connection
    - publication_dependency
    - nonexistent_subscription
    - privilege_insufficient
    - replication_connection_failure
    - publication_not_exists_on_remote
    - disable_while_enabled
    - drop_all_publications
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - subscription_state
  rendering:
    statement_template: "ALTER SUBSCRIPTION {name} {operation}"
    verification_query_template: "SELECT subname, subenabled FROM pg_subscription WHERE subname = '{name}'"
    factor_value_bindings: {}
```
