# 技能：DROP TRANSFORM

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-droptransform.html

```sql
DROP TRANSFORM [ IF EXISTS ] FOR type_name LANGUAGE lang_name [ CASCADE | RESTRICT ]
```

PG16 关键约束：
- DROP TRANSFORM 要求执行者同时拥有 type 和 language（与 CREATE TRANSFORM 权限要求一致）
- RESTRICT（默认）：如果有对象依赖该 transform，拒绝删除
- CASCADE：自动删除依赖该 transform 的所有对象
- IF EXISTS：如果 transform 不存在，不报错而是发出通知
- 该语句涉及 type_id 和 language_id 依赖，不涉及基表列类型

## 语句作用

官方说明：DROP TRANSFORM — remove a transform

该 reference 关注 transform 删除操作的权限边界（需拥有 type 和 language）、依赖对象驻留和 IF EXISTS 行为，不涉及表/列组合但涉及类型和语言依赖。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支（DROP TRANSFORM / DROP TRANSFORM IF EXISTS）
- object_state：目标 transform 对象状态（已存在 / 不存在）
- expected_status：预期结果（success / failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句开关（省略 / 指定）
- cascade_restrict：CASCADE / RESTRICT 子句（省略默认RESTRICT / CASCADE / RESTRICT）
- privilege_requirement：权限要求（own_type_and_language / missing_type_ownership / missing_language_ownership）
- type_existence：引用的 type 存在性（存在 / 不存在）
- language_existence：引用的 language 存在性（存在 / 不存在）

### T3：对象名与输入形态因子
- type_name_shape：type 名称形态
- language_name_shape：language 名称形态

### T4：依赖对象与环境因子
- privilege_on_type：对 type 的所有权
- privilege_on_language：对 language 的所有权
- dependency_context：依赖对象驻留情况

### T5：异常与边界因子
- nonexistent_transform：transform 不存在且无 IF EXISTS
- nonexistent_type：引用的 type 不存在
- nonexistent_language：引用的 language 不存在
- insufficient_privilege：缺少 type 或 language 的所有权
- dependent_object_exists：有对象依赖该 transform

### T6：验证与清理因子
- verification_mode：验证方式
- cleanup_mode：清理方式

## 覆盖策略

- 覆盖 DROP TRANSFORM 全部语法分支。
- 覆盖目标 transform 存在 / 不存在路径。
- 覆盖成功路径与失败路径，包括 type/language 所有权边界和依赖对象驻留。
- T1 因子做笛卡尔积覆盖；T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- DROP TRANSFORM 要求执行者同时拥有 type 和 language；缺少任一所有权属于失败路径。
- 必须覆盖目标 transform 存在时的成功删除路径，以及目标 transform 不存在时的失败路径。
- 支持 IF EXISTS 时，必须覆盖不存在对象的代表性 no-op 路径。
- 支持 CASCADE | RESTRICT 时，必须覆盖存在依赖对象下的 RESTRICT 失败与 CASCADE 成功路径。
- DROP TRANSFORM 不涉及 table / column 组合，不需要挂靠基表列类型，但涉及 type 和 language 依赖。
- 每个样本必须包含明确的前置对象准备（type、language、transform）、目标 DROP TRANSFORM 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。

## 挂靠规则

- 附属因子挂靠到代表性成功样本和关键失败样本。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏主覆盖归因。
- 与 type/language 所有权相关的因子必须挂靠到具有明确权限上下文的样本上。

## 规模控制规则

- 优先保证官方语法分支、目标对象存在/不存在、成功/失败路径和权限核心路径。
- 次优先保证 IF EXISTS 子句、CASCADE/RESTRICT 依赖边界代表性覆盖。
- 低优先级命名形态、边界和清理因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: transform
  skill_name: drop_transform
  official_source: https://www.postgresql.org/docs/16/sql-droptransform.html
  statement:
    key: drop_transform
    name: DROP TRANSFORM
    aliases:
    - drop_transform
    - DROP TRANSFORM
    purpose: DROP TRANSFORM — remove a transform
  syntax_templates:
  - "DROP TRANSFORM [ IF EXISTS ] FOR type_name LANGUAGE lang_name [ CASCADE | RESTRICT ]"
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
    - privilege_requirement
    - type_existence
    - language_existence
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - type_name_shape
    - language_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_on_type
    - privilege_on_language
    - dependency_context
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_transform
    - nonexistent_type
    - nonexistent_language
    - insufficient_privilege
    - dependent_object_exists
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
      - key: branch_drop_transform
        label: DROP TRANSFORM FOR type_name LANGUAGE lang_name
      - key: branch_drop_transform_if_exists
        label: DROP TRANSFORM IF EXISTS FOR type_name LANGUAGE lang_name
    object_state:
      label: 目标 transform 对象状态
      importance: important
      values:
      - exists
      - absent
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句开关
      importance: non_important
      values:
      - present
      - absent
    cascade_restrict:
      label: CASCADE / RESTRICT 子句
      importance: non_important
      values:
      - default_restrict
      - explicit_restrict
      - explicit_cascade
    privilege_requirement:
      label: 权限要求
      importance: non_important
      values:
      - own_type_and_language
      - missing_type_ownership
      - missing_language_ownership
    type_existence:
      label: 引用的 type 存在性
      importance: non_important
      values:
      - type_exists
      - type_not_exists
    language_existence:
      label: 引用的 language 存在性
      importance: non_important
      values:
      - language_exists
      - language_not_exists
    type_name_shape:
      label: type 名称形态
      importance: non_important
      values:
      - simple_id
      - schema_qualified_id
      - nonexistent_name
    language_name_shape:
      label: language 名称形态
      importance: non_important
      values:
      - simple_id
      - nonexistent_name
    privilege_on_type:
      label: 对 type 的所有权
      importance: non_important
      values:
      - owns_type
      - not_owns_type
    privilege_on_language:
      label: 对 language 的所有权
      importance: non_important
      values:
      - owns_language
      - not_owns_language
    dependency_context:
      label: 依赖对象驻留情况
      importance: non_important
      values:
      - no_dependencies
      - has_dependent_objects
    nonexistent_transform:
      label: transform 不存在且无 IF EXISTS
      importance: non_important
      values:
      - transform_exists
      - transform_missing_without_if_exists
    nonexistent_type:
      label: 引用的 type 不存在
      importance: non_important
      values:
      - type_exists
      - type_missing
    nonexistent_language:
      label: 引用的 language 不存在
      importance: non_important
      values:
      - language_exists
      - language_missing
    insufficient_privilege:
      label: 缺少 type 或 language 的所有权
      importance: non_important
      values:
      - owns_both
      - missing_type_ownership
      - missing_language_ownership
    dependent_object_exists:
      label: 有对象依赖该 transform
      importance: non_important
      values:
      - no_dependencies
      - has_dependencies
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - error_assertion
      - notice_assertion
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_transform
      - cascade_cleanup
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - cascade_restrict
    - privilege_requirement
    - type_existence
    - language_existence
    - type_name_shape
    - language_name_shape
    - privilege_on_type
    - privilege_on_language
    - dependency_context
    - nonexistent_transform
    - nonexistent_type
    - nonexistent_language
    - insufficient_privilege
    - dependent_object_exists
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "DROP TRANSFORM [ IF EXISTS ] FOR {type_name} LANGUAGE {lang_name} [ CASCADE | RESTRICT ]"
    verification_query_template: "SELECT trftype, trflang FROM pg_transform WHERE trftype = '{type_oid}' AND trflang = '{lang_oid}'"
    factor_value_bindings: {}
```
