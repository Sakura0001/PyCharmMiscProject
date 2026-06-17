# 技能：ALTER USER MAPPING

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterusermapping.html

```sql
ALTER USER MAPPING FOR { user_name | USER | CURRENT_ROLE | CURRENT_USER | SESSION_USER | PUBLIC }
    SERVER server_name
    OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] )
```

PG16 关键约束：
- 外部服务器的 owner 可修改任何用户的 user mapping
- 拥有外部服务器 USAGE 权限的用户只能修改自己用户名的 user mapping
- OPTIONS 中 ADD 为默认操作（未显式指定操作时）
- SET 替换已有选项值，DROP 移除选项
- 选项名必须唯一，选项由 FDW 验证
- 该语句不涉及列类型，不需要挂靠基表列类型
- ALTER USER MAPPING 只有一种语法形式（OPTIONS 修改），不支持 RENAME/OWNER/SET SCHEMA

## 语句作用

官方说明：ALTER USER MAPPING — change the definition of a user mapping

该 reference 关注用户映射的选项修改（ADD/SET/DROP）、权限边界（server owner / USAGE privilege）和 foreign server 依赖，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（ALTER USER MAPPING OPTIONS 标准形式）
- object_state：目标 user mapping 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- user_specification：FOR 用户指定形态（user_name / USER / CURRENT_ROLE / CURRENT_USER / SESSION_USER / PUBLIC）
- option_action：选项操作类型（ADD / SET / DROP / 默认ADD）
- option_clause：选项组合形态（单选项 / 多选项 / ADD加SET / SET加DROP）
- mapping_existence：目标 user mapping 是否存在（存在 / 不存在）

### T3：对象名与输入形态因子
- user_name_shape：用户名称形态
- server_name_shape：foreign server 名称形态
- option_name_shape：选项名称形态
- option_value_shape：选项值形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（server_owner / user_with_usage / non_privileged）
- server_dependency：foreign server 依赖关系

### T5：异常与边界因子
- nonexistent_mapping：目标 user mapping 不存在
- nonexistent_server：SERVER 引用的 foreign server 不存在
- insufficient_privilege：缺少 server owner 权限或 USAGE 权限
- invalid_option：无效的选项名或值（FDW 验证失败）
- duplicate_option_name：OPTIONS 中选项名重复

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER USER MAPPING 单一语法分支中的所有选项操作路径（ADD/SET/DROP）。
- 覆盖目标 user mapping 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 server owner 权限边界。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER USER MAPPING 只有一种语法形式（OPTIONS 修改），不支持 RENAME/OWNER/SET SCHEMA。
- 外部服务器的 owner 可修改任何用户的 user mapping；拥有 USAGE 权限的用户只能修改自己的映射。
- 必须预创建可被修改的目标 user mapping。
- OPTIONS 中 ADD 为默认操作，SET 替换已有选项值，DROP 移除选项。
- ALTER USER MAPPING 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的选项变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备（foreign server、foreign data wrapper、user mapping）、目标 ALTER USER MAPPING 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 server owner 权限相关的因子必须挂靠到具有明确权限上下文的样本上。
- ADD/SET/DROP 操作因子必须挂靠到对应操作类型的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 FOR 用户指定形态、选项操作类型代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: user_mapping
  skill_name: alter_user_mapping
  official_source: https://www.postgresql.org/docs/16/sql-alterusermapping.html
  statement:
    key: alter_user_mapping
    name: ALTER USER MAPPING
    aliases:
    - alter_user_mapping
    - ALTER USER MAPPING
    purpose: ALTER USER MAPPING — change the definition of a user mapping
  syntax_templates:
  - "ALTER USER MAPPING FOR { user_name | USER | CURRENT_ROLE | CURRENT_USER | SESSION_USER | PUBLIC }\n    SERVER server_name\n    OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] )"
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
    - user_specification
    - option_action
    - option_clause
    - mapping_existence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - user_name_shape
    - server_name_shape
    - option_name_shape
    - option_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - server_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_mapping
    - nonexistent_server
    - insufficient_privilege
    - invalid_option
    - duplicate_option_name
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
      - key: branch_1
        label: ALTER USER MAPPING FOR ... SERVER ... OPTIONS ( ... )
    object_state:
      label: 目标 user mapping 对象状态
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
    user_specification:
      label: FOR 用户指定形态
      importance: non_important
      values:
      - named_user
      - user_keyword
      - current_role
      - current_user
      - session_user
      - public
    option_action:
      label: 选项操作类型
      importance: non_important
      values:
      - add
      - set
      - drop
      - default_add
    option_clause:
      label: 选项组合形态
      importance: non_important
      values:
      - single_option_add
      - single_option_set
      - single_option_drop
      - multiple_options_mixed
    mapping_existence:
      label: 目标 user mapping 是否存在
      importance: non_important
      values:
      - mapping_exists
      - mapping_not_exists
    user_name_shape:
      label: 用户名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_name
      - public_keyword
    server_name_shape:
      label: foreign server 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_name
    option_name_shape:
      label: 选项名称形态
      importance: non_important
      values:
      - valid_option
      - invalid_option
    option_value_shape:
      label: 选项值形态
      importance: non_important
      values:
      - valid_value
      - quoted_value
      - drop_no_value
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - server_owner
      - user_with_usage
      - non_privileged
    server_dependency:
      label: foreign server 依赖关系
      importance: non_important
      values:
      - server_exists_and_valid
      - server_missing
    nonexistent_mapping:
      label: 目标 user mapping 不存在
      importance: non_important
      values:
      - mapping_exists
      - mapping_missing
    nonexistent_server:
      label: SERVER 引用的 foreign server 不存在
      importance: non_important
      values:
      - server_exists
      - server_missing
    insufficient_privilege:
      label: 缺少 server owner 权限或 USAGE 权限
      importance: non_important
      values:
      - has_privilege
      - lacks_privilege
    invalid_option:
      label: 无效的选项名或值
      importance: non_important
      values:
      - valid_option_and_value
      - invalid_option_name
      - invalid_option_value
    duplicate_option_name:
      label: OPTIONS 中选项名重复
      importance: non_important
      values:
      - unique_options
      - duplicate_option
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_user_mapping
      - option_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - revert_option
      - drop_user_mapping
      - drop_server
  defaults:
    expected_status: success
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - user_specification
    - option_action
    - option_clause
    - mapping_existence
    - user_name_shape
    - server_name_shape
    - option_name_shape
    - option_value_shape
    - privilege_level
    - server_dependency
    - nonexistent_mapping
    - nonexistent_server
    - insufficient_privilege
    - invalid_option
    - duplicate_option_name
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER USER MAPPING FOR {user_spec} SERVER {server_name} OPTIONS ( {options_clause} )"
    verification_query_template: "SELECT umuser, umserver, umoptions FROM pg_user_mapping WHERE umserver = '{server_oid}'"
    factor_value_bindings: {}
```
