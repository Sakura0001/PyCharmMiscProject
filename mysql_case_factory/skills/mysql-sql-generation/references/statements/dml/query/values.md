# VALUES

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/values.html
- https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: query
  skill_name: values
  official_source: https://dev.mysql.com/doc/refman/8.0/en/values.html
  statement:
    key: values
    name: VALUES
    aliases: [values]
    purpose: Generate MySQL VALUES statement cases available in MySQL 8.0.22.
  syntax_templates:
    - "VALUES ROW(value_list) [, ROW(value_list)] ... [ORDER BY column_designator] [LIMIT number]"
  factor_layers:
    - tier: T1
      factors: [row_shape, ordering_limit_shape, expected_status]
  factors:
    row_shape:
      label: Row constructor shape
      importance: important
      values: [single_row, multi_row, mismatched_arity]
    ordering_limit_shape:
      label: ORDER BY / LIMIT
      importance: important
      values: [omitted, order_by, limit, order_by_limit]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    row_shape: single_row
    ordering_limit_shape: omitted
    expected_status: success
  coverage_policy:
    main_combination_axes: [row_shape, ordering_limit_shape, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "VALUES ROW(1, 'a'), ROW(2, 'b')"
    verification_query_template: ""
    factor_value_bindings: {}
```
