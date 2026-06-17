# 技能：CLUSTER

## 官方语法范围补充

来源：https://www.postgresql.org/docs/16/sql-cluster.html

```sql
CLUSTER [VERBOSE] table_name [ USING index_name ]
CLUSTER ( option [, ...] ) table_name [ USING index_name ]
CLUSTER [VERBOSE]

where option can be one of:

    VERBOSE [ boolean ]

where boolean can be TRUE, ON, 1, FALSE, OFF, or 0.
```

遗留语法（pre-8.3 兼容，不作为正式覆盖分支）：

```sql
CLUSTER index_name ON table_name
```

## 语句作用

官方说明：CLUSTER — cluster a table according to an index

该 reference 关注 CLUSTER 语句的物理存储重排序行为、索引依赖关系、权限边界与全库重聚簇边界，不涉及列类型组合。

**重要声明**：CLUSTER 操作在整表物理存储级别执行，不涉及列类型组合。但 CLUSTER 间接涉及索引类型——所使用的索引必须已存在于目标表上且为有效索引。CLUSTER 获取 ACCESS EXCLUSIVE 锁，阻塞所有并发读写直到操作完成。

## 测试因子分级

### T1：核心语义因子
- statement_branch：官方语法分支
- object_state：目标表与索引对象状态
- expected_status：预期结果

### T2：重要行为因子
- using_clause：USING 子句开关
- verbose_option：VERBOSE 选项
- cluster_all：全库重聚簇行为

### T3：对象名与输入形态因子
- table_name_shape：表名形态
- index_name_shape：索引名形态

### T4：依赖对象与环境因子
- privilege_level：权限级别
- index_dependency：索引依赖关系
- partitioned_table：分区表行为

### T5：异常与边界因子
- nonexistent_table：不存在的表
- nonexistent_index：不存在的索引
- insufficient_privilege：权限不足
- index_not_on_table：索引不属于目标表
- transaction_block_restriction：事务块限制

### T6：验证与清理因子
- verification：验证方式
- cleanup：清理方式

## 覆盖策略

- 覆盖所有 CLUSTER 语法分支：指定索引聚簇、重聚簇（无 USING）、VERBOSE 选项、括号选项形式、全库重聚簇。
- 覆盖所有基表作为 CLUSTER 目标对象，不覆盖每张基表的列类型。
- CLUSTER 不涉及列类型组合，此约束必须体现在因子定义与覆盖策略中。
- CLUSTER 间接涉及索引依赖关系——指定 USING index_name 时索引必须存在于目标表上；不指定 USING 时目标表必须有先前记录的聚簇索引。
- T1 因子做笛卡尔积覆盖；如分支之间存在互斥前置条件，应先按语法分支拆分再做局部笛卡尔积。
- T2 因子按规模控制策略参与组合：
  - 当组合规模可控时，与 T1 一起参与笛卡尔积覆盖。
  - 当组合规模过大时，优先保留 T1 的完整覆盖，对 T2 做裁剪、抽样或轮转覆盖。
- T3、T4、T5、T6 不进入全局主笛卡尔积，仅作为附属因子挂靠到代表性主样本上。
- 必须同时保留成功路径与失败路径。
- 如果生成规模超过 100 万，优先裁剪 T3-T6，再裁剪局部语法开关，最后才允许压缩语句分支数量。

## 生成约束

- 必须覆盖该命令的所有顶层语法形式、成功路径、失败路径和对象状态验证。
- 需要为会修改对象元数据或物理状态的路径提供前置对象、执行语句、验证语句和清理语句。
- 对不可事务化、需要 superuser 或受环境约束的分支，必须单独标识生命周期边界。
- 对官方语法中出现的每一种顶层形式，都必须至少生成一个成功或失败可归因样本。
- 每个样本必须包含明确的前置对象准备（含索引创建）、目标 CLUSTER 语句、验证语句与清理语句。
- 不得把多个独立失败原因混在同一条失败样本中。
- CLUSTER 不涉及列类型组合，此约束必须体现在因子定义与覆盖策略中。
- CLUSTER 间接涉及索引依赖关系，指定 USING 时索引必须存在；不指定 USING 时必须有已记录的聚簇索引。
- CLUSTER 获取 ACCESS EXCLUSIVE 锁，阻塞所有并发操作，此行为边界必须在异常因子中体现。
- CLUSTER（全库重聚簇）不能在事务块内执行，此限制必须在异常因子中体现。
- 分区表聚簇时索引不可省略，此限制必须在异常因子中体现。

