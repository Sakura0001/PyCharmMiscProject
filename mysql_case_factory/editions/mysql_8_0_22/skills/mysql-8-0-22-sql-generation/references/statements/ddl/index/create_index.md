# CREATE INDEX

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-index.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: index
  skill_name: create_index
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-index.html
  statement:
    key: create_index
    name: CREATE INDEX
    aliases:
      - create index
      - 创建索引
    purpose: Create MySQL 8.0.22 secondary indexes and cover MySQL-specific index classes and online DDL options.
  syntax_templates:
    - "CREATE [UNIQUE | FULLTEXT | SPATIAL] INDEX index_name [index_type] ON tbl_name (key_part, ...) [index_option] ... [algorithm_option | lock_option] ..."
  factor_layers:
    - tier: T1
      name: Core syntax
      factors: [index_kind, key_part_shape, expected_status]
    - tier: T2
      name: Important behavior
      factors: [index_type, visibility, algorithm_lock]
    - tier: T3
      name: Names and inputs
      factors: [index_name_shape, prefix_length, parser_clause]
    - tier: T5
      name: Boundaries
      factors: [invalid_combination]
  factors:
    index_kind:
      label: Index class
      importance: important
      values:
        - normal
        - unique
        - fulltext
        - spatial
    key_part_shape:
      label: Key part shape
      importance: important
      values:
        - column
        - descending_column
        - functional_key_part
        - prefix_length
    expected_status:
      label: Expected result
      importance: important
      values:
        - success
        - failure
    index_type:
      label: USING index type
      importance: non_important
      values:
        - omitted
        - btree
        - hash
    visibility:
      label: Index visibility
      importance: non_important
      values:
        - omitted
        - visible
        - invisible
    algorithm_lock:
      label: Online DDL options
      importance: non_important
      values:
        - omitted
        - inplace_none
        - copy_shared
    index_name_shape:
      label: Index identifier shape
      importance: non_important
      values:
        - explicit
        - quoted_reserved
    prefix_length:
      label: Prefix length
      importance: non_important
      values:
        - omitted
        - varchar_prefix
    parser_clause:
      label: FULLTEXT parser
      importance: non_important
      values:
        - omitted
        - ngram_parser
    invalid_combination:
      label: Invalid combination
      importance: non_important
      values:
        - none
        - fulltext_on_int
        - spatial_on_nullable
  defaults:
    index_kind: normal
    key_part_shape: column
    expected_status: success
    index_type: omitted
    visibility: omitted
    algorithm_lock: omitted
    index_name_shape: explicit
    prefix_length: omitted
    parser_clause: omitted
    invalid_combination: none
  coverage_policy:
    main_combination_axes: [index_kind, key_part_shape, expected_status]
    non_main_factors: [index_type, visibility, algorithm_lock, index_name_shape, prefix_length, parser_clause, invalid_combination]
    python_expand_threshold: 200
  factor_catalog_mapping:
    source_catalog: references/common/mysql80_factor_catalog.md
    object_domain: index
    imported_factors:
      - catalog_factor: index.definition.index_kind
        local_factor: index_kind
        target_tier: T1
        coverage_role: main_axis
        value_policy: reuse_catalog_values
        reason: MySQL CREATE INDEX exposes UNIQUE, FULLTEXT, and SPATIAL index classes.
      - catalog_factor: index.definition.index_type
        local_factor: index_type
        target_tier: T2
        coverage_role: rotate_attach
        value_policy: reuse_catalog_values
        reason: USING BTREE/HASH is a MySQL index option.
      - catalog_factor: index.options.visibility
        local_factor: visibility
        target_tier: T2
        coverage_role: rotate_attach
        value_policy: reuse_catalog_values
        reason: MySQL supports visible and invisible indexes before 8.0.22.
      - catalog_factor: index.options.algorithm_lock
        local_factor: algorithm_lock
        target_tier: T2
        coverage_role: rotate_attach
        value_policy: reuse_catalog_values
        reason: CREATE INDEX maps to ALTER TABLE and supports online DDL options.
  rendering:
    statement_template: "CREATE {index_kind_sql}INDEX {index_name} ON {table_name} ({key_part_sql}){index_type_sql}{visibility_sql}"
    verification_query_template: "SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}' AND INDEX_NAME = '{index_name}'"
    factor_value_bindings:
      index_kind_sql:
        factor: index_kind
        values:
          normal: ""
          unique: "UNIQUE "
          fulltext: "FULLTEXT "
          spatial: "SPATIAL "
      key_part_sql:
        factor: key_part_shape
        values:
          column: "int_col"
          descending_column: "int_col DESC"
          functional_key_part: "((int_col + 1))"
          prefix_length: "varchar_col(10)"
      index_type_sql:
        factor: index_type
        values:
          omitted: ""
          btree: " USING BTREE"
          hash: " USING HASH"
      visibility_sql:
        factor: visibility
        values:
          omitted: ""
          visible: " VISIBLE"
          invisible: " INVISIBLE"
```
