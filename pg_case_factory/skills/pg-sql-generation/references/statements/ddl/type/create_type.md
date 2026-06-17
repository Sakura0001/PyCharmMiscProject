# 技能：CREATE TYPE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createtype.html

### Synopsis 形式 1：复合类型 (Composite Type)

```sql
CREATE TYPE name AS
    ( [ attribute_name data_type [ COLLATE collation ] [, ... ] ] )
```

### Synopsis 形式 2：枚举类型 (Enum Type)

```sql
CREATE TYPE name AS ENUM
    ( [ 'label' [, ... ] ] )
```

### Synopsis 形式 3：范围类型 (Range Type)

```sql
CREATE TYPE name AS RANGE (
    SUBTYPE = subtype
    [ , SUBTYPE_OPCLASS = subtype_operator_class ]
    [ , COLLATION = collation ]
    [ , CANONICAL = canonical_function ]
    [ , SUBTYPE_DIFF = subtype_diff_function ]
    [ , MULTIRANGE_TYPE_NAME = multirange_type_name ]
)
```

### Synopsis 形式 4：基础类型 (Base Type)

```sql
CREATE TYPE name (
    INPUT = input_function,
    OUTPUT = output_function
    [ , RECEIVE = receive_function ]
    [ , SEND = send_function ]
    [ , TYPMOD_IN = type_modifier_input_function ]
    [ , TYPMOD_OUT = type_modifier_output_function ]
    [ , ANALYZE = analyze_function ]
    [ , SUBSCRIPT = subscript_function ]
    [ , INTERNALLENGTH = { internallength | VARIABLE } ]
    [ , PASSEDBYVALUE ]
    [ , ALIGNMENT = alignment ]
    [ , STORAGE = storage ]
    [ , LIKE = like_type ]
    [ , CATEGORY = category ]
    [ , PREFERRED = preferred ]
    [ , DEFAULT = default ]
    [ , ELEMENT = element ]
    [ , DELIMITER = delimiter ]
    [ , COLLATABLE = collatable ]
)
```

### Synopsis 形式 5：Shell 类型 (Shell Type)

```sql
CREATE TYPE name
```

**重要行为说明**：
- CREATE TYPE 有五种形式：复合类型、枚举类型、范围类型、基础类型、Shell 类型。
- 复合类型的属性需要 USAGE 权限于所有属性数据类型；零属性允许（PostgreSQL 特有）。
- 枚举类型的标签长度须小于 NAMEDATALEN（标准构建为 64 字节）；零标签允许但类型无法持值（需 ALTER TYPE ADD VALUE 补充）。
- 范围类型的 subtype 必须有 b-tree 操作符类；canonical 和 subtype_diff 函数需要先创建 Shell 类型。
- 基础类型的 INPUT/OUTPUT 函数是必需的，其余可选；需要超级用户权限（错误定义可能导致服务器崩溃）；参数可以任意顺序出现。
- Shell 类型是占位符，仅含名称和 Owner；用于范围类型和基础类型的前向引用；同名的完整定义会自动替换 Shell 类型。
- PostgreSQL 自动创建关联数组类型（`_typename`）。
- 避免以 `_` 开头的类型/表名，以防与自动生成的数组类型混淆。
- 复合类型形式符合 SQL 标准；其余形式均为 PostgreSQL 扩展。

## 语句作用

官方说明：CREATE TYPE — define a new data type

该 reference 关注类型定义语句的语法分支、类型形式（复合、枚举、范围、基础、Shell）、属性类型选择、依赖环境与权限边界，不负责包装所有样本到统一外层事务。

CREATE TYPE **涉及类型定义**，具体表现为：
- 复合类型的属性数据类型选择（attribute data_type）
- 枚举类型的标签值定义
- 范围类型的 subtype 及操作符类选择
- 基础类型的 I/O 函数及其他属性定义
- Shell 类型仅创建名称占位符

