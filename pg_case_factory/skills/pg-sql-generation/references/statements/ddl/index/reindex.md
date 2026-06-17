# 技能：REINDEX

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-reindex.html

```sql
REINDEX [ ( option [, ...] ) ] { INDEX | TABLE | SCHEMA } [ CONCURRENTLY ] name
REINDEX [ ( option [, ...] ) ] { DATABASE | SYSTEM } [ CONCURRENTLY ] [ name ]

where option can be one of:

    CONCURRENTLY [ boolean ]
    TABLESPACE new_tablespace
    VERBOSE [ boolean ]
```

## 语句作用

用于描述 PostgreSQL REINDEX 生成规则。官方说明：rebuild indexes。

这个 skill 承担如下职责：

- 定义测试因子与覆盖策略
- 定义 REINDEX 的 SQL 生成范围
- 标识语法分支、前置依赖、权限边界、成功路径与失败路径

## 语法范围

```sql
REINDEX [ ( option [, ...] ) ] { INDEX | TABLE | SCHEMA } [ CONCURRENTLY ] name
REINDEX [ ( option [, ...] ) ] { DATABASE | SYSTEM } [ CONCURRENTLY ] [ name ]

where option can be one of:

    CONCURRENTLY [ boolean ]
    TABLESPACE new_tablespace
    VERBOSE [ boolean ]
```

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 中的顶层语法分支
  - REINDEX INDEX name
  - REINDEX TABLE name
  - REINDEX SCHEMA name
  - REINDEX DATABASE [ name ]
  - REINDEX SYSTEM [ name ]
- object_state：目标对象状态（已存在、不存在、损坏索引）
- expected_status：预期结果（success / failure / partial_success）

### T2：重要行为因子
- concurrently_keyword：CONCURRENTLY 关键字是否指定（语法后置形式）
- option_concurrently：括号内 CONCURRENTLY [ boolean ] 选项
- option_tablespace：括号内 TABLESPACE new_tablespace 选项
- option_verbose：括号内 VERBOSE [ boolean ] 选项
- boolean_value：CONCURRENTLY / VERBOSE 的 boolean 值形态（TRUE/ON/1/FALSE/OFF/0/省略）
- permission：权限与 owner 差异
  - INDEX/TABLE：需拥有该对象
  - SCHEMA：需拥有该 schema
  - DATABASE/SYSTEM：需拥有该 database（非 superuser 跳过不拥有的 shared catalog）

### T3：对象名与输入形态因子
- name_shape：目标对象名的标识符形态
  - 合法普通标识符
  - schema 限定标识符（INDEX/TABLE/SCHEMA 可 schema 限定；DATABASE/SYSTEM 必须为当前 database 名）
  - 双引号标识符
  - 保留字标识符
  - 已存在对象名
  - 不存在对象名

### T4：依赖对象与环境因子
- index_method：目标索引所属的索引方法（btree/hash/gist/spgist/gin/brin），影响 REINDEX 限制
  - exclusion constraint 索引不支持 CONCURRENTLY
  - partitioned 索引/表 CONCURRENTLY 不能在事务块内
- tablespace_dependency：TABLESPACE 选项依赖预创建 tablespace；系统关系被跳过（发出 WARNING）
- toast_indexes：TOAST 表索引也会被重建（TABLE/SCHEMA/DATABASE 分支）
- partition_behavior：分区索引/表的 REINDEX 在独立事务中处理每个分区；不能在事务块内

### T5：异常与边界因子
- invalid_combination：语义非法的组合
  - CONCURRENTLY + SYSTEM（不允许）
  - CONCURRENTLY + exclusion constraint 索引（不允许）
  - CONCURRENTLY + 事务块内（不允许）
  - DATABASE/SYSTEM name 不匹配当前 database
  - TABLESPACE 用于系统关系（WARNING 跳过）
- concurrent_failure：CONCURRENTLY 构建失败（留下 INVALID 索引，后缀 _ccnew / _ccold）
- syntax_error：语法非法的组合
- permission_insufficient：权限不足

