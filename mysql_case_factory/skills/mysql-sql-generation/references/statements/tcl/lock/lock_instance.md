# LOCK INSTANCE FOR BACKUP

Official source: https://dev.mysql.com/doc/refman/8.0/en/lock-instance-for-backup.html

```yaml
structured_config:
  kind: statement
  category: tcl
  domain: lock
  skill_name: lock_instance
  official_source: https://dev.mysql.com/doc/refman/8.0/en/lock-instance-for-backup.html
  statement:
    key: lock_instance
    name: LOCK INSTANCE FOR BACKUP
    aliases: [lock instance for backup]
    purpose: Acquire an instance backup lock. Requires BACKUP_ADMIN and should be isolated from normal test runs.
  syntax_templates:
    - "LOCK INSTANCE FOR BACKUP"
  factor_layers:
    - tier: T1
      factors: [backup_lock_state, privilege_context, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    backup_lock_state:
      label: Backup lock state
      importance: important
      values: [not_held, already_held_by_session, held_by_other_session]
    privilege_context:
      label: Privilege context
      importance: important
      values: [has_backup_admin, missing_backup_admin]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [isolated_positive, safe_negative]
  defaults:
    backup_lock_state: not_held
    privilege_context: missing_backup_admin
    expected_status: failure
    execution_mode: safe_negative
  coverage_policy:
    main_combination_axes: [backup_lock_state, privilege_context, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 80
  rendering:
    statement_template: "LOCK INSTANCE FOR BACKUP"
    verification_query_template: ""
    factor_value_bindings: {}
```