五种形式各自有不同的依赖和约束，需要分别覆盖。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（composite、enum、range、base、shell）
- object_state：目标 Type 对象存在性（不存在、已存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- type_form：类型形式（composite、enum、range、base、shell）
- attribute_count：属性数量（zero_attributes、single_attribute、multiple_attributes）— 仅复合类型
- enum_label_count：标签数量（zero_labels、single_label、multiple_labels）— 仅枚举类型
- range_subtype：范围 subtype 选择（smallint、integer、bigint、numeric、float8、timestamp、timestamptz、date）— 仅范围类型
- base_type_io_functions：基础类型 I/O 函数（with_shell_type_first、without_shell_type）— 仅基础类型

### T3：对象名与输入形态因子
- type_name_shape：类型名形态（simple、quoted、reserved_word、underscore_prefix、schema_qualified）
- attribute_name_shape：属性名形态（simple、quoted、reserved_word）— 仅复合类型
- attribute_data_type：属性数据类型— 仅复合类型
- enum_label_shape：标签形态（simple_label、quoted_label、long_label）— 仅枚举类型
- range_option_completeness：范围选项完整性（minimal、with_opclass、with_canonical、with_subtype_diff、with_multirange_name）— 仅范围类型
- base_type_option_completeness：基础类型选项完整性（required_only、with_optional_functions、with_all_options）— 仅基础类型

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、type_owner、non_owner）
- function_dependency：函数依赖（input_output_functions_exist、input_output_functions_not_exist）— 仅基础类型
- subtype_opclass_dependency：subtype 操作符类依赖（opclass_exists、opclass_not_exists）— 仅范围类型
- canonical_function_dependency：canonical 函数依赖（function_exists、function_not_exists）— 仅范围类型
- subtype_diff_dependency：subtype_diff 函数依赖（function_exists、function_not_exists）— 仅范围类型
- shell_type_dependency：Shell 类型依赖（shell_type_exists、shell_type_not_exists）— 仅基础/范围类型
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists）

### T5：异常与边界因子
- duplicate_type_name：重名冲突（with_existing_type、with_existing_table）
- zero_attributes_composite：零属性复合类型（合法但罕见）
- zero_labels_enum：零标签枚举类型（合法但无法持值）
- invalid_data_type_in_attribute：无效属性数据类型
- invalid_enum_label：无效标签（超长标签）
- missing_required_functions：缺失必需 I/O 函数（仅基础类型）
- insufficient_privilege：权限不足（非 superuser 创建基础类型）
- underscore_prefix_name：下划线前缀名称（与自动数组类型冲突风险）
- subtype_no_btree_opclass：subtype 无 b-tree 操作符类（仅范围类型）

### T6：验证与清理因子
- verification_mode：验证方式（pg_type_catalog_query、information_schema_user_defined_types、SELECT_type_query）
- cleanup_mode：清理方式（DROP_TYPE、DROP_TYPE_IF_EXISTS、DROP_TYPE_CASCADE）

## 覆盖策略

