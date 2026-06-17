# 技能：ALTER FOREIGN DATA WRAPPER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterforeigndatawrapper.html

```sql
ALTER FOREIGN DATA WRAPPER name
    [ HANDLER handler_function | NO HANDLER ]
    [ VALIDATOR validator_function | NO VALIDATOR ]
    [ OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ]) ]
ALTER FOREIGN DATA WRAPPER name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER FOREIGN DATA WRAPPER name RENAME TO new_name
```

PG16 关键约束：
- **只有 superuser 可以修改 foreign-data wrapper**，也只有 superuser 可以成为 FDW 的 owner。
- 修改 VALIDATOR 时，已有的 FDW 及其依赖服务器、用户映射、外部表的选项**可能在新 validator 下变得无效**。PostgreSQL 不检查此情况——由用户负责验证正确性。但同一 ALTER 命令内指定的选项会被新 validator 检查。
- NO HANDLER 会导致使用该 FDW 的外部表不可访问。
- OPTIONS 子句：ADD（默认）/ SET / DROP 指定操作；选项名必须唯一；由 FDW 的 validator 验证。
- OWNER TO / RENAME TO 子句是 PostgreSQL 扩展，不属于 SQL/MED 标准。
- HANDLER / NO HANDLER / VALIDATOR / NO VALIDATOR 子句也是 PostgreSQL 扩展。

## 语句作用

官方说明：ALTER FOREIGN DATA WRAPPER — change the definition of a foreign-data wrapper

该 reference 关注 FDW 定义变更语句的三个顶层语法分支（handler/validator/options 变更 / OWNER TO / RENAME TO）、superuser 权限边界、VALIDATOR 切换时的选项兼容性风险和 NO HANDLER 的行为边界。

ALTER FOREIGN DATA WRAPPER **不涉及列类型定义**——它操作 FDW 的元数据和配置，不直接创建或修改表/列结构。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（handler_validator_options 变更 / OWNER TO / RENAME TO）
- object_state：目标 FDW 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（change_handler_validator_options / owner / rename）
- handler_change：HANDLER 变更形态（指定新 handler / NO HANDLER / 省略）
- validator_change：VALIDATOR 变更形态（指定新 validator / NO VALIDATOR / 省略）
- options_operation：OPTIONS 操作形态（ADD / SET / DROP / ADD+SET+DROP 组合）
- owner_target：OWNER TO 目标形态（指定 new_owner / CURRENT_ROLE / CURRENT_USER / SESSION_USER）

### T3：对象名与输入形态因子
- fdw_name_shape：FDW 名称形态
- new_name_shape：RENAME TO 新名称形态
- owner_name_shape：OWNER TO 目标角色名称形态
- option_name_shape：OPTIONS 选项名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / non_superuser）
- handler_function_existence：HANDLER 函数存在性（存在 / 不存在）
- validator_function_existence：VALIDATOR 函数存在性（存在 / 不存在）
- preexisting_options_compatibility：切换 VALIDATOR 时已有选项兼容性（兼容 / 可能不兼容）

### T5：异常与边界因子
- nonexistent_fdw：目标 FDW 不存在
- nonexistent_handler_function：HANDLER 函数不存在
- nonexistent_validator_function：VALIDATOR 函数不存在
- non_superuser_attempt：非 superuser 尝试 ALTER FDW
- validator_switch_option_incompatibility：切换 VALIDATOR 时已有选项不兼容（行为边界）
- no_handler_access_limit：NO HANDLER 导致外部表不可访问
- nonexistent_owner_role：OWNER TO 目标角色不存在
- duplicate_new_name：RENAME TO 新名称与已有 FDW 重名

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER FOREIGN DATA WRAPPER 三个语法分支中的所有行为路径。
- 不需要覆盖所有基表和所有列类型，因为 ALTER FDW 不涉及表/列/索引组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER FOREIGN DATA WRAPPER 要求 SUPERUSER 权限，必须在生成样本中显式标注；非 superuser 执行路径属于失败路径。
- 只有 superuser 可以成为 FDW 的 owner，OWNER TO 目标必须为 superuser 角色。
- 必须预创建可被修改的目标 FDW 对象，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 FDW 存在时的成功修改路径、目标 FDW 不存在时的失败路径。
- handler_validator_options 变更 / OWNER TO / RENAME TO 三个分支需要保持独立归因。
- 切换 VALIDATOR 时已有选项可能不兼容——PostgreSQL 不自动检查此情况，此行为边界需要代表性覆盖。
- NO HANDLER 导致外部表不可访问的行为边界需要代表性覆盖。
- 成功路径必须包含可验证的对象变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER FOREIGN DATA WRAPPER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要 HANDLER/VALIDATOR 函数依赖、权限边界或选项兼容性的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（handler_validator_options / OWNER TO / RENAME TO）
  - 目标 FDW 存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - superuser 权限核心路径全覆盖
