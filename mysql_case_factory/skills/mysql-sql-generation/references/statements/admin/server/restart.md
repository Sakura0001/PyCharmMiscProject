# RESTART

Official source: https://dev.mysql.com/doc/refman/8.0/en/restart.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: server
  skill_name: restart
  official_source: https://dev.mysql.com/doc/refman/8.0/en/restart.html
  statement:
    key: restart
    name: RESTART
    aliases: [restart]
    purpose: Server-level restart statement; positive execution depends on monitor process and is disabled by default.
  syntax_templates:
    - "RESTART"
  factor_layers:
    - tier: T1
      factors: [privilege_context, monitor_state, execution_mode, expected_status]
  factors:
    privilege_context:
      label: Privilege context
      importance: important
      values: [shutdown_privilege, insufficient]
    monitor_state:
      label: Server monitor process
      importance: important
      values: [monitor_present, monitor_missing]
    execution_mode:
      label: Execution mode
      importance: important
      values: [skipped_negative, isolated_real_restart]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    privilege_context: insufficient
    monitor_state: monitor_missing
    execution_mode: skipped_negative
    expected_status: failure
  coverage_policy:
    main_combination_axes: [privilege_context, monitor_state, execution_mode, expected_status]
    non_main_factors: []
    python_expand_threshold: 20
  rendering:
    statement_template: "RESTART"
    verification_query_template: ""
    factor_value_bindings: {}
```
