# FETCH CURSOR

Official source: https://dev.mysql.com/doc/refman/8.0/en/fetch.html

```yaml
structured_config:
  kind: statement
  category: cursor
  domain: cursor
  skill_name: fetch
  official_source: https://dev.mysql.com/doc/refman/8.0/en/fetch.html
  statement:
    key: fetch
    name: FETCH
    aliases: [fetch cursor]
    purpose: Fetch the next row from a MySQL stored-program cursor.
  syntax_templates:
    - "FETCH [[NEXT] FROM] cursor_name INTO var_name [, var_name] ..."
  factor_layers:
    - tier: T1
      factors: [cursor_state, destination_shape, expected_status]
  factors:
    cursor_state:
      label: Cursor state
      importance: important
      values: [open_has_row, open_no_more_rows, closed, missing]
    destination_shape:
      label: INTO variables
      importance: important
      values: [matching_count, too_few, too_many]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    cursor_state: open_has_row
    destination_shape: matching_count
    expected_status: success
  coverage_policy:
    main_combination_axes: [cursor_state, destination_shape, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "FETCH {cursor_name} INTO v_id"
    verification_query_template: ""
    factor_value_bindings: {}
```
