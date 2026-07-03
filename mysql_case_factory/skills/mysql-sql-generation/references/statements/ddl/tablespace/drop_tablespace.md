# DROP TABLESPACE

Official source: https://dev.mysql.com/doc/refman/8.0/en/drop-tablespace.html

```yaml
structured_config:
  kind: statement
  category: ddl
  domain: tablespace
  skill_name: drop_tablespace
  official_source: https://dev.mysql.com/doc/refman/8.0/en/drop-tablespace.html
  statement:
    key: drop_tablespace
    name: DROP TABLESPACE
    aliases: [drop tablespace]
    purpose: Drop a MySQL tablespace. Non-empty and NDB cases require isolated handling.
  syntax_templates:
    - "DROP TABLESPACE tablespace_name [ENGINE [=] engine_name]"
    - "DROP UNDO TABLESPACE tablespace_name"
  factor_layers:
    - tier: T1
      factors: [tablespace_state, tablespace_kind, expected_status]
    - tier: T5
      factors: [execution_mode]
  factors:
    tablespace_state:
      label: Tablespace state
      importance: important
      values: [empty_exists, non_empty_exists, missing]
    tablespace_kind:
      label: Tablespace kind
      importance: important
      values: [innodb_general, undo, ndb_disk_data]
    expected_status:
      label: Expected result
      importance: important
      values: [success, failure]
    execution_mode:
      label: Execution safety mode
      importance: non_important
      values: [isolated_positive, safe_negative, skip_ndb]
  defaults:
    tablespace_state: empty_exists
    tablespace_kind: innodb_general
    expected_status: success
    execution_mode: isolated_positive
  coverage_policy:
    main_combination_axes: [tablespace_state, tablespace_kind, expected_status]
    non_main_factors: [execution_mode]
    python_expand_threshold: 100
  rendering:
    statement_template: "DROP TABLESPACE {tablespace_name} ENGINE = InnoDB"
    verification_query_template: "SELECT TABLESPACE_NAME FROM INFORMATION_SCHEMA.FILES WHERE TABLESPACE_NAME = '{tablespace_name}'"
    factor_value_bindings: {}
```
