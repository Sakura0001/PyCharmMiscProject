# ANALYZE TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/analyze-table.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: statistics
  skill_name: analyze_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/analyze-table.html
  statement:
    key: analyze_table
    name: ANALYZE TABLE
    aliases: [analyze table, analyze]
    purpose: Update MySQL table key distribution and histogram statistics.
  syntax_templates:
    - "ANALYZE [NO_WRITE_TO_BINLOG | LOCAL] TABLE tbl_name [, tbl_name] ..."
    - "ANALYZE TABLE tbl_name UPDATE HISTOGRAM ON col_name [, col_name] ... [WITH N BUCKETS]"
    - "ANALYZE TABLE tbl_name DROP HISTOGRAM ON col_name [, col_name] ..."
  factor_layers:
    - tier: T1
      factors: [statement_branch, table_state, expected_status]
    - tier: T2
      factors: [binlog_modifier, histogram_bucket_shape]
  factors:
    statement_branch:
      label: ANALYZE branch
      importance: important
      values: [key_distribution, update_histogram, drop_histogram]
    table_state:
      label: Table state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    binlog_modifier:
      label: Binary logging modifier
      importance: non_important
      values: [omitted, no_write_to_binlog, local]
    histogram_bucket_shape:
      label: Histogram bucket count
      importance: non_important
      values: [omitted, with_10_buckets]
  defaults:
    statement_branch: key_distribution
    table_state: exists
    expected_status: success
    binlog_modifier: omitted
    histogram_bucket_shape: omitted
  coverage_policy:
    main_combination_axes: [statement_branch, table_state, expected_status]
    non_main_factors: [binlog_modifier, histogram_bucket_shape]
    python_expand_threshold: 100
  rendering:
    statement_template: "ANALYZE TABLE {table_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
