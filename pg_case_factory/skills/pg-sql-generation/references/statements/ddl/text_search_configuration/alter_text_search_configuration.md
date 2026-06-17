# 技能：ALTER TEXT SEARCH CONFIGURATION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altertsconfiguration.html

```sql
ALTER TEXT SEARCH CONFIGURATION name
    ADD MAPPING FOR token_type [, ... ] WITH dictionary_name [, ... ]
ALTER TEXT SEARCH CONFIGURATION name
    ALTER MAPPING FOR token_type [, ... ] WITH dictionary_name [, ... ]
ALTER TEXT SEARCH CONFIGURATION name
    ALTER MAPPING REPLACE old_dictionary WITH new_dictionary
ALTER TEXT SEARCH CONFIGURATION name
    ALTER MAPPING FOR token_type [, ... ] REPLACE old_dictionary WITH new_dictionary
ALTER TEXT SEARCH CONFIGURATION name
    DROP MAPPING [ IF EXISTS ] FOR token_type [, ... ]
ALTER TEXT SEARCH CONFIGURATION name RENAME TO new_name
ALTER TEXT SEARCH CONFIGURATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER TEXT SEARCH CONFIGURATION name SET SCHEMA new_schema
```

PG16 关键约束：
- ALTER TEXT SEARCH CONFIGURATION 要求执行者是配置的 owner（superusers 自动拥有此权限）
- ADD MAPPING 要求引用的 dictionary 存在
- ALTER MAPPING REPLACE 要求 old_dictionary 在映射中存在，new_dictionary 存在
- DROP MAPPING IF EXISTS 对不存在的 token_type 映射不报错
- RENAME/OWNER/SET SCHEMA 与其他对象 ALTER 行为一致
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：ALTER TEXT SEARCH CONFIGURATION — change the definition of a text search configuration

该 reference 关注全文搜索配置的映射增删改、重命名、属主变更和 schema 移动，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（ADD MAPPING / ALTER MAPPING / ALTER MAPPING REPLACE / ALTER MAPPING FOR REPLACE / DROP MAPPING / RENAME TO / OWNER TO / SET SCHEMA）
- object_state：目标 text search configuration 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（add_mapping / alter_mapping / alter_mapping_replace / alter_mapping_for_replace / drop_mapping / rename / owner / set_schema）
- if_exists_clause：DROP MAPPING 的 IF EXISTS 子句（省略 / 指定）
- owner_target：OWNER TO 目标形态（指定 new_owner / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- dictionary_existence：引用的 dictionary 存在性（存在 / 不存在）
- token_type_existence：映射中的 token_type 存在性（存在 / 不存在）

### T3：对象名与输入形态因子
- config_name_shape：text search configuration 名称形态
- new_name_shape：RENAME TO 新名称形态
- owner_name_shape：OWNER TO 目标角色名称形态
- schema_name_shape：SET SCHEMA 目标 schema 名称形态
- dictionary_name_shape：dictionary 名称形态
- token_type_name_shape：token type 名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（owner / non_owner / superuser）
- role_existence：OWNER TO 指定的角色存在性（存在 / 不存在）
- schema_existence：SET SCHEMA 目标 schema 存在性（存在 / 不存在）
- dictionary_dependency：dictionary 依赖关系

