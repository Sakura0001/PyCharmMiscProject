# 技能：ALTER EXTENSION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterextension.html

```sql
ALTER EXTENSION name UPDATE [ TO new_version ]
ALTER EXTENSION name SET SCHEMA new_schema
ALTER EXTENSION name ADD member_object
ALTER EXTENSION name DROP member_object

where member_object is:

  ACCESS METHOD object_name |
  AGGREGATE aggregate_name ( aggregate_signature ) |
  CAST (source_type AS target_type) |
  COLLATION object_name |
  CONVERSION object_name |
  DOMAIN object_name |
  EVENT TRIGGER object_name |
  FOREIGN DATA WRAPPER object_name |
  FOREIGN TABLE object_name |
  FUNCTION function_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  MATERIALIZED VIEW object_name |
  OPERATOR operator_name (left_type, right_type) |
  OPERATOR CLASS object_name USING index_method |
  OPERATOR FAMILY object_name USING index_method |
  [ PROCEDURAL ] LANGUAGE object_name |
  PROCEDURE procedure_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  ROUTINE routine_name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ] |
  SCHEMA object_name |
  SEQUENCE object_name |
  SERVER object_name |
  TABLE object_name |
  TEXT SEARCH CONFIGURATION object_name |
  TEXT SEARCH DICTIONARY object_name |
  TEXT SEARCH PARSER object_name |
  TEXT SEARCH TEMPLATE object_name |
  TRANSFORM FOR type_name LANGUAGE lang_name |
  TYPE object_name |
  VIEW object_name

and aggregate_signature is:

* |
[ argmode ] [ argname ] argtype [ , ... ] |
[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]
```

PG16 关键约束：
- 必须拥有扩展才能使用 ALTER EXTENSION。ADD/DROP 形式还需要拥有被添加/移除的对象。
- UPDATE：更新扩展到新版本，扩展必须提供合适的更新脚本。
- SET SCHEMA：将扩展对象移动到另一个 schema，扩展必须是 relocatable 才能成功。
- ADD：将现有对象添加为扩展成员，主要用于扩展更新脚本。对象之后只能通过删除扩展来删除。
- DROP：从扩展中移除成员对象（不删除对象本身），主要用于扩展更新脚本。

## 语句作用

官方说明：ALTER EXTENSION — change the definition of an extension

该 reference 关注扩展定义变更语句的四个顶层语法分支（UPDATE / SET SCHEMA / ADD member_object / DROP member_object）、权限边界（owner 权限 + 对象 owner 权限）、relocatable 约束和 member_object 类型多样性。

ALTER EXTENSION **不涉及列类型定义**——它操作扩展的元数据和成员关系，不直接创建或修改表/列结构。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（UPDATE / SET SCHEMA / ADD member_object / DROP member_object）
- object_state：目标 extension 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- alter_action：ALTER 行为类型（update / set_schema / add / drop）
- update_version：UPDATE 版本形态（省略 / 指定新版本 / 指定不存在版本）
- relocatable_state：SET SCHEMA 依赖的 relocatable 状态（relocatable / non_relocatable）
- member_object_type：ADD/DROP 的 member_object 类型（table / function / type / view / sequence / domain / operator / 其他）
- role_specification：ADD/DROP 中 role_specification 形态

### T3：对象名与输入形态因子
- extension_name_shape：extension 名称形态
- new_schema_shape：SET SCHEMA 目标 schema 名称形态
- member_object_name_shape：member_object 名称形态
- version_string_shape：UPDATE 版本字符串形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（extension_owner / non_owner / superuser）
- object_owner_match：ADD/DROP 中对象 owner 是否与 extension owner 匹配（匹配 / 不匹配）
- target_schema_existence：SET SCHEMA 目标 schema 存在性（存在 / 不存在）
- member_object_existence：ADD/DROP 的 member_object 存在性（存在 / 不存在）

