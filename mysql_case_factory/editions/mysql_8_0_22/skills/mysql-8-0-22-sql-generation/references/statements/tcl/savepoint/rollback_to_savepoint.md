# ROLLBACK TO SAVEPOINT

Official source: https://dev.mysql.com/doc/refman/8.0/en/savepoint.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: savepoint
  skill_name: rollback_to_savepoint
  official_source: https://dev.mysql.com/doc/refman/8.0/en/savepoint.html
  statement:
    key: rollback_to_savepoint
    name: ROLLBACK TO SAVEPOINT
    aliases: [rollback to savepoint]
    purpose: Roll back a transaction to a named savepoint without ending the transaction.
  syntax_templates:
    - "ROLLBACK [WORK] TO [SAVEPOINT] identifier"
  factor_layers:
    - tier: T1
      factors: [savepoint_state, work_keyword, savepoint_keyword, expected_status]
    - tier: T2
      factors: [transaction_state]
  factors:
    savepoint_state:
      label: Savepoint state
      importance: important
      values: [exists, missing, released]
    work_keyword:
      label: WORK keyword
      importance: important
      values: [omitted, present]
    savepoint_keyword:
      label: SAVEPOINT keyword
      importance: important
      values: [omitted, present]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    transaction_state:
      label: Transaction state
      importance: non_important
      values: [active_transaction, outside_transaction]
  defaults:
    savepoint_state: exists
    work_keyword: omitted
    savepoint_keyword: present
    expected_status: success
    transaction_state: active_transaction
  coverage_policy:
    main_combination_axes: [savepoint_state, work_keyword, savepoint_keyword, expected_status]
    non_main_factors: [transaction_state]
    python_expand_threshold: 120
  rendering:
    statement_template: "ROLLBACK{work_sql} TO{savepoint_sql} {savepoint_name}"
    verification_query_template: ""
    factor_value_bindings:
      work_sql:
        factor: work_keyword
        values: {omitted: "", present: " WORK"}
      savepoint_sql:
        factor: savepoint_keyword
        values: {omitted: "", present: " SAVEPOINT"}
```
