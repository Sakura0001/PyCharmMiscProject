# 技能：REVOKE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-revoke.html

```sql
REVOKE [ GRANT OPTION FOR ]
    { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }
    [, ...] | ALL [ PRIVILEGES ] }
    ON { [ TABLE ] table_name [, ...]
         | ALL TABLES IN SCHEMA schema_name [, ...] }
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { { SELECT | INSERT | UPDATE | REFERENCES } ( column_name [, ...] )
    [, ...] | ALL [ PRIVILEGES ] ( column_name [, ...] ) }
    ON [ TABLE ] table_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { { USAGE | SELECT | UPDATE }
    [, ...] | ALL [ PRIVILEGES ] }
    ON { SEQUENCE sequence_name [, ...]
         | ALL SEQUENCES IN SCHEMA schema_name [, ...] }
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { { CREATE | CONNECT | TEMPORARY | TEMP } [, ...] | ALL [ PRIVILEGES ] }
    ON DATABASE database_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { USAGE | ALL [ PRIVILEGES ] }
    ON DOMAIN domain_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { USAGE | ALL [ PRIVILEGES ] }
    ON FOREIGN DATA WRAPPER fdw_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { USAGE | ALL [ PRIVILEGES ] }
    ON FOREIGN SERVER server_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { EXECUTE | ALL [ PRIVILEGES ] }
    ON { { FUNCTION | PROCEDURE | ROUTINE } function_name [ ( [ [ argmode ] [ arg_name ] arg_type [, ...] ] ) ] [, ...]
         | ALL { FUNCTIONS | PROCEDURES | ROUTINES } IN SCHEMA schema_name [, ...] }
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { USAGE | ALL [ PRIVILEGES ] }
    ON LANGUAGE lang_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { { SELECT | UPDATE } [, ...] | ALL [ PRIVILEGES ] }
    ON LARGE OBJECT loid [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { { SET | ALTER SYSTEM } [, ...] | ALL [ PRIVILEGES ] }
    ON PARAMETER configuration_parameter [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { { CREATE | USAGE } [, ...] | ALL [ PRIVILEGES ] }
    ON SCHEMA schema_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { CREATE | ALL [ PRIVILEGES ] }
    ON TABLESPACE tablespace_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ GRANT OPTION FOR ]
    { USAGE | ALL [ PRIVILEGES ] }
    ON TYPE type_name [, ...]
    FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

REVOKE [ { ADMIN | INHERIT | SET } OPTION FOR ]
    role_name [, ...] FROM role_specification [, ...]
    [ GRANTED BY role_specification ]
    [ CASCADE | RESTRICT ]

where role_specification can be:

    [ GROUP ] role_name
  | PUBLIC
  | CURRENT_ROLE
  | CURRENT_USER
  | SESSION_USER
```

## 语句作用

官方说明：REVOKE — remove access privileges

该 reference 关注权限控制语句的对象范围、权限项、授权对象和授权链路，不负责长期保留测试角色或权限状态。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- privilege_scope：权限范围
- grantee_shape：被授权对象
- expected_status：预期结果

### T2：重要行为因子
- grant_option_shape：授权选项
- grantor_shape：授权者形态

### T3：对象名与输入形态因子
- object_name_shape：对象名形态
- role_name_shape：角色名形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- privilege_context：授权者权限上下文

