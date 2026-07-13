# TRUNCATE TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/truncate-table.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: truncate
  official_source: https://dev.mysql.com/doc/refman/8.0/en/truncate-table.html
  statement:
    key: truncate
    name: TRUNCATE TABLE
    aliases: [truncate, truncate table]
    purpose: Empty a MySQL table and reset auto-increment state.
  syntax_templates:
    - "TRUNCATE [TABLE] tbl_name"
  factor_layers:
    - tier: T1
      factors: [table_keyword, table_state, foreign_key_state, expected_status]
  factors:
    table_keyword:
      label: TABLE keyword
      importance: important
      values: [omitted, present]
    table_state:
      label: Table state
      importance: important
      values: [exists, missing]
    foreign_key_state:
      label: Foreign-key dependency
      importance: important
      values: [none, referenced_by_other_table]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    table_keyword: present
    table_state: exists
    foreign_key_state: none
    expected_status: success
  coverage_policy:
    main_combination_axes: [table_keyword, table_state, foreign_key_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 100
  rendering:
    statement_template: "TRUNCATE {table_keyword_sql}{table_name}"
    verification_query_template: "SELECT COUNT(*) AS row_count FROM {table_name}"
    factor_value_bindings:
      table_keyword_sql:
        factor: table_keyword
        values: {omitted: "", present: "TABLE "}
```
