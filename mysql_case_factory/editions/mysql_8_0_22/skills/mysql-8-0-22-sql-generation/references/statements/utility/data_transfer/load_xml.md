# LOAD XML

Official source: https://dev.mysql.com/doc/refman/8.0/en/load-xml.html

```yaml
structured_config:
  kind: statement
  category: utility
  domain: data_transfer
  skill_name: load_xml
  official_source: https://dev.mysql.com/doc/refman/8.0/en/load-xml.html
  statement:
    key: load_xml
    name: LOAD XML
    aliases: [load xml]
    purpose: Load XML files into MySQL tables.
  syntax_templates:
    - "LOAD XML [LOW_PRIORITY | CONCURRENT] [LOCAL] INFILE 'file_name' [REPLACE | IGNORE] INTO TABLE tbl_name [CHARACTER SET charset_name] [ROWS IDENTIFIED BY '<tagname>'] [(field_or_var, ...)] [SET col_name = expr, ...]"
  factor_layers:
    - tier: T1
      factors: [local_shape, duplicate_handling, row_tag_shape, expected_status]
    - tier: T2
      factors: [field_mapping_shape, set_clause_shape, file_state]
  factors:
    local_shape:
      label: LOCAL file source
      importance: important
      values: [server_file, local_file]
    duplicate_handling:
      label: Duplicate handling
      importance: important
      values: [omitted, replace, ignore]
    row_tag_shape:
      label: ROWS IDENTIFIED BY
      importance: important
      values: [default_row, custom_tag]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    field_mapping_shape:
      label: Field/user-variable mapping
      importance: non_important
      values: [omitted, field_list, user_variables]
    set_clause_shape:
      label: SET preprocessing
      importance: non_important
      values: [omitted, transform_column]
    file_state:
      label: XML file state
      importance: non_important
      values: [exists, missing, malformed]
  defaults:
    local_shape: server_file
    duplicate_handling: omitted
    row_tag_shape: default_row
    expected_status: success
    field_mapping_shape: omitted
    set_clause_shape: omitted
    file_state: exists
  coverage_policy:
    main_combination_axes: [local_shape, duplicate_handling, row_tag_shape, expected_status]
    non_main_factors: [field_mapping_shape, set_clause_shape, file_state]
    python_expand_threshold: 140
  rendering:
    statement_template: "LOAD XML INFILE '/tmp/mysql_case_data.xml' INTO TABLE {table_name}"
    verification_query_template: "SELECT COUNT(*) AS row_count FROM {table_name}"
    factor_value_bindings: {}
```
