# 技能：CREATE USER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createuser.html

```sql
CREATE USER name [ [ WITH ] option [ ... ] ]

where option can be:

      SUPERUSER | NOSUPERUSER
    | CREATEDB | NOCREATEDB
    | CREATEROLE | NOCREATEROLE
    | INHERIT | NOINHERIT
    | LOGIN | NOLOGIN
    | REPLICATION | NOREPLICATION
    | BYPASSRLS | NOBYPASSRLS
    | CONNECTION LIMIT connlimit
    | [ ENCRYPTED ] PASSWORD 'password' | PASSWORD NULL
    | VALID UNTIL 'timestamp'
    | IN ROLE role_name [, ...]
    | IN GROUP role_name [, ...]
    | ROLE role_name [, ...]
    | ADMIN role_name [, ...]
    | USER role_name [, ...]
    | SYSID uid
```

PG16 关键约束：
- **CREATE USER 是 CREATE ROLE 的已弃用别名（deprecated alias）**，唯一行为差异是 CREATE USER 默认假定 LOGIN，而 CREATE ROLE 默认假定 NOLOGIN
- CREATE USER / CREATE ROLE 要求执行者拥有 CREATEROLE 权限（superuser 自动拥有）
- 该语句不涉及列类型，不需要挂靠基表列类型
- 不支持 IF NOT EXISTS 或 OR REPLACE
- IN GROUP、USER、SYSID 为遗留选项（IN GROUP 等同于 IN ROLE，USER 等同于 ROLE，SYSID 被忽略）

## 语句作用

官方说明：CREATE USER — define a new database role

**重要提示：CREATE USER 是 CREATE ROLE 的已弃用别名（deprecated alias）。唯一行为差异是 CREATE USER 默认假定 LOGIN（用户可连接），而 CREATE ROLE 默认假定 NOLOGIN。所有其他行为与 CREATE ROLE 一致。**

该 reference 关注角色定义的各种选项组合、权限边界和命名约束，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE USER 标准形式）
- object_state：目标 role 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- login_default：LOGIN 默认行为（CREATE USER 默认 LOGIN / 显式 NOLOGIN / 显式 LOGIN）
- role_options：角色选项组合（无选项 / 单选项 / 多选项）
- password_clause：PASSWORD 子句形态（省略 / PASSWORD 'value' / ENCRYPTED PASSWORD 'value' / PASSWORD NULL）
- valid_until_clause：VALID UNTIL 子句形态（省略 / 指定）
- membership_clause：成员关系子句（IN ROLE / IN GROUP / ROLE / ADMIN / USER）

### T3：对象名与输入形态因子
- role_name_shape：角色名称形态
- password_value_shape：PASSWORD 值形态
- referenced_role_name_shape：引用的角色名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（CREATEROLE / superuser / non_createrole）
- referenced_role_existence：引用的角色存在性（存在 / 不存在）

### T5：异常与边界因子
- duplicate_role_name：重名冲突
- insufficient_privilege：缺少 CREATEROLE 权限
- nonexistent_referenced_role：引用的角色不存在
- reserved_role_name：保留角色名

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE USER 单一语法分支中的所有选项组合路径。
- 覆盖目标 role 存在 / 不存在 / 冲突路径。
- 覆盖成功路径与失败路径，包括 CREATEROLE 权限边界。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE USER 是 CREATE ROLE 的已弃用别名，必须在每个样本中显式标注此关系。
- CREATE USER 默认假定 LOGIN，此默认行为必须覆盖；显式指定 NOLOGIN 或 LOGIN 的路径也必须覆盖。
- CREATE USER / CREATE ROLE 要求 CREATEROLE 权限；缺少 CREATEROLE 的执行路径属于失败路径。
- CREATE USER 不支持 IF NOT EXISTS 或 OR REPLACE，必须覆盖重名冲突的失败路径。
- CREATE USER 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的角色存在性检查，并在生命周期末尾清理角色。
- 每个样本必须包含明确的前置对象准备、目标 CREATE USER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 CREATEROLE 权限相关的因子必须挂靠到具有明确权限上下文的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 LOGIN 默认行为、PASSWORD 子句和角色选项组合代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: user
  skill_name: create_user
  official_source: https://www.postgresql.org/docs/16/sql-createuser.html
  statement:
    key: create_user
    name: CREATE USER
    aliases:
    - create_user
    - CREATE USER
    - create_role
    - CREATE ROLE
    purpose: CREATE USER — define a new database role (deprecated alias for CREATE ROLE)
  syntax_templates:
  - "CREATE USER name [ [ WITH ] option [ ... ] ]"
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
    - login_default
    - role_options
    - password_clause
    - valid_until_clause
    - membership_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - role_name_shape
    - password_value_shape
    - referenced_role_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - referenced_role_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_role_name
    - insufficient_privilege
    - nonexistent_referenced_role
    - reserved_role_name
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
        label: CREATE USER 标准形式
    object_state:
      label: 目标 role 对象状态
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
    login_default:
      label: LOGIN 默认行为
      importance: non_important
      values:
      - default_login
      - explicit_nologin
      - explicit_login
    role_options:
      label: 角色选项组合
      importance: non_important
      values:
      - no_options
      - single_option_superuser
      - single_option_createdb
      - single_option_createrole
      - multiple_options
    password_clause:
      label: PASSWORD 子句形态
      importance: non_important
      values:
      - omitted
      - password_value
      - encrypted_password_value
      - password_null
    valid_until_clause:
      label: VALID UNTIL 子句形态
      importance: non_important
      values:
      - omitted
      - specified
    membership_clause:
      label: 成员关系子句
      importance: non_important
      values:
      - omitted
      - in_role
      - in_group_legacy
      - role_clause
      - admin_clause
    role_name_shape:
      label: 角色名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_as_name
      - duplicate_name
      - invalid_name
    password_value_shape:
      label: PASSWORD 值形态
      importance: non_important
      values:
      - valid_password
      - empty_password
      - null_password
    referenced_role_name_shape:
      label: 引用的角色名称形态
      importance: non_important
      values:
      - existing_role
      - nonexistent_role
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - createrole
      - superuser
      - non_createrole
    referenced_role_existence:
      label: 引用的角色存在性
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    duplicate_role_name:
      label: 重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    insufficient_privilege:
      label: 缺少 CREATEROLE 权限
      importance: non_important
      values:
      - has_createrole
      - lacks_createrole
    nonexistent_referenced_role:
      label: 引用的角色不存在
      importance: non_important
      values:
      - role_exists
      - role_missing
    reserved_role_name:
      label: 保留角色名
      importance: non_important
      values:
      - normal_name
      - reserved_name
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_roles
      - login_test
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_user
      - drop_role
      - revoke_membership
  defaults:
    expected_status: success
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - login_default
    - role_options
    - password_clause
    - valid_until_clause
    - membership_clause
    - role_name_shape
    - password_value_shape
    - referenced_role_name_shape
    - privilege_level
    - referenced_role_existence
    - duplicate_role_name
    - insufficient_privilege
    - nonexistent_referenced_role
    - reserved_role_name
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE USER {role_name} [ [ WITH ] {option_clause} ]"
    verification_query_template: "SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = '{role_name}'"
    factor_value_bindings: {}
```
