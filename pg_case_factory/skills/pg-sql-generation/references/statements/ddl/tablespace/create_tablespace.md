# 技能：CREATE TABLESPACE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createtablespace.html

```sql
CREATE TABLESPACE tablespace_name
    [ OWNER { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER } ]
    LOCATION 'directory'
    [ WITH ( tablespace_option = value [, ... ] ) ]
```

## 语句作用

官方说明：CREATE TABLESPACE — define a new tablespace

该 reference 关注存储级对象（tablespace）的定义、权限边界、文件系统依赖和命名约束，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE TABLESPACE 单一顶层形式）
- object_state：目标 tablespace 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- owner_clause：OWNER 子句形态（省略 / 指定 new_owner / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- with_clause：WITH (tablespace_option) 子句形态（省略 / 指定单选项 / 指定多选项）
- directory_condition：LOCATION 目录条件（目录存在且合规 / 目录不存在 / 目录权限不符 / 目录非空）

### T3：对象名与输入形态因子
- tablespace_name_shape：tablespace 名称形态
- owner_name_shape：owner 名称形态
- directory_path_shape：LOCATION 目录路径形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / non_superuser）
- filesystem_dependency：文件系统依赖（目录物理存在 / 目录不存在 / 路径非绝对 / 目录所有权不符）
- transaction_context：事务上下文（事务外 / 事务内）
- role_existence：OWNER 指定的角色存在性（存在 / 不存在）

