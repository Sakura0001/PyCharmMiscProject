# 技能：ALTER AGGREGATE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alteraggregate.html

```sql
ALTER AGGREGATE name ( aggregate_signature ) RENAME TO new_name
ALTER AGGREGATE name ( aggregate_signature )
                OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER AGGREGATE name ( aggregate_signature ) SET SCHEMA new_schema

where aggregate_signature is:

* |
[ argmode ] [ argname ] argtype [ , ... ] |
[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]
```

**重要行为说明**：
- ALTER AGGREGATE 有三个语法分支：RENAME TO、OWNER TO、SET SCHEMA。
- aggregate_signature 用于标识目标聚合函数：`*` 表示零参数聚合，ORDER BY 分隔 direct/aggregated 参数。
- argname 不参与 PostgreSQL 聚合函数身份判断（仅 argtype 决定身份）。
- OWNER TO 要求执行用户能 SET ROLE 到新 Owner，且新 Owner 须在聚合函数所在 schema 有 CREATE 权限。超级用户可绕过此限制。
- SET SCHEMA 要求执行用户有目标 schema 的 CREATE 权限。
- 有序集聚合签名推荐使用 ORDER BY 形式；省略 ORDER BY 合并两列列表也合法（缩写形式）。

## 语句作用

官方说明：ALTER AGGREGATE — change the definition of an aggregate function

该 reference 关注聚合函数修改语句的语法分支、聚合签名形态、权限边界与目标对象状态，不负责覆盖表/列/索引类型组合。

ALTER AGGREGATE **不涉及列类型组合**，具体表现为：
- aggregate_signature 中的 argtype 是聚合函数身份标识，但不需要按列类型展开
- 签名匹配是核心关注点，而非类型组合覆盖

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（RENAME_TO、OWNER_TO、SET_SCHEMA）
- aggregate_signature：聚合签名形态（star_zero_arg、single_argtype、multi_argtype、ordered_set_signature、abbreviated_ordered_set）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- aggregate_form：聚合函数形态（single_arg、multi_arg、zero_arg、ordered_set）
- target_state：目标状态（new_name_available、new_name_conflict、new_owner_available、new_owner_unavailable、new_schema_available、new_schema_conflict）

### T3：对象名与输入形态因子
- aggregate_name_shape：聚合函数名称形态（plain_identifier、quoted_identifier、schema_qualified）
- new_name_shape：新名称形态（plain_identifier、quoted_identifier、reserved_word）— 仅 RENAME TO
- new_owner_shape：新 Owner 形态（plain_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER）— 仅 OWNER TO
- new_schema_shape：新 Schema 形态（existing_schema、nonexistent_schema）— 仅 SET SCHEMA

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、aggregate_owner、non_owner）
- owner_membership：Owner 成员关系（member_of_new_owner、not_member_of_new_owner）

### T5：异常与边界因子
- aggregate_not_exists：聚合函数不存在 → error
- signature_mismatch：签名参数个数或类型错误 → error
- new_name_conflict：RENAME TO 目标名称已存在同签名聚合 → error
- new_owner_not_exists：OWNER TO 目标 role 不存在 → error
- new_schema_not_exists：SET SCHEMA 目标 schema 不存在 → error
- insufficient_privilege：非 Owner 执行 ALTER → error
- star_mismatch：`*` 被错误用于非零参数聚合 → error

### T6：验证与清理因子
- verification_mode：验证方式（pg_aggregate_catalog_query、pg_proc_query、pg_aggregate_actual_execution）
- cleanup_mode：清理方式（DROP_AGGREGATE、DROP_AGGREGATE_IF_EXISTS、DROP_AGGREGATE_CASCADE）

## 覆盖策略

- 必须覆盖 ALTER AGGREGATE 的三个语法分支（RENAME TO、OWNER TO、SET SCHEMA）。
- 必须覆盖签名形态：`*`、单参数、多参数、有序集、缩写形式。
- 不需要覆盖所有基表列类型；签名中的 argtype 是身份标识而非列类型组合。
- T1/T2 绑定组合使用"聚合函数形态 + 合法签名"做主覆盖，不做无约束笛卡尔积。
- T3 因子按分支挂靠：new_name 仅挂到 RENAME TO，new_owner 仅挂到 OWNER TO，new_schema 仅挂到 SET SCHEMA。
- T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建用于成功路径的用户自定义聚合函数，不能直接改写内置聚合函数。
- 必须为每种聚合函数形态准备匹配的 CREATE AGGREGATE 前置对象。
- 单参数、多参数、零参数、有序集聚合函数都必须有成功修改路径。
- ALTER AGGREGATE name (aggregate_signature) 中的签名必须与目标聚合函数身份一致。
- RENAME TO 失败路径必须覆盖目标名称已存在同签名聚合函数。
- OWNER TO 成功路径依赖目标 role 存在且执行用户能成为该 role；失败路径必须覆盖 role 不存在或无成员关系。
- OWNER TO CURRENT_ROLE / CURRENT_USER / SESSION_USER 必须作为独立代表性分支覆盖。
- SET SCHEMA 成功路径依赖目标 schema 存在并具备 CREATE 权限；失败路径必须覆盖目标 schema 不存在、同名冲突。
- 非 Owner 用户执行 ALTER AGGREGATE 应作为失败路径保留。
- 不得修改 PostgreSQL 内置 pg_catalog 聚合函数。

