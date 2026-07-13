# LOAD DATA

Official source: https://dev.mysql.com/doc/refman/8.0/en/load-data.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: data_transfer
  skill_name: load_data
  official_source: https://dev.mysql.com/doc/refman/8.0/en/load-data.html
  statement:
    key: load_data
    name: LOAD DATA
    aliases: [load data]
    purpose: Load text files into MySQL tables.
  syntax_templates:
    - "LOAD DATA [LOW_PRIORITY | CONCURRENT] [LOCAL] INFILE 'file_name' [REPLACE | IGNORE] INTO TABLE tbl_name [PARTITION (...)] [CHARACTER SET charset_name] [FIELDS ...] [LINES ...] [(col_name_or_user_var, ...)] [SET col_name = expr, ...]"
  factor_layers:
    - tier: T1
      factors: [local_shape, duplicate_handling, file_state, expected_status]
    - tier: T2
      factors: [field_line_shape, column_mapping_shape, set_clause_shape, privilege_context]
  factors:
    local_shape:
      label: LOCAL file source
      importance: important
      values: [server_file, local_file]
    duplicate_handling:
      label: Duplicate handling
      importance: important
      values: [omitted, replace, ignore]
    file_state:
      label: Input file state
      importance: important
      values: [exists, missing, inaccessible]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    field_line_shape:
      label: FIELD and LINE options
      importance: non_important
      values: [default_format, csv_format, custom_terminated]
    column_mapping_shape:
      label: Column/user-variable mapping
      importance: non_important
      values: [omitted, column_list, user_variables]
    set_clause_shape:
      label: SET preprocessing
      importance: non_important
      values: [omitted, transform_column]
    privilege_context:
      label: FILE/local_infile privilege context
      importance: non_important
      values: [sufficient, insufficient]
  defaults:
    local_shape: server_file
    duplicate_handling: omitted
    file_state: exists
    expected_status: success
    field_line_shape: default_format
    column_mapping_shape: omitted
    set_clause_shape: omitted
    privilege_context: sufficient
  coverage_policy:
    main_combination_axes: [local_shape, duplicate_handling, file_state, expected_status]
    non_main_factors: [field_line_shape, column_mapping_shape, set_clause_shape, privilege_context]
    python_expand_threshold: 180
  rendering:
    statement_template: "LOAD DATA INFILE '/tmp/mysql_case_data.tsv' INTO TABLE {table_name}"
    verification_query_template: "SELECT COUNT(*) AS row_count FROM {table_name}"
    factor_value_bindings: {}
```
