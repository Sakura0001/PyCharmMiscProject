# DROP EVENT

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-event.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: event
  skill_name: drop_event
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-event.html
  statement:
    key: drop_event
    name: DROP EVENT
    aliases: [drop event]
    purpose: Drop a MySQL Event Scheduler event.
  syntax_templates:
    - "DROP EVENT [IF EXISTS] event_name"
  factor_layers:
    - tier: T1
      factors: [if_exists, event_state, expected_status]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    event_state:
      label: Event state
      importance: important
      values: [exists, missing]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    if_exists: omitted
    event_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [if_exists, event_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "DROP EVENT {if_exists_sql}{event_name}"
    verification_query_template: "SELECT EVENT_NAME FROM INFORMATION_SCHEMA.EVENTS WHERE EVENT_SCHEMA = DATABASE() AND EVENT_NAME = '{event_name}'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
