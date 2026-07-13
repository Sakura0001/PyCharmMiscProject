# SHUTDOWN

Official source: https://dev.mysql.com/doc/refman/8.0/en/shutdown.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: server
  skill_name: shutdown
  official_source: https://dev.mysql.com/doc/refman/8.0/en/shutdown.html
  statement:
    key: shutdown
    name: SHUTDOWN
    aliases: [shutdown]
    purpose: Server-level shutdown statement; positive execution must be isolated and disabled by default.
  syntax_templates:
    - "SHUTDOWN"
  factor_layers:
    - tier: T1
      factors: [privilege_context, execution_mode, expected_status]
  factors:
    privilege_context:
      label: Privilege context
      importance: important
      values: [shutdown_privilege, insufficient]
    execution_mode:
      label: Execution mode
      importance: important
      values: [skipped_negative, isolated_real_shutdown]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    privilege_context: insufficient
    execution_mode: skipped_negative
    expected_status: failure
  coverage_policy:
    main_combination_axes: [privilege_context, execution_mode, expected_status]
    non_main_factors: []
    python_expand_threshold: 20
  rendering:
    statement_template: "SHUTDOWN"
    verification_query_template: ""
    factor_value_bindings: {}
```
