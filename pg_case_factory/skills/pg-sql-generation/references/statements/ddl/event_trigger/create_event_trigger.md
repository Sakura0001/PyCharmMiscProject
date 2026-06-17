# 技能：CREATE EVENT TRIGGER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createeventtrigger.html

```sql
CREATE EVENT TRIGGER name
    ON event
    [ WHEN filter_variable IN (filter_value [, ... ]) [ AND ... ] ]
    EXECUTE { FUNCTION | PROCEDURE } function_name()
```

PG16 关键约束：
- 只有 superuser 才能创建 event trigger
- event trigger 名称在数据库内必须唯一
- 支持的 event 类型：ddl_command_start、ddl_command_end、table_rewrite
- WHEN 过滤子句：filter_variable 目前仅支持 TAG；filter_value 为命令标签列表（如 'DROP FUNCTION'、'ALTER TABLE'）
- 多个 WHEN 条件可用 AND 连接
- EXECUTE FUNCTION/PROCEDURE 引用的函数必须：无参数、返回类型为 event_trigger
- FUNCTION 和 PROCEDURE 关键字等效，但 PROCEDURE 已过时（引用的对象必须是函数而非 procedure）
- event trigger 在单用户模式下被禁用（postgres --single）
- 如果错误的 event trigger 使数据库不可用，在单用户模式下重启以删除它
- 函数体内可使用 tg_tag、tg_event 等特殊变量

## 语句作用

官方说明：CREATE EVENT TRIGGER — define a new event trigger

该 reference 关注事件触发器的创建。CREATE EVENT TRIGGER 监控 DDL 事件（ddl_command_start / ddl_command_end / table_rewrite），通过 TAG 过滤条件选择性触发，执行返回 event_trigger 类型的无参函数。该语句需要 superuser 权限，不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE EVENT TRIGGER 单一顶层形式）
- event_type：触发事件类型（ddl_command_start / ddl_command_end / table_rewrite）
- object_state：目标 event trigger 对象状态（not_exists / exists）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- when_filter_clause：WHEN 过滤子句形态（省略 / 单个 TAG IN 条件 / 多个 TAG IN 条件 / AND 连接多条件）
- execute_keyword：EXECUTE 关键字选择（FUNCTION / PROCEDURE）
- trigger_function_state：触发函数状态（存在且签名合法 / 不存在 / 签名不合法）
- privilege_level：执行权限（superuser / non_superuser）

### T3：对象名与输入形态因子
- trigger_name_shape：event trigger 名称形态
- function_name_shape：触发函数名称形态
- filter_value_shape：TAG 过滤值形态

### T4：依赖对象与环境因子
- function_existence：触发函数存在性
- function_return_type：函数返回类型（event_trigger / 非 event_trigger）
- function_parameter_count：函数参数数量（0 个 / 非 0 个）
- single_user_mode：单用户模式状态

### T5：异常与边界因子
- duplicate_trigger_name：同数据库内重名冲突
- privilege_denied_non_superuser：非 superuser 创建 event trigger
- nonexistent_function：触发函数不存在
- function_wrong_return_type：函数返回类型不是 event_trigger
- function_wrong_parameter_count：函数有参数（应为无参数）
- invalid_event_type：不支持的 event 类型
- invalid_filter_variable：不支持的 filter_variable（非 TAG）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE EVENT TRIGGER 单一语法分支的所有关键子句组合。
- 覆盖三种 event 类型（ddl_command_start / ddl_command_end / table_rewrite），每种至少一个成功样本。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖（event_type x object_state x expected_status）。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE EVENT TRIGGER 需要 superuser 权限，非 superuser 属于失败路径。
- 触发函数必须是无参、返回 event_trigger 类型的函数。每个成功样本必须先创建合法的触发函数。
- event trigger 名称在数据库内必须唯一，重名属于失败路径。
- WHEN TAG IN 过滤条件仅支持 TAG 变量，其他变量名属于失败路径（或语法层面不支持）。
- event 类型必须是 ddl_command_start / ddl_command_end / table_rewrite 之一。
- PROCEDURE 关键字已过时但仍可用，样本中应至少覆盖一次 PROCEDURE 关键字。
- 成功路径必须包含可验证的对象存在性检查（pg_event_trigger 查询），并在生命周期末尾清理 trigger 和函数。
- 每个样本必须包含明确的前置函数准备、目标 CREATE EVENT TRIGGER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- event_type 在三种类型上轮转覆盖，确保每种至少一个成功样本。
- when_filter_clause 在代表性成功样本上轮转注入（省略/单个 TAG/多个 TAG/AND 连接）。
- execute_keyword（FUNCTION/PROCEDURE）在代表性样本上轮转注入。
- privilege_level 必须挂靠到明确权限上下文的样本上（superuser 成功 / non_superuser 失败）。
- trigger_function_state 挂靠到函数存在/不存在/签名不合法的样本上。
- TAG 过滤值在代表性样本上轮转注入（DROP FUNCTION / ALTER TABLE / CREATE TABLE 等代表性命令标签）。

## 规模控制规则

