# 技能：CREATE TEXT SEARCH DICTIONARY

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createtsdictionary.html

```sql
CREATE TEXT SEARCH DICTIONARY name (
    TEMPLATE = template
    [, option = value [, ... ]]
)
```

PG16 关键约束：
- CREATE TEXT SEARCH DICTIONARY 要求执行者拥有 schema 的 CREATE 权限
- 必须指定 TEMPLATE = template，引用已存在的 text search template
- TEMPLATE 引用的 template 必须存在，否则失败
- 不支持 IF NOT EXISTS 或 OR REPLACE
- option = value 为 template 相关选项，值如果不是简单标识符或数字必须加引号
- 该语句不涉及列类型，不需要挂靠基表列类型

## 语句作用

官方说明：CREATE TEXT SEARCH DICTIONARY — define a new text search dictionary

该 reference 关注全文搜索字典对象的定义、template 依赖、选项配置和命名约束，不涉及表/列/索引组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE TEXT SEARCH DICTIONARY 标准形式）
- object_state：目标 text search dictionary 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- template_existence：TEMPLATE 引用的 template 存在性（存在 / 不存在）
- option_clause：选项子句形态（仅 TEMPLATE / TEMPLATE 加单选项 / TEMPLATE 加多选项）
- option_value_type：选项值形态（简单标识符 / 数字 / 加引号字符串）

### T3：对象名与输入形态因子
- dict_name_shape：text search dictionary 名称形态
- template_name_shape：TEMPLATE 名称形态
- option_value_shape：选项值形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（schema owner / non_owner / superuser）
- schema_existence：schema 存在性（存在 / 不存在）
- template_dependency：template 依赖关系

### T5：异常与边界因子
- duplicate_dict_name：重名冲突
- nonexistent_template：TEMPLATE 引用的 template 不存在
- invalid_option_value：无效的选项值
- schema_permission_denied：schema CREATE 权限不足

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE TEXT SEARCH DICTIONARY 单一语法分支中的所有可选子句组合。
- 覆盖目标 text search dictionary 存在 / 不存在 / 冲突路径。
- 覆盖成功路径与失败路径，包括 template 依赖缺失和重名冲突。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE TEXT SEARCH DICTIONARY 不支持 IF NOT EXISTS 或 OR REPLACE，必须覆盖重名冲突的失败路径。
- TEMPLATE 引用的 template 必须存在，不存在属于失败路径。
- CREATE TEXT SEARCH DICTIONARY 不涉及 table / column 组合，不需要挂靠基表列类型。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 CREATE TEXT SEARCH DICTIONARY 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 template 依赖相关的因子必须挂靠到引用 template 的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 TEMPLATE 依赖、选项子句形态代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: text_search_dictionary
  skill_name: create_text_search_dictionary
  official_source: https://www.postgresql.org/docs/16/sql-createtsdictionary.html
  statement:
    key: create_text_search_dictionary
    name: CREATE TEXT SEARCH DICTIONARY
    aliases:
    - create_text_search_dictionary
    - CREATE TEXT SEARCH DICTIONARY
    purpose: CREATE TEXT SEARCH DICTIONARY — define a new text search dictionary
  syntax_templates:
  - "CREATE TEXT SEARCH DICTIONARY name (\n    TEMPLATE = template\n    [, option = value [, ... ]]\n)"
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
    - template_existence
    - option_clause
    - option_value_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - dict_name_shape
    - template_name_shape
    - option_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_existence
    - template_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_dict_name
    - nonexistent_template
    - invalid_option_value
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
      - key: branch_1
        label: CREATE TEXT SEARCH DICTIONARY 标准形式
    object_state:
      label: 目标 text search dictionary 对象状态
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
    template_existence:
      label: TEMPLATE 引用的 template 存在性
      importance: non_important
      values:
      - template_exists
      - template_not_exists
    option_clause:
      label: 选项子句形态
      importance: non_important
      values:
      - only_template
      - template_plus_single_option
      - template_plus_multiple_options
    option_value_type:
      label: 选项值形态
      importance: non_important
      values:
      - simple_identifier
      - numeric_value
      - quoted_string_value
    dict_name_shape:
      label: text search dictionary 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - reserved_word_as_name
      - duplicate_name
      - invalid_name
    template_name_shape:
      label: TEMPLATE 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - nonexistent_name
    option_value_shape:
      label: 选项值形态
      importance: non_important
      values:
      - valid_value
      - quoted_value
      - invalid_value
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
    template_dependency:
      label: template 依赖关系
      importance: non_important
      values:
      - template_exists_and_valid
      - template_missing
    duplicate_dict_name:
      label: 重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_conflict
    nonexistent_template:
      label: TEMPLATE 引用的 template 不存在
      importance: non_important
      values:
      - template_exists
      - template_missing
    invalid_option_value:
      label: 无效的选项值
      importance: non_important
      values:
      - valid_value
      - invalid_value
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
      - catalog_query_pg_ts_dict
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_text_search_dictionary
      - drop_template
  defaults:
    expected_status: success
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - template_existence
    - option_clause
    - option_value_type
    - dict_name_shape
    - template_name_shape
    - option_value_shape
    - privilege_level
    - schema_existence
    - template_dependency
    - duplicate_dict_name
    - nonexistent_template
    - invalid_option_value
    - schema_permission_denied
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE TEXT SEARCH DICTIONARY {dict_name} ( TEMPLATE = {template_name} [, {option_clause} ] )"
    verification_query_template: "SELECT dictname FROM pg_ts_dict WHERE dictname = '{dict_name}'"
    factor_value_bindings: {}
```
