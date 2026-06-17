# 技能：CREATE TEXT SEARCH CONFIGURATION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createtsconfiguration.html

```sql
CREATE TEXT SEARCH CONFIGURATION name (
    PARSER = parser_name |
    COPY = source_config
)
```

PG16 关键约束：
- CREATE TEXT SEARCH CONFIGURATION 要求执行者拥有创建权限（非 superuser 也可执行，但需要 schema 的 CREATE 权限）
- 如果指定 PARSER = parser_name，必须引用已存在的 text search parser（superuser 才能创建 parser）
- 如果指定 COPY = source_config，新配置将复制源配置的映射（mapping），但不复制源配置的 parser
- PARSER 和 COPY 互斥：不能在同一语句中同时指定
- 不支持 IF NOT EXISTS 或 OR REPLACE
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：CREATE TEXT SEARCH CONFIGURATION — define a new text search configuration

该 reference 关注全文搜索配置对象的定义、parser 依赖、copy 来源和命名约束，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（PARSER 形式 / COPY 形式）
- object_state：目标 text search configuration 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- config_source_type：配置来源类型（PARSER = parser_name / COPY = source_config）
- parser_existence：PARSER 引用的 parser 存在性（存在 / 不存在）
- copy_source_existence：COPY 引用的源配置存在性（存在 / 不存在）
- parser_copy_conflict：PARSER 与 COPY 同时指定（互斥 / 仅其一）

### T3：对象名与输入形态因子
- config_name_shape：text search configuration 名称形态
- parser_name_shape：PARSER 名称形态
- copy_source_name_shape：COPY 源配置名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（schema owner / non_owner / superuser）
- schema_existence：schema 存在性（存在 / 不存在）
- parser_dependency：parser 依赖关系

### T5：异常与边界因子
- duplicate_config_name：重名冲突
- nonexistent_parser：PARSER 引用的 parser 不存在
- nonexistent_copy_source：COPY 引用的源配置不存在
- parser_copy_both_specified：PARSER 和 COPY 同时指定
- missing_parser_or_copy：既未指定 PARSER 也未指定 COPY
- schema_permission_denied：schema CREATE 权限不足

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE TEXT SEARCH CONFIGURATION 两个语法分支（PARSER / COPY）中的所有行为路径。
- 覆盖目标 text search configuration 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 parser 依赖缺失和 copy 来源缺失。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE TEXT SEARCH CONFIGURATION 不支持 IF NOT EXISTS 或 OR REPLACE，必须覆盖重名冲突的失败路径。
- PARSER 和 COPY 互斥，同时指定属于语法错误失败路径。
- PARSER 引用的 parser 必须存在，不存在属于失败路径。
- COPY 引用的源配置必须存在，不存在属于失败路径。
- CREATE TEXT SEARCH CONFIGURATION 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 CREATE TEXT SEARCH CONFIGURATION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 parser 依赖相关的因子必须挂靠到 PARSER 分支的样本上。
- 与 copy 来源相关的因子必须挂靠到 COPY 分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 PARSER/COPY 来源依赖、schema 权限边界代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: text_search_configuration
  skill_name: create_text_search_configuration
  official_source: https://www.postgresql.org/docs/16/sql-createtsconfiguration.html
  statement:
    key: create_text_search_configuration
    name: CREATE TEXT SEARCH CONFIGURATION
    aliases:
    - create_text_search_configuration
    - CREATE TEXT SEARCH CONFIGURATION
    purpose: CREATE TEXT SEARCH CONFIGURATION — define a new text search configuration
  syntax_templates:
  - "CREATE TEXT SEARCH CONFIGURATION name (\n    PARSER = parser_name\n)"
  - "CREATE TEXT SEARCH CONFIGURATION name (\n    COPY = source_config\n)"
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
    - config_source_type
    - parser_existence
    - copy_source_existence
    - parser_copy_conflict
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - config_name_shape
    - parser_name_shape
    - copy_source_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_existence
    - parser_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_config_name
    - nonexistent_parser
    - nonexistent_copy_source
    - parser_copy_both_specified
    - missing_parser_or_copy
    - schema_permission_denied
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
      - key: branch_parser
        label: CREATE TEXT SEARCH CONFIGURATION name ( PARSER = parser_name )
      - key: branch_copy
        label: CREATE TEXT SEARCH CONFIGURATION name ( COPY = source_config )
    object_state:
      label: 目标 text search configuration 对象状态
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
    config_source_type:
      label: 配置来源类型
      importance: non_important
      values:
      - parser
      - copy
    parser_existence:
      label: PARSER 引用的 parser 存在性
      importance: non_important
      values:
      - parser_exists
      - parser_not_exists
    copy_source_existence:
      label: COPY 引用的源配置存在性
      importance: non_important
      values:
      - source_exists
      - source_not_exists
    parser_copy_conflict:
      label: PARSER 与 COPY 同时指定
      importance: non_important
      values:
      - only_parser
      - only_copy
      - both_specified
    config_name_shape:
      label: text search configuration 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - reserved_word_as_name
      - duplicate_name
      - invalid_name
    parser_name_shape:
      label: PARSER 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - nonexistent_name
    copy_source_name_shape:
      label: COPY 源配置名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - nonexistent_name
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - schema_owner
      - non_owner
      - superuser
    schema_existence:
      label: schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    parser_dependency:
      label: parser 依赖关系
      importance: non_important
      values:
      - parser_exists_and_valid
      - parser_missing
    duplicate_config_name:
      label: 重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    nonexistent_parser:
      label: PARSER 引用的 parser 不存在
      importance: non_important
      values:
      - parser_exists
      - parser_missing
    nonexistent_copy_source:
      label: COPY 引用的源配置不存在
      importance: non_important
      values:
      - source_exists
      - source_missing
    parser_copy_both_specified:
      label: PARSER 和 COPY 同时指定
      importance: non_important
      values:
      - one_specified
      - both_specified
    missing_parser_or_copy:
      label: 既未指定 PARSER 也未指定 COPY
      importance: non_important
      values:
      - one_specified
      - none_specified
    schema_permission_denied:
      label: schema CREATE 权限不足
      importance: non_important
      values:
      - has_create_privilege
      - lacks_create_privilege
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_ts_config
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_text_search_configuration
      - drop_parser
  defaults:
    expected_status: success
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - config_source_type
    - parser_existence
    - copy_source_existence
    - parser_copy_conflict
    - config_name_shape
    - parser_name_shape
    - copy_source_name_shape
    - privilege_level
    - schema_existence
    - parser_dependency
    - duplicate_config_name
    - nonexistent_parser
    - nonexistent_copy_source
    - parser_copy_both_specified
    - missing_parser_or_copy
    - schema_permission_denied
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE TEXT SEARCH CONFIGURATION {config_name} ( {config_source_clause} )"
    verification_query_template: "SELECT cfgname FROM pg_ts_config WHERE cfgname = '{config_name}'"
    factor_value_bindings: {}
```
