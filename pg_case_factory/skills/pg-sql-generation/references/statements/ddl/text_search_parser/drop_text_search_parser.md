# 技能：DROP TEXT SEARCH PARSER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droptsparser.html

```sql
DROP TEXT SEARCH PARSER [ IF EXISTS ] name [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- DROP TEXT SEARCH PARSER 要求 SUPERUSER 权限
- RESTRICT（默认）：如果有 text search configuration 使用该 parser，拒绝删除
- CASCADE：自动删除依赖该 parser 的所有 text search configuration
- IF EXISTS：如果 parser 不存在，不报错而是发出通知
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：DROP TEXT SEARCH PARSER — remove a text search parser

该 reference 关注全文搜索解析器删除操作的 superuser 权限边界、依赖对象驻留和 IF EXISTS 行为，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP TEXT SEARCH PARSER / DROP TEXT SEARCH PARSER IF EXISTS）
- object_state：目标 text search parser 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- cascade_restrict：CASCADE / RESTRICT 子句（省略默认RESTRICT / CASCADE / RESTRICT）
- privilege_requirement：权限要求（superuser / non_superuser）
- dependency_status：依赖对象状态（无依赖 / 有 configuration 依赖）

### T3：对象名与输入形态因子
- parser_name_shape：text search parser 标识符形态

### T4：依赖对象与环境因子
- privilege_context：权限上下文
- dependency_context：依赖对象驻留情况

### T5：异常与边界因子
- error_type：失败原因分类

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP TEXT SEARCH PARSER 全部语法分支。
- 覆盖目标 text search parser 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 superuser 权限边界和依赖对象驻留。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- DROP TEXT SEARCH PARSER 要求 SUPERUSER 权限；非 superuser 执行路径属于失败路径，必须在生成样本中显式标注。
- 必须覆盖目标 parser 存在时的成功删除路径，以及目标 parser 不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- DROP TEXT SEARCH PARSER 不涉及 table / column 组合，不需要挂靠基表列类型。
- 每个样本必须包含明确的前置对象准备、目标 DROP TEXT SEARCH PARSER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与依赖对象驻留相关的因子必须挂靠到 CASCADE/RESTRICT 分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和 superuser 权限核心路径。
- 次优先保证 IF EXISTS 子句、CASCADE/RESTRICT 依赖边界代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: text_search_parser
  skill_name: drop_text_search_parser
  official_source: https://www.postgresql.org/docs/16/sql-droptsparser.html
  statement:
    key: drop_text_search_parser
    name: DROP TEXT SEARCH PARSER
    aliases:
    - drop_text_search_parser
    - DROP TEXT SEARCH PARSER
    purpose: DROP TEXT SEARCH PARSER — remove a text search parser
  syntax_templates:
  - "DROP TEXT SEARCH PARSER [ IF EXISTS ] name [ CASCADE | RESTRICT ]"
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
    - privilege_requirement
    - dependency_status
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - parser_name_shape
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
      - key: branch_drop_ts_parser
        label: DROP TEXT SEARCH PARSER name
      - key: branch_drop_ts_parser_if_exists
        label: DROP TEXT SEARCH PARSER IF EXISTS name
    object_state:
      label: 目标 text search parser 对象状态
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
    privilege_requirement:
      label: 权限要求
      importance: non_important
      values:
      - superuser
      - non_superuser
    dependency_status:
      label: 依赖对象状态
      importance: non_important
      values:
      - no_dependencies
      - has_config_dependencies
    parser_name_shape:
      label: text search parser 标识符形态
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
      - superuser_session
      - non_superuser_session
    dependency_context:
      label: 依赖对象驻留情况
      importance: non_important
      values:
      - no_dependencies
      - config_using_parser
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
    - privilege_requirement
    - dependency_status
    - parser_name_shape
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
    statement_template: "DROP TEXT SEARCH PARSER [ IF EXISTS ] {parser_name} [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT prsname FROM pg_ts_parser WHERE prsname = '{parser_name}'"
    factor_value_bindings: {}
```