### T5：异常与边界因子
- invalid_combination：非法组合
- ownership_boundary：所有权边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖对象权限、列级权限、schema/all-in-schema 分支、角色成员关系和参数权限。
- 授权选项、GRANTED BY、PUBLIC、CURRENT_ROLE/CURRENT_USER 等角色形态按代表性覆盖。
- 成功与失败路径都必须覆盖，包括授权者权限不足、对象不存在、权限项与对象类型不匹配。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 每个样本必须创建临时角色和最小对象依赖，并在清理阶段撤销权限、删除角色和对象。
- 验证优先使用 has_*_privilege、information_schema 或 pg_catalog 查询。
- 不得依赖集群中预先存在的业务角色。
- 需要特殊权限、外部服务、文件系统、两阶段事务、第二连接或非事务环境的分支必须显式标注，不得伪造为普通成功路径。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标/依赖状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: dcl
  domain: privilege
  skill_name: revoke
  official_source: https://www.postgresql.org/docs/16/sql-revoke.html
  statement:
    key: revoke
    name: REVOKE
    aliases:
    - revoke
    - revoke
    - revoke
    - REVOKE
    purpose: REVOKE — remove access privileges
  syntax_templates:
  - "REVOKE [ GRANT OPTION FOR ]\n    { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }\n    [, ...]\
    \ | ALL [ PRIVILEGES ] }\n    ON { [ TABLE ] table_name [, ...]\n         | ALL TABLES IN SCHEMA schema_name [, ...] }\n\
    \    FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT\
    \ OPTION FOR ]\n    { { SELECT | INSERT | UPDATE | REFERENCES } ( column_name [, ...] )\n    [, ...] | ALL [ PRIVILEGES\
    \ ] ( column_name [, ...] ) }\n    ON [ TABLE ] table_name [, ...]\n    FROM role_specification [, ...]\n    [ GRANTED\
    \ BY role_specification ]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { USAGE | SELECT | UPDATE\
    \ }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON { SEQUENCE sequence_name [, ...]\n         | ALL SEQUENCES IN SCHEMA schema_name\
    \ [, ...] }\n    FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE | RESTRICT ]\n\n\
    REVOKE [ GRANT OPTION FOR ]\n    { { CREATE | CONNECT | TEMPORARY | TEMP } [, ...] | ALL [ PRIVILEGES ] }\n    ON DATABASE\
    \ database_name [, ...]\n    FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE | RESTRICT\
    \ ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ] }\n    ON DOMAIN domain_name [, ...]\n    FROM role_specification\
    \ [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE\
    \ | ALL [ PRIVILEGES ] }\n    ON FOREIGN DATA WRAPPER fdw_name [, ...]\n    FROM role_specification [, ...]\n    [ GRANTED\
    \ BY role_specification ]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ]\
    \ }\n    ON FOREIGN SERVER server_name [, ...]\n    FROM role_specification [, ...]\n    [ GRANTED BY role_specification\
    \ ]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { EXECUTE | ALL [ PRIVILEGES ] }\n    ON { { FUNCTION\
    \ | PROCEDURE | ROUTINE } function_name [ ( [ [ argmode ] [ arg_name ] arg_type [, ...] ] ) ] [, ...]\n         | ALL\
    \ { FUNCTIONS | PROCEDURES | ROUTINES } IN SCHEMA schema_name [, ...] }\n    FROM role_specification [, ...]\n    [ GRANTED\
    \ BY role_specification ]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ]\
    \ }\n    ON LANGUAGE lang_name [, ...]\n    FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n \
    \   [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { SELECT | UPDATE } [, ...] | ALL [ PRIVILEGES ] }\n\
    \    ON LARGE OBJECT loid [, ...]\n    FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE\
    \ | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { SET | ALTER SYSTEM } [, ...] | ALL [ PRIVILEGES ] }\n    ON PARAMETER\
    \ configuration_parameter [, ...]\n    FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE\
    \ | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { CREATE | USAGE } [, ...] | ALL [ PRIVILEGES ] }\n    ON SCHEMA\
    \ schema_name [, ...]\n    FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE | RESTRICT\
    \ ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { CREATE | ALL [ PRIVILEGES ] }\n    ON TABLESPACE tablespace_name [, ...]\n \
    \   FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT\
    \ OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ] }\n    ON TYPE type_name [, ...]\n    FROM role_specification [, ...]\n\
    \    [ GRANTED BY role_specification ]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ { ADMIN | INHERIT | SET } OPTION FOR ]\n\
    \    role_name [, ...] FROM role_specification [, ...]\n    [ GRANTED BY role_specification ]\n    [ CASCADE | RESTRICT\
    \ ]\n\nwhere role_specification can be:\n\n    [ GROUP ] role_name\n  | PUBLIC\n  | CURRENT_ROLE\n  | CURRENT_USER\n \
    \ | SESSION_USER"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - privilege_scope
    - grantee_shape
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - grant_option_shape
    - grantor_shape
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - object_name_shape
    - role_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - privilege_context
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
      - key: branch_1
        label: 官方 synopsis 分支 1
      - key: branch_2
        label: 官方 synopsis 分支 2
      - key: branch_3
        label: 官方 synopsis 分支 3
      - key: branch_4
        label: 官方 synopsis 分支 4
      - key: branch_5
        label: 官方 synopsis 分支 5
      - key: branch_6
        label: 官方 synopsis 分支 6
      - key: branch_7
        label: 官方 synopsis 分支 7
      - key: branch_8
        label: 官方 synopsis 分支 8
      - key: branch_9
        label: 官方 synopsis 分支 9
      - key: branch_10
        label: 官方 synopsis 分支 10
      - key: branch_11
        label: 官方 synopsis 分支 11
      - key: branch_12
        label: 官方 synopsis 分支 12
      - key: branch_13
        label: 官方 synopsis 分支 13
      - key: branch_14
        label: 官方 synopsis 分支 14
      - key: branch_15
        label: 官方 synopsis 分支 15
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    privilege_scope:
      label: 权限范围
      importance: important
      values:
      - table_privilege
      - column_privilege
      - schema_database_tablespace
      - routine_language_type_fdw_server
      - role_membership
      - parameter_privilege
    grantee_shape:
      label: 被授权对象
      importance: important
      values:
      - role_name
      - public
      - current_role
      - current_user
      - session_user
    grant_option_shape:
      label: 授权选项
      importance: non_important
      values:
      - absent
      - grant_option
      - admin_option
      - inherit_or_set_option
    grantor_shape:
      label: 授权者形态
      importance: non_important
      values:
      - implicit_owner
      - granted_by_owner
      - granted_by_non_owner
    object_name_shape:
      label: 对象名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - all_objects_in_schema
      - missing_object
    role_name_shape:
      label: 角色名形态
      importance: non_important
      values:
      - plain_role
      - quoted_role
      - missing_role
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    privilege_context:
      label: 授权者权限上下文
      importance: non_important
      values:
      - owner
      - granted_role
      - insufficient_privilege
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
      - returned_rows
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - rollback
      - drop_objects
      - reset_state
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - privilege_scope
    - grantee_shape
    - expected_status
    non_main_factors:
    - grant_option_shape
    - grantor_shape
    - object_name_shape
    - role_name_shape
    - dependency_state
    - privilege_context
    - invalid_combination
    - ownership_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - privilege_scope
    - grantee_shape
  rendering:
    statement_template: REVOKE [ GRANT OPTION FOR ]
    verification_query_template: ''
    factor_value_bindings: {}
```
