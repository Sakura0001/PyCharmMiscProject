# SET TRANSACTION

Official source: https://dev.mysql.com/doc/refman/8.0/en/set-transaction.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: transaction
  skill_name: set_transaction
  official_source: https://dev.mysql.com/doc/refman/8.0/en/set-transaction.html
  statement:
    key: set_transaction
    name: SET TRANSACTION
    aliases: [set transaction]
    purpose: Set transaction isolation level or access mode for the next, session, or global transaction scope.
  syntax_templates:
    - "SET [GLOBAL | SESSION] TRANSACTION transaction_characteristic [, transaction_characteristic] ..."
  factor_layers:
    - tier: T1
      factors: [scope, characteristic_shape, transaction_state, expected_status]
    - tier: T2
      factors: [isolation_level, access_mode]
  factors:
    scope:
      label: Scope
      importance: important
      values: [next_transaction, session, global]
    characteristic_shape:
      label: Transaction characteristic
      importance: important
      values: [isolation_only, access_mode_only, isolation_and_access_mode]
    transaction_state:
      label: Transaction state
      importance: important
      values: [outside_transaction, active_transaction]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    isolation_level:
      label: Isolation level
      importance: non_important
      values: [read_uncommitted, read_committed, repeatable_read, serializable]
    access_mode:
      label: Access mode
      importance: non_important
      values: [read_write, read_only]
  defaults:
    scope: next_transaction
    characteristic_shape: isolation_only
    transaction_state: outside_transaction
    expected_status: success
    isolation_level: repeatable_read
    access_mode: read_write
  coverage_policy:
    main_combination_axes: [scope, characteristic_shape, transaction_state, expected_status]
    non_main_factors: [isolation_level, access_mode]
    python_expand_threshold: 140
  rendering:
    statement_template: "SET{scope_sql} TRANSACTION ISOLATION LEVEL REPEATABLE READ"
    verification_query_template: ""
    factor_value_bindings:
      scope_sql:
        factor: scope
        values:
          next_transaction: ""
          session: " SESSION"
          global: " GLOBAL"
```
