# 技能：ALTER FUNCTION

## 官方语法范围

来源：https://www.postgresql.org/docs/16/sql-alterfunction.html

### Synopsis 形式 1：属性修改 (action)

```sql
ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    action [ ... ] [ RESTRICT ]
```

### Synopsis 形式 2：重命名 (RENAME TO)

```sql
ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    RENAME TO new_name
```

### Synopsis 形式 3：变更 Owner (OWNER TO)

```sql
ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
```

### Synopsis 形式 4：变更 Schema (SET SCHEMA)

```sql
ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    SET SCHEMA new_schema
```

### Synopsis 形式 5：扩展依赖 ([ NO ] DEPENDS ON EXTENSION)

```sql
ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    [ NO ] DEPENDS ON EXTENSION extension_name
```

### action 子句

```sql
    CALLED ON NULL INPUT | RETURNS NULL ON NULL INPUT | STRICT
    IMMUTABLE | STABLE | VOLATILE
    [ NOT ] LEAKPROOF
    [ EXTERNAL ] SECURITY INVOKER | [ EXTERNAL ] SECURITY DEFINER
    PARALLEL { UNSAFE | RESTRICTED | SAFE }
    COST execution_cost
    ROWS result_rows
    SUPPORT support_function
    SET configuration_parameter { TO | = } { value | DEFAULT }
    SET configuration_parameter FROM CURRENT
    RESET configuration_parameter
    RESET ALL
```

## 语句作用

官方说明：ALTER FUNCTION — change the definition of a function

该 reference 关注函数修改语句的五种语法分支、属性变更子句、重命名、Owner 变更、Schema 变更与扩展依赖，以及前置依赖、权限边界与成功/失败路径。

ALTER FUNCTION 不直接涉及列数据类型选择，但参数类型签名（argtype）用于唯一标识目标函数，必须与 CREATE FUNCTION 的 argtype 覆盖协调。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（action属性修改、RENAME TO、OWNER TO、SET SCHEMA、DEPENDS ON EXTENSION）
- object_state：目标函数对象存在性（exists、not_exists、different_signature_exists）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- action_type：action 子句类型（CALLED_ON_NULL_INPUT、RETURNS_NULL_ON_NULL_INPUT、STRICT、IMMUTABLE、STABLE、VOLATILE、LEAKPROOF、NOT_LEAKPROOF、SECURITY_INVOKER、SECURITY_DEFINER、PARALLEL_UNSAFE、PARALLEL_RESTRICTED、PARALLEL_SAFE、COST、ROWS、SUPPORT、SET_parameter、RESET_parameter、RESET_ALL）
- restrict_clause：RESTRICT 子句（present、absent）
- rename_target：重命名目标形态（simple、quoted、reserved_word、duplicate_name）
- owner_target：Owner 目标形态（new_owner_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER、nonexistent_role）
- schema_target：Schema 目标形态（schema_exists、schema_not_exists、pg_catalog_reserved、information_schema_reserved）
- extension_target：扩展目标形态（extension_exists、extension_not_exists、NO_DEPENDS）
- argtype_specification：参数类型签名指定（with_full_signature、with_partial_signature、without_signature）

### T3：对象名与输入形态因子
- function_name_shape：函数名形态（simple、quoted、reserved_word、schema_qualified）
- new_name_shape：新名称形态（simple、quoted、reserved_word）
- configuration_parameter_shape：配置参数形态（valid_parameter、invalid_parameter）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、function_owner、non_owner_with_alter、non_owner_no_privilege）
- schema_dependency：Schema 依赖（target_schema_exists、target_schema_not_exists、reserved_schema）
- role_dependency：角色依赖（owner_role_exists、owner_role_not_exists）
- extension_dependency：扩展依赖（extension_installed、extension_not_installed）

### T5：异常与边界因子
- target_function_not_exists：目标函数不存在
- target_function_different_type：对象类型不匹配（同名但非函数）
- permission_insufficient：权限不足
- conflicting_action：action 冲突或非法组合
- cannot_change_signature：OR REPLACE 改签名边界（仅 CREATE FUNCTION 覆盖）
- identifier_length_exceeded：标识符长度超限

### T6：验证与清理因子
- verification_mode：验证方式（pg_proc_catalog_query、information_schema_routines、pg_get_functiondef）
- cleanup_mode：清理方式（DROP_FUNCTION、DROP_FUNCTION_IF_EXISTS、DROP_FUNCTION_CASCADE）

## 覆盖策略

