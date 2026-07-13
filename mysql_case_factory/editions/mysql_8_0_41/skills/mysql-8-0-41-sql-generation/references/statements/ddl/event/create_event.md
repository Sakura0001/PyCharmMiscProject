# CREATE EVENT

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-event.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: event
  skill_name: create_event
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-event.html
  statement:
    key: create_event
    name: CREATE EVENT
    aliases: [create event]
    purpose: Create a MySQL Event Scheduler event. This is not a PostgreSQL event trigger equivalent.
  syntax_templates:
    - "CREATE [DEFINER = user] EVENT [IF NOT EXISTS] event_name ON SCHEDULE schedule [ON COMPLETION [NOT] PRESERVE] [ENABLE | DISABLE | DISABLE ON SLAVE] [COMMENT 'string'] DO event_body"
  factor_layers:
    - tier: T1
      factors: [if_not_exists, schedule_shape, body_shape, expected_status]
    - tier: T2
      factors: [completion_shape, enable_state, definer_shape]
  factors:
    if_not_exists:
      label: IF NOT EXISTS
      importance: important
      values: [omitted, present]
    schedule_shape:
      label: Event schedule
      importance: important
      values: [at_timestamp, every_interval, starts_ends]
    body_shape:
      label: Event body
      importance: important
      values: [single_statement, compound_block, invalid_body]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    completion_shape:
      label: ON COMPLETION
      importance: non_important
      values: [omitted, preserve, not_preserve]
    enable_state:
      label: Event enable state
      importance: non_important
      values: [enable, disable, disable_on_slave]
    definer_shape:
      label: DEFINER
      importance: non_important
      values: [omitted, current_user, explicit_user]
  defaults:
    if_not_exists: omitted
    schedule_shape: at_timestamp
    body_shape: single_statement
    expected_status: success
    completion_shape: omitted
    enable_state: disable
    definer_shape: omitted
  coverage_policy:
    main_combination_axes: [if_not_exists, schedule_shape, body_shape, expected_status]
    non_main_factors: [completion_shape, enable_state, definer_shape]
    python_expand_threshold: 180
  rendering:
    statement_template: "CREATE EVENT {if_not_exists_sql}{event_name} ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 1 HOUR DISABLE DO SET @mysql_case_factory_event = 1"
    verification_query_template: "SELECT EVENT_NAME FROM INFORMATION_SCHEMA.EVENTS WHERE EVENT_SCHEMA = DATABASE() AND EVENT_NAME = '{event_name}'"
    factor_value_bindings:
      if_not_exists_sql:
        factor: if_not_exists
        values: {omitted: "", present: "IF NOT EXISTS "}
```
