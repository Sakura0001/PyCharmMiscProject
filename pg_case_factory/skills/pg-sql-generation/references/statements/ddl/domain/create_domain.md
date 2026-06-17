# 技能：CREATE DOMAIN

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createdomain.html

```sql
CREATE DOMAIN name [ AS ] data_type
    [ COLLATE collation ]
    [ DEFAULT expression ]
    [ constraint [ ... ] ]

where constraint is:

[ CONSTRAINT constraint_name ]
{ NOT NULL | NULL | CHECK (expression) }
```

PG16 关键约束：
- CREATE DOMAIN 必须指定底层基类型（data_type），域值基于该类型
- NOT NULL 约束仅在值转换为域类型时检查，名义上的域类型列仍可能读取为 null（例如外连接、空标量子 SELECT）
- CHECK 约束中只能引用 VALUE 关键字，不能包含子查询或变量
- 多个 CHECK 约束按名称字母顺序依次测试
- 需要 USAGE 权限于底层基类型
- domain 名称在其 schema 中的类型和域之间必须唯一

## 语句作用

官方说明：CREATE DOMAIN — define a new domain

该 reference 关注域（SQL DOMAIN）对象的定义、底层基类型选择、约束行为和命名约束。域的定义涉及基类型（data_type），因此需要覆盖代表性基类型，但不需要覆盖所有基表或所有列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（CREATE DOMAIN 单一顶层形式）
- base_data_type：底层基类型（域定义所基于的数据类型）
- object_state：目标 domain 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- default_clause：DEFAULT 子句形态（省略 / 指定 expression）
- collate_clause：COLLATE 子句形态（省略 / 指定 collation）
- constraint_type：约束类型组合（NOT NULL / NULL / CHECK / NOT NULL + CHECK / 无约束）
- constraint_naming：约束命名形态（省略名称 / 指定 CONSTRAINT constraint_name）

### T3：对象名与输入形态因子
- domain_name_shape：domain 名称形态
- type_name_shape：底层基类型名称形态
- collation_name_shape：COLLATE 指定的排序规则名称形态
- constraint_name_shape：约束名称形态
- default_expression_shape：DEFAULT expression 形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（owner_of_schema / non_owner / superuser）
- schema_existence：schema 存在性（存在 / 不存在）
- base_type_privilege：底层基类型的 USAGE 权限（有权限 / 无权限）
- collation_existence：COLLATE 指定的排序规则存在性（存在 / 不存在 / 基类型不可排序）

### T5：异常与边界因子
- duplicate_domain_name：重名冲突
- nonexistent_base_type：底层基类型不存在
- privilege_denied_on_base_type：USAGE 权限不足
- invalid_default_expression：DEFAULT expression 非法（子查询 / 类型不匹配）
- null_constraint_conflict：NOT NULL 与 NULL 同时指定
- check_expr_subquery：CHECK 表达式包含子查询
- check_expr_non_boolean：CHECK 表达式非布尔结果
- collation_on_non_collatable_type：在不可排序类型上指定 COLLATE
- reserved_name_conflict：与同 schema 内已有类型/域重名

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 CREATE DOMAIN 单一语法分支中的所有可选子句组合（DEFAULT / COLLATE / 约束）。
- 覆盖代表性底层基类型（整数、文本、布尔、日期时间、数值等核心类型族），不需要覆盖所有可能的数据类型。
- 不需要覆盖所有基表，不需要覆盖所有列类型组合。
- 覆盖目标 domain 存在 / 不存在 / 重名冲突路径。
- 覆盖成功路径与失败路径，包括权限边界和约束语义边界。
- T1 因子做笛卡尔积覆盖；base_data_type 做代表性覆盖而非全量覆盖。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- CREATE DOMAIN 必须指定底层基类型，每个成功样本必须包含有效的 data_type。
- 底层基类型需要覆盖核心类型族（integer, bigint, text, boolean, numeric, date, timestamp, uuid, jsonb 等代表性类型），不需要覆盖全部内置类型。
- NOT NULL 约束仅在值转换为域类型时检查，样本中必须反映此语义边界（外连接 null 可穿透域 NOT NULL 约束）。
- CHECK 约束只能引用 VALUE 关键字，不能包含子查询，违反此限制的路径属于失败路径。
- domain 名称在其 schema 中与类型和域之间必须唯一，重名属于失败路径。
- 需要 USAGE 权限于底层基类型，缺少权限属于失败路径。
- COLLATE 只能用于可排序的基类型，在不可排序类型上指定 COLLATE 属于失败路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 CREATE DOMAIN 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- base_data_type 因子挂靠到不同语法分支组合的代表性样本上轮转注入，确保每个核心类型族至少出现一次。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- 与约束语义边界相关的因子（NOT NULL 穿透、CHECK VALUE 引用）必须挂靠到对应分支的样本上。
- COLLATE 因子仅挂靠到使用可排序基类型的样本上。