### T5：异常与边界因子
- duplicate_tablespace_name：重名冲突
- pg_reserved_name：pg_ 前缀保留名
- nonexistent_directory：目录不存在
- non_absolute_path：非绝对路径
- invalid_option：无效的 tablespace_option
- directory_permission_denied：目录权限不符
- non_superuser_attempt：非 superuser 尝试
- inside_transaction_block：在事务块内执行
- nonexistent_owner_role：owner 角色不存在

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE TABLESPACE 单一语法分支中的所有可选子句组合（OWNER / WITH）。
- 覆盖目标 tablespace 存在 / 不存在 / 冲突（重名）路径。
- 覆盖成功路径与失败路径，包括 superuser 权限边界、文件系统依赖和事务限制。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE TABLESPACE 要求 SUPERUSER 权限，必须在生成样本中显式标注；非 superuser 执行路径属于失败路径。
- LOCATION 目录必须物理存在于文件系统上，且为绝对路径、空目录、由 PostgreSQL 系统用户所有；目录不存在 / 非绝对路径 / 权限不符 / 非空目录均属于失败路径。
- CREATE TABLESPACE 不能在事务块内执行（no transaction block），必须显式标注此环境限制。
- CREATE TABLESPACE 不涉及 table / column / index 组合，不需要挂靠基表列类型。
- tablespace 名称不能以 pg_ 开头（保留给系统 tablespace），此类命名属于失败路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 CREATE TABLESPACE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与文件系统依赖相关的因子必须挂靠到满足前置环境条件的样本上。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和 superuser 权限核心路径。
- 次优先保证 OWNER 子句形态、WITH 子句形态和目录条件代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: tablespace
  skill_name: create_tablespace
  official_source: https://www.postgresql.org/docs/16/sql-createtablespace.html
  statement:
    key: create_tablespace
    name: CREATE TABLESPACE
    aliases:
    - create_tablespace
    - CREATE TABLESPACE
    purpose: CREATE TABLESPACE — define a new tablespace
  syntax_templates:
  - "CREATE TABLESPACE tablespace_name\n    [ OWNER { new_owner | CURRENT_ROLE |\
    \ CURRENT_USER | SESSION_USER } ]\n    LOCATION 'directory'\n    [ WITH ( tablespace_option\
    \ = value [, ... ] ) ]"
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
    - owner_clause
    - with_clause
    - directory_condition
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - tablespace_name_shape
    - owner_name_shape
    - directory_path_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - filesystem_dependency
    - transaction_context
    - role_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_tablespace_name
    - pg_reserved_name
    - nonexistent_directory
    - non_absolute_path
    - invalid_option
    - directory_permission_denied
    - non_superuser_attempt
    - inside_transaction_block
    - nonexistent_owner_role
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
        label: CREATE TABLESPACE 标准形式
    object_state:
      label: 目标 tablespace 对象状态
      importance: important
      values:
      - not_exists
      - exists
      - reserved_name_conflict
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    owner_clause:
      label: OWNER 子句形态
      importance: non_important
      values:
      - omitted
      - specified_new_owner
      - specified_current_role
      - specified_current_user
      - specified_session_user
    with_clause:
      label: WITH 子句形态
      importance: non_important
      values:
      - omitted
      - single_option_seq_page_cost
      - single_option_random_page_cost
      - single_option_effective_io_concurrency
      - single_option_maintenance_io_concurrency
      - multiple_options
    directory_condition:
      label: LOCATION 目录条件
      importance: non_important
      values:
      - exists_valid
      - not_exists
      - permission_denied
      - non_empty
    tablespace_name_shape:
      label: tablespace 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - pg_prefix_reserved
      - duplicate_name
      - invalid_name
    owner_name_shape:
      label: owner 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_role
    directory_path_shape:
      label: LOCATION 目录路径形态
      importance: non_important
      values:
      - absolute_path
      - relative_path
      - empty_path
      - special_path
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - non_superuser
    filesystem_dependency:
      label: 文件系统依赖
      importance: non_important
      values:
      - directory_exists_owned_by_postgres
      - directory_not_exists
      - path_not_absolute
      - directory_wrong_owner
    transaction_context:
      label: 事务上下文
      importance: non_important
      values:
      - outside_transaction
      - inside_transaction_block
    role_existence:
      label: OWNER 角色存在性
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    duplicate_tablespace_name:
      label: 重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    pg_reserved_name:
      label: pg_ 前缀保留名
      importance: non_important
      values:
      - normal_name
      - pg_prefix_name
    nonexistent_directory:
      label: 目录不存在
      importance: non_important
      values:
      - directory_exists
      - directory_missing
    non_absolute_path:
      label: 非绝对路径
      importance: non_important
      values:
      - absolute_path
      - relative_path
    invalid_option:
      label: 无效的 tablespace_option
      importance: non_important
      values:
      - valid_option
      - invalid_option_name
    directory_permission_denied:
      label: 目录权限不符
      importance: non_important
      values:
      - proper_permission
      - wrong_owner
    non_superuser_attempt:
      label: 非 superuser 尝试
      importance: non_important
      values:
      - superuser_execution
      - non_superuser_execution
    inside_transaction_block:
      label: 在事务块内执行
      importance: non_important
      values:
      - outside_transaction
      - inside_transaction
    nonexistent_owner_role:
      label: owner 角色不存在
      importance: non_important
      values:
      - role_exists
      - role_missing
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_tablespace
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_tablespace
      - filesystem_cleanup
      - role_cleanup
  defaults:
    expected_status: success
    privilege_level: superuser
    transaction_context: outside_transaction
    directory_condition: exists_valid
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - owner_clause
    - with_clause
    - directory_condition
    - tablespace_name_shape
    - owner_name_shape
    - directory_path_shape
    - privilege_level
    - filesystem_dependency
    - transaction_context
    - role_existence
    - duplicate_tablespace_name
    - pg_reserved_name
    - nonexistent_directory
    - non_absolute_path
    - invalid_option
    - directory_permission_denied
    - non_superuser_attempt
    - inside_transaction_block
    - nonexistent_owner_role
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE TABLESPACE {tablespace_name} [ OWNER {owner_spec}\
      \ ] LOCATION '{directory}' [ WITH ( tablespace_option = value [, ... ] ) ]"
    verification_query_template: "SELECT spcname FROM pg_tablespace WHERE spcname\
      \ = '{tablespace_name}'"
    factor_value_bindings: {}
```
