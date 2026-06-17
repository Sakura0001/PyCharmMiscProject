# 技能：CREATE CAST

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createcast.html

### Synopsis 形式 1：WITH FUNCTION

```sql
CREATE CAST (source_type AS target_type)
    WITH FUNCTION function_name [ (argument_type [, ...]) ]
    [ AS ASSIGNMENT | AS IMPLICIT ]
```

### Synopsis 形式 2：WITHOUT FUNCTION

```sql
CREATE CAST (source_type AS target_type)
    WITHOUT FUNCTION
    [ AS ASSIGNMENT | AS IMPLICIT ]
```

### Synopsis 形式 3：WITH INOUT

```sql
CREATE CAST (source_type AS target_type)
    WITH INOUT
    [ AS ASSIGNMENT | AS IMPLICIT ]
```

**重要行为说明**：
- CREATE CAST 有三种形式：WITH FUNCTION、WITHOUT FUNCTION、WITH INOUT。
- `WITHOUT FUNCTION` 表示二进制强制转换（binary-coercible），**需要超级用户权限**（因为错误定义可能导致服务器崩溃）。
- `WITH INOUT` 使用源类型的输出函数和目标类型的输入函数进行转换。
- 默认情况下（无 AS 子句），转换只能通过显式 `CAST(x AS typename)` 或 `x::typename` 调用。
- `AS ASSIGNMENT` 允许在赋值上下文中隐式调用。
- `AS IMPLICIT` 允许在任意上下文中隐式调用（赋值和表达式内部）。
- Cast 实现函数可以有 1-3 个参数：第一个参数必须与 source_type 匹配或二进制兼容；可选第二参数 integer（类型修饰符）；可选第三参数 boolean（显式/隐式标记）。
- 源类型和目标类型通常必须不同，但相同类型允许当实现函数有多个参数时（表示长度强制函数）。
- source_type 和 target_type 是 cast 对象的身份关键组成部分，涉及类型转换覆盖。
- 必须拥有源类型或目标类型，且对另一类型有 USAGE 权限。

## 语句作用

官方说明：CREATE CAST — define a new cast

该 reference 关注类型转换定义语句的语法分支、source_type/target_type 类型选择（类型转换覆盖的核心维度）、转换实现方式和隐式上下文，不负责覆盖所有基表列类型组合。

CREATE CAST **涉及 source_type 和 target_type 数据类型**，具体表现为：
- source_type 和 target_type 是 cast 对象的身份关键组成部分
- 类型转换覆盖需要代表性 source_type → target_type 组合
- 二进制强制转换 (WITHOUT FUNCTION) 和 I/O 转换 (WITH INOUT) 有不同的类型约束

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（with_function、without_function、with_inout）
- object_state：目标 Cast 对象存在性（不存在、已存在_same_direction）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- cast_implementation：转换实现方式（with_function、without_function、with_inout）
- implicit_context：隐式调用上下文（explicit_only_default、as_assignment、as_implicit）
- source_type：源类型数据类型（cast 身份关键维度）
- target_type：目标类型数据类型（cast 身份关键维度）

### T3：对象名与输入形态因子
- source_type_shape：源类型名形态（plain_type、schema_qualified_type、quoted_type）
- target_type_shape：目标类型名形态（plain_type、schema_qualified_type、quoted_type）
- function_name_shape：转换函数名形态（plain_identifier、schema_qualified）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、type_owner_source、type_owner_target、non_owner）
- function_dependency：转换函数依赖（function_exists_correct_signature、function_exists_wrong_signature、function_not_exists）
- type_ownership：类型所有权（owns_source_type、owns_target_type、owns_both、owns_neither）

### T5：异常与边界因子
- duplicate_cast：重名冲突（same_source_target_direction_exists、reverse_direction_exists）
- same_source_and_target：source_type = target_type（仅多参数函数时合法）
- binary_coercible_non_superuser：非超级用户创建 WITHOUT FUNCTION cast → error
- function_signature_mismatch：转换函数签名不匹配
- insufficient_privilege：不拥有源类型或目标类型 → error
- bidirectional_cast：双向 cast 需分别声明

### T6：验证与清理因子
- verification_mode：验证方式（pg_cast_catalog_query、actual_cast_execution）
- cleanup_mode：清理方式（DROP_CAST、DROP_CAST_IF_EXISTS）

## 覆盖策略

