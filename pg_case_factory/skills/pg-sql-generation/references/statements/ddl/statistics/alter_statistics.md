# 技能：ALTER STATISTICS

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterstatistics.html

```sql
ALTER STATISTICS name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER STATISTICS name RENAME TO new_name
ALTER STATISTICS name SET SCHEMA new_schema
ALTER STATISTICS name SET STATISTICS new_target
```

**重要约束：**
- ALTER STATISTICS 有 4 个语法分支：OWNER TO / RENAME TO / SET SCHEMA / SET STATISTICS。
- SET STATISTICS 的 new_target 范围为 0 到 10000，-1 表示恢复到默认值。
- OWNER TO 需要超级用户或 CREATEROLE 加管理员权限。
- RENAME TO 和 SET SCHEMA 需要 table owner 权限。
- SET STATISTICS 需要 table owner 权限。

## 语句作用

官方说明：ALTER STATISTICS — change the definition of an extended statistics object

该 reference 关注扩展统计修改语句的 4 个语法分支、OWNER TO 子句形态、SET STATISTICS 目标值范围、SET SCHEMA 行为、权限边界和成功/失败路径。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（4 个 synopsis 分支）
- statistics_state：目标 statistics 存在状态
- expected_status：预期结果

### T2：重要行为因子
- owner_to_shape：OWNER TO 子句形态
- rename_behavior：RENAME 行为
- set_schema_behavior：SET SCHEMA 行为
- statistics_target_value：SET STATISTICS 目标值形态

### T3：对象名与输入形态因子
- statistics_name_shape：statistics 名形态
- new_name_shape：新名形态（RENAME 分支）
- new_schema_shape：新 schema 形态（SET SCHEMA 分支）
- new_owner_shape：新 owner 形态（OWNER TO 分支）
- target_value_shape：目标值形态（SET STATISTICS 分支）

### T4：依赖对象与环境因子
- **ALTER STATISTICS 不涉及表/列/索引组合的直接选择，但与依赖表对象相关。**
- executor_privilege：执行者权限上下文
- table_dependency：依赖表对象状态

### T5：异常与边界因子
- nonexistent_statistics：statistics 不存在
- privilege_insufficient：权限不足
- nonexistent_schema：schema 不存在（SET SCHEMA）
- nonexistent_owner：owner 不存在（OWNER TO）
- target_out_of_range：目标值超出范围（SET STATISTICS）
- rename_conflict：新名冲突

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖所有 4 个 ALTER STATISTICS 语法分支。
- 覆盖 SET STATISTICS 目标值的代表性取值（0 / 正整数 / -1 / 超范围）。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 statistics（需要先创建依赖表），并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 statistics 存在时的成功修改路径、statistics 不存在时的失败路径。
- OWNER TO / RENAME / SET SCHEMA / SET STATISTICS 各分支需要保持独立归因。
- 每个样本必须包含明确的前置表准备、目标 ALTER STATISTICS 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有 4 个语法分支全覆盖
  - statistics 存在/不存在全覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - SET STATISTICS 目标值代表性覆盖（0 / 正值 / -1 / 超范围）
  - CURRENT_ROLE / CURRENT_USER / SESSION_USER 代表性覆盖
  - SET SCHEMA 行为代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: statistics
  skill_name: alter_statistics
  official_source: https://www.postgresql.org/docs/16/sql-alterstatistics.html
  statement:
    key: alter_statistics
    name: ALTER STATISTICS
    aliases:
    - alter_statistics
    - ALTER STATISTICS
    purpose: ALTER STATISTICS — change the definition of an extended statistics object
  syntax_templates:
  - "ALTER STATISTICS name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER STATISTICS name RENAME TO new_name"
  - "ALTER STATISTICS name SET SCHEMA new_schema"
  - "ALTER STATISTICS name SET STATISTICS new_target"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - statistics_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - owner_to_shape
    - rename_behavior
    - set_schema_behavior
    - statistics_target_value
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - statistics_name_shape
    - new_name_shape
    - new_schema_shape
    - new_owner_shape
    - target_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - table_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_statistics
    - privilege_insufficient
    - nonexistent_schema
    - nonexistent_owner
    - target_out_of_range
    - rename_conflict
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
      - key: branch_owner_to
        label: ALTER STATISTICS name OWNER TO new_owner
      - key: branch_rename
        label: ALTER STATISTICS name RENAME TO new_name
      - key: branch_set_schema
        label: ALTER STATISTICS name SET SCHEMA new_schema
      - key: branch_set_statistics
        label: ALTER STATISTICS name SET STATISTICS new_target
    statistics_state:
      label: 目标 statistics 存在状态
      importance: important
      values:
      - exists
      - non_existent
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    owner_to_shape:
      label: OWNER TO 子句形态
      importance: non_important
      values:
      - explicit_role_name
      - current_role_keyword
      - current_user_keyword
      - session_user_keyword
    rename_behavior:
      label: RENAME 行为
      importance: non_important
      values:
      - rename_to_new_name
      - rename_to_existing_name_conflict
    set_schema_behavior:
      label: SET SCHEMA 行为
      importance: non_important
      values:
      - existing_schema
      - nonexistent_schema
    statistics_target_value:
      label: SET STATISTICS 目标值
      importance: non_important
      values:
      - zero
      - positive_integer
      - maximum_value_10000
      - negative_one_default
      - out_of_range
    statistics_name_shape:
      label: statistics 名形态
      importance: non_important
      values:
      - simple_name
      - schema_qualified_name
      - quoted_name
      - non_existent_name
    new_name_shape:
      label: 新名形态（RENAME 分支）
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - existing_name_conflict
    new_schema_shape:
      label: 新 schema 形态（SET SCHEMA 分支）
      importance: non_important
      values:
      - existing_schema
      - nonexistent_schema
    new_owner_shape:
      label: 新 owner 形态（OWNER TO 分支）
      importance: non_important
      values:
      - existing_role
      - nonexistent_role
    target_value_shape:
      label: 目标值形态（SET STATISTICS 分支）
      importance: non_important
      values:
      - integer_value
      - negative_one
      - very_large_value
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - table_owner
      - non_owner_no_privilege
    table_dependency:
      label: 依赖表对象状态
      importance: non_important
      values:
      - underlying_table_exists
    nonexistent_statistics:
      label: statistics 不存在
      importance: non_important
      values:
      - statistics_does_not_exist
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_table_owner_altering_statistics
    nonexistent_schema:
      label: schema 不存在
      importance: non_important
      values:
      - schema_does_not_exist
    nonexistent_owner:
      label: owner 不存在
      importance: non_important
      values:
      - owner_role_does_not_exist
    target_out_of_range:
      label: 目标值超范围
      importance: non_important
      values:
      - negative_other_than_minus_one
    rename_conflict:
      label: 新名冲突
      importance: non_important
      values:
      - new_name_already_exists
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_statistic_ext_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_statistics
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - statistics_state
    - expected_status
    non_main_factors:
    - owner_to_shape
    - rename_behavior
    - set_schema_behavior
    - statistics_target_value
    - statistics_name_shape
    - new_name_shape
    - new_schema_shape
    - new_owner_shape
    - target_value_shape
    - executor_privilege
    - table_dependency
    - nonexistent_statistics
    - privilege_insufficient
    - nonexistent_schema
    - nonexistent_owner
    - target_out_of_range
    - rename_conflict
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - statistics_state
  rendering:
    statement_template: "ALTER STATISTICS {name} {operation}"
    verification_query_template: "SELECT stxname FROM pg_statistic_ext WHERE stxname = '{name}'"
    factor_value_bindings: {}
```
