# 技能：query_context_policy

## 作用

定义 SQL 层 feature 涉及查询验证时必须联想到的查询上下文。它不是只服务 `SELECT` statement；任何 feature 如果需要通过查询证明正确性，例如 index、partition、statistics、collation、RLS、view、trigger、materialized view、FDW、generated column、constraint 或 optimizer 相关能力，都应该读取本规则。

查询相关测试不能只覆盖语法。必须同时设计：

```text
feature_under_test
-> query_role
-> query_shape
-> data_fixture
-> data_distribution
-> index_context
-> hint_context
-> statistics_context
-> optimizer_guc_context
-> parameterization_context
-> transaction_visibility_context
-> parallel_execution_context
-> oracle_context
```

## query_context 维度

### query_role

- `semantic_verification`：验证查询结果语义正确。
- `plan_activation`：触发某个执行路径，例如 index scan、partition pruning、join method、aggregate path。
- `visibility_verification`：验证 MVCC、事务隔离、锁、RLS 或权限可见性。
- `dependency_verification`：验证 feature 与 view、index、constraint、partition、statistics 等依赖关系。
- `regression_oracle`：用等价查询、对照查询或 metamorphic equivalence 证明结果一致。

### query_shape

- `source_shape`：no_from、single_table、multi_table、view、materialized_view、foreign_table、partitioned_table、subquery、cte、lateral、function_scan、tablesample。
- `projection_shape`：star、explicit_columns、expression、function_call、aggregate_expression、window_expression、alias、duplicate_column_name、type_coerced_expression。
- `predicate_shape`：none、equality、range、is_null、is_not_null、in_list、not_in_list、exists_subquery、not_exists_subquery、any_all、row_comparison、correlated_subquery、volatile_function_predicate。
- `join_shape`：inner_join、left_join、right_join、full_join、cross_join、natural_join、using_join、lateral_join、self_join、semi_join、anti_join。
- `aggregation_shape`：none、group_by、having、aggregate_filter、distinct、distinct_on、rollup、cube、grouping_sets。
- `set_operation_shape`：union、union_all、intersect、intersect_all、except、except_all、type_alignment、column_count_mismatch。
- `window_shape`：over_empty、partition_by、order_by、rows_frame、range_frame、groups_frame、ranking_function、aggregate_window_function、frame_boundary_edge。
- `ordering_pagination_shape`：no_order_by、order_by_single、order_by_multi、asc_desc、using_operator、nulls_first_last、limit、offset、fetch_first、with_ties。
- `cte_shape`：non_recursive_cte、recursive_cte、materialized_cte、not_materialized_cte、data_modifying_cte、search_clause、cycle_clause。
- `locking_shape`：plain_read、for_update、for_share、for_no_key_update、for_key_share、nowait、skip_locked。

### data_fixture

查询测试必须先设计可解释的数据夹具，而不是随意插几行数据。

- `empty_table`：验证空输入、聚合空集、无匹配 predicate。
- `single_row_table`：验证最小成功路径。
- `small_truth_table`：用少量手工可算数据验证精确结果。
- `null_heavy_table`：验证 SQL 三值逻辑、join key NULL、GROUP BY NULL、COUNT(col)。
- `duplicate_key_table`：验证 DISTINCT、UNION/UNION ALL、join fanout、aggregate count。
- `range_boundary_table`：验证 range predicate、partition boundary、histogram boundary。
- `skewed_value_table`：验证 hot key、MCV、选择率估计、计划选择。
- `join_cardinality_table`：必须包含 1:1、1:N、N:M、unmatched rows、NULL join key。
- `partition_boundary_table`：必须包含 single partition hit、multi partition hit、default partition hit、empty partition。
- `collation_sensitive_table`：必须包含大小写、多字节字符、locale-sensitive ordering。
- `wide_toast_table`：验证宽行、TOAST、projection pruning、sort/hash memory 压力。

### data_distribution

- `cardinality`：empty、one_row、small、medium、large。
- `selectivity`：zero_match、one_match、low_selectivity、high_selectivity、all_match。
- `null_rate`：no_null、sparse_nulls、dense_nulls。
- `duplicate_rate`：unique_values、few_duplicates、many_duplicates。
- `skew`：uniform、hot_key_skew、long_tail_skew。
- `correlation`：independent_columns、correlated_columns、anti_correlated_columns。
- `join_cardinality`：one_to_one、one_to_many、many_to_many、unmatched_left、unmatched_right。
- `partition_distribution`：single_partition_hit、multi_partition_hit、default_partition_hit、empty_partition、skewed_partition。
- `boundary_values`：min_value、max_value、overflow_candidate、empty_string、large_text、timezone_boundary、collation_boundary。

