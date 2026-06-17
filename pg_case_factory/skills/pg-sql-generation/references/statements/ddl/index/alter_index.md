# 技能：ALTER INDEX

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-alterindex.html

```sql
ALTER INDEX [ IF EXISTS ] name RENAME TO new_name
ALTER INDEX [ IF EXISTS ] name SET TABLESPACE tablespace_name
ALTER INDEX name ATTACH PARTITION index_name
ALTER INDEX name [ NO ] DEPENDS ON EXTENSION extension_name
ALTER INDEX [ IF EXISTS ] name SET ( storage_parameter [= value] [, ... ] )
ALTER INDEX [ IF EXISTS ] name RESET ( storage_parameter [, ... ] )
ALTER INDEX [ IF EXISTS ] name ALTER [ COLUMN ] column_number
    SET STATISTICS integer
ALTER INDEX ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]
    SET TABLESPACE new_tablespace [ NOWAIT ]
```

## 语句作用

用于描述 PostgreSQL ALTER INDEX 生成规则。该语句用于修改已有索引的定义，可覆盖索引重命名、迁移表空间、挂接分区索引、声明扩展依赖、调整存储参数、设置统计信息，以及对指定 tablespace 下全部索引做批量迁移。

这个 skill 承担如下职责：

- 定义测试因子与覆盖策略
- 定义 ALTER INDEX 的 SQL 生成范围
- 标识各语法分支的前置依赖与失败路径边界

## 语法范围

ALTER INDEX [ IF EXISTS ] name RENAME TO new_name
ALTER INDEX [ IF EXISTS ] name SET TABLESPACE tablespace_name
ALTER INDEX name ATTACH PARTITION index_name
ALTER INDEX name [ NO ] DEPENDS ON EXTENSION extension_name
ALTER INDEX [ IF EXISTS ] name SET ( storage_parameter [= value] [, ... ] )
ALTER INDEX [ IF EXISTS ] name RESET ( storage_parameter [, ... ] )
ALTER INDEX [ IF EXISTS ] name ALTER [ COLUMN ] column_number
    SET STATISTICS integer
ALTER INDEX ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]
    SET TABLESPACE new_tablespace [ NOWAIT ]

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方 synopsis 中的顶层语法分支
- object_state：目标索引对象状态（已存在、不存在）
- expected_status：预期结果（success / failure / no_op）

### T2：重要行为因子
- if_exists：IF EXISTS 是否指定（仅 RENAME、SET TABLESPACE、SET、RESET、SET STATISTICS 分支支持）
- no_keyword：NO 是否指定（仅 DEPENDS ON EXTENSION 分支）
- column_keyword：COLUMN 是否显式携带（仅 SET STATISTICS 分支）
- owned_by：ALL IN TABLESPACE 是否携带 OWNED BY
- nowait：ALL IN TABLESPACE 是否携带 NOWAIT

### T3：对象名与输入形态因子
- name_shape：索引名 / 新名 / tablespace 名 / partition 索引名 / extension 名 / role 名 的标识符形态
  - 合法普通标识符
  - schema 限定标识符
  - 双引号标识符
  - 保留字标识符
  - 已存在对象名
  - 不存在对象名

### T4：依赖对象与环境因子
- storage_parameter_set：SET 分支的 storage_parameter 组合形态（单个 / 多个、显式 value / 不显式 value）
- storage_parameter_reset：RESET 分支的 storage_parameter 组合形态（单个 / 多个）
- statistics_value：SET STATISTICS 的数值形态（0 / 正整数 / -1 / 越界值）
- column_number_value：ALTER COLUMN 的列号形态（正整数 / 0 / 越界值）
- index_method：目标索引所属的索引方法，影响可用 storage_parameter（btree: fillfactor/deduplicate_items; gist: fillfactor/buffering; gin: fastupdate/gin_pending_list_limit; brin: pages_per_range/autosummarize; hash/spgist: fillfactor）

### T5：异常与边界因子
- invalid_combination：语法合法但语义非法的组合
  - 不存在的索引 + 无 IF EXISTS
  - ATTACH PARTITION 的子分区索引定义不匹配
  - 系统目录索引修改
  - SET STATISTICS 列号越界
- syntax_error：语法非法的组合
- permission_boundary：权限不足（非 owner 修改索引、无 CREATE 权限迁移 tablespace）

### T6：验证与清理因子
- verification_mode：验证方式（pg_catalog 查询、\d 元命令）
- cleanup_mode：清理方式（DROP INDEX、RESET 参数）

