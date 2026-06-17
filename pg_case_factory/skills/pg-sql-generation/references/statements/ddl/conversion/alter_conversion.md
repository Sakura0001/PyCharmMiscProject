# 技能：ALTER CONVERSION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterconversion.html

```sql
ALTER CONVERSION name RENAME TO new_name
ALTER CONVERSION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER CONVERSION name SET SCHEMA new_schema
```

PG16 关键约束：
- 必须拥有该 conversion 才能使用 ALTER CONVERSION
- 更改 owner：必须能够 SET ROLE 到新拥有角色，且该角色必须对 conversion 所在 schema 有 CREATE 权限
- superuser 可以更改任何 conversion 的 owner，不受上述限制
- RENAME TO：需要 owner 权限；同一 schema 内新名称不能与已有 conversion 重名
- SET SCHEMA：需要 owner 权限且对目标 schema 有 CREATE 权限；目标 schema 内不能有同名 conversion
- ALTER CONVERSION 是 PostgreSQL 扩展，不在 SQL 标准中

## 语句作用

官方说明：ALTER CONVERSION — change the definition of a conversion

该 reference 关注字符集编码转换对象的元数据变更。ALTER CONVERSION 有三个独立语法分支（RENAME TO / OWNER TO / SET SCHEMA），每个分支有不同的前置依赖、权限要求和冲突边界。该语句不涉及列类型，不需要覆盖基表或列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（RENAME TO / OWNER TO / SET SCHEMA）
- object_state：目标 conversion 对象状态（exists / not_exists）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- privilege_level：执行权限（superuser / conversion_owner / non_owner）
- new_owner_target：OWNER TO 的目标形式（existing_role / nonexistent_role / CURRENT_ROLE / CURRENT_USER / SESSION_USER）
- rename_conflict：RENAME TO 目标名称状态（new_name_unique / new_name_exists）
- schema_conflict：SET SCHEMA 目标状态（target_schema_exists_no_conflict / target_schema_exists_with_conflict / target_schema_not_exists）

### T3：对象名与输入形态因子
- conversion_name_shape：conversion 名称形态
- new_name_shape：新名称形态（仅 RENAME TO）
- new_schema_shape：目标 schema 名称形态（仅 SET SCHEMA）
- new_owner_shape：目标 owner 名称形态（仅 OWNER TO）

### T4：依赖对象与环境因子
- schema_privilege：schema 权限（有 CREATE 权限 / 无 CREATE 权限）
- owner_membership：owner 成员关系（能 SET ROLE / 不能 SET ROLE）
- conversion_default_status：conversion 是否为 DEFAULT 转换

### T5：异常与边界因子
- conversion_not_exist：目标 conversion 不存在
- rename_target_conflict：RENAME TO 新名称在目标 schema 中已存在
- owner_not_exist：OWNER TO 目标角色不存在
- schema_not_exist：SET SCHEMA 目标 schema 不存在
- schema_name_conflict：SET SCHEMA 目标 schema 中已存在同名 conversion
- privilege_denied：非 owner 执行 ALTER CONVERSION
- no_create_privilege_on_target_schema：OWNER TO / SET SCHEMA 缺少 CREATE 权限
- cannot_set_role_to_new_owner：无法 SET ROLE 到新 owner

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 需要覆盖所有 ALTER CONVERSION 三个语法分支。
- 不需要覆盖所有基表，不需要覆盖每张基表中所有的列类型。
- T1 因子做笛卡尔积覆盖；statement_branch 跨三个分支。
- T2 因子按分支适用性参与组合：
  - new_owner_target 仅挂靠到 OWNER TO 分支。
  - rename_conflict 仅挂靠到 RENAME TO 分支。
  - schema_conflict 仅挂靠到 SET SCHEMA 分支。
  - privilege_level 覆盖所有分支。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 成功路径必须先创建测试 schema、转换函数和测试 conversion。
- 测试 conversion 应使用任务唯一前缀命名，避免与系统内置 conversion 冲突。
- 测试 conversion 不得直接修改 pg_catalog 内置 conversion；内置 conversion 只能作为只读查询或冲突参照。
- RENAME TO 必须覆盖新名称成功、新名称已存在失败、conversion 不存在失败、权限不足失败路径。
- OWNER TO 必须覆盖 owner/superuser 成功、CURRENT_ROLE/CURRENT_USER/SESSION_USER 目标形式、目标角色不存在失败、无 SET ROLE 权限失败路径。
- SET SCHEMA 必须覆盖目标 schema 存在成功、目标 schema 不存在失败、目标 schema 同名冲突失败、权限不足失败路径。
- DEFAULT conversion 场景应验证 pg_conversion.condefault、conforencoding、contoencoding 在变更后保持预期。
- 失败路径必须使用预期失败包装，不得让单个失败样本中断整批 SQL 执行。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- T2 异常场景挂靠到对应语法分支的代表性样本：
  - rename_target_conflict 仅挂到 RENAME TO。
  - owner_not_exist、cannot_set_role 仅挂到 OWNER TO。
  - schema_not_exist、schema_name_conflict 仅挂到 SET SCHEMA。
  - privilege_denied 覆盖所有分支各至少一个样本。
- T3 标识符因子在三个分支上轮转挂靠，必须包含合法标识符、带引号标识符、保留字形态。
- DEFAULT conversion 状态至少在三个分支各保留一个成功样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏语句分支、权限路径和成功/失败归因的可识别性。

## 规模控制规则

