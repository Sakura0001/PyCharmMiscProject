# 技能：DROP TEXT SEARCH CONFIGURATION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droptsconfiguration.html

```sql
DROP TEXT SEARCH CONFIGURATION [ IF EXISTS ] name [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- DROP TEXT SEARCH CONFIGURATION 要求执行者是配置的 owner（superusers 自动拥有此权限）
- RESTRICT（默认）：如果有任何对象依赖该配置，拒绝删除
- CASCADE：自动删除依赖该配置的所有对象
- IF EXISTS：如果配置不存在，不报错而是发出通知
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：DROP TEXT SEARCH CONFIGURATION — remove a text search configuration

该 reference 关注全文搜索配置删除操作的权限边界、依赖对象驻留和 IF EXISTS 行为，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP TEXT SEARCH CONFIGURATION / DROP TEXT SEARCH CONFIGURATION IF EXISTS）
- object_state：目标 text search configuration 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- cascade_restrict：CASCADE / RESTRICT 子句（省略默认RESTRICT / CASCADE / RESTRICT）
- authorization_path：权限路径（owner / non_owner / superuser）
- dependency_status：依赖对象状态（无依赖 / 有依赖）

### T3：对象名与输入形态因子
- config_name_shape：text search configuration 标识符形态

### T4：依赖对象与环境因子
- privilege_context：权限上下文
- dependency_context：依赖对象驻留情况

### T5：异常与边界因子
- error_type：失败原因分类

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP TEXT SEARCH CONFIGURATION 全部语法分支。
- 覆盖目标 text search configuration 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 owner 权限边界和依赖对象驻留。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标配置存在时的成功删除路径，以及目标配置不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- DROP TEXT SEARCH CONFIGURATION 要求执行者是 owner；非 owner 执行路径属于失败路径。
- DROP TEXT SEARCH CONFIGURATION 不涉及 table / column 组合，不需要挂靠基表列类型。
- 每个样本必须包含明确的前置对象准备、目标 DROP TEXT SEARCH CONFIGURATION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与依赖对象驻留相关的因子必须挂靠到 CASCADE/RESTRICT 分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 子句、CASCADE/RESTRICT 依赖边界代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: text_search_configuration
  skill_name: drop_text_search_configuration
  official_source: https://www.postgresql.org/docs/16/sql-droptsconfiguration.html
  statement:
    key: drop_text_search_configuration
    name: DROP TEXT SEARCH CONFIGURATION
    aliases:
    - drop_text_search_configuration
    - DROP TEXT SEARCH CONFIGURATION
    purpose: DROP TEXT SEARCH CONFIGURATION — remove a text search configuration
  syntax_templates:
  - "DROP TEXT SEARCH CONFIGURATION [ IF EXISTS ] name [ CASCADE | RESTRICT ]"
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
    - cascade_restrict
    - authorization_path
    - dependency_status
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - config_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_context
    - dependency_context
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
      - key: branch_drop_ts_config
        label: DROP TEXT SEARCH CONFIGURATION name
      - key: branch_drop_ts_config_if_exists
        label: DROP TEXT SEARCH CONFIGURATION IF EXISTS name
    object_state:
      label: 目标 text search configuration 对象状态
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
      importance: non_important
      values:
      - present
      - absent
    cascade_restrict:
      label: CASCADE / RESTRICT 子句
      importance: non_important
      values:
      - default_restrict
      - explicit_restrict
      - explicit_cascade
    authorization_path:
      label: 权限路径
      importance: non_important
      values:
      - owner
      - non_owner
      - superuser
    dependency_status:
      label: 依赖对象状态
      importance: non_important
      values:
      - no_dependencies
      - has_dependencies
    config_name_shape:
      label: text search configuration 标识符形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - reserved_word_id
      - non_existent_name
    privilege_context:
      label: 权限上下文
      importance: non_important
      values:
      - owner_session
      - non_owner_session
      - superuser_session
    dependency_context:
      label: 依赖对象驻留情况
      importance: non_important
      values:
      - no_dependencies
      - config_used_by_other_object
    error_type:
      label: 失败原因分类
      importance: non_important
      values:
      - none
      - non_existent_without_if_exists
      - dependent_object_exists
      - insufficient_privilege
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
      - cascade_cleanup
      - manual_dependency_cleanup
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - authorization_path
    - dependency_status
    - config_name_shape
    - privilege_context
    - dependency_context
    - error_type
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP TEXT SEARCH CONFIGURATION [ IF EXISTS ] {config_name} [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT cfgname FROM pg_ts_config WHERE cfgname = '{config_name}'"
    factor_value_bindings: {}
```
