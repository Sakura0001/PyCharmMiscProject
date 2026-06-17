# 技能：CREATE FOREIGN DATA WRAPPER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createforeigndatawrapper.html

```sql
CREATE FOREIGN DATA WRAPPER name
    [ HANDLER handler_function | NO HANDLER ]
    [ VALIDATOR validator_function | NO VALIDATOR ]
    [ OPTIONS ( option 'value' [, ... ] ) ]
```

PG16 关键约束：
- **只有 superuser 可以创建 foreign-data wrapper**。创建者成为该 FDW 的 owner。
- HANDLER：指定已注册的函数来检索外部表的执行函数。函数必须无参数且返回 `fdw_handler` 类型。无 HANDLER 的 wrapper 只能声明外部表但不能访问。
- NO HANDLER：创建无 handler 的 wrapper（表可声明但不可访问）。
- VALIDATOR：指定验证函数，检查 FDW、外部服务器、用户映射和外部表的通用选项。函数必须接受 `text[]` 和 `oid` 两个参数。
- NO VALIDATOR：选项在创建时不被检查，可能在运行时被忽略或拒绝。
- OPTIONS：指定 FDW 选项，选项名称必须唯一，由 validator 函数验证。
- HANDLER 和 VALIDATOR 子句是 PostgreSQL 扩展（不属于 SQL/MED 标准）。
- SQL/MED 标准的 LIBRARY 和 LANGUAGE 子句在 PostgreSQL 中未实现。

## 语句作用

官方说明：CREATE FOREIGN DATA WRAPPER — define a new foreign-data wrapper

该 reference 关注 foreign-data wrapper 创建语句的语法分支、HANDLER/VALIDATOR/OPTIONS 子句组合、superuser 权限边界和 fdw_handler 类型函数依赖。

CREATE FOREIGN DATA WRAPPER **不涉及列类型定义**——它定义数据访问框架，不直接创建表/列结构。但 FDW 是外部表和外部服务器的前置依赖。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE FOREIGN DATA WRAPPER 单一顶层形式）
- object_state：目标 FDW 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- handler_clause：HANDLER 子句形态（省略 / 指定 handler_function / NO HANDLER）
- validator_clause：VALIDATOR 子句形态（省略 / 指定 validator_function / NO VALIDATOR）
- options_clause：OPTIONS 子句形态（省略 / 指定单选项 / 指定多选项）
- handler_function_type：HANDLER 函数返回类型（fdw_handler 正确 / 非 fdw_handler 错误）

### T3：对象名与输入形态因子
- fdw_name_shape：FDW 名称形态
- handler_name_shape：HANDLER 函数名形态
- validator_name_shape：VALIDATOR 函数名形态
- option_name_shape：选项名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / non_superuser）
- handler_function_existence：HANDLER 函数存在性（存在 / 不存在）
- validator_function_existence：VALIDATOR 函数存在性（存在 / 不存在）
- handler_function_return_type：HANDLER 函数返回类型匹配（匹配 fdw_handler / 不匹配）

