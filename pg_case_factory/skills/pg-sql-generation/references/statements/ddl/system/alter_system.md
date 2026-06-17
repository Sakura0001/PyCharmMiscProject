# 技能：ALTER SYSTEM

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altersystem.html

```sql
ALTER SYSTEM SET configuration_parameter { TO | = } { value [, ...] | DEFAULT }

ALTER SYSTEM RESET configuration_parameter
ALTER SYSTEM RESET ALL
```

**重要约束：**
- ALTER SYSTEM 需要 superuser 权限。
- ALTER SYSTEM SET 将配置参数写入 `postgresql.auto.conf` 文件，不影响当前会话参数（需要 reload 或 restart 才生效）。
- ALTER SYSTEM SET ... DEFAULT 从 `postgresql.auto.conf` 中移除该参数条目，恢复到 `postgresql.conf` 的默认值。
- ALTER SYSTEM RESET 从 `postgresql.auto.conf` 中移除特定参数条目。
- ALTER SYSTEM RESET ALL 从 `postgresql.auto.conf` 中移除所有条目。
- 某些参数需要 restart 才能生效（如 shared_buffers），某些只需要 reload（如 work_mem）。
- ALTER SYSTEM 不涉及表/列/索引对象。

## 语句作用

官方说明：ALTER SYSTEM — change a server configuration parameter

该 reference 关注系统配置参数修改语句的 3 个语法分支（SET / RESET / RESET ALL）、参数类型（superuser-only / user-settable）、DEFAULT 行为、权限边界和成功/失败路径。ALTER SYSTEM 需要 superuser 权限且修改 `postgresql.auto.conf`。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（SET / RESET / RESET ALL）
- expected_status：预期结果

### T2：重要行为因子
- configuration_parameter_type：配置参数类型（superuser-only / user-settable / PGC_POSTMASTER / PGC_SIGHUP / PGC_BACKEND / PGC_SUSET / PGC_USERSET）
- set_value_behavior：SET 值行为（单值 / 多值 / DEFAULT）
- reset_behavior：RESET 行为（特定参数 / ALL）
- parameter_effect_scope：参数生效范围（需要 restart / 需要 reload / 立即生效）

### T3：对象名与输入形态因子
- parameter_name_shape：配置参数名形态
- value_shape：参数值形态

### T4：依赖对象与环境因子
- **ALTER SYSTEM 不涉及表/列/索引对象。它修改 postgresql.auto.conf 文件。**
- executor_privilege：执行者权限上下文（superuser 必须）
- parameter_validity：参数有效性

### T5：异常与边界因子
- privilege_insufficient：权限不足（非 superuser）
- nonexistent_parameter：配置参数不存在
- invalid_parameter_value：非法参数值
- superuser_only_parameter_by_non_superuser：非 superuser 设置 superuser-only 参数
- restart_required_parameter：需要 restart 的参数
- reset_nonexistent_parameter_entry：RESET 不存在于 auto.conf 的参数

### T6：验证与清理因子
- verification_mode：验证方式（pg_settings / pg_file_settings 查询）
- cleanup_mode：清理方式（ALTER SYSTEM RESET / RESET ALL）

## 覆盖策略

- 覆盖 3 个语法分支（SET / RESET / RESET ALL）。
- 覆盖 SET 值的代表性形态（单值 / 多值 / DEFAULT）。
- 覆盖参数类型的代表性取值（superuser-only / user-settable）。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 SET 成功路径、RESET 成功路径、RESET ALL 成功路径。
- 必须覆盖权限不足（非 superuser）的失败路径。
- SET DEFAULT 路径必须覆盖从 auto.conf 中移除参数条目的行为。
- RESET 不存在于 auto.conf 的参数时，应为 no-op（不报错）。
- 需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。
- 需要重启生效的参数（PGC_POSTMASTER 类型），必须在生命周期计划中显式标注环境限制。
- 每个样本必须包含目标 ALTER SYSTEM 语句、验证语句（pg_settings / pg_file_settings）与清理语句（ALTER SYSTEM RESET）。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或参数有效性的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、参数类型、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有 3 个语法分支全覆盖
  - SET 单值 / 多值 / DEFAULT 全覆盖
  - 成功/失败路径全覆盖
  - superuser 权限路径全覆盖
