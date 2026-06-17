# 技能：CREATE SUBSCRIPTION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createsubscription.html

```sql
CREATE SUBSCRIPTION subscription_name
    CONNECTION 'conninfo'
    PUBLICATION publication_name [, ...]
    [ WITH ( subscription_parameter [= value] [, ... ] ) ]
```

**重要约束：**
- CREATE SUBSCRIPTION 需要 superuser 权限。
- CONNECTION 'conninfo' 包含连接信息字符串（host、port、dbname、user、password 等）。
- PUBLICATION 必须指定至少一个 publication_name。
- subscription_parameter 包括：connect（true/false）、enabled（true/false）、create_slot（true/false）、slot_name、sync_method（table_name_list）、synchronous_commit、stream（true/false）、binary（true/false）、disable_on_error（true/false）、run_as_owner（true/false）、origin（none/any）、copy_data（true/false）。
- CREATE SUBSCRIPTION 需要复制连接到发布端数据库，属于非事务环境依赖。
- subscription 不支持 schema 限定（subscription 不属于 schema）。

## 语句作用

官方说明：CREATE SUBSCRIPTION — define a new subscription

该 reference 关注订阅定义语句的 CONNECTION 字符串、PUBLICATION 列表、WITH 参数组合、权限边界和成功/失败路径。CREATE SUBSCRIPTION 需要 superuser 权限且涉及复制连接依赖。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE SUBSCRIPTION 仅有一条 synopsis 形式）
- subscription_identity：目标 subscription 存在状态
- expected_status：预期结果

### T2：重要行为因子
- with_parameter_clause：WITH ( subscription_parameter ) 子句形态
- publication_list：PUBLICATION 列表形态
- connection_info：CONNECTION 字符串形态
- copy_data_behavior：copy_data 参数行为
- slot_name_behavior：slot_name 参数行为

### T3：对象名与输入形态因子
- subscription_name_shape：subscription 名标识符形态
- publication_name_shape：publication 名形态
- conninfo_string_shape：连接信息字符串形态

### T4：依赖对象与环境因子
- **CREATE SUBSCRIPTION 需要复制连接到发布端数据库。这是非事务环境依赖，必须在生命周期计划中显式标注。**
- executor_privilege：执行者权限上下文（superuser 必须）
- replication_connection：复制连接可用性
- publication_dependency：远程 publication 存在状态

### T5：异常与边界因子
- duplicate_subscription_name：subscription 名冲突
- privilege_insufficient：权限不足（非 superuser）
- replication_connection_failure：复制连接失败
- publication_not_exists_on_remote：远程 publication 不存在
- invalid_conninfo：连接信息字符串非法

### T6：验证与清理因子
- verification_mode：验证方式（pg_subscription 目录查询）
- cleanup_mode：清理方式（DROP SUBSCRIPTION）

## 覆盖策略

- 覆盖 subscription 不存在（成功创建）/ 已存在（失败冲突）核心状态。
- 覆盖 WITH 参数的代表性取值（connect / enabled / copy_data / slot_name 等）。
- 覆盖复制连接可用性/失败状态。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 subscription 成功创建、重名冲突、权限不足与复制连接失败路径。
- CREATE SUBSCRIPTION 不支持 IF NOT EXISTS，重名路径必定失败。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 复制连接依赖必须在生命周期计划中显式标注，不得伪造为普通成功路径。
- 每个样本必须包含明确的前置准备、目标 CREATE SUBSCRIPTION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或复制连接依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - subscription 存在/不存在全覆盖
  - 成功/失败路径全覆盖
  - superuser 权限路径全覆盖
- 次优先保证：
  - WITH 参数代表性覆盖
  - 复制连接失败路径代表性覆盖
  - 单/多 publication 列表代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: subscription
  skill_name: create_subscription
  official_source: https://www.postgresql.org/docs/16/sql-createsubscription.html
  statement:
    key: create_subscription
    name: CREATE SUBSCRIPTION
    aliases:
    - create_subscription
    - CREATE SUBSCRIPTION
    purpose: CREATE SUBSCRIPTION — define a new subscription
  syntax_templates:
  - "CREATE SUBSCRIPTION subscription_name\n    CONNECTION 'conninfo'\n    PUBLICATION publication_name [, ...]\n    [ WITH ( subscription_parameter [= value] [, ... ] ) ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - subscription_identity
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - with_parameter_clause
    - publication_list
    - connection_info
    - copy_data_behavior
    - slot_name_behavior
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - subscription_name_shape
    - publication_name_shape
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
    - duplicate_subscription_name
    - privilege_insufficient
    - replication_connection_failure
    - publication_not_exists_on_remote
    - invalid_conninfo
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
      - key: branch_create_subscription
        label: CREATE SUBSCRIPTION subscription_name CONNECTION 'conninfo' PUBLICATION publication_name [ WITH ( parameters ) ]
    subscription_identity:
      label: 目标 subscription 存在状态
      importance: important
      values:
      - not_exists
      - exists
      - reserved_word_name
      - quoted_duplicate
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    with_parameter_clause:
      label: WITH 参数子句
      importance: important
      values:
      - omitted
      - connect_true_enabled_true
      - connect_false_enabled_false
      - copy_data_true
      - copy_data_false
      - slot_name_explicit
      - create_slot_false
      - synchronous_commit_on
      - binary_true
      - stream_true
      - disable_on_error_true
      - run_as_owner_true
      - multiple_parameters
    publication_list:
      label: PUBLICATION 列表形态
      importance: non_important
      values:
      - single_publication
      - multiple_publications
    connection_info:
      label: CONNECTION 字符串形态
      importance: non_important
      values:
      - valid_conninfo
      - minimal_conninfo
    copy_data_behavior:
      label: copy_data 参数行为
      importance: non_important
      values:
      - copy_data_true
      - copy_data_false
    slot_name_behavior:
      label: slot_name 参数行为
      importance: non_important
      values:
      - default_auto_slot
      - explicit_slot_name
    subscription_name_shape:
      label: subscription 名标识符形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - reserved_word_name
      - non_existing_name
    publication_name_shape:
      label: publication 名形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
    conninfo_string_shape:
      label: 连接信息字符串形态
      importance: non_important
      values:
      - valid_conninfo_string
      - invalid_conninfo_string
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
    duplicate_subscription_name:
      label: subscription 名冲突
      importance: non_important
      values:
      - same_name_exists
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_creating_subscription
    replication_connection_failure:
      label: 复制连接失败
      importance: non_important
      values:
      - connection_refused
      - authentication_failed
    publication_not_exists_on_remote:
      label: 远程 publication 不存在
      importance: non_important
      values:
      - remote_publication_not_exists
    invalid_conninfo:
      label: 连接信息非法
      importance: non_important
      values:
      - malformed_conninfo
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
    - subscription_identity
    - expected_status
    non_main_factors:
    - with_parameter_clause
    - publication_list
    - connection_info
    - copy_data_behavior
    - slot_name_behavior
    - subscription_name_shape
    - publication_name_shape
    - conninfo_string_shape
    - executor_privilege
    - replication_connection
    - publication_dependency
    - duplicate_subscription_name
    - privilege_insufficient
    - replication_connection_failure
    - publication_not_exists_on_remote
    - invalid_conninfo
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - subscription_identity
  rendering:
    statement_template: "CREATE SUBSCRIPTION {subscription_name} CONNECTION '{conninfo}' PUBLICATION {publication_names} [ WITH ( {parameters} ) ]"
    verification_query_template: "SELECT subname FROM pg_subscription WHERE subname = '{subscription_name}'"
    factor_value_bindings: {}
```