### index_context

- `no_index`
- `btree_index`
- `hash_index`
- `brin_index`
- `gin_index`
- `gist_index`
- `spgist_index`
- `expression_index`
- `partial_index`
- `multicolumn_index`
- `covering_index`
- `unique_index`
- `invalid_or_unusable_index`
- `index_order_matches_query`
- `index_order_conflicts_with_query`

### hint_context

PostgreSQL 原生没有官方 SQL hint。若环境没有 hint 扩展，必须把 hint 语境建模为 optimizer GUC 或 extension availability，不得伪造官方 hint。

- `no_hint`
- `extension_hint_available`
- `extension_hint_unavailable`
- `extension_hint_valid`
- `extension_hint_invalid`
- `hint_matches_expected_plan`
- `hint_conflicts_with_data_distribution`
- `hint_ignored_or_invalid`
- `optimizer_guc_forced`

### statistics_context

- `not_analyzed`
- `analyzed`
- `stale_statistics`
- `default_statistics_target`
- `high_statistics_target`
- `mcv_skew`
- `histogram_boundary`
- `ndistinct_skew`
- `column_correlation`
- `extended_statistics`
- `functional_dependency_stats`
- `multi_column_ndistinct_stats`

### optimizer_guc_context

- `enable_seqscan`
- `enable_indexscan`
- `enable_bitmapscan`
- `enable_indexonlyscan`
- `enable_hashjoin`
- `enable_mergejoin`
- `enable_nestloop`
- `enable_partition_pruning`
- `enable_partitionwise_join`
- `enable_partitionwise_aggregate`
- `work_mem`
- `jit`
- `max_parallel_workers_per_gather`
- `random_page_cost`
- `cpu_tuple_cost`

### parameterization_context

- `literal_constant`
- `prepared_statement`
- `generic_plan`
- `custom_plan`
- `parameter_selectivity_change`
- `first_execution`
- `repeated_execution`
- `null_parameter`
- `unknown_parameter_type`
- `explicit_parameter_cast`

### transaction_visibility_context

- `read_committed`
- `repeatable_read`
- `serializable`
- `same_transaction_visibility`
- `uncommitted_data_invisible`
- `savepoint_visibility`
- `concurrent_update`
- `concurrent_delete`
- `select_for_update`
- `select_for_share`
- `skip_locked`
- `nowait`

### parallel_execution_context

- `parallel_disabled`
- `parallel_seq_scan`
- `parallel_index_scan`
- `parallel_hash_join`
- `partial_aggregate`
- `gather`
- `gather_merge`
- `parallel_safe_function`
- `parallel_unsafe_function`

### null_semantics_context

- `equals_null_is_unknown`
- `is_null`
- `is_not_null`
- `not_in_with_null`
- `in_with_null`
- `null_join_key`
- `group_by_null`
- `order_by_nulls_first_last`
- `count_star_vs_count_col`

### collation_context

- `c_collation`
- `non_c_collation`
- `case_sensitive_text`
- `case_insensitive_pattern`
- `multibyte_text`
- `unicode_text`
- `like_pattern`
- `ilike_pattern`
- `regex_pattern`
- `text_pattern_ops`
- `collation_mismatch`

### function_volatility_context

- `immutable_function`
- `stable_function`
- `volatile_function`
- `set_returning_function`
- `function_index`
- `predicate_pushdown`
- `constant_folding`
- `per_row_call_count`

### rewrite_context

- `subquery_flattening`
- `correlated_subquery`
- `exists_semijoin`
- `not_exists_antijoin`
- `in_to_semijoin`
- `not_in_null_sensitive`
- `lateral_dependency`
- `cte_inline`
- `cte_materialized`
- `view_expansion`
- `security_barrier_view`
- `predicate_pushdown`

### oracle_context

- `exact_ordered_result`：有 ORDER BY 且排序键唯一或规则明确时使用。
- `unordered_multiset_result`：没有 ORDER BY 时比较多重集合，不比较行顺序。
- `aggregate_result`：验证 count、sum、min、max、group rows、empty input。
- `column_shape_result`：验证列名、列数、类型、NULLability。
- `metamorphic_equivalence`：等价查询或对照查询结果必须一致。
- `plan_observation`：EXPLAIN/EXPLAIN ANALYZE 只能作为辅助验证，不能替代结果正确性。
- `error_assertion`：负例使用 SQLSTATE 或稳定错误原因。

