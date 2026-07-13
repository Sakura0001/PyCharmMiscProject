# SAVEPOINT

Official source: https://dev.mysql.com/doc/refman/8.0/en/savepoint.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: savepoint
  skill_name: savepoint
  official_source: https://dev.mysql.com/doc/refman/8.0/en/savepoint.html
  statement:
    key: savepoint
    name: SAVEPOINT
    aliases: [savepoint]
    purpose: Set or replace a named savepoint within the current transaction.
  syntax_templates:
    - "SAVEPOINT identifier"
  factor_layers:
    - tier: T1
      factors: [transaction_state, name_shape, duplicate_name_behavior, expected_status]
  factors:
    transaction_state:
      label: Transaction state
      importance: important
      values: [active_transaction, outside_transaction]
    name_shape:
      label: Savepoint identifier
      importance: important
      values: [simple_identifier, quoted_reserved, long_identifier]
    duplicate_name_behavior:
      label: Duplicate savepoint behavior
      importance: important
      values: [new_name, replace_existing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    transaction_state: active_transaction
    name_shape: simple_identifier
    duplicate_name_behavior: new_name
    expected_status: success
  coverage_policy:
    main_combination_axes: [transaction_state, name_shape, duplicate_name_behavior, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "SAVEPOINT {savepoint_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