- 次优先保证：
  - superuser-only / user-settable 参数类型代表性覆盖
  - restart / reload 参数生效范围代表性覆盖
  - RESET ALL 行为代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: system
  skill_name: alter_system
  official_source: https://www.postgresql.org/docs/16/sql-altersystem.html
  statement:
    key: alter_system
    name: ALTER SYSTEM
    aliases:
    - alter_system
    - ALTER SYSTEM
    purpose: ALTER SYSTEM — change a server configuration parameter
  syntax_templates:
  - "ALTER SYSTEM SET configuration_parameter { TO | = } { value [, ...] | DEFAULT }"
  - "ALTER SYSTEM RESET configuration_parameter"
  - "ALTER SYSTEM RESET ALL"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - configuration_parameter_type
    - set_value_behavior
    - reset_behavior
    - parameter_effect_scope
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - parameter_name_shape
    - value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - parameter_validity
  - tier: T5
    name: 异常与边界因子
    factors:
    - privilege_insufficient
    - nonexistent_parameter
    - invalid_parameter_value
    - superuser_only_parameter_by_non_superuser
    - restart_required_parameter
    - reset_nonexistent_parameter_entry
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
      - key: branch_set
        label: ALTER SYSTEM SET configuration_parameter = value
      - key: branch_set_default
        label: ALTER SYSTEM SET configuration_parameter = DEFAULT
      - key: branch_reset
        label: ALTER SYSTEM RESET configuration_parameter
      - key: branch_reset_all
        label: ALTER SYSTEM RESET ALL
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    configuration_parameter_type:
      label: 配置参数类型
      importance: important
      values:
      - superuser_only_parameter
      - user_settable_parameter
      - postmaster_restart_required
      - sighup_reload_required
      - backend_session_parameter
    set_value_behavior:
      label: SET 值行为
      importance: non_important
      values:
      - single_value
      - multiple_values
      - set_to_default
    reset_behavior:
      label: RESET 行为
      importance: non_important
      values:
      - reset_specific_parameter
      - reset_all_parameters
    parameter_effect_scope:
      label: 参数生效范围
      importance: non_important
      values:
      - requires_restart
      - requires_reload
      - immediate_effect
    parameter_name_shape:
      label: 配置参数名形态
      importance: non_important
      values:
      - valid_parameter_name
      - custom_parameter_name_with_dot
      - nonexistent_parameter_name
      - quoted_parameter_name
    value_shape:
      label: 参数值形态
      importance: non_important
      values:
      - valid_string_value
      - valid_integer_value
      - valid_boolean_value
      - multiple_comma_separated_values
      - default_keyword
      - invalid_value_type
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - non_superuser
    parameter_validity:
      label: 参数有效性
      importance: non_important
      values:
      - valid_parameter_and_value
      - valid_parameter_invalid_value
      - nonexistent_parameter
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_superuser_using_alter_system
    nonexistent_parameter:
      label: 配置参数不存在
      importance: non_important
      values:
      - parameter_does_not_exist
    invalid_parameter_value:
      label: 非法参数值
      importance: non_important
      values:
      - wrong_type_value
      - out_of_range_value
    superuser_only_parameter_by_non_superuser:
      label: 非 superuser 设置 superuser-only 参数
      importance: non_important
      values:
      - cannot_set_superuser_only_parameter
    restart_required_parameter:
      label: 需要重启的参数
      importance: non_important
      values:
      - parameter_change_requires_restart
      - parameter_change_requires_reload
    reset_nonexistent_parameter_entry:
      label: RESET 不存在于 auto.conf 的参数
      importance: non_important
      values:
      - reset_parameter_not_in_auto_conf_no_op
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_settings_query
      - pg_file_settings_query
      - show_command
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - alter_system_reset_parameter
      - alter_system_reset_all
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - expected_status
    non_main_factors:
    - configuration_parameter_type
    - set_value_behavior
    - reset_behavior
    - parameter_effect_scope
    - parameter_name_shape
    - value_shape
    - executor_privilege
    - parameter_validity
    - privilege_insufficient
    - nonexistent_parameter
    - invalid_parameter_value
    - superuser_only_parameter_by_non_superuser
    - restart_required_parameter
    - reset_nonexistent_parameter_entry
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
  rendering:
    statement_template: "ALTER SYSTEM {operation} {configuration_parameter} {value_or_default}"
    verification_query_template: "SELECT name, setting, source FROM pg_settings WHERE name = '{configuration_parameter}'"
    factor_value_bindings:
      set_value_behavior:
        single_value: "= '{value}'"
        multiple_values: "= '{value1}, {value2}'"
        set_to_default: "= DEFAULT"
```
