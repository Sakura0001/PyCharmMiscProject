# DROP TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-table.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: drop_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-table.html
  statement:
    key: drop_table
    name: DROP TABLE
    aliases: [drop table]
    purpose: Drop one or more MySQL tables, including temporary-table guarded drops.
  syntax_templates:
    - "DROP [TEMPORARY] TABLE [IF EXISTS] tbl_name [, tbl_name] ... [RESTRICT | CASCADE]"
  factor_layers:
    - tier: T1
      factors: [temporary_clause, if_exists, table_state, expected_status]
    - tier: T2
      factors: [multi_table_shape, restrict_cascade]
  factors:
    temporary_clause:
      label: TEMPORARY
      importance: important
      values: [omitted, temporary]
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    table_state:
      label: Table state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    multi_table_shape:
      label: Number of tables
      importance: non_important
      values: [single, multiple]
    restrict_cascade:
      label: RESTRICT or CASCADE parsed no-op
      importance: non_important
      values: [omitted, restrict, cascade]
  defaults:
    temporary_clause: omitted
    if_exists: omitted
    table_state: exists
    expected_status: success
    multi_table_shape: single
    restrict_cascade: omitted
  coverage_policy:
    main_combination_axes: [temporary_clause, if_exists, table_state, expected_status]
    non_main_factors: [multi_table_shape, restrict_cascade]
    python_expand_threshold: 120
  rendering:
    statement_template: "DROP {temporary_sql}TABLE {if_exists_sql}{table_name}{restrict_sql}"
    verification_query_template: "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}'"
    factor_value_bindings:
      temporary_sql:
        factor: temporary_clause
        values: {omitted: "", temporary: "TEMPORARY "}
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
      restrict_sql:
        factor: restrict_cascade
        values: {omitted: "", restrict: " RESTRICT", cascade: " CASCADE"}
```
