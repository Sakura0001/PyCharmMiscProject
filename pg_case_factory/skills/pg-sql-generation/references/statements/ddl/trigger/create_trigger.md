# 技能：CREATE TRIGGER

## 官方语法范围

来源：https://www.postgresql.org/docs/16/sql-createtrigger.html

### Synopsis

```sql
CREATE [ OR REPLACE ] [ CONSTRAINT ] TRIGGER name { BEFORE | AFTER | INSTEAD OF } { event [ OR ... ] }
    ON table_name
    [ FROM referenced_table_name ]
    [ NOT DEFERRABLE | [ DEFERRABLE ] [ INITIALLY IMMEDIATE | INITIALLY DEFERRED ] ]
    [ REFERENCING { { OLD | NEW } TABLE [ AS ] transition_relation_name } [ ... ] ]
    [ FOR [ EACH ] { ROW | STATEMENT } ]
    [ WHEN ( condition ) ]
    EXECUTE { FUNCTION | PROCEDURE } function_name ( arguments )
```

### event 子句

```sql
    INSERT
    UPDATE [ OF column_name [, ... ] ]
    DELETE
    TRUNCATE
```

## 语句作用

官方说明：CREATE TRIGGER — define a new trigger

该 reference 关注触发器定义语句的语法分支、触发时机（BEFORE/AFTER/INSTEAD OF）、事件类型（INSERT/UPDATE/DELETE/TRUNCATE）、WHEN 条件、DEFERRABLE/INITIALLY 子句与依赖环境。

CREATE TRIGGER 不直接涉及列数据类型选择，但 WHEN 条件和 UPDATE OF column_name 子句可能引用表中特定列。此外触发器需要依赖已存在的表和触发器函数。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 语法分支（基于 BEFORE/AFTER/INSTEAD OF 的触发器定义）
- trigger_timing：触发时机（BEFORE、AFTER、INSTEAD_OF）
- trigger_event：触发事件（INSERT、UPDATE、DELETE、TRUNCATE、INSERT_OR_UPDATE、UPDATE_OR_DELETE、INSERT_OR_UPDATE_OR_DELETE）
- object_state：目标触发器对象存在性（不存在、已存在同名同表触发器）
- expected_status：预期结果（success、failure）

### T2：重要行为因子
- or_replace_clause：OR REPLACE 子句（present、absent）
- constraint_trigger：CONSTRAINT 关键字（present、absent）
- for_each_clause：FOR EACH 子句（ROW、STATEMENT、absent）
- deferrable_clause：DEFERRABLE 子句（NOT_DEFERRABLE、DEFERRABLE_INITIALLY_IMMEDIATE、DEFERRABLE_INITIALLY_DEFERRED、absent）
- when_clause：WHEN 条件子句（with_WHEN_condition、without_WHEN）
- referencing_clause：REFERENCING 子句（with_OLD_TABLE、with_NEW_TABLE、with_BOTH、absent）
- from_clause：FROM referenced_table_name 子句（present、absent）
- update_of_columns：UPDATE OF column_name 子句（with_column_list、without_column_list）
- execute_clause：EXECUTE 子句形式（FUNCTION、PROCEDURE）

### T3：对象名与输入形态因子
- trigger_name_shape：触发器名形态（simple、quoted、reserved_word、duplicate）
- table_name_shape：表名形态（simple、quoted、schema_qualified）
- function_name_shape：触发器函数名形态（simple、quoted、schema_qualified）
- event_column_list：UPDATE OF 列名列表形态（single_column、multiple_columns、nonexistent_column）

### T4：依赖对象与环境因子
- privilege_level：权限级别（superuser、table_owner、non_owner_with_create_trigger、non_owner_no_privilege）
- table_dependency：表依赖（table_exists、table_not_exists、view_exists_for_INSTEAD_OF、partitioned_table）
- function_dependency：触发器函数依赖（trigger_function_exists、trigger_function_not_exists、function_returns_trigger、function_returns_wrong_type）
- referenced_table_dependency：引用表依赖（referenced_table_exists、referenced_table_not_exists）
- schema_dependency：Schema 依赖（schema_exists、schema_not_exists）

