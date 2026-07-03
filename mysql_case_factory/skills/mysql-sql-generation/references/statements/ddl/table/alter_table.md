# ALTER TABLE

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/alter-table.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-23.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: alter_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-table.html
  statement:
    key: alter_table
    name: ALTER TABLE
    aliases: [alter table]
    purpose: Alter MySQL tables using column, index, constraint, table-option, partition, algorithm, and lock operations available in 8.0.22.
  syntax_templates:
    - "ALTER TABLE tbl_name [alter_option [, alter_option] ...] [partition_options]"
  factor_layers:
    - tier: T1
      factors: [alter_branch, table_state, expected_status]
    - tier: T2
      factors: [algorithm_option, lock_option, validation_option]
    - tier: T3
      factors: [column_position_shape, index_visibility_shape]
    - tier: T5
      factors: [invalid_combination]
  factors:
    alter_branch:
      label: ALTER TABLE operation
      importance: important
      values:
        - add_column
        - modify_column
        - change_column
        - drop_column
        - rename_column
        - add_index
        - drop_index
        - rename_index
        - alter_index_visibility
        - add_primary_key
        - drop_primary_key
        - add_foreign_key
        - drop_foreign_key
        - add_check
        - drop_check
        - table_options
        - partition_options
        - rename_table
    table_state:
      label: Table state
      importance: important
      values: [exists, missing, wrong_object_type]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    algorithm_option:
      label: ALGORITHM option
      importance: non_important
      values: [omitted, default, instant, inplace, copy]
    lock_option:
      label: LOCK option
      importance: non_important
      values: [omitted, default, none, shared, exclusive]
    validation_option:
      label: WITH/WITHOUT VALIDATION
      importance: non_important
      values: [omitted, with_validation, without_validation]
    column_position_shape:
      label: FIRST / AFTER column position
      importance: non_important
      values: [omitted, first, after_column]
    index_visibility_shape:
      label: ALTER INDEX visibility
      importance: non_important
      values: [omitted, visible, invisible]
    invalid_combination:
      label: Invalid or excluded combination
      importance: non_important
      values: [none, invisible_column_8_0_23_excluded, autoextend_size_8_0_23_excluded]
  defaults:
    alter_branch: add_column
    table_state: exists
    expected_status: success
    algorithm_option: omitted
    lock_option: omitted
    validation_option: omitted
    column_position_shape: omitted
    index_visibility_shape: omitted
    invalid_combination: none
  coverage_policy:
    main_combination_axes: [alter_branch, table_state, expected_status]
    non_main_factors: [algorithm_option, lock_option, validation_option, column_position_shape, index_visibility_shape, invalid_combination]
    python_expand_threshold: 300
  rendering:
    statement_template: "ALTER TABLE {table_name} ADD COLUMN added_col INT NULL"
    verification_query_template: "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}' AND COLUMN_NAME = 'added_col'"
    factor_value_bindings: {}
```
