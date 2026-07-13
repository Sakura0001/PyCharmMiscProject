# CREATE FUNCTION

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: function
  skill_name: create_function
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html
  statement:
    key: create_function
    name: CREATE FUNCTION
    aliases: [create function, create stored function]
    purpose: Create a MySQL stored function, including IF NOT EXISTS available since 8.0.29. Loadable functions are tracked separately.
  syntax_templates:
    - "CREATE [DEFINER = user] FUNCTION [IF NOT EXISTS] sp_name ([func_parameter[,...]]) RETURNS type [characteristic ...] routine_body"
  factor_layers:
    - tier: T1
      factors: [if_not_exists, parameter_shape, return_type_shape, body_shape, expected_status]
    - tier: T2
      factors: [determinism_shape, data_access_shape, security_shape]
  factors:
    if_not_exists:
      label: IF NOT EXISTS (available since 8.0.29)
      importance: important
      values: [omitted, present]
    parameter_shape:
      label: Function parameters
      importance: important
      values: [none, one_parameter, multiple_parameters]
    return_type_shape:
      label: RETURNS type
      importance: important
      values: [int_type, varchar_type, json_type]
    body_shape:
      label: Function body
      importance: important
      values: [return_literal, compound_block, invalid_body]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    determinism_shape:
      label: DETERMINISTIC characteristic
      importance: non_important
      values: [omitted, deterministic, not_deterministic]
    data_access_shape:
      label: SQL data access characteristic
      importance: non_important
      values: [omitted, contains_sql, reads_sql_data, modifies_sql_data, no_sql]
    security_shape:
      label: SQL SECURITY
      importance: non_important
      values: [omitted, definer, invoker]
  defaults:
    if_not_exists: omitted
    parameter_shape: none
    return_type_shape: int_type
    body_shape: return_literal
    expected_status: success
    determinism_shape: deterministic
    data_access_shape: contains_sql
    security_shape: omitted
  coverage_policy:
    main_combination_axes: [if_not_exists, parameter_shape, return_type_shape, body_shape, expected_status]
    non_main_factors: [determinism_shape, data_access_shape, security_shape]
    python_expand_threshold: 180
  rendering:
    statement_template: "CREATE FUNCTION {function_name}() RETURNS INT DETERMINISTIC RETURN 1"
    verification_query_template: "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_NAME = '{function_name}'"
    factor_value_bindings: {}
```
