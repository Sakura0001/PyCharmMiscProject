# 技能：ALTER MATERIALIZED VIEW

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altermaterializedview.html

```sql
ALTER MATERIALIZED VIEW [ IF EXISTS ] name
    action [, ... ]
ALTER MATERIALIZED VIEW name
    [ NO ] DEPENDS ON EXTENSION extension_name
ALTER MATERIALIZED VIEW [ IF EXISTS ] name
    RENAME [ COLUMN ] column_name TO new_column_name
ALTER MATERIALIZED VIEW [ IF EXISTS ] name
    RENAME TO new_name
ALTER MATERIALIZED VIEW [ IF EXISTS ] name
    SET SCHEMA new_schema
ALTER MATERIALIZED VIEW ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]
    SET TABLESPACE new_tablespace [ NOWAIT ]

where action is one of:

    ALTER [ COLUMN ] column_name SET STATISTICS integer
    ALTER [ COLUMN ] column_name SET ( attribute_option = value [, ... ] )
    ALTER [ COLUMN ] column_name RESET ( attribute_option [, ... ] )
    ALTER [ COLUMN ] column_name SET STORAGE { PLAIN | EXTERNAL | EXTENDED | MAIN | DEFAULT }
    ALTER [ COLUMN ] column_name SET COMPRESSION compression_method
    CLUSTER ON index_name
    SET WITHOUT CLUSTER
    SET ACCESS METHOD new_access_method
    SET TABLESPACE new_tablespace
    SET ( storage_parameter [= value] [, ... ] )
    RESET ( storage_parameter [, ... ] )
    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
```

## 语句作用

官方说明：ALTER MATERIALIZED VIEW — change the definition of a materialized view

该 reference 关注 materialized view 的多种 ALTER 分支（action 列级操作、DEPENDS ON EXTENSION、RENAME COLUMN、RENAME、SET SCHEMA、SET TABLESPACE），不负责定义基础表模板本身。ALTER MATERIALIZED VIEW 涉及表、列、表达式、索引、约束或类型的分支，需要覆盖仓库基表的代表性表类型与核心列类型。注意：部分分支支持 IF EXISTS（产生 no-op 路径）；ALL IN TABLESPACE 分支不支持 IF EXISTS。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 materialized view 对象状态
- expected_status：预期结果

