# 技能：CREATE ACCESS METHOD

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-createaccessmethod.html

```sql
CREATE ACCESS METHOD name
    TYPE access_method_type
    HANDLER handler_function
```

**重要行为说明**：
- `access_method_type` 必须为 `INDEX` 或 `TABLE`。
- `handler_function` 必须事先已定义，且返回类型为 `internal`。
- 只有超级用户才能创建新的访问方法。
- 访问方法注册在 `pg_am` 系统目录中。
- CREATE ACCESS METHOD 不涉及表、列或索引类型组合，仅涉及访问方法名称、类型与 handler 函数的绑定。

## 语句作用

官方说明：CREATE ACCESS METHOD — define a new access method

该 reference 关注访问方法注册语句的语法分支、访问方法类型选择、handler 函数依赖与超级用户权限边界，不负责覆盖表/列/索引类型组合。

CREATE ACCESS METHOD **不涉及表/列/索引类型**，具体表现为：
- 语句仅注册访问方法名称与 handler 函数的绑定关系
- TYPE 子句选择 INDEX 或 TABLE，但不生成实际的表或索引对象
- handler 函数依赖是其核心前置条件

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支
- object_state：目标 Access Method 对象存在性（不存在、已存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- access_method_type：访问方法类型（INDEX、TABLE）
- handler_function_state：handler 函数状态（exists、not_exists、wrong_return_type）
- or_replace_support：是否支持 OR REPLACE（不支持）

### T3：对象名与输入形态因子
- am_name_shape：访问方法名称形态（plain_identifier、quoted_identifier、reserved_word、schema_qualified）
- handler_name_shape：handler 函数名称形态（plain_identifier、quoted_identifier）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、non_superuser）
- handler_dependency：handler 函数依赖（handler_exists_returns_internal、handler_exists_wrong_return_type、handler_not_exists）

### T5：异常与边界因子
- duplicate_am_name：重名冲突（with_existing_am、with_builtin_am）
- invalid_access_method_type：非法访问方法类型（unknown_type_value）
- handler_wrong_return_type：handler 函数返回类型错误
- insufficient_privilege：非超级用户创建访问方法

### T6：验证与清理因子
- verification_mode：验证方式（pg_am_catalog_query、pg_am_actual_usage）
- cleanup_mode：清理方式（DROP_ACCESS_METHOD、DROP_ACCESS_METHOD_IF_EXISTS、DROP_ACCESS_METHOD_CASCADE）

## 覆盖策略

- 必须覆盖 CREATE ACCESS METHOD 的唯一语法分支。
- 必须覆盖 INDEX 和 TABLE 两种访问方法类型。
- CREATE ACCESS METHOD 不涉及表/列/索引类型组合，仅涉及访问方法名称、类型与 handler 函数。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（handler 函数创建）、目标 CREATE ACCESS METHOD 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要超级用户权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - INDEX 和 TABLE 类型全覆盖
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 超级用户权限路径全覆盖
- 次优先保证：
  - handler 函数形态代表性覆盖
  - schema 限定名与双引号标识符代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: access_method
  skill_name: create_access_method
  official_source: https://www.postgresql.org/docs/16/sql-createaccessmethod.html
  statement:
    key: create_access_method
    name: CREATE ACCESS METHOD
    aliases:
    - CREATE ACCESS METHOD
    - create access method
    - create_access_method
    purpose: define a new access method
  syntax_templates:
  - "CREATE ACCESS METHOD name TYPE access_method_type HANDLER handler_function"
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
    - access_method_type
    - handler_function_state
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - am_name_shape
    - handler_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - handler_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_am_name
    - invalid_access_method_type
    - handler_wrong_return_type
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
      - key: branch_1
        label: 官方 synopsis 分支 1
    object_state:
      label: 目标Access Method对象存在性
      importance: important
      values:
      - key: not_exists
        label: 访问方法不存在
      - key: already_exists
        label: 访问方法已存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    access_method_type:
      label: 访问方法类型
      importance: important
      values:
      - key: INDEX
        label: 索引访问方法 (TYPE INDEX)
      - key: TABLE
        label: 表访问方法 (TYPE TABLE)
    handler_function_state:
      label: handler函数状态
      importance: important
      values:
      - key: exists
        label: handler函数已定义且返回internal
      - key: not_exists
        label: handler函数不存在
      - key: wrong_return_type
        label: handler函数存在但返回类型错误
    am_name_shape:
      label: 访问方法名称形态
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
    handler_name_shape:
      label: handler函数名称形态
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户 (创建访问方法必需)
      - key: non_superuser
        label: 非超级用户 → error
    handler_dependency:
      label: handler函数依赖
      importance: non_important
      values:
      - key: handler_exists_returns_internal
        label: handler函数已创建且返回internal类型
      - key: handler_exists_wrong_return_type
        label: handler函数已创建但返回类型错误 → error
      - key: handler_not_exists
        label: handler函数不存在 → error
    duplicate_am_name:
      label: 重名冲突
      importance: non_important
      values:
      - key: with_existing_am
        label: 与已存在访问方法同名 → error
      - key: with_builtin_am
        label: 与内置访问方法同名 (如 heap, btree) → error
    invalid_access_method_type:
      label: 非法访问方法类型
      importance: non_important
      values:
      - key: unknown_type_value
        label: TYPE 值不是 INDEX 或 TABLE → error
    handler_wrong_return_type:
      label: handler函数返回类型错误
      importance: non_important
      values:
      - key: returns_non_internal
        label: handler函数返回非internal类型 → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_superuser_create
        label: 非超级用户创建访问方法 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_am_catalog_query
        label: pg_am 系统目录查询
      - key: pg_am_actual_usage
        label: 创建使用该访问方法的索引/表来验证可用性
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_ACCESS_METHOD
        label: DROP ACCESS METHOD name
      - key: DROP_ACCESS_METHOD_IF_EXISTS
        label: DROP ACCESS METHOD IF EXISTS name
      - key: DROP_ACCESS_METHOD_CASCADE
        label: DROP ACCESS METHOD name CASCADE
  notes:
    requires_superuser: CREATE ACCESS METHOD 只有超级用户才能执行。
    no_table_column_index_types: CREATE ACCESS METHOD 不涉及表/列/索引类型组合。
    handler_returns_internal: handler 函数必须返回 internal 类型。
    access_method_types: TYPE 子句值为 INDEX 或 TABLE。
    pg_am_catalog: 访问方法注册在 pg_am 系统目录中。
  defaults:
    expected_status: success
    object_state: not_exists
    access_method_type: INDEX
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - access_method_type
    - handler_function_state
    - am_name_shape
    - handler_name_shape
    - privilege_level
    - handler_dependency
    - duplicate_am_name
    - invalid_access_method_type
    - handler_wrong_return_type
    - insufficient_privilege
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CREATE ACCESS METHOD {am_name} TYPE {access_method_type} HANDLER {handler_function}"
    verification_query_template: "SELECT count(*) FROM pg_am WHERE amname = '{am_name}'"
    factor_value_bindings:
      access_method_type:
        INDEX: "TYPE INDEX"
        TABLE: "TYPE TABLE"
```
