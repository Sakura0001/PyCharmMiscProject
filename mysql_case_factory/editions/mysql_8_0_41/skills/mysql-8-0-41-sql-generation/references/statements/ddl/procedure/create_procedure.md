# CREATE PROCEDURE

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: procedure
  skill_name: create_procedure
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html
  statement:
    key: create_procedure
    name: CREATE PROCEDURE
    aliases: [create procedure]
    purpose: Create a MySQL stored procedure, including IF NOT EXISTS available since 8.0.29.
  syntax_templates:
    - "CREATE [DEFINER = user] PROCEDURE [IF NOT EXISTS] sp_name ([proc_parameter[,...]]) [characteristic ...] routine_body"
  factor_layers:
    - tier: T1
      factors: [if_not_exists, parameter_shape, body_shape, expected_status]
    - tier: T2
      factors: [definer_shape, security_shape, comment_shape]
  factors:
    if_not_exists:
      label: IF NOT EXISTS
      importance: important
      values: [omitted, present]
    parameter_shape:
      label: Procedure parameters
      importance: important
      values: [none, in_parameter, out_parameter, inout_parameter]
    body_shape:
      label: Routine body
      importance: important
      values: [single_statement, compound_block, invalid_body]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    definer_shape:
      label: DEFINER
      importance: non_important
      values: [omitted, current_user, explicit_user]
    security_shape:
      label: SQL SECURITY
      importance: non_important
      values: [omitted, definer, invoker]
    comment_shape:
      label: COMMENT characteristic
      importance: non_important
      values: [omitted, comment]
  defaults:
    if_not_exists: omitted
    parameter_shape: none
    body_shape: single_statement
    expected_status: success
    definer_shape: omitted
    security_shape: omitted
    comment_shape: omitted
  coverage_policy:
    main_combination_axes: [if_not_exists, parameter_shape, body_shape, expected_status]
    non_main_factors: [definer_shape, security_shape, comment_shape]
    python_expand_threshold: 140
  rendering:
    statement_template: "CREATE PROCEDURE {procedure_name}() SELECT 1"
    verification_query_template: "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_NAME = '{procedure_name}'"
    factor_value_bindings: {}
```
