# 技能：ALTER SEQUENCE

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-altersequence.html

### Synopsis 形式 1：修改序列参数

```sql
ALTER SEQUENCE [ IF EXISTS ] name
    [ AS data_type ]
    [ INCREMENT [ BY ] increment ]
    [ MINVALUE minvalue | NO MINVALUE ] [ MAXVALUE maxvalue | NO MAXVALUE ]
    [ START [ WITH ] start ]
    [ RESTART [ [ WITH ] restart ] ]
    [ CACHE cache ] [ [ NO ] CYCLE ]
    [ OWNED BY { table_name.column_name | NONE } ]
```

### Synopsis 形式 2：更改日志状态

```sql
ALTER SEQUENCE [ IF EXISTS ] name SET { LOGGED | UNLOGGED }
```

### Synopsis 形式 3：更改 Owner

```sql
ALTER SEQUENCE [ IF EXISTS ] name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
```

### Synopsis 形式 4：重命名

```sql
ALTER SEQUENCE [ IF EXISTS ] name RENAME TO new_name
```

### Synopsis 形式 5：更改 Schema

```sql
ALTER SEQUENCE [ IF EXISTS ] name SET SCHEMA new_schema
```

**重要行为说明**：
- 未显式设置的参数保留先前值。
- AS data_type 仅支持 smallint、integer、bigint；改类型时仅在先前 min/max 来自 NO MINVALUE/NO MAXVALUE 时自动调整，否则保留原值；若值不兼容新类型则报错。
- START WITH 仅改变记录的起始值，不影响当前值；仅设置未来 RESTART（无显式值时）使用的值。
- RESTART [WITH] 改变当前值，等价于 setval(is_called=false)；是事务性的并阻塞并发事务。
- CYCLE 回绕；NO CYCLE 到极限后 nextval 报错。
- SET {LOGGED|UNLOGGED} 不能应用于临时序列。
- OWNED BY 要求关联表与序列同 Owner 同 Schema；替换先前关联；OWNED BY NONE 使序列独立。
- 必须拥有序列才能 ALTER SEQUENCE。
- SET SCHEMA 需要对新 Schema 有 CREATE 权限。
- OWNER TO 需要能 SET ROLE 到新 Owner，且新 Owner 必须对序列所在 Schema 有 CREATE 权限。
- ALTER SEQUENCE 阻塞并发 nextval/currval/lastval/setval 调用。
- 其他后端使用预分配缓存值时不受影响，直到缓存耗尽。

## 语句作用

官方说明：ALTER SEQUENCE — change the definition of a sequence generator

该 reference 关注序列修改语句的语法分支、参数修改、Owner 变更、重命名与 Schema 变更，不负责包装所有样本到统一外层事务。

ALTER SEQUENCE **不直接涉及列类型组合**，但涉及序列数据类型变更（AS data_type）。序列参数修改（INCREMENT、MINVALUE、MAXVALUE、START、RESTART、CACHE、CYCLE、OWNED BY）是本 skill 的核心职责。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（参数修改、SET LOGGED/UNLOGGED、OWNER TO、RENAME TO、SET SCHEMA）
- object_state：目标序列对象存在性（已存在、不存在）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- if_exists_clause：IF EXISTS 子句（present、absent）
- alter_parameter_type：修改参数类型（change_data_type、change_increment、change_minmax、change_start、restart_with、change_cache、change_cycle、change_owned_by、none_parameter）
- logged_unlogged_clause：SET LOGGED / UNLOGGED 子句（LOGGED、UNLOGGED）
- role_specification：角色指定形式（new_owner_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER）

### T3：对象名与输入形态因子
- sequence_name_shape：序列名形态（simple、quoted、reserved_word、schema_qualified）
- new_data_type：新数据类型（smallint、integer、bigint）
- new_owner_shape：新 Owner 名形态（existing_role、non_existing_role、CURRENT_ROLE、CURRENT_USER、SESSION_USER）
- new_schema_name：新 Schema 名形态（existing_schema、non_existing_schema）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、sequence_owner、non_owner）
- owned_by_table_dependency：OWNED BY 表列依赖（same_owner_same_schema、different_owner、different_schema）
- schema_privilege：新 Schema CREATE 权限（has_CREATE、no_CREATE）— 仅 SET SCHEMA
- owner_change_privilege：Owner 变更权限（can_SET_ROLE、cannot_SET_ROLE）
- new_owner_schema_privilege：新 Owner Schema CREATE 权限

