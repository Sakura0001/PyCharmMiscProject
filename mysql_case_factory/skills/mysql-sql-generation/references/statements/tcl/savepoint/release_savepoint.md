# RELEASE SAVEPOINT

Official source: https://dev.mysql.com/doc/refman/8.0/en/savepoint.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: savepoint
  skill_name: release_savepoint
  official_source: https://dev.mysql.com/doc/refman/8.0/en/savepoint.html
  statement:
    key: release_savepoint
    name: RELEASE SAVEPOINT
    aliases: [release savepoint]
    purpose: Remove a named savepoint from the current transaction.
  syntax_templates:
    - "RELEASE SAVEPOINT identifier"
  factor_layers:
    - tier: T1
      factors: [savepoint_state, transaction_state, expected_status]
    - tier: T2
      factors: [name_shape]
  factors:
    savepoint_state:
      label: Savepoint state
      importance: important
      values: [exists, missing, already_released]
    transaction_state:
      label: Transaction state
      importance: important
      values: [active_transaction, outside_transaction]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    name_shape:
      label: Savepoint identifier
      importance: non_important
      values: [simple_identifier, quoted_reserved]
  defaults:
    savepoint_state: exists
    transaction_state: active_transaction
    expected_status: success
    name_shape: simple_identifier
  coverage_policy:
    main_combination_axes: [savepoint_state, transaction_state, expected_status]
    non_main_factors: [name_shape]
    python_expand_threshold: 80
  rendering:
    statement_template: "RELEASE SAVEPOINT {savepoint_name}"
    verification_query_template: ""
    factor_value_bindings: {}
```