- 必须覆盖所有五种 ALTER FUNCTION 语法分支。
- 不需要覆盖所有基表列类型；参数类型签名仅用于标识目标函数。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须预创建可被修改的目标函数对象，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标对象存在时的成功修改路径、目标对象不存在时的失败路径。
- RENAME / OWNER / SET SCHEMA / action / DEPENDS ON EXTENSION 等分支需要保持独立归因。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER FUNCTION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 function_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 new_name_shape 挂靠到 RENAME 分支的样本上。
- T3 因子中 configuration_parameter_shape 挂靠到 SET/RESET action 分支的样本上。
- T4 因子仅挂靠到需要依赖对象、权限、schema、extension 或 role 的分支。
- T4 因子中 privilege_level 挂靠到所有分支，确保权限路径被覆盖。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（5种形式）
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的每种 action 类型代表性覆盖
  - RESTRICT 子句代表性覆盖
  - schema、owner、extension 等依赖对象代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - COST / ROWS / SUPPORT 子句
  - SET configuration_parameter 各变体
  - identifier 边界条件

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: function
  skill_name: alter_function
  official_source: https://www.postgresql.org/docs/16/sql-alterfunction.html
  statement:
    key: alter_function
    name: ALTER FUNCTION
    aliases:
    - ALTER FUNCTION
    - alter function
    - alter_function
    purpose: change the definition of a function
  syntax_templates:
  - |
    ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
        action [ ... ] [ RESTRICT ]
  - |
    ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
        RENAME TO new_name
  - |
    ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
        OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
  - |
    ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
        SET SCHEMA new_schema
  - |
    ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
        [ NO ] DEPENDS ON EXTENSION extension_name
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
    - action_type
    - restrict_clause
    - rename_target
    - owner_target
    - schema_target
    - extension_target
    - argtype_specification
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - function_name_shape
    - new_name_shape
    - configuration_parameter_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_dependency
    - role_dependency
    - extension_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - target_function_not_exists
    - target_function_different_type
    - permission_insufficient
    - conflicting_action
    - identifier_length_exceeded
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
        label: 属性修改 (action [ ... ] [ RESTRICT ])
      - key: branch_2
        label: 重命名 (RENAME TO new_name)
      - key: branch_3
        label: 变更 Owner (OWNER TO new_owner)
      - key: branch_4
        label: 变更 Schema (SET SCHEMA new_schema)
      - key: branch_5
        label: 扩展依赖 ([ NO ] DEPENDS ON EXTENSION)
    object_state:
      label: 目标函数对象存在性
      importance: important
      values:
      - key: exists
        label: 函数存在
      - key: not_exists
        label: 函数不存在
      - key: different_signature_exists
        label: 同名不同签名函数存在（签名标识错误）
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    action_type:
      label: action 子句类型
      importance: important
      values:
      - key: CALLED_ON_NULL_INPUT
        label: CALLED ON NULL INPUT
      - key: RETURNS_NULL_ON_NULL_INPUT
        label: RETURNS NULL ON NULL INPUT
      - key: STRICT
        label: STRICT
      - key: IMMUTABLE
        label: IMMUTABLE
      - key: STABLE
        label: STABLE
      - key: VOLATILE
        label: VOLATILE
      - key: LEAKPROOF
        label: LEAKPROOF
      - key: NOT_LEAKPROOF
        label: NOT LEAKPROOF
      - key: SECURITY_INVOKER
        label: SECURITY INVOKER
      - key: SECURITY_DEFINER
        label: SECURITY DEFINER
      - key: PARALLEL_UNSAFE
        label: PARALLEL UNSAFE
      - key: PARALLEL_RESTRICTED
        label: PARALLEL RESTRICTED
      - key: PARALLEL_SAFE
        label: PARALLEL SAFE
      - key: COST
        label: COST execution_cost
      - key: ROWS
        label: ROWS result_rows
      - key: SUPPORT
        label: SUPPORT support_function
      - key: SET_parameter
        label: SET configuration_parameter
      - key: RESET_parameter
        label: RESET configuration_parameter
      - key: RESET_ALL
        label: RESET ALL
    restrict_clause:
      label: RESTRICT 子句
      importance: important
      values:
      - key: present
        label: 包含 RESTRICT
      - key: absent
        label: 不包含 RESTRICT
    rename_target:
      label: 重命名目标形态
      importance: important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: duplicate_name
        label: 已存在函数名（冲突）
    owner_target:
      label: Owner 目标形态
      importance: important
      values:
      - key: new_owner_role
        label: 指定新角色名
      - key: CURRENT_ROLE
        label: CURRENT_ROLE
      - key: CURRENT_USER
        label: CURRENT_USER
      - key: SESSION_USER
        label: SESSION_USER
      - key: nonexistent_role
        label: 不存在的角色（失败路径）
    schema_target:
      label: Schema 目标形态
      importance: important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在（失败路径）
      - key: pg_catalog_reserved
        label: pg_catalog（系统保留）
      - key: information_schema_reserved
        label: information_schema（系统保留）
    extension_target:
      label: 扩展目标形态
      importance: important
      values:
      - key: extension_exists
        label: 扩展已安装
      - key: extension_not_exists
        label: 扩展未安装
      - key: NO_DEPENDS
        label: NO DEPENDS ON EXTENSION（解除依赖）
    argtype_specification:
      label: 参数类型签名指定
      importance: important
      values:
      - key: with_full_signature
        label: 包含完整参数类型签名
      - key: with_partial_signature
        label: 部分参数类型签名（错误）
      - key: without_signature
        label: 无参数类型签名（仅适用于唯一函数名）
    function_name_shape:
      label: 函数名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: schema_qualified
        label: Schema 限定标识符
    new_name_shape:
      label: 新名称形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
    configuration_parameter_shape:
      label: 配置参数形态
      importance: non_important
      values:
      - key: valid_parameter
        label: 有效配置参数名
      - key: invalid_parameter
        label: 无效配置参数名
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: function_owner
        label: 函数 Owner
      - key: non_owner_with_alter
        label: 非Owner但有ALTER权限
      - key: non_owner_no_privilege
        label: 非Owner且无权限
    schema_dependency:
      label: Schema 依赖
      importance: non_important
      values:
      - key: target_schema_exists
        label: 目标Schema存在
      - key: target_schema_not_exists
        label: 目标Schema不存在
      - key: reserved_schema
        label: 系统保留Schema
    role_dependency:
      label: 角色依赖
      importance: non_important
      values:
      - key: owner_role_exists
        label: Owner角色存在
      - key: owner_role_not_exists
        label: Owner角色不存在
    extension_dependency:
      label: 扩展依赖
      importance: non_important
      values:
      - key: extension_installed
        label: 扩展已安装
      - key: extension_not_installed
        label: 扩展未安装
    target_function_not_exists:
      label: 目标函数不存在
      importance: non_important
      values:
      - key: function_name_not_found
        label: 函数名不存在
      - key: function_signature_not_found
        label: 函数名存在但签名不匹配
    target_function_different_type:
      label: 对象类型不匹配
      importance: non_important
      values:
      - key: same_name_is_aggregate
        label: 同名对象是聚合函数
      - key: same_name_is_procedure
        label: 同名对象是过程
    permission_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: no_alter_privilege
        label: 无ALTER权限
      - key: not_owner_for_OWNER_TO
        label: 非Owner无法变更Owner
      - key: not_owner_for_SET_SCHEMA
        label: 非Owner无法变更Schema
    conflicting_action:
      label: action 冲突
      importance: non_important
      values:
      - key: multiple_conflicting_volatility
        label: 同时指定IMMUTABLE和VOLATILE
    identifier_length_exceeded:
      label: 标识符长度超限
      importance: non_important
      values:
      - key: over_63_chars
        label: 标识符超过63字符
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_proc_catalog_query
        label: pg_proc 系统目录查询
      - key: information_schema_routines
        label: information_schema.routines 查询
      - key: pg_get_functiondef
        label: pg_get_functiondef() 查询
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_FUNCTION
        label: DROP FUNCTION name(types)
      - key: DROP_FUNCTION_IF_EXISTS
        label: DROP FUNCTION IF EXISTS name(types)
      - key: DROP_FUNCTION_CASCADE
        label: DROP FUNCTION name(types) CASCADE
  defaults:
    expected_status: success
    object_state: exists
    restrict_clause: absent
    argtype_specification: with_full_signature
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - expected_status
    non_main_factors:
    - action_type
    - restrict_clause
    - rename_target
    - owner_target
    - schema_target
    - extension_target
    - argtype_specification
    - function_name_shape
    - new_name_shape
    - configuration_parameter_shape
    - privilege_level
    - schema_dependency
    - role_dependency
    - extension_dependency
    - target_function_not_exists
    - target_function_different_type
    - permission_insufficient
    - conflicting_action
    - identifier_length_exceeded
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
  rendering:
    statement_template: "ALTER FUNCTION name ( argtypes ) action [ RESTRICT ]"
    verification_query_template: "SELECT provolatile FROM pg_proc WHERE proname = '{function_name}'"
    factor_value_bindings:
      restrict_clause:
        present: "RESTRICT"
        absent: ""
      owner_target:
        new_owner_role: "new_owner"
        CURRENT_ROLE: "CURRENT_ROLE"
        CURRENT_USER: "CURRENT_USER"
        SESSION_USER: "SESSION_USER"
        nonexistent_role: "nonexistent_role"
```
```