### T6：验证与清理因子
- verification_mode：验证方式（pg_catalog 查询索引有效性、\d 元命令、INVALID 索引检测）
- cleanup_mode：清理方式（删除 INVALID 索引、REINDEX CONCURRENTLY 修复）

## 覆盖策略
- 需要覆盖所有 REINDEX 语法分支（INDEX、TABLE、SCHEMA、DATABASE、SYSTEM）。
- 需要覆盖所有基表。
- 需要覆盖每张基表中所有的列类型。
- T1 和 T2 作为主覆盖因子。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3 及之后因子不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖该命令的所有顶层语法形式、成功路径、失败路径和对象状态验证。
- 需要为会修改对象元数据或物理状态的路径提供前置对象、执行语句、验证语句和清理语句。
- 对不可事务化、需要 superuser 或受环境约束的分支，必须单独标识生命周期边界。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备、目标 REINDEX 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- 对需要 superuser、文件系统、复制连接、tablespace 目录、扩展、外部服务或非事务环境的分支，必须在生命周期计划中显式标注环境依赖。
- CONCURRENTLY 失败后留下的 INVALID 索引必须作为独立边界覆盖。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要索引方法、tablespace、TOAST 索引和分区行为的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖（INDEX、TABLE、SCHEMA、DATABASE、SYSTEM）
  - 目标对象存在 / 不存在 / 损坏全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - CONCURRENTLY 各限制条件代表性覆盖
  - 括号内选项（TABLESPACE、VERBOSE）代表性覆盖
  - partitioned 关系代表性覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 输出要求

