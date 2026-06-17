# 技能：CREATE PROCEDURE

## 官方语法范围

来源：https://www.postgresql.org/docs/16/sql-createprocedure.html

### Synopsis

```sql
CREATE [ OR REPLACE ] PROCEDURE
    name ( [ [ argmode ] [ argname ] argtype [ { DEFAULT | = } default_expr ] [, ...] ] )
  { LANGUAGE lang_name
    | TRANSFORM { FOR TYPE type_name } [, ... ]
    | [ EXTERNAL ] SECURITY INVOKER | [ EXTERNAL ] SECURITY DEFINER
    | SET configuration_parameter { TO value | = value | FROM CURRENT }
    | AS 'definition'
    | AS 'obj_file', 'link_symbol'
    | sql_body
  } ...
```

## 语句作用

官方说明：CREATE PROCEDURE — define a new procedure

该 reference 关注过程定义语句的语法分支、参数数据类型选择、语言与属性子句、依赖环境与权限边界。

CREATE PROCEDURE 是 PostgreSQL 中涉及参数数据类型的核心 DDL 语句之一。参数类型（argtype）覆盖是本 skill 的核心职责。与 CREATE FUNCTION 的关键差异：PROCEDURE 不支持 RETURNS、WINDOW、IMMUTABLE/STABLE/VOLATILE、LEAKPROOF、PARALLEL、COST/ROWS/SUPPORT 等子句。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（单一语法形式，但 sql_body 形式不同）
- object_state：目标过程对象存在性（不存在、已存在同名同参数签名、已存在同名不同参数签名）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- or_replace_clause：OR REPLACE 子句（present、absent）
- language_clause：LANGUAGE 子句（sql、plpgsql、c、internal、other）
- security_clause：安全子句（SECURITY_INVOKER、SECURITY_DEFINER、absent）
- transform_clause：TRANSFORM 子句（present、absent）
- sql_body_form：过程体形式（sql_body_inline、AS_definition、AS_obj_file_link_symbol）
- set_clause：SET configuration_parameter 子句（present、absent）

### T3：对象名与输入形态因子
- procedure_name_shape：过程名形态（simple、quoted、reserved_word、schema_qualified、duplicate）
- argmode：参数模式（IN、OUT、INOUT、VARIADIC、absent）
- argname：参数名形态（with_argname、without_argname）
- argtype：参数数据类型（重要！完整枚举见下方 factors 定义）
- default_expr_shape：默认值形态（with_DEFAULT、with_equals、without_DEFAULT）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、procedure_owner、non_owner_with_create、non_owner_no_privilege）
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists、pg_catalog_reserved、information_schema_reserved）
- role_dependency：角色依赖（owner_role_exists、owner_role_not_exists）
- language_dependency：语言依赖（language_installed_sql、language_installed_plpgsql、language_not_installed）

### T5：异常与边界因子
- duplicate_procedure_signature：重名冲突（with_OR_REPLACE_replace、without_OR_REPLACE_error）
- invalid_argtype：无效参数类型
- conflicting_name_with_function：同名同签名函数冲突
- permission_insufficient：权限不足
- language_not_available：语言不可用
- identifier_length_exceeded：标识符长度超限

### T6：验证与清理因子
- verification_mode：验证方式（pg_proc_catalog_query、information_schema_routines、CALL_procedure_execution、pg_get_functiondef）
- cleanup_mode：清理方式（DROP_PROCEDURE、DROP_PROCEDURE_IF_EXISTS、DROP_PROCEDURE_CASCADE）

## 覆盖策略