## 挂靠规则

- T3 因子按分支挂靠：new_name 仅挂到 RENAME TO，new_owner 仅挂到 OWNER TO，new_schema 仅挂到 SET SCHEMA。
- T4 权限因子挂靠到所有语法分支的代表性成功和失败样本上。
- T5 异常与边界因子挂靠到对应可归因分支。
- T6 依赖因子挂靠到稳定成功路径上，优先选择单参数、多参数和有序集聚合各至少一个样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏语句分支、聚合签名、权限预期和成功/失败归因的可识别性。

## 规模控制规则

- 优先保证：
  - 三个语法分支全覆盖
  - T1/T2 合法绑定组合全覆盖
  - 单参数、多参数、零参数、有序集聚合全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - new_name / new_owner / new_schema 的合法、冲突、不存在取值全覆盖
  - CURRENT_ROLE、CURRENT_USER、SESSION_USER 目标 Owner 形式全覆盖
  - 依赖视图/函数代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: aggregate
  skill_name: alter_aggregate
  official_source: https://www.postgresql.org/docs/16/sql-alteraggregate.html
  statement:
    key: alter_aggregate
    name: ALTER AGGREGATE
    aliases:
    - ALTER AGGREGATE
    - alter aggregate
    - alter_aggregate
    purpose: change the definition of an aggregate function
  syntax_templates:
  - "ALTER AGGREGATE name ( aggregate_signature ) RENAME TO new_name"
  - "ALTER AGGREGATE name ( aggregate_signature ) OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER AGGREGATE name ( aggregate_signature ) SET SCHEMA new_schema"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - aggregate_signature
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - aggregate_form
    - target_state
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - aggregate_name_shape
    - new_name_shape
    - new_owner_shape
    - new_schema_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - owner_membership
  - tier: T5
    name: 异常与边界因子
    factors:
    - aggregate_not_exists
    - signature_mismatch
    - new_name_conflict
    - new_owner_not_exists
    - new_schema_not_exists
    - insufficient_privilege
    - star_mismatch
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
        label: RENAME TO
      - key: branch_owner
        label: OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_set_schema
        label: SET SCHEMA
    aggregate_signature:
      label: 聚合签名形态
      importance: important
      values:
      - key: star_zero_arg
        label: "* (零参数聚合签名)"
      - key: single_argtype
        label: 单参数签名 (如 integer)
      - key: multi_argtype
        label: 多参数签名 (如 integer, text)
      - key: ordered_set_signature
        label: 有序集签名 (direct_args ORDER BY aggregated_args)
      - key: abbreviated_ordered_set
        label: 缩写有序集签名 (合并两列列表，省略ORDER BY)
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    aggregate_form:
      label: 聚合函数形态
      importance: important
      values:
      - key: single_arg
        label: 单参数聚合函数
      - key: multi_arg
        label: 多参数聚合函数
      - key: zero_arg
        label: 零参数聚合函数
      - key: ordered_set
        label: 有序集聚合函数
    target_state:
      label: 目标状态
      importance: important
      values:
      - key: new_name_available
        label: 新名称可用 (仅RENAME TO)
      - key: new_name_conflict
        label: 新名称已存在同签名聚合 (仅RENAME TO)
      - key: new_owner_available
        label: 新Owner可用 (仅OWNER TO)
      - key: new_owner_unavailable
        label: 新Owner不可用 (仅OWNER TO)
      - key: new_schema_available
        label: 新Schema可用 (仅SET SCHEMA)
      - key: new_schema_conflict
        label: 新Schema中有同名聚合 (仅SET SCHEMA)
    aggregate_name_shape:
      label: 聚合函数名称形态
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符
      - key: schema_qualified
        label: Schema限定标识符
    new_name_shape:
      label: 新名称形态 (仅RENAME TO)
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
    new_owner_shape:
      label: 新Owner形态 (仅OWNER TO)
      importance: non_important
      values:
      - key: plain_role
        label: 普通角色名
      - key: CURRENT_ROLE
        label: CURRENT_ROLE
      - key: CURRENT_USER
        label: CURRENT_USER
      - key: SESSION_USER
        label: SESSION_USER
    new_schema_shape:
      label: 新Schema形态 (仅SET SCHEMA)
      importance: non_important
      values:
      - key: existing_schema
        label: 存在的Schema
      - key: nonexistent_schema
        label: 不存在的Schema → error
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: aggregate_owner
        label: 聚合函数Owner
      - key: non_owner
        label: 非 Owner → error
    owner_membership:
      label: Owner成员关系
      importance: non_important
      values:
      - key: member_of_new_owner
        label: 执行用户是新Owner的成员 (可SET ROLE)
      - key: not_member_of_new_owner
        label: 执行用户不是新Owner的成员 → error
    aggregate_not_exists:
      label: 聚合函数不存在
      importance: non_important
      values:
      - key: not_exists
        label: 聚合函数不存在 → error
    signature_mismatch:
      label: 签名不匹配
      importance: non_important
      values:
      - key: wrong_arg_count
        label: 签名参数个数错误 → error
      - key: wrong_arg_type
        label: 签名参数类型错误 → error
    new_name_conflict:
      label: 新名称冲突 (仅RENAME TO)
      importance: non_important
      values:
      - key: same_signature_conflict
        label: 目标名称已存在同签名聚合 → error
    new_owner_not_exists:
      label: 新Owner不存在 (仅OWNER TO)
      importance: non_important
      values:
      - key: nonexistent_role
        label: 目标role不存在 → error
    new_schema_not_exists:
      label: 新Schema不存在 (仅SET SCHEMA)
      importance: non_important
      values:
      - key: nonexistent_schema
        label: 目标schema不存在 → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_owner
        label: 非Owner执行ALTER → error
      - key: no_create_on_schema
        label: 无目标Schema的CREATE权限 → error
    star_mismatch:
      label: "*签名误用"
      importance: non_important
      values:
      - key: star_for_nonzero_arg
        label: "*被用于非零参数聚合 → error (找不到匹配聚合)"
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_aggregate_catalog_query
        label: pg_aggregate 系统目录查询
      - key: pg_proc_query
        label: pg_proc 系统目录查询 (proowner等)
      - key: pg_aggregate_actual_execution
        label: 实际执行聚合函数验证行为
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_AGGREGATE
        label: DROP AGGREGATE name (signature)
      - key: DROP_AGGREGATE_IF_EXISTS
        label: DROP AGGREGATE IF EXISTS name (signature)
      - key: DROP_AGGREGATE_CASCADE
        label: DROP AGGREGATE name (signature) CASCADE
  notes:
    three_branches: ALTER AGGREGATE 有三个分支（RENAME TO、OWNER TO、SET SCHEMA），各分支依赖不同。
    signature_identity: aggregate_signature 中的 argtype 决定聚合函数身份，argname 不参与。
    owner_to_requires_set_role: OWNER TO 要求执行用户能 SET ROLE 到新 Owner。
    set_schema_requires_create: SET SCHEMA 要求执行用户有目标 Schema 的 CREATE 权限。
    ordered_set_abbreviated: 有序集聚合签名可使用缩写形式（省略 ORDER BY）。
    must_use_user_defined: 不得修改 PostgreSQL 内置 pg_catalog 聚合函数。
  defaults:
    expected_status: success
    aggregate_signature: single_argtype
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - aggregate_signature
    - expected_status
    non_main_factors:
    - aggregate_form
    - target_state
    - aggregate_name_shape
    - new_name_shape
    - new_owner_shape
    - new_schema_shape
    - privilege_level
    - owner_membership
    - aggregate_not_exists
    - signature_mismatch
    - new_name_conflict
    - new_owner_not_exists
    - new_schema_not_exists
    - insufficient_privilege
    - star_mismatch
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - aggregate_signature
  rendering:
    statement_template: "ALTER AGGREGATE {aggregate_name} ( {signature} ) {alter_action}"
    verification_query_template: "SELECT * FROM pg_aggregate WHERE aggfnoid = '{aggregate_name}'::regproc"
    factor_value_bindings:
      statement_branch:
        branch_rename: "RENAME TO {new_name}"
        branch_owner: "OWNER TO {new_owner}"
        branch_set_schema: "SET SCHEMA {new_schema}"
```
