# 技能：ALTER TYPE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altertype.html

### Synopsis 形式 1：更改 Owner

```sql
ALTER TYPE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
```

### Synopsis 形式 2：重命名类型

```sql
ALTER TYPE name RENAME TO new_name
```

### Synopsis 形式 3：更改 Schema

```sql
ALTER TYPE name SET SCHEMA new_schema
```

### Synopsis 形式 4：重命名属性（仅复合类型）

```sql
ALTER TYPE name RENAME ATTRIBUTE attribute_name TO new_attribute_name [ CASCADE | RESTRICT ]
```

### Synopsis 形式 5：复合操作（仅复合类型）

```sql
ALTER TYPE name action [, ... ]
```

where action is one of:

```sql
    ADD ATTRIBUTE attribute_name data_type [ COLLATE collation ] [ CASCADE | RESTRICT ]
    DROP ATTRIBUTE [ IF EXISTS ] attribute_name [ CASCADE | RESTRICT ]
    ALTER ATTRIBUTE attribute_name [ SET DATA ] TYPE data_type [ COLLATE collation ] [ CASCADE | RESTRICT ]
```

### Synopsis 形式 6：添加枚举值（仅枚举类型）

```sql
ALTER TYPE name ADD VALUE [ IF NOT EXISTS ] new_enum_value [ { BEFORE | AFTER } neighbor_enum_value ]
```

### Synopsis 形式 7：重命名枚举值（仅枚举类型）

```sql
ALTER TYPE name RENAME VALUE existing_enum_value TO new_enum_value
```

### Synopsis 形式 8：设置基础类型属性

```sql
ALTER TYPE name SET ( property = value [, ... ] )
```

**重要行为说明**：
- ALTER TYPE 有八种形式：OWNER TO、RENAME TO、SET SCHEMA、RENAME ATTRIBUTE、复合操作（ADD/DROP/ALTER ATTRIBUTE）、ADD VALUE、RENAME VALUE、SET 属性。
- 必须拥有该类型才能使用 ALTER TYPE。
- SET SCHEMA 需要对新 Schema 有 CREATE 权限。
- OWNER TO 需要能 SET ROLE 到新 Owner，且新 Owner 必须对类型所在 Schema 有 CREATE 权限。
- 复合操作中 ADD ATTRIBUTE/ALTER ATTRIBUTE 需要对属性数据类型有 USAGE 权限。
- CASCADE/RESTRICT 默认为 RESTRICT；CASCADE 会将操作传播到使用该类型的 typed table。
- 枚举 ADD VALUE 在事务块内执行时，新值在事务提交前不可使用。
- 枚举比较性能可能降低（特别是 BEFORE/AFTER 插入时）；修复方法是重建枚举类型。
- SET 属性更改（RECEIVE/SEND/TYPMOD_IN/TYPMOD_OUT/ANALYZE/SUBSCRIPT/STORAGE）需要超级用户权限。
- STORAGE 从 plain 改为其他需要超级用户；从其他改回 plain 永远不允许。
- 复合操作（ADD/DROP/ALTER ATTRIBUTE）可在同一命令中组合。

## 语句作用

官方说明：ALTER TYPE — change the definition of a type

该 reference 关注类型修改语句的语法分支、重命名语义、Owner 变更、属性修改、枚举值操作与权限边界，不负责包装所有样本到统一外层事务。

ALTER TYPE **涉及类型定义修改**，具体表现为：
- 复合类型属性的数据类型变更（ALTER ATTRIBUTE TYPE）
- 复合类型属性的添加/删除（ADD/DROP ATTRIBUTE）
- 枚举值的添加/重命名（ADD VALUE / RENAME VALUE）
- 基础类型属性设置（SET 属性）

