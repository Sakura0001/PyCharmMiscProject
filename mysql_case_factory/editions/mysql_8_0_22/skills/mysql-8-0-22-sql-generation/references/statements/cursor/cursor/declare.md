# DECLARE CURSOR

Official source: https://dev.mysql.com/doc/refman/8.0/en/declare-cursor.html

```yaml
structured_config:
  kind: statement
  category: cursor
  domain: cursor
  skill_name: declare
  official_source: https://dev.mysql.com/doc/refman/8.0/en/declare-cursor.html
  statement:
    key: declare
    name: DECLARE CURSOR
    aliases: [declare cursor]
    purpose: Declare a MySQL stored-program cursor.
  syntax_templates:
    - "DECLARE cursor_name CURSOR FOR select_statement"
  factor_layers:
    - tier: T1
      factors: [query_shape, declaration_order_state, expected_status]
  factors:
    query_shape:
      label: Cursor SELECT statement
      importance: important
      values: [simple_select, join_select, select_with_into_invalid]
    declaration_order_state:
      label: Stored program declaration order
      importance: important
      values: [before_handlers, after_handler_invalid]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    query_shape: simple_select
    declaration_order_state: before_handlers
    expected_status: success
  coverage_policy:
    main_combination_axes: [query_shape, declaration_order_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "DECLARE {cursor_name} CURSOR FOR SELECT id_col FROM {table_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
