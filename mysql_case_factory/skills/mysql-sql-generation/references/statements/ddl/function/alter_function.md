# ALTER FUNCTION

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-function.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: function
  skill_name: alter_function
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-function.html
  statement:
    key: alter_function
    name: ALTER FUNCTION
    aliases: [alter function, alter stored function]
    purpose: Alter MySQL stored function characteristics. MySQL does not alter routine parameters or body in place.
  syntax_templates:
    - "ALTER FUNCTION sp_name [characteristic ...]"
  factor_layers:
    - tier: T1
      factors: [function_state, characteristic_shape, expected_status]
  factors:
    function_state:
      label: Function state
      importance: important
      values: [exists, missing, wrong_routine_type]
    characteristic_shape:
      label: Altered characteristic
      importance: important
      values: [comment, sql_security_definer, sql_security_invoker, deterministic]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    function_state: exists
    characteristic_shape: comment
    expected_status: success
  coverage_policy:
    main_combination_axes: [function_state, characteristic_shape, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "ALTER FUNCTION {function_name} COMMENT 'mysql case function'"
    verification_query_template: "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_NAME = '{function_name}'"
    factor_value_bindings: {}
```