### T5：异常与边界因子
- duplicate_fdw_name：重名冲突
- nonexistent_handler_function：HANDLER 函数不存在
- nonexistent_validator_function：VALIDATOR 函数不存在
- invalid_handler_return_type：HANDLER 函数返回类型不匹配 fdw_handler
- non_superuser_attempt：非 superuser 尝试创建
- duplicate_option_name：OPTIONS 中重复选项名
- no_handler_access_limit：NO HANDLER 外部表不可访问（行为边界）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE FOREIGN DATA WRAPPER 单一语法分支中的所有可选子句组合（HANDLER / VALIDATOR / OPTIONS）。
- 覆盖目标 FDW 存在 / 不存在 / 冲突（重名）路径。
- 覆盖成功路径与失败路径，包括 superuser 权限边界和函数依赖。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE FOREIGN DATA WRAPPER 要求 SUPERUSER 权限，必须在生成样本中显式标注；非 superuser 执行路径属于失败路径。
- HANDLER 函数必须返回 fdw_handler 类型，不匹配的函数属于失败路径。
- NO HANDLER 创建的 wrapper 可以声明外部表但不可访问，此行为边界需要代表性覆盖。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 CREATE FOREIGN DATA WRAPPER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- HANDLER 和 VALIDATOR 函数需要先创建才能引用，必须在生命周期计划中显式标注函数依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要 HANDLER/VALIDATOR 函数依赖或权限边界的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和 superuser 权限核心路径。
- 次优先保证 HANDLER/VALIDATOR/OPTIONS 子句形态代表性覆盖和函数依赖覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: foreign_data_wrapper
  skill_name: create_foreign_data_wrapper
  official_source: https://www.postgresql.org/docs/16/sql-createforeigndatawrapper.html
  statement:
    key: create_foreign_data_wrapper
    name: CREATE FOREIGN DATA WRAPPER
    aliases:
    - CREATE FOREIGN DATA WRAPPER
    - create foreign data wrapper
    - create_foreign_data_wrapper
    purpose: define a new foreign-data wrapper
  syntax_templates:
  - "CREATE FOREIGN DATA WRAPPER name [ HANDLER handler_function | NO HANDLER ]\
    \ [ VALIDATOR validator_function | NO VALIDATOR ] [ OPTIONS ( option 'value'\
    \ [, ... ] ) ]"
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
    - handler_clause
    - validator_clause
    - options_clause
    - handler_function_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - fdw_name_shape
    - handler_name_shape
    - validator_name_shape
    - option_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - handler_function_existence
    - validator_function_existence
    - handler_function_return_type
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_fdw_name
    - nonexistent_handler_function
    - nonexistent_validator_function
    - invalid_handler_return_type
    - non_superuser_attempt
    - duplicate_option_name
    - no_handler_access_limit
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
      - key: branch_create_fdw
        label: CREATE FOREIGN DATA WRAPPER 标准形式
    object_state:
      label: 目标 FDW 对象状态
      importance: important
      values:
      - key: not_exists
        label: FDW 不存在
      - key: already_exists
        label: FDW 已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    handler_clause:
      label: HANDLER 子句形态
      importance: important
      values:
      - key: omitted
        label: 省略 HANDLER
      - key: specified_handler_function
        label: 指定 handler_function
      - key: no_handler
        label: NO HANDLER (无 handler)
    validator_clause:
      label: VALIDATOR 子句形态
      importance: important
      values:
      - key: omitted
        label: 省略 VALIDATOR
      - key: specified_validator_function
        label: 指定 validator_function
      - key: no_validator
        label: NO VALIDATOR (无 validator)
    options_clause:
      label: OPTIONS 子句形态
      importance: non_important
      values:
      - key: omitted
        label: 省略 OPTIONS
      - key: single_option
        label: 单选项
      - key: multiple_options
        label: 多选项
    handler_function_type:
      label: HANDLER 函数返回类型
      importance: non_important
      values:
      - key: correct_fdw_handler
        label: 返回 fdw_handler 类型 (正确)
      - key: wrong_return_type
        label: 返回非 fdw_handler 类型 (错误)
    fdw_name_shape:
      label: FDW 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: reserved_word_name
        label: 保留字作为名称
      - key: duplicate_name
        label: 已存在的 FDW 名称
      - key: nonexistent_name
        label: 不存在的 FDW 名称
    handler_name_shape:
      label: HANDLER 函数名形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: schema_qualified
        label: Schema 限定标识符
      - key: nonexistent_function
        label: 不存在的函数名
    validator_name_shape:
      label: VALIDATOR 函数名形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: schema_qualified
        label: Schema 限定标识符
      - key: nonexistent_function
        label: 不存在的函数名
    option_name_shape:
      label: 选项名称形态
      importance: non_important
      values:
      - key: valid_option
        label: 合法选项名
      - key: duplicate_option
        label: 重复选项名
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
    handler_function_return_type:
      label: HANDLER 函数返回类型匹配
      importance: non_important
      values:
      - key: matches_fdw_handler
        label: 返回 fdw_handler → success
      - key: mismatches_fdw_handler
        label: 返回非 fdw_handler → error
    duplicate_fdw_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: no_conflict
        label: 无冲突
      - key: same_name_conflict
        label: 同名 FDW 已存在 → error
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
    invalid_handler_return_type:
      label: HANDLER 函数返回类型不匹配
      importance: non_important
      values:
      - key: correct_type
        label: 返回类型正确
      - key: wrong_type
        label: 返回类型错误 → error
    non_superuser_attempt:
      label: 非 superuser 尝试创建
      importance: non_important
      values:
      - key: superuser_execution
        label: superuser 执行 → success
      - key: non_superuser_execution
        label: 非 superuser 执行 → error
    duplicate_option_name:
      label: OPTIONS 中重复选项名
      importance: non_important
      values:
      - key: unique_options
        label: 选项名唯一
      - key: duplicate_options
        label: 选项名重复 → error
    no_handler_access_limit:
      label: NO HANDLER 外部表不可访问
      importance: non_important
      values:
      - key: with_handler_accessible
        label: 有 HANDLER → 外部表可访问
      - key: no_handler_not_accessible
        label: 无 HANDLER → 外部表不可访问 (行为边界)
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_foreign_data_wrapper_catalog
        label: pg_foreign_data_wrapper 系统目录查询
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_fdw
        label: DROP FOREIGN DATA WRAPPER
      - key: drop_handler_function
        label: 删除 HANDLER 函数
      - key: drop_validator_function
        label: 删除 VALIDATOR 函数
      - key: role_cleanup
        label: 角色/权限清理
  notes:
    superuser_only: 只有 superuser 可以创建 foreign-data wrapper。
    handler_fdw_handler_type: HANDLER 函数必须返回 fdw_handler 类型，不匹配的函数会导致错误。
    no_handler_declarable: NO HANDLER 的 FDW 可以声明外部表但不可访问。
    validator_checks_options: VALIDATOR 函数在创建时检查选项有效性。
    no_validator_no_check: NO VALIDATOR 时选项在创建时不被检查。
    handler_validator_extensions: HANDLER 和 VALIDATOR 子句是 PostgreSQL 扩展，不属于 SQL/MED 标准。
    fdw_no_column_types: CREATE FOREIGN DATA WRAPPER 不涉及列类型定义，不需要挂靠基表列类型。
  defaults:
    expected_status: success
    privilege_level: superuser
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - handler_clause
    - validator_clause
    - options_clause
    - handler_function_type
    - fdw_name_shape
    - handler_name_shape
    - validator_name_shape
    - option_name_shape
    - privilege_level
    - handler_function_existence
    - validator_function_existence
    - handler_function_return_type
    - duplicate_fdw_name
    - nonexistent_handler_function
    - nonexistent_validator_function
    - invalid_handler_return_type
    - non_superuser_attempt
    - duplicate_option_name
    - no_handler_access_limit
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE FOREIGN DATA WRAPPER {fdw_name} [ HANDLER {handler_function} | NO HANDLER ] [ VALIDATOR {validator_function} | NO VALIDATOR ] [ OPTIONS ( {options} ) ]"
    verification_query_template: "SELECT fdwname FROM pg_foreign_data_wrapper WHERE fdwname = '{fdw_name}'"
    factor_value_bindings: {}
```
