# INSERT

Official source: https://dev.mysql.com/doc/refman/8.0/en/insert.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: table
  skill_name: insert
  official_source: https://dev.mysql.com/doc/refman/8.0/en/insert.html
  statement:
    key: insert
    name: INSERT
    aliases: [insert, 插入]
    purpose: Insert rows using MySQL 8.0.22 VALUES, SET, SELECT, TABLE, and duplicate-key branches.
  syntax_templates:
    - "INSERT [LOW_PRIORITY | DELAYED | HIGH_PRIORITY] [IGNORE] [INTO] tbl_name [(col_name, ...)] {VALUES | VALUE} (value_list) [, ...] [ON DUPLICATE KEY UPDATE assignment_list]"
    - "INSERT [INTO] tbl_name SET assignment_list [ON DUPLICATE KEY UPDATE assignment_list]"
    - "INSERT [INTO] tbl_name [(col_name, ...)] SELECT ..."
  factor_layers:
    - tier: T1
      factors: [statement_branch, duplicate_handling, expected_status]
    - tier: T2
      factors: [priority, partition_clause, column_list_shape]
  factors:
    statement_branch:
      label: INSERT branch
      importance: important
      values: [values_list, set_clause, insert_select]
    duplicate_handling:
      label: Duplicate handling
      importance: important
      values: [none, ignore, on_duplicate_key_update]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    priority:
      label: Priority modifier
      importance: non_important
      values: [omitted, low_priority, high_priority]
    partition_clause:
      label: PARTITION clause
      importance: non_important
      values: [omitted, named_partition]
    column_list_shape:
      label: Column list
      importance: non_important
      values: [explicit, omitted]
  defaults:
    statement_branch: values_list
    duplicate_handling: none
    expected_status: success
    priority: omitted
    partition_clause: omitted
    column_list_shape: explicit
  coverage_policy:
    main_combination_axes: [statement_branch, duplicate_handling, expected_status]
    non_main_factors: [priority, partition_clause, column_list_shape]
    python_expand_threshold: 200
  rendering:
    statement_template: "INSERT {ignore_sql}INTO {table_name} (int_col, varchar_col) VALUES (101, 'inserted'){duplicate_sql}"
    verification_query_template: "SELECT COUNT(*) AS row_count FROM {table_name} WHERE int_col = 101"
    factor_value_bindings:
      ignore_sql:
        factor: duplicate_handling
        values:
          none: ""
          ignore: "IGNORE "
          on_duplicate_key_update: ""
      duplicate_sql:
        factor: duplicate_handling
        values:
          none: ""
          ignore: ""
          on_duplicate_key_update: " ON DUPLICATE KEY UPDATE varchar_col = VALUES(varchar_col)"
```
