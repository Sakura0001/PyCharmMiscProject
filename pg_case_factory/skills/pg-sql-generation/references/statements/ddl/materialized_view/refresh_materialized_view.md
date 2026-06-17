# 技能：REFRESH MATERIALIZED VIEW

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-refreshmaterializedview.html

```sql
REFRESH MATERIALIZED VIEW [ CONCURRENTLY ] name
    [ WITH [ NO ] DATA ]
```

## 语句作用

官方说明：REFRESH MATERIALIZED VIEW — replace the contents of a materialized view

该 reference 关注 materialized view 的刷新操作、CONCURRENTLY 选项和 DATA/NO DATA 状态控制，不负责定义基础表模板本身。REFRESH MATERIALIZED VIEW 涉及表和查询结果的分支，需要覆盖仓库基表的代表性表类型与核心列类型。注意：CONCURRENTLY 不与 WITH NO DATA 同时使用（互斥）；CONCURRENTLY 要求 materialized view 上至少有一个 UNIQUE 索引（仅使用列名，不含表达式或 WHERE 子句）；CONCURRENTLY 不能用于未填充的 materialized view；同一 materialized view 上只能同时运行一个 REFRESH 操作。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- target_object_state：目标 materialized view 对象状态
- expected_status：预期结果

### T2：重要行为因子
- concurrently_clause：CONCURRENTLY 子句
- data_clause：WITH [ NO ] DATA 子句
- unique_index_state：UNIQUE 索引状态（仅适用于 CONCURRENTLY）
- privilege_context：权限上下文

### T3：对象名与输入形态因子
- name_shape：materialized view 名形态

### T4：依赖对象与环境因子
- dependency_state：依赖对象状态
- concurrently_restriction：CONCURRENTLY 限制条件

### T5：异常与边界因子
- invalid_combination：非法组合
- constraint_boundary：约束与边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 REFRESH MATERIALIZED VIEW 语法分支。
- 需要覆盖仓库基表的代表性表类型与核心列类型。
- 不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖该命令的所有顶层语法形式、成功路径、失败路径和对象状态验证。
- CONCURRENTLY 与 WITH NO DATA 的互斥组合必须覆盖失败路径。
- CONCURRENTLY 要求 UNIQUE 索引和已填充状态的限制必须显式标注。
- 成功路径必须包含可验证的数据刷新效果检查。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 REFRESH MATERIALIZED VIEW 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 需要特殊权限或索引前置条件的分支必须在生命周期计划中显式标注环境依赖。

## 指靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与状态机相关的因子必须挂靠到满足前置状态的样本上。
- CONCURRENTLY 限制因子仅挂靠到使用 CONCURRENTLY 的分支。

## 规模控制规则

- 优先保证官方语法分支、目标对象状态、核心输入形态和成功/失败路径。
- 次优先保证关键可选子句（CONCURRENTLY、WITH DATA/NO DATA）、权限上下文和环境上下文代表性覆盖。
- 低优先级命名、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: materialized_view
  skill_name: refresh_materialized_view
  official_source: https://www.postgresql.org/docs/16/sql-refreshmaterializedview.html
  statement:
    key: refresh_materialized_view
    name: REFRESH MATERIALIZED VIEW
    aliases:
    - refresh materialized view
    - REFRESH MATERIALIZED VIEW
    purpose: replace the contents of a materialized view
  syntax_templates:
  - "REFRESH MATERIALIZED VIEW [ CONCURRENTLY ] name\n    [ WITH [ NO ] DATA ]"
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
    - concurrently_clause
    - data_clause
    - unique_index_state
    - privilege_context
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - dependency_state
    - concurrently_restriction
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - constraint_boundary
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
        label: REFRESH MATERIALIZED VIEW 唯一语法分支
    target_object_state:
      label: 目标 materialized view 对象状态
      importance: important
      values:
      - exists_populated
      - exists_unpopulated
      - missing
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    concurrently_clause:
      label: CONCURRENTLY 子句
      importance: important
      values:
      - absent
      - present
    data_clause:
      label: WITH [ NO ] DATA 子句
      importance: non_important
      values:
      - with_data
      - with_no_data
    unique_index_state:
      label: UNIQUE 索引状态
      importance: non_important
      values:
      - has_unique_index
      - no_unique_index
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
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    concurrently_restriction:
      label: CONCURRENTLY 限制条件
      importance: non_important
      values:
      - all_conditions_met
      - no_unique_index
      - unpopulated_view
      - with_no_data_conflict
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - concurrently_with_no_data
      - concurrently_without_unique_index
    constraint_boundary:
      label: 约束与边界
      importance: non_important
      values:
      - none
      - concurrent_refresh_lock
      - security_restricted_query
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
    - concurrently_clause
    - data_clause
    - unique_index_state
    - privilege_context
    - name_shape
    - dependency_state
    - concurrently_restriction
    - invalid_combination
    - constraint_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - target_object_state
  rendering:
    statement_template: REFRESH MATERIALIZED VIEW {name}
    verification_query_template: ''
    factor_value_bindings: {}
```
