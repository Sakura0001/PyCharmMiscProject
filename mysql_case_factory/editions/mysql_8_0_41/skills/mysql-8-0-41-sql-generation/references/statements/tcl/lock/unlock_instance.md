# UNLOCK INSTANCE

Official source: https://dev.mysql.com/doc/refman/8.0/en/lock-instance-for-backup.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: lock
  skill_name: unlock_instance
  official_source: https://dev.mysql.com/doc/refman/8.0/en/lock-instance-for-backup.html
  statement:
    key: unlock_instance
    name: UNLOCK INSTANCE
    aliases: [unlock instance]
    purpose: Release an instance backup lock held by the current session.
  syntax_templates:
    - "UNLOCK INSTANCE"
  factor_layers:
    - tier: T1
      factors: [held_backup_lock_state, session_ownership, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    held_backup_lock_state:
      label: Held backup lock state
      importance: important
      values: [held_by_session, not_held, held_by_other_session]
    session_ownership:
      label: Session ownership
      importance: important
      values: [same_session, different_session]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [isolated_positive, safe_negative]
  defaults:
    held_backup_lock_state: not_held
    session_ownership: same_session
    expected_status: failure
    execution_mode: safe_negative
  coverage_policy:
    main_combination_axes: [held_backup_lock_state, session_ownership, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "UNLOCK INSTANCE"
    verification_query_template: ""
    factor_value_bindings: {}
```
