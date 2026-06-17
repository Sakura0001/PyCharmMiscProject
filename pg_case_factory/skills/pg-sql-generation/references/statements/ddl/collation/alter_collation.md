# 技能：ALTER COLLATION

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altercollation.html

```sql
ALTER COLLATION name REFRESH VERSION

ALTER COLLATION name RENAME TO new_name
ALTER COLLATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
ALTER COLLATION name SET SCHEMA new_schema
```

**重要行为说明**：
- ALTER COLLATION 有四个语法分支：REFRESH VERSION、RENAME TO、OWNER TO、SET SCHEMA。
- REFRESH VERSION 更新 pg_collation 中记录的版本信息，**不检查**受影响对象是否已重建。正确使用流程：先重建依赖对象（REINDEX 等），再 REFRESH VERSION。
- collation 版本不匹配会触发 WARNING，可能导致索引损坏。
- OWNER TO 要求执行用户能 SET ROLE 到新 Owner，且新 Owner 须有 collation 所在 schema 的 CREATE 权限。超级用户可绕过此限制。
- SET SCHEMA 要求执行用户有目标 schema 的 CREATE 权限。
- 必须拥有 collation 才能执行 ALTER COLLATION。
- 版本跟踪：libc (GNU C library 版本作为代理)、ICU (ICU 库版本)、Windows (仅 BCP 47 语言标签)。
- ALTER COLLATION 不直接涉及列类型组合。

## 语句作用

官方说明：ALTER COLLATION — change the definition of a collation

该 reference 关注校对规则修改语句的四个语法分支、权限边界、版本刷新行为与目标对象状态，不负责覆盖表/列/索引类型组合。

ALTER COLLATION **不直接涉及列类型组合**，具体表现为：
- 语句仅修改校对规则的元数据（名称、Owner、Schema、版本信息）
- collation 被列定义引用，但修改 collation 不涉及列类型组合

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（REFRESH_VERSION、RENAME_TO、OWNER_TO、SET_SCHEMA）
- object_state：目标 Collation 对象存在性（collation_exists、collation_not_exists）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- collation_usage_state：校对规则使用状态（no_dependencies、referenced_by_table_column、referenced_by_index）
- target_state：目标状态（new_name_available、new_name_conflict、new_owner_available、new_owner_not_available、new_schema_available、new_schema_conflict）— 按分支适用

### T3：对象名与输入形态因子
- collation_name_shape：校对规则名称形态（plain_identifier、quoted_identifier、schema_qualified）
- new_name_shape：新名称形态（plain_identifier、quoted_identifier）— 仅 RENAME TO
- new_owner_shape：新 Owner 形态（plain_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER）— 仅 OWNER TO
- new_schema_shape：新 Schema 形态（existing_schema、nonexistent_schema）— 仅 SET SCHEMA

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、collation_owner、non_owner）
- owner_membership：Owner 成员关系（member_of_new_owner、not_member_of_new_owner）— 仅 OWNER TO
- referenced_objects：被引用对象（table_column_with_collate、index_using_collation）— 用于验证依赖行为

### T5：异常与边界因子
- collation_not_exists：校对规则不存在 → error
- new_name_conflict：RENAME TO 目标名称已存在 → error
- new_owner_not_exists：OWNER TO 目标 role 不存在 → error
- new_schema_not_exists：SET SCHEMA 目标 schema 不存在 → error
- insufficient_privilege：非 Owner 执行 ALTER → error
- new_schema_same_name_conflict：SET SCHEMA 目标 schema 有同名 collation → error

### T6：验证与清理因子
- verification_mode：验证方式（pg_collation_catalog_query、pg_collation_actual_version_query、collation_sort_verification）
- cleanup_mode：清理方式（DROP_COLLATION_CASCADE、DROP_DEPENDENT_OBJECTS_FIRST）

## 覆盖策略

- 必须覆盖 ALTER COLLATION 的四个语法分支（REFRESH VERSION、RENAME TO、OWNER TO、SET SCHEMA）。
- 不需要覆盖所有基表列类型；仅在"被引用"场景中准备最小依赖对象。
- T1 和 T2 作为主覆盖因子。
- T1 因子做笛卡尔积覆盖，但 target_state 仅挂到对应分支。
- T2 因子按分支适用性参与组合。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径、失败路径和权限路径。

## 生成约束