### T5：异常与边界因子
- non_existent_sequence：目标序列不存在
- insufficient_privilege：权限不足（非 Owner、不能 SET ROLE）
- data_type_incompatible_values：数据类型与现有值不兼容
- logged_unlogged_on_temporary：SET LOGGED/UNLOGGED 作用于临时序列（非法）
- owned_by_different_owner：OWNED BY 不同 Owner
- owned_by_different_schema：OWNED BY 不同 Schema
- restart_value_out_of_range：RESTART 值超出范围

### T6：验证与清理因子
- verification_mode：验证方式（pg_class_catalog_query、sequence_inspection_query、nextval_call、currval_call）
- cleanup_mode：清理方式（DROP_SEQUENCE、DROP_SEQUENCE_IF_EXISTS、DROP_SEQUENCE_CASCADE）

## 覆盖策略

- 必须覆盖所有五种 ALTER SEQUENCE 语法分支。
- ALTER SEQUENCE 不涉及列类型组合，但 AS data_type 变更必须覆盖。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合或降级为代表性覆盖。
- T3 及之后因子只做轮转挂靠，保证主要取值至少覆盖一次。
- 必须同时保留成功路径与失败路径。
- 参数修改分支需覆盖代表性参数组合。

## 生成约束

- 必须预创建可被修改的目标序列，并为每个 ALTER 分支准备最小合法前置状态。
- 必须覆盖目标序列存在时的成功修改路径、目标序列不存在时的失败路径，以及 IF EXISTS 分支的代表性 no-op 路径。
- 参数修改 / SET LOGGED/UNLOGGED / OWNER TO / RENAME TO / SET SCHEMA 分支需要保持独立归因。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 ALTER SEQUENCE 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- **AS data_type 变更必须参与生成**：smallint、integer、bigint 三种数据类型变更必须在至少一个 ALTER SEQUENCE 样本中出现。
- RESTART WITH 必须覆盖（改变当前值）。
- SET LOGGED/UNLOGGED 不能应用于临时序列，必须作为失败边界覆盖。
- OWNED BY 要求关联表与序列同 Owner 同 Schema，必须作为边界覆盖。
- 对需要 superuser 权限的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 sequence_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 new_data_type 挂靠到参数修改分支（含 AS）的代表性样本。
- T4 因子仅挂靠到需要依赖对象、权限或角色限定的分支。
- T4 因子中 privilege_level 挂靠到所有分支的失败路径。
- T4 因子中 schema_privilege 挂靠到 SET SCHEMA 分支。
- T4 因子中 owner_change_privilege 挂靠到 OWNER TO 分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标对象存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - AS data_type 变更全覆盖（smallint、integer、bigint）
  - 权限核心路径全覆盖
