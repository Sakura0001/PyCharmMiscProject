# 技能：DROP USER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropuser.html

```sql
DROP USER [ IF EXISTS ] name [, ...]
```

PG16 关键约束：
- **DROP USER 是 DROP ROLE 的已弃用别名（deprecated alias）**，行为完全一致
- DROP USER / DROP ROLE 要求执行者拥有 CREATEROLE 权限（superuser 自动拥有）
- 不支持 CASCADE 或 RESTRICT 子句（与 DROP TEXT SEARCH 等不同）
- 如果角色仍拥有对象或仍有活跃连接，DROP 可能失败（需要先移除或重新分配对象）
- 可一次删除多个角色（逗号分隔）
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：DROP USER — remove a database role

**重要提示：DROP USER 是 DROP ROLE 的已弃用别名（deprecated alias）。所有行为与 DROP ROLE 一致。**

该 reference 关注角色删除操作的 CREATEROLE 权限边界、对象驻留和 IF EXISTS 行为，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP USER / DROP USER IF EXISTS）
- object_state：目标 role 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- multi_user_clause：多角色删除（单一角色 / 多角色逗号列表）
- authorization_path：权限路径（CREATEROLE / superuser / non_createrole）
- role_dependency：角色依赖（无依赖 / 拥有对象 / 有活跃连接）

### T3：对象名与输入形态因子
- role_name_shape：角色标识符形态

### T4：依赖对象与环境因子
- privilege_context：权限上下文
- dependency_context：依赖对象驻留情况

### T5：异常与边界因子
- error_type：失败原因分类

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP USER 全部语法分支。
- 覆盖目标角色存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 CREATEROLE 权限边界和对象驻留。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- DROP USER 是 DROP ROLE 的已弃用别名，必须在每个样本中显式标注此关系。
- DROP USER 要求 CREATEROLE 权限；缺少 CREATEROLE 的执行路径属于失败路径。
- DROP USER 不支持 CASCADE 或 RESTRICT，不得伪造这些子句的分支。
- 必须覆盖目标角色存在时的成功删除路径，以及目标角色不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- DROP USER 不涉及 table / column 组合，不需要挂靠基表列类型。
- 每个样本必须包含明确的前置对象准备、目标 DROP USER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 CREATEROLE 权限相关的因子必须挂靠到具有明确权限上下文的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 子句、多角色删除和角色依赖代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: user
  skill_name: drop_user
  official_source: https://www.postgresql.org/docs/16/sql-dropuser.html
  statement:
    key: drop_user
    name: DROP USER
    aliases:
    - drop_user
    - DROP USER
    - drop_role
    - DROP ROLE
    purpose: DROP USER — remove a database role (deprecated alias for DROP ROLE)
  syntax_templates:
  - "DROP USER [ IF EXISTS ] name [, ...]"
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
    - multi_user_clause
    - authorization_path
    - role_dependency
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - role_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_context
    - dependency_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - error_type
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
      - key: branch_drop_user
        label: DROP USER name
      - key: branch_drop_user_if_exists
        label: DROP USER IF EXISTS name
    object_state:
      label: 目标 role 对象状态
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
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: non_important
      values:
      - present
      - absent
    multi_user_clause:
      label: 多角色删除
      importance: non_important
      values:
      - single_role
      - multiple_roles
    authorization_path:
      label: 权限路径
      importance: non_important
      values:
      - createrole
      - superuser
      - non_createrole
    role_dependency:
      label: 角色依赖
      importance: non_important
      values:
      - no_dependencies
      - owns_objects
      - has_active_connections
    role_name_shape:
      label: 角色标识符形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_id
      - non_existent_name
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - createrole_session
      - superuser_session
      - non_createrole_session
    dependency_context:
      label: 依赖对象驻留情况
      importance: non_important
      values:
      - no_dependencies
      - role_owns_objects
      - role_has_active_sessions
    error_type:
      label: 失败原因分类
      importance: non_important
      values:
      - none
      - non_existent_without_if_exists
      - role_owns_objects
      - insufficient_privilege
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
      - reassign_objects_then_drop
      - drop_role
      - terminate_sessions
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - multi_user_clause
    - authorization_path
    - role_dependency
    - role_name_shape
    - privilege_context
    - dependency_context
    - error_type
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP USER [ IF EXISTS ] {role_name} [, ...]"
    verification_query_template: "SELECT rolname FROM pg_roles WHERE rolname = '{role_name}'"
    factor_value_bindings: {}
```
