# 技能：CREATE STATISTICS

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createstatistics.html

```sql
CREATE STATISTICS [ [ IF NOT EXISTS ] statistics_name ]
    ON ( expression )
    FROM table_name

CREATE STATISTICS [ [ IF NOT EXISTS ] statistics_name ]
    [ ( statistics_kind [, ... ] ) ]
    ON { column_name | ( expression ) }, { column_name | ( expression ) } [, ...]
    FROM table_name
```

**重要约束：**
- CREATE STATISTICS 有两种语法形式：单变量表达式统计（Form 1）和多变量列/表达式统计（Form 2）。
- statistics_kind 包括 ndistinct、dependencies、mcv。省略时包含所有支持的统计类型。
- 多变量统计（Form 2）至少需要两个列名或表达式。
- 单变量统计（Form 1）仅支持单个表达式，不支持 statistics_kind 指定。
- statistics_name 可选省略（自动生成基于表名和列名的名称），但 IF NOT EXISTS 指定时名称必填。
- statistics_name 支持 schema 限定。
- 需要 table 的 owner 权限或 superuser 权限。
- 统计对象涉及列组合选择，决定了在哪些列上构建扩展统计。

## 语句作用

官方说明：CREATE STATISTICS — define extended statistics

该 reference 关注扩展统计定义语句的两种语法形式（单变量 / 多变量）、statistics_kind 组合、列组合选择、IF NOT EXISTS 行为、表达式形态、权限边界和成功/失败路径。CREATE STATISTICS 涉及列组合选择。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（Form 1 单变量 / Form 2 多变量）
- statistics_identity：目标 statistics 存在状态
- expected_status：预期结果

### T2：重要行为因子
- statistics_kind_clause：statistics_kind 子句形态（ndistinct / dependencies / mcv / 组合 / 略省）
- column_combination：列组合形态（单列 / 多列 / 列+表达式混合）
- if_not_exists_clause：IF NOT EXISTS 子句行为
- expression_shape：表达式形态
- statistics_name_presence：statistics_name 是否出现

### T3：对象名与输入形态因子
- statistics_name_shape：statistics 名标识符形态
- table_name_shape：表名形态
- column_name_shape：列名形态

### T4：依赖对象与环境因子
- **CREATE STATISTICS 需要引用已有的表和列。列组合选择决定了统计覆盖范围。**
- executor_privilege：执行者权限上下文
- table_dependency：依赖表存在状态
- column_dependency：依赖列存在状态

### T5：异常与边界因子
- duplicate_statistics_name：statistics 名冲突
- privilege_insufficient：权限不足（非 table owner）
- nonexistent_table：依赖表不存在
- nonexistent_column：依赖列不存在
- single_column_for_multivariate：多变量形式仅指定单列
- expression_syntax_error：表达式语法错误

### T6：验证与清理因子
- verification_mode：验证方式（pg_statistic_ext 目录查询）
- cleanup_mode：清理方式（DROP STATISTICS）

## 覆盖策略

- 覆盖两种语法形式（单变量表达式统计 / 多变量列组合统计）。
- 覆盖 statistics_kind 的代表性组合（ndistinct / dependencies / mcv / 略省）。
- 覆盖列组合的代表性形态（2 列 / 3 列 / 列+表达式混合）。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖 statistics 成功创建、重名冲突（IF NOT EXISTS no-op）、权限不足与依赖对象缺失路径。
- Form 1（单变量）和 Form 2（多变量）需要分别覆盖，不得将单列归入多变量形式。
- 成功路径必须包含可通过 pg_statistic_ext 目录验证的统计对象存在性检查，并在生命周期末尾清理。
- 每个样本必须包含明确的前置表准备、目标 CREATE STATISTICS 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限上下文或表/列依赖的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 两种语法形式全覆盖（Form 1 / Form 2）
  - statistics 存在/不存在/冲突全覆盖
  - IF NOT EXISTS no-op 覆盖
  - 成功/失败路径全覆盖