## 覆盖策略
- 需要覆盖所有 ALTER INDEX 语法分支。
- 需要覆盖所有基表。
- 需要覆盖每张基表中所有的列类型。
- T1 和 T2 作为主覆盖因子。
- T1 因子做笛卡尔积覆盖。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- IF EXISTS 仅挂到支持 IF EXISTS 的分支（RENAME、SET TABLESPACE、SET、RESET、SET STATISTICS）。
- NO 仅挂到 DEPENDS ON EXTENSION 分支。
- COLUMN 仅挂到 SET STATISTICS 分支。
- OWNED BY / NOWAIT 仅挂到 ALL IN TABLESPACE 分支。
- T3 及之后因子不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖所有基表列类型。
- 必须覆盖已有索引成功修改的路径。
- 必须覆盖目标索引不存在、但 IF EXISTS 缺失时的失败路径。
- 必须覆盖目标索引不存在、但 IF EXISTS 存在时的代表性 no-op 路径。
- ATTACH PARTITION 仅能挂到已准备好父分区索引与子分区索引的生命周期样本。
- SET TABLESPACE 与 ALL IN TABLESPACE ... SET TABLESPACE 的成功路径依赖预创建 tablespace。
- DEPENDS ON EXTENSION 的成功路径依赖扩展存在。
- OWNED BY 的成功路径依赖角色存在；角色数量变化应保留代表性覆盖。
- SET ( storage_parameter = value ) 与 RESET ( storage_parameter ) 既要覆盖合法组合，也要覆盖语法或语义非法组合。
- column_number / statistics_value 的非法数值形态应作为失败路径保留，不得误判为成功样本。

## 挂靠规则

- T3 因子挂靠到 RENAME、SET TABLESPACE、ATTACH PARTITION、DEPENDS ON EXTENSION、ALL IN TABLESPACE 等代表性分支上轮转注入。
- T4 因子仅挂靠到 SET STORAGE 与 RESET STORAGE 分支（storage_parameter），以及 SET STATISTICS 分支（statistics_value / column_number）。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得破坏语句分支与成功/失败归因的可识别性。

## 规模控制规则

- 优先保证：
  - 各语句分支全覆盖
  - 语法开关代表性覆盖
  - 已存在 / 不存在 / 非法标识符输入全覆盖
  - 成功 / 失败路径全覆盖
- 次优先保证：
  - storage_parameter 写法全覆盖
  - 数值输入形态全覆盖
  - OWNED BY 角色数量全覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 输出要求

