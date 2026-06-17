# 技能：CREATE SERVER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createserver.html

```sql
CREATE SERVER [ IF NOT EXISTS ] server_name [ TYPE 'server_type' ] [ VERSION 'server_version' ]
    FOREIGN DATA WRAPPER fdw_name
    [ OPTIONS ( option 'value' [, ... ] ) ]
```

**重要约束：**
- CREATE SERVER 需要 superuser 权限。
- FOREIGN DATA WRAPPER 必须是已存在的 FDW 对象。
- server_name 不支持 schema 限定（server 不属于 schema）。
- IF NOT EXISTS 在 server_name 已存在时不报错，而是发出 notice。
- TYPE 和 VERSION 是可选的描述性字符串。
- OPTIONS 中的选项由 FDW 的 validator 函数验证。

## 语句作用

官方说明：CREATE SERVER — define a new foreign server

该 reference 关注外部服务器定义语句的 IF NOT EXISTS 行为、TYPE/VERSION 可选子句、OPTIONS 参数、FDW 依赖和权限边界。CREATE SERVER 需要 superuser 权限，是 FDW 依赖对象。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE SERVER / CREATE SERVER IF NOT EXISTS）
- server_identity：目标 server 存在状态
- expected_status：预期结果

### T2：重要行为因子
- if_not_exists_clause：IF NOT EXISTS 子句行为
- type_version_clause：TYPE / VERSION 子句形态
- options_clause：OPTIONS 子句形态
- fdw_dependency：FDW 依赖形态

### T3：对象名与输入形态因子
- server_name_shape：server 名标识符形态
- fdw_name_shape：FDW 名形态
- option_value_shape：选项值形态

### T4：依赖对象与环境因子
- **CREATE SERVER 不涉及表/列/索引组合。它依赖已存在的 FDW 对象。**
- executor_privilege：执行者权限上下文
- fdw_existence：FDW 存在状态

### T5：异常与边界因子
- duplicate_server_name：server 名冲突
- privilege_insufficient：权限不足（非 superuser）
- nonexistent_fdw：依赖 FDW 不存在
- fdw_validator_rejection：FDW validator 拒绝 OPTIONS

### T6：验证与清理因子
- verification_mode：验证方式（pg_foreign_server 目录查询）
- cleanup_mode：清理方式（DROP SERVER）

## 覆盖策略

- 覆盖 server 不存在（成功创建）/ 已存在（失败冲突）/ IF NOT EXISTS（no-op）核心状态。
- 覆盖 TYPE / VERSION / OPTIONS 的代表性取值。
- 覆盖 FDW 依赖存在/不存在状态。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 server 成功创建、重名冲突、IF NOT EXISTS no-op 与 FDW 依赖缺失路径。
- 成功路径必须包含可通过 pg_foreign_server 目录验证的对象存在性检查，并在生命周期末尾清理 server。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 每个样本必须包含明确的前置 FDW 准备、目标 CREATE SERVER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或 FDW 依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 官方语法分支全覆盖
  - server 存在/不存在/冲突全覆盖
  - IF NOT EXISTS no-op 覆盖
  - 成功/失败路径全覆盖
  - superuser 权限路径全覆盖
- 次优先保证：
  - TYPE / VERSION / OPTIONS 代表性覆盖
  - FDW 依赖代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: server
  skill_name: create_server
  official_source: https://www.postgresql.org/docs/16/sql-createserver.html
  statement:
    key: create_server
    name: CREATE SERVER
    aliases:
    - create_server
    - CREATE SERVER
    purpose: CREATE SERVER — define a new foreign server
  syntax_templates:
  - "CREATE SERVER [ IF NOT EXISTS ] server_name [ TYPE 'server_type' ] [ VERSION 'server_version' ]\n    FOREIGN DATA WRAPPER fdw_name\n    [ OPTIONS ( option 'value' [, ... ] ) ]"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - server_identity
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - if_not_exists_clause
    - type_version_clause
    - options_clause
    - fdw_dependency
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - server_name_shape
    - fdw_name_shape
    - option_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - fdw_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_server_name
    - privilege_insufficient
    - nonexistent_fdw
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
      - key: branch_create_server
        label: CREATE SERVER server_name FOREIGN DATA WRAPPER fdw_name
      - key: branch_create_server_if_not_exists
        label: CREATE SERVER IF NOT EXISTS server_name FOREIGN DATA WRAPPER fdw_name
    server_identity:
      label: 目标 server 存在状态
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
    if_not_exists_clause:
      label: IF NOT EXISTS 子句
      importance: important
      values:
      - without_if_not_exists
      - with_if_not_exists
    type_version_clause:
      label: TYPE / VERSION 子句
      importance: non_important
      values:
      - omitted
      - type_only
      - version_only
      - both_type_and_version
    options_clause:
      label: OPTIONS 子句
      importance: non_important
      values:
      - omitted
      - single_option
      - multiple_options
    fdw_dependency:
      label: FDW 依赖形态
      importance: non_important
      values:
      - existing_fdw
      - nonexistent_fdw
    server_name_shape:
      label: server 名标识符形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - reserved_word_name
      - non_existing_name
    fdw_name_shape:
      label: FDW 名形态
      importance: non_important
      values:
      - existing_fdw_name
      - nonexistent_fdw_name
    option_value_shape:
      label: 选项值形态
      importance: non_important
      values:
      - valid_option_value
      - empty_option_value
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - non_superuser
    fdw_existence:
      label: FDW 存在状态
      importance: non_important
      values:
      - fdw_exists
      - fdw_not_exists
    duplicate_server_name:
      label: server 名冲突
      importance: non_important
      values:
      - none
      - same_name_exists
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_creating_server
    nonexistent_fdw:
      label: FDW 不存在
      importance: non_important
      values:
      - fdw_does_not_exist
    fdw_validator_rejection:
      label: FDW validator 拒绝
      importance: non_important
      values:
      - none
      - validator_rejects_invalid_option
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_foreign_server_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_server
      - drop_fdw_then_drop_server
  defaults:
    expected_status: success
    if_not_exists_clause: without_if_not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - server_identity
    - expected_status
    non_main_factors:
    - if_not_exists_clause
    - type_version_clause
    - options_clause
    - fdw_dependency
    - server_name_shape
    - fdw_name_shape
    - option_value_shape
    - executor_privilege
    - fdw_existence
    - duplicate_server_name
    - privilege_insufficient
    - nonexistent_fdw
    - fdw_validator_rejection
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - server_identity
  rendering:
    statement_template: "CREATE SERVER [ IF NOT EXISTS ] {server_name} FOREIGN DATA WRAPPER {fdw_name} [ OPTIONS ( {options} ) ]"
    verification_query_template: "SELECT srvname FROM pg_foreign_server WHERE srvname = '{server_name}'"
    factor_value_bindings:
      if_not_exists_clause:
        without_if_not_exists: ""
        with_if_not_exists: "IF NOT EXISTS"
```