- 必须覆盖 CREATE CAST 的三种语法分支（WITH FUNCTION、WITHOUT FUNCTION、WITH INOUT）。
- **必须覆盖 source_type 和 target_type 的代表性类型组合**：这是 cast 对象身份和类型转换行为的核心维度。
- 代表性类型组合应覆盖：integer → bigint、text → integer、numeric → float8、boolean → text、date → timestamp、自定义类型 → text 等。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：source_type/target_type 按代表性类型类别覆盖，不做全类型笛卡尔积。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE CAST 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要超级用户权限的分支（WITHOUT FUNCTION），必须在生命周期计划中显式标注环境依赖。
- source_type 和 target_type 的代表性类型组合必须在至少一个 CREATE CAST 样本中出现。

## 挂靠规则

- source_type/target_type 因子挂靠到各语法分支的代表性成功样本，按类型类别轮转注入。
- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（三种形式）
  - source_type / target_type 代表性类型组合覆盖
  - 隐式调用上下文全覆盖（explicit_only、ASSIGNMENT、IMPLICIT）
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 转换函数依赖覆盖
  - 类型所有权覆盖
  - 二进制强制转换 superuser 限制覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: cast
  skill_name: create_cast
  official_source: https://www.postgresql.org/docs/16/sql-createcast.html
  statement:
    key: create_cast
    name: CREATE CAST
    aliases:
    - CREATE CAST
    - create cast
    - create_cast
    purpose: define a new cast
  syntax_templates:
  - "CREATE CAST (source_type AS target_type) WITH FUNCTION function_name [ (argument_type [, ...]) ] [ AS ASSIGNMENT | AS IMPLICIT ]"
  - "CREATE CAST (source_type AS target_type) WITHOUT FUNCTION [ AS ASSIGNMENT | AS IMPLICIT ]"
  - "CREATE CAST (source_type AS target_type) WITH INOUT [ AS ASSIGNMENT | AS IMPLICIT ]"
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
    - cast_implementation
    - implicit_context
    - source_type
    - target_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - source_type_shape
    - target_type_shape
    - function_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - function_dependency
    - type_ownership
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_cast
    - same_source_and_target
    - binary_coercible_non_superuser
    - function_signature_mismatch
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
      - key: branch_with_function
        label: WITH FUNCTION
      - key: branch_without_function
        label: WITHOUT FUNCTION (binary-coercible)
      - key: branch_with_inout
        label: WITH INOUT (I/O conversion)
    object_state:
      label: 目标Cast对象存在性
      importance: important
      values:
      - key: not_exists
        label: Cast不存在 (同方向)
      - key: already_exists
        label: Cast已存在 (同source→target方向)
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    cast_implementation:
      label: 转换实现方式
      importance: important
      values:
      - key: with_function
        label: WITH FUNCTION (函数实现转换)
      - key: without_function
        label: WITHOUT FUNCTION (二进制强制转换，需superuser)
      - key: with_inout
        label: WITH INOUT (I/O转换)
    implicit_context:
      label: 隐式调用上下文
      importance: important
      values:
      - key: explicit_only_default
        label: 仅显式调用 (默认，无AS子句)
      - key: as_assignment
        label: AS ASSIGNMENT (赋值上下文隐式调用)
      - key: as_implicit
        label: AS IMPLICIT (任意上下文隐式调用)
    source_type:
      label: 源类型 (Cast身份关键维度)
      importance: important
      values:
      - key: integer
        label: integer
      - key: bigint
        label: bigint
      - key: text
        label: text
      - key: numeric
        label: numeric
      - key: boolean
        label: boolean
      - key: date
        label: date
      - key: timestamp
        label: timestamp
      - key: custom_type
        label: 自定义类型 (用户定义)
    target_type:
      label: 目标类型 (Cast身份关键维度)
      importance: important
      values:
      - key: integer
        label: integer
      - key: bigint
        label: bigint
      - key: text
        label: text
      - key: numeric
        label: numeric
      - key: float8
        label: float8 (double precision)
      - key: boolean
        label: boolean
      - key: timestamp
        label: timestamp
      - key: custom_type
        label: 自定义类型 (用户定义)
    source_type_shape:
      label: 源类型名形态
      importance: non_important
      values:
      - key: plain_type
        label: 普通类型名 (如 integer)
      - key: schema_qualified_type
        label: Schema限定类型名
      - key: quoted_type
        label: 双引号类型名
    target_type_shape:
      label: 目标类型名形态
      importance: non_important
      values:
      - key: plain_type
        label: 普通类型名 (如 integer)
      - key: schema_qualified_type
        label: Schema限定类型名
    function_name_shape:
      label: 转换函数名形态 (仅WITH FUNCTION)
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: schema_qualified
        label: Schema限定标识符
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户 (WITHOUT FUNCTION必需)
      - key: type_owner_source
        label: 拥有源类型
      - key: type_owner_target
        label: 拥有目标类型
      - key: non_owner
        label: 不拥有任何类型 → error
    function_dependency:
      label: 转换函数依赖 (仅WITH FUNCTION)
      importance: non_important
      values:
      - key: function_exists_correct_signature
        label: 转换函数已创建且签名匹配
      - key: function_exists_wrong_signature
        label: 转换函数存在但签名不匹配 → error
      - key: function_not_exists
        label: 转换函数不存在 → error
    type_ownership:
      label: 类型所有权
      importance: non_important
      values:
      - key: owns_source_type
        label: 拥有源类型
      - key: owns_target_type
        label: 拥有目标类型
      - key: owns_both
        label: 同时拥有源和目标类型
      - key: owns_neither
        label: 不拥有任何类型 → error
    duplicate_cast:
      label: 重名冲突
      importance: non_important
      values:
      - key: same_source_target_direction
        label: 同source→target方向已存在 → error
      - key: reverse_direction_exists
        label: 反方向cast已存在 (不同对象，可创建)
    same_source_and_target:
      label: 源类型=目标类型
      importance: non_important
      values:
      - key: same_type_multiarg_function
        label: 同类型仅当实现函数有多个参数时合法 (长度强制)
      - key: same_type_no_function
        label: 同类型无多参数函数 → error
    binary_coercible_non_superuser:
      label: 二进制强制转换非superuser
      importance: non_important
      values:
      - key: non_superuser_without_function
        label: 非超级用户创建WITHOUT FUNCTION → error
    function_signature_mismatch:
      label: 转换函数签名不匹配
      importance: non_important
      values:
      - key: wrong_first_arg_type
        label: 函数首参数类型与source_type不匹配 → error
      - key: wrong_return_type
        label: 函数返回类型与target_type不匹配 → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: owns_no_type
        label: 不拥有源类型或目标类型 → error
      - key: no_usage_on_other_type
        label: 对另一类型无USAGE权限 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_cast_catalog_query
        label: pg_cast 系统目录查询
      - key: actual_cast_execution
        label: 实际执行 CAST(source_value AS target_type) 验证
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_CAST
        label: DROP CAST (source_type AS target_type)
      - key: DROP_CAST_IF_EXISTS
        label: DROP CAST IF EXISTS (source_type AS target_type)
  notes:
    three_forms: CREATE CAST 有三种形式（WITH FUNCTION、WITHOUT FUNCTION、WITH INOUT），各自有不同的依赖和约束。
    source_target_type_identity: source_type 和 target_type 是 cast 对象身份的关键组成部分。
    without_function_requires_superuser: WITHOUT FUNCTION (binary-coercible cast) 需要超级用户权限。
    implicit_context_hierarchy: explicit_only < ASSIGNMENT < IMPLICIT，隐式级别越高越容易被自动调用。
    cast_function_1_to_3_args: Cast 实现函数可以有 1-3 个参数。
    same_type_only_multiarg: 源类型=目标类型仅当实现函数有多参数时合法 (长度强制函数)。
    bidirectional_requires_two: 双向类型转换需要分别声明两个 CAST。
  defaults:
    expected_status: success
    object_state: not_exists
    cast_implementation: with_function
    implicit_context: explicit_only_default
    source_type: integer
    target_type: bigint
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - cast_implementation
    - implicit_context
    - source_type
    - target_type
    - source_type_shape
    - target_type_shape
    - function_name_shape
    - privilege_level
    - function_dependency
    - type_ownership
    - duplicate_cast
    - same_source_and_target
    - binary_coercible_non_superuser
    - function_signature_mismatch
    - insufficient_privilege
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE CAST ({source_type} AS {target_type}) {cast_implementation_clause} {implicit_clause}"
    verification_query_template: "SELECT count(*) FROM pg_cast WHERE castsource = '{source_type}'::regtype AND casttarget = '{target_type}'::regtype"
    factor_value_bindings:
      cast_implementation:
        with_function: "WITH FUNCTION {function_name}"
        without_function: "WITHOUT FUNCTION"
        with_inout: "WITH INOUT"
      implicit_context:
        explicit_only_default: ""
        as_assignment: "AS ASSIGNMENT"
        as_implicit: "AS IMPLICIT"
```
