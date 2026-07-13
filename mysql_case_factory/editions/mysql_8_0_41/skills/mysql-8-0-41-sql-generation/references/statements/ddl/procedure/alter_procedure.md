# ALTER PROCEDURE

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-procedure.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: procedure
  skill_name: alter_procedure
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-procedure.html
  statement:
    key: alter_procedure
    name: ALTER PROCEDURE
    aliases: [alter procedure]
    purpose: Alter MySQL stored procedure characteristics.
  syntax_templates:
    - "ALTER PROCEDURE sp_name [characteristic ...]"
  factor_layers:
    - tier: T1
      factors: [procedure_state, characteristic_shape, expected_status]
  factors:
    procedure_state:
      label: Procedure state
      importance: important
      values: [exists, missing, wrong_routine_type]
    characteristic_shape:
      label: Altered characteristic
      importance: important
      values: [comment, sql_security_definer, sql_security_invoker]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    procedure_state: exists
    characteristic_shape: comment
    expected_status: success
  coverage_policy:
    main_combination_axes: [procedure_state, characteristic_shape, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "ALTER PROCEDURE {procedure_name} COMMENT 'mysql case procedure'"
    verification_query_template: "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_NAME = '{procedure_name}'"
    factor_value_bindings: {}
```
