# PREPARE

Official source: https://dev.mysql.com/doc/refman/8.0/en/prepare.html

```yaml
structured_config:
  kind: statement
  category: prepared
  domain: prepared_statement
  skill_name: prepare
  official_source: https://dev.mysql.com/doc/refman/8.0/en/prepare.html
  statement:
    key: prepare
    name: PREPARE
    aliases: [prepare, prepared statement]
    purpose: Create a MySQL session prepared statement from SQL text.
  syntax_templates:
    - "PREPARE stmt_name FROM preparable_stmt"
  factor_layers:
    - tier: T1
      factors: [source_shape, marker_shape, expected_status]
    - tier: T2
      factors: [name_reuse]
  factors:
    source_shape:
      label: SQL text source
      importance: important
      values: [string_literal, user_variable]
    marker_shape:
      label: Parameter marker shape
      importance: important
      values: [no_marker, one_marker, two_markers]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    name_reuse:
      label: Existing prepared statement name
      importance: non_important
      values: [new_name, replace_existing]
  defaults:
    source_shape: string_literal
    marker_shape: no_marker
    expected_status: success
    name_reuse: new_name
  coverage_policy:
    main_combination_axes: [source_shape, marker_shape, expected_status]
    non_main_factors: [name_reuse]
    python_expand_threshold: 100
  rendering:
    statement_template: "PREPARE {prepared_name} FROM {source_sql}"
    verification_query_template: ""
    factor_value_bindings:
      source_sql:
        factor: source_shape
        values:
          string_literal: "'SELECT 1'"
          user_variable: "@prepared_sql"
```
