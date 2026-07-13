# LOCK TABLES

Official source: https://dev.mysql.com/doc/refman/8.0/en/lock-tables.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: lock
  skill_name: lock_tables
  official_source: https://dev.mysql.com/doc/refman/8.0/en/lock-tables.html
  statement:
    key: lock_tables
    name: LOCK TABLES
    aliases: [lock tables]
    purpose: Acquire explicit table locks for the current session.
  syntax_templates:
    - "LOCK TABLES tbl_name [[AS] alias] lock_type [, tbl_name [[AS] alias] lock_type] ..."
  factor_layers:
    - tier: T1
      factors: [target_shape, lock_type, expected_status]
    - tier: T2
      factors: [transaction_interaction, privilege_context]
  factors:
    target_shape:
      label: Lock target
      importance: important
      values: [single_table, table_alias, multiple_tables, missing_table]
    lock_type:
      label: Lock type
      importance: important
      values: [read, read_local, write, low_priority_write]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    transaction_interaction:
      label: Transaction interaction
      importance: non_important
      values: [outside_transaction, active_transaction]
    privilege_context:
      label: Privilege context
      importance: non_important
      values: [has_required_privilege, missing_required_privilege]
  defaults:
    target_shape: single_table
    lock_type: read
    expected_status: success
    transaction_interaction: outside_transaction
    privilege_context: has_required_privilege
  coverage_policy:
    main_combination_axes: [target_shape, lock_type, expected_status]
    non_main_factors: [transaction_interaction, privilege_context]
    python_expand_threshold: 120
  rendering:
    statement_template: "LOCK TABLES {table_name} {lock_type_sql}"
    verification_query_template: ""
    factor_value_bindings:
      lock_type_sql:
        factor: lock_type
        values:
          read: "READ"
          read_local: "READ LOCAL"
          write: "WRITE"
          low_priority_write: "LOW_PRIORITY WRITE"
```
