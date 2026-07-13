# CREATE TABLE

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-table.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: table
  skill_name: create_table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-table.html
  statement:
    key: create_table
    name: CREATE TABLE
    aliases:
      - create table
      - 创建表
    purpose: Create MySQL 8.0.22 base tables, temporary tables, LIKE tables, and SELECT-derived tables.
  syntax_templates:
    - "CREATE [TEMPORARY] TABLE [IF NOT EXISTS] tbl_name (create_definition, ...) [table_options] [partition_options]"
    - "CREATE [TEMPORARY] TABLE [IF NOT EXISTS] tbl_name LIKE old_tbl_name"
    - "CREATE [TEMPORARY] TABLE [IF NOT EXISTS] tbl_name [create_definition, ...] [table_options] [IGNORE | REPLACE] [AS] query_expression"
  factor_layers:
    - tier: T1
      name: Core syntax
      factors: [statement_branch, table_kind, if_not_exists, expected_status]
    - tier: T2
      name: Important behavior
      factors: [constraint_shape, generated_column_shape, table_option_shape]
    - tier: T3
      name: Names and data shapes
      factors: [table_name_shape, data_type_family]
    - tier: T5
      name: Boundaries
      factors: [duplicate_table_state]
  factors:
    statement_branch:
      label: CREATE TABLE syntax branch
      importance: important
      values:
        - column_definition
        - create_like
        - create_select
    table_kind:
      label: TEMPORARY option
      importance: important
      values:
        - permanent
        - temporary
    if_not_exists:
      label: IF NOT EXISTS
      importance: important
      values:
        - omitted
        - present
    expected_status:
      label: Expected result
      importance: important
      values:
        - success
        - failure
    constraint_shape:
      label: Constraint shape
      importance: non_important
      values:
        - primary_key
        - unique_key
        - foreign_key
        - check_enforced
        - check_not_enforced
    generated_column_shape:
      label: Generated column
      importance: non_important
      values:
        - omitted
        - virtual
        - stored
    table_option_shape:
      label: Table options
      importance: non_important
      values:
        - engine_innodb
        - engine_memory
        - charset_collate
        - encryption
    table_name_shape:
      label: Table identifier shape
      importance: non_important
      values:
        - unquoted_lower
        - quoted_reserved
    data_type_family:
      label: Data type family
      importance: non_important
      values:
        - numeric
        - string
        - temporal
        - json
        - spatial
    duplicate_table_state:
      label: Duplicate table state
      importance: non_important
      values:
        - no_conflict
        - name_already_exists
  defaults:
    statement_branch: column_definition
    table_kind: permanent
    if_not_exists: omitted
    expected_status: success
    constraint_shape: primary_key
    generated_column_shape: omitted
    table_option_shape: engine_innodb
    table_name_shape: unquoted_lower
    data_type_family: numeric
    duplicate_table_state: no_conflict
  coverage_policy:
    main_combination_axes: [statement_branch, table_kind, if_not_exists, expected_status]
    non_main_factors: [constraint_shape, generated_column_shape, table_option_shape, table_name_shape, data_type_family, duplicate_table_state]
    python_expand_threshold: 200
  factor_catalog_mapping:
    source_catalog: references/common/mysql80_factor_catalog.md
    object_domain: table
    imported_factors:
      - catalog_factor: table.definition.temporary
        local_factor: table_kind
        target_tier: T1
        coverage_role: main_axis
        value_policy: statement_specific_subset
        selected_values: [permanent, temporary]
        reason: CREATE TABLE exposes TEMPORARY as a top-level branch.
      - catalog_factor: table.definition.if_not_exists
        local_factor: if_not_exists
        target_tier: T1
        coverage_role: main_axis
        value_policy: statement_specific_subset
        selected_values: [omitted, present]
        reason: IF NOT EXISTS changes duplicate-name behavior.
      - catalog_factor: table.definition.storage_engine
        local_factor: table_option_shape
        target_tier: T2
        coverage_role: representative_or_main
        value_policy: statement_specific_subset
        selected_values: [innodb, memory]
        reason: ENGINE affects physical behavior and feature support.
  rendering:
    statement_template: "{temporary_clause}CREATE TABLE {if_not_exists_clause}{table_name} (id BIGINT NOT NULL AUTO_INCREMENT, value_col INT, label_col VARCHAR(100), PRIMARY KEY (id)) ENGINE=InnoDB"
    verification_query_template: "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}'"
    factor_value_bindings:
      temporary_clause:
        factor: table_kind
        values:
          permanent: ""
          temporary: "TEMPORARY "
      if_not_exists_clause:
        factor: if_not_exists
        values:
          omitted: ""
          present: "IF NOT EXISTS "
```
