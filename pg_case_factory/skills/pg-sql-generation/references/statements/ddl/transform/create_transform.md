# 技能：CREATE TRANSFORM

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createtransform.html

```sql
CREATE [ OR REPLACE ] TRANSFORM FOR type_name LANGUAGE lang_name (
    FROM SQL WITH FUNCTION from_sql_function_name [ (argument_type [, ...]) ],
    TO SQL WITH FUNCTION to_sql_function_name [ (argument_type [, ...]) ]
);
```

PG16 关键约束：
- CREATE TRANSFORM 要求：必须拥有并具有 type 的 USAGE 权限，必须拥有 language 的 USAGE 权限，必须拥有并具有指定函数的 EXECUTE 权限
- 不需要提供两个方向函数；只提供 FROM SQL 或只提供 TO SQL 也可以
- 支持 OR REPLACE，可替换已有 transform 定义
- FROM SQL 函数声明参数和返回类型为 internal，但实际参数为 transform 的 type、实际返回为语言特定表示
- TO SQL 函数声明返回类型为 transform 的 type，参数为 internal，但实际参数为语言特定值
- 函数名未指定参数列表时必须在 schema 中唯一
- 该语句涉及 type_id（数据类型依赖）和 language_id（语言依赖），不涉及基表列类型

## 语句作用

官方说明：CREATE TRANSFORM — define a new transform

该 reference 关注数据类型与语言之间的 transform 定义、函数依赖、权限边界和 OR REPLACE 行为，不涉及表/列组合但涉及类型和语言依赖。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE TRANSFORM / CREATE OR REPLACE TRANSFORM）
- object_state：目标 transform 对象状态（不存在 / 已存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- or_replace_clause：OR REPLACE 子句形态（省略 / 指定）
- transform_direction：transform 方向组合（both directions / only FROM SQL / only TO SQL）
- function_existence：引用函数存在性（全部存在 / 部分不存在）
- type_existence：引用的 type 存在性（存在 / 不存在）
- language_existence：引用的 language 存在性（存在 / 不存在）

### T3：对象名与输入形态因子
- type_name_shape：type 名称形态
- language_name_shape：language 名称形态
- function_name_shape：transform 函数名称形态

### T4：依赖对象与环境因子
- privilege_on_type：对 type 的权限（owner_with_usage / non_owner / no_usage）
- privilege_on_language：对 language 的权限（has_usage / no_usage）
- privilege_on_function：对函数的权限（owner_with_execute / no_execute）
- type_dependency：type 依赖关系
- language_dependency：language 依赖关系

