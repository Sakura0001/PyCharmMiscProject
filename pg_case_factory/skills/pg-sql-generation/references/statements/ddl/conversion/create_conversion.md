# 技能：CREATE CONVERSION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createconversion.html

```sql
CREATE [ DEFAULT ] CONVERSION name
    FOR source_encoding TO dest_encoding FROM function_name
```

PG16 关键约束：
- 需要 CREATE 权限于目标 schema 和 EXECUTE 权限于转换函数
- 创建 conversion 的权限要求可能在未来版本中变更
- DEFAULT 标记该转换为 source→dest 编码对的默认转换；同一 schema 内每个编码对只能有一个 DEFAULT 转换
- DEFAULT 转换要启用自动客户端↔服务器编码转换，必须定义双向转换（A→B 和 B→A）
- 转换函数必须具有特定签名：conv_proc(integer, integer, cstring, internal, integer, boolean) RETURNS integer
- 源编码和目标编码都不能是 SQL_ASCII（SQL_ASCII 的服务器行为是硬编码的）
- 转换名称在其 schema 内必须唯一
- conversion 函数实际上需要 C 语言实现（内部签名要求），实践中需要 superuser 创建该函数

## 语句作用

官方说明：CREATE CONVERSION — define a new encoding conversion

该 reference 关注字符集编码转换对象的定义。CREATE CONVERSION 涉及源编码与目标编码的组合选择、转换函数依赖、DEFAULT 标记语义和命名唯一性约束。该语句不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE CONVERSION / CREATE DEFAULT CONVERSION）
- source_encoding：源编码名称
- dest_encoding：目标编码名称
- object_state：目标 conversion 对象状态（not_exists / exists / same_encoding_pair_default_exists）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- default_flag：DEFAULT 标记（省略 / 指定 DEFAULT）
- conversion_function_state：转换函数状态（存在且签名合法 / 不存在 / 签名不满足要求）
- encoding_pair_direction：编码对方向（单方向 / 双方向已存在反向）

### T3：对象名与输入形态因子
- conversion_name_shape：conversion 名称形态
- function_name_shape：转换函数名称形态
- encoding_name_shape：编码名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（superuser / schema_owner_with_create / non_owner_no_create）
- schema_existence：schema 存在性（存在 / 不存在）
- function_privilege：转换函数 EXECUTE 权限（有权限 / 无权限）

### T5：异常与边界因子
- duplicate_conversion_name：同 schema 内重名冲突
- duplicate_default_for_encoding_pair：同一编码对的 DEFAULT 转换已存在
- nonexistent_function：转换函数不存在
- function_signature_mismatch：函数签名不满足 conv_proc 要求
- sql_ascii_encoding：源或目标编码为 SQL_ASCII
- nonexistent_encoding：编码名称不存在
- nonexistent_schema：schema 不存在

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE CONVERSION 和 CREATE DEFAULT CONVERSION 两种语法分支。
- 覆盖代表性编码组合（UTF8→LATIN1、LATIN1→UTF8、UTF8→EUC_JP 等核心编码对），不需要覆盖所有可能的编码组合。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖；source_encoding/dest_encoding 做代表性覆盖而非全量覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE CONVERSION 必须指定源编码、目标编码和转换函数名称，每个成功样本必须包含有效参数。
- 转换函数实际上需要 C 语言实现，样本中应使用 plpgsql 或其他可用语言构造替代函数（注意实际 conv_proc 签名要求仅 C 语言可满足）。
- DEFAULT 转换同一 schema 内同一编码对只能有一个，重复定义属于失败路径。
- SQL_ASCII 不能作为源或目标编码，违反此限制的路径属于失败路径。
- conversion 名称在其 schema 内必须唯一，重名属于失败路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 CREATE CONVERSION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- source_encoding/dest_encoding 因子挂靠到不同语法分支组合的代表性样本上轮转注入，确保每个核心编码对至少出现一次。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- DEFAULT 标记因子仅挂靠到 CREATE DEFAULT CONVERSION 分支的样本上。
- encoding_pair_direction 因子挂靠到 DEFAULT 转换的成功/失败样本上。

## 规模控制规则

