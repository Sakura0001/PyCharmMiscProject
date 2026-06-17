# 技能：CREATE AGGREGATE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createaggregate.html

### Synopsis 形式 1：常规聚合函数

```sql
CREATE [ OR REPLACE ] AGGREGATE name ( [ argmode ] [ argname ] arg_data_type [ , ... ] ) (
    SFUNC = sfunc,
    STYPE = state_data_type
    [ , SSPACE = state_data_size ]
    [ , FINALFUNC = ffunc ]
    [ , FINALFUNC_EXTRA ]
    [ , FINALFUNC_MODIFY = { READ_ONLY | SHAREABLE | READ_WRITE } ]
    [ , COMBINEFUNC = combinefunc ]
    [ , SERIALFUNC = serialfunc ]
    [ , DESERIALFUNC = deserialfunc ]
    [ , INITCOND = initial_condition ]
    [ , MSFUNC = msfunc ]
    [ , MINVFUNC = minvfunc ]
    [ , MSTYPE = mstate_data_type ]
    [ , MSSPACE = mstate_data_size ]
    [ , MFINALFUNC = mffunc ]
    [ , MFINALFUNC_EXTRA ]
    [ , MFINALFUNC_MODIFY = { READ_ONLY | SHAREABLE | READ_WRITE } ]
    [ , MINITCOND = minitial_condition ]
    [ , SORTOP = sort_operator ]
    [ , PARALLEL = { SAFE | RESTRICTED | UNSAFE } ]
)
```

### Synopsis 形式 2：有序集/假设集聚合函数

```sql
CREATE [ OR REPLACE ] AGGREGATE name ( [ [ argmode ] [ argname ] arg_data_type [ , ... ] ]
                        ORDER BY [ argmode ] [ argname ] arg_data_type [ , ... ] ) (
    SFUNC = sfunc,
    STYPE = state_data_type
    [ , SSPACE = state_data_size ]
    [ , FINALFUNC = ffunc ]
    [ , FINALFUNC_EXTRA ]
    [ , FINALFUNC_MODIFY = { READ_ONLY | SHAREABLE | READ_WRITE } ]
    [ , INITCOND = initial_condition ]
    [ , PARALLEL = { SAFE | RESTRICTED | UNSAFE } ]
    [ , HYPOTHETICAL ]
)
```

### Synopsis 形式 3：旧语法

```sql
CREATE [ OR REPLACE ] AGGREGATE name (
    BASETYPE = base_type,
    SFUNC = sfunc,
    STYPE = state_data_type
    [ , SSPACE = state_data_size ]
    [ , FINALFUNC = ffunc ]
    [ , FINALFUNC_EXTRA ]
    [ , FINALFUNC_MODIFY = { READ_ONLY | SHAREABLE | READ_WRITE } ]
    [ , COMBINEFUNC = combinefunc ]
    [ , SERIALFUNC = serialfunc ]
    [ , DESERIALFUNC = deserialfunc ]
    [ , INITCOND = initial_condition ]
    [ , MSFUNC = msfunc ]
    [ , MINVFUNC = minvfunc ]
    [ , MSTYPE = mstate_data_type ]
    [ , MSSPACE = mstate_data_size ]
    [ , MFINALFUNC = mffunc ]
    [ , MFINALFUNC_EXTRA ]
    [ , MFINALFUNC_MODIFY = { READ_ONLY | SHAREABLE | READ_WRITE } ]
    [ , MINITCOND = minitial_condition ]
    [ , SORTOP = sort_operator ]
)
```

**重要行为说明**：
- CREATE AGGREGATE 有三种形式：常规聚合、有序集聚合、旧语法。
- sfunc 输入参数类型 = STYPE + arg_data_type(s)；输出类型 = STYPE。这些参数数据类型是聚合函数身份的关键组成部分。
- OR REPLACE 不可改变参数类型、返回类型和直接参数数量；新定义必须与旧定义同种类。
- PARALLEL 默认 UNSAFE；启用并行聚合需要 COMBINEFUNC，internal 状态还需 SERIALFUNC/DESERIALFUNC。
- FINALFUNC_EXTRA 让最终函数额外接收聚合参数的 NULL 值（用于多态结果类型解析）。
- 有序集聚合仅允许 VARIADIC "any"，不允许其他 variadic 数组类型。
- 旧语法无法定义有序集聚合。
- strict sfunc 的特殊行为：首行全非 NULL 输入直接替换 null 初始状态值。

## 语句作用