- 次优先保证：
  - HANDLER/VALIDATOR 变更形态代表性覆盖
  - OPTIONS 操作形态代表性覆盖
  - OWNER TO 目标形态代表性覆盖
  - VALIDATOR 切换选项兼容性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: foreign_data_wrapper
  skill_name: alter_foreign_data_wrapper
  official_source: https://www.postgresql.org/docs/16/sql-alterforeigndatawrapper.html
  statement:
    key: alter_foreign_data_wrapper
    name: ALTER FOREIGN DATA WRAPPER
    aliases:
    - ALTER FOREIGN DATA WRAPPER
    - alter foreign data wrapper
    - alter_foreign_data_wrapper
    purpose: change the definition of a foreign-data wrapper
  syntax_templates:
  - "ALTER FOREIGN DATA WRAPPER name [ HANDLER handler_function | NO HANDLER ]\
    \ [ VALIDATOR validator_function | NO VALIDATOR ] [ OPTIONS ( [ ADD | SET |\
    \ DROP ] option ['value'] [, ... ]) ]"
  - "ALTER FOREIGN DATA WRAPPER name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER\
    \ | SESSION_USER }"
  - "ALTER FOREIGN DATA WRAPPER name RENAME TO new_name"
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
    - handler_change
    - validator_change
    - options_operation
    - owner_target
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - fdw_name_shape
    - new_name_shape
    - owner_name_shape
    - option_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - handler_function_existence
    - validator_function_existence
    - preexisting_options_compatibility
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_fdw
    - nonexistent_handler_function
    - nonexistent_validator_function
    - non_superuser_attempt
    - validator_switch_option_incompatibility
    - no_handler_access_limit
    - nonexistent_owner_role
    - duplicate_new_name
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
      - key: branch_change_handler_validator_options
        label: ALTER FOREIGN DATA WRAPPER name [ HANDLER/NO HANDLER ] [ VALIDATOR/NO VALIDATOR ] [ OPTIONS ]
      - key: branch_owner
        label: ALTER FOREIGN DATA WRAPPER name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_rename
        label: ALTER FOREIGN DATA WRAPPER name RENAME TO new_name
    object_state:
      label: 目标 FDW 对象状态
      importance: important
      values:
      - key: exists
        label: FDW 已存在
      - key: not_exists
        label: FDW 不存在
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
      - key: change_handler_validator_options
        label: 变更 HANDLER/VALIDATOR/OPTIONS
      - key: owner
        label: OWNER TO
      - key: rename
        label: RENAME TO
    handler_change:
      label: HANDLER 变更形态
      importance: non_important
      values:
      - key: omitted
        label: 省略 HANDLER 变更
      - key: specified_new_handler
        label: 指定新 handler_function
      - key: no_handler
        label: NO HANDLER (移除 handler)
    validator_change:
      label: VALIDATOR 变更形态
      importance: non_important
      values:
      - key: omitted
        label: 省略 VALIDATOR 变更
      - key: specified_new_validator
        label: 指定新 validator_function
      - key: no_validator
        label: NO VALIDATOR (移除 validator)
    options_operation:
      label: OPTIONS 操作形态
      importance: non_important
      values:
      - key: add_option
        label: ADD option
      - key: set_option
        label: SET option
      - key: drop_option
        label: DROP option
      - key: combined_operations
        label: ADD + SET + DROP 组合
    owner_target:
      label: OWNER TO 目标形态
      importance: non_important
      values:
      - key: specified_new_owner
        label: 指定 new_owner (必须为 superuser)
      - key: specified_current_role
        label: CURRENT_ROLE
      - key: specified_current_user
        label: CURRENT_USER
      - key: specified_session_user
        label: SESSION_USER
    fdw_name_shape:
      label: FDW 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_name
        label: 不存在的 FDW 名称
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: duplicate_name
        label: 与已有 FDW 重名
    owner_name_shape:
      label: OWNER TO 目标角色名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_role
        label: 不存在的角色
    option_name_shape:
      label: OPTIONS 选项名称形态
      importance: non_important
      values:
      - key: valid_option
        label: 合法选项名
      - key: invalid_option
        label: 无效选项名
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: superuser
        label: 超级用户 → success
      - key: non_superuser
        label: 非 superuser → error
    handler_function_existence:
      label: HANDLER 函数存在性
      importance: non_important
      values:
      - key: function_exists
        label: HANDLER 函数已创建
      - key: function_not_exists
        label: HANDLER 函数不存在 → error
    validator_function_existence:
      label: VALIDATOR 函数存在性
      importance: non_important
      values:
      - key: function_exists
        label: VALIDATOR 函数已创建
      - key: function_not_exists
        label: VALIDATOR 函数不存在 → error
    preexisting_options_compatibility:
      label: 切换 VALIDATOR 时已有选项兼容性
      importance: non_important
      values:
      - key: compatible
        label: 已有选项与新 validator 兼容
      - key: potentially_incompatible
        label: 已有选项可能不兼容 (PG 不自动检查)
    nonexistent_fdw:
      label: 目标 FDW 不存在
      importance: non_important
      values:
      - key: fdw_exists
        label: FDW 存在
      - key: fdw_missing
        label: FDW 不存在 → error
    nonexistent_handler_function:
      label: HANDLER 函数不存在
      importance: non_important
      values:
      - key: function_exists
        label: 函数存在
      - key: function_missing
        label: 函数不存在 → error
    nonexistent_validator_function:
      label: VALIDATOR 函数不存在
      importance: non_important
      values:
      - key: function_exists
        label: 函数存在
      - key: function_missing
        label: 函数不存在 → error
    non_superuser_attempt:
      label: 非 superuser 尝试 ALTER FDW
      importance: non_important
      values:
      - key: superuser_execution
        label: superuser 执行 → success
      - key: non_superuser_execution
        label: 非 superuser 执行 → error
    validator_switch_option_incompatibility:
      label: 切换 VALIDATOR 时已有选项不兼容
      importance: non_important
      values:
      - key: no_validator_switch
        label: 未切换 validator
      - key: switch_with_incompatible_options
        label: 切换 validator 后已有选项可能失效 (行为边界)
    no_handler_access_limit:
      label: NO HANDLER 导致外部表不可访问
      importance: non_important
      values:
      - key: with_handler
        label: 有 HANDLER → 外部表可访问
      - key: no_handler
        label: NO HANDLER → 外部表不可访问
    nonexistent_owner_role:
      label: OWNER TO 目标角色不存在
      importance: non_important
      values:
      - key: role_exists_superuser
        label: 目标角色为存在的 superuser → success
      - key: role_missing
        label: 目标角色不存在 → error
    duplicate_new_name:
      label: RENAME TO 新名称与已有 FDW 重名
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: same_name_conflict
        label: 新名称与已有 FDW 重名 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_foreign_data_wrapper_catalog
        label: pg_foreign_data_wrapper 系统目录查询
      - key: effect_query
        label: 效果查询 (验证 handler/validator/owner 变更)
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: revert_handler
        label: 还原 HANDLER 变更
      - key: revert_validator
        label: 还原 VALIDATOR 变更
      - key: revert_owner
        label: 还原 OWNER 变更
      - key: revert_rename
        label: 还原 RENAME 变更
      - key: drop_fdw
        label: DROP FOREIGN DATA WRAPPER
  notes:
    superuser_only: 只有 superuser 可以修改和拥有 foreign-data wrapper。
    validator_switch_risk: 修改 VALIDATOR 时已有选项可能在新 validator 下变得无效，PG 不自动检查。
    no_handler_inaccessible: NO HANDLER 导致使用该 FDW 的外部表不可访问。
    owner_must_be_superuser: 只有 superuser 可以成为 FDW 的 owner。
    handler_validator_extensions: HANDLER/VALIDATOR/OWNER TO/RENAME TO 子句是 PostgreSQL 扩展。
    fdw_no_column_types: ALTER FOREIGN DATA WRAPPER 不涉及列类型定义，不需要挂靠基表列类型。
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
    - handler_change
    - validator_change
    - options_operation
    - owner_target
    - fdw_name_shape
    - new_name_shape
    - owner_name_shape
    - option_name_shape
    - privilege_level
    - handler_function_existence
    - validator_function_existence
    - preexisting_options_compatibility
    - nonexistent_fdw
    - nonexistent_handler_function
    - nonexistent_validator_function
    - non_superuser_attempt
    - validator_switch_option_incompatibility
    - no_handler_access_limit
    - nonexistent_owner_role
    - duplicate_new_name
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER FOREIGN DATA WRAPPER {fdw_name} {alter_clause}"
    verification_query_template: "SELECT fdwname, fdwhandler, fdwvalidator, fdwowner FROM pg_foreign_data_wrapper WHERE fdwname = '{fdw_name}'"
    factor_value_bindings:
      alter_action:
        change_handler_validator_options: "[ HANDLER handler_function | NO HANDLER ] [ VALIDATOR validator_function | NO VALIDATOR ] [ OPTIONS ]"
        owner: "OWNER TO {owner_spec}"
        rename: "RENAME TO {new_name}"
```
