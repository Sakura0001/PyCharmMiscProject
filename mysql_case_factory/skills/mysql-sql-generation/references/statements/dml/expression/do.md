# DO

Official source: https://dev.mysql.com/doc/refman/8.0/en/do.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: expression
  skill_name: do
  official_source: https://dev.mysql.com/doc/refman/8.0/en/do.html
  statement:
    key: do
    name: DO
    aliases: [do]
    purpose: Execute MySQL expressions without returning a result set.
  syntax_templates:
    - "DO expr [, expr] ..."
  factor_layers:
    - tier: T1
      factors: [expression_shape, expected_status]
    - tier: T2
      factors: [side_effect_shape]
  factors:
    expression_shape:
      label: Expression shape
      importance: important
      values: [literal_expression, function_call, assignment_expression, invalid_expression]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    side_effect_shape:
      label: Side effect
      importance: non_important
      values: [none, user_variable_assignment]
  defaults:
    expression_shape: literal_expression
    expected_status: success
    side_effect_shape: none
  coverage_policy:
    main_combination_axes: [expression_shape, expected_status]
    non_main_factors: [side_effect_shape]
    python_expand_threshold: 80
  rendering:
    statement_template: "DO 1 + 1"
    verification_query_template: ""
    factor_value_bindings: {}
```