官方说明：CREATE AGGREGATE — define a new aggregate function

该 reference 关注聚合函数定义语句的语法分支、参数数据类型选择（sfunc 输入/输出类型是关键覆盖维度）、OR REPLACE 行为与函数依赖，不负责覆盖所有基表列类型组合。

CREATE AGGREGATE **涉及参数数据类型**，具体表现为：
- arg_data_type 决定聚合函数的输入类型，是聚合函数身份的核心
- STYPE（state_data_type）决定内部状态类型，影响 sfunc 签名
- 有序集聚合的 direct argument 与 ORDER BY argument 的类型区分
- 多态聚合使用 polymorphic 类型（anyelement 等）

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（regular、ordered_set、old_syntax）
- object_state：目标 Aggregate 对象存在性（不存在、已存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- aggregate_form：聚合函数形态（single_arg、multi_arg、zero_arg、ordered_set、old_syntax）
- or_replace_clause：OR REPLACE 子句（absent、present_replace_existing、present_replace_with_constraint_violation）
- parallel_option：PARALLEL 选项（SAFE、RESTRICTED、UNSAFE_default）
- arg_data_type：参数数据类型—聚合函数身份关键维度

### T3：对象名与输入形态因子
- aggregate_name_shape：聚合函数名称形态（plain_identifier、quoted_identifier、schema_qualified、reserved_word）
- argmode_shape：参数模式形态（IN、VARIADIC）
- argname_shape：参数名称形态（absent、plain、quoted）
- sfunc_name_shape：sfunc 函数名形态（plain、schema_qualified）

### T4：依赖对象与环境因子
- privilege_level：权限级别（aggregate_owner、non_owner）
- support_function_dependency：支持函数依赖（sfunc_exists、sfunc_not_exists、sfunc_wrong_signature）
- combinefunc_dependency：COMBINEFUNC 依赖（exists、not_exists）— 仅并行聚合
- finalfunc_dependency：FINALFUNC 依赖（exists、not_exists、wrong_return_type）

### T5：异常与边界因子
- duplicate_aggregate：重名冲突（same_name_same_signature、same_name_different_signature）
- sfunc_signature_mismatch：sfunc 签名与聚合参数类型不匹配
- or_replace_constraint_violation：OR REPLACE 改变参数/返回类型
- invalid_ordered_set_variadic：有序集聚合使用非 VARIADIC "any"
- missing_required_sfunc：缺失必需的 sfunc 函数
- insufficient_privilege：非 Owner 创建聚合函数

### T6：验证与清理因子
- verification_mode：验证方式（pg_aggregate_catalog_query、pg_proc_query、actual_execution）
- cleanup_mode：清理方式（DROP_AGGREGATE、DROP_AGGREGATE_IF_EXISTS、DROP_AGGREGATE_CASCADE）

## 覆盖策略