### T5：异常与边界因子
- nonexistent_extension：目标 extension 不存在
- non_relocatable_set_schema：对非 relocatable 扩展执行 SET SCHEMA
- nonexistent_member_object：ADD/DROP 引用的 member_object 不存在
- object_not_owner：ADD/DROP 时非对象 owner 尝试操作
- version_not_available：UPDATE 指定不存在的版本
- insufficient_privilege：非 owner 尝试 ALTER EXTENSION
- nonexistent_target_schema：SET SCHEMA 目标 schema 不存在

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 ALTER EXTENSION 四个语法分支中的所有行为路径。
- 不需要覆盖所有基表和所有列类型，因为 ALTER EXTENSION 不涉及表/列/索引组合。
- 需要覆盖 member_object 的代表性类型（至少 table、function、type、view），不需要枚举所有 24 种 member_object 类型。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标 extension 对象，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标 extension 存在时的成功修改路径、目标 extension 不存在时的失败路径。
- UPDATE / SET SCHEMA / ADD / DROP 四个分支需要保持独立归因。
- ADD/DROP 分支还需要对象 owner 与 extension owner 的权限匹配/不匹配路径。
- SET SCHEMA 分支需要覆盖 relocatable 和 non_relocatable 两种扩展状态。
- 成功路径必须包含可验证的对象变更检查，并在生命周期末尾清理对象。
- 每个样本必须包含明确的前置对象准备、目标 ALTER EXTENSION 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- ALTER EXTENSION 要求执行者是 extension 的 owner，ADD/DROP 还要求对象 owner 权限，必须在生成样本中显式标注。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要权限匹配、schema 存在性或 member_object 存在性的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（UPDATE / SET SCHEMA / ADD / DROP）
  - 目标 extension 存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖（owner / non_owner / superuser）