### T5：异常与边界因子
- duplicate_transform：已存在的 transform（without OR REPLACE）
- nonexistent_type：引用的 type 不存在
- nonexistent_language：引用的 language 不存在
- nonexistent_function：引用的函数不存在
- insufficient_type_privilege：缺少 type 的 USAGE 权限或所有权
- insufficient_language_privilege：缺少 language 的 USAGE 权限
- insufficient_function_privilege：缺少函数的 EXECUTE 权限或所有权
- function_signature_mismatch：函数参数/返回类型不匹配 transform 要求

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE TRANSFORM 和 CREATE OR REPLACE TRANSFORM 两个顶层语法分支。
- 覆盖目标 transform 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 type/language 权限边界和函数依赖缺失。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE TRANSFORM 要求拥有并具有 type 的 USAGE 权限、language 的 USAGE 权限和函数的 EXECUTE 权限与所有权。
- 支持 OR REPLACE 时，需要覆盖正常创建和替换已有定义两种路径。
- FROM SQL 和 TO SQL 两个方向不必同时提供；只提供一个方向也属于合法路径。
- CREATE TRANSFORM 不涉及 table / column 组合，不需要挂靠基表列类型，但涉及 type（数据类型）和 language 依赖。
- 成功路径必须包含可验证的 transform 存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备（type、language、函数）、目标 CREATE TRANSFORM 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 type 权限相关的因子必须挂靠到引用 type 的样本上。
- 与 language 权限相关的因子必须挂靠到引用 language 的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 OR REPLACE 替换语义、transform 方向组合和函数依赖代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: transform
  skill_name: create_transform
  official_source: https://www.postgresql.org/docs/16/sql-createtransform.html
  statement:
    key: create_transform
    name: CREATE TRANSFORM
    aliases:
    - create_transform
    - CREATE TRANSFORM
    - CREATE OR REPLACE TRANSFORM
    purpose: CREATE TRANSFORM — define a new transform
  syntax_templates:
  - "CREATE [ OR REPLACE ] TRANSFORM FOR type_name LANGUAGE lang_name (\n    FROM SQL WITH FUNCTION from_sql_function_name [ (argument_type [, ...]) ],\n    TO SQL WITH FUNCTION to_sql_function_name [ (argument_type [, ...]) ]\n);"
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
    - or_replace_clause
    - transform_direction
    - function_existence
    - type_existence
    - language_existence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - type_name_shape
    - language_name_shape
    - function_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_on_type
    - privilege_on_language
    - privilege_on_function
    - type_dependency
    - language_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_transform
    - nonexistent_type
    - nonexistent_language
    - nonexistent_function
    - insufficient_type_privilege
    - insufficient_language_privilege
    - insufficient_function_privilege
    - function_signature_mismatch
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
      - key: branch_create_transform
        label: CREATE TRANSFORM FOR type_name LANGUAGE lang_name ( ... )
      - key: branch_create_or_replace_transform
        label: CREATE OR REPLACE TRANSFORM FOR type_name LANGUAGE lang_name ( ... )
    object_state:
      label: 目标 transform 对象状态
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
    or_replace_clause:
      label: OR REPLACE 子句形态
      importance: non_important
      values:
      - omitted
      - present
    transform_direction:
      label: transform 方向组合
      importance: non_important
      values:
      - both_from_and_to_sql
      - only_from_sql
      - only_to_sql
    function_existence:
      label: 引用函数存在性
      importance: non_important
      values:
      - all_functions_exist
      - some_functions_missing
    type_existence:
      label: 引用的 type 存在性
      importance: non_important
      values:
      - type_exists
      - type_not_exists
    language_existence:
      label: 引用的 language 存在性
      importance: non_important
      values:
      - language_exists
      - language_not_exists
    type_name_shape:
      label: type 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - quoted_id
      - nonexistent_name
    language_name_shape:
      label: language 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_name
    function_name_shape:
      label: transform 函数名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - nonexistent_name
    privilege_on_type:
      label: 对 type 的权限
      importance: non_important
      values:
      - owner_with_usage
      - non_owner_with_usage
      - no_usage_privilege
    privilege_on_language:
      label: 对 language 的权限
      importance: non_important
      values:
      - has_usage
      - no_usage
    privilege_on_function:
      label: 对函数的权限
      importance: non_important
      values:
      - owner_with_execute
      - no_execute_privilege
    type_dependency:
      label: type 依赖关系
      importance: non_important
      values:
      - type_exists_and_valid
      - type_missing
    language_dependency:
      label: language 依赖关系
      importance: non_important
      values:
      - language_exists_and_valid
      - language_missing
    duplicate_transform:
      label: 已存在的 transform（without OR REPLACE）
      importance: non_important
      values:
      - no_conflict
      - existing_transform_without_or_replace
    nonexistent_type:
      label: 引用的 type 不存在
      importance: non_important
      values:
      - type_exists
      - type_missing
    nonexistent_language:
      label: 引用的 language 不存在
      importance: non_important
      values:
      - language_exists
      - language_missing
    nonexistent_function:
      label: 引用的函数不存在
      importance: non_important
      values:
      - function_exists
      - function_missing
    insufficient_type_privilege:
      label: 缺少 type 的 USAGE 权限或所有权
      importance: non_important
      values:
      - has_privilege
      - lacks_privilege
    insufficient_language_privilege:
      label: 缺少 language 的 USAGE 权限
      importance: non_important
      values:
      - has_privilege
      - lacks_privilege
    insufficient_function_privilege:
      label: 缺少函数的 EXECUTE 权限或所有权
      importance: non_important
      values:
      - has_privilege
      - lacks_privilege
    function_signature_mismatch:
      label: 函数参数/返回类型不匹配
      importance: non_important
      values:
      - signature_matches
      - signature_mismatch
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_transform
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_transform
      - drop_type
      - drop_function
  defaults:
    expected_status: success
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - or_replace_clause
    - transform_direction
    - function_existence
    - type_existence
    - language_existence
    - type_name_shape
    - language_name_shape
    - function_name_shape
    - privilege_on_type
    - privilege_on_language
    - privilege_on_function
    - type_dependency
    - language_dependency
    - duplicate_transform
    - nonexistent_type
    - nonexistent_language
    - nonexistent_function
    - insufficient_type_privilege
    - insufficient_language_privilege
    - insufficient_function_privilege
    - function_signature_mismatch
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE [ OR REPLACE ] TRANSFORM FOR {type_name} LANGUAGE {lang_name} ( {transform_clause} );"
    verification_query_template: "SELECT trftype, trflang FROM pg_transform WHERE trftype = '{type_oid}' AND trflang = '{lang_oid}'"
    factor_value_bindings: {}
```
