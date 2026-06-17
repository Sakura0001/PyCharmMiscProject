# 技能：DROP DATABASE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropdatabase.html

```sql
DROP DATABASE [ IF EXISTS ] name [ [ WITH ] ( option [, ...] ) ]

where option can be:
    FORCE
```

PG16 关键约束：
- 只能由 database owner 执行（superuser 也可以）
- 不能在连接到目标数据库时执行，必须先连接到其他数据库（如 postgres）
- 如果其他人连接到目标数据库，命令失败除非使用 FORCE
- FORCE：尝试终止所有现有连接到目标数据库的连接；通过 pg_terminate_backend 终止当前用户有权终止的连接
- 如果目标数据库有 prepared transactions、active logical replication slots 或 subscriptions，连接终止后仍可能保留，此时命令失败
- DROP DATABASE 不能撤销
- 不能在事务块内执行
- 删除数据库的目录条目和数据目录

## 语句作用

官方说明：DROP DATABASE — remove a database

该 reference 关注数据库对象的删除。DROP DATABASE 语法简单（单一顶层形式），核心维度是对象存在性、IF EXISTS 容错行为、FORCE 选项语义和连接状态处理。该语句不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP DATABASE 单一顶层形式）
- object_state：目标 database 对象状态（exists / not_exists）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句形态（省略 / 指定 IF EXISTS）
- force_option：WITH (FORCE) 选项形态（省略 / 指定 FORCE）
- privilege_level：执行权限（superuser / database_owner / non_owner）
- connection_state：目标数据库连接状态（无其他连接 / 有其他连接 / 当前连接到目标数据库）

### T3：对象名与输入形态因子
- database_name_shape：database 名称形态

### T4：依赖对象与环境因子
- active_connections：活动连接状态（无活动连接 / 有可终止连接 / 有不可终止连接）
- prepared_transactions：prepared transactions 存在性
- replication_slots：active logical replication slots 存在性
- subscriptions：subscriptions 存在性

