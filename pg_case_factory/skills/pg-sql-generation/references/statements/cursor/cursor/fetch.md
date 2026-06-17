# 技能：FETCH

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-fetch.html

```sql
FETCH [ direction ] [ FROM | IN ] cursor_name

where direction can be one of:

    NEXT
    PRIOR
    FIRST
    LAST
    ABSOLUTE count
    RELATIVE count
    count
    ALL
    FORWARD
    FORWARD count
    FORWARD ALL
    BACKWARD
    BACKWARD count
    BACKWARD ALL
```

## 语句作用

官方说明：FETCH — retrieve rows from a query using a cursor

该 reference 关注游标声明、定位、读取和关闭的状态机，不负责定义复杂业务查询。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- cursor_state：游标状态
- expected_status：预期结果

### T2：重要行为因子
- direction_shape：方向与数量
- hold_scroll_shape：保持性与滚动性

### T3：对象名与输入形态因子
- cursor_name_shape：游标名称形态
- query_shape：游标查询形态

### T4：依赖对象与环境因子
- transaction_context：事务上下文
- dependency_state：依赖对象状态

### T5：异常与边界因子
- invalid_combination：非法组合
- position_boundary：位置边界

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖游标存在/不存在、打开/关闭、WITH HOLD、SCROLL/NO SCROLL、方向和数量。
- FETCH/MOVE 方向枚举应按官方 synopsis 全覆盖或代表性轮转覆盖。
- 二进制游标、不可滚动查询和事务边界作为重要行为覆盖。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 除 WITH HOLD 特殊分支外，游标样本需要明确事务块边界。
- FETCH 成功样本必须验证返回行数或当前位置变化；MOVE 成功样本验证后续 FETCH 位置。
- 清理阶段必须 CLOSE 游标并结束事务。
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
  category: cursor
  domain: cursor
  skill_name: fetch
  official_source: https://www.postgresql.org/docs/16/sql-fetch.html
  statement:
    key: fetch
    name: FETCH
    aliases:
    - fetch
    - fetch
    - fetch
    - FETCH
    purpose: FETCH — retrieve rows from a query using a cursor
  syntax_templates:
  - "FETCH [ direction ] [ FROM | IN ] cursor_name\n\nwhere direction can be one of:\n\n    NEXT\n    PRIOR\n    FIRST\n \
    \   LAST\n    ABSOLUTE count\n    RELATIVE count\n    count\n    ALL\n    FORWARD\n    FORWARD count\n    FORWARD ALL\n\
    \    BACKWARD\n    BACKWARD count\n    BACKWARD ALL"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - cursor_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - direction_shape
    - hold_scroll_shape
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - cursor_name_shape
    - query_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - transaction_context
    - dependency_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - position_boundary
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
    cursor_state:
      label: 游标状态
      importance: important
      values:
      - declared_open
      - missing_cursor
      - closed_cursor
      - with_hold_after_commit
    direction_shape:
      label: 方向与数量
      importance: non_important
      values:
      - next
      - prior
      - absolute
      - relative
      - all
      - forward_backward_count
    hold_scroll_shape:
      label: 保持性与滚动性
      importance: non_important
      values:
      - default
      - with_hold
      - without_hold
      - scroll
      - no_scroll
    cursor_name_shape:
      label: 游标名称形态
      importance: non_important
      values:
      - plain_identifier
      - quoted_identifier
      - all_cursors
      - missing_name
    query_shape:
      label: 游标查询形态
      importance: non_important
      values:
      - simple_select
      - ordered_select
      - empty_result
      - non_scrollable_query
    transaction_context:
      label: 事务上下文
      importance: non_important
      values:
      - outside_transaction
      - inside_transaction
      - after_rollback
    dependency_state:
      label: 依赖对象状态
      importance: non_important
      values:
      - ready
      - missing_dependency
    invalid_combination:
      label: 非法组合
      importance: non_important
      values:
      - none
      - syntax_valid_semantic_error
      - object_type_mismatch
    position_boundary:
      label: 位置边界
      importance: non_important
      values:
      - before_first
      - middle
      - after_last
      - negative_or_zero_count
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
    - cursor_state
    - expected_status
    non_main_factors:
    - direction_shape
    - hold_scroll_shape
    - cursor_name_shape
    - query_shape
    - transaction_context
    - dependency_state
    - invalid_combination
    - position_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - cursor_state
  rendering:
    statement_template: FETCH [ direction ] [ FROM | IN ] cursor_name
    verification_query_template: ''
    factor_value_bindings: {}
```
