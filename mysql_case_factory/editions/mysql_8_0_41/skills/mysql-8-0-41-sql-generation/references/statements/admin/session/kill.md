# KILL

Official source: https://dev.mysql.com/doc/refman/8.0/en/kill.html

```yaml
structured_config:
  kind: statement
  category: admin
  domain: session
  skill_name: kill
  official_source: https://dev.mysql.com/doc/refman/8.0/en/kill.html
  statement:
    key: kill
    name: KILL
    aliases: [kill]
    purpose: Kill a MySQL connection or query; executable positive cases should be isolated.
  syntax_templates:
    - "KILL [CONNECTION | QUERY] processlist_id"
  factor_layers:
    - tier: T1
      factors: [kill_modifier, target_thread, expected_status]
    - tier: T2
      factors: [privilege_context]
  factors:
    kill_modifier:
      label: KILL modifier
      importance: important
      values: [omitted, connection, query]
    target_thread:
      label: Target thread
      importance: important
      values: [own_thread, other_thread, system_user_thread, missing_thread]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    privilege_context:
      label: Privilege context
      importance: non_important
      values: [own_only, connection_admin, system_user, insufficient]
  defaults:
    kill_modifier: query
    target_thread: missing_thread
    expected_status: failure
    privilege_context: own_only
  coverage_policy:
    main_combination_axes: [kill_modifier, target_thread, expected_status]
    non_main_factors: [privilege_context]
    python_expand_threshold: 100
  rendering:
    statement_template: "KILL QUERY 999999999"
    verification_query_template: ""
    factor_value_bindings: {}
```
