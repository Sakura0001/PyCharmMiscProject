# 技能：DROP USER MAPPING

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropusermapping.html

```sql
DROP USER MAPPING [ IF EXISTS ] FOR { user_name | USER | CURRENT_ROLE | CURRENT_USER | PUBLIC } SERVER server_name
```

PG16 关键约束：
- 外部服务器的 owner 可删除任何用户的 user mapping
- 拥有外部服务器 USAGE 权限的用户只能删除自己用户名的 user mapping
- 不支持 CASCADE 或 RESTRICT 子句
- IF EXISTS：如果映射不存在，不报错而是发出通知
- 该语句不涉及列类型，不需要挂靠基表列类型
- server_name 必须引用已存在的 foreign server

## 语句作用

官方说明：DROP USER MAPPING — remove a user mapping for a foreign server

该 reference 关注用户映射删除操作的权限边界（server owner / USAGE privilege）、foreign server 依赖和 IF EXISTS 行为，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP USER MAPPING / DROP USER MAPPING IF EXISTS）
- object_state：目标 user mapping 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- user_specification：FOR 用户指定形态（user_name / USER / CURRENT_ROLE / CURRENT_USER / PUBLIC）
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- authorization_path：权限路径（server_owner / user_with_usage / non_privileged）
- server_existence：SERVER 引用的 foreign server 存在性（存在 / 不存在）

### T3：对象名与输入形态因子
- user_name_shape：用户名称形态
- server_name_shape：foreign server 名称形态

### T4：依赖对象与环境因子
- privilege_context：权限上下文
- server_dependency：foreign server 依赖关系

### T5：异常与边界因子
- nonexistent_mapping：user mapping 不存在且无 IF EXISTS
- nonexistent_server：SERVER 引用的 foreign server 不存在
- insufficient_privilege：缺少 server owner 权限或 USAGE 权限
- self_mapping_only：拥有 USAGE 权限的用户只能删除自己的映射

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP USER MAPPING 全部语法分支。
- 覆盖目标 user mapping 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 server owner 权限边界和 USAGE 权限。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- DROP USER MAPPING 不支持 CASCADE 或 RESTRICT，不得伪造这些子句的分支。
- 外部服务器的 owner 可删除任何用户的 user mapping；拥有 USAGE 权限的用户只能删除自己的映射。
- 必须覆盖目标映射存在时的成功删除路径，以及目标映射不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- DROP USER MAPPING 不涉及 table / column 组合，不需要挂靠基表列类型。
- 每个样本必须包含明确的前置对象准备（foreign server、foreign data wrapper）、目标 DROP USER MAPPING 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 server owner 权限相关的因子必须挂靠到具有明确权限上下文的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 FOR 用户指定形态、IF EXISTS 子句代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: user_mapping
  skill_name: drop_user_mapping
  official_source: https://www.postgresql.org/docs/16/sql-dropusermapping.html
  statement:
    key: drop_user_mapping
    name: DROP USER MAPPING
    aliases:
    - drop_user_mapping
    - DROP USER MAPPING
    purpose: DROP USER MAPPING — remove a user mapping for a foreign server
  syntax_templates:
  - "DROP USER MAPPING [ IF EXISTS ] FOR { user_name | USER | CURRENT_ROLE | CURRENT_USER | PUBLIC } SERVER server_name"
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
    - if_exists_clause
    - authorization_path
    - server_existence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - user_name_shape
    - server_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_context
    - server_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_mapping
    - nonexistent_server
    - insufficient_privilege
    - self_mapping_only
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
      - key: branch_drop_user_mapping
        label: DROP USER MAPPING FOR ... SERVER ...
      - key: branch_drop_user_mapping_if_exists
        label: DROP USER MAPPING IF EXISTS FOR ... SERVER ...
    object_state:
      label: 目标 user mapping 对象状态
      importance: important
      values:
      - exists
      - absent
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
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: non_important
      values:
      - present
      - absent
    authorization_path:
      label: 权限路径
      importance: non_important
      values:
      - server_owner
      - user_with_usage
      - non_privileged
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
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - server_owner_session
      - user_with_usage_session
      - non_privileged_session
    server_dependency:
      label: foreign server 依赖关系
      importance: non_important
      values:
      - server_exists_and_valid
      - server_missing
    nonexistent_mapping:
      label: user mapping 不存在且无 IF EXISTS
      importance: non_important
      values:
      - mapping_exists
      - mapping_missing_without_if_exists
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
    self_mapping_only:
      label: 拥有 USAGE 权限的用户只能删除自己的映射
      importance: non_important
      values:
      - deleting_own_mapping
      - attempting_other_user_mapping
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - error_assertion
      - notice_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_user_mapping
      - drop_server
      - drop_fdw
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - user_specification
    - if_exists_clause
    - authorization_path
    - server_existence
    - user_name_shape
    - server_name_shape
    - privilege_context
    - server_dependency
    - nonexistent_mapping
    - nonexistent_server
    - insufficient_privilege
    - self_mapping_only
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP USER MAPPING [ IF EXISTS ] FOR {user_spec} SERVER {server_name}"
    verification_query_template: "SELECT umuser, umserver FROM pg_user_mapping WHERE umserver = '{server_oid}'"
    factor_value_bindings: {}
```