- 次优先保证：
  - member_object 代表性类型覆盖（table / function / type / view）
  - relocatable / non_relocatable 状态覆盖
  - UPDATE 版本子句代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: extension
  skill_name: alter_extension
  official_source: https://www.postgresql.org/docs/16/sql-alterextension.html
  statement:
    key: alter_extension
    name: ALTER EXTENSION
    aliases:
    - ALTER EXTENSION
    - alter extension
    - alter_extension
    purpose: change the definition of an extension
  syntax_templates:
  - "ALTER EXTENSION name UPDATE [ TO new_version ]"
  - "ALTER EXTENSION name SET SCHEMA new_schema"
  - "ALTER EXTENSION name ADD member_object"
  - "ALTER EXTENSION name DROP member_object"
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
    - alter_action
    - update_version
    - relocatable_state
    - member_object_type
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - extension_name_shape
    - new_schema_shape
    - member_object_name_shape
    - version_string_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - object_owner_match
    - target_schema_existence
    - member_object_existence
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_extension
    - non_relocatable_set_schema
    - nonexistent_member_object
    - object_not_owner
    - version_not_available
    - insufficient_privilege
    - nonexistent_target_schema
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
      - key: branch_update
        label: ALTER EXTENSION name UPDATE [ TO new_version ]
      - key: branch_set_schema
        label: ALTER EXTENSION name SET SCHEMA new_schema
      - key: branch_add_member
        label: ALTER EXTENSION name ADD member_object
      - key: branch_drop_member
        label: ALTER EXTENSION name DROP member_object
    object_state:
      label: 目标 extension 对象状态
      importance: important
      values:
      - key: exists
        label: 扩展已存在
      - key: not_exists
        label: 扩展不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    alter_action:
      label: ALTER 行为类型
      importance: non_important
      values:
      - key: update
        label: UPDATE (更新版本)
      - key: set_schema
        label: SET SCHEMA (移动对象到新 schema)
      - key: add
        label: ADD member_object (添加成员对象)
      - key: drop
        label: DROP member_object (移除成员对象)
    update_version:
      label: UPDATE 版本形态
      importance: non_important
      values:
      - key: omitted_default
        label: 省略版本 (使用默认版本)
      - key: specified_new_version
        label: 指定有效新版本
      - key: nonexistent_version
        label: 指定不存在的版本
    relocatable_state:
      label: SET SCHEMA 依赖的 relocatable 状态
      importance: non_important
      values:
      - key: relocatable
        label: 扩展标记为 relocatable
      - key: non_relocatable
        label: 扩展标记为 non-relocatable
    member_object_type:
      label: ADD/DROP 的 member_object 类型
      importance: non_important
      values:
      - key: table
        label: TABLE object_name
      - key: function
        label: FUNCTION function_name
      - key: type
        label: TYPE object_name
      - key: view
        label: VIEW object_name
      - key: sequence
        label: SEQUENCE object_name
      - key: domain
        label: DOMAIN object_name
      - key: aggregate
        label: AGGREGATE aggregate_name
      - key: operator
        label: OPERATOR operator_name
    extension_name_shape:
      label: extension 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_name
        label: 不存在的扩展名
    new_schema_shape:
      label: SET SCHEMA 目标 schema 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: quoted_id
        label: 双引号标识符
      - key: nonexistent_schema
        label: 不存在的 schema
    member_object_name_shape:
      label: member_object 名称形态
      importance: non_important
      values:
      - key: simple_id
        label: 合法普通标识符
      - key: schema_qualified
        label: Schema 限定标识符
      - key: quoted_id
        label: 双引号标识符
    version_string_shape:
      label: UPDATE 版本字符串形态
      importance: non_important
      values:
      - key: identifier_form
        label: 标识符形式
      - key: string_literal_form
        label: 字符串字面量形式
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - key: extension_owner
        label: 扩展 owner
      - key: non_owner
        label: 非 owner 用户
      - key: superuser
        label: 超级用户
    object_owner_match:
      label: ADD/DROP 中对象 owner 匹配
      importance: non_important
      values:
      - key: same_owner
        label: 对象 owner 与 extension owner 一致
      - key: different_owner
        label: 对象 owner 与 extension owner 不同
    target_schema_existence:
      label: SET SCHEMA 目标 schema 存在性
      importance: non_important
      values:
      - key: schema_exists
        label: 目标 schema 存在
      - key: schema_not_exists
        label: 目标 schema 不存在
    member_object_existence:
      label: ADD/DROP 的 member_object 存在性
      importance: non_important
      values:
      - key: object_exists
        label: member_object 存在
      - key: object_not_exists
        label: member_object 不存在
    nonexistent_extension:
      label: 目标 extension 不存在
      importance: non_important
      values:
      - key: extension_exists
        label: 扩展存在
      - key: extension_missing
        label: 扩展不存在
    non_relocatable_set_schema:
      label: 对非 relocatable 扩展执行 SET SCHEMA
      importance: non_important
      values:
      - key: relocatable_extension
        label: relocatable 扩展 → success
      - key: non_relocatable_extension
        label: non-relocatable 扩展 → error
    nonexistent_member_object:
      label: ADD/DROP 引用的 member_object 不存在
      importance: non_important
      values:
      - key: object_exists
        label: member_object 存在
      - key: object_missing
        label: member_object 不存在 → error
    object_not_owner:
      label: ADD/DROP 时非对象 owner 尝试操作
      importance: non_important
      values:
      - key: owner_matches
        label: 对象 owner 与 extension owner 一致 → success
      - key: owner_mismatch
        label: 对象 owner 不同 → error
    version_not_available:
      label: UPDATE 指定不存在的版本
      importance: non_important
      values:
      - key: version_available
        label: 版本可用
      - key: version_unavailable
        label: 版本不可用 → error
    insufficient_privilege:
      label: 非 owner 尝试 ALTER EXTENSION
      importance: non_important
      values:
      - key: owner_execution
        label: extension owner 执行
      - key: non_owner_execution
        label: 非 owner 执行 → error
      - key: superuser_execution
        label: superuser 执行 → success
    nonexistent_target_schema:
      label: SET SCHEMA 目标 schema 不存在
      importance: non_important
      values:
      - key: schema_exists
        label: 目标 schema 存在
      - key: schema_missing
        label: 目标 schema 不存在 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_extension_catalog_query
        label: pg_extension 系统目录查询
      - key: pg_depend_catalog_query
        label: pg_depend 成员关系查询
      - key: error_assertion
        label: 错误断言
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_member_from_extension
        label: 从扩展中移除成员对象
      - key: revert_schema
        label: 还原 schema 变更
      - key: revert_version
        label: 还原版本变更
      - key: drop_extension
        label: 删除扩展
  notes:
    owner_privilege: 必须拥有扩展才能使用 ALTER EXTENSION。ADD/DROP 形式还需要拥有被添加/移除的对象。
    relocatable_constraint: SET SCHEMA 仅适用于标记为 relocatable 的扩展。
    add_drop_usage: ADD/DROP 主要用于扩展更新脚本，添加后对象只能通过删除扩展来删除。
    member_object_variety: member_object 有 24 种类型，不需要全部枚举，代表性覆盖即可。
    extension_no_column_types: ALTER EXTENSION 不涉及列类型定义，不需要挂靠基表列类型。
  defaults:
    expected_status: success
    privilege_level: extension_owner
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - alter_action
    - update_version
    - relocatable_state
    - member_object_type
    - extension_name_shape
    - new_schema_shape
    - member_object_name_shape
    - version_string_shape
    - privilege_level
    - object_owner_match
    - target_schema_existence
    - member_object_existence
    - nonexistent_extension
    - non_relocatable_set_schema
    - nonexistent_member_object
    - object_not_owner
    - version_not_available
    - insufficient_privilege
    - nonexistent_target_schema
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER EXTENSION {extension_name} {alter_clause}"
    verification_query_template: "SELECT extname, extversion FROM pg_extension WHERE extname = '{extension_name}'"
    factor_value_bindings:
      alter_action:
        update: "UPDATE [ TO {version} ]"
        set_schema: "SET SCHEMA {new_schema}"
        add: "ADD {member_object}"
        drop: "DROP {member_object}"
```
