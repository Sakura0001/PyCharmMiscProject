# CREATE TRIGGER

Official source: https://dev.mysql.com/doc/refman/8.0/en/create-trigger.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: trigger
  skill_name: create_trigger
  official_source: https://dev.mysql.com/doc/refman/8.0/en/create-trigger.html
  statement:
    key: create_trigger
    name: CREATE TRIGGER
    aliases: [create trigger]
    purpose: Create a MySQL row trigger. MySQL 8.0.22 excludes CREATE TRIGGER IF NOT EXISTS.
  syntax_templates:
    - "CREATE [DEFINER = user] TRIGGER trigger_name trigger_time trigger_event ON tbl_name FOR EACH ROW [trigger_order] trigger_body"
  factor_layers:
    - tier: T1
      factors: [trigger_time, trigger_event, body_shape, expected_status]
    - tier: T2
      factors: [definer_shape, trigger_order]
  factors:
    trigger_time:
      label: Trigger time
      importance: important
      values: [before, after]
    trigger_event:
      label: Trigger event
      importance: important
      values: [insert, update, delete]
    body_shape:
      label: Trigger body
      importance: important
      values: [set_new_value, audit_insert, invalid_body]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    definer_shape:
      label: DEFINER
      importance: non_important
      values: [omitted, current_user, explicit_user]
    trigger_order:
      label: Trigger order
      importance: non_important
      values: [omitted, follows, precedes]
  defaults:
    trigger_time: before
    trigger_event: insert
    body_shape: set_new_value
    expected_status: success
    definer_shape: omitted
    trigger_order: omitted
  coverage_policy:
    main_combination_axes: [trigger_time, trigger_event, body_shape, expected_status]
    non_main_factors: [definer_shape, trigger_order]
    python_expand_threshold: 160
  rendering:
    statement_template: "CREATE TRIGGER {trigger_name} BEFORE INSERT ON {table_name} FOR EACH ROW SET NEW.value_col = COALESCE(NEW.value_col, 0)"
    verification_query_template: "SELECT TRIGGER_NAME FROM INFORMATION_SCHEMA.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE() AND TRIGGER_NAME = '{trigger_name}'"
    factor_value_bindings: {}
```
