# 技能：DROP TABLESPACE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droptablespace.html

```sql
DROP TABLESPACE [ IF EXISTS ] name
```

PG16 关键约束：
- 只有 tablespace 的 **owner** 或 **superuser** 才能执行 DROP TABLESPACE
- tablespace 必须**为空**（当前数据库及所有其他数据库中均无对象驻留）才能被删除
- 如果任何活跃 session 的 `temp_tablespaces` 配置引用了该 tablespace，DROP 可能因临时文件驻留而失败
- DROP TABLESPACE **不能在事务块内执行**
- PG16 不支持 CASCADE/RESTRICT 子句

## 语句作用

官方说明：DROP TABLESPACE — remove a tablespace

该 reference 关注 tablespace 删除操作的权限边界、对象驻留约束和 IF EXISTS 行为，不负责包装所有样本到统一外层事务。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP TABLESPACE / DROP TABLESPACE IF EXISTS）
- object_state：目标 tablespace 对象状态（已存在 / 不存在）
- expected_status：预期结果（成功 / 失败）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关
- authorization_path：权限路径（superuser / owner / 非owner非superuser）
- object_occupancy：tablespace 是否驻留对象（空 / 有对象）

### T3：对象名与输入形态因子
- tablespace_name_shape：tablespace 标识符形态

### T4：依赖对象与环境因子
- privilege_context：权限上下文
- dependency_context：依赖对象驻留情况
- environment_context：环境上下文（事务块 / 活跃 temp_tablespaces）

### T5：异常与边界因子
- error_type：失败原因分类

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP TABLESPACE 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表和所有列类型，因为 DROP TABLESPACE 不涉及表/列/索引组合。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 tablespace 存在且为空时的成功删除路径，以及目标 tablespace 不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- DROP TABLESPACE 不支持 CASCADE/RESTRICT，不得伪造这些子句的分支。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 DROP TABLESPACE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 需要 superuser、非事务环境、跨数据库检查或 temp_tablespaces 依赖的分支必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限、依赖对象驻留、事务环境或 temp_tablespaces 配置的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（DROP TABLESPACE / DROP TABLESPACE IF EXISTS）
  - 目标 tablespace 存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖（superuser / owner / 非owner非superuser）
- 次优先保证：
  - IF EXISTS 子句代表性覆盖
  - tablespace 驻留对象 / 为空的边界覆盖
  - 事务块内执行 / 事务块外执行的边界覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: tablespace
  skill_name: drop_tablespace
  official_source: https://www.postgresql.org/docs/16/sql-droptablespace.html
  statement:
    key: drop_tablespace
    name: DROP TABLESPACE
    aliases:
    - drop_tablespace
    - DROP TABLESPACE
    purpose: DROP TABLESPACE — remove a tablespace
  syntax_templates:
  - "DROP TABLESPACE [ IF EXISTS ] name"
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
    - if_exists_clause
    - authorization_path
    - object_occupancy
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - tablespace_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_context
    - dependency_context
    - environment_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - error_type
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
      - key: branch_drop_tablespace
        label: DROP TABLESPACE name
      - key: branch_drop_tablespace_if_exists
        label: DROP TABLESPACE IF EXISTS name
    object_state:
      label: 目标 tablespace 对象状态
      importance: important
      values:
      - exists
      - absent
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: important
      values:
      - present
      - absent
    authorization_path:
      label: 权限路径
      importance: important
      values:
      - superuser
      - owner
      - non_owner_non_superuser
    object_occupancy:
      label: tablespace 是否驻留对象
      importance: important
      values:
      - empty
      - has_objects_in_current_db
      - has_objects_in_other_db
      - has_temp_files
    tablespace_name_shape:
      label: tablespace 标识符形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_id
      - non_existent_name
      - existing_name
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - superuser_session
      - owner_session
      - non_owner_session
    dependency_context:
      label: 依赖对象驻留情况
      importance: non_important
      values:
      - no_dependencies
      - objects_in_current_db
      - objects_in_other_db
      - temp_tablespace_active
    environment_context:
      label: 环境上下文
      importance: non_important
      values:
      - outside_transaction_block
      - inside_transaction_block
      - active_temp_tablespaces
    error_type:
      label: 失败原因分类
      importance: non_important
      values:
      - none
      - non_existent_without_if_exists
      - occupied_tablespace
      - insufficient_privilege
      - inside_transaction_block
      - temp_tablespace_in_use
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - error_assertion
      - notice_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - remove_objects_first
      - drop_tablespace
      - reset_temp_tablespaces
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - authorization_path
    - object_occupancy
    - tablespace_name_shape
    - privilege_context
    - dependency_context
    - environment_context
    - error_type
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP TABLESPACE [ IF EXISTS ] {tablespace_name}"
    verification_query_template: "SELECT spcname FROM pg_tablespace WHERE spcname = '{tablespace_name}'"
    factor_value_bindings: {}
```
