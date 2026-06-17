# 技能：DROP DOMAIN

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-dropdomain.html

```sql
DROP DOMAIN [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- 只有 domain 的 owner 或 superuser 才能执行 DROP DOMAIN
- RESTRICT 是默认行为（省略 CASCADE/RESTRICT 时等效于 RESTRICT）
- 当 domain 被表列或其他对象引用时，RESTRICT 模式拒绝删除
- CASCADE 会自动删除所有依赖对象（包括使用该 domain 的表列）
- 可以在一条命令中删除多个 domain（逗号分隔的 name 列表）
- IF EXISTS 是 PostgreSQL 扩展（不在 SQL 标准中）

## 语句作用

官方说明：DROP DOMAIN — remove a domain

该 reference 关注域（SQL DOMAIN）对象的删除操作，包括权限边界、依赖对象处理和 IF EXISTS 行为。域删除涉及被引用列的依赖处理（CASCADE/RESTRICT），但不涉及基表列类型组合。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP DOMAIN / DROP DOMAIN IF EXISTS）
- object_state：目标 domain 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关
- cascade_restrict：CASCADE / RESTRICT 子句
- multi_domain：是否删除多个 domain（单个 / 多个逗号列表）
- dependency_status：domain 是否被依赖对象引用

### T3：对象名与输入形态因子
- domain_name_shape：domain 名称形态

### T4：依赖对象与环境因子
- privilege_level：执行权限（domain_owner / non_owner / superuser）
- dependency_context：依赖对象驻留情况

### T5：异常与边界因子
- nonexistent_domain：domain 不存在且无 IF EXISTS
- has_dependents_restrict：RESTRICT 模式下有依赖对象
- privilege_denied：非 owner 非 superuser 执行

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP DOMAIN 全部语法分支（2 个顶层形式）。
- 不需要覆盖所有基表和所有列类型，因为 DROP DOMAIN 不涉及基表列类型组合。
- 覆盖目标 domain 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括权限边界和依赖对象处理。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须覆盖目标 domain 存在时的成功删除路径，以及目标 domain 不存在时的失败路径。
- IF EXISTS 必须覆盖不存在 domain 的代表性 no-op 路径。
- CASCADE / RESTRICT 必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- RESTRICT 是默认行为，省略 CASCADE/RESTRICT 的路径必须等效于 RESTRICT 路径。
- 可以在一条命令中删除多个 domain，必须覆盖单目标和多目标路径。
- 非 owner 非 superuser 执行 DROP DOMAIN 属于失败路径。
- 成功路径必须包含可验证的对象不存在性检查。
- 每个样本必须包含明确的前置对象准备、目标 DROP DOMAIN 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 与权限边界相关的因子必须挂靠到具有明确权限上下文的样本上。
- 与依赖对象相关的因子必须挂靠到 CASCADE/RESTRICT 分支的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 子句、CASCADE/RESTRICT 子句和多 domain 列表代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: domain
  skill_name: drop_domain
  official_source: https://www.postgresql.org/docs/16/sql-dropdomain.html
  statement:
    key: drop_domain
    name: DROP DOMAIN
    aliases:
    - drop_domain
    - DROP DOMAIN
    purpose: DROP DOMAIN — remove a domain
  syntax_templates:
  - "DROP DOMAIN [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]"
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
    - if_exists_clause
    - cascade_restrict
    - multi_domain
    - dependency_status
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - domain_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - dependency_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_domain
    - has_dependents_restrict
    - privilege_denied
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
      - key: branch_drop_domain
        label: DROP DOMAIN name [, ...] [ CASCADE | RESTRICT ]
      - key: branch_drop_domain_if_exists
        label: DROP DOMAIN IF EXISTS name [, ...] [ CASCADE | RESTRICT ]
    object_state:
      label: 目标 domain 对象状态
      importance: important
      values:
      - exists
      - absent
      - partially_exists_multi
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: important
      values:
      - present
      - absent
    cascade_restrict:
      label: CASCADE / RESTRICT 子句
      importance: important
      values:
      - cascade
      - restrict
      - omitted_default_restrict
    multi_domain:
      label: 是否删除多个 domain
      importance: non_important
      values:
      - single_domain
      - multiple_domains
    dependency_status:
      label: domain 是否被依赖对象引用
      importance: important
      values:
      - no_dependents
      - has_table_column_dependent
      - has_other_dependent
    domain_name_shape:
      label: domain 名称形态
      importance: non_important
      values:
      - simple_id
      - quoted_id
      - schema_qualified
      - reserved_word_as_name
      - nonexistent_name
      - existing_name
    privilege_level:
      label: 执行权限
      importance: non_important
      values:
      - superuser
      - domain_owner
      - non_owner
    dependency_context:
      label: 依赖对象驻留情况
      importance: non_important
      values:
      - no_dependencies
      - column_using_domain
      - other_type_dependency
    nonexistent_domain:
      label: domain 不存在且无 IF EXISTS
      importance: non_important
      values:
      - domain_exists
      - domain_missing_without_if_exists
    has_dependents_restrict:
      label: RESTRICT 模式下有依赖对象
      importance: non_important
      values:
      - no_dependents_safe
      - dependents_block_restrict
    privilege_denied:
      label: 非 owner 非 superuser 执行
      importance: non_important
      values:
      - owner_execution
      - non_owner_denied
      - superuser_execution
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query_pg_type
      - error_assertion
      - notice_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_domain
      - cascade_cleanup
      - role_cleanup
  defaults:
    expected_status: success
    cascade_restrict: restrict
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - multi_domain
    - dependency_status
    - domain_name_shape
    - privilege_level
    - dependency_context
    - nonexistent_domain
    - has_dependents_restrict
    - privilege_denied
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP DOMAIN {if_exists_clause} {domain_name_list} {cascade_restrict_clause}"
    verification_query_template: "SELECT typname FROM pg_type WHERE typname = '{domain_name}'\
      \ AND typtype = 'd'"
    factor_value_bindings: {}
```
