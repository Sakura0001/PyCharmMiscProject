# CALL

Official source: https://dev.mysql.com/doc/refman/8.0/en/call.html

```yaml
structured_config:
  kind: statement
  category: dml
  domain: routine
  skill_name: call
  official_source: https://dev.mysql.com/doc/refman/8.0/en/call.html
  statement:
    key: call
    name: CALL
    aliases: [call]
    purpose: Call MySQL stored procedures, including OUT and INOUT parameter cases.
  syntax_templates:
    - "CALL sp_name([parameter[,...]])"
    - "CALL sp_name[()]"
  factor_layers:
    - tier: T1
      factors: [parameter_shape, procedure_state, expected_status]
    - tier: T2
      factors: [parentheses_shape, prepared_call_shape]
  factors:
    parameter_shape:
      label: Procedure parameter shape
      importance: important
      values: [no_parameter, in_parameter, out_parameter, inout_parameter]
    procedure_state:
      label: Procedure state
      importance: important
      values: [exists, missing, wrong_routine_type]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    parentheses_shape:
      label: Parentheses for no-arg call
      importance: non_important
      values: [present, omitted_when_no_arg]
    prepared_call_shape:
      label: Prepared CALL parameter markers
      importance: non_important
      values: [not_prepared, prepared_with_markers]
  defaults:
    parameter_shape: no_parameter
    procedure_state: exists
    expected_status: success
    parentheses_shape: present
    prepared_call_shape: not_prepared
  coverage_policy:
    main_combination_axes: [parameter_shape, procedure_state, expected_status]
    non_main_factors: [parentheses_shape, prepared_call_shape]
    python_expand_threshold: 120
  rendering:
    statement_template: "CALL {procedure_name}()"
    verification_query_template: ""
    factor_value_bindings: {}
```