### T5：异常与边界因子
- nonexistent_config：目标 text search configuration 不存在
- nonexistent_dictionary：引用的 dictionary 不存在
- nonexistent_token_type_mapping：映射中不存在指定 token_type
- duplicate_new_name：RENAME TO 新名称与已有配置重名
- nonexistent_owner_role：OWNER TO 目标角色不存在
- nonexistent_target_schema：SET SCHEMA 目标 schema 不存在
- non_owner_attempt：非 owner 尝试修改
- drop_mapping_without_if_exists：DROP MAPPING 不存在映射且无 IF EXISTS

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER TEXT SEARCH CONFIGURATION 八个语法分支中的所有行为路径。
- 覆盖目标 text search configuration 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 owner 权限边界和 dictionary 依赖。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER TEXT SEARCH CONFIGURATION 要求执行者是配置的 owner；非 owner 执行路径属于失败路径。
- 必须预创建可被修改的目标 text search configuration，并为每个 ALTER 分支准备最小合法前置状态。
- ADD MAPPING 要求引用的 dictionary 存在；不存在属于失败路径。
- ALTER MAPPING REPLACE 要求 old_dictionary 在映射中存在，new_dictionary 存在。
- DROP MAPPING IF EXISTS 对不存在的 token_type 映射不报错（no-op 路径）。
- ALTER TEXT SEARCH CONFIGURATION 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的对象变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER TEXT SEARCH CONFIGURATION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- ADD/ALTER/DROP MAPPING 分支的 dictionary 依赖因子必须挂靠到对应分支的样本上。
- DROP MAPPING IF EXISTS 因子必须挂靠到 DROP MAPPING 分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 OWNER TO 目标形态、IF EXISTS 子句和 dictionary 依赖代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: text_search_configuration
  skill_name: alter_text_search_configuration
  official_source: https://www.postgresql.org/docs/16/sql-altertsconfiguration.html
  statement:
    key: alter_text_search_configuration
    name: ALTER TEXT SEARCH CONFIGURATION
    aliases:
    - alter_text_search_configuration
    - ALTER TEXT SEARCH CONFIGURATION
    purpose: ALTER TEXT SEARCH CONFIGURATION — change the definition of a text search configuration
  syntax_templates:
  - "ALTER TEXT SEARCH CONFIGURATION name\n    ADD MAPPING FOR token_type [, ... ] WITH dictionary_name [, ... ]"
  - "ALTER TEXT SEARCH CONFIGURATION name\n    ALTER MAPPING FOR token_type [, ... ] WITH dictionary_name [, ... ]"
  - "ALTER TEXT SEARCH CONFIGURATION name\n    ALTER MAPPING REPLACE old_dictionary WITH new_dictionary"
  - "ALTER TEXT SEARCH CONFIGURATION name\n    ALTER MAPPING FOR token_type [, ... ] REPLACE old_dictionary WITH new_dictionary"
  - "ALTER TEXT SEARCH CONFIGURATION name\n    DROP MAPPING [ IF EXISTS ] FOR token_type [, ... ]"
  - "ALTER TEXT SEARCH CONFIGURATION name RENAME TO new_name"
  - "ALTER TEXT SEARCH CONFIGURATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER TEXT SEARCH CONFIGURATION name SET SCHEMA new_schema"
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
    - if_exists_clause
    - owner_target
    - dictionary_existence
    - token_type_existence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - config_name_shape
    - new_name_shape
    - owner_name_shape
    - schema_name_shape
    - dictionary_name_shape
    - token_type_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - role_existence
    - schema_existence
    - dictionary_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_config
    - nonexistent_dictionary
    - nonexistent_token_type_mapping
    - duplicate_new_name
    - nonexistent_owner_role
    - nonexistent_target_schema
    - non_owner_attempt
    - drop_mapping_without_if_exists
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
      - key: branch_add_mapping
        label: ALTER TEXT SEARCH CONFIGURATION name ADD MAPPING FOR ... WITH ...
      - key: branch_alter_mapping
        label: ALTER TEXT SEARCH CONFIGURATION name ALTER MAPPING FOR ... WITH ...
      - key: branch_alter_mapping_replace
        label: ALTER TEXT SEARCH CONFIGURATION name ALTER MAPPING REPLACE old_dictionary WITH new_dictionary
      - key: branch_alter_mapping_for_replace
        label: ALTER TEXT SEARCH CONFIGURATION name ALTER MAPPING FOR ... REPLACE old_dictionary WITH new_dictionary
      - key: branch_drop_mapping
        label: ALTER TEXT SEARCH CONFIGURATION name DROP MAPPING [ IF EXISTS ] FOR ...
      - key: branch_rename
        label: ALTER TEXT SEARCH CONFIGURATION name RENAME TO new_name
      - key: branch_owner
        label: ALTER TEXT SEARCH CONFIGURATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_set_schema
        label: ALTER TEXT SEARCH CONFIGURATION name SET SCHEMA new_schema
    object_state:
      label: 目标 text search configuration 对象状态
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
      - add_mapping
      - alter_mapping
      - alter_mapping_replace
      - alter_mapping_for_replace
      - drop_mapping
      - rename
      - owner
      - set_schema
    if_exists_clause:
      label: DROP MAPPING 的 IF EXISTS 子句
      importance: non_important
      values:
      - omitted
      - present
    owner_target:
      label: OWNER TO 目标形态
      importance: non_important
      values:
      - specified_new_owner
      - specified_current_role
      - specified_current_user
      - specified_session_user
    dictionary_existence:
      label: 引用的 dictionary 存在性
      importance: non_important
      values:
      - dictionary_exists
      - dictionary_not_exists
    token_type_existence:
      label: 映射中的 token_type 存在性
      importance: non_important
      values:
      - token_type_mapped
      - token_type_not_mapped
    config_name_shape:
      label: text search configuration 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - reserved_word_as_name
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
    dictionary_name_shape:
      label: dictionary 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - nonexistent_name
    token_type_name_shape:
      label: token type 名称形态
      importance: non_important
      values:
      - valid_token_type
      - invalid_token_type
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
    schema_existence:
      label: SET SCHEMA 目标 schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    dictionary_dependency:
      label: dictionary 依赖关系
      importance: non_important
      values:
      - dictionary_exists_and_valid
      - dictionary_missing
    nonexistent_config:
      label: 目标 text search configuration 不存在
      importance: non_important
      values:
      - config_exists
      - config_missing
    nonexistent_dictionary:
      label: 引用的 dictionary 不存在
      importance: non_important
      values:
      - dictionary_exists
      - dictionary_missing
    nonexistent_token_type_mapping:
      label: 映射中不存在指定 token_type
      importance: non_important
      values:
      - mapping_exists
      - mapping_missing
    duplicate_new_name:
      label: RENAME TO 新名称与已有配置重名
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
    drop_mapping_without_if_exists:
      label: DROP MAPPING 不存在映射且无 IF EXISTS
      importance: non_important
      values:
      - with_if_exists
      - without_if_exists
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_ts_config
      - mapping_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_mapping_revert
      - revert_rename
      - revert_owner
      - drop_text_search_configuration
      - role_cleanup
  defaults:
    expected_status: success
    object_state: exists
    privilege_level: owner
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - if_exists_clause
    - owner_target
    - dictionary_existence
    - token_type_existence
    - config_name_shape
    - new_name_shape
    - owner_name_shape
    - schema_name_shape
    - dictionary_name_shape
    - token_type_name_shape
    - privilege_level
    - role_existence
    - schema_existence
    - dictionary_dependency
    - nonexistent_config
    - nonexistent_dictionary
    - nonexistent_token_type_mapping
    - duplicate_new_name
    - nonexistent_owner_role
    - nonexistent_target_schema
    - non_owner_attempt
    - drop_mapping_without_if_exists
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER TEXT SEARCH CONFIGURATION {config_name} {alter_clause}"
    verification_query_template: "SELECT cfgname FROM pg_ts_config WHERE cfgname = '{config_name}'"
    factor_value_bindings: {}
```