### T5：异常与边界因子
- database_not_exist_no_if_exists：目标 database 不存在且无 IF EXISTS
- privilege_denied：非 owner 尝试删除
- connected_to_target_database：当前连接到目标数据库
- active_connections_without_force：有其他连接但未使用 FORCE
- force_with_unterminable_connections：FORCE 但有不可终止的连接
- inside_transaction_block：在事务块内执行
- drop_current_database：尝试删除当前连接的数据库

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP DATABASE 单一语法分支的所有可选子句组合。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖（object_state x expected_status）。
- T2 因子按规模控制策略参与组合，重点覆盖 FORCE 选项语义和连接状态。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 database 存在时的成功删除路径，以及目标 database 不存在时的失败路径。
- IF EXISTS 必须覆盖不存在对象的代表性 no-op 路径。
- FORCE 必须覆盖：有活动连接时使用 FORCE 成功终止并删除、FORCE 但有不可终止连接时失败。
- 不能在连接到目标数据库时执行 DROP DATABASE，样本必须连接到其他数据库后执行。
- 不能在事务块内执行 DROP DATABASE。
- 必须覆盖 owner 成功删除和 non_owner 失败删除的路径。
- 每个样本必须包含明确的前置对象准备、目标 DROP DATABASE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- if_exists_clause 挂靠到对象不存在场景的样本上。
- force_option 挂靠到有活动连接的样本上。
- connection_state 挂靠到 FORCE 相关场景的样本上。
- privilege_level 挂靠到 owner 成功和 non_owner 失败的样本上。
- T3 因子挂靠到代表性成功样本和失败样本上轮转注入。
- T5 因子按失败原因单独挂靠。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 形态、FORCE 选项语义和连接状态覆盖。
- 低优先级命名形态和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: database
  skill_name: drop_database
  official_source: https://www.postgresql.org/docs/16/sql-dropdatabase.html
  statement:
    key: drop_database
    name: DROP DATABASE
    aliases:
    - drop_database
    - DROP DATABASE
    purpose: DROP DATABASE — remove a database
  syntax_templates:
  - "DROP DATABASE [ IF EXISTS ] name [ [ WITH ] ( option [, ...] ) ]\nwhere option\
    \ can be:\n    FORCE"
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
    - force_option
    - privilege_level
    - connection_state
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - database_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - active_connections
    - prepared_transactions
    - replication_slots
    - subscriptions
  - tier: T5
    name: 异常与边界因子
    factors:
    - database_not_exist_no_if_exists
    - privilege_denied
    - connected_to_target_database
    - active_connections_without_force
    - force_with_unterminable_connections
    - inside_transaction_block
    - drop_current_database
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
      - key: branch_drop_database
        label: DROP DATABASE [ IF EXISTS ] name [ [ WITH ] ( FORCE ) ]
    object_state:
      label: 目标 database 对象状态
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
    force_option:
      label: WITH (FORCE) 选项形态
      importance: non_important
      values:
      - omitted
      - specified_force
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - database_owner
      - non_owner
    connection_state:
      label: 目标数据库连接状态
      importance: non_important
      values:
      - no_other_connections
      - has_other_connections
      - connected_to_target_database
    database_name_shape:
      label: database 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_name
    active_connections:
      label: 活动连接状态
      importance: non_important
      values:
      - no_active_connections
      - has_terminable_connections
      - has_unterminable_connections
    prepared_transactions:
      label: prepared transactions 存在性
      importance: non_important
      values:
      - no_prepared_transactions
      - has_prepared_transactions
    replication_slots:
      label: active logical replication slots 存在性
      importance: non_important
      values:
      - no_active_slots
      - has_active_slots
    subscriptions:
      label: subscriptions 存在性
      importance: non_important
      values:
      - no_subscriptions
      - has_subscriptions
    database_not_exist_no_if_exists:
      label: 目标 database 不存在且无 IF EXISTS
      importance: non_important
      values:
      - database_exists
      - database_not_exists_no_if_exists
    privilege_denied:
      label: 非 owner 尝试删除
      importance: non_important
      values:
      - owner_success
      - non_owner_failure
      - superuser_success
    connected_to_target_database:
      label: 当前连接到目标数据库
      importance: non_important
      values:
      - connected_to_different_database
      - connected_to_target_database
    active_connections_without_force:
      label: 有其他连接但未使用 FORCE
      importance: non_important
      values:
      - no_connections_or_force_used
      - connections_without_force
    force_with_unterminable_connections:
      label: FORCE 但有不可终止的连接
      importance: non_important
      values:
      - all_connections_terminable
      - unterminable_connections_remain
    inside_transaction_block:
      label: 在事务块内执行
      importance: non_important
      values:
      - outside_transaction
      - inside_transaction
    drop_current_database:
      label: 尝试删除当前连接的数据库
      importance: non_important
      values:
      - different_database
      - current_database
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_database_absence
      - error_assertion
      - notice_assertion_if_exists
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - force_drop_database
      - drop_database_simple
  defaults:
    expected_status: success
    object_state: exists
    if_exists_clause: omitted
    force_option: omitted
    connection_state: no_other_connections
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - force_option
    - privilege_level
    - connection_state
    - database_name_shape
    - active_connections
    - prepared_transactions
    - replication_slots
    - subscriptions
    - database_not_exist_no_if_exists
    - privilege_denied
    - connected_to_target_database
    - active_connections_without_force
    - force_with_unterminable_connections
    - inside_transaction_block
    - drop_current_database
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 100
    preserve_axes_first:
    - statement_branch
  rendering:
    statement_template: "DROP DATABASE {if_exists} {database_name} {force_clause}"
    verification_query_template: "SELECT count(*) FROM pg_database WHERE datname\
      \ = '{database_name}'"
    factor_value_bindings: {}
```
