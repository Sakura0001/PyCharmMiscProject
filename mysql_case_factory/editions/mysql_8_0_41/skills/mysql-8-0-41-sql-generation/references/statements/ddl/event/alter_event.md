# ALTER EVENT

Official source: https://dev.mysql.com/doc/refman/8.0/en/alter-event.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: event
  skill_name: alter_event
  official_source: https://dev.mysql.com/doc/refman/8.0/en/alter-event.html
  statement:
    key: alter_event
    name: ALTER EVENT
    aliases: [alter event]
    purpose: Alter a MySQL Event Scheduler event.
  syntax_templates:
    - "ALTER [DEFINER = user] EVENT event_name [ON SCHEDULE schedule] [ON COMPLETION [NOT] PRESERVE] [RENAME TO new_event_name] [ENABLE | DISABLE | DISABLE ON SLAVE] [COMMENT 'string'] [DO event_body]"
  factor_layers:
    - tier: T1
      factors: [event_state, alteration_shape, expected_status]
    - tier: T2
      factors: [schedule_shape, enable_state]
  factors:
    event_state:
      label: Event state
      importance: important
      values: [exists, missing]
    alteration_shape:
      label: Alteration branch
      importance: important
      values: [reschedule, rename, enable_disable, replace_body, comment]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    schedule_shape:
      label: Event schedule
      importance: non_important
      values: [at_timestamp, every_interval]
    enable_state:
      label: Event enable state
      importance: non_important
      values: [enable, disable, disable_on_slave]
  defaults:
    event_state: exists
    alteration_shape: comment
    expected_status: success
    schedule_shape: at_timestamp
    enable_state: disable
  coverage_policy:
    main_combination_axes: [event_state, alteration_shape, expected_status]
    non_main_factors: [schedule_shape, enable_state]
    python_expand_threshold: 120
  rendering:
    statement_template: "ALTER EVENT {event_name} COMMENT 'mysql case event'"
    verification_query_template: "SELECT EVENT_NAME FROM INFORMATION_SCHEMA.EVENTS WHERE EVENT_SCHEMA = DATABASE() AND EVENT_NAME = '{event_name}'"
    factor_value_bindings: {}
```