- 成功路径必须先创建测试 schema、测试 collation 和必要角色。
- 测试 collation 优先使用 `CREATE COLLATION <name> FROM "C"` 构造，避免依赖环境特定 locale。
- 所有对象名必须带任务唯一前缀，结束清理必须使用 CASCADE 覆盖依赖对象。
- REFRESH VERSION 必须覆盖 collation 存在、不存在、权限不足路径；验证可读取 pg_collation.collversion 与 pg_collation_actual_version(oid)。
- RENAME TO 必须覆盖新名称成功、已存在失败、collation 不存在失败、权限不足失败。
- OWNER TO 必须覆盖 owner、普通用户、super 用户、CURRENT_ROLE、CURRENT_USER、SESSION_USER，以及 new_owner 不存在失败路径。
- SET SCHEMA 必须覆盖目标 schema 存在成功、不存在失败、同名冲突失败、权限不足失败。
- 被其他对象引用的场景应至少创建一张表字段使用该 collation。

## 挂靠规则

- T3 因子按分支挂靠：new_name 仅挂到 RENAME TO，new_owner 仅挂到 OWNER TO，new_schema 仅挂到 SET SCHEMA。
- T4 权限因子挂靠到所有语法分支的代表性成功和失败样本上。
- T5 异常与边界因子挂靠到对应可归因分支。
- referenced_objects 因子在四个分支各至少保留一个样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏语句分支、权限预期和成功/失败归因的可识别性。

## 规模控制规则

- 优先保证：
  - 四个语法分支全覆盖
  - super 用户、owner、普通用户、无权限用户路径全覆盖
  - collation 存在、不存在、被引用状态全覆盖
  - 成功、失败、权限失败路径全覆盖
