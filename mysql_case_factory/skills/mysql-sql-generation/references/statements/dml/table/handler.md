# HANDLER

Official source: https://dev.mysql.com/doc/refman/8.0/en/handler.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: table
  skill_name: handler
  official_source: https://dev.mysql.com/doc/refman/8.0/en/handler.html
  statement:
    key: handler
    name: HANDLER
    aliases: [handler]
    purpose: Use MySQL low-level HANDLER table access statements.
  syntax_templates:
    - "HANDLER tbl_name OPEN [AS alias]"
    - "HANDLER tbl_name READ index_name {= | >= | <= | < | >} (value_list) [WHERE where_condition] [LIMIT ...]"
    - "HANDLER tbl_name READ {FIRST | NEXT | PREV | LAST} [WHERE where_condition] [LIMIT ...]"
    - "HANDLER tbl_name CLOSE"
  factor_layers:
    - tier: T1
      factors: [handler_branch, handler_state, expected_status]
    - tier: T2
      factors: [read_direction, where_limit_shape]
  factors:
    handler_branch:
      label: HANDLER branch
      importance: important
      values: [open, read_key, read_first, read_next, read_prev, read_last, close]
    handler_state:
      label: Handler lifecycle state
      importance: important
      values: [closed, open, missing_table, missing_index]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    read_direction:
      label: Read direction
      importance: non_important
      values: [not_applicable, first, next, prev, last, key_compare]
    where_limit_shape:
      label: WHERE and LIMIT
      importance: non_important
      values: [omitted, where_filter, limit, where_limit]
  defaults:
    handler_branch: open
    handler_state: closed
    expected_status: success
    read_direction: not_applicable
    where_limit_shape: omitted
  coverage_policy:
    main_combination_axes: [handler_branch, handler_state, expected_status]
    non_main_factors: [read_direction, where_limit_shape]
    python_expand_threshold: 160
  rendering:
    statement_template: "HANDLER {table_name} OPEN"
    verification_query_template: ""
    factor_value_bindings: {}
```
