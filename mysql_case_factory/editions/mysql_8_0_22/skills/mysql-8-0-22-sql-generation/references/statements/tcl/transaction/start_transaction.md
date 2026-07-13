# START TRANSACTION

Official source: https://dev.mysql.com/doc/refman/8.0/en/commit.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: transaction
  skill_name: start_transaction
  official_source: https://dev.mysql.com/doc/refman/8.0/en/commit.html
  statement:
    key: start_transaction
    name: START TRANSACTION
    aliases: [start transaction, begin]
    purpose: Start a MySQL transaction.
  syntax_templates:
    - "START TRANSACTION [transaction_characteristic [, transaction_characteristic] ...]"
    - "BEGIN [WORK]"
  factor_layers:
    - tier: T1
      factors: [statement_branch, access_mode, expected_status]
  factors:
    statement_branch:
      label: Start branch
      importance: important
      values: [start_transaction, begin]
    access_mode:
      label: Access mode
      importance: important
      values: [omitted, read_write, read_only, consistent_snapshot]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    statement_branch: start_transaction
    access_mode: omitted
    expected_status: success
  coverage_policy:
    main_combination_axes: [statement_branch, access_mode, expected_status]
    non_main_factors: []
    python_expand_threshold: 100
  rendering:
    statement_template: "{start_sql}{access_mode_sql}"
    verification_query_template: ""
    factor_value_bindings:
      start_sql:
        factor: statement_branch
        values:
          start_transaction: "START TRANSACTION"
          begin: "BEGIN"
      access_mode_sql:
        factor: access_mode
        values:
          omitted: ""
          read_write: " READ WRITE"
          read_only: " READ ONLY"
          consistent_snapshot: " WITH CONSISTENT SNAPSHOT"
```