- 必须覆盖 CREATE AGGREGATE 的三种语法分支（常规、有序集、旧语法）。
- **必须覆盖参数数据类型**：arg_data_type 是聚合函数身份的关键维度，需至少覆盖 integer、bigint、numeric、float8、text、boolean、date 等代表性类型。
- 有序集聚合的 direct argument 和 ORDER BY argument 类型区分需覆盖。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
- arg_data_type 因子按代表性类型类别覆盖，不做全类型笛卡尔积。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 OR REPLACE 时，需要分别覆盖正常创建、替换语义与约束冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（支持函数创建）、目标 CREATE AGGREGATE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser 的分支，必须在生命周期计划中显式标注环境依赖。
- 支持函数（sfunc、ffunc、combinefunc 等）必须先创建，签名须与聚合参数类型匹配。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限、schema 的分支。
- arg_data_type 因子挂靠到常规聚合和有序集聚合的成功样本，按类型类别轮转注入。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（三种形式）
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 参数数据类型代表性覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - OR REPLACE 行为覆盖
  - PARALLEL 选项覆盖
  - 有序集聚合 direct/aggregated 参数类型覆盖
  - 支持函数依赖覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: aggregate
  skill_name: create_aggregate
  official_source: https://www.postgresql.org/docs/16/sql-createaggregate.html
  statement:
    key: create_aggregate
    name: CREATE AGGREGATE
    aliases:
    - CREATE AGGREGATE
    - create aggregate
    - create_aggregate
    purpose: define a new aggregate function
  syntax_templates:
  - "CREATE [ OR REPLACE ] AGGREGATE name ( [ argmode ] [ argname ] arg_data_type [ , ... ] ) ( SFUNC = sfunc, STYPE = state_data_type [ , ... ] )"
  - "CREATE [ OR REPLACE ] AGGREGATE name ( [ [ argmode ] [ argname ] arg_data_type [ , ... ] ] ORDER BY [ argmode ] [ argname ] arg_data_type [ , ... ] ) ( SFUNC = sfunc, STYPE = state_data_type [ , ... ] )"
  - "CREATE [ OR REPLACE ] AGGREGATE name ( BASETYPE = base_type, SFUNC = sfunc, STYPE = state_data_type [ , ... ] )"
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
    - aggregate_form
    - or_replace_clause
    - parallel_option
    - arg_data_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - aggregate_name_shape
    - argmode_shape
    - argname_shape
    - sfunc_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - support_function_dependency
    - combinefunc_dependency
    - finalfunc_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_aggregate
    - sfunc_signature_mismatch
    - or_replace_constraint_violation
    - invalid_ordered_set_variadic
    - missing_required_sfunc
    - insufficient_privilege
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
      - key: branch_regular
        label: 常规聚合函数 (Form 1)
      - key: branch_ordered_set
        label: 有序集/假设集聚合函数 (Form 2)
      - key: branch_old_syntax
        label: 旧语法 (Form 3)
    object_state:
      label: 目标Aggregate对象存在性
      importance: important
      values:
      - key: not_exists
        label: 聚合函数不存在
      - key: already_exists
        label: 聚合函数已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    aggregate_form:
      label: 聚合函数形态
      importance: important
      values:
      - key: single_arg
        label: 单参数聚合函数
      - key: multi_arg
        label: 多参数聚合函数
      - key: zero_arg
        label: 零参数聚合函数
      - key: ordered_set
        label: 有序集聚合函数
      - key: old_syntax
        label: 旧语法聚合函数
    or_replace_clause:
      label: OR REPLACE子句
      importance: important
      values:
      - key: absent
        label: 不使用OR REPLACE
      - key: present_replace_existing
        label: OR REPLACE替换已存在聚合函数
      - key: present_replace_with_constraint_violation
        label: OR REPLACE违反约束 (改变参数/返回类型) → error
    parallel_option:
      label: PARALLEL选项
      importance: non_important
      values:
      - key: UNSAFE_default
        label: 默认UNSAFE (省略PARALLEL子句)
      - key: SAFE
        label: PARALLEL SAFE
      - key: RESTRICTED
        label: PARALLEL RESTRICTED
    arg_data_type:
      label: 参数数据类型 (聚合函数身份关键维度)
      importance: important
      values:
      - key: integer
        label: integer
      - key: bigint
        label: bigint
      - key: numeric
        label: numeric
      - key: float8
        label: float8 (double precision)
      - key: text
        label: text
      - key: boolean
        label: boolean
      - key: date
        label: date
      - key: timestamp
        label: timestamp
      - key: anyelement
        label: anyelement (多态类型)
      - key: internal
        label: internal (需SERIALFUNC/DESERIALFUNC)
    aggregate_name_shape:
      label: 聚合函数名称形态
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符
      - key: schema_qualified
        label: Schema限定标识符
      - key: reserved_word
        label: 保留字标识符
    argmode_shape:
      label: 参数模式形态
      importance: non_important
      values:
      - key: IN_default
        label: IN (默认，省略)
      - key: IN_explicit
        label: IN (显式)
      - key: VARIADIC
        label: VARIADIC
    argname_shape:
      label: 参数名称形态
      importance: non_important
      values:
      - key: absent
        label: 省略参数名
      - key: plain
        label: 合法普通参数名
      - key: quoted
        label: 双引号参数名
    sfunc_name_shape:
      label: sfunc函数名形态
      importance: non_important
      values:
      - key: plain
        label: 合法普通标识符
      - key: schema_qualified
        label: Schema限定标识符
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: aggregate_owner
        label: 聚合函数创建者
      - key: non_owner
        label: 非 Owner 用户 → 需CREATE权限于schema
    support_function_dependency:
      label: 支持函数依赖
      importance: non_important
      values:
      - key: sfunc_exists
        label: sfunc函数已创建且签名匹配
      - key: sfunc_not_exists
        label: sfunc函数不存在 → error
      - key: sfunc_wrong_signature
        label: sfunc函数存在但签名不匹配 → error
    combinefunc_dependency:
      label: COMBINEFUNC依赖 (仅并行聚合)
      importance: non_important
      values:
      - key: exists
        label: COMBINEFUNC已创建
      - key: not_exists
        label: COMBINEFUNC不存在 → 警告或功能受限
    finalfunc_dependency:
      label: FINALFUNC依赖
      importance: non_important
      values:
      - key: exists
        label: FINALFUNC已创建且签名匹配
      - key: not_exists
        label: FINALFUNC不存在 → 警告或受限
      - key: wrong_return_type
        label: FINALFUNC返回类型不匹配
    duplicate_aggregate:
      label: 重名冲突
      importance: non_important
      values:
      - key: same_name_same_signature
        label: 同名同签名 → error (无OR REPLACE)
      - key: same_name_different_signature
        label: 同名不同签名 → 可创建 (不同聚合函数)
    sfunc_signature_mismatch:
      label: sfunc签名不匹配
      importance: non_important
      values:
      - key: wrong_input_types
        label: sfunc输入参数类型与聚合参数不匹配 → error
      - key: wrong_return_type
        label: sfunc返回类型与STYPE不匹配 → error
    or_replace_constraint_violation:
      label: OR REPLACE约束违反
      importance: non_important
      values:
      - key: changed_arg_types
        label: OR REPLACE改变参数类型 → error
      - key: changed_return_type
        label: OR REPLACE改变返回类型 → error
      - key: changed_kind
        label: OR REPLACE改变聚合种类 → error
    invalid_ordered_set_variadic:
      label: 有序集聚合variadic非法
      importance: non_important
      values:
      - key: non_variadic_any
        label: 有序集聚合使用非VARIADIC "any" → error
    missing_required_sfunc:
      label: 缺失必需sfunc
      importance: non_important
      values:
      - key: sfunc_not_found
        label: sfunc函数不存在 → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_owner_create
        label: 非 Owner 在Schema中创建聚合函数
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_aggregate_catalog_query
        label: pg_aggregate 系统目录查询
      - key: pg_proc_query
        label: pg_proc 系统目录查询
      - key: actual_execution
        label: 实际执行聚合函数验证可用性
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_AGGREGATE
        label: DROP AGGREGATE name (signature)
      - key: DROP_AGGREGATE_IF_EXISTS
        label: DROP AGGREGATE IF EXISTS name (signature)
      - key: DROP_AGGREGATE_CASCADE
        label: DROP AGGREGATE name (signature) CASCADE
  notes:
    three_forms: CREATE AGGREGATE 有三种形式（常规、有序集、旧语法），各自有不同的依赖和约束。
    arg_data_type_identity: arg_data_type 是聚合函数身份的关键组成部分，不同参数类型定义不同的聚合函数。
    sfunc_input_output_types: sfunc 输入类型 = STYPE + arg_data_type(s)，输出类型 = STYPE；这是关键覆盖维度。
    or_replace_constraints: OR REPLACE 不可改变参数类型、返回类型和直接参数数量。
    ordered_set_variadic: 有序集聚合仅允许 VARIADIC "any"。
    parallel_requires_combinefunc: PARALLEL SAFE 需要 COMBINEFUNC；internal 状态还需 SERIALFUNC/DESERIALFUNC。
  defaults:
    expected_status: success
    object_state: not_exists
    aggregate_form: single_arg
    arg_data_type: integer
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - aggregate_form
    - or_replace_clause
    - parallel_option
    - arg_data_type
    - aggregate_name_shape
    - argmode_shape
    - argname_shape
    - sfunc_name_shape
    - privilege_level
    - support_function_dependency
    - combinefunc_dependency
    - finalfunc_dependency
    - duplicate_aggregate
    - sfunc_signature_mismatch
    - or_replace_constraint_violation
    - invalid_ordered_set_variadic
    - missing_required_sfunc
    - insufficient_privilege
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE {or_replace} AGGREGATE {aggregate_name} ( {arg_spec} ) ( SFUNC = {sfunc}, STYPE = {state_data_type} {extra_options} )"
    verification_query_template: "SELECT count(*) FROM pg_aggregate WHERE aggfnoid = '{aggregate_name}'::regproc"
    factor_value_bindings:
      or_replace_clause:
        absent: ""
        present_replace_existing: "OR REPLACE"
      arg_data_type:
        integer: "integer"
        bigint: "bigint"
        numeric: "numeric"
        float8: "float8"
        text: "text"
        boolean: "boolean"
        date: "date"
        timestamp: "timestamp"
        anyelement: "anyelement"
        internal: "internal"
```