### T5：异常与边界因子
- duplicate_trigger：重名冲突（with_OR_REPLACE_replace、without_OR_REPLACE_error）
- INSTEAD_OF_on_table：INSTEAD OF 用于普通表（非法）
- BEFORE_INSTEAD_OF_on_view：BEFORE/AFTER 用于视图（非法）
- TRUNCATE_with_FOR_EACH_ROW：TRUNCATE 与 FOR EACH ROW 组合（非法）
- UPDATE_OF_nonexistent_column：UPDATE OF 引用不存在列
- constraint_trigger_on_non_constraint_event：CONSTRAINT 触发器与非约束事件组合
- permission_insufficient：权限不足
- referenced_table_not_exists：FROM 引用的表不存在
- identifier_length_exceeded：标识符长度超限

### T6：验证与清理因子
- verification_mode：验证方式（pg_trigger_catalog_query、information_schema_triggers、SELECT_trigger_test）
- cleanup_mode：清理方式（DROP_TRIGGER、DROP_TRIGGER_IF_EXISTS、DROP_TRIGGER_ON_TABLE）

## 覆盖策略

- 必须覆盖所有 CREATE TRIGGER 语法分支。
- 必须覆盖所有触发时机（BEFORE、AFTER、INSTEAD OF）与事件类型组合的合法路径。
- 不需要覆盖每张基表中所有的列类型；仅在 WHEN 条件和 UPDATE OF 子句中引用代表性列类型。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖对象成功创建、重名冲突、非法定义与依赖对象缺失路径。
- 支持 OR REPLACE 时，需要分别覆盖正常创建、替换语义与冲突边界。
- 成功路径必须包含可验证的对象存在性检查，并在生命周期末尾清理对象。
- 对官方语法中出现的每一种顶层 synopsis 形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（创建表、创建触发器函数）、目标 CREATE TRIGGER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。

## 挂靠规则

