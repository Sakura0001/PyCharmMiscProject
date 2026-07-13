# IMPORT TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/import-table.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: data_transfer
  skill_name: import_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/import-table.html
  statement:
    key: import_table
    name: IMPORT TABLE
    aliases: [import table]
    purpose: Import MySQL tables from SDI metadata files.
  syntax_templates:
    - "IMPORT TABLE FROM sdi_file [, sdi_file] ..."
  factor_layers:
    - tier: T1
      factors: [sdi_file_state, schema_conflict_state, expected_status]
    - tier: T2
      factors: [engine_shape, privilege_context]
  factors:
    sdi_file_state:
      label: SDI file state
      importance: important
      values: [exists, missing, malformed]
    schema_conflict_state:
      label: Schema conflict
      importance: important
      values: [no_conflict, table_already_exists]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    engine_shape:
      label: Storage engine
      importance: non_important
      values: [supported, unsupported]
    privilege_context:
      label: FILE and CREATE privilege
      importance: non_important
      values: [sufficient, insufficient]
  defaults:
    sdi_file_state: exists
    schema_conflict_state: no_conflict
    expected_status: success
    engine_shape: supported
    privilege_context: sufficient
  coverage_policy:
    main_combination_axes: [sdi_file_state, schema_conflict_state, expected_status]
    non_main_factors: [engine_shape, privilege_context]
    python_expand_threshold: 100
  rendering:
    statement_template: "IMPORT TABLE FROM '/tmp/mysql_case_table.sdi'"
    verification_query_template: ""
    factor_value_bindings: {}
```
