# RESET

Official sources:

- https://dev.mysql.com/doc/refman/8.0/en/reset.html
- https://dev.mysql.com/doc/refman/8.0/en/reset-persist.html

```yaml
structured_config:
  kind: statement
  category: session
  domain: runtime_parameter
  skill_name: reset
  official_source: https://dev.mysql.com/doc/refman/8.0/en/reset.html
  statement:
    key: reset
    name: RESET
    aliases: [reset, reset persist]
    purpose: Generate MySQL RESET and RESET PERSIST administrative cases.
  syntax_templates:
    - "RESET reset_option [, reset_option] ..."
    - "RESET PERSIST [IF EXISTS] system_var_name"
  factor_layers:
    - tier: T1
      factors: [statement_branch, target_shape, expected_status]
    - tier: T2
      factors: [if_exists, privilege_context]
  factors:
    statement_branch:
      label: RESET branch
      importance: important
      values: [reset_master, reset_replica, reset_persist]
    target_shape:
      label: Reset target
      importance: important
      values: [existing_target, missing_target]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    if_exists:
      label: IF EXISTS for RESET PERSIST
      importance: non_important
      values: [omitted, present]
    privilege_context:
      label: Privilege context
      importance: non_important
      values: [sufficient, insufficient]
  defaults:
    statement_branch: reset_persist
    target_shape: existing_target
    expected_status: success
    if_exists: omitted
    privilege_context: sufficient
  coverage_policy:
    main_combination_axes: [statement_branch, target_shape, expected_status]
    non_main_factors: [if_exists, privilege_context]
    python_expand_threshold: 100
  rendering:
    statement_template: "RESET PERSIST {if_exists_sql}max_connections"
    verification_query_template: ""
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