- 优先保证官方语法分支、编码对代表性覆盖、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 DEFAULT 标记形态、转换函数状态和编码对方向代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: conversion
  skill_name: create_conversion
  official_source: https://www.postgresql.org/docs/16/sql-createconversion.html
  statement:
    key: create_conversion
    name: CREATE CONVERSION
    aliases:
    - create_conversion
    - CREATE CONVERSION
    purpose: CREATE CONVERSION — define a new encoding conversion
  syntax_templates:
  - "CREATE [ DEFAULT ] CONVERSION name\n    FOR source_encoding TO dest_encoding\
    \ FROM function_name"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - source_encoding
    - dest_encoding
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - default_flag
    - conversion_function_state
    - encoding_pair_direction
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - conversion_name_shape
    - function_name_shape
    - encoding_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_existence
    - function_privilege
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_conversion_name
    - duplicate_default_for_encoding_pair
    - nonexistent_function
    - function_signature_mismatch
    - sql_ascii_encoding
    - nonexistent_encoding
    - nonexistent_schema
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
      - key: branch_create_conversion
        label: CREATE CONVERSION name FOR source_encoding TO dest_encoding FROM function_name
      - key: branch_create_default_conversion
        label: CREATE DEFAULT CONVERSION name FOR source_encoding TO dest_encoding FROM function_name
    source_encoding:
      label: 源编码名称
      importance: important
      values:
      - UTF8
      - LATIN1
      - EUC_JP
      - EUC_KR
      - WIN1252
      - ISO_8859_5
      - SQL_ASCII
    dest_encoding:
      label: 目标编码名称
      importance: important
      values:
      - UTF8
      - LATIN1
      - EUC_JP
      - WIN1252
      - ISO_8859_5
      - SQL_ASCII
    object_state:
      label: 目标 conversion 对象状态
      importance: important
      values:
      - not_exists
      - exists
      - same_encoding_pair_default_exists
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    default_flag:
      label: DEFAULT 标记
      importance: non_important
      values:
      - omitted
      - specified_default
    conversion_function_state:
      label: 转换函数状态
      importance: non_important
      values:
      - function_exists_valid_signature
      - function_not_exists
      - function_exists_invalid_signature
    encoding_pair_direction:
      label: 编码对方向
      importance: non_important
      values:
      - single_direction
      - reverse_direction_exists
    conversion_name_shape:
      label: conversion 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified
      - reserved_word_as_name
      - duplicate_name
    function_name_shape:
      label: 转换函数名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified
      - nonexistent_name
    encoding_name_shape:
      label: 编码名称形态
      importance: non_important
      values:
      - valid_encoding_name
      - nonexistent_encoding_name
      - sql_ascii_encoding_name
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - schema_owner_with_create
      - non_owner_no_create
    schema_existence:
      label: schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    function_privilege:
      label: 转换函数 EXECUTE 权限
      importance: non_important
      values:
      - has_execute
      - no_execute
    duplicate_conversion_name:
      label: 同 schema 内重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_schema_conflict
    duplicate_default_for_encoding_pair:
      label: 同一编码对的 DEFAULT 转换已存在
      importance: non_important
      values:
      - no_existing_default
      - default_already_exists
    nonexistent_function:
      label: 转换函数不存在
      importance: non_important
      values:
      - function_exists
      - function_not_exists
    function_signature_mismatch:
      label: 函数签名不满足 conv_proc 要求
      importance: non_important
      values:
      - valid_conv_proc_signature
      - invalid_signature
    sql_ascii_encoding:
      label: 源或目标编码为 SQL_ASCII
      importance: non_important
      values:
      - neither_is_sql_ascii
      - source_is_sql_ascii
      - dest_is_sql_ascii
    nonexistent_encoding:
      label: 编码名称不存在
      importance: non_important
      values:
      - encoding_exists
      - encoding_not_exists
    nonexistent_schema:
      label: schema 不存在
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_conversion
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_conversion
      - cascade_drop
  defaults:
    expected_status: success
    statement_branch: branch_create_conversion
    object_state: not_exists
    source_encoding: UTF8
    dest_encoding: LATIN1
    default_flag: omitted
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - source_encoding
    - dest_encoding
    - object_state
    - expected_status
    non_main_factors:
    - default_flag
    - conversion_function_state
    - encoding_pair_direction
    - conversion_name_shape
    - function_name_shape
    - encoding_name_shape
    - privilege_level
    - schema_existence
    - function_privilege
    - duplicate_conversion_name
    - duplicate_default_for_encoding_pair
    - nonexistent_function
    - function_signature_mismatch
    - sql_ascii_encoding
    - nonexistent_encoding
    - nonexistent_schema
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - source_encoding
  rendering:
    statement_template: "CREATE {default_flag} CONVERSION {conversion_name} FOR\
      \ {source_encoding} TO {dest_encoding} FROM {function_name}"
    verification_query_template: "SELECT conname, conforencoding, contoencoding,\
      \ condefault FROM pg_conversion WHERE conname = '{conversion_name}'"
    factor_value_bindings: {}
```
