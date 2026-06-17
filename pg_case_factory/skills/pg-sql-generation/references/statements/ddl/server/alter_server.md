# 技能：ALTER SERVER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterserver.html

```sql
ALTER SERVER name [ VERSION 'new_version' ]
    [ OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] ) ]
ALTER SERVER name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER SERVER name RENAME TO new_name
```

**重要约束：**
- ALTER SERVER 需要 superuser 权限（或 owner 且有 USAGE ON FOREIGN DATA WRAPPER 权限）。
- 第一种形式修改 VERSION 和 OPTIONS：ADD 添加新选项，SET 修改已有选项值，DROP 移除选项。
- OWNER TO 需要超级用户权限或 CREATEROLE 加管理员权限。
- RENAME TO 需要超级用户权限。
- server 不支持 schema 限定（server 不属于 schema）。

## 语句作用

官方说明：ALTER SERVER — change the definition of a foreign server

该 reference 关注外部服务器修改语句的 3 个语法分支（VERSION/OPTIONS 变更 / OWNER TO / RENAME TO）、OPTIONS 操作类型、权限边界和成功/失败路径。ALTER SERVER 需要 superuser 权限。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（3 个 synopsis 分支）
- server_state：目标 server 存在状态
- expected_status：预期结果

### T2：重要行为因子
- version_clause：VERSION 子句形态
- options_operation：OPTIONS 操作类型（ADD / SET / DROP）
- owner_to_shape：OWNER TO 子句形态
- rename_behavior：RENAME 行为

### T3：对象名与输入形态因子
- server_name_shape：server 名形态
- new_name_shape：新名形态（RENAME 分支）
- new_owner_shape：新 owner 形态（OWNER TO 分支）
- option_key_value_shape：选项键值形态

### T4：依赖对象与环境因子
- **ALTER SERVER 不涉及表/列/索引组合。它依赖已存在的 FDW 对象。**
- executor_privilege：执行者权限上下文
- user_mapping_dependency：user mapping 依赖状态

### T5：异常与边界因子
- nonexistent_server：server 不存在
- privilege_insufficient：权限不足
- nonexistent_owner：owner 不存在
- nonexistent_new_name_conflict：新名冲突
- fdw_validator_rejection：FDW validator 拒绝 OPTIONS

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖所有 3 个 ALTER SERVER 语法分支。
- 覆盖 OPTIONS 的 ADD / SET / DROP 操作类型。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 server（需要先创建 FDW），并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 server 存在时的成功修改路径、server 不存在时的失败路径。
- VERSION/OPTIONS / OWNER TO / RENAME TO 各分支需要保持独立归因。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 每个样本必须包含明确的前置 FDW 准备、目标 ALTER SERVER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有 3 个语法分支全覆盖
  - server 存在/不存在全覆盖
  - 成功/失败路径全覆盖
  - superuser 权限路径全覆盖
- 次优先保证：
  - OPTIONS ADD / SET / DROP 操作类型代表性覆盖
  - VERSION 子句代表性覆盖
  - CURRENT_ROLE / CURRENT_USER / SESSION_USER 代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: server
  skill_name: alter_server
  official_source: https://www.postgresql.org/docs/16/sql-alterserver.html
  statement:
    key: alter_server
    name: ALTER SERVER
    aliases:
    - alter_server
    - ALTER SERVER
    purpose: ALTER SERVER — change the definition of a foreign server
  syntax_templates:
  - "ALTER SERVER name [ VERSION 'new_version' ]\n    [ OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] ) ]"
  - "ALTER SERVER name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER SERVER name RENAME TO new_name"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - server_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - version_clause
    - options_operation
    - owner_to_shape
    - rename_behavior
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - server_name_shape
    - new_name_shape
    - new_owner_shape
    - option_key_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - user_mapping_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_server
    - privilege_insufficient
    - nonexistent_owner
    - nonexistent_new_name_conflict
    - fdw_validator_rejection
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
      - key: branch_version_options
        label: ALTER SERVER name [ VERSION ] [ OPTIONS ]
      - key: branch_owner_to
        label: ALTER SERVER name OWNER TO new_owner
      - key: branch_rename
        label: ALTER SERVER name RENAME TO new_name
    server_state:
      label: 目标 server 存在状态
      importance: important
      values:
      - exists
      - non_existent
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    version_clause:
      label: VERSION 子句形态
      importance: non_important
      values:
      - omitted
      - set_new_version
      - set_version_null
    options_operation:
      label: OPTIONS 操作类型
      importance: non_important
      values:
      - add_option
      - set_option
      - drop_option
      - add_and_set_combined
      - omitted_no_options
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
    server_name_shape:
      label: server 名形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - non_existent_name
    new_name_shape:
      label: 新名形态（RENAME 分支）
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - existing_name_conflict
    new_owner_shape:
      label: 新 owner 形态（OWNER TO 分支）
      importance: non_important
      values:
      - existing_role
      - nonexistent_role
    option_key_value_shape:
      label: 选项键值形态
      importance: non_important
      values:
      - valid_option
      - invalid_option_rejected_by_validator
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - owner_with_usage_on_fdw
      - non_owner_no_privilege
    user_mapping_dependency:
      label: user mapping 依赖状态
      importance: non_important
      values:
      - no_user_mapping
      - has_user_mapping
    nonexistent_server:
      label: server 不存在
      importance: non_important
      values:
      - server_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_altering_server
      - non_owner_altering_server
    nonexistent_owner:
      label: owner 不存在
      importance: non_important
      values:
      - owner_role_does_not_exist
    nonexistent_new_name_conflict:
      label: 新名冲突
      importance: non_important
      values:
      - new_name_already_exists
    fdw_validator_rejection:
      label: FDW validator 拒绝
      importance: non_important
      values:
      - validator_rejects_invalid_option
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_foreign_server_catalog
      - pg_foreign_server_options_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_server
      - drop_user_mapping_then_drop_server
      - drop_fdw_then_drop_server
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - server_state
    - expected_status
    non_main_factors:
    - version_clause
    - options_operation
    - owner_to_shape
    - rename_behavior
    - server_name_shape
    - new_name_shape
    - new_owner_shape
    - option_key_value_shape
    - executor_privilege
    - user_mapping_dependency
    - nonexistent_server
    - privilege_insufficient
    - nonexistent_owner
    - nonexistent_new_name_conflict
    - fdw_validator_rejection
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - server_state
  rendering:
    statement_template: "ALTER SERVER {name} {operation}"
    verification_query_template: "SELECT srvname, srvoptions FROM pg_foreign_server WHERE srvname = '{name}'"
    factor_value_bindings: {}
```
