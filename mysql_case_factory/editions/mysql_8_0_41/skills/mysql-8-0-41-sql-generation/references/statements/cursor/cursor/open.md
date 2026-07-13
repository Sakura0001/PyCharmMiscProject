# OPEN CURSOR

Official source: https://dev.mysql.com/doc/refman/8.0/en/open.html

```yaml
structured_config:
  kind: statement
  category: cursor
  domain: cursor
  skill_name: open
  official_source: https://dev.mysql.com/doc/refman/8.0/en/open.html
  statement:
    key: open
    name: OPEN
    aliases: [open cursor]
    purpose: Open a MySQL stored-program cursor.
  syntax_templates:
    - "OPEN cursor_name"
  factor_layers:
    - tier: T1
      factors: [cursor_state, expected_status]
  factors:
    cursor_state:
      label: Cursor declaration/open state
      importance: important
      values: [declared_closed, missing, already_open]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    cursor_state: declared_closed
    expected_status: success
  coverage_policy:
    main_combination_axes: [cursor_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 40
  rendering:
    statement_template: "OPEN {cursor_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