## 必须遵守的查询 oracle 规则

- 没有 ORDER BY，不允许断言行顺序。
- `UNION` 与 `UNION ALL` 必须区分重复行语义。
- `INTERSECT`、`EXCEPT` 与 `ALL` 版本必须区分多重集合计数。
- NULL 必须按 SQL 三值逻辑验证，尤其是 `NOT IN + NULL`。
- `COUNT(*)` 与 `COUNT(col)` 必须分别验证。
- 浮点、时间、collation 排序、locale-sensitive 文本必须使用稳定 oracle。
- EXPLAIN plan 只能证明计划形态，不证明结果正确性。
- 有 hint、optimizer GUC 或 plan forcing 时，主 oracle 仍然是结果正确性；plan observation 是 secondary oracle。

## feature_to_query_context_rules

- 如果 feature 涉及 index，必须联想到 `predicate_shape`、`selectivity`、`null_rate`、`duplicate_rate`、`index_context`、`statistics_context`、`optimizer_guc_context`、有/无 hint 对照、ANALYZE 前后。
- 如果 feature 涉及 join，必须联想到 `join_shape`、`join_cardinality`、NULL join key、unmatched rows、duplicate matches、join key index、join method GUC。
- 如果 feature 涉及 partition，必须联想到 partition key、single/multi partition hit、default partition、empty partition、runtime pruning、static pruning、partition-wise join、partition-wise aggregate。
- 如果 feature 涉及 collation，必须联想到 ORDER BY、text comparison、LIKE/ILIKE、regex、index ordering、locale-sensitive data、collation mismatch。
- 如果 feature 涉及 RLS 或权限，必须联想到 role、policy USING、WITH CHECK、security barrier view、subquery visibility、SELECT privilege。
- 如果 feature 涉及 aggregate，必须联想到 GROUP BY、HAVING、NULL group、duplicate rows、empty input、partial aggregate、parallel aggregate。
- 如果 feature 涉及 optimizer，必须联想到 no index/index、statistics freshness、data skew、selectivity、join cardinality、parameterized query、plan cache、optimizer GUC、hint_context、result equivalence。
- 如果 feature 涉及 prepared statement，必须联想到 literal constant、generic_plan、custom_plan、parameter_selectivity_change、null_parameter、unknown_parameter_type。
- 如果 feature 涉及 transaction or locking，必须联想到 isolation level、MVCC visibility、concurrent update/delete、SELECT FOR UPDATE/SHARE、NOWAIT、SKIP LOCKED。
- 如果 feature 涉及 view or rewrite，必须联想到 view expansion、security barrier view、subquery flattening、predicate pushdown、CTE materialization。

## query_dependency 声明格式

Feature 或 statement matrix 如果需要查询验证，应声明：

```text
query_dependency:
  required: true
  query_roles:
    - semantic_verification
    - plan_activation
  required_query_shapes:
    - equality_predicate
    - range_predicate
    - order_by
  required_data_fixtures:
    - small_truth_table
    - duplicate_key_table
    - null_heavy_table
  required_data_distributions:
    - low_selectivity
    - high_selectivity
    - hot_key_skew
  required_contexts:
    - index_context
    - hint_context
    - statistics_context
    - optimizer_guc_context
    - parameterization_context
  oracle:
    primary: unordered_multiset_result
    secondary: plan_observation
```

## 结构化配置

```yaml
structured_config:
  kind: common_policy
  skill_name: query_context_policy
  query_context:
    required_when:
      - statement.domain == query
      - feature uses SELECT, TABLE, VALUES, CTE, subquery, view, or EXPLAIN for verification
      - feature correctness depends on data distribution, indexes, statistics, optimizer, MVCC, hints, or result-set oracle
    context_groups:
      - query_role
      - query_shape
      - data_fixture
      - data_distribution
      - index_context
      - hint_context
      - statistics_context
      - optimizer_guc_context
      - parameterization_context
      - transaction_visibility_context
      - parallel_execution_context
      - null_semantics_context
      - collation_context
      - function_volatility_context
      - rewrite_context
      - oracle_context
    oracle_rules:
      order_requires_order_by: true
      explain_plan_is_secondary_oracle: true
      compare_unordered_multiset_without_order_by: true
      preserve_duplicate_semantics: true
```