- 生成结果应为可执行的 PostgreSQL REINDEX 测试样本集合。
- 输出样本应具备明确因子归因能力。
- 每个样本应标注所属语法分支、预期成功/失败、前置依赖和清理策略。
- 当采用裁剪策略时，应优先保留语句分支、成功/失败路径和对象状态覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: index
  skill_name: reindex
  official_source: https://www.postgresql.org/docs/16/sql-reindex.html
  statement:
    key: reindex
    name: REINDEX
    aliases:
    - reindex
    - 重建索引
    - 索引重建
    - reindex索引
    purpose: 重建索引，覆盖 INDEX、TABLE、SCHEMA、DATABASE、SYSTEM 分支以及 CONCURRENTLY、TABLESPACE、VERBOSE 等选项因子。
  syntax_templates:
  - "REINDEX [ ( option [, ...] ) ] { INDEX | TABLE | SCHEMA } [ CONCURRENTLY ] name"
  - "REINDEX [ ( option [, ...] ) ] { DATABASE | SYSTEM } [ CONCURRENTLY ] [ name ]"
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
    - concurrently_keyword
    - option_concurrently
    - option_tablespace
    - option_verbose
    - boolean_value
    - permission
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - index_method
    - tablespace_dependency
    - toast_indexes
    - partition_behavior
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - concurrent_failure
    - syntax_error
    - permission_insufficient
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification_mode
    - cleanup_mode
  factors:
    statement_branch:
      label: 语句分支
      importance: important
      values:
      - key: reindex_index
        label: REINDEX INDEX
      - key: reindex_table
        label: REINDEX TABLE
      - key: reindex_schema
        label: REINDEX SCHEMA
      - key: reindex_database
        label: REINDEX DATABASE
      - key: reindex_system
        label: REINDEX SYSTEM
    object_state:
      label: 目标对象状态
      importance: important
      values:
      - exists
      - not_exists
      - corrupted_index
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
      - partial_success
    concurrently_keyword:
      label: CONCURRENTLY 关键字（后置形式）
      importance: non_important
      values:
      - "false"
      - "true"
    option_concurrently:
      label: 括号内 CONCURRENTLY 选项
      importance: non_important
      values:
      - absent
      - present_true
      - present_false
      - present_boolean_keyword
    option_tablespace:
      label: 括号内 TABLESPACE 选项
      importance: non_important
      values:
      - absent
      - present_default
      - present_custom
    option_verbose:
      label: 括号内 VERBOSE 选项
      importance: non_important
      values:
      - absent
      - present_true
      - present_false
    boolean_value:
      label: boolean 值形态
      importance: non_important
      values:
      - omitted_default
      - true_keyword
      - on_keyword
      - one_numeric
      - false_keyword
      - off_keyword
      - zero_numeric
    permission:
      label: 权限与 owner
      importance: non_important
      values:
      - owner
      - non_owner
      - superuser
      - insufficient_privilege
    name_shape:
      label: 目标对象名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
      - reserved_word
      - existing_object
      - missing_object
    index_method:
      label: 目标索引方法
      importance: non_important
      values:
      - btree
      - hash
      - gist
      - spgist
      - gin
      - brin
      - exclusion_constraint
    tablespace_dependency:
      label: TABLESPACE 依赖
      importance: non_important
      values:
      - no_tablespace_move
      - move_to_default
      - move_to_custom
      - system_relation_warning
    toast_indexes:
      label: TOAST 索引处理
      importance: non_important
      values:
      - included
      - not_applicable
    partition_behavior:
      label: 分区行为
      importance: non_important
      values:
      - non_partitioned
      - partitioned_separate_transaction
      - partitioned_concurrently_restricted
    invalid_combination:
      label: 语义非法组合
      importance: non_important
      values:
      - concurrently_with_system
      - concurrently_with_exclusion_constraint
      - concurrently_in_transaction
      - database_name_mismatch
      - tablespace_on_system_relation
      - none
    concurrent_failure:
      label: CONCURRENTLY 构建失败
      importance: non_important
      values:
      - none
      - invalid_index_leftover
      - ccnew_suffix
      - ccold_suffix
    syntax_error:
      label: 语法非法组合
      importance: non_important
      values:
      - none
      - invalid_syntax
    permission_insufficient:
      label: 权限不足
      importance: non_important
      values:
      - none
      - non_owner_reindex
      - non_superuser_shared_catalog
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_validity_check
      - invalid_index_detection
      - verbose_output_check
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_invalid_index
      - reindex_concurrently_fix
      - rollback
  defaults:
    object_state: exists
    expected_status: success
    concurrently_keyword: "false"
    option_concurrently: absent
    option_tablespace: absent
    option_verbose: absent
    boolean_value: omitted_default
    permission: owner
    name_shape: plain_identifier
    index_method: btree
    tablespace_dependency: no_tablespace_move
    toast_indexes: included
    partition_behavior: non_partitioned
    invalid_combination: none
    concurrent_failure: none
    syntax_error: none
    permission_insufficient: none
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - concurrently_keyword
    - option_concurrently
    - option_tablespace
    - option_verbose
    - boolean_value
    - permission
    - name_shape
    - index_method
    - tablespace_dependency
    - toast_indexes
    - partition_behavior
    - invalid_combination
    - concurrent_failure
    - syntax_error
    - permission_insufficient
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "REINDEX {option_clause}{target_type} {concurrently_clause}{target_name};"
    verification_query_template: "SELECT c.relname, i.indisvalid FROM pg_class c JOIN pg_index i ON i.indexrelid = c.oid WHERE c.relname = '{index_name}';"
    factor_value_bindings:
      target_type:
        factor: statement_branch
        values:
          reindex_index: "INDEX"
          reindex_table: "TABLE"
          reindex_schema: "SCHEMA"
          reindex_database: "DATABASE"
          reindex_system: "SYSTEM"
      concurrently_clause:
        factor: concurrently_keyword
        values:
          "false": ""
          "true": "CONCURRENTLY "
      option_clause:
        factor: option_concurrently
        values:
          absent: ""
          present_true: "(CONCURRENTLY TRUE) "
          present_false: "(CONCURRENTLY FALSE) "
```