- 必须覆盖所有五种 CREATE TYPE 语法分支（composite、enum、range、base、shell）。
- **必须覆盖类型定义形式**：CREATE TYPE 是类型定义的核心语句，复合类型的属性数据类型、枚举类型的标签值、范围类型的 subtype 选择必须至少有一个代表性覆盖。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- attribute_data_type 因子（T3）按数据类型类别做代表性覆盖，每个类别至少一个类型。
- T3 其余因子、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE TYPE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- **类型定义与属性数据类型必须参与生成**：复合类型的属性数据类型必须在至少一个 CREATE TYPE 样本中出现。
- 枚举类型的标签值、范围类型的 subtype 选择必须在至少一个 CREATE TYPE 样本中出现。
- 基础类型需要先创建 Shell 类型与 I/O 函数，必须在生命周期计划中显式标注环境依赖（需要 superuser）。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 attribute_data_type 挂靠到复合类型分支的代表性成功样本，按数据类型类别轮转注入属性定义。
- T3 因子中 type_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 enum_label_shape 挂靠到枚举类型分支的代表性样本。
- T3 因子中 range_option_completeness 挂靠到范围类型分支的代表性样本。
- T3 因子中 base_type_option_completeness 挂靠到基础类型分支的代表性样本。
- T4 因子仅挂靠到需要依赖对象、权限、Schema 或函数对象的分支。
- T4 因子中 function_dependency 挂靠到基础类型分支。
- T4 因子中 shell_type_dependency 挂靠到基础/范围类型分支。
- T4 因子中 subtype_opclass_dependency 挂靠到范围类型分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（五种形式）
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 复合类型属性数据类型类别代表性覆盖
  - 枚举类型标签值代表性覆盖
  - 范围类型 subtype 代表性覆盖
  - 基础类型 I/O 函数依赖覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - 基础类型可选参数（RECEIVE、SEND 等）
  - 范围类型可选参数（CANONICAL、SUBTYPE_DIFF 等）
  - 标识符边界条件

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: type
  skill_name: create_type
  official_source: https://www.postgresql.org/docs/16/sql-createtype.html
  statement:
    key: create_type
    name: CREATE TYPE
    aliases:
    - CREATE TYPE
    - create type
    - create_type
    purpose: define a new data type
  syntax_templates:
  - "CREATE TYPE name AS ( [ attribute_name data_type [ COLLATE collation ] [, ... ] ] )"
  - "CREATE TYPE name AS ENUM ( [ 'label' [, ... ] ] )"
  - "CREATE TYPE name AS RANGE ( SUBTYPE = subtype [ , ... ] )"
  - "CREATE TYPE name ( INPUT = input_function, OUTPUT = output_function [ , ... ] )"
  - "CREATE TYPE name"
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
    - type_form
    - attribute_count
    - enum_label_count
    - range_subtype
    - base_type_io_functions
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - type_name_shape
    - attribute_name_shape
    - attribute_data_type
    - enum_label_shape
    - range_option_completeness
    - base_type_option_completeness
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - function_dependency
    - subtype_opclass_dependency
    - canonical_function_dependency
    - subtype_diff_dependency
    - shell_type_dependency
    - schema_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_type_name
    - zero_attributes_composite
    - zero_labels_enum
    - invalid_data_type_in_attribute
    - invalid_enum_label
    - missing_required_functions
    - insufficient_privilege
    - underscore_prefix_name
    - subtype_no_btree_opclass
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
      - key: branch_composite
        label: 复合类型 (CREATE TYPE name AS (...))
      - key: branch_enum
        label: 枚举类型 (CREATE TYPE name AS ENUM (...))
      - key: branch_range
        label: 范围类型 (CREATE TYPE name AS RANGE (...))
      - key: branch_base
        label: 基础类型 (CREATE TYPE name (INPUT=..., OUTPUT=...))
      - key: branch_shell
        label: Shell 类型 (CREATE TYPE name)
    object_state:
      label: 目标Type对象存在性
      importance: important
      values:
      - key: not_exists
        label: 类型不存在
      - key: already_exists
        label: 类型已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    type_form:
      label: 类型形式
      importance: important
      values:
      - key: composite
        label: 复合类型
      - key: enum
        label: 枚举类型
      - key: range
        label: 范围类型
      - key: base
        label: 基础类型
      - key: shell
        label: Shell 类型 (占位符)
    attribute_count:
      label: 属性数量 (仅复合类型)
      importance: important
      values:
      - key: zero_attributes
        label: 零属性 (合法但罕见)
      - key: single_attribute
        label: 单属性
      - key: multiple_attributes
        label: 多属性
    enum_label_count:
      label: 标签数量 (仅枚举类型)
      importance: important
      values:
      - key: zero_labels
        label: 零标签 (合法但无法持值)
      - key: single_label
        label: 单标签
      - key: multiple_labels
        label: 多标签
    range_subtype:
      label: 范围subtype (仅范围类型)
      importance: important
      values:
      - key: integer
        label: int4 (整数范围)
      - key: bigint
        label: int8 (大整数范围)
      - key: numeric
        label: numeric (数值范围)
      - key: float8
        label: float8 (浮点范围)
      - key: timestamp
        label: timestamp (时间戳范围)
      - key: timestamptz
        label: timestamptz (带时区时间戳范围)
      - key: date
        label: date (日期范围)
    base_type_io_functions:
      label: 基础类型I/O函数 (仅基础类型)
      importance: important
      values:
      - key: with_shell_type_first
        label: 先创建Shell类型再定义I/O函数
      - key: without_shell_type
        label: 无Shell类型前置 (依赖隐式创建)
    type_name_shape:
      label: 类型名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: underscore_prefix
        label: 下划线前缀标识符 (与数组类型冲突风险)
      - key: schema_qualified
        label: Schema限定标识符
    attribute_name_shape:
      label: 属性名形态 (仅复合类型)
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
    attribute_data_type:
      label: 属性数据类型 (仅复合类型)
      importance: important
      values:
      - key: integer
        label: integer
      - key: bigint
        label: bigint
      - key: text
        label: text
      - key: varchar
        label: character varying
      - key: numeric
        label: numeric
      - key: boolean
        label: boolean
      - key: date
        label: date
      - key: timestamp
        label: timestamp
      - key: jsonb
        label: jsonb
      - key: uuid
        label: uuid
    enum_label_shape:
      label: 标签形态 (仅枚举类型)
      importance: non_important
      values:
      - key: simple_label
        label: 简单合法标签
      - key: quoted_label
        label: 需引号标签
      - key: long_label
        label: 长标签 (接近NAMEDATALEN上限)
    range_option_completeness:
      label: 范围选项完整性 (仅范围类型)
      importance: non_important
      values:
      - key: minimal
        label: 仅SUBTYPE (最小定义)
      - key: with_opclass
        label: SUBTYPE + SUBTYPE_OPCLASS
      - key: with_canonical
        label: SUBTYPE + CANONICAL
      - key: with_subtype_diff
        label: SUBTYPE + SUBTYPE_DIFF
      - key: with_multirange_name
        label: SUBTYPE + MULTIRANGE_TYPE_NAME
    base_type_option_completeness:
      label: 基础类型选项完整性 (仅基础类型)
      importance: non_important
      values:
      - key: required_only
        label: 仅INPUT+OUTPUT (最小定义)
      - key: with_optional_functions
        label: 包含RECEIVE/SEND等可选函数
      - key: with_all_options
        label: 包含所有可选参数
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户 (基础类型必需)
      - key: type_owner
        label: 类型创建者
      - key: non_owner
        label: 非 Owner 用户
    function_dependency:
      label: 函数依赖 (仅基础类型)
      importance: non_important
      values:
      - key: input_output_functions_exist
        label: I/O函数已创建
      - key: input_output_functions_not_exist
        label: I/O函数不存在 → error
    subtype_opclass_dependency:
      label: subtype操作符类依赖 (仅范围类型)
      importance: non_important
      values:
      - key: opclass_exists
        label: b-tree操作符类已存在
      - key: opclass_not_exists
        label: b-tree操作符类不存在 → error
    canonical_function_dependency:
      label: canonical函数依赖 (仅范围类型)
      importance: non_important
      values:
      - key: function_exists
        label: canonical函数已创建
      - key: function_not_exists
        label: canonical函数不存在 → error
    subtype_diff_dependency:
      label: subtype_diff函数依赖 (仅范围类型)
      importance: non_important
      values:
      - key: function_exists
        label: subtype_diff函数已创建
      - key: function_not_exists
        label: subtype_diff函数不存在
    shell_type_dependency:
      label: Shell类型依赖 (仅基础/范围类型)
      importance: non_important
      values:
      - key: shell_type_exists
        label: Shell类型已创建
      - key: shell_type_not_exists
        label: Shell类型不存在
    schema_dependency:
      label: Schema依赖
      importance: non_important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在
    duplicate_type_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: with_existing_type
        label: 与已存在类型同名 → error
      - key: with_existing_table
        label: 与已存在表同名 → error
    zero_attributes_composite:
      label: 零属性复合类型
      importance: non_important
      values:
      - key: valid_but_unusual
        label: 零属性复合类型 (合法但罕见)
    zero_labels_enum:
      label: 零标签枚举类型
      importance: non_important
      values:
      - key: valid_but_unusable
        label: 零标签枚举类型 (合法但无法持值)
    invalid_data_type_in_attribute:
      label: 无效属性数据类型
      importance: non_important
      values:
      - key: unknown_type
        label: 属性引用未知类型 → error
    invalid_enum_label:
      label: 无效标签
      importance: non_important
      values:
      - key: too_long_label
        label: 标签超过NAMEDATALEN → error
    missing_required_functions:
      label: 缺失必需I/O函数
      importance: non_important
      values:
      - key: no_input_function
        label: 无INPUT函数 → error
      - key: no_output_function
        label: 无OUTPUT函数 → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_superuser_base_type
        label: 非超级用户创建基础类型 → error
      - key: non_owner_create
        label: 非 Owner 在Schema中创建类型
    underscore_prefix_name:
      label: 下划线前缀名称
      importance: non_important
      values:
      - key: underscore_prefix_conflict
        label: 类型名以_开头 (与数组类型冲突风险)
    subtype_no_btree_opclass:
      label: subtype无b-tree操作符类
      importance: non_important
      values:
      - key: no_opclass
        label: subtype无b-tree操作符类 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_type_catalog_query
        label: pg_type 系统目录查询
      - key: information_schema_user_defined_types
        label: information_schema.user_defined_types 查询
      - key: SELECT_type_query
        label: SELECT 类型表达式验证
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_TYPE
        label: DROP TYPE type_name
      - key: DROP_TYPE_IF_EXISTS
        label: DROP TYPE IF EXISTS type_name
      - key: DROP_TYPE_CASCADE
        label: DROP TYPE type_name CASCADE
  notes:
    type_definition_forms: CREATE TYPE 有五种形式（复合、枚举、范围、基础、Shell），各自有不同的依赖和约束。
    composite_attribute_types: 复合类型的属性需要指定数据类型，需要覆盖代表性数据类型。
    enum_labels: 枚举类型的标签值是类型定义的核心组成部分。
    range_subtype: 范围类型的 subtype 选择决定范围的语义和行为。
    base_type_requires_superuser: 基础类型创建需要超级用户权限。
    shell_type_forward_reference: 范围类型和基础类型通常需要先创建 Shell 类型作为前向引用。
    auto_array_type: PostgreSQL 自动创建关联数组类型，避免以 _ 开头的类型名。
  defaults:
    expected_status: success
    type_form: composite
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - type_form
    - attribute_count
    - enum_label_count
    - range_subtype
    - base_type_io_functions
    - type_name_shape
    - attribute_name_shape
    - attribute_data_type
    - enum_label_shape
    - range_option_completeness
    - base_type_option_completeness
    - privilege_level
    - function_dependency
    - subtype_opclass_dependency
    - canonical_function_dependency
    - subtype_diff_dependency
    - shell_type_dependency
    - schema_dependency
    - duplicate_type_name
    - zero_attributes_composite
    - zero_labels_enum
    - invalid_data_type_in_attribute
    - invalid_enum_label
    - missing_required_functions
    - insufficient_privilege
    - underscore_prefix_name
    - subtype_no_btree_opclass
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE TYPE {type_name} [ AS ( attribute_definitions ) | AS ENUM ( labels ) | AS RANGE ( range_options ) | ( base_type_options ) ]"
    verification_query_template: "SELECT count(*) FROM pg_type WHERE typname = '{type_name}'"
    factor_value_bindings:
      type_form:
        composite: "AS"
        enum: "AS ENUM"
        range: "AS RANGE"
        base: "(INPUT=..., OUTPUT=...)"
        shell: ""
```
