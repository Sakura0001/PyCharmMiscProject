# TABLE

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/table.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: query
  skill_name: table
  official_source: https://dev.mysql.com/doc/refman/8.0/en/table.html
  statement:
    key: table
    name: TABLE
    aliases: [table statement]
    purpose: Generate MySQL TABLE statement cases available in MySQL 8.0.22.
  syntax_templates:
    - "TABLE table_name [ORDER BY column_name] [LIMIT number [OFFSET number]] [INTO OUTFILE ... | INTO DUMPFILE ... | INTO var_name [, var_name] ...]"
  factor_layers:
    - tier: T1
      factors: [target_state, ordering_limit_shape, expected_status]
    - tier: T2
      factors: [into_shape]
  factors:
    target_state:
      label: Table target state
      importance: important
      values: [exists, missing, wrong_object_type]
    ordering_limit_shape:
      label: ORDER BY / LIMIT
      importance: important
      values: [omitted, order_by, limit, order_by_limit]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    into_shape:
      label: INTO destination
      importance: non_important
      values: [omitted, into_variables, into_outfile, into_dumpfile]
  defaults:
    target_state: exists
    ordering_limit_shape: omitted
    expected_status: success
    into_shape: omitted
  coverage_policy:
    main_combination_axes: [target_state, ordering_limit_shape, expected_status]
    non_main_factors: [into_shape]
    python_expand_threshold: 100
  rendering:
    statement_template: "TABLE {table_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
