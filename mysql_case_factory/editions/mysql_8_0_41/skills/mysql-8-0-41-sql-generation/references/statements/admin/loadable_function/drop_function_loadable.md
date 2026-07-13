# DROP FUNCTION (Loadable Function)

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-function-loadable.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: loadable_function
  skill_name: drop_function_loadable
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-function-loadable.html
  statement:
    key: drop_function_loadable
    name: DROP FUNCTION
    aliases: [drop loadable function, drop udf]
    purpose: Unregister a MySQL loadable function. This is separate from stored DROP FUNCTION.
  syntax_templates:
    - "DROP FUNCTION function_name"
  factor_layers:
    - tier: T1
      factors: [function_state, privilege_context, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    function_state:
      label: Loadable function state
      importance: important
      values: [registered_test_function, missing, builtin_or_stored_function]
    privilege_context:
      label: Privilege context
      importance: important
      values: [has_required_privilege, missing_required_privilege]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [safe_negative, isolated_positive, skip_dynamic_load]
  defaults:
    function_state: missing
    privilege_context: missing_required_privilege
    expected_status: failure
    execution_mode: safe_negative
  coverage_policy:
    main_combination_axes: [function_state, privilege_context, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "DROP FUNCTION {loadable_function_name}"
    verification_query_template: "SELECT NAME FROM mysql.func WHERE NAME = '{loadable_function_name}'"
    factor_value_bindings: {}
```
