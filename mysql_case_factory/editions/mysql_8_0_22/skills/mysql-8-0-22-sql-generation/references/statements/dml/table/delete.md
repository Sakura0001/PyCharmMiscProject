# DELETE

Official source: https://dev.mysql.com/doc/refman/8.0/en/delete.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: table
  skill_name: delete
  official_source: https://dev.mysql.com/doc/refman/8.0/en/delete.html
  statement:
    key: delete
    name: DELETE
    aliases: [delete]
    purpose: Generate MySQL 8.0.22 single-table and multiple-table DELETE cases.
  syntax_templates:
    - "DELETE [LOW_PRIORITY] [QUICK] [IGNORE] FROM tbl_name [PARTITION (...)] [WHERE where_condition] [ORDER BY ...] [LIMIT row_count]"
    - "DELETE [LOW_PRIORITY] [QUICK] [IGNORE] tbl_name[.*] [, tbl_name[.*]] ... FROM table_references [WHERE where_condition]"
    - "DELETE [LOW_PRIORITY] [QUICK] [IGNORE] FROM tbl_name[.*] [, tbl_name[.*]] ... USING table_references [WHERE where_condition]"
  factor_layers:
    - tier: T1
      factors: [statement_branch, condition_shape, expected_status]
    - tier: T2
      factors: [priority_modifier, quick_modifier, ignore_modifier, order_limit_shape, partition_clause]
  factors:
    statement_branch:
      label: DELETE branch
      importance: important
      values: [single_table, multiple_table_from, multiple_table_using]
    condition_shape:
      label: WHERE / join condition
      importance: important
      values: [omitted, where_filter, join_filter]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    priority_modifier:
      label: LOW_PRIORITY
      importance: non_important
      values: [omitted, low_priority]
    quick_modifier:
      label: QUICK
      importance: non_important
      values: [omitted, quick]
    ignore_modifier:
      label: IGNORE
      importance: non_important
      values: [omitted, ignore]
    order_limit_shape:
      label: ORDER BY / LIMIT
      importance: non_important
      values: [omitted, order_by, limit, order_by_limit]
    partition_clause:
      label: PARTITION clause
      importance: non_important
      values: [omitted, named_partition]
  defaults:
    statement_branch: single_table
    condition_shape: where_filter
    expected_status: success
    priority_modifier: omitted
    quick_modifier: omitted
    ignore_modifier: omitted
    order_limit_shape: omitted
    partition_clause: omitted
  coverage_policy:
    main_combination_axes: [statement_branch, condition_shape, expected_status]
    non_main_factors: [priority_modifier, quick_modifier, ignore_modifier, order_limit_shape, partition_clause]
    python_expand_threshold: 180
  rendering:
    statement_template: "DELETE {ignore_sql}FROM {table_name} WHERE id_col = 1"
    verification_query_template: "SELECT COUNT(*) AS row_count FROM {table_name} WHERE id_col = 1"
    factor_value_bindings:
      ignore_sql:
        factor: ignore_modifier
        values: {omitted: "", ignore: "IGNORE "}
```
