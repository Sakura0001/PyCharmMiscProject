# DROP FUNCTION

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-procedure.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: function
  skill_name: drop_function
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-procedure.html
  statement:
    key: drop_function
    name: DROP FUNCTION
    aliases: [drop function, drop stored function]
    purpose: Drop a MySQL stored function. Loadable-function DROP FUNCTION is tracked separately.
  syntax_templates:
    - "DROP FUNCTION [IF EXISTS] sp_name"
  factor_layers:
    - tier: T1
      factors: [if_exists, function_state, expected_status]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    function_state:
      label: Function state
      importance: important
      values: [exists, missing, wrong_routine_type]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    if_exists: omitted
    function_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [if_exists, function_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "DROP FUNCTION {if_exists_sql}{function_name}"
    verification_query_template: "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_NAME = '{function_name}'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