- 次优先保证：
  - 参数组合代表性覆盖（INCREMENT、MINVALUE、MAXVALUE、START、RESTART、CACHE、CYCLE）
  - SET LOGGED/UNLOGGED 代表性覆盖
  - OWNED BY 代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: sequence
  skill_name: alter_sequence
  official_source: https://www.postgresql.org/docs/16/sql-altersequence.html
  statement:
    key: alter_sequence
    name: ALTER SEQUENCE
    aliases:
    - ALTER SEQUENCE
    - alter sequence
    - alter_sequence
    purpose: change the definition of a sequence generator
  syntax_templates:
  - "ALTER SEQUENCE [ IF EXISTS ] name [ AS data_type ] [ INCREMENT [ BY ] increment ] [ MINVALUE minvalue | NO MINVALUE ] [ MAXVALUE maxvalue | NO MAXVALUE ] [ START [ WITH ] start ] [ RESTART [ [ WITH ] restart ] ] [ CACHE cache ] [ [ NO ] CYCLE ] [ OWNED BY { table_name.column_name | NONE } ]"
  - "ALTER SEQUENCE [ IF EXISTS ] name SET { LOGGED | UNLOGGED }"
  - "ALTER SEQUENCE [ IF EXISTS ] name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
  - "ALTER SEQUENCE [ IF EXISTS ] name RENAME TO new_name"
  - "ALTER SEQUENCE [ IF EXISTS ] name SET SCHEMA new_schema"
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
    - alter_parameter_type
    - logged_unlogged_clause
    - role_specification
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - sequence_name_shape
    - new_data_type
    - new_owner_shape
    - new_schema_name
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - owned_by_table_dependency
    - schema_privilege
    - owner_change_privilege
    - new_owner_schema_privilege
  - tier: T5
    name: 异常与边界因子
    factors:
    - non_existent_sequence
    - insufficient_privilege
    - data_type_incompatible_values
    - logged_unlogged_on_temporary
    - owned_by_different_owner
    - owned_by_different_schema
    - restart_value_out_of_range
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
      - key: branch_alter_parameters
        label: ALTER SEQUENCE name [ AS | INCREMENT | MINVALUE | MAXVALUE | START | RESTART | CACHE | CYCLE | OWNED BY ]
      - key: branch_set_logged_unlogged
        label: ALTER SEQUENCE name SET { LOGGED | UNLOGGED }
      - key: branch_owner
        label: ALTER SEQUENCE name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }
      - key: branch_rename
        label: ALTER SEQUENCE name RENAME TO new_name
      - key: branch_set_schema
        label: ALTER SEQUENCE name SET SCHEMA new_schema
    object_state:
      label: 目标序列对象存在性
      importance: important
      values:
      - key: exists
        label: 序列已存在
      - key: not_exists
        label: 序列不存在
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    if_exists_clause:
      label: IF EXISTS 子句
      importance: important
      values:
      - key: absent
        label: 无 IF EXISTS
      - key: present
        label: 包含 IF EXISTS
    alter_parameter_type:
      label: 修改参数类型 (仅参数修改分支)
      importance: important
      values:
      - key: change_data_type
        label: AS data_type 变更
      - key: change_increment
        label: INCREMENT 变更
      - key: change_minmax
        label: MINVALUE/MAXVALUE 变更
      - key: change_start
        label: START WITH 变更
      - key: restart_with
        label: RESTART [WITH] 变更
      - key: change_cache
        label: CACHE 变更
      - key: change_cycle
        label: CYCLE/NO CYCLE 变更
      - key: change_owned_by
        label: OWNED BY 变更
      - key: none_parameter
        label: 无参数修改 (仅确认序列存在)
    logged_unlogged_clause:
      label: SET LOGGED/UNLOGGED (仅SET分支)
      importance: important
      values:
      - key: LOGGED
        label: SET LOGGED
      - key: UNLOGGED
        label: SET UNLOGGED
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
    sequence_name_shape:
      label: 序列名形态
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
    new_data_type:
      label: 新数据类型 (仅AS变更)
      importance: important
      values:
      - key: smallint
        label: AS smallint
      - key: integer
        label: AS integer
      - key: bigint
        label: AS bigint
    new_owner_shape:
      label: 新Owner名形态 (仅OWNER TO)
      importance: non_important
      values:
      - key: existing_role
        label: 已存在角色名
      - key: non_existing_role
        label: 不存在角色名
      - key: CURRENT_ROLE
        label: CURRENT_ROLE
      - key: CURRENT_USER
        label: CURRENT_USER
      - key: SESSION_USER
        label: SESSION_USER
    new_schema_name:
      label: 新Schema名 (仅SET SCHEMA)
      importance: non_important
      values:
      - key: existing_schema
        label: 已存在Schema名
      - key: non_existing_schema
        label: 不存在Schema名
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: sequence_owner
        label: 序列 Owner
      - key: non_owner
        label: 非 Owner 用户
    owned_by_table_dependency:
      label: OWNED BY表列依赖
      importance: non_important
      values:
      - key: same_owner_same_schema
        label: 同Owner同Schema (合法)
      - key: different_owner
        label: 不同Owner → error
      - key: different_schema
        label: 不同Schema → error
    schema_privilege:
      label: 新Schema权限 (仅SET SCHEMA)
      importance: non_important
      values:
      - key: has_CREATE
        label: 对新Schema有CREATE权限
      - key: no_CREATE
        label: 对新Schema无CREATE权限 → error
    owner_change_privilege:
      label: Owner变更权限 (仅OWNER TO)
      importance: non_important
      values:
      - key: can_SET_ROLE
        label: 可以SET ROLE到新Owner
      - key: cannot_SET_ROLE
        label: 不能SET ROLE到新Owner → error
    new_owner_schema_privilege:
      label: 新Owner Schema权限 (仅OWNER TO)
      importance: non_important
      values:
      - key: has_CREATE
        label: 新Owner对序列Schema有CREATE权限
      - key: no_CREATE
        label: 新Owner对序列Schema无CREATE权限 → error
    non_existent_sequence:
      label: 目标序列不存在
      importance: non_important
      values:
      - key: target_not_exists_no_if_exists
        label: 不存在且无IF EXISTS → error
      - key: target_not_exists_with_if_exists
        label: 不存在但有IF EXISTS → notice
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - key: non_owner
        label: 非Owner尝试修改 → error
      - key: cannot_SET_ROLE_to_owner
        label: 不能SET ROLE → error
      - key: no_CREATE_on_new_schema
        label: 无新Schema CREATE权限 → error
    data_type_incompatible_values:
      label: 数据类型与值不兼容
      importance: non_important
      values:
      - key: values_exceed_new_type_range
        label: 现有值超出新数据类型范围 → error
    logged_unlogged_on_temporary:
      label: SET LOGGED/UNLOGGED作用于临时序列
      importance: non_important
      values:
      - key: logged_unlogged_on_temp_illegal
        label: 临时序列不能SET LOGGED/UNLOGGED → error
    owned_by_different_owner:
      label: OWNED BY不同Owner
      importance: non_important
      values:
      - key: table_different_owner
        label: 关联表与序列不同Owner → error
    owned_by_different_schema:
      label: OWNED BY不同Schema
      importance: non_important
      values:
      - key: table_different_schema
        label: 关联表与序列不同Schema → error
    restart_value_out_of_range:
      label: RESTART值超出范围
      importance: non_important
      values:
      - key: restart_exceeds_bounds
        label: RESTART值超出MIN/MAX范围 → error
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_catalog_query
        label: pg_class 系统目录查询
      - key: sequence_inspection_query
        label: SELECT * FROM sequence_name 查询
      - key: nextval_call
        label: nextval() 调用验证
      - key: currval_call
        label: currval() 调用验证
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_SEQUENCE
        label: DROP SEQUENCE sequence_name
      - key: DROP_SEQUENCE_IF_EXISTS
        label: DROP SEQUENCE IF EXISTS sequence_name
      - key: DROP_SEQUENCE_CASCADE
        label: DROP SEQUENCE sequence_name CASCADE
  notes:
    no_column_type_combination: ALTER SEQUENCE 不直接涉及列类型组合，但涉及序列数据类型变更（AS data_type）。
    as_data_type_change: AS data_type 变改时仅在先前 min/max 来自 NO MINVALUE/NO MAXVALUE 时自动调整。
    start_vs_restart: START WITH 仅改变记录起始值；RESTART 改变当前值并阻塞并发事务。
    logged_unlogged_no_temporary: SET LOGGED/UNLOGGED 不能应用于临时序列。
    owned_by_constraints: OWNED BY 要求关联表与序列同 Owner 同 Schema。
    concurrent_behavior: ALTER SEQUENCE 阻塞并发 nextval/currval/lastval/setval 调用。
  defaults:
    expected_status: success
    object_state: exists
    if_exists_clause: absent
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists_clause
    - alter_parameter_type
    - logged_unlogged_clause
    - role_specification
    - sequence_name_shape
    - new_data_type
    - new_owner_shape
    - new_schema_name
    - privilege_level
    - owned_by_table_dependency
    - schema_privilege
    - owner_change_privilege
    - new_owner_schema_privilege
    - non_existent_sequence
    - insufficient_privilege
    - data_type_incompatible_values
    - logged_unlogged_on_temporary
    - owned_by_different_owner
    - owned_by_different_schema
    - restart_value_out_of_range
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER SEQUENCE [ IF EXISTS ] {sequence_name} {alter_action}"
    verification_query_template: "SELECT count(*) FROM pg_class WHERE relname = '{sequence_name}' AND relkind = 'S'"
    factor_value_bindings:
      if_exists_clause:
        absent: ""
        present: "IF EXISTS"
      logged_unlogged_clause:
        LOGGED: "SET LOGGED"
        UNLOGGED: "SET UNLOGGED"
      role_specification:
        new_owner_role: "OWNER TO {new_owner_name}"
        CURRENT_ROLE: "OWNER TO CURRENT_ROLE"
        CURRENT_USER: "OWNER TO CURRENT_USER"
        SESSION_USER: "OWNER TO SESSION_USER"
```