八种形式各自有不同的依赖和约束，需要分别覆盖。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（OWNER TO、RENAME TO、SET SCHEMA、RENAME ATTRIBUTE、ADD ATTRIBUTE、DROP ATTRIBUTE、ALTER ATTRIBUTE TYPE、ADD VALUE、RENAME VALUE、SET 属性）
- object_state：目标 Type 对象存在性（已存在、不存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- type_category：目标类型类别（composite、enum、base、shell）
- cascade_restrict：CASCADE / RESTRICT 行为（仅复合操作与 RENAME ATTRIBUTE）
- if_exists_clause：IF EXISTS 子句（仅 DROP ATTRIBUTE）
- if_not_exists_clause：IF NOT EXISTS 子句（仅 ADD VALUE）
- enum_position_clause：枚举值位置子句（BEFORE、AFTER、absent）— 仅 ADD VALUE
- role_specification：角色指定形式（new_owner_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER）

### T3：对象名与输入形态因子
- type_name_shape：类型名形态（simple、quoted、reserved_word、schema_qualified）
- attribute_name_shape：属性名形态（simple、quoted、reserved_word）— 仅复合类型操作
- new_attribute_type：新属性数据类型— 仅 ALTER ATTRIBUTE TYPE
- new_enum_value_shape：新枚举值形态（simple_value、quoted_value、long_value）— 仅 ADD VALUE / RENAME VALUE

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、type_owner、non_owner）
- typed_table_dependency：Typed table 依赖（no_typed_tables、has_typed_tables）— 仅复合操作
- attribute_usage_privilege：属性数据类型 USAGE 权限（has_USAGE、no_USAGE）— 仅 ADD/ALTER ATTRIBUTE
- owner_change_privilege：Owner 变更权限（can_SET_ROLE、cannot_SET_ROLE）
- schema_privilege：新 Schema CREATE 权限（has_CREATE、no_CREATE）— 仅 SET SCHEMA
- new_owner_schema_privilege：新 Owner Schema CREATE 权限
- enum_transaction_state：事务状态（inside_transaction、outside_transaction）— 仅 ADD VALUE

### T5：异常与边界因子
- non_existent_type：目标类型不存在
- non_existent_attribute：属性不存在（仅 DROP/ALTER ATTRIBUTE 无 IF EXISTS）
- insufficient_privilege：权限不足（非 Owner、非 superuser 对 SET 属性）
- cascade_with_typed_tables：CASCADE 与 typed table 传播
- restrict_with_typed_tables：RESTRICT 拒绝 typed table 依赖
- enum_value_conflict：枚举值已存在（仅 ADD VALUE 无 IF NOT EXISTS）
- storage_plain_to_other_requires_superuser：STORAGE 从 plain 改为其他需 superuser
- storage_other_to_plain_never_allowed：STORAGE 从其他改回 plain 不允许

### T6：验证与清理因子
- verification_mode：验证方式（pg_type_catalog_query、pg_attribute_query、information_schema_user_defined_types、enum_value_query）
- cleanup_mode：清理方式（DROP_TYPE、DROP_TYPE_IF_EXISTS、DROP_TYPE_CASCADE）

## 覆盖策略

- 必须覆盖所有八种 ALTER TYPE 语法分支。
- **必须覆盖类型定义修改**：复合类型属性数据类型变更、枚举值操作必须在至少一个 ALTER TYPE 样本中出现。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。

## 生成约束