- 优先保证官方语法分支、三种 event 类型、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 WHEN 过滤子句形态、EXECUTE 关键字选择和触发函数状态代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: event_trigger
  skill_name: create_event_trigger
  official_source: https://www.postgresql.org/docs/16/sql-createeventtrigger.html
  statement:
    key: create_event_trigger
    name: CREATE EVENT TRIGGER
    aliases:
    - create_event_trigger
    - CREATE EVENT TRIGGER
    purpose: CREATE EVENT TRIGGER — define a new event trigger
  syntax_templates:
  - "CREATE EVENT TRIGGER name\n    ON event\n    [ WHEN filter_variable IN (filter_value\
    \ [, ... ]) [ AND ... ] ]\n    EXECUTE { FUNCTION | PROCEDURE } function_name()"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - event_type
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - when_filter_clause
    - execute_keyword
    - trigger_function_state
    - privilege_level
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - trigger_name_shape
    - function_name_shape
    - filter_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - function_existence
    - function_return_type
    - function_parameter_count
    - single_user_mode
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_trigger_name
    - privilege_denied_non_superuser
    - nonexistent_function
    - function_wrong_return_type
    - function_wrong_parameter_count
    - invalid_event_type
    - invalid_filter_variable
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
      - key: branch_create_event_trigger
        label: CREATE EVENT TRIGGER name ON event [ WHEN ... ] EXECUTE FUNCTION/PROCEDURE function_name()
    event_type:
      label: 触发事件类型
      importance: important
      values:
      - ddl_command_start
      - ddl_command_end
      - table_rewrite
    object_state:
      label: 目标 event trigger 对象状态
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
    when_filter_clause:
      label: WHEN 过滤子句形态
      importance: non_important
      values:
      - omitted
      - single_tag_in_condition
      - multiple_tag_in_values
      - and_connected_multiple_conditions
    execute_keyword:
      label: EXECUTE 关键字选择
      importance: non_important
      values:
      - FUNCTION
      - PROCEDURE
    trigger_function_state:
      label: 触发函数状态
      importance: non_important
      values:
      - function_exists_valid_signature
      - function_not_exists
      - function_exists_wrong_return_type
      - function_exists_with_parameters
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - non_superuser
    trigger_name_shape:
      label: event trigger 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - duplicate_name
      - reserved_word_as_name
    function_name_shape:
      label: 触发函数名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified
      - nonexistent_name
    filter_value_shape:
      label: TAG 过滤值形态
      importance: non_important
      values:
      - single_command_tag
      - multiple_command_tags
      - representative_tags_drop_function
      - representative_tags_alter_table
      - representative_tags_create_table
    function_existence:
      label: 触发函数存在性
      importance: non_important
      values:
      - function_exists
      - function_not_exists
    function_return_type:
      label: 函数返回类型
      importance: non_important
      values:
      - event_trigger_return_type
      - non_event_trigger_return_type
    function_parameter_count:
      label: 函数参数数量
      importance: non_important
      values:
      - zero_parameters
      - nonzero_parameters
    single_user_mode:
      label: 单用户模式状态
      importance: non_important
      values:
      - normal_mode
      - single_user_mode_disabled
    duplicate_trigger_name:
      label: 同数据库内重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    privilege_denied_non_superuser:
      label: 非 superuser 创建 event trigger
      importance: non_important
      values:
      - superuser_success
      - non_superuser_failure
    nonexistent_function:
      label: 触发函数不存在
      importance: non_important
      values:
      - function_exists
      - function_not_exists
    function_wrong_return_type:
      label: 函数返回类型不是 event_trigger
      importance: non_important
      values:
      - correct_return_type
      - wrong_return_type
    function_wrong_parameter_count:
      label: 函数有参数（应为无参数）
      importance: non_important
      values:
      - zero_parameters
      - nonzero_parameters
    invalid_event_type:
      label: 不支持的 event 类型
      importance: non_important
      values:
      - valid_event_type
      - invalid_event_type
    invalid_filter_variable:
      label: 不支持的 filter_variable（非 TAG）
      importance: non_important
      values:
      - tag_variable
      - unsupported_variable
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_event_trigger
      - error_assertion
      - trigger_firing_test
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_event_trigger
      - drop_function
      - cascade_cleanup
  defaults:
    expected_status: success
    event_type: ddl_command_start
    object_state: not_exists
    execute_keyword: FUNCTION
    privilege_level: superuser
    when_filter_clause: omitted
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - event_type
    - object_state
    - expected_status
    non_main_factors:
    - when_filter_clause
    - execute_keyword
    - trigger_function_state
    - privilege_level
    - trigger_name_shape
    - function_name_shape
    - filter_value_shape
    - function_existence
    - function_return_type
    - function_parameter_count
    - single_user_mode
    - duplicate_trigger_name
    - privilege_denied_non_superuser
    - nonexistent_function
    - function_wrong_return_type
    - function_wrong_parameter_count
    - invalid_event_type
    - invalid_filter_variable
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - event_type
  rendering:
    statement_template: "CREATE EVENT TRIGGER {trigger_name} ON {event_type} {when_clause}\
      \ EXECUTE {execute_keyword} {function_name}()"
    verification_query_template: "SELECT evtname, evtevent, evtfoid FROM pg_event_trigger\
      \ WHERE evtname = '{trigger_name}'"
    factor_value_bindings: {}
```