- 生成结果应为可执行的 PostgreSQL ALTER INDEX 测试样本集合。
- 输出样本应具备明确因子归因能力。
- 对于依赖分区索引、tablespace、extension、role 的分支，应在生命周期计划里显式准备前置对象。
- 当采用裁剪策略时，应优先保留语句分支、成功/失败路径和标识符输入形态的覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: index
  skill_name: alter_index
  official_source: https://www.postgresql.org/docs/16/sql-alterindex.html
  statement:
    key: alter_index
    name: ALTER INDEX
    aliases:
    - alter index
    - 修改索引
    - 索引修改
    - 重命名索引
    - 索引重命名
    purpose: 修改已有索引的定义，覆盖重命名、迁移表空间、挂接分区索引、声明扩展依赖、调整存储参数、设置统计信息和批量迁移等分支。
  syntax_templates:
  - "ALTER INDEX [ IF EXISTS ] name RENAME TO new_name"
  - "ALTER INDEX [ IF EXISTS ] name SET TABLESPACE tablespace_name"
  - "ALTER INDEX name ATTACH PARTITION index_name"
  - "ALTER INDEX name [ NO ] DEPENDS ON EXTENSION extension_name"
  - "ALTER INDEX [ IF EXISTS ] name SET ( storage_parameter [= value] [, ... ] )"
  - "ALTER INDEX [ IF EXISTS ] name RESET ( storage_parameter [, ... ] )"
  - "ALTER INDEX [ IF EXISTS ] name ALTER [ COLUMN ] column_number SET STATISTICS integer"
  - "ALTER INDEX ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ] SET TABLESPACE new_tablespace [ NOWAIT ]"
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
    - if_exists
    - no_keyword
    - column_keyword
    - owned_by
    - nowait
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - storage_parameter_set
    - storage_parameter_reset
    - statistics_value
    - column_number_value
    - index_method
  - tier: T5
    name: 异常与边界因子
    factors:
    - invalid_combination
    - syntax_error
    - permission_boundary
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
      - key: rename
        label: RENAME TO
      - key: set_tablespace
        label: SET TABLESPACE
      - key: attach_partition
        label: ATTACH PARTITION
      - key: depends_on_extension
        label: DEPENDS ON EXTENSION
      - key: no_depends_on_extension
        label: NO DEPENDS ON EXTENSION
      - key: set_storage
        label: SET ( storage_parameter )
      - key: reset_storage
        label: RESET ( storage_parameter )
      - key: set_statistics
        label: ALTER COLUMN SET STATISTICS
      - key: all_in_tablespace
        label: ALL IN TABLESPACE SET TABLESPACE
    object_state:
      label: 目标索引对象状态
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
      - no_op
    if_exists:
      label: IF EXISTS
      importance: non_important
      values:
      - "false"
      - "true"
    no_keyword:
      label: NO 关键字
      importance: non_important
      values:
      - "false"
      - "true"
    column_keyword:
      label: COLUMN 关键字
      importance: non_important
      values:
      - "false"
      - "true"
    owned_by:
      label: OWNED BY
      importance: non_important
      values:
      - absent
      - single_role
      - multiple_roles
    nowait:
      label: NOWAIT
      importance: non_important
      values:
      - "false"
      - "true"
    name_shape:
      label: 对象名形态
      importance: non_important
      values:
      - plain_identifier
      - schema_qualified
      - quoted_identifier
      - reserved_word
      - existing_object
      - missing_object
    storage_parameter_set:
      label: SET storage_parameter 组合
      importance: non_important
      values:
      - single_param_with_value
      - single_param_no_value
      - multiple_params
    storage_parameter_reset:
      label: RESET storage_parameter 组合
      importance: non_important
      values:
      - single_param
      - multiple_params
    statistics_value:
      label: SET STATISTICS 数值
      importance: non_important
      values:
      - positive_integer
      - zero
      - negative_one
      - out_of_range
    column_number_value:
      label: ALTER COLUMN 列号
      importance: non_important
      values:
      - valid_position
      - zero
      - out_of_range
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
    invalid_combination:
      label: 语义非法组合
      importance: non_important
      values:
      - nonexistent_index_no_if_exists
      - attach_partition_definition_mismatch
      - system_catalog_index
      - statistics_column_out_of_range
      - none
    syntax_error:
      label: 语法非法组合
      importance: non_important
      values:
      - none
      - invalid_syntax
    permission_boundary:
      label: 权限边界
      importance: non_important
      values:
      - owner
      - non_owner
      - insufficient_tablespace_privilege
    verification_mode:
      label: 验证方式
      importance: non_important
      values:
      - catalog_query
      - meta_command
      - parameter_check
    cleanup_mode:
      label: 清理方式
      importance: non_important
      values:
      - drop_index
      - reset_parameter
      - detach_partition
  defaults:
    object_state: exists
    expected_status: success
    if_exists: "false"
    no_keyword: "false"
    column_keyword: "false"
    owned_by: absent
    nowait: "false"
    name_shape: plain_identifier
    storage_parameter_set: single_param_with_value
    storage_parameter_reset: single_param
    statistics_value: positive_integer
    column_number_value: valid_position
    index_method: btree
    invalid_combination: none
    syntax_error: none
    permission_boundary: owner
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - if_exists
    - no_keyword
    - column_keyword
    - owned_by
    - nowait
    - name_shape
    - storage_parameter_set
    - storage_parameter_reset
    - statistics_value
    - column_number_value
    - index_method
    - invalid_combination
    - syntax_error
    - permission_boundary
    - verification_mode
    - cleanup_mode
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "ALTER INDEX {if_exists_clause}{index_name} {branch_action};"
    verification_query_template: "SELECT c.relname, i.indisvalid FROM pg_class c JOIN pg_index i ON i.indexrelid = c.oid WHERE c.relname = '{index_name}';"
    factor_value_bindings:
      if_exists_clause:
        factor: if_exists
        values:
          "false": ""
          "true": "IF EXISTS "
      branch_action:
        factor: statement_branch
        values:
          rename: "RENAME TO {new_name}"
          set_tablespace: "SET TABLESPACE {tablespace_name}"
          attach_partition: "ATTACH PARTITION {partition_index_name}"
          depends_on_extension: "DEPENDS ON EXTENSION {extension_name}"
          no_depends_on_extension: "NO DEPENDS ON EXTENSION {extension_name}"
          set_storage: "SET ({storage_params})"
          reset_storage: "RESET ({storage_params})"
          set_statistics: "ALTER {column_clause}{column_number} SET STATISTICS {statistics_value}"
          all_in_tablespace: "ALL IN TABLESPACE {source_tablespace} {owned_by_clause}SET TABLESPACE {new_tablespace} {nowait_clause}"
      column_clause:
        factor: column_keyword
        values:
          "false": ""
          "true": "COLUMN "
      owned_by_clause:
        factor: owned_by
        values:
          absent: ""
          single_role: "OWNED BY {role_name} "
          multiple_roles: "OWNED BY {role_name_1}, {role_name_2} "
      nowait_clause:
        factor: nowait
        values:
          "false": ""
          "true": "NOWAIT"
```