- 必须预创建可被修改的目标类型，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标类型存在时的成功修改路径、目标类型不存在时的失败路径。
- OWNER TO / RENAME TO / SET SCHEMA / RENAME ATTRIBUTE / ADD ATTRIBUTE / DROP ATTRIBUTE / ALTER ATTRIBUTE / ADD VALUE / RENAME VALUE / SET 属性 分支需要保持独立归因。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER TYPE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- **类型定义修改必须参与生成**：复合类型属性数据类型变更、枚举值添加/重命名必须在至少一个 ALTER TYPE 样本中出现。
- ADD VALUE 在事务块内新值不可用，必须作为边界覆盖。
- 对需要 superuser 权限的分支（SET 属性），必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 new_attribute_type 挂靠到 ALTER ATTRIBUTE TYPE 分支的代表性成功样本，按数据类型类别轮转注入。
- T3 因子中 type_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 new_enum_value_shape 挂靠到 ADD VALUE / RENAME VALUE 分支。
- T4 因子仅挂靠到需要依赖对象、权限或角色限定的分支。
- T4 因子中 privilege_level 挂靠到所有分支的失败路径。
- T4 因子中 typed_table_dependency 挂靠到 CASCADE/RESTRICT 分支。
- T4 因子中 enum_transaction_state 挂靠到 ADD VALUE 分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 复合类型属性数据类型变更代表性覆盖
  - 枚举值操作（ADD VALUE / RENAME VALUE）代表性覆盖
  - CASCADE/RESTRICT 与 typed table 传播代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: type
  skill_name: alter_type
  official_source: https://www.postgresql.org/docs/16/sql-altertype.html
  statement:
    key: alter_type
    name: ALTER TYPE
    aliases:
    - ALTER TYPE
    - alter type
    - alter_type
    purpose: change the definition of a type
  syntax_templates:
  - "ALTER TYPE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER TYPE name RENAME TO new_name"
  - "ALTER TYPE name SET SCHEMA new_schema"
  - "ALTER TYPE name RENAME ATTRIBUTE attribute_name TO new_attribute_name [ CASCADE | RESTRICT ]"
  - "ALTER TYPE name action [, ... ]"
  - "ALTER TYPE name ADD VALUE [ IF NOT EXISTS ] new_enum_value [ { BEFORE | AFTER } neighbor_enum_value ]"
  - "ALTER TYPE name RENAME VALUE existing_enum_value TO new_enum_value"
  - "ALTER TYPE name SET ( property = value [, ... ] )"
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
    - type_category
    - cascade_restrict
    - if_exists_clause
    - if_not_exists_clause
    - enum_position_clause
    - role_specification
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - type_name_shape
    - attribute_name_shape
    - new_attribute_type
    - new_enum_value_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - typed_table_dependency
    - attribute_usage_privilege
    - owner_change_privilege
    - schema_privilege
    - new_owner_schema_privilege
    - enum_transaction_state
  - tier: T5
    name: 异常与边界因子
    factors:
    - non_existent_type
    - non_existent_attribute
    - insufficient_privilege
    - cascade_with_typed_tables
    - restrict_with_typed_tables
    - enum_value_conflict
    - storage_plain_to_other_requires_superuser
    - storage_other_to_plain_never_allowed
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
      - key: branch_owner
        label: ALTER TYPE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_rename
        label: ALTER TYPE name RENAME TO new_name
      - key: branch_set_schema
        label: ALTER TYPE name SET SCHEMA new_schema
      - key: branch_rename_attribute
        label: ALTER TYPE name RENAME ATTRIBUTE attribute_name TO new_attribute_name [ CASCADE | RESTRICT ]
      - key: branch_add_attribute
        label: ALTER TYPE name ADD ATTRIBUTE attribute_name data_type [ COLLATE collation ] [ CASCADE | RESTRICT ]
      - key: branch_drop_attribute
        label: ALTER TYPE name DROP ATTRIBUTE [ IF EXISTS ] attribute_name [ CASCADE | RESTRICT ]
      - key: branch_alter_attribute_type
        label: ALTER TYPE name ALTER ATTRIBUTE attribute_name [ SET DATA ] TYPE data_type [ COLLATE collation ] [ CASCADE | RESTRICT ]
      - key: branch_add_value
        label: ALTER TYPE name ADD VALUE [ IF NOT EXISTS ] new_enum_value [ { BEFORE | AFTER } neighbor_enum_value ]
      - key: branch_rename_value
        label: ALTER TYPE name RENAME VALUE existing_enum_value TO new_enum_value
      - key: branch_set_property
        label: ALTER TYPE name SET ( property = value [, ... ] )
    object_state:
      label: 目标Type对象存在性
      importance: important
      values:
      - key: exists
        label: 类型已存在
      - key: not_exists
        label: 类型不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    type_category:
      label: 目标类型类别
      importance: important
      values:
      - key: composite
        label: 复合类型
      - key: enum
        label: 枚举类型
      - key: base
        label: 基础类型
      - key: shell
        label: Shell 类型
    cascade_restrict:
      label: CASCADE / RESTRICT 行为
      importance: important
      values:
      - key: none
        label: 无 CASCADE/RESTRICT (默认RESTRICT)
      - key: cascade
        label: CASCADE
      - key: restrict
        label: RESTRICT
    if_exists_clause:
      label: IF EXISTS 子句 (仅DROP ATTRIBUTE)
      importance: important
      values:
      - key: absent
        label: 无 IF EXISTS
      - key: present
        label: 包含 IF EXISTS
    if_not_exists_clause:
      label: IF NOT EXISTS 子句 (仅ADD VALUE)
      importance: important
      values:
      - key: absent
        label: 无 IF NOT EXISTS
      - key: present
        label: 包含 IF NOT EXISTS
    enum_position_clause:
      label: 枚举值位置子句 (仅ADD VALUE)
      importance: important
      values:
      - key: absent
        label: 无 BEFORE/AFTER (追加到末尾)
      - key: BEFORE
        label: BEFORE neighbor_value
      - key: AFTER
        label: AFTER neighbor_value
    role_specification:
      label: 角色指定形式 (仅OWNER TO)
      importance: important
      values:
      - key: new_owner_role
        label: 显式角色名
      - key: CURRENT_ROLE
        label: CURRENT_ROLE
      - key: CURRENT_USER
        label: CURRENT_USER
      - key: SESSION_USER
        label: SESSION_USER
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
      - key: schema_qualified
        label: Schema限定标识符
    attribute_name_shape:
      label: 属性名形态 (仅复合类型操作)
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
    new_attribute_type:
      label: 新属性数据类型 (仅ALTER ATTRIBUTE TYPE)
      importance: important
      values:
      - key: integer
        label: integer
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
    new_enum_value_shape:
      label: 新枚举值形态 (仅ADD VALUE / RENAME VALUE)
      importance: non_important
      values:
      - key: simple_value
        label: 简单合法枚举值
      - key: quoted_value
        label: 需引号枚举值
      - key: long_value
        label: 长枚举值
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: type_owner
        label: 类型 Owner
      - key: non_owner
        label: 非 Owner 用户
    typed_table_dependency:
      label: Typed table依赖 (仅复合操作)
      importance: non_important
      values:
      - key: no_typed_tables
        label: 无 typed table 依赖
      - key: has_typed_tables
        label: 存在 typed table 依赖
    attribute_usage_privilege:
      label: 属性数据类型USAGE权限 (仅ADD/ALTER ATTRIBUTE)
      importance: non_important
      values:
      - key: has_USAGE
        label: 对属性数据类型有USAGE权限
      - key: no_USAGE
        label: 对属性数据类型无USAGE权限 → error
    owner_change_privilege:
      label: Owner变更权限
      importance: non_important
      values:
      - key: can_SET_ROLE
        label: 可以SET ROLE到新Owner
      - key: cannot_SET_ROLE
        label: 不能SET ROLE到新Owner → error
    schema_privilege:
      label: 新Schema权限 (仅SET SCHEMA)
      importance: non_important
      values:
      - key: has_CREATE
        label: 对新Schema有CREATE权限
      - key: no_CREATE
        label: 对新Schema无CREATE权限 → error
    new_owner_schema_privilege:
      label: 新Owner Schema权限 (仅OWNER TO)
      importance: non_important
      values:
      - key: has_CREATE
        label: 新Owner对类型Schema有CREATE权限
      - key: no_CREATE
        label: 新Owner对类型Schema无CREATE权限 → error
    enum_transaction_state:
      label: 事务状态 (仅ADD VALUE)
      importance: non_important
      values:
      - key: inside_transaction
        label: 事务块内执行 (新值提交前不可用)
      - key: outside_transaction
        label: 非事务块内执行 (新值立即可用)
    non_existent_type:
      label: 目标类型不存在
      importance: non_important
      values:
      - key: target_not_exists
        label: 目标类型不存在 → error
    non_existent_attribute:
      label: 属性不存在
      importance: non_important
      values:
      - key: attribute_not_exists_no_if_exists
        label: 属性不存在且无IF EXISTS → error
      - key: attribute_not_exists_with_if_exists
        label: 属性不存在但有IF EXISTS → notice
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_owner
        label: 非Owner尝试修改 → error
      - key: non_superuser_set_property
        label: 非superuser执行SET属性 → error
      - key: no_USAGE_on_attribute_type
        label: 无USAGE权限于属性数据类型 → error
    cascade_with_typed_tables:
      label: CASCADE与typed table传播
      importance: non_important
      values:
      - key: cascade_propagates_to_typed_tables
        label: CASCADE将操作传播到typed table
    restrict_with_typed_tables:
      label: RESTRICT拒绝typed table依赖
      importance: non_important
      values:
      - key: restrict_refuses_typed_tables
        label: RESTRICT拒绝存在typed table依赖的操作 → error
    enum_value_conflict:
      label: 枚举值冲突 (仅ADD VALUE)
      importance: non_important
      values:
      - key: value_exists_no_if_not_exists
        label: 枚举值已存在且无IF NOT EXISTS → error
      - key: value_exists_with_if_not_exists
        label: 枚举值已存在但有IF NOT EXISTS → no-op
    storage_plain_to_other_requires_superuser:
      label: STORAGE从plain改为其他需superuser
      importance: non_important
      values:
      - key: plain_to_extended_requires_superuser
        label: STORAGE从plain改为extended需superuser
    storage_other_to_plain_never_allowed:
      label: STORAGE从其他改回plain不允许
      importance: non_important
      values:
      - key: other_to_plain_never_allowed
        label: STORAGE从extended改回plain永远不允许 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_type_catalog_query
        label: pg_type 系统目录查询
      - key: pg_attribute_query
        label: pg_attribute 属性查询
      - key: information_schema_user_defined_types
        label: information_schema.user_defined_types 查询
      - key: enum_value_query
        label: pg_enum 枚举值查询
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
    type_definition_modification: ALTER TYPE 涉及类型定义修改（属性数据类型变更、枚举值操作等），不同形式各自有不同的依赖和约束。
    cascade_restrict_on_typed_tables: CASCADE/RESTRICT 默认为 RESTRICT；CASCADE 会将操作传播到 typed table。
    enum_add_value_in_transaction: ADD VALUE 在事务块内新值提交前不可用。
    set_property_requires_superuser: SET 属性更改（RECEIVE/SEND等）需要超级用户权限。
    storage_plain_constraint: STORAGE 从 plain 改为其他需 superuser；从其他改回 plain 不允许。
    composite_action_combination: ADD/DROP/ALTER ATTRIBUTE 可在同一命令中组合。
  defaults:
    expected_status: success
    object_state: exists
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - type_category
    - cascade_restrict
    - if_exists_clause
    - if_not_exists_clause
    - enum_position_clause
    - role_specification
    - type_name_shape
    - attribute_name_shape
    - new_attribute_type
    - new_enum_value_shape
    - privilege_level
    - typed_table_dependency
    - attribute_usage_privilege
    - owner_change_privilege
    - schema_privilege
    - new_owner_schema_privilege
    - enum_transaction_state
    - non_existent_type
    - non_existent_attribute
    - insufficient_privilege
    - cascade_with_typed_tables
    - restrict_with_typed_tables
    - enum_value_conflict
    - storage_plain_to_other_requires_superuser
    - storage_other_to_plain_never_allowed
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER TYPE {type_name} {alter_action}"
    verification_query_template: "SELECT count(*) FROM pg_type WHERE typname = '{type_name}'"
    factor_value_bindings:
      cascade_restrict:
        none: ""
        cascade: "CASCADE"
        restrict: "RESTRICT"
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      if_not_exists_clause:
        absent: ""
        present: "IF NOT EXISTS"
      enum_position_clause:
        absent: ""
        BEFORE: "BEFORE {neighbor_value}"
        AFTER: "AFTER {neighbor_value}"
```