- 优先保证：
  - 三个语法分支全覆盖
  - superuser/owner/non_owner 权限路径全覆盖
  - conversion 存在/不存在状态全覆盖
  - 重名冲突、目标角色不存在、目标 schema 不存在/冲突全覆盖
  - 成功/失败/权限失败路径全覆盖
- 次优先保证：
  - CURRENT_ROLE/CURRENT_USER/SESSION_USER 目标 owner 形式全覆盖
  - schema 限定名与非限定名全覆盖
  - DEFAULT conversion 状态覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: conversion
  skill_name: alter_conversion
  official_source: https://www.postgresql.org/docs/16/sql-alterconversion.html
  statement:
    key: alter_conversion
    name: ALTER CONVERSION
    aliases:
    - alter_conversion
    - ALTER CONVERSION
    purpose: ALTER CONVERSION — change the definition of a conversion
  syntax_templates:
  - "ALTER CONVERSION name RENAME TO new_name"
  - "ALTER CONVERSION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER\
    \ | SESSION_USER }"
  - "ALTER CONVERSION name SET SCHEMA new_schema"
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
    - privilege_level
    - new_owner_target
    - rename_conflict
    - schema_conflict
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - conversion_name_shape
    - new_name_shape
    - new_schema_shape
    - new_owner_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - schema_privilege
    - owner_membership
    - conversion_default_status
  - tier: T5
    name: 异常与边界因子
    factors:
    - conversion_not_exist
    - rename_target_conflict
    - owner_not_exist
    - schema_not_exist
    - schema_name_conflict
    - privilege_denied
    - no_create_privilege_on_target_schema
    - cannot_set_role_to_new_owner
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
      - key: branch_rename
        label: ALTER CONVERSION name RENAME TO new_name
      - key: branch_owner
        label: ALTER CONVERSION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_set_schema
        label: ALTER CONVERSION name SET SCHEMA new_schema
    object_state:
      label: 目标 conversion 对象状态
      importance: important
      values:
      - exists
      - not_exists
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - conversion_owner
      - non_owner
    new_owner_target:
      label: OWNER TO 目标形式
      importance: non_important
      values:
      - existing_role
      - nonexistent_role
      - CURRENT_ROLE
      - CURRENT_USER
      - SESSION_USER
    rename_conflict:
      label: RENAME TO 目标名称状态
      importance: non_important
      values:
      - new_name_unique
      - new_name_exists_in_schema
    schema_conflict:
      label: SET SCHEMA 目标状态
      importance: non_important
      values:
      - target_schema_exists_no_conflict
      - target_schema_exists_with_conflict
      - target_schema_not_exists
    conversion_name_shape:
      label: conversion 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified
      - nonexistent_name
    new_name_shape:
      label: 新名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - reserved_word_as_name
    new_schema_shape:
      label: 目标 schema 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_schema_name
    new_owner_shape:
      label: 目标 owner 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - special_token
    schema_privilege:
      label: schema CREATE 权限
      importance: non_important
      values:
      - has_create_privilege
      - lacks_create_privilege
    owner_membership:
      label: SET ROLE 成员关系
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role
    conversion_default_status:
      label: DEFAULT 转换状态
      importance: non_important
      values:
      - is_default_conversion
      - is_not_default_conversion
    conversion_not_exist:
      label: 目标 conversion 不存在
      importance: non_important
      values:
      - conversion_exists
      - conversion_not_exists
    rename_target_conflict:
      label: RENAME 目标冲突
      importance: non_important
      values:
      - no_conflict
      - name_already_exists
    owner_not_exist:
      label: OWNER TO 目标角色不存在
      importance: non_important
      values:
      - role_exists
      - role_not_exists
    schema_not_exist:
      label: SET SCHEMA 目标 schema 不存在
      importance: non_important
      values:
      - schema_exists
      - schema_not_exists
    schema_name_conflict:
      label: SET SCHEMA 目标同名冲突
      importance: non_important
      values:
      - no_conflict
      - same_name_in_target_schema
    privilege_denied:
      label: 非 owner 执行 ALTER
      importance: non_important
      values:
      - owner_success
      - non_owner_failure
      - superuser_success
    no_create_privilege_on_target_schema:
      label: 目标 schema 缺少 CREATE 权限
      importance: non_important
      values:
      - has_create_privilege
      - lacks_create_privilege
    cannot_set_role_to_new_owner:
      label: 无法 SET ROLE 到新 owner
      importance: non_important
      values:
      - can_set_role
      - cannot_set_role
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_conversion
      - catalog_query_pg_namespace
      - error_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_conversion
      - drop_schema
      - drop_role
      - cascade_cleanup
  defaults:
    expected_status: success
    statement_branch: branch_rename
    object_state: exists
    privilege_level: conversion_owner
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - privilege_level
    - new_owner_target
    - rename_conflict
    - schema_conflict
    - conversion_name_shape
    - new_name_shape
    - new_schema_shape
    - new_owner_shape
    - schema_privilege
    - owner_membership
    - conversion_default_status
    - conversion_not_exist
    - rename_target_conflict
    - owner_not_exist
    - schema_not_exist
    - schema_name_conflict
    - privilege_denied
    - no_create_privilege_on_target_schema
    - cannot_set_role_to_new_owner
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
  rendering:
    statement_template: "ALTER CONVERSION {conversion_name} {alter_action} {alter_target}"
    verification_query_template: "SELECT conname, connamespace FROM pg_conversion\
      \ WHERE conname = '{conversion_name}'"
    factor_value_bindings: {}
```