- 次优先保证：
  - statistics_kind 组合代表性覆盖
  - 列组合代表性覆盖（2 列、3 列、列+表达式）
  - expression 形态代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: statistics
  skill_name: create_statistics
  official_source: https://www.postgresql.org/docs/16/sql-createstatistics.html
  statement:
    key: create_statistics
    name: CREATE STATISTICS
    aliases:
    - create_statistics
    - CREATE STATISTICS
    purpose: CREATE STATISTICS — define extended statistics
  syntax_templates:
  - "CREATE STATISTICS [ [ IF NOT EXISTS ] statistics_name ]\n    ON ( expression )\n    FROM table_name"
  - "CREATE STATISTICS [ [ IF NOT EXISTS ] statistics_name ]\n    [ ( statistics_kind [, ... ] ) ]\n    ON { column_name | ( expression ) }, { column_name | ( expression ) } [, ...]\n    FROM table_name"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - statistics_identity
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - statistics_kind_clause
    - column_combination
    - if_not_exists_clause
    - expression_shape
    - statistics_name_presence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - statistics_name_shape
    - table_name_shape
    - column_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - executor_privilege
    - table_dependency
    - column_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_statistics_name
    - privilege_insufficient
    - nonexistent_table
    - nonexistent_column
    - single_column_for_multivariate
    - expression_syntax_error
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
      - key: branch_univariate_expression
        label: CREATE STATISTICS ON ( expression ) FROM table_name — 单变量表达式统计
      - key: branch_multivariate_columns
        label: CREATE STATISTICS ON column_name, column_name FROM table_name — 多变量列组合统计
    statistics_identity:
      label: 目标 statistics 存在状态
      importance: important
      values:
      - not_exists
      - exists
      - exists_with_if_not_exists
      - reserved_word_name
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    statistics_kind_clause:
      label: statistics_kind 子句
      importance: important
      values:
      - omitted_all_kinds
      - ndistinct_only
      - dependencies_only
      - mcv_only
      - ndistinct_and_dependencies
      - all_three_kinds
    column_combination:
      label: 列组合形态
      importance: important
      values:
      - two_columns
      - three_columns
      - column_and_expression_mix
      - single_expression_univariate
    if_not_exists_clause:
      label: IF NOT EXISTS 子句
      importance: non_important
      values:
      - without_if_not_exists
      - with_if_not_exists
    expression_shape:
      label: 表达式形态
      importance: non_important
      values:
      - simple_column_reference
      - arithmetic_expression
      - function_call_expression
    statistics_name_presence:
      label: statistics_name 是否出现
      importance: non_important
      values:
      - explicit_name
      - auto_generated_name_omitted
    statistics_name_shape:
      label: statistics 名标识符形态
      importance: non_important
      values:
      - simple_name
      - schema_qualified_name
      - quoted_name
      - reserved_word_name
      - non_existing_name
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - simple_name
      - schema_qualified_name
      - quoted_name
      - nonexistent_table
    column_name_shape:
      label: 列名形态
      importance: non_important
      values:
      - simple_name
      - quoted_name
      - nonexistent_column
    executor_privilege:
      label: 执行者权限上下文
      importance: non_important
      values:
      - superuser
      - table_owner
      - non_owner_no_privilege
    table_dependency:
      label: 依赖表存在状态
      importance: non_important
      values:
      - table_exists
      - table_not_exists
    column_dependency:
      label: 依赖列存在状态
      importance: non_important
      values:
      - column_exists
      - column_not_exists
    duplicate_statistics_name:
      label: statistics 名冲突
      importance: non_important
      values:
      - none
      - same_name_exists
    privilege_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - non_table_owner_creating_statistics
    nonexistent_table:
      label: 依赖表不存在
      importance: non_important
      values:
      - table_not_exists_failure
    nonexistent_column:
      label: 依赖列不存在
      importance: non_important
      values:
      - column_not_exists_failure
    single_column_for_multivariate:
      label: 多变量形式仅指定单列
      importance: non_important
      values:
      - single_column_multivariate_failure
    expression_syntax_error:
      label: 表达式语法错误
      importance: non_important
      values:
      - invalid_expression_failure
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - pg_statistic_ext_catalog
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_statistics
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - statistics_identity
    - expected_status
    non_main_factors:
    - statistics_kind_clause
    - column_combination
    - if_not_exists_clause
    - expression_shape
    - statistics_name_presence
    - statistics_name_shape
    - table_name_shape
    - column_name_shape
    - executor_privilege
    - table_dependency
    - column_dependency
    - duplicate_statistics_name
    - privilege_insufficient
    - nonexistent_table
    - nonexistent_column
    - single_column_for_multivariate
    - expression_syntax_error
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - statistics_identity
  rendering:
    statement_template: "CREATE STATISTICS [ IF NOT EXISTS ] {statistics_name} [ ( {statistics_kind} ) ] ON {columns_or_expression} FROM {table_name}"
    verification_query_template: "SELECT stxname FROM pg_statistic_ext WHERE stxname = '{statistics_name}'"
    factor_value_bindings:
      if_not_exists_clause:
        without_if_not_exists: ""
        with_if_not_exists: "IF NOT EXISTS"
```