## 挂靠规则

- T3 因子挂靠到各语法分支的代表性成功样本和失败样本上轮转注入。
- T4 因子仅挂靠到需要依赖对象（索引存在性）、权限、分区表的分支。
- T5 因子按失败原因单独挂靠，不得破坏主覆盖因子的可识别性与可归因性。
- T6 因子挂靠到稳定成功路径和关键失败路径上，确保每个分支都有验证与清理策略。
- 单条样本允许同时挂靠多个低优先级因子，但不得让语句分支、对象状态、权限预期和成功/失败归因变得不可识别。

## 规模控制规则

- 优先保证：
  - 所有语法分支全覆盖
  - 目标表存在 / 不存在 / 索引存在 / 不存在全覆盖
  - 成功 / 失败路径全覆盖
  - 权限核心路径全覆盖
- 次优先保证：
  - 官方 Synopsis 中的可选关键字和子句代表性覆盖
  - VERBOSE 选项与括号选项形式代表性覆盖
  - 全库重聚簇行为覆盖
  - schema、owner 等依赖对象代表性覆盖
  - 分区表行为覆盖
- 低优先级因子仅保证冒烟覆盖与代表性覆盖。

## 结构化配置

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: cluster
  official_source: https://www.postgresql.org/docs/16/sql-cluster.html
  statement:
    key: cluster
    name: CLUSTER
    aliases:
    - CLUSTER
    - CLUSTER VERBOSE
    purpose: CLUSTER — cluster a table according to an index
  syntax_templates:
  - "CLUSTER [VERBOSE] table_name [ USING index_name ]"
  - "CLUSTER ( option [, ...] ) table_name [ USING index_name ]"
  - "CLUSTER [VERBOSE]"
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
    - using_clause
    - verbose_option
    - cluster_all
  - tier: T3
    name: 对象名与输入形态因子
    factors:
    - table_name_shape
    - index_name_shape
  - tier: T4
    name: 依赖对象与环境因子
    factors:
    - privilege_level
    - index_dependency
    - partitioned_table
  - tier: T5
    name: 异常与边界因子
    factors:
    - nonexistent_table
    - nonexistent_index
    - insufficient_privilege
    - index_not_on_table
    - transaction_block_restriction
  - tier: T6
    name: 验证与清理因子
    factors:
    - verification
    - cleanup
  factors:
    statement_branch:
      label: 官方语法分支
      importance: important
      values:
      - key: cluster_table_using_index
        label: CLUSTER table_name USING index_name — 指定索引聚簇
      - key: cluster_table_recluster
        label: CLUSTER table_name — 重聚簇（使用先前记录的索引）
      - key: cluster_verbose_table_using_index
        label: CLUSTER VERBOSE table_name USING index_name — 指定索引加 VERBOSE
      - key: cluster_verbose_table_recluster
        label: CLUSTER VERBOSE table_name — 重聚簇加 VERBOSE
      - key: cluster_paren_option_table_using_index
        label: CLUSTER (VERBOSE) table_name USING index_name — 括号选项加指定索引
      - key: cluster_paren_option_table_recluster
        label: CLUSTER (VERBOSE) table_name — 括号选项重聚簇
      - key: cluster_all
        label: CLUSTER — 全库重聚簇（无表名）
      - key: cluster_verbose_all
        label: CLUSTER VERBOSE — 全库重聚簇加 VERBOSE
    object_state:
      label: 目标表与索引对象状态
      importance: important
      values:
      - key: table_exists_index_exists
        label: 表存在且指定索引存在
      - key: table_exists_index_does_not_exist
        label: 表存在但指定索引不存在
      - key: table_does_not_exist
        label: 表不存在
      - key: table_exists_clustered_index_recorded
        label: 表存在且已有先前记录的聚簇索引（支持无 USING 重聚簇）
      - key: table_exists_no_clustered_index_recorded
        label: 表存在但无先前记录的聚簇索引（无 USING 重聚簇将失败）
    expected_status:
      label: 预期结果
      importance: important
      values:
      - success
      - failure
    using_clause:
      label: USING 子 clause 开关
      importance: non_important
      values:
      - key: using_index
        label: USING index_name — 显式指定聚簇索引
      - key: without_using
        label: 无 USING — 重聚簇使用先前记录的索引
    verbose_option:
      label: VERBOSE 选项
      importance: non_important
      values:
      - key: no_verbose
        label: 无 VERBOSE
      - key: verbose_keyword
        label: VERBOSE 关键字
      - key: paren_verbose_true
        label: (VERBOSE TRUE) 括号选项
      - key: paren_verbose_false
        label: (VERBOSE FALSE) 括号选项关闭进度报告
    cluster_all:
      label: 全库重聚簇行为
      importance: non_important
      values:
      - key: single_table
        label: 指定单表聚簇
      - key: all_tables
        label: 全库重聚簇（CLUSTER 无表名）
    table_name_shape:
      label: 表名形态
      importance: non_important
      values:
      - simple
      - quoted
      - schema_qualified
      - non_existent
    index_name_shape:
      label: 索引名形态
      importance: non_important
      values:
      - simple
      - quoted
      - non_existent
    privilege_level:
      label: 权限级别
      importance: non_important
      values:
      - owner
      - superuser
      - insufficient_privilege
    index_dependency:
      label: 索引依赖关系
      importance: non_important
      values:
      - key: index_exists_on_table
        label: 索引存在于目标表上 — 聚簇依赖满足
      - key: index_not_on_table
        label: 索引不属于目标表 — 聚簇依赖失败
      - key: no_clustered_index_recorded
        label: 无先前记录的聚簇索引 — 无 USING 重聚簇失败
    partitioned_table:
      label: 分区表行为
      importance: non_important
      values:
      - none
      - partitioned_table_with_partitioned_index
      - partitioned_table_without_index_specified
    nonexistent_table:
      label: 不存在的表
      importance: non_important
      values:
      - none
      - cluster_nonexistent_table
    nonexistent_index:
      label: 不存在的索引
      importance: non_important
      values:
      - none
      - cluster_with_nonexistent_index
    insufficient_privilege:
      label: 权限不足
      importance: non_important
      values:
      - none
      - non_owner_cluster
    index_not_on_table:
      label: 索引不属于目标表
      importance: non_important
      values:
      - none
      - index_belongs_to_different_table
    transaction_block_restriction:
      label: 事务块限制
      importance: non_important
      values:
      - none
      - cluster_all_inside_transaction_block
    verification:
      label: 验证方式
      importance: non_important
      values:
      - key: pg_class_relclustered
        label: pg_class relclustered — 验证聚簇索引已记录
      - key: physical_ordering_check
        label: 物理排序检查 — 验证行按索引顺序存储
      - key: pg_stat_progress_cluster
        label: pg_stat_progress_cluster — 进度监控视图
      - key: error_assertion
        label: 错误断言 — 验证预期失败确实发生
    cleanup:
      label: 清理方式
      importance: non_important
      values:
      - key: drop_objects
        label: DROP 已创建的测试对象（表与索引）
      - key: none
        label: CLUSTER 非破坏性操作 — 不需要额外清理
  defaults:
    expected_status: success
  coverage_policy:
    main_combination_axes:
    - statement_branch
    - object_state
    - expected_status
    non_main_factors:
    - using_clause
    - verbose_option
    - cluster_all
    - table_name_shape
    - index_name_shape
    - privilege_level
    - index_dependency
    - partitioned_table
    - nonexistent_table
    - nonexistent_index
    - insufficient_privilege
    - index_not_on_table
    - transaction_block_restriction
    - verification
    - cleanup
    python_expand_threshold: 200
    preserve_axes_first:
    - statement_branch
    - object_state
  rendering:
    statement_template: "CLUSTER [VERBOSE] {table_name} [ USING {index_name} ]"
    verification_query_template: "SELECT indisclustered FROM pg_index WHERE indexrelid = '{index_name}'::regclass"
    factor_value_bindings:
      using_clause:
        using_index: "USING {index_name}"
        without_using: ""
      verbose_option:
        no_verbose: ""
        verbose_keyword: "VERBOSE"
        paren_verbose_true: "(VERBOSE TRUE)"
        paren_verbose_false: "(VERBOSE FALSE)"
      cluster_all:
        single_table: "{table_name}"
        all_tables: ""
```