- 必须覆盖所有 CREATE PROCEDURE 语法分支。
- **必须覆盖参数数据类型：CREATE PROCEDURE 是参数数据类型选择的核心语句，argtype 中所有 PostgreSQL 16 支持的常用数据类型类别必须至少有一个代表性参数定义。**
- 必须覆盖所有过程体形式（sql_body_inline、AS_definition、AS_obj_file_link_symbol）。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- argtype 因子（T3）按数据类型类别做代表性覆盖，每个类别至少一个类型，常用类型（integer、varchar、boolean 等）做完整覆盖。
- T3 其余因子、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。参数数据类型覆盖不得被裁剪至零——每个类别至少保留一个代表。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 OR REPLACE 时，需要分别覆盖正常创建、替换语义与签名冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 CREATE PROCEDURE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- **参数数据类型必须参与生成：每个 argtype 类别必须在至少一个 CREATE PROCEDURE 样本的参数定义中出现。**
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 argtype 挂靠到代表性成功样本，按数据类型类别轮转注入参数定义。
- T3 因子中 procedure_name_shape、argmode、argname、default_expr_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象、权限、schema、language 的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在 / 冲突 / 非法输入全覆盖
  - 成功 / 失败路径全覆盖
  - 参数数据类型各类别至少一个代表性类型全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - 所有过程体形式代表性覆盖
  - schema、owner、language 等依赖对象代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - TRANSFORM 子句
  - SET configuration_parameter 子句
  - identifier 边界条件

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: procedure
  skill_name: create_procedure
  official_source: https://www.postgresql.org/docs/16/sql-createprocedure.html
  statement:
    key: create_procedure
    name: CREATE PROCEDURE
    aliases:
    - CREATE PROCEDURE
    - create procedure
    - create_procedure
    purpose: define a new procedure
  syntax_templates:
  - |
    CREATE [ OR REPLACE ] PROCEDURE
        name ( [ [ argmode ] [ argname ] argtype [ { DEFAULT | = } default_expr ] [, ...] ] )
      { LANGUAGE lang_name
        | TRANSFORM { FOR TYPE type_name } [, ... ]
        | [ EXTERNAL ] SECURITY INVOKER | [ EXTERNAL ] SECURITY DEFINER
        | SET configuration_parameter { TO value | = value | FROM CURRENT }
        | AS 'definition'
        | AS 'obj_file', 'link_symbol'
        | sql_body
      } ...
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
    - language_clause
    - security_clause
    - transform_clause
    - sql_body_form
    - set_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - procedure_name_shape
    - argmode
    - argname
    - argtype
    - default_expr_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - schema_dependency
    - role_dependency
    - language_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_procedure_signature
    - invalid_argtype
    - conflicting_name_with_function
    - permission_insufficient
    - language_not_available
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
        label: 基础过程定义 (单一 synopsis)
    object_state:
      label: 目标过程对象存在性
      importance: important
      values:
      - key: not_exists
        label: 过程不存在
      - key: already_exists_same_signature
        label: 过程已存在且参数签名相同
      - key: already_exists_different_signature
        label: 过程已存在但参数签名不同（合法重载）
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    or_replace_clause:
      label: OR REPLACE 子句
      importance: important
      values:
      - key: present
        label: 包含 OR REPLACE
      - key: absent
        label: 不包含 OR REPLACE
    language_clause:
      label: LANGUAGE 子句
      importance: important
      values:
      - key: sql
        label: LANGUAGE sql
      - key: plpgsql
        label: LANGUAGE plpgsql
      - key: c
        label: LANGUAGE c
      - key: internal
        label: LANGUAGE internal
      - key: other
        label: 其他已安装语言
    security_clause:
      label: 安全子句
      importance: important
      values:
      - key: SECURITY_INVOKER
        label: SECURITY INVOKER
      - key: SECURITY_DEFINER
        label: SECURITY DEFINER
      - key: absent
        label: 无安全子句（默认 SECURITY INVOKER）
    transform_clause:
      label: TRANSFORM 子句
      importance: important
      values:
      - key: present
        label: 包含 TRANSFORM FOR TYPE
      - key: absent
        label: 不包含 TRANSFORM
    sql_body_form:
      label: 过程体形式
      importance: important
      values:
      - key: sql_body_inline
        label: SQL 过程体内联
      - key: AS_definition
        label: AS 'definition' 字符串体
      - key: AS_obj_file_link_symbol
        label: AS 'obj_file', 'link_symbol' C 过程体
    set_clause:
      label: SET configuration_parameter 子句
      importance: important
      values:
      - key: present
        label: 包含 SET configuration_parameter
      - key: absent
        label: 不包含 SET 子句
    procedure_name_shape:
      label: 过程名形态
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
      - key: duplicate
        label: 已存在过程名
    argmode:
      label: 参数模式
      importance: non_important
      values:
      - key: IN
        label: IN 参数
      - key: OUT
        label: OUT 参数
      - key: INOUT
        label: INOUT 参数
      - key: VARIADIC
        label: VARIADIC 参数
      - key: absent
        label: 无显式参数模式（默认 IN）
    argname:
      label: 参数名
      importance: non_important
      values:
      - key: with_argname
        label: 包含参数名
      - key: without_argname
        label: 不包含参数名
    argtype:
      label: 参数数据类型
      importance: important
      values:
      # --- 整数类型 ---
      - key: smallint
        label: smallint (2字节整数)
      - key: integer
        label: integer / int (4字节整数)
      - key: bigint
        label: bigint (8字节整数)
      # --- 浮点类型 ---
      - key: real
        label: real (4字节浮点)
      - key: double_precision
        label: double precision (8字节浮点)
      # --- 精确数值类型 ---
      - key: numeric
        label: numeric (可变精度)
      # --- 字符类型 ---
      - key: character_varying
        label: character varying / varchar (可变长度字符串)
      - key: character
        label: character / char (定长字符串)
      - key: text
        label: text (可变长度无限制字符串)
      # --- 二进制类型 ---
      - key: bytea
        label: bytea (二进制数据)
      # --- 日期时间类型 ---
      - key: date
        label: date (日期)
      - key: timestamp
        label: timestamp (无时区时间戳)
      - key: timestamp_with_time_zone
        label: timestamp with time zone / timestamptz
      - key: interval
        label: interval (时间间隔)
      # --- 布尔类型 ---
      - key: boolean
        label: boolean / bool (布尔值)
      # --- JSON 类型 ---
      - key: json
        label: json (JSON数据文本存储)
      - key: jsonb
        label: jsonb (JSON数据二进制存储)
      # --- UUID 类型 ---
      - key: uuid
        label: uuid (通用唯一标识符)
      # --- 数组类型 ---
      - key: integer_array
        label: integer[] (整数数组)
      - key: text_array
        label: text[] (文本数组)
      # --- 范围类型 ---
      - key: int4range
        label: int4range (整数范围)
      - key: tsrange
        label: tsrange (时间戳范围)
      # --- 复合类型 ---
      - key: composite_type
        label: 用户定义复合类型
      # --- 枚举类型 ---
      - key: enum_type
        label: 用户定义枚举类型
      # --- 对象标识符类型 ---
      - key: oid
        label: oid (对象标识符)
      - key: regclass
        label: regclass (关系名OID别名)
    default_expr_shape:
      label: 默认值形态
      importance: non_important
      values:
      - key: with_DEFAULT
        label: DEFAULT default_expr
      - key: with_equals
        label: = default_expr
      - key: without_DEFAULT
        label: 无默认值子句
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: procedure_owner
        label: 过程 Owner
      - key: non_owner_with_create
        label: 非Owner但有CREATE权限
      - key: non_owner_no_privilege
        label: Owner且无权限
    schema_dependency:
      label: Schema 依赖
      importance: non_important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在
      - key: pg_catalog_reserved
        label: pg_catalog (系统保留Schema)
      - key: information_schema_reserved
        label: information_schema (系统保留Schema)
    role_dependency:
      label: 角色依赖
      importance: non_important
      values:
      - key: owner_role_exists
        label: Owner角色存在
      - key: owner_role_not_exists
        label: Owner角色不存在
    language_dependency:
      label: 语言依赖
      importance: non_important
      values:
      - key: language_installed_sql
        label: SQL 语言已安装
      - key: language_installed_plpgsql
        label: PL/pgSQL 语言已安装
      - key: language_not_installed
        label: 语言未安装
    duplicate_procedure_signature:
      label: 重名冲突
      importance: non_important
      values:
      - key: with_OR_REPLACE_replace
        label: 重名 + OR REPLACE → 替换
      - key: without_OR_REPLACE_error
        label: 重名 + 无 OR REPLACE → error
    invalid_argtype:
      label: 无效参数类型
      importance: non_important
      values:
      - key: unknown_type_name
        label: 未知类型名
    conflicting_name_with_function:
      label: 同名同签名函数冲突
      importance: non_important
      values:
      - key: same_name_same_argtypes_function_exists
        label: 同名同参数签名函数已存在
    permission_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: no_create_privilege_in_schema
        label: 在Schema中无CREATE权限
      - key: no_usage_privilege_on_language
        label: 无语言USAGE权限
    language_not_available:
      label: 语言不可用
      importance: non_important
      values:
      - key: untrusted_language_requires_superuser
        label: 非可信语言需要superuser权限
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
      - key: CALL_procedure_execution
        label: CALL procedure_name() 验证
      - key: pg_get_functiondef
        label: pg_get_functiondef() 查询
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_PROCEDURE
        label: DROP PROCEDURE name(types)
      - key: DROP_PROCEDURE_IF_EXISTS
        label: DROP PROCEDURE IF EXISTS name(types)
      - key: DROP_PROCEDURE_CASCADE
        label: DROP PROCEDURE name(types) CASCADE
  defaults:
    expected_status: success
    or_replace_clause: absent
    language_clause: sql
    security_clause: absent
    transform_clause: absent
    sql_body_form: sql_body_inline
    set_clause: absent
    object_state: not_exists
    argmode: absent
    argname: without_argname
    default_expr_shape: without_DEFAULT
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - expected_status
    non_main_factors:
    - or_replace_clause
    - language_clause
    - security_clause
    - transform_clause
    - sql_body_form
    - set_clause
    - procedure_name_shape
    - argmode
    - argname
    - argtype
    - default_expr_shape
    - privilege_level
    - schema_dependency
    - role_dependency
    - language_dependency
    - duplicate_procedure_signature
    - invalid_argtype
    - conflicting_name_with_function
    - permission_insufficient
    - language_not_available
    - identifier_length_exceeded
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - argtype
  rendering:
    statement_template: "CREATE [ OR REPLACE ] PROCEDURE name ( [ argtype [, ...] ] ) LANGUAGE lang_name sql_body"
    verification_query_template: "SELECT count(*) FROM pg_proc WHERE proname = '{procedure_name}' AND prokind = 'p'"
    factor_value_bindings:
      or_replace_clause:
        present: "OR REPLACE"
        absent: ""
      security_clause:
        SECURITY_INVOKER: "SECURITY INVOKER"
        SECURITY_DEFINER: "SECURITY DEFINER"
        absent: ""
```
```