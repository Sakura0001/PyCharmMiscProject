# DROP TRIGGER

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-trigger.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: trigger
  skill_name: drop_trigger
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-trigger.html
  statement:
    key: drop_trigger
    name: DROP TRIGGER
    aliases: [drop trigger]
    purpose: Drop a MySQL trigger. MySQL has no ON table clause and no CASCADE/RESTRICT for this statement.
  syntax_templates:
    - "DROP TRIGGER [IF EXISTS] [schema_name.]trigger_name"
  factor_layers:
    - tier: T1
      factors: [if_exists, trigger_state, expected_status]
  factors:
    if_exists:
      label: IF EXISTS
      importance: important
      values: [omitted, present]
    trigger_state:
      label: Trigger state
      importance: important
      values: [exists, missing, table_dropped]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
  defaults:
    if_exists: omitted
    trigger_state: exists
    expected_status: success
  coverage_policy:
    main_combination_axes: [if_exists, trigger_state, expected_status]
    non_main_factors: []
    python_expand_threshold: 80
  rendering:
    statement_template: "DROP TRIGGER {if_exists_sql}{trigger_name}"
    verification_query_template: "SELECT TRIGGER_NAME FROM INFORMATION_SCHEMA.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE() AND TRIGGER_NAME = '{trigger_name}'"
    factor_value_bindings:
      if_exists_sql:
        factor: if_exists
        values: {omitted: "", present: "IF EXISTS "}
```
