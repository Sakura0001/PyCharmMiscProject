# EXECUTE

Official source: https://dev.mysql.com/doc/refman/8.0/en/execute.html

```yaml
structured_config:
  kind: statement
  category: prepared
  domain: prepared_statement
  skill_name: execute
  official_source: https://dev.mysql.com/doc/refman/8.0/en/execute.html
  statement:
    key: execute
    name: EXECUTE
    aliases: [execute prepared statement]
    purpose: Execute a MySQL prepared statement.
  syntax_templates:
    - "EXECUTE stmt_name [USING @var_name [, @var_name] ...]"
  factor_layers:
    - tier: T1
      factors: [argument_shape, prepared_state, expected_status]
  factors:
    argument_shape:
      label: USING variables
      importance: important
      values: [omitted, one_user_variable, two_user_variables]
    prepared_state:
      label: Prepared statement state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    argument_shape: omitted
    prepared_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [argument_shape, prepared_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 100
  rendering:
    statement_template: "EXECUTE {prepared_name}{using_sql}"
    verification_query_template: ""
    factor_value_bindings:
      using_sql:
        factor: argument_shape
        values:
          omitted: ""
          one_user_variable: " USING @p1"
          two_user_variables: " USING @p1, @p2"
```
