# 技能：ALTER TEXT SEARCH PARSER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altertsparser.html

```sql
ALTER TEXT SEARCH PARSER name RENAME TO new_name
ALTER TEXT SEARCH PARSER name SET SCHEMA new_schema
```

PG16 关键约束：
- ALTER TEXT SEARCH PARSER 要求 SUPERUSER 权限
- PG16 中 ALTER TEXT SEARCH PARSER 仅支持 RENAME TO 和 SET SCHEMA 两种形式，不支持修改 parser 的底层函数（START/GETTOKEN/END/LEXTYPES/HEADLINE）
- 这与 text search configuration 和 text search dictionary 不同，后者有更多 ALTER 形式
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：ALTER TEXT SEARCH PARSER — change the definition of a text search parser

该 reference 关注全文搜索解析器的重命名和 schema 移动，不涉及表/列/索引组合。特别注意 PG16 中仅支持 RENAME TO 和 SET SCHEMA，不支持任何其他 ALTER 形式。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（RENAME TO / SET SCHEMA）
- object_state：目标 text search parser 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（rename / set_schema）
- duplicate_new_name：RENAME TO 新名称与已有 parser 重名（无冲突 / 重名冲突）
- nonexistent_target_schema：SET SCHEMA 目标 schema 不存在（存在 / 不存在）

### T3：对象名与输入形态因子
- parser_name_shape：text search parser 名称形态
- new_name_shape：RENAME TO 新名称形态
- schema_name_shape：SET SCHEMA 目标 schema 名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / non_superuser）
- schema_existence：SET SCHEMA 目标 schema 存在性（存在 / 不存在）

### T5：异常与边界因子
- nonexistent_parser：目标 text search parser 不存在
- duplicate_new_name：RENAME TO 新名称与已有 parser 重名
- nonexistent_target_schema：SET SCHEMA 目标 schema 不存在
- non_superuser_attempt：非 superuser 尝试修改

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER TEXT SEARCH PARSER 两个语法分支（RENAME TO / SET SCHEMA）中的所有行为路径。
- 覆盖目标 text search parser 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 superuser 权限边界。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- ALTER TEXT SEARCH PARSER 要求 SUPERUSER 权限；非 superuser 执行路径属于失败路径。
- PG16 中仅支持 RENAME TO 和 SET SCHEMA 两种形式，不得伪造其他 ALTER 形式（如修改 parser 函数）。
- 必须预创建可被修改的目标 text search parser，并为每个 ALTER 分支准备最小合法前置状态。
- ALTER TEXT SEARCH PARSER 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的对象变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER TEXT SEARCH PARSER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 superuser 权限相关的因子必须挂靠到具有明确权限上下文的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和 superuser 权限核心路径。
- 次优先保证重名冲突和 schema 存在性代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: text_search_parser
  skill_name: alter_text_search_parser
  official_source: https://www.postgresql.org/docs/16/sql-altertsparser.html
  statement:
    key: alter_text_search_parser
    name: ALTER TEXT SEARCH PARSER
    aliases:
    - alter_text_search_parser
    - ALTER TEXT SEARCH PARSER
    purpose: ALTER TEXT SEARCH PARSER — change the definition of a text search parser
  syntax_templates:
  - "ALTER TEXT SEARCH PARSER name RENAME TO new_name"
  - "ALTER TEXT SEARCH PARSER name SET SCHEMA new_schema"
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
    - alter_action
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - parser_name_shape
    - new_name_shape
    - schema_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_parser
    - duplicate_new_name
    - nonexistent_target_schema
    - non_superuser_attempt
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
      - key: branch_rename
        label: ALTER TEXT SEARCH PARSER name RENAME TO new_name
      - key: branch_set_schema
        label: ALTER TEXT SEARCH PARSER name SET SCHEMA new_schema
    object_state:
      label: 目标 text search parser 对象状态
      importance: important
      values:
      - exists
      - not_exists
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    alter_action:
      label: ALTER 行为类型
      importance: non_important
      values:
      - rename
      - set_schema
    duplicate_new_name:
      label: RENAME TO 新名称与已有 parser 重名
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    nonexistent_target_schema:
      label: SET SCHEMA 目标 schema 不存在
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    parser_name_shape:
      label: text search parser 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - nonexistent_name
    new_name_shape:
      label: RENAME TO 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - duplicate_name
    schema_name_shape:
      label: SET SCHEMA 目标 schema 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_schema
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - non_superuser
    schema_existence:
      label: SET SCHEMA 目标 schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    nonexistent_parser:
      label: 目标 text search parser 不存在
      importance: non_important
      values:
      - parser_exists
      - parser_missing
    non_superuser_attempt:
      label: 非 superuser 尝试修改
      importance: non_important
      values:
      - superuser_execution
      - non_superuser_execution
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_ts_parser
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - revert_rename
      - drop_text_search_parser
  defaults:
    expected_status: success
    object_state: exists
    privilege_level: superuser
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - duplicate_new_name
    - nonexistent_target_schema
    - parser_name_shape
    - new_name_shape
    - schema_name_shape
    - privilege_level
    - schema_existence
    - nonexistent_parser
    - non_superuser_attempt
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER TEXT SEARCH PARSER {parser_name} {alter_clause}"
    verification_query_template: "SELECT prsname FROM pg_ts_parser WHERE prsname = '{parser_name}'"
    factor_value_bindings: {}
```
