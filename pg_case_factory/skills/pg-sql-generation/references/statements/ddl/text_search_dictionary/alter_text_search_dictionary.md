# 技能：ALTER TEXT SEARCH DICTIONARY

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altertsdictionary.html

```sql
ALTER TEXT SEARCH DICTIONARY name (
    option [ = value ] [, ... ]
)
ALTER TEXT SEARCH DICTIONARY name RENAME TO new_name
ALTER TEXT SEARCH DICTIONARY name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER TEXT SEARCH DICTIONARY name SET SCHEMA new_schema
```

PG16 关键约束：
- ALTER TEXT SEARCH DICTIONARY 要求执行者是字典的 owner
- 选项形式：option [ = value ]；省略 "= value" 则移除该选项设置（恢复默认值）
- RENAME/OWNER/SET SCHEMA 与其他对象 ALTER 行为一致
- OWNER TO 还要求当前用户能够 SET ROLE 到新 owner
- 可用 dummy 选项强制重读配置文件（如 ALTER ... (dummy)）
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：ALTER TEXT SEARCH DICTIONARY — change the definition of a text search dictionary

该 reference 关注全文搜索字典的选项修改、重命名、属主变更和 schema 移动，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（option 形式 / RENAME TO / OWNER TO / SET SCHEMA）
- object_state：目标 text search dictionary 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（option_modify / rename / owner / set_schema）
- option_action：选项操作类型（设置新值 / 移除选项恢复默认 / dummy 刷新）
- owner_target：OWNER TO 目标形态（指定 new_owner / CURRENT_ROLE / CURRENT_USER / SESSION_USER）

### T3：对象名与输入形态因子
- dict_name_shape：text search dictionary 名称形态
- new_name_shape：RENAME TO 新名称形态
- owner_name_shape：OWNER TO 目标角色名称形态
- schema_name_shape：SET SCHEMA 目标 schema 名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（owner / non_owner / superuser）
- role_existence：OWNER TO 指定的角色存在性（存在 / 不存在）
- set_role_capability：当前用户能否 SET ROLE 到新 owner（可以 / 不可以）
- schema_existence：SET SCHEMA 目标 schema 存在性（存在 / 不存在）

### T5：异常与边界因子
- nonexistent_dict：目标 text search dictionary 不存在
- duplicate_new_name：RENAME TO 新名称与已有字典重名
- nonexistent_owner_role：OWNER TO 目标角色不存在
- nonexistent_target_schema：SET SCHEMA 目标 schema 不存在
- non_owner_attempt：非 owner 尝试修改
- cannot_set_role：当前用户无法 SET ROLE 到新 owner

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER TEXT SEARCH DICTIONARY 四个语法分支中的所有行为路径。
- 覆盖目标 text search dictionary 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 owner 权限边界和选项操作。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER TEXT SEARCH DICTIONARY 要求执行者是字典的 owner；非 owner 执行路径属于失败路径。
- ALTER TEXT SEARCH DICTIONARY OWNER TO 还要求当前用户能够 SET ROLE 到新 owner 角色。
- 选项形式中省略 "= value" 时移除该选项（恢复默认值），此行为属于成功路径。
- ALTER TEXT SEARCH DICTIONARY 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的对象变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER TEXT SEARCH DICTIONARY 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- OWNER TO 分支的角色存在性和 SET ROLE 能力因子必须挂靠到对应分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证选项操作类型、OWNER TO 目标形态代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: text_search_dictionary
  skill_name: alter_text_search_dictionary
  official_source: https://www.postgresql.org/docs/16/sql-altertsdictionary.html
  statement:
    key: alter_text_search_dictionary
    name: ALTER TEXT SEARCH DICTIONARY
    aliases:
    - alter_text_search_dictionary
    - ALTER TEXT SEARCH DICTIONARY
    purpose: ALTER TEXT SEARCH DICTIONARY — change the definition of a text search dictionary
  syntax_templates:
  - "ALTER TEXT SEARCH DICTIONARY name (\n    option [ = value ] [, ... ]\n)"
  - "ALTER TEXT SEARCH DICTIONARY name RENAME TO new_name"
  - "ALTER TEXT SEARCH DICTIONARY name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER TEXT SEARCH DICTIONARY name SET SCHEMA new_schema"
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
    - option_action
    - owner_target
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - dict_name_shape
    - new_name_shape
    - owner_name_shape
    - schema_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - role_existence
    - set_role_capability
    - schema_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_dict
    - duplicate_new_name
    - nonexistent_owner_role
    - nonexistent_target_schema
    - non_owner_attempt
    - cannot_set_role
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
      - key: branch_option
        label: ALTER TEXT SEARCH DICTIONARY name ( option [ = value ] [, ... ] )
      - key: branch_rename
        label: ALTER TEXT SEARCH DICTIONARY name RENAME TO new_name
      - key: branch_owner
        label: ALTER TEXT SEARCH DICTIONARY name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_set_schema
        label: ALTER TEXT SEARCH DICTIONARY name SET SCHEMA new_schema
    object_state:
      label: 目标 text search dictionary 对象状态
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
      - option_modify
      - rename
      - owner
      - set_schema
    option_action:
      label: 选项操作类型
      importance: non_important
      values:
      - set_new_value
      - remove_option_restore_default
      - dummy_refresh
    owner_target:
      label: OWNER TO 目标形态
      importance: non_important
      values:
      - specified_new_owner
      - specified_current_role
      - specified_current_user
      - specified_session_user
    dict_name_shape:
      label: text search dictionary 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - nonexistent_name
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - duplicate_name
    owner_name_shape:
      label: OWNER TO 目标角色名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - nonexistent_role
    schema_name_shape:
      label: SET SCHEMA 目标 schema 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_schema
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - owner
      - non_owner
      - superuser
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
    schema_existence:
      label: SET SCHEMA 目标 schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    nonexistent_dict:
      label: 目标 text search dictionary 不存在
      importance: non_important
      values:
      - dict_exists
      - dict_missing
    duplicate_new_name:
      label: RENAME TO 新名称与已有字典重名
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    nonexistent_owner_role:
      label: OWNER TO 目标角色不存在
      importance: non_important
      values:
      - role_exists
      - role_missing
    nonexistent_target_schema:
      label: SET SCHEMA 目标 schema 不存在
      importance: non_important
      values:
      - schema_exists
      - schema_missing
    non_owner_attempt:
      label: 非 owner 尝试修改
      importance: non_important
      values:
      - owner_execution
      - non_owner_execution
    cannot_set_role:
      label: 当前用户无法 SET ROLE 到新 owner
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role_to_target
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_ts_dict
      - option_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - revert_option
      - revert_rename
      - revert_owner
      - drop_text_search_dictionary
      - role_cleanup
  defaults:
    expected_status: success
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - option_action
    - owner_target
    - dict_name_shape
    - new_name_shape
    - owner_name_shape
    - schema_name_shape
    - privilege_level
    - role_existence
    - set_role_capability
    - schema_existence
    - nonexistent_dict
    - duplicate_new_name
    - nonexistent_owner_role
    - nonexistent_target_schema
    - non_owner_attempt
    - cannot_set_role
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER TEXT SEARCH DICTIONARY {dict_name} {alter_clause}"
    verification_query_template: "SELECT dictname FROM pg_ts_dict WHERE dictname = '{dict_name}'"
    factor_value_bindings: {}
```
