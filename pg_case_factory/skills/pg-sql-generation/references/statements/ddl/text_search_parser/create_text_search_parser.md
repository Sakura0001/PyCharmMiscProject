# 技能：CREATE TEXT SEARCH PARSER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createtsparser.html

```sql
CREATE TEXT SEARCH PARSER name (
    START = start_function ,
    GETTOKEN = gettoken_function ,
    END = end_function ,
    LEXTYPES = lextypes_function
    [, HEADLINE = headline_function ]
)
```

PG16 关键约束：
- CREATE TEXT SEARCH PARSER 要求 SUPERUSER 权限，非 superuser 执行路径属于失败路径
- START、GETTOKEN、END、LEXTYPES 四个函数必须全部指定（强制性）
- HEADLINE 为可选函数
- 函数名可 schema 限定，但不指定参数类型（参数列表是预定义好的）
- 不支持 IF NOT EXISTS 或 OR REPLACE
- parser 本身不能独立使用，必须绑定到 text search configuration 中
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：CREATE TEXT SEARCH PARSER — define a new text search parser

该 reference 关注全文搜索解析器对象的定义、函数依赖、superuser 权限和命名约束，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（带 HEADLINE / 不带 HEADLINE）
- object_state：目标 text search parser 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- headline_clause：HEADLINE 子句形态（省略 / 指定）
- function_existence：引用函数存在性（全部存在 / 部分不存在）
- privilege_requirement：权限要求（superuser / non_superuser）

### T3：对象名与输入形态因子
- parser_name_shape：text search parser 名称形态
- function_name_shape：函数名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / non_superuser）
- function_dependency：函数依赖关系

### T5：异常与边界因子
- duplicate_parser_name：重名冲突
- nonexistent_function：引用的函数不存在
- non_superuser_attempt：非 superuser 尝试创建
- missing_required_function：缺少必需函数（START/GETTOKEN/END/LEXTYPES）

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE TEXT SEARCH PARSER 语法分支（HEADLINE 省略 / HEADLINE 指定）中的所有行为路径。
- 覆盖目标 text search parser 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 superuser 权限边界和函数依赖缺失。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE TEXT SEARCH PARSER 要求 SUPERUSER 权限；非 superuser 执行路径属于失败路径，必须在生成样本中显式标注。
- START、GETTOKEN、END、LEXTYPES 四个函数必须全部指定，缺少任何一个属于失败路径。
- HEADLINE 为可选函数，省略和指定两种形态都必须覆盖。
- CREATE TEXT SEARCH PARSER 不支持 IF NOT EXISTS 或 OR REPLACE，必须覆盖重名冲突的失败路径。
- CREATE TEXT SEARCH PARSER 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 CREATE TEXT SEARCH PARSER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 superuser 权限相关的因子必须挂靠到具有明确权限上下文的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和 superuser 权限核心路径。
- 次优先保证 HEADLINE 子句形态和函数依赖代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: text_search_parser
  skill_name: create_text_search_parser
  official_source: https://www.postgresql.org/docs/16/sql-createtsparser.html
  statement:
    key: create_text_search_parser
    name: CREATE TEXT SEARCH PARSER
    aliases:
    - create_text_search_parser
    - CREATE TEXT SEARCH PARSER
    purpose: CREATE TEXT SEARCH PARSER — define a new text search parser
  syntax_templates:
  - "CREATE TEXT SEARCH PARSER name (\n    START = start_function ,\n    GETTOKEN = gettoken_function ,\n    END = end_function ,\n    LEXTYPES = lextypes_function\n)"
  - "CREATE TEXT SEARCH PARSER name (\n    START = start_function ,\n    GETTOKEN = gettoken_function ,\n    END = end_function ,\n    LEXTYPES = lextypes_function ,\n    HEADLINE = headline_function\n)"
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
    - headline_clause
    - function_existence
    - privilege_requirement
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - parser_name_shape
    - function_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - function_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_parser_name
    - nonexistent_function
    - non_superuser_attempt
    - missing_required_function
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
      - key: branch_without_headline
        label: CREATE TEXT SEARCH PARSER name ( START, GETTOKEN, END, LEXTYPES )
      - key: branch_with_headline
        label: CREATE TEXT SEARCH PARSER name ( START, GETTOKEN, END, LEXTYPES, HEADLINE )
    object_state:
      label: 目标 text search parser 对象状态
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
    headline_clause:
      label: HEADLINE 子句形态
      importance: non_important
      values:
      - omitted
      - specified
    function_existence:
      label: 引用函数存在性
      importance: non_important
      values:
      - all_functions_exist
      - some_functions_missing
    privilege_requirement:
      label: 权限要求
      importance: non_important
      values:
      - superuser
      - non_superuser
    parser_name_shape:
      label: text search parser 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - reserved_word_as_name
      - duplicate_name
      - invalid_name
    function_name_shape:
      label: 函数名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - nonexistent_name
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - non_superuser
    function_dependency:
      label: 函数依赖关系
      importance: non_important
      values:
      - all_functions_valid
      - function_missing
    duplicate_parser_name:
      label: 重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    nonexistent_function:
      label: 引用的函数不存在
      importance: non_important
      values:
      - function_exists
      - function_missing
    non_superuser_attempt:
      label: 非 superuser 尝试创建
      importance: non_important
      values:
      - superuser_execution
      - non_superuser_execution
    missing_required_function:
      label: 缺少必需函数
      importance: non_important
      values:
      - all_required_present
      - missing_required_function
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
      - drop_text_search_parser
      - drop_function
  defaults:
    expected_status: success
    object_state: not_exists
    privilege_level: superuser
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - headline_clause
    - function_existence
    - privilege_requirement
    - parser_name_shape
    - function_name_shape
    - privilege_level
    - function_dependency
    - duplicate_parser_name
    - nonexistent_function
    - non_superuser_attempt
    - missing_required_function
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE TEXT SEARCH PARSER {parser_name} ( START = {start_fn} , GETTOKEN = {gettoken_fn} , END = {end_fn} , LEXTYPES = {lextypes_fn} [, HEADLINE = {headline_fn} ] )"
    verification_query_template: "SELECT prsname FROM pg_ts_parser WHERE prsname = '{parser_name}'"
    factor_value_bindings: {}
```
