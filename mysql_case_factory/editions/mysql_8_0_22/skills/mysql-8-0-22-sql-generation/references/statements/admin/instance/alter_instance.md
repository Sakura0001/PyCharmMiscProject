# ALTER INSTANCE

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-instance.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: instance
  skill_name: alter_instance
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-instance.html
  statement:
    key: alter_instance
    name: ALTER INSTANCE
    aliases: [alter instance]
    purpose: Execute MySQL instance-level maintenance actions available in 8.0.22. RELOAD KEYRING is excluded because it was added in 8.0.24.
  syntax_templates:
    - "ALTER INSTANCE {ENABLE|DISABLE} INNODB REDO_LOG"
    - "ALTER INSTANCE ROTATE INNODB MASTER KEY"
    - "ALTER INSTANCE ROTATE BINLOG MASTER KEY"
    - "ALTER INSTANCE RELOAD TLS [FOR CHANNEL channel] [NO ROLLBACK ON ERROR]"
  factor_layers:
    - tier: T1
      factors: [action_branch, privilege_state, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    action_branch:
      label: Instance action
      importance: important
      values: [enable_redo_log, disable_redo_log, rotate_innodb_master_key, rotate_binlog_master_key, reload_tls]
    privilege_state:
      label: Privilege state
      importance: important
      values: [has_required_privilege, missing_required_privilege]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [safe_negative, isolated_positive, skip_destructive]
  defaults:
    action_branch: reload_tls
    privilege_state: missing_required_privilege
    expected_status: failure
    execution_mode: safe_negative
  coverage_policy:
    main_combination_axes: [action_branch, privilege_state, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 120
  rendering:
    statement_template: "ALTER INSTANCE RELOAD TLS"
    verification_query_template: "SHOW STATUS LIKE 'Ssl_server_not_after'"
    factor_value_bindings: {}
```
