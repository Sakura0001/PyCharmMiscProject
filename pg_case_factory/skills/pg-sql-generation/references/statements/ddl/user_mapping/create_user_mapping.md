# 技能：CREATE USER MAPPING

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createusermapping.html

```sql
CREATE USER MAPPING [ IF NOT EXISTS ] FOR { user_name | USER | CURRENT_ROLE | CURRENT_USER | PUBLIC }
    SERVER server_name
    [ OPTIONS ( option 'value' [ , ... ] ) ]
```

PG16 关键约束：
- 外部服务器的 owner 可为任何用户创建 user mapping
- 拥有外部服务器 USAGE 权限的用户可为自己的用户名创建 user mapping
- IF NOT EXISTS：如果映射已存在，不报错而是发出通知（但不保证现有映射与指定内容一致）
- PUBLIC 创建公共映射，当无用户特定映射适用时作为回退
- OPTIONS 中的选项名称必须唯一，选项名和值由外部数据包装器（FDW）定义
- 该语句不涉及列类型，不需要挂靠基表列类型
- server_name 必须引用已存在的 foreign server

## 语句作用

官方说明：CREATE USER MAPPING — define a new mapping of a user to a foreign server

该 reference 关注用户映射对象的定义、foreign server 依赖、权限边界（server owner / USAGE privilege）和 IF NOT EXISTS 行为，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE USER MAPPING / CREATE USER MAPPING IF NOT EXISTS）
- object_state：目标 user mapping 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- user_specification：FOR 用户指定形态（user_name / USER / CURRENT_ROLE / CURRENT_USER / PUBLIC）
- if_not_exists_clause：IF NOT EXISTS 子句开关（省略 / 指定）
- options_clause：OPTIONS 子句形态（省略 / 单选项 / 多选项）
- server_existence：SERVER 引用的 foreign server 存在性（存在 / 不存在）

### T3：对象名与输入形态因子
- user_name_shape：用户名称形态
- server_name_shape：foreign server 名称形态
- option_value_shape：选项值形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（server_owner / user_with_usage / non_privileged）
- server_dependency：foreign server 依赖关系

### T5：异常与边界因子
- duplicate_mapping：已存在的 user mapping（without IF NOT EXISTS）
- nonexistent_server：SERVER 引用的 foreign server 不存在
- insufficient_privilege：缺少 server owner 权限或 USAGE 权限
- duplicate_option_name：OPTIONS 中选项名重复

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE USER MAPPING 全部语法分支中的所有行为路径。
- 覆盖目标 user mapping 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 server owner 权限边界和 USAGE 权限。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 外部服务器的 owner 可为任何用户创建 user mapping；拥有 USAGE 权限的用户只能为自己的用户名创建。
- 支持 IF NOT EXISTS 时，必须覆盖已存在映射的代表性 no-op 路径。
- SERVER 引用的 foreign server 必须存在，不存在属于失败路径。
- CREATE USER MAPPING 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的映射存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备（foreign server、foreign data wrapper）、目标 CREATE USER MAPPING 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 server owner 权限相关的因子必须挂靠到具有明确权限上下文的样本上。
- FOR PUBLIC 映射因子必须挂靠到 PUBLIC 分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 FOR 用户指定形态、IF NOT EXISTS 子句和 OPTIONS 子句代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: user_mapping
  skill_name: create_user_mapping
  official_source: https://www.postgresql.org/docs/16/sql-createusermapping.html
  statement:
    key: create_user_mapping
    name: CREATE USER MAPPING
    aliases:
    - create_user_mapping
    - CREATE USER MAPPING
    purpose: CREATE USER MAPPING — define a new mapping of a user to a foreign server
  syntax_templates:
  - "CREATE USER MAPPING [ IF NOT EXISTS ] FOR { user_name | USER | CURRENT_ROLE | CURRENT_USER | PUBLIC }\n    SERVER server_name\n    [ OPTIONS ( option 'value' [ , ... ] ) ]"
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
    - if_not_exists_clause
    - options_clause
    - server_existence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - user_name_shape
    - server_name_shape
    - option_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - server_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_mapping
    - nonexistent_server
    - insufficient_privilege
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
      - key: branch_create_user_mapping
        label: CREATE USER MAPPING FOR ... SERVER ...
      - key: branch_create_user_mapping_if_not_exists
        label: CREATE USER MAPPING IF NOT EXISTS FOR ... SERVER ...
    object_state:
      label: 目标 user mapping 对象状态
      importance: important
      values:
      - not_exists
      - exists
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
      - public
    if_not_exists_clause:
      label: IF NOT EXISTS 子句开关
      importance: non_important
      values:
      - omitted
      - present
    options_clause:
      label: OPTIONS 子句形态
      importance: non_important
      values:
      - omitted
      - single_option
      - multiple_options
    server_existence:
      label: SERVER 引用的 foreign server 存在性
      importance: non_important
      values:
      - server_exists
      - server_not_exists
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
    option_value_shape:
      label: 选项值形态
      importance: non_important
      values:
      - valid_value
      - quoted_value
      - duplicate_option_name
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
    duplicate_mapping:
      label: 已存在的 user mapping（without IF NOT EXISTS）
      importance: non_important
      values:
      - no_conflict
      - existing_mapping_without_if_not_exists
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
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_user_mapping
      - drop_server
      - drop_fdw
  defaults:
    expected_status: success
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - user_specification
    - if_not_exists_clause
    - options_clause
    - server_existence
    - user_name_shape
    - server_name_shape
    - option_value_shape
    - privilege_level
    - server_dependency
    - duplicate_mapping
    - nonexistent_server
    - insufficient_privilege
    - duplicate_option_name
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE USER MAPPING [ IF NOT EXISTS ] FOR {user_spec} SERVER {server_name} [ OPTIONS ( {options_clause} ) ]"
    verification_query_template: "SELECT umuser, umserver FROM pg_user_mapping WHERE umserver = '{server_oid}'"
    factor_value_bindings: {}
```
