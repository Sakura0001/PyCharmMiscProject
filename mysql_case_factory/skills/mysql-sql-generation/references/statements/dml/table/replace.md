# REPLACE

Official source: https://dev.mysql.com/doc/refman/8.0/en/replace.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: table
  skill_name: replace
  official_source: https://dev.mysql.com/doc/refman/8.0/en/replace.html
  statement:
    key: replace
    name: REPLACE
    aliases: [replace]
    purpose: Generate MySQL REPLACE cases with delete-plus-insert conflict semantics.
  syntax_templates:
    - "REPLACE [LOW_PRIORITY | DELAYED] [INTO] tbl_name [(col_name, ...)] {VALUES | VALUE} (value_list) [, ...]"
    - "REPLACE [LOW_PRIORITY | DELAYED] [INTO] tbl_name SET assignment_list"
    - "REPLACE [LOW_PRIORITY | DELAYED] [INTO] tbl_name [(col_name, ...)] SELECT ..."
  factor_layers:
    - tier: T1
      factors: [statement_branch, conflict_state, expected_status]
    - tier: T2
      factors: [priority_modifier, partition_clause]
  factors:
    statement_branch:
      label: REPLACE branch
      importance: important
      values: [values_list, set_clause, replace_select, replace_table]
    conflict_state:
      label: Unique-key conflict
      importance: important
      values: [no_conflict, duplicate_key]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    priority_modifier:
      label: Priority modifier
      importance: non_important
      values: [omitted, low_priority, delayed]
    partition_clause:
      label: PARTITION clause
      importance: non_important
      values: [omitted, named_partition]
  defaults:
    statement_branch: values_list
    conflict_state: no_conflict
    expected_status: success
    priority_modifier: omitted
    partition_clause: omitted
  coverage_policy:
    main_combination_axes: [statement_branch, conflict_state, expected_status]
    non_main_factors: [priority_modifier, partition_clause]
    python_expand_threshold: 120
  rendering:
    statement_template: "REPLACE INTO {table_name} (id_col, int_col, varchar_col) VALUES (1, 200, 'replaced')"
    verification_query_template: "SELECT int_col, varchar_col FROM {table_name} WHERE id_col = 1"
    factor_value_bindings: {}
```
