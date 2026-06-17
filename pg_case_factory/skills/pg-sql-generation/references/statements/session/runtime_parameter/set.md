# 技能：SET

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-set.html

```sql
SET [ SESSION | LOCAL ] configuration_parameter { TO | = } { value | 'value' | DEFAULT }
SET [ SESSION | LOCAL ] TIME ZONE { value | 'value' | LOCAL | DEFAULT }
```

## 语句作用

官方说明：SET — change a run-time parameter

该 reference 关注会话状态、运行时参数、通知通道和授权上下文的变化，不负责跨进程通知框架实现。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- session_state：会话状态
- expected_status：预期结果

### T2：重要行为因子
- scope_shape：作用域形态
- value_shape：取值形态

### T3：对象名与输入形态因子
- name_shape：名称形态
- payload_shape：payload 形态

### T4：依赖对象与环境因子
- dependency_state：依赖状态
- privilege_context：权限上下文

### T5：异常与边界因子
- invalid_combination：非法组合
- transaction_visibility：事务可见性

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖默认值、显式值、RESET/ALL、SESSION/LOCAL、角色切换和通知通道状态。
- 事务提交前后可见性、权限限制和非法名称按代表性覆盖。
- SET/RESET/SHOW 类语句应覆盖参数存在性、取值合法性和作用域。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 样本必须在结束阶段恢复会话参数、角色、监听状态或约束模式。
- LISTEN/NOTIFY 的完整投递验证可能需要第二连接；单连接样本只能验证语句成功与通道状态。
- SET ROLE 和 SET SESSION AUTHORIZATION 必须显式准备角色和权限边界。
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
  category: session
  domain: runtime_parameter
  skill_name: set
  official_source: https://www.postgresql.org/docs/16/sql-set.html
  statement:
    key: set
    name: SET
    aliases:
    - set
    - set
    - set
    - SET
    purpose: SET — change a run-time parameter
  syntax_templates:
  - 'SET [ SESSION | LOCAL ] configuration_parameter { TO | = } { value | ''value'' | DEFAULT }

    SET [ SESSION | LOCAL ] TIME ZONE { value | ''value'' | LOCAL | DEFAULT }'
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - session_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - scope_shape
    - value_shape
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
    - payload_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - privilege_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - transaction_visibility
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
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    session_state:
      label: 会话状态
      importance: important
      values:
      - default_state
      - modified_state
      - missing_channel_or_role
      - restored_state
    scope_shape:
      label: 作用域形态
      importance: non_important
      values:
      - session
      - local
      - all
      - default_or_reset
    value_shape:
      label: 取值形态
      importance: non_important
      values:
      - valid_value
      - default_value
      - invalid_value
      - list_or_identifier_value
    name_shape:
      label: 名称形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
      - alias_used
    payload_shape:
      label: payload 形态
      importance: non_important
      values:
      - absent
      - short_text
      - boundary_length
      - invalid_payload
    dependency_state:
      label: 依赖状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    privilege_context:
      label: 权限上下文
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
    transaction_visibility:
      label: 事务可见性
      importance: non_important
      values:
      - outside_transaction
      - inside_committed_transaction
      - inside_rolled_back_transaction
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
    - session_state
    - expected_status
    non_main_factors:
    - scope_shape
    - value_shape
    - name_shape
    - payload_shape
    - dependency_state
    - privilege_context
    - invalid_combination
    - transaction_visibility
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - session_state
  rendering:
    statement_template: SET [ SESSION | LOCAL ] configuration_parameter { TO | = } { value | 'value' | DEFAULT }
    verification_query_template: ''
    factor_value_bindings: {}
```
