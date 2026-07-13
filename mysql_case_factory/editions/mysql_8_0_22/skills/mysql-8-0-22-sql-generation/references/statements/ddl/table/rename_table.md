# RENAME TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/rename-table.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: rename_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/rename-table.html
  statement:
    key: rename_table
    name: RENAME TABLE
    aliases: [rename table]
    purpose: Rename one or more MySQL tables atomically.
  syntax_templates:
    - "RENAME TABLE tbl_name TO new_tbl_name [, tbl_name2 TO new_tbl_name2] ..."
  factor_layers:
    - tier: T1
      factors: [rename_shape, object_state, expected_status]
    - tier: T2
      factors: [schema_shape, dependency_shape]
  factors:
    rename_shape:
      label: Rename branch
      importance: important
      values: [single_table, multi_table, swap_names]
    object_state:
      label: Object state
      importance: important
      values: [table_exists, source_missing, target_exists, view_instead_of_table]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    schema_shape:
      label: Schema boundary
      importance: non_important
      values: [same_schema, cross_schema]
    dependency_shape:
      label: Dependency shape
      importance: non_important
      values: [none, trigger_dependency, foreign_key_dependency]
  defaults:
    rename_shape: single_table
    object_state: table_exists
    expected_status: success
    schema_shape: same_schema
    dependency_shape: none
  coverage_policy:
    main_combination_axes: [rename_shape, object_state, expected_status]
    non_main_factors: [schema_shape, dependency_shape]
    python_expand_threshold: 120
  rendering:
    statement_template: "RENAME TABLE {table_name} TO {table_name}_renamed"
    verification_query_template: "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}_renamed'"
    factor_value_bindings: {}
```