### T2：重要行为因子
- alter_action_type：ALTER 动作类型
- if_exists_clause：IF EXISTS 子句
- new_owner_shape：新 owner 形态（仅适用于 OWNER TO）
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：materialized view 名形态
- column_name_shape：列名形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- extension_state：扩展依赖状态

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 ALTER MATERIALIZED VIEW 语法分支。
- 需要覆盖仓库基表的代表性表类型与核心列类型。
- ALTER MATERIALIZED VIEW 涉及表、列、表达式、索引、约束或类型的分支，需要覆盖仓库基表的代表性表类型与核心列类型。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 materialized view，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标对象存在时的成功修改路径、目标对象不存在时的失败路径，以及支持 IF EXISTS 分支的代表性 no-op 路径。
- action 列级操作、RENAME COLUMN、RENAME、SET SCHEMA、OWNER TO、DEPENDS ON EXTENSION、ALL IN TABLESPACE 各分支需要保持独立归因。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER MATERIALIZED VIEW 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 需要特殊权限、extension、tablespace 或非事务环境的分支必须在生命周期计划中显式标注环境依赖。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句（IF EXISTS、各 action 类型）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: materialized_view
  skill_name: alter_materialized_view
  official_source: https://www.postgresql.org/docs/16/sql-altermaterializedview.html
  statement:
    key: alter_materialized_view
    name: ALTER MATERIALIZED VIEW
    aliases:
    - alter materialized view
    - ALTER MATERIALIZED VIEW
    purpose: change the definition of a materialized view
  syntax_templates:
  - "ALTER MATERIALIZED VIEW [ IF EXISTS ] name\n    action [, ... ]\nALTER MATERIALIZED\
    \ VIEW name\n    [ NO ] DEPENDS ON EXTENSION extension_name\nALTER MATERIALIZED\
    \ VIEW [ IF EXISTS ] name\n    RENAME [ COLUMN ] column_name TO new_column_name\n\
    ALTER MATERIALIZED VIEW [ IF EXISTS ] name\n    RENAME TO new_name\nALTER MATERIALIZED\
    \ VIEW [ IF EXISTS ] name\n    SET SCHEMA new_schema\nALTER MATERIALIZED VIEW\
    \ ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]\n    SET TABLESPACE\
    \ new_tablespace [ NOWAIT ]\n\nwhere action is one of:\n\n    ALTER [ COLUMN\
    \ ] column_name SET STATISTICS integer\n    ALTER [ COLUMN ] column_name SET\
    \ ( attribute_option = value [, ... ] )\n    ALTER [ COLUMN ] column_name RESET\
    \ ( attribute_option [, ... ] )\n    ALTER [ COLUMN ] column_name SET STORAGE\
    \ { PLAIN | EXTERNAL | EXTENDED | MAIN | DEFAULT }\n    ALTER [ COLUMN ] column_name\
    \ SET COMPRESSION compression_method\n    CLUSTER ON index_name\n    SET WITHOUT\
    \ CLUSTER\n    SET ACCESS METHOD new_access_method\n    SET TABLESPACE new_tablespace\n\
    \    SET ( storage_parameter [= value] [, ... ] )\n    RESET ( storage_parameter\
    \ [, ... ] )\n    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER\
    \ }"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - target_object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - alter_action_type
    - if_exists_clause
    - new_owner_shape
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - column_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - extension_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - ownership_boundary
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
      - key: branch_action
        label: action 列级/存储操作分支
      - key: branch_depends_extension
        label: DEPENDS ON EXTENSION 分支
      - key: branch_rename_column
        label: RENAME COLUMN 分支
      - key: branch_rename
        label: RENAME TO 分支
      - key: branch_set_schema
        label: SET SCHEMA 分支
      - key: branch_set_tablespace_all
        label: ALL IN TABLESPACE 分支
    target_object_state:
      label: 目标 materialized view 对象状态
      importance: important
      values:
      - exists
      - missing
      - wrong_object_type
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    alter_action_type:
      label: ALTER 动作类型
      importance: important
      values:
      - set_statistics
      - set_attribute_option
      - reset_attribute_option
      - set_storage
      - set_compression
      - cluster_on
      - set_without_cluster
      - set_access_method
      - set_tablespace
      - set_storage_parameter
      - reset_storage_parameter
      - owner_to
    if_exists_clause:
      label: IF EXISTS 子句
      importance: non_important
      values:
      - absent
      - present
    new_owner_shape:
      label: 新 owner 形态
      importance: non_important
      values:
      - plain_role
      - current_role
      - current_user
      - session_user
      - missing_role
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - owner
      - granted_role
      - insufficient_privilege
    name_shape:
      label: materialized view 名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
    column_name_shape:
      label: 列名形态
      importance: non_important
      values:
      - plain_identifier
      - quoted_identifier
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    extension_state:
      label: 扩展依赖状态
      importance: non_important
      values:
      - extension_exists
      - extension_missing
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
      - object_type_mismatch
    ownership_boundary:
      label: 所有权边界
      importance: non_important
      values:
      - owner
      - member_role
      - non_owner
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - effect_query
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_objects
      - reset_state
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - target_object_state
    - expected_status
    non_main_factors:
    - alter_action_type
    - if_exists_clause
    - new_owner_shape
    - privilege_context
    - name_shape
    - column_name_shape
    - dependency_state
    - extension_state
    - invalid_combination
    - ownership_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
  rendering:
    statement_template: ALTER MATERIALIZED VIEW {name}
    verification_query_template: ''
    factor_value_bindings: {}
```