- T3 因子中 trigger_name_shape 挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T3 因子中 event_column_list 挂靠到包含 UPDATE OF 子句的样本上，轮转注入代表性列名。
- T4 因子中 table_dependency 挂靠到所有分支，确保前置表准备被覆盖。
- T4 因子中 function_dependency 挂靠到所有分支，确保触发器函数准备被覆盖。
- T4 因子中 privilege_level 挂靠到所有分支，确保权限路径被覆盖。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有触发时机全覆盖（BEFORE、AFTER、INSTEAD OF）
  - 所有事件类型全覆盖（INSERT、UPDATE、DELETE、TRUNCATE 及合法组合）
  - 目标对象存在 / 不存在 / 冲突全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - CONSTRAINT 触发器代表性覆盖
  - DEFERRABLE / INITIALLY 子句代表性覆盖
  - WHEN 条件代表性覆盖
  - REFERENCING 子句代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖：
  - FROM referenced_table_name 子句
  - FOR EACH ROW / STATEMENT 各选项
  - identifier 边界条件

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: trigger
  skill_name: create_trigger
  official_source: https://www.postgresql.org/docs/16/sql-createtrigger.html
  statement:
    key: create_trigger
    name: CREATE TRIGGER
    aliases:
    - CREATE TRIGGER
    - create trigger
    - create_trigger
    purpose: define a new trigger
  syntax_templates:
  - |
    CREATE [ OR REPLACE ] [ CONSTRAINT ] TRIGGER name { BEFORE | AFTER | INSTEAD OF } { event [ OR ... ] }
        ON table_name
        [ FROM referenced_table_name ]
        [ NOT DEFERRABLE | [ DEFERRABLE ] [ INITIALLY IMMEDIATE | INITIALLY DEFERRED ] ]
        [ REFERENCING { { OLD | NEW } TABLE [ AS ] transition_relation_name } [ ... ] ]
        [ FOR [ EACH ] { ROW | STATEMENT } ]
        [ WHEN ( condition ) ]
        EXECUTE { FUNCTION | PROCEDURE } function_name ( arguments )
  factor_layers:
  - tier: T1
    name: 核心语义因子
    factors:
    - statement_branch
    - trigger_timing
    - trigger_event
    - object_state
    - expected_status
  - tier: T2
    name: 重要行为因子
    factors:
    - or_replace_clause
    - constraint_trigger
    - for_each_clause
    - deferrable_clause
    - when_clause
    - referencing_clause
    - from_clause
    - update_of_columns
    - execute_clause
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - trigger_name_shape
    - table_name_shape
    - function_name_shape
    - event_column_list
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - table_dependency
    - function_dependency
    - referenced_table_dependency
    - schema_dependency
  - tier: T5
    name: 异常与边界因子
    factors:
    - duplicate_trigger
    - INSTEAD_OF_on_table
    - BEFORE_INSTEAD_OF_on_view
    - TRUNCATE_with_FOR_EACH_ROW
    - UPDATE_OF_nonexistent_column
    - constraint_trigger_on_non_constraint_event
    - permission_insufficient
    - referenced_table_not_exists
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
        label: BEFORE 触发器
      - key: branch_2
        label: AFTER 触发器
      - key: branch_3
        label: INSTEAD OF 触发器（仅用于视图/外部表）
    trigger_timing:
      label: 触发时机
      importance: important
      values:
      - key: BEFORE
        label: BEFORE (事件发生前触发)
      - key: AFTER
        label: AFTER (事件发生后触发)
      - key: INSTEAD_OF
        label: INSTEAD OF (替代事件触发，仅视图/外部表)
    trigger_event:
      label: 触发事件
      importance: important
      values:
      - key: INSERT
        label: INSERT 事件
      - key: UPDATE
        label: UPDATE 事件
      - key: DELETE
        label: DELETE 事件
      - key: TRUNCATE
        label: TRUNCATE 事件
      - key: INSERT_OR_UPDATE
        label: INSERT OR UPDATE 事件组合
      - key: UPDATE_OR_DELETE
        label: UPDATE OR DELETE 事件组合
      - key: INSERT_OR_UPDATE_OR_DELETE
        label: INSERT OR UPDATE OR DELETE 事件组合
    object_state:
      label: 目标触发器对象存在性
      importance: important
      values:
      - key: not_exists
        label: 触发器不存在
      - key: already_exists
        label: 触发器已存在（同名同表）
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
    constraint_trigger:
      label: CONSTRAINT 关键字
      importance: important
      values:
      - key: present
        label: CONSTRAINT TRIGGER
      - key: absent
        label: 普通触发器
    for_each_clause:
      label: FOR EACH 子句
      importance: important
      values:
      - key: ROW
        label: FOR EACH ROW
      - key: STATEMENT
        label: FOR EACH STATEMENT
      - key: absent
        label: 无 FOR EACH 子句
    deferrable_clause:
      label: DEFERRABLE 子句
      importance: important
      values:
      - key: NOT_DEFERRABLE
        label: NOT DEFERRABLE
      - key: DEFERRABLE_INITIALLY_IMMEDIATE
        label: DEFERRABLE INITIALLY IMMEDIATE
      - key: DEFERRABLE_INITIALLY_DEFERRED
        label: DEFERRABLE INITIALLY DEFERRED
      - key: absent
        label: 无 DEFERRABLE 子句（默认 NOT DEFERRABLE）
    when_clause:
      label: WHEN 条件子句
      importance: important
      values:
      - key: with_WHEN_condition
        label: 包含 WHEN (condition) 子句
      - key: without_WHEN
        label: 不包含 WHEN 子句
    referencing_clause:
      label: REFERENCING 子句
      importance: important
      values:
      - key: with_OLD_TABLE
        label: REFERENCING OLD TABLE AS transition_relation
      - key: with_NEW_TABLE
        label: REFERENCING NEW TABLE AS transition_relation
      - key: with_BOTH
        label: REFERENCING OLD TABLE / NEW TABLE
      - key: absent
        label: 无 REFERENCING 子句
    from_clause:
      label: FROM 子句
      importance: important
      values:
      - key: present
        label: 包含 FROM referenced_table_name
      - key: absent
        label: 不包含 FROM 子句
    update_of_columns:
      label: UPDATE OF column_name 子句
      importance: important
      values:
      - key: with_column_list
        label: UPDATE OF column_name [, ...]
      - key: without_column_list
        label: UPDATE (无 OF 限定)
    execute_clause:
      label: EXECUTE 子句形式
      importance: important
      values:
      - key: FUNCTION
        label: EXECUTE FUNCTION function_name
      - key: PROCEDURE
        label: EXECUTE PROCEDURE function_name
    trigger_name_shape:
      label: 触发器名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: reserved_word
        label: 保留字标识符
      - key: duplicate
        label: 已存在触发器名
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: schema_qualified
        label: Schema 限定标识符
    function_name_shape:
      label: 触发器函数名形态
      importance: non_important
      values:
      - key: simple
        label: 合法普通标识符
      - key: quoted
        label: 双引号标识符
      - key: schema_qualified
        label: Schema 限定标识符
    event_column_list:
      label: UPDATE OF 列名列表形态
      importance: non_important
      values:
      - key: single_column
        label: 单列名
      - key: multiple_columns
        label: 多列名列表
      - key: nonexistent_column
        label: 引用不存在列名（失败路径）
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - key: superuser
        label: 超级用户
      - key: table_owner
        label: 表 Owner
      - key: non_owner_with_create_trigger
        label: 非Owner但有CREATE TRIGGER权限
      - key: non_owner_no_privilege
        label: 非Owner且无权限
    table_dependency:
      label: 表依赖
      importance: non_important
      values:
      - key: table_exists
        label: 目标表存在
      - key: table_not_exists
        label: 目标表不存在
      - key: view_exists_for_INSTEAD_OF
        label: 视图存在（用于 INSTEAD OF）
      - key: partitioned_table
        label: 分区表
    function_dependency:
      label: 触发器函数依赖
      importance: non_important
      values:
      - key: trigger_function_exists
        label: 返回 trigger 的函数存在
      - key: trigger_function_not_exists
        label: 触发器函数不存在
      - key: function_returns_trigger
        label: 函数返回类型为 trigger
      - key: function_returns_wrong_type
        label: 函数返回类型不匹配（失败路径）
    referenced_table_dependency:
      label: 引用表依赖
      importance: non_important
      values:
      - key: referenced_table_exists
        label: FROM 引用的表存在
      - key: referenced_table_not_exists
        label: FROM 引用的表不存在
    schema_dependency:
      label: Schema 依赖
      importance: non_important
      values:
      - key: schema_exists
        label: 目标Schema存在
      - key: schema_not_exists
        label: 目标Schema不存在
    duplicate_trigger:
      label: 重名冲突
      importance: non_important
      values:
      - key: with_OR_REPLACE_replace
        label: 重名 + OR REPLACE → 替换
      - key: without_OR_REPLACE_error
        label: 重名 + 无 OR REPLACE → error
    INSTEAD_OF_on_table:
      label: INSTEAD OF 用于普通表
      importance: non_important
      values:
      - key: INSTEAD_OF_INSERT_on_regular_table
        label: INSTEAD OF INSERT on 普通表（非法）
    BEFORE_INSTEAD_OF_on_view:
      label: BEFORE/AFTER 用于视图
      importance: non_important
      values:
      - key: BEFORE_INSERT_on_view
        label: BEFORE INSERT on 视图（非法）
      - key: AFTER_INSERT_on_view
        label: AFTER INSERT on 视图（非法）
    TRUNCATE_with_FOR_EACH_ROW:
      label: TRUNCATE 与 FOR EACH ROW 组合
      importance: non_important
      values:
      - key: TRUNCATE_FOR_EACH_ROW
        label: TRUNCATE + FOR EACH ROW（非法）
    UPDATE_OF_nonexistent_column:
      label: UPDATE OF 引用不存在列
      importance: non_important
      values:
      - key: UPDATE_OF_missing_column
        label: UPDATE OF nonexistent_column（失败路径）
    constraint_trigger_on_non_constraint_event:
      label: CONSTRAINT 触发器与非约束事件
      importance: non_important
      values:
      - key: CONSTRAINT_with_INSTEAD_OF
        label: CONSTRAINT + INSTEAD OF（非法组合）
    permission_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - key: no_create_trigger_privilege
        label: 无CREATE TRIGGER权限
      - key: not_table_owner_for_CONSTRAINT
        label: 非表Owner无法创建CONSTRAINT触发器
    referenced_table_not_exists:
      label: FROM 引用的表不存在
      importance: non_important
      values:
      - key: FROM_table_not_found
        label: FROM referenced_table_name 不存在
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
      - key: pg_trigger_catalog_query
        label: pg_trigger 系统目录查询
      - key: information_schema_triggers
        label: information_schema.triggers 查询
      - key: SELECT_trigger_test
        label: INSERT/UPDATE/DELETE 操作触发测试
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - key: DROP_TRIGGER
        label: DROP TRIGGER name ON table_name
      - key: DROP_TRIGGER_IF_EXISTS
        label: DROP TRIGGER IF EXISTS name ON table_name
      - key: DROP_TRIGGER_ON_TABLE
        label: DROP TRIGGER name ON table_name（随表删除）
  defaults:
    expected_status: success
    or_replace_clause: absent
    constraint_trigger: absent
    for_each_clause: absent
    deferrable_clause: absent
    when_clause: without_WHEN
    referencing_clause: absent
    from_clause: absent
    update_of_columns: without_column_list
    execute_clause: FUNCTION
    object_state: not_exists
  coverage_policy:
    main_combination_axes:
    - trigger_timing
    - trigger_event
    - expected_status
    non_main_factors:
    - or_replace_clause
    - constraint_trigger
    - for_each_clause
    - deferrable_clause
    - when_clause
    - referencing_clause
    - from_clause
    - update_of_columns
    - execute_clause
    - trigger_name_shape
    - table_name_shape
    - function_name_shape
    - event_column_list
    - privilege_level
    - table_dependency
    - function_dependency
    - referenced_table_dependency
    - schema_dependency
    - duplicate_trigger
    - INSTEAD_OF_on_table
    - BEFORE_INSTEAD_OF_on_view
    - TRUNCATE_with_FOR_EACH_ROW
    - UPDATE_OF_nonexistent_column
    - constraint_trigger_on_non_constraint_event
    - permission_insufficient
    - referenced_table_not_exists
    - identifier_length_exceeded
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - trigger_timing
    - trigger_event
  rendering:
    statement_template: "CREATE TRIGGER name { BEFORE | AFTER | INSTEAD OF } { event } ON table_name EXECUTE FUNCTION function_name ()"
    verification_query_template: "SELECT count(*) FROM pg_trigger WHERE tgname = '{trigger_name}'"
    factor_value_bindings:
      trigger_timing:
        BEFORE: "BEFORE"
        AFTER: "AFTER"
        INSTEAD_OF: "INSTEAD OF"
      trigger_event:
        INSERT: "INSERT"
        UPDATE: "UPDATE"
        DELETE: "DELETE"
        TRUNCATE: "TRUNCATE"
        INSERT_OR_UPDATE: "INSERT OR UPDATE"
        UPDATE_OR_DELETE: "UPDATE OR DELETE"
        INSERT_OR_UPDATE_OR_DELETE: "INSERT OR UPDATE OR DELETE"
      or_replace_clause:
        present: "OR REPLACE"
        absent: ""
      constraint_trigger:
        present: "CONSTRAINT"
        absent: ""
      for_each_clause:
        ROW: "FOR EACH ROW"
        STATEMENT: "FOR EACH STATEMENT"
        absent: ""
      deferrable_clause:
        NOT_DEFERRABLE: "NOT DEFERRABLE"
        DEFERRABLE_INITIALLY_IMMEDIATE: "DEFERRABLE INITIALLY IMMEDIATE"
        DEFERRABLE_INITIALLY_DEFERRED: "DEFERRABLE INITIALLY DEFERRED"
        absent: ""
      execute_clause:
        FUNCTION: "EXECUTE FUNCTION"
        PROCEDURE: "EXECUTE PROCEDURE"
```
```