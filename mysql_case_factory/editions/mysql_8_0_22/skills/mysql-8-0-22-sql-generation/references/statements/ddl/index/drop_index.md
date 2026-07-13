# DROP INDEX

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-index.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: index
  skill_name: drop_index
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-index.html
  statement:
    key: drop_index
    name: DROP INDEX
    aliases: [drop index]
    purpose: Drop a MySQL index from a table.
  syntax_templates:
    - "DROP INDEX index_name ON tbl_name [algorithm_option | lock_option] ..."
  factor_layers:
    - tier: T1
      factors: [index_state, table_state, expected_status]
    - tier: T2
      factors: [algorithm_lock]
  factors:
    index_state:
      label: Index state
      importance: important
      values: [exists, missing]
    table_state:
      label: Table state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    algorithm_lock:
      label: ALGORITHM/LOCK options
      importance: non_important
      values: [omitted, inplace_none, copy_shared]
  defaults:
    index_state: exists
    table_state: exists
    expected_status: success
    algorithm_lock: omitted
  coverage_policy:
    main_combination_axes: [index_state, table_state, expected_status]
    non_main_factors: [algorithm_lock]
    python_expand_threshold: 100
  rendering:
    statement_template: "DROP INDEX {index_name} ON {table_name}{algorithm_lock_sql}"
    verification_query_template: "SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}' AND INDEX_NAME = '{index_name}'"
    factor_value_bindings:
      algorithm_lock_sql:
        factor: algorithm_lock
        values: {omitted: "", inplace_none: " ALGORITHM=INPLACE LOCK=NONE", copy_shared: " ALGORITHM=COPY LOCK=SHARED"}
```
