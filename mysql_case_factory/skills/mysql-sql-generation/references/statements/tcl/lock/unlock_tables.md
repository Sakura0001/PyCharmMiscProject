# UNLOCK TABLES

Official source: https://dev.mysql.com/doc/refman/8.0/en/lock-tables.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: lock
  skill_name: unlock_tables
  official_source: https://dev.mysql.com/doc/refman/8.0/en/lock-tables.html
  statement:
    key: unlock_tables
    name: UNLOCK TABLES
    aliases: [unlock tables]
    purpose: Release explicit table locks held by the current session.
  syntax_templates:
    - "UNLOCK TABLES"
  factor_layers:
    - tier: T1
      factors: [held_lock_state, global_read_lock_state, expected_status]
    - tier: T2
      factors: [transaction_interaction]
  factors:
    held_lock_state:
      label: Held table lock state
      importance: important
      values: [locks_held, no_locks_held]
    global_read_lock_state:
      label: Global read lock state
      importance: important
      values: [not_held, held_by_session]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    transaction_interaction:
      label: Transaction interaction
      importance: non_important
      values: [outside_transaction, active_transaction]
  defaults:
    held_lock_state: locks_held
    global_read_lock_state: not_held
    expected_status: success
    transaction_interaction: outside_transaction
  coverage_policy:
    main_combination_axes: [held_lock_state, global_read_lock_state, expected_status]
    non_main_factors: [transaction_interaction]
    python_expand_threshold: 80
  rendering:
    statement_template: "UNLOCK TABLES"
    verification_query_template: ""
    factor_value_bindings: {}
```
