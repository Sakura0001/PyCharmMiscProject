# CREATE FUNCTION (Loadable Function)

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-function-loadable.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: loadable_function
  skill_name: create_function_loadable
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-function-loadable.html
  statement:
    key: create_function_loadable
    name: CREATE FUNCTION
    aliases: [create loadable function, create udf]
    purpose: Register a MySQL loadable function implemented by a shared library. This is separate from stored CREATE FUNCTION.
  syntax_templates:
    - "CREATE [AGGREGATE] FUNCTION function_name RETURNS {STRING|INTEGER|REAL|DECIMAL} SONAME shared_library_name"
  factor_layers:
    - tier: T1
      factors: [aggregate_keyword, return_type, soname_shape, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    aggregate_keyword:
      label: AGGREGATE keyword
      importance: important
      values: [omitted, aggregate]
    return_type:
      label: Return type
      importance: important
      values: [string, integer, real, decimal]
    soname_shape:
      label: Shared library shape
      importance: important
      values: [existing_library, missing_library, invalid_soname]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [safe_negative, isolated_positive, skip_dynamic_load]
  defaults:
    aggregate_keyword: omitted
    return_type: integer
    soname_shape: missing_library
    expected_status: failure
    execution_mode: safe_negative
  coverage_policy:
    main_combination_axes: [aggregate_keyword, return_type, soname_shape, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 120
  rendering:
    statement_template: "CREATE FUNCTION {loadable_function_name} RETURNS INTEGER SONAME 'missing_mysql_case_udf.so'"
    verification_query_template: "SELECT NAME FROM mysql.func WHERE NAME = '{loadable_function_name}'"
    factor_value_bindings: {}
```
