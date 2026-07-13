# CLOSE CURSOR

Official source: https://dev.mysql.com/doc/refman/8.0/en/close.html

```yaml
structured_config:
  kind: statement
  category: cursor
  domain: cursor
  skill_name: close
  official_source: https://dev.mysql.com/doc/refman/8.0/en/close.html
  statement:
    key: close
    name: CLOSE
    aliases: [close cursor]
    purpose: Close a MySQL stored-program cursor.
  syntax_templates:
    - "CLOSE cursor_name"
  factor_layers:
    - tier: T1
      factors: [cursor_state, expected_status]
  factors:
    cursor_state:
      label: Cursor state
      importance: important
      values: [open, closed, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    cursor_state: open
    expected_status: success
  coverage_policy:
    main_combination_axes: [cursor_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 40
  rendering:
    statement_template: "CLOSE {cursor_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
