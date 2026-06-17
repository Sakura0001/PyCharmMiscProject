# 技能：ALTER TABLESPACE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altertablespace.html

```sql
ALTER TABLESPACE name RENAME TO new_name
ALTER TABLESPACE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER TABLESPACE name SET ( tablespace_option = value [, ... ] )
ALTER TABLESPACE name RESET ( tablespace_option [, ... ] )
```

## 语句作用

官方说明：ALTER TABLESPACE — change the definition of a tablespace

该 reference 关注存储级对象（tablespace）的定义变更、权限边界、选项配置和命名约束，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（RENAME TO / OWNER TO / SET / RESET 四种顶层形式）
- object_state：目标 tablespace 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（rename / owner / set / reset）
- owner_target：OWNER TO 目标形态（指定 new_owner / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- tablespace_option：SET/RESET 选项内容（seq_page_cost / random_page_cost / effective_io_concurrency / maintenance_io_concurrency / 多选项组合）

### T3：对象名与输入形态因子
- tablespace_name_shape：tablespace 名称形态
- new_name_shape：RENAME TO 新名称形态
- owner_name_shape：OWNER TO 目标角色名称形态
- option_name_shape：SET/RESET 选项名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / owner / non_owner）
- role_existence：OWNER TO 指定的角色存在性（存在 / 不存在）
- set_role_capability：当前用户能否 SET ROLE 到新 owner（可以 / 不可以）

### T5：异常与边界因子
- nonexistent_tablespace：目标 tablespace 不存在
- pg_reserved_new_name：新名称 pg_ 前缀保留名
- duplicate_new_name：新名称与已有 tablespace 重名
- non_owner_attempt：非 owner 尝试修改
- cannot_set_role：当前用户无法 SET ROLE 到新 owner
- nonexistent_owner_role：OWNER TO 目标角色不存在
- invalid_option_name：无效的 tablespace_option 名称
- invalid_option_value：无效的 tablespace_option 值

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER TABLESPACE 四个语法分支中的所有行为路径。
- 覆盖目标 tablespace 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 owner 权限边界和 pg_ 前缀命名约束。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER TABLESPACE 要求执行者是 tablespace 的 owner；superusers 自动拥有此权限。非 owner 执行路径属于失败路径。
- ALTER TABLESPACE OWNER TO 还要求当前用户能够 SET ROLE 到新 owner 角色；无法 SET ROLE 的路径属于失败路径。
- RENAME TO 新名称不能以 pg_ 开头（保留给系统 tablespace），此类命名属于失败路径。
- ALTER TABLESPACE 不涉及 table / column / index 组合，不需要挂靠基表列类型。
- ALTER TABLESPACE 可在事务块内执行，无事务限制。
- 成功路径必须包含可验证的对象变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER TABLESPACE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- OWNER TO 分支的角色存在性和 SET ROLE 能力因子必须挂靠到对应分支的样本上。
- SET/RESET 分支的选项因子必须挂靠到对应分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 OWNER TO 目标形态、SET/RESET 选项形态和命名约束代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: tablespace
  skill_name: alter_tablespace
  official_source: https://www.postgresql.org/docs/16/sql-altertablespace.html
  statement:
    key: alter_tablespace
    name: ALTER TABLESPACE
    aliases:
    - alter_tablespace
    - ALTER TABLESPACE
    purpose: ALTER TABLESPACE — change the definition of a tablespace
  syntax_templates:
  - "ALTER TABLESPACE name RENAME TO new_name"
  - "ALTER TABLESPACE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER\
    \ }"
  - "ALTER TABLESPACE name SET ( tablespace_option = value [, ... ] )"
  - "ALTER TABLESPACE name RESET ( tablespace_option [, ... ] )"
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
    - owner_target
    - tablespace_option
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - tablespace_name_shape
    - new_name_shape
    - owner_name_shape
    - option_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - role_existence
    - set_role_capability
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_tablespace
    - pg_reserved_new_name
    - duplicate_new_name
    - non_owner_attempt
    - cannot_set_role
    - nonexistent_owner_role
    - invalid_option_name
    - invalid_option_value
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
      - key: branch_rename
        label: ALTER TABLESPACE name RENAME TO new_name
      - key: branch_owner
        label: ALTER TABLESPACE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_set
        label: ALTER TABLESPACE name SET ( tablespace_option = value [, ... ] )
      - key: branch_reset
        label: ALTER TABLESPACE name RESET ( tablespace_option [, ... ] )
    object_state:
      label: 目标 tablespace 对象状态
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
    alter_action:
      label: ALTER 行为类型
      importance: non_important
      values:
      - rename
      - owner
      - set
      - reset
    owner_target:
      label: OWNER TO 目标形态
      importance: non_important
      values:
      - specified_new_owner
      - specified_current_role
      - specified_current_user
      - specified_session_user
    tablespace_option:
      label: SET/RESET 选项内容
      importance: non_important
      values:
      - seq_page_cost
      - random_page_cost
      - effective_io_concurrency
      - maintenance_io_concurrency
      - multiple_options
    tablespace_name_shape:
      label: tablespace 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_as_name
      - nonexistent_name
      - invalid_name
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - pg_prefix_reserved
      - duplicate_name
      - invalid_name
    owner_name_shape:
      label: OWNER TO 目标角色名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_role
    option_name_shape:
      label: SET/RESET 选项名称形态
      importance: non_important
      values:
      - valid_option
      - invalid_option_name
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - owner
      - non_owner
    role_existence:
      label: OWNER TO 角色存在性
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    set_role_capability:
      label: 当前用户能否 SET ROLE 到新 owner
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role
    nonexistent_tablespace:
      label: 目标 tablespace 不存在
      importance: non_important
      values:
      - tablespace_exists
      - tablespace_missing
    pg_reserved_new_name:
      label: 新名称 pg_ 前缀保留名
      importance: non_important
      values:
      - normal_name
      - pg_prefix_name
    duplicate_new_name:
      label: 新名称与已有 tablespace 重名
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    non_owner_attempt:
      label: 非 owner 尝试修改
      importance: non_important
      values:
      - owner_execution
      - non_owner_execution
      - superuser_execution
    cannot_set_role:
      label: 当前用户无法 SET ROLE 到新 owner
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role_to_target
    nonexistent_owner_role:
      label: OWNER TO 目标角色不存在
      importance: non_important
      values:
      - role_exists
      - role_missing
    invalid_option_name:
      label: 无效的 tablespace_option 名称
      importance: non_important
      values:
      - valid_option
      - unrecognized_option
    invalid_option_value:
      label: 无效的 tablespace_option 值
      importance: non_important
      values:
      - valid_value
      - invalid_value
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_tablespace
      - effect_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - revert_rename
      - revert_owner
      - reset_option
      - drop_tablespace
      - role_cleanup
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
    - owner_target
    - tablespace_option
    - tablespace_name_shape
    - new_name_shape
    - owner_name_shape
    - option_name_shape
    - privilege_level
    - role_existence
    - set_role_capability
    - nonexistent_tablespace
    - pg_reserved_new_name
    - duplicate_new_name
    - non_owner_attempt
    - cannot_set_role
    - nonexistent_owner_role
    - invalid_option_name
    - invalid_option_value
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER TABLESPACE {tablespace_name} {alter_clause}"
    verification_query_template: "SELECT spcname, spcowner FROM pg_tablespace WHERE spcname = '{tablespace_name}'"
    factor_value_bindings: {}
```