- 次优先保证：
  - CURRENT_ROLE、CURRENT_USER、SESSION_USER 目标 Owner 形式全覆盖
  - schema 限定名与非限定名全覆盖
  - 合法、带引号、保留字标识符形态全覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: collation
  skill_name: alter_collation
  official_source: https://www.postgresql.org/docs/16/sql-altercollation.html
  statement:
    key: alter_collation
    name: ALTER COLLATION
    aliases:
    - ALTER COLLATION
    - alter collation
    - alter_collation
    purpose: change the definition of a collation
  syntax_templates:
  - "ALTER COLLATION name REFRESH VERSION"
  - "ALTER COLLATION name RENAME TO new_name"
  - "ALTER COLLATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER COLLATION name SET SCHEMA new_schema"
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
    - collation_usage_state
    - target_state
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - collation_name_shape
    - new_name_shape
    - new_owner_shape
    - new_schema_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - owner_membership
    - referenced_objects
  - tier: T5
    name: 异常与边界因子
    factors:
    - collation_not_exists
    - new_name_conflict
    - new_owner_not_exists
    - new_schema_not_exists
    - insufficient_privilege
    - new_schema_same_name_conflict
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
      - key: branch_refresh_version
        label: REFRESH VERSION
      - key: branch_rename
        label: RENAME TO new_name
      - key: branch_owner
        label: OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_set_schema
        label: SET SCHEMA new_schema
    object_state:
      label: 目标Collation对象存在性
      importance: important
      values:
      - key: collation_exists
        label: 校对规则存在
      - key: collation_not_exists
        label: 校对规则不存在 → error
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    collation_usage_state:
      label: 校对规则使用状态
      importance: important
      values:
      - key: no_dependencies
        label: 无依赖对象
      - key: referenced_by_table_column
        label: 表字段使用该collation (text COLLATE collation_name)
      - key: referenced_by_index
        label: 索引依赖该collation
    target_state:
      label: 目标状态 (按分支适用)
      importance: important
      values:
      - key: new_name_available
        label: 新名称可用 (仅RENAME TO)
      - key: new_name_conflict
        label: 新名称已存在 (仅RENAME TO)
      - key: new_owner_available
        label: 新Owner可用 (仅OWNER TO)
      - key: new_owner_not_available
        label: 新Owner不可用 (仅OWNER TO)
      - key: new_schema_available
        label: 新Schema可用 (仅SET SCHEMA)
      - key: new_schema_conflict
        label: 新Schema有同名collation (仅SET SCHEMA)
    collation_name_shape:
      label: 校对规则名称形态
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符 (如 "de_DE")
      - key: schema_qualified
        label: Schema限定标识符
    new_name_shape:
      label: 新名称形态 (仅RENAME TO)
      importance: non_important
      values:
      - key: plain_identifier
        label: 合法普通标识符
      - key: quoted_identifier
        label: 双引号标识符
    new_owner_shape:
      label: 新Owner形态 (仅OWNER TO)
      importance: non_important
      values:
      - key: plain_role
        label: 普通角色名
      - key: CURRENT_ROLE
        label: CURRENT_ROLE
      - key: CURRENT_USER
        label: CURRENT_USER
      - key: SESSION_USER
        label: SESSION_USER
    new_schema_shape:
      label: 新Schema形态 (仅SET SCHEMA)
      importance: non_important
      values:
      - key: existing_schema
        label: 存在的Schema
      - key: nonexistent_schema
        label: 不存在的Schema → error
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户 (可绕过所有权限制)
      - key: collation_owner
        label: 校对规则Owner
      - key: non_owner
        label: 非 Owner → error
    owner_membership:
      label: Owner成员关系 (仅OWNER TO)
      importance: non_important
      values:
      - key: member_of_new_owner
        label: 执行用户是新Owner的成员 (可SET ROLE)
      - key: not_member_of_new_owner
        label: 执行用户不是新Owner的成员 → error
    referenced_objects:
      label: 被引用对象
      importance: non_important
      values:
      - key: table_column_with_collate
        label: 表字段显式使用该collation
      - key: index_using_collation
        label: 索引依赖该collation
    collation_not_exists:
      label: 校对规则不存在
      importance: non_important
      values:
      - key: not_exists
        label: 校对规则不存在 → error
    new_name_conflict:
      label: 新名称冲突 (仅RENAME TO)
      importance: non_important
      values:
      - key: name_already_exists
        label: 目标名称已存在 → error
    new_owner_not_exists:
      label: 新Owner不存在 (仅OWNER TO)
      importance: non_important
      values:
      - key: nonexistent_role
        label: 目标role不存在 → error
    new_schema_not_exists:
      label: 新Schema不存在 (仅SET SCHEMA)
      importance: non_important
      values:
      - key: nonexistent_schema
        label: 目标schema不存在 → error
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_owner
        label: 非Owner执行ALTER → error
      - key: no_create_on_schema
        label: 无目标Schema的CREATE权限 → error
    new_schema_same_name_conflict:
      label: SET SCHEMA同名冲突
      importance: non_important
      values:
      - key: same_name_in_target_schema
        label: 目标Schema中已有同名collation → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_collation_catalog_query
        label: pg_collation 系统目录查询
      - key: pg_collation_actual_version_query
        label: pg_collation_actual_version(oid) 版本查询 (仅REFRESH VERSION)
      - key: collation_sort_verification
        label: 使用collation排序验证行为
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_COLLATION_CASCADE
        label: DROP COLLATION name CASCADE
      - key: DROP_DEPENDENT_OBJECTS_FIRST
        label: 先删除依赖对象再删除collation
  notes:
    four_branches: ALTER COLLATION 有四个分支（REFRESH VERSION、RENAME TO、OWNER TO、SET SCHEMA）。
    refresh_version_no_check: REFRESH VERSION 仅更新记录版本，不检查受影响对象是否已重建。
    version_mismatch_warning: collation 版本不匹配会触发 WARNING，可能导致索引损坏。
    owner_to_requires_set_role: OWNER TO 要求执行用户能 SET ROLE 到新 Owner。
    set_schema_requires_create: SET SCHEMA 要求有目标 Schema 的 CREATE 权限。
    preferred_from_c: 测试优先使用 FROM "C" 构造校对规则。
  defaults:
    expected_status: success
    object_state: collation_exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - collation_usage_state
    - target_state
    - collation_name_shape
    - new_name_shape
    - new_owner_shape
    - new_schema_shape
    - privilege_level
    - owner_membership
    - referenced_objects
    - collation_not_exists
    - new_name_conflict
    - new_owner_not_exists
    - new_schema_not_exists
    - insufficient_privilege
    - new_schema_same_name_conflict
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER COLLATION {collation_name} {alter_action}"
    verification_query_template: "SELECT * FROM pg_collation WHERE collname = '{collation_name}'"
    factor_value_bindings:
      statement_branch:
        branch_refresh_version: "REFRESH VERSION"
        branch_rename: "RENAME TO {new_name}"
        branch_owner: "OWNER TO {new_owner}"
        branch_set_schema: "SET SCHEMA {new_schema}"
```