## 规模控制规则

- 优先保证官方语法分支、底层基类型代表性覆盖、目标对象存在/不存在/冲突、成功/失败路径和权限核心路径。
- 次优先保证 DEFAULT 子句形态、COLLATE 子句形态、约束类型组合和约束命名代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: domain
  skill_name: create_domain
  official_source: https://www.postgresql.org/docs/16/sql-createdomain.html
  statement:
    key: create_domain
    name: CREATE DOMAIN
    aliases:
    - create_domain
    - CREATE DOMAIN
    purpose: CREATE DOMAIN — define a new domain
  syntax_templates:
  - "CREATE DOMAIN name [ AS ] data_type\n    [ COLLATE collation ]\n    [ DEFAULT\
    \ expression ]\n    [ constraint [ ... ] ]\n\nwhere constraint is:\n\n[ CONSTRAINT\
    \ constraint_name ]\n{ NOT NULL | NULL | CHECK (expression) }"
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - base_data_type
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - default_clause
    - collate_clause
    - constraint_type
    - constraint_naming
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - domain_name_shape
    - type_name_shape
    - collation_name_shape
    - constraint_name_shape
    - default_expression_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_existence
    - base_type_privilege
    - collation_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_domain_name
    - nonexistent_base_type
    - privilege_denied_on_base_type
    - invalid_default_expression
    - null_constraint_conflict
    - check_expr_subquery
    - check_expr_non_boolean
    - collation_on_non_collatable_type
    - reserved_name_conflict
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
      - key: branch_create_domain
        label: CREATE DOMAIN name [ AS ] data_type [ COLLATE ] [ DEFAULT ] [ constraint [...]
    base_data_type:
      label: 底层基类型
      importance: important
      values:
      - integer
      - bigint
      - smallint
      - numeric
      - real
      - double_precision
      - text
      - varchar
      - character
      - boolean
      - date
      - timestamp
      - timestamptz
      - time
      - interval
      - uuid
      - jsonb
      - bytea
      - int_array
      - text_array
    object_state:
      label: 目标 domain 对象状态
      importance: important
      values:
      - not_exists
      - exists
      - type_name_conflict
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    default_clause:
      label: DEFAULT 子句形态
      importance: non_important
      values:
      - omitted
      - literal_default
      - expression_default
      - null_default
    collate_clause:
      label: COLLATE 子句形态
      importance: non_important
      values:
      - omitted
      - specified_collation
    constraint_type:
      label: 约束类型组合
      importance: non_important
      values:
      - none
      - not_null
      - null_explicit
      - check_only
      - not_null_and_check
      - multiple_check
    constraint_naming:
      label: 约束命名形态
      importance: non_important
      values:
      - auto_named
      - explicitly_named
    domain_name_shape:
      label: domain 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified
      - reserved_word_as_name
      - duplicate_name
      - invalid_name
    type_name_shape:
      label: 底层基类型名称形态
      importance: non_important
      values:
      - standard_type_name
      - quoted_type_name
      - nonexistent_type
      - array_type_specifier
    collation_name_shape:
      label: COLLATE 排序规则名称形态
      importance: non_important
      values:
      - default_collation
      - explicit_collation_name
      - nonexistent_collation
    constraint_name_shape:
      label: 约束名称形态
      importance: non_important
      values:
      - auto_generated
      - simple_id
      - quoted_id
    default_expression_shape:
      label: DEFAULT expression 形态
      importance: non_important
      values:
      - literal_value
      - type_matching_expression
      - type_mismatching_expression
      - subquery_illegal
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - schema_owner
      - non_owner_with_create
      - non_owner_no_create
    schema_existence:
      label: schema 存在性
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    base_type_privilege:
      label: 底层基类型 USAGE 权限
      importance: non_important
      values:
      - has_usage
      - no_usage
    collation_existence:
      label: COLLATE 排序规则存在性
      importance: non_important
      values:
      - collation_exists
      - collation_not_exists
      - base_type_not_collatable
    duplicate_domain_name:
      label: 重名冲突
      importance: non_important
      values:
      - no_conflict
      - same_schema_conflict
      - cross_schema_no_conflict
    nonexistent_base_type:
      label: 底层基类型不存在
      importance: non_important
      values:
      - type_exists
      - type_not_exists
    privilege_denied_on_base_type:
      label: USAGE 权限不足
      importance: non_important
      values:
      - has_usage_privilege
      - lacks_usage_privilege
    invalid_default_expression:
      label: DEFAULT expression 非法
      importance: non_important
      values:
      - valid_expression
      - subquery_in_default
      - type_mismatch_default
    null_constraint_conflict:
      label: NOT NULL 与 NULL 同时指定
      importance: non_important
      values:
      - single_constraint
      - conflicting_null_not_null
    check_expr_subquery:
      label: CHECK 表达式包含子查询
      importance: non_important
      values:
      - valid_check
      - subquery_in_check
    check_expr_non_boolean:
      label: CHECK 表达式非布尔结果
      importance: non_important
      values:
      - boolean_check
      - non_boolean_check
    collation_on_non_collatable_type:
      label: 在不可排序类型上指定 COLLATE
      importance: non_important
      values:
      - collatable_type_with_collate
      - non_collatable_type_with_collate
    reserved_name_conflict:
      label: 与同 schema 内已有类型/域重名
      importance: non_important
      values:
      - unique_name
      - name_conflicts_with_type
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_type
      - domain_value_test
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_domain
      - cascade_drop_domain
  defaults:
    expected_status: success
    object_state: not_exists
    base_data_type: integer
    default_clause: omitted
    collate_clause: omitted
    constraint_type: none
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - base_data_type
    - object_state
    - expected_status
    non_main_factors:
    - default_clause
    - collate_clause
    - constraint_type
    - constraint_naming
    - domain_name_shape
    - type_name_shape
    - collation_name_shape
    - constraint_name_shape
    - default_expression_shape
    - privilege_level
    - schema_existence
    - base_type_privilege
    - collation_existence
    - duplicate_domain_name
    - nonexistent_base_type
    - privilege_denied_on_base_type
    - invalid_default_expression
    - null_constraint_conflict
    - check_expr_subquery
    - check_expr_non_boolean
    - collation_on_non_collatable_type
    - reserved_name_conflict
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - base_data_type
  rendering:
    statement_template: "CREATE DOMAIN {domain_name} [ AS ] {base_data_type} [ COLLATE\
      \ {collation} ] [ DEFAULT {default_expression} ] [{constraint_clause}]"
    verification_query_template: "SELECT typname, typtype FROM pg_type WHERE typname\
      \ = '{domain_name}' AND typtype = 'd'"
    factor_value_bindings: {}
```
